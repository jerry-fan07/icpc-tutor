# icpc tutor

A local website that prepares you for ICPC-style contests. It teaches C++ first (to someone
who already programs in Python), then teaches contest algorithms as **Socratic
dialogues**: each technique is rebuilt from a concrete problem through questions — the
brute force, what it costs, what it wastes, the insight, why it is correct — before the
code. Every lesson ends in ICPC-style problems judged by compiling your C++ and running it
against hidden tests, and everything you learn comes back on an SM-2 spaced-repetition
schedule.

```
python3 cp.py serve --open        # http://127.0.0.1:8000
```

Python 3.10+ and a C++ compiler. Standard library only; no build step, no packages.

It is modelled on `../leetcode-tutor` (same stdlib server, same SM-2 scheduler, same
paper-and-hairline design), with three deliberate differences: C++ and stdin/stdout
problems instead of Python functions; lessons as dialogues instead of sections to read;
and **one learner, no accounts** — progress is a JSON file and your code is a folder of
`.cpp` files, so you can also work in your own editor.

## The compiler

The judge compiles with `-std=gnu++17 -O2`, the way ICPC judges do. It looks for, in order:
`$CPTUTOR_CXX`, the newest versioned GCC on the machine (`g++-16`, `g++-15`, ...), a `g++`
that really is GCC, then clang. On a Mac, `/usr/bin/g++` is Apple clang, which has no
`<bits/stdc++.h>`; install GCC with `brew install gcc` to match contest judges. (Clang
still works: `harness/include/bits/stdc++.h` is a stand-in for that one header.)

```
python3 cp.py compiler            # which compiler and flags the judge uses
```

## What is in it

**Two tracks, 35 lessons: about 1,350 dialogue steps (900 of them questions), 152 judged
problems and 400 review cards.** `curriculum/AUTHORING.md` has the full map.

- `cpp01`–`cpp10`, **C++ for contests**: from Python to contest C++, types and overflow,
  functions and references, vectors and strings, STL containers, STL algorithms and
  lambdas, structs and recursion patterns, reading complexity from the constraints,
  debugging and stress testing, bits and modular arithmetic.
- `algo01`–`algo25`, **algorithms, from the question up**: prefix sums, greedy with
  exchange arguments, binary search, two pointers, complete search and meet in the
  middle, three DP lessons, graph traversal, shortest paths, DSU and MST, DAGs and SCC,
  trees and tree DP, binary lifting and LCA, Fenwick trees and sparse tables, segment
  trees with lazy propagation, number theory, combinatorics and probability, string
  hashing / KMP / Z, tries and suffix arrays, geometry, max flow and matching, game
  theory, square-root decomposition and Mo's algorithm, and a contest-day capstone.

**Screens.**

- **today** — the plan (review what is due, continue your lesson, solve the problem you
  reached, re-solve your weakest one), the next lessons, recent verdicts, the review forecast.
- **lesson** — the dialogue. Everything up to the next question is on the page; answering
  unfolds the next stretch. Multiple choice (every wrong option explains *why* it is wrong),
  numbers (`2e5`, `4*10^10`, `2^20` all parse — you estimate a lot), short answers ("what
  does this print?"), open "think it through" questions you answer in your own words and
  compare with the tutor's, and "now solve it" steps that open a problem. `hint` and
  `show me` are always there; nothing is locked. The outline on the right tracks each part;
  the end of a lesson has cards to rate for review.
- **problem** — the statement beside an editor (C++ highlighting, auto-indent, `⌘↵` submit,
  `⌘'` run samples, `⌘/` comment). The judge reports AC / WA / TLE / RE / CE per test and
  stops at the first failure, like a contest judge; unlike one, small failing tests show the
  input, the expected output and yours. **Custom input** runs your program *and the
  reference solution* on anything you type. Hints and the editorial are there (reading the
  editorial first counts as giving up, for the schedule). After an AC a balloon floats up —
  solved problems get balloons, as at a contest — and you rate the solve to schedule a re-solve.
- **contest** — a virtual contest: 4–10 problems from lessons you have started, in random
  order as A, B, C…, a clock, ICPC scoring (problems solved, then penalty minutes: time of
  each AC plus 20 per rejected submission). No hints, no editorials, no lesson names, and
  hidden tests say only their verdict. The lessons are revealed afterwards.
- **notebook** — the code of everything you have solved (your last accepted version, or the
  reference), lesson by lesson, with a print stylesheet: the seed of the printed team
  reference document ICPC lets you bring.
- **review** — cards and problems that are due. **problems** — every problem, filterable.
  **stats** — solved, verdict mix, first-try rate on questions, streak, activity, retention.
  **playground** — compile and run any C++ on any input.

Single-key shortcuts: `t` today, `b` lessons, `o` problems, `r` review, `s` stats,
`c` contest, `n` notebook, `g` playground, `?` about; in a lesson, `1`–`4` pick an option.

## On your phone

`ios/` is a SwiftUI app for the same tutor: the dialogues, problems, judge verdicts,
review, contest, notebook, stats and playground, laid out for a phone. Nothing moves to the
phone: lessons, progress, your `.cpp` files and the compiler all stay on the Mac, and the
app talks to the server over Wi-Fi, so the phone and the browser share one progress file.

```
python3 cp.py serve --host 0.0.0.0        # prints the address to type into the phone
```

Open `ios/ICPCTutor.xcodeproj` in Xcode, plug in the phone, and Run (the project is
generated from `ios/project.yml` with [xcodegen](https://github.com/yonaskolb/XcodeGen);
`xcodegen generate` in `ios/` rebuilds it after adding files). The first run asks for
local-network permission. The server address lives under **more › settings**; the Mac's
Bonjour name (`<name>.local:8000`) usually works and its IP address always does.
`--host 0.0.0.0` means anyone on the network can run code on your Mac: home Wi-Fi only
(see Security). The app's UI tests (`ICPCTutorUITests`) expect a server on port 8123
pointed at a scratch copy of `data/` and `workspace/`, because they answer questions and
submit code.

## Where things live

```
cp.py                  entry point: serve / list / validate / judge / compiler
cptutor/
  schema.py            Lesson, Part, the dialogue steps, Problem, Test, Gen, Card
  judge.py             compile (cached by hash), run with limits, checkers, verdicts
  dialogue.py          grading answers (number parsing, short-answer normalising)
  api.py               everything the pages ask for; all scheduling decisions
  server.py            stdlib HTTP server, JSON API
  validate.py          the content checker (see below)
  store.py srs.py loader.py markup.py
curriculum/            one module per lesson, plus AUTHORING.md (the contract + the map)
web/                   index.html, app.js, style.css — plain JS, no framework
ios/                   the iPhone app (SwiftUI), a client of the same JSON API
harness/include/       the <bits/stdc++.h> stand-in for clang
data/                  progress.json and the judge's caches (created on first run)
workspace/             your code: workspace/<lesson>/<problem>.cpp (+ .accepted.cpp)
```

Progress is `data/progress.json` (written atomically) and your code is in `workspace/`;
override them with `CPTUTOR_DATA` and `CPTUTOR_WORKSPACE`. Edit a `.cpp` in any editor and
the problem page picks it up the next time it opens; the page autosaves to the same file.

## The judge

Each test runs as a separate process. CPU time is measured with `wait4()` and compared with
the problem's limit; a wall-clock timer kills runaways; output goes to a file and is capped
at 32 MB, so an infinite print loop is an Output Limit Exceeded rather than a frozen
machine. The main thread gets a 512 MB stack (a linker flag on macOS, `ulimit -s` on Linux)
because contest judges allow deep recursion. Memory is reported but not enforced (macOS
ignores `RLIMIT_AS`). Compiled binaries and the reference solution's outputs are cached in
`data/cache/`, keyed by the hash of what determines them.

Every problem has a reference solution, and generated tests get their expected output from
it. Where it helps, a problem also has a `brute` (slow and obviously correct, cross-checked
against the reference on every small test) and a `naive` (the tempting approach the lesson
steers away from, which must time out on a large test — that is what proves the large
tests enforce the complexity being taught).

```
python3 cp.py judge algo01.static_range_sum            # judge workspace/algo01/static_range_sum.cpp
python3 cp.py judge algo01.static_range_sum mine.cpp   # or any file
```

## Checking the curriculum

```
python3 cp.py validate                 # everything (several minutes: it runs every program)
python3 cp.py validate algo10 --no-run # one lesson, structure only
python3 cp.py list                     # every lesson and problem id
```

`validate` checks the dialogue's shape (at most two explanations in a row before a
question; every wrong option has a `why`; every question accepts its own answer; every
problem is reached from the dialogue), then compiles and runs every reference, brute,
naive, listed `wrong` program and starter against every test. The whole curriculum takes
a few minutes once the caches are warm. To add a lesson, follow `curriculum/AUTHORING.md`.

The dialogue answers were checked by the validator (each question accepts its own key)
and by hand with scratch programs while the lessons were written; the validator cannot
tell that a key is *right*. If an answer looks wrong to you, it may be: the lesson file is
plain Python, easy to fix.

## Security

Judging compiles and runs whatever C++ is submitted, with time and output limits but **no
sandbox**. That is what a local tutor needs, and it is why the server binds to
`127.0.0.1`. `--host 0.0.0.0` exists; use it only on a network you control, for people you
trust.
