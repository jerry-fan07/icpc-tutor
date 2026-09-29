from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _parents(rng, n, shape):
    """par[i] < i for every i >= 1 (0-indexed nodes, node 0 is the root)."""
    if shape == "path":
        return [-1] + list(range(n - 1))
    if shape == "star":
        return [-1] + [0] * (n - 1)
    if shape == "binary":
        return [-1] + [(i - 1) // 2 for i in range(1, n)]
    if shape == "deep":                      # long chains with short side branches
        return [-1] + [rng.randrange(max(0, i - 3), i) for i in range(1, n)]
    if shape == "broom":                     # a long handle, then many leaves at its end
        h = max(1, n // 2)
        return [-1] + [i - 1 if i < h else h - 1 for i in range(1, n)]
    if shape == "caterpillar":               # a spine with leaves hanging off it
        h = max(1, n // 3)
        return [-1] + [i - 1 if i < h else rng.randrange(h) for i in range(1, n)]
    return [-1] + [rng.randrange(i) for i in range(1, n)]


def _labels(rng, n, root_is_one):
    lab = list(range(1, n + 1))
    rng.shuffle(lab)
    if root_is_one:
        k = lab.index(1)
        lab[0], lab[k] = lab[k], lab[0]
    return lab


def _bosses(rng, n, shape, shuffle=True):
    """Subordinates input: n, then the boss of employees 2..n."""
    par = _parents(rng, n, shape)
    lab = _labels(rng, n, True) if shuffle else list(range(1, n + 1))
    boss = [0] * (n + 1)
    for i in range(1, n):
        boss[lab[i]] = lab[par[i]]
    return f"{n}\n" + " ".join(map(str, boss[2:])) + "\n"


def _edges(rng, n, shape):
    """A tree as n, then n - 1 edges in random order and orientation."""
    par = _parents(rng, n, shape)
    lab = _labels(rng, n, False)
    rows = []
    for i in range(1, n):
        a, b = lab[i], lab[par[i]]
        if rng.random() < 0.5:
            a, b = b, a
        rows.append(f"{a} {b}")
    rng.shuffle(rows)
    return f"{n}\n" + "\n".join(rows) + "\n"


SHAPES = ["random", "path", "star", "binary", "deep", "broom", "caterpillar"]


def _small_edges(rng, lo, hi):
    return _edges(rng, rng.randint(lo, hi), rng.choice(SHAPES))


# --------------------------------------------------------------------- problems
SUBORDINATES = Problem(
    id="subordinates",
    title="Subordinates",
    difficulty="easy",
    source="CSES 1674 - Subordinates",
    complexity="O(n)",
    statement=r"""
A company has `n` employees numbered 1 to `n`. Employee 1 is the director; every other
employee has exactly one direct boss, and following bosses upward always ends at the
director.

For every employee, count their subordinates: the employees below them, directly or
indirectly.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n − 1` integers: the direct boss of employees 2, 3, ..., n. A boss
can have any number, larger or smaller than the employee's own.
""",
    output=r"""
Print `n` integers: the number of subordinates of employees 1, 2, ..., n.
""",
    samples=[
        Test("7\n1 1 2 2 4 3\n", "6 3 1 1 0 0 0\n"),
        Test("3\n3 1\n", "2 0 1\n",
             note="Employee 3 is the boss of employee 2. Bosses do not always have smaller numbers."),
    ],
    tests=[
        Test("1\n\n"),
        Test("2\n1\n"),
        Test("6\n5 6 2 1 4\n"),
        Test("5\n1 1 1 1\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _bosses(rng, rng.randint(1, 12), rng.choice(SHAPES)), 16),
        Gen("medium random", lambda rng: _bosses(rng, 3000, rng.choice(SHAPES)), 3),
        Gen("max chain, shuffled labels", lambda rng: _bosses(rng, 200000, "path"), 1, large=True),
        Gen("max deep tree", lambda rng: _bosses(rng, 200000, "deep"), 1, large=True),
        Gen("max random tree", lambda rng: _bosses(rng, 200000, "random"), 1, large=True),
        Gen("max star", lambda rng: _bosses(rng, 200000, "star"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> boss(n + 1, 0);
    vector<vector<int>> reports(n + 1);
    for (int i = 2; i <= n; i++) {
        cin >> boss[i];
        reports[boss[i]].push_back(i);
    }
    // BFS order from the director: every employee appears after their boss
    vector<int> order;
    order.reserve(n);
    order.push_back(1);
    for (int i = 0; i < (int)order.size(); i++)
        for (int c : reports[order[i]]) order.push_back(c);
    // read it backwards: every employee is finished before being added to their boss
    vector<int> sz(n + 1, 1);
    for (int i = n - 1; i >= 1; i--) sz[boss[order[i]]] += sz[order[i]];
    for (int i = 1; i <= n; i++) cout << sz[i] - 1 << (i == n ? '\n' : ' ');
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<int> boss(n + 1, 0);
    for (int i = 2; i <= n; i++) cin >> boss[i];
    for (int u = 1; u <= n; u++) {
        int c = 0;
        for (int v = 1; v <= n; v++) {            // is u a strict ancestor of v?
            int w = boss[v];
            while (w != 0 && w != u) w = boss[w];
            if (w == u) c++;
        }
        cout << c << ' ';
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
    int n;
    cin >> n;
    vector<int> boss(n + 1, 0);
    for (int i = 2; i <= n; i++) cin >> boss[i];
    vector<int> cnt(n + 1, 0);
    for (int i = 2; i <= n; i++)                   // walk up, crediting every boss
        for (int b = boss[i]; b != 0; b = boss[b]) cnt[b]++;
    for (int i = 1; i <= n; i++) cout << cnt[i] << ' ';
    cout << '\n';
}
""",
    hints=[
        r"""An employee's subordinates are their direct reports plus *their* subordinates. If you
knew the answer for every direct report, how would you get the boss's answer?""",
        r"""`size[u] = 1 + sum of size[c]` over direct reports `c`. You need an order in which
every employee comes before their boss. Looping `i = n..2` only works if bosses have
smaller numbers, which is not promised.""",
        r"""BFS from employee 1 lists every employee after their boss. Process that list backwards.""",
    ],
    editorial=r"""
The subtree of `u` is `u` itself plus the disjoint subtrees of its children, so
`size[u] = 1 + Σ size[c]`, and the answer is `size[u] − 1`. Every edge is used once: O(n).

The only requirement is order: children must be finished before their parent. A recursive
DFS gives that (add a child's size after the call returns). Without recursion, BFS from
the root lists every node after its parent, so the reversed BFS list has every node
before its parent.

Two traps. Walking up from each employee costs the sum of all depths, 2·10^10 on a chain.
And the shortcut `for (i = n; i >= 2; i--) sz[boss[i]] += sz[i]` is only right when every
boss has a smaller number than their employees; the second sample and the hidden tests
break that.
""",
)

TREE_DIAMETER = Problem(
    id="tree_diameter",
    title="Tree Diameter",
    difficulty="easy",
    source="CSES 1131 - Tree Diameter",
    complexity="O(n)",
    statement=r"""
You are given a tree with `n` nodes. The diameter of a tree is the largest distance between
two of its nodes, where the distance is the number of edges on the path between them.

Find the diameter.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n − 1` lines has two integers `a b` (1 ≤ a, b ≤ n): an edge between
nodes `a` and `b`. The edges form a tree.
""",
    output=r"""
Print one integer: the diameter.
""",
    samples=[
        Test("5\n1 2\n1 3\n3 4\n3 5\n", "3\n"),
        Test("3\n2 1\n1 3\n", "2\n", note="Node 1 sits in the middle of the longest path."),
    ],
    tests=[
        Test("1\n\n"),
        Test("2\n2 1\n"),
        Test("8\n1 2\n2 3\n3 4\n2 5\n5 6\n6 7\n1 8\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _small_edges(rng, 1, 12), 16),
        Gen("medium random", lambda rng: _edges(rng, 2000, rng.choice(SHAPES)), 3),
        Gen("max random tree", lambda rng: _edges(rng, 200000, "random"), 1, large=True),
        Gen("max path, shuffled", lambda rng: _edges(rng, 200000, "path"), 1, large=True),
        Gen("max caterpillar", lambda rng: _edges(rng, 200000, "caterpillar"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<vector<int>> adj;

// BFS from s; returns the distance of every node
vector<int> bfs(int s) {
    vector<int> d(n + 1, -1);
    vector<int> q = {s};
    d[s] = 0;
    for (int i = 0; i < (int)q.size(); i++) {
        int u = q[i];
        for (int v : adj[u])
            if (d[v] < 0) { d[v] = d[u] + 1; q.push_back(v); }
    }
    return d;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n;
    adj.assign(n + 1, {});
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    vector<int> d1 = bfs(1);
    int a = max_element(d1.begin() + 1, d1.end()) - d1.begin();   // farthest from 1
    vector<int> d2 = bfs(a);                                       // a is an end of a diameter
    cout << *max_element(d2.begin() + 1, d2.end()) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    int best = 0;
    for (int s = 1; s <= n; s++) {                 // BFS from every node
        vector<int> d(n + 1, -1);
        queue<int> q;
        q.push(s);
        d[s] = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            best = max(best, d[u]);
            for (int v : adj[u]) if (d[v] < 0) { d[v] = d[u] + 1; q.push(v); }
        }
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
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    int best = 0;
    vector<int> d(n + 1), q(n);
    for (int s = 1; s <= n; s++) {
        fill(d.begin(), d.end(), -1);
        int head = 0, tail = 0;
        q[tail++] = s;
        d[s] = 0;
        while (head < tail) {
            int u = q[head++];
            best = max(best, d[u]);
            for (int v : adj[u]) if (d[v] < 0) { d[v] = d[u] + 1; q[tail++] = v; }
        }
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""BFS from every node is n BFS runs: 4·10^10 steps. One BFS from node 1 is not enough
either (node 1 may sit in the middle of the longest path). What does that one BFS give you?""",
        r"""The node farthest from *any* start is an end of some longest path. BFS again from it.""",
    ],
    editorial=r"""
Two BFS runs. From any node `s`, find the farthest node `a`; from `a`, find the farthest
node `b`; the answer is `dist(a, b)`. O(n).

Why `a` is an end of a longest path: take a longest path `x–y` and let `c` be the node of
that path closest to `s`. If the route from `s` to `a` passes through `c`, then "a is at
least as far from s as x and y" gives `dist(c, a) ≥ dist(c, x)` and `≥ dist(c, y)`; the
route `c → a` leaves `c` along at most one of the two directions of the path, so for the
other end, say `x`, `dist(a, x) = dist(a, c) + dist(c, x) ≥ dist(c, y) + dist(c, x)`, a
longest path ending at `a`. If the route to `a` branches off before `c`, the same
computation makes `a–x` strictly longer than `x–y`, which is impossible.

The argument needs non-negative edge lengths; with negative weights, two sweeps can
return a wrong answer. An alternative that also generalises: root the tree, and for every
node add up the two largest child heights (+1 each); the maximum is the diameter.
""",
)

TREE_MATCHING = Problem(
    id="tree_matching",
    title="Tree Matching",
    difficulty="medium",
    source="CSES 1130 - Tree Matching",
    complexity="O(n)",
    statement=r"""
You are given a tree with `n` nodes. A matching is a set of edges in which no two edges
share an endpoint.

Find the largest possible number of edges in a matching.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n − 1` lines has two integers `a b`: an edge between nodes `a` and `b`.
The edges form a tree.
""",
    output=r"""
Print one integer: the maximum number of edges in a matching.
""",
    samples=[
        Test("5\n1 2\n1 3\n3 4\n3 5\n", "2\n"),
        Test("4\n1 2\n2 3\n3 4\n", "2\n",
             note="Taking the middle edge 2–3 first blocks both others."),
    ],
    tests=[
        Test("1\n\n"),
        Test("2\n1 2\n"),
        Test("7\n1 2\n1 3\n2 4\n2 5\n3 6\n6 7\n"),
        Test("6\n1 2\n1 3\n1 4\n1 5\n1 6\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _small_edges(rng, 1, 13), 20),
        Gen("max random tree", lambda rng: _edges(rng, 200000, "random"), 1, large=True),
        Gen("max path", lambda rng: _edges(rng, 200000, "path"), 1, large=True),
        Gen("max star", lambda rng: _edges(rng, 200000, "star"), 1, large=True),
        Gen("max broom", lambda rng: _edges(rng, 200000, "broom"), 1, large=True),
        Gen("max deep tree", lambda rng: _edges(rng, 200000, "deep"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    vector<int> par(n + 1, 0), order = {1};
    order.reserve(n);
    for (int i = 0; i < (int)order.size(); i++) {
        int u = order[i];
        for (int v : adj[u])
            if (v != par[u]) { par[v] = u; order.push_back(v); }
    }
    // dp0[u]: best matching inside u's subtree with u left free
    // dp1[u]: best matching inside u's subtree with u matched to one of its children
    const int NEG = -1000000000;
    vector<int> dp0(n + 1, 0), dp1(n + 1, NEG);
    for (int i = n - 1; i >= 0; i--) {              // children before parents
        int u = order[i];
        int bestGain = NEG;
        for (int c : adj[u]) {
            if (c == par[u]) continue;
            int free = max(dp0[c], dp1[c]);
            dp0[u] += free;
            bestGain = max(bestGain, dp0[c] + 1 - free);   // what matching u–c changes
        }
        if (bestGain > NEG) dp1[u] = dp0[u] + bestGain;
    }
    cout << max(dp0[1], dp1[1]) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<pair<int,int>> e(n - 1);
    for (auto& [a, b] : e) cin >> a >> b;
    int m = n - 1, best = 0;
    for (int mask = 0; mask < (1 << m); mask++) {  // every set of edges
        vector<int> used(n + 1, 0);
        bool ok = true;
        for (int k = 0; k < m && ok; k++)
            if (mask >> k & 1) {
                auto [a, b] = e[k];
                if (used[a] || used[b]) ok = false;
                used[a] = used[b] = 1;
            }
        if (ok) best = max(best, __builtin_popcount(mask));
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
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    vector<int> par(n + 1, 0), order = {1};
    for (int i = 0; i < (int)order.size(); i++) {
        int u = order[i];
        for (int v : adj[u]) if (v != par[u]) { par[v] = u; order.push_back(v); }
    }
    const int NEG = -1000000000;
    vector<int> dp0(n + 1, 0), dp1(n + 1, NEG);
    for (int i = n - 1; i >= 0; i--) {
        int u = order[i];
        for (int c : adj[u]) if (c != par[u]) dp0[u] += max(dp0[c], dp1[c]);
        for (int c : adj[u]) {                     // every candidate partner...
            if (c == par[u]) continue;
            int total = dp0[c] + 1;
            for (int d : adj[u])                   // ...re-adds all the other children
                if (d != par[u] && d != c) total += max(dp0[d], dp1[d]);
            dp1[u] = max(dp1[u], total);
        }
    }
    cout << max(dp0[1], dp1[1]) << '\n';
}
""",
    hints=[
        r"""Grabbing any free edge is wrong: on the path 1–2–3–4, taking 2–3 first leaves nothing.
Root the tree. What does a node need to know about a child's subtree to decide whether to
match itself with that child?""",
        r"""Only whether the child is already matched inside its own subtree. Keep two values per
node: `dp0[u]` (u free) and `dp1[u]` (u matched to a child).""",
        r"""`dp0[u] = Σ max(dp0[c], dp1[c])`. For `dp1[u]`, pick the child `c` that loses the least:
`dp0[u] − max(dp0[c], dp1[c]) + dp0[c] + 1`. Compute it in one pass over the children.""",
    ],
    editorial=r"""
Root the tree at 1. For each node keep two numbers about its subtree:
`dp0[u]`, the largest matching with `u` unmatched, and `dp1[u]`, the largest with `u`
matched to one of its children. The parent of `u` only cares which of the two situations
it is in, so nothing else about the subtree needs remembering.

- `dp0[u] = Σ max(dp0[c], dp1[c])`: the children's subtrees are independent.
- `dp1[u] = max over c of dp0[u] − max(dp0[c], dp1[c]) + dp0[c] + 1`: match `u` with
  `c`, which forces `c` to be free inside its subtree.

The answer is `max(dp0[1], dp1[1])`. Process nodes children-first (reversed BFS order).
Computing each candidate for `dp1[u]` by re-summing the other children is O(deg^2) per
node, 4·10^10 on a star; the "total minus my own term" form keeps it O(n).

A greedy also works: process nodes children-first and match a node with its parent
whenever both are still free (an exchange argument shows some maximum matching uses the
edge from a leaf to its parent).
""",
)

TREE_DISTANCES_2 = Problem(
    id="tree_distances_2",
    title="Tree Distances II",
    difficulty="medium",
    source="CSES 1133 - Tree Distances II",
    complexity="O(n)",
    statement=r"""
You are given a tree with `n` nodes. For every node, compute the sum of its distances to
all other nodes (distance = number of edges on the path).
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n − 1` lines has two integers `a b`: an edge between nodes `a` and `b`.
The edges form a tree.
""",
    output=r"""
Print `n` integers: the sums for nodes 1, 2, ..., n.
""",
    samples=[
        Test("5\n1 2\n2 3\n2 4\n4 5\n", "8 5 8 6 9\n"),
    ],
    tests=[
        Test("1\n\n"),
        Test("2\n2 1\n"),
        Test("4\n1 2\n1 3\n1 4\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _small_edges(rng, 1, 12), 16),
        Gen("medium random", lambda rng: _edges(rng, 2000, rng.choice(SHAPES)), 3),
        Gen("max path (answers past 2^31)", lambda rng: _edges(rng, 200000, "path"), 1, large=True),
        Gen("max random tree", lambda rng: _edges(rng, 200000, "random"), 1, large=True),
        Gen("max broom", lambda rng: _edges(rng, 200000, "broom"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    vector<int> par(n + 1, 0), depth(n + 1, 0), order = {1};
    order.reserve(n);
    for (int i = 0; i < (int)order.size(); i++) {
        int u = order[i];
        for (int v : adj[u])
            if (v != par[u]) { par[v] = u; depth[v] = depth[u] + 1; order.push_back(v); }
    }
    // pass 1, children first: subtree sizes
    vector<long long> sz(n + 1, 1);
    for (int i = n - 1; i >= 1; i--) sz[par[order[i]]] += sz[order[i]];
    // the answer for the root is the sum of all depths
    vector<long long> ans(n + 1, 0);
    for (int v = 1; v <= n; v++) ans[1] += depth[v];
    // pass 2, parents first: moving the root from par[v] to v brings sz[v] nodes
    // one step closer and pushes the other n - sz[v] one step away
    for (int i = 1; i < n; i++) {
        int v = order[i];
        ans[v] = ans[par[v]] - sz[v] + (n - sz[v]);
    }
    for (int v = 1; v <= n; v++) cout << ans[v] << (v == n ? '\n' : ' ');
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    for (int s = 1; s <= n; s++) {
        vector<int> d(n + 1, -1);
        queue<int> q;
        q.push(s);
        d[s] = 0;
        long long sum = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            sum += d[u];
            for (int v : adj[u]) if (d[v] < 0) { d[v] = d[u] + 1; q.push(v); }
        }
        cout << sum << ' ';
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
    int n;
    cin >> n;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    vector<int> d(n + 1), q(n);
    for (int s = 1; s <= n; s++) {                 // one BFS per node
        fill(d.begin(), d.end(), -1);
        int head = 0, tail = 0;
        q[tail++] = s;
        d[s] = 0;
        long long sum = 0;
        while (head < tail) {
            int u = q[head++];
            sum += d[u];
            for (int v : adj[u]) if (d[v] < 0) { d[v] = d[u] + 1; q[tail++] = v; }
        }
        cout << sum << ' ';
    }
    cout << '\n';
}
""",
    hints=[
        r"""The answer for one root is the sum of the depths: one BFS. Doing that from every node
is 4·10^10 steps. Move the root one edge instead: what changes?""",
        r"""Moving the root from `u` to its child `v`: the `sz[v]` nodes in v's subtree get one step
closer, the other `n − sz[v]` one step farther. So `ans[v] = ans[u] + n − 2·sz[v]`.""",
        r"""On a path of 2·10^5 nodes the endpoint's sum is about 2·10^10: `long long`.""",
    ],
    editorial=r"""
Rerooting. Root the tree at 1 and compute subtree sizes (children first). The answer for
node 1 is the sum of all depths. Now move the root across one edge, from `u` to its child
`v`: every node in v's subtree gets one step closer (`sz[v]` of them), every other node one
step farther (`n − sz[v]`), so

```
ans[v] = ans[u] − sz[v] + (n − sz[v])
```

Fill `ans` parents first (BFS order). Two linear passes, O(n), instead of one BFS per
node, O(n^2) = 4·10^10.

The sums reach `n(n − 1)/2 ≈ 2·10^10` on a path, past the 2.1·10^9 an `int` holds.
""",
)

TREE_DISTANCES_1 = Problem(
    id="tree_distances_1",
    title="Tree Distances I",
    difficulty="medium",
    source="CSES 1132 - Tree Distances I",
    complexity="O(n)",
    statement=r"""
You are given a tree with `n` nodes. For every node, find the largest distance from it to
any other node (distance = number of edges on the path).
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n − 1` lines has two integers `a b`: an edge between nodes `a` and `b`.
The edges form a tree.
""",
    output=r"""
Print `n` integers: the largest distance from nodes 1, 2, ..., n.
""",
    samples=[
        Test("5\n1 2\n2 3\n2 4\n4 5\n", "3 2 3 2 3\n"),
    ],
    tests=[
        Test("1\n\n"),
        Test("2\n1 2\n"),
        Test("6\n1 2\n1 3\n1 4\n4 5\n4 6\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _small_edges(rng, 1, 12), 16),
        Gen("medium random", lambda rng: _edges(rng, 2000, rng.choice(SHAPES)), 3),
        Gen("max random tree", lambda rng: _edges(rng, 200000, "random"), 1, large=True),
        Gen("max path", lambda rng: _edges(rng, 200000, "path"), 1, large=True),
        Gen("max caterpillar", lambda rng: _edges(rng, 200000, "caterpillar"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<vector<int>> adj;

vector<int> bfs(int s) {
    vector<int> d(n + 1, -1);
    vector<int> q = {s};
    d[s] = 0;
    for (int i = 0; i < (int)q.size(); i++) {
        int u = q[i];
        for (int v : adj[u])
            if (d[v] < 0) { d[v] = d[u] + 1; q.push_back(v); }
    }
    return d;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n;
    adj.assign(n + 1, {});
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    vector<int> d1 = bfs(1);
    int a = max_element(d1.begin() + 1, d1.end()) - d1.begin();   // one end of a diameter
    vector<int> da = bfs(a);
    int b = max_element(da.begin() + 1, da.end()) - da.begin();   // the other end
    vector<int> db = bfs(b);
    // the farthest node from any v is one of the two diameter ends
    for (int v = 1; v <= n; v++) cout << max(da[v], db[v]) << (v == n ? '\n' : ' ');
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    for (int s = 1; s <= n; s++) {
        vector<int> d(n + 1, -1);
        queue<int> q;
        q.push(s);
        d[s] = 0;
        int far = 0;
        while (!q.empty()) {
            int u = q.front(); q.pop();
            far = max(far, d[u]);
            for (int v : adj[u]) if (d[v] < 0) { d[v] = d[u] + 1; q.push(v); }
        }
        cout << far << ' ';
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
    int n;
    cin >> n;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    vector<int> d(n + 1), q(n);
    for (int s = 1; s <= n; s++) {
        fill(d.begin(), d.end(), -1);
        int head = 0, tail = 0, far = 0;
        q[tail++] = s;
        d[s] = 0;
        while (head < tail) {
            int u = q[head++];
            far = max(far, d[u]);
            for (int v : adj[u]) if (d[v] < 0) { d[v] = d[u] + 1; q[tail++] = v; }
        }
        cout << far << ' ';
    }
    cout << '\n';
}
""",
    hints=[
        r"""The subtraction trick of Tree Distances II does not work for a maximum. What did the
diameter lesson say about the farthest node from any start?""",
        r"""Find the two ends `a`, `b` of a diameter (two BFS). The farthest node from any `v` is
`a` or `b`: answer `max(dist(a, v), dist(b, v))`, one more BFS.""",
        r"""Or reroot with the two largest child heights per node: when the root moves to child `v`,
the best path from `u` that avoids `v` uses the largest height not coming from `v`.""",
    ],
    editorial=r"""
Let `a–b` be a diameter (found by two BFS). For every node `v`, the farthest node from `v`
is `a` or `b`, so the answer is `max(dist(a, v), dist(b, v))`: three BFS runs, O(n).

Why: any node `w` hangs off the path `a–b` at some node `c'`. It cannot hang deeper than
the shorter end of the path at `c'`, `dist(c', w) ≤ min(dist(c', a), dist(c', b))`,
otherwise replacing that end by `w` would give a longer path than the diameter. So walking
from `v` to `w` is never longer than walking from `v` to whichever of `a`, `b` lies beyond
`c'`.

Rerooting also works, but not with a subtraction: a maximum has no inverse. Keep the two
largest child heights of every node, so that when the root moves from `u` to `v` you know
the longest path out of `u` that does not go through `v`.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo13",
    title="trees: traversal & tree DP",
    track="algo",
    order=13,
    summary="Root a tree and let every node answer from its children: subtree sizes, "
            "children-first orders without recursion, the diameter by two BFS, DP on trees, "
            "and rerooting to get an answer for every root at once.",
    prereqs=["algo09", "algo06"],
    tags=["trees", "subtree size", "diameter", "tree dp", "rerooting", "bfs order",
          "iterative dfs"],
    parts=[
        Part("One answer per node", [
            Say(r"""
A company has `n ≤ 2·10^5` employees. Employee 1 is the director; for every other employee
you are told their direct boss. For **every** employee, count their subordinates: everyone
below them, directly or indirectly. One second.

This is a **rooted tree**: every node except the root has exactly one parent, and following
parents always reaches the root. So there are `n − 1` edges, no cycles, and exactly one
path between any two nodes. The **subtree** of `u` is `u` together with everyone below it.

The first idea that comes to mind: every employee walks up the chain of bosses to the
director and adds 1 to each boss on the way. Each boss is credited once per subordinate,
so it is correct.
"""),
            MCQ(r"""
Which company makes walking up the most expensive?
""", [
                Opt("A star: the director manages everyone directly.",
                    why="Every walk is a single step, `n − 1` steps in all. That is the cheapest "
                        "shape, not the most expensive."),
                Opt("A company where everyone's boss is a random earlier employee.",
                    why="In trees built like this a typical employee is only about ln n ≈ 12 levels "
                        "deep, so the total is a few million steps. Random tests are the ones naive tree "
                        "code survives."),
                Opt("A chain: 1 is the boss of 2, who is the boss of 3, and so on.", correct=True,
                    why="Yes. Employee `i` sits at depth `i − 1`, so its walk takes `i − 1` steps. "
                        "The total is the sum of all depths, and a chain maximises it."),
                Opt("A complete binary tree.",
                    why="Its depth is log2 n ≈ 17, so each walk is at most 17 steps: about 3·10^6 "
                        "in total."),
            ]),
            Numeric(r"""
On a chain with `n = 2·10^5`, roughly how many steps does walking up take in total?
""", answer=2e10, rel=0.5, unit="steps",
                hint="Employee `i` walks `i − 1` steps. Add them up.",
                explain=r"""
`0 + 1 + ... + (n − 1) = n(n − 1)/2 ≈ 2·10^10`, 20 to 200 times what fits in a
second. Judges put a chain (a "bamboo") in the tests of nearly every tree problem for
exactly this reason: on random trees the naive code looks fast.
"""),
            Reflect(r"""
Take an employee `u` with direct reports `c1, c2, c3`. How does `u`'s answer relate to
theirs? What is the walk-up approach doing over and over?
""", answer=r"""
Everyone below `u` is below exactly one of `c1, c2, c3` (or is one of them), so
`size[u] = 1 + size[c1] + size[c2] + size[c3]`, where `size` counts the subtree including
its root. The walk-up approach recounts every subtree from scratch: an employee at depth
10 is re-added separately to all 10 bosses above them. Computing sizes from the children's
sizes uses each edge once: O(n).
"""),
            Say(r"""
That recurrence, `size[u] = 1 + Σ size[c]` over the children `c`, is the simplest example
of **DP on a tree**: a node's value is built from its children's values. The answer to
the problem is `size[u] − 1`.

The one requirement is order: when you compute `size[u]`, every child must already be
done. A recursive DFS gives that order for free:

```cpp
vector<vector<int>> children;   // children[u] = direct reports of u
vector<int> sz;

void dfs(int u) {
    sz[u] = 1;
    for (int c : children[u]) {
        dfs(c);                 // c's whole subtree is finished when this returns
        sz[u] += sz[c];
    }
}
```
"""),
            Short(r"""
The bosses of employees 2..7 are `1 1 2 2 4 3` (so 2 and 3 report to 1, 4 and 5 to 2, 6
to 4, 7 to 3). Give the number of subordinates of employees 1 to 7, separated by spaces.
""", accept=["6 3 1 1 0 0 0", "6, 3, 1, 1, 0, 0, 0"], placeholder="seven numbers",
                hint="Start from the employees nobody reports to (0 each) and work upward.",
                explain=r"""
Leaves 5, 6, 7 have size 1. Then `size[4] = 1 + size[6] = 2`, `size[3] = 1 + size[7] = 2`,
`size[2] = 1 + size[4] + size[5] = 4`, `size[1] = 1 + 4 + 2 = 7`. Subtract 1 each:
`6 3 1 1 0 0 0`.
"""),
        ]),
        Part("Children first, without recursion", [
            MCQ(r"""
A shortcut that skips building the tree: set every `sz[i] = 1`, then run
`for (int i = n; i >= 2; i--) sz[boss[i]] += sz[i];`. When is this right?
""", [
                Opt("Always: every employee is added to their boss exactly once.",
                    why="Once, yes, but possibly before their own subordinates were added to them. "
                        "With `n = 3`, `boss[2] = 3`, `boss[3] = 1`: `i = 3` adds `sz[3] = 1` to "
                        "`sz[1]`, and only then does `i = 2` add 1 to `sz[3]`. `sz[1]` ends at 2, "
                        "not 3."),
                Opt("Never.",
                    why="It is right whenever every boss has a smaller number than their employees, "
                        "which is how many sample inputs happen to look. That is exactly why this "
                        "bug passes the samples."),
                Opt("Only when every boss has a smaller number than their employees.", correct=True,
                    why="Yes. Then all of `i`'s reports have larger numbers and were finished before "
                        "`i`. Unless the statement promises `boss[i] < i`, the hidden tests will "
                        "shuffle the labels."),
                Opt("Only when the tree is a path.",
                    why="The counterexample (`boss[2] = 3`, `boss[3] = 1`) is a path. What matters is "
                        "the order of the labels, not the shape."),
            ]),
            Numeric(r"""
The recursive `dfs` goes as deep as the tree. Suppose each call's stack frame takes 100
bytes. How many bytes of stack does a chain of 2·10^5 employees need?
""", answer=2e7, rel=0.3, unit="bytes",
                explain=r"""
`2·10^5 · 100 = 2·10^7` bytes, 20 MB. A default Linux stack is 8 MB (Windows: 1 MB), so on
a machine with default settings the recursion dies with a segmentation fault on the chain
test. Many contest judges raise the stack limit (this site gives 512 MB), but not all do,
and a crash on your own machine while testing wastes contest time. Know the iterative
version too.
"""),
            MCQ(r"""
BFS from the root visits every node after its parent (a node is discovered *from* its
parent). In which order should you process a BFS list to compute `sz`?
""", [
                Opt("Front to back.",
                    why="Then every parent comes before its children, whose sizes are not ready yet."),
                Opt("By label, from `n` down to 1.",
                    why="That is the shortcut above: correct only when parents have smaller labels."),
                Opt("Any order, recomputing every `sz[u] = 1 + Σ sz[c]` in rounds until nothing "
                    "changes.",
                    why="It converges eventually, but can need as many rounds as the tree is deep: "
                        "O(n^2) on a chain."),
                Opt("Back to front.", correct=True,
                    why="Yes. Reversed, every node comes before its parent, so when `sz[u]` is added "
                        "to its parent, u's subtree is complete."),
            ], explain=r"""
Any order in which parents come before children works when reversed. BFS order is the
easiest to build without recursion. (A true DFS order, where each subtree is contiguous,
matters in algo14; for sizes and most tree DPs, BFS order is enough.)
"""),
            Say(r"""
Most tree problems give the tree as `n − 1` undirected edges and let you pick the root.
Here is the whole iterative template: root at 1, record parents, list nodes in BFS order,
then do the children-first pass.

```cpp
vector<vector<int>> adj(n + 1);          // undirected edges, both directions
// ... read the edges ...
vector<int> par(n + 1, 0), order = {1};
order.reserve(n);
for (int i = 0; i < (int)order.size(); i++) {   // the list is the queue
    int u = order[i];
    for (int v : adj[u])
        if (v != par[u]) { par[v] = u; order.push_back(v); }
}
vector<int> sz(n + 1, 1);
for (int i = n - 1; i >= 1; i--) sz[par[order[i]]] += sz[order[i]];
```
"""),
            MCQ(r"""
BFS in a general graph needs a `visited` array (algo09). This one only checks
`v != par[u]`. Why is that enough in a tree?
""", [
                Opt("Because `par[1] = 0` and 0 is not a node.",
                    why="That is why the root needs no special case, but it does not explain why no "
                        "other visited node ever shows up as a neighbour."),
                Opt("It is not enough: without `visited` the loop can run forever.",
                    why="It would in a graph with cycles. In a tree, try to find a second visited "
                        "neighbour of `u`: it would give two different routes from the root to `u`."),
                Opt("In a tree, the only neighbour of `u` discovered before `u` is its parent.",
                    correct=True,
                    why="Yes. Any other neighbour already visited would close a cycle. So the parent "
                        "check replaces the visited array, and it costs no extra memory."),
            ], explain=r"""
Forgetting the check is a different story: then `u` pushes its parent again, the parent
pushes `u` again, and `order` grows until memory runs out.
"""),
            Try("subordinates", note="Bosses can have larger numbers than their employees. The "
                "hidden tests include a 2·10^5 chain."),
        ]),
        Part("The longest path", [
            Say(r"""
New problem. A tree of `n ≤ 2·10^5` nodes is given as an edge list. Its **diameter** is the
largest distance (in edges) between two nodes. Find it.

The brute force is to BFS from every node and take the largest distance seen.
"""),
            Numeric(r"""
How many steps does BFS from every node take, for `n = 2·10^5`?
""", answer=4e10, rel=0.5, unit="steps",
                explain=r"""
`n` runs of O(n) each: `n^2 = 4·10^10`. Every BFS rediscovers the whole tree.
"""),
            MCQ(r"""
A cheaper idea: BFS once from node 1 and report the largest distance found. Is that the
diameter?
""", [
                Opt("Yes: the farthest node from 1 is at the end of a longest path.",
                    why="The first half is true (it is the key fact of this part), but the distance "
                        "*from 1* is not the diameter unless 1 happens to be the other end."),
                Opt("No: node 1 may sit in the middle of the longest path.", correct=True,
                    why="Right. On the path 2–1–3, BFS from 1 reports 1, while the diameter 2–3 has "
                        "length 2."),
                Opt("Yes, if you first root the tree at 1.",
                    why="Rooting is bookkeeping: it does not change any distance."),
            ]),
            Say(r"""
The fix costs one more BFS. From any node `s`, find the farthest node `a`. Then BFS from
`a` and find the farthest node `b`. The diameter is `dist(a, b)`.

Everything rests on one claim: **the farthest node from any start is an end of some
longest path.** Once `a` is an end of a longest path, the farthest node from `a` is the
other end.
"""),
            Reflect(r"""
Prove the claim in the main case. Take a longest path `x–y`, and let `c` be the node of
that path closest to `s`, so the routes from `s` to `x` and to `y` both pass through `c`.
Suppose the route from `s` to `a` also passes through `c`. Using "a is at least as far from
`s` as `x` and `y` are", show that `a–x` or `a–y` is a longest path too.
""", answer=r"""
All three routes from `s` pass through `c`, so subtract `dist(s, c)` from each:
`dist(c, a) ≥ dist(c, x)` and `dist(c, a) ≥ dist(c, y)`. The route from `c` to `a` leaves
`c` along at most one of the two directions of the path `x–y`; say it does not share an
edge with `c → x`. Then `dist(a, x) = dist(a, c) + dist(c, x) ≥ dist(c, y) + dist(c, x) =
dist(x, y)`. So `a–x` is at least as long as a longest path, hence a longest path, and `a`
is its end. (If the route to `a` branches off before `c`, the same computation makes
`a–x` strictly longer than `x–y`: impossible.)
"""),
            Short(r"""
The tree has edges `1-2, 2-3, 3-4, 2-5, 5-6, 6-7, 1-8`. BFS from node 1: which node is
farthest?
""", accept=["7"], placeholder="a node",
                explain=r"""
Distances from 1: `2, 8` at 1; `3, 5` at 2; `4, 6` at 3; `7` at 4. So `a = 7`.
"""),
            Numeric(r"""
Now BFS from 7. What is the diameter?
""", answer=5,
                explain=r"""
From 7: `6` at 1, `5` at 2, `2` at 3, `1, 3` at 4, `4, 8` at 5. The farthest nodes, 4 and 8,
are both at distance 5 (ties do not matter: either is an end of a longest path). The path
7–6–5–2–3–4 has 5 edges.
"""),
            MCQ(r"""
Edge lengths can be weights; the BFS then becomes a DFS that adds up weights. Does the
two-sweep trick survive negative weights? Try the tree `s–c` (−100), `c–A` (5), `c–B` (5).
""", [
                Opt("Yes: the proof never looked at the weights.",
                    why="It did, in the branching case: a detour of negative length can make a route "
                        "shorter rather than longer."),
                Opt("No: every node is at negative distance from `s`, so the first sweep picks `s` "
                    "itself, and the second finds 0 while `A–B` has length 10.", correct=True,
                    why="Right. The proof needs non-negative lengths. With negative weights, use the "
                        "DP of the next part instead, which only compares sums."),
                Opt("Yes, if you start from a leaf.",
                    why="`s` is a leaf here, and the answer is still wrong."),
            ]),
            Try("tree_diameter"),
        ]),
        Part("DP on trees", [
            Say(r"""
There is a second way to find the diameter, and it generalises. Root the tree. Every path
has exactly one **highest** node (closest to the root). The longest path whose highest
node is `u` goes down into at most two different child subtrees, as deep as possible in
each.

So give every node its **height** `h[u]`, the number of edges down to the deepest node of
its subtree (`h = 0` for a leaf, `h[u] = 1 + max h[c]` otherwise). The best path with top
`u` is the sum of the two largest `h[c] + 1` over the children. The diameter is the best
over all `u`, and the whole thing is one children-first pass.
"""),
            Numeric(r"""
Same tree as before (`1-2, 2-3, 3-4, 2-5, 5-6, 6-7, 1-8`), rooted at 1. Node 2 has children
3 (height 1) and 5 (height 2). What is the longest path whose highest node is 2?
""", answer=5,
                explain=r"""
`(1 + 1) + (2 + 1) = 5`: down through 3 to 4, and down through 5, 6 to 7. It matches the
two-BFS answer. Unlike two sweeps, it only adds and compares, so it also works with negative
weights, provided a branch is used only when it adds a positive amount (a path may stop
at `u`).
"""),
            Say(r"""
That is the pattern: each node keeps a small summary of its subtree, built from its
children's summaries. The art is choosing the summary.

New problem, **Tree Matching**: choose as many edges as possible so that no two chosen
edges share a node. `n ≤ 2·10^5`.
"""),
            MCQ(r"""
Why not repeatedly take any edge whose two ends are both still free?
""", [
                Opt("It is correct: a matching you cannot extend is a largest one.",
                    why="Being unable to extend (maximal) is not the same as being largest "
                        "(maximum). See the path below."),
                Opt("It is correct if you take the edges in input order.",
                    why="The input may list 2–3 first on the path 1–2–3–4."),
                Opt("On the path 1–2–3–4, taking 2–3 first blocks both other edges: 1 instead of 2.",
                    correct=True,
                    why="Right. The choice at one edge constrains its neighbours, and a careless "
                        "greedy choice cannot be undone."),
            ]),
            Reflect(r"""
Root the tree. Node `u` wants to combine the best matchings of its children's subtrees.
Out of everything about a child's subtree solution, what is the only fact `u` cares about?
""", answer=r"""
Whether the child `c` itself is already used by a matching edge inside its subtree. If it
is, `u` cannot be matched with `c`; if it is not, `u` may take the edge `u–c`. Nothing
deeper in the subtree can interact with `u`. So keep two numbers per node: `dp0[u]`, the
best matching in u's subtree with `u` free, and `dp1[u]`, the best with `u` matched to one
of its children.
"""),
            Short(r"""
If `u` stays free, each child's subtree is independent and can do whatever is best. Fill
in: `dp0[u] = Σ over children c of ____`
""", accept=["max(dp0[c], dp1[c])", "max(dp0[c],dp1[c])", "max(dp1[c], dp0[c])",
             "max(dp1[c],dp0[c])"],
                placeholder="an expression in dp0[c], dp1[c]",
                explain=r"""
`max(dp0[c], dp1[c])`: whether `c` is matched below or not does not matter to a free `u`.
"""),
            MCQ(r"""
Which formula gives `dp1[u]` (u matched to exactly one child)?
""", [
                Opt("`dp0[u] + 1`",
                    why="It assumes the chosen child `c` was free anyway. If the best solution for c's "
                        "subtree used `c` (`dp1[c] > dp0[c]`), matching `u–c` forces c's subtree down "
                        "to `dp0[c]`."),
                Opt("`max over c of dp0[u] − max(dp0[c], dp1[c]) + dp0[c] + 1`", correct=True,
                    why="Yes: start from the free total, swap c's contribution for the version where "
                        "`c` is free, and add the edge `u–c`. Try every child."),
                Opt("`Σ dp0[c] + 1`",
                    why="Only the partner `c` must be free. The other children can still be matched "
                        "inside their own subtrees."),
            ]),
            Short(r"""
Tree rooted at 1: 1 has children 2 and 3; 2 has children 4 and 5; 3 has child 6; 6 has
child 7. Leaves have `dp0 = 0` and no `dp1` (−∞). Give `dp0[1]` and `dp1[1]`, separated by a
space.
""", accept=["2 3", "2, 3", "(2, 3)"], placeholder="two numbers",
                hint="Work up: node 6 first, then 3, then 2, then 1.",
                explain=r"""
`dp[6] = (0, 1)` (match 6–7). `dp[3] = (max(0,1), 1 − 1 + 0 + 1) = (1, 1)`.
`dp[2] = (0, 1)`. At the root, `dp0[1] = max(0,1) + max(1,1) = 2`, and `dp1[1]` is the
better of partner 2 (`2 − 1 + 0 + 1 = 2`) and partner 3 (`2 − 1 + 1 + 1 = 3`): 3. The
answer is 3, for example `1–3, 6–7, 2–4`.
"""),
            MCQ(r"""
You code `dp1[u]` by looping over each candidate partner `c`, and inside, re-adding
`max(dp0, dp1)` of all the other children. What does that cost on a star with 2·10^5
leaves?
""", [
                Opt("O(n): each edge is still looked at once.",
                    why="Each edge is looked at once *per candidate partner*: the centre has 2·10^5 "
                        "candidates and re-adds 2·10^5 terms for each."),
                Opt("O(n^2) = 4·10^10: TLE on the star test.", correct=True,
                    why="Right. Use the total: `dp0[u]` already is the sum, so the candidate for `c` is "
                        "`dp0[u] − max(dp0[c], dp1[c]) + dp0[c] + 1`, O(1) each."),
                Opt("O(n log n), because the tree has depth log n.",
                    why="A star has depth 1, and depth is not what costs here: the degree of one node "
                        "is."),
            ], explain=r"""
Stars punish per-node work that is quadratic in the degree, the way chains punish work
that is linear in the depth. Tree tests contain both.
"""),
            Try("tree_matching", note="Two values per node, children first. Watch the star."),
        ]),
        Part("Every node as the root", [
            Say(r"""
**Tree Distances II**: for every node of a tree with `n ≤ 2·10^5` nodes, print the sum of
its distances to all other nodes.

For one root this is easy: the sum of the depths. For every root, the brute force is `n`
BFS runs, 4·10^10 steps again. And before any algorithm: check the size of the answer.
"""),
            Numeric(r"""
How large can one answer get? Take the end of a path of `n = 2·10^5` nodes.
""", answer=2e10, rel=0.3,
                explain=r"""
`0 + 1 + ... + (n − 1) = n(n − 1)/2 ≈ 2·10^10`, far past the 2.1·10^9 of an `int`. Answers
and subtree-size products go in `long long`.
"""),
            Reflect(r"""
You know the answer with the root at `u`. Move the root across one edge to a child `v`.
Which distances change, and by how much? Write `ans[v]` in terms of `ans[u]`, `sz[v]`
(the size of v's subtree when rooted at 1) and `n`.
""", answer=r"""
Every node in v's subtree gets one step closer (its path to `v` no longer detours through
`u`): `sz[v]` nodes, −1 each. Every other node gets one step farther (its path now has to
go through `u` and then take the edge to `v`): `n − sz[v]` nodes, +1 each. So
`ans[v] = ans[u] − sz[v] + (n − sz[v]) = ans[u] + n − 2·sz[v]`. This is **rerooting**: move
the root one edge and account for what changes, instead of recomputing.
"""),
            Short(r"""
Tree: `1-2, 2-3, 2-4, 4-5`. Rooted at 1, the depths are `0 1 2 2 3`, so `ans[1] = 8`, and
the subtree sizes are `5 4 1 2 1`. Give `ans[1..5]`, separated by spaces.
""", accept=["8 5 8 6 9", "8, 5, 8, 6, 9"], placeholder="five numbers",
                hint="`ans[2] = ans[1] + 5 − 2·4`. Then go from 2 to its children 3 and 4, and from 4 to 5.",
                explain=r"""
`ans[2] = 8 + 5 − 8 = 5`, `ans[3] = 5 + 5 − 2 = 8`, `ans[4] = 5 + 5 − 4 = 6`,
`ans[5] = 6 + 5 − 2 = 9`. Check one directly: from 5, the distances are 1 (to 4), 2 (to 2),
3 (to 1 and 3): 9.
"""),
            MCQ(r"""
The algorithm has two passes: sizes children-first, then `ans` from parent to child. In
what order does the second pass visit the nodes?
""", [
                Opt("Reversed BFS order, like the sizes.",
                    why="That visits a child before its parent, whose `ans` is not known yet."),
                Opt("BFS order, front to back.", correct=True,
                    why="Yes: `ans[v]` needs `ans[par[v]]`, so parents first. This down-then-up "
                        "shape (a children-first pass, then a parents-first pass) is every "
                        "rerooting solution."),
                Opt("Any order: `ans[v]` only depends on `sz[v]`.",
                    why="It also depends on `ans[par[v]]`."),
            ]),
            Try("tree_distances_2", note="Two passes. `long long` answers."),
            MCQ(r"""
**Tree Distances I** asks for the *largest* distance from every node instead of the sum.
Can you move the root from `u` to `v` with a one-line update like the one above?
""", [
                Opt("Yes: `far[v] = far[u] + 1`.",
                    why="Not if u's farthest node lies inside v's subtree: then moving to `v` brings it "
                        "*closer*."),
                Opt("Yes: subtract v's contribution from `far[u]`, as with the sums.",
                    why="A maximum cannot be un-taken. If the maximum came from v's subtree, `far[u]` "
                        "does not say what the second-best was. Same lesson as prefix maxima in algo01."),
                Opt("Not directly: a maximum has no inverse. Keep the two best child heights, or use "
                    "the diameter.", correct=True,
                    why="Right. With the two largest heights of `u` you always know the best path out of "
                        "`u` that avoids `v`. Or use the diameter trick below, which is shorter to code."),
            ]),
            Reflect(r"""
A shortcut for Tree Distances I: find the two ends `a` and `b` of a diameter, then answer
`max(dist(v, a), dist(v, b))` for every `v` (three BFS in total). Why can no other node be
farther from `v` than both `a` and `b`?
""", answer=r"""
Take any node `w`; it hangs off the path `a–b` at some node `c'`. First,
`dist(c', w) ≤ dist(c', a)` and `dist(c', w) ≤ dist(c', b)`: otherwise `w–b` (or `w–a`)
would be longer than the diameter. Now walk from `v` to `w` via `c'`, and replace the last
leg, `c' → w`, by the leg from `c'` to the end of the diameter that lies beyond `c'` as seen
from `v`. That leg is at least as long, and the new walk is exactly the route from `v` to
that end. So no `w` is farther from `v` than `a` or `b`.
"""),
            Try("tree_distances_1", note="Three BFS runs, or rerooting with the two best heights."),
        ]),
    ],
    problems=[SUBORDINATES, TREE_DIAMETER, TREE_MATCHING, TREE_DISTANCES_2, TREE_DISTANCES_1],
    cards=[
        Card(r"""Subtree sizes: the recurrence, and the order it needs?""",
             r"""`size[u] = 1 + Σ size[c]` over children; children must be computed before their parent (post-order). O(n)."""),
        Card(r"""How do you get a children-first order without recursion?""",
             r"""BFS from the root (every node appears after its parent), then process the BFS list backwards."""),
        Card(r"""When is `for (i = n; i >= 2; i--) sz[boss[i]] += sz[i];` correct?""",
             r"""Only if every parent has a smaller label than its child. Unless the statement promises it, use a real traversal order."""),
        Card(r"""Rooting a tree from an edge list: why does `if (v != par[u])` replace a visited array?""",
             r"""In a tree the only neighbour of `u` discovered before `u` is its parent; another would close a cycle."""),
        Card(r"""Which test shapes break naive tree code?""",
             r"""A chain/bamboo (depth n: walking up is O(n^2), recursion goes 2·10^5 deep) and a star (degree n: per-node O(deg^2) work is O(n^2))."""),
        Card(r"""Tree diameter in O(n)?""",
             r"""BFS from any node to the farthest node `a`; BFS from `a` to the farthest `b`; answer `dist(a, b)`. Needs non-negative edge lengths."""),
        Card(r"""Why does the double-BFS diameter work?""",
             r"""The farthest node from any start is an endpoint of some longest path, so the farthest node from *it* is the other end. (Proof: compare distances through the point where the start's route meets a longest path.)"""),
        Card(r"""Diameter by tree DP?""",
             r"""Height `h[u] = 1 + max h[c]`; the longest path with top `u` is the sum of the two largest `h[c] + 1`. Take the max over `u`. With weights (even negative), use a branch only if it adds a positive amount."""),
        Card(r"""Tree Matching DP states and transitions?""",
             r"""`dp0[u] = Σ max(dp0[c], dp1[c])` (u free); `dp1[u] = max_c dp0[u] − max(dp0[c], dp1[c]) + dp0[c] + 1` (u matched to c). Answer `max(dp0[root], dp1[root])`."""),
        Card(r"""Rerooting the sum of distances from `u` to its child `v`?""",
             r"""`ans[v] = ans[u] − sz[v] + (n − sz[v])`: v's subtree gets one step closer, everyone else one step farther. Fill parents first."""),
        Card(r"""Largest distance from every node of a tree (Tree Distances I)?""",
             r"""Find a diameter `a–b`; answer `max(dist(v, a), dist(v, b))`. Three BFS runs."""),
    ],
)
