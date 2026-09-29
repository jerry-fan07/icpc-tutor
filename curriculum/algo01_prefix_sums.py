from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _array_queries(rng, n, q, lo, hi, wide):
    a = [rng.randint(lo, hi) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        if wide:                                   # nearly the whole array, every time
            l = rng.randint(1, min(n, 40))
            r = rng.randint(max(l, n - 40), n)
        else:
            l = rng.randint(1, n)
            r = rng.randint(l, n)
        out.append(f"{l} {r}")
    return "\n".join(out) + "\n"


def _updates(rng, n, q, vmax, wide):
    out = [f"{n} {q}"]
    for _ in range(q):
        if wide:
            l = rng.randint(1, min(n, 40))
            r = rng.randint(max(l, n - 40), n)
        else:
            l = rng.randint(1, n)
            r = rng.randint(l, n)
        out.append(f"{l} {r} {rng.randint(-vmax, vmax)}")
    return "\n".join(out) + "\n"


def _forest(rng, n, q, density, wide):
    rows = []
    for _ in range(n):
        bits = rng.getrandbits(n) if density == 0.5 else None
        if bits is not None:
            rows.append("".join("*" if bits >> k & 1 else "." for k in range(n)))
        else:
            rows.append("".join("*" if rng.random() < density else "." for _ in range(n)))
    out = [f"{n} {q}", *rows]
    for _ in range(q):
        if wide:
            y1, x1 = rng.randint(1, 5), rng.randint(1, 5)
            y2, x2 = rng.randint(n - 4, n), rng.randint(n - 4, n)
        else:
            y1, y2 = sorted((rng.randint(1, n), rng.randint(1, n)))
            x1, x2 = sorted((rng.randint(1, n), rng.randint(1, n)))
        out.append(f"{y1} {x1} {y2} {x2}")
    return "\n".join(out) + "\n"


def _divisible(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


# --------------------------------------------------------------------- problems
STATIC_RANGE_SUM = Problem(
    id="static_range_sum",
    title="Static Range Sums",
    difficulty="easy",
    source="CSES 1646 - Static Range Sum Queries",
    complexity="O(n + q)",
    statement=r"""
The rainfall station on Mount Kattis logged one integer per day for `n` days. The
climatologists have `q` questions, each of the form "how much rain fell from day `l` to
day `r`, inclusive?".

Answer every question.
""",
    input=r"""
The first line has two integers `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has `n` integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

Each of the next `q` lines has two integers `l` and `r` (1 ≤ l ≤ r ≤ n).
""",
    output=r"""
For each question, print a_l + a_(l+1) + ... + a_r on its own line.
""",
    samples=[
        Test("8 4\n3 2 4 5 1 1 5 3\n2 4\n5 6\n1 8\n3 3\n", "11\n2\n24\n4\n"),
    ],
    tests=[
        Test("1 1\n1000000000\n1 1\n"),
        Test("3 3\n1000000000 1000000000 1000000000\n1 3\n2 3\n1 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _array_queries(rng, rng.randint(1, 12), rng.randint(1, 12), 1, 20, False), 12),
        Gen("big values", lambda rng: _array_queries(rng, 2000, 2000, 10**9 - 1000, 10**9, False), 2),
        Gen("max size, whole-array queries", lambda rng: _array_queries(rng, 200000, 200000, 1, 10**9, True), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<long long> p(n + 1, 0);           // p[i] = a[1] + ... + a[i], p[0] = 0
    for (int i = 1; i <= n; i++) {
        long long x;
        cin >> x;
        p[i] = p[i - 1] + x;
    }
    while (q--) {
        int l, r;
        cin >> l >> r;
        cout << p[r] - p[l - 1] << '\n';
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
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int l, r;
        cin >> l >> r;
        long long s = 0;
        for (int i = l; i <= r; i++) s += a[i];
        cout << s << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int l, r;
        cin >> l >> r;
        long long s = 0;
        for (int i = l; i <= r; i++) s += a[i];
        cout << s << '\n';
    }
}
""",
    wrong=[r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // an int prefix array: overflows past 2.1e9
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> p(n + 1, 0);
    for (int i = 1; i <= n; i++) { int x; cin >> x; p[i] = p[i - 1] + x; }
    while (q--) { int l, r; cin >> l >> r; cout << p[r] - p[l - 1] << '\n'; }
}
""", r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // p[r] - p[l]: drops a[l]
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<long long> p(n + 1, 0);
    for (int i = 1; i <= n; i++) { long long x; cin >> x; p[i] = p[i - 1] + x; }
    while (q--) { int l, r; cin >> l >> r; cout << p[r] - p[l] << '\n'; }
}
"""],
    hints=[
        r"""Every query re-adds numbers that some earlier work already added. What single array,
computed once, would let you get any range sum with one subtraction?""",
        r"""Let `p[i] = a[1] + ... + a[i]` with `p[0] = 0`. Then the answer is `p[r] - p[l-1]`.
Sums reach 2·10^5 · 10^9 = 2·10^14: use `long long`.""",
    ],
    editorial=r"""
Precompute `p[i] = p[i-1] + a[i]` with `p[0] = 0` in one pass: O(n). The sum of
`a[l..r]` is everything up to `r` minus everything before `l`, so `p[r] - p[l-1]`: O(1)
per query, O(n + q) in total instead of the O(n·q) = 4·10^10 of re-adding each range.

Two things decide whether this is accepted rather than just correct: `p` must be
`long long` (the total can reach 2·10^14, far past the 2.1·10^9 an `int` holds), and
2·10^5 lines of output want `'\n'` rather than `endl`, which flushes every line.
""",
)

RANGE_ADD = Problem(
    id="range_add",
    title="Stage Lights",
    difficulty="easy",
    complexity="O(n + q)",
    statement=r"""
A theatre has `n` spotlights in a row, all starting at brightness 0. During rehearsal
the lighting director issues `q` commands of the form "change the brightness of every
light from `l` to `r` by `v`" (`v` may be negative; brightness may go negative too, the
director is creative).

Print the brightness of every light after all commands.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

Each of the next `q` lines has `l r v` (1 ≤ l ≤ r ≤ n, −10^9 ≤ v ≤ 10^9).
""",
    output=r"""
Print `n` integers on one line: the final brightness of lights 1..n.
""",
    samples=[
        Test("5 3\n1 3 2\n2 5 -1\n3 3 10\n", "2 1 11 -1 -1\n"),
    ],
    tests=[
        Test("1 1\n1 1 -1000000000\n"),
        Test("4 2\n1 4 1000000000\n4 4 1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _updates(rng, rng.randint(1, 10), rng.randint(1, 10), 20, False), 12),
        Gen("large values", lambda rng: _updates(rng, 3000, 3000, 10**9, False), 2),
        Gen("max size, whole-row updates", lambda rng: _updates(rng, 200000, 200000, 10**9, True), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<long long> d(n + 2, 0);           // d[i] = a[i] - a[i-1]
    while (q--) {
        int l, r;
        long long v;
        cin >> l >> r >> v;
        d[l] += v;
        d[r + 1] -= v;                       // r + 1 can be n + 1: hence n + 2 slots
    }
    long long cur = 0;
    for (int i = 1; i <= n; i++) {
        cur += d[i];
        cout << cur << (i == n ? '\n' : ' ');
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
    vector<long long> a(n + 1, 0);
    while (q--) {
        int l, r; long long v;
        cin >> l >> r >> v;
        for (int i = l; i <= r; i++) a[i] += v;
    }
    for (int i = 1; i <= n; i++) cout << a[i] << ' ';
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<long long> a(n + 1, 0);
    while (q--) {
        int l, r; long long v;
        cin >> l >> r >> v;
        for (int i = l; i <= r; i++) a[i] += v;
    }
    for (int i = 1; i <= n; i++) cout << a[i] << ' ';
    cout << '\n';
}
""",
    hints=[
        r"""An update touches up to `n` lights. Can you record it by touching only two numbers,
and recover every light with one pass at the end?""",
        r"""Keep `d[i] = a[i] - a[i-1]`. Adding `v` to `a[l..r]` only changes `d[l]` (up by v) and
`d[r+1]` (down by v). The prefix sums of `d` are `a`.""",
    ],
    editorial=r"""
Store the *differences* `d[i] = a[i] - a[i-1]` instead of the values. Adding `v` to a
whole block `a[l..r]` leaves every difference inside the block unchanged; only the step up
into the block (`d[l] += v`) and the step down out of it (`d[r+1] -= v`) move. After all
updates, `a[i] = d[1] + ... + d[i]`: a prefix sum. O(1) per update, O(n) at the end.

The array needs `n + 2` slots because `r + 1` reaches `n + 1`. Values reach
2·10^5 · 10^9 in absolute value, so `long long` again.
""",
)

FOREST = Problem(
    id="forest_queries",
    title="Forest Queries",
    difficulty="medium",
    source="CSES 1652 - Forest Queries",
    complexity="O(n^2 + q)",
    statement=r"""
A forest is mapped as an `n × n` grid where every cell is either empty (`.`) or a tree
(`*`). Rows are numbered 1..n from top to bottom, columns 1..n from left to right.

Answer `q` questions: how many trees are inside the rectangle with upper-left corner
`(y1, x1)` and lower-right corner `(y2, x2)`?
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n ≤ 1000, 1 ≤ q ≤ 2·10^5).

Then `n` lines of `n` characters each describe the forest.

Each of the next `q` lines has `y1 x1 y2 x2` (1 ≤ y1 ≤ y2 ≤ n, 1 ≤ x1 ≤ x2 ≤ n).
""",
    output=r"""
For each question, print the number of trees in the rectangle.
""",
    samples=[
        Test("4 3\n.*..\n*.**\n**..\n****\n2 2 3 4\n3 1 3 1\n1 1 2 2\n", "3\n1\n2\n"),
    ],
    tests=[
        Test("1 2\n*\n1 1 1 1\n1 1 1 1\n"),
        Test("2 1\n..\n..\n1 1 2 2\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _forest(rng, rng.randint(1, 8), rng.randint(1, 10), 0.4, False), 12),
        Gen("medium random", lambda rng: _forest(rng, 200, 2000, 0.5, False), 2),
        Gen("max size, huge rectangles", lambda rng: _forest(rng, 1000, 200000, 0.5, True), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    // p[i][j] = trees in the rectangle (1,1)..(i,j); row 0 and column 0 stay 0
    vector<vector<int>> p(n + 1, vector<int>(n + 1, 0));
    for (int i = 1; i <= n; i++) {
        string row;
        cin >> row;
        for (int j = 1; j <= n; j++)
            p[i][j] = (row[j - 1] == '*') + p[i - 1][j] + p[i][j - 1] - p[i - 1][j - 1];
    }
    while (q--) {
        int y1, x1, y2, x2;
        cin >> y1 >> x1 >> y2 >> x2;
        cout << p[y2][x2] - p[y1 - 1][x2] - p[y2][x1 - 1] + p[y1 - 1][x1 - 1] << '\n';
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
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    while (q--) {
        int y1, x1, y2, x2;
        cin >> y1 >> x1 >> y2 >> x2;
        int c = 0;
        for (int i = y1; i <= y2; i++)
            for (int j = x1; j <= x2; j++) c += g[i - 1][j - 1] == '*';
        cout << c << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    while (q--) {
        int y1, x1, y2, x2;
        cin >> y1 >> x1 >> y2 >> x2;
        int c = 0;
        for (int i = y1; i <= y2; i++)
            for (int j = x1; j <= x2; j++) c += g[i - 1][j - 1] == '*';
        cout << c << '\n';
    }
}
""",
    hints=[
        r"""Let `p[i][j]` count the trees in the rectangle from `(1,1)` to `(i,j)`. Draw the query
rectangle inside the big rectangle `(1,1)..(y2,x2)`: which two strips do you remove?""",
        r"""Removing the strip above and the strip to the left removes the top-left corner block
twice, so add it back: `p[y2][x2] - p[y1-1][x2] - p[y2][x1-1] + p[y1-1][x1-1]`.""",
    ],
    editorial=r"""
Two-dimensional prefix sums. `p[i][j]` is the number of trees in the rectangle
`(1,1)..(i,j)`, built cell by cell with inclusion-exclusion:

```
p[i][j] = cell(i,j) + p[i-1][j] + p[i][j-1] - p[i-1][j-1]
```

(the block `(1,1)..(i-1,j-1)` is inside both `p[i-1][j]` and `p[i][j-1]`, so it was
counted twice). A query is the same picture in reverse: start from `p[y2][x2]`, remove the
rows above `y1` and the columns left of `x1`, and add back the corner removed twice.
O(n^2) to build, O(1) per query. The brute force costs up to 10^6 per query, 2·10^11 in
all.
""",
)


DIVISIBLE = Problem(
    id="divisible_subarrays",
    title="Divisible Subarrays",
    difficulty="medium",
    source="CSES 1662 - Subarray Divisibility",
    complexity="O(n)",
    statement=r"""
Given an array of `n` integers, count the subarrays (contiguous, non-empty) whose sum is
divisible by `n`.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers a_1, ..., a_n (−10^9 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print one integer: the number of subarrays whose sum is divisible by `n`.
""",
    samples=[
        Test("5\n3 1 2 7 4\n", "1\n"),
        Test("3\n-1 -2 3\n", "3\n", note="The negative values are the point of this sample."),
    ],
    tests=[
        Test("1\n-7\n"),
        Test("4\n4 4 4 4\n"),
        Test("6\n-1 -1 -1 -1 -1 -1\n"),
    ],
    gens=[
        Gen("small, negatives", lambda rng: _divisible(rng, rng.randint(1, 12), -20, 20), 14),
        Gen("mid, huge values", lambda rng: _divisible(rng, 2000, -10**9, 10**9), 2),
        Gen("max size, all equal residues", lambda rng: _divisible(rng, 200000, 200000, 200000), 1, large=True),
        Gen("max size, random", lambda rng: _divisible(rng, 200000, -10**9, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> cnt(n, 0);             // cnt[r] = prefixes seen with residue r
    cnt[0] = 1;                              // the empty prefix p[0] = 0
    long long pre = 0, ans = 0;
    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;
        pre = ((pre + x) % n + n) % n;       // C++ % keeps the sign: force it into [0, n)
        ans += cnt[pre];                     // every earlier equal residue closes a subarray
        cnt[pre]++;
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
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;
    long long ans = 0;
    for (int l = 0; l < n; l++) {
        long long s = 0;
        for (int r = l; r < n; r++) {
            s += a[r];
            if (s % n == 0) ans++;
        }
    }
    cout << ans << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> a(n);
    for (auto& x : a) cin >> x;
    long long ans = 0;
    for (int l = 0; l < n; l++) {
        long long s = 0;
        for (int r = l; r < n; r++) {
            s += a[r];
            if (s % n == 0) ans++;
        }
    }
    cout << ans << '\n';
}
""",
    wrong=[r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // no fix for C++'s negative remainders
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    map<long long, long long> cnt;
    cnt[0] = 1;
    long long pre = 0, ans = 0;
    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;
        pre = (pre + x) % n;
        ans += cnt[pre];
        cnt[pre]++;
    }
    cout << ans << '\n';
}
"""],
    hints=[
        r"""The sum of `a[l..r]` is `p[r] - p[l-1]`. When is a difference divisible by `n`?""",
        r"""Exactly when `p[r]` and `p[l-1]` leave the same remainder mod `n`. So count pairs of
prefixes (including `p[0] = 0`) with equal remainders.""",
        r"""In C++ `-7 % 5 == -2`, not 3. Normalise every remainder with `((x % n) + n) % n`, or
equal residues will land in different buckets (and negative indices will crash).""",
    ],
    editorial=r"""
A subarray sum is `p[r] - p[l-1]`, and it is divisible by `n` exactly when
`p[r] ≡ p[l-1] (mod n)`. So the answer is the number of pairs of equal residues among
`p[0], p[1], ..., p[n]`. Walk left to right, keeping how many prefixes so far have each
residue; the current prefix pairs with all of them. O(n).

The trap is the sign of `%` in C++: it truncates toward zero, so `-7 % 5 == -2`. Without
the `((x % n) + n) % n` fix, a prefix of −2 and a prefix of 3 (both ≡ 3 mod 5) land in
different buckets, and `cnt[-2]` is an out-of-bounds write. The answer can reach
n(n+1)/2 ≈ 2·10^10: `long long`.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo01",
    title="prefix sums & difference arrays",
    track="algo",
    order=1,
    summary="Answer a million range questions by paying once up front: prefix sums, "
            "difference arrays, the 2D version, and when the trick works at all.",
    prereqs=["cpp08"],
    tags=["prefix sums", "difference array", "2d prefix", "hashing prefixes", "modular residues"],
    parts=[
        Part("A question asked 200,000 times", [
            Say(r"""
Here is the kind of problem that opens many contest sets.

You get an array `a` of `n` integers and `q` queries. Each query names a range `[l, r]`
and asks for `a[l] + a[l+1] + ... + a[r]`. The limits: `n, q ≤ 2·10^5`, one second.

The first program anyone writes loops from `l` to `r` for every query and adds. It is
obviously correct. The question is whether it is fast enough, and in contests that
question comes *before* you write any code.
"""),
            Numeric(r"""
In the worst case every query covers the whole array. With `n = q = 2·10^5`, roughly
how many additions does the loop-per-query program do in total?
""", answer=4e10, rel=0.5, unit="additions",
                hint="Each query costs up to `n`. There are `q` queries.",
                explain=r"""
`q · n = 2·10^5 · 2·10^5 = 4·10^10`. (If you said half that for the average query, the
grader let it through: the order of magnitude is what matters.)
"""),
            MCQ(r"""
A judge machine does roughly 10^8 to 10^9 simple operations per second. Does
4·10^10 additions fit in one second?
""", [
                Opt("Yes, comfortably: C++ is fast.",
                    why="C++ is fast, but not 40 times faster than the fastest estimate of "
                        "a machine. 4·10^10 / 10^9 = 40 seconds at the very best."),
                Opt("Yes, if I add fast I/O.",
                    why="Fast I/O fixes reading and printing, which here is only 6·10^5 numbers. "
                        "The additions are the problem, and I/O tricks do not touch them."),
                Opt("No: it is off by a factor of roughly 40 to 400.", correct=True,
                    why="Right. No constant-factor trick recovers two orders of magnitude; the "
                        "algorithm has to change."),
                Opt("It depends on the test data.",
                    why="The limits allow the worst case, and judges include it. Assume every "
                        "query spans the whole array."),
            ], explain=r"""
This is the habit the whole algorithms track leans on: estimate the operation count from
the limits, compare it with ~10^8 per second, and only then choose an approach. (cpp08
drilled this; here it bites.)
"""),
            Reflect(r"""
Look at two consecutive queries, `[2, 7]` and `[2, 8]`. What does the brute force do
twice? Say it in one sentence, as generally as you can.
""", answer=r"""
It re-adds `a[2..7]`: the second answer is just the first plus `a[8]`, but the loop
starts from scratch. In general, different queries overlap, and every query re-adds
numbers that were already added before. The waste is the overlap, so the fix is to add
each number once and *reuse* the running totals.
"""),
        ]),
        Part("Stop re-adding", [
            Say(r"""
So we want to pay for the additions once, up front, and then answer each query by
combining a few precomputed numbers. The question is *which* numbers to precompute.
"""),
            MCQ(r"""
Which quantity, if you had it for every index, would give any range sum in O(1)?
""", [
                Opt("The sum of every range `[l, r]`, in a table.",
                    why="It would answer queries instantly, but there are n(n+1)/2 ≈ 2·10^10 "
                        "ranges. Building the table costs as much as the brute force."),
                Opt("The sum of the first `i` elements, for every `i`.", correct=True,
                    why="Yes. Two of these, subtracted, give any range, and there are only n "
                        "of them."),
                Opt("The largest element among the first `i`.",
                    why="A maximum cannot be 'subtracted': knowing the max of a prefix tells "
                        "you nothing about a range inside it. Sums have an inverse; max does not."),
                Opt("The sum of each block of about √n elements.",
                    why="That is a real technique (square-root decomposition) and it gives "
                        "O(√n) per query, far better than O(n). But it is not O(1): a range "
                        "still has partial blocks at its ends."),
            ], explain=r"""
Define the **prefix sum** `p[i] = a[1] + a[2] + ... + a[i]`, with `p[0] = 0`. The sum of
`a[l..r]` is "everything up to r" minus "everything before l":

```
sum(l, r) = p[r] - p[l-1]
```
"""),
            Short(r"""
Take `a = [3, 1, 4, 1, 5, 9]` (1-indexed), so `p = [0, 3, 4, 8, 9, 14, 23]` for
`p[0..6]`. Using only `p`, what is `a[3] + a[4] + a[5]`?
""", accept=["10"], placeholder="a number",
                hint="Which two entries of `p` subtract to leave exactly positions 3 to 5?",
                explain=r"""
`p[5] - p[2] = 14 - 4 = 10`, and indeed `4 + 1 + 5 = 10`. `p[5]` holds `a[1..5]`; taking
away `p[2]` removes `a[1..2]`, leaving `a[3..5]`.
"""),
            MCQ(r"""
Why is it `p[r] - p[l-1]` and not `p[r] - p[l]`?
""", [
                Opt("`p[r] - p[l]` would drop `a[l]`: it covers `a[l+1..r]`.", correct=True,
                    why="Yes. `p[l]` includes `a[l]` itself, so subtracting it removes one "
                        "element too many."),
                Opt("Because the array is 1-indexed; with 0-indexing it would be `p[r] - p[l]`.",
                    why="Indexing shifts every subscript, but the off-by-one survives: with "
                        "0-indexed `a` and `p[i] = a[0] + ... + a[i-1]`, the sum of `a[l..r]` "
                        "is `p[r+1] - p[l]`. You still subtract the prefix that *ends just "
                        "before* `l`."),
                Opt("It is a convention; both work.",
                    why="Try it on the example: `p[5] - p[3] = 14 - 8 = 6 = a[4] + a[5]`. "
                        "`a[3]` went missing."),
            ], explain=r"""
Say it in words and the index writes itself: *the prefix that ends at r, minus the prefix
that ends just before l*.
"""),
            MCQ(r"""
Why keep `p[0] = 0` (so `p` has `n + 1` entries) instead of starting at `p[1] = a[1]`?
""", [
                Opt("So a query with `l = 1` needs no special case: `p[r] - p[0] = p[r]`.",
                    correct=True,
                    why="Exactly. The sentinel `p[0] = 0` is 'the sum of nothing', and it makes "
                        "the formula hold for every `l`."),
                Opt("Because C++ vectors must start at index 0.",
                    why="They do start at 0, but you could store `p[1..n]` at indices 0..n-1. "
                        "The real reason is the `l = 1` case."),
                Opt("To make the array one longer, which avoids overflow.",
                    why="Length has nothing to do with overflow; the type does (we get to that)."),
            ], explain=r"""
Sentinels like `p[0] = 0` appear all over contest code: they turn edge cases into
ordinary cases, and edge cases are where bugs live.
"""),
            Numeric(r"""
With prefix sums, how many additions and subtractions does the whole program do now:
building `p` plus answering all `q` queries? Take `n = q = 2·10^5`.
""", answer=4e5, rel=0.5, unit="operations",
                explain=r"""
`n` additions to build `p`, one subtraction per query: `n + q = 4·10^5`. From 4·10^10
down to 4·10^5, a factor of 100,000. Nothing about the machine changed; the work just
stopped repeating itself.
"""),
        ]),
        Part("Getting it accepted in C++", [
            Say(r"""
Here is the whole program. Read it line by line before the questions.

```cpp
int n, q;
cin >> n >> q;
vector<long long> p(n + 1, 0);
for (int i = 1; i <= n; i++) {
    long long x;
    cin >> x;
    p[i] = p[i - 1] + x;
}
while (q--) {
    int l, r;
    cin >> l >> r;
    cout << p[r] - p[l - 1] << '\n';
}
```
"""),
            Numeric(r"""
With `n = 2·10^5` and every `a[i]` up to `10^9`, how large can `p[n]` get?
""", answer=2e14, rel=0.1,
                explain=r"""
`2·10^5 · 10^9 = 2·10^14`. An `int` stops at 2^31 − 1 ≈ 2.1·10^9, so an `int` prefix array
would silently overflow on big tests and print garbage. `long long` goes to ≈ 9.2·10^18.
"""),
            MCQ(r"""
The loop prints 2·10^5 lines. What goes wrong if `'\n'` is replaced by `endl`?
""", [
                Opt("Nothing; they are the same.",
                    why="They print the same character, but `endl` also *flushes* the output "
                        "buffer: a system call per line."),
                Opt("It may be several times slower, because `endl` flushes every line.",
                    correct=True,
                    why="Right. With hundreds of thousands of lines, flushing each one can cost "
                        "more than the whole algorithm. Use `'\\n'` and let the buffer flush once."),
                Opt("It prints Windows line endings, which the judge rejects.",
                    why="`endl` prints `'\\n'` on every platform; judges also ignore trailing "
                        "whitespace differences in most problems."),
            ]),
            Reflect(r"""
Before you code it: which of these bugs would the four sample tests of a typical problem
catch, and which would only show up on the big hidden tests? (1) using `p[l]` instead of
`p[l-1]`; (2) an `int` prefix array; (3) `endl` instead of `'\n'`.
""", answer=r"""
(1) shows up on almost any sample: the answer is simply wrong. (2) and (3) usually pass
the samples, which are small, and fail only on the large hidden tests: (2) as Wrong Answer
once sums pass 2.1·10^9, (3) as Time Limit Exceeded. That is why you check types and I/O
against the *limits*, not against the samples.
"""),
            Try("static_range_sum", note="Prefix sums, `long long`, fast output. The hidden tests "
                "include the worst case."),
        ]),
        Part("Running it backwards: difference arrays", [
            Say(r"""
Now flip the problem. Instead of many range *questions* on a fixed array, you get many
range *updates*: "add `v` to every `a[l..r]`", `q` of them, and only at the end must you
print the final array. Same limits: `n, q ≤ 2·10^5`.

The direct approach loops over `[l, r]` for each update, and you already know what that
costs: up to 4·10^10 operations.
"""),
            Reflect(r"""
Prefix sums turned a range *query* into two point lookups. What could you store so that a
range *update* becomes two point updates? Think about what the update does to neighbouring
elements.
""", answer=r"""
Store the differences between neighbours, `d[i] = a[i] - a[i-1]`. Adding `v` to all of
`a[l..r]` does not change any difference *inside* the block, because both neighbours moved
together. Only two differences change: the step up into the block, `d[l] += v`, and the
step down out of it, `d[r+1] -= v`. At the end, `a` is recovered as the prefix sums of `d`.
"""),
            Short(r"""
Let `n = 5` and start with `d[1..6]` all zero. Apply "+3 on `[2, 4]`". Write `d[1..6]`,
separated by spaces.
""", accept=["0 3 0 0 -3 0"], placeholder="six numbers",
                explain=r"""
`d[2] += 3` and `d[5] -= 3`: `0 3 0 0 -3 0`. Prefix sums give `a[1..5] = 0 3 3 3 0`, which
is exactly `+3` on positions 2 through 4.
"""),
            MCQ(r"""
Why does `d` need a slot at index `n + 1`?
""", [
                Opt("An update with `r = n` writes `d[r+1] = d[n+1]`.", correct=True,
                    why="Yes. You can either allocate `n + 2` slots or skip the write when "
                        "`r == n`; the extra slot is simpler and cannot be forgotten."),
                Opt("Because prefix sums need `p[0] = 0` at the front.",
                    why="That is the front of the array. The extra slot here is at the back, "
                        "for the 'step down' after the last light."),
                Opt("It does not; `d[n+1]` is never used.",
                    why="It is written whenever `r = n`. Writing past the end of a `vector` is "
                        "undefined behaviour: sometimes a crash, sometimes silent corruption."),
            ]),
            MCQ(r"""
Suppose queries "what is the sum of `a[l..r]` right now?" are mixed in between the
updates. Does the difference array still give O(1) per operation?
""", [
                Opt("Yes: keep a prefix array of `d` too.",
                    why="That prefix array goes stale after every update, and rebuilding it is "
                        "O(n). The trick works only when all updates come before all reads."),
                Opt("No: difference arrays only work *offline*, when every update comes before "
                    "every read.", correct=True,
                    why="Right. Mixing updates and queries online needs a structure that "
                        "supports both in O(log n): a Fenwick or segment tree (algo15, algo16)."),
                Opt("Yes, if you process the queries in sorted order.",
                    why="Reordering would change the answers: a query must see exactly the "
                        "updates that came before it."),
            ], explain=r"""
Keep this distinction; it comes back constantly. **Offline**: all the input is known before
you answer, so you can reorder or batch. **Online**: each answer must be given before the
next operation. Prefix sums and difference arrays are offline tools.
"""),
            Try("range_add", note="Difference array, `n + 2` slots, one pass at the end."),
        ]),
        Part("Two dimensions", [
            Say(r"""
The same idea works on a grid. Let `p[i][j]` be the sum of the rectangle with corners
`(1, 1)` and `(i, j)`. Row 0 and column 0 are all zeros (the 2D version of the sentinel).

To get the sum of an arbitrary rectangle `(r1, c1)..(r2, c2)`, start from the big
rectangle `p[r2][c2]` and cut away what does not belong: the rows above `r1` and the
columns left of `c1`.
"""),
            MCQ(r"""
Which formula gives the sum of the rectangle `(r1, c1)..(r2, c2)`?
""", [
                Opt("`p[r2][c2] - p[r1-1][c2] - p[r2][c1-1]`",
                    why="The block above-and-left of the rectangle, `(1,1)..(r1-1, c1-1)`, is "
                        "inside *both* strips you subtracted, so it was removed twice."),
                Opt("`p[r2][c2] - p[r1-1][c2] - p[r2][c1-1] + p[r1-1][c1-1]`", correct=True,
                    why="Yes: inclusion-exclusion. Two strips out, the doubly-removed corner "
                        "back in."),
                Opt("`p[r2][c2] - p[r1][c1]`",
                    why="That treats the grid like a 1D array. Draw it: `p[r1][c1]` is a "
                        "rectangle in the corner, and the strips above and left of the query "
                        "are not removed."),
                Opt("`(p[r2][c2] - p[r1-1][c2]) * (p[r2][c2] - p[r2][c1-1])`",
                    why="Sums of areas are not products of row sums and column sums."),
            ]),
            Short(r"""
Building `p` uses the same picture. Fill in the blank:
`p[i][j] = a[i][j] + p[i-1][j] + p[i][j-1] - ____`
""", accept=["p[i-1][j-1]", "p[i - 1][j - 1]"], placeholder="an entry of p",
                explain=r"""
`p[i-1][j]` and `p[i][j-1]` overlap in the block `(1,1)..(i-1, j-1)`, counted twice, so
subtract `p[i-1][j-1]` once. Build row by row, left to right, and every entry you need is
already there.
"""),
            Numeric(r"""
For an `n × n` grid with `n = 1000` and `q = 2·10^5` rectangle queries, how many cell
visits would the brute force make in the worst case (every query is the whole grid)?
""", answer=2e11, rel=0.5, unit="cell visits",
                explain=r"""
`q · n^2 = 2·10^5 · 10^6 = 2·10^11`. With 2D prefix sums it is 10^6 to build and four
lookups per query.
"""),
            Try("forest_queries"),
        ]),
        Part("Why it works, and when it does not", [
            MCQ(r"""
Could "prefix maximums" answer "what is the largest `a[i]` for `l ≤ i ≤ r`?" in O(1), the
way prefix sums answer range sums?
""", [
                Opt("Yes: `max(l..r) = pmax[r] - pmax[l-1]`.",
                    why="Subtraction undoes addition, but nothing undoes a max. If `pmax[r] = 9` "
                        "because of `a[1] = 9`, no operation with `pmax[l-1]` tells you the max "
                        "of `a[l..r]`."),
                Opt("No: max has no inverse, so a prefix cannot be 'removed'.", correct=True,
                    why="Right. Range max needs a different structure: a sparse table (O(1) "
                        "queries after O(n log n) preprocessing, algo15) or a segment tree (algo16)."),
                Opt("Only if the array is sorted.",
                    why="On a sorted array the answer is simply `a[r]`, no prefix needed; that "
                        "does not help the general case."),
            ]),
            Reflect(r"""
What property of `+` is the prefix trick really using? State it so that it would tell you,
for a new operation, whether "prefix something" works.
""", answer=r"""
The operation must be associative (so a running total makes sense) and invertible (so the
prefix before `l` can be *removed* from the prefix up to `r`). Addition works, and so does
XOR, which is its own inverse, and multiplication as long as nothing is zero (mod a prime:
with modular inverses). Max, min and gcd are associative but not invertible, so they need
other structures.
"""),
            Short(r"""
With prefix XORs `px[i] = a[1] ^ ... ^ a[i]` and `a = [5, 3, 6]`, what is `a[2] ^ a[3]`?
Compute it as `px[3] ^ px[1]`.
""", accept=["5"], placeholder="a number",
                explain=r"""
`px = [0, 5, 6, 0]`, so `px[3] ^ px[1] = 0 ^ 5 = 5`. Check directly: `3 ^ 6 = 011 ^ 110 =
101 = 5`. XOR undoes itself, which plays the role of subtraction.
"""),
            Say(r"""
One more twist, and it is the most useful one. Instead of *computing* range sums, count
them. How many subarrays have a sum divisible by `m`?

The sum of `a[l..r]` is `p[r] - p[l-1]`, and a difference is divisible by `m` exactly
when both numbers leave the *same remainder* mod `m`. So a question about O(n^2)
subarrays becomes a question about pairs among `n + 1` prefix remainders.
"""),
            Numeric(r"""
For `a = [3, 1, 2, 7, 4]` and `m = 5`, the prefix sums `p[0..5]` are `0, 3, 4, 6, 13, 17`,
with remainders `0, 3, 4, 1, 3, 2`. How many subarrays have a sum divisible by 5?
""", answer=1,
                hint="Count pairs of equal remainders.",
                explain=r"""
Only remainder 3 repeats (at `p[1]` and `p[4]`), one pair, so one subarray: `a[2..4] = 1 +
2 + 7 = 10`. In general each remainder seen `c` times contributes `c(c-1)/2` pairs; or walk
left to right adding "how many earlier prefixes share my remainder".
"""),
            Short(r"""
Negative numbers make this trickier in C++. What does `cout << -7 % 5;` print?
""", accept=["-2"], placeholder="what C++ prints",
                explain=r"""
C++ division truncates toward zero, so `-7 / 5 == -1` and `-7 % 5 == -2`. (Python floors,
giving 3.) Two prefixes with remainders `-2` and `3` are congruent mod 5, but they land in
different buckets, and `cnt[-2]` writes out of bounds. The fix is `((x % m) + m) % m`,
which is always in `[0, m)`.
"""),
            MCQ(r"""
Counting subarrays with sum exactly `k` (not divisibility), with negative numbers
allowed. Which approach is right?
""", [
                Opt("Sliding window: grow the right end, shrink the left while the sum is too big.",
                    why="A window only works when extending it never decreases the sum, i.e. no "
                        "negative numbers. With negatives, shrinking can make the sum *larger*."),
                Opt("Prefix sums plus a hash map: for each `r`, add the number of earlier "
                    "prefixes equal to `p[r] - k`.", correct=True,
                    why="Yes. `p[r] - p[l-1] = k` means `p[l-1] = p[r] - k`: a lookup, not a "
                        "search. O(n) expected."),
                Opt("Sort the array, then use two pointers.",
                    why="Sorting destroys which elements are contiguous, and subarrays are all "
                        "about contiguity."),
            ], explain=r"""
This is the general pattern behind half of this lesson: rewrite a condition on a range as a
condition on *two prefixes*, then count or search among prefixes instead of ranges.
"""),
            Try("divisible_subarrays", note="Prefix remainders, the C++ negative-modulo trap, and a "
                "`long long` answer (it can reach about 2·10^10)."),
        ]),
    ],
    problems=[STATIC_RANGE_SUM, RANGE_ADD, FOREST, DIVISIBLE],
    cards=[
        Card(r"""With prefix sums `p[i] = a[1] + ... + a[i]` and `p[0] = 0`, what is the sum of `a[l..r]`?""",
             r"""`p[r] - p[l-1]`: the prefix ending at `r` minus the prefix ending just before `l`."""),
        Card(r"""Why do prefix-sum arrays keep a sentinel `p[0] = 0`?""",
             r"""So `l = 1` needs no special case: `p[r] - p[0] = p[r]`."""),
        Card(r"""How do you add `v` to all of `a[l..r]` in O(1) with a difference array?""",
             r"""`d[l] += v; d[r+1] -= v;` then prefix-sum `d` once at the end to recover `a`. Allocate `n + 2` slots."""),
        Card(r"""When do difference arrays stop working?""",
             r"""When reads are interleaved with updates (online). They are offline: all updates, then one O(n) pass. Online needs a Fenwick/segment tree."""),
        Card(r"""2D prefix sums: sum of the rectangle `(r1,c1)..(r2,c2)`?""",
             r"""`p[r2][c2] - p[r1-1][c2] - p[r2][c1-1] + p[r1-1][c1-1]` (the corner was subtracted twice)."""),
        Card(r"""2D prefix sums: how is `p[i][j]` built?""",
             r"""`p[i][j] = a[i][j] + p[i-1][j] + p[i][j-1] - p[i-1][j-1]`."""),
        Card(r"""Which operations support the prefix trick, and which do not?""",
             r"""It needs an associative, invertible operation: `+`, XOR, `*` (no zeros / mod prime). Not max, min, gcd: those need sparse tables or segment trees."""),
        Card(r"""Count subarrays with sum exactly `k` when values can be negative?""",
             r"""Prefix sums + hash map of counts: for each `r`, `ans += cnt[p[r] - k]`, then `cnt[p[r]]++`, starting with `cnt[0] = 1`."""),
        Card(r"""Count subarrays whose sum is divisible by `m`?""",
             r"""Count pairs of prefixes (including `p[0] = 0`) with equal remainder mod `m`: `c(c-1)/2` per remainder."""),
        Card(r"""What is `-7 % 5` in C++, and how do you get a remainder in `[0, m)`?""",
             r"""`-2` (C++ truncates toward zero). Use `((x % m) + m) % m`."""),
    ],
)
