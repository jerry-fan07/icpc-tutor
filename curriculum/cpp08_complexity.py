from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _array(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _mostly_positive(rng, n):
    a = [rng.randint(10**9 - 1000, 10**9) if rng.random() < 0.97 else -rng.randint(1, 10**9)
         for _ in range(n)]
    return f"{n}\n" + " ".join(map(str, a)) + "\n"


def _tests_of_values(rng, t, nmin, nmax, vmax):
    out = [str(t)]
    for _ in range(t):
        n = rng.randint(nmin, nmax)
        out.append(str(n))
        out.append(" ".join(str(rng.randint(1, vmax)) for _ in range(n)))
    return "\n".join(out) + "\n"


def _many_pairs(rng):
    t = 100000                                   # sum of n = 2·10^5: every test has n = 2
    out = [str(t)]
    for _ in range(t):
        out.append("2")
        out.append(f"{rng.randint(1, 10**6)} {rng.randint(1, 10**6)}")
    return "\n".join(out) + "\n"


def _one_big_test(rng):
    n = 200000
    return f"1\n{n}\n" + " ".join(str(rng.randint(1, 1000)) for _ in range(n)) + "\n"


def _pairs(rng, n, vmax, x):
    return f"{n} {x}\n" + " ".join(str(rng.randint(1, vmax)) for _ in range(n)) + "\n"


def _pairs_small(rng):
    n = rng.randint(1, 10)
    return _pairs(rng, n, 6, rng.randint(2, 12))


def _pairs_hit(rng, n, vmax):
    """x is the sum of two random elements, so the answer is rarely zero."""
    a = [rng.randint(1, vmax) for _ in range(n)]
    x = a[rng.randrange(n)] + a[rng.randrange(n)]
    return f"{n} {x}\n" + " ".join(map(str, a)) + "\n"


def _pairs_all_equal(rng):
    n = 200000
    return f"{n} 1000000000\n" + " ".join(["500000000"] * n) + "\n"


# --------------------------------------------------------------------- problems
MAX_SUBARRAY = Problem(
    id="max_subarray",
    title="Best Stretch",
    difficulty="easy",
    source="CSES 1643 - Maximum Subarray Sum",
    complexity="O(n)",
    statement=r"""
A trader logged the profit (possibly negative) of each of `n` consecutive days. She wants
to brag about her best *stretch*: a run of one or more consecutive days whose total profit
is as large as possible.

Print that total.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers a_1, ..., a_n (−10^9 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print the largest sum of a non-empty block of consecutive values.
""",
    samples=[
        Test("8\n-1 3 -2 5 3 -5 2 2\n", "9\n"),
        Test("3\n-3 -1 -2\n", "-1\n",
             note="A stretch has at least one day. When every day loses money, the best "
                  "stretch is the single least-bad day, not the empty stretch."),
    ],
    tests=[
        Test("1\n-1000000000\n"),
        Test("1\n1000000000\n"),
        Test("5\n1000000000 1000000000 1000000000 1000000000 1000000000\n"),
        Test("6\n5 -100 1 1 1 1\n"),
        Test("4\n-5 -5 -5 -5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _array(rng, rng.randint(1, 10), -10, 10), 12),
        Gen("small negative", lambda rng: _array(rng, rng.randint(1, 8), -10, -1), 4),
        Gen("medium random", lambda rng: _array(rng, 3000, -10**9, 10**9), 2),
        Gen("max size, random", lambda rng: _array(rng, 200000, -10**9, 10**9), 1, large=True),
        Gen("max size, huge answer", lambda rng: _mostly_positive(rng, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    long long cur = 0, best = LLONG_MIN;     // not 0: the answer can be negative
    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;
        // best sum of a block that ends exactly here: extend the previous one, or restart
        cur = (i == 0) ? x : max(x, cur + x);
        best = max(best, cur);
    }
    cout << best << '\n';
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
    long long best = LLONG_MIN;
    for (int l = 0; l < n; l++)
        for (int r = l; r < n; r++) {
            long long s = 0;
            for (int k = l; k <= r; k++) s += a[k];
            best = max(best, s);
        }
    cout << best << '\n';
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
    long long best = LLONG_MIN;
    for (int l = 0; l < n; l++) {
        long long s = 0;
        for (int r = l; r < n; r++) {
            s += a[r];
            best = max(best, s);
        }
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""The double loop over `(l, r)` is about 2·10^10 steps. You need one pass. What do you
need to know about the blocks that end at position `i − 1` to handle the blocks that end
at `i`?""",
        r"""Let `cur` be the best sum of a block ending exactly at `i`. Either that block is just
`a[i]`, or it extends the best block ending at `i − 1`: `cur = max(a[i], cur + a[i])`.
The answer is the largest `cur` ever seen.""",
        r"""Start `best` at `LLONG_MIN` (or at `a[0]`), not at 0, and keep sums in `long long`:
2·10^5 values of 10^9 add up to 2·10^14.""",
    ],
    editorial=r"""
Kadane's algorithm. Let `cur(i)` be the largest sum of a block that ends exactly at `i`.
Such a block is either `a[i]` alone or a block ending at `i − 1` extended by `a[i]`, and
the best of the latter is `cur(i−1) + a[i]`. So `cur(i) = max(a[i], cur(i−1) + a[i])`,
and the answer is the maximum of all `cur(i)`: every block ends somewhere. One pass, O(n).

The costs of the three natural programs at `n = 2·10^5`: recomputing every block sum is
about n^3/6 ≈ 1.3·10^15 additions; keeping a running sum per left end is n^2/2 = 2·10^10
(about 10 s on this machine); Kadane is 2·10^5.

Two traps cost a WA even with the right idea: starting `best` at 0 (all-negative input
has a negative answer), and `int` sums (the answer reaches 2·10^14).
""",
)

MOST_COMMON = Problem(
    id="most_common",
    title="Most Common, Many Times",
    difficulty="easy",
    complexity="O(sum of n)",
    statement=r"""
A survey robot runs `t` separate surveys. In each, it records `n` answers, each an integer
code between 1 and 10^6. For every survey, report the code that was given most often; if
several codes tie, report the smallest of them.

Read the input section carefully: all of it.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5).

Each survey is two lines: `n` (1 ≤ n ≤ 2·10^5), then `n` integers a_1, ..., a_n
(1 ≤ a_i ≤ 10^6).

The sum of `n` over all surveys is at most 2·10^5.
""",
    output=r"""
For each survey, print the most common code (the smallest one on ties) on its own line.
""",
    samples=[
        Test("3\n5\n4 1 4 2 1\n1\n1000000\n3\n2 2 9\n", "1\n1000000\n2\n",
             note="In the first survey, 1 and 4 both appear twice; the smaller wins."),
    ],
    tests=[
        Test("1\n1\n1\n"),
        Test("2\n3\n7 7 3\n3\n3 3 7\n"),
        Test("1\n6\n1000000 999999 1000000 999999 5 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _tests_of_values(rng, rng.randint(1, 5), 1, 8, 5), 12),
        Gen("medium random", lambda rng: _tests_of_values(rng, 200, 1, 60, 10**6), 2),
        Gen("10^5 surveys of two answers", _many_pairs, 1, large=True),
        Gen("one big survey", _one_big_test, 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

static int cnt[1000001];                      // zero at the start of every survey

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (auto& x : a) {
            cin >> x;
            cnt[x]++;
        }
        int best = a[0];
        for (int x : a)                       // only the codes this survey used: O(n)
            if (cnt[x] > cnt[best] || (cnt[x] == cnt[best] && x < best)) best = x;
        cout << best << '\n';
        for (int x : a) cnt[x] = 0;           // undo exactly what we touched: O(n), not O(10^6)
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
        int best = -1, bestc = 0;
        for (int v : a) {
            int c = count(a.begin(), a.end(), v);
            if (c > bestc || (c == bestc && v < best)) best = v, bestc = c;
        }
        cout << best << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int cnt[1000001];
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        memset(cnt, 0, sizeof cnt);
        for (int i = 0; i < n; i++) {
            int x;
            cin >> x;
            cnt[x]++;
        }
        int best = 1;
        for (int v = 1; v <= 1000000; v++)
            if (cnt[v] > cnt[best]) best = v;
        cout << best << '\n';
    }
}
""",
    hints=[
        r"""Multiply it out: `t` can be 10^5. Anything your loop body does that costs 10^6
regardless of `n` (clearing an array, scanning all codes) costs 10^11 in total.""",
        r"""The sum of `n` is small, so work proportional to `n` per survey is free. Find the
answer by looking only at the codes that appeared, and clean up only the entries you
incremented. (Sorting each survey's answers also works.)""",
    ],
    editorial=r"""
The line that decides this problem is the last one of the input section: the *sum* of `n`
over all surveys is at most 2·10^5. So the total work may be proportional to that sum, but
nothing may cost 10^6 *per survey*: with 10^5 surveys, one `memset` of a 10^6-entry array
plus one scan over all codes is about 10^11 operations.

A counting array is still the right tool; use it proportionally. Increment `cnt[x]` for
the survey's `n` codes, pick the best among those same `n` codes, then set exactly those
entries back to zero. Every survey costs O(n), everything costs O(sum of n). Sorting each
survey's codes and counting runs (O(n log n) per survey) is just as good here.

The same trap hides in `vector<int> cnt(1000001)` declared inside the loop: it allocates
and zeroes 4 MB per survey.
""",
)

DIVISOR_CLASSES = Problem(
    id="divisor_classes",
    title="Deficient, Perfect, Abundant",
    difficulty="medium",
    complexity="O(n log n)",
    time_limit=1.5,
    statement=r"""
The ancient Greeks sorted numbers by their *proper divisors* (all divisors except the
number itself). A number `k` is **deficient** if its proper divisors add up to less than
`k`, **perfect** if they add up to exactly `k`, and **abundant** if they add up to more.
For example 12 is abundant: 1 + 2 + 3 + 4 + 6 = 16 > 12. The number 1 has no proper
divisors, so it is deficient.

Count the numbers of each kind among 1, 2, ..., n.
""",
    input=r"""
One integer `n` (1 ≤ n ≤ 10^7).
""",
    output=r"""
Three integers on one line: how many of 1..n are deficient, perfect and abundant.
""",
    samples=[
        Test("12\n", "10 1 1\n"),
        Test("30\n", "23 2 5\n"),
    ],
    tests=[
        Test("1\n"),
        Test("6\n"),
        Test("8128\n"),
    ],
    gens=[
        Gen("small n", lambda rng: f"{rng.randint(1, 3000)}\n", 10),
        Gen("medium n", lambda rng: f"{rng.randint(10**5, 10**6)}\n", 2),
        Gen("n = 10^7", lambda rng: "10000000\n", 1, large=True),
        Gen("n near 10^7", lambda rng: f"{rng.randint(9 * 10**6, 10**7)}\n", 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    // s[k] = sum of the proper divisors of k. Instead of asking every k for its divisors,
    // every d adds itself to its multiples 2d, 3d, ...: n/1 + n/2 + ... = O(n log n).
    // The largest s[k] for k <= 10^7 is about 3.6 * 10^7, so int is enough.
    vector<int> s(n + 1, 0);
    for (int d = 1; 2 * d <= n; d++)
        for (int m = 2 * d; m <= n; m += d) s[m] += d;
    long long deficient = 0, perfect = 0, abundant = 0;
    for (int k = 1; k <= n; k++) {
        if (s[k] < k) deficient++;
        else if (s[k] == k) perfect++;
        else abundant++;
    }
    cout << deficient << ' ' << perfect << ' ' << abundant << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    long long def = 0, perf = 0, ab = 0;
    for (int k = 1; k <= n; k++) {
        long long s = 0;
        for (long long d = 1; d * d <= k; d++)
            if (k % d == 0) {
                s += d;
                if (d != k / d) s += k / d;
            }
        s -= k;                                // proper divisors only
        if (s < k) def++; else if (s == k) perf++; else ab++;
    }
    cout << def << ' ' << perf << ' ' << ab << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    long long def = 0, perf = 0, ab = 0;
    for (int k = 1; k <= n; k++) {
        long long s = 0;
        for (long long d = 1; d * d <= k; d++)
            if (k % d == 0) {
                s += d;
                if (d != k / d) s += k / d;
            }
        s -= k;
        if (s < k) def++; else if (s == k) perf++; else ab++;
    }
    cout << def << ' ' << perf << ' ' << ab << '\n';
}
""",
    hints=[
        r"""Trial division up to √k for every `k` costs about (2/3)·n^1.5 ≈ 2·10^10 steps at
n = 10^7. Turn the question around: which numbers is `d` a divisor of?""",
        r"""`d` divides exactly `2d, 3d, 4d, ...` (as a proper divisor). Loop `m = 2*d; m <= n;
m += d` and add `d` to `s[m]`. The total is n/1 + n/2 + ... ≈ n ln n ≈ 1.6·10^8 cheap
additions.""",
    ],
    editorial=r"""
Trial division finds the divisors of one `k` in O(√k), so all of 1..n cost about
(2/3)·n^1.5: roughly 6.7·10^8 steps at n = 10^6 (under half a second here, so it would
squeak through) but 2·10^10 at n = 10^7 (13 seconds here).

Turn the loops inside out. Instead of asking each `k` for its divisors, let each `d` visit
its multiples `2d, 3d, ...` and add itself to their running sums. The inner loop runs
`n/d − 1` times, so the total is about n/1 + n/2 + n/3 + ... + n/n = n·H(n) ≈ n ln n:
about 1.6·10^8 simple additions for n = 10^7, a few tenths of a second.

This is the harmonic-sum pattern: a double loop whose inner bound shrinks like `n/d` is
O(n log n), not O(n^2). The sieve of Eratosthenes is the same loop restricted to primes
`d`, and costs only O(n log log n).
""",
)

PAIR_SUMS = Problem(
    id="pair_sums",
    title="Pairs Summing to x",
    difficulty="medium",
    complexity="O(n log n)",
    statement=r"""
Given `n` positive integers and a target `x`, count the pairs of positions `i < j` with
a_i + a_j = x.
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 2·10^5, 2 ≤ x ≤ 2·10^9).

The second line has `n` integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print the number of pairs.
""",
    samples=[
        Test("6 6\n3 1 5 3 3 2\n", "4\n",
             note="1 + 5 is one pair; the three 3s form three more pairs among themselves."),
        Test("5 10\n5 5 5 5 5\n", "10\n",
             note="Every one of the 5·4/2 = 10 pairs of positions counts. With 2·10^5 equal "
                  "values, that is about 2·10^10 pairs."),
    ],
    tests=[
        Test("1 2\n1\n"),
        Test("5 2000000000\n1000000000 1000000000 1000000000 1000000000 1000000000\n"),
        Test("4 5\n1 2 3 4\n"),
        Test("3 7\n1 1 1\n"),
    ],
    gens=[
        Gen("small random", _pairs_small, 14),
        Gen("medium, many hits", lambda rng: _pairs_hit(rng, 3000, 60), 2),
        Gen("max size, all equal", lambda rng: _pairs_all_equal(rng), 1, large=True),
        Gen("max size, small values", lambda rng: _pairs_hit(rng, 200000, 100000), 1, large=True),
        Gen("max size, big values", lambda rng: _pairs_hit(rng, 200000, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;                              // up to 2 * 10^9: an int holds it, barely
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    sort(a.begin(), a.end());
    long long ans = 0;                        // up to n(n-1)/2, about 2 * 10^10
    int l = 0, r = n - 1;
    // Each step moves l right or r left, and they never move back: O(n) after the sort.
    while (l < r) {
        long long s = a[l] + a[r];
        if (s < x) l++;
        else if (s > x) r--;
        else if (a[l] == a[r]) {              // everything in [l, r] equals x / 2
            long long k = r - l + 1;
            ans += k * (k - 1) / 2;
            break;
        } else {                              // a group of equal lows meets a group of equal highs
            long long cl = 1, cr = 1;
            while (a[l + cl] == a[l]) cl++;
            while (a[r - cr] == a[r]) cr++;
            ans += cl * cr;
            l += cl;
            r -= cr;
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
            if (a[i] + a[j] == x) ans++;
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
    long long x;
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    long long ans = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] + a[j] == x) ans++;
    cout << ans << '\n';
}
""",
    hints=[
        r"""All pairs is n(n−1)/2 ≈ 2·10^10. After sorting, look at the smallest and the largest
value: if their sum is too big, can the largest value be part of *any* pair?""",
        r"""Two pointers `l = 0`, `r = n − 1` on the sorted array: too small, `l++`; too big,
`r--`; equal, count the group of equal values at each end and multiply. Careful when
`a[l] == a[r]`: then any two of the `r − l + 1` equal values form a pair.""",
        r"""Alternative: walk left to right with a `map<long long, int>` of values seen so far and
add `seen[x - a[j]]` before inserting `a[j]`. Either way, the answer needs `long long`:
it can reach about 2·10^10.""",
    ],
    editorial=r"""
Sort, then put `l` at the smallest value and `r` at the largest. If `a[l] + a[r] < x`, then
`a[l]` is too small to pair with anything (everything else is at most `a[r]`), so `l++`.
If the sum is too big, `a[r]` pairs with nothing, so `r--`. If it is exactly `x`, all
copies of `a[l]` pair with all copies of `a[r]`: count both groups, add the product, and
step past both. When `a[l] == a[r]` the whole remaining range is one value `x/2`, and any
two of those `k` copies pair up: `k(k−1)/2`.

Each step moves a pointer inward and none ever moves back, so the loop is O(n) in total
(amortised: a single step can skip a whole group, but all steps together skip each index
once). With the sort, O(n log n). A hash map of counts works too.

Type traps: the answer for 2·10^5 equal values is n(n−1)/2 ≈ 2·10^10, ten times what an
`int` holds, and only the large tests reach it. `x` and `a[l] + a[r]` go up to 2·10^9,
which fits in an `int` with 7% to spare; `long long` for them costs nothing.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp08",
    title="complexity: reading the constraints",
    track="cpp",
    order=8,
    summary="Estimate the operation count before you write code: the 10^8-per-second rule, "
            "what Big-O keeps, reading the intended complexity off the limits, harmonic "
            "sums, amortised loops, and the constants that still decide verdicts.",
    prereqs=["cpp07"],
    tags=["complexity", "big-o", "constraints", "harmonic sum", "amortised", "kadane",
          "two pointers", "time limit"],
    parts=[
        Part("Count before you code", [
            Say(r"""
Python taught you that correct code is the goal. In a contest, correct code that takes a
minute is a Time Limit Exceeded, and you find out only after the 20-minute penalty. So
contest programmers estimate the running time *before* they type anything, from the
limits in the input section.

A running example. **Maximum subarray sum**: given `n` integers (possibly negative), find
the largest sum of a block of consecutive values. Limits: `n ≤ 2·10^5`, `|a_i| ≤ 10^9`,
one second. The first program anyone writes tries every block:

```cpp
for (int l = 0; l < n; l++)
    for (int r = l; r < n; r++) {
        long long s = 0;
        for (int k = l; k <= r; k++) s += a[k];   // the innermost line
        best = max(best, s);
    }
```
"""),
            Numeric(r"""
Count exactly: for `n = 4`, how many times does the innermost line `s += a[k]` run?
""", answer=20, unit="times",
                hint="List the blocks by length: how many blocks of length 1, 2, 3, 4, and how "
                     "much does each cost?",
                explain=r"""
4 blocks of length 1, 3 of length 2, 2 of length 3, 1 of length 4: `4·1 + 3·2 + 2·3 + 1·4
= 20`. In general the count is `n(n+1)(n+2)/6`, which for large `n` is about n^3/6.
"""),
            Numeric(r"""
Now estimate the same count for `n = 2·10^5`. (A rough estimate is fine: within 50%.)
""", answer=1.33e15, rel=0.5, unit="additions",
                hint="Your `n = 4` count was `4·5·6/6`. For large `n`, that is about n^3/6.",
                explain=r"""
`(2·10^5)^3 / 6 = 8·10^15 / 6 ≈ 1.3·10^15`. If your first try was `8·10^15` (n^3), you had
the right shape and dropped the `/6`; for deciding the verdict, both say the same thing:
hopeless.
"""),
            MCQ(r"""
Budget with **10^8 simple operations per second**. How long would 1.3·10^15 additions take?
""", [
                Opt("About 13 seconds.",
                    why="That would be 10^14 per second, a million times faster than the budget. "
                        "Divide again: 1.3·10^15 / 10^8 = 1.3·10^7 seconds."),
                Opt("About 4 hours.",
                    why="4 hours is about 1.4·10^4 seconds. The quotient is 1.3·10^7 seconds, a "
                        "thousand times longer."),
                Opt("About 150 days.", correct=True,
                    why="Right: 1.3·10^7 seconds. No compiler flag or faster machine closes a gap "
                        "of seven orders of magnitude; only a different algorithm does."),
                Opt("It depends on how fast the judge machine is.",
                    why="Judges differ by a factor of 2 or 3. The gap here is a factor of 10^7."),
            ]),
            Say(r"""
Why **10^8**? It is a deliberately pessimistic planning number, not a measurement. A tight
loop of additions on this judge runs about 2·10^9 per second, while a loop full of
`map` lookups, divisions or cache misses manages 10^7 to 10^8. The estimate you make
from the limits is itself only good to a factor of a few. So:

| your estimate | verdict you should expect |
| up to ~10^7 | safe, even with heavy operations |
| ~10^8 | fine for simple loops over arrays |
| ~10^9 | only if the inner loop is trivial; think twice |
| 10^10 and up | too slow: change the algorithm |

For comparison, CPython runs a bare `for` loop at roughly 2.5·10^7 iterations per second
here (10^7 additions in 0.4 s). That factor of 40 to 100 is why C++ is the contest language.
"""),
        ]),
        Part("Stop recomputing: n^3, then n^2, then n", [
            Reflect(r"""
The triple loop computes the sum of `a[l..r]` from scratch for every `r`. What does it
recompute, and what is the cheaper way to get the sum of `a[l..r]` if you already know the
sum of `a[l..r-1]`?
""", answer=r"""
For a fixed `l`, the sum of `a[l..r]` is the sum of `a[l..r-1]` plus `a[r]`, but the loop
re-adds `a[l..r-1]` from the start every time. Keep a running sum per left end: `s += a[r]`
as `r` advances. That removes the innermost loop and makes the program O(n^2).
"""),
            Numeric(r"""
With the running sum, the program has two nested loops, `l` from 0 and `r` from `l`. About
how many times does the inner body run for `n = 2·10^5`?
""", answer=2e10, rel=0.5, unit="times",
                explain=r"""
`n(n+1)/2 ≈ 2·10^10`. By the budget, 200 seconds. Measured on this judge, where the loop
body is two instructions: about 10 seconds. Better than 150 days and still ten times over
the limit. Quadratic is dead at `n = 2·10^5`; you need about `n` or `n log n`.
"""),
            MCQ(r"""
Aim for one pass. Let `cur(i)` be the largest sum of a block that **ends exactly at**
position `i`. If you know `cur(i−1)`, what is `cur(i)`?
""", [
                Opt("`cur(i−1) + a[i]`",
                    why="That forces the block to extend the previous one. If `cur(i−1) = −8` and "
                        "`a[i] = 3`, the block `[3]` alone is better than `−5`."),
                Opt("`max(cur(i−1), a[i])`",
                    why="`cur(i−1)` is a block that ends at `i − 1`, not at `i`. The block ending at "
                        "`i` must contain `a[i]`."),
                Opt("`max(a[i], cur(i−1) + a[i])`", correct=True,
                    why="Yes. A block ending at `i` is either `a[i]` alone, or a block ending at "
                        "`i − 1` plus `a[i]`, and the best of those is `cur(i−1) + a[i]`."),
                Opt("`max(0, cur(i−1)) + a[i] + a[i+1]`",
                    why="`cur(i)` is about blocks ending at `i`; `a[i+1]` belongs to `cur(i+1)`."),
            ], explain=r"""
Every block ends somewhere, so the answer is the largest `cur(i)` over all `i`. This is
**Kadane's algorithm**: O(n) time, O(1) memory. The move that produced it (name the
quantity that ends at `i`, then express it through `i − 1`) is the heart of dynamic
programming, which the algorithms track builds on.
"""),
            Short(r"""
Trace it on `a = [2, -5, 3, -1, 4, -7, 2]`. Write the seven values of `cur`, separated by
spaces.
""", accept=["2 -3 3 2 6 -1 2"], placeholder="seven numbers",
                hint="`cur` starts as `a[0] = 2`. Next: `max(-5, 2 + -5)`.",
                explain=r"""
`2 -3 3 2 6 -1 2`. The largest is 6, the block `3, -1, 4`. Notice where `cur` restarts:
at index 2, where `-3 + 3 = 0` loses to `3` on its own.
"""),
            MCQ(r"""
A classmate writes `long long cur = 0, best = 0;` and then, for every `x`,
`cur = max(x, cur + x); best = max(best, cur);`. Which input breaks it?
""", [
                Opt("`3` / `-3 -1 -2`, where every value is negative.", correct=True,
                    why="Yes: `best` starts at 0 and nothing negative beats it, so it prints 0. "
                        "But a block must be non-empty, and the right answer is −1. Start `best` "
                        "at `LLONG_MIN` or at the first `cur`."),
                Opt("`5` / `1 2 3 4 5`, where the best block is everything.",
                    why="All positive: `cur` never restarts, and `best` ends at 15, which is right."),
                Opt("`3` / `1000000000 1000000000 1000000000`.",
                    why="The sum 3·10^9 would overflow an `int`, but these are `long long`: prints "
                        "3000000000, correctly."),
            ], explain=r"""
Initial values are part of the algorithm. "Maximum over a non-empty set" starts at minus
infinity or at the first element; "sum over a possibly empty set" starts at 0.
"""),
            Try("max_subarray", note="Kadane, `long long`, and a correct starting value for `best`. "
                "The naive double loop is the thing the large tests are there to reject."),
        ]),
        Part("Big-O: what survives", [
            Say(r"""
Big-O keeps only what decides the verdict. `n(n+1)(n+2)/6` becomes O(n^3): lower-order
terms vanish next to the leading one, and constant factors (the `/6`) are dropped because
they change the time by a factor, not by an order of magnitude. At `n = 2·10^5`, the gap
between O(n^2) and O(n log n) is a factor of 10^4; no constant is that big.

The one factor that looks scary and is not: **log n**. `log2(10^6) ≈ 20`, and
`log2(2·10^5) ≈ 18`. A log factor costs about 20x, which is why O(n log n) passes for
`n` up to 10^6, and why sorting is almost free.
"""),
            MCQ(r"""
Which fragment is O(n log n)?

```cpp
// A
for (int i = 0; i < n; i++)
    for (int j = 0; j < i; j++) work();
// B
for (int i = 0; i < n; i++)
    for (int j = 1; j < n; j *= 2) work();
// C
for (int i = n; i > 0; i /= 2)
    for (int j = 0; j < i; j++) work();
// D
for (int i = 0; i < n; i++)
    for (int j = 0; j < 100; j++) work();
```
""", [
                Opt("A",
                    why="0 + 1 + ... + (n−1) = n(n−1)/2. The `/2` is a constant: O(n^2)."),
                Opt("B", correct=True,
                    why="Yes: `j` doubles, so the inner loop runs about log2(n) times, for each of "
                        "the `n` values of `i`."),
                Opt("C",
                    why="It looks like it, but the inner loop runs `n + n/2 + n/4 + ...` times in "
                        "total, and that sum is below `2n`. C is O(n)."),
                Opt("D",
                    why="100 is a constant: O(100n) = O(n). Constants matter a little in practice "
                        "(100n for n = 10^7 is 10^9), but the class is O(n)."),
            ]),
            Numeric(r"""
Fragment C with `n = 1024`: how many times does `work()` run in total?
""", answer=2047, unit="times",
                explain=r"""
`1024 + 512 + ... + 2 + 1 = 2047 = 2n − 1`. A geometric series is dominated by its first
term. The same argument shows that `vector` doubling costs O(1) per `push_back` on
average, which comes back later in this lesson.
"""),
            Numeric(r"""
How many times does this loop run for `n = 10^6`?

```cpp
for (int i = n; i > 0; i /= 2) steps++;
```
""", answer=20, unit="times",
                explain=r"""
`10^6, 5·10^5, ..., 1`: halving takes 20 steps to reach 0 from 10^6, since 2^20 ≈ 10^6.
Anything that halves (binary search, a segment tree walk, fast exponentiation) is
O(log n) and costs about 20 to 60 steps for any size a contest can give you.
"""),
            Numeric(r"""
Sorting costs about `n log2 n` comparisons. For `n = 2·10^5`, roughly how many?
""", answer=3.5e6, rel=0.5, unit="comparisons",
                explain=r"""
`2·10^5 · 18 ≈ 3.6·10^6`: a few milliseconds. When in doubt, sort. It is almost never the
bottleneck at contest sizes.
"""),
        ]),
        Part("Reading the limits backwards", [
            Say(r"""
Problem setters choose the limits so that the intended solution passes comfortably and the
obvious slower one does not. That makes the limits a *hint*: the size of `n` tells you
which complexity the setter has in mind, before you have any idea how to solve the problem.
"""),
            MCQ(r"""
A problem says `n ≤ 5000`, one second. Which complexity is the setter inviting?
""", [
                Opt("O(n^3)",
                    why="5000^3 = 1.25·10^11: over 1000 seconds on the budget."),
                Opt("O(n^2)", correct=True,
                    why="Yes: 5000^2 = 2.5·10^7, comfortable even with a heavy loop body. The "
                        "limit stops just where n^2 stops being comfortable."),
                Opt("O(n log n)",
                    why="It would pass, of course, but then why stop at 5000? A setter who wanted "
                        "n log n would allow 2·10^5 or 10^6. Small limits usually mean the fast "
                        "solution is not known or not needed."),
                Opt("O(2^n)",
                    why="2^5000 is a number with 1506 digits. Exponential algorithms need n ≤ 20 "
                        "or so."),
            ]),
            Say(r"""
The same arithmetic, run for every common limit, gives the table contest programmers carry
in their heads:

| `n` up to | affordable | typically |
| 10 | O(n!) | all permutations (10! ≈ 3.6·10^6) |
| 20 | O(2^n · n) | all subsets (2^20 ≈ 10^6) |
| 500 | O(n^3) | triple loops, Floyd-Warshall |
| 5000 | O(n^2) | double loops, quadratic DP |
| 10^5 to 10^6 | O(n log n) | sorting, binary search, heaps, trees |
| 10^7 to 10^8 | O(n) | one tight pass, a sieve |
| 10^9 and beyond | O(√n), O(log n), O(1) | math, binary search on the answer |

Read it in both directions: from a limit to an intended complexity, and from an idea to
"will it pass?".
"""),
            MCQ(r"""
`n ≤ 10^12`. What is the *slowest* complexity that still fits in one second?
""", [
                Opt("O(n)",
                    why="10^12 steps: hours. Not even a trivial loop can count that far in a second."),
                Opt("O(n / log n)",
                    why="10^12 / 40 = 2.5·10^10: still hundreds of seconds."),
                Opt("O(√n)", correct=True,
                    why="Yes: √10^12 = 10^6. Trial division up to √n is the classic example: "
                        "factorising one number up to 10^12."),
                Opt("O(log n)",
                    why="It fits (about 40 steps), but it is not the slowest one that fits. When "
                        "the limit is 10^12 rather than 10^18, √n is often what is intended."),
            ]),
            MCQ(r"""
The input section says: `t ≤ 10^4` test cases, each with `n ≤ 2·10^5`, and **the sum of
`n` over all test cases is at most 2·10^5**. Your solution is O(n^2) per test case. Safe?
""", [
                Opt("Yes: the average test has only 20 elements, and 20^2 is tiny.",
                    why="The judge does not send average tests. The sum limit also allows a single "
                        "test with `n = 2·10^5`, and that one costs 4·10^10."),
                Opt("No: one test case may use the whole budget, n = 2·10^5.", correct=True,
                    why="Right. The sum limit bounds the *total* of per-test costs that are linear "
                        "(or n log n) in that test's `n`; it does nothing for a quadratic one."),
                Opt("Yes, because 10^4 · 20^2 = 4·10^6.",
                    why="That is the cost if every test is equally small. The worst case "
                        "concentrates everything in one test."),
            ]),
            Numeric(r"""
Same constraints, but now `t ≤ 10^5` (so most tests are tiny) and values go up to 10^6.
Your per-test code does `memset(cnt, 0, sizeof cnt)` on an array of 10^6 counters, then
scans all 10^6 of them for the answer. Roughly how many operations in total, worst case?
""", answer=2e11, rel=0.5, unit="operations",
                hint="Per test: clearing 10^6 plus scanning 10^6. Then multiply by the number of "
                     "tests.",
                explain=r"""
`10^5 tests · 2·10^6 = 2·10^11`. The `n` values are tiny, but the loop body costs 10^6
*regardless of n*. Rule: with "the sum of `n` is bounded", every per-test cost must be
proportional to that test's `n`, never to the maximum value or the maximum size. Undo
only what the test touched.
"""),
            Try("most_common", note="The trap is in the last line of the input section."),
        ]),
        Part("Double loops that are not n^2", [
            Say(r"""
Here is a task where the obvious bound on a double loop is badly wrong. For every
`k ≤ n`, compute σ(k), the sum of the divisors of `k`.

Per number, trial division up to √k finds all divisors (they come in pairs `d` and
`k/d`). Summed over all `k`, that is about (2/3)·n^1.5: 6.7·10^8 steps for n = 10^6,
2·10^10 for n = 10^7.
"""),
            Reflect(r"""
Trial division asks every `k`: "which `d` divide you?". Turn the question around. What
could each `d` do instead, and why is that cheaper?
""", answer=r"""
Each `d` knows exactly which numbers it divides: `d, 2d, 3d, ...`. So loop over `d`, and
for each `d` walk its multiples, adding `d` to `sigma[m]`. No division, no failed tests:
every step of the inner loop does useful work, and the inner loop for `d` has only `n/d`
steps, which is short for all but the smallest `d`.
"""),
            Say(r"""
In code:

```cpp
vector<long long> sigma(n + 1, 0);
for (int d = 1; d <= n; d++)
    for (int m = d; m <= n; m += d)
        sigma[m] += d;
```

A double loop over `n` and `n`, apparently. Count it before you believe it.
"""),
            Numeric(r"""
For `n = 12`, how many times does `sigma[m] += d` run in total?
""", answer=35, unit="times",
                hint="For `d = 1` the inner loop runs 12 times, for `d = 2` six times, ... "
                     "For `d = 7..12`, once each.",
                explain=r"""
`12 + 6 + 4 + 3 + 2 + 2 + 1 + 1 + 1 + 1 + 1 + 1 = 35`, compared with `12^2 = 144` for a
full double loop. The inner loop for `d` runs `⌊n/d⌋` times.
"""),
            MCQ(r"""
In general the count is `n/1 + n/2 + n/3 + ... + n/n`. What is that, asymptotically?
""", [
                Opt("O(n^2): the average inner loop is n/2 long.",
                    why="The *first* inner loop is `n` long, but the lengths fall off fast: half "
                        "of all `d` have loops of length 1. The average length is about ln n, not "
                        "n/2."),
                Opt("O(n log n)", correct=True,
                    why="Yes. It is `n · (1 + 1/2 + ... + 1/n)`, and the harmonic sum "
                        "`1 + 1/2 + ... + 1/n` is about ln n."),
                Opt("O(n √n)",
                    why="That is the trial-division approach. The multiples loop is much cheaper: "
                        "for n = 10^6, 1.4·10^7 steps against 6.7·10^8."),
                Opt("O(n): each number is visited once.",
                    why="Each `m` is visited once *per divisor*, and numbers have on average "
                        "about ln n divisors."),
            ]),
            Numeric(r"""
Estimate `n/1 + n/2 + ... + n/n` for `n = 10^6`. (Use ln(10^6) ≈ 13.8.)
""", answer=1.4e7, rel=0.5, unit="steps",
                explain=r"""
`10^6 · 13.8 ≈ 1.4·10^7`. The exact sum is 13,970,034. For `n = 10^7` it is about
1.6·10^8: still fine, while trial division has grown to 2·10^10.
"""),
            MCQ(r"""
And this one, which differs only in its inner loop?

```cpp
for (int d = 1; d <= n; d++)
    for (int m = 1; m <= n; m++)
        if (m % d == 0) sigma[m] += d;
```
""", [
                Opt("O(n log n), the same harmonic sum.",
                    why="The *additions* happen n log n times, but the loop visits every `m` for "
                        "every `d` to find out: n^2 iterations, each with a division."),
                Opt("O(n^2)", correct=True,
                    why="Right. The harmonic bound comes from *jumping* to the next multiple "
                        "(`m += d`), not from the `if`. Filtering is not skipping."),
                Opt("O(n √n)",
                    why="Nothing here stops at √n: both loops run to `n`."),
            ], explain=r"""
Count the iterations of the loop, not the times the interesting line runs. Work that finds
out that there is nothing to do is still work.
"""),
            Try("divisor_classes", note="Up to 10^7. Trial division is about 13 seconds here; the "
                "harmonic loop, a few tenths."),
        ]),
        Part("Amortised: n steps in total", [
            Say(r"""
Another double loop that lies. Given positive `a_i`, find the longest block with sum at
most `S`:

```cpp
long long sum = 0;
int l = 0, best = 0;
for (int r = 0; r < n; r++) {
    sum += a[r];
    while (sum > S) sum -= a[l++];     // shrink from the left
    best = max(best, r - l + 1);
}
```

The `while` can run many times for one `r`.
"""),
            Numeric(r"""
For `n = 2·10^5`, what is the largest possible total number of runs of the `while` body,
over the whole program?
""", answer=2e5, rel=0.1, unit="runs",
                hint="Each run does `l++`. Where does `l` start, can it ever decrease, and how far "
                     "can it go?",
                explain=r"""
At most `n`. Each run increments `l`, `l` never decreases, and it cannot pass `n`. One
`r` may trigger many runs, but then later `r`s trigger fewer: the total is bounded, so the
whole loop is O(n). This is an **amortised** bound: not a bound per iteration, but on the
sum over all iterations, found by asking what can only move forward.
"""),
            Numeric(r"""
A `vector` doubles its capacity when it is full, copying the old elements into the new
buffer. Starting empty, you `push_back` 2^20 elements. About how many element copies
do the reallocations make in total?
""", answer=1048575, rel=0.5, unit="copies",
                hint="Reallocations happen at sizes 1, 2, 4, ..., 2^19. Each copies the elements it "
                     "already has.",
                explain=r"""
`1 + 2 + 4 + ... + 2^19 = 2^20 − 1 ≈ 10^6` (measured here with a copy-counting type:
exactly 1,048,575 extra copies over 21 reallocations). Fewer than one extra copy per
element: `push_back` is **amortised O(1)**, even though one unlucky call copies half a
million elements.
"""),
            MCQ(r"""
Each loop runs `n = 2·10^5` times. Which one is O(n^2) in total?
""", [
                Opt("`v.push_back(x);`",
                    why="Amortised O(1), as you just computed."),
                Opt("`s += c;` on a `string`",
                    why="Appends in place, with doubling like `vector`: amortised O(1)."),
                Opt("`v.insert(v.begin(), x);`", correct=True,
                    why="Yes. Inserting at the front shifts every element each time: 1 + 2 + ... + n "
                        "≈ 2·10^10 moves. Push to the back and reverse once, or use a `deque`."),
                Opt("`while (!st.empty() && st.top() < x) st.pop(); st.push(x);`",
                    why="Each element is pushed once and popped at most once, so all the pops "
                        "together are at most `n`: amortised O(1), the same argument as the two "
                        "pointers."),
            ], explain=r"""
Its Python twin is `lst.insert(0, x)`, also O(n) per call. The same goes for `s = s + c`
(copies the whole string, unlike `s += c`) and `v.erase(v.begin())` in a loop.
"""),
            Say(r"""
Two pointers also count pairs. To count pairs with `a_i + a_j = x`, sort, and start `l`
at the smallest value and `r` at the largest. If `a[l] + a[r] < x`, then `a[l]` is too
small to reach `x` even with the largest partner, so `l++`. If the sum is too big, `a[r]`
is too big even with the smallest partner, so `r--`. When it equals `x`, count and move
both. Every step moves one pointer inward, so after the O(n log n) sort the scan is O(n).
"""),
            MCQ(r"""
The limits are `n ≤ 2·10^5`, `a_i ≤ 10^9`, `x ≤ 2·10^9`. Which of these *must* be a
`long long`?
""", [
                Opt("`x`",
                    why="2·10^9 is below `INT_MAX` = 2147483647, by 7%. It fits, barely; making it "
                        "`long long` costs nothing and removes the worry, but it is not forced."),
                Opt("`a[l] + a[r]`",
                    why="At most 10^9 + 10^9 = 2·10^9: fits, with the same thin margin as `x`. One "
                        "more addition and it would not."),
                Opt("The pointers `l` and `r`.",
                    why="They are indices below 2·10^5: `int` is right."),
                Opt("The answer counter.", correct=True,
                    why="Yes. With 2·10^5 equal values and `x` twice that value, every pair counts: "
                        "n(n−1)/2 ≈ 2·10^10, ten times `INT_MAX`."),
            ], explain=r"""
Check every quantity against the limits, including the ones that come out "just fits": a
sum of two values up to 10^9 fits in `int` and a sum of three does not. The quantity that
grows fastest here is the one people forget: the count.
"""),
            Try("pair_sums", note="Sort plus two pointers (or a map of counts). The large tests "
                "include 2·10^5 equal values."),
        ]),
        Part("Constants that still matter", [
            MCQ(r"""
Count how often each of 10^6 random values in `[0, 10^6)` occurs, then read every count
back once. Four implementations. Which is the slowest by far?
""", [
                Opt("A `vector<int>` of size 10^6, indexed by value.",
                    why="The fastest: one array access per operation, and the array stays in cache."),
                Opt("`unordered_map<int, int>`",
                    why="Hashing costs something (about 20x the array here), but it is O(1) per "
                        "operation and far from the slowest."),
                Opt("`map<int, int>`", correct=True,
                    why="Yes. Each access walks a balanced tree about 20 levels deep, jumping "
                        "between nodes scattered in memory: a cache miss per level."),
                Opt("Sort a copy, then count runs of equal values.",
                    why="Sorting 10^6 ints takes a few tens of milliseconds: slower than the array, "
                        "much faster than a tree."),
            ]),
            Say(r"""
Measured on this judge, for exactly that task (10^6 inserts and 10^6 lookups):

| method | time |
| array indexed by value | about 2 ms |
| `unordered_map` | about 35 ms |
| sort, then scan | about 50 ms |
| `map` | about 550 ms |

Same problem, answers identical, and a factor of 300 between the extremes. Big-O puts
`map` at O(log n) per operation, which sounds cheap; the constant hidden in that O is a
cache miss per tree level. So: an array when the keys are small integers, `unordered_map`
or sort-and-scan when they are not, and `map` when you need order.
"""),
            Numeric(r"""
Using the table, roughly how long do 10^7 `map` operations take? (The table's `map` row
is 2·10^6 operations.)
""", answer=2.75, rel=0.5, unit="seconds",
                explain=r"""
`550 ms · 5 ≈ 2.75 s`. So an O(n log n) solution built on `map` can TLE at `n = 10^7`
while the same algorithm on a sorted array passes. Big-O decides whether you are in the
right ballpark; the constant decides the close calls.
"""),
            MCQ(r"""
Your solution has the right complexity but prints 10^6 lines and gets TLE. Which change
is most likely to fix it without touching the algorithm?
""", [
                Opt("Use `int` instead of `long long` everywhere.",
                    why="64-bit arithmetic costs about the same as 32-bit on modern CPUs, and it "
                        "risks overflow. Not where the time goes."),
                Opt("Replace `endl` with `'\\n'`, and add the two fast-I/O lines.", correct=True,
                    why="Yes. cpp01 measured it: a million `endl`s cost about a second by "
                        "themselves, and unsynchronised streams save almost another."),
                Opt("Replace every `vector` with a plain C array.",
                    why="With -O2, indexing a `vector` compiles to the same instructions as a C "
                        "array. There is nothing to gain."),
                Opt("Pass `-O3` or add optimisation pragmas.",
                    why="You do not control the judge's flags, and pragmas rarely give more than a "
                        "small factor. They cannot rescue flushing a million times."),
            ]),
            Reflect(r"""
Your estimate for an idea comes out at about 3·10^8 operations, and the limit is one
second. What do you look at before deciding whether to code it?
""", answer=r"""
What one "operation" is. If the inner loop is a few additions over an array walked in
order, 3·10^8 runs in a few tenths of a second and the idea is fine. If each step is a
`map` lookup, a division, a hash, or a jump to a random place in a big array, it can be 10
to 100 times slower, and 3·10^8 is hopeless. Also check that the estimate is the worst
case the limits allow, and whether a clearly better complexity is within reach: if it is,
prefer it to a close call.
"""),
        ]),
    ],
    problems=[MAX_SUBARRAY, MOST_COMMON, DIVISOR_CLASSES, PAIR_SUMS],
    cards=[
        Card(r"""The planning speed for contest C++, and for CPython?""",
             r"""Budget about 10^8 simple operations per second in C++ (tight array loops reach 10^9; `map`/division-heavy code 10^7). CPython: a few 10^7 per second at best."""),
        Card(r"""From the limit on `n` to the intended complexity: 10, 20, 500, 5000, 10^6, 10^12?""",
             r"""n ≤ 10: n!; n ≤ 20: 2^n·n; n ≤ 500: n^3; n ≤ 5000: n^2; n ≤ 10^6: n log n; n ≤ 10^12: √n (larger: log n)."""),
        Card(r"""log2 of 10^6, of 2·10^5, and of 10^18, roughly?""",
             r"""About 20, 18 and 60. 2^10 ≈ 10^3, 2^20 ≈ 10^6, 2^30 ≈ 10^9, 2^60 ≈ 10^18."""),
        Card(r"""What does `for (d = 1; d <= n; d++) for (m = d; m <= n; m += d)` cost?""",
             r"""n/1 + n/2 + ... + n/n ≈ n ln n (harmonic sum): about 1.4·10^7 for n = 10^6. O(n log n), not O(n^2)."""),
        Card(r"""`for (i = n; i > 0; i /= 2) for (j = 0; j < i; j++)`: complexity?""",
             r"""O(n): the inner loops total n + n/2 + n/4 + ... < 2n. A geometric series is dominated by its first term."""),
        Card(r"""Kadane's recurrence for the maximum subarray sum?""",
             r"""`cur = max(a[i], cur + a[i]); best = max(best, cur);` with `best` starting at `LLONG_MIN` (subarrays are non-empty). O(n)."""),
        Card(r""""The sum of n over all test cases is at most 2·10^5": what must every per-test cost be?""",
             r"""Proportional to that test's `n` (or n log n). Never O(max value) or O(max n) per test: clearing a 10^6 array per test with t = 10^5 is 10^11."""),
        Card(r"""Why is the two-pointer loop `for r ... while (cond) l++;` O(n) in total?""",
             r"""`l` only moves forward and stops at `n`, so the `while` body runs at most `n` times over the whole program (amortised), however it is distributed among the `r`s."""),
        Card(r"""Why is `push_back` O(1) amortised?""",
             r"""Capacity doubles when full, so n pushes cause copies of 1 + 2 + 4 + ... < n elements in total: less than one extra copy per element."""),
        Card(r"""Counting 10^6 small-integer keys: array vs `unordered_map` vs `map`, measured?""",
             r"""About 2 ms, 35 ms and 550 ms. Use an array for small integer keys; `map` pays a cache miss per tree level."""),
        Card(r"""Name three loops that are O(n) per call, so O(n^2) when repeated n times.""",
             r"""`v.insert(v.begin(), x)`, `v.erase(v.begin())`, `s = s + c` (copies the string; `s += c` does not)."""),
    ],
)
