#!/usr/bin/env python3
"""ICPC tutor.

    python3 cp.py serve [--port 8000]          the website (http://127.0.0.1:8000)
    python3 cp.py list                         every lesson and problem
    python3 cp.py validate [ids] [--no-run]    check lessons, run every solution
    python3 cp.py judge <lesson.problem> [file.cpp]   judge a file (default: workspace)
    python3 cp.py compiler                     which C++ compiler the judge uses
"""
import os
import sys

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "serve"
    rest = argv[1:]
    if cmd == "serve":
        from cptutor.server import main as serve
        return serve(rest)
    if cmd == "validate":
        from cptutor.validate import validate
        ids = [a for a in rest if not a.startswith("-")]
        return validate(ids or None, run="--no-run" not in rest, quiet="-q" in rest)
    if cmd == "list":
        from cptutor import loader
        for l in loader.load_all():
            print(f"{l.id:7s} {l.title}  ({', '.join(l.prereqs) or 'no prereqs'})")
            for p in l.problems:
                print(f"          {l.id}.{p.id:28s} {p.difficulty:6s} {p.title}")
        for m, e in loader.load_errors().items():
            print(f"LOAD ERROR {m}: {e}")
        return 0
    if cmd == "judge":
        import json
        from cptutor import judge, loader, store
        if not rest:
            print("usage: cp.py judge <lesson.problem> [file.cpp]")
            return 2
        l, p = loader.find_problem(rest[0])
        if p is None:
            print(f"no problem {rest[0]!r}")
            return 2
        path = rest[1] if len(rest) > 1 else store.code_path(l.id, p.id)
        with open(path, encoding="utf-8") as f:
            res = judge.judge(l, p, f.read())
        if res["verdict"] == "CE":
            print(res["compile"])
        for c in res["cases"]:
            print(f"  {c['name']:10s} {c['verdict']:4s} {c['ms']:5d} ms  {c.get('message', '')}")
        print(f"{res['verdict']}  {res['passed']}/{res['total']}"
              + (f"  (first failure: {res['failed']})" if res["failed"] else ""))
        return 0 if res["verdict"] == "AC" else 1
    if cmd == "compiler":
        from cptutor import judge
        c = judge.compiler()
        print(c["version"], "at", c["path"])
        print("flags:", " ".join(judge.flags()))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
