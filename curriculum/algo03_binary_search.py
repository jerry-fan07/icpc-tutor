from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _machines(rng, n, kmax, t):
    return f"{n} {t}\n" + " ".join(str(rng.randint(1, kmax)) for _ in range(n)) + "\n"


def _machines_ones(rng, n, t):
    """Mostly k = 1 plus one slow machine: a generic hi (10^18, or max(k)·t) makes the
    unguarded sum in ok() overflow long before the answer (about t/n) is reached."""
    k = [1] * (n - 1) + [10**9]
    rng.shuffle(k)
    return f"{n} {t}\n" + " ".join(map(str, k)) + "\n"


def _division(rng, n, k, vmax):
    return f"{n} {k}\n" + " ".join(str(rng.randint(1, vmax)) for _ in range(n)) + "\n"


def _division_small(rng):
    n = rng.randint(1, 8)
    return _division(rng, n, rng.randint(1, n), 20)


def _stalls(rng, n, c, span):
    xs = rng.sample(range(span + 1), n)
    return f"{n} {c}\n" + " ".join(map(str, xs)) + "\n"


def _stalls_small(rng):
    n = rng.randint(2, 9)
    return _stalls(rng, n, rng.randint(2, n), 40)


def _avg(rng, n, L, lo, hi):
    return f"{n} {L}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _avg_small(rng):
    n = rng.randint(1, 10)
    return _avg(rng, n, rng.randint(1, n), -20, 20)


def _avg_needle(rng, n, L):
    """A sea of -10^4 with one stretch of small values: the answer is near 0 while the
    shifted prefix sums reach about n·10^4, which is where floating point gets tested."""
    a = [-10**4] * n
    w = rng.randint(L, min(n, L + 50))
    s = rng.randint(0, n - w)
    for i in range(s, s + w):
        a[i] = rng.randint(-3, 4)
    return f"{n} {L}\n" + " ".join(map(str, a)) + "\n"


# --------------------------------------------------------------------- problems
FACTORY = Problem(
    id="factory_machines",
    title="Factory Machines",
    difficulty="medium",
    source="CSES 1620 - Factory Machines",
    complexity="O(n log(min k · t))",
    statement=r"""
A factory has `n` machines that work in parallel. Machine `i` needs `k_i` seconds to make one
product, so it finishes products at times `k_i, 2k_i, 3k_i, ...`.

What is the shortest time in which the machines can make `t` products in total?
""",
    input=r"""
The first line has `n` and `t` (1 ≤ n ≤ 2·10^5, 1 ≤ t ≤ 10^9).

The second line has `n` integers k_1, ..., k_n (1 ≤ k_i ≤ 10^9).
""",
    output=r"""
Print one integer: the minimum time.
""",
    samples=[
        Test("3 7\n3 2 5\n", "8\n",
             note="By time 8 the machines have made 2 + 4 + 1 = 7 products; by time 7 only 6."),
        Test("1 1000000000\n1000000000\n", "1000000000000000000\n",
             note="The answer itself can be 10^18."),
    ],
    tests=[
        Test("1 1\n1\n"),
        Test("3 1000000000\n1 1000000000 1000000000\n"),
        Test("50 1000\n" + " ".join(["1"] * 50) + "\n"),
        Test("2 5\n1000000000 1\n"),
    ],
    gens=[
        # small but flagged large: the brute (a t-step simulation) cannot handle t = 10^9
        Gen("forty machines, t = 10^9", lambda rng: "40 1000000000\n" + " ".join(["1"] * 39 + ["1000000000"]) + "\n", 1, large=True),
        Gen("small random", lambda rng: _machines(rng, rng.randint(1, 6), 10, rng.randint(1, 40)), 15),
        Gen("medium random", lambda rng: _machines(rng, 1000, 1000, 100000), 2),
        Gen("max size, random", lambda rng: _machines(rng, 200000, 10**9, 10**9), 1, large=True),
        Gen("max size, all slow", lambda rng: "200000 1000000000\n" + " ".join(["1000000000"] * 200000) + "\n", 1, large=True),
        Gen("max size, fast machines and one slow", lambda rng: _machines_ones(rng, 200000, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long t;
    cin >> n >> t;
    vector<long long> k(n);
    for (auto& v : k) cin >> v;

    auto ok = [&](long long T) {              // are T seconds enough for t products?
        long long made = 0;
        for (long long v : k) {
            made += T / v;
            if (made >= t) return true;       // stop before the sum can overflow
        }
        return false;
    };

    // invariant: ok(lo) is false, ok(hi) is true
    long long lo = 0, hi = *min_element(k.begin(), k.end()) * t;
    while (hi - lo > 1) {
        long long mid = lo + (hi - lo) / 2;
        if (ok(mid)) hi = mid;
        else lo = mid;
    }
    cout << hi << '\n';                       // the first time that is enough
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    long long t;
    cin >> n >> t;
    // simulate: pop the next product to be finished, t times
    priority_queue<pair<long long, long long>, vector<pair<long long, long long>>, greater<>> pq;
    for (int i = 0; i < n; i++) {
        long long k;
        cin >> k;
        pq.push({k, k});
    }
    long long last = 0;
    for (long long i = 0; i < t; i++) {
        auto [when, k] = pq.top();
        pq.pop();
        last = when;
        pq.push({when + k, k});
    }
    cout << last << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long t;
    cin >> n >> t;
    vector<long long> k(n);
    for (auto& v : k) cin >> v;
    for (long long T = 1;; T++) {             // try every time in order
        long long made = 0;
        for (long long v : k) {
            made += T / v;
            if (made >= t) break;
        }
        if (made >= t) {
            cout << T << '\n';
            return 0;
        }
    }
}
""",
    hints=[
        r"""For a fixed time `T`, the number of products is `Σ ⌊T / k_i⌋`. If `T` is enough, what
about `T + 1`?""",
        r"""Binary search on `T` with `lo = 0` (not enough) and `hi = min(k) · t` (enough).""",
        r"""The sum in the check can overflow when `T` is huge and the `k_i` are small: return as
soon as it reaches `t`.""",
    ],
    editorial=r"""
The number of products made by time `T` is `count(T) = Σ ⌊T / k_i⌋`, which never decreases as
`T` grows. So "is `T` enough?" is false, false, ..., true, true, and the answer is the first
true: binary search on the answer. Keep `ok(lo)` false and `ok(hi)` true: `lo = 0` makes
nothing, and `hi = min(k) · t` is enough because the fastest machine alone makes `t`
products by then. Loop while `hi − lo > 1`, move the end that `mid` just proved, print `hi`.

About 60 iterations of O(n): O(n log(min(k) · t)). The traps are all about size. The answer
reaches 10^18, so `long long`. And with a generic `hi = 10^18` (or `max(k) · t`), a check
at `mid ≈ 5·10^17` with thousands of `k_i = 1` machines sums to around 10^23 and overflows,
which can make the check answer "not enough" and send the search the wrong way. Returning as
soon as the sum reaches `t` fixes it and saves time as well.
""",
)

ARRAY_DIVISION = Problem(
    id="array_division",
    title="Array Division",
    difficulty="medium",
    source="CSES 1085 - Array Division",
    complexity="O(n log Σa)",
    statement=r"""
You are given an array of `n` positive integers. Cut it into `k` contiguous, non-empty pieces
so that the largest sum of a piece is as small as possible.

Print that smallest possible largest sum.
""",
    input=r"""
The first line has `n` and `k` (1 ≤ k ≤ n ≤ 2·10^5).

The second line has `n` integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print one integer: the minimum possible maximum piece sum.
""",
    samples=[
        Test("5 3\n2 4 7 3 5\n", "8\n", note="`[2 4] [7] [3 5]`."),
        Test("6 3\n5 2 4 7 1 3\n", "11\n"),
    ],
    tests=[
        Test("1 1\n1000000000\n"),
        Test("2 2\n1 10\n"),
        Test("3 2\n1 10 1\n"),
        Test("4 4\n5 1 9 2\n"),
        Test("5 1\n1000000000 1000000000 1000000000 1000000000 1000000000\n"),
        Test("6 2\n1 1 1 1 1 100\n"),
    ],
    gens=[
        Gen("small random", _division_small, 15),
        Gen("medium random", lambda rng: _division(rng, 300, rng.randint(1, 300), 10**9), 3),
        Gen("max size, random k", lambda rng: _division(rng, 200000, rng.randint(1, 200000), 10**9), 1, large=True),
        Gen("max size, k = 2", lambda rng: _division(rng, 200000, 2, 10**9), 1, large=True),
        Gen("max size, k = n", lambda rng: _division(rng, 200000, 200000, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<long long> a(n);
    long long mx = 0, total = 0;
    for (auto& v : a) {
        cin >> v;
        mx = max(mx, v);
        total += v;
    }

    auto ok = [&](long long S) {              // at most k pieces, each with sum <= S?
        int pieces = 1;
        long long cur = 0;
        for (long long v : a) {
            if (cur + v > S) {                // v starts a new piece (it fits alone: S >= mx)
                pieces++;
                cur = 0;
            }
            cur += v;
        }
        return pieces <= k;
    };

    // invariant: ok(lo) false (the largest element alone exceeds it), ok(hi) true (one piece)
    long long lo = mx - 1, hi = total;
    while (hi - lo > 1) {
        long long mid = lo + (hi - lo) / 2;
        if (ok(mid)) hi = mid;
        else lo = mid;
    }
    cout << hi << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, k;
    cin >> n >> k;
    vector<long long> pre(n + 1, 0);
    for (int i = 1; i <= n; i++) {
        long long v;
        cin >> v;
        pre[i] = pre[i - 1] + v;
    }
    // dp[j][i]: best largest sum when the first i elements form exactly j pieces
    const long long INF = LLONG_MAX;
    vector<vector<long long>> dp(k + 1, vector<long long>(n + 1, INF));
    dp[0][0] = 0;
    for (int j = 1; j <= k; j++)
        for (int i = j; i <= n; i++)
            for (int p = j - 1; p < i; p++)
                if (dp[j - 1][p] != INF)
                    dp[j][i] = min(dp[j][i], max(dp[j - 1][p], pre[i] - pre[p]));
    cout << dp[k][n] << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<long long> a(n);
    long long mx = 0;
    for (auto& v : a) { cin >> v; mx = max(mx, v); }
    for (long long S = mx;; S++) {            // try every candidate answer in order
        int pieces = 1;
        long long cur = 0;
        for (long long v : a) {
            if (cur + v > S) { pieces++; cur = 0; }
            cur += v;
        }
        if (pieces <= k) {
            cout << S << '\n';
            return 0;
        }
    }
}
""",
    hints=[
        r"""Do not search for the cutting. Ask instead: can the largest piece be at most `S`? For
a fixed `S`, how do you answer that in one pass?""",
        r"""Fill each piece greedily while its sum stays ≤ `S`; `S` works if that uses at most `k`
pieces. Larger `S` only makes it easier: binary search on `S`.""",
        r"""Start at `lo = max(a) − 1` (impossible) and `hi = Σa` (one piece). Otherwise the check
can be asked about an `S` smaller than a single element.""",
    ],
    editorial=r"""
Turn the optimisation into a yes/no question: can every piece have sum at most `S` using at
most `k` pieces? Answer it greedily: extend the current piece while its sum stays ≤ `S`, and
start a new one otherwise. Greedy stays ahead: after `j` pieces it has covered at least as
many elements as the first `j` pieces of any valid cutting, so if any cutting uses at most `k`
pieces, the greedy does too. At most `k` is as good as exactly `k`, because splitting a piece
never increases a sum and `n ≥ k`.

The answer is monotone in `S`, so binary search with `lo = max(a) − 1` (the piece holding
the largest element exceeds it) and `hi = Σa` (one piece holds everything). That choice of
`lo` also means the check is never asked about an `S` below a single element, which a check
without special cases gets wrong (`[1, 10]`, `k = 2`: it would accept `S = 1`). Sums reach
2·10^14: `long long`. O(n log Σa).
""",
)

AGGRESSIVE_COWS = Problem(
    id="aggressive_cows",
    title="Aggressive Cows",
    difficulty="medium",
    source="SPOJ AGGRCOW - Aggressive cows",
    complexity="O(n log n + n log(max x))",
    statement=r"""
A barn has `n` stalls along a straight corridor, at distinct positions `x_1, ..., x_n`. The
farmer has `c` cows, who get aggressive when they stand close to each other. Each cow goes into
a different stall.

Place the cows so that the smallest distance between two of them is as large as possible.
Print that distance.
""",
    input=r"""
The first line has `n` and `c` (2 ≤ c ≤ n ≤ 2·10^5).

The second line has `n` distinct integers x_1, ..., x_n (0 ≤ x_i ≤ 10^9), in no particular
order.
""",
    output=r"""
Print one integer: the largest possible minimum distance between two cows.
""",
    samples=[
        Test("5 3\n1 2 8 4 9\n", "3\n", note="Cows at 1, 4 and 8 (or 9)."),
        Test("2 2\n1000000000 0\n", "1000000000\n"),
    ],
    tests=[
        Test("3 3\n5 1 3\n"),
        Test("4 2\n0 1 2 3\n"),
        Test("5 5\n0 10 11 30 50\n"),
        Test("6 3\n0 1000000000 1 999999999 500000000 500000001\n"),
    ],
    gens=[
        Gen("small random", _stalls_small, 15),
        Gen("medium random", lambda rng: _stalls(rng, 300, rng.randint(2, 300), 10**9), 3),
        Gen("max size, random c", lambda rng: _stalls(rng, 200000, rng.randint(2, 200000), 10**9), 1, large=True),
        Gen("max size, two cows", lambda rng: _stalls(rng, 200000, 2, 10**9), 1, large=True),
        Gen("max size, few cows", lambda rng: _stalls(rng, 200000, 7, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, c;
    cin >> n >> c;
    vector<long long> x(n);
    for (auto& v : x) cin >> v;
    sort(x.begin(), x.end());                 // the input is not sorted

    auto ok = [&](long long D) {              // can every two cows be at least D apart?
        int placed = 1;
        long long last = x[0];                // leftmost stall first: never a mistake
        for (int i = 1; i < n && placed < c; i++)
            if (x[i] - last >= D) {
                placed++;
                last = x[i];
            }
        return placed >= c;
    };

    // invariant: ok(lo) true, ok(hi) false -- the good side is now the low side
    long long lo = 0, hi = x[n - 1] - x[0] + 1;
    while (hi - lo > 1) {
        long long mid = lo + (hi - lo) / 2;
        if (ok(mid)) lo = mid;
        else hi = mid;
    }
    cout << lo << '\n';                       // the last distance that works
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, c;
    cin >> n >> c;
    vector<long long> x(n);
    for (auto& v : x) cin >> v;
    sort(x.begin(), x.end());
    // best[j][i]: largest minimum gap with j cows, the last one in stall i
    const long long INF = LLONG_MAX;
    vector<vector<long long>> best(c + 1, vector<long long>(n, -1));
    for (int i = 0; i < n; i++) best[1][i] = INF;
    for (int j = 2; j <= c; j++)
        for (int i = 0; i < n; i++)
            for (int p = 0; p < i; p++)
                if (best[j - 1][p] >= 0)
                    best[j][i] = max(best[j][i], min(best[j - 1][p], x[i] - x[p]));
    cout << *max_element(best[c].begin(), best[c].end()) << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, c;
    cin >> n >> c;
    vector<long long> x(n);
    for (auto& v : x) cin >> v;
    sort(x.begin(), x.end());
    long long D = 1;
    while (true) {                            // raise D until it stops working
        int placed = 1;
        long long last = x[0];
        for (int i = 1; i < n; i++)
            if (x[i] - last >= D) { placed++; last = x[i]; }
        if (placed < c) break;
        D++;
    }
    cout << D - 1 << '\n';
}
""",
    hints=[
        r"""Ask a yes/no question: can the cows all be at least `D` apart? If yes for `D`, what
about `D − 1`?""",
        r"""Check a `D` greedily on the sorted stalls: first cow in the leftmost stall, every next
cow in the first stall at least `D` beyond the previous one.""",
        r"""Here small `D` works and large `D` does not: keep `ok(lo)` true and `ok(hi)` false,
and print `lo`.""",
    ],
    editorial=r"""
"Can every two cows be at least `D` apart?" is true for small `D` and false for large `D`, so
the answer is the *last* `D` that works. Binary search with the invariant flipped: `ok(lo)`
true (`lo = 0` always works), `ok(hi)` false (`hi = max − min + 1` is farther than any two
stalls), and print `lo`.

The check is greedy on the sorted stalls: the first cow goes into the leftmost stall and each
next cow into the first stall at least `D` beyond the previous one. That is safe by an
exchange: moving any cow of a valid placement to the earliest allowed stall only widens the
gap in front of it. O(n log n) to sort plus O(n) per check, about 30 checks. Forgetting the
sort gives wrong answers: both samples are unsorted.
""",
)

BEST_AVERAGE = Problem(
    id="best_average",
    title="Best Average",
    difficulty="hard",
    complexity="O(n · iterations)",
    statement=r"""
A weather station has `n` daily temperature anomalies `a_1, ..., a_n` (integers, possibly
negative). A *heat wave* is any stretch of at least `L` consecutive days.

Find the largest possible average anomaly of a heat wave.
""",
    input=r"""
The first line has `n` and `L` (1 ≤ L ≤ n ≤ 2·10^5).

The second line has `n` integers a_1, ..., a_n (−10^4 ≤ a_i ≤ 10^4).
""",
    output=r"""
Print the largest average of a contiguous subarray with at least `L` elements. Answers within
an absolute or relative error of 10^-6 are accepted.
""",
    samples=[
        Test("6 4\n1 12 -5 -6 50 3\n", "12.750000000\n", note="`12 −5 −6 50` averages 51/4."),
        Test("3 2\n4 -1 5\n", "2.666666667\n",
             note="All three days average 8/3. Printed with default precision this is `2.66667`, "
                  "which is not within 10^-6."),
        Test("3 1\n-3 -1 -2\n", "-1.000000000\n"),
    ],
    tests=[
        Test("1 1\n-10000\n"),
        Test("4 2\n7 7 7 7\n"),
        Test("2 2\n10000 -10000\n"),
        Test("3 3\n12 12 13\n"),
        Test("5 1\n-10000 -10000 10000 -10000 -10000\n"),
    ],
    gens=[
        Gen("small random", _avg_small, 15),
        Gen("medium random", lambda rng: _avg(rng, 2000, rng.randint(1, 2000), -10**4, 10**4), 2),
        Gen("medium, answer near zero", lambda rng: _avg_needle(rng, 3000, rng.randint(1, 30)), 3),
        Gen("max size, random L", lambda rng: _avg(rng, 200000, rng.randint(1, 1000), -10**4, 10**4), 1, large=True),
        Gen("max size, L = 1", lambda rng: _avg(rng, 200000, 1, -10**4, 10**4), 1, large=True),
        Gen("max size, answer near zero", lambda rng: _avg_needle(rng, 200000, rng.randint(1, 30)), 1, large=True),
    ],
    checker="float:1e-6",
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, L;
    cin >> n >> L;
    vector<long long> pre(n + 1, 0);          // exact integer prefix sums
    for (int i = 1; i <= n; i++) {
        long long v;
        cin >> v;
        pre[i] = pre[i - 1] + v;
    }

    // ok(m): does some subarray of length >= L have average >= m?
    //   average of a[l+1..r] >= m  <=>  (pre[r] - m*r) - (pre[l] - m*l) >= 0
    auto ok = [&](double m) {
        double lowest = 1e300;                // min of pre[l] - m*l over l <= r - L
        for (int r = L; r <= n; r++) {
            lowest = min(lowest, pre[r - L] - m * (r - L));
            if (pre[r] - m * r - lowest >= 0) return true;
        }
        return false;
    };

    double lo = -1e4, hi = 1e4 + 1;           // ok(lo) true, ok(hi) false
    for (int it = 0; it < 100; it++) {        // a fixed count: always terminates
        double mid = (lo + hi) / 2;
        if (ok(mid)) lo = mid;
        else hi = mid;
    }
    cout << fixed << setprecision(9) << lo << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, L;
    cin >> n >> L;
    vector<long long> pre(n + 1, 0);
    for (int i = 1; i <= n; i++) {
        long long v;
        cin >> v;
        pre[i] = pre[i - 1] + v;
    }
    long long bs = 0, bl = 0;                 // best sum / best length, compared exactly
    bool have = false;
    for (int l = 0; l < n; l++)
        for (int r = l + L; r <= n; r++) {
            long long s = pre[r] - pre[l], len = r - l;
            if (!have || (__int128)s * bl > (__int128)bs * len) { bs = s; bl = len; have = true; }
        }
    cout << fixed << setprecision(9) << (long double)bs / bl << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, L;
    cin >> n >> L;
    vector<long long> pre(n + 1, 0);
    for (int i = 1; i <= n; i++) {
        long long v;
        cin >> v;
        pre[i] = pre[i - 1] + v;
    }
    double best = -1e18;
    for (int l = 0; l < n; l++)               // every subarray, O(1) each with prefix sums
        for (int r = l + L; r <= n; r++)
            best = max(best, (double)(pre[r] - pre[l]) / (r - l));
    cout << fixed << setprecision(9) << best << '\n';
}
""",
    hints=[
        r"""Fix a candidate average `m`. "Some subarray has average ≥ m" is the same as "some
subarray of `a_i − m` has sum ≥ 0". Is that monotone in `m`?""",
        r"""For the check: prefix sums `P` of `a_i − m`; the best subarray ending at `r` subtracts
the smallest `P[l]` with `l ≤ r − L`. Keep that minimum as you go.""",
        r"""Run a fixed number of iterations (100) instead of `while (hi − lo > eps)`, and print with
`fixed << setprecision(9)`.""",
    ],
    editorial=r"""
Binary search on the answer `m`. The average of a subarray is at least `m` exactly when the
sum of `a_i − m` over it is at least 0, so `ok(m)` asks whether some subarray of length at
least `L` has a non-negative sum after subtracting `m` from everything. With prefix sums `P`
of the shifted values, the best subarray ending at `r` is `P[r] − min(P[0..r−L])`, and that
minimum is a running one: O(n) per check. `ok` is monotone (true for small `m`, false for
large), so keep `ok(lo)` true, `ok(hi)` false.

For real numbers, iterate a fixed number of times: 100 halvings exhaust a `double` from any
starting range, while `while (hi − lo > 1e-9)` can loop forever when neighbouring doubles
near the answer are further apart than `1e-9`. Computing `P` from exact integer prefix sums
(`pre[r] − m·r`) keeps rounding errors small. Print with `fixed << setprecision(9)`: the
default 6 significant digits are not within 10^-6 of `8/3`. O(100 · n) against the O(n^2)
of trying every subarray.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo03",
    title="binary search",
    track="algo",
    order=3,
    summary="Search the answer, not the input: monotone predicates, the lo-bad / hi-good "
            "invariant that makes off-by-ones impossible, minimise-the-maximum and "
            "maximise-the-minimum, and real-valued searches that always terminate.",
    prereqs=["cpp06", "cpp08"],
    tags=["binary search", "binary search on the answer", "invariant", "monotone predicate",
          "real-valued binary search", "greedy check"],
    parts=[
        Part("Guessing the time", [
            Say(r"""
A factory has `n` machines working in parallel. Machine `i` needs `k_i` seconds per product,
so it finishes products at times `k_i, 2k_i, 3k_i, ...`. What is the shortest time in which
the machines make `t` products together? The limits: `n ≤ 2·10^5`, `k_i, t ≤ 10^9`, one
second.

Start with the easier question: *given* a time `T`, how many products are done by then?
"""),
            Short(r"""
Three machines with `k = 3, 2, 5`. How many products are finished by time `T = 7`?
""", accept=["6", "six"], placeholder="a number",
                explain=r"""
`⌊7/3⌋ + ⌊7/2⌋ + ⌊7/5⌋ = 2 + 3 + 1 = 6`. In general `count(T) = Σ ⌊T / k_i⌋`: O(n) for one
`T`.
"""),
            Say(r"""
So one obviously correct program tries `T = 1, 2, 3, ...` and stops at the first `T` with
`count(T) ≥ t`.
"""),
            Numeric(r"""
How large can the answer itself be, at these limits?
""", answer=1e18, rel=0.5, unit="seconds",
                hint="Make the factory as slow as the limits allow.",
                explain=r"""
One machine with `k = 10^9` and `t = 10^9`: 10^18 seconds. The scan would need 10^18 steps of
O(n) each; at one step per nanosecond that is 30 years.
"""),
            MCQ(r"""
The scan checks every `T` in order. What does it ignore about `count(T)`?
""", [
                Opt("`count(T)` grows linearly, so the answer is one division away.",
                    why="It grows roughly like `T · Σ 1/k_i`, but the floors make it a staircase: "
                        "with `k = 3, 2, 5` and `t = 7`, `7 / (1/3 + 1/2 + 1/5) ≈ 6.8`, while the "
                        "answer is 8."),
                Opt("Nothing: the answer could be any `T`, so every `T` must be checked.",
                    why="It could be any `T`, but one check tells you about more than one `T`. If "
                        "`T = 500` is not enough, is `T = 300`?"),
                Opt("`count(T)` never decreases as `T` grows: once a time is enough, every later "
                    "time is enough.", correct=True,
                    why="Yes. The answers to 'is `T` enough?' read no, no, ..., no, yes, yes, ...: "
                        "a sorted array of booleans, and you want the first yes."),
                Opt("`count(T)` is expensive, so the scan should cache it.",
                    why="Each `T` is asked once, so there is nothing to cache. The problem is the "
                        "number of `T`s, not the cost of each."),
            ]),
            Reflect(r"""
You check `T = 500` and it is enough. What have you learnt about all the other times? What if
it is not enough? How many checks does that suggest for a range of 10^18?
""", answer=r"""
If 500 is enough, so is every `T > 500`: the answer is at most 500. If not, no `T < 500` is
enough either: the answer is above 500. Either way one check discards everything on one side,
so checking the middle of the remaining range halves it every time: about 60 checks for
10^18. That is **binary search on the answer**. What makes it possible is not a sorted array
but a **monotone predicate**, `ok(T) = count(T) ≥ t`.
"""),
        ]),
        Part("An invariant, not a guess", [
            Say(r"""
Binary search has a reputation for off-by-one bugs, and nearly all of them come from never
saying what the two ends *mean*. So say it, as an **invariant**: something true before the
loop starts and after every iteration.

- `lo` is a time known to be **not enough**: `ok(lo)` is false.
- `hi` is a time known to be **enough**: `ok(hi)` is true.

The answer, the first time that is enough, then always lies in `(lo, hi]`.
"""),
            MCQ(r"""
Which starting values make the invariant true before the first iteration?
""", [
                Opt("`lo = 1`, `hi = 10^18`",
                    why="`lo = 1` may already be enough (one machine with `k = 1`, `t = 1`). Then "
                        "the invariant is false from the start, and the loop can only return "
                        "values above `lo`: it prints 2 instead of 1."),
                Opt("`lo = 0`, `hi = t`",
                    why="`t` seconds are enough only if some machine has `k = 1`. With "
                        "`k = 3, 2, 5` and `t = 7`, time 7 makes only 6 products."),
                Opt("`lo = min(k)`, `hi = max(k) · t`",
                    why="`hi` satisfies the invariant (a large generic `hi` has a problem of its "
                        "own, coming up), but `lo = min(k)` is already enough when `t = 1`: the "
                        "first product appears exactly then."),
                Opt("`lo = 0`, `hi = min(k) · t`", correct=True,
                    why="Yes. At time 0 nothing is made and `t ≥ 1`; the fastest machine alone "
                        "makes `t` products by `min(k) · t`. Both facts are proved, not hoped."),
            ]),
            Say(r"""
The loop moves an end only to a point it has just checked, so the invariant survives every
iteration:

```cpp
long long lo = 0, hi = min_k * t;         // ok(lo) false, ok(hi) true
while (hi - lo > 1) {
    long long mid = lo + (hi - lo) / 2;
    if (ok(mid)) hi = mid;                // mid is enough: the new hi
    else lo = mid;                        // mid is not: the new lo
}
cout << hi << '\n';
```
"""),
            MCQ(r"""
Why does this loop always terminate?
""", [
                Opt("Because `mid` is rounded down.",
                    why="Rounding only decides *which* point is checked. Termination needs every "
                        "iteration to shrink the gap."),
                Opt("Because `ok` has to return true eventually.",
                    why="If every `mid` were false, `lo` would still climb toward `hi`. Termination "
                        "has nothing to do with the answers."),
                Opt("It does not always: it loops forever when `hi = lo + 1`.",
                    why="When `hi = lo + 1`, the condition `hi − lo > 1` is false and the loop does "
                        "not run at all."),
                Opt("Inside the loop `hi − lo ≥ 2`, so `lo < mid < hi`: whichever end moves, the "
                    "gap shrinks.", correct=True,
                    why="Yes. And it roughly halves, so there are about `log2(hi − lo)` "
                        "iterations."),
            ]),
            Short(r"""
When the loop stops, which variable holds the answer?
""", accept=["hi"], placeholder="a variable name",
                explain=r"""
`hi`. The loop stops at `hi = lo + 1` with `ok(lo)` false and `ok(hi)` true: `hi` is enough and
the time just before it is not, so `hi` is the *first* time that is enough. No `+1` or `−1`
anywhere; the invariant says which end to print.
"""),
            Numeric(r"""
Run it by hand on `k = 3, 2, 5`, `t = 7`, from `lo = 0`, `hi = 14`. What does it print?
""", answer=8,
                hint="Three calls to `ok`. The first `mid` is 7.",
                explain=r"""
`mid = 7`: 6 products, not enough, `lo = 7`. `mid = 10`: 10 products, `hi = 10`. `mid = 8`:
`2 + 4 + 1 = 7`, enough, `hi = 8`. Now `hi − lo = 1`: print 8.
"""),
            MCQ(r"""
A variant you will see in other people's code:

```cpp
while (lo < hi) {
    long long mid = (lo + hi) / 2;
    if (ok(mid)) hi = mid;
    else lo = mid;
}
```

What does it do?
""", [
                Opt("The same as the loop above.",
                    why="The condition is different: this loop runs even when `hi = lo + 1`."),
                Opt("It can loop forever: once `hi = lo + 1` and `ok(lo)` is false, `mid = lo`, and "
                    "`lo = mid` changes nothing.", correct=True,
                    why="Yes. It hangs on the last step, which is exactly where testing by hand "
                        "rarely looks."),
                Opt("It returns one less than the answer.",
                    why="It never returns in the bad case: `mid = lo` again and again."),
                Opt("It is correct but slower.",
                    why="Speed is not the issue; it may never stop."),
            ], explain=r"""
The usual repair is `lo = mid + 1`, which is right under a *different* invariant: `lo` is the
smallest value not yet ruled out, and the answer is in `[lo, hi]`. Both styles work; bugs come
from mixing them. This lesson uses "lo bad, hi good" throughout, because it has a single rule:
move the end that `mid` just proved.
"""),
            Numeric(r"""
With `hi = 10^18`, at most how many iterations does the loop run?
""", answer=60, tol=1,
                explain=r"""
Each iteration halves the gap: `log2(10^18) ≈ 59.8`, so 60 calls to `ok`, each O(n): about
1.2·10^7 operations, against 10^18 for the scan.
"""),
        ]),
        Part("Getting it accepted", [
            Say(r"""
The check itself:

```cpp
auto ok = [&](long long T) {              // are T seconds enough?
    long long made = 0;
    for (long long v : k) made += T / v;
    return made >= t;
};
```

Many people skip computing `min_k * t` and start with `hi = 10^18`, which is also enough (any
machine makes 10^9 products in 10^18 seconds).
"""),
            MCQ(r"""
With `hi = 10^18`, the first `mid` is about `5·10^17`. There are 2·10^5 machines with `k = 1`.
What happens inside `ok`?
""", [
                Opt("Nothing special: `made` is a `long long`.",
                    why="A `long long` stops at about 9.2·10^18. Here `made` heads for "
                        "`2·10^5 · 5·10^17 = 10^23`."),
                Opt("It only overflows if `made` is an `int`.",
                    why="`int` overflows sooner, but 10^23 is beyond any 64-bit type."),
                Opt("`made` overflows and can wrap to a negative number; `ok` then says 'not "
                    "enough' and the search walks off to a wrong answer.", correct=True,
                    why="Yes, and no sample will show it. Return as soon as `made >= t` (which "
                        "also saves time), or use `hi = min(k) · t`, which keeps every `T / k_i` "
                        "below `t`."),
                Opt("The division `T / v` overflows.",
                    why="Division makes numbers smaller. It is the running sum that grows."),
            ]),
            MCQ(r"""
Here `lo` and `hi` stay at most 10^18. Does `mid = (lo + hi) / 2` overflow?
""", [
                Opt("Yes: always write `lo + (hi − lo) / 2`.",
                    why="The habit is good, but check the numbers: `lo + hi ≤ 2·10^18`, well below "
                        "9.2·10^18."),
                Opt("No, because `mid` is declared `long long`.",
                    why="The type of `mid` does not matter: `lo + hi` is computed first, in the "
                        "type of `lo` and `hi`, and only its size decides."),
                Opt("No: the sum is at most 2·10^18, which fits. It would overflow with `int` "
                    "bounds near 2^31, or with `hi` near 9·10^18.", correct=True,
                    why="Right. `lo + (hi − lo) / 2` is safe in every case, so it costs nothing to "
                        "make it the habit."),
            ]),
            Try("factory_machines", note="`lo = 0`, `hi = min(k) · t`, stop summing once the count "
                "reaches `t`, print `hi`. The second sample's answer is 10^18."),
        ]),
        Part("Minimise the largest piece", [
            Say(r"""
The same pattern solves problems that do not look like searches at all. You get `n` positive
integers and must cut the array into `k` contiguous non-empty pieces so that the largest
piece sum is as small as possible. `n ≤ 2·10^5`, `a_i ≤ 10^9`.

Choosing `k − 1` cut positions among `n − 1` is hopeless. Instead, turn the optimisation into
a yes/no question about a candidate answer: *can the largest piece sum be at most `S`?*
"""),
            MCQ(r"""
How do you answer "can every piece have sum ≤ `S`, using at most `k` pieces?" for one `S`?
""", [
                Opt("Cut into `k` pieces of equal length and compare the largest sum with `S`.",
                    why="Equal lengths ignore the values: `9 1 1 1` with `k = 2` cut in the "
                        "middle gives 10, while `[9] [1 1 1]` gives 9."),
                Opt("Sort the array and fill pieces from the largest element down.",
                    why="Pieces must be contiguous, so the order of the array is part of the "
                        "problem. Sorting throws it away."),
                Opt("Walk left to right, adding each element to the current piece while its sum "
                    "stays ≤ `S` and starting a new piece otherwise; yes if that used at most "
                    "`k` pieces.", correct=True,
                    why="Yes, O(n) for one `S`. Larger `S` can only need fewer pieces, so the "
                        "answer is monotone in `S`: binary search."),
                Opt("Try every set of cut positions and check each.",
                    why="Correct, but that is the exponential search we are escaping."),
            ]),
            Reflect(r"""
Why does packing as many elements as possible into each piece never hurt? Compare the greedy's
pieces with those of any other valid cutting.
""", answer=r"""
Greedy stays ahead (algo02). After `j` pieces, the greedy has covered at least as many elements
as the first `j` pieces of any valid cutting. For `j = 1` it is true because the greedy takes
the longest prefix with sum ≤ `S`. If it holds after `j` pieces, the greedy's next piece starts
at or after the start of the other's next piece, and every element up to the end of that piece
fits (a part of a piece with sum ≤ `S` has sum ≤ `S`, since values are positive), so the greedy
reaches at least as far. So if any cutting uses at most `k` pieces, the greedy does too.
"""),
            Numeric(r"""
`a = 5 2 4 7 1 3` and `k = 3`. How many pieces does the greedy use for `S = 10`?
""", answer=4,
                explain=r"""
`[5 2] [4] [7 1] [3]`: 4 pieces, more than 3, so 10 is not enough. For `S = 11` it builds
`[5 2 4] [7 1 3]`: 2 pieces, enough. The answer is 11.
"""),
            MCQ(r"""
The problem demands *exactly* `k` pieces, but the check accepts *at most* `k`. Is that a bug?
""", [
                Opt("Yes: a cutting with fewer pieces is not a valid answer.",
                    why="It is not valid itself, but it can always be turned into one with the same "
                        "largest sum. How?"),
                Opt("No: any cutting with fewer pieces can be split further (any piece with two "
                    "elements or more), and splitting never increases a piece sum. Since "
                    "`n ≥ k`, exactly `k` is always reachable.", correct=True,
                    why="Right. Relaxing 'exactly' to 'at most' is what makes the check monotone "
                        "and greedy-friendly."),
                Opt("Only when the greedy happens to use exactly `k` pieces.",
                    why="The greedy often uses fewer, and the answer is still right, because extra "
                        "cuts are free."),
            ]),
            MCQ(r"""
Someone writes the check without special cases:

```cpp
int pieces = 1; long long cur = 0;
for (long long v : a) {
    if (cur + v > S) { pieces++; cur = 0; }
    cur += v;
}
return pieces <= k;
```

and starts the search at `lo = 0`, `hi = Σa`. On `a = 1 10`, `k = 2`, it prints 1. Why?
""", [
                Opt("`hi = Σa` is too small.",
                    why="`Σa` is always enough: one piece holds everything."),
                Opt("`cur` should be reset to `v`, not to 0.",
                    why="`cur = 0` followed by `cur += v` is the same thing."),
                Opt("`ok(1)` says yes: the code gives 10 its own piece without checking it against "
                    "`S`, so `[1] [10]` passes as two pieces of sum at most 1.", correct=True,
                    why="Yes. Either return false when some `a_i > S`, or start at "
                        "`lo = max(a) − 1`: provably not enough, since the piece holding the "
                        "largest element exceeds it, and every `mid` is then at least `max(a)`."),
                Opt("The loop should be `while (lo < hi)`.",
                    why="The loop is fine; its invariant is broken, because `ok` lies about "
                        "`S = 1`."),
            ], explain=r"""
Choosing `lo` and `hi` is part of the proof. A good `lo` is not just "small": it is a value you
can prove is not enough, and a `lo` like that often protects the check from inputs it was never
designed for.
"""),
            Try("array_division", note="`lo = max(a) − 1`, `hi = Σa`, greedy check. Sums reach "
                "2·10^14."),
        ]),
        Part("Maximise the smallest gap", [
            Say(r"""
Now flip the objective. A barn has `n` stalls at positions `x_i` along a corridor, and `c`
cows who fight when they stand close. Put the cows in distinct stalls so that the smallest
distance between two cows is as large as possible. `n ≤ 2·10^5`, `x_i ≤ 10^9`, `2 ≤ c ≤ n`.

The yes/no question is `ok(D)`: can every two cows be at least `D` apart?
"""),
            MCQ(r"""
How does `ok(D)` behave as `D` grows, and what does that do to the template?
""", [
                Opt("As before: false for small `D`, true for large `D`. Keep `lo` bad and `hi` "
                    "good.",
                    why="Try `D = 0`: always possible. `D = 10^10`: never. It is the other way "
                        "round."),
                Opt("It is not monotone, so binary search does not apply.",
                    why="If the cows can be `D` apart, the same placement has them at least `D − 1` "
                        "apart. That is monotone."),
                Opt("True for small `D`, false for large `D`. Same loop, flipped meanings: `ok(lo)` "
                    "true, `ok(hi)` false, and the answer is `lo`.", correct=True,
                    why="Yes: we want the *last* `D` that works. `lo = 0` surely works, and "
                        "`hi = (max x − min x) + 1` surely does not: no two stalls are that far "
                        "apart."),
                Opt("Binary search over the stall positions instead of over `D`.",
                    why="The answer is a distance, not a position, and usually it is not any "
                        "`x_i`: for stalls `1 2 4 8 9` and 3 cows it is 3."),
            ]),
            Reflect(r"""
How do you compute `ok(D)` in O(n)? Where does the first cow go, and why is that safe?
""", answer=r"""
Sort the stalls. Put the first cow in the leftmost stall, and each next cow in the first stall
at least `D` beyond the previous cow; answer yes if `c` cows fit. Leftmost is safe by an
exchange: in any valid placement, moving the first cow left to the leftmost stall only widens
its gap to the second cow. The same holds for every later cow: placing it as early as allowed
leaves the most room for the rest.
"""),
            Numeric(r"""
Stalls `1 2 8 4 9`, `c = 3`. What is the largest possible minimum distance?
""", answer=3,
                explain=r"""
Sorted: `1 2 4 8 9`. `ok(3)`: cows at 1, 4, 8: yes. `ok(4)`: 1, then the first stall at 5 or
beyond is 8, then nothing at 12 or beyond: only 2 cows, no. The answer is 3.
"""),
            Try("aggressive_cows", note="Sort first (the input is not sorted), keep `ok(lo)` true and "
                "`ok(hi)` false, print `lo`."),
        ]),
        Part("Real numbers", [
            Say(r"""
Sometimes the answer is not an integer. Given `n` integers (some negative) and a length `L`,
find the largest average of a contiguous subarray with at least `L` elements. `n ≤ 2·10^5`,
`|a_i| ≤ 10^4`, answers within 10^-6 accepted.

With prefix sums (algo01) each subarray's average costs O(1), but there are about
n^2/2 = 2·10^10 subarrays. And an average is awkward: averages of pieces do not add up the way sums
do. Binary search on the answer turns it into something that does.
"""),
            Reflect(r"""
Fix a candidate `m`. Rewrite "some subarray of length ≥ `L` has average ≥ `m`" as a statement
about sums, so that checking it needs no division.
""", answer=r"""
The average of `a[l..r]` is at least `m` exactly when `Σ (a_i − m) ≥ 0` over that range
(multiply both sides by the length, which is positive). So subtract `m` from every element and
ask whether some subarray of length at least `L` has a non-negative sum. If yes, the best
average is at least `m`; if not, it is below `m`. That is monotone in `m`, so binary search
applies.
"""),
            Short(r"""
`a = 1 12 −5 −6 50 3`, `L = 4`, candidate `m = 13`. After subtracting 13 the values are
`−12 −1 −18 −19 37 −10`. What is the largest sum of a subarray with at least 4 elements?
""", accept=["-1", "−1"], placeholder="a number",
                explain=r"""
The four values `−1, −18, −19, 37` add up to −1, and every other qualifying subarray is
lower. The best is negative, so no average reaches 13: the answer is below 13. (It is 12.75,
from `12 −5 −6 50`.)
"""),
            MCQ(r"""
How do you check "some subarray with at least `L` elements has sum ≥ 0" in O(n)?
""", [
                Opt("Prefix sums `P` of the shifted values: for each `r ≥ L`, compare `P[r]` with "
                    "the minimum of `P[0..r−L]`, kept as a running minimum.", correct=True,
                    why="Yes. The best subarray ending at `r` subtracts the smallest prefix that "
                        "ends at least `L` positions earlier, and that minimum only gains one "
                        "candidate per step."),
                Opt("A sliding window of exactly `L` elements.",
                    why="Longer subarrays count too: shifted values `3 −4 3` with `L = 2` have no "
                        "good window of length 2 (both sum to −1), but all three sum to 2."),
                Opt("Two pointers: grow the window while its sum is non-negative.",
                    why="Windows behave monotonically only for non-negative values (algo04); the "
                        "shifted values have both signs."),
                Opt("Kadane's maximum subarray sum.",
                    why="Kadane ignores the minimum length: with `L = 4` it happily reports one "
                        "large element on its own."),
            ]),
            Say(r"""
A real-valued search has no `hi − lo = 1` to stop at. Run a fixed number of iterations:

```cpp
double lo = -1e4, hi = 1e4 + 1;           // ok(lo) true, ok(hi) false
for (int it = 0; it < 100; it++) {
    double mid = (lo + hi) / 2;
    if (ok(mid)) lo = mid; else hi = mid;
}
cout << fixed << setprecision(9) << lo << '\n';
```
"""),
            Numeric(r"""
The range starts about 2·10^4 wide. How many halvings until it is narrower than 10^-6?
""", answer=35, tol=1,
                explain=r"""
`log2(2·10^4 / 10^-6) = log2(2·10^10) ≈ 34.2`, so 35. 100 iterations is far more than enough
and costs `100 · n = 2·10^7` operations; the extra ones just sit at the limit of `double`
precision.
"""),
            MCQ(r"""
Why not simply loop `while (hi − lo > 1e-9)`?
""", [
                Opt("It is slower.",
                    why="Here it would stop after about 45 iterations, fewer than 100."),
                Opt("Comparing doubles with `>` is undefined behaviour.",
                    why="The comparison is well defined. It is the *gap* that has a floor."),
                Opt("It can loop forever when the answer is large: near 10^9, neighbouring doubles "
                    "are about 1.2·10^-7 apart, so `hi − lo` never drops below 1e-9.",
                    correct=True,
                    why="Yes: `mid` rounds to `lo` or `hi`, nothing changes, and the loop spins "
                        "until the time limit. A fixed iteration count always ends."),
            ]),
            MCQ(r"""
The best average in the second sample is `8/3 = 2.6666...`. What does a plain `cout << lo`
print, and is it accepted within 10^-6?
""", [
                Opt("`2.666666667`: accepted.",
                    why="`cout` prints 6 significant digits unless told otherwise."),
                Opt("`2.66667`: accepted, since the checker is lenient.",
                    why="Lenient to 10^-6 relative to the answer: 2.7·10^-6 here. `2.66667` is "
                        "3.3·10^-6 away."),
                Opt("`2.66667`: rejected, because it is 3.3·10^-6 away and only 2.7·10^-6 is "
                    "allowed.", correct=True,
                    why="Yes. `fixed << setprecision(9)` prints `2.666666667`. Set it once, before "
                        "the first real number you print."),
            ]),
            Try("best_average", note="Shift by `m`, check with prefix sums and a running minimum, "
                "100 iterations, print 9 decimals."),
            MCQ(r"""
Binary search on the answer needs a monotone `ok`. Which of these does *not* fit the pattern
directly?
""", [
                Opt("The smallest integer `x ≥ 0` with `x^2 ≥ N`.",
                    why="`x^2` only grows for `x ≥ 0`: monotone. It is the exact way to compute an "
                        "integer square root of a 10^18-sized number (cpp02)."),
                Opt("The time at which a thrown ball is highest.", correct=True,
                    why="Right: the height rises and then falls, so 'is the height at least `h` at "
                        "time `T`' is not monotone in `T`. 'Is the ball still rising at `T`' is, "
                        "so you can binary search on that instead (or use ternary search)."),
                Opt("The most books you can buy, taking them in shelf order, with budget `B`.",
                    why="Buying the first `j` books costs more as `j` grows: monotone. (Prefix sums "
                        "plus `upper_bound`, in fact.)"),
                Opt("The minimum time for `t` products.",
                    why="The lesson's first example: more time never makes fewer products."),
            ], explain=r"""
Look for the monotone predicate first. Once you have it, the template never changes: a `lo`
proved on one side, a `hi` proved on the other, and move the end that `mid` just proved.
`lower_bound` (cpp06) is the same loop with `ok(i) = a[i] ≥ x` on a sorted array.
"""),
        ]),
    ],
    problems=[FACTORY, ARRAY_DIVISION, AGGRESSIVE_COWS, BEST_AVERAGE],
    cards=[
        Card(r"""The binary-search invariant used in this track?""",
             r"""`ok(lo)` is false, `ok(hi)` is true. Loop `while (hi - lo > 1)`, set whichever end `mid` proved, and at the end `hi` is the first value that works."""),
        Card(r"""Why does `while (hi - lo > 1) { mid = lo + (hi - lo) / 2; ... }` always terminate?""",
             r"""Inside the loop `hi − lo ≥ 2`, so `lo < mid < hi`, and either end moving shrinks the gap (roughly by half)."""),
        Card(r"""What goes wrong with `while (lo < hi) { mid = (lo + hi) / 2; if (ok(mid)) hi = mid; else lo = mid; }`?""",
             r"""When `hi = lo + 1` and `ok(lo)` is false, `mid = lo` and nothing changes: an infinite loop. That style needs `lo = mid + 1`."""),
        Card(r"""What must be true of the starting `lo` and `hi`?""",
             r"""They must satisfy the invariant: `lo` provably fails and `hi` provably works (Factory Machines: `lo = 0`, `hi = min(k) · t`)."""),
        Card(r"""Factory Machines: why can `Σ T / k_i` overflow, and the fix?""",
             r"""With a generic `hi` like 10^18 and many `k_i = 1`, the sum reaches about 10^23. Return as soon as it reaches `t`."""),
        Card(r"""Minimise the maximum (Array Division): what do you binary search, and how is it checked?""",
             r"""The answer `S`. Check greedily: fill each piece while its sum stays ≤ `S`, count pieces, compare with `k`. Start at `lo = max(a) − 1`, `hi = Σa`."""),
        Card(r"""Maximise the minimum (Aggressive Cows): how does the template change?""",
             r"""`ok(D)` is true for small `D`: keep `ok(lo)` true, `ok(hi)` false, and print `lo`. The check places cows greedily from the left on sorted positions."""),
        Card(r"""Real-valued binary search: how do you stop?""",
             r"""A fixed number of iterations (e.g. 100), not `while (hi - lo > eps)`, which can loop forever when doubles near the answer are further apart than `eps`."""),
        Card(r"""How do you binary search a maximum *average*?""",
             r"""Average ≥ m ⟺ `Σ (a_i − m) ≥ 0`. Subtract `m` from everything and check for a subarray with non-negative sum (prefix sums + running minimum for a minimum length)."""),
        Card(r"""How many iterations does a binary search over a range of 10^18 take?""",
             r"""About 60 (`log2(10^18) ≈ 59.8`)."""),
        Card(r"""How do you print a double so that a 10^-6 checker accepts it?""",
             r"""`cout << fixed << setprecision(9) << x;` The default prints only 6 significant digits."""),
        Card(r"""When does binary search on the answer apply?""",
             r"""When "is `x` good enough?" is monotone: all no, then all yes (or the reverse). A rise-then-fall function needs a different predicate, such as "still rising?", or ternary search."""),
    ],
)
