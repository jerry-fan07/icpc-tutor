"""Grading the learner's side of the dialogue.

Kept apart from the web API so the validator can check that every question in the
curriculum accepts its own answer: a Numeric whose answer does not parse, or a Short
whose accepted answers normalise to nothing, is a bug in the lesson.
"""
from __future__ import annotations

import ast
import math
import operator
import re

from .schema import MCQ, Numeric, Reflect, Short, Try

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in ("e", "pi"):
        return math.e if node.id == "e" else math.pi
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        a, b = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(b) > 400:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](a, b)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1:
        fn = {"log2": math.log2, "log": math.log, "sqrt": math.sqrt,
              "lg": math.log2, "ln": math.log}.get(node.func.id)
        if fn:
            return fn(_eval(node.args[0]))
    raise ValueError("not arithmetic")


def parse_number(text: str) -> float:
    return float(parse_value(text))


def parse_value(text: str) -> int | float:
    """'4e10', '4*10^10', '4·10¹⁰'-ish, '2^20', '1,000,000', '2 * 10^5', '1e9+7',
    '10**9', '3/4' all parse.  Raises ValueError otherwise."""
    s = (text or "").strip().lower()
    if not s:
        raise ValueError("empty")
    s = s.replace("·", "*").replace("×", "*").replace("−", "-")
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)          # 1,000,000
    s = re.sub(r"(?<=\d)_(?=\d)", "", s)                # 1_000_000
    s = s.replace("^", "**")
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"(\d)(\()", r"\1*\2", s)                 # 2(3) -> 2*(3)
    for word, value in (("thousand", "*1e3"), ("million", "*1e6"), ("billion", "*1e9")):
        s = s.replace(word, value)
    s = s.lstrip("~≈")
    if len(s) > 80:
        raise ValueError("too long")
    try:
        v = _eval(ast.parse(s, mode="eval"))
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as e:
        raise ValueError(str(e)) from None
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        raise ValueError("not finite")
    return v


def normalize(text: str) -> str:
    """Case-folded, whitespace-collapsed, with surrounding quotes/backticks and a
    trailing period removed: what a Short answer is compared by."""
    s = (text or "").strip()
    s = s.replace("\u2212", "-").replace("\u2013", "-")      # typographic minus / en dash
    s = s.strip("`\"'")
    s = s.rstrip(".")
    return " ".join(s.lower().split())


def loose(text: str) -> str:
    """normalize(), with commas, semicolons and brackets read as separators."""
    return " ".join(re.sub(r"[,;()\[\]{}]", " ", normalize(text)).split())


def numeric_ok(step: Numeric, value) -> bool:
    if isinstance(value, float) and math.isnan(value):
        return False
    # an exact integer answer is compared exactly: floats would let 2^53 + 1 pass as 2^53
    if not step.tol and not step.rel and float(step.answer).is_integer() \
            and float(value).is_integer():
        exact = step.answer if isinstance(step.answer, int) else int(step.answer)
        return (value if isinstance(value, int) else int(value)) == exact
    diff = abs(value - step.answer)
    if diff <= step.tol + 1e-9 * max(1.0, abs(step.answer)):
        return True
    if step.rel and diff <= step.rel * abs(step.answer):
        return True
    return False


def grade(step, response) -> dict:
    """{"correct": bool, "feedback": markup} for one attempt at a question.

    MCQ response: option index.  Numeric/Short: the text typed."""
    if isinstance(step, MCQ):
        try:
            i = int(response)
            opt = step.options[i]
        except (TypeError, ValueError, IndexError):
            return {"correct": False, "feedback": "Pick one of the options."}
        return {"correct": bool(opt.correct), "feedback": opt.why, "choice": i}
    if isinstance(step, Numeric):
        try:
            v = parse_value(str(response))
        except ValueError:
            return {"correct": False, "invalid": True,
                    "feedback": "That did not read as a number. Try forms like `2e5`, "
                                "`4*10^10`, `2^20` or `1,000,000`."}
        ok = numeric_ok(step, v)
        fb = ""
        if not ok and step.answer:
            ratio = v / step.answer if step.answer else 0
            if ratio > 0 and (ratio >= 10 or ratio <= 0.1):
                fb = f"Off by a factor of about {max(ratio, 1 / ratio):.0f}."
            elif v > step.answer:
                fb = "Too high."
            else:
                fb = "Too low."
        return {"correct": ok, "feedback": fb, "value": v}
    if isinstance(step, Short):
        given = normalize(str(response))
        if not given:
            return {"correct": False, "invalid": True, "feedback": "Type an answer first."}
        ok = any(given == normalize(a) for a in step.accept)
        if not ok:
            # "0 1 2" vs "0\n1\n2": whitespace was collapsed already; try without spaces
            squashed = given.replace(" ", "")
            ok = any(squashed == normalize(a).replace(" ", "") for a in step.accept)
        if not ok:
            # "6,3,1", "(6, 3, 1)" and "[6 3 1]" all mean the list 6 3 1
            ok = any(loose(given) == loose(a) for a in step.accept)
        return {"correct": ok, "feedback": "" if ok else "Not quite."}
    if isinstance(step, (Reflect, Try)):
        return {"correct": True, "feedback": ""}
    return {"correct": False, "feedback": "This step takes no answer."}


def format_number(a) -> str:
    """2,147,483,647 / 0.5 / 8·10^18 (the page renders ^ as a superscript)."""
    if isinstance(a, int):
        return f"{a:,}"                     # an exact answer is shown exactly
    if float(a).is_integer() and abs(a) < 1e6:
        return f"{int(a):,}"
    shown = f"{a:.4g}"
    if "e" in shown:
        mant, exp = shown.split("e")
        return f"{mant}·10^{int(exp)}"
    return shown


def answer_text(step) -> str:
    """The right answer, as markup, for when the learner asks to be shown."""
    if isinstance(step, MCQ):
        right = [o.text for o in step.options if o.correct]
        return "The answer: " + " / ".join(right)
    if isinstance(step, Numeric):
        return f"The answer: {format_number(step.answer)}" + (f" {step.unit}" if step.unit else "")
    if isinstance(step, Short):
        return f"The answer: `{step.accept[0]}`"
    if isinstance(step, Reflect):
        return step.answer
    return ""
