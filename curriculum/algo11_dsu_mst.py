from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _rand_pair(rng, n):
    a = rng.randint(1, n)
    b = rng.randint(1, n - 1)
    return (a, b + 1 if b >= a else b)


def _roads_text(n, roads):
    return f"{n} {len(roads)}\n" + "".join(f"{a} {b}\n" for a, b in roads)


def _construction(rng, n, m):
    return _roads_text(n, [_rand_pair(rng, n) for _ in range(m)])


def _construction_chain(rng, n, m, forward):
    """Roads that build a chain under naive linking, then roads that all touch city 1.

    forward: `i i+1` makes parent[find(a)] = find(b) a chain 1 -> 2 -> ... -> n.
    backward: `i+1 i` does the same for parent[find(b)] = find(a)."""
    if forward:
        roads = [(i, i + 1) for i in range(1, n)]
        roads += [(1, rng.randint(2, n)) for _ in range(m - (n - 1))]
    else:
        roads = [(i + 1, i) for i in range(1, n)]
        roads += [(rng.randint(2, n), 1) for _ in range(m - (n - 1))]
    return _roads_text(n, roads)


def _spanning(rng, n):
    """The edges of a random tree on 1..n."""
    order = rng.sample(range(1, n + 1), n)
    return [(order[i], order[rng.randint(0, i - 1)]) for i in range(1, n)]


def _weighted_text(n, roads):
    return f"{n} {len(roads)}\n" + "".join(f"{a} {b} {c}\n" for a, b, c in roads)


def _repair(rng, n, m, cmin, cmax, connected=True):
    if n == 1:
        return "1 0\n"
    pairs = _spanning(rng, n) if connected else []
    while len(pairs) < m:
        pairs.append(_rand_pair(rng, n))
    rng.shuffle(pairs)
    return _weighted_text(n, [(a, b, rng.randint(cmin, cmax)) for a, b in pairs])


def _repair_small(rng):
    n = rng.randint(1, 6)
    if n == 1:
        return "1 0\n"
    m = rng.randint(max(0, n - 2), 12)
    return _repair(rng, n, m, 1, rng.choice([3, 10, 10**9]), rng.random() < 0.7)


def _repair_split(rng, n, m):
    """Two halves, each connected, no road between them."""
    h = n // 2
    left = _spanning(rng, h)
    right = [(a + h, b + h) for a, b in _spanning(rng, n - h)]
    pairs = left + right
    while len(pairs) < m:
        if rng.random() < 0.5:
            a, b = _rand_pair(rng, h)
        else:
            a, b = _rand_pair(rng, n - h)
            a, b = a + h, b + h
        pairs.append((a, b))
    rng.shuffle(pairs)
    return _weighted_text(n, [(a, b, rng.randint(1, 10**9)) for a, b in pairs])


def _repair_path_chords(rng, n, m):
    """A cheap path 1-2-...-n, then expensive roads from city 1 to random cities."""
    roads = [(i, i + 1, rng.randint(1, 1000)) for i in range(1, n)]
    while len(roads) < m:
        x = rng.randint(3, n)
        a, b = (1, x) if rng.random() < 0.5 else (x, 1)
        roads.append((a, b, rng.randint(10**9 - 10**6, 10**9)))
    rng.shuffle(roads)
    return _weighted_text(n, roads)


def _points_text(pts):
    return f"{len(pts)}\n" + "".join(f"{x} {y}\n" for x, y in pts)


def _points_random(rng, n, lim):
    return _points_text([(rng.randint(-lim, lim), rng.randint(-lim, lim)) for _ in range(n)])


def _points_small(rng):
    n = rng.randint(1, 7)
    lim = rng.choice([5, 20, 10**9])
    return _points_random(rng, n, lim)


def _points_clusters(rng, n, k):
    lim = 10**9
    centres = [(rng.randint(-lim, lim), rng.randint(-lim, lim)) for _ in range(k)]
    pts = []
    for _ in range(n):
        cx, cy = rng.choice(centres)
        pts.append((min(lim, max(-lim, cx + rng.randint(-1000, 1000))),
                    min(lim, max(-lim, cy + rng.randint(-1000, 1000)))))
    return _points_text(pts)


def _points_line(rng, n):
    return _points_text([(rng.randint(-10**9, 10**9), 0) for _ in range(n)])


def _closures(rng, n, m, q, connected):
    pairs = _spanning(rng, n) if connected else []
    while len(pairs) < m:
        pairs.append(_rand_pair(rng, n))
    pairs = pairs[:m]
    rng.shuffle(pairs)
    order = rng.sample(range(1, m + 1), q)
    return (f"{n} {m} {q}\n" + "".join(f"{a} {b}\n" for a, b in pairs)
            + " ".join(map(str, order)) + "\n")


def _closures_small(rng):
    n = rng.randint(2, 7)
    m = rng.randint(1, 9)
    return _closures(rng, n, m, rng.randint(1, m), rng.random() < 0.5)


DSU_CODE = r"""
struct DSU {
    vector<int> parent, sz;
    DSU(int n) : parent(n + 1), sz(n + 1, 1) { iota(parent.begin(), parent.end(), 0); }
    int find(int v) {                          // path compression: point straight at the root
        return parent[v] == v ? v : parent[v] = find(parent[v]);
    }
    bool unite(int a, int b) {                 // false if a and b were already together
        a = find(a), b = find(b);
        if (a == b) return false;
        if (sz[a] < sz[b]) swap(a, b);         // union by size: small tree under big root
        parent[b] = a;
        sz[a] += sz[b];
        return true;
    }
};
"""


# --------------------------------------------------------------------- problems
ROAD_CONSTRUCTION = Problem(
    id="road_construction",
    title="Road Construction",
    difficulty="easy",
    source="CSES 1676 - Road Construction",
    complexity="O((n + m) α(n))",
    statement=r"""
Syrjälä has `n` cities and no roads. Then `m` roads are built, one at a time; each joins
two cities in both directions.

After each new road, print the number of components (maximal groups of cities that can
all reach each other) and the number of cities in the largest component.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 10^5, 1 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): the next
road. A road may join two cities that are already connected, even directly.
""",
    output=r"""
Print `m` lines. Line `i` has two integers: the number of components and the size of the
largest component after the first `i` roads are built.
""",
    samples=[
        Test("5 3\n1 2\n1 3\n4 5\n", "4 2\n3 3\n2 3\n"),
    ],
    tests=[
        Test("2 1\n2 1\n"),
        Test("3 4\n1 2\n2 1\n1 2\n2 3\n",
             note="Roads between cities that are already connected change nothing."),
        Test("6 5\n1 2\n3 4\n5 6\n2 4\n6 3\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _construction(rng, rng.randint(2, 8), rng.randint(1, 10)), 16),
        Gen("medium random", lambda rng: _construction(rng, 400, 800), 3),
        Gen("max random", lambda rng: _construction(rng, 100000, 200000), 1, large=True),
        Gen("max chain, then roads to city 1",
            lambda rng: _construction_chain(rng, 100000, 200000, True), 1, large=True),
        Gen("max chain the other way, then roads to city 1",
            lambda rng: _construction_chain(rng, 100000, 200000, False), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;
""" + DSU_CODE + r"""
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    DSU dsu(n);
    int comps = n, largest = 1;
    while (m--) {
        int a, b;
        cin >> a >> b;
        if (dsu.unite(a, b)) {                 // two components became one
            comps--;
            largest = max(largest, dsu.sz[dsu.find(a)]);   // sizes only grow
        }
        cout << comps << ' ' << largest << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// After every road, recount the components from scratch with BFS.
int main() {
    int n, m;
    cin >> n >> m;
    vector<vector<int>> adj(n + 1);
    vector<int> seen(n + 1);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
        fill(seen.begin(), seen.end(), 0);
        int comps = 0, largest = 0;
        for (int s = 1; s <= n; s++) {
            if (seen[s]) continue;
            comps++;
            int size = 0;
            queue<int> q;
            q.push(s);
            seen[s] = 1;
            while (!q.empty()) {
                int u = q.front();
                q.pop();
                size++;
                for (int v : adj[u])
                    if (!seen[v]) { seen[v] = 1; q.push(v); }
            }
            largest = max(largest, size);
        }
        cout << comps << ' ' << largest << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// DSU without union by size and without path compression.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<int> parent(n + 1), sz(n + 1, 1);
    iota(parent.begin(), parent.end(), 0);
    auto find = [&](int v) {
        while (parent[v] != v) v = parent[v];
        return v;
    };
    int comps = n, largest = 1;
    while (m--) {
        int a, b;
        cin >> a >> b;
        a = find(a), b = find(b);
        if (a != b) {
            parent[a] = b;
            sz[b] += sz[a];
            comps--;
            largest = max(largest, sz[b]);
        }
        cout << comps << ' ' << largest << '\n';
    }
}
""",
    hints=[
        r"""A new road either changes nothing (its cities were already connected) or merges two
components. What structure answers "same component?" and "merge" quickly?""",
        r"""A DSU. The count starts at `n` and drops by one for each successful `unite`. The largest
component can only be the one that just grew: `largest = max(largest, size of the new root)`.""",
        r"""Plain parent pointers can degenerate into a chain of 10^5 cities; one hidden test does
exactly that. Hang the smaller tree under the larger root, and compress paths in `find`.""",
    ],
    editorial=r"""
Keep the cities in a disjoint set union. Each road is one `unite(a, b)`: if it returns
`true`, two components merged, so the count drops by one and the new root's size is a
candidate for the largest. Components never shrink, so a single running maximum is
enough; no need to scan all components.

Union by size keeps every tree at most log2 n ≈ 17 levels deep, because a city only gets
deeper when its tree is merged into one at least as large, which at least doubles its
tree's size. Path compression flattens the trees further; with both, each operation is
O(α(n)), effectively constant.

The trap is the DSU without either heuristic: roads `1 2`, `2 3`, ..., `n−1 n` build a
chain of length `n − 1` under `parent[find(a)] = find(b)`, and every later `find(1)` walks
it. Two hidden tests build such chains (one for each linking direction) and then add
10^5 roads at city 1: about 10^10 steps.
""",
)

ROAD_REPARATION = Problem(
    id="road_reparation",
    title="Road Reparation",
    difficulty="medium",
    source="CSES 1675 - Road Reparation",
    complexity="O(m log m)",
    statement=r"""
There are `n` cities and `m` roads between them, all in poor condition. Repairing a road
has a cost. Your task is to repair a set of roads so that every city can reach every
other city along repaired roads, and the total cost is as small as possible.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2·10^5).

Each of the next `m` lines has three integers `a`, `b` and `c` (1 ≤ a, b ≤ n, a ≠ b,
1 ≤ c ≤ 10^9): a two-way road between `a` and `b` with repair cost `c`. There can be
several roads between the same two cities.
""",
    output=r"""
Print the minimum total cost, or `IMPOSSIBLE` if the cities cannot all be connected.
""",
    samples=[
        Test("5 6\n1 2 3\n2 3 5\n2 4 2\n3 4 8\n5 1 7\n5 4 4\n", "14\n"),
        Test("4 3\n1 2 1\n2 4 1\n1 4 1\n", "IMPOSSIBLE\n",
             note="Cities 1 and 4 are connected, but city 3 is not connected to anything."),
    ],
    tests=[
        Test("1 0\n"),
        Test("2 3\n1 2 5\n2 1 3\n1 2 1000000000\n"),
        Test("4 3\n1 2 1000000000\n2 3 1000000000\n3 4 1000000000\n",
             note="The total, 3·10^9, does not fit in an `int`."),
        Test("3 1\n1 2 7\n"),
        Test("4 6\n1 2 4\n1 3 4\n1 4 4\n2 3 4\n2 4 4\n3 4 4\n"),
    ],
    gens=[
        Gen("small random", _repair_small, 18),
        Gen("medium random", lambda rng: _repair(rng, 300, 900, 1, 10**9), 2, large=True),
        Gen("max random", lambda rng: _repair(rng, 100000, 200000, 1, 10**9), 1, large=True),
        Gen("max, every cost 10^9", lambda rng: _repair(rng, 100000, 200000, 10**9, 10**9), 1,
            large=True),
        Gen("max, two halves", lambda rng: _repair_split(rng, 100000, 200000), 1, large=True),
        Gen("max, cheap path and expensive chords",
            lambda rng: _repair_path_chords(rng, 100000, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;
""" + DSU_CODE + r"""
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<array<int, 3>> roads(m);            // {cost, a, b}: sorting compares cost first
    for (auto& r : roads) cin >> r[1] >> r[2] >> r[0];
    sort(roads.begin(), roads.end());

    DSU dsu(n);
    long long total = 0;                       // up to (n - 1) * 10^9: long long
    int taken = 0;
    for (auto& [c, a, b] : roads)
        if (dsu.unite(a, b)) {                 // cheapest road joining two components: safe
            total += c;
            taken++;
        }
    if (taken != n - 1) cout << "IMPOSSIBLE\n";
    else cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Try every subset of roads; keep the cheapest one that connects all cities.
int main() {
    int n, m;
    cin >> n >> m;
    vector<int> A(m), B(m);
    vector<long long> C(m);
    for (int i = 0; i < m; i++) cin >> A[i] >> B[i] >> C[i];
    long long best = -1;
    for (int mask = 0; mask < (1 << m); mask++) {
        vector<int> comp(n + 1);
        iota(comp.begin(), comp.end(), 0);
        long long cost = 0;
        for (int i = 0; i < m; i++)
            if (mask >> i & 1) {
                cost += C[i];
                int x = comp[A[i]], y = comp[B[i]];
                if (x != y)
                    for (int v = 1; v <= n; v++)
                        if (comp[v] == y) comp[v] = x;
            }
        bool connected = true;
        for (int v = 1; v <= n; v++)
            if (comp[v] != comp[1]) connected = false;
        if (connected && (best == -1 || cost < best)) best = cost;
    }
    if (best == -1) cout << "IMPOSSIBLE\n";
    else cout << best << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Kruskal, but "already connected?" is answered by a BFS over the roads taken so far.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<array<int, 3>> roads(m);
    for (auto& r : roads) cin >> r[1] >> r[2] >> r[0];
    sort(roads.begin(), roads.end());
    vector<vector<int>> forest(n + 1);
    vector<int> mark(n + 1, 0);
    int stamp = 0, taken = 0;
    long long total = 0;
    for (auto& [c, a, b] : roads) {
        stamp++;
        bool connected = false;
        queue<int> q;
        q.push(a);
        mark[a] = stamp;
        while (!q.empty() && !connected) {
            int u = q.front();
            q.pop();
            for (int v : forest[u]) {
                if (v == b) { connected = true; break; }
                if (mark[v] != stamp) { mark[v] = stamp; q.push(v); }
            }
        }
        if (connected) continue;
        forest[a].push_back(b);
        forest[b].push_back(a);
        total += c;
        taken++;
    }
    if (taken != n - 1) cout << "IMPOSSIBLE\n";
    else cout << total << '\n';
}
""",
    hints=[
        r"""The repaired roads form a tree (a cycle always has a road you could skip). Which roads
should a greedy look at first, and which should it refuse?""",
        r"""Kruskal: sort the roads by cost, and take a road exactly when its two cities are not yet
connected by the roads already taken. A DSU answers that in near O(1).""",
        r"""Print `IMPOSSIBLE` when fewer than `n − 1` roads were taken. The total can reach
(n − 1)·10^9 ≈ 10^14: `long long`.""",
    ],
    editorial=r"""
Kruskal's algorithm: sort the roads by cost and scan them, taking a road whenever it
joins two different components of the roads taken so far (one DSU `unite`). O(m log m)
for the sort, near O(1) per road after that.

Why it is optimal: the **cut property**. For any split of the cities into two sides, some
minimum spanning tree contains a cheapest road crossing the split (take an optimal tree
without it, add it, and the cycle this closes crosses the split at another road that is
no cheaper; swap them). When Kruskal takes `u–v`, no cheaper road leaves `u`'s current
component (each cheaper road was either taken, and now lies inside a component, or
refused because it lay inside one), so `u–v` is a cheapest road across that cut.

Traps: the total needs `long long` (a hidden test with three roads of cost 10^9 in a
row already overflows `int`), and `IMPOSSIBLE` is decided by counting `n − 1` taken roads, not by
checking that cities 1 and `n` are connected. With `n = 1` the answer is 0.
""",
)

WIRING = Problem(
    id="wiring",
    title="Wiring the Campus",
    difficulty="medium",
    complexity="O(n^2)",
    statement=r"""
A campus has `n` buildings at integer points `(x_i, y_i)`. A cable can join any two
buildings, and it costs their Manhattan distance, `|x_i − x_j| + |y_i − y_j|` (cables run
along the streets of a grid).

Choose cables so that every building is connected to every other, directly or through
other buildings, with the smallest total cost.
""",
    input=r"""
The first line has an integer `n` (1 ≤ n ≤ 10^4).

Each of the next `n` lines has two integers `x_i` and `y_i` (−10^9 ≤ x_i, y_i ≤ 10^9).
Several buildings may share a point.
""",
    output=r"""
Print the minimum total cost.
""",
    samples=[
        Test("4\n0 0\n2 1\n5 0\n2 4\n", "10\n"),
        Test("2\n-1000000000 -1000000000\n1000000000 1000000000\n", "4000000000\n",
             note="One cable already costs more than an `int` holds."),
    ],
    tests=[
        Test("1\n5 5\n"),
        Test("3\n7 7\n7 7\n7 7\n"),
        Test("3\n-1000000000 0\n1000000000 0\n0 1000000000\n"),
        Test("2\n1000000000 -1000000000\n-1000000000 1000000000\n"),
    ],
    gens=[
        Gen("small random", _points_small, 18),
        Gen("medium random", lambda rng: _points_random(rng, 300, 10**9), 3),
        Gen("max random", lambda rng: _points_random(rng, 10000, 10**9), 1, large=True),
        Gen("max clusters", lambda rng: _points_clusters(rng, 10000, 12), 1, large=True),
        Gen("max on a line", lambda rng: _points_line(rng, 10000), 1, large=True),
        Gen("max small grid", lambda rng: _points_random(rng, 10000, 50), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> x(n), y(n);
    for (int i = 0; i < n; i++) cin >> x[i] >> y[i];

    // Prim on the implicit complete graph: best[v] = cheapest cable from v to the tree.
    vector<long long> best(n, LLONG_MAX);
    vector<char> inTree(n, 0);
    best[0] = 0;
    long long total = 0;                       // up to about 10^13: long long
    int u = 0;                                 // the next building to add
    for (int step = 0; step < n; step++) {
        inTree[u] = 1;
        total += best[u];
        int next = -1;
        for (int v = 0; v < n; v++) {          // one O(n) pass: update best, find the minimum
            if (inTree[v]) continue;
            long long d = llabs(x[u] - x[v]) + llabs(y[u] - y[v]);   // up to 4*10^9
            if (d < best[v]) best[v] = d;
            if (next == -1 || best[v] < best[next]) next = v;
        }
        u = next;
    }
    cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Kruskal on every pair of buildings (fine for small n).
int main() {
    int n;
    cin >> n;
    vector<long long> x(n), y(n);
    for (int i = 0; i < n; i++) cin >> x[i] >> y[i];
    vector<tuple<long long, int, int>> e;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            e.push_back({llabs(x[i] - x[j]) + llabs(y[i] - y[j]), i, j});
    sort(e.begin(), e.end());
    vector<int> comp(n);
    iota(comp.begin(), comp.end(), 0);
    long long total = 0;
    for (auto [w, a, b] : e) {
        int ca = comp[a], cb = comp[b];
        if (ca == cb) continue;
        for (int v = 0; v < n; v++)
            if (comp[v] == cb) comp[v] = ca;
        total += w;
    }
    cout << total << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Kruskal on all n(n-1)/2 pairs: correct, but 5*10^7 edges to build and sort at n = 10^4.
struct Edge { long long w; int a, b; };
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> x(n), y(n);
    for (int i = 0; i < n; i++) cin >> x[i] >> y[i];
    vector<Edge> e;
    e.reserve((size_t)n * (n - 1) / 2);
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            e.push_back({llabs(x[i] - x[j]) + llabs(y[i] - y[j]), i, j});
    sort(e.begin(), e.end(), [](const Edge& p, const Edge& q) { return p.w < q.w; });
    vector<int> parent(n), sz(n, 1);
    iota(parent.begin(), parent.end(), 0);
    function<int(int)> find = [&](int v) { return parent[v] == v ? v : parent[v] = find(parent[v]); };
    long long total = 0;
    for (auto& [w, a, b] : e) {
        int ra = find(a), rb = find(b);
        if (ra == rb) continue;
        if (sz[ra] < sz[rb]) swap(ra, rb);
        parent[rb] = ra;
        sz[ra] += sz[rb];
        total += w;
    }
    cout << total << '\n';
}
""",
    hints=[
        r"""Every pair of buildings is a possible cable: about 5·10^7 edges at `n = 10^4`. Building
and sorting them all is too slow and too big. Which MST algorithm never needs the edge
list?""",
        r"""Prim with an array: `best[v]` is the cheapest cable from `v` to the tree so far. Each step
adds the outside building with the smallest `best`, then lowers `best[v]` using the
distance to the new building. `n` steps of O(n).""",
        r"""A single distance can be 4·10^9, past `int`. Compute distances and the total in
`long long`.""",
    ],
    editorial=r"""
The graph is complete: every pair of buildings is an edge, and the edges are never
written down. Kruskal would have to create all n(n−1)/2 ≈ 5·10^7 of them (about 800 MB
with a `long long` cost) and sort them; measured here, that takes about 4 seconds.

Prim needs only one number per building: `best[v]`, the cheapest cable from `v` to any
building already in the tree. Each of the `n` steps adds the outside building with the
smallest `best` (safe by the cut property: it is the cheapest edge between the tree and
the rest) and then updates `best` for every outside building with its distance to the
newcomer. Both jobs fit in one O(n) loop, so the total is O(n^2) = 10^8 simple
operations and O(n) memory. On a dense graph that is optimal, since the graph itself has
n^2 edges.

Coordinates range over ±10^9, so one distance can be 4·10^9: compute it in `long long`. (A
heap-based Prim would push O(n^2) edges through the heap, O(n^2 log n); the plain array
is both simpler and faster here.)
""",
)

ROAD_CLOSURES = Problem(
    id="road_closures",
    title="Road Closures",
    difficulty="medium",
    complexity="O((n + m) α(n))",
    statement=r"""
A country has `n` cities and `m` two-way roads, numbered 1 to `m`. A storm is coming, and
the authorities will close `q` of the roads, one at a time, in a known order. Closed roads
stay closed.

After each closure, print the number of components: maximal groups of cities that can
still reach each other along open roads.
""",
    input=r"""
The first line has three integers `n`, `m` and `q` (2 ≤ n ≤ 10^5, 1 ≤ m ≤ 2·10^5,
1 ≤ q ≤ m).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): road number
`i` on the `i`-th of these lines. Two roads may join the same pair of cities.

The last line has `q` distinct integers between 1 and `m`: the roads in the order they are
closed.
""",
    output=r"""
Print `q` integers: the number of components right after each closure, in order.
""",
    samples=[
        Test("4 4 3\n1 2\n2 3\n3 4\n4 1\n2 4 1\n", "1 2 3\n"),
    ],
    tests=[
        Test("2 1 1\n1 2\n1\n"),
        Test("3 3 3\n1 2\n1 2\n2 3\n1 3 2\n",
             note="Roads 1 and 2 both join cities 1 and 2: closing one of them splits nothing."),
        Test("5 2 1\n1 2\n4 5\n2\n"),
    ],
    gens=[
        Gen("small random", _closures_small, 18),
        Gen("medium random", lambda rng: _closures(rng, 300, 500, 500, True), 2),
        Gen("medium sparse", lambda rng: _closures(rng, 300, 280, 150, False), 2),
        Gen("max random, every road closes",
            lambda rng: _closures(rng, 100000, 200000, 200000, True), 1, large=True),
        Gen("max tree, every road closes",
            lambda rng: _closures(rng, 100000, 99999, 99999, True), 1, large=True),
        Gen("max random, half the roads close",
            lambda rng: _closures(rng, 100000, 200000, 100000, True), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;
""" + DSU_CODE + r"""
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, q;
    cin >> n >> m >> q;
    vector<int> A(m + 1), B(m + 1);
    for (int i = 1; i <= m; i++) cin >> A[i] >> B[i];
    vector<int> order(q);
    vector<char> closes(m + 1, 0);
    for (auto& r : order) {
        cin >> r;
        closes[r] = 1;
    }

    // The final state: only the roads that never close.
    DSU dsu(n);
    int comps = n;
    for (int i = 1; i <= m; i++)
        if (!closes[i] && dsu.unite(A[i], B[i])) comps--;

    // Run time backwards: re-opening roads only merges components.
    vector<int> ans(q);
    for (int i = q - 1; i >= 0; i--) {
        ans[i] = comps;                        // the count right after closure i
        if (dsu.unite(A[order[i]], B[order[i]])) comps--;
    }
    for (int i = 0; i < q; i++) cout << ans[i] << " \n"[i + 1 == q];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// After every closure, count the components of the open roads from scratch.
int main() {
    int n, m, q;
    cin >> n >> m >> q;
    vector<int> A(m + 1), B(m + 1);
    for (int i = 1; i <= m; i++) cin >> A[i] >> B[i];
    vector<char> open(m + 1, 1);
    vector<int> seen(n + 1);
    for (int k = 0; k < q; k++) {
        int r;
        cin >> r;
        open[r] = 0;
        vector<vector<int>> adj(n + 1);
        for (int i = 1; i <= m; i++)
            if (open[i]) { adj[A[i]].push_back(B[i]); adj[B[i]].push_back(A[i]); }
        fill(seen.begin(), seen.end(), 0);
        int comps = 0;
        for (int s = 1; s <= n; s++) {
            if (seen[s]) continue;
            comps++;
            queue<int> bq;
            bq.push(s);
            seen[s] = 1;
            while (!bq.empty()) {
                int u = bq.front();
                bq.pop();
                for (int v : adj[u])
                    if (!seen[v]) { seen[v] = 1; bq.push(v); }
            }
        }
        cout << comps << ' ';
    }
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, q;
    cin >> n >> m >> q;
    vector<int> A(m + 1), B(m + 1);
    for (int i = 1; i <= m; i++) cin >> A[i] >> B[i];
    vector<char> open(m + 1, 1);
    vector<int> seen(n + 1);
    for (int k = 0; k < q; k++) {
        int r;
        cin >> r;
        open[r] = 0;
        vector<vector<int>> adj(n + 1);
        for (int i = 1; i <= m; i++)
            if (open[i]) { adj[A[i]].push_back(B[i]); adj[B[i]].push_back(A[i]); }
        fill(seen.begin(), seen.end(), 0);
        int comps = 0;
        for (int s = 1; s <= n; s++) {
            if (seen[s]) continue;
            comps++;
            queue<int> bq;
            bq.push(s);
            seen[s] = 1;
            while (!bq.empty()) {
                int u = bq.front();
                bq.pop();
                for (int v : adj[u])
                    if (!seen[v]) { seen[v] = 1; bq.push(v); }
            }
        }
        cout << comps << ' ';
    }
    cout << '\n';
}
""",
    hints=[
        r"""A DSU can merge but never split. Is there a way to see this story as a sequence of
merges?""",
        r"""Run time backwards: start from the network after the last closure and re-open the roads
in reverse order. Each re-opening is a `unite`.""",
        r"""The answer after closure `i` is the count *before* re-opening road `order[i]` in the
backwards pass. Store the answers in an array and print it forwards.""",
    ],
    editorial=r"""
Deleting edges is hard for a DSU: it forgets which road caused which merge, and one
closed road may or may not split a component. But all closures are known in advance, so
reverse time. After the last closure, the open roads are exactly the roads that never
close: unite them. Then walk the closures from last to first. Just before re-opening
road `order[i]`, the network is the one right after closure `i`, so record the current
count as `ans[i]`, then `unite` the road's cities (decrementing the count if they were
apart). Print `ans` in the original order. O((n + m) α(n)).

This only works *offline*, when every closure is known before the first answer is
needed, the same distinction as for difference arrays in algo01. Recounting components
with a BFS after every closure is correct but costs O(q·(n + m)), about 6·10^10 steps on
the largest tests.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo11",
    title="disjoint set union & minimum spanning trees",
    track="algo",
    order=11,
    summary="Merging components in near-constant time with a DSU (and why the two tricks make "
            "it fast), Kruskal and the cut property, Prim for dense graphs, and running "
            "deletions backwards.",
    prereqs=["algo09", "algo02"],
    tags=["dsu", "union-find", "union by size", "path compression", "mst", "kruskal",
          "prim", "cut property", "exchange argument", "offline", "reverse time"],
    parts=[
        Part("Components that only grow", [
            Say(r"""
algo09 counted components once. Now the graph changes, and the question is asked after
every change.

**Road Construction** (CSES 1676): there are `n` cities and no roads. `m` roads are built
one at a time, each joining two cities in both directions. After each new road, print the
number of components and the size of the largest one. Limits: `n ≤ 10^5`, `m ≤ 2·10^5`,
one second.

The obvious program rebuilds the answer from scratch: add the road to the adjacency lists,
then count the components with a BFS from every unvisited city, exactly as in algo09.
"""),
            Numeric(r"""
One recount costs about `n + m` steps, and there is one recount per road. With
`n = 10^5` and `m = 2·10^5`, roughly how many steps is that in total?
""", answer=6e10, rel=0.5, unit="steps",
                explain=r"""
`2·10^5 · 3·10^5 = 6·10^10`: a minute of work for a one-second limit.
"""),
            Reflect(r"""
What does the recount redo for nothing? Think about what one new road `a–b` can possibly
change.
""", answer=r"""
A new road changes at most two components. If `a` and `b` were already connected, it
changes nothing; otherwise it merges their two components into one, and every other
component stays exactly as it was. The recount rediscovers all the untouched components
every time. What we need is a structure that answers "are `a` and `b` already in the same
component?" and "merge these two components" quickly. The answers follow: each merge
lowers the count by one, and the merged size is the sum of the two sizes.
"""),
            Say(r"""
First attempt: give every city a label `comp[v]`, the name of its component, starting
with `comp[v] = v`. "Same component?" is `comp[a] == comp[b]`, O(1). A merge must rename
every city of one of the two components.
"""),
            Numeric(r"""
Suppose you always rename the component of `a`. The roads arrive as `1 2`, `1 3`, `1 4`,
..., `1 n`. With `n = 10^5`, how many renamings happen in total?
""", answer=5e9, rel=0.5, unit="renamings",
                hint="How big is city 1's component when road `1 k` arrives?",
                explain=r"""
When road `1 k` arrives, city 1's component has `k − 1` cities, and all of them are
renamed: `1 + 2 + ... + (n − 1) ≈ n^2/2 = 5·10^9`.
"""),
            MCQ(r"""
Which rule makes renaming cheap on every input?
""", [
                Opt("Always rename the component of `b` instead.",
                    why="The input just writes the roads as `2 1`, `3 1`, ... instead. Any rule "
                        "that ignores the sizes can be made to rename the big side every time."),
                Opt("Give both components a fresh name.",
                    why="That renames the big side as well, and the `1 2`, `1 3`, ... input is "
                        "back to n^2/2."),
                Opt("Rename the smaller of the two components.", correct=True,
                    why="Right. A city is renamed only when its component is the smaller one, so "
                        "afterwards it lives in a component at least twice as big. Sizes cannot "
                        "double past `n`, so each city is renamed at most log2 n ≈ 17 times: "
                        "O(n log n) in total."),
            ], explain=r"""
Remember this doubling argument, "small to large": it proves bounds all over contest
programming. Here there is an even cheaper structure. Instead of renaming cities, let them
*point* at each other.
"""),
        ]),
        Part("Disjoint set union", [
            Say(r"""
A **disjoint set union** (DSU, or union-find) stores one number per city, `parent[v]`.
Each component is a tree of parent pointers; its root, the city with `parent[r] = r`,
names the component. `find(v)` follows the pointers up to the root. A merge renames
nothing: it makes one root point to the other.

```cpp
vector<int> parent(n + 1);
iota(parent.begin(), parent.end(), 0);   // parent[v] = v: n components of one city

int find(int v) {
    while (parent[v] != v) v = parent[v];
    return v;
}
void unite(int a, int b) {
    a = find(a), b = find(b);
    if (a != b) parent[a] = b;           // a's root now hangs under b's root
}
```

A merge is O(1) after the two `find`s. The cost has moved into `find`, which walks as far
as the tree is deep.
"""),
            Short(r"""
With `n = 5`, apply `unite(1, 2)`, `unite(2, 3)`, `unite(3, 4)`, `unite(4, 5)` using the
code above. How many steps (parent pointers followed) does `find(1)` then take to reach
the root?
""", accept=["4", "four"], placeholder="a number",
                hint="Track `parent[]` after each call: which root ends up under which?",
                explain=r"""
`unite(1, 2)` sets `parent[1] = 2`. `unite(2, 3)`: 2 is a root, so `parent[2] = 3`. Then
`parent[3] = 4` and `parent[4] = 5`. The tree is a chain 1 → 2 → 3 → 4 → 5, and `find(1)`
takes 4 steps. Each call hung a whole tree under a single fresh city.
"""),
            Numeric(r"""
Build that chain with `n = 10^5` cities, then add another 10^5 roads, each from city 1 to
some other city. Every one of them calls `find(1)`, which walks the whole chain. Roughly
how many steps in total?
""", answer=1e10, rel=0.5, unit="steps",
                explain=r"""
`10^5 · 10^5 = 10^10`, several seconds at best. Two hidden tests of Road Construction do
exactly this, one for each way of writing the link (`parent[a] = b` or `parent[b] = a`).
"""),
            MCQ(r"""
The fix: keep `sz[root]`, and always hang the root of the *smaller* tree under the root of
the larger one (**union by size**). A city `x` gets one level deeper only when its root is
hung under another root. What happens to the size of `x`'s tree at that moment?
""", [
                Opt("It at least doubles, because the tree it joins is at least as large.",
                    correct=True,
                    why="Right: the same doubling as renaming the smaller side, now bounding the "
                        "depth instead of the renamings."),
                Opt("It stays the same; only the depth changed.",
                    why="`x`'s tree was just merged into another, so its size is now the sum of "
                        "both."),
                Opt("It grows by exactly one city.",
                    why="It grows by the whole other tree, which under union by size is at least "
                        "as big as `x`'s own."),
            ]),
            Numeric(r"""
So with `n = 10^5` cities, how deep can any tree get under union by size? (A whole number
is fine.)
""", answer=16.6, tol=1.0, unit="levels",
                explain=r"""
A city at depth `d` has had its tree double `d` times, so its tree has at least `2^d`
cities, and `2^d ≤ 10^5` gives `d ≤ log2(10^5) ≈ 16.6`: at most 16 levels, so a `find`
follows at most 16 pointers. From 10^10 steps down to a few million.
"""),
            Short(r"""
Union by size, where on a tie `b`'s root goes under `a`'s root. On cities 1..6, apply
`unite(1, 2)`, `unite(3, 4)`, `unite(5, 6)`, `unite(1, 3)`, `unite(6, 4)`. Write
`parent[1..6]`, separated by spaces.
""", accept=["1 1 1 3 1 5", "1,1,1,3,1,5", "[1, 1, 1, 3, 1, 5]", "1, 1, 1, 3, 1, 5"],
                placeholder="six numbers",
                hint="`unite(6, 4)` joins the tree rooted at 5 (size 2) and the tree rooted at 1 "
                     "(size 4).",
                explain=r"""
The first three calls hang 2 under 1, 4 under 3 and 6 under 5. `unite(1, 3)` is a tie
(2 and 2), so 3 goes under 1 and `sz[1] = 4`. `unite(6, 4)` finds roots 5 (size 2) and
1 (size 4): the smaller root, 5, goes under 1. Result `1 1 1 3 1 5`: cities 4 and 6 are
at depth 2, the rest at depth 0 or 1.
"""),
            Say(r"""
The second trick is **path compression**: once `find(v)` knows the root, point every city
it passed straight at the root, so the next `find` from any of them takes one step. Either
trick alone gives O(log n) per operation; together they give O(α(n)) amortised, where α
is the inverse Ackermann function, at most 4 for any `n` that fits in memory.
""" + r"""
```cpp""" + DSU_CODE + r"""```

The recursive `find` is safe: union by size keeps every tree at most 17 levels deep.
"""),
            MCQ(r"""
Road Construction also asks for the size of the largest component after every road. How
do you keep it up to date?
""", [
                Opt("After each road, scan all roots for the largest `sz`.",
                    why="That is O(n) per road, 2·10^10 in total: the recount problem again."),
                Opt("Keep a `multiset` of all component sizes; erase the two old sizes and insert "
                    "their sum on each merge.",
                    why="It works, and you would need it if components could shrink. They never "
                        "do here, so it is extra code and an extra log factor for nothing."),
                Opt("Keep one variable `largest`; after a successful `unite`, set it to "
                    "`max(largest, sz[root])`.", correct=True,
                    why="Right. Components only grow, so the only candidate for a new maximum is "
                        "the component that just grew."),
            ], explain=r"""
The count works the same way: start at `n` and subtract one for every `unite` that returns
`true`. A road inside one component changes neither number, and the input may repeat
roads, so the return value matters.
"""),
            Try("road_construction", note="A DSU with both tricks. The hidden tests include the "
                "chain that ruins plain parent pointers."),
        ]),
        Part("Minimum spanning trees", [
            Say(r"""
**Road Reparation** (CSES 1675): `n ≤ 10^5` cities and `m ≤ 2·10^5` broken two-way roads,
each with a repair cost up to 10^9. Repair a set of roads so that every city can reach
every other, as cheaply as possible, and print the total; or `IMPOSSIBLE`.
"""),
            MCQ(r"""
What shape does a cheapest set of repaired roads have? (Every cost is positive.)
""", [
                Opt("A path through all the cities.",
                    why="Sometimes, but a star (one hub joined to everyone) can be much cheaper. "
                        "A path is one special kind of tree."),
                Opt("A tree: `n − 1` roads and no cycle.", correct=True,
                    why="Yes. If the chosen roads contained a cycle, dropping any road of that "
                        "cycle keeps everything connected and saves money. Connected without a "
                        "cycle is a tree, a **spanning tree** of the graph."),
                Opt("It depends on the costs; the cheapest network may contain a cycle.",
                    why="Any road on a cycle can be dropped without disconnecting anything, and "
                        "every cost is positive, so a network with a cycle is never the "
                        "cheapest."),
            ]),
            Numeric(r"""
The brute force tries every spanning tree. By Cayley's formula, the complete graph on `n`
vertices has `n^(n−2)` spanning trees. How many is that for `n = 20`?
""", answer=20**18, rel=0.5, unit="trees",
                explain=r"""
`20^18 ≈ 2.6·10^23`. Even `n = 10` gives 10^8. The minimum has to be built, not searched
for.
"""),
            Reflect(r"""
Propose a greedy rule. In what order would you consider the roads, and when would you
refuse one?
""", answer=r"""
Consider the roads from cheapest to most expensive, and take each road unless its two
cities are already connected by the roads taken so far (such a road would only close a
cycle). Stop after `n − 1` roads. This is **Kruskal's algorithm**, and "already connected
by the roads taken so far?" is exactly the question a DSU answers: one `unite` per road,
with the verdict in its return value.
"""),
            Short(r"""
Five cities, roads written as `a b cost`: `1 2 3`, `2 3 1`, `1 3 2`, `3 4 5`, `4 5 4`,
`3 5 6`, `2 5 7`. Run Kruskal. What is the total cost?
""", accept=["12"], placeholder="a number",
                hint="Sort by cost. Which is the first road you refuse, and why?",
                explain=r"""
Take 2–3 (1) and 1–3 (2). Refuse 1–2 (3): 1 and 2 are already joined through 3. Take
4–5 (4) and 3–4 (5); now four roads join all five cities, so 3–5 (6) and 2–5 (7) are
refused. Total `1 + 2 + 4 + 5 = 12`.
"""),
            Say(r"""
Why is the greedy right? The key fact is about **cuts**. Split the cities into two
non-empty groups: a set `S` and the rest. A road *crosses* the cut if it has one end on
each side. Every spanning tree uses at least one crossing road, or the two sides would not
be connected.
"""),
            MCQ(r"""
Let `e` be a cheapest road crossing some cut, and suppose a cheapest network `T*` does not
use `e`. Add `e` to `T*`. Which step finishes the argument?
""", [
                Opt("`T* + e` has `n` roads, so it is not a tree, which contradicts `T*` being "
                    "optimal.",
                    why="One road too many does not show that `T*` was too expensive. You need to "
                        "remove something and compare costs."),
                Opt("Because `e` is the cheapest road in the whole graph, it must be in every "
                    "optimal network.",
                    why="`e` is only the cheapest among the roads crossing *this* cut; there may "
                        "be much cheaper roads elsewhere."),
                Opt("`e` closes a cycle in `T*`. The cycle crosses the cut at `e`, so it must cross "
                    "back at another road `f`, and `cost(f) ≥ cost(e)`. Removing `f` leaves a "
                    "spanning tree that uses `e` and costs no more.", correct=True,
                    why="Yes: an exchange argument, as in algo02. Some cheapest network contains "
                        "`e`. This is the **cut property**."),
            ]),
            MCQ(r"""
When Kruskal takes a road `u–v`, which cut is it a cheapest crossing road of?
""", [
                Opt("The cut between `u`'s current component (of the roads taken so far) and "
                    "everything else.", correct=True,
                    why="Right. Every cheaper road was looked at earlier: it was either taken, so "
                        "it now lies inside a component, or refused because both its ends were "
                        "in one component. Either way no cheaper road crosses this cut, so the "
                        "cut property says `u–v` is safe."),
                Opt("The cut between the single city `u` and all other cities.",
                    why="Cheaper roads may leave `u` towards cities already in `u`'s component. "
                        "The cut that works is the whole component."),
                Opt("None: Kruskal is correct for a different reason.",
                    why="The cut property is exactly the reason: each road Kruskal takes is a "
                        "cheapest road across one particular cut."),
            ], explain=r"""
Kruskal in code is a sort and a DSU:

```cpp
sort(roads.begin(), roads.end());          // {cost, a, b}: by cost first
long long total = 0;
int taken = 0;
for (auto& [c, a, b] : roads)
    if (dsu.unite(a, b)) total += c, taken++;
```

O(m log m), and the sort dominates.
"""),
            MCQ(r"""
Which test tells you to print `IMPOSSIBLE`?
""", [
                Opt("`find(1) != find(n)` after all the roads.",
                    why="Cities 1 and `n` may be connected while some other city is cut off. The "
                        "second sample is built that way."),
                Opt("The total cost is 0.",
                    why="It is 0 only when `n = 1`, which is possible: one city needs no roads."),
                Opt("Fewer than `n − 1` roads were taken.", correct=True,
                    why="Right: `n − 1` successful unites happen exactly when everything ended up "
                        "in one component."),
            ], explain=r"""
And the total: up to `(n − 1)·10^9 ≈ 10^14`, so `long long`. A hidden test with just three
roads of cost 10^9 already overflows `int` (3·10^9 > 2^31 − 1 ≈ 2.1·10^9).
"""),
            Try("road_reparation", note="Kruskal with the DSU from Road Construction."),
        ]),
        Part("Prim, and dense graphs", [
            Say(r"""
Kruskal looks at all roads in cost order. **Prim's algorithm** grows a single tree
instead: start from any city, and repeatedly add the cheapest road that joins a city in
the tree to a city outside it.
"""),
            MCQ(r"""
Why is Prim's choice always safe?
""", [
                Opt("It is not always safe; Prim is a fast heuristic.",
                    why="Prim is exact. Every step is justified by the same lemma as Kruskal's."),
                Opt("The cheapest road leaving the tree is a cheapest road across the cut "
                    "(tree, rest), so the cut property applies.", correct=True,
                    why="Right: the same lemma, applied to a different cut at every step."),
                Opt("Because the tree is connected at every step.",
                    why="It is, by construction; the question is why the *cheapest* road leaving "
                        "it belongs to some optimal tree."),
            ]),
            Say(r"""
Prim shines on complete graphs given implicitly. **Wiring the Campus**: `n ≤ 10^4`
buildings at integer points `(x_i, y_i)`, and a cable between any two costs their
Manhattan distance `|x_i − x_j| + |y_i − y_j|`. Connect every building as cheaply as
possible.
"""),
            Numeric(r"""
Kruskal needs the list of all possible cables. How many pairs of buildings are there for
`n = 10^4`?
""", answer=49995000, rel=0.1, unit="pairs",
                explain=r"""
`n(n−1)/2 ≈ 5·10^7`. At 16 bytes per edge (a `long long` cost and two indices) that is
800 MB before sorting even starts; measured here, Kruskal on all pairs takes about 4
seconds. Prim does not need the list at all.
"""),
            MCQ(r"""
How should Prim run on this complete graph?
""", [
                Opt("Keep `best[v]`, the cheapest cable from `v` to the tree. Each step scans for "
                    "the outside building with the smallest `best`, adds it, and lowers `best[v]` "
                    "for every outside building using its distance to the newcomer.", correct=True,
                    why="Right: `n` steps of O(n), 10^8 simple operations and O(n) memory. On a "
                        "dense graph O(n^2) is optimal, since the graph itself has about n^2 edges."),
                Opt("With a priority queue, pushing every cable out of each new tree building.",
                    why="That pushes all 5·10^7 cables through a heap: O(n^2 log n), slower than "
                        "the plain array and just as hungry for memory."),
                Opt("Run Kruskal only on each building's 10 nearest neighbours.",
                    why="Far-apart clusters need a cable that is nobody's near neighbour: with 20 "
                        "buildings per cluster, every building's 10 nearest are in its own "
                        "cluster, and the candidate graph is disconnected."),
            ], explain=r"""
The rule of thumb: sparse graphs (m ≈ n) want Kruskal or heap-based Prim, O(m log m);
dense graphs (m ≈ n^2, or edges defined by a formula) want array-based Prim, O(n^2).
"""),
            MCQ(r"""
Coordinates range over −10^9..10^9. With `int x[], y[]`, what can go wrong in
`abs(x[i] - x[j]) + abs(y[i] - y[j])`?
""", [
                Opt("Nothing: each difference is at most 2·10^9, which fits in an `int`.",
                    why="Each difference fits (2·10^9 < 2^31 − 1 ≈ 2.147·10^9, barely), but their "
                        "sum can reach 4·10^9."),
                Opt("`abs` does not accept negative numbers.",
                    why="`abs(-5) == 5` for `int`; the problem is the size of the sum."),
                Opt("The sum can reach 4·10^9 and overflow `int`; compute distances and the total "
                    "in `long long`.", correct=True,
                    why="Right. The second sample is exactly one such cable."),
            ]),
            Try("wiring", note="Array-based Prim, O(n^2), everything in `long long`."),
        ]),
        Part("Running time backwards", [
            Say(r"""
A DSU only merges. Here is a problem where the graph only loses edges.

**Road Closures**: `n ≤ 10^5` cities, `m ≤ 2·10^5` roads, and `q ≤ m` of the roads are
closed one at a time, in a given order. After each closure, print the number of
components. Recounting with BFS after every closure is the Road Construction brute force
again: about 6·10^10 steps.
"""),
            MCQ(r"""
Can a DSU undo a merge when a road closes?
""", [
                Opt("Yes: point the root that was linked last back at itself.",
                    why="The pointers do not record which road caused which link, path "
                        "compression has rewritten them, and the component may stay connected "
                        "through other roads anyway."),
                Opt("No: a DSU forgets *why* cities are together, and whether one closed road "
                    "splits a component is exactly the hard question.", correct=True,
                    why="Right. Deciding it needs to know about every other road of the "
                        "component, which is what the DSU threw away to be fast."),
                Opt("Yes, if each root also stores the list of roads inside its component.",
                    why="Then a closure still requires checking whether the rest of the component "
                        "is connected without that road: a BFS, back to the slow recount."),
            ]),
            Reflect(r"""
You know all the closures in advance. Read them from the last to the first. What does the
story become, and how do you get the answers?
""", answer=r"""
Roads re-opening one by one, starting from the network where every listed road is
closed. Re-opening only merges components, which is what a DSU does. So: unite the roads
that never close; then go through the closures backwards, and before re-opening road
`order[i]`, record the current count as the answer for closure `i` (the network right
after closure `i` is exactly the current one); then unite that road. Print the recorded
answers in the original order. O((n + m) α(n)).
"""),
            Short(r"""
Cities 1..4. Road 1 is `1 2`, road 2 is `2 3`, road 3 is `3 4`, road 4 is `4 1`. The roads
2, 4, 1 close in that order. Write the three answers.
""", accept=["1 2 3", "1,2,3", "1, 2, 3", "[1, 2, 3]"], placeholder="three numbers",
                hint="Backwards: start with only road 3 open.",
                explain=r"""
Backwards: only road 3 is open, 3 components; record 3 for the last closure, re-open road
1 (2 components); record 2, re-open road 4 (1 component); record 1 for the first closure.
Forwards that reads `1 2 3`, which you can check directly: closing road 2 leaves the path
2–1–4–3, closing road 4 splits it into {1, 2} and {3, 4}, closing road 1 isolates 1 and 2.
"""),
            MCQ(r"""
Would the trick still work if each answer had to be printed before the next closure is
revealed (an interactive judge)?
""", [
                Opt("Yes: reverse the closures as they arrive.",
                    why="You cannot reverse a sequence you have not seen: the *first* answer is "
                        "computed last, from the final state."),
                Opt("Yes, if you rebuild the DSU after every closure.",
                    why="That works and costs O(n + m) per closure: the slow recount again."),
                Opt("No: it needs every closure in advance. Answering online needs a much heavier "
                    "structure (fully dynamic connectivity).", correct=True,
                    why="Right. The reversal is an *offline* technique."),
            ], explain=r"""
The same distinction as algo01's difference arrays: offline, you may reorder the work.
"Deletions become insertions when time runs backwards" is a standard contest trick.
"""),
            Try("road_closures", note="Unite the roads that never close, then re-open backwards "
                "and print the answers forwards."),
        ]),
        Part("Variations on the theme", [
            MCQ(r"""
You want the spanning tree with the *largest* total (say, maximising total bandwidth).
What changes?
""", [
                Opt("Nothing works greedily: the exchange argument breaks for maxima.",
                    why="It works in mirror image: a most expensive road across a cut belongs to "
                        "some maximum spanning tree, by the same swap."),
                Opt("Run Kruskal with the roads sorted from most to least expensive.", correct=True,
                    why="Right (or negate every cost). The proof is the same with the inequalities "
                        "reversed."),
                Opt("Take the minimum spanning tree: it is also the maximum one.",
                    why="Only when all costs are equal. In general the two are very different."),
            ]),
            MCQ(r"""
A truck drives from city `a` to city `b`. What matters is the heaviest road on its route
(say, a bridge with a weight limit), and you want the route whose heaviest road is as
light as possible. How do you find that value?
""", [
                Opt("Dijkstra, minimising the sum of the road costs.",
                    why="A sum is a different objective: the route with the smallest sum may use "
                        "one very heavy road."),
                Opt("Run Kruskal and stop as soon as `a` and `b` are connected; the answer is the "
                    "cost of the road just taken.", correct=True,
                    why="Right. The roads taken so far are all at most that cost, and before this "
                        "road no set of cheaper roads connected `a` and `b`, so every route uses a "
                        "road at least that heavy. Equivalently, the path in the MST is a best "
                        "route."),
                Opt("BFS for the route with the fewest roads.",
                    why="Fewest roads says nothing about how heavy they are."),
            ]),
            MCQ(r"""
Every city has a population, and after each merge you must report the total population
of the merged component. Where does that number live?
""", [
                Opt("In every city, updated for all cities of the component at each merge.",
                    why="Updating every city of a component is the renaming cost from the first "
                        "part again."),
                Opt("Recompute it after each merge by summing over the component.",
                    why="O(component size) per merge: the same renaming cost."),
                Opt("In a `sum[root]` array: when root `b` goes under root `a`, do "
                    "`sum[a] += sum[b]`.", correct=True,
                    why="Right. Any summary that combines when two sets merge (size, sum, minimum, "
                        "maximum, a count) lives at the root and is combined in `unite`, exactly "
                        "like `sz`."),
            ], explain=r"""
DSUs with data at the root appear constantly: component sums, the minimum label in a
component, whether a component contains a cycle (`unite` returning `false` means the road
closed one).
"""),
        ]),
    ],
    problems=[ROAD_CONSTRUCTION, ROAD_REPARATION, WIRING, ROAD_CLOSURES],
    cards=[
        Card(r"""What does a disjoint set union (DSU) support, and how fast?""",
             r"""`find(v)` (which set is `v` in?) and `unite(a, b)` (merge two sets), each O(α(n)) amortised, effectively constant, with union by size and path compression."""),
        Card(r"""Write a DSU `find` with path compression.""",
             r"""`int find(int v) { return parent[v] == v ? v : parent[v] = find(parent[v]); }`"""),
        Card(r"""Why does union by size keep DSU trees at most log2 n deep?""",
             r"""A city gets deeper only when its tree is hung under a tree at least as large, so its tree's size at least doubles each time; sizes stay ≤ n."""),
        Card(r"""What goes wrong with a DSU that uses neither heuristic?""",
             r"""Unions like `1 2`, `2 3`, ... can build a chain of depth n − 1, and every later `find` walks it: O(n) per operation."""),
        Card(r"""Counting components and the largest component while roads are added?""",
             r"""Start with `comps = n`; on each `unite` that returns true, `comps--` and `largest = max(largest, sz[root])` (components never shrink)."""),
        Card(r"""Kruskal's algorithm?""",
             r"""Sort edges by weight; take an edge exactly when `unite(a, b)` succeeds. O(m log m). Fewer than n − 1 edges taken means the graph is disconnected."""),
        Card(r"""State the cut property.""",
             r"""For any cut (S, V∖S), some minimum spanning tree contains a cheapest edge crossing it. Proof: exchange it with the other crossing edge on the cycle it closes."""),
        Card(r"""Prim's algorithm, and when to prefer it?""",
             r"""Grow one tree, always adding the cheapest edge leaving it. Array version O(n^2): best for dense or implicit complete graphs; heap version O(m log n) for sparse graphs."""),
        Card(r"""How do you handle edge deletions with a DSU when all deletions are known in advance?""",
             r"""Reverse time: start from the final graph, re-add the deleted edges in reverse order, record each answer before re-adding, and print the answers forwards."""),
        Card(r"""Minimise the heaviest edge on a route from a to b?""",
             r"""Run Kruskal until `a` and `b` are connected; the last edge taken is the answer (the MST path between them is a minimax path)."""),
        Card(r"""Maximum spanning tree?""",
             r"""Kruskal with edges sorted in decreasing order (or negate the weights); the cut property holds in mirror image."""),
    ],
)
