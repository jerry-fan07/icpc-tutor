from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _hike(rng, n, q, hmax, wide, zigzag=False):
    if zigzag:
        h = [0 if i % 2 == 0 else hmax for i in range(n)]
    else:
        h = [rng.randint(0, hmax) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, h))]
    for _ in range(q):
        if wide:                                   # nearly the whole trail, either way
            a = rng.randint(1, min(n, 40))
            b = rng.randint(max(1, n - 40), n)
            s, t = (a, b) if rng.random() < 0.5 else (b, a)
        else:
            s, t = rng.randint(1, n), rng.randint(1, n)
        out.append(f"{s} {t}")
    return "\n".join(out) + "\n"


def _crates(rng, n, wmin, wmax):
    return f"{n}\n" + " ".join(str(rng.randint(wmin, wmax)) for _ in range(n)) + "\n"


def _pantry(rng, n, amin, amax, bmax, kmax):
    a = [rng.randint(amin, amax) for _ in range(n)]
    b = [rng.randint(0, bmax) for _ in range(n)]
    k = rng.randint(0, kmax)
    return f"{n} {k}\n" + " ".join(map(str, a)) + "\n" + " ".join(map(str, b)) + "\n"


def _pantry_flat(n, a, b, k):
    return f"{n} {k}\n" + " ".join([str(a)] * n) + "\n" + " ".join([str(b)] * n) + "\n"


def _floor(rng, n, m, wall, exits):
    g = [["#" if rng.random() < wall else "." for _ in range(m)] for _ in range(n)]
    for c in rng.sample(range(n * m), min(exits, n * m)):
        g[c // m][c % m] = "E"
    if all(ch == "#" for row in g for ch in row):
        g[rng.randrange(n)][rng.randrange(m)] = "."
    return f"{n} {m}\n" + "\n".join("".join(r) for r in g) + "\n"


def _floor_open(rng, n, m, exits):
    g = [["."] * m for _ in range(n)]
    for c in rng.sample(range(n * m), exits):
        g[c // m][c % m] = "E"
    return f"{n} {m}\n" + "\n".join("".join(r) for r in g) + "\n"


def _floor_snake(n, m):
    """Wall rows with one gap at alternating ends: one exit, very long walks."""
    rows = []
    for i in range(n):
        if i % 2 == 1:
            r = ["#"] * m
            r[m - 1 if (i // 2) % 2 == 0 else 0] = "."
            rows.append("".join(r))
        else:
            rows.append("." * m)
    rows[0] = "E" + rows[0][1:]
    return f"{n} {m}\n" + "\n".join(rows) + "\n"


def _jobs(rng, n, tvals, wvals):
    return f"{n}\n" + "\n".join(f"{rng.choice(tvals)} {rng.choice(wvals)}" for _ in range(n)) + "\n"


def _jobs_range(rng, n, tmax, wmax):
    return f"{n}\n" + "\n".join(f"{rng.randint(1, tmax)} {rng.randint(1, wmax)}" for _ in range(n)) + "\n"


# --------------------------------------------------------------------- problems
ASCENT = Problem(
    id="total_ascent",
    title="Total Ascent",
    difficulty="easy",
    complexity="O(n + q)",
    statement=r"""
A hiking app stores the elevation of `n` checkpoints along a trail, in order:
h_1, ..., h_n metres. Hikers ask `q` questions: "if I walk along the trail from
checkpoint `s` to checkpoint `t`, how many metres do I climb in total?" Only the uphill
parts count: walking from a checkpoint to the next one climbs the elevation gain if the
next one is higher, and nothing otherwise.

Hikers may walk the trail in either direction.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has h_1, ..., h_n (0 ≤ h_i ≤ 10^9).

Each of the next `q` lines has `s` and `t` (1 ≤ s, t ≤ n). If `s > t`, the hiker walks
from checkpoint `s` back down the list to checkpoint `t`.
""",
    output=r"""
For each question, print the total climb in metres on its own line.
""",
    samples=[
        Test("5 4\n10 30 20 50 40\n1 5\n5 1\n3 3\n2 4\n", "50\n20\n0\n30\n",
             note="The second hiker walks from checkpoint 5 back to checkpoint 1."),
    ],
    tests=[
        Test("1 2\n1000000000\n1 1\n1 1\n"),
        Test("6 3\n0 1000000000 0 1000000000 0 1000000000\n1 6\n6 1\n2 5\n"),
        Test("4 4\n7 7 7 7\n1 4\n4 1\n2 3\n3 2\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _hike(rng, rng.randint(1, 12), rng.randint(1, 12), 20, False), 14),
        Gen("medium, big heights", lambda rng: _hike(rng, 2000, 2000, 10**9, False), 2),
        Gen("max size, zigzag, whole trail", lambda rng: _hike(rng, 200000, 200000, 10**9, True, True), 1, large=True),
        Gen("max size, random, whole trail", lambda rng: _hike(rng, 200000, 200000, 10**9, True), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<long long> h(n + 1);
    for (int i = 1; i <= n; i++) cin >> h[i];
    // up[k]:   metres climbed walking forward from checkpoint 1 to checkpoint k
    // down[k]: metres climbed walking backward from checkpoint k to checkpoint 1
    vector<long long> up(n + 1, 0), down(n + 1, 0);
    for (int k = 2; k <= n; k++) {
        up[k] = up[k - 1] + max(0LL, h[k] - h[k - 1]);
        down[k] = down[k - 1] + max(0LL, h[k - 1] - h[k]);
    }
    while (q--) {
        int s, t;
        cin >> s >> t;
        if (s <= t) cout << up[t] - up[s] << '\n';
        else cout << down[s] - down[t] << '\n';
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
    vector<long long> h(n + 1);
    for (int i = 1; i <= n; i++) cin >> h[i];
    while (q--) {
        int s, t;
        cin >> s >> t;
        long long c = 0;
        int step = s <= t ? 1 : -1;
        for (int i = s; i != t; i += step)
            if (h[i + step] > h[i]) c += h[i + step] - h[i];
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
    vector<long long> h(n + 1);
    for (int i = 1; i <= n; i++) cin >> h[i];
    while (q--) {
        int s, t;
        cin >> s >> t;
        long long c = 0;
        int step = s <= t ? 1 : -1;
        for (int i = s; i != t; i += step)
            if (h[i + step] > h[i]) c += h[i + step] - h[i];
        cout << c << '\n';
    }
}
""",
    hints=[
        r"""The climb over a stretch of trail is a sum of the climbs between neighbouring
checkpoints, and those never change.""",
        r"""Walking backwards, a step climbs when the *earlier* checkpoint is higher. Keep one
running total for each direction.""",
        r"""2·10^5 steps of up to 10^9 metres: the totals need `long long`.""",
    ],
    editorial=r"""
Prefix sums, twice. Let `up[k]` be the metres climbed walking forward from checkpoint 1
to checkpoint `k`: `up[k] = up[k-1] + max(0, h[k] − h[k-1])`. A forward walk from `s` to
`t` climbs `up[t] − up[s]`. Walking backwards, a step from `k` to `k − 1` climbs
`max(0, h[k-1] − h[k])`, so keep `down[k]` the same way and answer `down[s] − down[t]`.
O(n + q), against up to 4·10^10 steps for walking every question.

The traps are both in the reading: the direction (a single `up` array, or swapping `s` and
`t`, gets the second sample wrong), and the size of the answer (three steps of 10^9
already pass the 2.1·10^9 an `int` holds).
""",
)

TRUCKS = Problem(
    id="two_trucks",
    title="Two Trucks",
    difficulty="medium",
    complexity="O(n · W)",
    statement=r"""
A moving company must carry `n` crates with two trucks. Crate `i` weighs `w_i` kg, and
every crate goes on exactly one of the trucks. The trucks drive best when their loads are
as close as possible.

Print the smallest possible difference between the two loads.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 100).

The second line has w_1, ..., w_n (1 ≤ w_i ≤ 1000).
""",
    output=r"""
Print one integer: the minimum of |load of truck 1 − load of truck 2|.
""",
    samples=[
        Test("4\n1 2 3 10\n", "4\n"),
        Test("5\n3 3 2 2 2\n", "0\n",
             note="Loading the heaviest crate first, always onto the lighter truck, gives 7 and 5 here."),
    ],
    tests=[
        Test("1\n1000\n"),
        Test("2\n1000 1000\n"),
        Test("3\n1 1 1000\n"),
        Test("6\n8 7 6 5 4 4\n"),
        Test("20\n1000 999 998 997 996 995 994 993 992 991 1 2 3 4 5 6 7 8 9 10\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _crates(rng, rng.randint(1, 14), 1, 20), 14),
        Gen("twenty crates, heavy", lambda rng: _crates(rng, 20, 1, 1000), 3),
        Gen("max size, random", lambda rng: _crates(rng, 100, 1, 1000), 2, large=True),
        Gen("max size, heavy and close", lambda rng: _crates(rng, 100, 990, 1000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> w(n);
    int total = 0;
    for (auto& x : w) {
        cin >> x;
        total += x;                               // at most 100 * 1000 = 10^5
    }
    // can[s]: some set of the crates seen so far weighs exactly s
    vector<char> can(total + 1, 0);
    can[0] = 1;
    for (int x : w)
        for (int s = total; s >= x; s--)          // downwards: each crate used at most once
            if (can[s - x]) can[s] = 1;
    int best = total;
    for (int s = 0; s <= total; s++)
        if (can[s]) best = min(best, abs(total - 2 * s));   // truck 1 carries s
    cout << best << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n, total, best;
vector<int> w;
void go(int i, int s) {
    if (i == n) { best = min(best, abs(total - 2 * s)); return; }
    go(i + 1, s + w[i]);
    go(i + 1, s);
}
int main() {
    cin >> n;
    w.resize(n);
    for (auto& x : w) { cin >> x; total += x; }
    best = INT_MAX;
    go(0, 0);
    cout << best << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int n, total, best;
vector<int> w;
void go(int i, int s) {                           // every crate on truck 1 or not: 2^n
    if (i == n) { best = min(best, abs(total - 2 * s)); return; }
    go(i + 1, s + w[i]);
    go(i + 1, s);
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n;
    w.resize(n);
    for (auto& x : w) { cin >> x; total += x; }
    best = INT_MAX;
    go(0, 0);
    cout << best << '\n';
}
""",
    hints=[
        r"""100 crates is far too many to try every split. What is small in this problem?""",
        r"""The total weight is at most 10^5. Which loads can truck 1 carry exactly?""",
        r"""`can[s]` for s = 0..total, like a 0/1 knapsack: for each crate, for `s` from the
total down to `w`, `can[s] |= can[s - w]`. Then minimise |total − 2s|.""",
    ],
    editorial=r"""
Only the load of truck 1 matters: if it carries `s`, the difference is `|total − 2s|`. So
the question is which loads are *reachable*, and the total is at most 100 · 1000 = 10^5.
A 0/1-knapsack table does it: `can[0] = true`, and each crate `x` sets
`can[s] |= can[s − x]` for `s` from the total down to `x` (downwards so the crate is used
once). O(n · total) = 10^7 steps.

The traps: 2^100 splits is hopeless (2^n is for n ≤ 20), and the natural greedy (heaviest
crate onto the lighter truck) is wrong: `3 3 2 2 2` loads 7 and 5 greedily, while
`3 + 3 = 2 + 2 + 2`. The signal in the limits is the small *sum*, not the small `n`.
""",
)

COOKIES = Problem(
    id="cookie_batch",
    title="Cookie Batch",
    difficulty="medium",
    source="Codeforces 670D2",
    complexity="O(n log A)",
    statement=r"""
A bakery makes one kind of cookie. A cookie needs `a_i` grams of ingredient `i`, for each
of the `n` ingredients, and the pantry holds `b_i` grams of ingredient `i`. The baker can
also buy up to `k` grams of ingredients in total, split among the ingredients in any way.

What is the largest number of cookies the bakery can make?
""",
    input=r"""
The first line has `n` and `k` (1 ≤ n ≤ 10^5, 0 ≤ k ≤ 10^9).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

The third line has b_1, ..., b_n (0 ≤ b_i ≤ 10^9).
""",
    output=r"""
Print the maximum number of cookies.
""",
    samples=[
        Test("3 5\n3 1 2\n10 2 5\n", "3\n"),
        Test("1 1000000000\n1\n1000000000\n", "2000000000\n",
             note="Two billion cookies: more than an `int` holds."),
    ],
    tests=[
        Test("2 0\n5 5\n4 100\n"),
        Test("1 0\n1000000000\n0\n"),
        Test("3 1000000000\n1 1 1\n0 0 0\n"),
        Test("10 1000000000\n" + " ".join(["1000000000"] * 10) + "\n" + " ".join(["1000000000"] * 10) + "\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _pantry(rng, rng.randint(1, 8), 1, 10, 60, 60), 14),
        Gen("medium, huge amounts", lambda rng: _pantry(rng, 1000, 1, 10**9, 10**9, 10**9), 2),
        Gen("medium, small recipe", lambda rng: _pantry(rng, 1000, 1, 10, 10**4, 10**4), 2),
        Gen("max size, a billion cookies", lambda rng: _pantry(rng, 100000, 1, 3, 10**9, 10**9), 1, large=True),
        Gen("max size, everything 10^9", lambda rng: _pantry_flat(100000, 10**9, 10**9, 10**9), 1, large=True),
        Gen("max size, random", lambda rng: _pantry(rng, 100000, 1, 10**9, 10**9, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
long long k;
vector<long long> a, b;

// can we bake c cookies buying at most k grams?
bool can(long long c) {
    long long need = 0;
    for (int i = 0; i < n; i++) {
        long long want = c * a[i];               // up to 2*10^9 * 10^9 = 2*10^18: fits
        if (want > b[i]) need += want - b[i];
        if (need > k) return false;              // stop before the sum can overflow
    }
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> k;
    a.resize(n);
    b.resize(n);
    for (auto& x : a) cin >> x;
    for (auto& x : b) cin >> x;
    // can(lo) is always true, can(hi) always false: (b_i + k) / a_i <= 2*10^9
    long long lo = 0, hi = 2000000001;
    while (hi - lo > 1) {
        long long mid = lo + (hi - lo) / 2;
        if (can(mid)) lo = mid;
        else hi = mid;
    }
    cout << lo << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    long long k;
    cin >> n >> k;
    vector<long long> a(n), b(n);
    for (auto& x : a) cin >> x;
    for (auto& x : b) cin >> x;
    long long c = 0;
    while (true) {                               // is one more cookie possible?
        long long need = 0;
        for (int i = 0; i < n; i++) need += max(0LL, (c + 1) * a[i] - b[i]);
        if (need > k) break;
        c++;
    }
    cout << c << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long k;
    cin >> n >> k;
    vector<long long> a(n), b(n);
    for (auto& x : a) cin >> x;
    for (auto& x : b) cin >> x;
    long long c = 0;
    while (true) {                               // bake one cookie, buying what is missing
        long long need = 0;
        bool ok = true;
        for (int i = 0; i < n; i++) {
            if (b[i] < a[i]) need += a[i] - b[i];
            if (need > k) { ok = false; break; }
        }
        if (!ok) break;
        k -= need;
        for (int i = 0; i < n; i++) b[i] = max(0LL, b[i] - a[i]);
        c++;
    }
    cout << c << '\n';
}
""",
    hints=[
        r"""If the bakery can make `c` cookies, can it make `c − 1`? How fast can you check a
single `c`?""",
        r"""Checking `c` is one pass: buy `max(0, c·a_i − b_i)` of each ingredient and compare
the total with `k`. The answer is the largest `c` that passes.""",
        r"""The answer can reach 2·10^9 (sample 2), so the search range is `long long`, and
`c·a_i` reaches 2·10^18: stop summing as soon as the total passes `k`, or the sum
overflows.""",
    ],
    editorial=r"""
Binary search on the answer. "Can we bake `c` cookies?" is monotone (if `c` works, so does
every smaller number) and cheap to check: ingredient `i` needs `max(0, c·a_i − b_i)` extra
grams, and `c` works when the sum is at most `k`. The answer lies in `[0, 2·10^9]`
(the most any ingredient allows is `(b_i + k)/a_i ≤ 2·10^9`), so about 31 checks of
O(n) each.

The overflow traps are the problem. The answer itself passes the `int` range (sample 2).
In the check, `c·a_i` can be 2·10^18, which fits in a `long long`, but ten such terms do
not: with `n = 10` and every value 10^9, an unguarded sum wraps around to a small number
and the check says yes for 10^9 cookies. Return false as soon as the running total
exceeds `k`. Baking one cookie at a time is correct but can take 2·10^9 rounds.
""",
)

EVAC = Problem(
    id="evacuation",
    title="Evacuation",
    difficulty="medium",
    complexity="O(nm)",
    statement=r"""
A fire drill on one floor of an office. The floor is an `n × m` grid: `#` is a wall, `.`
is floor, and `E` is an exit (also floor). There is one person on every cell that is not
a wall. When the alarm sounds, everyone walks to the exit nearest to them, moving one cell
up, down, left or right per second and never through walls. People do not get in each
other's way.

How many seconds until everyone has reached an exit? If someone cannot reach any exit,
print −1.
""",
    input=r"""
The first line has `n` and `m` (1 ≤ n, m ≤ 1000).

Each of the next `n` lines has `m` characters, each `#`, `.` or `E`. At least one cell is
not a wall.
""",
    output=r"""
Print the number of seconds until the last person reaches an exit, or −1 if someone never
can. People standing on an exit are out at second 0.
""",
    samples=[
        Test("4 5\nE..#.\n.#...\n...#E\n##...\n", "4\n"),
        Test("3 3\nE#.\n##.\n...\n", "-1\n"),
    ],
    tests=[
        Test("1 1\nE\n"),
        Test("1 1\n.\n"),
        Test("2 2\n##\n#E\n"),
        Test("1 7\nE.....E\n"),
        Test("3 4\n....\n.##.\n...E\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _floor(rng, rng.randint(1, 8), rng.randint(1, 8), 0.3, rng.randint(0, 3)), 14),
        Gen("medium random", lambda rng: _floor(rng, 60, 80, 0.15, 6), 2),
        Gen("medium snake", lambda rng: _floor_snake(41, 60), 1),
        Gen("max size, open floor, 3000 exits", lambda rng: _floor_open(rng, 1000, 1000, 3000), 1, large=True),
        Gen("max size, snake, one exit", lambda rng: _floor_snake(1000, 1000), 1, large=True),
        Gen("max size, one exit", lambda rng: _floor_open(rng, 1000, 1000, 1), 1, large=True),
        Gen("max size, walls, many exits", lambda rng: _floor(rng, 1000, 1000, 0.25, 2000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    // one BFS from every exit at once: the first time a cell is reached,
    // it is reached from its nearest exit
    vector<int> dist(n * m, -1), queue;
    queue.reserve(n * m);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (g[i][j] == 'E') {
                dist[i * m + j] = 0;
                queue.push_back(i * m + j);
            }
    const int di[] = {1, -1, 0, 0}, dj[] = {0, 0, 1, -1};
    for (size_t head = 0; head < queue.size(); head++) {
        int u = queue[head], i = u / m, j = u % m;
        for (int d = 0; d < 4; d++) {
            int x = i + di[d], y = j + dj[d];
            if (x < 0 || x >= n || y < 0 || y >= m || g[x][y] == '#') continue;
            if (dist[x * m + y] != -1) continue;
            dist[x * m + y] = dist[u] + 1;
            queue.push_back(x * m + y);
        }
    }
    int worst = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            if (g[i][j] == '#') continue;
            if (dist[i * m + j] == -1) {           // this person can never get out
                cout << -1 << '\n';
                return 0;
            }
            worst = max(worst, dist[i * m + j]);
        }
    cout << worst << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    int worst = 0;
    for (int si = 0; si < n; si++)
        for (int sj = 0; sj < m; sj++) {
            if (g[si][sj] == '#') continue;
            // a BFS from this person until the first exit
            vector<vector<int>> d(n, vector<int>(m, -1));
            queue<pair<int, int>> q;
            d[si][sj] = 0;
            q.push({si, sj});
            int found = -1;
            while (!q.empty()) {
                auto [i, j] = q.front();
                q.pop();
                if (g[i][j] == 'E') { found = d[i][j]; break; }
                int di[] = {1, -1, 0, 0}, dj[] = {0, 0, 1, -1};
                for (int k = 0; k < 4; k++) {
                    int x = i + di[k], y = j + dj[k];
                    if (x < 0 || x >= n || y < 0 || y >= m || g[x][y] == '#' || d[x][y] != -1) continue;
                    d[x][y] = d[i][j] + 1;
                    q.push({x, y});
                }
            }
            if (found == -1) { cout << -1 << '\n'; return 0; }
            worst = max(worst, found);
        }
    cout << worst << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    // a BFS from each exit, keeping the smallest distance seen for every cell
    vector<int> best(n * m, INT_MAX), d(n * m), q(n * m);
    const int di[] = {1, -1, 0, 0}, dj[] = {0, 0, 1, -1};
    for (int ei = 0; ei < n; ei++)
        for (int ej = 0; ej < m; ej++) {
            if (g[ei][ej] != 'E') continue;
            fill(d.begin(), d.end(), -1);
            int head = 0, tail = 0;
            d[ei * m + ej] = 0;
            q[tail++] = ei * m + ej;
            while (head < tail) {
                int u = q[head++], i = u / m, j = u % m;
                best[u] = min(best[u], d[u]);
                for (int k = 0; k < 4; k++) {
                    int x = i + di[k], y = j + dj[k];
                    if (x < 0 || x >= n || y < 0 || y >= m || g[x][y] == '#' || d[x * m + y] != -1) continue;
                    d[x * m + y] = d[u] + 1;
                    q[tail++] = x * m + y;
                }
            }
        }
    int worst = 0;
    for (int u = 0; u < n * m; u++) {
        if (g[u / m][u % m] == '#') continue;
        if (best[u] == INT_MAX) { cout << -1 << '\n'; return 0; }
        worst = max(worst, best[u]);
    }
    cout << worst << '\n';
}
""",
    hints=[
        r"""A search from every person is 10^6 searches. A search from every exit is one per
exit, and there can be thousands. Can one search do the work of all of them?""",
        r"""Put every exit in the BFS queue at distance 0 before starting. The first time the
BFS reaches a cell, it comes from the nearest exit.""",
        r"""The answer is the largest distance over non-wall cells; a non-wall cell the BFS never
reaches means −1.""",
    ],
    editorial=r"""
A **multi-source BFS**: start the breadth-first search with *all* exits in the queue at
distance 0. It is the ordinary BFS from an imaginary "street" vertex joined to every exit,
so it computes, for every cell, the shortest distance to the street, which is the distance
to the nearest exit. One BFS, O(nm), however many exits there are. The answer is the
largest distance; any non-wall cell left unreached means −1.

The tempting versions are correct and slow: a BFS from each person is up to 10^6 searches
of 10^6 cells, and a BFS from each exit is one full search per exit (3·10^9 steps with
3000 exits on an open floor). Keep the grid as flat arrays and read rows as strings: the
input is up to a million characters.
""",
)

PRINT_SHOP = Problem(
    id="print_shop",
    title="Print Shop",
    difficulty="hard",
    complexity="O(n log n)",
    statement=r"""
A copy shop receives `n` print jobs at the same moment. It has one printer, which prints
the jobs one after another, without pauses, starting at minute 0. Job `i` takes `t_i`
minutes. The shop promised compensation: the customer of job `i` receives `w_i` coins
for every minute until their job is finished, so if job `i` finishes at minute `C_i`, it
costs `w_i · C_i` coins.

Choose the printing order that minimises the total compensation, and print that total.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has `t_i` and `w_i` (1 ≤ t_i ≤ 10^5, 1 ≤ w_i ≤ 1000).
""",
    output=r"""
Print the minimum total compensation. (It fits in a signed 64-bit integer.)
""",
    samples=[
        Test("2\n3 10\n1 1\n", "34\n",
             note="Printing the shorter job first would cost 1·1 + 4·10 = 41."),
        Test("3\n10 2\n1 1\n4 4\n", "51\n"),
    ],
    tests=[
        Test("1\n100000 1000\n"),
        Test("2\n4 5\n1 2\n"),
        Test("3\n2 4\n1 2\n3 6\n"),
        Test("4\n5 1\n5 1000\n100000 1\n1 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _jobs_range(rng, rng.randint(1, 8), 10, 10), 14),
        Gen("small, many equal ratios", lambda rng: _jobs(rng, rng.randint(2, 8), [1, 2, 3, 4, 6], [1, 2, 3, 4, 6]), 4),
        Gen("small, big values", lambda rng: _jobs_range(rng, 8, 10**5, 1000), 3),
        Gen("max size, random", lambda rng: _jobs_range(rng, 200000, 10**5, 1000), 1, large=True),
        Gen("max size, everything maximal", lambda rng: f"200000\n" + "100000 1000\n" * 200000, 1, large=True),
        Gen("max size, small values", lambda rng: _jobs_range(rng, 200000, 20, 20), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<pair<long long, long long>> job(n);     // (minutes t, coins per minute w)
    for (auto& [t, w] : job) cin >> t >> w;
    // swapping neighbours i, j changes the total by w_i*t_j - w_j*t_i, so i goes first
    // exactly when t_i * w_j < t_j * w_i: compare by cross-multiplying, no division
    sort(job.begin(), job.end(), [](const auto& x, const auto& y) {
        return x.first * y.second < y.first * x.second;
    });
    long long now = 0, total = 0;                  // now reaches 2*10^10, total 2*10^18
    for (auto [t, w] : job) {
        now += t;
        total += w * now;
    }
    cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<long long> t(n), w(n);
    for (int i = 0; i < n; i++) cin >> t[i] >> w[i];
    vector<int> p(n);
    iota(p.begin(), p.end(), 0);
    long long best = LLONG_MAX;
    do {                                           // every order
        long long now = 0, total = 0;
        for (int i : p) {
            now += t[i];
            total += w[i] * now;
        }
        best = min(best, total);
    } while (next_permutation(p.begin(), p.end()));
    cout << best << '\n';
}
""",
    hints=[
        r"""Take two jobs next to each other in some order and swap them. Which finishing times
change, and by how much does the total change?""",
        r"""Swapping neighbours `i, j` changes the total by `w_i·t_j − w_j·t_i`, whatever comes
before them. So `i` should come first exactly when `t_i·w_j < t_j·w_i`.""",
        r"""Sort with that comparison, cross-multiplied (integer `t/w` rounds 4/5 and 1/2 both
to 0). The clock reaches 2·10^10 minutes and the total 2·10^18: `long long` for both.""",
    ],
    editorial=r"""
An exchange argument. Take any order and two neighbouring jobs `i` then `j`, starting at
minute `S`. Before the swap they cost `w_i(S + t_i) + w_j(S + t_i + t_j)`; after it,
`w_j(S + t_j) + w_i(S + t_j + t_i)`. Every other job finishes at the same minute either
way, so the swap changes the total by exactly `w_i·t_j − w_j·t_i`. Hence `i` belongs
before `j` when `t_i/w_i < t_j/w_j`. Any order, the optimal one included, can be
bubble-sorted into `t/w` order by swapping out-of-order neighbours, and no such swap
increases the total, so the sorted order is optimal (**Smith's rule**, the weighted version
of "shortest job first", which is the case `w_i = 1`). Jobs with equal ratios can go in
any order: swapping them changes nothing.

In code, compare `t_i·w_j < t_j·w_i`: exact, and at most 10^8 here. Integer `t/w` is wrong
(4/5 and 1/2 are both 0). Sorting by time alone fails sample 1, by rate alone fails
sample 2. The finishing time reaches 2·10^10 (past `int`) and the total 2·10^18.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo25",
    title="contest day: strategy & a mixed problem set",
    track="algo",
    order=25,
    summary="How ICPC scores a contest, the order to solve in and why, three people at one "
            "keyboard, testing before submitting, and five unlabelled problems to recognise.",
    prereqs=["algo04", "algo07", "algo10", "algo16"],
    tags=["contest strategy", "penalty", "team play", "testing", "recognition", "mixed set"],
    parts=[
        Part("How the scoreboard counts", [
            Say(r"""
The last lesson is about the contest itself. An ICPC contest gives a team of **three**
people **one** computer, five hours, and usually 10 to 13 problems. You submit a program,
the judge replies with a verdict, and a problem is solved at its first accepted
submission. The ranking:

1. more problems solved beats fewer, always;
2. among teams with the same number, less **penalty time** wins;
3. if that ties too, the earlier last accepted submission wins.

The penalty time of a *solved* problem is the contest minute of its accepted submission,
plus **20 minutes for every rejected submission on that problem before it**. Unsolved
problems add nothing, however often they were rejected. At most ICPC contests, and in
this site's virtual contests, a compile error does not count as a rejection; read your
contest's rules to be sure.
"""),
            Numeric(r"""
Your team's contest: A accepted at minute 17 on the first try; C accepted at minute 45
after 2 rejected submissions; D accepted at minute 130 after 1 rejection; E rejected 3
times and never solved. What is the team's penalty time?
""", answer=252, unit="minutes",
                hint="Only solved problems count, each with 20 minutes per rejection before its acceptance.",
                explain=r"""
`17 + (45 + 2·20) + (130 + 20) = 17 + 85 + 150 = 252`. The three rejections on E cost
nothing, because E was never solved.
"""),
            MCQ(r"""
Minute 290 of 300. Your team has 5 solved. Problem F has been rejected twice and you have
a fix you are not sure about. Submit it?
""", [
                Opt("No: another rejection costs 20 more minutes.",
                    why="Rejections only count on problems you end up solving. If this one is "
                        "rejected too, F stays unsolved and costs nothing."),
                Opt("Only if the team's penalty is low right now.",
                    why="Penalty only separates teams with the same number of problems. With "
                        "6 solved you rank above every team with 5, whatever the penalties."),
                Opt("Yes: a rejection changes nothing, and an acceptance means 6 solved, which "
                    "beats every team with 5.", correct=True,
                    why="Right. F would add 290 + 2·20 = 330 penalty minutes if accepted, and it "
                        "is still worth it: the problem count comes first."),
            ], explain=r"""
The same rule says: in the last minutes, submit anything that has a chance. Earlier in the
contest a careless rejection *is* expensive, as the next part shows.
"""),
        ]),
        Part("The order you solve in", [
            Say(r"""
Penalty is a sum of acceptance minutes, so the order of solving matters even when the set
of solved problems is the same. A simple model: one person solves the problems one after
another from minute 0, problem `i` takes `t_i` minutes, and nothing is ever rejected.
"""),
            Numeric(r"""
Three problems need 60, 10 and 30 minutes, solved in that order. What is the total
penalty?
""", answer=230, unit="minutes",
                explain=r"""
They are accepted at minutes 60, 70 and 100: `60 + 70 + 100 = 230`.
"""),
            Numeric(r"""
The same three problems in the best order. Total penalty?
""", answer=150, unit="minutes",
                explain=r"""
10, then 30, then 60: accepted at 10, 40 and 100, total 150. The last acceptance is at
minute 100 in every order (all the work is done by then). What changes is how long the
short problems wait behind the long one.
"""),
            Numeric(r"""
Go back to the order 60, 10, 30 and swap only the first two problems. What is the new
total?
""", answer=180, unit="minutes",
                explain=r"""
10, 60, 30: accepted at 10, 70 and 100, total 180, exactly 50 less than 230. The third
problem did not move (the first two take 70 minutes either way), and 50 = 60 − 10 is the
difference of the two swapped times.
"""),
            Reflect(r"""
Now prove it in general. In some order, problem `i` (taking `t_i`) sits immediately before
problem `j`, and `t_j < t_i`. Swap them. Which acceptance times change, and by how much
does the total change?
""", answer=r"""
Say the pair starts at minute `S`. Before: `i` is accepted at `S + t_i`, `j` at
`S + t_i + t_j`. After: `j` at `S + t_j`, `i` at `S + t_j + t_i`. Every other problem is
accepted at the same minute as before, because the pair takes `t_i + t_j` either way. The
total changes by `(S + t_j) − (S + t_i) = t_j − t_i < 0`. So any order with a longer problem
right before a shorter one can be improved, and the only orders without such a pair are
sorted by time, shortest first. This is an **exchange argument** (algo02 uses the same
shape for scheduling problems).
"""),
            Numeric(r"""
At minute 20 you lose 15 minutes to a silly bug on your first problem. The team goes on to
solve 6 more problems, each accepted 15 minutes later than it would have been. Counting
the first problem too, how many penalty minutes did the bug cost?
""", answer=105, unit="minutes",
                explain=r"""
7 accepted problems, each 15 minutes later: 105 (plus 20 for each rejection, if the bug was
submitted). Minutes lost early are charged again to every later acceptance. That is why
the first hour is about solving the easy problems quickly and cleanly, and why the
shortest problems go first.
"""),
        ]),
        Part("Three people, one computer", [
            Say(r"""
The computer is the bottleneck: 300 minutes of keyboard time shared by three people.
Strong teams keep the keyboard for one job, typing solutions that are already worked out
on paper, and do everything else away from it: reading, designing, and debugging on a
printout (ICPC contests let you print your code). Everyone reads, everyone thinks, one
person types at a time.
"""),
            MCQ(r"""
The contest starts. Which plan wastes the least of the first twenty minutes?
""", [
                Opt("All three read problem A together, then B, and so on, so everyone "
                    "understands every problem.",
                    why="Three times the reading time, and the easiest problem may be the last "
                        "one you reach: problems are rarely ordered by difficulty."),
                Opt("The strongest coder starts typing problem A at once; the other two wait "
                    "until A is accepted before reading anything.",
                    why="A may not be the easiest problem, and two people sit idle for the most "
                        "valuable half hour of the contest."),
                Opt("One person sets up the machine (template, compile command, a test that "
                    "everything works) while the other two split the problem set and read, "
                    "flagging the easy-looking ones.", correct=True,
                    why="Right. By minute 20 the team has read everything once, knows which "
                        "problems look easy, and has a working setup to type the first one."),
            ]),
            MCQ(r"""
Minute 40. The scoreboard shows problem G solved by 48 teams; no other problem has more
than 6. Your team read G at minute 5 and thought it looked hard, and one of you has spent
25 minutes on problem B (solved by 2 teams). What now?
""", [
                Opt("Stay on B: other teams' choices say nothing about your team.",
                    why="48 teams in 40 minutes is the strongest signal a contest gives: G has a "
                        "short solution. If it looked hard, you probably misread it or missed a "
                        "simple idea."),
                Opt("Someone re-reads G now, looking for the simple solution 48 teams found.",
                    correct=True,
                    why="Right. The scoreboard is the best difficulty estimate you have: sort the "
                        "problems by how many teams solved them and make sure you have really "
                        "read the top ones."),
                Opt("Move the whole team onto B: a problem few teams solved gains the most.",
                    why="Every problem is worth the same, one more solved. A problem 2 teams have "
                        "solved is hard, and hard problems cost the most time."),
            ]),
            MCQ(r"""
Your submission for D gets Wrong Answer. A teammate has problem E worked out on paper and
is ready to type. What do you do?
""", [
                Opt("Keep the keyboard and debug D; E can wait.",
                    why="The computer sits idle while you read your own code. E could be typed, "
                        "tested and accepted in that time."),
                Opt("Print D, hand the keyboard over, and debug D on paper: re-check the idea, "
                    "the types, the bounds and the edge cases.", correct=True,
                    why="Right. Debugging is mostly reading, and reading needs no keyboard. Take "
                        "it back when you know exactly what to change."),
                Opt("Resubmit D with small changes until it passes.",
                    why="Each rejection costs 20 minutes if D is solved in the end, and random "
                        "changes rarely fix a bug nobody has found."),
            ]),
            Reflect(r"""
You have been stuck on a problem for 30 minutes without a new idea. How do you decide
whether to keep going or to switch?
""", answer=r"""
The 30 minutes are gone either way; the only question is where the next 30 produce the
most. If problems that many teams have solved are still open for your team, switch, and
hand this one to a teammate for fresh eyes (explaining it out loud often finds the bug on
its own). If you are close (the idea is right and the bug is local), keep going. In the
last hour, put the whole team on the one or two problems closest to done rather than
starting new ones.
"""),
        ]),
        Part("Before you press submit", [
            Say(r"""
A rejection costs 20 minutes and another turn at the keyboard. Before submitting, spend a
few minutes on:

- **all the samples**, compared exactly, not by eye;
- **edge cases**: n = 1, all values equal, the smallest and largest values the limits allow;
- **a maximum test**: generate the largest input with a three-line script, and time it;
- **overflow**: what is the largest number the program *computes*, not reads?
- **the output format**: exact words (`YES` or `Yes`), one answer per line, no debug output;
- **state between test cases**: everything reset.
"""),
            Numeric(r"""
Say submitting right now has a 30% chance of Wrong Answer. A WA costs 20 penalty minutes,
plus about 10 minutes to find and fix the bug (which delays the acceptance by 10 more
minutes). Counting only this problem, what is the expected penalty cost of submitting
right now?
""", answer=9, rel=0.02, unit="minutes",
                explain=r"""
`0.3 · (20 + 10) = 9` minutes.
"""),
            Numeric(r"""
Instead, you test for 5 minutes first (so the acceptance comes 5 minutes later), which
cuts the chance of a WA to 5%. Expected cost now?
""", answer=6.5, rel=0.02, unit="minutes",
                explain=r"""
`5 + 0.05 · 30 = 6.5` minutes, less than 9. And testing wins by more than that: a WA also
takes keyboard time from the rest of the team, and every later problem waits for it.
"""),
            MCQ(r"""
A solution passes the samples. The limits say `n ≤ 2·10^5` and values up to 10^9, and the
program adds values into an `int`. Which single extra test is most likely to catch a bug
the samples missed?
""", [
                Opt("A maximum-size test with every value 10^9.", correct=True,
                    why="Right. It exercises two things samples never do: sums past 2.1·10^9 in "
                        "that `int`, and the running time at the limits."),
                Opt("Another small random test.",
                    why="Small tests catch logic bugs, which the samples probably exercised "
                        "already. They do not overflow and do not time out."),
                Opt("A test with n = 0.",
                    why="The limits say n ≥ 1, so the judge never sends it. Test what the "
                        "limits allow, especially their extremes."),
            ]),
            MCQ(r"""
At the World Finals each team may bring a team reference document (TRD) of up to 25
printed pages, and most regionals have a similar rule. What belongs in it?
""", [
                Opt("Solutions to as many past problems as fit.",
                    why="Problems do not repeat, and you will not find the right one in time. A "
                        "TRD holds building blocks, not answers."),
                Opt("The syntax of loops, `vector` and `sort`.",
                    why="You type those without thinking, and the pages are limited."),
                Opt("Tested code for long, easy-to-get-wrong algorithms: a lazy segment tree, max "
                    "flow, convex hull, modular arithmetic helpers.", correct=True,
                    why="Right. Code you trust because you tested it before the contest, and "
                        "could not type correctly from memory under pressure."),
                Opt("Algorithms copied from the internet the night before.",
                    why="Untested code in a TRD is worse than none: at minute 250 you will trust "
                        "it."),
            ], explain=r"""
This site builds the start of one for you: the notebook collects your accepted code and the
reference solution for every problem you have solved.
"""),
        ]),
        Part("The set: problems A and B", [
            Say(r"""
Now the problem set: five problems, **easiest first** (in a contest they come in no
particular order, and finding the easy ones is part of the job). The statements do not
say which technique they need. That is the skill left to practise: read the limits and
the shape of the question, and name the tool *before* writing code. What the limits
usually allow in one second:

| limit | affordable |
| n ≤ 20 | 2^n, every subset |
| n ≤ 500 | n^3 |
| n ≤ 5000 | n^2 |
| n ≤ 2·10^5 | n log n, n√n |
| a small *sum* of values | a table indexed by the sum |
| an answer up to 10^9 or 10^18 | binary search on it, if checking one value is cheap |
"""),
            MCQ(r"""
**Problem A, Total Ascent.** `n, q ≤ 2·10^5`; the heights of `n` checkpoints along a trail
are fixed, and each question asks how many metres a hiker climbs walking from checkpoint
`s` to checkpoint `t`. What do the constraints suggest?
""", [
                Opt("Walk each question checkpoint by checkpoint.",
                    why="Up to 2·10^5 steps per question and 2·10^5 questions: 4·10^10."),
                Opt("Prefix sums of the climbs between neighbouring checkpoints.", correct=True,
                    why="Right: the climb over a stretch is a sum over the steps inside it, and "
                        "nothing ever changes. O(n + q)."),
                Opt("A segment tree over the climbs.",
                    why="It works, but there are no updates, so there is nothing for a tree to "
                        "do: sixty lines where six will do."),
                Opt("Binary search.",
                    why="Nothing is being searched for; each question has a direct answer."),
            ]),
            Short(r"""
Heights `10 30 20 50 40`. How many metres do you climb walking from checkpoint 5 *back* to
checkpoint 1?
""", accept=["20"], placeholder="metres",
                explain=r"""
40 → 50 climbs 10, 50 → 20 does not, 20 → 30 climbs 10, 30 → 10 does not: 20. Walking
forward from 1 to 5 climbs 50. Read the input section to the end before you code: the
statement allows `s > t`.
"""),
            Try("total_ascent", note="Before submitting: which direction, and which type?"),
            MCQ(r"""
**Problem B, Two Trucks.** `n ≤ 100` crates, each at most 1000 kg; split them between two
trucks so the loads differ as little as possible. What do the constraints suggest?
""", [
                Opt("Try all 2^n ways to split them.",
                    why="Fine for n ≤ 20 (CSES Apple Division). Here it is 2^100."),
                Opt("Heaviest crate first, always onto the lighter truck.",
                    why="Crates `3 3 2 2 2`: it loads 7 and 5, while `3 + 3` against `2 + 2 + 2` "
                        "gives 6 and 6."),
                Opt("Binary search on the difference.",
                    why="To test 'difference ≤ D' you still need to know which loads are "
                        "possible: the same problem, no easier."),
                Opt("A table of which loads truck 1 can carry exactly: the total weight is at "
                    "most 10^5, so the table is small.", correct=True,
                    why="Right: a 0/1 knapsack over sums (algo07), 100 · 10^5 = 10^7 steps. The "
                        "signal is the small *sum*, not the small n."),
            ]),
            Try("two_trucks", note="The second sample is where the obvious idea breaks."),
        ]),
        Part("Problems C and D", [
            MCQ(r"""
**Problem C, Cookie Batch.** `n ≤ 10^5` ingredients; a cookie needs `a_i` grams of each,
the pantry has `b_i`, and you may buy `k ≤ 10^9` extra grams in any mix. Maximise the
number of cookies. What do the constraints suggest?
""", [
                Opt("Bake one cookie at a time, buying whatever is missing.",
                    why="Correct, but the answer can reach 2·10^9 cookies, each costing a pass "
                        "over n ingredients."),
                Opt("A DP over the amount of extra ingredients bought so far.",
                    why="`k` reaches 10^9: the table alone is too big."),
                Opt("Binary search on the number of cookies: checking one number `c` is a single "
                    "O(n) pass, and if `c` cookies are possible, so are fewer.", correct=True,
                    why="Right: a yes/no question, monotone in `c`, over a huge range. About 31 "
                        "checks (algo03)."),
                Opt("Spend all `k` grams on the ingredient that runs out first.",
                    why="Once it is topped up, another one runs out first. For a fixed `c`, the "
                        "right purchase is simply `max(0, c·a_i − b_i)` of each ingredient."),
            ]),
            Numeric(r"""
The answer can be as large as 2·10^9, so `lo`, `hi` and `mid` are `long long`. Inside the
check, how large can `c · a_i` get, with `c = 2·10^9` and `a_i = 10^9`?
""", answer=2e18, rel=0.1,
                explain=r"""
2·10^18. It fits in a `long long` (up to 9.2·10^18), but the sum of five such terms does
not. Return false as soon as the running total passes `k`; otherwise ten ingredients can
wrap the sum around to a small number and the check wrongly says yes.
"""),
            Try("cookie_batch", note="Two of the hidden tests are about overflow, not about the idea."),
            MCQ(r"""
**Problem D, Evacuation.** A floor plan of up to 1000 × 1000 cells with walls and any
number of exits; everyone walks to their nearest exit, one cell per second. Find the time
until the last person is out (or −1 if someone is trapped). What do the constraints
suggest?
""", [
                Opt("A BFS from every person until it meets an exit.",
                    why="Up to 10^6 searches, each over up to 10^6 cells."),
                Opt("A BFS from each exit, keeping the smallest distance for every cell.",
                    why="Correct, but it is one full search per exit: 3·10^9 steps with 3000 "
                        "exits on an open floor."),
                Opt("One BFS that starts with all the exits in the queue at distance 0.",
                    correct=True,
                    why="Right: a **multi-source BFS**, O(nm) however many exits there are."),
                Opt("Dijkstra from every cell.",
                    why="Every step costs 1, so BFS already finds shortest paths; and from every "
                        "cell it is the first option again, slower."),
            ]),
            Reflect(r"""
Why does a BFS started from all the exits at once give every cell the distance to its
*nearest* exit?
""", answer=r"""
Add an imaginary "street" vertex joined to every exit by one edge. A BFS from the street is
an ordinary single-source BFS, so it finds every cell's shortest distance to the street,
and a shortest path to the street leaves through the nearest exit; subtract 1. The first
layer of that BFS is exactly "all the exits", so starting with every exit in the queue at
distance 0 is the same algorithm. The queue still holds distances in non-decreasing order,
which is all BFS needs.
"""),
            Try("evacuation", note="One number to print; up to a million cells to read."),
        ]),
        Part("Problem E, and after the contest", [
            MCQ(r"""
**Problem E, Print Shop.** `n ≤ 2·10^5` jobs on one printer; job `i` takes `t_i` minutes,
and its customer receives `w_i` coins for every minute until that job is finished. Choose
the order that minimises the total paid. What do the constraints suggest?
""", [
                Opt("Shortest job first, as in the penalty argument.",
                    why="That ignores the rates. Jobs (3 min, 10 coins/min) and (1 min, 1 "
                        "coin/min): shortest first pays 1 + 40 = 41, the other order 30 + 4 = 34."),
                Opt("Sort by a key found with an exchange argument: swap two neighbours and see "
                    "which order is cheaper.", correct=True,
                    why="Right: n log n says 'sort by something', and the neighbour swap you did "
                        "for penalties tells you by what, once the rates are in it."),
                Opt("Highest rate first.",
                    why="Jobs (10 min, 2 coins/min) and (1 min, 1 coin/min): highest rate first "
                        "pays 20 + 11 = 31, the short job first 1 + 22 = 23."),
                Opt("A DP over the set of jobs already printed.",
                    why="2^n sets: fine for n ≤ 20, hopeless for 2·10^5."),
            ]),
            MCQ(r"""
Swapping neighbours shows that job `i` should come before job `j` exactly when
`t_i · w_j < t_j · w_i`. Which comparator do you write for `sort`?
""", [
                Opt("`return x.t / x.w < y.t / y.w;` with integer fields.",
                    why="Integer division: jobs (4, 5) and (1, 2) both give 0, so they look "
                        "equal, yet (1, 2) must go first (27 coins against 30)."),
                Opt("`return x.t < y.t || x.w > y.w;`",
                    why="For (1, 1) and (2, 5) it says each must come before the other. That is "
                        "not a strict weak ordering: `sort` may misbehave or crash, and the order "
                        "is wrong anyway."),
                Opt("`return x.t * y.w < y.t * x.w;` in `long long`.", correct=True,
                    why="Right: exact, no division, no rounding. The products are at most 10^8 "
                        "here, but cross-multiplied comparisons are where `long long` habits "
                        "pay off."),
            ], explain=r"""
Dividing in `double` would also work at these limits, but cross-multiplying never needs
you to think about rounding. With `w_i = 1` for every job, the key is just `t_i`: the
shortest-first rule from the penalty argument is the special case.
"""),
            Try("print_shop", note="Check your key on both samples by hand before submitting."),
            Reflect(r"""
The contest is over. What do you do with it the next day?
""", answer=r"""
Upsolve: solve the problems you did not, reading the editorial only after a real attempt,
because the problems just beyond your reach are exactly the ones worth learning. Then look
at where the penalty came from (which rejections, which minutes the keyboard sat idle,
which problem you read too late) and change one habit. Add any code you wished you had to
the reference document, tested. Then do it again: this site's virtual contests draw
problems from every lesson, in random order, with no hints.
"""),
        ]),
    ],
    problems=[ASCENT, TRUCKS, COOKIES, EVAC, PRINT_SHOP],
    cards=[
        Card(r"""How does ICPC rank teams?""",
             r"""By problems solved (more is better, always), then by total penalty time (less is better), then by the earlier last accepted submission."""),
        Card(r"""ICPC penalty time for one problem?""",
             r"""For a solved problem: the contest minute of its acceptance + 20 minutes per rejected submission on it before that. Unsolved problems cost nothing."""),
        Card(r"""Should you submit an uncertain fix in the last minutes?""",
             r"""Yes. A rejection on a problem you never solve costs nothing, and one more solved problem outranks any penalty."""),
        Card(r"""In which order should you solve problems to minimise penalty, and why?""",
             r"""Shortest first. Swapping a longer problem that sits right before a shorter one changes the total by `t_j − t_i < 0` and leaves every other acceptance time unchanged (exchange argument)."""),
        Card(r"""Why is a delay in the first hour so expensive?""",
             r"""Every later acceptance inherits it: 15 minutes lost before 7 accepted problems cost 105 penalty minutes."""),
        Card(r"""How do three people share one computer well?""",
             r"""The keyboard is only for typing solutions worked out on paper. Read, design and debug (on a printout) away from it; hand the keyboard over after a WA."""),
        Card(r"""What does the scoreboard tell you early in a contest?""",
             r"""Which problems are easy: one that many teams solved quickly has a short solution. If your team skipped it, re-read it now."""),
        Card(r"""What to test before submitting?""",
             r"""All samples exactly; edge cases (n = 1, all equal, extreme values); a max-size test for time; overflow of computed values; output format; state reset between test cases."""),
        Card(r"""What goes in a team reference document?""",
             r"""Tested implementations of long, error-prone algorithms (lazy segment tree, flow, geometry, modular helpers), not past solutions or basic syntax. 25 pages at the World Finals."""),
        Card(r"""Distance from every cell to the nearest of many sources?""",
             r"""Multi-source BFS: start with every source in the queue at distance 0. O(V + E), however many sources."""),
        Card(r"""Order jobs to minimise the sum of `w_i · C_i` (weight times finishing time)?""",
             r"""Sort by `t_i / w_i` ascending, compared as `t_i * w_j < t_j * w_i` (Smith's rule, by an exchange argument). With all `w_i = 1`: shortest first."""),
        Card(r"""Two constraint signals: "small sum of values" and "maximise x such that it is feasible"?""",
             r"""A small sum means a DP indexed by the sum (subset sum, knapsack). A monotone yes/no over a huge range means binary search on the answer."""),
    ],
)
