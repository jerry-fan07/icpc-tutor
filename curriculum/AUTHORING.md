# Writing a lesson

This is the contract every lesson in `curriculum/` follows. Read it all, then read the two
reference lessons, which are the quality bar:

- `curriculum/cpp01_first_program.py` (C++ track)
- `curriculum/algo01_prefix_sums.py` (algorithms track)

Then validate:

```
python3 cp.py validate <lesson_id>          # structure + every question + every C++ program
python3 cp.py validate <lesson_id> --no-run # structure only (fast, while drafting)
```

A lesson is done when validation prints `ok` with **zero errors**. Warnings are worth
reading; timing warnings can be noise when the machine is busy (rerun before changing a
time limit).

## Who the learner is

A programmer who is fluent in Python and knows LeetCode-style data structures, preparing
for the ICPC. They are new to C++ and to contest-level algorithms. The C++ track teaches
by *contrast with Python*; it never explains what a loop is. The algorithms track assumes
the C++ track.

## The file

One module per lesson: `curriculum/<id>_<slug>.py`, defining `LESSON = Lesson(...)`.

```python
from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)
```

**Every text and code literal is a raw string: `r"""..."""`.** C++ is full of `'\n'` and
`"%d\n"`; in a normal Python string those become real newlines and the program no longer
compiles (or, worse, a Say block shows a broken snippet). Short `why=` strings on options
may be plain strings, but if they contain a backslash, write `'\\n'` or use `r"..."`.

Do not edit anything outside your own lesson files: not `cptutor/`, not `web/`, not other
lessons. If the engine seems wrong, say so in your final report instead.

## The dialogue: Socratic, not a textbook with a quiz

A lesson is a list of `Part`s; each part is a list of steps. The page shows every step up
to the first unanswered question and waits. Answering unfolds the next stretch, so **the
text after a question may give away its answer**, and should.

| step | what it is |
| `Say(text)` | the tutor talks: short paragraphs, code, tables |
| `MCQ(q, [Opt(text, correct, why)], explain, hint)` | pick one |
| `Numeric(q, answer, tol, rel, explain, hint, unit)` | type a number; `2e5`, `4*10^10`, `2^20`, `1,000` all parse |
| `Short(q, accept=[...], explain, hint, placeholder)` | type a short answer; compared lowercased with whitespace collapsed |
| `Reflect(q, answer)` | the learner writes their idea, then sees yours |
| `Try(problem_id, note)` | "now solve this": links a problem of this lesson |

### The shape of an algorithms lesson

The learner should *discover* each idea one step before being told it. The required arc,
per technique (a lesson usually has 2-4 techniques or variants, so it repeats):

1. **A concrete problem** with real limits (`n ≤ 2·10^5`, one second). Not "consider an
   array"; a problem statement.
2. **The brute force**, which the learner usually proposes or recognises (MCQ/Reflect).
3. **Its cost, estimated by the learner** (Numeric, `rel=0.5` for order-of-magnitude) and
   **compared with ~10^8 simple operations per second** (MCQ or Numeric).
4. **What work is wasted or repeated?** (Reflect or MCQ whose distractors are the things a
   real learner would say). This is the heart of the lesson.
5. **The idea falls out** of the answer to 4; the tutor names it only now.
6. **Why it is correct**: an invariant, an exchange argument, a proof by contradiction,
   asked as questions ("what would have to be true for this to fail?"), not recited.
7. **A worked micro-example** the learner computes by hand (Short/Numeric).
8. **The C++**, then questions about the details that cost points: types, bounds,
   off-by-ones, the I/O.
9. `Try(...)` the problem.
10. **Variants and limits**: when does the idea break? what changes if...?

The anti-pattern to avoid: `Say(explains Dijkstra fully) -> MCQ(what is its complexity?)`.
That is a textbook followed by a quiz. If a Say explains something, the question should
come *before* it, or ask the learner to apply it to a case the Say did not cover.

### The shape of a C++ lesson

Teach by prediction and by trap. "What does this print?" (Short) before the rule; "which
of these compiles?" (MCQ); "here is Python you would write; what is the C++?". Show the
trap *before* the fix: the overflow, the O(n) copy, the `set` that silently deduplicates.
Every C++ lesson still has problems, judged on stdin/stdout, and they should be designed
so that the lesson's trap actually costs a verdict (a sample or hidden test that the
naive/Python-habit version fails).

### Rules the validator enforces

- At least 3 parts and 10 questions (MCQ/Numeric/Short/Reflect). Aim for **5-7 parts and
  18-30 questions**.
- **At most 2 `Say` steps in a row.** Keep each `Say` under ~1500 characters (warning at
  2600). Long explanations are split by questions.
- Every MCQ option has a `why`, and every MCQ has at least one correct option.
- Every question accepts its own answer (the validator grades your answer key).
- Every problem is reached by at least one `Try` step.

### Writing good questions

- **Wrong options are where the teaching happens.** Each distractor is a misconception a
  real learner holds, and its `why` explains what exactly is wrong with it, often with a
  counterexample. "Incorrect." is not a why. The correct option's `why` confirms and adds
  one sentence of insight.
- 3-4 options. Vary the position of the correct one. Options are one line of inline
  markup (no code blocks); put code in the question.
- `explain` consolidates after the question is done: the general principle, a name, a
  pointer to what comes next. It may be empty when the whys already say it all.
- `Numeric`: use `rel=0.5` (or up to 0.9) for estimates, exact (`tol=0`) for computed
  values. Put the unit in `unit=`. Answers must be numbers, not strings.
- `Short`: for small computed values, program output, a formula. List reasonable variants
  in `accept` (`"p[i-1][j-1]"`, `"dp[i-1][j-1]"`). Case is ignored, whitespace is collapsed,
  and an answer also matches if it equals an accepted one with all spaces removed
  (so `p[i - 1][j - 1]` matches `p[i-1][j-1]` without listing it).
- `Reflect`: ask for the insight *before* it is given ("What does the brute force do
  twice?"). The `answer` is the tutor's model answer, 2-5 sentences, and it should be
  better than what a learner will write: it names the idea and says why.
- `hint`: optional nudge, never the answer.
- Use concrete numbers and tiny examples the learner can compute in their head.
- Do not ask trivia. Every question should either force a prediction, force a decision,
  or check a detail that costs a verdict.

### Voice

Second person, plain, specific, a little dry. Contest-honest: say what costs a WA or a
TLE. No emojis, no exclamation marks, no "great job", no "let's dive in". Prefer numbers
to adjectives ("4·10^10 operations", not "very slow").

## Markup (every text field)

- blank line = paragraph; `# heading`; `- bullet`; `1. numbered`; `| a | b |` table rows
  (the first row is the header; a `|---|` rule row is optional and ignored)
- fenced code blocks with three backticks; C++ is highlighted by default
- inline: backticks for code, `**bold**`, `*emphasis*`
- math in prose: `n ≤ 2·10^5`, `O(n log n)`, `2^31 − 1`, `a_i`, `a_(l+1)`: outside
  backticks, `x^k` renders as a superscript and a single letter followed by `_i` or
  `_(...)` as a subscript. Inside backticks everything is literal code.
- no links, no HTML
- a table cell cannot contain `|` (cells split on it); put such code in a code block
- part titles render inline markup; lesson titles, summaries and problem titles are plain
  text
- `assert` needs `#include <cassert>`: GCC 15+ no longer pulls it in through
  `<bits/stdc++.h>`

## Problems

ICPC-shaped: the program reads stdin and writes stdout. The judge compiles with
`g++ -std=gnu++17 -O2` (GCC 16 here), runs every test, and the first failure is the
verdict. There is no interactive-problem support.

```python
Problem(
    id="snake_case", title="Title Case", difficulty="easy|medium|hard",
    source="CSES 1646 - Static Range Sum Queries",   # when it mirrors a known problem
    complexity="O(n log n)",                          # target; shown after solving
    statement=r"""story + task""", input=r"""format + ALL constraints""",
    output=r"""format""",
    samples=[Test(input, output, note="optional: shown with the sample")],
    tests=[Test(input)],                              # hidden, handwritten edge cases
    gens=[Gen(name, fn, count, large=False)],         # hidden, generated
    solution=r"""reference C++""", brute=r"""slow obvious C++""", naive=r"""tempting-too-slow C++""",
    starter=...,                                      # default: the contest skeleton
    checker="tokens",                                 # see below
    time_limit=1.0, hints=[...], editorial=r"""...""",
)
```

- **Statement**: a short story (one or two sentences) and a precise task. Input section
  gives every constraint, including sums over test cases. Numbers in constraints as
  `2·10^5`.
- **Samples**: 1-3, small, with explicit outputs. A sample that exposes the lesson's trap
  is great (cpp01's `A + B` has one that overflows `int`), with a `note`.
- **Hidden tests**, in this order (the judge stops at the first failure, and hidden
  inputs up to 1500 characters are shown to the learner when they fail, so small failing
  tests teach):
  1. handwritten edge cases (`tests=`): n = 1, all equal, extremes of every value range,
     negative numbers when allowed, answers that overflow `int`;
  2. small random `Gen`s, with enough cases (`count` 8-20) to cross-check the brute;
  3. medium random;
  4. `large=True` gens at the maximum limits, including the worst case for the naive
     approach (e.g. queries spanning the whole array).
- **Generators**: `fn(rng) -> str`, using only the `random.Random` passed in (so tests
  are deterministic). Keep each generated input under ~10 MB and its generation under
  ~1 s of Python (e.g. `" ".join(map(str, list))`, not character-by-character string
  building for millions of characters). Module-level helper functions are fine.
- **`solution`**: clean, commented where the idea lives, fast I/O. Must run within a
  third of the time limit (aim for a tenth); the validator warns otherwise.
- **`brute`**: the simplest obviously-correct program (exponential or cubic is fine). The
  validator runs it on every non-large test and compares with the reference. Include one
  for every algorithms problem unless a brute is genuinely impractical to write.
- **`naive`**: the approach the lesson is steering away from (the O(n^2) loop, `endl`, a
  vector passed by value). When present, the validator requires it to exceed the time
  limit on at least one large test, which proves the large tests enforce the complexity.
  Include one whenever the lesson's point is complexity.
- **`wrong=[...]`**: tempting wrong programs (the `int` version, the missing reset, the
  greedy that fails); the validator requires each to be rejected, which keeps the lesson's
  traps enforced when tests change. Add one for every trap the dialogue promises will cost
  a verdict.
- **Brute scope**: the brute runs on every test except `large=True` gens. Turn it off for
  a single test with `Test(..., brute=False)` or a gen with `Gen(..., brute=False)` (an
  exponential brute on a small-but-extreme test), without marking it large.
- **`check_input=fn`**: `fn(input_text)` raises, or returns `False` or an error string,
  when an input breaks the stated constraints; the validator runs it on every test.
- **`checker`**: `"tokens"` (default: whitespace-separated tokens must match),
  `"tokens_ci"` (case-insensitive, for YES/NO), `"lines"` (line by line, trailing spaces
  ignored), `"float"` or `"float:1e-9"` (numeric tokens within that absolute-or-relative
  error). When several answers are valid, pass a Python function
  `check(input, expected, got) -> bool | (bool, message)` that validates `got` (parse
  defensively; raising counts as a wrong answer). The validator checks that it accepts
  the reference's own output.
- **`time_limit`**: 1.0 s is normal; use 0.5 s when the lesson is about I/O or constant
  factors, up to 2-3 s for heavy problems. Never raise a limit to rescue a slow reference.
- **`hints`**: 2-3, from a gentle nudge to nearly the idea.
- **`editorial`**: the idea, why it is correct, the complexity, and the traps. Shown after
  the learner solves it (or gives up).
- **`starter`**: default is the skeleton (includes, fast I/O, empty main). Override when
  the problem is about fixing or completing given code (cpp09 debugging problems ship a
  buggy program as the starter).
- The starter must not already pass (validated).
- Per lesson: **3-5 problems**, ordered from the one the dialogue introduces first to the
  hardest. Mirroring well-known problems (CSES, AtCoder, Codeforces, past ICPC) is good;
  write the statement in your own words and name the source in `source`.

The judge compiles C++17 (`-std=gnu++17`), as many contest judges still do: keep C++20
(`map::contains`, `erase_if`, ranges, `<bit>`'s `popcount`) out of solutions *and* out of
lesson snippets, or mention that it needs C++20.

On this machine (Apple silicon) `long double` is the same as `double`, while x86 judges
give it 64 bits of mantissa: never let a reference depend on `long double` precision
(`sqrtl` on 10^18, say); use integer arithmetic and correct the result.

Do not rely on GCC-only extensions (`__gnu_pbds`) in reference solutions. `__int128`,
`__builtin_popcount` and friends are fine (both GCC and clang have them).

## Cards

8-12 per lesson. A card is a fact, formula or idiom recalled in under 30 seconds, for
spaced repetition after the lesson. Answers 1-3 sentences, code allowed. No duplicates.

## Checklist before you report back

- `python3 cp.py validate <id>` prints `ok` for each of your lessons, zero errors.
- Every step of the dialogue reads well *in order*, with the questions answered wrongly
  first: does each `why` teach?
- The problems' traps are real: the naive version TLEs, the `int` version WAs, the
  missing reset WAs.
- Report: lesson ids, one line each on what they cover, problem list, validation output,
  anything in the engine that got in your way.

# Curriculum map

Ids, titles and prerequisites are fixed (other lessons refer to them). Scope and problem
ideas are suggestions; the lesson author has the final say on what makes it teach well.

## C++ track

- **cpp01** from Python to contest C++ *(done)*: judge model, skeleton, verdicts, types
  taste, input shapes, getline trap, fast I/O.
- **cpp02** types, overflow & arithmetic (prereqs: cpp01): `int`/`long long`/`unsigned`/
  `__int128` ranges; overflow in intermediate expressions (`1LL * a * b`); integer division
  and `%` truncating toward zero (negatives!), ceiling division and its negative trap;
  `double` precision (`0.1 + 0.2`, comparing with an epsilon, 53-bit mantissa: `(long
  long)(double)` loses precision past 2^53), printing with `setprecision`; `sqrt` on big
  integers and correcting it; `char` arithmetic (`c - '0'`, `'a' + k`); `INT_MAX`,
  `LLONG_MAX`, `1LL << 40` vs `1 << 40`. Problems: ceil division with negatives, product
  modulo m for m up to 10^18 (needs `__int128`), exact integer square root of values up to
  10^18, digit sums of a 10^5-digit number (read as a string).
- **cpp03** control flow, functions & references (prereqs: cpp02): value vs reference
  (`vector<int> v` parameter copies: O(n) per call, the TLE trap), `const&`, returning
  several values (`pair`, `tuple`, structured bindings `auto [a, b] = ...`), recursion and
  the call stack, globals (zero-initialised, big arrays go global not on the stack),
  `static`, lambdas as local helpers, early `return`/`break` patterns, `do/while`, `switch`.
  Problems: one where passing a big vector by value TLEs (naive), a recursion problem
  (e.g. Tower of Hanoi moves, CSES 2165), something with structured bindings / multiple
  returns.
- **cpp04** arrays, vectors & strings (prereqs: cpp03): `vector` API and costs (`push_back`
  amortised O(1), `insert`/`erase` in the middle O(n)), `resize`/`assign`, 2D vectors and
  grids, C arrays vs vectors, `string` API (`substr` is a copy: O(len); `s = s + c` is O(n)
  vs `s += c`), `find`, `to_string`, `stoi`/`stoll`, `char` classification, `reverse`,
  reading grids. Problems: grid processing, run-length encoding, the quadratic
  concatenation trap (naive), palindrome/string manipulation.
- **cpp05** STL containers (prereqs: cpp04): `pair`/`tuple` comparison, `set`/`multiset`
  (ordered, O(log n); `ms.erase(x)` erases *all* copies, `ms.erase(ms.find(x))` one),
  `map` (`m[k]` inserts a default!, `count`/`find`), `unordered_map` (average O(1),
  adversarial worst case, `reserve`), `priority_queue` (max-heap by default,
  `greater<>` for min), `stack`/`queue`/`deque`, member `s.lower_bound(x)` O(log n) vs
  `std::lower_bound(s.begin(), s.end(), x)` O(n) on a set (the TLE trap). Problems:
  Concert Tickets (CSES 1091, multiset), Distinct Numbers (CSES 1621), a running-median or
  priority-queue simulation, a map-counting problem.
- **cpp06** STL algorithms, iterators & lambdas (prereqs: cpp05): `sort` with comparators
  (strict weak ordering: a comparator using `<=` is undefined behaviour and can crash),
  sorting by several keys, lambdas with captures, `stable_sort`, `lower_bound`/
  `upper_bound`/`equal_range`/`binary_search` on sorted vectors, `unique` + `erase`,
  coordinate compression, `next_permutation`, `accumulate` (the `0` vs `0LL` trap),
  `min_element`/`max_element`, `count`, `iota`, `reverse`, `nth_element`. Problems:
  sort by custom key with ties, coordinate compression, counting values in ranges with
  `lower_bound`/`upper_bound`, generating permutations (CSES 1622 Creating Strings).
- **cpp07** structs, operator overloading & recursion patterns (prereqs: cpp06): `struct`
  with members and constructors, `operator<` for sorting and sets, arrays of structs vs
  parallel arrays, recursive lambdas (`auto dfs = [&](auto&& self, int u) -> void {...}`
  and `function<>`), memoisation arrays (`memset(dp, -1, sizeof dp)` works for -1 and 0
  only), resetting global state between test cases. Problems: events sorted by a struct
  key, a recursive generation problem (e.g. Gray code, CSES 2205), a memoised recursion,
  a multi-test problem where forgetting to reset fails.
- **cpp08** complexity: reading the constraints (prereqs: cpp07): counting operations,
  Big-O and the ~10^8 simple operations per second rule, the constraint table (n ≤ 10:
  n!, n ≤ 20: 2^n, n ≤ 500: n^3, n ≤ 5000: n^2, n ≤ 10^6: n log n, larger: n or log n),
  nested loops that are not n^2 (harmonic sums: n/1 + n/2 + ... = n ln n), amortised
  analysis (two pointers, vector growth), log factors, constants that matter (I/O, `map`
  vs array). Problems: maximum subarray (O(n^3) naive vs Kadane), sum over divisors for
  every number up to 10^6 (harmonic loop vs O(n√n)), pair counting that needs sorting or
  hashing instead of O(n^2).
- **cpp09** debugging & stress testing (prereqs: cpp08): reading GCC errors (the first one
  matters), `-Wall` warnings that are bugs, `assert`, debug printing to `cerr`, the bug
  checklist (overflow, uninitialised variables, off-by-one, array too small, state not
  reset between tests, shadowed variables, `=` vs `==`, integer division), stress testing
  (generator + brute + compare loop, shrinking a failing case). Problems ship a **buggy
  program as the starter** that the learner fixes; each bug is one from the checklist and
  the samples pass while hidden tests fail.
- **cpp10** bits & modular arithmetic (prereqs: cpp08): bit operators, masks, `1LL << k`,
  testing/setting/clearing bits, iterating all subsets of n ≤ 20 items with masks,
  `__builtin_popcount`/`ctz`/`clz` (and `ll` versions), XOR tricks; modular arithmetic:
  why problems say "mod 10^9 + 7", `(a * b) % m` in `long long`, subtraction fix, fast
  exponentiation (binary exponentiation), modular inverse by Fermat. Problems:
  Exponentiation (CSES 1095), Exponentiation II (CSES 1712), subset sums with masks
  (n ≤ 20), bit counting.

## Algorithms track

- **algo01** prefix sums & difference arrays *(done)* (prereqs: cpp08)
- **algo02** sorting & greedy: exchange arguments (prereqs: cpp06, cpp08): when greedy
  works and how to prove it (exchange argument, "greedy stays ahead"), when it fails
  (coin change counterexample), activity selection by earliest end, scheduling by
  deadline, sorting by a ratio or a clever key, the median minimises absolute deviation.
  Problems: Movie Festival (CSES 1629), Tasks and Deadlines (1630), Ferris Wheel (1090),
  Stick Lengths (1074).
- **algo03** binary search (prereqs: cpp06, cpp08): invariants (`lo` always bad, `hi`
  always good), the off-by-one-proof template, monotone predicates, binary search on the
  answer, bounds for the search range and overflow in `mid`, real-valued binary search by
  iteration count. Problems: Factory Machines (CSES 1620), Array Division (1085), a
  maximise-the-minimum-distance problem (Aggressive Cows), a real-valued one.
- **algo04** two pointers & sliding window (prereqs: algo01, algo03): why the pointers
  never move back (amortised O(n)), sum of two values on sorted data (CSES 1640),
  subarrays with sum ≤ x for positive values, longest window with at most k distinct
  values (with a count map), when windows fail (negative numbers: back to algo01).
  Problems: Sum of Two Values, Subarray Sums I (1660), Playlist (1141), a k-distinct window.
- **algo05** complete search, backtracking & meet in the middle (prereqs: cpp07, cpp10):
  the recursion tree, generating subsets and permutations, pruning, counting the states,
  the n ≤ 20 / n ≤ 40 signals, meet in the middle. Problems: Apple Division (CSES 1623),
  Chessboard and Queens (1624), Meet in the Middle (1628), a permutation search.
- **algo06** dynamic programming I: states and transitions (prereqs: algo05): from the
  exponential recursion to memoisation to a table; overlapping subproblems; defining the
  state in words; order of computation; counting vs optimising. Problems: Dice
  Combinations (CSES 1633), Minimizing Coins (1634), Coin Combinations I and II (1635,
  1636: ordered vs unordered is a loop-order question), Grid Paths (1638).
- **algo07** dynamic programming II: knapsack & sequences (prereqs: algo06, algo03): 0/1
  knapsack (Book Shop 1158) and why the capacity loop runs backwards in 1D, LCS and edit
  distance (1639), LIS in O(n^2) then O(n log n) (1145) with the patience-sorting
  argument. Problems: those four.
- **algo08** dynamic programming III: bitmasks, intervals & digits (prereqs: algo07,
  cpp10): subsets as states (Hamiltonian Flights 1690, Elevator Rides 1653), interval DP
  (Removal Game 1097), digit DP (Counting Numbers 2220).
- **algo09** graphs: representation & traversal (prereqs: cpp05, cpp08): adjacency lists,
  BFS (shortest paths in unweighted graphs, why), DFS (components, iterative vs recursive
  and the stack), grids as graphs, path reconstruction with parents, bipartiteness, cycle
  detection. Problems: Counting Rooms (1192), Labyrinth (1193), Building Teams (1668),
  Round Trip (1669) or Message Route (1667).
- **algo10** shortest paths (prereqs: algo09): relaxation; Dijkstra with a heap and lazy
  deletion and the proof that needs non-negative weights; Bellman-Ford and negative
  cycles; Floyd-Warshall; 0-1 BFS; choosing from the constraints. Problems: Shortest
  Routes I (1671), Shortest Routes II (1672), Cycle Finding (1197), Flight Discount (1195,
  state expansion).
- **algo11** disjoint set union & minimum spanning trees (prereqs: algo09, algo02): DSU
  with path compression and union by size, why it is nearly O(1), Kruskal with the cut
  property proof, Prim. Problems: Road Construction (1676), Road Reparation (1675), a
  dynamic-connectivity-offline or "last edge that connects" problem.
- **algo12** DAGs: topological order, DP on DAGs, SCC (prereqs: algo09, algo06): Kahn and
  DFS order, detecting cycles, longest/counting paths on a DAG, strongly connected
  components (Kosaraju), the condensation graph. Problems: Course Schedule (1679),
  Longest Flight Route (1680), Game Routes (1681), Planets and Kingdoms (1683).
- **algo13** trees: traversal & tree DP (prereqs: algo09, algo06): rooted trees from edge
  lists, subtree sizes, diameter (two BFS and why it works), DP on trees (Tree Matching
  1130), rerooting (Tree Distances I 1132 / II 1133). Problems: Subordinates (1674), Tree
  Diameter (1131), Tree Matching, Tree Distances II.
- **algo14** binary lifting & lowest common ancestor (prereqs: algo13, cpp10): k-th
  ancestor via powers of two, LCA by lifting, distances via LCA, Euler tour and the
  subtree-as-interval idea. Problems: Company Queries I (1687), Company Queries II (1688),
  Distance Queries (1135), Subtree Queries (1137) optional.
- **algo15** range queries I: sparse tables & Fenwick trees (prereqs: algo01, cpp10):
  idempotent operations and O(1) range minimum, the Fenwick tree's `i & -i` from first
  principles, point update / prefix query, range update / point query with a difference
  Fenwick. Problems: Static Range Minimum Queries (1647), Dynamic Range Sum Queries
  (1648), Range Update Queries (1651), inversion counting.
- **algo16** range queries II: segment trees (prereqs: algo15): recursive and iterative
  segment trees, what a node stores and the merge, walking down the tree (Hotel Queries
  1143), lazy propagation for range add / range assign (Range Updates and Sums 1735),
  storing a combined summary (maximum subarray sum in a range).
- **algo17** number theory (prereqs: cpp10): gcd and why Euclid terminates fast, extended
  Euclid and linear Diophantine equations, the sieve (and linear/smallest-prime-factor
  sieve), factorisation, counting divisors, Euler's totient, modular inverses when the
  modulus is not prime, CRT for two congruences. Problems: Counting Divisors (1713),
  Common Divisors (1081), a totient/sieve problem, a Diophantine one.
- **algo18** combinatorics & probability (prereqs: algo17, algo06): nCr mod p with
  factorial and inverse-factorial tables, stars and bars, inclusion-exclusion (Prime
  Multiples 2185), derangements (Christmas Party 1717), linearity of expectation, DP over
  probabilities (Dice Probability 1725). Problems: Binomial Coefficients (1079) and the
  above.
- **algo19** strings I: hashing, prefix function, Z-function (prereqs: algo01, cpp10):
  polynomial hashing and collision probability (two mods or mod 2^61 − 1, random base),
  the prefix function (KMP) from "what did we already learn about the pattern?", the
  Z-function, borders and periods. Problems: String Matching (1753), Finding Borders
  (1732), Finding Periods (1733), a hashing problem (e.g. longest palindrome via hashing
  or comparing substrings).
- **algo20** strings II: tries & suffix arrays (prereqs: algo19, algo06): tries and DP
  over them (Word Combinations 1731), suffix array by prefix doubling O(n log n) (or
  O(n log^2 n) with sort), LCP array (Kasai), distinct substrings (2105), repeating
  substring (2106).
- **algo21** computational geometry (prereqs: cpp02, algo02): points as vectors, cross
  product and orientation (all in `long long`, no floating point), segment intersection,
  shoelace polygon area, point in polygon, convex hull by monotone chain. Problems: Point
  Location Test (2189), Line Segment Intersection (2190), Polygon Area (2191), Convex Hull
  (2195).
- **algo22** network flow & matching (prereqs: algo10): the flow network model, augmenting
  paths and residual edges (why the reverse edge is needed), Edmonds-Karp then Dinic, max
  flow = min cut, bipartite matching as flow. Problems: Download Speed (1694), Police
  Chase (1695, output the cut), School Dance (1696, output the matching).
- **algo23** game theory (prereqs: algo06, cpp10): winning and losing positions by
  backward induction, Nim and the XOR rule (with the proof), Sprague-Grundy numbers and
  sums of games. Problems: Stick Game (1729), Nim Game I (1730), Nim Game II (1098),
  Grundy's Game (2207) or another Grundy problem.
- **algo24** square-root decomposition & offline queries (prereqs: algo15): blocks of size
  √n, the balance argument, Mo's algorithm and why the query order gives O((n + q)√n),
  answering queries offline by sorting them. Problems: Distinct Values Queries (1734), a
  block-decomposition update/query problem, an offline-sorted-queries problem with a
  Fenwick tree.
- **algo25** contest day: strategy & a mixed problem set (prereqs: algo04, algo07,
  algo10, algo16): ICPC as a team sport (three people, one computer), reading every
  problem first, using the scoreboard to find the easy ones, penalty arithmetic (time of
  each AC + 20 minutes per rejected submission), when to print and debug on paper, the
  team reference document, testing before submitting. Problems: 5 mixed problems whose
  technique is *not* announced (the learner must recognise it: prefix sums, binary search,
  a graph, a DP, a greedy), easiest first.
