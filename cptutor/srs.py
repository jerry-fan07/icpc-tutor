"""SM-2 spaced repetition (the algorithm behind SuperMemo / Anki's defaults).

Each item (a concept card or a coding exercise) carries:
  ease      multiplier applied to the interval after each successful review (min 1.3)
  interval  days until the next review
  reps      consecutive successful reviews
  lapses    number of failures overall
  due       ISO date (YYYY-MM-DD) of the next review

Quality scale (0-5):
  0-2  failure (again)        -> reps reset, interval 1 day, ease drops
  3    hard, recalled with effort
  4    good
  5    easy
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta

MIN_EASE = 1.3


@dataclass
class ItemState:
    ease: float = 2.5
    interval: int = 0
    reps: int = 0
    lapses: int = 0
    due: str = ""          # "" means new (never reviewed)
    last: str = ""         # ISO datetime of the last review
    reviews: int = 0
    correct: int = 0
    history: list = field(default_factory=list)   # last 20 qualities

    @classmethod
    def from_dict(cls, d: dict) -> "ItemState":
        s = cls()
        for k, v in d.items():
            if hasattr(s, k):
                setattr(s, k, v)
        return s

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def is_new(self) -> bool:
        return self.reviews == 0

    def due_date(self) -> date | None:
        return date.fromisoformat(self.due) if self.due else None

    def is_due(self, today: date | None = None) -> bool:
        today = today or date.today()
        d = self.due_date()
        return d is not None and d <= today


def sm2(state: ItemState, quality: int, today: date | None = None, now: datetime | None = None) -> ItemState:
    """Return the updated state after a review with the given quality (0-5)."""
    today = today or date.today()
    now = now or datetime.now()
    q = max(0, min(5, int(quality)))
    s = ItemState.from_dict(state.to_dict())
    s.reviews += 1
    s.history = (s.history + [q])[-20:]
    if q < 3:
        s.reps = 0
        s.lapses += 1
        s.interval = 1 if s.reviews > 1 else 0   # brand-new failure: see it again today
        # a failed card should still get harder, but never below the floor
        s.ease = max(MIN_EASE, s.ease - 0.2)
    else:
        s.correct += 1
        if s.reps == 0:
            s.interval = 1
        elif s.reps == 1:
            s.interval = 6
        else:
            s.interval = max(s.interval + 1, round(s.interval * s.ease))
        if q == 5 and s.reps >= 1:
            s.interval = round(s.interval * 1.15)  # small "easy" bonus, like Anki
        s.reps += 1
        s.ease = max(MIN_EASE, s.ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
    s.due = (today + timedelta(days=s.interval)).isoformat()
    s.last = now.replace(microsecond=0).isoformat()
    return s


def retention(state: ItemState) -> float:
    """Fraction of reviews answered correctly (1.0 for new items)."""
    return state.correct / state.reviews if state.reviews else 1.0


def forecast(states: dict[str, ItemState], days: int = 7, today: date | None = None) -> list[int]:
    """Number of items due on each of the next `days` days (index 0 = today, overdue included)."""
    today = today or date.today()
    out = [0] * days
    for s in states.values():
        d = s.due_date()
        if d is None:
            continue
        k = (d - today).days
        if k <= 0:
            out[0] += 1
        elif k < days:
            out[k] += 1
    return out
