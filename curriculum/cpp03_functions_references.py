from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _brackets(rng, n, q, vmax):
    a = sorted(rng.randint(0, vmax) for _ in range(n))
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        x, y = rng.randint(0, vmax), rng.randint(0, vmax)
        out.append(f"{min(x, y)} {max(x, y)}")
    return "\n".join(out) + "\n"


_MDAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _leap(y):
    return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0


def _date(rng, ylo=1, yhi=9000):
    y = rng.randint(ylo, yhi)
    m = rng.randint(1, 12)
    top = 29 if (m == 2 and _leap(y)) else _MDAYS[m]
    d = rng.choice((rng.randint(1, top), top, top - 1))      # month ends are where bugs live
    return y, m, d


def _days(rng, t, kmax):
    out = [str(t)]
    for _ in range(t):
        y, m, d = _date(rng)
        out.append(f"{y} {m} {d} {rng.randint(0, kmax)}")
    return "\n".join(out) + "\n"


def _month_ends():
    rows = []
    for y in (2023, 2024, 1900, 2000):
        for m in range(1, 13):
            top = 29 if (m == 2 and _leap(y)) else _MDAYS[m]
            rows.append(f"{y} {m} {top} 1")
    return f"{len(rows)}\n" + "\n".join(rows) + "\n"


def _fib_small(rng):
    t = 20
    return f"{t}\n" + "\n".join(str(rng.randint(0, 2000)) for _ in range(t)) + "\n"


def _fib_mixed(rng, t):
    vals = []
    for _ in range(t):
        digits = rng.randint(1, 18)
        vals.append(rng.randint(0, 10**digits))
    return f"{t}\n" + "\n".join(map(str, vals)) + "\n"


def _fib_huge(rng, t):
    return f"{t}\n" + "\n".join(str(rng.randint(10**17, 10**18)) for _ in range(t)) + "\n"


# --------------------------------------------------------------------- problems
BRACKET_STARTER = r"""#include <bits/stdc++.h>
using namespace std;

// How many values in a (sorted, non-decreasing) are <= x?
int count_at_most(vector<int> a, int x) {
    // binary search here
    return 0;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> a(n);
    for (auto& v : a) cin >> v;
    while (q--) {
        int l, r;
        cin >> l >> r;
        cout << count_at_most(a, r) - count_at_most(a, l - 1) << '\n';
    }
    return 0;
}
"""

BRACKETS = Problem(
    id="score_brackets",
    title="Scores in a Bracket",
    difficulty="easy",
    complexity="O(n + q log n)",
    statement=r"""
The final standings of a contest list the scores of `n` contestants in non-decreasing
order. The organisers have `q` questions, each of the form "how many contestants scored at
least `L` and at most `R`?".

Answer every question. The starter code already has the shape of a solution; you write the
helper.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n ≤ 5·10^5, 1 ≤ q ≤ 2·10^5).

The second line has `n` integers a_1 ≤ a_2 ≤ ... ≤ a_n (0 ≤ a_i ≤ 10^6).

Each of the next `q` lines has two integers `L R` (0 ≤ L ≤ R ≤ 10^6).
""",
    output=r"""
For each question, print the number of scores `s` with `L ≤ s ≤ R` on its own line.
""",
    samples=[
        Test("6 4\n10 20 20 30 50 50\n20 30\n0 9\n15 50\n50 100\n", "3\n0\n5\n2\n"),
    ],
    tests=[
        Test("1 3\n7\n7 7\n0 6\n8 1000000\n"),
        Test("5 3\n4 4 4 4 4\n4 4\n0 3\n0 1000000\n"),
        Test("4 2\n0 0 1000000 1000000\n0 0\n1 999999\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _brackets(rng, rng.randint(1, 15), rng.randint(1, 15), 30), 12),
        Gen("medium random", lambda rng: _brackets(rng, 2000, 2000, 10**6), 2),
        Gen("max size", lambda rng: _brackets(rng, 500000, 200000, 10**6), 2, large=True),
    ],
    starter=BRACKET_STARTER,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// How many values in a (sorted, non-decreasing) are <= x?
// const&: no copy per call, and the compiler stops us from modifying a by accident.
int count_at_most(const vector<int>& a, int x) {
    int lo = 0, hi = (int)a.size();          // answer in [lo, hi]
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] <= x) lo = mid + 1;       // a[0..mid] are all <= x
        else hi = mid;
    }
    return lo;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> a(n);
    for (auto& v : a) cin >> v;
    while (q--) {
        int l, r;
        cin >> l >> r;
        cout << count_at_most(a, r) - count_at_most(a, l - 1) << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, q;
    cin >> n >> q;
    vector<int> a(n);
    for (auto& v : a) cin >> v;
    while (q--) {
        int l, r;
        cin >> l >> r;
        int c = 0;
        for (int v : a) if (l <= v && v <= r) c++;
        cout << c << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;

int count_at_most(vector<int> a, int x) {    // by value: copies all n scores per call
    int lo = 0, hi = (int)a.size();
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] <= x) lo = mid + 1;
        else hi = mid;
    }
    return lo;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> a(n);
    for (auto& v : a) cin >> v;
    while (q--) {
        int l, r;
        cin >> l >> r;
        cout << count_at_most(a, r) - count_at_most(a, l - 1) << '\n';
    }
    return 0;
}
""",
    hints=[
        r"""The number of scores in `[L, R]` is (scores ≤ R) − (scores ≤ L − 1), and "how many are
≤ x" in a sorted array is one binary search.""",
        r"""If your binary search is right and you still get TLE, count what one call of
`count_at_most` does *before* its first line runs. Look at the parameter.""",
        r"""`int count_at_most(const vector<int>& a, int x)`: a reference, so nothing is copied.""",
    ],
    editorial=r"""
The answer to a question is (scores ≤ R) − (scores ≤ L − 1), two binary searches on the
sorted array: O(log n) each.

The trap is in the starter's signature. `vector<int> a` as a parameter makes a fresh copy of
all `n` scores on every call. With two calls per question, that is 2 · 2·10^5 · 5·10^5 =
2·10^11 integers copied, 800 GB of memory traffic. Measured here: about 15 s with the copy,
0.07 s without. The binary search itself is 20 steps.

In Python the same helper costs nothing extra, because a parameter is just another name
for the caller's list. In C++, write `const vector<int>& a`: a reference (no copy) that the
function promises not to modify. That is the default signature for any container or string
a function only reads. (cpp06 introduces `upper_bound`, which does this binary search for
you.)
""",
)

K_DAYS = Problem(
    id="k_days_later",
    title="k Days Later",
    difficulty="easy",
    complexity="O(k) per query",
    statement=r"""
Given a date and a number `k`, print the date `k` days later.

Use the Gregorian calendar for every year. A year is a leap year if it is divisible by 4,
except that a year divisible by 100 is a leap year only if it is also divisible by 400 (so
2000 was a leap year and 1900 was not). February has 29 days in a leap year and 28
otherwise; April, June, September and November have 30 days; the other months have 31.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 1000). Each of the next `t` lines has four integers
`y m d k`: a valid date (year `y`, month `m`, day `d`, with 1 ≤ y ≤ 9000) and
0 ≤ k ≤ 10^4.
""",
    output=r"""
For each line, print the date `k` days later as `y m d`.
""",
    samples=[
        Test("4\n2024 2 28 1\n2023 2 28 1\n2023 12 31 1\n2024 1 31 30\n",
             "2024 2 29\n2023 3 1\n2024 1 1\n2024 3 1\n"),
    ],
    tests=[
        Test("3\n1900 2 28 1\n2000 2 28 1\n2100 2 28 1\n"),
        Test("1\n2024 5 17 0\n"),
        Test(_month_ends()),
        Test("2\n1 1 1 10000\n9000 12 31 10000\n"),
    ],
    gens=[
        Gen("short hops", lambda rng: _days(rng, 50, 400), 10),
        Gen("long hops", lambda rng: _days(rng, 1000, 10000), 2),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

bool is_leap(int y) {
    return (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
}

int days_in_month(int y, int m) {
    switch (m) {
        case 2:
            return is_leap(y) ? 29 : 28;
        case 4: case 6: case 9: case 11:     // stacked labels: fallthrough on purpose
            return 30;
        default:
            return 31;
    }
}

tuple<int, int, int> next_day(int y, int m, int d) {
    if (d < days_in_month(y, m)) return {y, m, d + 1};
    if (m < 12) return {y, m + 1, 1};
    return {y + 1, 1, 1};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int y, m, d, k;
        cin >> y >> m >> d >> k;
        for (int i = 0; i < k; i++) tie(y, m, d) = next_day(y, m, d);   // assign, not declare
        cout << y << ' ' << m << ' ' << d << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// A different method: convert to a day count and back (H. Hinnant's civil-date formulas).
long long days_from_civil(long long y, long long m, long long d) {
    y -= m <= 2;
    long long era = (y >= 0 ? y : y - 399) / 400;
    long long yoe = y - era * 400;
    long long doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
    long long doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + doe - 719468;
}
void civil_from_days(long long z, long long& y, long long& m, long long& d) {
    z += 719468;
    long long era = (z >= 0 ? z : z - 146096) / 146097;
    long long doe = z - era * 146097;
    long long yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    y = yoe + era * 400;
    long long doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    long long mp = (5 * doy + 2) / 153;
    d = doy - (153 * mp + 2) / 5 + 1;
    m = mp < 10 ? mp + 3 : mp - 9;
    y += (m <= 2);
}
int main() {
    int t;
    cin >> t;
    while (t--) {
        long long y, m, d, k;
        cin >> y >> m >> d >> k;
        civil_from_days(days_from_civil(y, m, d) + k, y, m, d);
        cout << y << ' ' << m << ' ' << d << '\n';
    }
}
""",
    hints=[
        r"""Write `int days_in_month(int y, int m)` with a `switch`, and a
`tuple<int, int, int> next_day(int y, int m, int d)`. Then step `k` times.""",
        r"""Inside the loop, `auto [y, m, d] = next_day(y, m, d);` does not compile: it declares
new variables. `tie(y, m, d) = next_day(y, m, d);` assigns to the ones you have.""",
        r"""Test your leap-year function on 1900 (not leap), 2000 (leap) and 2024 (leap).""",
    ],
    editorial=r"""
Split the work into small functions: `is_leap(y)`, `days_in_month(y, m)` (a `switch` with
stacked labels for the 30-day months), and `next_day(y, m, d)`, which returns the three
parts of the new date as a `tuple`. The main loop applies it `k` times:

```cpp
for (int i = 0; i < k; i++) tie(y, m, d) = next_day(y, m, d);
```

`tie` builds a tuple of *references* to `y`, `m`, `d`, so assigning to it assigns to them.
Structured bindings (`auto [y, m, d] = ...`) always declare new variables, which is what
you want when unpacking a result once, and not what you want when updating a state in a
loop.

The places this goes wrong are always the same: a `switch` case without `break` or `return`
falling into the next one, the century rule for leap years, and December 31. The hidden
tests step off the last day of every month in 1900, 2000, 2023 and 2024. At most
10^3 · 10^4 = 10^7 steps, well inside the limit.
""",
)

HANOI = Problem(
    id="tower_of_hanoi",
    title="Tower of Hanoi",
    difficulty="medium",
    source="CSES 2165 - Tower of Hanoi",
    complexity="O(2^n)",
    statement=r"""
There are three stacks, numbered 1, 2 and 3. Stack 1 holds `n` disks of different sizes,
the largest at the bottom and each disk smaller than the one below it. Move all the disks
to stack 3.

A move takes the top disk of one stack and puts it on top of another stack. A disk may
never be placed on a smaller disk. Find a way to do it with the minimum number of moves.
""",
    input=r"""
One integer `n` (1 ≤ n ≤ 16).
""",
    output=r"""
First print `k`, the minimum number of moves. Then print `k` lines, each with two integers
`a b`: move the top disk of stack `a` onto stack `b`.
""",
    samples=[
        Test("2\n", "3\n1 2\n1 3\n2 3\n"),
    ],
    tests=[Test(f"{n}\n") for n in (1, 3, 4, 5, 8, 11, 13, 15, 16)],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

vector<pair<int, int>> moves;

// Move n disks from `from` to `to`, using `via` as the spare stack.
void solve(int n, int from, int to, int via) {
    if (n == 0) return;
    solve(n - 1, from, via, to);      // clear the n-1 smaller disks out of the way
    moves.push_back({from, to});      // the largest disk moves exactly once
    solve(n - 1, via, to, from);      // put the smaller disks back on top of it
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    solve(n, 1, 3, 2);
    cout << moves.size() << '\n';     // 2^n - 1
    for (auto [a, b] : moves) cout << a << ' ' << b << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// The iterative solution: move i goes from peg (i & (i-1)) % 3 to ((i | (i-1)) + 1) % 3
// (pegs 0..2). That carries the tower to peg 2 for odd n and to peg 1 for even n, so
// for even n pegs 1 and 2 are swapped.
int main() {
    int n;
    cin >> n;
    int total = (1 << n) - 1;
    printf("%d\n", total);
    for (int i = 1; i <= total; i++) {
        int a = (i & (i - 1)) % 3, b = ((i | (i - 1)) + 1) % 3;
        if (n % 2 == 0) { if (a) a = 3 - a; if (b) b = 3 - b; }
        printf("%d %d\n", a + 1, b + 1);
    }
}
""",
    hints=[
        r"""The largest disk has to go from stack 1 to stack 3 at some point, and it can only move
when every other disk is out of the way. Where must the other `n − 1` disks be then?""",
        r"""On stack 2. So: move `n − 1` disks from 1 to 2 (using 3 as the spare), move the
largest from 1 to 3, move `n − 1` disks from 2 to 3 (using 1 as the spare). Each "move
`n − 1` disks" is the same problem, smaller.""",
        r"""`void solve(int n, int from, int to, int via)` with base case `n == 0`. Collect the
moves in a `vector<pair<int,int>>` so you can print the count first.""",
    ],
    editorial=r"""
The largest disk must travel from stack 1 to stack 3, and when it moves, all `n − 1`
smaller disks must be on the remaining stack, 2. So any solution contains: move `n − 1`
disks from 1 to 2, move the largest, move `n − 1` disks from 2 to 3. Both halves are the
same problem with one disk fewer and the stacks renamed, which is exactly what a recursive
call with parameters `(n, from, to, via)` expresses.

The count satisfies T(n) = 2·T(n − 1) + 1 with T(0) = 0, so T(n) = 2^n − 1: 65535 moves
for `n = 16`. No solution can do better, because the argument above shows every solution
has this shape. The recursion is only `n` calls deep, but it makes 2^n calls in total, so
the output, not the stack, is the cost.
""",
)

FIB = Problem(
    id="fibonacci_far",
    title="Fibonacci, Far Out",
    difficulty="medium",
    complexity="O(log n) per query",
    statement=r"""
The Fibonacci numbers are `F(0) = 0`, `F(1) = 1` and `F(n) = F(n−1) + F(n−2)`. For each
given `n`, print `F(n) mod (10^9 + 7)`.

`n` goes up to 10^18, so stepping from 0 to `n` is out of the question. Use the doubling
identities, valid for every `k ≥ 0`:

```
F(2k)   = F(k) * (2 F(k+1) - F(k))
F(2k+1) = F(k)^2 + F(k+1)^2
```
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5). Each of the next `t` lines has one integer `n`
(0 ≤ n ≤ 10^18).
""",
    output=r"""
For each `n`, print `F(n) mod (10^9 + 7)` on its own line.
""",
    samples=[
        Test("4\n0\n1\n10\n50\n", "0\n1\n55\n586268941\n"),
        Test("2\n88\n1000000000000000000\n", "665487541\n209783453\n",
             note="If you printed a negative number, some subtraction went below zero "
                  "before a `%`. If you ran out of time, count your recursive calls."),
    ],
    tests=[
        Test("5\n2\n3\n4\n5\n6\n"),
        Test("3\n999999999999999999\n576460752303423487\n576460752303423488\n"),
    ],
    gens=[
        Gen("small n", _fib_small, 10),
        Gen("mixed magnitudes", lambda rng: _fib_mixed(rng, 200), 4),
        Gen("max t, huge n", lambda rng: _fib_huge(rng, 100000), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;

// Returns (F(n), F(n+1)) mod MOD.
pair<long long, long long> fib(long long n) {
    if (n == 0) return {0, 1};
    auto [a, b] = fib(n / 2);                           // ONE call: a = F(k), b = F(k+1)
    long long c = a * ((2 * b - a + MOD) % MOD) % MOD;  // F(2k); + MOD keeps it >= 0
    long long d = (a * a + b * b) % MOD;                // F(2k+1)
    if (n % 2 == 0) return {c, d};
    return {d, (c + d) % MOD};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        long long n;
        cin >> n;
        cout << fib(n).first << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// A different method: [[1,1],[1,0]]^n = [[F(n+1),F(n)],[F(n),F(n-1)]].
typedef long long ll;
const ll M = 1000000007;
struct Mat { ll a, b, c, d; };
Mat mul(const Mat& x, const Mat& y) {
    return {(x.a * y.a + x.b * y.c) % M, (x.a * y.b + x.b * y.d) % M,
            (x.c * y.a + x.d * y.c) % M, (x.c * y.b + x.d * y.d) % M};
}
int main() {
    int t;
    cin >> t;
    while (t--) {
        ll n;
        cin >> n;
        Mat r = {1, 0, 0, 1}, p = {1, 1, 1, 0};
        while (n) {
            if (n & 1) r = mul(r, p);
            p = mul(p, p);
            n >>= 1;
        }
        cout << r.b << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;

pair<long long, long long> fib(long long n) {
    if (n == 0) return {0, 1};
    long long a = fib(n / 2).first;                     // two calls per level:
    long long b = fib(n / 2).second;                    // 2^60 calls for n = 10^18
    long long c = a * ((2 * b - a + MOD) % MOD) % MOD;
    long long d = (a * a + b * b) % MOD;
    if (n % 2 == 0) return {c, d};
    return {d, (c + d) % MOD};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        long long n;
        cin >> n;
        cout << fib(n).first << '\n';
    }
    return 0;
}
""",
    hints=[
        r"""Write `pair<long long, long long> fib(long long n)` that returns `(F(n), F(n+1))`, with
`fib(0) = {0, 1}`. With `k = n / 2`, one recursive call gives `F(k)` and `F(k+1)`.""",
        r"""From `a = F(k)`, `b = F(k+1)` compute `c = F(2k)` and `d = F(2k+1)`. If `n` is even,
return `{c, d}`; if odd, `n = 2k + 1`, so return `{d, c + d}`.""",
        r"""Call `fib(n / 2)` exactly once and unpack it: `auto [a, b] = fib(n / 2);`. Keep every
value in `long long` and reduce mod 10^9 + 7 after each operation; `2b − a` can be
negative, so add `MOD` before taking `%`.""",
    ],
    editorial=r"""
Let `fib(n)` return the pair `(F(n), F(n+1))`. With `k = ⌊n/2⌋`, one recursive call gives
`a = F(k)` and `b = F(k+1)`, and the identities give `c = F(2k)` and `d = F(2k+1)`. If `n`
is even the answer is `(c, d)`; if `n = 2k + 1` it is `(d, c + d)`. Each call halves `n`,
so the recursion is about log₂(10^18) ≈ 60 calls deep, and there is one call per level.

Returning the pair is the whole trick: the two values have to travel together. Writing
`fib(n / 2).first` and `fib(n / 2).second` as two separate calls looks harmless and turns
60 calls into 2^60, because each level doubles the number of calls below it. Unpack one
call with `auto [a, b] = fib(n / 2);`.

The arithmetic has the cpp02 traps. Values are below 10^9 + 7, so products reach 10^18:
`long long`. And `2b − a` is negative whenever `a > 2b` (as residues, that happens all the
time), and C++'s `%` keeps the sign, so write `(2 * b - a + MOD) % MOD`. The second sample
(`n = 88`) is the first small `n` where forgetting this prints a negative number.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp03",
    title="control flow, functions & references",
    track="cpp",
    order=3,
    summary="Parameters are copies (and what that costs), references and const&, returning "
            "several values, switch and the loops Python lacks, lambdas, where variables "
            "live, and recursion.",
    prereqs=["cpp02"],
    tags=["functions", "references", "const&", "pass by value", "pair", "tuple",
          "structured bindings", "switch", "lambda", "globals", "static", "recursion"],
    parts=[
        Part("Arguments are copies", [
            Say(r"""
In Python, a parameter is another name for the caller's object. `def f(lst): lst.append(1)`
changes the caller's list, and passing a list of a million elements costs nothing.

C++ is different. By default a parameter is a **new variable initialised with a copy** of
the argument, whether it is an `int` or a `vector` of a million elements. Functions look
the same as in Python; this one difference is behind a Wrong Answer and a Time Limit
Exceeded that Python programmers hit in their first weeks.
"""),
            Short(r"""
What does this print? (The Python version would print 3.)

```cpp
void add_one(vector<int> v) {
    v.push_back(1);
}

int main() {
    vector<int> a = {5, 6};
    add_one(a);
    cout << a.size() << '\n';
}
```
""", accept=["2"], placeholder="what it prints",
                explain=r"""
`2`. `v` is a copy of `a`; `push_back` grows the copy, and the copy is destroyed when the
function returns. To let a function change the caller's object, take a **reference**:
`void add_one(vector<int>& v)`. The `&` makes `v` another name for `a`, which is what
Python always gives you.
"""),
            MCQ(r"""
The same rule applies to the variable of a range-`for`. Which loop reads `n` numbers into
`a`?

```cpp
vector<int> a(n);
for (auto x : a) cin >> x;     // (1)
for (auto& x : a) cin >> x;    // (2)
```
""", [
                Opt("Both: they differ only in style.",
                    why="`auto x` is a copy of each element. (1) reads every number into a "
                        "temporary copy and throws it away; `a` stays all zeros."),
                Opt("(2) only.", correct=True,
                    why="Right. `auto& x` is the element itself, so `cin >> x` writes into "
                        "`a`. This is why cpp01's reading idiom has the `&`."),
                Opt("(1) only: (2) does not compile, you cannot read into a reference.",
                    why="A reference is just another name for the element; reading into it "
                        "reads into the element."),
            ], explain=r"""
Use `for (auto& x : v)` to modify elements, `for (const auto& x : v)` to read big elements
(strings, inner vectors) without copying them, and `for (auto x : v)` for small values you
only read.
"""),
            Numeric(r"""
Now the cost. A helper `int count_at_most(vector<int> a, int x)` does a binary search,
about 20 steps. `main` calls it twice per query, for 2·10^5 queries, on an array of 5·10^5
`int`s. Roughly how many `int`s are copied in total?
""", answer=2e11, rel=0.5, unit="ints copied",
                hint="Every call copies the whole array before its first line runs.",
                explain=r"""
`2 · 2·10^5 · 5·10^5 = 2·10^11` ints, 800 GB of memory traffic. Measured on this judge: about
15 seconds, against 0.07 s for the same program with the copy removed. The binary searches
themselves are only `4·10^5 · 20 = 8·10^6` steps; the time goes entirely into a line you
cannot see.
"""),
            MCQ(r"""
Which signature should a function that only *reads* a big vector have?
""", [
                Opt("`int f(vector<int> a)`",
                    why="Copies the whole vector on every call: the TLE above."),
                Opt("`int f(vector<int>& a)`",
                    why="No copy, so it is fast. But it tells the reader (and the compiler) "
                        "that `f` may modify `a`, and it refuses temporaries and `const` "
                        "vectors as arguments."),
                Opt("`int f(const vector<int>& a)`", correct=True,
                    why="Yes: no copy, and `a.push_back(1)` inside `f` becomes a compile "
                        "error instead of a silent bug."),
                Opt("`int f(vector<int>* a)`",
                    why="A pointer also avoids the copy, C style, but then every use is "
                        "`(*a)[i]` and callers write `f(&v)`. References exist for this."),
            ], explain=r"""
The rule of thumb: small values (`int`, `long long`, `double`, `char`, a `pair` of ints) by
value; containers and strings by `const&` when read, by `&` when modified.
"""),
            MCQ(r"""
And the other direction: is this return an O(n) copy?

```cpp
vector<int> squares(int n) {
    vector<int> v(n);
    for (int i = 0; i < n; i++) v[i] = i * i;
    return v;
}
```
""", [
                Opt("Yes: `v` is copied into the caller's variable, so return a pointer instead.",
                    why="Returning a pointer to a local is a real bug (the local dies at the "
                        "`return`). And no copy happens here anyway."),
                Opt("No: the compiler builds `v` directly in the caller's variable, or moves "
                    "it, which is O(1).", correct=True,
                    why="Right. Returning a local by value is copy-elided or moved: the vector "
                        "hands over its buffer. Return big results by value freely."),
                Opt("Yes, unless you write `return move(v);`",
                    why="The compiler already treats a returned local as movable, and the "
                        "explicit `move` can even prevent the elision."),
            ]),
            Try("score_brackets", note="The starter has a helper for you to fill in. Before "
                "you submit, look hard at its first parameter."),
        ]),
        Part("Returning several values", [
            Say(r"""
Python returns several values as a tuple: `return q, r`, and `q, r = divmod(a, b)`. C++17
has the same thing with a little more typing:

```cpp
pair<long long, long long> divmod(long long a, long long b) {
    return {a / b, a % b};
}

auto [q, r] = divmod(17, 5);     // structured bindings: q = 3, r = 2
```

A `pair` has `.first` and `.second`; a `tuple<int, int, int>` holds three (or more), read
with `get<0>(t)`. `auto [x, y, z] = ...` unpacks either, and works in range-`for` too:
`for (auto [a, b] : moves)`.
"""),
            Short(r"""
With the `divmod` above, what does this print?

```cpp
auto [q, r] = divmod(-17, 5);
cout << q << ' ' << r << '\n';
```
""", accept=["-3 -2", "−3 −2"], placeholder="what it prints",
                hint="Remember how C++ rounds a negative quotient (cpp02).",
                explain=r"""
`-3 -2`: C++ truncates toward zero, and the remainder takes the sign of `-17`. Python's
`divmod(-17, 5)` is `(-4, 3)`. A function that wraps a language primitive inherits its
rules.
"""),
            MCQ(r"""
You step a date forward `k` times with `tuple<int, int, int> next_day(int y, int m, int d)`,
and write the Python habit:

```cpp
int y = 2024, m = 2, d = 27;
for (int i = 0; i < k; i++) {
    auto [y, m, d] = next_day(y, m, d);
}
```

What happens?
""", [
                Opt("It advances the date by `k` days, like `y, m, d = next_day(y, m, d)` in "
                    "Python.",
                    why="Structured bindings never assign to existing variables; they always "
                        "declare new ones."),
                Opt("It compiles, but the new `y, m, d` vanish at the end of each iteration, "
                    "so the date never moves.",
                    why="A good guess, and it is what happens if you rename the new variables. "
                        "Here GCC does not get that far."),
                Opt("Compile error: the new `y, m, d` are already in scope in their own "
                    "initialiser.", correct=True,
                    why="Right. GCC says \"use of 'y' before deduction of 'auto'\": the "
                        "`y` inside `next_day(y, m, d)` refers to the new, not yet "
                        "initialised variable."),
            ], explain=r"""
To assign a returned pair or tuple to variables you already have, use `tie`:

```cpp
tie(y, m, d) = next_day(y, m, d);
```

`tie` makes a tuple of references, and assigning to it assigns through them. Structured
bindings declare; `tie` assigns.
"""),
        ]),
        Part("Control flow Python does not have", [
            Say(r"""
Three constructs have no exact Python counterpart. `switch` jumps to the `case` matching an
integer or `char`. `do { ... } while (cond);` tests its condition *after* the body. And
`cond ? a : b` is Python's `a if cond else b`.

`switch` has one rule that surprises everyone once: after jumping to a `case`, execution
**keeps going** through the following cases until a `break` or `return`.
"""),
            Short(r"""
What does this print?

```cpp
int m = 4, days = 0;
switch (m) {
    case 2: days = 28;
    case 4: case 6: case 9: case 11: days = 30;
    default: days = 31;
}
cout << days << '\n';
```
""", accept=["31"], placeholder="what it prints",
                explain=r"""
`31`. The jump lands on `case 4`, sets 30, then falls through into `default` and sets 31.
End each case with `break;`, or `return` straight out of a helper function, which is the
cleaner style:

```cpp
int days_in_month(int y, int m) {
    switch (m) {
        case 2: return is_leap(y) ? 29 : 28;
        case 4: case 6: case 9: case 11: return 30;
        default: return 31;
    }
}
```

Stacked labels (`case 4: case 6:`) are the intended use of fallthrough. GCC can warn about
the accidental kind with `-Wimplicit-fallthrough`.
"""),
            Short(r"""
The goal is to stop at the first pair with `i + j == 2`. What does this print?

```cpp
int found = -1;
for (int i = 0; i < 3; i++)
    for (int j = 0; j < 3; j++)
        if (i + j == 2) { found = i * 10 + j; break; }
cout << found << '\n';
```
""", accept=["20"], placeholder="what it prints",
                hint="Which loop does `break` leave?",
                explain=r"""
`20`. `break` leaves only the innermost loop, so the outer loop carries on and `found` is
overwritten by (1, 1) and then (2, 0). Python has the same rule. To stop both loops, put
them in a function (or a lambda) and `return`, or test a flag in the outer loop's
condition: `for (int i = 0; i < 3 && found < 0; i++)`.
"""),
            Short(r"""
A `do/while` runs its body before testing. This counts Collatz steps (halve if even, else
`3n + 1`) until `n` reaches 1. What does it print for `n = 1`?

```cpp
int n = 1, steps = 0;
do {
    n = (n % 2 == 0) ? n / 2 : 3 * n + 1;
    steps++;
} while (n != 1);
cout << steps << '\n';
```
""", accept=["3"], placeholder="what it prints",
                explain=r"""
`3`: the body runs once before the test (1 → 4), and then 4 → 2 → 1. A `while (n != 1)` loop
prints 0. Use `do/while` exactly when the body must run at least once (retry loops,
"generate until valid"); otherwise the plain `while` states the intent.
"""),
            Try("k_days_later", note="A `switch`, a function returning a `tuple`, and `tie` to "
                "update the date in a loop."),
        ]),
        Part("Lambdas: helpers inside main", [
            Say(r"""
A lambda is a function written where you need it, like Python's `lambda` but with a full
body. The brackets say which local variables it can see and how: `[&]` by reference (it
sees later changes and can modify them), `[=]` by copy, taken when the lambda is created.

```cpp
int n, m;
cin >> n >> m;
auto inside = [&](int r, int c) {
    return 0 <= r && r < n && 0 <= c && c < m;
};
if (inside(r + 1, c)) { ... }
```

This is the contest use: a small helper that needs `n`, `m` or a grid from `main`, without
making them global or passing them every time.
"""),
            Short(r"""
What does this print?

```cpp
int k = 1;
auto by_copy = [=](int x) { return x + k; };
auto by_ref  = [&](int x) { return x + k; };
k = 10;
cout << by_copy(5) << ' ' << by_ref(5) << '\n';
```
""", accept=["6 15"], placeholder="what it prints",
                explain=r"""
`6 15`. `[=]` copied `k` (then 1) into the lambda when it was created; `[&]` reads `k` each
time it is called. In contest code `[&]` is the usual choice: the helper sees the current
state, and nothing gets copied.
"""),
            MCQ(r"""
`a` is a `vector<int>` with 10^6 elements. What does this loop cost, apart from the work
inside?

```cpp
for (int qi = 0; qi < q; qi++) {
    auto get = [=](int i) { return a[i]; };
    ...
}
```
""", [
                Opt("Nothing: creating a lambda is free.",
                    why="Creating it runs its captures, and `[=]` means \"copy every local the "
                        "body uses\", here the whole vector."),
                Opt("A copy of all of `a` every iteration: 10^6 · q ints.", correct=True,
                    why="Right: the parameter trap again, hidden in a capture list. `[&]` "
                        "captures a reference instead, O(1)."),
                Opt("A compile error: a lambda cannot capture a vector.",
                    why="It can capture anything; by copy, it copies it."),
            ]),
        ]),
        Part("Where variables live", [
            Say(r"""
A C++ variable lives in one of three places, and the place decides its initial value and
how big it can be:

| where | what goes there | initial value | size limit |
| the stack | locals, parameters | **garbage** (for `int`, arrays) | small: often 8 MB |
| static storage | globals, `static` locals | **zero** | as big as memory |
| the heap | the elements of a `vector`, `string` | whatever the container sets | as big as memory |
"""),
            MCQ(r"""
What does this print?

```cpp
int g[5];

int main() {
    int l[5];
    cout << g[2] << ' ' << l[2] << '\n';
}
```
""", [
                Opt("`0 0`",
                    why="Only `g` is guaranteed zero. `l` is a local array: its elements are "
                        "whatever bytes were on the stack. It may print 0 today and not after "
                        "an unrelated change."),
                Opt("`0`, then an unpredictable value.", correct=True,
                    why="Yes. Globals are zero-initialised; locals are not initialised at "
                        "all, and reading one is undefined behaviour."),
                Opt("Two unpredictable values.",
                    why="Globals and `static` variables are always zero-initialised before "
                        "`main` starts."),
                Opt("A compile error: `l` is used uninitialised.",
                    why="At most a warning (and not always). It compiles and reads garbage."),
            ], explain=r"""
The classic: `int cnt[26];` inside a function, then `cnt[c - 'a']++`. It passes the samples
on your machine and fails on the judge. Write `int cnt[26] = {};` or use
`vector<int> cnt(26)`, both zero-filled.
"""),
            Numeric(r"""
Linux and macOS give the main thread an 8 MB stack by default. About how many `int`s fit in
it?
""", answer=2097152, rel=0.1, unit="ints",
                explain=r"""
8·2^20 / 4 ≈ 2.1·10^6. So `int a[10000000];` (40 MB) *inside* `main` overflows an 8 MB stack
and crashes before your first line runs. Declare big arrays globally, or use a `vector`
(its elements are on the heap).

This site's judge gives the main thread 512 MB of stack, as some contest judges do, so it
would not crash *here*. Your own machine, and judges that keep the default, will; so
contest code keeps the habit.
"""),
            Short(r"""
A `static` local is created once and keeps its value between calls. What does this print?

```cpp
int calls() {
    static int c = 0;      // initialised once, on the first call
    return ++c;
}

int main() {
    calls();
    calls();
    cout << calls() << '\n';
}
```
""", accept=["3"], placeholder="what it prints",
                explain=r"""
`3`. A `static` local is a global that only its function can see: it is zero-initialised,
lives for the whole run, and does not reset between calls. That is also the trap with
globals in multi-test problems: nothing resets them between test cases for you (cpp07).
"""),
        ]),
        Part("Recursion and the call stack", [
            Say(r"""
Recursion in C++ is the same idea as in Python, with two practical differences. There is
no recursion limit of 1000: the only limit is the stack size. And calls are far cheaper
than in Python, so 10^7 of them take well under a second. What does not change is the
number of calls a recursion makes, and that is where recursive solutions go wrong.
"""),
            MCQ(r"""
In Python, recursing too deep raises `RecursionError`. What happens in C++ when a
recursion needs more stack than there is?
""", [
                Opt("A `RecursionError`-style exception you can catch.",
                    why="C++ does not count calls at all. Each call just takes another frame "
                        "from the stack until there is no more."),
                Opt("The program crashes with a segmentation fault: the judge says RE, with "
                    "no message pointing at the recursion.", correct=True,
                    why="Right. Running off the end of the stack is a memory access violation. "
                        "A DFS 10^6 levels deep can do this on an 8 MB stack."),
                Opt("Nothing: `-O2` turns recursion into a loop.",
                    why="GCC can turn some *tail* calls into jumps, but you cannot count on "
                        "it: a DFS that loops over neighbours and recurses into each keeps one "
                        "frame per level."),
                Opt("It gets slower and eventually times out.",
                    why="Depth costs memory, not time. It crashes, usually well within the "
                        "time limit."),
            ]),
            Numeric(r"""
How many calls does `fib(30)` make in total, counting the first one?

```cpp
long long fib(int n) {
    return n < 2 ? n : fib(n - 1) + fib(n - 2);
}
```
""", answer=2692537, rel=0.7, unit="calls",
                hint="calls(n) = 1 + calls(n−1) + calls(n−2), and calls(0) = calls(1) = 1. It "
                     "grows like the Fibonacci numbers themselves; F(30) = 832040.",
                explain=r"""
Exactly 2·F(31) − 1 = 2692537 (a counter in the function agrees). The tree recomputes the
same small values over and over: `fib(28)` is computed twice, `fib(27)` three times, and so
on. For `n = 50` it is about 4·10^10 calls. Storing each answer the first time
(memoisation, cpp07 and algo06) makes it `n` calls.
"""),
            Reflect(r"""
Tower of Hanoi: move `n` disks from stack 1 to stack 3, one at a time, never a larger disk
on a smaller one. Suppose you already know how to move `n − 1` disks between any two
stacks. How do you move `n`, and how many moves does it take in total?
""", answer=r"""
The largest disk must go from 1 to 3 at some point, and at that moment all the others must
be on stack 2. So: move `n − 1` disks from 1 to 2 (using 3 as the spare), move the largest
from 1 to 3, then move `n − 1` disks from 2 to 3 (using 1 as the spare). The moves satisfy
T(n) = 2·T(n − 1) + 1 with T(0) = 0, so T(n) = 2^n − 1. In code, "move `n − 1` disks" is a
recursive call with the stacks renamed: `solve(n, from, to, via)`.
"""),
            Numeric(r"""
How many moves for `n = 16`?
""", answer=65535, unit="moves",
                explain=r"""
2^16 − 1 = 65535. The recursion is only 16 calls deep, but it makes 2^16 − 1 moves, so the
output is the real cost. The stack depth of a recursion and its number of calls are
different quantities; keep both in mind.
"""),
            Try("tower_of_hanoi"),
            Say(r"""
One more recursion, where returning two values is the entire trick. The Fibonacci numbers
satisfy the doubling identities

```
F(2k)   = F(k) * (2 F(k+1) - F(k))
F(2k+1) = F(k)^2 + F(k+1)^2
```

So a function `fib(n)` that returns the *pair* `(F(n), F(n+1))` can get it from
`(F(k), F(k+1))` with `k = n / 2`: one recursive call on half the input.
"""),
            Numeric(r"""
Each call halves `n`. About how deep does the recursion go for `n = 10^18`?
""", answer=60, rel=0.1, unit="levels",
                explain=r"""
log₂(10^18) ≈ 59.8, so 60 levels. A 60-deep recursion with O(1) work per level: about 60
operations for a number no loop could ever count up to.
"""),
            MCQ(r"""
Someone writes the recursive step like this:

```cpp
long long a = fib(n / 2).first;
long long b = fib(n / 2).second;
```

For `n` near 10^18, how many calls does it make?
""", [
                Opt("About 120: twice the depth.",
                    why="Each call makes two calls, each of which makes two more: the count "
                        "doubles at every one of the 60 levels, so it is 2^60, not 2·60."),
                Opt("About 60: the compiler notices the two calls are identical and merges "
                    "them.",
                    why="It would have to prove `fib` has no side effects, and it does not "
                        "memoise for you. This version timed out on this judge for "
                        "`n = 10^18`."),
                Opt("About 2^61 ≈ 2·10^18: every level doubles the number of calls.",
                    correct=True,
                    why="Right. T(n) = 2·T(n/2) + 1 is O(n): the logarithmic algorithm became "
                        "a linear one. Call once and unpack: `auto [a, b] = fib(n / 2);`."),
            ], explain=r"""
This is why the function returns a pair: `F(k)` and `F(k+1)` come out of *one* call and
travel together. A recursion that calls itself twice on half the input is linear; once is
logarithmic.
"""),
            Try("fibonacci_far", note="Return a pair, call once per level, and bring cpp02 "
                "along: products reach 10^18, and `2b − a` can be negative."),
        ]),
    ],
    problems=[BRACKETS, K_DAYS, HANOI, FIB],
    cards=[
        Card(r"""What does a C++ function receive for a parameter declared `vector<int> v`?""",
             r"""A full copy of the argument, made on every call (O(n)). Changes to `v` do not reach the caller."""),
        Card(r"""Signature for a function that only reads a big vector or string?""",
             r"""`const vector<int>& a` (or `const string& s`): no copy, and modifying it is a compile error."""),
        Card(r"""Why does `for (auto x : a) cin >> x;` leave `a` unchanged?""",
             r"""`auto x` is a copy of each element. Write `for (auto& x : a) cin >> x;`."""),
        Card(r"""Is `return v;` of a local `vector` an O(n) copy?""",
             r"""No: it is copy-elided or moved (O(1)). Return big results by value."""),
        Card(r"""How do you return two values and unpack them in C++17?""",
             r"""Return `pair<A, B>` (`return {x, y};`), unpack with `auto [x, y] = f();`. `tuple` for three or more."""),
        Card(r"""How do you assign a returned tuple to variables that already exist?""",
             r"""`tie(y, m, d) = next_day(y, m, d);` Structured bindings always declare new variables."""),
        Card(r"""What happens in a `switch` case without `break`?""",
             r"""Execution falls through into the next case. End cases with `break` or `return`."""),
        Card(r"""How do you leave two nested loops at once?""",
             r"""`break` leaves only the inner loop. Put the loops in a function/lambda and `return`, or check a flag in the outer condition."""),
        Card(r"""Lambda captures `[=]` vs `[&]`?""",
             r"""`[=]` copies the used locals when the lambda is created (a vector is copied!); `[&]` refers to them and sees later changes."""),
        Card(r"""Which variables start at zero, and which hold garbage?""",
             r"""Globals and `static` locals are zero-initialised; local variables and local arrays are not (`int cnt[26] = {};` fixes it)."""),
        Card(r"""Where should a 10^7-element array go, and why?""",
             r"""Global (or a `vector`). A local array lives on the stack, often 8 MB ≈ 2·10^6 ints, and overflows it."""),
        Card(r"""Why is `a = f(n/2).first; b = f(n/2).second;` slow in a halving recursion?""",
             r"""Two calls per level doubles the calls at each of log n levels: O(n) instead of O(log n). Call once: `auto [a, b] = f(n/2);`."""),
    ],
)
