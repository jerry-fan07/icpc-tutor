from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _flights_random(rng, n, m):
    out = [f"{n} {m}"]
    for _ in range(m):
        a = rng.randint(1, n)
        b = rng.randint(1, n - 1)
        if b >= a:
            b += 1                                 # a != b
        out.append(f"{a} {b}")
    return "\n".join(out) + "\n"


def _flights_complete(rng, n, extra):
    edges = [(a, b) for a in range(1, n + 1) for b in range(1, n + 1) if a != b]
    edges += [rng.choice(edges) for _ in range(extra)]
    rng.shuffle(edges)
    return f"{n} {len(edges)}\n" + "\n".join(f"{a} {b}" for a, b in edges) + "\n"


def _flights_dense(rng, n, p):
    edges = [(a, b) for a in range(1, n + 1) for b in range(1, n + 1) if a != b and rng.random() < p]
    if not edges:
        edges = [(1, n)]
    return f"{n} {len(edges)}\n" + "\n".join(f"{a} {b}" for a, b in edges) + "\n"


def _people(rng, n, x, lo, hi):
    w = [rng.randint(lo, hi) for _ in range(n)]
    return f"{n} {x}\n" + " ".join(map(str, w)) + "\n"


def _row(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _range_small(rng):
    a = rng.randint(0, 10000)
    return f"{a} {rng.randint(a, min(10000, a + rng.randint(0, 3000)))}\n"


def _range_narrow_high(rng):
    # an 18-digit number with no equal neighbours, so the range is not trivially empty
    d = [rng.randint(1, 9)]
    while len(d) < 18:
        d.append(rng.choice([x for x in range(10) if x != d[-1]]))
    a = int("".join(map(str, d))) - rng.randint(0, 50000)
    return f"{a} {a + rng.randint(0, 10**5)}\n"


def _range_wide(rng):
    a, b = sorted((rng.randint(0, 10**18), rng.randint(0, 10**18)))
    return f"{a} {b}\n"


# --------------------------------------------------------------------- problems
HAMILTON = Problem(
    id="hamiltonian_flights",
    title="Hamiltonian Flights",
    difficulty="medium",
    source="CSES 1690 - Hamiltonian Flights",
    complexity="O(2^n · n^2)",
    statement=r"""
There are `n` cities and `m` one-way flights. You want to travel from city 1 to city `n`,
visiting every city exactly once. How many routes are there?

Two routes are different if they use a different sequence of flights. There can be several
flights from one city to another, and each of them is a different flight.
""",
    input=r"""
The first line has `n` and `m` (2 ≤ n ≤ 20, 1 ≤ m ≤ n^2).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): a flight
from city `a` to city `b`.
""",
    output=r"""
The number of routes, modulo 10^9 + 7.
""",
    samples=[
        Test("4 6\n1 2\n1 3\n2 3\n3 2\n2 4\n3 4\n", "2\n"),
        Test("3 3\n1 2\n1 2\n2 3\n", "2\n", note="Two different flights from 1 to 2: two routes."),
    ],
    tests=[
        Test("2 1\n1 2\n"),
        Test("2 1\n2 1\n"),
        Test("3 2\n1 3\n3 2\n"),
        Test("3 3\n1 3\n1 2\n2 3\n"),
        Test("4 4\n1 2\n2 3\n3 4\n4 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _flights_random(rng, (k := rng.randint(2, 8)), rng.randint(k, k * k)), 15),
        Gen("small dense", lambda rng: _flights_dense(rng, rng.randint(3, 8), 0.8), 8),
        Gen("small complete, repeated flights", lambda rng: _flights_complete(rng, rng.randint(3, 7), rng.randint(0, 6)), 4),
        Gen("n = 20, every flight", lambda rng: _flights_complete(rng, 20, 20), 1, large=True),
        Gen("n = 20, random flights", lambda rng: _flights_random(rng, 20, 400), 1, large=True),
        Gen("n = 20, dense", lambda rng: _flights_dense(rng, 20, 0.7), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int MOD = 1'000'000'007;
// dp[mask][v] = routes that start at city 0, visit exactly the cities in mask, end at v
static int dp[1 << 20][20];                  // 80 MB as int; global, not on the stack

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<int>> cnt(n, vector<int>(n, 0));   // cnt[u][v] = flights u -> v
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        cnt[a - 1][b - 1]++;
    }
    int full = (1 << n) - 1, last = n - 1;
    dp[1][0] = 1;                            // at city 0, having visited only city 0
    for (int mask = 3; mask <= full; mask += 2) {    // odd masks: every route contains city 0
        if ((mask >> last & 1) && mask != full) continue;   // reached city n too early
        for (int v = 1; v < n; v++) {
            if (!(mask >> v & 1)) continue;
            if (mask == full && v != last) continue;
            int prev = mask ^ (1 << v);      // the cities visited before arriving at v
            unsigned long long acc = 0;      // < 20 terms of < 1e9 * 400: fits
            for (int u = 0; u < n; u++)
                if ((prev >> u & 1) && cnt[u][v])
                    acc += (unsigned long long)dp[prev][u] * cnt[u][v];
            dp[mask][v] = acc % MOD;
        }
    }
    cout << dp[full][last] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n, m;
vector<vector<int>> adj;                     // one entry per flight, repeats included
long long dfs(int v, int mask) {
    if (mask == (1 << n) - 1) return v == n - 1;
    long long t = 0;
    for (int w : adj[v])
        if (!(mask >> w & 1)) t += dfs(w, mask | 1 << w);
    return t;
}
int main() {
    cin >> n >> m;
    adj.resize(n);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a - 1].push_back(b - 1);
    }
    cout << dfs(0, 1) % 1000000007 << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
int n, m;
vector<vector<int>> adj;
long long dfs(int v, int mask) {             // backtracking over every route
    if (mask == (1 << n) - 1) return v == n - 1;
    long long t = 0;
    for (int w : adj[v])
        if (!(mask >> w & 1)) t = (t + dfs(w, mask | 1 << w)) % MOD;
    return t;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> m;
    adj.resize(n);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a - 1].push_back(b - 1);
    }
    cout << dfs(0, 1) << '\n';
}
""",
    hints=[
        r"""Two partial routes that have visited the same set of cities and stand in the same city
have exactly the same completions. So the state is (set of visited cities, current city).""",
        r"""`dp[mask][v] = Σ over u in mask, u ≠ v, of dp[mask without v][u] · (flights u → v)`.
Process masks in increasing numeric order; only odd masks (containing city 1) matter.""",
        r"""For speed: skip masks that contain city `n` unless they are complete (the route must end
there), and multiply in `long long` before reducing.""",
    ],
    editorial=r"""
A partial route's future depends only on the set of cities it has visited and the city it
is in, not on the order. So let `dp[mask][v]` be the number of routes from city 1 that visit
exactly the cities of `mask` and end at `v`. The flight into `v` came from some `u` in
`mask`, after a route over `mask` minus `v`:

```
dp[mask][v] = sum over u of dp[mask ^ (1 << v)][u] * cnt[u][v]
```

with `dp[{1}][1] = 1`, and the answer `dp[all][n]`. Removing a bit makes the number smaller,
so increasing numeric order computes every mask after the ones it reads.

That is 2^20 · 20 · 20 ≈ 4·10^8 steps in the worst case. Two cuts make it comfortable: every
useful mask contains city 1 (odd masks only, half of them), and a mask containing city `n`
is useful only when it is complete (half again). The table is 2^20 · 20 `int`s = 80 MB,
global. Repeated flights are a count, not a flag, and `dp · cnt` needs 64 bits before the
reduction. Backtracking, by comparison, walks up to 18! ≈ 6.4·10^15 routes.
""",
)

ELEVATOR = Problem(
    id="elevator_rides",
    title="Elevator Rides",
    difficulty="hard",
    source="CSES 1653 - Elevator Rides",
    complexity="O(2^n · n)",
    statement=r"""
`n` people want to reach the top floor of a building that has one elevator. The elevator
carries any group of people whose total weight is at most `x`. What is the minimum number
of rides?
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 20, 1 ≤ x ≤ 10^9).

The second line has the weights w_1, ..., w_n (1 ≤ w_i ≤ x).
""",
    output=r"""
The minimum number of rides.
""",
    samples=[
        Test("4 10\n4 8 6 1\n", "2\n"),
        Test("6 10\n6 5 3 2 2 2\n", "2\n",
             note="Heaviest first, each into the first ride with room, needs 3 rides."),
    ],
    tests=[
        Test("1 5\n5\n"),
        Test("3 1000000000\n1000000000 1000000000 1000000000\n"),
        Test("3 1000000000\n600000000 700000000 400000000\n"),
        Test("5 10\n1 1 1 1 1\n"),
        Test("4 10\n6 6 6 6\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _people(rng, rng.randint(1, 9), (x := rng.randint(5, 30)), 1, x), 15),
        Gen("small, around a third of x", lambda rng: _people(rng, rng.randint(4, 10), 30, 6, 14), 6),
        Gen("small, huge weights", lambda rng: _people(rng, rng.randint(2, 9), 10**9, 2 * 10**8, 10**9), 4),
        Gen("n = 20, random", lambda rng: _people(rng, 20, 10**9, 1, 10**9), 1, large=True),
        Gen("n = 20, around a third of x", lambda rng: _people(rng, 20, 10**9, 2 * 10**8, 4 * 10**8), 1, large=True),
        Gen("n = 20, small people", lambda rng: _people(rng, 20, 1000, 1, 300), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> w(n);
    for (auto& v : w) cin >> v;
    // best[mask] = (rides, load of the last ride), lexicographically smallest, over all
    // orders in which the people of mask can board; the last ride is still open
    vector<pair<int, long long>> best(1 << n, {INT_MAX, 0});
    best[0] = {1, 0};                        // one empty ride, open
    for (int mask = 0; mask < (1 << n); mask++) {
        auto [rides, load] = best[mask];
        for (int i = 0; i < n; i++) {
            if (mask >> i & 1) continue;
            pair<int, long long> cand = load + w[i] <= x
                ? make_pair(rides, load + w[i])          // i fits in the open ride
                : make_pair(rides + 1, w[i]);            // i starts a new ride
            best[mask | 1 << i] = min(best[mask | 1 << i], cand);
        }
    }
    cout << best[(1 << n) - 1].first << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
long long x;
vector<long long> w, load;
int best;
void rec(int i) {                            // put person i into an existing ride or a new one
    if ((int)load.size() >= best) return;
    if (i == n) { best = load.size(); return; }
    for (size_t j = 0; j < load.size(); j++)   // by index: rec() may reallocate load
        if (load[j] + w[i] <= x) { load[j] += w[i]; rec(i + 1); load[j] -= w[i]; }
    load.push_back(w[i]);
    rec(i + 1);
    load.pop_back();
}
int main() {
    cin >> n >> x;
    w.resize(n);
    for (auto& v : w) cin >> v;
    best = n + 1;
    rec(0);
    cout << best << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> w(n);
    for (auto& v : w) cin >> v;
    sort(w.begin(), w.end());
    int best = n;
    do {                                     // every boarding order, packed in that order
        int rides = 1;
        long long load = 0;
        for (long long v : w) {
            if (load + v <= x) load += v;
            else { rides++; load = v; }
        }
        best = min(best, rides);
    } while (next_permutation(w.begin(), w.end()));
    cout << best << '\n';
}
""",
    hints=[
        r"""Let the people board one at a time. For a set of people who have boarded, what do you
need to know to continue? Not just the number of rides.""",
        r"""For each subset keep the pair (rides used, weight in the current ride), and keep the
lexicographically smallest pair. Adding person `i` either fits in the current ride or
opens a new one.""",
        r"""Start from `(1, 0)`: one open, empty ride, and compare pairs with `min`. `load + w` can
reach 2·10^9, just under the `int` limit of about 2.147·10^9; `long long` removes the doubt.""",
    ],
    editorial=r"""
Think of the people boarding in some order, each joining the current ride if it has room
and otherwise opening a new one. Every partition into rides arises this way (list each
ride's people consecutively), so it is enough to find the best order.

For a set `S` of people who have already boarded, all that matters for the rest is the
number of rides used and the load of the open ride. Keep, for each `S`, the
lexicographically smallest pair `(rides, load)`. That is safe: fewer rides always wins,
because a state with `r` rides can open a fresh ride and become `(r + 1, 0)`, which is at
least as good as any `(r + 1, load)`; with equal rides, a lighter open ride is at least as
good. Transition: adding person `i` gives `(rides, load + w_i)` if it fits, else
`(rides + 1, w_i)`. 2^n · n = 2·10^7 steps.

The DP over rides as subsets (`dp[S] = 1 + min over rides R ⊆ S`) is also correct but
visits every (set, subset) pair: 3^20 ≈ 3.5·10^9. The sum `load + w_i` reaches 2·10^9
before it is compared with `x`: that still fits in an `int`, by 7%. With a limit of
2·10^9 it would not, which is why the reference uses `long long` anyway.
""",
)

REMOVAL = Problem(
    id="removal_game",
    title="Removal Game",
    difficulty="medium",
    source="CSES 1097 - Removal Game",
    complexity="O(n^2)",
    statement=r"""
There are `n` numbers in a row. Two players take turns; on each turn a player removes
either the first or the last number of the row and adds it to their score. The game ends
when the row is empty.

Both players play optimally, each maximising their own score. What is the first player's
score?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 5000).

The second line has `n` integers x_1, ..., x_n (−10^9 ≤ x_i ≤ 10^9).
""",
    output=r"""
The first player's final score.
""",
    samples=[
        Test("4\n4 5 1 3\n", "8\n", note="Always taking the larger end gives the first player 7."),
    ],
    tests=[
        Test("1\n-5\n"),
        Test("2\n-1 -2\n"),
        Test("3\n1000000000 1000000000 1000000000\n"),
        Test("4\n2 1 100 3\n"),
        Test("5\n-1000000000 -1000000000 -1000000000 -1000000000 -1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _row(rng, rng.randint(1, 16), -20, 20), 15),
        Gen("small, huge values", lambda rng: _row(rng, rng.randint(1, 14), -10**9, 10**9), 5),
        Gen("n = 5000, random", lambda rng: _row(rng, 5000, -10**9, 10**9), 1, large=True),
        Gen("n = 5000, positive", lambda rng: _row(rng, 5000, 1, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> a(n);
    long long total = 0;
    for (auto& v : a) { cin >> v; total += v; }
    // d[l][r] = (mover's score) - (other's score) on a[l..r] under optimal play.
    // One array: while l is fixed, d[r] holds d[l+1][r] until it is overwritten with d[l][r].
    vector<long long> d(n);
    for (int l = n - 1; l >= 0; l--) {
        d[l] = a[l];
        for (int r = l + 1; r < n; r++)
            d[r] = max(a[l] - d[r],          // take a[l]; opponent then leads by d[l+1][r]
                       a[r] - d[r - 1]);     // take a[r]; d[r-1] is already d[l][r-1]
    }
    cout << (total + d[n - 1]) / 2 << '\n';  // first + second = total, first - second = d
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
vector<long long> a;
long long diff(int l, int r) {               // no memo: 2^n
    if (l > r) return 0;
    return max(a[l] - diff(l + 1, r), a[r] - diff(l, r - 1));
}
int main() {
    int n;
    cin >> n;
    a.resize(n);
    long long total = 0;
    for (auto& v : a) { cin >> v; total += v; }
    cout << (total + diff(0, n - 1)) / 2 << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
vector<long long> a;
long long diff(int l, int r) {
    if (l > r) return 0;
    return max(a[l] - diff(l + 1, r), a[r] - diff(l, r - 1));
}
int main() {
    int n;
    cin >> n;
    a.resize(n);
    long long total = 0;
    for (auto& v : a) { cin >> v; total += v; }
    cout << (total + diff(0, n - 1)) / 2 << '\n';
}
""",
    hints=[
        r"""Whatever happens, the numbers left form a contiguous block `x[l..r]`. That block is the
state.""",
        r"""Store the difference `d[l][r]` = (score of the player to move) − (score of the other)
on `x[l..r]`. Taking `x_l` leaves the opponent to move on `[l+1, r]`, so
`d[l][r] = max(x_l − d[l+1][r], x_r − d[l][r−1])`.""",
        r"""Compute `l` from right to left and `r` from `l` upward. The answer is
`(total + d[1][n]) / 2`, in `long long`.""",
    ],
    editorial=r"""
Every position of the game is a contiguous block `x[l..r]` plus whose turn it is, and the
game from there does not depend on how the block was reached. Store the difference
`d[l][r]` = (mover's total) − (other's total) from this block on, under optimal play. After
taking `x_l`, the roles swap and the opponent leads by `d[l+1][r]`, so

```
d[l][r] = max(x_l - d[l+1][r], x_r - d[l][r-1]),      d[l][l] = x_l
```

Because the total is fixed, maximising one's own score and maximising the difference are
the same goal, and the first player's score is `(total + d[1][n]) / 2`.

`d[l][r]` needs `d[l+1][r]` (a later `l`) and `d[l][r−1]` (a smaller `r`): run `l` downward
and `r` upward. That is n^2/2 = 1.25·10^7 states. A full `long long` table is 200 MB; one
array updated in place works, because in that loop order `d[r]` still holds `d[l+1][r]` when
it is read. Scores reach 5·10^12: `long long`. Greedy (take the larger end) fails on the
sample.
""",
)

DIGITS = Problem(
    id="counting_numbers",
    title="Counting Numbers",
    difficulty="hard",
    source="CSES 2220 - Counting Numbers",
    complexity="O(digits · 10 · 10)",
    statement=r"""
Count the integers between `a` and `b` (inclusive) in which no two adjacent digits are
equal. Numbers are written in the usual way, without leading zeros; `0` itself counts.
""",
    input=r"""
One line with two integers `a` and `b` (0 ≤ a ≤ b ≤ 10^18).
""",
    output=r"""
The number of integers in `[a, b]` with no two equal adjacent digits.
""",
    samples=[
        Test("123 321\n", "171\n"),
        Test("0 10\n", "11\n", note="All of 0..9 count, and so does 10."),
    ],
    tests=[
        Test("0 0\n"),
        Test("11 11\n"),
        Test("10 11\n"),
        Test("98 102\n"),
        Test("999999999999999999 1000000000000000000\n"),
        Test("1000000000000000000 1000000000000000000\n"),
        Test("989898989898989898 989898989898989898\n"),
    ],
    gens=[
        Gen("small ranges", _range_small, 10),
        Gen("narrow ranges near 10^18", _range_narrow_high, 8),
        Gen("everything", lambda rng: "0 1000000000000000000\n", 1, large=True),
        Gen("wide random ranges", _range_wide, 3, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

string s;                                    // digits of the current upper bound N
long long memo[20][11][2];
bool seen[20][11][2];

// Numbers whose digits from position pos onward are still free, given:
//   prev    = the previous digit (10 while nothing has been written),
//   tight   = the digits so far equal N's prefix, so the next one is capped by s[pos],
//   started = a nonzero digit has been written (leading zeros are not digits).
long long go(int pos, int prev, bool tight, bool started) {
    if (pos == (int)s.size()) return 1;      // one finished number (0 if never started)
    if (!tight && seen[pos][prev][started]) return memo[pos][prev][started];
    int lim = tight ? s[pos] - '0' : 9;
    long long res = 0;
    for (int dgt = 0; dgt <= lim; dgt++) {
        if (started && dgt == prev) continue;          // equal adjacent digits
        bool st = started || dgt != 0;
        res += go(pos + 1, st ? dgt : 10, tight && dgt == lim, st);
    }
    if (!tight) { seen[pos][prev][started] = true; memo[pos][prev][started] = res; }
    return res;
}

long long countUpTo(long long N) {           // valid numbers in [0, N]
    if (N < 0) return 0;
    s = to_string(N);
    memset(seen, 0, sizeof seen);            // the memo depends on the length of N
    return go(0, 10, true, false);
}

int main() {
    long long a, b;
    cin >> a >> b;
    cout << countUpTo(b) - countUpTo(a - 1) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
bool ok(long long v) {
    string s = to_string(v);
    for (size_t i = 0; i + 1 < s.size(); i++)
        if (s[i] == s[i + 1]) return false;
    return true;
}
int main() {
    long long a, b;
    cin >> a >> b;
    long long c = 0;
    for (long long v = a; v <= b; v++) c += ok(v);
    cout << c << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long a, b;
    cin >> a >> b;
    long long c = 0;
    for (long long v = a; v <= b; v++) {     // check every number: up to 10^18 of them
        long long t = v;
        int prev = -1;
        bool good = true;
        while (t > 0) {
            int d = t % 10;
            if (d == prev) { good = false; break; }
            prev = d;
            t /= 10;
        }
        c += good;
    }
    cout << c << '\n';
}
""",
    hints=[
        r"""Count `f(N)` = valid numbers in `[0, N]`; the answer is `f(b) − f(a − 1)`, with
`f(−1) = 0`.""",
        r"""Build the number digit by digit from the left. Remember the previous digit, whether you
are still equal to `N`'s prefix (then the next digit is capped by `N`'s digit), and whether
you have written a nonzero digit yet.""",
        r"""Leading zeros are not digits: `7` is not `007`, so a zero before the first nonzero digit
must not be compared with the next one.""",
    ],
    editorial=r"""
Counting in a range is two prefix counts (the algo01 idea): `f(b) − f(a − 1)`, where `f(N)`
counts valid numbers in `[0, N]` and `f(−1) = 0`, which matters when `a = 0`.

`f(N)` builds numbers digit by digit, left to right, against the digits of `N`. The state:
the position, the previous digit, **tight** (the prefix so far equals `N`'s prefix, so the
next digit may not exceed `N`'s digit there; once a smaller digit is placed, every later
digit is free), and **started** (a nonzero digit has been written; before that, zeros are
padding and are not compared). Each state tries at most 10 digits, and there are about
19 · 11 · 2 · 2 states: nothing, compared with the 10^18 numbers a loop would check.

Only non-tight states are memoised: there is a single tight path, so caching it gains
nothing, and caching it with the non-tight results would be wrong. The memo must be
cleared between `f(b)` and `f(a − 1)`, since "position" means something different for a
bound with a different number of digits.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo08",
    title="dynamic programming III: bitmasks, intervals & digits",
    track="algo",
    order=8,
    summary="Three state shapes beyond prefixes: a subset as a bitmask (n ≤ 20), a "
            "contiguous interval, and the digits of a bound, with the dominance argument "
            "that makes Elevator Rides O(2^n · n).",
    prereqs=["algo07", "cpp10"],
    tags=["dynamic programming", "bitmask dp", "interval dp", "digit dp", "games",
          "hamiltonian path"],
    parts=[
        Part("When the state is a set", [
            Say(r"""
There are `n ≤ 20` cities and `m ≤ n^2` one-way flights, possibly several between the same
two cities. Count the routes from city 1 to city `n` that visit every city exactly once,
modulo 10^9 + 7 (CSES *Hamiltonian Flights*).

algo05's backtracking extends the route one city at a time and counts the complete ones.
"""),
            Numeric(r"""
With 20 cities and a flight between every ordered pair of cities, how many complete routes
does backtracking walk through?
""", answer=6.4e15, rel=0.5, unit="routes",
                hint="The first and last cities are fixed. The other 18 can come in any order.",
                explain=r"""
18! ≈ 6.4·10^15. Hopeless, and it is not a contrived worst case: dense graphs are exactly
where the answer is large.
"""),
            Reflect(r"""
Two partial routes start at city 1, have both visited exactly the cities {1, 3, 4, 7}, and
both stand at city 7: one went `1 → 3 → 4 → 7`, the other `1 → 4 → 3 → 7`. How do their
possible completions compare? What, then, should the state of a DP be?
""", answer=r"""
They have exactly the same completions: the rest of the route must start at 7 and cover
exactly the unvisited cities, and neither depends on the order in which 3 and 4 were
visited. So the state is (set of visited cities, current city), and `dp` counts the partial
routes that reach it. Backtracking explores the same completions once per ordering of the
visited cities; the DP explores them once. The set cannot be dropped (it says which cities
are still allowed), and neither can the current city (it says which flights leave).
"""),
            Say(r"""
Number the cities from 0 in code (city 1 becomes 0, city `n` becomes `n − 1`). A set of
cities is stored as a **bitmask** (cpp10): an integer whose bit `i` is 1 exactly when city
`i` is in the set. `mask >> i & 1` tests membership, `mask | 1 << i` adds city `i`,
`mask ^ 1 << i` removes it (XOR toggles, so only when it is present), and the sets of `n`
cities are the integers `0..2^n − 1`.
"""),
            Short(r"""
Which integer represents the set {0, 2, 3}?
""", accept=["13"], placeholder="an integer",
                explain=r"""
`2^0 + 2^2 + 2^3 = 1 + 4 + 8 = 13`, binary `1101`.
"""),
            Numeric(r"""
How many states (mask, current city) are there for `n = 20`?
""", answer=2.1e7, rel=0.5, unit="states",
                explain=r"""
`2^20 · 20 ≈ 2.1·10^7`. Against 6.4·10^15 routes. That is the signal to remember: **n ≤ 20
(or so) suggests a state that is a subset**, because 2^20 ≈ 10^6 fits and 20! does not.
"""),
            MCQ(r"""
Let `dp[mask][v]` = the number of routes from city 0 that visit exactly the cities of
`mask` and end at `v`. How is it computed?
""", [
                Opt("Sum over `u` of `dp[mask][u]` · (flights `u → v`).",
                    why="`mask` already contains `v`. Before the last flight, the route had "
                        "visited `mask` *without* `v`; using `mask` would allow visiting `v` twice."),
                Opt("Sum over `u` in `mask`, `u ≠ v`, of `dp[mask without v][u]`, for each `u` that "
                    "has a flight to `v`.",
                    why="Close, but two different flights from `u` to `v` make two different "
                        "routes. The second sample has exactly that: the answer is 2, not 1."),
                Opt("Sum over `u` in `mask`, `u ≠ v`, of `dp[mask without v][u]` · (flights `u → v`).",
                    correct=True,
                    why="Yes: classify by the city before `v`. Multiply by the number of flights, "
                        "since each is a different route."),
            ]),
            MCQ(r"""
In which order can the masks be processed?
""", [
                Opt("Increasing numeric order: `mask without v` is always a smaller integer than "
                    "`mask`.", correct=True,
                    why="Right. Clearing a bit always decreases the number, so `for (mask = 0; mask "
                        "< 1 << n; mask++)` computes every set after all its subsets."),
                Opt("Only by number of cities (popcount): numeric order can reach a set before "
                    "one of its subsets.",
                    why="Popcount order works, but numeric order does too: a subset of `mask` is "
                        "never a larger integer than `mask`."),
                Opt("Decreasing numeric order, from the full set down.",
                    why="The full set would read `dp[full without v]`, which is not computed yet."),
            ]),
            Numeric(r"""
The work: every mask, every last city `v`, every previous city `u`. For `n = 20`, about
how many steps?
""", answer=4.2e8, rel=0.5, unit="steps",
                explain=r"""
`2^20 · 20 · 20 ≈ 4.2·10^8`: borderline for one second. Two observations remove three
quarters of it. Every useful mask contains city 0 (the routes start there): odd masks only.
And a mask containing city `n − 1` is useful only if it is complete, since the route must
end there: skip the others. That leaves about 10^8 cheap steps.
"""),
            MCQ(r"""
`dp` is an `int` table reduced modulo 10^9 + 7, and `cnt[u][v] ≤ 400`. What is wrong with
`dp[mask][v] = (dp[mask][v] + dp[prev][u] * cnt[u][v]) % MOD;`?
""", [
                Opt("`dp[prev][u] * cnt[u][v]` is an `int` product up to 4·10^11: it overflows "
                    "before the `%`.", correct=True,
                    why="Right. Write `1LL * dp[prev][u] * cnt[u][v]`, or accumulate the sum over "
                        "`u` in a 64-bit variable and reduce once."),
                Opt("Nothing: the `% MOD` keeps it in range.",
                    why="The `%` comes after the multiplication, and the multiplication already "
                        "overflowed."),
                Opt("The table should be `long long` to hold the answer.",
                    why="Every stored value is below 10^9 + 7, which fits in `int`; `long long` "
                        "would double the table to 160 MB. Only the product needs 64 bits."),
            ], explain=r"""
Memory is the other cost of bitmask DPs: `int dp[1 << 20][20]` is 80 MB. Make it global
(a local array of that size overflows the stack), and prefer `int` when values fit.
"""),
            Try("hamiltonian_flights", note="Odd masks, `cnt[u][v]` as a count, 64-bit products."),
        ]),
        Part("A set and a little more: Elevator Rides", [
            Say(r"""
`n ≤ 20` people must reach the top floor; the elevator carries any group of total weight at
most `x` (up to 10^9). Minimise the number of rides (CSES *Elevator Rides*). This is bin
packing, a famously hard problem in general, and `n ≤ 20` is the hint. Trying every
boarding order (algo05) is 20! ≈ 2.4·10^18 orders; a greedy is the other temptation.
"""),
            MCQ(r"""
Weights `6 5 3 2 2 2`, `x = 10`. Greedy: take people heaviest first, each into the first
ride with room. What happens?
""", [
                Opt("Rides `6+3`, `5+2+2`, `2`: three rides, and three is optimal.",
                    why="The total is exactly 20 = 2 · 10, and `6+2+2` with `5+3+2` fills two rides "
                        "exactly."),
                Opt("Rides `6+2+2` and `5+3+2`: greedy finds the optimum.",
                    why="After 6 and 5 open two rides, greedy puts the 3 with the 6 (the first ride "
                        "with room), and then the 2s no longer fit in the right places."),
                Opt("Rides `6+3`, `5+2+2`, `2`: three rides, but `6+2+2` and `5+3+2` need only two.",
                    correct=True,
                    why="Right. Every ride must be exactly full for two rides to work, and greedy "
                        "has no way to see that."),
            ]),
            Say(r"""
A first DP: `dp[S]` = the fewest rides for the set of people `S`, where the last ride is
some subset `R ⊆ S` with weight at most `x`:
`dp[S] = 1 + min over such R of dp[S without R]`. Correct, but it loops over every subset of
every subset.
"""),
            Numeric(r"""
How many pairs (set `S`, subset `R ⊆ S`) are there for `n = 20`?
""", answer=3486784401, rel=0.5, unit="pairs",
                hint="For each person, in how many ways can they relate to the pair (S, R)?",
                explain=r"""
`3^20 ≈ 3.5·10^9`: each person is outside `S`, in `S` but not in `R`, or in `R`. Several
seconds. (The `for (R = S; R > 0; R = (R - 1) & S)` loop that enumerates submasks is worth
knowing, and this 3^n bound is its cost.)
"""),
            Reflect(r"""
Here is the better idea. Let people board one at a time: each joins the current ride if it
has room, or else opens a new ride. After a set `S` of people has boarded, what do you need
to know to continue?
""", answer=r"""
Two numbers: how many rides have been used, and how much weight is in the current (open)
ride. Which people are in which earlier ride is irrelevant, since those rides are gone.
Every way of splitting people into rides can be produced by some boarding order (list each
ride's people together), so optimising over orders loses nothing. The state is the set `S`,
and for each `S` we want the best pair (rides, load).
"""),
            MCQ(r"""
For the same set `S`, two boarding orders end in (2 rides, open ride holding 9) and
(3 rides, open ride holding 1). Which one should `dp[S]` keep?
""", [
                Opt("(3, 1): its open ride has much more room.",
                    why="From (2, 9) you can simply open a new ride and be at (3, 0), which beats "
                        "(3, 1) outright. More room never makes up for an extra ride."),
                Opt("Both: neither dominates the other.",
                    why="(2, 9) dominates: whatever (3, 1) does next, (2, 9) can match it after "
                        "opening a fresh ride, with one ride fewer or the same."),
                Opt("(2, 9): compare rides first, then load. The lexicographically smallest pair "
                    "is never worse.", correct=True,
                    why="Right. Fewer rides always wins, because a fresh ride is always available; "
                        "with equal rides, a lighter open ride is at least as good. So one pair "
                        "per set suffices, compared with plain `<` on `pair`."),
            ], explain=r"""
This is the same kind of **dominance** argument as LIS's smallest tails in algo07: among
partial solutions that look the same to the future, keep only the one that is at least as
good in every respect.
"""),
            Short(r"""
`x = 10`, weights A = 4, B = 8, C = 6, D = 1. The base case is `dp[{}] = (1, 0)`: one
open, empty ride. What is `dp[{A, C, D}]`? Write it as two numbers, rides then load.
""", accept=["2 1", "(2, 1)", "2,1"], placeholder="rides load",
                hint="Can A, C, D (4 + 6 + 1 = 11) share one ride? If not, which order leaves the "
                     "lightest open ride?",
                explain=r"""
`(2, 1)`: 4 + 6 + 1 = 11 does not fit in one ride, so two rides are needed, and the best
order puts A and C in the first ride (exactly 10) and D alone in the open one. The full set
ends at `(2, 9)`: rides `4 + 6` and `8 + 1`.
"""),
            MCQ(r"""
Why is the base case `(1, 0)` and not `(0, 0)`?
""", [
                Opt("With `(0, 0)`, the first person fits in the 'current ride' of load 0 and the "
                    "ride is never counted: every answer comes out one too small.", correct=True,
                    why="Right. The transition only counts a ride when it *opens* one. Starting with "
                        "one open, empty ride counts it up front. (`(0, x)`, a full imaginary ride, "
                        "also works.)"),
                Opt("They give the same answers; it is a matter of style.",
                    why="Try the sample: with `(0, 0)` the full set ends at `(1, 9)` and the "
                        "program prints 1."),
                Opt("Because `(0, 0)` would make the pairs compare wrongly.",
                    why="Pairs compare fine either way; the problem is that the first ride is never "
                        "counted."),
            ]),
            Try("elevator_rides", note="`pair<int, long long>` per mask, `min` on pairs, start from "
                "`(1, 0)`."),
        ]),
        Part("Intervals: a two-player game", [
            Say(r"""
`n ≤ 5000` numbers (possibly negative) in a row. Two players alternately remove the first
or the last number and add it to their score; both play optimally for their own score.
What does the first player get (CSES *Removal Game*)? The game tree branches twice per move:
2^5000 leaves, so searching it is out.
"""),
            MCQ(r"""
Row `4 5 1 3`. If both players always take the larger end, what does the first player
score, and is that optimal for them?
""", [
                Opt("7 (4, then 3), and it is optimal.",
                    why="Taking 3 first scores 8: whatever the opponent takes next, the 5 becomes "
                        "available to you. Grabbing the larger end hands the 5 to the opponent."),
                Opt("8, and greedy is optimal.",
                    why="Greedy takes 4, the opponent takes 5, then 3 and 1: 4 + 3 = 7."),
                Opt("7, but taking 3 first gives 8.", correct=True,
                    why="Right. Taking the 4 exposes the 5. The value of a move depends on what it "
                        "leaves for the opponent."),
            ]),
            Reflect(r"""
Whatever the players do, what do the remaining numbers always look like? Use that to
define a state. Then: what should the state store, given that the next move is made by the
*other* player?
""", answer=r"""
Removing only from the ends leaves a contiguous block `x[l..r]`, so the state is the
interval `(l, r)`: about n^2/2 = 1.25·10^7 of them. Store the **difference** `d[l][r]` =
(score of the player about to move) − (score of the other), from this block on, under
optimal play. After a move the roles swap, and the opponent's best difference on the
remaining block counts *against* the mover, which is why a single number per interval is
enough.
"""),
            MCQ(r"""
Which transition is right?
""", [
                Opt("`d[l][r] = max(x_l − d[l+1][r], x_r − d[l][r−1])`", correct=True,
                    why="Yes. Take `x_l`, and the opponent then leads by `d[l+1][r]` on the rest; "
                        "or take `x_r` similarly. The mover picks the better."),
                Opt("`d[l][r] = max(x_l + d[l+1][r], x_r + d[l][r−1])`",
                    why="That treats the rest as if the same player kept moving. After your move the "
                        "opponent moves, and their lead is your loss."),
                Opt("`d[l][r] = min(x_l − d[l+1][r], x_r − d[l][r−1])`",
                    why="The mover chooses the move that is best *for them*: `max`. The opponent's "
                        "minimising is already inside `d[l+1][r]` and `d[l][r−1]`."),
            ], explain=r"""
Base case `d[l][l] = x_l`. Since both totals add up to the sum of the row, the first
player's score is `(total + d[1][n]) / 2`.
"""),
            Short(r"""
Row `4 5 1 3`. Single numbers: `d = x`. Pairs: `d[1][2] = 1`, `d[2][3] = 4`, `d[3][4] = 2`.
Compute `d[1][3]`, `d[2][4]` and `d[1][4]`, in that order.
""", accept=["0 3 3", "0,3,3"], placeholder="three numbers",
                hint="`d[1][3] = max(4 − d[2][3], 1 − d[1][2])`.",
                explain=r"""
`d[1][3] = max(4 − 4, 1 − 1) = 0`, `d[2][4] = max(5 − 2, 3 − 4) = 3`,
`d[1][4] = max(4 − 3, 3 − 0) = 3`: take the 3. The total is 13, so the first player scores
`(13 + 3) / 2 = 8`.
"""),
            MCQ(r"""
`d[l][r]` reads `d[l+1][r]` and `d[l][r−1]`. Which loop order computes every entry after
both of them?
""", [
                Opt("`l` from 1 up to `n`, and `r` from `l` up to `n`.",
                    why="`d[l][r]` would read `d[l+1][r]`, a row that has not been computed yet."),
                Opt("`l` from `n` down to 1, and `r` from `l` up to `n`.", correct=True,
                    why="Right: the row below (`l + 1`) is finished, and `d[l][r−1]` was computed "
                        "just before in the same row. Looping over the length `r − l` in "
                        "increasing order also works."),
                Opt("`l` from `n` down to 1, and `r` from `n` down to `l`.",
                    why="`d[l][r]` would read `d[l][r−1]`, which in this row comes later."),
            ], explain=r"""
Interval DPs always depend on shorter intervals, so "by increasing length" is the safe
default. The full `long long` table would be 200 MB; in the `l`-down, `r`-up order a
single array works, because `d[r]` still holds `d[l+1][r]` when it is read.
"""),
            Try("removal_game", note="`long long` everywhere: scores reach 5·10^12."),
        ]),
        Part("Digits: counting up to a huge bound", [
            Say(r"""
Count the integers in `[a, b]`, `0 ≤ a ≤ b ≤ 10^18`, in which no two adjacent digits are
equal (CSES *Counting Numbers*). `123` counts, `122` and `100` do not, `0` does.

A loop over the range checks up to 10^18 numbers: at 10^9 per second, thirty years. The
numbers are too many, but their *digits* are few: at most 19.
"""),
            MCQ(r"""
First, turn the range into something simpler. Let `f(N)` = the count in `[0, N]`. What is
the answer?
""", [
                Opt("`f(b) − f(a)`",
                    why="That drops `a` itself: `f(a)` includes `a`, so subtracting it removes it "
                        "from the range. Try `a = b = 5`: the answer is 1, not 0."),
                Opt("`f(b) − f(a − 1)`, with `f(−1) = 0` for the case `a = 0`.", correct=True,
                    why="Right: the prefix-sum trick of algo01, applied to counts. The `a = 0` case "
                        "needs `f(−1)` to be 0, not a digit DP on the string `-1`."),
                Opt("`f(b − a)`",
                    why="The property depends on the actual digits, not on the width of the range: "
                        "`[10, 12]` contains two valid numbers (10 and 12), while `f(2)` counts "
                        "three (0, 1, 2)."),
            ]),
            Short(r"""
How many 3-digit numbers (100 to 999) have no two equal adjacent digits?
""", accept=["729"], placeholder="a number",
                hint="Choose the digits left to right. How many choices does each one have?",
                explain=r"""
`9 · 9 · 9 = 729`: the first digit is 1..9, and every later digit is anything except the
digit before it. When nothing caps the digits, counting is multiplication. The only
difficulty in `f(N)` is the cap `N` itself.
"""),
            Reflect(r"""
To count up to `N` (say `N = 234`), build numbers digit by digit from the left. At each
step, what do you need to remember about the digits written so far to know which digits
are allowed next?
""", answer=r"""
The previous digit (the next one must differ). Whether the digits so far are exactly `N`'s
prefix (**tight**): if they are, the next digit can be at most `N`'s digit in that position;
once some digit is smaller than `N`'s, every later digit is free. And whether a nonzero
digit has been written (**started**): the zeros before it are not really digits, so they
must not be compared. State: (position, previous digit, tight, started), about
19 · 11 · 2 · 2 of them.
"""),
            MCQ(r"""
`N = 234`. Which digits may come next after writing `2 1`, and after writing `2 3`?
""", [
                Opt("After `2 1`: `0` to `4` except `1`. After `2 3`: `0` to `4` except `3`.",
                    why="`21_` is already below `23_`, so the cap no longer applies: `219` is "
                        "fine. Only the tight prefix `23` is capped by `N`'s last digit."),
                Opt("After `2 1`: any digit except `1`. After `2 3`: `0` to `4` except `3`.",
                    correct=True,
                    why="Right. `2 1` left the tight path, so everything is free except repeating "
                        "the 1. `2 3` is still tight: at most 4, and not 3."),
                Opt("After both: any digit except the previous one.",
                    why="`239` is larger than 234. While the prefix equals `N`'s, the next digit is "
                        "capped."),
            ]),
            Numeric(r"""
Count the valid numbers in `[200, 234]` by walking the digits of 234.
""", answer=22, hint="Split by the second digit: `20_`, `21_`, `22_`, and the tight `23_`.",
                explain=r"""
22. `20_`: 9 (anything but 0). `21_`: 9 (anything but 1). `22_`: none. `23_`, capped at 4:
`230, 231, 232, 234`, 4. That is `9 + 9 + 0 + 4`, exactly what the DP computes, with the
free branches counted by multiplication and only one tight path.
"""),
            MCQ(r"""
Without the **started** flag (treating the number as `N`'s length with leading zeros),
what happens to `7` when `N = 234`?
""", [
                Opt("It is counted correctly as `007`, since leading zeros are ignored anyway.",
                    why="Without the flag nothing ignores them: `0` followed by `0` is two equal "
                        "adjacent digits, as far as the DP can tell."),
                Opt("It is written `007`, the two zeros look equal and adjacent, and 7 is wrongly "
                    "rejected.", correct=True,
                    why="Right. Every number shorter than `N` with more than one leading zero "
                        "disappears. The flag makes zeros before the first nonzero digit invisible."),
                Opt("It is counted twice, once as `7` and once as `07`.",
                    why="Each number corresponds to exactly one digit string of `N`'s length; the "
                        "problem is that string's zeros, not duplicates."),
            ]),
            Say(r"""
The DP as a memoised recursion (the order of states is awkward as loops, and depth is only
19):

```cpp
long long go(int pos, int prev, bool tight, bool started) {
    if (pos == (int)s.size()) return 1;          // one finished number
    if (!tight && seen[pos][prev][started]) return memo[pos][prev][started];
    int lim = tight ? s[pos] - '0' : 9;
    long long res = 0;
    for (int d = 0; d <= lim; d++) {
        if (started && d == prev) continue;      // equal adjacent digits
        bool st = started || d != 0;
        res += go(pos + 1, st ? d : 10, tight && d == lim, st);
    }
    if (!tight) { seen[pos][prev][started] = true; memo[pos][prev][started] = res; }
    return res;
}
```

`s` is `to_string(N)`, and `prev = 10` means "no digit yet".
"""),
            MCQ(r"""
The memo is cleared between computing `f(b)` and `f(a − 1)`. Is that necessary?
""", [
                Opt("No: the counts from the same state are the same for any bound.",
                    why="`pos` counts from the left of *this* bound. With `b` of 19 digits and "
                        "`a − 1` of 3, 'position 1' leaves 18 free digits in one and 2 in the other."),
                Opt("Yes: `pos` is measured from the left, so the same state means a different "
                    "number of remaining digits for bounds of different lengths.", correct=True,
                    why="Right. Clearing a 20 × 11 × 2 table costs nothing. (Indexing by digits "
                        "*remaining* instead would make the memo reusable.)"),
                Opt("Yes, because the tight states are memoised too.",
                    why="The code never memoises tight states; there is only one tight path, and "
                        "it depends on the bound."),
            ]),
            Try("counting_numbers", note="`f(b) − f(a − 1)`, `f(−1) = 0`, and mind the leading zeros."),
        ]),
        Part("Recognising the state", [
            MCQ(r"""
`n ≤ 16` workers and `n` jobs, a cost matrix; each worker gets exactly one job. Minimise
the total cost. Which state?
""", [
                Opt("`dp[mask]` = the minimum cost to give the jobs in `mask` to the first "
                    "`popcount(mask)` workers.", correct=True,
                    why="Right. The next worker is determined by how many jobs are taken, so the "
                        "mask alone is the state: 2^16 · 16 ≈ 10^6 steps. The worker index is "
                        "implied, not stored."),
                Opt("`dp[i][j]` = the cost of giving job `j` to worker `i`, then take the "
                    "cheapest job for each worker.",
                    why="That is a greedy, and two workers may want the same job. The state must "
                        "remember which jobs are taken: a set."),
                Opt("`dp[mask][i]` with the last worker `i`, as in Hamiltonian Flights.",
                    why="Correct but wasteful: here the order of assignment is fixed (worker 1, "
                        "then 2, ...), so the last worker is `popcount(mask)` and need not be stored."),
            ]),
            MCQ(r"""
`n ≤ 400` piles in a row; merging two *adjacent* piles costs the sum of their sizes; merge
everything into one pile at minimum total cost. What is the DP and its cost?
""", [
                Opt("Intervals: `dp[l][r] = min over split k of dp[l][k] + dp[k+1][r] + sum(l..r)`: "
                    "n^2 states, n choices each, O(n^3) ≈ 6.4·10^7.", correct=True,
                    why="Right. The last merge joins some `[l, k]` with `[k+1, r]`, and trying every "
                        "split point costs a factor of `n`: the typical interval DP."),
                Opt("Always merge the two adjacent piles with the smallest sum: O(n^2).",
                    why="The Huffman-style greedy is correct when *any* two piles may merge. With "
                        "adjacency required it fails, like the removal game's greedy."),
                Opt("A bitmask over the piles: 2^400 states.",
                    why="The merged piles are always contiguous blocks, so an interval `(l, r)` "
                        "describes them; a subset state throws that structure away."),
            ]),
            Reflect(r"""
From this lesson and the two before it: what in a problem statement suggests each state
shape: a prefix, a subset, an interval, digits of a bound?
""", answer=r"""
Prefix (`dp[i]`, `dp[i][j]`): items or sequences processed left to right, where the future
depends on a small summary (money spent, a position in the other string). Subset
(`dp[mask]`, maybe with a last element): n ≤ 20 or so, and the order of the chosen items
matters to the problem but not to the future. Interval (`dp[l][r]`): elements removed or
merged at the ends or between neighbours, so what remains is always contiguous; n up to a
few thousand for O(n^2), a few hundred for O(n^3). Digits: count numbers in `[a, b]` with
`b` up to 10^18 and a property of their digits; state (position, what the property needs,
tight, started).
"""),
        ]),
    ],
    problems=[HAMILTON, ELEVATOR, REMOVAL, DIGITS],
    cards=[
        Card(r"""What limit on `n` suggests a bitmask DP, and why?""",
             r"""n ≤ 20 or so: 2^20 ≈ 10^6 subsets fit, while n! (orders) does not."""),
        Card(r"""Bitmask idioms: test, add, remove element `i`?""",
             r"""`mask >> i & 1`, `mask | 1 << i`, `mask ^ 1 << i` (or `mask & ~(1 << i)`)."""),
        Card(r"""Hamiltonian paths counting: state and transition?""",
             r"""`dp[mask][v]` = paths from the start over exactly `mask`, ending at `v`; `dp[mask][v] = Σ dp[mask ^ 1<<v][u] · cnt[u][v]`. Masks in increasing numeric order."""),
        Card(r"""Why does increasing numeric order work for DPs over subsets?""",
             r"""Removing an element clears a bit, which always gives a smaller integer; so every subset is processed before its supersets."""),
        Card(r"""How many (set, subset) pairs are there for n elements?""",
             r"""3^n: each element is outside, in the set only, or in both. 3^20 ≈ 3.5·10^9."""),
        Card(r"""Elevator Rides: what is stored per subset, and why is one value enough?""",
             r"""The lexicographically smallest (rides, load of the open ride). Fewer rides always wins, since opening a fresh ride gives (r + 1, 0); with equal rides, less load is better. Base `(1, 0)`."""),
        Card(r"""Removal Game: state and transition?""",
             r"""`d[l][r]` = mover's score minus the other's on `x[l..r]`; `d[l][r] = max(x_l − d[l+1][r], x_r − d[l][r−1])`. First player gets `(total + d[1][n]) / 2`."""),
        Card(r"""Interval DP: what order of computation is always safe?""",
             r"""Increasing interval length (or `l` downward with `r` upward), since every interval reads only shorter ones."""),
        Card(r"""Count numbers in `[a, b]` with a digit property?""",
             r"""`f(b) − f(a − 1)` with `f(−1) = 0`, where `f(N)` is a digit DP over (position, property state, tight, started)."""),
        Card(r"""Digit DP: what do the `tight` and `started` flags mean?""",
             r"""`tight`: the prefix so far equals `N`'s, so the next digit is capped by `N`'s digit. `started`: a nonzero digit was written; leading zeros are ignored."""),
        Card(r"""Merging adjacent piles at minimum cost: DP and complexity?""",
             r"""Interval DP over the split point: `dp[l][r] = min_k dp[l][k] + dp[k+1][r] + sum(l..r)`, O(n^3)."""),
    ],
)
