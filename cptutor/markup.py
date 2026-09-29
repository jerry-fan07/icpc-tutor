"""One tokenizer for the lesson markup described in schema.py.

`blocks()` turns markup into a flat list of typed blocks that the web front end
renders.  Inline markup (`code`, **bold**, *emphasis*) is left in the text for
the renderer.

Block shapes:
    {"type": "paragraph", "text": "one long line"}
    {"type": "heading",   "text": "Sub-heading"}
    {"type": "bullet",    "text": "item text"}
    {"type": "num",       "text": "item text", "n": 3}
    {"type": "code",      "text": "dedented\\nsource", "lang": "cpp" | "text" | ...}
    {"type": "table",     "rows": [["a", "b"], ["c", "d"]]}
"""
from __future__ import annotations

import re
import textwrap

TYPES = ("paragraph", "heading", "bullet", "num", "code", "table")
NUM_RE = re.compile(r"^(\d{1,2})[.)]\s+(.*)$")
RULE_RE = re.compile(r"^\|?[\s|:-]+\|?$")


def _cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def blocks(text: str) -> list[dict]:
    out: list[dict] = []
    para: list[str] = []
    code: list[str] = []
    lang = ""
    in_code = False
    open_item = False       # an indented line here continues the bullet/num above

    def emit(block: dict) -> None:
        nonlocal open_item
        open_item = block["type"] in ("bullet", "num")
        out.append(block)

    def flush_para() -> None:
        if para:
            emit({"type": "paragraph", "text": " ".join(para)})
            para.clear()

    for raw in (text or "").strip("\n").splitlines():
        line = raw.rstrip()
        s = line.strip()
        if s.startswith("```"):
            if in_code:
                emit({"type": "code", "lang": lang or "cpp",
                      "text": textwrap.dedent("\n".join(code)).strip("\n")})
                code, lang, in_code = [], "", False
            else:
                flush_para()
                lang = s[3:].strip().lower()
                in_code = True
            continue
        if in_code:
            code.append(line)
            continue
        if not s:
            flush_para()
            open_item = False
            continue
        if open_item and not para and line[:1].isspace() and not s.startswith(("- ", "|", "# ")) \
                and not NUM_RE.match(s):
            out[-1]["text"] += " " + s
            continue
        if s.startswith("# "):
            flush_para()
            emit({"type": "heading", "text": s[2:].strip()})
            continue
        if s.startswith("- "):
            flush_para()
            emit({"type": "bullet", "text": s[2:].strip()})
            continue
        m = NUM_RE.match(s)
        if m and not para:
            emit({"type": "num", "n": int(m.group(1)), "text": m.group(2).strip()})
            continue
        open_item = False
        if s.startswith("|"):
            if RULE_RE.match(s):
                continue
            if out and out[-1]["type"] == "table" and not para:
                out[-1]["rows"].append(_cells(s))
                continue
            flush_para()
            emit({"type": "table", "rows": [_cells(s)]})
            continue
        para.append(s)
    flush_para()
    if in_code:   # unbalanced fence: keep what we have rather than dropping it
        emit({"type": "code", "lang": lang or "cpp", "text": "\n".join(code), "unterminated": True})
    return out


def plain(text: str) -> str:
    """Markup stripped to one line of plain text, for labels."""
    text = re.sub(r"```.*?```", " ", text or "", flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*?([^*]+)\*\*?", r"\1", text)
    return " ".join(text.split())


def clip(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"
