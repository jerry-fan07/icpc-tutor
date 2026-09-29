"""Progress persistence: one JSON file, written atomically, plus the workspace of
.cpp files (one per problem) so the code can also be edited in any editor."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime

from .srs import ItemState

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("CPTUTOR_DATA") or os.path.join(ROOT, "data")
PROGRESS_PATH = os.path.join(DATA_DIR, "progress.json")
WORKSPACE_DIR = os.environ.get("CPTUTOR_WORKSPACE") or os.path.join(ROOT, "workspace")

DEFAULT = {
    "version": 1,
    "created": "",
    # lesson id -> {"status": "new"|"started"|"learned", "answers": {step: {...}}, "completed": iso}
    "lessons": {},
    # "lesson.problem" -> {"solved": iso, "submits": n, "wrong": n, "gave_up": bool, "best_ms": n}
    "problems": {},
    "items": {},            # item id -> ItemState dict (cards and problems)
    "attempts": [],         # SRS log: {"item", "ts", "q", ...}              (capped)
    "submissions": [],      # {"ref", "ts", "verdict", "failed", "ms"}         (capped)
    "settings": {"daily_target": 45},
    "streak": {"last_day": "", "count": 0, "best": 0},
    "sessions": {},         # iso day -> seconds spent on a lesson/problem/review screen
    "contests": [],         # virtual contests: {"id", "started", "minutes", "problems", "subs", ...}
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


class Store:
    def __init__(self, path: str = PROGRESS_PATH):
        self.path = path
        self.data = json.loads(json.dumps(DEFAULT))
        self.data["created"] = now_iso()
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    loaded = json.load(f)
                for k, v in loaded.items():
                    self.data[k] = v
                for k, v in DEFAULT.items():
                    self.data.setdefault(k, json.loads(json.dumps(v)))
                for k, v in DEFAULT["settings"].items():
                    self.data["settings"].setdefault(k, v)
            except (json.JSONDecodeError, OSError):
                try:                    # keep the damaged file, start fresh
                    os.replace(path, path + ".corrupt")
                except OSError:
                    pass
        self._items = {k: ItemState.from_dict(v) for k, v in self.data["items"].items()}

    # ---- persistence --------------------------------------------------------
    def save(self) -> None:
        self.data["items"] = {k: v.to_dict() for k, v in self._items.items()}
        self.data["attempts"] = self.data["attempts"][-5000:]
        self.data["submissions"] = self.data["submissions"][-3000:]
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".progress-", suffix=".json", dir=os.path.dirname(self.path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=1, sort_keys=True)
            os.replace(tmp, self.path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ---- SRS items ----------------------------------------------------------
    @property
    def items(self) -> dict[str, ItemState]:
        return self._items

    def item(self, item_id: str) -> ItemState:
        if item_id not in self._items:
            self._items[item_id] = ItemState()
        return self._items[item_id]

    def set_item(self, item_id: str, state: ItemState) -> None:
        self._items[item_id] = state

    def has_item(self, item_id: str) -> bool:
        return item_id in self._items

    def record_attempt(self, item_id: str, q: int, **extra) -> None:
        self.data["attempts"].append({"item": item_id, "ts": now_iso(), "q": q, **extra})
        self.touch()

    # ---- lessons ------------------------------------------------------------
    def lesson_state(self, lesson_id: str) -> dict:
        st = self.data["lessons"].setdefault(lesson_id, {"status": "new", "completed": ""})
        st.setdefault("answers", {})
        return st

    def lesson_status(self, lesson_id: str) -> str:
        return self.data["lessons"].get(lesson_id, {}).get("status", "new")

    def answers(self, lesson_id: str) -> dict:
        return self.data["lessons"].get(lesson_id, {}).get("answers", {})

    def set_status(self, lesson_id: str, status: str) -> None:
        st = self.lesson_state(lesson_id)
        st["status"] = status
        if status == "learned" and not st.get("completed"):
            st["completed"] = date.today().isoformat()
        self.touch()

    # ---- problems -----------------------------------------------------------
    def problem_state(self, ref: str) -> dict:
        return self.data["problems"].setdefault(
            ref, {"solved": "", "submits": 0, "wrong": 0, "gave_up": False, "best_ms": None})

    def peek_problem(self, ref: str) -> dict:
        return self.data["problems"].get(ref) or {}

    def solved(self, ref: str) -> bool:
        return bool(self.peek_problem(ref).get("solved"))

    # ---- settings / streak / time ------------------------------------------
    def setting(self, key: str, default=None):
        return self.data["settings"].get(key, default)

    def touch(self) -> None:
        """Anything done today keeps the streak alive."""
        today = date.today()
        s = self.data["streak"]
        last = s.get("last_day") or ""
        if last == today.isoformat():
            return
        if last and (today - date.fromisoformat(last)).days == 1:
            s["count"] = s.get("count", 0) + 1
        else:
            s["count"] = 1
        s["last_day"] = today.isoformat()
        s["best"] = max(s.get("best", 0), s["count"])

    def streak(self) -> int:
        s = self.data["streak"]
        last = s.get("last_day") or ""
        if not last:
            return 0
        gap = (date.today() - date.fromisoformat(last)).days
        return s.get("count", 0) if gap <= 1 else 0

    def add_session_seconds(self, seconds: int, day: str | None = None) -> int:
        day = day or date.today().isoformat()
        sessions = self.data.setdefault("sessions", {})
        sessions[day] = int(sessions.get(day, 0)) + max(0, min(120, int(seconds)))
        return sessions[day]

    def session_seconds(self, day: str | None = None) -> int:
        return int(self.data.get("sessions", {}).get(day or date.today().isoformat(), 0))

    def total_session_seconds(self) -> int:
        return sum(int(v) for v in self.data.get("sessions", {}).values())


# ------------------------------------------------------------------- workspace
def code_path(lesson_id: str, problem_id: str) -> str:
    return os.path.join(WORKSPACE_DIR, lesson_id, f"{problem_id}.cpp")


def read_code(lesson_id: str, problem_id: str, starter: str) -> str:
    p = code_path(lesson_id, problem_id)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return starter


def save_code(lesson_id: str, problem_id: str, code: str) -> str:
    p = code_path(lesson_id, problem_id)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(code)
    os.replace(tmp, p)
    return p


def accepted_path(lesson_id: str, problem_id: str) -> str:
    return os.path.join(WORKSPACE_DIR, lesson_id, f"{problem_id}.accepted.cpp")


def save_accepted(lesson_id: str, problem_id: str, code: str) -> None:
    """The last accepted version, kept apart from the file being edited, for the notebook."""
    p = accepted_path(lesson_id, problem_id)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(code)


def read_accepted(lesson_id: str, problem_id: str) -> str | None:
    p = accepted_path(lesson_id, problem_id)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return f.read()


def reset_code(lesson_id: str, problem_id: str) -> None:
    try:
        os.unlink(code_path(lesson_id, problem_id))
    except OSError:
        pass
