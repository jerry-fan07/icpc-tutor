from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _coins(rng, n, x, lo, hi, parity=None):
    pool = list(range(lo, hi + 1))
    if parity is not None:
        pool = [v for v in pool if v % 2 == parity]
    c = rng.sample(pool, min(n, len(pool)))
    return f"{len(c)} {x}\n" + " ".join(map(str, c)) + "\n"


def _grid_random(rng, n, density):
    rows = []
    for i in range(n):
        rows.append("".join("*" if rng.random() < density else "." for _ in range(n)))
    return f"{n}\n" + "\n".join(rows) + "\n"


def _grid_sparse(rng, n, traps):
    g = [["."] * n for _ in range(n)]
    for _ in range(traps):
        i, j = rng.randrange(n), rng.randrange(n)
        if (i, j) not in ((0, 0), (n - 1, n - 1)):
            g[i][j] = "*"
    return f"{n}\n" + "\n".join("".join(r) for r in g) + "\n"


# --------------------------------------------------------------------- problems
DICE = Problem(
    id="dice_combinations",
    title="Dice Combinations",
    difficulty="easy",
    source="CSES 1633 - Dice Combinations",
    complexity="O(6n)",
    statement=r"""
You throw an ordinary die (faces 1 to 6) as many times as you like and add up the results.
Count the ways to reach a total of exactly `n`.

Two ways are different if their sequences of throws differ, so `1 + 2` and `2 + 1` are two
ways, and `3` on its own is a third.
""",
    input=r"""
One integer `n` (1 ≤ n ≤ 10^6).
""",
    output=r"""
The number of ways, modulo 10^9 + 7.
""",
    samples=[
        Test("3\n", "4\n"),
        Test("7\n", "63\n", note="Not 64: no single throw shows 7."),
    ],
    tests=[
        Test("1\n"),
        Test("2\n"),
        Test("6\n"),
    ],
    gens=[
        Gen("small n", lambda rng: f"{rng.randint(1, 20)}\n", 12),
        Gen("needs the modulus", lambda rng: f"{rng.randint(60, 5000)}\n", 2, large=True),
        Gen("max n", lambda rng: f"{rng.randint(999000, 1000000)}\n", 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int MOD = 1'000'000'007;
    int n;
    cin >> n;
    // dp[s] = number of ordered sequences of throws (each 1..6) with total exactly s
    vector<int> dp(n + 1, 0);
    dp[0] = 1;                                   // the empty sequence
    for (int s = 1; s <= n; s++)
        for (int k = 1; k <= 6 && k <= s; k++) { // classify by the last throw, k
            dp[s] += dp[s - k];                  // both terms < MOD: the sum fits in int
            if (dp[s] >= MOD) dp[s] -= MOD;
        }
    cout << dp[n] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
long long ways(int s) {
    if (s == 0) return 1;
    long long t = 0;
    for (int k = 1; k <= 6 && k <= s; k++) t += ways(s - k);
    return t;
}
int main() {
    int n;
    cin >> n;
    cout << ways(n) % 1000000007 << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
long long ways(int s) {
    if (s == 0) return 1;
    long long t = 0;
    for (int k = 1; k <= 6 && k <= s; k++) t += ways(s - k);
    return t % MOD;
}
int main() {
    int n;
    cin >> n;
    cout << ways(n) << '\n';
}
""",
    hints=[
        r"""Classify the sequences with total `s` by their last throw `k`. What is left before it?""",
        r"""`dp[s] = dp[s-1] + dp[s-2] + ... + dp[s-6]` (only the terms with `s - k ≥ 0`), with
`dp[0] = 1`. Fill `s = 1, 2, ..., n` in that order.""",
        r"""Reduce modulo 10^9 + 7 after every addition. Six values below 10^9 + 7 add up to
about 6·10^9, which does not fit in an `int`.""",
    ],
    editorial=r"""
Let `dp[s]` be the number of ordered sequences of throws with total exactly `s`. Every such
sequence (for `s ≥ 1`) has a last throw `k` in 1..6, and removing it leaves a sequence with
total `s − k`; different `k` give different sequences, so

```
dp[s] = dp[s-1] + dp[s-2] + ... + dp[s-6]      (terms with s - k >= 0)
dp[0] = 1                                        (the empty sequence)
```

Each entry reads only smaller indices, so filling `s = 1..n` in increasing order works.
`n + 1` states, 6 transitions each: 6·10^6 operations.

The plain recursion computes the same values, but it recomputes `ways(t)` once for every
sequence of throws that leaves `t`, and that is exponential: about 7.8·10^14 calls already
for `n = 50`. The traps: reduce modulo 10^9 + 7 as you add (the sum of six residues
overflows `int`), and do not index `dp[s - k]` with `s - k < 0`.
""",
)

MIN_COINS = Problem(
    id="minimizing_coins",
    title="Minimizing Coins",
    difficulty="easy",
    source="CSES 1634 - Minimizing Coins",
    complexity="O(n·x)",
    statement=r"""
A coin system has `n` different coin values, and you have as many coins of each value as
you like. Pay exactly `x` using as few coins as possible.
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 100, 1 ≤ x ≤ 10^6).

The second line has `n` distinct integers c_1, ..., c_n (1 ≤ c_i ≤ 10^6).
""",
    output=r"""
The minimum number of coins, or `-1` if the sum `x` cannot be made.
""",
    samples=[
        Test("3 11\n1 5 7\n", "3\n"),
        Test("3 6\n1 3 4\n", "2\n",
             note="Taking the largest coin that fits gives 4 + 1 + 1, three coins. 3 + 3 is two."),
    ],
    tests=[
        Test("2 7\n2 4\n"),
        Test("1 1\n1\n"),
        Test("1 5\n7\n"),
        Test("2 11\n3 5\n"),
        Test("2 1000000\n1 1000000\n"),
        Test("1 1000000\n1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _coins(rng, rng.randint(1, 4), rng.randint(1, 40), 1, 15), 15),
        Gen("small, no coin 1", lambda rng: _coins(rng, rng.randint(1, 3), rng.randint(1, 40), 2, 12), 8),
        Gen("max size, coins up to 1000", lambda rng: _coins(rng, 100, 10**6, 1, 1000), 1, large=True),
        Gen("max size, small coins", lambda rng: _coins(rng, 100, rng.randint(999000, 10**6), 1, 150), 1, large=True),
        Gen("max size, impossible", lambda rng: _coins(rng, 100, 999999, 2, 2000, parity=0), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, x;
    cin >> n >> x;
    vector<int> c(n);
    for (auto& v : c) cin >> v;
    const int INF = 1e9;                     // INF + 1 still fits in an int
    // dp[s] = fewest coins with total exactly s (INF if impossible)
    vector<int> dp(x + 1, INF);
    dp[0] = 0;
    for (int s = 1; s <= x; s++)
        for (int v : c)                      // v is the last coin used
            if (v <= s && dp[s - v] + 1 < dp[s]) dp[s] = dp[s - v] + 1;
    cout << (dp[x] >= INF ? -1 : dp[x]) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
vector<int> c;
// fewest coins for rem using coin types i..n-1; choose how many of type i
int best(int i, int rem) {
    if (rem == 0) return 0;
    if (i == n) return INT_MAX;
    int res = INT_MAX;
    for (int k = 0; (long long)k * c[i] <= rem; k++) {
        int r = best(i + 1, rem - k * c[i]);
        if (r != INT_MAX) res = min(res, r + k);
    }
    return res;
}
int main() {
    int x;
    cin >> n >> x;
    c.resize(n);
    for (auto& v : c) cin >> v;
    int r = best(0, x);
    cout << (r == INT_MAX ? -1 : r) << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
vector<int> c;
int solve(int s) {                           // no memo: exponential
    if (s == 0) return 0;
    int res = 1e9;
    for (int v : c)
        if (v <= s) res = min(res, solve(s - v) + 1);
    return res;
}
int main() {
    int x;
    cin >> n >> x;
    c.resize(n);
    for (auto& v : c) cin >> v;
    int r = solve(x);
    cout << (r >= 1e9 ? -1 : r) << '\n';
}
""",
    hints=[
        r"""Greedy (largest coin first) fails: sample 2. Think about the *last* coin of an optimal
solution for the sum `s`: what must the remaining coins be?""",
        r"""`dp[s] = 1 + min over coins c ≤ s of dp[s - c]`, `dp[0] = 0`, and "impossible" is a big
value `INF`. Answer `-1` when `dp[x]` is still `INF`.""",
        r"""Choose `INF = 1e9`, not `INT_MAX`: `INT_MAX + 1` overflows to a negative number, which
then wins every `min`.""",
    ],
    editorial=r"""
`dp[s]` = the fewest coins with total exactly `s`, or `INF` if `s` cannot be made. An
optimal solution for `s` ends with some coin `c ≤ s`, and the coins before it must be an
optimal solution for `s − c` (if a better one existed, swapping it in would beat the optimum
for `s`). So

```
dp[s] = 1 + min over coins c <= s of dp[s - c],     dp[0] = 0
```

filled for `s = 1..x`: `(x + 1) · n ≤ 10^8` simple operations, about 0.1 s.

Greedy is wrong for general coin systems (`{1, 3, 4}`, `x = 6`: greedy 3 coins, optimum 2).
The implementation trap is the sentinel: with `INF = INT_MAX`, `dp[s - c] + 1` overflows to
a large negative number, which wins every `min` and poisons the table. `INF = 1e9` leaves
room for the `+ 1`.
""",
)

COMB_ORDERED = Problem(
    id="coin_combinations_i",
    title="Coin Combinations I",
    difficulty="easy",
    source="CSES 1635 - Coin Combinations I",
    complexity="O(n·x)",
    statement=r"""
A coin system has `n` different coin values, with unlimited coins of each. Count the ways to
produce the sum `x`, where **order matters**: the same coins in a different order are a
different way.

For coins `{2, 3, 5}` and `x = 9` there are 8 ways: `2+2+5`, `2+5+2`, `5+2+2`, `3+3+3`,
`2+2+2+3`, `2+2+3+2`, `2+3+2+2`, `3+2+2+2`.
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 100, 1 ≤ x ≤ 10^6).

The second line has `n` distinct integers c_1, ..., c_n (1 ≤ c_i ≤ 10^6).
""",
    output=r"""
The number of ordered ways, modulo 10^9 + 7.
""",
    samples=[
        Test("3 9\n2 3 5\n", "8\n"),
    ],
    tests=[
        Test("1 1\n2\n"),
        Test("2 3\n1 2\n"),
        Test("3 4\n1 2 3\n"),
        Test("1 10\n1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _coins(rng, rng.randint(1, 4), rng.randint(1, 20), 1, 10), 15),
        Gen("max size, coins up to 1000", lambda rng: _coins(rng, 100, 10**6, 1, 1000), 1, large=True),
        Gen("max size, coins up to 100", lambda rng: _coins(rng, 100, rng.randint(999000, 10**6), 1, 100), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int MOD = 1'000'000'007;
    int n, x;
    cin >> n >> x;
    vector<int> c(n);
    for (auto& v : c) cin >> v;
    sort(c.begin(), c.end());
    // dp[s] = ordered sequences of coins with total s
    vector<int> dp(x + 1, 0);
    dp[0] = 1;
    for (int s = 1; s <= x; s++) {           // sums outside: any coin can be last
        long long acc = 0;                   // at most 100 residues: below 10^11, fits
        for (int v : c) {
            if (v > s) break;                // sorted: every later coin is too big too
            acc += dp[s - v];
        }
        dp[s] = acc % MOD;                   // one % per sum, not one per addition
    }
    cout << dp[x] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
vector<int> c;
long long ways(int s) {
    if (s == 0) return 1;
    long long t = 0;
    for (int v : c) if (v <= s) t += ways(s - v);
    return t;
}
int main() {
    int x;
    cin >> n >> x;
    c.resize(n);
    for (auto& v : c) cin >> v;
    cout << ways(x) % 1000000007 << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
int n;
vector<int> c;
long long ways(int s) {
    if (s == 0) return 1;
    long long t = 0;
    for (int v : c) if (v <= s) t = (t + ways(s - v)) % MOD;
    return t;
}
int main() {
    int x;
    cin >> n >> x;
    c.resize(n);
    for (auto& v : c) cin >> v;
    cout << ways(x) << '\n';
}
""",
    hints=[
        r"""This is Dice Combinations with the faces replaced by the coin values.""",
        r"""`dp[s] = sum over coins c ≤ s of dp[s - c]`, `dp[0] = 1`, with the loop over `s` on the
outside. Reduce modulo 10^9 + 7 as you go.""",
    ],
    editorial=r"""
Classify the ordered sequences with total `s` by their last coin `c`: removing it leaves any
ordered sequence with total `s − c`. So `dp[s] = Σ dp[s − c]` over coins `c ≤ s`, with
`dp[0] = 1`, filled for increasing `s`. That is Dice Combinations with arbitrary faces:
`n · x ≤ 10^8` additions.

10^8 is close to the limit, so the constant factor matters. The reference sums the terms for
one `s` in a `long long` (100 residues stay below 10^11) and reduces once per sum instead of
once per addition, and it sorts the coins so the inner loop can stop at the first coin larger
than `s`. Measured here: about 0.04 s, against 0.17 s when every single addition is followed by its
own reduction. Both pass; the margin is worth knowing about.
""",
)

COMB_UNORDERED = Problem(
    id="coin_combinations_ii",
    title="Coin Combinations II",
    difficulty="medium",
    source="CSES 1636 - Coin Combinations II",
    complexity="O(n·x)",
    statement=r"""
Same coins, same unlimited supply, but now **order does not matter**: count the different
multisets of coins with total `x`.

For coins `{2, 3, 5}` and `x = 9` there are 3 ways: `2+2+5`, `3+3+3` and `2+2+2+3`.
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 100, 1 ≤ x ≤ 10^6).

The second line has `n` distinct integers c_1, ..., c_n (1 ≤ c_i ≤ 10^6).
""",
    output=r"""
The number of unordered ways, modulo 10^9 + 7.
""",
    samples=[
        Test("3 9\n2 3 5\n", "3\n",
             note="If you print 8, you counted orderings: look at which loop is outside."),
    ],
    tests=[
        Test("2 3\n1 2\n"),
        Test("1 7\n2\n"),
        Test("3 4\n1 2 3\n"),
        Test("1 1\n1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _coins(rng, rng.randint(1, 4), rng.randint(1, 30), 1, 10), 15),
        Gen("max size, coins up to 1000", lambda rng: _coins(rng, 100, 10**6, 1, 1000), 1, large=True),
        Gen("max size, coins up to 100", lambda rng: _coins(rng, 100, rng.randint(999000, 10**6), 1, 100), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int MOD = 1'000'000'007;
    int n, x;
    cin >> n >> x;
    vector<int> c(n);
    for (auto& v : c) cin >> v;
    // after processing coin types c[0..i]: dp[s] = multisets of those types with total s
    vector<int> dp(x + 1, 0);
    dp[0] = 1;
    for (int v : c)                          // coin types outside: each multiset is built
        for (int s = v; s <= x; s++) {       // in one order only (by type), upward: unlimited copies
            dp[s] += dp[s - v];
            if (dp[s] >= MOD) dp[s] -= MOD;
        }
    cout << dp[x] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
vector<int> c;
// multisets of coin types i..n-1 with total rem: choose how many of type i
long long ways(int i, int rem) {
    if (rem == 0) return 1;
    if (i == n) return 0;
    long long t = 0;
    for (int k = 0; (long long)k * c[i] <= rem; k++) t += ways(i + 1, rem - k * c[i]);
    return t;
}
int main() {
    int x;
    cin >> n >> x;
    c.resize(n);
    for (auto& v : c) cin >> v;
    cout << ways(0, x) % 1000000007 << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
int n;
vector<int> c;
long long ways(int i, int rem) {             // no memo: exponential
    if (rem == 0) return 1;
    if (i == n) return 0;
    long long t = ways(i + 1, rem);          // no more of type i
    if (c[i] <= rem) t += ways(i, rem - c[i]);   // one more of type i
    return t % MOD;
}
int main() {
    int x;
    cin >> n >> x;
    c.resize(n);
    for (auto& v : c) cin >> v;
    cout << ways(0, x) << '\n';
}
""",
    hints=[
        r"""The ordered recurrence counts `2+2+5`, `2+5+2` and `5+2+2` separately. Pick one
canonical order for each multiset and count only that one.""",
        r"""Canonical order: all copies of the first coin type, then all of the second, and so on.
So decide coin types one at a time: `for (coin) for (s = coin; s <= x; s++) dp[s] += dp[s - coin];`""",
        r"""A 2D table `dp[type][sum]` would be 100 · 10^6 ints = 400 MB. One row, updated in
place, is enough.""",
    ],
    editorial=r"""
Count each multiset in exactly one arrangement: the one that lists coin types in input order.
Let `dp_i[s]` be the number of multisets of the first `i` types with total `s`. Either the
multiset has no more copies of type `i`, or it has at least one, and removing one leaves a
multiset of the same types with total `s − c_i`:

```
dp_i[s] = dp_(i-1)[s] + dp_i[s - c_i]
```

Keeping one array and running `s` *upward* inside the coin loop computes exactly this:
`dp[s]` still holds `dp_(i-1)[s]` when it is read, and `dp[s - c_i]` has already been
updated to `dp_i`. That is the whole difference from Coin Combinations I: with the coin loop
outside, a larger coin type can never be followed by a smaller one, so orderings are not
counted. (Running `s` *downward* would read `dp_(i-1)[s - c_i]` and use each coin at most
once: the 0/1 knapsack of algo07.)
""",
)

GRID = Problem(
    id="grid_paths",
    title="Grid Paths",
    difficulty="easy",
    source="CSES 1638 - Grid Paths",
    complexity="O(n^2)",
    statement=r"""
An `n × n` grid has free cells (`.`) and traps (`*`). A path starts in the upper-left
corner, ends in the lower-right corner, and moves one cell right or one cell down at each
step. It may never enter a trap (including the first and last cells).

Count the paths.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 1000). Then `n` lines of `n` characters, each `.` or `*`.
""",
    output=r"""
The number of paths, modulo 10^9 + 7.
""",
    samples=[
        Test("4\n....\n.*..\n...*\n*...\n", "3\n"),
    ],
    tests=[
        Test("1\n.\n"),
        Test("1\n*\n"),
        Test("2\n*.\n..\n"),
        Test("2\n..\n.*\n"),
        Test("3\n...\n...\n...\n"),
        Test("3\n.*.\n*..\n...\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _grid_random(rng, rng.randint(1, 10), 0.15), 15),
        Gen("small, dense traps", lambda rng: _grid_random(rng, rng.randint(2, 10), 0.35), 6),
        Gen("max size, empty", lambda rng: _grid_sparse(rng, 1000, 0), 1, large=True),
        Gen("max size, a few traps", lambda rng: _grid_sparse(rng, 1000, 3000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int MOD = 1'000'000'007;
    int n;
    cin >> n;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    // dp[i][j] = paths from (0,0) to (i,j) avoiding traps
    vector<vector<int>> dp(n, vector<int>(n, 0));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            if (g[i][j] == '*') { dp[i][j] = 0; continue; }
            if (i == 0 && j == 0) { dp[i][j] = 1; continue; }
            long long v = 0;
            if (i > 0) v += dp[i - 1][j];    // arrived from above
            if (j > 0) v += dp[i][j - 1];    // arrived from the left
            dp[i][j] = v % MOD;
        }
    cout << dp[n - 1][n - 1] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
vector<string> g;
long long paths(int i, int j) {
    if (i >= n || j >= n || g[i][j] == '*') return 0;
    if (i == n - 1 && j == n - 1) return 1;
    return paths(i + 1, j) + paths(i, j + 1);
}
int main() {
    cin >> n;
    g.resize(n);
    for (auto& r : g) cin >> r;
    cout << paths(0, 0) % 1000000007 << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
int n;
vector<string> g;
long long paths(int i, int j) {              // walks every path: exponential
    if (i >= n || j >= n || g[i][j] == '*') return 0;
    if (i == n - 1 && j == n - 1) return 1;
    return (paths(i + 1, j) + paths(i, j + 1)) % MOD;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n;
    g.resize(n);
    for (auto& r : g) cin >> r;
    cout << paths(0, 0) << '\n';
}
""",
    hints=[
        r"""Every path into cell `(i, j)` arrives either from the cell above or from the cell to the
left, never both.""",
        r"""`dp[i][j] = dp[i-1][j] + dp[i][j-1]` for a free cell, `0` for a trap, `dp[0][0] = 1`
unless it is a trap. Fill row by row.""",
    ],
    editorial=r"""
`dp[i][j]` = the number of trap-free paths from the corner to `(i, j)`. The last step into
`(i, j)` comes from above or from the left, and those two sets of paths are disjoint, so
`dp[i][j] = dp[i-1][j] + dp[i][j-1]` for a free cell and `0` for a trap. The start is `1`
(the path of length zero) unless it is a trap, in which case every answer is `0`. Row by
row, left to right: every cell's two sources are done before it. `n^2 = 10^6` cells.

Enumerating the paths is hopeless: an empty 1000 × 1000 grid has C(1998, 999) ≈ 10^600 of
them. The details that cost verdicts: a trap on the start or end cell, and the sum of two
residues, which should be reduced (or computed in `long long`) before it is stored.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo06",
    title="dynamic programming I: states and transitions",
    track="algo",
    order=6,
    summary="From an exponential recursion to a table: overlapping subproblems, memoisation, "
            "defining the state in words, the order of computation, and counting versus "
            "optimising.",
    prereqs=["algo05"],
    tags=["dynamic programming", "memoisation", "recursion", "counting", "coin change",
          "grid paths", "modular arithmetic"],
    parts=[
        Part("The same question, over and over", [
            Say(r"""
Throw an ordinary die again and again and add up the results. In how many ways can the
total come out to exactly `n`? Order matters: `1 + 2` and `2 + 1` are different ways. The
limits: `n ≤ 10^6`, one second, and the count is astronomical, so print it modulo
10^9 + 7 (cpp10).

This is CSES *Dice Combinations*, the cleanest first problem for this lesson's idea. Start
with something you can count on your fingers.
"""),
            Short(r"""
For `n = 3`, how many ways are there?
""", accept=["4"], placeholder="a number",
                hint="List them: sequences of throws, each 1 to 6, that add up to 3.",
                explain=r"""
`1+1+1`, `1+2`, `2+1`, `3`: four ways.
"""),
            MCQ(r"""
algo05 would build the sequence throw by throw. Classify all the ways to reach a total `s`
by the value of the **first** throw. Which recursion counts them?
""", [
                Opt("`ways(s) = 6 · ways(s-1)`",
                    why="That counts sequences by *length*: six choices per throw. But a throw of 4 "
                        "uses up 4 of the total, not 1, so the six branches leave six different "
                        "remainders."),
                Opt("`ways(s) = ways(s-1) + ... + ways(s-6)`, with `ways(0) = 1` and negative "
                    "arguments skipped", correct=True,
                    why="Yes. A first throw of `k` leaves `s - k` to make, in `ways(s-k)` ways, and "
                        "different first throws give different sequences, so the cases add."),
                Opt("`ways(s) = ways(s-1) + ... + ways(s-6)`, with `ways(0) = 0`",
                    why="Then every value is a sum of zeros and the answer is always 0. Reaching "
                        "exactly 0 is a finished sequence, and it counts as one way."),
            ], explain=r"""
`ways(0) = 1` is the same kind of sentinel as `p[0] = 0` in algo01: the empty sequence is
one way to make a total of zero, and the formula needs it to be counted.
"""),
            Say(r"""
In C++:

```cpp
long long ways(int s) {             // sequences of throws with total exactly s
    if (s == 0) return 1;           // the empty sequence
    long long total = 0;
    for (int k = 1; k <= 6 && k <= s; k++)
        total += ways(s - k);
    return total % MOD;
}
```

Correct, and exactly what backtracking would do. Before you submit it, count the work.
"""),
            Numeric(r"""
Each call is one node of the recursion tree. Counted by a program: `ways(10)` makes 992
calls, `ways(20)` makes 935,680, and each +1 on `n` multiplies the count by about 1.98.
Roughly how many calls does `ways(50)` make?
""", answer=7.85e14, rel=0.5, unit="calls",
                hint="From n = 20 to n = 50 is 30 more factors of about 2.",
                explain=r"""
About 935,680 · 1.98^30 ≈ 7.8·10^14. At 10^9 calls per second that is nine days, and
`n = 50` is 20,000 times smaller than the real limit. Brute force is out.
"""),
            Numeric(r"""
Now the question that matters. While `ways(6)` runs, how many times is `ways(2)` called?
""", answer=8, hint=r"""Every chain of calls from `ways(6)` down to `ways(2)` is a sequence of first throws.
What do those throws add up to?""",
                explain=r"""
8 times. Each chain of calls from 6 down to 2 is a sequence of throws with total 4, and
there are `ways(4) = 8` of those. In general `ways(t)` is called `ways(n − t)` times: inside
`ways(20)`, `ways(10)` is computed from scratch 492 times, and every one of those computations
produces the same number.
"""),
            Reflect(r"""
`ways(50)` makes about 7.8·10^14 calls, but how many *different* arguments do they have?
Given that number, say what the recursion is wasting, and what property of `ways(s)` makes
the waste avoidable.
""", answer=r"""
Only 51 different arguments, 0 to 50, so each question is asked about 10^13 times on
average. The recursion re-solves the same subproblem every time a different sequence of
early throws happens to leave the same remainder. That is avoidable because the answer to
`ways(s)` depends only on `s`, not on the throws that led there: compute each one once,
store it, and look it up afterwards. Subproblems that repeat (they **overlap**) and whose
answers depend only on a small description (here the number `s`) are exactly what dynamic
programming exploits.
"""),
        ]),
        Part("Remember, then fill a table", [
            Say(r"""
The fix has a name: **memoisation**. Keep an array of answers, fill each entry the first time
it is computed, and return the stored value every later time.

```cpp
vector<long long> memo;             // memo[s] == -1: not computed yet

long long ways(int s) {
    if (s == 0) return 1;
    if (memo[s] != -1) return memo[s];
    long long total = 0;
    for (int k = 1; k <= 6 && k <= s; k++)
        total += ways(s - k);
    return memo[s] = total % MOD;
}
// in main: memo.assign(n + 1, -1);
```
"""),
            Numeric(r"""
With the memo, the loop inside `ways(s)` runs once per distinct `s`. For `n = 10^6`, about
how many additions does the whole computation do?
""", answer=6e6, rel=0.5, unit="additions",
                explain=r"""
`n + 1` distinct states, at most 6 additions each: about 6·10^6. That is the cost formula
for every DP in this track: **(number of states) × (work per state)**. From 10^14-and-up to
6·10^6, and the machine did not change.
"""),
            Reflect(r"""
Before turning this into loops, write what `memo[s]` *means*, as one sentence you could put
in a comment. Why bother being that precise?
""", answer=r"""
`dp[s]` = the number of ordered sequences of throws (each 1 to 6) whose total is exactly
`s`. The sentence decides everything else: the base case (`dp[0] = 1`, the empty sequence),
where the answer is (`dp[n]`), and the transition (classify by one throw and add). Most
wrong DPs are wrong because the state was never defined: "the answer for s" is not a
definition, and a vague state lets a transition that double-counts or misses cases look
plausible.
"""),
            MCQ(r"""
Now drop the recursion and fill an array `dp[0..n]` with a loop. `dp[s]` reads
`dp[s-1]` through `dp[s-6]`. In which order must the entries be filled?
""", [
                Opt("Any order: each entry is computed exactly once anyway.",
                    why="Once, yes, but it must be computed *after* the entries it reads. Fill "
                        "`dp[5]` before `dp[4]` and it adds a 0 that should have been 8."),
                Opt("Decreasing: `s = n, n-1, ..., 1`.",
                    why="`dp[n]` would read `dp[n-1..n-6]` while they are still 0."),
                Opt("Increasing: `s = 1, 2, ..., n`.", correct=True,
                    why="Yes. Every entry depends only on smaller indices, and those are final "
                        "by the time it is computed."),
            ], explain=r"""
The recursion found this order for you, silently; a table makes you choose it. The rule is
always the same: every state after all the states it reads. (For general dependency graphs
that is a topological order, algo12.)
"""),
            Short(r"""
Fill it by hand, starting from `dp[0] = 1`. Write `dp[0]` through `dp[7]`, separated by
spaces.
""", accept=["1 1 2 4 8 16 32 63", "1,1,2,4,8,16,32,63"], placeholder="eight numbers",
                hint="`dp[s]` is the sum of the (up to) six entries before it.",
                explain=r"""
`1 1 2 4 8 16 32 63`. Up to `dp[6]` every entry is the sum of *all* earlier ones, so it
doubles. `dp[7] = dp[6] + ... + dp[1] = 63`: `dp[0]` has dropped out of reach, because no
single throw is 7. Doubling was a pattern of small `n`, not the rule; the recurrence is the
rule.
"""),
            MCQ(r"""
The memoised recursion and the table do the same 6·10^6 additions. On a judge with an
8 MB stack, the recursion crashes for `n = 10^6`. Why?
""", [
                Opt("`ways(10^6)` calls `ways(10^6 - 1)`, which calls ..., a million frames deep "
                    "before anything returns.", correct=True,
                    why="Right. Each frame is tens of bytes, so 10^6 of them need tens of MB of "
                        "stack. The loop has no call stack at all."),
                Opt("The memo array lives on the stack and is too big.",
                    why="A `vector`'s elements are on the heap. 10^6 `long long`s are 8 MB of heap, "
                        "which is fine."),
                Opt("Memoisation makes the same calls as the plain recursion, so it is still "
                    "exponential.",
                    why="Every repeated call now returns after one lookup: about 6·10^6 calls in "
                        "all. Speed is not the problem; depth is."),
            ], explain=r"""
Many judges (and this one) give a large stack, but not all do. Write the table when states
have an obvious order and the depth would reach 10^5 or more; keep memoised recursion for
state spaces whose order is awkward to write as loops (the digit DP of algo08).
"""),
            MCQ(r"""
`dp` holds `int`s, each already reduced below 10^9 + 7. For `s ≥ 6`, what is wrong with
this line?

```cpp
dp[s] = (dp[s-1] + dp[s-2] + dp[s-3] + dp[s-4] + dp[s-5] + dp[s-6]) % MOD;
```
""", [
                Opt("Nothing: `% MOD` keeps the value below 10^9 + 7.",
                    why="The `%` runs after the sum, and the overflow happens during the sum. By "
                        "then the value is already garbage."),
                Opt("The sum can reach about 6·10^9, past the `int` limit, before `%` runs.",
                    correct=True,
                    why="Yes. Add in `long long`, or add one term at a time and subtract `MOD` "
                        "whenever the running value reaches it (two residues sum to under 2^31)."),
                Opt("`%` is slow; it should be replaced by a loop of subtractions.",
                    why="Speed is a fair concern at 10^8 operations (the problems below use a "
                        "conditional subtraction), but here the result is simply wrong."),
            ]),
            Try("dice_combinations", note="The table, in increasing `s`, with the modulus applied as "
                "you add. The hidden tests go up to `n = 10^6`."),
        ]),
        Part("Fewest coins: optimising instead of counting", [
            Say(r"""
A different question with the same skeleton. A coin system has `n ≤ 100` coin values with
unlimited coins of each. Pay exactly `x ≤ 10^6` using as few coins as possible, or report
that it cannot be done (CSES *Minimizing Coins*).
"""),
            MCQ(r"""
Coins `{1, 3, 4}`, `x = 6`. The first idea everyone has: take the largest coin that fits,
repeat. What does it give, and is it optimal?
""", [
                Opt("`4 + 1 + 1`: three coins, and nothing better exists.",
                    why="`3 + 3` is two coins. Greedy is optimal for euro and dollar coins, which "
                        "is why it feels safe, but not for coin systems in general."),
                Opt("`3 + 3`: greedy finds the optimum here.",
                    why="Greedy starts with the largest coin that fits, which is 4, and then must "
                        "finish with `1 + 1`."),
                Opt("`4 + 1 + 1`: three coins, but `3 + 3` uses only two.", correct=True,
                    why="Right. Taking the 4 looks like progress and blocks the better answer."),
            ], explain=r"""
Greedy commits to one choice. A DP tries *every* choice for one decision, and the stored
answers make trying them all cheap. (algo02 shows how to prove a greedy correct when it is.)
"""),
            Reflect(r"""
Define the state in words, then the transition. Hint: look at the *last* coin of an optimal
way to pay `s`.
""", answer=r"""
`dp[s]` = the fewest coins whose values add up to exactly `s`, or ∞ if `s` cannot be made.
Any way to pay `s` ends with some coin `c ≤ s`, and the coins before it pay `s − c`. So
`dp[s] = 1 + min over coins c ≤ s of dp[s − c]`, with `dp[0] = 0`. Compared with Dice
Combinations, the sum over cases became a minimum over cases, and the base case "one way"
became "zero coins".
"""),
            MCQ(r"""
The transition trusts that when an optimal payment of `s` ends with coin `c`, the other
coins form an *optimal* payment of `s − c`. Could that be false?
""", [
                Opt("No: a cheaper payment of `s − c`, plus coin `c`, would beat the optimum for `s`.",
                    correct=True,
                    why="Right: proof by contradiction. If the remainder were not optimal, you "
                        "could swap in a better remainder and improve the optimum, which is "
                        "impossible."),
                Opt("Yes, when `c` is more than half of `s`.",
                    why="The size of `c` plays no part in the argument; it works for any `c ≤ s`."),
                Opt("Yes, if the coins must be paid in a particular order.",
                    why="Order does not change the number of coins, and the argument only needs "
                        "*some* coin to be last."),
            ], explain=r"""
This "cut and paste" argument, called **optimal substructure**, is how every optimisation
DP is justified: after the last decision, what remains must itself be solved optimally,
or you could replace it with something better.
"""),
            Short(r"""
Coins `{1, 3, 4}`. Fill `dp[0]` through `dp[6]` by hand (fewest coins for each sum).
""", accept=["0 1 2 1 1 2 2", "0,1,2,1,1,2,2"], placeholder="seven numbers",
                hint="`dp[s] = 1 + min(dp[s-1], dp[s-3], dp[s-4])`, skipping negative indices.",
                explain=r"""
`0 1 2 1 1 2 2`. `dp[5] = 1 + min(dp[4], dp[2], dp[1]) = 2` (4 + 1), and
`dp[6] = 1 + min(dp[5], dp[3], dp[2]) = 1 + dp[3] = 2` (3 + 3). The table found the answer
greedy missed without anyone having to spot it.
"""),
            Numeric(r"""
`x + 1` states, `n` transitions each. With `n = 100` and `x = 10^6`, how many operations?
""", answer=1e8, rel=0.5, unit="operations",
                explain=r"""
About 10^8, each a comparison and an addition: roughly 0.1 s of C++. That is near the top
of what one second allows, so keep the inner loop simple (no `map`, no `%` you do not
need). The same loop in Python would take about a minute.
"""),
            MCQ(r"""
Impossible sums hold a sentinel `INF`. A contestant writes `const int INF = INT_MAX;` and
`dp[s] = min(dp[s], dp[s - c] + 1);`. What happens when `dp[s - c]` is `INF`?
""", [
                Opt("Nothing: `min` keeps `dp[s]`.",
                    why="`min` compares against `INT_MAX + 1`, and that value is not what you think."),
                Opt("The compiler rejects `INT_MAX + 1`.",
                    why="It cannot see it: `dp[s - c]` is only known at run time."),
                Opt("`INT_MAX + 1` overflows to a large negative number, which wins every `min`.",
                    correct=True,
                    why="Yes. In practice it wraps to −2147483648, and the impossible sums become "
                        "the 'best' ones. Use `INF = 1e9`, so `INF + 1` still fits, or skip "
                        "entries equal to `INF`."),
            ]),
            Try("minimizing_coins", note="One hidden test has sums that are impossible on the way to a "
                "possible `x`: that is where a bad `INF` shows."),
        ]),
        Part("Does order matter? Loop order decides", [
            Say(r"""
Same coins, now counting (CSES *Coin Combinations I* and *II*), modulo 10^9 + 7, with the
same limits:

- **I**: count *ordered* ways to make `x`: `2+2+5` and `2+5+2` are different.
- **II**: count *unordered* ways: `2+2+5` and `2+5+2` are the same multiset of coins.
"""),
            Short(r"""
Coins `{2, 3, 5}`, `x = 9`. How many ordered ways, and how many unordered? Two numbers,
ordered first.
""", accept=["8 3", "8,3", "8 and 3"], placeholder="two numbers",
                hint="First find the multisets. Then count the arrangements of each.",
                explain=r"""
The multisets are `{2,2,5}`, `{3,3,3}` and `{2,2,2,3}`: 3 unordered ways. They have 3, 1
and 4 arrangements: 8 ordered ways.
"""),
            MCQ(r"""
Version I is Dice Combinations with the faces replaced by coins: `dp[s] = Σ dp[s − c]` over
coins `c ≤ s`. Why does that same recurrence *overcount* for version II?
""", [
                Opt("It counts `dp[0] = 1`, the empty payment, as a way.",
                    why="Both versions need `dp[0] = 1`: it is the one way to finish, and without it "
                        "everything is zero."),
                Opt("It allows the same coin more than once.",
                    why="Both versions allow unlimited coins. Repetition is not the issue; order is."),
                Opt("It classifies by the last coin, and `2+2+5`, `2+5+2`, `5+2+2` have different "
                    "last coins, so one multiset lands in several cases.", correct=True,
                    why="Right. The cases are disjoint as *sequences*, but not as multisets, so "
                        "every multiset is counted once per distinct arrangement."),
            ]),
            Reflect(r"""
How can you count every multiset exactly once? Hint: choose one canonical arrangement of
each multiset, and make the DP build only that one.
""", answer=r"""
Agree to list the coins by type: all copies of `c_1` first, then all copies of `c_2`, and so
on. Every multiset has exactly one such arrangement. Then the DP decides coin types one at a
time: `dp[i][s]` = the number of multisets using only the first `i` types with total `s`,
and `dp[i][s] = dp[i-1][s]` (no more copies of type `i`) `+ dp[i][s - c_i]` (one more copy of
type `i`). Once the DP moves past a type it never returns to it, so no multiset is built
twice.
"""),
            Say(r"""
That table, `100 × 10^6` `int`s, would be 400 MB, more than most judges allow. But row `i`
reads only row `i − 1` and itself, so one row, overwritten in place, is enough. The order
of the overwriting is what matters. Here are two programs; both start from `dp[0] = 1` and
zeros elsewhere, and they differ only in which loop is outside:

```cpp
// Program A
for (int s = 1; s <= x; s++)
    for (int c : coins)
        if (c <= s) dp[s] = (dp[s] + dp[s - c]) % MOD;

// Program B
for (int c : coins)
    for (int s = c; s <= x; s++)
        dp[s] = (dp[s] + dp[s - c]) % MOD;
```
"""),
            Short(r"""
Trace **Program B** by hand with coins `{1, 2}` and `x = 3`. What is `dp[3]` at the end?
""", accept=["2"], placeholder="a number",
                hint="After the pass for coin 1, `dp = 1 1 1 1`. Now do the pass for coin 2.",
                explain=r"""
2. After coin 1: `dp = 1 1 1 1`. Coin 2: `dp[2] = 1 + dp[0] = 2`, `dp[3] = 1 + dp[1] = 2`.
Those are the multisets `{1,1,1}` and `{1,2}`. Program A prints 3: `1+1+1`, `1+2`, `2+1`.
"""),
            MCQ(r"""
So which program counts ordered sequences, and why?
""", [
                Opt("Both count the same thing; the loop order only changes speed.",
                    why="The trace says otherwise: 3 against 2 for coins `{1, 2}`, `x = 3`."),
                Opt("A: when it computes `dp[s]`, every coin may be the last one, whatever came "
                    "before it.", correct=True,
                    why="Yes. In A, `dp[s - c]` already counts sequences with every coin type, so "
                        "`2` may follow `1` and `1` may follow `2`."),
                Opt("B: its outer loop tries every coin in turn.",
                    why="Trying types in a fixed order is exactly what forbids a smaller-index "
                        "type after a larger one. B builds each multiset in its canonical order "
                        "only."),
            ], explain=r"""
In B, during the pass for coin `c`, `dp[s - c]` contains only ways built from the types
processed so far, so a later type can never be followed by an earlier one: that is the
`dp[i][s]` recurrence from the Reflect, one row at a time. Loop order is not a detail in a
DP; it is part of the definition of the state.
"""),
            Short(r"""
One more variant: Program B with the inner loop running *downward*,
`for (int s = x; s >= c; s--)`. Coins `{1, 2}`, `x = 3`. What is `dp[3]` at the end?
""", accept=["1"], placeholder="a number",
                hint="Going down, when `dp[s]` reads `dp[s - c]`, has `dp[s - c]` been updated for this "
                     "coin yet?",
                explain=r"""
1: only `{1, 2}`. Downward, `dp[s - c]` still holds the value from *before* this coin's pass,
so each coin can be used at most once. That loop is the 0/1 knapsack, the first thing algo07
builds on.
"""),
            Try("coin_combinations_i", note="Dice Combinations with coins for faces."),
            Try("coin_combinations_ii", note="Coins outside, sums inside, upward. The sample tells you "
                "which way round you wrote it."),
        ]),
        Part("Two dimensions: paths through a grid", [
            Say(r"""
An `n × n` grid (`n ≤ 1000`) has free cells and traps. Count the paths from the upper-left
corner to the lower-right corner that move only right or down and never enter a trap,
modulo 10^9 + 7 (CSES *Grid Paths*).
"""),
            Numeric(r"""
Ignore traps for a moment. How many paths cross an empty 3 × 3 grid?
""", answer=6, hint="Every path makes the same number of right moves and down moves; only their "
                    "order differs.",
                explain=r"""
Every path is 2 rights and 2 downs in some order: C(4, 2) = 6. For `n = 1000` it is
C(1998, 999) ≈ 10^600 paths, so walking them one by one (the plain recursion) is not an
option, even though each path is short.
"""),
            MCQ(r"""
Which state gives a DP?
""", [
                Opt("`dp[i][j]` = the number of trap-free paths from the start to cell `(i, j)`.",
                    correct=True,
                    why="Yes. The last step into `(i, j)` comes from above or from the left, never "
                        "both, so `dp[i][j] = dp[i-1][j] + dp[i][j-1]`, and 0 on a trap."),
                Opt("`dp[k]` = the number of paths of length `k`.",
                    why="Every path to the corner has the same length, `2n − 2`. Length says nothing "
                        "about *where* you are, and which cells are still reachable depends on that."),
                Opt("`dp[i][j]` = `true` if `(i, j)` can be reached.",
                    why="That answers 'is there a path', not 'how many'. The count needs the number "
                        "of ways into each cell, not a yes/no."),
            ]),
            Short(r"""
The grid (row 1 on top):

```
....
.*..
...*
*...
```

Row 1 of `dp` is `1 1 1 1` and row 2 is `1 0 1 2`. Compute rows 3 and 4, and write **row 4**.
""", accept=["0 1 3 3", "0,1,3,3"], placeholder="four numbers",
                hint="Row 3 first. Each free cell is the cell above plus the cell to the left; traps "
                     "are 0.",
                explain=r"""
Row 3 is `1 1 2 0` (the last cell is a trap), row 4 is `0 1 3 3` (the first cell is a trap).
The answer is the last entry, 3.
"""),
            MCQ(r"""
What should the start, `dp[0][0]`, be?
""", [
                Opt("0, because no move has been made yet.",
                    why="Then every entry is a sum of zeros. The path that has not moved yet is one "
                        "path, like the empty sequence of throws."),
                Opt("1, even if it is a trap: you start there, you do not step onto it.",
                    why="The statement forbids paths through a trap, and the start is on the path. "
                        "A hidden test starts on a trap and expects 0."),
                Opt("1, unless it is a trap, in which case it is 0 and so is every answer.",
                    correct=True,
                    why="Right. Treat the start like any other cell: traps are 0, and the free start "
                        "is the base case 1."),
            ]),
            Try("grid_paths", note="Row by row. Check the start and end cells."),
        ]),
        Part("The recipe, and what a state must hold", [
            Say(r"""
Five problems, one recipe:

1. **State**, in words: what `dp[...]` counts or optimises, for which subproblem.
2. **Transition**: classify by one decision (the last throw, the last coin, the last step)
   and combine the cases: `+` to count, `min`/`max` to optimise.
3. **Base case**: usually the empty object (`1` way, `0` coins).
4. **Order**: every state after the states it reads.
5. **Answer**: which entry (or which max over entries).

Cost: states × work per state. The hard part is almost always step 1.
"""),
            MCQ(r"""
New rule for the dice: no two consecutive throws may be equal (`1+1+2` is forbidden,
`1+2+1` is fine). Why can `dp[s]` alone no longer be computed from smaller entries?
""", [
                Opt("Whether the next throw is allowed depends on the previous throw, and `dp[s]` "
                    "forgets it.", correct=True,
                    why="Right. The state must hold everything the future depends on. Add the last "
                        "throw: `dp[s][last]`, 6(n + 1) states, still tiny."),
                Opt("The problem now needs the whole sequence, so it is backtracking again.",
                    why="The future depends on the past only through one number, the last throw. "
                        "A slightly bigger state keeps it a DP."),
                Opt("The counts no longer fit in `long long`.",
                    why="They are smaller than before, and they are reduced modulo 10^9 + 7 anyway."),
            ], explain=r"""
When a transition needs information the state does not have, do not abandon the DP: add
that information to the state, and check that the number of states stays small.
"""),
            MCQ(r"""
A counting DP adds its cases, so the cases must not overlap (or some objects are counted
twice). What about a `min` DP like Minimizing Coins: may its cases overlap?
""", [
                Opt("No: overlapping cases double-count in a `min` DP too.",
                    why="`min` does not count anything. Seeing the same candidate twice does not "
                        "change the minimum."),
                Opt("Yes: `min(a, a) = a`, so overlap is harmless, as long as every candidate is "
                    "covered by some case.", correct=True,
                    why="Right. Optimisation needs the cases to be *exhaustive*; counting needs them "
                        "exhaustive *and* disjoint. Coin Combinations II is what overlapping cases "
                        "do to a count."),
                Opt("It does not matter for either kind; the DP sorts it out.",
                    why="Coin Combinations I's recurrence applied to multisets is exactly a count "
                        "with overlapping cases, and it gives 8 instead of 3."),
            ]),
            Numeric(r"""
Last estimate. Minimizing Coins with `n = 100` but `x = 10^9`: how many operations would the
same DP do?
""", answer=1e11, rel=0.5, unit="operations",
                explain=r"""
10^11: far too slow, and a 4 GB table besides. The cost of these DPs grows with the *value*
of `x`, not with the size of the input (a 10-digit number). That is called
**pseudo-polynomial**, and it is why the limits on sums and capacities in DP problems sit
around 10^5 to 10^6. When they are larger, the state has to be something else.
"""),
        ]),
    ],
    problems=[DICE, MIN_COINS, COMB_ORDERED, COMB_UNORDERED, GRID],
    cards=[
        Card(r"""What two properties make a recursion worth turning into a DP?""",
             r"""Overlapping subproblems (the same arguments recur) and answers that depend only on a small state, not on how you got there. Then compute each state once."""),
        Card(r"""How do you estimate the running time of a DP?""",
             r"""(number of states) × (work per transition). Dice Combinations: (n + 1) × 6."""),
        Card(r"""Dice Combinations: state, transition, base case?""",
             r"""`dp[s]` = ordered sequences of throws with total `s`; `dp[s] = dp[s-1] + ... + dp[s-6]` (non-negative indices only); `dp[0] = 1`."""),
        Card(r"""Minimizing Coins: transition and base case?""",
             r"""`dp[s] = 1 + min over coins c ≤ s of dp[s-c]`, `dp[0] = 0`, `INF` for impossible sums."""),
        Card(r"""Why is `INF = INT_MAX` a bad sentinel in a min-DP?""",
             r"""`INF + 1` overflows to a large negative number, which wins every `min`. Use `1e9` (or `1e18` for `long long`)."""),
        Card(r"""Coin combinations: which loop order counts ordered sequences, and which counts multisets?""",
             r"""Sums outside, coins inside: ordered. Coins outside, sums inside (upward): multisets, each built in one canonical order."""),
        Card(r"""What changes if the inner sum loop of the coins-outside version runs downward?""",
             r"""Each coin is used at most once: `dp[s - c]` still holds the value from before this coin's pass. That is the 0/1 knapsack loop."""),
        Card(r"""Memoised recursion vs bottom-up table: when does the recursion fail?""",
             r"""When the dependency chain is very deep (10^5–10^6): each state is a stack frame, and an 8 MB stack overflows. The table has no call stack."""),
        Card(r"""A transition needs information the state does not hold. What do you do?""",
             r"""Add it to the state (e.g. `dp[s][last throw]`) and check that the number of states stays small."""),
        Card(r"""Counting DP vs optimisation DP: what must the cases satisfy?""",
             r"""Counting: exhaustive and disjoint (each object counted once). Min/max: exhaustive; overlap is harmless."""),
        Card(r"""Why is `(a + b + c + d + e + f) % MOD` wrong for six `int` residues?""",
             r"""The sum reaches about 6·10^9 and overflows `int` before `%` runs. Sum in `long long`, or add one term at a time and subtract `MOD` when it is reached."""),
    ],
)
