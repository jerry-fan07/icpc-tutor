"""`python3 cp.py validate [lesson_id ...]`

Checks every lesson for structural problems, checks that every question accepts its
own answer, and runs every problem's C++ through the real judge:

  - the reference solution compiles, matches the sample outputs, and passes every
    test inside a third of the time limit (warning) and inside the limit (error);
  - generators return strings and are deterministic;
  - `brute`, when given, agrees with the reference on every test that is not large;
  - `naive`, when given, times out on at least one large test -- otherwise the large
    tests do not enforce the complexity the lesson is teaching;
  - the starter does not already pass.

Exit status 1 on any error.
"""
from __future__ import annotations

import random
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from . import judge, loader
from .dialogue import grade
from .schema import (CHECKERS, DIFFICULTIES, MCQ, TRACKS, Card, Lesson, Numeric, Opt, Part,
                     Problem, Reflect, Say, Short, Try, is_gate)

MIN_PARTS = 3
MIN_QUESTIONS = 10          # MCQ / Numeric / Short / Reflect across the dialogue
MIN_CARDS = 6
MIN_PROBLEMS = 2
MAX_SAY_RUN = 2             # consecutive Say steps before the learner must be asked something
SAY_LONG = 2600             # characters; longer Say steps are a lecture, not a dialogue
ID_RE = re.compile(r"^(cpp|algo)\d{2}$")
# The fixed curriculum map (curriculum/AUTHORING.md).  A prereq may name a lesson that
# is planned but not written yet; anything else is a typo.
PLANNED = {f"cpp{i:02d}" for i in range(1, 11)} | {f"algo{i:02d}" for i in range(1, 26)}
SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _fences(text: str) -> bool:
    return (text or "").count("```") % 2 == 0


def check_structure(l: Lesson, all_ids: set[str]) -> tuple[list[str], list[str]]:
    errs: list[str] = []
    warns: list[str] = []
    lid = l.id
    if not ID_RE.match(lid):
        errs.append(f"{lid}: id must look like cpp03 or algo12")
    if l.track not in TRACKS or not lid.startswith(l.track):
        errs.append(f"{lid}: track {l.track!r} does not match the id")
    if not l.title.strip() or not l.summary.strip():
        errs.append(f"{lid}: missing title or summary")
    for p in l.prereqs:
        if p not in all_ids and p not in PLANNED:
            errs.append(f"{lid}: unknown prereq {p!r}")
        elif p not in all_ids:
            warns.append(f"{lid}: prereq {p} is planned but not written yet")
        if p == lid:
            errs.append(f"{lid}: lists itself as a prereq")

    # ---- dialogue -----------------------------------------------------------
    if len(l.parts) < MIN_PARTS:
        errs.append(f"{lid}: only {len(l.parts)} parts (min {MIN_PARTS})")
    questions = 0
    tried = set()
    for pi, part in enumerate(l.parts):
        if not isinstance(part, Part):
            errs.append(f"{lid}: parts[{pi}] is not a Part")
            continue
        where = f"{lid} part {pi + 1} ({part.title[:30]!r})"
        if not part.title.strip() or not part.steps:
            errs.append(f"{where}: empty title or no steps")
        run = 0
        for si, s in enumerate(part.steps):
            at = f"{where} step {si + 1}"
            if not isinstance(s, (Say, MCQ, Numeric, Short, Reflect, Try)):
                errs.append(f"{at}: {type(s).__name__} is not a step type")
                continue
            if isinstance(s, Say):
                run += 1
                if run > MAX_SAY_RUN:
                    errs.append(f"{at}: {run} Say steps in a row -- ask the learner something")
                if not s.text.strip():
                    errs.append(f"{at}: empty Say")
                if len(s.text) > SAY_LONG:
                    warns.append(f"{at}: Say is {len(s.text)} chars; split it with a question")
                if not _fences(s.text):
                    errs.append(f"{at}: unbalanced ``` fence")
                continue
            run = 0
            texts = []
            if isinstance(s, MCQ):
                questions += 1
                texts = [s.q, s.explain, s.hint] + [o.text + o.why for o in s.options]
                if len(s.options) < 2:
                    errs.append(f"{at}: MCQ needs at least 2 options")
                if not any(o.correct for o in s.options):
                    errs.append(f"{at}: MCQ has no correct option")
                for k, o in enumerate(s.options):
                    if not isinstance(o, Opt):
                        errs.append(f"{at}: option {k + 1} is not an Opt")
                    elif not o.why.strip():
                        errs.append(f"{at}: option {k + 1} ({o.text[:30]!r}) has no `why`")
                right = next((k for k, o in enumerate(s.options) if o.correct), None)
                if right is not None and not grade(s, right)["correct"]:
                    errs.append(f"{at}: MCQ does not accept its own answer")
            elif isinstance(s, Numeric):
                questions += 1
                texts = [s.q, s.explain, s.hint]
                if not isinstance(s.answer, (int, float)):
                    errs.append(f"{at}: Numeric answer must be a number")
                elif not grade(s, repr(s.answer))["correct"]:
                    errs.append(f"{at}: Numeric does not accept its own answer")
                if not s.explain.strip():
                    warns.append(f"{at}: Numeric has no `explain`")
            elif isinstance(s, Short):
                questions += 1
                texts = [s.q, s.explain, s.hint]
                if not s.accept or not all(isinstance(a, str) and a.strip() for a in s.accept):
                    errs.append(f"{at}: Short needs non-empty accepted answers")
                elif not grade(s, s.accept[0])["correct"]:
                    errs.append(f"{at}: Short does not accept its own answer")
                if not s.explain.strip():
                    warns.append(f"{at}: Short has no `explain`")
            elif isinstance(s, Reflect):
                questions += 1
                texts = [s.q, s.answer]
                if len(s.answer.strip()) < 40:
                    errs.append(f"{at}: Reflect answer is too thin (<40 chars)")
            elif isinstance(s, Try):
                texts = [s.note]
                if l.problem(s.problem) is None:
                    errs.append(f"{at}: Try names unknown problem {s.problem!r}")
                tried.add(s.problem)
            if hasattr(s, "q") and not s.q.strip():
                errs.append(f"{at}: empty question")
            for t in texts:
                if not _fences(t):
                    errs.append(f"{at}: unbalanced ``` fence")
    if questions < MIN_QUESTIONS:
        errs.append(f"{lid}: only {questions} questions in the dialogue (min {MIN_QUESTIONS})")
    if l.parts and l.parts[-1].steps and not any(is_gate(s) for s in l.parts[-1].steps):
        warns.append(f"{lid}: the last part asks nothing")

    # ---- cards --------------------------------------------------------------
    if len(l.cards) < MIN_CARDS:
        errs.append(f"{lid}: only {len(l.cards)} cards (min {MIN_CARDS})")
    for q, n in Counter(c.q.strip() for c in l.cards).items():
        if n > 1:
            errs.append(f"{lid}: duplicate card {q[:50]!r}")
    for c in l.cards:
        if not isinstance(c, Card) or not c.q.strip() or not c.a.strip():
            errs.append(f"{lid}: card with an empty side")
        elif not (_fences(c.q) and _fences(c.a)):
            errs.append(f"{lid}: card {c.q[:40]!r} has an unbalanced fence")

    # ---- problems -----------------------------------------------------------
    if len(l.problems) < MIN_PROBLEMS:
        errs.append(f"{lid}: only {len(l.problems)} problems (min {MIN_PROBLEMS})")
    seen = set()
    for p in l.problems:
        tag = f"{lid}.{getattr(p, 'id', '?')}"
        if not isinstance(p, Problem):
            errs.append(f"{tag}: not a Problem")
            continue
        if p.id in seen:
            errs.append(f"{tag}: duplicate problem id")
        seen.add(p.id)
        if not SNAKE_RE.match(p.id):
            errs.append(f"{tag}: id must be lower snake_case")
        if p.id not in tried:
            errs.append(f"{tag}: no Try step leads to this problem")
        if p.difficulty not in DIFFICULTIES:
            errs.append(f"{tag}: bad difficulty {p.difficulty!r}")
        if not callable(p.checker) and p.checker.split(":")[0] not in CHECKERS:
            errs.append(f"{tag}: bad checker {p.checker!r}")
        for name in ("statement", "input", "output", "editorial"):
            if len(getattr(p, name).strip()) < (40 if name in ("statement", "editorial") else 8):
                errs.append(f"{tag}: `{name}` is missing or too short")
            if not _fences(getattr(p, name)):
                errs.append(f"{tag}: `{name}` has an unbalanced fence")
        if not p.samples:
            errs.append(f"{tag}: no samples")
        for i, t in enumerate(p.samples, 1):
            if t.output is None:
                errs.append(f"{tag}: sample {i} needs an explicit output")
        if not p.hints:
            warns.append(f"{tag}: no hints")
        if not p.tests and not p.gens:
            errs.append(f"{tag}: no hidden tests (tests or gens)")
        for name, n in Counter(g.name for g in p.gens).items():
            if n > 1:
                errs.append(f"{tag}: two generators are named {name!r}; names key the test "
                            f"cache, so they must be unique within a problem")
        if not (0.2 <= p.time_limit <= 10):
            errs.append(f"{tag}: time_limit {p.time_limit} is outside 0.2..10 s")
        for name in ("solution", "brute", "naive", "starter"):
            code = getattr(p, name)
            if code and "main" not in code:
                errs.append(f"{tag}: `{name}` has no main()")
    return errs, warns


def check_problem(l: Lesson, p: Problem) -> tuple[list[str], list[str], str]:
    """Run the problem's C++ through the judge.  Returns (errors, warnings, summary)."""
    errs: list[str] = []
    warns: list[str] = []
    tag = f"{l.id}.{p.id}"
    t0 = time.monotonic()

    ref = judge.compile_source(p.solution)
    if not ref.ok:
        return [f"{tag}: reference does not compile:\n{_indent(ref.errors)}"], warns, ""
    if ref.errors:
        warns.append(f"{tag}: reference compiles with warnings:\n{_indent(ref.errors, 6)}")

    # generators: strings, deterministic
    for g in p.gens:
        try:
            a = g.fn(random.Random(12345))
            b = g.fn(random.Random(12345))
        except Exception as e:                              # noqa: BLE001
            errs.append(f"{tag}: generator {g.name!r} raised {type(e).__name__}: {e}")
            continue
        if not isinstance(a, str):
            errs.append(f"{tag}: generator {g.name!r} returned {type(a).__name__}, not str")
        elif a != b:
            errs.append(f"{tag}: generator {g.name!r} is not deterministic (use the rng argument)")
    if errs:
        return errs, warns, ""

    try:
        all_cases = judge.cases(l, p)
    except Exception as e:                                  # noqa: BLE001
        return [f"{tag}: building tests failed: {type(e).__name__}: {e}"], warns, ""

    # samples must match what the statement says
    worst = 0.0
    for c in all_cases:
        o = judge.run(ref.binary, c.input, max(p.time_limit * 3, 3.0))
        worst = max(worst, o.cpu_ms)
        if o.status != "ok":
            errs.append(f"{tag}: reference fails {c.name} ({c.gen or c.kind}): {o.status} {o.message}")
            continue
        if c.output is not None:
            ok, msg = judge.check(p.checker, c.input, c.output, o.stdout)
            if not ok:
                errs.append(f"{tag}: reference disagrees with the given output of {c.name}: {msg}")
        if o.cpu_ms > p.time_limit * 1000:
            errs.append(f"{tag}: reference takes {o.cpu_ms:.0f} ms on {c.name}; "
                        f"limit is {p.time_limit:g} s")
        elif o.cpu_ms > p.time_limit * 1000 / 3:
            warns.append(f"{tag}: reference takes {o.cpu_ms:.0f} ms on {c.name}, "
                         f"more than a third of the {p.time_limit:g} s limit")
    if errs:
        return errs, warns, ""
    # a custom checker must accept the reference's own output
    if callable(p.checker):
        for c in all_cases:
            want = judge.expected(p, c)
            ok, msg = judge.check(p.checker, c.input, want, want)
            if not ok:
                errs.append(f"{tag}: checker rejects the reference's own output on {c.name}: {msg}")
                break

    sizes = [len(c.input) for c in all_cases if c.large]
    if p.naive and not sizes:
        errs.append(f"{tag}: has a `naive` solution but no large generated tests")

    # every test input respects the statement
    if p.check_input is not None:
        for c in all_cases:
            try:
                verdict = p.check_input(c.input)
            except Exception as e:                          # noqa: BLE001
                verdict = f"{type(e).__name__}: {e}"
            if verdict is False or isinstance(verdict, str):
                errs.append(f"{tag}: {c.name} ({c.gen or c.kind}) breaks the constraints: "
                            f"{verdict if isinstance(verdict, str) else 'check_input said no'}")
                break

    # brute agrees on everything small
    if p.brute:
        b = judge.compile_source(p.brute)
        if not b.ok:
            errs.append(f"{tag}: brute does not compile:\n{_indent(b.errors)}")
        else:
            checked = 0
            for c in all_cases:
                if not c.brute:
                    continue
                o = judge.run(b.binary, c.input, 10.0)
                if o.status != "ok":
                    errs.append(f"{tag}: brute fails {c.name}: {o.status} {o.message}")
                    break
                ok, msg = judge.check(p.checker, c.input, judge.expected(p, c), o.stdout)
                if not ok:
                    errs.append(f"{tag}: brute and reference disagree on {c.name} "
                                f"({c.gen or c.kind}): {msg}\n      input: {c.input[:200]!r}")
                    break
                checked += 1
            if checked and checked < 8:
                warns.append(f"{tag}: brute cross-checked on only {checked} tests; add small gens")

    # naive must be too slow somewhere
    if p.naive:
        nv = judge.compile_source(p.naive)
        if not nv.ok:
            errs.append(f"{tag}: naive does not compile:\n{_indent(nv.errors)}")
        else:
            slow = False
            crashed = ""
            for c in all_cases:
                if not c.large:
                    continue
                o = judge.run(nv.binary, c.input, p.time_limit, wall_factor=1.0)
                if o.status == "tle":
                    slow = True
                    break
                if o.status != "ok" and not crashed:
                    crashed = f"{c.name}: {o.status} {o.message}"
            if not slow:
                errs.append(f"{tag}: naive never exceeds the time limit on a large test"
                            + (f" (it crashed instead on {crashed})" if crashed else
                               f" -- the large tests do not enforce the intended complexity"))

    # each tempting wrong program is rejected
    for i, w in enumerate(p.wrong, 1):
        wc = judge.compile_source(w)
        if not wc.ok:
            errs.append(f"{tag}: wrong[{i}] does not compile:\n{_indent(wc.errors)}")
            continue
        res = judge.judge_binary(l, p, wc.binary, "submit")
        if res["verdict"] == "AC":
            errs.append(f"{tag}: wrong[{i}] is accepted -- the tests no longer catch that mistake")

    # the starter must not already pass
    st = judge.compile_source(p.starter)
    if st.ok:
        res = judge.judge_binary(l, p, st.binary, "submit")
        if res["verdict"] == "AC":
            errs.append(f"{tag}: the starter already passes")

    n = len(all_cases)
    big = f", largest input {max(sizes) / 1024:.0f} KB" if sizes else ""
    summary = (f"{tag}: {n} tests{big}, reference worst {worst:.0f} ms / {p.time_limit:g} s"
               f"{', brute ok' if p.brute and not errs else ''}"
               f"{', naive TLEs' if p.naive and not errs else ''}"
               f"{f', {len(p.wrong)} wrong rejected' if p.wrong and not errs else ''}"
               f"  [{time.monotonic() - t0:.1f}s]")
    return errs, warns, summary


def _indent(text: str, n: int = 6) -> str:
    lines = (text or "").strip().splitlines()[:25]
    return "\n".join(" " * n + ln for ln in lines)


def validate(ids: list[str] | None = None, run: bool = True, quiet: bool = False) -> int:
    lessons = loader.load_all()
    errors = loader.load_errors()
    total_errs = 0
    for mod, e in errors.items():
        if not ids or any(mod.startswith(i) for i in ids):
            print(f"LOAD ERROR curriculum/{mod}.py: {e}")
            total_errs += 1
    all_ids = {l.id for l in lessons}
    dupes = [i for i, n in Counter(l.id for l in lessons).items() if n > 1]
    for d in dupes:
        print(f"ERROR: duplicate lesson id {d}")
        total_errs += 1
    chosen = [l for l in lessons if not ids or l.id in ids]
    if ids:
        missing = set(ids) - {l.id for l in chosen}
        for m in sorted(missing):
            if not any(k.startswith(m) for k in errors):
                print(f"ERROR: no lesson {m!r}")
                total_errs += 1

    jobs = []
    report: dict[str, list] = {}
    for l in chosen:
        errs, warns = check_structure(l, all_ids)
        report[l.id] = [errs, warns, []]
        if run:
            jobs += [(l, p) for p in l.problems if isinstance(p, Problem)]

    if jobs:
        judge.compiler()          # fail fast, and once, if there is no compiler
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [(l, p, pool.submit(check_problem, l, p)) for l, p in jobs]
            for l, p, f in futures:
                try:
                    e, w, s = f.result()
                except Exception as ex:                    # noqa: BLE001
                    e, w, s = [f"{l.id}.{p.id}: validator crashed: {type(ex).__name__}: {ex}"], [], ""
                report[l.id][0] += e
                report[l.id][1] += w
                if s:
                    report[l.id][2].append(s)

    for l in chosen:
        errs, warns, sums = report[l.id]
        qs = sum(1 for _, _, s in l.steps() if isinstance(s, (MCQ, Numeric, Short, Reflect)))
        head = (f"{l.id:7s} {l.title[:40]:40s} {len(l.parts)} parts, {len(l.steps())} steps, "
                f"{qs} questions, {len(l.problems)} problems, {len(l.cards)} cards")
        print(("ok      " if not errs else "FAIL    ") + head)
        if not quiet:
            for s in sums:
                print("          " + s)
        for w in warns:
            print("   warn  " + w)
        for e in errs:
            print("   ERROR " + e)
        total_errs += len(errs)
    print(f"\n{len(chosen)} lessons, {total_errs} errors")
    return 1 if total_errs else 0
