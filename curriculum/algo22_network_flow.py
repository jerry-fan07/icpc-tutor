from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _net(rng, n, m, cmax, big=0.0):
    """n computers, m one-way links; some short paths from 1 to n are planted so the
    answer is rarely 0. A fraction `big` of the links run at 10^9."""
    out = []
    while len(out) < m:
        if rng.random() < 0.3:
            path = [0] + rng.sample(range(1, n - 1), min(n - 2, rng.randint(0, 3))) + [n - 1]
            for a, b in zip(path, path[1:]):
                if len(out) < m:
                    out.append((a, b))
        else:
            a, b = rng.randrange(n), rng.randrange(n)
            if a != b:
                out.append((a, b))
    lines = [f"{n} {m}"]
    for a, b in out:
        c = 10**9 if rng.random() < big else rng.randint(1, cmax)
        lines.append(f"{a + 1} {b + 1} {c}")
    return "\n".join(lines) + "\n"


def _fan(rng, n):
    """1 -> v -> n for every middle v at about 10^9: the answer is about 5·10^11."""
    lines = []
    for v in range(2, n):
        lines.append(f"1 {v} {10**9}")
        lines.append(f"{v} {n} {10**9 - rng.randint(0, 5)}")
    rng.shuffle(lines)
    return f"{n} {len(lines)}\n" + "\n".join(lines) + "\n"


def _layers(rng, n, m, cmax):
    """Ten layers with links from each layer to the next (and a few back)."""
    size = (n - 2) // 10
    layer = [[0]] + [list(range(1 + i * size, 1 + (i + 1) * size)) for i in range(10)] + [[n - 1]]
    out = []
    while len(out) < m:
        i = rng.randrange(len(layer) - 1)
        a, b = rng.choice(layer[i]), rng.choice(layer[i + 1])
        if rng.random() < 0.1:
            a, b = b, a
        out.append((a, b, rng.randint(1, cmax)))
    return f"{n} {m}\n" + "\n".join(f"{a + 1} {b + 1} {c}" for a, b, c in out) + "\n"


def _streets(rng, n, m):
    """A random town: a spanning tree on the crossings plus extra streets; no loops, no
    repeated street."""
    edges = set()
    order = list(range(n))
    rng.shuffle(order)
    for i in range(1, n):
        if len(edges) >= m:
            break
        a, b = order[i], order[rng.randrange(i)]
        edges.add((min(a, b), max(a, b)))
    tries = 0
    while len(edges) < m and tries < 50 * m:
        tries += 1
        a, b = rng.randrange(n), rng.randrange(n)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    edges = list(edges)
    rng.shuffle(edges)
    lines = [f"{n} {len(edges)}"]
    for a, b in edges:
        if rng.random() < 0.5:
            a, b = b, a
        lines.append(f"{a + 1} {b + 1}")
    return "\n".join(lines) + "\n"


def _two_towns(rng, n, m, bridges):
    """Two dense halves joined by a few streets: the cheapest cut is in the middle, far
    from crossings 1 and n."""
    half = n // 2
    edges = set()
    while len(edges) < m - bridges:
        lo, hi = (0, half) if rng.randrange(2) == 0 else (half, n)
        a, b = rng.randrange(lo, hi), rng.randrange(lo, hi)
        if a != b:
            edges.add((min(a, b), max(a, b)))
    while len(edges) < m:
        edges.add((rng.randrange(0, half), rng.randrange(half, n)))
    edges = list(edges)
    rng.shuffle(edges)
    return f"{n} {len(edges)}\n" + "\n".join(f"{a + 1} {b + 1}" for a, b in edges) + "\n"


def _dance(rng, n, m, k):
    k = min(k, n * m)
    pairs = set()
    while len(pairs) < k:
        pairs.add((rng.randint(1, n), rng.randint(1, m)))
    pairs = list(pairs)
    rng.shuffle(pairs)
    return f"{n} {m} {k}\n" + "\n".join(f"{b} {g}" for b, g in pairs) + "\n"


def _dance_chain(rng, n):
    """Boy b may dance with girls b + 1 and b, the wrong one listed first: a greedy match
    leaves the last boy alone, and augmenting paths run the whole length of the chain."""
    pairs = []
    for b in range(1, n + 1):
        if b < n:
            pairs.append((b, b + 1))
        pairs.append((b, b))
    return f"{n} {n} {len(pairs)}\n" + "\n".join(f"{b} {g}" for b, g in pairs) + "\n"


def _carpool(rng, n, m, k, cmax):
    caps = [rng.randint(1, cmax) for _ in range(n)]
    k = min(k, n * m)
    pairs = set()
    while len(pairs) < k:
        pairs.add((rng.randint(1, n), rng.randint(1, m)))
    pairs = list(pairs)
    rng.shuffle(pairs)
    return (f"{n} {m} {k}\n" + " ".join(map(str, caps)) + "\n"
            + "\n".join(f"{a} {b}" for a, b in pairs) + "\n")


def _carpool_tight(rng, n, m, k):
    """The seats add up to exactly m and everyone can be served, so the last augmenting
    paths are long."""
    caps = [1] * n
    for _ in range(m - n):
        caps[rng.randrange(n)] += 1
    owner = [i + 1 for i in range(n) for _ in range(caps[i])]
    rng.shuffle(owner)
    pairs = {(owner[j], j + 1) for j in range(m)}
    while len(pairs) < k:
        pairs.add((rng.randint(1, n), rng.randint(1, m)))
    pairs = list(pairs)
    rng.shuffle(pairs)
    return (f"{n} {m} {k}\n" + " ".join(map(str, caps)) + "\n"
            + "\n".join(f"{a} {b}" for a, b in pairs) + "\n")


# -------------------------------------------------------------------- checkers
def _ints(text):
    return [int(v) for v in text.split()]


def _police_check(inp, expected, got):
    """Any minimum set of streets whose closure separates 1 from n."""
    v = _ints(inp)
    n, m = v[0], v[1]
    streets = {frozenset((v[2 + 2 * i], v[3 + 2 * i])) for i in range(m)}
    k = _ints(expected)[0]
    g = _ints(got)
    if not g:
        return False, "no output"
    if g[0] != k:
        return False, f"the minimum is {k} streets; you close {g[0]}"
    if len(g) != 1 + 2 * k:
        return False, f"expected {k} streets after the count, found {(len(g) - 1) / 2:g}"
    closed = set()
    for i in range(k):
        a, b = g[1 + 2 * i], g[2 + 2 * i]
        s = frozenset((a, b))
        if s not in streets:
            return False, f"there is no street between {a} and {b}"
        if s in closed:
            return False, f"the street {a} {b} is listed twice"
        closed.add(s)
    adj = {u: [] for u in range(1, n + 1)}
    for s in streets:
        if s not in closed:
            a, b = tuple(s)
            adj[a].append(b)
            adj[b].append(a)
    seen, stack = {1}, [1]
    while stack:
        u = stack.pop()
        for w in adj[u]:
            if w not in seen:
                seen.add(w)
                stack.append(w)
    if n in seen:
        return False, f"with those streets closed, crossing {n} is still reachable from 1"
    return True, ""


def _dance_check(inp, expected, got):
    """Any maximum set of allowed pairs with nobody dancing twice."""
    v = _ints(inp)
    k = v[2]
    allowed = {(v[3 + 2 * i], v[4 + 2 * i]) for i in range(k)}
    r = _ints(expected)[0]
    g = _ints(got)
    if not g:
        return False, "no output"
    if g[0] != r:
        return False, f"the maximum is {r} pairs; you printed {g[0]}"
    if len(g) != 1 + 2 * r:
        return False, f"expected {r} pairs after the count, found {(len(g) - 1) / 2:g}"
    boys, girls = set(), set()
    for i in range(r):
        b, q = g[1 + 2 * i], g[2 + 2 * i]
        if (b, q) not in allowed:
            return False, f"boy {b} and girl {q} are not a possible pair"
        if b in boys:
            return False, f"boy {b} dances twice"
        if q in girls:
            return False, f"girl {q} dances twice"
        boys.add(b)
        girls.add(q)
    return True, ""


# ------------------------------------------------------------------- the code
DINIC = r"""
struct Dinic {
    struct Edge { int to, rev; long long cap; };     // rev: index of the reverse edge in adj[to]
    vector<vector<Edge>> adj;
    vector<int> level, it;
    Dinic(int n) : adj(n), level(n), it(n) {}
    void addEdge(int u, int v, long long c, long long back = 0) {
        adj[u].push_back({v, (int)adj[v].size(), c});
        adj[v].push_back({u, (int)adj[u].size() - 1, back});   // residual edge
    }
    bool bfs(int s, int t) {                    // level = distance from s in the residual graph
        fill(level.begin(), level.end(), -1);
        vector<int> q = {s};
        level[s] = 0;
        for (size_t h = 0; h < q.size(); h++)
            for (auto& e : adj[q[h]])
                if (e.cap > 0 && level[e.to] < 0) {
                    level[e.to] = level[q[h]] + 1;
                    q.push_back(e.to);
                }
        return level[t] >= 0;
    }
    long long dfs(int u, int t, long long f) {  // one augmenting path along level + 1 edges
        if (u == t) return f;
        for (int& i = it[u]; i < (int)adj[u].size(); i++) {   // it[u] never moves back in a phase
            Edge& e = adj[u][i];
            if (e.cap > 0 && level[e.to] == level[u] + 1) {
                long long d = dfs(e.to, t, min(f, e.cap));
                if (d > 0) {
                    e.cap -= d;
                    adj[e.to][e.rev].cap += d;
                    return d;
                }
            }
        }
        return 0;
    }
    long long maxflow(int s, int t) {
        long long flow = 0;
        while (bfs(s, t)) {                     // one phase per BFS
            fill(it.begin(), it.end(), 0);
            while (long long f = dfs(s, t, LLONG_MAX)) flow += f;
        }
        return flow;
    }
};
"""

HEAD = r"""#include <bits/stdc++.h>
using namespace std;
"""


# --------------------------------------------------------------------- problems
DOWNLOAD_SPEED = Problem(
    id="download_speed",
    title="Download Speed",
    difficulty="medium",
    source="CSES 1694 - Download Speed",
    complexity="O(n^2 m) worst case (Dinic); far less in practice",
    statement=r"""
A file is copied from computer 1 to computer `n` over a network of one-way links. Link
`i` carries at most `c_i` megabytes per second. The data may be split over many routes
at once, and every computer in between forwards whatever it receives.

What is the largest total speed at which the file can arrive at computer `n`?
""",
    input=r"""
The first line has `n` and `m` (2 ≤ n ≤ 500, 1 ≤ m ≤ 1000). Each of the next `m` lines
has `a b c` (1 ≤ a, b ≤ n, a ≠ b, 1 ≤ c ≤ 10^9): a link from `a` to `b` with capacity
`c`. There can be several links between the same two computers, in either direction.
""",
    output=r"""
Print one integer: the maximum speed.
""",
    samples=[
        Test("5 7\n1 2 5\n1 3 7\n2 4 4\n3 2 3\n3 5 4\n4 5 6\n2 5 2\n", "10\n"),
        Test("4 5\n1 2 1\n1 3 1\n2 3 1\n2 4 1\n3 4 1\n", "2\n",
             note="Pushing along the first path found, 1 → 2 → 3 → 4, and never undoing it gets stuck "
                  "at 1."),
    ],
    tests=[
        Test("2 1\n1 2 1000000000\n"),
        Test("3 2\n1 2 5\n3 2 5\n"),
        Test("3 3\n2 1 7\n3 2 7\n3 1 7\n"),
        Test("4 6\n1 2 1000000000\n1 3 1000000000\n2 3 1\n3 2 1\n2 4 1000000000\n3 4 1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _net(rng, rng.randint(2, 9), rng.randint(1, 16), 10, 0.1), 16),
        Gen("random, max size", lambda rng: _net(rng, 500, 1000, 10**9), 2, large=True),
        Gen("fan, answer past int", lambda rng: _fan(rng, 500), 1, large=True),
        Gen("layered", lambda rng: _layers(rng, 500, 1000, 10**9), 1, large=True),
        Gen("layered, small capacities", lambda rng: _layers(rng, 500, 1000, 5), 1, large=True),
    ],
    solution=HEAD + DINIC + r"""
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    Dinic d(n);
    for (int i = 0; i < m; i++) {
        int a, b;
        long long c;
        cin >> a >> b >> c;
        d.addEdge(a - 1, b - 1, c);
    }
    cout << d.maxflow(0, n - 1) << '\n';    // up to 1000 * 10^9: long long
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Max flow = min cut: try every set S that contains 1 and not n.
int main() {
    int n, m;
    cin >> n >> m;
    vector<array<long long, 3>> ed(m);
    for (auto& [a, b, c] : ed) { cin >> a >> b >> c; a--; b--; }
    long long best = LLONG_MAX;
    for (int mask = 0; mask < (1 << n); mask++) {
        if (!(mask & 1) || (mask >> (n - 1) & 1)) continue;
        long long cut = 0;
        for (auto& [a, b, c] : ed)
            if ((mask >> a & 1) && !(mask >> b & 1)) cut += c;
        best = min(best, cut);
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""Repeatedly find a route with spare capacity on every link and push as much as its
tightest link allows. The second sample shows why you must also be able to *undo* flow.""",
        r"""For every link keep a reverse residual edge whose capacity is the flow on the link. An
augmenting path may use it, which moves flow away from that link.""",
        r"""Find augmenting paths by BFS (Edmonds-Karp) or use Dinic. The answer reaches 10^12:
capacities and the total in `long long`.""",
    ],
    editorial=r"""
Maximum flow. Keep, for every link `u → v`, its remaining capacity and a reverse residual
edge `v → u` whose capacity is the flow currently on the link. Any path from 1 to `n`
using edges of positive residual capacity (an augmenting path) can carry its bottleneck
more; pushing along a reverse edge cancels flow sent earlier. When no augmenting path is
left, the vertices reachable from 1 form a cut whose every outgoing link is full and whose
every incoming link is empty, so the flow equals that cut's capacity, and no flow can
exceed any cut: it is maximum.

The second sample is the reason for reverse edges: without them, the first path
1 → 2 → 3 → 4 blocks both 1 → 3 and 2 → 4 and the search stops at 1.

Choosing paths by BFS (Edmonds-Karp) bounds the augmentations by O(n·m) whatever the
capacities; Dinic does a BFS per phase and then pushes along all shortest paths at once,
O(n^2·m) in the worst case and much faster in practice. The total can reach 10^12.
""",
)

POLICE_CHASE = Problem(
    id="police_chase",
    title="Police Chase",
    difficulty="medium",
    source="CSES 1695 - Police Chase",
    complexity="O(flow · (n + m)); the flow is at most n",
    statement=r"""
A getaway car is at crossing 1 and wants to reach the harbour at crossing `n`. The police
can close streets. Find the smallest number of streets to close so that no route from 1
to `n` remains, and say which ones.
""",
    input=r"""
The first line has `n` and `m` (2 ≤ n ≤ 500, 1 ≤ m ≤ 1000). Each of the next `m` lines
has `a b` (1 ≤ a, b ≤ n, a ≠ b): a two-way street between crossings `a` and `b`. There is
at most one street between two crossings.
""",
    output=r"""
First print `k`, the minimum number of streets. Then print `k` lines `a b`, the streets to
close (either end first, in any order). If several choices are minimum, print any of them.
""",
    samples=[
        Test("8 14\n1 2\n1 3\n1 4\n2 3\n2 4\n3 4\n5 6\n5 7\n5 8\n6 7\n6 8\n7 8\n3 5\n4 6\n",
             "2\n3 5\n4 6\n",
             note="Two tightly connected districts joined by two streets."),
    ],
    tests=[
        Test("2 1\n2 1\n"),
        Test("4 2\n1 2\n3 4\n"),
        Test("3 2\n1 2\n2 3\n"),
        Test("4 5\n1 2\n1 3\n2 3\n2 4\n3 4\n"),
        Test("5 10\n1 2\n1 3\n1 4\n1 5\n2 3\n2 4\n2 5\n3 4\n3 5\n4 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _streets(rng, rng.randint(2, 8), rng.randint(1, 12)), 16),
        Gen("small districts", lambda rng: _two_towns(rng, 8, rng.randint(9, 13), rng.randint(1, 3)), 4),
        Gen("random, max size", lambda rng: _streets(rng, 500, 1000), 1, large=True),
        Gen("districts, max size", lambda rng: _two_towns(rng, 500, 1000, rng.randint(5, 12)), 2, large=True),
    ],
    checker=_police_check,
    solution=HEAD + DINIC + r"""
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    Dinic d(n);
    vector<pair<int, int>> streets(m);
    for (auto& [a, b] : streets) {
        cin >> a >> b;
        a--; b--;
        d.addEdge(a, b, 1, 1);             // two-way: one unit in each direction, each the
    }                                      // other's residual edge
    long long k = d.maxflow(0, n - 1);
    // S = crossings still reachable from 1 in the residual graph; close every street leaving S
    vector<char> inS(n, 0);
    vector<int> q = {0};
    inS[0] = 1;
    for (size_t h = 0; h < q.size(); h++)
        for (auto& e : d.adj[q[h]])
            if (e.cap > 0 && !inS[e.to]) {
                inS[e.to] = 1;
                q.push_back(e.to);
            }
    cout << k << '\n';
    for (auto [a, b] : streets)
        if (inS[a] != inS[b]) cout << a + 1 << ' ' << b + 1 << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Try every set of streets, smallest first, until one separates 1 from n.
int main() {
    int n, m;
    cin >> n >> m;
    vector<pair<int, int>> st(m);
    for (auto& [a, b] : st) { cin >> a >> b; a--; b--; }
    vector<int> order(1 << m);
    iota(order.begin(), order.end(), 0);
    stable_sort(order.begin(), order.end(), [](int x, int y) { return __builtin_popcount(x) < __builtin_popcount(y); });
    for (int mask : order) {
        vector<vector<int>> g(n);
        for (int i = 0; i < m; i++)
            if (!(mask >> i & 1)) { g[st[i].first].push_back(st[i].second); g[st[i].second].push_back(st[i].first); }
        vector<char> seen(n, 0);
        vector<int> stk = {0};
        seen[0] = 1;
        while (!stk.empty()) {
            int u = stk.back(); stk.pop_back();
            for (int v : g[u]) if (!seen[v]) { seen[v] = 1; stk.push_back(v); }
        }
        if (!seen[n - 1]) {
            cout << __builtin_popcount(mask) << '\n';
            for (int i = 0; i < m; i++) if (mask >> i & 1) cout << st[i].first + 1 << ' ' << st[i].second + 1 << '\n';
            return 0;
        }
    }
}
""",
    hints=[
        r"""Give every street capacity 1 in both directions. The maximum flow from 1 to `n` is the
number of streets in a minimum cut.""",
        r"""After the flow, collect the crossings still reachable from 1 through edges with positive
residual capacity. The streets with exactly one end in that set are a minimum cut.""",
        r"""Printing every street that carries flow is not the same thing: in a chain 1 – 2 – 3, both
streets carry flow and only one needs closing.""",
    ],
    editorial=r"""
Closing streets is cutting edges, so the answer is a minimum cut with every street of
capacity 1. By max-flow min-cut its size is the maximum flow from 1 to `n`, where a two-way
street is a pair of opposite edges of capacity 1 (conveniently stored as each other's
residual edge).

To find the streets themselves, run the flow to the end and let `S` be the set of
crossings reachable from 1 through edges with positive residual capacity. Every street
from `S` to the rest is saturated away from `S` (otherwise its far end would be reachable),
so the number of such streets equals the flow: they form a minimum cut. Printing all
saturated streets instead overcounts whenever flow passes through several streets in
series.

The flow is at most `n − 1` (crossing 1 has at most that many streets), and each
augmentation costs O(n + m).
""",
)

SCHOOL_DANCE = Problem(
    id="school_dance",
    title="School Dance",
    difficulty="medium",
    source="CSES 1696 - School Dance",
    complexity="O(k·√(n + m)) (Dinic on a unit network)",
    statement=r"""
At the school dance there are `n` boys and `m` girls, and `k` boy-girl pairs who are
willing to dance together. Form as many dancing pairs as possible, with nobody in two
pairs.
""",
    input=r"""
The first line has `n m k` (1 ≤ n, m ≤ 500, 1 ≤ k ≤ 1000). Each of the next `k` lines has
`a b` (1 ≤ a ≤ n, 1 ≤ b ≤ m): boy `a` and girl `b` are willing to dance. No pair is listed
twice.
""",
    output=r"""
First print `r`, the maximum number of pairs. Then print `r` lines `a b`: the pairs, in any
order. If several choices are maximum, print any of them.
""",
    samples=[
        Test("3 3 5\n1 1\n1 2\n2 1\n3 2\n3 3\n", "3\n1 2\n2 1\n3 3\n",
             note="Pairing boy 1 with girl 1 because she is listed first leaves boy 2 alone."),
    ],
    tests=[
        Test("1 1 1\n1 1\n"),
        Test("3 1 3\n1 1\n2 1\n3 1\n"),
        Test("4 4 7\n1 2\n1 1\n2 3\n2 2\n3 4\n3 3\n4 4\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _dance(rng, rng.randint(1, 8), rng.randint(1, 8), rng.randint(1, 14)), 16),
        Gen("small chain", lambda rng: _dance_chain(rng, rng.randint(2, 8)), 3),
        Gen("random, max size", lambda rng: _dance(rng, 500, 500, 1000), 2, large=True),
        Gen("chain, max size", lambda rng: _dance_chain(rng, 500), 1, large=True),
    ],
    checker=_dance_check,
    solution=HEAD + DINIC + r"""
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, k;
    cin >> n >> m >> k;
    int s = 0, t = n + m + 1;                    // boys 1..n, girls n+1..n+m
    Dinic d(n + m + 2);
    for (int b = 1; b <= n; b++) d.addEdge(s, b, 1);          // each boy dances at most once
    for (int g = 1; g <= m; g++) d.addEdge(n + g, t, 1);      // each girl too
    vector<array<int, 3>> pairs(k);              // boy, girl, index of the edge in adj[boy]
    for (auto& [b, g, idx] : pairs) {
        cin >> b >> g;
        idx = d.adj[b].size();
        d.addEdge(b, n + g, 1);
    }
    cout << d.maxflow(s, t) << '\n';
    for (auto [b, g, idx] : pairs)
        if (d.adj[b][idx].cap == 0) cout << b << ' ' << g << '\n';   // it carries the unit
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Every boy either sits out or takes a free girl he may dance with: try every choice.
int n, m, k, bestCnt = -1;
vector<vector<int>> likes;
vector<int> cur, best;
void go(int b, int used, int cnt) {
    if (b > n) {
        if (cnt > bestCnt) { bestCnt = cnt; best = cur; }
        return;
    }
    cur[b] = 0;
    go(b + 1, used, cnt);
    for (int g : likes[b])
        if (!(used >> g & 1)) { cur[b] = g; go(b + 1, used | 1 << g, cnt + 1); cur[b] = 0; }
}
int main() {
    cin >> n >> m >> k;
    likes.assign(n + 1, {});
    for (int i = 0; i < k; i++) { int b, g; cin >> b >> g; likes[b].push_back(g); }
    cur.assign(n + 1, 0);
    go(1, 0, 0);
    cout << bestCnt << '\n';
    for (int b = 1; b <= n; b++) if (best[b]) cout << b << ' ' << best[b] << '\n';
}
""",
    hints=[
        r"""Build a network: a source with an edge of capacity 1 to every boy, an edge of capacity
1 from each boy to each girl he may dance with, and an edge of capacity 1 from every girl
to a sink.""",
        r"""With integer capacities the maximum flow is integral, so every boy-girl edge carries 0
or 1: the edges carrying 1 are the pairs. Their residual capacity is 0 after the flow.""",
    ],
    editorial=r"""
Bipartite matching as flow: source → boy (1), boy → girl (1) for each willing pair,
girl → sink (1). A flow of value `r` uses `r` boy-girl edges with no boy or girl twice,
because one unit at most enters a boy and at most one leaves a girl; and any set of pairs
gives a flow. Augmenting paths push whole units, so the maximum flow is integral and reads
off as a matching: the boy-girl edges whose residual capacity dropped to 0.

In matching terms an augmenting path starts at a free boy, alternates between an edge not
in the matching and a matched edge taken backwards, and ends at a free girl; flipping it
adds one pair. Picking partners greedily fails on the sample, where the first choice for
boy 1 must be undone.

Dinic on this unit network runs in O(k·√(n + m)).
""",
)

CARPOOL = Problem(
    id="carpool",
    title="Carpool",
    difficulty="hard",
    complexity="Dinic: a few dozen BFS phases of O(n + m + k) each",
    statement=r"""
After the company party, `n` colleagues are driving home, and driver `i` has `c_i` free
seats. `m` other colleagues need a ride, and each has told you which drivers go their
way. Assign riders to drivers (every rider to at most one driver on their list, no driver
beyond their seats) so that as many colleagues as possible get a ride.
""",
    input=r"""
The first line has `n m k` (1 ≤ n, m ≤ 5·10^4, 1 ≤ k ≤ 10^5). The second line has
c_1, ..., c_n (1 ≤ c_i ≤ 5·10^4). Each of the next `k` lines has `a b` (1 ≤ a ≤ n,
1 ≤ b ≤ m): rider `b` can go with driver `a`. No pair is listed twice.
""",
    output=r"""
Print the maximum number of riders who get a seat.
""",
    samples=[
        Test("2 4 4\n2 1\n1 1\n1 2\n1 3\n2 1\n", "3\n",
             note="Seating riders 1 and 2 with driver 1 strands rider 3; rider 1 should go with driver 2."),
        Test("3 3 6\n2 1 1\n1 1\n1 2\n2 1\n3 1\n2 3\n3 3\n", "3\n"),
    ],
    tests=[
        Test("1 1 1\n50000\n1 1\n"),
        Test("1 5 5\n2\n1 1\n1 2\n1 3\n1 4\n1 5\n"),
        Test("3 2 2\n1 1 1\n2 1\n2 2\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _carpool(rng, rng.randint(1, 6), rng.randint(1, 7),
                                                 rng.randint(1, 20), rng.choice([1, 2, 3, 100])), 16),
        Gen("random, max size", lambda rng: _carpool(rng, 25000, 50000, 100000, 3), 1, large=True),
        Gen("every rider fits", lambda rng: _carpool_tight(rng, 30000, 50000, 100000), 1, large=True),
        Gen("few big cars", lambda rng: _carpool(rng, 2000, 50000, 100000, 30), 1, large=True),
    ],
    solution=HEAD + DINIC + r"""
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, k;
    cin >> n >> m >> k;
    int s = 0, t = n + m + 1;                    // drivers 1..n, riders n+1..n+m
    Dinic d(n + m + 2);
    for (int i = 1; i <= n; i++) {
        int c;
        cin >> c;
        d.addEdge(s, i, c);                      // the seats are a capacity: no copies needed
    }
    for (int j = 1; j <= m; j++) d.addEdge(n + j, t, 1);   // each rider rides once
    for (int i = 0; i < k; i++) {
        int a, b;
        cin >> a >> b;
        d.addEdge(a, n + b, 1);
    }
    cout << d.maxflow(s, t) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Max flow = min cut on source -> drivers -> riders -> sink: try every S.
int main() {
    int n, m, k;
    cin >> n >> m >> k;
    vector<long long> c(n);
    for (auto& x : c) cin >> x;
    vector<pair<int, int>> pr(k);
    for (auto& [a, b] : pr) { cin >> a >> b; a--; b--; }
    long long best = LLONG_MAX;
    for (int mask = 0; mask < (1 << (n + m)); mask++) {     // bit i: driver i in S; bit n + j: rider j
        long long cut = 0;
        for (int i = 0; i < n; i++) if (!(mask >> i & 1)) cut += c[i];
        for (int j = 0; j < m; j++) if (mask >> (n + j) & 1) cut += 1;
        for (auto [a, b] : pr) if ((mask >> a & 1) && !(mask >> (n + b) & 1)) cut += 1;
        best = min(best, cut);
    }
    cout << best << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Edmonds-Karp: a fresh BFS from the source for every augmenting path.
struct Edge { int to; long long cap; };
vector<Edge> e;
vector<vector<int>> g;
void addEdge(int u, int v, long long c) {
    g[u].push_back(e.size()); e.push_back({v, c});
    g[v].push_back(e.size()); e.push_back({u, 0});
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, k;
    cin >> n >> m >> k;
    int s = 0, t = n + m + 1, N = n + m + 2;
    g.assign(N, {});
    for (int i = 1; i <= n; i++) { int c; cin >> c; addEdge(s, i, c); }
    for (int j = 1; j <= m; j++) addEdge(n + j, t, 1);
    for (int i = 0; i < k; i++) { int a, b; cin >> a >> b; addEdge(a, n + b, 1); }
    long long flow = 0;
    vector<int> via(N);
    while (true) {
        fill(via.begin(), via.end(), -1);
        via[s] = -2;
        queue<int> q;
        q.push(s);
        while (!q.empty() && via[t] == -1) {
            int u = q.front(); q.pop();
            for (int id : g[u])
                if (e[id].cap > 0 && via[e[id].to] == -1) { via[e[id].to] = id; q.push(e[id].to); }
        }
        if (via[t] == -1) break;
        long long f = LLONG_MAX;
        for (int v = t; v != s; v = e[via[v] ^ 1].to) f = min(f, e[via[v]].cap);
        for (int v = t; v != s; v = e[via[v] ^ 1].to) { e[via[v]].cap -= f; e[via[v] ^ 1].cap += f; }
        flow += f;
    }
    cout << flow << '\n';
}
""",
    hints=[
        r"""Source → driver with capacity `c_i`, driver → rider with capacity 1 for each pair, rider
→ sink with capacity 1. The answer is the maximum flow.""",
        r"""Edmonds-Karp finds one path per BFS, and here every BFS scans all drivers with free
seats and their edges before it reaches a single rider: about 10^5 steps, repeated up to
5·10^4 times.""",
        r"""Dinic finds all the shortest augmenting paths of one length in a single phase, using the
current-edge pointers `it[u]`; on these networks a few dozen phases suffice.""",
    ],
    editorial=r"""
The model is School Dance with seats: source → driver `i` with capacity `c_i`, driver →
rider with capacity 1 for each allowed pair, rider → sink with capacity 1. An integral
maximum flow is an optimal assignment. Copying each driver `c_i` times would also work
but can create 2.5·10^9 vertices; a capacity says the same thing for free.

The difference between the algorithms is the point of the problem. Edmonds-Karp augments
one path per BFS, and a BFS from the source first queues every driver with a free seat,
then scans all their edges before it meets a rider: Θ(n + k) per augmentation, and there
are up to 5·10^4 augmentations, about 5·10^9 steps (tens of seconds). Dinic computes the
BFS levels once per phase and then finds *every* shortest augmenting path of that length
with a DFS that never re-scans a dead edge (the pointer `it[u]` only moves forward). The
number of phases here is a few dozen, each O(n + m + k): well under a second.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo22",
    title="network flow & matching",
    track="algo",
    order=22,
    summary="Maximum flow from the ground up: why pushing greedily gets stuck, residual "
            "edges that undo it, max flow = min cut, Edmonds-Karp and Dinic, reading off a "
            "cut, and matching as a flow.",
    prereqs=["algo10"],
    tags=["max flow", "min cut", "residual graph", "Edmonds-Karp", "Dinic",
          "bipartite matching", "modelling"],
    parts=[
        Part("Pipes, and a greedy that gets stuck", [
            Say(r"""
A file travels from computer 1 to computer `n` over `m ≤ 1000` one-way links between
`n ≤ 500` computers. Link `u → v` carries at most `c ≤ 10^9` megabytes per second. The
data may be split across many routes at once. What is the largest total speed?

This is a **flow network**. A flow assigns each edge an amount `f` with two rules:

- **capacity**: `0 ≤ f ≤ c` on every edge;
- **conservation**: at every vertex except the source `s` and the sink `t`, what flows
  in flows out.

The value of the flow is the net amount leaving `s`, and we want it as large as possible.
"""),
            MCQ(r"""
Before any algorithm: which of these is always an upper bound on the answer?
""", [
                Opt("The capacity of the fastest link in the network.",
                    why="Several routes can run in parallel, each carrying up to its own tightest link. "
                        "Two disjoint routes at 7 give 14, more than any single link."),
                Opt("The total capacity of the links leaving computer 1.", correct=True,
                    why="Yes: every unit of flow has to leave the source along one of them. The same "
                        "holds for the links entering `n`, and for any 'wall' that separates 1 from `n`, "
                        "an idea that becomes the whole proof of correctness."),
                Opt("The smallest capacity of any link.",
                    why="That link may not be on any useful route at all. A bottleneck limits the "
                        "routes that go through it, not the whole network."),
            ]),
            Say(r"""
The natural algorithm is greedy: find any route from `s` to `t` on which every link still
has spare capacity, push as much as its tightest link allows (the **bottleneck**), and
repeat until no such route exists.

Try it on this network, with every capacity 1:

```
1 -> 2,  1 -> 3,  2 -> 3,  2 -> 4,  3 -> 4        (s = 1, t = 4)
```
"""),
            Numeric(r"""
Suppose the route search happens to find `1 → 2 → 3 → 4` first and pushes 1 unit along
it. The greedy then looks for another route with spare capacity everywhere. What total
does it end with?
""", answer=1,
                hint="After the first push, which links are full? Is there still a route from 1 to 4 avoiding them?",
                explain=r"""
1. The links `1 → 2`, `2 → 3` and `3 → 4` are full. From 1 you can still go to 3, but 3's
only way out, `3 → 4`, is full: no route left.
"""),
            Numeric(r"""
What is the true maximum flow of that network?
""", answer=2,
                explain=r"""
2: send one unit along `1 → 2 → 4` and one along `1 → 3 → 4`. Both links out of 1 are
full, so 2 is also the upper bound from the previous question. The greedy's first route
used `2 → 3`, which blocked both of the good routes.
"""),
            Reflect(r"""
The greedy is stuck at 1 with the unit on `1 → 2 → 3 → 4`; the optimum uses `1 → 2 → 4`
and `1 → 3 → 4`. What operation would let the greedy get from its state to the optimum
by pushing one more unit along some route?
""", answer=r"""
It must be allowed to take back the unit it sent over `2 → 3`. Push a new unit along
`1 → 3`, then "backwards" over `3 → 2`, which cancels the unit on `2 → 3`, then `2 → 4`.
Net effect: the first unit now travels `1 → 2 → 4`, the second `1 → 3 → 4`. Greedy
choices are fine as long as later steps can undo them.
"""),
        ]),
        Part("Undo: the residual graph", [
            Say(r"""
Make undoing an ordinary move. For an edge `u → v` with capacity `c` currently carrying
`f`, the **residual graph** has

- a forward edge `u → v` with residual capacity `c − f` (room to send more), and
- a backward edge `v → u` with residual capacity `f` (room to cancel what was sent).

An **augmenting path** is any path from `s` to `t` in the residual graph. Pushing `d`
along it adds `d` to the flow on forward edges and cancels `d` on edges used backwards.
Repeating this until no augmenting path exists is the **Ford-Fulkerson** method.
"""),
            Short(r"""
In the four-vertex network, after the greedy pushed 1 unit along `1 → 2 → 3 → 4`, there
is exactly one path from 1 to 4 in the residual graph. List its vertices, separated by
spaces.
""", accept=["1 3 2 4", "1-3-2-4", "1->3->2->4", "1 → 3 → 2 → 4", "1,3,2,4"],
                placeholder="vertices in order",
                hint="`1 → 3` has room; which residual edges leave 3?",
                explain=r"""
`1 3 2 4`: forward `1 → 3` (room 1), backward `3 → 2` (it cancels the unit on `2 → 3`),
forward `2 → 4` (room 1). Its bottleneck is 1, and after pushing it the flow is 2.
"""),
            MCQ(r"""
After that push, how much flow is on the original edge `2 → 3`?
""", [
                Opt("0: the backward step cancelled it.", correct=True,
                    why="Right. The final flow is `1 → 2 → 4` plus `1 → 3 → 4`; the detour through "
                        "`2 → 3` has disappeared. The algorithm never needs to know which path each "
                        "unit 'really' took."),
                Opt("1: flow on an edge only ever grows.",
                    why="That is the greedy without undo, which is exactly what got stuck. Backward "
                        "residual edges exist to decrease flow."),
                Opt("2: one unit from each augmentation.",
                    why="The second augmentation used the *reverse* of `2 → 3`, which subtracts."),
            ]),
            MCQ(r"""
All capacities are integers. Can Ford-Fulkerson end with a fractional flow on some edge?
""", [
                Opt("Yes: splitting flow evenly is sometimes needed for the maximum.",
                    why="Some maximum flows split fractionally, but there is always an integral one, "
                        "and augmenting paths find it: see the other answer."),
                Opt("No: every bottleneck is a difference of integers, so every push is an integer.",
                    correct=True,
                    why="Yes. This **integrality** is what makes flow solve matching and assignment "
                        "problems: an edge of capacity 1 then carries exactly 0 or 1."),
                Opt("Only if the capacities are large.",
                    why="The size of the capacities has nothing to do with it: integers minus integers "
                        "stay integers."),
            ]),
        ]),
        Part("When to stop: max flow = min cut", [
            Say(r"""
Ford-Fulkerson stops when no augmenting path exists. Why is the flow then *maximum*, and
not just stuck somewhere else?

A **cut** is a set `S` of vertices with `s ∈ S` and `t ∉ S`. Its capacity is the total
capacity of the edges going from `S` to the rest (edges coming back into `S` do not
count).
"""),
            MCQ(r"""
Why is the value of every flow at most the capacity of every cut?
""", [
                Opt("Each unit leaving `s` has to cross from `S` to the outside at least once more "
                    "than it crosses back, and edges out of `S` carry at most their capacity.",
                    correct=True,
                    why="Yes: the flow value equals (flow out of `S`) − (flow back into `S`) ≤ capacity "
                        "of the edges out of `S`. The source-edges bound from the first question is "
                        "the cut `S = {s}`."),
                Opt("Because the algorithm saturates the cut edges.",
                    why="This holds for *every* flow, not only the algorithm's: it is a statement "
                        "about any flow and any cut."),
                Opt("Because the cut contains the smallest-capacity edge.",
                    why="A cut is any separating set of vertices; it need not contain any particular "
                        "edge."),
            ]),
            Numeric(r"""
In the four-vertex network (all capacities 1), what is the capacity of the cut
`S = {1, 2}`?
""", answer=3,
                hint="Count the edges from {1, 2} to {3, 4}.",
                explain=r"""
`1 → 3`, `2 → 3` and `2 → 4`: capacity 3. The cuts `{1}` and `{1, 2, 3}` have capacity 2,
which matches the maximum flow. Not every cut is tight, but the smallest one always is.
"""),
            Reflect(r"""
When Ford-Fulkerson stops, let `S` be the set of vertices reachable from `s` in the
residual graph (so `t ∉ S`). Why does the flow equal the capacity of this particular cut?
Think about an edge leaving `S` and an edge entering `S`.
""", answer=r"""
An edge `u → v` from `S` to the outside must be full: if it had room, `v` would be
reachable too. An edge `v → u` coming into `S` must carry 0: otherwise the backward
residual edge `u → v` would have room and again `v` would be reachable. So the net flow
across the cut is exactly its capacity. Since no flow exceeds any cut, this flow is
maximum and this cut is minimum: **max flow = min cut**, and the reachable set hands you
the minimum cut for free.
"""),
        ]),
        Part("How many augmentations? Edmonds-Karp and Dinic", [
            Numeric(r"""
Network: `s → a`, `s → b`, `a → t`, `b → t` with capacity 10^9 each, plus `a → b` with
capacity 1. Suppose augmenting paths alternate between `s → a → b → t` and
`s → b → a → t` (the second uses the backward edge of `a → b`). Each pushes 1 unit. How
many augmentations until the maximum flow is reached?
""", answer=2e9, rel=0.1, unit="augmentations",
                explain=r"""
The maximum is 2·10^9 and every augmentation adds 1: 2·10^9 augmentations, each costing a
graph search. Ford-Fulkerson with arbitrary paths is bounded only by the flow value, and
with capacities up to 10^9 that is no bound at all.
"""),
            MCQ(r"""
**Edmonds-Karp** always augments along a *shortest* path (fewest edges), found by BFS.
What does that buy?
""", [
                Opt("Each path has the largest possible bottleneck.",
                    why="That is a different rule ('fattest path'). Shortest paths can have tiny "
                        "bottlenecks; the gain is elsewhere."),
                Opt("The number of augmentations is O(n·m), whatever the capacities.", correct=True,
                    why="Yes. Distances from `s` in the residual graph never decrease, and each edge "
                        "can be the bottleneck only O(n) times, so O(n·m) augmentations of O(m) each: "
                        "O(n·m^2). In the example above, the first BFS takes `s → a → t` directly."),
                Opt("BFS is faster than DFS per search.",
                    why="Both are O(n + m) per search. The gain is in how many searches are needed."),
            ]),
            Say(r"""
**Dinic** goes further. Each *phase* runs one BFS to label every vertex with its distance
`level` from `s`, then pushes flow along every shortest augmenting path at once, using only
edges from level `i` to level `i + 1`, before the next BFS. Shortest paths only get longer,
so there are at most `n` phases: O(n^2·m) in general, and O(m·√n) on unit-capacity
networks like matchings.

In the code, every edge stores the index `rev` of its reverse edge in the other endpoint's
list; `addEdge` creates both at once:

```cpp
struct Edge { int to, rev; long long cap; };
vector<vector<Edge>> adj;
void addEdge(int u, int v, long long c) {
    adj[u].push_back({v, (int)adj[v].size(), c});
    adj[v].push_back({u, (int)adj[u].size() - 1, 0});
}
```
"""),
            Short(r"""
Inside the DFS you push `d` units along `Edge& e = adj[u][i]` with `e.cap -= d;`. What
expression names the reverse edge, whose capacity must go up by `d`?
""", accept=["adj[e.to][e.rev]", "adj[e.to][e.rev].cap"], placeholder="an expression",
                explain=r"""
`adj[e.to][e.rev]`: the reverse edge lives in the list of the vertex the edge points to,
at the position recorded when both were created. Forgetting this line gives a program
that runs and returns the greedy's wrong answer; it passes samples that do not need an
undo. (Another common layout keeps all edges in one array in pairs, so that edge `i`'s
reverse is `i ^ 1`.)
"""),
            Say(r"""
The phase's DFS, from the reference solution:

```cpp
long long dfs(int u, int t, long long f) {
    if (u == t) return f;
    for (int& i = it[u]; i < (int)adj[u].size(); i++) {
        Edge& e = adj[u][i];
        if (e.cap > 0 && level[e.to] == level[u] + 1) {
            long long d = dfs(e.to, t, min(f, e.cap));
            if (d > 0) { e.cap -= d; adj[e.to][e.rev].cap += d; return d; }
        }
    }
    return 0;
}
```

It is called repeatedly from `s` until it returns 0, with `it` reset to 0 at the start of
each phase.
"""),
            MCQ(r"""
Why is the loop variable a *reference* to `it[u]`, which survives from one call to the
next within a phase?
""", [
                Opt("An edge that led nowhere once in this phase leads nowhere for the rest of it, "
                    "so it is skipped for good.", correct=True,
                    why="Yes. Within a phase, a dead end stays dead (levels do not change), so each edge "
                        "is abandoned at most once per phase. Without the pointer, Dinic re-scans dead "
                        "edges on every path and can be far slower."),
                Opt("To save memory.",
                    why="It costs an extra array. The point is not rescanning dead edges."),
                Opt("It is a style choice; a local `int i = 0` behaves the same.",
                    why="It returns the same flow, but re-scanning dead ends on every call is what the "
                        "pointer exists to prevent. On large inputs that is the difference between "
                        "fast and too slow."),
            ]),
            Numeric(r"""
In Download Speed, how large can the answer get? (`m ≤ 1000` links of capacity up to 10^9.)
""", answer=1e12, rel=0.1,
                explain=r"""
At most the sum of all capacities: 1000·10^9 = 10^12. Capacities, the DFS's `f` and the
total must be `long long`. One hidden test sends 498 parallel routes at 10^9 each.
"""),
            Try("download_speed", note="Dinic as above. The second sample is the network where the greedy "
                "gets stuck."),
        ]),
        Part("Reading off the cut", [
            Say(r"""
Police Chase: a town has `n ≤ 500` crossings and `m ≤ 1000` two-way streets. Close as few
streets as possible so that no route leads from crossing 1 to crossing `n`, and print
which ones.

Closing streets is cutting edges: this is a minimum cut, with every street of capacity 1.
Two details remain: how to represent a two-way street, and how to get the cut out of a
max-flow algorithm that only returns a number.
"""),
            MCQ(r"""
How should a two-way street between `a` and `b` enter the flow network?
""", [
                Opt("One edge `a → b` of capacity 1, with its usual empty reverse edge.",
                    why="Then a route that uses the street from `b` to `a` cannot send flow, and the "
                        "maximum flow, and so the cut, can come out too small."),
                Opt("Capacity 1 in each direction: `a → b` and `b → a`.", correct=True,
                    why="Yes. The neat way is one pair of edges that are each other's reverse, both "
                        "starting at capacity 1. The reference's `addEdge` takes an optional fourth "
                        "argument, the reverse edge's starting capacity: `addEdge(a, b, 1, 1)`."),
                Opt("Capacity 2 in one direction, since the street works both ways.",
                    why="Capacity is about how much crosses, not about direction; a one-way edge still "
                        "blocks the other direction entirely."),
            ]),
            MCQ(r"""
After the flow, a classmate prints every street that carries flow. On the chain of
streets `1 – 2 – 3` (n = 3), what goes wrong?
""", [
                Opt("Nothing: those streets are exactly the cut.",
                    why="Both streets carry the one unit of flow, so both would be printed. Closing just "
                        "one of them already separates 1 from 3."),
                Opt("It prints 2 streets, but the minimum is 1.", correct=True,
                    why="Right. Flow passes through edges in series, and all of them are full, but a cut "
                        "needs only one per route. Use the reachable set instead."),
                Opt("It prints 0 streets.",
                    why="The unit of flow uses both streets, so both carry flow."),
            ], explain=r"""
The recipe from the proof: BFS from `s` along edges with positive residual capacity, mark
the reachable set `S`, and print every street with one end in `S` and the other outside.
On the chain, `S = {1}` and the answer is the single street `1 – 2`. By the proof their
number equals the maximum flow, as the problem demands.
"""),
            Try("police_chase", note="Max flow with capacity 1 both ways, then the reachable set. Any "
                "minimum cut is accepted."),
        ]),
        Part("Matching is a flow", [
            Say(r"""
School Dance: `n ≤ 500` boys, `m ≤ 500` girls, and `k ≤ 1000` pairs willing to dance.
Form as many pairs as possible, nobody in two pairs, and print them.

Greedy fails the same way the greedy flow did. Boy 1 is happy with girls 1 and 2, boy 2
only with girl 1. Give boy 1 the first girl on his list and boy 2 stays alone, although 2
pairs were possible.
"""),
            MCQ(r"""
Which network has a maximum flow equal to the maximum number of pairs?
""", [
                Opt("Source → each boy (capacity 1), boy → girl for each willing pair (capacity 1), "
                    "each girl → sink (capacity 1).", correct=True,
                    why="Yes. The capacity 1 into a boy means at most one unit leaves him, so at most "
                        "one pair; the capacity 1 out of a girl does the same for her. By integrality "
                        "the flow is 0 or 1 on every edge."),
                Opt("Boy → girl edges only, with capacity 1, and every boy a source.",
                    why="Flow needs a single source and sink, and without the source edges nothing stops "
                        "a boy from sending units to several girls."),
                Opt("Source → each boy with capacity equal to the number of girls he may dance "
                    "with, then boy → girl (1) and girl → sink (1).",
                    why="Then a boy with three willing partners can send three units: three pairs at "
                        "once. The 1 on the source edge is what limits each boy to one pair."),
            ]),
            Short(r"""
Boys 1, 2; girls 1, 2; boy 1 may dance with girls 1 and 2, boy 2 only with girl 1. The
current matching is boy 1 – girl 1. The augmenting path is `s → boy 2 → girl 1 → boy 1 →
girl 2 → t`, where `girl 1 → boy 1` is a backward edge. After pushing along it, which girl
dances with boy 1?
""", accept=["2", "girl 2"], placeholder="a girl",
                explain=r"""
Girl 2. The backward step cancels boy 1 – girl 1, and the path adds boy 2 – girl 1 and
boy 1 – girl 2. In matching language, an augmenting path alternates between unused and
used pairs, starts at a free boy and ends at a free girl; flipping it adds one pair. The
classic matching algorithm (Kuhn's) is exactly this, one DFS per boy.
"""),
            MCQ(r"""
The flow is computed. How do you print the pairs?
""", [
                Opt("Every boy → girl edge whose residual capacity is now 0.", correct=True,
                    why="Yes: capacity 1, residual 0 means it carries one unit. Record where each such "
                        "edge sits in `adj[boy]` when you create it, then look it up afterwards."),
                Opt("Every boy → girl edge that was ever on an augmenting path.",
                    why="A later path can cancel it (the backward step above did exactly that). Only "
                        "the final flow counts."),
                Opt("Every edge into the sink that is saturated, with its girl's first boy.",
                    why="The saturated sink edges tell you *which* girls dance, but not with whom."),
            ]),
            Try("school_dance", note="Source, boys, girls, sink, capacity 1 everywhere. Any maximum set of "
                "pairs is accepted."),
        ]),
        Part("Bigger networks, other models", [
            Say(r"""
Carpool: `n ≤ 5·10^4` drivers, driver `i` has `c_i` free seats; `m ≤ 5·10^4` riders; `k ≤
10^5` allowed rider-driver pairs. Seat as many riders as possible.

It is School Dance with seats: source → driver `i` with capacity `c_i`, driver → rider
with capacity 1, rider → sink with capacity 1. What changes is the size, and with it the
choice of algorithm.
"""),
            Numeric(r"""
Edmonds-Karp augments one path per BFS. There can be about 5·10^4 augmentations, and each
BFS from the source first queues every driver with a free seat and scans all their edges
before it reaches any rider, about 10^5 edge scans. Roughly how many scans in total?
""", answer=5e9, rel=0.8, unit="edge scans",
                explain=r"""
5·10^4 · 10^5 = 5·10^9: tens of seconds. The reference Dinic needs a few dozen phases on
these tests, each one BFS plus a DFS that looks at every edge at most once more: a few
million steps.
"""),
            MCQ(r"""
Why does one Dinic phase find so many augmenting paths for the price of one BFS?
""", [
                Opt("The level graph stays valid for all shortest paths of the current length, so "
                    "the DFS keeps finding them without a new BFS.", correct=True,
                    why="Yes. The reverse edges created by a push point from level `i + 1` back to level "
                        "`i`, so they never form a new path as short as the current ones: all of them can "
                        "be taken from one set of levels. In the first phase here, that is every "
                        "source → driver → rider → sink path that still fits, in one pass."),
                Opt("Dinic pushes more than one unit per path.",
                    why="On this network every path's bottleneck is 1 (the rider's edge), so each path "
                        "still carries one unit. The saving is in the searching, not the pushing."),
                Opt("Dinic skips the riders that cannot be seated.",
                    why="It does not know which riders those are until the flow is done."),
            ]),
            Try("carpool", note="The same Dinic. Edmonds-Karp times out on the large tests."),
            MCQ(r"""
A variant: find the most routes from 1 to `n` that share no **crossing** (vertex) other
than 1 and `n`. Edges have capacities, vertices do not. What is the standard trick?
""", [
                Opt("Split every vertex `v` into `v_in → v_out` with capacity 1; edges into `v` go to "
                    "`v_in`, edges out of `v` leave from `v_out`.", correct=True,
                    why="Yes. Any vertex capacity becomes an edge capacity this way. With it, vertex "
                        "cuts (the fewest crossings to block) are min cuts too."),
                Opt("Give every edge capacity 1.",
                    why="That gives routes sharing no *street*. Two such routes can still meet at a "
                        "crossing."),
                Opt("Run the flow once per vertex, deleting it.",
                    why="That is n max-flows and still does not model 'each vertex used once'."),
            ]),
            Reflect(r"""
Distinct Routes (CSES 1711) asks for the most routes from 1 to `n` that share no street,
and wants the routes printed, not just counted. With capacity 1 on every street, the max
flow gives the count. How do you turn the final flow into actual routes?
""", answer=r"""
Decompose the flow: every unit-flow edge is used by exactly one route. Start at 1, follow
any outgoing edge that carries flow, mark it used (set its flow to 0), and continue until
reaching `n`; conservation guarantees you can always continue. Repeat once per unit of
flow. Each walk is a route, and no street is used twice because each flow edge is removed
when used. (Cycles of flow may appear in a walk; they can be cut out or left in, depending
on whether the problem requires simple paths.)
"""),
        ]),
    ],
    problems=[DOWNLOAD_SPEED, POLICE_CHASE, SCHOOL_DANCE, CARPOOL],
    cards=[
        Card(r"""The two rules a flow must satisfy?""",
             r"""Capacity: `0 ≤ f(e) ≤ c(e)` on every edge. Conservation: inflow = outflow at every vertex except the source and the sink."""),
        Card(r"""Residual graph of an edge `u → v` with capacity `c` and flow `f`?""",
             r"""Forward `u → v` with room `c − f`, backward `v → u` with room `f`. Pushing along the backward edge cancels flow already sent."""),
        Card(r"""Why does "push along any path with spare capacity" fail without reverse edges?""",
             r"""An early path can block better ones: in `1→2, 1→3, 2→3, 2→4, 3→4` (all 1), taking `1→2→3→4` first gets stuck at 1; the maximum is 2. Reverse edges allow `1→3→2→4`."""),
        Card(r"""Max-flow min-cut: the statement, and how to find a minimum cut?""",
             r"""Maximum flow value = minimum cut capacity. After the flow, BFS from `s` along edges with positive residual capacity; the reachable set `S` gives the cut (edges from `S` to the rest)."""),
        Card(r"""Why is Ford-Fulkerson with arbitrary paths dangerous, and what does Edmonds-Karp guarantee?""",
             r"""Arbitrary paths can each add 1, so up to (flow value) searches, e.g. 2·10^9. BFS shortest paths: O(n·m) augmentations, O(n·m^2) total, independent of capacities."""),
        Card(r"""Dinic in one breath, and its complexity?""",
             r"""Per phase: BFS levels from `s`, then DFS along `level+1` edges with persistent current-edge pointers until blocked. At most n phases: O(n^2·m); O(m·√n) on unit networks such as bipartite matching."""),
        Card(r"""How is the reverse edge stored so that `addEdge` and the DFS can find it in O(1)?""",
             r"""Each edge keeps `rev`, the index of its reverse in `adj[to]`: `adj[u].push_back({v, adj[v].size(), c}); adj[v].push_back({u, adj[u].size()-1, 0});`. (Or: one array of edges in pairs, reverse of `i` is `i ^ 1`.)"""),
        Card(r"""How does a two-way street of capacity `c` enter a flow network?""",
             r"""As a pair of opposite edges, each with capacity `c`, used as each other's reverse (`addEdge(a, b, c, c)`)."""),
        Card(r"""Bipartite matching as flow, and reading the pairs back?""",
             r"""Source → left (1), left → right for each allowed pair (1), right → sink (1). Pairs = left→right edges with residual 0 at the end."""),
        Card(r"""Integrality theorem, and why it matters?""",
             r"""With integer capacities, augmenting paths find an integral maximum flow. So capacity-1 edges carry 0 or 1, and flows read off as matchings, cuts and routes."""),
        Card(r"""Capacity on a vertex, or vertex-disjoint paths?""",
             r"""Split `v` into `v_in → v_out` with the vertex's capacity; incoming edges go to `v_in`, outgoing leave from `v_out`."""),
    ],
)
