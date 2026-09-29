"""Discovers lesson modules in curriculum/ and exposes them in track order."""
from __future__ import annotations

import hashlib
import importlib
import pkgutil
from functools import lru_cache

import curriculum
from .schema import Card, Lesson, Problem

TRACK_NAMES = {"cpp": "C++ for contests", "algo": "algorithms, from the question up"}
TRACK_BLURBS = {
    "cpp": "The language, taught to someone who already programs: what C++ does differently "
           "from Python, and the habits contest code needs.",
    "algo": "Each idea is rebuilt from a concrete problem: the brute force, what it wastes, "
            "the insight, why it is correct, then the code.",
}
TRACK_ORDER = ["cpp", "algo"]


def card_id(lesson_id: str, card: Card) -> str:
    h = hashlib.sha1(card.q.strip().encode("utf-8")).hexdigest()[:8]
    return f"card:{lesson_id}:{h}"


def problem_id(lesson_id: str, p: Problem) -> str:
    return f"pb:{lesson_id}:{p.id}"


def ref(lesson_id: str, p: Problem) -> str:
    return f"{lesson_id}.{p.id}"


def _module_names() -> list[str]:
    return sorted(m.name for m in pkgutil.iter_modules(curriculum.__path__)
                  if not m.name.startswith("_"))


_LOAD_ERRORS: dict[str, str] = {}


@lru_cache(maxsize=1)
def load_all() -> list[Lesson]:
    """Import every curriculum module.  One that fails to import is skipped and
    recorded in `load_errors()`, so one broken file cannot take the tutor down."""
    lessons = []
    _LOAD_ERRORS.clear()
    for name in _module_names():
        try:
            mod = importlib.import_module(f"curriculum.{name}")
            lesson = getattr(mod, "LESSON", None)
            if lesson is None:
                raise ValueError("module does not define LESSON")
            if not isinstance(lesson, Lesson):
                raise TypeError("LESSON is not a Lesson instance")
        except Exception as e:  # noqa: BLE001 - any import-time failure
            _LOAD_ERRORS[name] = f"{type(e).__name__}: {e}"
            continue
        lesson._module = name  # type: ignore[attr-defined]
        lessons.append(lesson)
    lessons.sort(key=lambda l: (TRACK_ORDER.index(l.track) if l.track in TRACK_ORDER else 99,
                                l.order, l.id))
    return lessons


def load_errors() -> dict[str, str]:
    load_all()
    return dict(_LOAD_ERRORS)


def by_id() -> dict[str, Lesson]:
    return {l.id: l for l in load_all()}


def get(lesson_id: str) -> Lesson | None:
    return by_id().get(lesson_id)


def find_problem(r: str):
    """'algo03.aggressive_cows' or 'pb:algo03:aggressive_cows' -> (lesson, problem)."""
    r = (r or "").strip()
    if r.startswith("pb:"):
        r = r[3:].replace(":", ".", 1)
    if "." not in r:
        return None, None
    lid, pid = r.split(".", 1)
    lesson = get(lid)
    if lesson is None:
        return None, None
    return lesson, lesson.problem(pid)


def all_items(lessons: list[Lesson] | None = None) -> dict[str, tuple[str, Lesson, object]]:
    """item_id -> (kind, lesson, obj) for every card and problem."""
    out = {}
    for l in lessons or load_all():
        for c in l.cards:
            out[card_id(l.id, c)] = ("card", l, c)
        for p in l.problems:
            out[problem_id(l.id, p)] = ("problem", l, p)
    return out
