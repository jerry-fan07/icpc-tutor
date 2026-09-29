from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _mats(rng, n, lim):
    out = [str(n)]
    for _ in range(n):
        out.append(f"{rng.randint(1, lim)} {rng.randint(1, lim)}")
    return "\n".join(out) + "\n"


def _days(rng, t, nmax, idmax):
    out = [str(t)]
    for _ in range(t):
        n = rng.randint(1, nmax)
        out.append(str(n))
        out.append(" ".join(str(rng.randint(1, idmax)) for _ in range(n)))
    return "\n".join(out) + "\n"


def _days_big(rng):
    t = 10000                                   # 20 ids per day, ids shared across days
    out = [str(t)]
    for _ in range(t):
        out.append("20")
        out.append(" ".join(str(rng.randint(1, 50)) for _ in range(20)))
    return "\n".join(out) + "\n"


def _temps(rng, n, lim):
    return f"{n}\n" + " ".join(str(rng.randint(-lim, lim)) for _ in range(n)) + "\n"


def _classes(rng, n, smax, kmax):
    k = rng.randint(1, kmax)
    return f"{n} {k}\n" + " ".join(str(rng.randint(1, smax)) for _ in range(n)) + "\n"


def _budget(rng, n, vmax, xmax):
    x = rng.randint(2, xmax)
    return f"{n} {x}\n" + " ".join(str(rng.randint(1, vmax)) for _ in range(n)) + "\n"


# --------------------------------------------------------------------- problems
TOTAL_AREA = Problem(
    id="total_area",
    title="Floor Mats",
    difficulty="easy",
    complexity="O(n)",
    statement=r"""
A gym floor is covered by `n` rectangular mats that do not overlap. Mat `i` measures
w_i × h_i. Print the total area covered.

**This problem comes with a program** (it is in the editor): it passes both samples and
fails a hidden test. Find the bug and fix it.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has two integers w_i and h_i (1 ≤ w_i, h_i ≤ 10^5).
""",
    output=r"""
Print the total area.
""",
    samples=[
        Test("3\n2 3\n4 5\n1 1\n", "27\n"),
        Test("1\n40000 50000\n", "2000000000\n"),
    ],
    tests=[
        Test("1\n1 1\n"),
        Test("1\n100000 100000\n"),
        Test("3\n100000 99999\n1 1\n50000 50000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _mats(rng, rng.randint(1, 10), 100), 8),
        Gen("big mats", lambda rng: _mats(rng, 1000, 10**5), 2),
        Gen("max size", lambda rng: _mats(rng, 200000, 10**5), 1, large=True),
    ],
    starter=r"""#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    long long total = 0;        // long long: the total can reach 2 * 10^15
    for (int i = 0; i < n; i++) {
        int w, h;
        cin >> w >> h;
        total += w * h;
    }
    cout << total << '\n';
    return 0;
}
""",
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    long long total = 0;
    for (int i = 0; i < n; i++) {
        int w, h;
        cin >> w >> h;
        total += 1LL * w * h;   // multiply in 64 bits: w * h alone is an int product
    }
    cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long n, w, h, total = 0;
    cin >> n;
    while (n--) { cin >> w >> h; total += w * h; }
    cout << total << '\n';
}
""",
    hints=[
        r"""Go down the checklist. The first item is overflow: what is the largest value each
*expression* can take, not just each variable?""",
        r"""`total` is `long long`, but `w * h` is computed from two `int`s, in 32 bits, before it
is added. 10^5 · 10^5 = 10^10 does not fit.""",
    ],
    editorial=r"""
The bug is overflow in an intermediate expression: `w * h` multiplies two `int`s, so the
product is an `int`, and 10^5 · 10^5 = 10^10 overflows it (this judge prints 1410065408
for that one mat) before the `+=` widens anything. Declaring `total` as `long long` does
not help, because C++ chooses the type of `w * h` from `w` and `h`, not from where the
result goes.

Fix: `total += 1LL * w * h;` (or declare `w` and `h` as `long long`). The second sample
is the tease: 40000 · 50000 = 2·10^9 still fits in an `int`, by 7%.

Compiling with `-fsanitize=undefined` finds this immediately: "runtime error: signed
integer overflow: 100000 * 100000 cannot be represented in type 'int'".
""",
)

DAILY_VISITORS = Problem(
    id="daily_visitors",
    title="Daily Visitors",
    difficulty="easy",
    complexity="O(sum of n log n)",
    statement=r"""
A museum records the id of every visitor each time they walk in. For each of `t` days,
print how many *different* visitors came that day.

**This problem comes with a program** (it is in the editor): it passes the sample and
fails a hidden test. Find the bug and fix it.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^4), the number of days.

Each day is two lines: `n` (1 ≤ n ≤ 2·10^5), then `n` visitor ids (1 ≤ id ≤ 10^9).
The sum of `n` over all days is at most 2·10^5.
""",
    output=r"""
For each day, print the number of different ids on its own line.
""",
    samples=[
        Test("2\n4\n1 2 2 3\n3\n7 7 8\n", "3\n2\n"),
    ],
    tests=[
        Test("1\n1\n1000000000\n"),
        Test("2\n2\n5 5\n1\n5\n"),
        Test("3\n3\n1 2 3\n3\n3 2 1\n2\n4 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _days(rng, rng.randint(1, 5), 6, 5), 10),
        Gen("medium random", lambda rng: _days(rng, 200, 50, 1000), 2),
        Gen("10^4 days, shared ids", _days_big, 1, large=True),
    ],
    starter=r"""#include <bits/stdc++.h>
using namespace std;

set<int> seen;                  // ids seen so far

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        int distinct = 0;
        for (int i = 0; i < n; i++) {
            int id;
            cin >> id;
            if (seen.insert(id).second) distinct++;   // .second is true when id is new
        }
        cout << distinct << '\n';
    }
    return 0;
}
""",
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        set<int> seen;          // one fresh set per day: nothing survives from yesterday
        for (int i = 0; i < n; i++) {
            int id;
            cin >> id;
            seen.insert(id);
        }
        cout << seen.size() << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (auto& x : a) cin >> x;
        sort(a.begin(), a.end());
        cout << unique(a.begin(), a.end()) - a.begin() << '\n';
    }
}
""",
    hints=[
        r"""The sample has two days that share no visitors. What if the same person visits on
two different days?""",
        r"""`seen` is a global that is never cleared, so on day two it still remembers day one.
`distinct` is reset for every day; the set it depends on is not.""",
    ],
    editorial=r"""
The bug is state that survives between test cases. `distinct` is reset at the start of
every day, but the set `seen` is a global that is never cleared, so a visitor who came
yesterday is not "new" today. The sample cannot see it because its two days have no id in
common; the second hidden test (`5 5`, then `5`) prints `1 0` instead of `1 1`.

Fix: declare the set inside the loop (or call `seen.clear()` at the start of each day).
Clearing costs O(size of the set), so with the sum of `n` bounded the total is still
O(sum of n log n).

When a multi-test program is right on the first test and wrong later, suspect this first:
list every variable and container declared outside the test loop and ask whether each one
should be reset.
""",
)

HIGHS = Problem(
    id="highs_from_here",
    title="Highs From Here",
    difficulty="easy",
    complexity="O(n)",
    statement=r"""
A weather station recorded `n` daily temperatures. For each day, report the highest
temperature on that day or any later day.

**This problem comes with a program** (it is in the editor): it passes the samples and
fails a hidden test. Find the bug and fix it.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers t_1, ..., t_n (−10^9 ≤ t_i ≤ 10^9).
""",
    output=r"""
Print `n` integers on one line: for each `i`, the maximum of t_i, ..., t_n.
""",
    samples=[
        Test("6\n3 9 2 7 1 4\n", "9 9 7 7 4 4\n"),
        Test("1\n-5\n", "-5\n"),
    ],
    tests=[
        Test("3\n-1 -2 -3\n"),
        Test("4\n1000000000 -1000000000 1000000000 -1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _temps(rng, rng.randint(1, 10), 20), 8),
        Gen("medium random", lambda rng: _temps(rng, 3000, 10**9), 2),
        Gen("max size", lambda rng: _temps(rng, 200000, 10**9), 1, large=True),
        Gen("150000 days", lambda rng: _temps(rng, 150000, 10**9), 1, large=True),
    ],
    starter=r"""#include <bits/stdc++.h>
using namespace std;

const int MAXN = 100005;        // n <= 10^5
long long a[MAXN];

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    for (int i = 0; i < n; i++) cin >> a[i];
    for (int i = n - 2; i >= 0; i--) a[i] = max(a[i], a[i + 1]);   // suffix maximum, in place
    for (int i = 0; i < n; i++) cout << a[i] << (i + 1 < n ? ' ' : '\n');
    return 0;
}
""",
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int MAXN = 200005;        // the limit is 2 * 10^5, plus a little slack
long long a[MAXN];

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    for (int i = 0; i < n; i++) cin >> a[i];
    for (int i = n - 2; i >= 0; i--) a[i] = max(a[i], a[i + 1]);
    for (int i = 0; i < n; i++) cout << a[i] << (i + 1 < n ? ' ' : '\n');
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<long long> t(n);
    for (auto& x : t) cin >> x;
    for (int i = 0; i < n; i++) {
        long long m = t[i];
        for (int j = i; j < n; j++) m = max(m, t[j]);
        cout << m << (i + 1 < n ? ' ' : '\n');
    }
}
""",
    hints=[
        r"""The verdict is RE (a crash), and only on big tests. On the checklist, which bugs crash
only when the input is large?""",
        r"""Compare the comment next to `MAXN` with the input section.""",
    ],
    editorial=r"""
The array is too small. The comment says `n <= 10^5`, but the limit is 2·10^5, so on the
big tests `cin >> a[i]` writes up to 10^5 `long long`s (800 KB) past the end of `a`. C++
does not check: writing out of bounds is undefined behaviour. Here it runs off the end of
the program's data into unmapped memory and the program dies (RE, "bus error" or
"segmentation fault"); on another machine it might silently overwrite other variables and
give a WA instead.

Fix: size arrays from the input section, with slack: `const int MAXN = 200005;`. Or use
`vector<long long> a(n)`, which is sized at run time; then `-D_GLIBCXX_DEBUG` or
`-fsanitize=address` catch any out-of-range index during local testing.

An RE that appears only on large tests points at array sizes (or recursion depth); an RE
on small tests points at index arithmetic (`i - 1` at `i = 0`, `i + 1` at the last index).
""",
)

BUSES = Problem(
    id="school_trip",
    title="School Trip",
    difficulty="easy",
    complexity="O(n)",
    statement=r"""
`n` classes go on a trip. Class `i` has s_i students. Every bus holds `k` students, and
classes do not share buses. How many buses are needed?

**This problem comes with a program** (it is in the editor): it passes both samples and
fails a hidden test. Find the bug and fix it.
""",
    input=r"""
The first line has `n` and `k` (1 ≤ n ≤ 2·10^5, 1 ≤ k ≤ 10^9).

The second line has `n` integers s_1, ..., s_n (1 ≤ s_i ≤ 10^9).
""",
    output=r"""
Print the total number of buses.
""",
    samples=[
        Test("3 10\n20 30 10\n", "6\n"),
        Test("2 7\n14 7\n", "3\n"),
    ],
    tests=[
        Test("1 10\n25\n"),
        Test("3 1\n1000000000 1000000000 1000000000\n"),
        Test("2 1000000000\n1 1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _classes(rng, rng.randint(1, 8), 30, 10), 10),
        Gen("big values", lambda rng: _classes(rng, 1000, 10**9, 10**9), 2),
        Gen("max size", lambda rng: _classes(rng, 200000, 10**9, 1000), 1, large=True),
    ],
    starter=r"""#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    long long buses = 0;
    for (int i = 0; i < n; i++) {
        int s;
        cin >> s;
        buses += ceil(s / k);   // round up: a half-full bus is still a bus
    }
    cout << buses << '\n';
    return 0;
}
""",
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long n, k;
    cin >> n >> k;
    long long buses = 0;
    for (int i = 0; i < n; i++) {
        long long s;
        cin >> s;
        buses += (s + k - 1) / k;   // integer ceiling for positive s and k
    }
    cout << buses << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long n, k, buses = 0;
    cin >> n >> k;
    for (int i = 0; i < n; i++) {
        long long s;
        cin >> s;
        buses += s / k;
        if (s % k != 0) buses++;
    }
    cout << buses << '\n';
}
""",
    hints=[
        r"""The samples only contain class sizes that are multiples of `k`. Try `1 10` / `25` by
hand, then trace the program on it.""",
        r"""`s / k` with two `int`s is already rounded down to an integer; `ceil` of an integer
changes nothing. Round up with integers: `(s + k - 1) / k`.""",
    ],
    editorial=r"""
Integer division. `s / k` divides two `int`s, so it truncates first: 25 / 10 is 2, and
`ceil(2)` is 2. The `ceil` was meant to act on 2.5, which never existed. Both samples use
multiples of `k`, where truncating and rounding up agree, so they pass.

The integer way to round up a positive quotient is `(s + k - 1) / k`: adding `k − 1`
pushes every non-multiple past the next multiple and leaves exact multiples alone. Keep it
in `long long` (here `s + k − 1` stays below 2^31, but only just). `ceil((double)s / k)`
also works for these limits, but floating point in integer problems is a habit that
eventually bites (doubles are exact only up to 2^53).

Division is a checklist item for another reason too: `/` and `%` on negative numbers
truncate toward zero in C++ (`-7 / 2 == -3`), so the formula above is only for positive
values.
""",
)

BUDGET_PAIRS = Problem(
    id="budget_pairs",
    title="Pairs on a Budget",
    difficulty="medium",
    complexity="O(n log n)",
    statement=r"""
Given `n` prices and a budget `x`, count the pairs of positions `i < j` with
a_i + a_j ≤ x.

**This problem comes with a program** (it is in the editor). It is fast, it looks right,
and it passes both samples, but it fails hidden tests, and the ones it fails are too big
for the judge to show you. Find a small failing input yourself by stress testing: write a
brute force and a generator and compare them, as the lesson shows. Then fix the program.
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 2·10^5, 1 ≤ x ≤ 2·10^9).

The second line has `n` integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print the number of pairs.
""",
    samples=[
        Test("4 9\n1 2 6 9\n", "3\n"),
        Test("3 100\n50 60 70\n", "0\n"),
    ],
    tests=[
        Test("1 5\n3\n"),
        Test("3 1\n1 1 1\n"),
        Test("3 1000000000\n1 2 3\n"),
    ],
    gens=[
        # these come first on purpose: the judge stops at the first failure, and these
        # inputs are too long to be shown, so the learner has to stress test
        Gen("medium, small values", lambda rng: _budget(rng, 1000, 60, 120), 3),
        Gen("small random", lambda rng: _budget(rng, rng.randint(1, 8), 10, 20), 12),
        Gen("max size", lambda rng: _budget(rng, 200000, 10**9, 2 * 10**9), 1, large=True),
        Gen("max size, all equal pairs", lambda rng: "200000 2000000000\n" + " ".join(["1000000000"] * 200000) + "\n",
            1, large=True),
    ],
    starter=r"""#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    sort(a.begin(), a.end());
    long long ans = 0;
    int l = 0, r = n - 1;
    while (l < r) {
        if (a[l] + a[r] < x) {
            ans += r - l;       // a[l] pairs with every a[l+1..r]
            l++;
        } else {
            r--;                // a[r] is too big for anything left
        }
    }
    cout << ans << '\n';
    return 0;
}
""",
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    sort(a.begin(), a.end());
    long long ans = 0;
    int l = 0, r = n - 1;
    while (l < r) {
        if (a[l] + a[r] <= x) {  // "at most x": equal to x is within budget
            ans += r - l;
            l++;
        } else {
            r--;
        }
    }
    cout << ans << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    long long ans = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] + a[j] <= x) ans++;
    cout << ans << '\n';
}
""",
    hints=[
        r"""The brute force is two nested loops over `i < j`. The generator should make tiny
inputs: `n` from 1 to 5, prices from 1 to 10, `x` from 1 to 20. Small values make
coincidences (like a sum landing exactly on `x`) frequent.""",
        r"""Once the loop finds a failing input, shrink it: most failures here can be reproduced
with `n = 2`. Then compare the statement's condition, word for word, with the `if`.""",
    ],
    editorial=r"""
The condition says *at most* `x`, and the program tests `a[l] + a[r] < x`. Every pair
whose sum is exactly `x` is missed. The samples happen to contain no such pair; small
random tests hit one almost immediately (`2 4` / `2 2` expects 1, and the program prints
0). An off-by-one in a comparison is the same bug as an off-by-one in a loop bound, and it
is just as invisible when you reread code you believe in.

With `<=`, the two-pointer argument holds: after sorting, if `a[l] + a[r] ≤ x`, then `a[l]`
fits with every element between `l + 1` and `r`, so add `r − l` and advance `l`; otherwise
`a[r]` fits with nothing that remains, so drop it. O(n log n) for the sort, O(n) for the
scan.

The general lesson is the workflow, not the character: when a fast solution fails and you
cannot see why, let a brute force and a generator find you a failing input of size 2.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp09",
    title="debugging & stress testing",
    track="cpp",
    order=9,
    summary="Reading GCC's errors and warnings, making the program talk with cerr and "
            "assert, the checklist of bugs that pass the samples, and stress testing: a "
            "generator, a brute force and a loop that finds the failing input for you.",
    prereqs=["cpp08"],
    tags=["debugging", "compiler errors", "warnings", "sanitizers", "assert", "stress testing",
          "overflow", "off-by-one", "reset between tests"],
    parts=[
        Part("The first error is the real one", [
            Say(r"""
Python stops at the first error and prints one traceback. GCC does something else: after
an error it tries to carry on, guesses what you meant, and keeps reporting. Those later
reports are often consequences of the first. Here is a 10-line program and everything GCC
said about it:

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    cout << a[0] << '\n';
}
```

```text
main.cpp:6:13: error: expected ';' before 'vector'
main.cpp:8:20: error: 'a' was not declared in this scope
main.cpp:9:13: error: 'a' was not declared in this scope
```
"""),
            Numeric(r"""
How many mistakes are there in the program?
""", answer=1, unit="mistakes",
                explain=r"""
One. The missing `;` after `cin >> n` makes GCC swallow the declaration of `a`, and then
every use of `a` is an error too. Fix the first error, recompile, and the other two vanish.
"""),
            MCQ(r"""
The first message says line 6, column 13, "expected ';' before 'vector'". Where does the
semicolon go?
""", [
                Opt("At the end of line 6, after `cin >> n`.", correct=True,
                    why="Yes. GCC reports a missing `;` at the point where it noticed, which is "
                        "the end of the line that lacks it (here it even draws the `;` for you)."),
                Opt("At the start of line 7, before `vector`.",
                    why="That would also compile, but the statement that is unfinished is line "
                        "6. 'before vector' names the token GCC tripped over."),
                Opt("Lines 8 and 9 need `a` declared again.",
                    why="`a` is declared on line 7; GCC just never parsed that declaration "
                        "because of the missing `;`. Those errors are consequences."),
            ], explain=r"""
Rule: read the first error, fix it, recompile. Never try to fix error number 5 while error
number 1 is still there.
"""),
            Say(r"""
Errors inside the standard library are longer. Sorting a `set` produces 141 lines, and the
first line that says `error` points into GCC's own `stl_algo.h`:

```text
In file included from .../bits/stdc++.h:51,
                 from main.cpp:1:
.../bits/stl_algo.h: In instantiation of 'void std::__sort(...)':
.../bits/stl_algo.h:4817:18:   required from 'void std::sort(...)'
main.cpp:6:9:   required from here
    6 |     sort(s.begin(), s.end());
.../bits/stl_algo.h:1914:50: error: no match for 'operator-' (operand types
are 'std::_Rb_tree_const_iterator<int>' and 'std::_Rb_tree_const_iterator<int>')
```
"""),
            MCQ(r"""
Which line of that output tells you what to change?
""", [
                Opt("The `error:` line in `stl_algo.h`: `operator-` is missing, so add one.",
                    why="The library is not broken, and you should never edit it. That line is "
                        "where the problem *surfaced*, deep inside `sort`."),
                Opt("`main.cpp:6:9: required from here`, the last line that mentions your file.",
                    correct=True,
                    why="Yes. Everything above and below is the library explaining itself; the "
                        "line in `main.cpp` is where your call started it. Then the error text "
                        "says why: `sort` subtracts iterators, and set iterators cannot do that."),
                Opt("The first line, `In file included from`.",
                    why="That only says which headers were being read. It is the same for every "
                        "program that includes `bits/stdc++.h`."),
            ], explain=r"""
Here the fix is to delete the line: a `set` is always sorted. `sort` needs random-access
iterators (a `vector`, an array, a `string`). The other classic wall of text,
`cout << v` for a `vector`, is 748 lines; its first line is already in `main.cpp` and says
"no match for 'operator<<'": there is no built-in way to print a vector.
"""),
        ]),
        Part("Warnings are bug reports", [
            Say(r"""
The judge here compiles with `-Wall` and shows you the warnings, so they are worth reading
before the verdict. This program compiles, and GCC says:

```cpp
int n, k;
cin >> n >> k;
vector<int> a(n);
long long sum;
for (int i = 0; i < n; i++) {
    cin >> a[i];
    sum += a[i];
}
int cnt = 0;
for (int i = 0; i < n; i++)
    if (a[i] = k) cnt++;
```

```text
warning: suggest parentheses around assignment used as truth value [-Wparentheses]
warning: 'sum' may be used uninitialized [-Wmaybe-uninitialized]
```
"""),
            MCQ(r"""
With input `n = 3, k = 2` and `a = 1 2 3`, what does `cnt` end up as?
""", [
                Opt("1: one element equals 2.",
                    why="That is what `==` would count. `a[i] = k` *assigns* 2 to `a[i]`, and the "
                        "`if` then tests the assigned value."),
                Opt("3, and the array is now `2 2 2`.", correct=True,
                    why="Yes. The condition is the value of the assignment, 2, which is true every "
                        "time; and every element has been overwritten on the way."),
                Opt("0: an assignment is not a condition.",
                    why="In C++ an assignment is an expression with a value, so it is a legal "
                        "condition. That is why the compiler can only warn."),
            ], explain=r"""
The warning text is the tell: "assignment used as truth value". Python rejects `if x = 0:`
as a syntax error; C++ accepts it. When you really mean it, GCC wants double parentheses,
`if ((x = f()))`, which is how you say "yes, on purpose".
"""),
            MCQ(r"""
On this machine, the program above prints `-10` as the sum of `1 2 3`. A similar program
keeps a running maximum in an uninitialised `int best;` and, compiled with `-O2`, prints
the right answer on every test you try. Is *that* program correct?
""", [
                Opt("Yes: it gave the right answers.",
                    why="It gave the right answers *this time, with these flags*. A local starts "
                        "with whatever its memory or register held. Measured here: the same "
                        "program compiled with `-O0` prints `1` for the input `-5 -9 -2`."),
                Opt("No: reading an uninitialised local is undefined behaviour, whatever it printed.",
                    correct=True,
                    why="Right. Undefined behaviour includes 'works on my machine'. It may break "
                        "with other flags, another compiler, or a different test. Initialise every "
                        "local, and treat the warning as an error."),
                Opt("Yes, because `int` variables start at 0.",
                    why="*Global* variables start at 0, whatever their type. Locals start with "
                        "garbage; the sum program above shows how much."),
            ]),
            Short(r"""
The judge's flags hide one more classic. What does this print? (`size()` returns an
unsigned 64-bit integer.)

```cpp
vector<int> v;
cout << v.size() - 1 << '\n';
```
""", accept=["18446744073709551615", "2^64 - 1", "2^64-1"], placeholder="a number",
                hint="Unsigned arithmetic wraps around: 0 − 1 is the largest value the type holds.",
                explain=r"""
`18446744073709551615`, which is 2^64 − 1. So `for (int i = 0; i < v.size() - 1; i++)` on
an empty vector does not run zero times: it runs until `v[i]` crashes. Write `i + 1 <
v.size()`, or cast: `(int)v.size() - 1`. `-Wall` warns about signed/unsigned comparisons,
but this judge turns that warning off (`-Wno-sign-compare`) because it fires on every
ordinary `i < v.size()`.
"""),
            Say(r"""
Locally, compile with more checks than the judge uses. A reasonable debugging command:

```bash
g++ -std=gnu++17 -O2 -g -Wall -Wextra -Wshadow -D_GLIBCXX_DEBUG \
    -fsanitize=address,undefined -fno-sanitize-recover=undefined sol.cpp -o sol
```

- `-Wextra -Wshadow`: more warnings, including a local variable hiding another one.
- `-fsanitize=undefined`: signed overflow, bad shifts and division by zero print a message
  such as `runtime error: signed integer overflow: 100000 * 100000 cannot be represented
  in type 'int'`; `-fno-sanitize-recover` makes the program stop there instead of going on.
- `-fsanitize=address`: any out-of-bounds or use-after-free memory access stops the
  program; with `-g` the report names the file and line.
- `-D_GLIBCXX_DEBUG`: `vector`, `string` and friends check every `[]` index.

These make the program several times slower, so use them for debugging, not for the
final timing. All of them work with the GCC this judge uses.
"""),
            MCQ(r"""
Your program reads `n` values into `vector<int> a(n)` with `for (int i = 1; i <= n; i++)
cin >> a[i];`. It prints correct answers on the samples. Which tool reports the bug?
""", [
                Opt("`-Wall`",
                    why="The compiler cannot know what `n` will be, so it cannot see that `a[n]` is "
                        "out of range. No warning."),
                Opt("`-fsanitize=address` or `-D_GLIBCXX_DEBUG`", correct=True,
                    why="Yes. Both check at run time; the first reports a heap-buffer-overflow "
                        "naming the line, the second aborts with 'attempt to subscript container "
                        "with out-of-bounds index 5, but container only holds 5 elements'."),
                Opt("Nothing: writing one past the end is harmless.",
                    why="It is undefined behaviour. Usually it lands in unused memory and nothing "
                        "happens, which is exactly why it survives until the one test where it "
                        "overwrites something important."),
            ]),
        ]),
        Part("Make the program talk", [
            Say(r"""
When the answer is wrong and the code looks right, stop reading and start *looking*:
print the intermediate values. Print to `cerr`, which the judge ignores (cpp01), so a
forgotten debug line is not an instant WA. A one-line macro saves typing:

```cpp
#define dbg(x) cerr << #x << " = " << (x) << '\n'
```

`#x` turns the macro argument into a string literal of its own source text.
"""),
            Short(r"""
With `int a = 3, b = 4;`, what does `dbg(a + b);` print (to stderr)?
""", accept=["a + b = 7", "a+b = 7", "a+b=7", "a + b=7"], placeholder="the printed line",
                explain=r"""
`a + b = 7`: `#x` is the text `a + b`, then the value. The label is what makes debug output
readable when you print twenty values in a loop. The parentheses around `(x)` in the macro
matter: without them, `dbg(a << 1)` expands to `cerr << ... << a << 1` and prints
`a << 1 = 31` (the 3, then the 1) instead of `a << 1 = 6`.
"""),
            MCQ(r"""
You forget a `dbg(i);` inside a loop that runs 10^6 times, and submit. The judge ignores
stderr. What happens?
""", [
                Opt("WA: the extra lines are compared with the expected output.",
                    why="Only stdout is compared. That is the whole point of printing to `cerr`."),
                Opt("Nothing: stderr is thrown away, so it costs nothing.",
                    why="It is thrown away *after* your program has paid to write it, and `cerr` is "
                        "unbuffered: every `<<` is its own system call."),
                Opt("Likely TLE: 10^6 debug lines cost about 6 seconds of CPU here.", correct=True,
                    why="Yes, measured on this judge: 0.7 s of user time and 5.7 s of system time, "
                        "four unbuffered writes per line. A few debug lines are free; a million are "
                        "not."),
            ], explain=r"""
The usual guard: wrap debug code in `#ifdef LOCAL ... #endif` and compile locally with
`-DLOCAL`. On the judge, where `LOCAL` is not defined, the lines are not even compiled.
"""),
            Say(r"""
The other half is `assert(condition)`: if the condition is false, the program stops at
once, printing the condition and its line number. On a judge that is a **run-time error**
instead of a wrong answer.

One detail specific to recent GCC (including this judge's GCC 16): `<bits/stdc++.h>` no
longer includes `<cassert>`, so `assert` does not compile without its own include:

```cpp
#include <bits/stdc++.h>
#include <cassert>          // needed for assert with recent GCC (this judge: GCC 16)
using namespace std;
```
"""),
            MCQ(r"""
Your solution assumes that some pair is always found, so after the search you add
`assert(found);`. You submit: RE on test 12, where before you had WA on test 12. What have
you learned?
""", [
                Opt("Nothing: it still fails on test 12.",
                    why="You have learned *why* it fails there: the assumption is false on that "
                        "input. A WA could have been any bug; the RE points at one line."),
                Opt("That your assumption is false for test 12, so either the search is wrong or the assumption is.",
                    correct=True,
                    why="Yes. An assert converts a silent wrong answer into a loud, located "
                        "failure. Several asserts, submitted one version at a time, narrow down "
                        "which assumption breaks."),
                Opt("That the assert itself is buggy and should be removed.",
                    why="An assert only reads a condition. If it fires, the condition was false; "
                        "that is information, not a bug in the assert."),
            ], explain=r"""
Good places for asserts: input assumptions ("the array is sorted", "n ≥ 1"), invariants
inside a loop ("lo < hi"), and results ("the answer was set"). They cost almost nothing.
"""),
        ]),
        Part("The checklist", [
            Say(r"""
Most wrong answers from a correct idea come from a short list of mechanical bugs. When the
verdict is WA or RE and the idea is right, go down this list, item by item, before
rereading the logic:

1. **Overflow**: every *expression*, not just every variable: `a * b`, sums, counters.
2. **Uninitialised** locals, and wrong starting values (a max starting at 0).
3. **Off by one**: loop bounds, `<` vs `<=`, `n - 1` vs `n`.
4. **Array too small** for the limits, or an index of `-1` or `n`.
5. **State not reset** between test cases.
6. **Shadowing**: an inner declaration hides the variable you meant.
7. **`=` instead of `==`**.
8. **Integer division** where you meant real division, or rounding the wrong way.
"""),
            MCQ(r"""
This is the heart of a program that passes the samples and fails a hidden test with
`w, h ≤ 10^5`. Which checklist item?

```cpp
long long total = 0;          // the total can reach 2 * 10^15
int w, h;
cin >> w >> h;
total += w * h;
```
""", [
                Opt("Overflow in `w * h`.", correct=True,
                    why="Yes. The product of two `int`s is an `int`: 10^10 overflows before the "
                        "`+=` widens it. `1LL * w * h`."),
                Opt("Uninitialised `total`.",
                    why="`total` is initialised to 0. Read the declaration again."),
                Opt("Nothing: `total` is a `long long`.",
                    why="The type of `w * h` is decided by `w` and `h`, not by `total`."),
            ]),
            Try("total_area", note="Checklist item 1."),
            MCQ(r"""
A multi-test program prints the right answer for the first test case and wrong ones
after that, but only on some inputs. Which checklist item do you check first?
""", [
                Opt("Off by one in the input loop.",
                    why="That would usually break the first test case too, or all of them."),
                Opt("State not reset between test cases.", correct=True,
                    why="Yes. 'First test right, later ones wrong' is its signature: something "
                        "declared outside the test loop still remembers the previous test."),
                Opt("Integer division.",
                    why="It would affect the first test as much as the others."),
            ], explain=r"""
Look at every global and every variable declared above `while (t--)`, and ask of each:
does the next test case need it fresh? Counters, `set`s, `map`s, adjacency lists, visited
arrays, "best so far" values.
"""),
            Try("daily_visitors", note="Checklist item 5. The sample's two days share no "
                "visitors."),
            Numeric(r"""
Checklist item 3. A loop is meant to visit every window of `k` consecutive elements,
starting at index `i`. With `n = 5` and `k = 2`, how many windows does this loop visit?

```cpp
for (int i = 0; i + k < n; i++) { /* window a[i..i+k-1] */ }
```
""", answer=3, unit="windows",
                hint="List the values of `i` for which `i + 2 < 5`.",
                explain=r"""
Three (`i = 0, 1, 2`), but there are `n − k + 1 = 4` windows: the last one starts at `i = 3`
and ends at index 4, the last element. The condition should be `i + k <= n`. The samples
catch this only if the best window happens to be the last one. The cure is to check every
bound on the smallest case: the last window, `n = k`, `n = 1`.
"""),
            MCQ(r"""
A program gets **RE** on the large hidden tests and passes every small one. Which item is
the most likely cause?
""", [
                Opt("An array sized for a smaller limit than the input section allows.",
                    correct=True,
                    why="Yes. Out-of-bounds writes only happen once `n` passes the size, so the "
                        "small tests are fine. Deep recursion is the other large-input-only crash."),
                Opt("`=` instead of `==`.",
                    why="That changes the logic on every input, small or large, and does not "
                        "crash."),
                Opt("Overflow.",
                    why="Signed overflow gives wrong numbers, not crashes (unless the garbage is "
                        "then used as an index)."),
            ]),
            Try("highs_from_here", note="The failing test is too big to show. The verdict and "
                "the checklist are enough."),
            Short(r"""
What does `cout << ceil(25 / 10);` print?
""", accept=["2"], placeholder="a number",
                explain=r"""
`2`. `25 / 10` is integer division, 2, and `ceil(2)` is 2. The rounding up was meant for
2.5, which was never computed. With integers, round up with `(a + b - 1) / b` (for
positive `a` and `b`).
"""),
            Try("school_trip", note="Checklist item 8."),
            MCQ(r"""
Checklist item 6. Compiled with `-Wshadow`, GCC says about this code: "declaration of
'best' shadows a previous local". What does the program print for `a = 1 5 2`, and why?

```cpp
long long best = 0;
for (int i = 0; i < n; i++) {
    long long cur = a[i];
    if (cur > best) {
        long long best = cur;
    }
}
cout << best << '\n';
```
""", [
                Opt("0: the inner `long long best = cur;` creates a new variable, and the outer `best` never changes.",
                    correct=True,
                    why="Yes. The inner `best` lives only inside the braces and dies there. The fix "
                        "is `best = cur;` without the type. `-Wall` alone does not report it; "
                        "`-Wshadow` does (and `-Wall` may notice the inner one is unused)."),
                Opt("It does not compile: `best` is declared twice.",
                    why="Declaring the same name in an inner scope is legal C++, which is exactly "
                        "why this bug is easy to write."),
                Opt("5: the inner assignment updates `best`.",
                    why="A declaration with a type always makes a new variable, even when the "
                        "name already exists outside."),
            ]),
        ]),
        Part("Stress testing", [
            Say(r"""
Sometimes the checklist comes up empty: WA on test 9, the input is too big to show, and
the code looks right no matter how often you read it. Then stop reading and let the
computer search. You need three programs:

1. your solution, `sol.cpp`;
2. a **brute force**, `brute.cpp`: the slowest, dumbest, obviously correct approach (all
   pairs, all subsets, a direct simulation);
3. a **generator**, `gen.py`, that prints a random small input.

Then a loop runs both on thousands of random inputs and stops at the first one where
their outputs differ.
"""),
            MCQ(r"""
What kind of inputs should the generator produce?
""", [
                Opt("Maximum-size inputs, since that is where the judge's tests fail.",
                    why="The brute force is too slow for them, and even if it were not, a failing "
                        "input with 2·10^5 numbers teaches you nothing. You want a failure you can "
                        "trace by hand."),
                Opt("Tiny inputs with small values: n from 1 to 6, values from 1 to 10.",
                    correct=True,
                    why="Yes. Thousands per second, and when one fails it fits on a line. Small "
                        "values also make coincidences (equal elements, sums hitting a bound "
                        "exactly) frequent, and coincidences are where bugs hide."),
                Opt("Only the edge cases: n = 1, all equal, all maximum.",
                    why="Those belong in your handwritten tests too, but a stress test is "
                        "valuable precisely because it tries cases you did not think of."),
            ]),
            MCQ(r"""
Your fast solution counts pairs `i < j` with a_i + a_j ≤ x by sorting and two pointers.
Which brute force should you compare it with?
""", [
                Opt("Two nested loops over all pairs `i < j`, testing the condition exactly as the statement words it.",
                    correct=True,
                    why="Yes: nothing clever, nothing shared with the solution, and short enough to "
                        "be obviously right. Its O(n^2) does not matter on inputs of size 6."),
                Opt("A copy of the two-pointer code, rewritten carefully from scratch.",
                    why="A rewrite of the same idea tends to repeat the same mistake, and then the "
                        "two programs agree on the wrong answer."),
                Opt("Sorting plus `upper_bound(x - a[i])` for each `i`.",
                    why="A different fast algorithm is a decent cross-check, but it has its own "
                        "boundaries to get wrong (`upper_bound` vs `lower_bound`, `j > i`). The "
                        "brute should be the one you cannot get wrong."),
            ]),
            Say(r"""
For a problem whose input is `n x` and then `n` values, the generator and the loop:

```python
# gen.py: one random small test; the seed comes from the command line
import random, sys
random.seed(int(sys.argv[1]))
n = random.randint(1, 6)
x = random.randint(1, 20)
print(n, x)
print(*[random.randint(1, 10) for _ in range(n)])
```

```bash
g++ -O2 -o sol sol.cpp && g++ -O2 -o brute brute.cpp
for i in $(seq 1 2000); do
    python3 gen.py $i > in.txt
    ./sol < in.txt > out_sol.txt
    ./brute < in.txt > out_brute.txt
    if ! cmp -s out_sol.txt out_brute.txt; then
        echo "seed $i:"; cat in.txt
        echo "sol: $(cat out_sol.txt)  brute: $(cat out_brute.txt)"
        break
    fi
done
```
"""),
            MCQ(r"""
Why does the generator take its seed from the loop counter instead of using a fresh
random seed each time?
""", [
                Opt("A fixed seed makes the numbers more random.",
                    why="Seeding does not change the quality of the numbers; it fixes which ones "
                        "you get."),
                Opt("So a failure is reproducible: `python3 gen.py 437` recreates the failing input exactly.",
                    correct=True,
                    why="Yes. You can rerun that one case after every attempted fix, and add it to "
                        "your own tests."),
                Opt("Python's random module crashes without a seed.",
                    why="Without a seed it seeds itself from the clock or the OS. It works, but "
                        "a failure could not be recreated."),
            ]),
            Reflect(r"""
The stress loop runs 2000 seeds and finds no difference, but the judge still says WA.
Give two reasons this can happen, and what you would change in each case.
""", answer=r"""
First, the generator may not produce the inputs that fail: the bug may need large values
(overflow), a large `n` (array size, a `-1` sentinel that collides), multiple test cases
(reset bugs), or a special structure (all equal, n = 1). Widen the generator in those
directions, one at a time. Second, the brute force may share the bug: if it was written
with the same misreading of the statement (`<` for "at most", 0-indexed vs 1-indexed), both
agree and both are wrong. Write the brute as differently as possible, check it against
the samples by hand, and reread the statement.
"""),
            MCQ(r"""
The loop finds a failing input with `n = 6`. What is the fastest way to a failing input
you can understand?
""", [
                Opt("Trace the program on it by hand, all six elements.",
                    why="Possible, but slow. Let the computer shrink it first."),
                Opt("Lower the generator's maximum `n` to 2 or 3 and rerun the loop.",
                    correct=True,
                    why="Yes. If the bug can happen at size 2, the loop finds such a case in "
                        "seconds, and a 2-element failure usually shows the bug on sight. "
                        "(Deleting elements from the failing input while it still fails also "
                        "works.)"),
                Opt("Increase the number of seeds to 100,000.",
                    why="You already have a failure; more seeds only find more of the same size."),
            ], explain=r"""
Shrinking is the step that turns "it is wrong somewhere" into "it is wrong *here*". A
failure of size 2 usually needs no debugger.
"""),
            Try("budget_pairs", note="The judge will not show the failing inputs. Stress test: "
                "the generator above fits this problem's input format as it is."),
        ]),
    ],
    problems=[TOTAL_AREA, DAILY_VISITORS, HIGHS, BUSES, BUDGET_PAIRS],
    cards=[
        Card(r"""GCC prints 12 errors. Which one do you fix first?""",
             r"""The first. Later errors are often consequences of it (a missing `;` makes the next declaration vanish). Fix it and recompile."""),
        Card(r"""How do you find your own line in a 100-line template error?""",
             r"""Look for the last line mentioning your file: `main.cpp:LINE:COL: required from here`. The error text above it says what the library could not do."""),
        Card(r"""A good local debugging compile command?""",
             r"""`g++ -std=gnu++17 -O2 -g -Wall -Wextra -Wshadow -D_GLIBCXX_DEBUG -fsanitize=address,undefined -fno-sanitize-recover=undefined sol.cpp` (slower; for debugging, not timing)."""),
        Card(r"""What does "suggest parentheses around assignment used as truth value" mean?""",
             r"""You wrote `if (a = b)`: an assignment, whose value is tested. You almost certainly meant `==`."""),
        Card(r"""What is `v.size() - 1` for an empty vector, and why does it matter?""",
             r"""2^64 − 1 (unsigned wrap-around), so `i < v.size() - 1` loops almost forever. Write `i + 1 < v.size()`."""),
        Card(r"""A debug-print macro that labels the value?""",
             r"""`#define dbg(x) cerr << #x << " = " << (x) << '\n'`; `dbg(a + b)` prints `a + b = 7`. `cerr` is ignored by judges."""),
        Card(r"""`assert` with GCC 16's `<bits/stdc++.h>`?""",
             r"""Add `#include <cassert>`: recent GCC no longer pulls it in. A failing assert aborts: RE on a judge, with the condition and line printed locally."""),
        Card(r"""The bug checklist for a WA with a correct idea?""",
             r"""Overflow (every expression), uninitialised/wrong start values, off-by-one (bounds, `<` vs `<=`), array too small, state not reset between tests, shadowing, `=` vs `==`, integer division."""),
        Card(r"""Signature of "state not reset between test cases"?""",
             r"""First test case right, later ones wrong (on some inputs). Check every variable and container declared outside `while (t--)`."""),
        Card(r"""RE only on large tests: first suspects?""",
             r"""An array smaller than the limits allow, or recursion too deep. RE on small tests: an index like `i - 1` at 0 or `i + 1` at the end."""),
        Card(r"""`ceil(a / b)` with `int a, b`?""",
             r"""Wrong: `a / b` is already truncated. Round up with `(a + b - 1) / b` for positive values."""),
        Card(r"""The three parts of a stress test, and the generator's two rules?""",
             r"""Solution, obviously-correct brute force, random generator, compared in a loop. Generator: tiny sizes and small values, seeded by the loop counter so failures are reproducible."""),
    ],
)
