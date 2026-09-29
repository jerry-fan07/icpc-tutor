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
    if shape == "twolegs":                   # two long chains hanging from the root
        return [-1] + [0 if i <= 2 else i - 2 for i in range(1, n)]
    if shape == "broom":                     # a long handle, then many leaves at its end
        h = max(1, n // 2)
        return [-1] + [i - 1 if i < h else h - 1 for i in range(1, n)]
    return [-1] + [rng.randrange(i) for i in range(1, n)]


SHAPES = ["random", "path", "star", "binary", "deep", "twolegs", "broom"]


def _tree(rng, n, shape):
    """(par, depth, labels) with the root (index 0) labelled 1."""
    par = _parents(rng, n, shape)
    dep = [0] * n
    for i in range(1, n):
        dep[i] = dep[par[i]] + 1
    lab = list(range(1, n + 1))
    rng.shuffle(lab)
    k = lab.index(1)
    lab[0], lab[k] = lab[k], lab[0]
    return par, dep, lab


def _boss_line(n, par, lab):
    boss = [0] * (n + 1)
    for i in range(1, n):
        boss[lab[i]] = lab[par[i]]
    return " ".join(map(str, boss[2:]))


def _deep_index(rng, n):
    return rng.randrange(max(0, n - max(1, n // 5)), n)


def _kth_input(rng, n, q, shape, deep=False):
    par, dep, lab = _tree(rng, n, shape)
    out = [f"{n} {q}", _boss_line(n, par, lab)]
    for _ in range(q):
        if deep:
            i = rng.randrange(n // 2, n)
            k = rng.randint(max(1, dep[i] // 2), n)
        else:
            i = rng.randrange(n)
            k = rng.randint(1, min(n, dep[i] + 2))
        out.append(f"{lab[i]} {k}")
    return "\n".join(out) + "\n"


def _lca_input(rng, n, q, shape, deep=False):
    par, dep, lab = _tree(rng, n, shape)
    out = [f"{n} {q}", _boss_line(n, par, lab)]
    for _ in range(q):
        if deep:
            a, b = _deep_index(rng, n), _deep_index(rng, n)
        else:
            a, b = rng.randrange(n), rng.randrange(n)
        out.append(f"{lab[a]} {lab[b]}")
    return "\n".join(out) + "\n"


def _dist_input(rng, n, q, shape, wmax, deep=False):
    par, dep, lab = _tree(rng, n, shape)
    rows = []
    for i in range(1, n):
        a, b = lab[i], lab[par[i]]
        if rng.random() < 0.5:
            a, b = b, a
        rows.append(f"{a} {b} {rng.randint(1, wmax)}")
    rng.shuffle(rows)
    out = [f"{n} {q}"] + rows
    for _ in range(q):
        if deep:
            a, b = _deep_index(rng, n), _deep_index(rng, n)
        else:
            a, b = rng.randrange(n), rng.randrange(n)
        out.append(f"{lab[a]} {lab[b]}")
    return "\n".join(out) + "\n"


def _cousin_input(rng, n, q, shape, whole=False):
    par, dep, lab = _tree(rng, n, shape)
    out = [f"{n} {q}", _boss_line(n, par, lab)]
    for _ in range(q):
        if whole:                                # ancestor = the root: the whole tree
            i = _deep_index(rng, n)
            p = max(1, dep[i])
        else:
            i = rng.randrange(n)
            p = rng.randint(1, min(n, dep[i] + 1))
        out.append(f"{lab[i]} {p}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- problems
KTH_BOSS = Problem(
    id="kth_boss",
    title="Company Queries I",
    difficulty="easy",
    source="CSES 1687 - Company Queries I",
    complexity="O((n + q) log n)",
    statement=r"""
A company has `n` employees numbered 1 to `n`. Employee 1 is the director; every other
employee has one direct boss, and following bosses upward always ends at the director.

Answer `q` queries: who is the `k`-th boss of employee `x`? The 1st boss is the direct
boss, the 2nd boss is the direct boss's direct boss, and so on.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has `n − 1` integers: the direct boss of employees 2, 3, ..., n. A boss
can have a larger number than the employee.

Each of the next `q` lines has two integers `x k` (1 ≤ x, k ≤ n).
""",
    output=r"""
For each query print the `k`-th boss of `x`, or `-1` if `x` has fewer than `k` bosses above.
""",
    samples=[
        Test("5 3\n1 1 3 3\n4 1\n4 2\n4 3\n", "3\n1\n-1\n"),
        Test("8 4\n1 2 3 4 5 3 7\n8 3\n6 4\n6 5\n6 6\n", "2\n2\n1\n-1\n"),
    ],
    tests=[
        Test("1 2\n\n1 1\n1 1\n"),
        Test("5 4\n5 4 1 3\n2 4\n2 2\n2 3\n2 5\n"),
        Test("2 2\n1\n2 1\n2 2\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _kth_input(rng, rng.randint(1, 12), rng.randint(1, 12), rng.choice(SHAPES)), 16),
        Gen("medium random", lambda rng: _kth_input(rng, 3000, 3000, rng.choice(SHAPES)), 3),
        Gen("max chain, deep queries", lambda rng: _kth_input(rng, 200000, 200000, "path", True), 1, large=True),
        Gen("max deep tree, deep queries", lambda rng: _kth_input(rng, 200000, 200000, "deep", True), 1, large=True),
        Gen("max random tree", lambda rng: _kth_input(rng, 200000, 200000, "random"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int LOG = 18;                 // 2^18 = 262144 > 2·10^5 >= k
int up[200001][LOG];                // up[v][j] = the 2^j-th boss of v, 0 if there is none;
                                    // one node's jumps sit side by side in memory

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    for (int v = 2; v <= n; v++) cin >> up[v][0];   // up[1][0] = 0: nobody above the director
    // level by level: level j-1 is complete before level j reads it, whatever the labels.
    // up[0][j] = 0 (globals are zero), so a jump past the director stays at 0.
    for (int j = 1; j < LOG; j++)
        for (int v = 1; v <= n; v++)
            up[v][j] = up[up[v][j - 1]][j - 1];
    while (q--) {
        int x, k;
        cin >> x >> k;
        for (int j = 0; j < LOG; j++)                // one jump per set bit of k
            if (k >> j & 1) x = up[x][j];
        cout << (x == 0 ? -1 : x) << '\n';
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
    vector<int> boss(n + 1, 0);
    for (int v = 2; v <= n; v++) cin >> boss[v];
    while (q--) {
        int x, k;
        cin >> x >> k;
        while (k-- && x != 0) x = boss[x];
        cout << (x == 0 ? -1 : x) << '\n';
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
    vector<int> boss(n + 1, 0);
    for (int v = 2; v <= n; v++) cin >> boss[v];
    while (q--) {
        int x, k;
        cin >> x >> k;
        while (k-- && x != 0) x = boss[x];          // one step at a time
        cout << (x == 0 ? -1 : x) << '\n';
    }
}
""",
    hints=[
        r"""Walking up `k` steps is 4·10^10 steps on a chain. Write `k` in binary: which jumps
would you need if every employee knew their 1st, 2nd, 4th, 8th, ... boss?""",
        r"""`up[v][j] = up[up[v][j-1]][j-1]`. Build level by level (`j` in the outer loop), because
a boss can have a larger number than their employee.""",
        r"""Use 0 as "nobody" with `up[0][j] = 0`: a jump past the director lands on 0 and stays.""",
    ],
    editorial=r"""
Binary lifting. `up[v][j]` is the `2^j`-th boss of `v`: `up[v][0]` is the input, and a jump
of `2^j` is two jumps of `2^(j−1)`, so `up[v][j] = up[up[v][j−1]][j−1]`. A query writes `k` in
binary and makes one jump per set bit: at most 18 jumps, since `k < 2^18`. The jumps all
climb the same chain, so their order does not matter. O(n log n) to build, O(log n) per
query, 14.4 MB of `int`s.

Node 0 is a sink: `up[0][j] = 0`, so overshooting the director gives 0, printed as −1.

The loop order matters: with `j` outside, level `j − 1` is complete before level `j` reads
it. With `v` outside, `up[v][j]` reads the row of an ancestor that may not be filled yet
if that ancestor has a larger number; one hidden test (a chain labelled 1, 4, 3, 5, 2) fails
that way.
""",
)

LOWEST_COMMON_BOSS = Problem(
    id="lowest_common_boss",
    title="Company Queries II",
    difficulty="medium",
    source="CSES 1688 - Company Queries II",
    complexity="O((n + q) log n)",
    statement=r"""
A company has `n` employees numbered 1 to `n`. Employee 1 is the director; every other
employee has one direct boss.

Answer `q` queries: for employees `a` and `b`, who is their lowest common boss? That is the
employee farthest from the director who is a boss of both, where every employee counts
as their own boss (so if `a` is above `b`, the answer is `a`).
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has `n − 1` integers: the direct boss of employees 2, 3, ..., n. A boss
can have a larger number than the employee.

Each of the next `q` lines has two integers `a b` (1 ≤ a, b ≤ n).
""",
    output=r"""
For each query print the lowest common boss of `a` and `b`.
""",
    samples=[
        Test("5 3\n1 1 3 3\n4 5\n2 5\n1 4\n", "3\n1\n1\n"),
        Test("8 3\n1 2 3 4 5 3 7\n6 8\n3 6\n7 7\n", "3\n3\n7\n",
             note="In the second query, 3 is itself a boss of 6."),
    ],
    tests=[
        Test("1 1\n\n1 1\n"),
        Test("2 3\n1\n1 2\n2 1\n2 2\n"),
        Test("6 4\n6 5 1 4 3\n2 5\n2 1\n5 3\n2 2\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _lca_input(rng, rng.randint(1, 12), rng.randint(1, 12), rng.choice(SHAPES)), 16),
        Gen("medium random", lambda rng: _lca_input(rng, 3000, 3000, rng.choice(SHAPES)), 3),
        Gen("max two chains, deep pairs", lambda rng: _lca_input(rng, 200000, 200000, "twolegs", True), 1, large=True),
        Gen("max chain, deep pairs", lambda rng: _lca_input(rng, 200000, 200000, "path", True), 1, large=True),
        Gen("max random tree", lambda rng: _lca_input(rng, 200000, 200000, "random"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int LOG = 18;
int up[200001][LOG], depth_[200001];

int lca(int a, int b) {
    if (depth_[a] < depth_[b]) swap(a, b);
    int k = depth_[a] - depth_[b];                 // lift a to b's depth: a k-th boss query
    for (int j = 0; j < LOG; j++)
        if (k >> j & 1) a = up[a][j];
    if (a == b) return a;                          // b was a boss of a
    for (int j = LOG - 1; j >= 0; j--)             // largest jumps first
        if (up[a][j] != up[b][j]) {                // both still strictly below the answer
            a = up[a][j];
            b = up[b][j];
        }
    return up[a][0];                               // a and b are now children of the answer
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<vector<int>> reports(n + 1);
    for (int v = 2; v <= n; v++) {
        cin >> up[v][0];
        reports[up[v][0]].push_back(v);
    }
    // depths in BFS order (bosses can have larger numbers than their employees)
    vector<int> order = {1};
    order.reserve(n);
    for (int i = 0; i < (int)order.size(); i++)
        for (int c : reports[order[i]]) {
            depth_[c] = depth_[order[i]] + 1;
            order.push_back(c);
        }
    for (int j = 1; j < LOG; j++)
        for (int v = 1; v <= n; v++)
            up[v][j] = up[up[v][j - 1]][j - 1];
    while (q--) {
        int a, b;
        cin >> a >> b;
        cout << lca(a, b) << '\n';
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
    vector<int> boss(n + 1, 0);
    for (int v = 2; v <= n; v++) cin >> boss[v];
    while (q--) {
        int a, b;
        cin >> a >> b;
        vector<bool> above(n + 1, false);          // a and all its bosses
        for (int x = a; x != 0; x = boss[x]) above[x] = true;
        int x = b;
        while (!above[x]) x = boss[x];
        cout << x << '\n';
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
    vector<int> boss(n + 1, 0), depth(n + 1, 0);
    vector<vector<int>> reports(n + 1);
    for (int v = 2; v <= n; v++) {
        cin >> boss[v];
        reports[boss[v]].push_back(v);
    }
    vector<int> order = {1};
    for (int i = 0; i < (int)order.size(); i++)
        for (int c : reports[order[i]]) { depth[c] = depth[order[i]] + 1; order.push_back(c); }
    while (q--) {
        int a, b;
        cin >> a >> b;
        while (depth[a] > depth[b]) a = boss[a];   // one step at a time
        while (depth[b] > depth[a]) b = boss[b];
        while (a != b) { a = boss[a]; b = boss[b]; }
        cout << a << '\n';
    }
}
""",
    hints=[
        r"""First lift the deeper employee to the other's depth: that is Company Queries I with
`k = depth[a] − depth[b]`. If they now coincide, you are done.""",
        r"""Otherwise, for `j` from large to small: if `up[a][j] != up[b][j]`, both jumps land
strictly below the answer, so take them. At the end the answer is `up[a][0]`.""",
    ],
    editorial=r"""
Compute depths (BFS from the director, since labels are arbitrary) and the lifting table
of Company Queries I. For a query, lift the deeper node by the depth difference; if the two
nodes coincide, that node is the answer.

Otherwise keep the invariant "`a ≠ b`, same depth", so the answer is strictly above both.
For `j` from high to low, jump both by `2^j` exactly when `up[a][j] != up[b][j]`: different
landing points are still below the answer; equal ones are at or above it, and you cannot
tell which, so you do not jump. This greedy writes the unknown distance (to the answer's
children) in binary, largest bit first, which is why the order matters here when it did
not for k-th boss. At the end `a` and `b` are children of the answer: return `up[a][0]`.

O(log n) per query. Walking up one step at a time is O(depth), 4·10^10 on the two-chain
test.
""",
)

DISTANCE_QUERIES = Problem(
    id="distance_queries",
    title="Distance Queries",
    difficulty="medium",
    source="CSES 1135 - Distance Queries (with road lengths)",
    complexity="O((n + q) log n)",
    statement=r"""
A kingdom has `n` towns and `n − 1` roads, each with a length; the roads connect all towns,
so there is exactly one route between any two towns.

Answer `q` queries: how long is the route between towns `a` and `b`?
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

Each of the next `n − 1` lines has three integers `a b w`: a road of length `w` between
towns `a` and `b` (1 ≤ w ≤ 10^9).

Each of the next `q` lines has two integers `a b` (1 ≤ a, b ≤ n).
""",
    output=r"""
For each query print the length of the route from `a` to `b`.
""",
    samples=[
        Test("5 3\n1 2 5\n2 3 3\n2 4 10\n1 5 1\n3 4\n3 5\n4 4\n", "13\n9\n0\n"),
    ],
    tests=[
        Test("1 1\n1 1\n"),
        Test("3 3\n1 2 1000000000\n3 2 1000000000\n1 3\n3 1\n2 2\n"),
        Test("4 3\n4 3 7\n3 2 1\n2 1 2\n4 1\n1 4\n3 1\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _dist_input(rng, rng.randint(1, 12), rng.randint(1, 12), rng.choice(SHAPES), 20), 16),
        Gen("medium, huge lengths", lambda rng: _dist_input(rng, 3000, 3000, rng.choice(SHAPES), 10**9), 3),
        Gen("max two chains, deep pairs", lambda rng: _dist_input(rng, 200000, 200000, "twolegs", 10**9, True), 1, large=True),
        Gen("max random tree", lambda rng: _dist_input(rng, 200000, 200000, "random", 10**9), 1, large=True),
        Gen("max deep tree, deep pairs", lambda rng: _dist_input(rng, 200000, 200000, "deep", 10**9, True), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int LOG = 18;
int up[200001][LOG], dep[200001];      // dep: number of edges from town 1
long long dist1[200001];               // length of the route from town 1

int lca(int a, int b) {
    if (dep[a] < dep[b]) swap(a, b);
    int k = dep[a] - dep[b];           // edges, not lengths: lifting counts steps
    for (int j = 0; j < LOG; j++)
        if (k >> j & 1) a = up[a][j];
    if (a == b) return a;
    for (int j = LOG - 1; j >= 0; j--)
        if (up[a][j] != up[b][j]) { a = up[a][j]; b = up[b][j]; }
    return up[a][0];
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<vector<pair<int,int>>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b, w;
        cin >> a >> b >> w;
        adj[a].push_back({b, w});
        adj[b].push_back({a, w});
    }
    vector<int> order = {1};
    order.reserve(n);
    for (int i = 0; i < (int)order.size(); i++) {
        int u = order[i];
        for (auto [v, w] : adj[u])
            if (v != up[u][0]) {
                up[v][0] = u;
                dep[v] = dep[u] + 1;
                dist1[v] = dist1[u] + w;
                order.push_back(v);
            }
    }
    for (int j = 1; j < LOG; j++)
        for (int v = 1; v <= n; v++)
            up[v][j] = up[up[v][j - 1]][j - 1];
    while (q--) {
        int a, b;
        cin >> a >> b;
        cout << dist1[a] + dist1[b] - 2 * dist1[lca(a, b)] << '\n';
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
    vector<vector<pair<int,int>>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b, w;
        cin >> a >> b >> w;
        adj[a].push_back({b, w});
        adj[b].push_back({a, w});
    }
    while (q--) {
        int a, b;
        cin >> a >> b;
        vector<long long> d(n + 1, -1);             // walk the whole tree from a
        vector<int> st = {a};
        d[a] = 0;
        while (!st.empty()) {
            int u = st.back(); st.pop_back();
            for (auto [v, w] : adj[u]) if (d[v] < 0) { d[v] = d[u] + w; st.push_back(v); }
        }
        cout << d[b] << '\n';
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
    vector<vector<pair<int,int>>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a, b, w;
        cin >> a >> b >> w;
        adj[a].push_back({b, w});
        adj[b].push_back({a, w});
    }
    vector<int> par(n + 1, 0), dep(n + 1, 0), order = {1};
    vector<long long> d(n + 1, 0);
    for (int i = 0; i < (int)order.size(); i++) {
        int u = order[i];
        for (auto [v, w] : adj[u])
            if (v != par[u]) { par[v] = u; dep[v] = dep[u] + 1; d[v] = d[u] + w; order.push_back(v); }
    }
    while (q--) {
        int a, b;
        cin >> a >> b;
        int x = a, y = b;
        while (dep[x] > dep[y]) x = par[x];
        while (dep[y] > dep[x]) y = par[y];
        while (x != y) { x = par[x]; y = par[y]; }
        cout << d[a] + d[b] - 2 * d[x] << '\n';
    }
}
""",
    hints=[
        r"""Root the tree at town 1 and store `d[v]`, the length of the route from town 1. The route
from `a` to `b` goes up to their lowest common ancestor and back down.""",
        r"""`dist(a, b) = d[a] + d[b] − 2·d[lca(a, b)]`. Lift by *edge counts* (depth), not by
lengths, and keep lengths in `long long`: a route can be 2·10^14 long.""",
    ],
    editorial=r"""
Root the tree at town 1, and in one BFS record for every town its parent, its depth in
edges, and `d[v]`, the length of its route from town 1. The route `a → b` climbs from `a` to
`c = lca(a, b)` and descends to `b`; the part from town 1 down to `c` is contained in both
`d[a]` and `d[b]` and is not on the route, so

```
dist(a, b) = d[a] + d[b] − 2·d[c]
```

`c` comes from binary lifting as in Company Queries II. Two things cost points: the lifting
must use depths in edges (a jump of `2^j` is `2^j` edges, whatever their lengths), and the
lengths must be `long long` (up to `(n − 1)·10^9 ≈ 2·10^14`). O((n + q) log n).
""",
)

COUSINS = Problem(
    id="cousins",
    title="Cousins",
    difficulty="hard",
    source="Codeforces 208E - Blood Cousins (one tree)",
    complexity="O((n + q) log n)",
    statement=r"""
A family tree has `n` people numbered 1 to `n`. Person 1 is the founder; every other person
has exactly one parent in the tree. The 1st ancestor of a person is their parent, and the
`p`-th ancestor is the parent of the `(p − 1)`-th ancestor.

Two different people are **`p`-th cousins** if they have the same `p`-th ancestor. Answer `q`
queries: how many `p`-th cousins does person `v` have?
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has `n − 1` integers: the parent of persons 2, 3, ..., n (a parent can have
a larger number than the child).

Each of the next `q` lines has two integers `v p` (1 ≤ v, p ≤ n).
""",
    output=r"""
For each query print the number of `p`-th cousins of `v` (0 if `v` has no `p`-th ancestor).
""",
    samples=[
        Test("7 5\n1 1 2 3 2 5\n6 1\n7 2\n5 2\n4 1\n1 1\n", "1\n0\n2\n1\n0\n"),
    ],
    tests=[
        Test("1 1\n\n1 1\n"),
        Test("4 3\n1 1 1\n2 1\n3 2\n4 1\n"),
        Test("6 3\n6 5 1 4 3\n2 5\n2 4\n3 2\n"),
    ],
    gens=[
        Gen("small random shapes", lambda rng: _cousin_input(rng, rng.randint(1, 12), rng.randint(1, 12), rng.choice(SHAPES)), 16),
        Gen("medium random", lambda rng: _cousin_input(rng, 2000, 2000, rng.choice(SHAPES)), 3),
        Gen("max broom, whole-tree queries", lambda rng: _cousin_input(rng, 200000, 200000, "broom", True), 1, large=True),
        Gen("max random tree, whole-tree queries", lambda rng: _cousin_input(rng, 200000, 200000, "random", True), 1, large=True),
        Gen("max deep tree", lambda rng: _cousin_input(rng, 200000, 200000, "deep"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int LOG = 18;
int up[200001][LOG];

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<vector<int>> kids(n + 1);
    for (int v = 2; v <= n; v++) {
        cin >> up[v][0];
        kids[up[v][0]].push_back(v);
    }
    for (int j = 1; j < LOG; j++)
        for (int v = 1; v <= n; v++)
            up[v][j] = up[up[v][j - 1]][j - 1];

    // iterative DFS: entry times, exit times, depths; nodes of equal depth in entry order
    vector<int> tin(n + 1), tout(n + 1), dep(n + 1, 0), it(n + 1, 0), st = {1};
    vector<vector<int>> atDepth(n);
    int timer = 0;
    tin[1] = timer++;
    atDepth[0].push_back(tin[1]);
    while (!st.empty()) {
        int u = st.back();
        if (it[u] < (int)kids[u].size()) {
            int c = kids[u][it[u]++];
            dep[c] = dep[u] + 1;
            tin[c] = timer++;
            atDepth[dep[c]].push_back(tin[c]);   // pushed in increasing tin: already sorted
            st.push_back(c);
        } else {
            tout[u] = timer - 1;                 // u's subtree is tin[u]..tout[u]
            st.pop_back();
        }
    }

    while (q--) {
        int v, p;
        cin >> v >> p;
        if (p > dep[v]) { cout << 0 << '\n'; continue; }
        int u = v;
        for (int j = 0; j < LOG; j++)
            if (p >> j & 1) u = up[u][j];
        // cousins = nodes at v's depth inside u's subtree, minus v itself
        const vector<int>& row = atDepth[dep[v]];
        int cnt = upper_bound(row.begin(), row.end(), tout[u])
                - lower_bound(row.begin(), row.end(), tin[u]);
        cout << cnt - 1 << '\n';
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
    vector<int> par(n + 1, 0);
    for (int v = 2; v <= n; v++) cin >> par[v];
    auto anc = [&](int x, int p) {
        while (p-- && x != 0) x = par[x];
        return x;
    };
    while (q--) {
        int v, p;
        cin >> v >> p;
        int a = anc(v, p), cnt = 0;
        if (a != 0)
            for (int w = 1; w <= n; w++)
                if (w != v && anc(w, p) == a) cnt++;
        cout << cnt << '\n';
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
    vector<int> par(n + 1, 0), dep(n + 1, 0);
    vector<vector<int>> kids(n + 1);
    for (int v = 2; v <= n; v++) { cin >> par[v]; kids[par[v]].push_back(v); }
    vector<int> order = {1};
    for (int i = 0; i < (int)order.size(); i++)
        for (int c : kids[order[i]]) { dep[c] = dep[order[i]] + 1; order.push_back(c); }
    vector<int> st;
    while (q--) {
        int v, p;
        cin >> v >> p;
        if (p > dep[v]) { cout << 0 << '\n'; continue; }
        int u = v;
        for (int k = 0; k < p; k++) u = par[u];
        int cnt = 0;                                 // walk u's whole subtree
        st.assign(1, u);
        while (!st.empty()) {
            int x = st.back(); st.pop_back();
            if (dep[x] == dep[v]) { cnt++; continue; }
            for (int c : kids[x]) st.push_back(c);
        }
        cout << cnt - 1 << '\n';
    }
}
""",
    hints=[
        r"""The `p`-th cousins of `v` are the other people at `v`'s depth inside the subtree of `v`'s
`p`-th ancestor `u`. Find `u` by binary lifting.""",
        r"""In DFS entry order, u's subtree is the block `tin[u]..tout[u]`. For every depth keep the
list of entry times of the people at that depth; it is sorted if you append during the DFS.""",
        r"""Count with `upper_bound(tout[u]) − lower_bound(tin[u])` in the list for `depth[v]`, then
subtract 1 for `v` itself.""",
    ],
    editorial=r"""
Two ideas combined. Binary lifting finds `u`, the `p`-th ancestor of `v` (if `p > depth[v]`,
the answer is 0). The `p`-th cousins of `v` are exactly the other nodes at `depth[v]` in the
subtree of `u`.

An Euler tour (DFS entry times) turns that subtree into the contiguous block
`tin[u]..tout[u]`. During the DFS, append each node's `tin` to the list of its depth; the
lists come out sorted because entry times increase. Then the count is two binary searches
in the list for `depth[v]`, minus 1 for `v` itself. O((n + q) log n).

Walking the subtree of `u` per query costs O(n) when `u` is near the root, 4·10^10 in the
worst case. Recursion depth reaches 2·10^5 on a chain; the reference uses an explicit
stack with a per-node child index.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo14",
    title="binary lifting & lowest common ancestor",
    track="algo",
    order=14,
    summary="Jump up a tree by powers of two: k-th ancestors in O(log n), the lowest common "
            "ancestor, distances through it, and the Euler tour that turns every subtree into "
            "an interval.",
    prereqs=["algo13", "cpp10"],
    tags=["binary lifting", "lca", "k-th ancestor", "tree distances", "euler tour",
          "subtree interval", "tin tout"],
    parts=[
        Part("The k-th boss", [
            Say(r"""
Back to the company of algo13: `n ≤ 2·10^5` employees, employee 1 is the director, and you
are given every other employee's direct boss (with arbitrary numbers). Now there are
`q ≤ 2·10^5` queries: **who is the `k`-th boss of `x`?** The 1st boss is the direct boss, the
2nd is the boss's boss, and so on; print −1 if the chain ends first. `k ≤ n`.

The obvious answer: step up `k` times.
"""),
            Numeric(r"""
In the worst case (a chain, deep `x`, large `k`), roughly how many steps do all `q` queries
take together?
""", answer=4e10, rel=0.5, unit="steps",
                explain=r"""
Up to `n` steps per query, `q · n = 4·10^10` in all. Storing every node's full list of
ancestors instead would make each query a lookup, but on a chain those lists hold
`n(n − 1)/2 ≈ 2·10^10` entries: 80 GB. We need something in between.
"""),
            Reflect(r"""
Any `k` is a sum of distinct powers of two: its binary representation. Suppose every
employee knew their 1st, 2nd, 4th, 8th, 16th, ... boss. How would you find the 13th boss
of `x`, and how many lookups would it take?
""", answer=r"""
13 = 8 + 4 + 1 (binary 1101). Jump 8 up from `x`, then 4 up from where you landed, then 1:
three lookups. In general one jump per set bit of `k`, so at most ⌊log2 k⌋ + 1 jumps, and
each node stores only about log2 n ancestors. This is **binary lifting**: the table of
power-of-two ancestors is the precomputation, and a query reads `k` in binary.
"""),
            Numeric(r"""
With `k ≤ 2·10^5`, how many levels `j = 0, 1, ..., LOG − 1` (the `2^j`-th ancestors) does
the table need?
""", answer=18,
                hint="Find the smallest power of two above 2·10^5.",
                explain=r"""
2^17 = 131072 < 2·10^5 < 2^18 = 262144, so every `k` fits in 18 bits: levels 0..17, at
most 18 jumps per query. The table is 18 · 2·10^5 `int`s, 14.4 MB.
"""),
            Short(r"""
The `2^j`-th boss of `v` is the `2^(j−1)`-th boss of the `2^(j−1)`-th boss of `v`. Fill in
the table recurrence: `up[v][j] = up[ ____ ][j-1]`
""", accept=["up[v][j-1]", "up[v][j - 1]"], placeholder="an entry of up",
                explain=r"""
`up[v][j] = up[up[v][j-1]][j-1]`: two half-jumps make a full jump. Level 0 is the input
(each employee's direct boss).
"""),
            Say(r"""
Here is the table and the query. Node 0 plays "nobody": the director's boss is 0.

```cpp
const int LOG = 18;
int up[200001][LOG];               // up[v][j] = the 2^j-th boss of v, 0 if none

// up[v][0] = direct boss of v, read from the input; up[1][0] = 0
for (int j = 1; j < LOG; j++)
    for (int v = 1; v <= n; v++)
        up[v][j] = up[up[v][j - 1]][j - 1];

// the k-th boss of x
for (int j = 0; j < LOG; j++)
    if (k >> j & 1) x = up[x][j];
cout << (x == 0 ? -1 : x) << '\n';
```
"""),
            MCQ(r"""
Nothing in the query checks whether a jump goes past the director. Why is `x == 0` at the
end still the right test for "no such boss"?
""", [
                Opt("Because `k` never exceeds the depth of `x`.",
                    why="Nothing promises that: `k` can be as large as `n`, and the sample asks for the "
                        "3rd boss of someone with only two."),
                Opt("Because `up[0][j] = 0` for every `j`: once a jump overshoots, `x` becomes 0 and "
                    "stays 0.", correct=True,
                    why="Yes. Node 0 is a sink. The global array starts zeroed, so the sentinel costs "
                        "nothing, and no jump ever reads outside the array."),
                Opt("It is not: you must compare `k` with `depth[x]` first.",
                    why="That works too, but it needs depths. The sentinel makes the check unnecessary."),
            ]),
            MCQ(r"""
Someone swaps the building loops: `v` outside, `j` inside. When does that go wrong?
""", [
                Opt("Never: the same assignments are made, just in another order.",
                    why="Order is the point. `up[v][j]` reads the row of `w = up[v][j-1]`, an ancestor of "
                        "`v`. With `v` outside, that row is filled only if `w` was processed before `v`."),
                Opt("When some boss has a larger number than their employee.", correct=True,
                    why="Right. Then the ancestor's row is still zero when it is read, and the jump "
                        "silently lands on 0. With `j` outside, level `j − 1` is complete before level "
                        "`j` starts, whatever the labels."),
                Opt("Only when `n` is not a power of two.",
                    why="`n` plays no role; the table has `LOG` levels regardless."),
            ]),
            MCQ(r"""
For the `k`-th boss, does it matter whether you take the jumps from the lowest bit of `k`
up, or from the highest bit down?
""", [
                Opt("Yes: highest first, like a binary search.",
                    why="That will matter for the next problem, where the distance is unknown. Here "
                        "`k` is known, and the jumps just add up to it."),
                Opt("No: every jump climbs the same unique chain of bosses, so the total climb is `k` "
                    "either way.", correct=True,
                    why="Right. A node has one ancestor at each height, so 1 + 4 + 8 and 8 + 4 + 1 "
                        "land on the same node."),
                Opt("Yes: lowest first, or you overshoot the director.",
                    why="Overshooting lands on 0 in any order, and 0 is a sink."),
            ]),
            Short(r"""
Bosses of employees 2..8 are `1 2 3 4 5 3 7`: a chain 1–2–3–4–5–6 with a branch 3–7–8.
For the 3rd boss of 8, write `3 = 1 + 2`: the 1-jump from 8 lands on 7. What is `up[7][1]`?
""", accept=["2"], placeholder="an employee",
                explain=r"""
7's boss is 3 and 3's boss is 2, so `up[7][1] = 2`. The 3rd boss of 8 is 2
(8 → 7 → 3 → 2), reached with two lookups.
"""),
            Try("kth_boss", note="Level-by-level table, the 0 sentinel, `'\\n'` output. One hidden "
                "test labels a chain 1, 4, 3, 5, 2."),
        ]),
        Part("Lowest common ancestor", [
            Say(r"""
Same company, new queries: for employees `a` and `b`, who is their **lowest common boss**,
the deepest employee who is a boss of both (everyone counts as their own boss)? This is the
**lowest common ancestor**, `lca(a, b)`, and it is the workhorse of tree queries.

The naive method: step the deeper of the two up until the depths are equal, then step
both up together until they meet. On a tree made of two long chains, a query between two
deep nodes on different chains costs about `n` steps: 4·10^10 again.
"""),
            Short(r"""
The first phase, lifting the deeper node `a` to the depth of `b`, is a problem you have
already solved. It is a `k`-th boss query with `k = ?`
""", accept=["depth[a]-depth[b]", "depth[a] - depth[b]", "dep[a]-dep[b]", "d[a]-d[b]",
             "depth(a)-depth(b)"],
                placeholder="an expression",
                explain=r"""
`k = depth[a] − depth[b]`. After it, if `a == b`, then `b` was an ancestor of `a` and is the
answer. Otherwise `a ≠ b` at the same depth, and the second phase begins.
"""),
            Reflect(r"""
Now `a ≠ b`, same depth, and you do not know how far above them the LCA is. For a jump of
`2^j` you can compare `up[a][j]` with `up[b][j]`. What does it tell you when they differ,
and when they are equal? Which jumps are safe to take?
""", answer=r"""
If `up[a][j] != up[b][j]`, both landing points are still strictly below the LCA (at or
above it, the two ancestors would be the same node), so jumping both is safe. If they are
equal, the landing point is at or above the LCA, and you cannot tell whether it is the LCA
or higher, so do not jump. Taking every safe jump from large `j` to small keeps "`a ≠ b`,
same depth" true and climbs as far as possible: at the end `a` and `b` are two different
children of the LCA, and the answer is `up[a][0]`.
"""),
            Say(r"""
```cpp
int lca(int a, int b) {
    if (depth[a] < depth[b]) swap(a, b);
    int k = depth[a] - depth[b];
    for (int j = 0; j < LOG; j++)
        if (k >> j & 1) a = up[a][j];
    if (a == b) return a;
    for (int j = LOG - 1; j >= 0; j--)
        if (up[a][j] != up[b][j]) { a = up[a][j]; b = up[b][j]; }
    return up[a][0];
}
```

Depths come from a BFS from the root, as in algo13 (labels are arbitrary, so a loop over
`v = 2..n` would not do).
"""),
            Short(r"""
Trace `lca(6, 8)` on the company from before (chain 1–2–3–4–5–6, branch 3–7–8; depths:
6 is at 5, 8 is at 4). After lifting 6 to depth 4 and running the second loop, which two
nodes do `a` and `b` hold? Answer as `a b`.
""", accept=["4 7", "4, 7", "(4, 7)"], placeholder="two nodes",
                hint="After lifting, `a = 5`, `b = 8`. With LOG = 3, try `j = 2, 1, 0`: jump only when the two ancestors differ.",
                explain=r"""
`j = 2`: `up[5][2] = 1`, `up[8][2] = 1`, equal: no jump. `j = 1`: both 2-jumps land on 3,
equal: no jump. `j = 0`: 4 and 7 differ: jump, `a = 4`, `b = 7`. They are children of 3,
and `lca(6, 8) = up[4][0] = 3`.
"""),
            MCQ(r"""
For the k-th boss, the order of the jumps did not matter. In the second LCA loop, `j` must
go from high to low. Why?
""", [
                Opt("It does not matter here either.",
                    why="Try `a` and `b` 6 steps below the LCA. Low to high: jump 1 (5 below), jump 2 "
                        "(3 below), refuse 4 (it would overshoot), and stop 3 below: `up[a][0]` is not "
                        "the LCA."),
                Opt("Big jumps first finish sooner.",
                    why="The loop always runs `LOG` iterations. It is about correctness, not speed."),
                Opt("The distance to climb is unknown, and taking the largest safe jump first writes "
                    "it in binary, top bit down.", correct=True,
                    why="Right. It is a binary search on the height: each refusal fixes one bit as 0, "
                        "each jump fixes it as 1. Low-to-high cannot come back for a bit it skipped."),
            ]),
            MCQ(r"""
What goes wrong if you drop the line `if (a == b) return a;`?
""", [
                Opt("Nothing: the second loop never jumps when `a == b`, so it is harmless.",
                    why="The loop does not jump, but the function then returns `up[a][0]`: the boss "
                        "of the right answer."),
                Opt("`lca(3, 6)` returns 2 instead of 3: whenever one node is an ancestor of the other, "
                    "the answer comes out one level too high.", correct=True,
                    why="Yes. The final `up[a][0]` assumes `a` and `b` are distinct children of the "
                        "LCA, which is false when they already coincide."),
                Opt("An infinite loop.",
                    why="Both loops are bounded by `LOG`."),
            ]),
            MCQ(r"""
The table can be declared `int up[LOG][200001]` (level first) or `int up[200001][LOG]`
(node first). Same answers either way. With 2·10^5 LCA queries on a random tree, which runs
faster, and why?
""", [
                Opt("No difference: both are 14.4 MB of `int`s.",
                    why="Same size, different order in memory. On this judge the level-first table takes "
                        "about 240 ms on that test and the node-first one about 90 ms."),
                Opt("`up[200001][LOG]`: the second loop reads `up[a][j]` for the same `a` and "
                    "decreasing `j`, and those 18 numbers sit in one or two cache lines.", correct=True,
                    why="Right. With levels first, each `up[j][a]` is 800 KB away from `up[j-1][a]`, "
                        "so every read is a cache miss. Most loop iterations do not jump, so they keep "
                        "reading the same node's row."),
                Opt("`up[LOG][200001]`: the build loop walks each level in order.",
                    why="The build is faster that way, but it runs once; the queries run 2·10^5 times "
                        "and dominate."),
            ], explain=r"""
Constant factors rarely decide a verdict, but memory layout is the one that most often
does: a cache miss costs as much as a hundred additions. Put the index you vary in the
innermost loop last.
"""),
            Try("lowest_common_boss", note="Depths by BFS, the equal-depth loop from high `j` down, and "
                "the `a == b` case."),
        ]),
        Part("Distances through the LCA", [
            Say(r"""
A kingdom's `n ≤ 2·10^5` towns are joined by `n − 1` roads with lengths up to 10^9, forming
a tree. `q ≤ 2·10^5` queries ask for the length of the route between two towns.

Root the tree at town 1 and let `d[v]` be the length of the route from town 1 to `v`,
computed in one BFS.
"""),
            MCQ(r"""
With `c = lca(a, b)`, which formula gives the length of the route from `a` to `b`?
""", [
                Opt("`d[a] + d[b]`",
                    why="That is the length of going from `a` up to town 1 and back down to `b`. The part "
                        "from town 1 to `c` is walked twice and is not on the route at all."),
                Opt("`d[a] + d[b] − d[c]`",
                    why="The stretch from town 1 to `c` is inside both `d[a]` and `d[b]`; it must be "
                        "removed from both."),
                Opt("`d[a] + d[b] − 2·d[c]`", correct=True,
                    why="Yes: `(d[a] − d[c]) + (d[b] − d[c])`, the climb from `a` to `c` plus the descent "
                        "from `c` to `b`."),
                Opt("`|d[a] − d[b]|`",
                    why="Only when one town is an ancestor of the other. Two towns on different "
                        "branches at the same distance from town 1 would get 0."),
            ]),
            Numeric(r"""
Roads `1-2` (5), `2-3` (3), `2-4` (10), `1-5` (1). What is the distance from town 3 to town 4?
""", answer=13,
                explain=r"""
`d = [0, 5, 8, 15, 1]` for towns 1..5, `lca(3, 4) = 2`, so `8 + 15 − 2·5 = 13`: the roads
3–2 and 2–4.
"""),
            MCQ(r"""
The lifting needs depths to equalise `a` and `b`. Can it use `d[]`, the road lengths from
town 1, as those depths?
""", [
                Opt("Yes: both measure how far down a node is.",
                    why="A jump of `2^j` climbs `2^j` edges, whatever their lengths. With `k = d[a] − d[b]` "
                        "(a length, maybe 10^9) you would climb that many *edges*."),
                Opt("No: lifting counts edges, so it needs `depth[]` in edges; `d[]` is only for the "
                    "final formula.", correct=True,
                    why="Right. Keep both arrays: `depth` for the jumps, `d` for the answer."),
                Opt("Yes, but only if all roads have length 1.",
                    why="True, but then `d` and `depth` are the same array; in this problem they are not."),
            ]),
            Numeric(r"""
How long can the longest route be, with `n = 2·10^5` and roads up to 10^9?
""", answer=2e14, rel=0.1,
                explain=r"""
`(n − 1) · 10^9 ≈ 2·10^14`: `d[]` and the answers need `long long`. The `2 * d[c]` must be
computed in `long long` too, which it is if `d` is `long long`.
"""),
            Try("distance_queries", note="Two arrays: depth in edges for the lifting, length in "
                "`long long` for the answer."),
            MCQ(r"""
A follow-up question asks: does town `x` lie on the route from `a` to `b`? Which test is
right (road lengths are positive)?
""", [
                Opt("`lca(a, x) == x` or `lca(b, x) == x` (x is an ancestor of `a` or `b`).",
                    why="That also accepts ancestors *above* `lca(a, b)`, like town 1, which are not on "
                        "the route unless they are the LCA."),
                Opt("`dist(a, x) + dist(x, b) == dist(a, b)`", correct=True,
                    why="Yes. In a tree the route is unique; going through `x` costs exactly the same only "
                        "if `x` is on it. (With zero-length roads, compare edge counts instead.)"),
                Opt("`d[a] ≤ d[x] ≤ d[b]`",
                    why="Distances from town 1 say nothing about which branch `x` is on."),
            ]),
        ]),
        Part("Subtrees as intervals", [
            Say(r"""
A different kind of question: "how many people below `u` are at depth 7?" or "what is the
total salary in u's department?" These are questions about a **subtree**, and they become
array questions if every subtree occupies a contiguous block of an array.

A DFS gives such an order. Number the nodes in the order the DFS first enters them:

```cpp
int timer = 0;
void dfs(int u) {
    tin[u] = timer++;              // entry time
    for (int c : children[u]) dfs(c);
    tout[u] = timer - 1;           // the largest entry time inside u's subtree
}
```

This numbering is the **Euler tour** (or DFS order) of the tree.
"""),
            Short(r"""
Tree: 1 has children 2 and 3; 2 has children 4 and 6; 3 has child 5; 5 has child 7.
Children are visited in increasing order. List the nodes in the order the DFS enters them.
""", accept=["1 2 4 6 3 5 7", "1, 2, 4, 6, 3, 5, 7"], placeholder="seven nodes",
                explain=r"""
1, then all of 2's subtree (2, 4, 6), then all of 3's (3, 5, 7): `1 2 4 6 3 5 7`. So
`tin = 0, 1, 4, 2, 5, 3, 6` for nodes 1..7.
"""),
            Short(r"""
Same tree. What are `tin[2]` and `tout[2]`? Answer as two numbers.
""", accept=["1 3", "1, 3", "(1, 3)"], placeholder="tin tout",
                explain=r"""
2 is entered at time 1, and its subtree `{2, 4, 6}` occupies times 1, 2, 3. So the subtree
of 2 is exactly the nodes with entry time in `[1, 3]`.
"""),
            MCQ(r"""
Why is every subtree a contiguous block of entry times?
""", [
                Opt("Because the nodes of a subtree have consecutive labels.",
                    why="The subtree of 2 is `{2, 4, 6}`. Labels are arbitrary; entry times are not."),
                Opt("Any traversal order would do, BFS included.",
                    why="BFS order here is `1 2 3 4 6 5 7`: the subtree of 2 sits at positions 1, 3, 4, "
                        "with 3 in between. Only depth-first order keeps subtrees together."),
                Opt("Once DFS enters `u`, it visits nothing outside u's subtree until it has finished "
                    "all of it.", correct=True,
                    why="Yes. Entering `u` and leaving `u` bracket exactly the visits to u's descendants, "
                        "so they get the consecutive times `tin[u]..tout[u]`."),
            ]),
            MCQ(r"""
Which test says that `u` is an ancestor of `v` (or `v` itself), in O(1)?
""", [
                Opt("`tin[u] ≤ tin[v]`",
                    why="Everything entered after `u` passes this, including nodes in later subtrees: "
                        "`tin[2] = 1 ≤ tin[3] = 4`, but 2 is not an ancestor of 3."),
                Opt("`tin[u] ≤ tin[v] ≤ tout[u]`", correct=True,
                    why="Yes: `v` is in u's subtree exactly when its entry time is inside u's block."),
                Opt("`depth[u] < depth[v]`",
                    why="Depth alone cannot tell different branches apart."),
            ], explain=r"""
With this test, a subtree question becomes a range question on the array indexed by entry
time. For example, "change one salary, then total the salaries of a subtree" is a point
update and a range sum over `[tin[u], tout[u]]`: a Fenwick tree (algo15).
"""),
            Say(r"""
On a chain the recursion goes 2·10^5 deep, so here is the iterative version. The stack
holds the current path; `it[u]` remembers which child of `u` to visit next.

```cpp
vector<int> st = {1}, it(n + 1, 0);
tin[1] = timer++;
while (!st.empty()) {
    int u = st.back();
    if (it[u] < (int)children[u].size()) {
        int c = children[u][it[u]++];
        depth[c] = depth[u] + 1;
        tin[c] = timer++;
        st.push_back(c);
    } else {
        tout[u] = timer - 1;
        st.pop_back();
    }
}
```

Now the problem. Two different people are **`p`-th cousins** if they have the same `p`-th
ancestor. For `q ≤ 2·10^5` queries `(v, p)`, count the `p`-th cousins of `v`.
"""),
            Reflect(r"""
How do you answer `(v, p)` in O(log n), using binary lifting and the Euler tour? Assume
that for each depth you have the sorted list of the entry times of the nodes at that depth.
""", answer=r"""
Find `u`, the `p`-th ancestor of `v`, by lifting (if `p > depth[v]` the answer is 0). The
`p`-th cousins of `v` are the other nodes at `depth[v]` in u's subtree, and those are the
nodes at `depth[v]` whose entry time lies in `[tin[u], tout[u]]`. Two binary searches in
the list for `depth[v]` count them (`upper_bound(tout[u]) − lower_bound(tin[u])`); subtract
1 for `v` itself. The lists come out sorted for free if you append each node when the DFS
enters it.
"""),
            Numeric(r"""
In the tree above (1 → 2, 3; 2 → 4, 6; 3 → 5; 5 → 7), how many 2nd cousins does node 5
have?
""", answer=2,
                hint="The 2nd ancestor of 5 is 1. Which nodes share 5's depth?",
                explain=r"""
5's 2nd ancestor is 1, and the depth-2 nodes are 4, 6, 5 with entry times 2, 3, 5, all
inside `[tin[1], tout[1]] = [0, 6]`. That is 3 nodes, minus 5 itself: 2.
"""),
            Try("cousins", note="Lifting for the ancestor, an iterative DFS for entry times, binary "
                "search per depth."),
        ]),
        Part("Variants and limits", [
            MCQ(r"""
Queries now ask for the **longest single road** on the route from `a` to `b`. What do you
add to binary lifting?
""", [
                Opt("Store `mx[v]`, the longest road from town 1 to `v`, and answer `max(mx[a], mx[b])`.",
                    why="That includes the roads above the LCA, which are not on the route. And a maximum "
                        "cannot be 'subtracted' back out (algo01)."),
                Opt("Store `mx[v][j]`, the longest road on the `2^j` jump from `v`, built like `up`; "
                    "take the max over every jump made while lifting `a` and `b`.", correct=True,
                    why="Yes: `mx[v][j] = max(mx[v][j-1], mx[up[v][j-1]][j-1])`. Any associative "
                        "summary of a path (max, min, gcd, sum) can ride along with the jumps."),
                Opt("It cannot be done faster than walking the route.",
                    why="Jumps can carry any associative summary of the edges they skip."),
            ]),
            MCQ(r"""
An old contest gives `q = 10^6` LCA queries and a tight limit. What is the standard way to
answer each in O(1)?
""", [
                Opt("Cache every answer in a `map<pair<int,int>, int>`.",
                    why="Queries can all be different, and a map lookup is O(log q) anyway."),
                Opt("Write down the full DFS walk (2n − 1 visits, a node each time the DFS returns to "
                    "it); the LCA is the shallowest node visited between `a` and `b`. Answer that "
                    "range-minimum with a sparse table.", correct=True,
                    why="Yes: O(n log n) preprocessing, O(1) per query, and the sparse table is the first "
                        "thing algo15 builds."),
                Opt("Use a larger `LOG`.",
                    why="A larger table only means more (useless) levels; each query still loops over them."),
            ]),
            MCQ(r"""
Which of these problems does the Euler tour turn into an array problem?
""", [
                Opt("Add `x` to every node on the route from `a` to `b`.",
                    why="A route is not a contiguous block of entry times: it is made of two climbs. "
                        "That needs heavier machinery (heavy-light decomposition)."),
                Opt("Add `x` to every node in u's subtree; later ask for one node's value.", correct=True,
                    why="Yes: a range update on `[tin[u], tout[u]]` and a point query, exactly the "
                        "difference-array Fenwick tree of algo15."),
                Opt("Find the k-th ancestor.",
                    why="Ancestors are not a block of entry times either; that is what lifting is for."),
            ]),
        ]),
    ],
    problems=[KTH_BOSS, LOWEST_COMMON_BOSS, DISTANCE_QUERIES, COUSINS],
    cards=[
        Card(r"""Binary lifting: what is `up[v][j]` and how is it built?""",
             r"""The `2^j`-th ancestor of `v` (0 if none). `up[v][j] = up[up[v][j-1]][j-1]`, with `j` in the outer loop."""),
        Card(r"""How many levels does a lifting table need for n ≤ 2·10^5?""",
             r"""18 (2^18 = 262144 > 2·10^5). 18 · 2·10^5 `int`s ≈ 14.4 MB."""),
        Card(r"""k-th ancestor with binary lifting?""",
             r"""For each set bit `j` of `k`, `x = up[x][j]`. The order of the jumps does not matter. With `up[0][j] = 0`, overshooting gives 0."""),
        Card(r"""Why must the lifting table be built with `j` as the outer loop?""",
             r"""`up[v][j]` reads `up[w][j-1]` for an ancestor `w`; with `j` outside, all of level j−1 is done first, whatever the labels."""),
        Card(r"""LCA by binary lifting, the two phases?""",
             r"""Lift the deeper node by the depth difference; if equal, done. Else for `j` from high to low, jump both when `up[a][j] != up[b][j]`; answer `up[a][0]`."""),
        Card(r"""Why does the LCA loop jump only when `up[a][j] != up[b][j]`, and why high to low?""",
             r"""Different ancestors are still below the LCA (safe); equal ones may overshoot. High to low builds the unknown distance bit by bit, like a binary search."""),
        Card(r"""Distance between `a` and `b` in a weighted tree?""",
             r"""`d[a] + d[b] − 2·d[lca(a, b)]`, where `d` is the distance from the root (`long long`). Lift using depths in edges, not `d`."""),
        Card(r"""Euler tour: what are `tin`/`tout`, and what is a subtree?""",
             r"""DFS entry time, and the largest entry time inside the subtree. The subtree of `u` is exactly the nodes with `tin` in `[tin[u], tout[u]]`."""),
        Card(r"""O(1) ancestor test?""",
             r"""`u` is an ancestor of `v` (or equal) iff `tin[u] ≤ tin[v] ≤ tout[u]`."""),
        Card(r"""Count nodes at depth D in the subtree of `u`?""",
             r"""Keep, per depth, the sorted list of `tin`s (append during the DFS). Count those in `[tin[u], tout[u]]` with `upper_bound − lower_bound`."""),
        Card(r"""Iterative DFS that computes `tin`/`tout`?""",
             r"""A stack of nodes plus `it[u]`, the index of u's next child: if a child remains, enter it (set `tin`, push); else set `tout[u] = timer − 1` and pop."""),
    ],
)
