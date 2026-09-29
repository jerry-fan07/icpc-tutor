from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _ri(rng, lo, hi):
    """rng.randint(lo, hi), several times faster for the big generators."""
    return lo + int(rng.random() * (hi - lo + 1))


def _wtext(n, edges):
    return f"{n} {len(edges)}\n" + "".join(f"{a} {b} {c}\n" for a, b, c in edges)


def _out_tree(rng, n, span, lo, hi):
    """Directed tree away from 1 on shuffled labels: every city reachable from 1.
    A small `span` makes it deep (each city hangs off one of the last few)."""
    order = [1] + rng.sample(range(2, n + 1), n - 1)
    return [(order[_ri(rng, max(0, i - span), i - 1)], order[i], _ri(rng, lo, hi))
            for i in range(1, n)]


def _flights(rng, n, m, lo, hi, span):
    edges = _out_tree(rng, n, span, lo, hi)
    while len(edges) < m:
        a, b = _ri(rng, 1, n), _ri(rng, 1, n)
        if a != b:
            edges.append((a, b, _ri(rng, lo, hi)))
    rng.shuffle(edges)
    return _wtext(n, edges)


def _flights_small(rng):
    n = rng.randint(2, 8)
    return _flights(rng, n, rng.randint(n - 1, 16), 1, 20, rng.randint(1, n))


def _reversed_path(rng, n, m, price):
    """1 -> 2 -> ... -> n listed back to front (one Bellman-Ford round per edge), plus
    backward flights that never help."""
    edges = [(i, i + 1, price) for i in range(n - 1, 0, -1)]
    while len(edges) < m:
        a, b = _ri(rng, 1, n), _ri(rng, 1, n)
        if a < b:
            edges.append((b, a, _ri(rng, 1, 10**9)))
    return _wtext(n, edges)


def _hub(rng, k, leaves):
    """1 -> a_i (price i), a_i -> H (price C - 2i): H improves k times, and every stale
    copy of H in the heap rescans H's `leaves` outgoing flights."""
    C = 10**9
    hub = k + 2
    edges = [(1, 1 + i, i) for i in range(1, k + 1)]
    edges += [(1 + i, hub, C - 2 * i) for i in range(1, k + 1)]
    edges += [(hub, hub + j, 1) for j in range(1, leaves + 1)]
    rng.shuffle(edges)
    return _wtext(hub + leaves, edges)


def _neg_random(rng, n, m, lo, hi):
    """Directed, self-loops and parallel edges allowed."""
    edges = [(rng.randint(1, n), rng.randint(1, n), rng.randint(lo, hi)) for _ in range(m)]
    return _wtext(n, edges)


def _potential(rng, n, m, extra_hi, bad=0, skip_one_out=False):
    """w(a,b) = p[b] - p[a] + extra with extra >= 0: every cycle weighs the sum of its
    extras, so there is no negative cycle.  `bad` > 0 threads one Hamiltonian cycle
    through all cities whose extras sum to -1: exactly the kind of cycle that needs all
    n rounds to show up.  `skip_one_out` gives city 1 no outgoing edges."""
    p = [0] + [rng.randint(0, 5 * 10**8) for _ in range(n)]
    edges = []
    if bad:
        order = rng.sample(range(1, n + 1), n)
        if skip_one_out:
            order.remove(1)
        k = len(order)
        for i in range(k):
            a, b = order[i], order[(i + 1) % k]
            edges.append((a, b, p[b] - p[a] - (1 if i == 0 else 0)))
    while len(edges) < m:
        a, b = rng.randint(1, n), rng.randint(1, n)
        if skip_one_out and a == 1:
            continue
        edges.append((a, b, p[b] - p[a] + rng.randint(0, extra_hi)))
    rng.shuffle(edges)
    return _wtext(n, edges)


def _neg_small(rng):
    n = rng.randint(1, 7)
    m = rng.randint(1, 12)
    if rng.random() < 0.5:
        return _neg_random(rng, n, m, -10, 10)
    return _potential(rng, n, m, 3)


def _chain_dag(rng, n, m):
    """No cycle at all; the chain 1 -> 2 -> ... -> n (price -1000 each) is listed back to
    front, and heavy forward shortcuts never help."""
    edges = [(i, i + 1, -1000) for i in range(n - 1, 0, -1)]
    while len(edges) < m:
        a, b = sorted(rng.sample(range(1, n + 1), 2))
        edges.append((a, b, 10**9))
    return _wtext(n, edges)


def _roads(rng, n, m, q, lo, hi, parts=1):
    """Two-way roads (parallel roads allowed) and q queries. `parts` > 1 splits the
    cities into groups with no road between them."""
    group = [0] + [rng.randint(0, parts - 1) for _ in range(n)]
    members = [[v for v in range(1, n + 1) if group[v] == g] for g in range(parts)]
    members = [g for g in members if len(g) >= 2] or [list(range(1, n + 1))]
    edges = []
    while len(edges) < m and n >= 2:
        g = members[_ri(rng, 0, len(members) - 1)]
        a, b = g[_ri(rng, 0, len(g) - 1)], g[_ri(rng, 0, len(g) - 1)]
        if a != b:
            edges.append((a, b, _ri(rng, lo, hi)))
    lines = [f"{n} {len(edges)} {q}"] + [f"{a} {b} {c}" for a, b, c in edges]
    lines += [f"{_ri(rng, 1, n)} {_ri(rng, 1, n)}" for _ in range(q)]
    return "\n".join(lines) + "\n"


def _roads_path(rng, n, q):
    """A single long road chain: distances up to (n-1)*10^9."""
    order = rng.sample(range(1, n + 1), n)
    edges = [(order[i], order[i + 1], 10**9) for i in range(n - 1)]
    lines = [f"{n} {len(edges)} {q}"] + [f"{a} {b} {c}" for a, b, c in edges]
    lines += [f"{order[0]} {order[-1]}" if i % 2 == 0 else f"{rng.randint(1, n)} {rng.randint(1, n)}"
              for i in range(q)]
    return "\n".join(lines) + "\n"


def _roads_small(rng):
    n = rng.randint(1, 8)
    return _roads(rng, n, rng.randint(0, 14), rng.randint(1, 12), 1, 20, rng.choice([1, 1, 2]))


# --------------------------------------------------------------------- checkers
def _check_cycle(inp, expected, got):
    it = inp.split()
    n, m = int(it[0]), int(it[1])
    best = {}
    for i in range(m):
        a, b, c = int(it[2 + 3 * i]), int(it[3 + 3 * i]), int(it[4 + 3 * i])
        if (a, b) not in best or c < best[(a, b)]:
            best[(a, b)] = c
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    if e[0] == "NO":
        if g == ["NO"]:
            return True, ""
        return False, "there is no negative cycle; expected NO"
    if g[0] != "YES":
        return False, "there is a negative cycle; the first line should be YES"
    cyc = [int(x) for x in g[1:]]
    if len(cyc) < 2:
        return False, "list the cycle's vertices, repeating the first one at the end"
    if len(cyc) > n + 1:
        return False, f"a cycle has at most {n} distinct vertices"
    if cyc[0] != cyc[-1]:
        return False, "the cycle must end at the vertex where it starts"
    if len(set(cyc[:-1])) != len(cyc) - 1:
        return False, "a vertex appears twice before the cycle closes"
    total = 0
    for a, b in zip(cyc, cyc[1:]):
        if (a, b) not in best:
            return False, f"there is no edge {a} -> {b}"
        total += best[(a, b)]
    if total >= 0:
        return False, f"the cheapest edges along your cycle add up to {total}, which is not negative"
    return True, ""


# --------------------------------------------------------------------- problems
SHORTEST_ROUTES_1 = Problem(
    id="shortest_routes_1",
    title="Shortest Routes I",
    difficulty="easy",
    source="CSES 1671 - Shortest Routes I",
    complexity="O((n + m) log n)",
    statement=r"""
There are `n` cities and `m` one-way flights between them, each with a price. Every
city can be reached from city 1.

For every city, find the price of the cheapest route from city 1 to it.
""",
    input=r"""
The first line has two integers `n` and `m` (2 ≤ n ≤ 10^5, 1 ≤ m ≤ 2·10^5).

Each of the next `m` lines has three integers `a`, `b`, `c` (1 ≤ a, b ≤ n, a ≠ b,
1 ≤ c ≤ 10^9): a flight from `a` to `b` costing `c`. There may be several flights between
the same two cities.
""",
    output=r"""
Print `n` integers on one line: the cheapest price from city 1 to cities 1, 2, ..., n.
""",
    samples=[
        Test("3 4\n1 2 6\n1 3 2\n3 2 3\n1 3 4\n", "0 5 2\n"),
        Test("3 3\n1 2 1000000000\n2 3 1000000000\n1 3 1\n", "0 1000000000 1\n"),
    ],
    tests=[
        Test("2 1\n1 2 1000000000\n"),
        Test("3 3\n1 3 10\n1 2 1\n2 3 1\n",
             note="Fewer flights is not cheaper: BFS would say 10 for city 3."),
        Test("4 5\n1 2 5\n1 2 3\n2 3 1\n3 4 1\n2 4 7\n"),
        Test("5 4\n4 5 1000000000\n3 4 1000000000\n2 3 1000000000\n1 2 1000000000\n"),
    ],
    gens=[
        Gen("small random", _flights_small, 16),
        Gen("medium random", lambda rng: _flights(rng, 1000, 3000, 1, 10**9, 4), 3),
        Gen("max long path listed backwards", lambda rng: _reversed_path(rng, 100000, 200000, 10**9),
            1, large=True),
        Gen("max random deep", lambda rng: _flights(rng, 100000, 200000, 1, 10**9, 3), 1, large=True),
        Gen("max random shallow", lambda rng: _flights(rng, 100000, 200000, 1, 10**9, 100000), 1,
            large=True),
        Gen("max hub with many improvements", lambda rng: _hub(rng, 49999, 49999), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, int>>> adj(n + 1);          // (to, price)
    for (int i = 0; i < m; i++) {
        int a, b, c;
        cin >> a >> b >> c;
        adj[a].push_back({b, c});                       // one-way
    }

    const long long INF = LLONG_MAX;                    // never added to: only popped
    vector<long long> dist(n + 1, INF);                 // distances reach ~10^14
    priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> pq;
    dist[1] = 0;
    pq.push({0, 1});
    while (!pq.empty()) {
        auto [d, u] = pq.top();
        pq.pop();
        if (d > dist[u]) continue;                      // stale copy: u was settled cheaper
        for (auto [v, w] : adj[u])                      // u is final: relax its flights once
            if (d + w < dist[v]) {
                dist[v] = d + w;
                pq.push({dist[v], v});
            }
    }
    for (int v = 1; v <= n; v++) cout << dist[v] << " \n"[v == n];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Bellman-Ford: relax every flight until a whole round changes nothing.
int main() {
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    vector<long long> c(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i] >> c[i];
    const long long INF = LLONG_MAX;
    vector<long long> dist(n + 1, INF);
    dist[1] = 0;
    bool changed = true;
    while (changed) {
        changed = false;
        for (int i = 0; i < m; i++)
            if (dist[a[i]] != INF && dist[a[i]] + c[i] < dist[b[i]]) {
                dist[b[i]] = dist[a[i]] + c[i];
                changed = true;
            }
    }
    for (int v = 1; v <= n; v++) cout << dist[v] << ' ';
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Bellman-Ford with early exit: fine when few rounds are needed, n - 1 rounds at worst.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    vector<long long> c(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i] >> c[i];
    const long long INF = LLONG_MAX;
    vector<long long> dist(n + 1, INF);
    dist[1] = 0;
    for (int round = 1; round < n; round++) {
        bool changed = false;
        for (int i = 0; i < m; i++)
            if (dist[a[i]] != INF && dist[a[i]] + c[i] < dist[b[i]]) {
                dist[b[i]] = dist[a[i]] + c[i];
                changed = true;
            }
        if (!changed) break;
    }
    for (int v = 1; v <= n; v++) cout << dist[v] << " \n"[v == n];
}
""",
    hints=[
        r"""Prices are positive, so the unfinished city with the smallest tentative distance cannot
be improved any more. Settle it, relax its flights, repeat.""",
        r"""Use `priority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<>>` so the
smallest distance comes out first. Push a new entry on every improvement, and skip an
entry whose distance is larger than the city's current `dist` when you pop it.""",
        r"""Distances reach (n − 1)·10^9 ≈ 10^14: `long long`.""",
    ],
    editorial=r"""
Dijkstra's algorithm. Keep `dist` (tentative, ∞ except `dist[1] = 0`) and a min-heap of
`(dist, city)`. Pop the smallest; if it is a stale copy (`d > dist[u]`), skip it;
otherwise `u`'s distance is final, so relax each of its flights once, pushing a new copy
of every city that improves.

Why the popped city is final: any route to it must leave the set of settled cities at some
first unsettled city `x`, and already costs at least `dist[x]`, which is at least the
popped distance; the rest of the route adds non-negative prices. This is where "prices
are positive" is used.

Each flight is relaxed once and pushes at most once, so there are at most `m + 1` heap
entries: O((n + m) log n). The details that cost verdicts: the default `priority_queue` is a
max-heap (use `greater<>`); skipping stale entries matters (the hub test makes a city
improve 5·10^4 times, and without the skip each copy rescans its 5·10^4 flights);
distances need `long long`. Bellman-Ford is also correct here but needs n − 1 rounds of
2·10^5 relaxations on the path that is listed backwards: 2·10^10.
""",
)

CYCLE_FINDING = Problem(
    id="cycle_finding",
    title="Cycle Finding",
    difficulty="medium",
    source="CSES 1197 - Cycle Finding",
    complexity="O(n·m)",
    statement=r"""
You are given a directed graph with `n` vertices and `m` weighted edges; weights may be
negative. Decide whether the graph contains a negative cycle (a cycle whose total weight
is below zero), and if so, print one.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 2500, 1 ≤ m ≤ 5000).

Each of the next `m` lines has three integers `a`, `b`, `c` (1 ≤ a, b ≤ n,
−10^9 ≤ c ≤ 10^9): an edge from `a` to `b` of weight `c`. An edge may start and end at
the same vertex, and there may be several edges between the same two vertices.
""",
    output=r"""
If there is a negative cycle, print `YES`, then the vertices of one negative cycle in
order, starting and ending with the same vertex (no other vertex repeated). Any negative
cycle is accepted.

Otherwise print `NO`.
""",
    samples=[
        Test("4 5\n1 2 1\n2 4 1\n3 1 1\n4 1 -3\n4 3 -2\n", "YES\n1 2 4 1\n"),
        Test("3 3\n1 2 5\n2 3 -2\n3 1 -2\n", "NO\n"),
    ],
    tests=[
        Test("1 1\n1 1 -1\n"),
        Test("1 1\n1 1 0\n"),
        Test("2 3\n1 2 5\n2 1 -3\n1 2 1\n"),
        Test("4 3\n1 2 1\n3 4 -2\n4 3 1\n",
             note="The negative cycle 3 → 4 → 3 cannot be reached from vertex 1."),
        Test("3 3\n1 2 -600000000\n2 3 -500000000\n3 1 1000000000\n"),
        Test("3 3\n1 2 -500000000\n2 3 -500000000\n3 1 1000000000\n",
             note="This cycle weighs exactly 0, which is not negative."),
    ],
    gens=[
        Gen("small random", _neg_small, 20),
        # the brute is exponential: anything past n = 7 is marked large so it skips the brute
        Gen("medium random", lambda rng: _neg_random(rng, 200, 400, -10**9, 10**9), 2, large=True),
        Gen("medium, no negative cycle", lambda rng: _potential(rng, 200, 400, 10**8), 2, large=True),
        Gen("max, no negative cycle", lambda rng: _potential(rng, 2500, 5000, 10**8), 1, large=True),
        Gen("max, one cycle through everything", lambda rng: _potential(rng, 2500, 5000, 10**8, bad=1),
            1, large=True),
        Gen("max, cycle unreachable from 1", lambda rng: _potential(rng, 2500, 5000, 10**8, bad=1,
                                                                     skip_one_out=True), 1, large=True),
        Gen("max chain listed backwards", lambda rng: _chain_dag(rng, 2500, 5000), 1, large=True),
    ],
    checker=_check_cycle,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    vector<long long> c(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i] >> c[i];

    // Every dist starts at 0: as if a new vertex had a 0-weight edge to every vertex,
    // so cycles anywhere in the graph are "reachable".
    vector<long long> dist(n + 1, 0);
    vector<int> par(n + 1, 0);
    int x = -1;                                   // a vertex relaxed in the last round
    for (int round = 1; round <= n; round++) {
        x = -1;
        for (int i = 0; i < m; i++)
            if (dist[a[i]] + c[i] < dist[b[i]]) {
                dist[b[i]] = dist[a[i]] + c[i];
                par[b[i]] = a[i];
                x = b[i];
            }
        if (x == -1) break;                       // a quiet round: everything is final
    }
    if (x == -1) {                                // n - 1 rounds sufficed: no negative cycle
        cout << "NO\n";
        return 0;
    }
    // Still relaxing in round n. x may hang below the cycle; n steps up par lands on it.
    for (int i = 0; i < n; i++) x = par[x];
    vector<int> cyc = {x};
    for (int v = par[x]; v != x; v = par[v]) cyc.push_back(v);
    cyc.push_back(x);
    reverse(cyc.begin(), cyc.end());              // par points backwards along the edges
    cout << "YES\n";
    for (int i = 0; i < (int)cyc.size(); i++) cout << cyc[i] << " \n"[i + 1 == (int)cyc.size()];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Try every simple cycle (n <= 7): a negative closed walk contains a negative simple cycle.
int n, m;
long long w[8][8];
const long long NONE = LLONG_MAX;
vector<int> path;
bool used[8];
bool dfs(long long sum) {
    int last = path.back();
    if (w[last][path[0]] != NONE && sum + w[last][path[0]] < 0) {
        cout << "YES\n";
        for (int v : path) cout << v << ' ';
        cout << path[0] << '\n';
        return true;
    }
    for (int v = 1; v <= n; v++)
        if (!used[v] && w[last][v] != NONE) {
            used[v] = true;
            path.push_back(v);
            if (dfs(sum + w[last][v])) return true;
            path.pop_back();
            used[v] = false;
        }
    return false;
}
int main() {
    cin >> n >> m;
    for (int i = 0; i < 8; i++)
        for (int j = 0; j < 8; j++) w[i][j] = NONE;
    for (int i = 0; i < m; i++) {
        int a, b;
        long long c;
        cin >> a >> b >> c;
        w[a][b] = min(w[a][b], c);
    }
    for (int s = 1; s <= n; s++) {
        path = {s};
        used[s] = true;
        if (dfs(0)) return 0;
        used[s] = false;
    }
    cout << "NO\n";
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Bellman-Ford from every vertex in turn, to be sure no cycle is out of reach.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    vector<long long> c(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i] >> c[i];
    const long long INF = LLONG_MAX;
    vector<long long> dist(n + 1);
    vector<int> par(n + 1);
    for (int s = 1; s <= n; s++) {
        fill(dist.begin(), dist.end(), INF);
        dist[s] = 0;
        int x = -1;
        for (int round = 1; round <= n; round++) {
            x = -1;
            for (int i = 0; i < m; i++)
                if (dist[a[i]] != INF && dist[a[i]] + c[i] < dist[b[i]]) {
                    dist[b[i]] = dist[a[i]] + c[i];
                    par[b[i]] = a[i];
                    x = b[i];
                }
            if (x == -1) break;
        }
        if (x == -1) continue;
        for (int i = 0; i < n; i++) x = par[x];
        vector<int> cyc = {x};
        for (int v = par[x]; v != x; v = par[v]) cyc.push_back(v);
        cyc.push_back(x);
        reverse(cyc.begin(), cyc.end());
        cout << "YES\n";
        for (int v : cyc) cout << v << ' ';
        cout << '\n';
        return 0;
    }
    cout << "NO\n";
}
""",
    hints=[
        r"""Without a negative cycle, Bellman-Ford's distances are final after n − 1 rounds. What
does it mean if round n still improves something?""",
        r"""A cycle nobody reaches from vertex 1 still counts. Start every `dist` at 0 instead of
∞: it is as if an extra vertex had a 0-weight edge to every vertex.""",
        r"""Record `par[v]` on each relaxation. The vertex `x` relaxed in round n may only hang
*below* the cycle: step `x = par[x]` n times to land on the cycle, then follow `par` until
you are back at `x`, and reverse.""",
    ],
    editorial=r"""
Bellman-Ford with all distances starting at 0 (a virtual source joined to every vertex by
a 0-weight edge, so no cycle is out of reach), and `par[v]` recorded at each relaxation.

If there is no negative cycle, every shortest route from the virtual source is simple, so
n − 1 rounds (plus the virtual edge) settle everything and round n changes nothing. If
there is a negative cycle, some edge on it relaxes in *every* round: if none of
`dist[v] ≤ dist[u] + w(u,v)` could be violated around the cycle, summing them would give
0 ≤ total weight. So round n relaxes some vertex `x` exactly when a negative cycle exists.

`x` itself may only be reachable *through* the cycle. Its parent chain, followed n times,
must repeat a vertex, and the repeated part is the cycle (the parent graph's cycle is
negative). Follow `par` from there back to the start and reverse, since `par` points
against the edges. O(n·m) = 1.25·10^7.

Traps: `dist[1] = 0` with the rest at ∞ misses cycles that vertex 1 cannot reach (a hidden
test has one); printing the cycle backwards; stopping the parent walk too early. Running
Bellman-Ford from every vertex separately fixes the first trap but costs n times more.
""",
)

SHORTEST_ROUTES_2 = Problem(
    id="shortest_routes_2",
    title="Shortest Routes II",
    difficulty="medium",
    source="CSES 1672 - Shortest Routes II",
    complexity="O(n^3 + q)",
    statement=r"""
There are `n` cities and `m` two-way roads, each with a length. Answer `q` questions of
the form: what is the length of the shortest route between cities `a` and `b`?
""",
    input=r"""
The first line has three integers `n`, `m`, `q` (1 ≤ n ≤ 500, 0 ≤ m ≤ n^2,
1 ≤ q ≤ 10^5).

Each of the next `m` lines has three integers `a`, `b`, `c` (1 ≤ a, b ≤ n, a ≠ b,
1 ≤ c ≤ 10^9): a road between `a` and `b` of length `c`. There may be several roads
between the same two cities.

Each of the next `q` lines has two integers `a` and `b` (1 ≤ a, b ≤ n).
""",
    output=r"""
For each question, print the length of the shortest route, or `-1` if there is none.
""",
    samples=[
        Test("4 3 5\n1 2 5\n1 3 9\n2 3 3\n1 2\n2 1\n1 3\n1 4\n3 2\n", "5\n5\n8\n-1\n3\n"),
    ],
    tests=[
        Test("1 0 1\n1 1\n"),
        Test("2 3 3\n1 2 7\n2 1 3\n1 2 9\n1 2\n2 1\n2 2\n",
             note="Three roads join 1 and 2; only the shortest counts."),
        Test("4 5 3\n1 2 5\n2 3 2\n1 3 9\n3 4 1\n1 4 20\n1 4\n4 1\n2 4\n"),
        Test("3 2 2\n1 2 1000000000\n2 3 1000000000\n1 3\n3 1\n"),
    ],
    gens=[
        Gen("small random", _roads_small, 18),
        Gen("medium random", lambda rng: _roads(rng, 60, 200, 500, 1, 10**9, 2), 3),
        Gen("max dense", lambda rng: _roads(rng, 500, 250000, 100000, 1, 10**9), 1, large=True),
        Gen("max sparse, split", lambda rng: _roads(rng, 500, 2000, 100000, 1, 10**9, 3), 1,
            large=True),
        Gen("max one long chain", lambda rng: _roads_path(rng, 500, 100000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const long long INF = 1e18;              // INF + INF = 2e18 still fits in long long
long long d[501][501];

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, q;
    cin >> n >> m >> q;
    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= n; j++) d[i][j] = (i == j ? 0 : INF);
    for (int i = 0; i < m; i++) {
        int a, b;
        long long c;
        cin >> a >> b >> c;
        d[a][b] = min(d[a][b], c);       // parallel roads: keep the shortest
        d[b][a] = min(d[b][a], c);
    }
    // After round k, d[i][j] is the shortest route using only cities 1..k in between.
    for (int k = 1; k <= n; k++)         // k must be the OUTER loop
        for (int i = 1; i <= n; i++) {
            if (d[i][k] == INF) continue;
            for (int j = 1; j <= n; j++)
                d[i][j] = min(d[i][j], d[i][k] + d[k][j]);
        }
    while (q--) {
        int a, b;
        cin >> a >> b;
        cout << (d[a][b] == INF ? -1 : d[a][b]) << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Bellman-Ford from scratch for every question.
int main() {
    int n, m, q;
    cin >> n >> m >> q;
    vector<int> a(m), b(m);
    vector<long long> c(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i] >> c[i];
    const long long INF = LLONG_MAX;
    while (q--) {
        int s, t;
        cin >> s >> t;
        vector<long long> dist(n + 1, INF);
        dist[s] = 0;
        bool changed = true;
        while (changed) {
            changed = false;
            for (int i = 0; i < m; i++)
                for (int k = 0; k < 2; k++) {
                    int u = k ? b[i] : a[i], v = k ? a[i] : b[i];
                    if (dist[u] != INF && dist[u] + c[i] < dist[v]) {
                        dist[v] = dist[u] + c[i];
                        changed = true;
                    }
                }
        }
        cout << (dist[t] == INF ? -1 : dist[t]) << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Dijkstra for every question, stopping as soon as the target is settled.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, q;
    cin >> n >> m >> q;
    vector<vector<pair<int, int>>> adj(n + 1);
    for (int i = 0; i < m; i++) {
        int a, b, c;
        cin >> a >> b >> c;
        adj[a].push_back({b, c});
        adj[b].push_back({a, c});
    }
    const long long INF = LLONG_MAX;
    vector<long long> dist(n + 1);
    while (q--) {
        int s, t;
        cin >> s >> t;
        fill(dist.begin(), dist.end(), INF);
        priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> pq;
        dist[s] = 0;
        pq.push({0, s});
        while (!pq.empty()) {
            auto [d, u] = pq.top();
            pq.pop();
            if (d > dist[u]) continue;
            if (u == t) break;
            for (auto [v, w] : adj[u])
                if (d + w < dist[v]) {
                    dist[v] = d + w;
                    pq.push({dist[v], v});
                }
        }
        cout << (dist[t] == INF ? -1 : dist[t]) << '\n';
    }
}
""",
    hints=[
        r"""10^5 questions but only 500 cities: compute the answer for *every* pair once, then answer
each question by a lookup.""",
        r"""Floyd-Warshall: `for k, for i, for j: d[i][j] = min(d[i][j], d[i][k] + d[k][j])`, with
`k` as the outermost loop. 500^3 = 1.25·10^8 simple steps.""",
        r"""Initialise `d[i][i] = 0`, everything else ∞, and read each road with `min`, since two roads
can join the same cities. Pick ∞ so that ∞ + ∞ does not overflow (`1e18` in `long long`).""",
    ],
    editorial=r"""
Floyd-Warshall. Let `d_k[i][j]` be the length of the shortest route from `i` to `j` whose
intermediate cities all lie in `{1, ..., k}`. A route allowed to use city `k` either does
not use it (`d_(k−1)[i][j]`) or passes through it once, splitting into two routes that use
only `{1, ..., k−1}` inside (`d_(k−1)[i][k] + d_(k−1)[k][j]`). With `k` as the outer loop,
one table updated in place is enough: during round `k` the entries `d[i][k]` and `d[k][j]`
do not change, because `d[k][k] = 0`. O(n^3) = 1.25·10^8, then O(1) per question.

Traps: `k` must be the outermost loop (inside, `d[i][j]` would be finished before the
entries it depends on); two roads between the same cities (read with `min`); `d[i][i] = 0`
even though no road says so; ∞ + ∞ overflowing (use `1e18`, not `LLONG_MAX`, or skip
`d[i][k] == INF`); answers up to 499·10^9 need `long long`. Dijkstra per question costs
about q·m = 2.5·10^10 here.
""",
)

FLIGHT_DISCOUNT = Problem(
    id="flight_discount",
    title="Flight Discount",
    difficulty="hard",
    source="CSES 1195 - Flight Discount",
    complexity="O((n + m) log n)",
    statement=r"""
You want to fly from city 1 to city `n` as cheaply as possible, and you have one discount
coupon: it halves the price of one flight of your choice (rounding down, so a flight
costing `c` then costs `⌊c/2⌋`). The coupon can be used at most once.

What is the minimum total price?
""",
    input=r"""
The first line has two integers `n` and `m` (2 ≤ n ≤ 10^5, 1 ≤ m ≤ 2·10^5).

Each of the next `m` lines has three integers `a`, `b`, `c` (1 ≤ a, b ≤ n, a ≠ b,
1 ≤ c ≤ 10^9): a one-way flight from `a` to `b` costing `c`. City `n` can be reached from
city 1.
""",
    output=r"""
Print one integer: the minimum price of a route from 1 to `n` using the coupon at most
once.
""",
    samples=[
        Test("3 4\n1 2 3\n2 3 1\n1 3 7\n2 1 5\n", "2\n"),
        Test("3 3\n1 3 100\n1 2 40\n2 3 40\n", "50\n",
             note="The cheapest route costs 80, but the coupon is worth more on the expensive direct flight."),
    ],
    tests=[
        Test("2 1\n1 2 1\n"),
        Test("2 2\n1 2 7\n1 2 5\n"),
        Test("4 4\n1 2 1000000000\n2 3 1000000000\n3 4 1000000000\n1 4 1000000000\n"),
        Test("4 5\n1 2 1\n2 4 9\n1 3 4\n3 4 4\n4 1 1\n"),
    ],
    gens=[
        Gen("small random", _flights_small, 18),
        Gen("medium random", lambda rng: _flights(rng, 500, 2000, 1, 10**9, 3), 3),
        Gen("max random deep", lambda rng: _flights(rng, 100000, 200000, 1, 10**9, 3), 1, large=True),
        Gen("max random shallow", lambda rng: _flights(rng, 100000, 200000, 1, 10**9, 100000), 1,
            large=True),
        Gen("max long path listed backwards", lambda rng: _reversed_path(rng, 100000, 200000, 10**9),
            1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, int>>> adj(n + 1);
    for (int i = 0; i < m; i++) {
        int a, b, c;
        cin >> a >> b >> c;
        adj[a].push_back({b, c});
    }

    // State (city, used): used = 1 once the coupon is spent. State id = 2 * city + used.
    const long long INF = LLONG_MAX;
    vector<long long> dist(2 * (n + 1), INF);
    priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> pq;
    auto relax = [&](int s, long long d) {
        if (d < dist[s]) {
            dist[s] = d;
            pq.push({d, s});
        }
    };
    relax(2 * 1 + 0, 0);
    while (!pq.empty()) {
        auto [d, s] = pq.top();
        pq.pop();
        if (d > dist[s]) continue;
        int u = s / 2, used = s % 2;
        for (auto [v, c] : adj[u]) {
            relax(2 * v + used, d + c);             // pay in full, coupon state unchanged
            if (!used) relax(2 * v + 1, d + c / 2); // spend the coupon on this flight
        }
    }
    cout << min(dist[2 * n], dist[2 * n + 1]) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Try the coupon on each flight in turn (and on none), Bellman-Ford each time.
int main() {
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    vector<long long> c(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i] >> c[i];
    const long long INF = LLONG_MAX;
    long long best = INF;
    for (int k = -1; k < m; k++) {
        vector<long long> dist(n + 1, INF);
        dist[1] = 0;
        bool changed = true;
        while (changed) {
            changed = false;
            for (int i = 0; i < m; i++) {
                long long w = (i == k ? c[i] / 2 : c[i]);
                if (dist[a[i]] != INF && dist[a[i]] + w < dist[b[i]]) {
                    dist[b[i]] = dist[a[i]] + w;
                    changed = true;
                }
            }
        }
        best = min(best, dist[n]);
    }
    cout << best << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Dijkstra once for every choice of the discounted flight.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<array<int, 3>>> adj(n + 1);        // (to, price, flight id)
    for (int i = 0; i < m; i++) {
        int a, b, c;
        cin >> a >> b >> c;
        adj[a].push_back({b, c, i});
    }
    const long long INF = LLONG_MAX;
    vector<long long> dist(n + 1);
    long long best = INF;
    for (int k = 0; k < m; k++) {
        fill(dist.begin(), dist.end(), INF);
        priority_queue<pair<long long, int>, vector<pair<long long, int>>, greater<>> pq;
        dist[1] = 0;
        pq.push({0, 1});
        while (!pq.empty()) {
            auto [d, u] = pq.top();
            pq.pop();
            if (d > dist[u]) continue;
            if (u == n) break;
            for (auto [v, c, id] : adj[u]) {
                long long w = (id == k ? c / 2 : c);
                if (d + w < dist[v]) {
                    dist[v] = d + w;
                    pq.push({dist[v], v});
                }
            }
        }
        best = min(best, dist[n]);
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""Taking the cheapest route and halving its most expensive flight is wrong: see the second
sample. The coupon changes which route is best.""",
        r"""Let the search remember whether the coupon is spent. The vertices become pairs
`(city, used)`: from `(u, 0)` a flight `u → v` leads to `(v, 0)` at price `c` or to
`(v, 1)` at price `c/2`; from `(u, 1)` only to `(v, 1)` at price `c`. Dijkstra on that
graph of 2n vertices.""",
        r"""Alternative: Dijkstra from 1, and Dijkstra from `n` on the reversed flights. Then try
each flight `u → v` as the discounted one: `from1[u] + c/2 + ton[v]`.""",
    ],
    editorial=r"""
State expansion. A partial route is described by its city *and* whether the coupon has
been spent, so run Dijkstra on the graph whose vertices are `(city, used)`: each flight
`u → v` gives the edges `(u,0) → (v,0)` at `c`, `(u,0) → (v,1)` at `⌊c/2⌋` and
`(u,1) → (v,1)` at `c`. That is 2n vertices and 3m edges, still O((n + m) log n). The
answer is `dist(n, 1)` (spending the coupon never hurts once a route has a flight).

An equivalent solution: `A` = Dijkstra from 1, `B` = Dijkstra from `n` on reversed
flights, answer = min over flights `u → v` of `A[u] + ⌊c/2⌋ + B[v]`.

The greedy "cheapest route, then halve its priciest flight" fails: flights 1→3 at 100 and
1→2→3 at 40 + 40 give 60 by greedy, 50 by halving the direct flight. Trying every flight
as the discounted one with a fresh Dijkstra is correct but costs m Dijkstras: about
2·10^5 · 2·10^5 steps. Prices sum to about 10^14: `long long`.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo10",
    title="shortest paths",
    track="algo",
    order=10,
    summary="Relaxation, Bellman-Ford and why n − 1 rounds suffice, Dijkstra and exactly where "
            "negative edges break it, negative cycles, Floyd-Warshall, and state expansion.",
    prereqs=["algo09"],
    tags=["shortest paths", "dijkstra", "bellman-ford", "negative cycle", "floyd-warshall",
          "state graph", "0-1 bfs", "priority queue"],
    parts=[
        Part("When edges have lengths", [
            Say(r"""
algo09's BFS finds routes with the fewest edges. Most shortest-path problems put a price
on each edge.

**Shortest Routes I** (CSES 1671): `n ≤ 10^5` cities, `m ≤ 2·10^5` one-way flights, each
with a price between 1 and 10^9. Every city is reachable from city 1. Print the cheapest
price from city 1 to every city. One second.
"""),
            MCQ(r"""
Run BFS from city 1 anyway, counting each flight as one step. Flights: `1→3` costs 10,
`1→2` costs 1, `2→3` costs 1. What goes wrong for city 3?
""", [
                Opt("Nothing: BFS reaches 3 through 2, at price 2.",
                    why="BFS reaches 3 in layer 1, straight from city 1, and never looks at 3 "
                        "again. It reports the route that costs 10."),
                Opt("BFS only goes wrong when some prices are negative.",
                    why="It already fails here with positive prices: 'fewest flights' and "
                        "'cheapest' are different questions."),
                Opt("BFS reaches 3 with one flight and keeps it: price 10, while `1→2→3` costs 2.",
                    correct=True,
                    why="Right. The first arrival is the one with the fewest edges, and with "
                        "prices that is no longer the cheapest."),
            ]),
            Numeric(r"""
One way to rescue BFS: replace a flight of price `c` by a chain of `c` flights of price 1,
through `c − 1` new cities. With `m = 2·10^5` flights of price up to 10^9, how many cities
could the new graph have?
""", answer=2e14, rel=0.5, unit="cities",
                explain=r"""
About `2·10^5 · 10^9 = 2·10^14`. The trick is fine when prices are tiny (1 or 2, as at the
end of algo09); here we need something that works with the prices directly.
"""),
            Say(r"""
Keep a tentative price `dist[v]` for every city: 0 for city 1, ∞ for the rest. The one
operation every shortest-path algorithm is built from is **relaxing** an edge `u → v` of
price `w`:

```cpp
if (dist[u] + w < dist[v]) dist[v] = dist[u] + w;   // found a cheaper way into v
```

`dist[v]` only ever goes down, and it is always the price of some real route. The
simplest algorithm, **Bellman-Ford**, relaxes every edge, in any fixed order, over and
over, in *rounds*, until a whole round changes nothing.
"""),
            Short(r"""
The path `1→2→3→4→5`, every price 1, with the edges listed in the order `4→5`, `3→4`,
`2→3`, `1→2`. Each round relaxes the list once, in this order, updating `dist` as it goes.
How many rounds change at least one distance?
""", accept=["4", "four"], placeholder="a number",
                hint="In round 1, when `4→5` is relaxed, what is `dist[4]`?",
                explain=r"""
Four. Round 1 only fixes city 2 (every other edge is relaxed while its start is still at
∞), round 2 fixes city 3, and so on; round 5 changes nothing. Listed front to back, one
round would fix everything. The order of the list decides, and the worst case is one
round per edge of the route.
"""),
            MCQ(r"""
What does round `k` of Bellman-Ford guarantee, whatever the order of the list?
""", [
                Opt("The `k` cities closest to city 1 have their final price.",
                    why="Closeness in price is not what rounds measure: a very expensive city "
                        "reached by a single flight is final after round 1."),
                Opt("Every city whose cheapest route uses at most `k` flights has its final price.",
                    correct=True,
                    why="Yes, by induction: if the cheapest route to `v` has `k` flights and ends "
                        "with `u → v`, the route to `u` has `k − 1`, so `u` is final after round "
                        "`k − 1`, and round `k` relaxes `u → v`."),
                Opt("The edges in the first `k` positions of the list have been relaxed correctly.",
                    why="Positions in the list do not enter the guarantee; the number of flights "
                        "on the cheapest route does."),
            ], explain=r"""
A cheapest route never visits a city twice (with no negative cycles, a detour cannot make it
cheaper), so it has at most `n − 1` flights: **`n − 1` rounds always suffice**. Remember
this; part 3 turns it into a negative-cycle detector.
"""),
            Numeric(r"""
`n − 1` rounds of `m` relaxations. With `n = 10^5` and `m = 2·10^5`, how many relaxations
is that in the worst case?
""", answer=2e10, rel=0.5, unit="relaxations",
                explain=r"""
`10^5 · 2·10^5 = 2·10^10`: twenty seconds or more. The hidden tests include the long path
listed backwards, which really needs every round.
"""),
        ]),
        Part("Dijkstra: settle the closest city first", [
            Reflect(r"""
Bellman-Ford relaxes every flight in every round, including flights out of cities whose
price will still change, and flights it has already relaxed with the same price. Ideally
each flight would be relaxed exactly once, from a city whose price is already final. With
non-negative prices, which city's price can you be sure is final at any moment?
""", answer=r"""
Among the cities not yet finished, the one with the smallest tentative price. Any other
route to it has to pass through some unfinished city first, and reaching that city
already costs at least as much; the rest of the route cannot make it cheaper, because
prices are non-negative. So: repeatedly take the unfinished city with the smallest
`dist`, declare it final (*settle* it), and relax its outgoing flights once. That is
**Dijkstra's algorithm**. Each flight is relaxed once instead of up to `n − 1` times.
"""),
            MCQ(r"""
Make that precise. City `v` has the smallest tentative price `D` among the unsettled
cities. Take *any* route from 1 to `v`. Why does it cost at least `D`?
""", [
                Opt("Because `v` was discovered before the other unsettled cities.",
                    why="The order of discovery means nothing here; a city discovered early can "
                        "still get a much cheaper price later."),
                Opt("It starts among the settled cities and ends outside, so it has a first "
                    "unsettled city `x`; the part up to `x` costs at least `dist[x] ≥ D`, and "
                    "the rest adds prices that are not negative.", correct=True,
                    why="Right. `dist[x]` is already the best price over routes whose earlier "
                        "cities are all settled (the settled cities relaxed their flights), and "
                        "the tail cannot bring the total below that."),
                Opt("Because every flight out of `v` costs at least `D`.",
                    why="Flights *out of* `v` have nothing to do with routes *into* `v`."),
            ], explain=r"""
Point at the exact step that needs non-negative prices: "the rest adds prices that are not
negative". Remove it and the argument collapses, as the next question shows.
"""),
            MCQ(r"""
Consider a version of Dijkstra that marks a city as done when it is popped and never
changes it afterwards. For which of these graphs, all from source `s`, does it print a
wrong distance?
""", [
                Opt("`s→u` costs −2, `u→t` costs 1, `s→t` costs 5.",
                    why="Trace it: `u` gets −2 and `t` gets 5; `u` is popped first (−2 is the "
                        "smallest) and improves `t` to −1 before `t` is popped. Correct, because "
                        "the negative flight leaves a city that is settled first anyway."),
                Opt("`s→t` costs 1, `t→u` costs −5, `s→u` costs 3.",
                    why="`t` is popped at 1 and relaxes `t→u` to −4 while `u` is still waiting. "
                        "Correct: the negative flight leads into a city that is not settled yet."),
                Opt("`s→t` costs 1, `s→u` costs 2, `u→t` costs −2.", correct=True,
                    why="Yes. `t` is popped at 1 and declared final; then `u` (at 2) finds "
                        "2 − 2 = 0 < 1, too late. The true distance to `t` is 0."),
            ], explain=r"""
The route `s→u→t` first goes to a *more* expensive city and then gets cheaper: exactly the
step "the rest adds nothing negative" forbids. The lazy implementation below would push
`t` again and repair this small case, but then a city can be processed many times, and on
specially built graphs exponentially many times. With negative prices, use Bellman-Ford.
"""),
            Say(r"""
In C++ the "unsettled city with the smallest `dist`" comes from a heap. `priority_queue`
has no "decrease key", so every improvement pushes a *new* entry, and outdated entries are
skipped when they surface (*lazy deletion*):

```cpp
vector<long long> dist(n + 1, LLONG_MAX);
priority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<>> pq;
dist[1] = 0;
pq.push({0, 1});
while (!pq.empty()) {
    auto [d, u] = pq.top();
    pq.pop();
    if (d > dist[u]) continue;           // stale copy: u was settled with less
    for (auto [v, w] : adj[u])           // adj[u] holds (to, price) pairs
        if (d + w < dist[v]) {
            dist[v] = d + w;
            pq.push({dist[v], v});
        }
}
```

Every flight pushes at most once, so the heap sees at most `m + 1` entries:
O((n + m) log n), about 3·10^5 · 18 ≈ 5·10^6 steps here.
"""),
            Short(r"""
Flights: `1→2` costs 4, `1→3` costs 1, `3→2` costs 2, `2→4` costs 1, `3→4` costs 5,
`4→5` costs 3. In which order does Dijkstra from city 1 settle the cities?
""", accept=["1 3 2 4 5", "1,3,2,4,5", "1-3-2-4-5", "1, 3, 2, 4, 5", "1 -> 3 -> 2 -> 4 -> 5"],
                placeholder="e.g. 1 2 3 4 5",
                hint="After settling 1, city 3 is at 1 and city 2 at 4. What does settling 3 do to city 2?",
                explain=r"""
`1` (0), `3` (1), then `2` at 3 (improved from 4 through 3), `4` at 4 (improved from 6 through
2), `5` at 7. Not the BFS order `1 2 3 4 5`: cities come out in order of *price*, and city
2's first price was not its final one.
"""),
            MCQ(r"""
You write `priority_queue<pair<long long,int>> pq;`, without `greater<>`. What happens?
""", [
                Opt("A compile error: pairs cannot be compared.",
                    why="Pairs compare lexicographically, so it compiles without a word."),
                Opt("Nothing: a priority queue gives the elements in sorted order either way.",
                    why="`priority_queue` is a max-heap by default: `top()` is the *largest* "
                        "element."),
                Opt("The *farthest* city comes out first, so popped cities are not final: they "
                    "get improved and re-expanded again and again. Still correct in the end, "
                    "but far too slow.", correct=True,
                    why="Right. The stale-entry check keeps the answer right, but the settle-once "
                        "guarantee is gone. Use `greater<>`, or push `{-dist, v}` and negate "
                        "back."),
            ]),
            Numeric(r"""
How large can a distance get in Shortest Routes I (`n = 10^5`, prices up to 10^9)?
""", answer=1e14, rel=0.5,
                explain=r"""
A route of `n − 1` flights at 10^9 each: about `10^14`, so `dist` is `long long`. For ∞,
`LLONG_MAX` is safe here because Dijkstra only adds a price to the distance of a popped,
finite city. In code that adds to ∞ (Floyd-Warshall, part 4), `LLONG_MAX + w` overflows to
a negative number; `1e18` leaves room. And `INT_MAX` is doubly wrong: too small for the
answers, and `INT_MAX + w` overflows.
"""),
            MCQ(r"""
What happens if you leave out the line `if (d > dist[u]) continue;`?
""", [
                Opt("Wrong answers: a stale entry overwrites a good distance.",
                    why="A stale entry has `d ≥ dist[u]`, so relaxing from it can never produce "
                        "anything below the true distances. The answers stay right."),
                Opt("Nothing: stale entries never exist, because each city is pushed once.",
                    why="Each *improvement* pushes a new entry and the old one stays in the heap; "
                        "a city can be pushed once per incoming flight."),
                Opt("The answers stay right, but a city pushed `k` times is expanded `k` times, "
                    "each time rescanning all its flights.", correct=True,
                    why="Right. One hidden test has a hub city that improves 5·10^4 times and has "
                        "5·10^4 outgoing flights: 2.5·10^9 wasted steps without the check."),
            ]),
            Try("shortest_routes_1", note="Dijkstra with `greater<>`, the stale check and `long long`. "
                "One hidden test is the backwards-listed path, another the hub."),
        ]),
        Part("Negative prices: Bellman-Ford and negative cycles", [
            Say(r"""
Negative edges appear when an edge is a gain rather than a cost (currency exchange,
rewards, "potential" tricks). Then Bellman-Ford is the tool, and a new question appears:
a cycle whose total is negative can be driven around forever, each lap lowering the
price, so "the shortest route" stops existing.

**Cycle Finding** (CSES 1197): a directed graph with `n ≤ 2500` vertices and `m ≤ 5000`
edges of weight between −10^9 and 10^9. Decide whether it has a negative cycle, and print
one.
"""),
            MCQ(r"""
If the graph has no negative cycle, part 1 says `n − 1` rounds settle everything, so round
`n` changes nothing. The converse is what makes a detector: why must a negative cycle make
*some* edge relax in round `n` (indeed in every round)?
""", [
                Opt("If no edge of the cycle could relax, then `dist[v] ≤ dist[u] + w` for each of "
                    "its edges `u → v`; adding them around the cycle, the `dist` terms cancel and "
                    "`0 ≤ total weight`, contradicting that it is negative.", correct=True,
                    why="Exactly. As long as the `dist` values on the cycle are finite, the cycle "
                        "can never be 'at rest'."),
                Opt("Because the distances on the cycle keep getting smaller until they overflow.",
                    why="They do keep shrinking, but that describes the symptom; the question "
                        "is why some edge must be relaxable in every single round."),
                Opt("It need not: a negative cycle can be quiet in round `n` if it is long enough.",
                    why="Length does not matter; the telescoping sum shows some edge of the "
                        "cycle is always relaxable."),
            ]),
            MCQ(r"""
You start with `dist[1] = 0` and every other `dist` at ∞, skipping relaxations out of cities
still at ∞. Which negative cycles can this miss?
""", [
                Opt("None: `n` rounds reach every vertex.",
                    why="Rounds only spread outward from vertex 1. A vertex that 1 cannot reach "
                        "stays at ∞ forever."),
                Opt("Short cycles, of length 1 or 2.",
                    why="A self-loop of weight −1 on a vertex reachable from 1 relaxes every "
                        "round. Length is not the issue."),
                Opt("Cycles that vertex 1 cannot reach: their vertices stay at ∞ and never relax.",
                    correct=True,
                    why="Right. The fix: start *every* `dist` at 0, as if a new vertex had a "
                        "0-weight edge to every vertex. Now every cycle is reachable."),
            ], explain=r"""
One hidden test has vertex 1 with no outgoing edges at all and a negative cycle elsewhere.
Running Bellman-Ford once from every vertex would also find it, at `n` times the cost.
"""),
            MCQ(r"""
Record `par[v] = u` at every relaxation. Vertex `x` was relaxed in round `n`. Why step
`x = par[x]` `n` times before reading off the cycle, instead of walking `par` from `x`
straight away?
""", [
                Opt("To make the printed cycle start at its smallest vertex.",
                    why="Any starting vertex is accepted; the reason is about where `x` is."),
                Opt("`x` may hang *below* the cycle, reached through it; after `n` steps back "
                    "along `par` you must be inside the cycle.", correct=True,
                    why="Right. A chain of `n + 1` parents repeats a vertex, and from there on "
                        "the chain goes round the cycle. Then follow `par` until you are back, "
                        "and reverse, because `par` points against the edges."),
                Opt("Because `par[x]` only becomes valid after `n` rounds.",
                    why="`par` is valid from the first relaxation; it just may lead from `x` "
                        "up into the cycle rather than around it."),
            ]),
            Numeric(r"""
Bellman-Ford with `n` rounds on Cycle Finding: `n = 2500`, `m = 5000`. How many
relaxations at most?
""", answer=1.25e7, rel=0.5, unit="relaxations",
                explain=r"""
`2500 · 5000 = 1.25·10^7`: comfortable. That is the budget Bellman-Ford needs. With
`n, m ≈ 10^5` it would be 10^10, which is why problems with negative edges have small
limits.
"""),
            Try("cycle_finding", note="All distances start at 0, `n` rounds, the parent walk. "
                "Any negative cycle is accepted."),
        ]),
        Part("All pairs at once: Floyd-Warshall", [
            Say(r"""
**Shortest Routes II** (CSES 1672): `n ≤ 500` cities, up to `n^2` two-way roads with
lengths up to 10^9, and `q ≤ 10^5` questions "shortest route between `a` and `b`?".
"""),
            Numeric(r"""
Dijkstra for each question relaxes up to all `m` roads. With `m = 2.5·10^5` and
`q = 10^5`, about how many relaxations is that?
""", answer=2.5e10, rel=0.5, unit="relaxations",
                explain=r"""
`q · m = 2.5·10^10`, before the heap's log factor. But there are only 500 cities: computing
all `500^2` answers once and looking them up is the better plan.
"""),
            Say(r"""
Number the cities `1..n`. Let `d_k[i][j]` be the shortest route from `i` to `j` whose
*intermediate* cities all lie in `{1, ..., k}`. `d_0` is the road table itself. A route
allowed to pass through `k` either avoids `k`, or passes through it once and splits there:

```cpp
// d[i][i] = 0, d[i][j] = shortest road i-j or INF
for (int k = 1; k <= n; k++)
    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= n; j++)
            d[i][j] = min(d[i][j], d[i][k] + d[k][j]);
```

After round `n`, every city is allowed in between: all pairs are done. `n^3 = 1.25·10^8`
steps for `n = 500`.
"""),
            Short(r"""
Two-way roads: `1–2` length 5, `2–3` length 2, `1–3` length 9, `3–4` length 1, `1–4`
length 20. What is `d[1][4]` after round `k = 2`, and after round `k = 3`? Write both
numbers.
""", accept=["20 8", "20, 8", "20,8", "20 and 8", "20 then 8"], placeholder="two numbers",
                hint="With only cities 1 and 2 allowed in between, can any route beat the direct road?",
                explain=r"""
`20`, then `8`. Using only cities 1 and 2 in between, no route to 4 exists except the
direct road (no road touches both 2 and 4). Round 2 did improve `d[1][3]` from 9 to 7
(through 2), so round 3 finds `d[1][3] + d[3][4] = 7 + 1 = 8`.
"""),
            MCQ(r"""
Someone writes the loops in the order `i`, `j`, `k` (with `k` innermost). What breaks?
""", [
                Opt("Nothing: `min` does not care about order, and every triple is still tried.",
                    why="Every triple is tried, but at the wrong moment: when `d[i][j]` takes its "
                        "minimum over `k`, the entries `d[i][k]` and `d[k][j]` may not be final "
                        "yet, and `d[i][j]` is never revisited."),
                Opt("`d[i][j]` is finished in one go, using `d[i][k]` and `d[k][j]` that may still "
                    "be too large: routes that need several intermediate cities get missed.",
                    correct=True,
                    why="Right. With `k` outermost, round `k` only needs round `k − 1`'s values, "
                        "which are all complete. Updating one table in place is safe because "
                        "`d[i][k]` and `d[k][j]` do not change during round `k` (`d[k][k] = 0`)."),
                Opt("It becomes slower because of cache misses, but stays correct.",
                    why="It is not a speed issue; the answers are wrong."),
            ]),
            MCQ(r"""
The roads are read with `d[a][b] = d[b][a] = c;`. Which input breaks this?
""", [
                Opt("Two roads between the same pair of cities, the cheaper one listed first.",
                    correct=True,
                    why="Right: the later, longer road overwrites the shorter one. Read with "
                        "`d[a][b] = min(d[a][b], c)`."),
                Opt("A city with no roads at all.",
                    why="Its row stays at `INF` except `d[i][i] = 0`, which is correct; questions "
                        "about it print -1."),
                Opt("A question that asks about the same city twice, `a = b`.",
                    why="That is `d[a][a] = 0`, as long as the diagonal is initialised to 0."),
            ], explain=r"""
Three more details: `d[i][i] = 0` even though no road says so; choose `INF = 1e18` so that
`INF + INF` does not overflow (or skip `d[i][k] == INF`); and answers reach 499·10^9, so
`long long`. Floyd-Warshall also works with negative edges, as long as there is no negative
cycle (then some `d[i][i]` becomes negative).
"""),
            Try("shortest_routes_2", note="Floyd-Warshall, `min` when reading, `-1` for unreachable pairs."),
        ]),
        Part("More state: Flight Discount", [
            Say(r"""
**Flight Discount** (CSES 1195): the Shortest Routes I setting, from city 1 to city `n`,
but you hold one coupon that halves the price of one flight (rounded down). Minimise the
total.
"""),
            MCQ(r"""
Plan: find the cheapest route, then use the coupon on its most expensive flight. Flights:
`1→3` costs 100, `1→2` costs 40, `2→3` costs 40, and `n = 3`. What does the plan pay, and
what is the best possible?
""", [
                Opt("The plan pays 50, which is optimal.",
                    why="The cheapest route is `1→2→3` at 80; halving one of its 40s gives 60. "
                        "The plan never considers the direct flight."),
                Opt("The plan pays 60; halving the direct flight gives 50.", correct=True,
                    why="Right. The coupon is worth the most on an expensive flight, so it changes "
                        "which route is best. Choosing the route first and the coupon second "
                        "cannot work."),
                Opt("Both pay 40.",
                    why="Halving a 40 on the route `1→2→3` gives 20 + 40 = 60, not 40."),
            ]),
            Reflect(r"""
A search from city 1 must decide route and coupon together. Besides the city a partial
route has reached, what does the search need to remember about it, and what graph does that
give you?
""", answer=r"""
Whether the coupon has been spent. Make that part of the vertex: the vertices become pairs
`(city, used)`. A flight `u → v` of price `c` gives three edges: `(u,0) → (v,0)` at `c`,
`(u,0) → (v,1)` at `⌊c/2⌋` (spend it now), and `(u,1) → (v,1)` at `c`. Run Dijkstra from
`(1,0)` and read `dist(n,1)`. This is **state expansion**: whenever a greedy choice
depends on something you have not decided yet, put that something into the vertex.
"""),
            Numeric(r"""
With `m = 2·10^5` flights, how many edges does the expanded graph have?
""", answer=6e5, rel=0.1, unit="edges",
                explain=r"""
Three per flight: `6·10^5`, on `2n = 2·10^5` vertices. Still O((n + m) log n). You do not
build it explicitly: store `dist` for id `2·v + used` and generate the edges while relaxing.
"""),
            MCQ(r"""
A second correct solution runs Dijkstra twice, then tries every flight `u → v` as the
discounted one: `A[u] + ⌊c/2⌋ + B[v]`. What are `A` and `B`?
""", [
                Opt("`A` from city 1; `B` from city `n` in the original graph.",
                    why="Dijkstra from `n` in the original graph gives routes *leaving* `n`. You "
                        "need the cheapest route from `v` *into* `n`."),
                Opt("`A` from city 1; `B` from city `n` with every flight reversed.", correct=True,
                    why="Right. A route from `v` to `n` is a route from `n` to `v` in the "
                        "reversed graph. The trick 'Dijkstra from both ends, then combine over "
                        "the middle edge' solves many 'one special edge' problems."),
                Opt("Both from city 1; `B[v]` is the price to `v` with the coupon spent.",
                    why="`B[v]` must cover the part of the route *after* the discounted flight, "
                        "from `v` to `n`."),
            ]),
            Try("flight_discount", note="State expansion (or two Dijkstras). The second sample is "
                "the greedy trap."),
        ]),
        Part("Choosing the algorithm", [
            Say(r"""
Shortest-path problems are chosen from the limits and the weights:

| weights | one source | all pairs |
| none (unit) | BFS, O(n + m) | BFS from each source |
| 0 or 1 | 0-1 BFS with a deque, O(n + m) | |
| non-negative | Dijkstra, O((n + m) log n) | Floyd-Warshall O(n^3) if n ≤ ~500 |
| negative | Bellman-Ford, O(n·m) | Floyd-Warshall O(n^3) |
"""),
            MCQ(r"""
**0-1 BFS**: edges cost 0 or 1 (for instance "the fewest one-way streets you must drive
against": a street costs 0 in its direction and 1 against it). Use a deque, pop from the
front, and relax as in Dijkstra. Where does a city improved through a 0-edge go?
""", [
                Opt("To the back, like in BFS.",
                    why="It has the *same* distance as the city just popped, while the back of "
                        "the deque may hold cities at distance + 1. Putting it behind them breaks "
                        "the order."),
                Opt("To the front: it has the same distance as the city just popped. A 1-edge "
                    "goes to the back.", correct=True,
                    why="Right. The deque then always holds distance `d` at the front and `d + 1` "
                        "at the back: algo09's layer invariant, so the deque is a free priority "
                        "queue. O(n + m), no log."),
                Opt("Anywhere; the stale-entry check fixes the order later.",
                    why="The check only discards outdated entries. It cannot make a city come "
                        "out in the right order."),
            ]),
            MCQ(r"""
SPFA (Bellman-Ford that only re-relaxes cities whose distance just changed, using a queue)
is often very fast on random graphs. Why is it a risky choice for a contest problem with
non-negative weights, `n = 10^5` and `m = 2·10^5`?
""", [
                Opt("Its worst case is still O(n·m), and problem setters include graphs built to "
                    "hit it.", correct=True,
                    why="Right. Graphs that make SPFA re-relax the same cities over and over are "
                        "well known, and setters add them precisely because SPFA is tempting. "
                        "Dijkstra's O((n + m) log n) holds on every input."),
                Opt("It gives wrong answers when weights are non-negative.",
                    why="It is correct for any weights without negative cycles; the problem is "
                        "its running time."),
                Opt("It cannot handle parallel edges.",
                    why="Parallel edges are just more relaxations; nothing special happens."),
            ], explain=r"""
The rule of thumb: non-negative weights, use Dijkstra; negative weights, the limits will be
small enough for Bellman-Ford; many queries on few vertices, Floyd-Warshall; and whenever
the problem has an extra resource (a coupon, a number of free moves, a key), put it into
the vertex. algo22 (flows) reuses Bellman-Ford and Dijkstra on residual graphs.
"""),
        ]),
    ],
    problems=[SHORTEST_ROUTES_1, CYCLE_FINDING, SHORTEST_ROUTES_2, FLIGHT_DISCOUNT],
    cards=[
        Card(r"""What does relaxing an edge `u → v` of weight `w` mean?""",
             r"""`if (dist[u] + w < dist[v]) dist[v] = dist[u] + w;` Every shortest-path algorithm is a strategy for choosing which edges to relax, and when."""),
        Card(r"""Why does Bellman-Ford need at most `n − 1` rounds?""",
             r"""After round `k`, every vertex whose shortest path has ≤ `k` edges is final. Without negative cycles a shortest path is simple, so it has ≤ `n − 1` edges."""),
        Card(r"""Why is Dijkstra's popped vertex final, and which assumption does that use?""",
             r"""Any other path to it leaves the settled set at some `x` with `dist[x]` ≥ the popped distance, and the rest of the path adds non-negative weights. Negative edges break exactly that step."""),
        Card(r"""Dijkstra in C++: the heap declaration and the stale check?""",
             r"""`priority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<>> pq;` and after popping `(d, u)`: `if (d > dist[u]) continue;`"""),
        Card(r"""What goes wrong with `priority_queue<pair<long long,int>>` in Dijkstra?""",
             r"""It is a max-heap: the farthest vertex comes out first, vertices are re-expanded many times, TLE. Use `greater<>` or push negated distances."""),
        Card(r"""A small Dijkstra counterexample with a negative edge?""",
             r"""`s→t 1, s→u 2, u→t −2`: `t` is settled at 1, the true distance is 0."""),
        Card(r"""How do you detect a negative cycle anywhere in the graph?""",
             r"""Bellman-Ford with every `dist` starting at 0 (a virtual source); if round `n` still relaxes some `x`, there is a negative cycle."""),
        Card(r"""How do you extract the negative cycle from Bellman-Ford?""",
             r"""Take `x` relaxed in round `n`, do `x = par[x]` `n` times (to land on the cycle), then follow `par` back to `x` and reverse."""),
        Card(r"""Floyd-Warshall: loop order and initialisation?""",
             r"""`for k, for i, for j: d[i][j] = min(d[i][j], d[i][k] + d[k][j])` with `k` outermost; `d[i][i] = 0`, roads read with `min`, `INF = 1e18` so `INF + INF` fits."""),
        Card(r"""What is state expansion (e.g. one discount coupon)?""",
             r"""Make the extra information part of the vertex: `(city, used)`, with edges for paying in full or using the coupon. Run the usual algorithm on the bigger graph."""),
        Card(r"""How does 0-1 BFS work?""",
             r"""A deque: pop the front; a vertex improved via a 0-edge goes to the front, via a 1-edge to the back. The deque holds distances `d` then `d + 1`. O(n + m)."""),
        Card(r"""Shortest paths from every vertex to a target `t` in a directed graph?""",
             r"""Run the single-source algorithm from `t` on the graph with every edge reversed."""),
    ],
)
