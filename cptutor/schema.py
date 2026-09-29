"""Data model for lessons: a Socratic dialogue, ICPC-style problems, and review cards.

Every lesson module in curriculum/ builds exactly one `Lesson` and assigns it to a
module-level name `LESSON`.  The loader discovers modules automatically.

A lesson is a dialogue.  `parts` is a list of `Part`s, each a list of steps:

    Say(text)                  the tutor talks: prose, code, tables
    MCQ(q, options, explain)   pick one; every wrong option says *why* it is wrong
    Numeric(q, answer, ...)    type a number ("4e10", "2*10^5" and "1,000" all parse)
    Short(q, accept, ...)      type a short answer (a word, a value, a program's output)
    Reflect(q, answer)         think, write your idea down, then compare with the tutor's
    Try(problem, note)         go and solve one of the lesson's problems now

The page shows everything up to the first unanswered question, so reading flows and
questions gate.  Answering (or asking to be shown) unfolds the next stretch.

Markup used in every text field (see markup.py):
  - blank line            paragraph break
  - ```  ...  ```         code block, verbatim (C++ is highlighted)
  - "- item"              bullet
  - "1. item"             numbered item
  - "# heading"           sub-heading
  - "| a | b |"           table row (first row is the header)
  - `code`, **bold**, *emphasis* inline

Problems are ICPC-shaped: read stdin, write stdout, judged by compiling the learner's
C++ and comparing against expected output (see judge.py).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

TRACKS = ("cpp", "algo")
DIFFICULTIES = ("easy", "medium", "hard")
CHECKERS = ("tokens", "tokens_ci", "lines", "float")   # or "float:1e-9", or a callable

DEFAULT_STARTER = r"""#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return 0;
}
"""


# --------------------------------------------------------------------- dialogue
@dataclass
class Say:
    text: str


@dataclass
class Opt:
    text: str
    correct: bool = False
    why: str = ""                      # shown when this option is picked; required


@dataclass
class MCQ:
    q: str
    options: list[Opt]
    explain: str = ""                  # shown once the right option is found (or revealed)
    hint: str = ""


@dataclass
class Numeric:
    q: str
    answer: float
    tol: float = 0.0                   # absolute tolerance
    rel: float = 0.0                   # relative tolerance; 0.5 accepts "the right ballpark"
    explain: str = ""
    hint: str = ""
    unit: str = ""                     # shown after the input box, e.g. "operations"


@dataclass
class Short:
    q: str
    accept: list[str]                  # compared after lowercasing and collapsing whitespace
    explain: str = ""
    hint: str = ""
    placeholder: str = ""


@dataclass
class Reflect:
    q: str
    answer: str                        # the tutor's answer, shown after the learner commits theirs


@dataclass
class Try:
    problem: str                       # id of a problem in this lesson
    note: str = ""


Step = Union[Say, MCQ, Numeric, Short, Reflect, Try]
QUESTION_TYPES = (MCQ, Numeric, Short, Reflect, Try)


@dataclass
class Part:
    title: str
    steps: list


# --------------------------------------------------------------------- problems
@dataclass
class Test:
    input: str
    output: Optional[str] = None       # None: whatever the reference solution prints
    note: str = ""                     # shown when a visible test fails (samples)
    brute: bool = True                 # False: too big for `brute`; skip the cross-check


@dataclass
class Gen:
    """A family of generated tests.  `fn(rng)` returns one input as a string; it is
    called `count` times with a deterministically seeded `random.Random`.  Expected
    output comes from the reference solution.  `large` tests are the ones a too-slow
    `naive` solution must time out on; the `brute` solution is only checked against
    tests that are not large."""
    name: str
    fn: Callable[[random.Random], str]
    count: int = 1
    large: bool = False
    brute: Optional[bool] = None       # cross-check against `brute`? default: when not large


Checker = Union[str, Callable[[str, str, str], Any]]


@dataclass
class Problem:
    id: str                            # unique inside the lesson, snake_case
    title: str
    statement: str                     # markup: the story and the task
    input: str                         # markup: input format and constraints
    output: str                        # markup: output format
    samples: list[Test]                # shown to the learner, outputs required
    solution: str                      # reference C++; must pass everything
    tests: list[Test] = field(default_factory=list)      # hidden, handwritten
    gens: list[Gen] = field(default_factory=list)        # hidden, generated
    brute: str = ""                    # slow, obviously-correct C++: cross-checks `solution`
    naive: str = ""                    # the tempting-but-too-slow C++: must TLE on a large test
    wrong: list[str] = field(default_factory=list)   # tempting wrong C++: each must be rejected
    check_input: Optional[Callable[[str], Any]] = None  # validates a test input: raise or return
                                                        # False / an error string when it breaks
                                                        # the stated constraints
    starter: str = DEFAULT_STARTER
    checker: Checker = "tokens"
    time_limit: float = 1.0            # seconds of CPU per test
    difficulty: str = "easy"
    hints: list[str] = field(default_factory=list)       # gentle to explicit
    editorial: str = ""                # markup: the idea and the proof, shown after AC
    source: str = ""                   # e.g. "CSES 1646 - Static Range Sum Queries"
    complexity: str = ""               # target, e.g. "O(n + q)"


# ------------------------------------------------------------------------ cards
@dataclass
class Card:
    q: str
    a: str


# ----------------------------------------------------------------------- lesson
@dataclass
class Lesson:
    id: str                            # "cpp03", "algo12"
    title: str
    track: str                         # one of TRACKS
    order: int                         # position inside the track
    summary: str                       # one line
    prereqs: list[str]
    parts: list[Part]
    problems: list[Problem] = field(default_factory=list)
    cards: list[Card] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def problem(self, pid: str) -> Optional[Problem]:
        for p in self.problems:
            if p.id == pid:
                return p
        return None

    def steps(self) -> list[tuple[int, int, Any]]:
        """Every step in reading order as (part index, step index, step)."""
        return [(i, j, s) for i, part in enumerate(self.parts) for j, s in enumerate(part.steps)]


def step_kind(step) -> str:
    return {Say: "say", MCQ: "mcq", Numeric: "numeric", Short: "short",
            Reflect: "reflect", Try: "try"}.get(type(step), "?")


def is_gate(step) -> bool:
    """A step the dialogue waits on."""
    return isinstance(step, QUESTION_TYPES)
