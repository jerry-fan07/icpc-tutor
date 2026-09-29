"""Everything the web front end asks for.  One learner, one progress file.

Every decision that touches the schedule -- SM-2 quality, streaks, when a lesson counts
as learned, how far a dialogue has unfolded -- is made here, so the page only renders.

The dialogue is served progressively: a lesson view contains every step up to and
including the first unanswered question, and nothing after it.  Answering unfolds the
next stretch.  That keeps the Socratic order honest -- the explanation that follows a
question is not on the page until the question has been tried.
"""
from __future__ import annotations

import collections
import random
import threading
from datetime import date, datetime, timedelta

from . import dialogue, judge, loader, store as storemod
from .markup import blocks, clip, plain
from .schema import MCQ, Lesson, Numeric, Problem, Reflect, Say, Short, Try, is_gate, step_kind
from .srs import ItemState, forecast, sm2
from .store import Store

QUALITY_CARD = {1: 1, 2: 3, 3: 4, 4: 5}      # again / hard / good / easy
QUALITY_PROBLEM = {1: 3, 2: 4, 3: 5}         # hard / good / easy
FORECAST_DAYS = 14
ACTIVITY_WEEKS = 12
MIN_PER = {"say": 0.8, "mcq": 0.8, "numeric": 1.0, "short": 1.0, "reflect": 2.0, "try": 0.0}
PROBLEM_MIN = {"easy": 10, "medium": 20, "hard": 35}
CONTEST_PENALTY = 20


class Api:
    def __init__(self, path: str | None = None):
        self.store = Store(path or storemod.PROGRESS_PATH)
        self.lessons = loader.load_all()
        self.by_id = {l.id: l for l in self.lessons}
        self.items = loader.all_items(self.lessons)
        self.lock = threading.RLock()

    # ================================================================ lookup
    def lesson(self, lesson_id: str) -> Lesson:
        l = self.by_id.get((lesson_id or "").strip())
        if l is None:
            raise KeyError(f"no lesson {lesson_id!r}")
        return l

    def problem(self, ref: str) -> tuple[Lesson, Problem]:
        l, p = loader.find_problem(ref)
        if p is None:
            raise KeyError(f"no problem {ref!r}")
        return l, p

    # ============================================================== dialogue
    def _done(self, l: Lesson, k: int, step, answers: dict) -> bool:
        if isinstance(step, Try):
            return bool(answers.get(str(k), {}).get("done")) or self.store.solved(f"{l.id}.{step.problem}")
        return bool(answers.get(str(k), {}).get("done"))

    def reached(self, l: Lesson) -> int:
        """Flat index of the first gate not yet done; len(steps) when finished."""
        answers = self.store.answers(l.id)
        for k, (_, _, s) in enumerate(l.steps()):
            if is_gate(s) and not self._done(l, k, s, answers):
                return k
        return len(l.steps())

    def dialogue_progress(self, l: Lesson) -> tuple[int, int]:
        """(gates done, gates total)."""
        answers = self.store.answers(l.id)
        gates = [(k, s) for k, (_, _, s) in enumerate(l.steps()) if is_gate(s)]
        return sum(1 for k, s in gates if self._done(l, k, s, answers)), len(gates)

    def step_view(self, l: Lesson, k: int) -> dict:
        pi, si, s = l.steps()[k]
        kind = step_kind(s)
        v = {"k": k, "part": pi, "kind": kind}
        if isinstance(s, Say):
            v["blocks"] = blocks(s.text)
            return v
        a = self.store.answers(l.id).get(str(k), {})
        done = self._done(l, k, s, self.store.answers(l.id))
        v["done"] = done
        if isinstance(s, Try):
            p = l.problem(s.problem)
            r = f"{l.id}.{s.problem}"
            ps = self.store.peek_problem(r)
            v.update({"ref": r, "title": p.title if p else s.problem,
                      "difficulty": p.difficulty if p else "", "note": blocks(s.note),
                      "solved": self.store.solved(r), "skipped": bool(a.get("skipped")),
                      "submits": ps.get("submits", 0)})
            return v
        v["q"] = blocks(s.q)
        v["tries"] = a.get("tries", 0)
        if isinstance(s, MCQ):
            v["options"] = [o.text for o in s.options]
            picked = a.get("picked", [])
            v["picked"] = [{"i": i, "correct": bool(s.options[i].correct),
                            "why": blocks(s.options[i].why)} for i in picked if 0 <= i < len(s.options)]
        if isinstance(s, Numeric):
            v["unit"] = s.unit
        if isinstance(s, Short):
            v["placeholder"] = s.placeholder
        if isinstance(s, (MCQ, Numeric, Short)):
            v["has_hint"] = bool(s.hint.strip())
            if a.get("hinted") and s.hint:
                v["hint"] = blocks(s.hint)
        if isinstance(s, (Numeric, Short)):
            v["responses"] = [{"text": r["text"], "correct": r["correct"],
                               "feedback": blocks(r.get("feedback", ""))}
                              for r in a.get("responses", [])]
        if done:
            v["correct"] = bool(a.get("correct"))
            v["revealed"] = bool(a.get("revealed"))
            if isinstance(s, Reflect):
                v["mine"] = a.get("text", "")
                v["answer"] = blocks(s.answer)
                v["self"] = a.get("self", "")
            else:
                if a.get("revealed"):
                    v["answer"] = blocks(dialogue.answer_text(s))
                if isinstance(s, MCQ):
                    v["right"] = [i for i, o in enumerate(s.options) if o.correct]
                v["explain"] = blocks(getattr(s, "explain", ""))
        return v

    def _unfold(self, l: Lesson, start: int) -> tuple[list[dict], int]:
        """Views for steps start..reached (inclusive of the new gate)."""
        r = self.reached(l)
        end = min(r, len(l.steps()) - 1)
        return [self.step_view(l, k) for k in range(start, end + 1)], r

    def _touch_lesson(self, l: Lesson) -> None:
        if self.store.lesson_status(l.id) == "new":
            self.store.set_status(l.id, "started")

    def maybe_learned(self, l: Lesson) -> bool:
        """A lesson is learned once the dialogue is finished and every problem is either
        solved or given up on (editorial read)."""
        if self.store.lesson_status(l.id) == "learned":
            return False
        if self.reached(l) < len(l.steps()):
            return False
        for p in l.problems:
            ps = self.store.peek_problem(f"{l.id}.{p.id}")
            if not (ps.get("solved") or ps.get("gave_up")):
                return False
        self.store.set_status(l.id, "learned")
        return True

    # ============================================================== summaries
    def lesson_row(self, l: Lesson) -> dict:
        done, total = self.dialogue_progress(l)
        solved = sum(1 for p in l.problems if self.store.solved(f"{l.id}.{p.id}"))
        due = sum(1 for iid in ([loader.card_id(l.id, c) for c in l.cards] +
                                [loader.problem_id(l.id, p) for p in l.problems])
                  if (st := self.store.items.get(iid)) and st.is_due())
        steps = l.steps()
        minutes = sum(MIN_PER[step_kind(s)] for _, _, s in steps) + \
            sum(PROBLEM_MIN.get(p.difficulty, 15) for p in l.problems)
        return {"id": l.id, "title": l.title, "track": l.track, "summary": l.summary,
                "status": self.store.lesson_status(l.id), "parts": len(l.parts),
                "questions": total, "answered": done, "problems": len(l.problems),
                "solved": solved, "cards": len(l.cards), "due": due,
                "minutes": round(minutes / 5) * 5,
                "prereqs": list(l.prereqs),
                "missing": [p for p in l.prereqs if self.store.lesson_status(p) != "learned"],
                "balloons": [{"ref": f"{l.id}.{p.id}", "solved": self.store.solved(f"{l.id}.{p.id}"),
                              "color": balloon(l, p)} for p in l.problems]}

    def problem_row(self, l: Lesson, p: Problem) -> dict:
        r = f"{l.id}.{p.id}"
        ps = self.store.peek_problem(r)
        st = self.store.items.get(loader.problem_id(l.id, p))
        return {"ref": r, "lesson": l.id, "lesson_title": l.title, "id": p.id, "title": p.title,
                "difficulty": p.difficulty, "source": p.source, "color": balloon(l, p),
                "solved": bool(ps.get("solved")), "submits": ps.get("submits", 0),
                "gave_up": bool(ps.get("gave_up")),
                "due": bool(st and st.is_due()), "next_review": st.due if st else ""}

    def current_lesson(self) -> Lesson | None:
        for l in self.lessons:
            if self.store.lesson_status(l.id) == "started":
                return l
        return self.next_lesson()

    def next_lesson(self) -> Lesson | None:
        for l in self.lessons:
            if self.store.lesson_status(l.id) == "learned":
                continue
            if all(self.store.lesson_status(p) == "learned" for p in l.prereqs):
                return l
        for l in self.lessons:
            if self.store.lesson_status(l.id) != "learned":
                return l
        return None

    def due_queue(self) -> list[dict]:
        today = date.today()
        order = {l.id: i for i, l in enumerate(self.lessons)}
        rows = []
        for iid, st in self.store.items.items():
            if iid not in self.items or not st.is_due(today):
                continue
            kind, l, obj = self.items[iid]
            rows.append((st.due, order[l.id], iid, kind, l, obj))
        rows.sort(key=lambda t: (t[0], t[1], t[2]))
        out = []
        for _, _, iid, kind, l, obj in rows:
            if kind == "card":
                out.append({"kind": "card", "item": iid, "lesson": l.id, "lesson_title": l.title,
                            "card": self.card_view(l, obj)})
            else:
                out.append({"kind": "problem", "item": iid, "lesson": l.id,
                            "lesson_title": l.title, "problem": self.problem_row(l, obj)})
        return out

    def card_view(self, l: Lesson, c) -> dict:
        iid = loader.card_id(l.id, c)
        st = self.store.items.get(iid)
        return {"item": iid, "lesson": l.id, "q": blocks(c.q), "a": blocks(c.a),
                "seen": st is not None, "due": st.due if st else "",
                "is_due": bool(st and st.is_due()),
                "intervals": [sm2(st or ItemState(), QUALITY_CARD[r]).interval for r in (1, 2, 3, 4)]}

    # ================================================================ grading
    def grade(self, item_id: str, q: int, **extra) -> ItemState:
        st = sm2(self.store.item(item_id), q)
        self.store.set_item(item_id, st)
        self.store.record_attempt(item_id, q, **extra)
        return st

    # ==================================================================== ops
    def op_ping(self, a: dict) -> dict:
        return {"lessons": len(self.lessons)}

    def op_env(self, a: dict) -> dict:
        try:
            c = judge.compiler()
            comp = {"ok": True, "version": c["version"], "path": c["path"], "gcc": c["gcc"],
                    "flags": " ".join(judge.flags())}
        except judge.JudgeError as e:
            comp = {"ok": False, "error": str(e)}
        return {"compiler": comp, "progress": self.store.path,
                "workspace": storemod.WORKSPACE_DIR,
                "load_errors": loader.load_errors()}

    def op_lessons(self, a: dict) -> dict:
        tracks = []
        for t in loader.TRACK_ORDER:
            rows = [self.lesson_row(l) for l in self.lessons if l.track == t]
            if rows:
                tracks.append({"track": t, "name": loader.TRACK_NAMES[t],
                               "blurb": loader.TRACK_BLURBS[t], "lessons": rows})
        return {"tracks": tracks}

    def op_lesson(self, a: dict) -> dict:
        l = self.lesson(a.get("id", ""))
        steps = l.steps()
        r = self.reached(l)
        visible = min(r, len(steps) - 1)
        parts = []
        for i, part in enumerate(l.parts):
            ks = [k for k, (pi, _, _) in enumerate(steps) if pi == i]
            gates = [k for k in ks if is_gate(steps[k][2])]
            parts.append({"title": part.title, "first": ks[0] if ks else 0,
                          "gates": len(gates),
                          "done": sum(1 for k in gates if k < r) if r < len(steps) else len(gates),
                          "open": bool(ks) and ks[0] <= visible})
        i = self.lessons.index(l)
        nxt = next((o for o in self.lessons[i + 1:] if o.track == l.track), None) or \
            (self.lessons[i + 1] if i + 1 < len(self.lessons) else None)
        return {
            "lesson": self.lesson_row(l),
            "parts": parts,
            "steps": [self.step_view(l, k) for k in range(0, visible + 1)],
            "reached": r,
            "total": len(steps),
            "finished": r >= len(steps),
            "problems": [self.problem_row(l, p) | {"statement": clip(plain(p.statement), 140)}
                         for p in l.problems],
            "cards": [self.card_view(l, c) for c in l.cards],
            "prereqs": [{"id": p, "title": self.by_id[p].title if p in self.by_id else p,
                         "done": self.store.lesson_status(p) == "learned"} for p in l.prereqs],
            "unlocks": [{"id": o.id, "title": o.title} for o in self.lessons if l.id in o.prereqs][:4],
            "next": {"id": nxt.id, "title": nxt.title} if nxt else None,
            "tags": list(l.tags),
        }

    def _gate(self, l: Lesson, k: int):
        steps = l.steps()
        if not 0 <= k < len(steps):
            raise IndexError(f"{l.id} has no step {k}")
        s = steps[k][2]
        if not is_gate(s):
            raise ValueError(f"step {k} of {l.id} takes no answer")
        if k > self.reached(l):
            raise ValueError("answer the questions before this one first")
        return s

    def _after(self, l: Lesson, k: int, extra: dict | None = None) -> dict:
        unfolded, r = self._unfold(l, k + 1)
        learned = self.maybe_learned(l)
        self.store.save()
        out = {"step": self.step_view(l, k), "unfolded": unfolded, "reached": r,
               "finished": r >= len(l.steps()), "learned": learned,
               "progress": dict(zip(("done", "total"), self.dialogue_progress(l)))}
        out.update(extra or {})
        return out

    def op_answer(self, a: dict) -> dict:
        l = self.lesson(a.get("lesson", ""))
        k = int(a.get("k", -1))
        s = self._gate(l, k)
        if not isinstance(s, (MCQ, Numeric, Short)):
            raise ValueError("use reflect/try ops for this step")
        ans = self.store.lesson_state(l.id)["answers"].setdefault(str(k), {})
        if ans.get("done"):
            return self._after(l, k, {"result": {"correct": ans.get("correct", False),
                                                 "feedback": [], "repeat": True}})
        res = dialogue.grade(s, a.get("response"))
        if res.get("invalid"):
            return {"result": {"correct": False, "invalid": True, "feedback": blocks(res["feedback"])},
                    "step": self.step_view(l, k), "unfolded": [], "reached": self.reached(l)}
        self._touch_lesson(l)
        ans["tries"] = ans.get("tries", 0) + 1
        if isinstance(s, MCQ):
            picked = ans.setdefault("picked", [])
            if res["choice"] not in picked:
                picked.append(res["choice"])
        else:
            ans.setdefault("responses", []).append(
                {"text": str(a.get("response", ""))[:200], "correct": res["correct"],
                 "feedback": res.get("feedback", "")})
            ans["responses"] = ans["responses"][-6:]
        if res["correct"]:
            ans["done"] = True
            ans["correct"] = ans["tries"] == 1
        self.store.touch()
        return self._after(l, k, {"result": {"correct": res["correct"],
                                             "feedback": blocks(res.get("feedback", ""))}})

    def op_hint_step(self, a: dict) -> dict:
        l = self.lesson(a.get("lesson", ""))
        k = int(a.get("k", -1))
        s = self._gate(l, k)
        ans = self.store.lesson_state(l.id)["answers"].setdefault(str(k), {})
        ans["hinted"] = True
        self.store.save()
        return {"step": self.step_view(l, k)}

    def op_reveal(self, a: dict) -> dict:
        l = self.lesson(a.get("lesson", ""))
        k = int(a.get("k", -1))
        s = self._gate(l, k)
        if isinstance(s, (Reflect, Try)):
            raise ValueError("nothing to reveal on this step")
        ans = self.store.lesson_state(l.id)["answers"].setdefault(str(k), {})
        self._touch_lesson(l)
        if not ans.get("done"):
            ans.update({"done": True, "revealed": True, "correct": False})
            ans["tries"] = ans.get("tries", 0)
        return self._after(l, k)

    def op_reflect(self, a: dict) -> dict:
        l = self.lesson(a.get("lesson", ""))
        k = int(a.get("k", -1))
        s = self._gate(l, k)
        if not isinstance(s, Reflect):
            raise ValueError("not a reflect step")
        ans = self.store.lesson_state(l.id)["answers"].setdefault(str(k), {})
        self._touch_lesson(l)
        if not ans.get("done"):
            ans.update({"done": True, "text": str(a.get("text", ""))[:4000], "correct": True})
        self.store.touch()
        return self._after(l, k)

    def op_reflect_self(self, a: dict) -> dict:
        """How the learner's own answer compared: got | partly | missed.  Recorded only."""
        l = self.lesson(a.get("lesson", ""))
        k = int(a.get("k", -1))
        ans = self.store.lesson_state(l.id)["answers"].setdefault(str(k), {})
        verdict = a.get("self", "")
        if verdict in ("got", "partly", "missed"):
            ans["self"] = verdict
            ans["correct"] = verdict == "got"
        self.store.save()
        return {"step": self.step_view(l, k)}

    def op_try_skip(self, a: dict) -> dict:
        l = self.lesson(a.get("lesson", ""))
        k = int(a.get("k", -1))
        s = self._gate(l, k)
        if not isinstance(s, Try):
            raise ValueError("not a try step")
        ans = self.store.lesson_state(l.id)["answers"].setdefault(str(k), {})
        self._touch_lesson(l)
        ans.update({"done": True, "skipped": True})
        return self._after(l, k)

    def op_lesson_reset(self, a: dict) -> dict:
        l = self.lesson(a.get("id", ""))
        st = self.store.lesson_state(l.id)
        st["answers"] = {}
        if st.get("status") == "learned":
            st["status"] = "started"
        self.store.save()
        return {"ok": True}

    # ---------------------------------------------------------------- problems
    def op_problem(self, a: dict) -> dict:
        l, p = self.problem(a.get("ref", ""))
        r = f"{l.id}.{p.id}"
        if a.get("contest"):
            return self.contest_problem(l, p)
        ps = self.store.peek_problem(r)
        row = self.problem_row(l, p)
        open_editorial = bool(ps.get("solved") or ps.get("gave_up"))
        subs = [s for s in self.store.data["submissions"] if s.get("ref") == r][-12:][::-1]
        siblings = [{"ref": f"{l.id}.{q.id}", "title": q.title, "color": balloon(l, q),
                     "solved": self.store.solved(f"{l.id}.{q.id}")} for q in l.problems]
        row.update({
            "statement": blocks(p.statement), "input": blocks(p.input), "output": blocks(p.output),
            "samples": [{"input": t.input, "output": t.output, "note": blocks(t.note)}
                        for t in p.samples],
            "time_limit": p.time_limit, "complexity": p.complexity,
            "hints_total": len(p.hints),
            "hints": [blocks(h) for h in p.hints[:int(ps.get("hints", 0))]],
            "editorial": blocks(p.editorial) if open_editorial else None,
            "solution": p.solution.strip("\n") if open_editorial else None,
            "code": storemod.read_code(l.id, p.id, p.starter),
            "starter": p.starter,
            "path": storemod.code_path(l.id, p.id),
            "submissions": subs,
            "siblings": siblings,
            "wrong": ps.get("wrong", 0),
            "graded": bool(ps.get("graded")),
            "srs": self._problem_srs(l, p),
        })
        return row

    def _problem_srs(self, l: Lesson, p: Problem) -> dict:
        st = self.store.items.get(loader.problem_id(l.id, p))
        return {"scheduled": st is not None, "due": st.due if st else "",
                "is_due": bool(st and st.is_due())}

    def op_hint(self, a: dict) -> dict:
        l, p = self.problem(a.get("ref", ""))
        ps = self.store.problem_state(f"{l.id}.{p.id}")
        n = min(len(p.hints), int(ps.get("hints", 0)) + 1)
        ps["hints"] = n
        self._touch_lesson(l)
        self.store.save()
        return {"hints": [blocks(h) for h in p.hints[:n]], "total": len(p.hints)}

    def op_editorial(self, a: dict) -> dict:
        l, p = self.problem(a.get("ref", ""))
        ps = self.store.problem_state(f"{l.id}.{p.id}")
        if not ps.get("solved"):
            ps["gave_up"] = True
        self._touch_lesson(l)
        learned = self.maybe_learned(l)
        self.store.save()
        return {"editorial": blocks(p.editorial), "solution": p.solution.strip("\n"),
                "learned": learned}

    def op_code_save(self, a: dict) -> dict:
        l, p = self.problem(a.get("ref", ""))
        return {"path": storemod.save_code(l.id, p.id, str(a.get("code", "")))}

    def op_code_reset(self, a: dict) -> dict:
        l, p = self.problem(a.get("ref", ""))
        storemod.reset_code(l.id, p.id)
        return {"code": p.starter}

    def judge_run(self, a: dict) -> dict:
        """Compile and judge.  Runs outside the store lock; `record_run` books it."""
        l, p = self.problem(a.get("ref", ""))
        code = str(a.get("code", ""))
        storemod.save_code(l.id, p.id, code)
        mode = "samples" if a.get("mode") == "samples" else "submit"
        return judge.judge(l, p, code, mode)

    def record_run(self, a: dict, res: dict) -> dict:
        l, p = self.problem(a.get("ref", ""))
        r = f"{l.id}.{p.id}"
        if a.get("mode") == "samples":
            return {"result": res}
        ps = self.store.problem_state(r)
        first_ac = False
        ps["submits"] = ps.get("submits", 0) + 1
        if res["verdict"] == "AC":
            if not ps.get("solved"):
                ps["solved"] = storemod.now_iso()
                first_ac = True
            storemod.save_accepted(l.id, p.id, str(a.get("code", "")))
            best = ps.get("best_ms")
            ps["best_ms"] = res["max_ms"] if best is None else min(best, res["max_ms"])
        elif not ps.get("solved"):
            ps["wrong"] = ps.get("wrong", 0) + 1
        self.store.data["submissions"].append({
            "ref": r, "ts": storemod.now_iso(), "verdict": res["verdict"],
            "failed": res.get("failed", ""), "ms": res.get("max_ms", 0),
            "passed": res.get("passed", 0), "total": res.get("total", 0)})
        self._touch_lesson(l)
        self.store.touch()
        learned = self.maybe_learned(l)
        contest = None
        if a.get("contest"):
            c = self._contest()
            if c is not None and r in c["problems"]:
                self._contest_submit(c, r, res["verdict"])
                contest = self.contest_view(c)
        self.store.save()
        return {"result": res, "first_ac": first_ac, "learned": learned,
                "state": self.problem_row(l, p), "srs": self._problem_srs(l, p),
                "reviewing": bool(self.store.items.get(loader.problem_id(l.id, p))),
                "contest": contest}

    @staticmethod
    def contest_filter(res: dict) -> dict:
        """What a contest judge tells you about hidden tests: the verdict, nothing more."""
        for c in res.get("cases", []):
            if c.get("kind") != "sample":
                for k in ("input", "expected", "got", "stderr", "message", "gen", "note"):
                    c.pop(k, None)
                c["hidden"] = True
        return res

    def op_custom(self, a: dict) -> dict:
        l, p = self.problem(a.get("ref", ""))
        code = str(a.get("code", ""))
        storemod.save_code(l.id, p.id, code)
        if a.get("contest") and self._contest_running():
            return judge.run_custom(None, code, str(a.get("input", "")))   # no oracle in a contest
        return judge.run_custom(p, code, str(a.get("input", "")))

    def op_playground(self, a: dict) -> dict:
        return judge.run_custom(None, str(a.get("code", "")), str(a.get("input", "")))

    def op_grade_problem(self, a: dict) -> dict:
        """After an AC: how did it feel?  Schedules the next re-solve.  Mirrors the
        leetcode tutor's penalties: hints cap the grade at good, many wrong
        submissions at hard, reading the editorial first means again."""
        l, p = self.problem(a.get("ref", ""))
        r = f"{l.id}.{p.id}"
        ps = self.store.problem_state(r)
        iid = loader.problem_id(l.id, p)
        if a.get("skip"):
            q = 1
        elif ps.get("gave_up"):
            q = 2
        else:
            q = QUALITY_PROBLEM.get(int(a.get("feel", 2)), 4)
            if int(ps.get("hints", 0)) and q > 4:
                q = 4
            if int(a.get("wrong", ps.get("wrong", 0))) >= 3 and q > 3:
                q = 3
        st = self.grade(iid, q, passed=not a.get("skip"), wrong=int(a.get("wrong", 0)),
                        hints=int(ps.get("hints", 0)), solution=bool(ps.get("gave_up")))
        ps["graded"] = True
        # a re-solve starts clean: hints, rejections and giving up count against one attempt
        ps["hints"] = 0
        ps["wrong"] = 0
        ps["gave_up"] = False
        self.store.save()
        return {"quality": q, "interval": st.interval, "due": st.due}

    def op_grade_card(self, a: dict) -> dict:
        l = self.lesson(a.get("lesson", ""))
        item = a.get("item", "")
        card = next((c for c in l.cards if loader.card_id(l.id, c) == item), None)
        if card is None:
            raise KeyError(f"no card {item!r} in {l.id}")
        q = QUALITY_CARD.get(int(a.get("rating", 3)), 4)
        st = self.grade(item, q)
        self.store.save()
        return {"quality": q, "interval": st.interval, "due": st.due}

    def op_due(self, a: dict) -> dict:
        return {"queue": self.due_queue()}

    def op_problems(self, a: dict) -> dict:
        groups = []
        for t in loader.TRACK_ORDER:
            ls = [l for l in self.lessons if l.track == t]
            if ls:
                groups.append({"track": t, "name": loader.TRACK_NAMES[t],
                               "lessons": [{"id": l.id, "title": l.title,
                                            "status": self.store.lesson_status(l.id),
                                            "problems": [self.problem_row(l, p) for p in l.problems]}
                                           for l in ls]})
        return {"groups": groups}

    def op_notebook(self, a: dict) -> dict:
        """The team reference document you are building: for every problem you have
        solved, your accepted code and the reference solution, lesson by lesson."""
        out = []
        for l in self.lessons:
            rows = []
            for p in l.problems:
                if not self.store.solved(f"{l.id}.{p.id}"):
                    continue
                rows.append({"ref": f"{l.id}.{p.id}", "title": p.title, "color": balloon(l, p),
                             "complexity": p.complexity, "source": p.source,
                             "mine": storemod.read_accepted(l.id, p.id),
                             "reference": p.solution.strip("\n")})
            if rows:
                out.append({"id": l.id, "title": l.title, "track": l.track, "problems": rows})
        return {"lessons": out}

    def op_heartbeat(self, a: dict) -> dict:
        total = self.store.add_session_seconds(int(a.get("seconds", 60)))
        self.store.save()
        return {"minutes": round(total / 60)}

    # --------------------------------------------------------------- contest
    # A virtual contest: a handful of problems in random order, labelled A, B, C...,
    # no hints, no editorials, no lesson names (recognising the technique is the skill),
    # a clock, and ICPC scoring: problems solved, then penalty = the minute of each
    # accepted submission + 20 minutes per rejected one before it on that problem.
    # Compilation errors cost nothing, as at most ICPC contests.
    def _contests(self) -> list:
        return self.store.data.setdefault("contests", [])

    @staticmethod
    def _elapsed(c: dict) -> float:
        try:
            return (datetime.now() - datetime.fromisoformat(c["started"])).total_seconds()
        except (KeyError, ValueError):
            return 0.0

    def _contest(self) -> dict | None:
        """The running contest; one past its end is closed on the way."""
        for c in reversed(self._contests()):
            if c.get("finished"):
                continue
            if self._elapsed(c) >= c["minutes"] * 60:
                c["finished"] = True
                c["ended"] = storemod.now_iso()
                self.store.save()
                continue
            return c
        return None

    def _contest_running(self) -> bool:
        """Read-only check, safe outside the store lock."""
        return any(not c.get("finished") and self._elapsed(c) < c["minutes"] * 60
                   for c in list(self.store.data.get("contests", [])))

    def _contest_submit(self, c: dict, ref: str, verdict: str) -> None:
        minute = int(self._elapsed(c) // 60)
        if any(s["ref"] == ref and s["verdict"] == "AC" for s in c["subs"]):
            return                                   # already solved: nothing changes
        c["subs"].append({"ref": ref, "minute": minute, "verdict": verdict, "ts": storemod.now_iso()})

    def contest_view(self, c: dict) -> dict:
        rows = []
        for i, ref in enumerate(c["problems"]):
            l, p = loader.find_problem(ref)
            if p is None:
                continue
            subs = [s for s in c["subs"] if s["ref"] == ref]
            ac = next((s for s in subs if s["verdict"] == "AC"), None)
            before = subs[:subs.index(ac)] if ac else subs
            wrong = sum(1 for s in before if s["verdict"] != "CE")
            row = {"letter": chr(65 + i), "ref": ref, "title": p.title, "color": balloon(l, p),
                   "solved": ac is not None, "minute": ac["minute"] if ac else None,
                   "wrong": wrong, "tries": len(subs),
                   "penalty": ac["minute"] + CONTEST_PENALTY * wrong if ac else 0,
                   "last": subs[-1]["verdict"] if subs else ""}
            if c.get("finished"):
                row.update({"lesson": l.id, "lesson_title": l.title, "difficulty": p.difficulty,
                            "source": p.source})
            rows.append(row)
        elapsed = self._elapsed(c)
        solved = [r for r in rows if r["solved"]]
        return {"id": c["id"], "started": c["started"], "minutes": c["minutes"],
                "elapsed": round(elapsed), "remaining": max(0, round(c["minutes"] * 60 - elapsed)),
                "finished": bool(c.get("finished")), "ended": c.get("ended", ""),
                "solved": len(solved), "penalty": sum(r["penalty"] for r in solved),
                "rows": rows, "pool": c.get("pool", "")}

    def op_contest(self, a: dict) -> dict:
        c = self._contest()
        past = []
        for old in reversed(self._contests()):
            if old.get("finished"):
                v = self.contest_view(old)
                past.append({k: v[k] for k in ("id", "started", "minutes", "solved", "penalty")} |
                            {"problems": len(v["rows"])})
        last = next((x for x in reversed(self._contests()) if x.get("finished")), None)
        return {"active": self.contest_view(c) if c else None,
                "last": self.contest_view(last) if last else None,
                "past": past[:20],
                "studied": sum(1 for l in self.lessons if self.store.lesson_status(l.id) != "new"
                               for _ in l.problems)}

    def op_contest_start(self, a: dict) -> dict:
        if self._contest() is not None:
            raise ValueError("a contest is already running")
        minutes = max(10, min(300, int(a.get("minutes", 120))))
        count = max(3, min(12, int(a.get("count", 6))))
        pool_kind = a.get("pool") if a.get("pool") in ("studied", "algo", "all") else "studied"

        def pool_for(kind: str) -> list:
            out = []
            for l in self.lessons:
                if kind == "studied" and self.store.lesson_status(l.id) == "new":
                    continue
                if kind == "algo" and l.track != "algo":
                    continue
                out += [(l, p) for p in l.problems]
            return out

        pool = pool_for(pool_kind)
        if len(pool) < count:
            pool = pool_for("algo") if len(pool_for("algo")) >= count else pool_for("all")
        if len(pool) < 3:
            raise ValueError("not enough problems for a contest yet")
        rng = random.Random()
        rng.shuffle(pool)
        # unsolved first, and a spread of difficulty like a real set
        pool.sort(key=lambda lp: self.store.solved(f"{lp[0].id}.{lp[1].id}"))
        quota = {"easy": max(1, round(count * .3)), "medium": max(1, round(count * .45))}
        quota["hard"] = max(0, count - quota["easy"] - quota["medium"])
        chosen = []
        for l, p in pool:
            if len(chosen) < count and quota.get(p.difficulty, 0) > 0:
                chosen.append((l, p))
                quota[p.difficulty] -= 1
        for lp in pool:
            if len(chosen) >= count:
                break
            if lp not in chosen:
                chosen.append(lp)
        rng.shuffle(chosen)
        c = {"id": len(self._contests()) + 1, "started": storemod.now_iso(), "minutes": minutes,
             "pool": pool_kind, "problems": [f"{l.id}.{p.id}" for l, p in chosen], "subs": []}
        self._contests().append(c)
        self.store.touch()
        self.store.save()
        return {"active": self.contest_view(c)}

    def op_contest_end(self, a: dict) -> dict:
        c = self._contest()
        if c is None:
            raise ValueError("no contest is running")
        c["finished"] = True
        c["ended"] = storemod.now_iso()
        self.store.save()
        return {"last": self.contest_view(c)}

    def contest_problem(self, l: Lesson, p: Problem) -> dict:
        """The problem as a contestant sees it: statement, samples, limits, clock."""
        r = f"{l.id}.{p.id}"
        c = self._contest()
        if c is None or r not in c["problems"]:
            raise ValueError("that problem is not in a running contest")
        view = self.contest_view(c)
        row = next(x for x in view["rows"] if x["ref"] == r)
        return {"ref": r, "title": p.title, "color": balloon(l, p), "letter": row["letter"],
                "statement": blocks(p.statement), "input": blocks(p.input), "output": blocks(p.output),
                "samples": [{"input": t.input, "output": t.output, "note": []} for t in p.samples],
                "time_limit": p.time_limit, "code": storemod.read_code(l.id, p.id, p.starter),
                "starter": p.starter, "path": storemod.code_path(l.id, p.id),
                "contest": view, "row": row,
                "subs": [s for s in c["subs"] if s["ref"] == r][::-1]}

    # ------------------------------------------------------------------ home
    def _weakest_problem(self):
        best = None
        for l in self.lessons:
            for p in l.problems:
                st = self.store.items.get(loader.problem_id(l.id, p))
                if st is None:
                    continue
                score = st.ease - (1.0 if not st.correct else 0.0)
                if best is None or score < best[0]:
                    best = (score, l, p)
        return (best[1], best[2]) if best else None

    def _open_problem(self):
        """An unsolved problem whose Try step the learner has already reached."""
        for l in self.lessons:
            if self.store.lesson_status(l.id) == "new":
                continue
            r = self.reached(l)
            for k, (_, _, s) in enumerate(l.steps()):
                if k > r:
                    break
                if isinstance(s, Try):
                    ref = f"{l.id}.{s.problem}"
                    ps = self.store.peek_problem(ref)
                    if not ps.get("solved") and not ps.get("gave_up"):
                        return l, l.problem(s.problem)
        return None

    def op_today(self, a: dict) -> dict:
        today = date.today()
        due = self.due_queue()
        created = str(self.store.data.get("created", ""))[:10]
        try:
            day = (today - date.fromisoformat(created)).days + 1
        except ValueError:
            day = 1
        target = int(self.store.setting("daily_target", 45) or 45)
        todays = [x for x in self.store.data["attempts"] if str(x.get("ts", ""))[:10] == today.isoformat()]
        rows = []
        if due:
            nc = sum(1 for d in due if d["kind"] == "card")
            rows.append({"key": "r", "title": "review", "state": "pending",
                         "detail": f"{len(due)} due · {nc} cards, {len(due) - nc} re-solves",
                         "minutes": min(target, round(nc * 0.5 + (len(due) - nc) * 8)),
                         "route": "#/review"})
        else:
            rows.append({"key": "r", "title": "review", "state": "done",
                         "detail": f"{len(todays)} reviewed today" if todays else "nothing due today",
                         "minutes": 0, "route": "#/review"})
        cur = self.current_lesson()
        if cur is not None:
            done, total = self.dialogue_progress(cur)
            r = self.reached(cur)
            steps = cur.steps()
            where = (f"part {steps[r][0] + 1}/{len(cur.parts)} · {cur.parts[steps[r][0]].title}"
                     if r < len(steps) else "dialogue finished · problems left")
            rows.append({"key": "l", "title": "continue", "state": "pending",
                         "detail": f"{cur.id} {cur.title} · {where}",
                         "minutes": 20, "route": f"#/lesson/{cur.id}"})
        else:
            rows.append({"key": "l", "title": "continue", "state": "done",
                         "detail": "every lesson learned", "minutes": 0, "route": "#/browse"})
        op = self._open_problem()
        if op:
            ol, opb = op
            rows.append({"key": "p", "title": "solve", "state": "pending",
                         "detail": f"{ol.id} · {opb.title} ({opb.difficulty})",
                         "minutes": PROBLEM_MIN.get(opb.difficulty, 15),
                         "route": f"#/problem/{ol.id}.{opb.id}"})
        weak = self._weakest_problem()
        if weak:
            wl, wp = weak
            rows.append({"key": "d", "title": "drill", "state": "pending",
                         "detail": f"re-solve {wl.id} · {wp.title}",
                         "minutes": PROBLEM_MIN.get(wp.difficulty, 15),
                         "route": f"#/problem/{wl.id}.{wp.id}"})
        for row in rows:
            if row["state"] != "done":
                row["state"] = "active"
                break

        upcoming = []
        for l in self.lessons:
            if self.store.lesson_status(l.id) == "learned":
                continue
            row = self.lesson_row(l)
            row["state"] = ("started" if row["status"] == "started"
                            else "ahead" if row["missing"] else "open")
            upcoming.append(row)
            if len(upcoming) >= 5:
                break
        upcoming.sort(key=lambda u: {"started": 0, "open": 1, "ahead": 2}[u["state"]])

        solved = sum(1 for v in self.store.data["problems"].values() if v.get("solved"))
        return {
            "today": today.isoformat(), "day": day,
            "streak": self.store.streak(), "best": self.store.data["streak"].get("best", 0),
            "minutes": round(self.store.session_seconds() / 60), "target": target,
            "due": len(due),
            "learned": sum(1 for l in self.lessons if self.store.lesson_status(l.id) == "learned"),
            "lessons": len(self.lessons),
            "solved": solved,
            "problems": sum(len(l.problems) for l in self.lessons),
            "plan": rows,
            "upcoming": upcoming,
            "forecast": forecast(self.store.items, FORECAST_DAYS),
            "recent": self._recent_verdicts(8),
            "retention": self._retention_by_lesson(5),
            "warnings": [f"curriculum/{m}.py failed to load: {e.splitlines()[0][:100]}"
                         for m, e in loader.load_errors().items()],
        }

    def _recent_verdicts(self, n: int) -> list[dict]:
        out = []
        for s in reversed(self.store.data["submissions"]):
            l, p = loader.find_problem(s.get("ref", ""))
            if p is None:
                continue
            out.append({"ref": s["ref"], "title": p.title, "verdict": s["verdict"],
                        "ts": s["ts"], "color": balloon(l, p)})
            if len(out) >= n:
                break
        return out

    # ------------------------------------------------------------------ stats
    def _retention_by_lesson(self, limit: int = 8) -> list[dict]:
        rows = []
        for l in self.lessons:
            reviews = correct = 0
            for iid in ([loader.card_id(l.id, c) for c in l.cards] +
                        [loader.problem_id(l.id, p) for p in l.problems]):
                st = self.store.items.get(iid)
                if st:
                    reviews += st.reviews
                    correct += st.correct
            if reviews >= 3:
                rows.append({"lesson": l.id, "label": l.title, "reviews": reviews,
                             "pct": round(100 * correct / reviews)})
        rows.sort(key=lambda r: (-r["pct"], r["lesson"]))
        return rows[:limit]

    def _activity(self, weeks: int = ACTIVITY_WEEKS) -> list[int]:
        counts = collections.Counter(str(x.get("ts", ""))[:10] for x in self.store.data["attempts"])
        counts.update(str(x.get("ts", ""))[:10] for x in self.store.data["submissions"])
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        first = monday - timedelta(weeks=weeks - 1)
        out = []
        for dow in range(7):
            for w in range(weeks):
                d = first + timedelta(weeks=w, days=dow)
                out.append(0 if d > today else counts.get(d.isoformat(), 0))
        return out

    def _hardest(self, limit: int = 6) -> list[dict]:
        out = []
        for ease, k in sorted(((v.ease, k) for k, v in self.store.items.items() if v.reviews >= 2))[:limit]:
            kind, l, obj = self.items.get(k, (None, None, None))
            if l is None:
                continue
            label = obj.title if kind == "problem" else plain(obj.q.strip().splitlines()[0])
            out.append({"item": k, "lesson": l.id, "kind": kind, "label": clip(label, 70),
                        "ease": round(ease, 2),
                        "ref": f"{l.id}.{obj.id}" if kind == "problem" else ""})
        return out

    def op_stats(self, a: dict) -> dict:
        items = self.store.items
        subs = self.store.data["submissions"]
        verdicts = collections.Counter(s["verdict"] for s in subs)
        attempts = self.store.data["attempts"]
        answers = [v for st in self.store.data["lessons"].values()
                   for v in st.get("answers", {}).values() if v.get("done") and "tries" in v]
        first_try = sum(1 for v in answers if v.get("correct"))
        tracks = []
        for t in loader.TRACK_ORDER:
            ls = [l for l in self.lessons if l.track == t]
            if ls:
                tracks.append({"track": t, "name": loader.TRACK_NAMES[t],
                               "learned": sum(1 for l in ls if self.store.lesson_status(l.id) == "learned"),
                               "total": len(ls),
                               "solved": sum(1 for l in ls for p in l.problems
                                             if self.store.solved(f"{l.id}.{p.id}")),
                               "problems": sum(len(l.problems) for l in ls)})
        return {
            "tracks": tracks,
            "verdicts": dict(verdicts),
            "submissions": len(subs),
            "solved": sum(1 for v in self.store.data["problems"].values() if v.get("solved")),
            "problems": sum(len(l.problems) for l in self.lessons),
            "first_try_pct": round(100 * first_try / len(answers)) if answers else 0,
            "questions": len(answers),
            "cards_seen": sum(1 for k in items if k.startswith("card:")),
            "cards_total": sum(len(l.cards) for l in self.lessons),
            "reviews": len(attempts),
            "remembered": (100 * sum(1 for x in attempts if x["q"] >= 3) // len(attempts)) if attempts else 0,
            "streak": self.store.streak(), "best": self.store.data["streak"].get("best", 0),
            "forecast": forecast(items, FORECAST_DAYS),
            "hardest": self._hardest(6),
            "retention": self._retention_by_lesson(8),
            "activity": self._activity(),
            "activity_weeks": ACTIVITY_WEEKS,
            "hours": round(self.store.total_session_seconds() / 3600, 1),
            "lessons_learned": sum(1 for l in self.lessons if self.store.lesson_status(l.id) == "learned"),
            "lessons_total": len(self.lessons),
        }

    def op_reset_progress(self, a: dict) -> dict:
        if a.get("confirm") != "reset":
            raise ValueError("send confirm: 'reset'")
        fresh = Store(path="")
        fresh.path = self.store.path
        self.store = fresh
        self.store.save()
        return {"ok": True}

    # ------------------------------------------------------------------ loop
    def dispatch(self, op: str, args: dict):
        fn = getattr(self, "op_" + op, None)
        if fn is None or not op.isidentifier():
            raise KeyError(f"unknown op {op!r}")
        return fn(args or {})


BALLOONS = ["#E5484D", "#F76B15", "#FFC53D", "#30A46C", "#12A594", "#0090FF", "#3E63DD",
            "#8E4EC6", "#D6409F", "#A18072", "#6E56CF", "#46A758"]


def balloon(l: Lesson, p: Problem) -> str:
    """Every problem gets a balloon colour, as solved problems do at an ICPC contest.
    Neighbouring problems in a lesson get different colours."""
    i = l.problems.index(p) if p in l.problems else 0
    offset = sum(map(ord, l.id)) % len(BALLOONS)
    return BALLOONS[(offset + i * 5) % len(BALLOONS)]
