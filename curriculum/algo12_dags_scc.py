from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _edges_text(n, edges):
    return f"{n} {len(edges)}\n" + "".join(f"{a} {b}\n" for a, b in edges)


def _dag(rng, n, m, spread=0, first=False, last=False):
    """Random DAG on 1..n: a hidden topological order and m distinct edges pointing forward
    in it. `spread` > 0 keeps every edge short (long paths). `first`/`last` put 1 at the
    front and n at the back of the hidden order."""
    if n < 2:
        return []
    order = rng.sample(range(1, n + 1), n)
    if first:
        order.remove(1)
        order.insert(0, 1)
    if last:
        order.remove(n)
        order.append(n)
    m = min(m, n * (n - 1) // 2)
    seen, edges = set(), []
    tries = 0
    while len(edges) < m and tries < 20 * m + 100:
        tries += 1
        if spread:
            i = rng.randrange(n - 1)
            j = min(n - 1, i + rng.randint(1, spread))
        else:
            i, j = sorted(rng.sample(range(n), 2))
        a, b = order[i], order[j]
        if (a, b) in seen:
            continue
        seen.add((a, b))
        edges.append((a, b))
    rng.shuffle(edges)
    return edges


def _digraph(rng, n, m):
    """Any directed graph without self-loops; repeated edges allowed."""
    edges = []
    while len(edges) < m and n >= 2:
        a, b = rng.randint(1, n), rng.randint(1, n)
        if a != b:
            edges.append((a, b))
    return edges


def _swap_ends(n, edges):
    """Rename 1 <-> n."""
    f = lambda v: n if v == 1 else (1 if v == n else v)
    return [(f(a), f(b)) for a, b in edges]


def _relabel(rng, n, edges):
    name = [0] + rng.sample(range(1, n + 1), n)
    return [(name[a], name[b]) for a, b in edges]


def _ladder(n):
    """i -> i+1 and i -> i+2: the number of routes from 1 to n is a Fibonacci number."""
    edges = [(i, i + 1) for i in range(1, n)] + [(i, i + 2) for i in range(1, n - 1)]
    return edges


def _clusters(rng, n, m, size):
    """Groups of about `size` vertices, each closed into a directed cycle (plus chords),
    with extra edges only from earlier groups to later ones: many SCCs, a DAG between them."""
    order = rng.sample(range(1, n + 1), n)
    groups = [order[i:i + size] for i in range(0, n, size)]
    edges = []
    for g in groups:
        if len(g) > 1:
            edges += [(g[i], g[(i + 1) % len(g)]) for i in range(len(g))]
    while len(edges) < m:
        i, j = rng.randrange(len(groups)), rng.randrange(len(groups))
        if i == j:
            g = groups[i]
            if len(g) > 1:
                a, b = rng.sample(g, 2)
                edges.append((a, b))
            continue
        if i > j:
            i, j = j, i
        edges.append((rng.choice(groups[i]), rng.choice(groups[j])))
    rng.shuffle(edges)
    return edges


# course schedule
def _course_small(rng):
    n = rng.randint(1, 8)
    m = rng.randint(0, min(12, n * (n - 1)))
    if rng.random() < 0.5:
        edges = _dag(rng, n, m)
        if edges and rng.random() < 0.4:            # close a cycle somewhere
            a, b = rng.choice(edges)
            edges.append((b, a))
            rng.shuffle(edges)
        if edges and rng.random() < 0.3:            # a repeated requirement
            edges.append(rng.choice(edges))
    else:
        edges = _digraph(rng, n, m)
    return _edges_text(n, edges)


def _course_chain(rng, n):
    """Course i needs i+1 and i+2: the only order is n, n-1, ..., 1, and a scan over 1..n
    finds exactly one new course per pass."""
    edges = [(i + 1, i) for i in range(1, n)] + [(i + 2, i) for i in range(1, n - 1)]
    rng.shuffle(edges)
    return _edges_text(n, edges)


def _course_deep_cycle(rng, n, m):
    """A long DAG with one requirement pointing backwards across a stretch of the order."""
    order = list(range(1, n + 1))
    edges = [(order[i], order[i + 1]) for i in range(n - 1)]
    extra = _dag(rng, n, m - n, spread=3)
    edges += [(a, b) if a < b else (b, a) for a, b in extra]
    edges = edges[:m - 1]
    k = rng.randint(n // 2, n - 10)
    edges.append((k + 7, k))                         # k -> ... -> k+7 -> k
    edges = _relabel(rng, n, edges)
    rng.shuffle(edges)
    return _edges_text(n, edges)


# longest flight / game routes
def _flight_small(rng):
    n = rng.randint(2, 9)
    m = rng.randint(1, min(14, n * (n - 1) // 2))
    edges = _dag(rng, n, m, first=rng.random() < 0.7, last=rng.random() < 0.7)
    return _edges_text(n, edges)


def _flight_trap(rng, n):
    """1 -> n directly; a long chain 2 -> 3 -> ... -> n that city 1 cannot reach."""
    edges = [(1, n)] + [(i, i + 1) for i in range(2, n)]
    rng.shuffle(edges)
    return _edges_text(n, edges)


def _flight_big(rng, n, m, spread=0, impossible=False):
    edges = _dag(rng, n, m, spread=spread, first=True, last=True)
    if impossible:
        edges = _swap_ends(n, edges)                 # now n comes first and 1 last
    return _edges_text(n, edges)


def _ladder_text(rng, n):
    edges = _ladder(n)
    rng.shuffle(edges)
    return _edges_text(n, edges)


# planets
def _planets_small(rng):
    n = rng.randint(1, 8)
    m = rng.randint(0, 16) if n >= 2 else 0
    return _edges_text(n, _digraph(rng, n, m))


def _chain_text(rng, n):
    edges = _relabel(rng, n, [(i, i + 1) for i in range(1, n)])
    rng.shuffle(edges)
    return _edges_text(n, edges)


def _big_cycle_text(rng, n):
    order = rng.sample(range(1, n + 1), n)
    edges = [(order[i], order[(i + 1) % n]) for i in range(n)]
    rng.shuffle(edges)
    return _edges_text(n, edges)


# coins
def _coins_text(n, coins, edges):
    return (f"{n} {len(edges)}\n" + " ".join(map(str, coins)) + "\n"
            + "".join(f"{a} {b}\n" for a, b in edges))


def _coins_small(rng):
    n = rng.randint(1, 8)
    m = rng.randint(0, 14) if n >= 2 else 0
    hi = rng.choice([10, 10**9])
    return _coins_text(n, [rng.randint(1, hi) for _ in range(n)], _digraph(rng, n, m))


def _coins_big(rng, n, edges, hi):
    return _coins_text(n, [rng.randint(max(1, hi - 1000), hi) for _ in range(n)], edges)


# --------------------------------------------------------------------- checkers
def _check_order(inp, expected, got):
    it = inp.split()
    n, m = int(it[0]), int(it[1])
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    if e[0] == "IMPOSSIBLE":
        if g == ["IMPOSSIBLE"]:
            return True, ""
        return False, "the requirements contain a cycle; expected IMPOSSIBLE"
    if g[0] == "IMPOSSIBLE":
        return False, "a valid order exists, but you printed IMPOSSIBLE"
    if len(g) != n:
        return False, f"expected {n} courses, found {len(g)}"
    pos = [0] * (n + 1)
    for i, x in enumerate(g, 1):
        c = int(x)
        if not 1 <= c <= n:
            return False, f"{c} is not a course number"
        if pos[c]:
            return False, f"course {c} appears twice"
        pos[c] = i
    for j in range(m):
        a, b = int(it[2 + 2 * j]), int(it[3 + 2 * j])
        if pos[a] > pos[b]:
            return False, f"course {a} must come before course {b}"
    return True, ""


def _check_flight(inp, expected, got):
    it = inp.split()
    n, m = int(it[0]), int(it[1])
    es = {(int(it[2 + 2 * j]), int(it[3 + 2 * j])) for j in range(m)}
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    if e[0] == "IMPOSSIBLE":
        if g == ["IMPOSSIBLE"]:
            return True, ""
        return False, f"no route leads from 1 to {n}; expected IMPOSSIBLE"
    if g[0] == "IMPOSSIBLE":
        return False, "a route exists, but you printed IMPOSSIBLE"
    k = int(g[0])
    route = [int(x) for x in g[1:]]
    if len(route) != k:
        return False, f"you announced {k} cities but listed {len(route)}"
    if k < 2 or route[0] != 1 or route[-1] != n:
        return False, f"the route must start in city 1 and end in city {n}"
    for a, b in zip(route, route[1:]):
        if (a, b) not in es:
            return False, f"there is no flight from {a} to {b}"
    if k != int(e[0]):
        return False, f"your route visits {k} cities; the longest visits {e[0]}"
    return True, ""


def _check_kingdoms(inp, expected, got):
    n = int(inp.split()[0])
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    ke, kg = int(e[0]), int(g[0])
    le, lg = e[1:], [int(x) for x in g[1:]]
    if len(lg) != n:
        return False, f"expected {n} kingdom labels after k, found {len(lg)}"
    if kg != ke:
        return False, f"there are {ke} kingdoms, not {kg}"
    first_g, first_e = {}, {}
    for i in range(n):
        a, b = lg[i], le[i]
        if not 1 <= a <= kg:
            return False, f"planet {i + 1} has label {a}, outside 1..{kg}"
        if a in first_g and le[first_g[a]] != b:
            return False, (f"planets {first_g[a] + 1} and {i + 1} share label {a}, but they "
                           f"cannot reach each other in both directions")
        if b in first_e and lg[first_e[b]] != a:
            return False, (f"planets {first_e[b] + 1} and {i + 1} are in the same kingdom, "
                           f"but have different labels")
        first_g.setdefault(a, i)
        first_e.setdefault(b, i)
    return True, ""


# --------------------------------------------------------------------- problems
COURSE_SCHEDULE = Problem(
    id="course_schedule",
    title="Course Schedule",
    difficulty="easy",
    source="CSES 1679 - Course Schedule",
    complexity="O(n + m)",
    statement=r"""
You have to complete `n` courses, numbered 1 to `n`. There are `m` requirements of the
form "course `a` has to be completed before course `b`".

Find an order in which you can complete all the courses, or report that there is none.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): course `a`
must come before course `b`. The same requirement may be listed more than once.
""",
    output=r"""
Print `n` integers: the courses in an order that satisfies every requirement. Any valid
order is accepted.

If there is none, print `IMPOSSIBLE`.
""",
    samples=[
        Test("5 3\n1 2\n3 1\n4 5\n", "3 4 1 5 2\n"),
        Test("4 4\n1 2\n2 3\n3 4\n4 2\n", "IMPOSSIBLE\n",
             note="Course 1 can be taken, then nothing: 2, 3 and 4 wait for each other."),
    ],
    tests=[
        Test("1 0\n"),
        Test("2 3\n2 1\n2 1\n2 1\n"),
        Test("3 2\n1 2\n2 1\n"),
        Test("6 5\n6 5\n5 4\n4 3\n3 2\n2 1\n"),
        Test("5 4\n1 2\n2 3\n3 2\n4 5\n"),
    ],
    gens=[
        Gen("small random", _course_small, 18),
        Gen("medium DAG", lambda rng: _edges_text(2000, _dag(rng, 2000, 4000)), 2),
        Gen("medium long DAG", lambda rng: _edges_text(2000, _dag(rng, 2000, 4000, spread=3)), 1),
        Gen("medium with cycle", lambda rng: _course_deep_cycle(rng, 2000, 4000), 1),
        Gen("max chain, one course per pass", lambda rng: _course_chain(rng, 100000), 1, large=True),
        Gen("max random DAG", lambda rng: _edges_text(100000, _dag(rng, 100000, 200000)), 1,
            large=True),
        Gen("max long DAG", lambda rng: _edges_text(100000, _dag(rng, 100000, 200000, spread=3)),
            1, large=True),
        Gen("max with a deep cycle", lambda rng: _course_deep_cycle(rng, 100000, 200000), 1,
            large=True),
    ],
    checker=_check_order,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<int>> adj(n + 1);
    vector<int> indeg(n + 1, 0);             // prerequisites not yet taken
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        indeg[b]++;                          // a repeated requirement counts twice, and is
    }                                        // also released twice: consistent

    queue<int> q;
    for (int v = 1; v <= n; v++)
        if (indeg[v] == 0) q.push(v);
    vector<int> order;
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        order.push_back(u);
        for (int v : adj[u])
            if (--indeg[v] == 0) q.push(v);  // u was v's last missing prerequisite
    }

    if ((int)order.size() < n) {             // the rest wait on each other: a cycle
        cout << "IMPOSSIBLE\n";
        return 0;
    }
    for (int i = 0; i < n; i++) cout << order[i] << " \n"[i + 1 == n];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Repeated passes: take every course whose prerequisites are all taken.
int main() {
    int n, m;
    cin >> n >> m;
    vector<vector<int>> pre(n + 1);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        pre[b].push_back(a);
    }
    vector<char> done(n + 1, 0);
    vector<int> order;
    while ((int)order.size() < n) {
        bool progress = false;
        for (int c = 1; c <= n; c++) {
            if (done[c]) continue;
            bool ok = true;
            for (int a : pre[c])
                if (!done[a]) { ok = false; break; }
            if (ok) { done[c] = 1; order.push_back(c); progress = true; }
        }
        if (!progress) { cout << "IMPOSSIBLE\n"; return 0; }
    }
    for (int c : order) cout << c << ' ';
    cout << '\n';
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
    vector<vector<int>> pre(n + 1);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        pre[b].push_back(a);
    }
    vector<char> done(n + 1, 0);
    vector<int> order;
    while ((int)order.size() < n) {
        bool progress = false;
        for (int c = 1; c <= n; c++) {
            if (done[c]) continue;
            bool ok = true;
            for (int a : pre[c])
                if (!done[a]) { ok = false; break; }
            if (ok) { done[c] = 1; order.push_back(c); progress = true; }
        }
        if (!progress) { cout << "IMPOSSIBLE\n"; return 0; }
    }
    for (int c : order) cout << c << ' ';
    cout << '\n';
}
""",
    hints=[
        r"""A course can be taken once all its prerequisites are taken. After taking course `c`, which
courses can have become available? Only those that require `c`.""",
        r"""Keep `indeg[v]`, the number of untaken prerequisites of `v`. Start a queue with every
course whose count is 0; taking `u` decrements the count of each `v` in `adj[u]`, and a
count that reaches 0 joins the queue.""",
        r"""If the queue empties before all `n` courses are taken, the remaining ones wait on each
other in a cycle: print `IMPOSSIBLE`.""",
    ],
    editorial=r"""
Kahn's algorithm. Build `adj[a]` (the courses that need `a`) and `indeg[b]` (how many
prerequisites `b` still waits for). Every course with `indeg = 0` is available; take one,
decrement the counters of the courses that need it, and push any course whose counter
reaches 0. Each requirement is processed once, when its first course is taken: O(n + m).

If fewer than `n` courses come out, every remaining course has an untaken prerequisite
that is itself remaining; following prerequisites backwards from any of them never leaves
the remaining set, so it must repeat a course: a cycle, and no order exists. Printing the
partial order instead of `IMPOSSIBLE` is the classic WA.

Rescanning all courses until nothing changes is also correct, but on the chain test
(course `i` needs `i + 1`) each pass finds one course: about n^2 / 2 = 5·10^9 checks.
""",
)

LONGEST_FLIGHT = Problem(
    id="longest_flight_route",
    title="Longest Flight Route",
    difficulty="medium",
    source="CSES 1680 - Longest Flight Route",
    complexity="O(n + m)",
    statement=r"""
Uolevi has won a trip: any sequence of one-way flights from city 1 to city `n`, and he
wants it to visit as many cities as possible. The flight network has no cycles: no
sequence of flights ever returns to a city it has left.

Find a route from 1 to `n` that visits the most cities, or report that there is none.
""",
    input=r"""
The first line has two integers `n` and `m` (2 ≤ n ≤ 10^5, 1 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): a flight
from `a` to `b`. No flight is listed twice, and the flights contain no directed cycle.
""",
    output=r"""
If there is a route, print `k`, the number of cities on it (both ends included), and then
the `k` cities in order. Any route of maximum length is accepted.

Otherwise print `IMPOSSIBLE`.
""",
    samples=[
        Test("5 5\n1 2\n2 5\n1 3\n3 4\n4 5\n", "4\n1 3 4 5\n"),
        Test("6 5\n1 6\n2 3\n3 4\n4 5\n5 6\n", "2\n1 6\n",
             note="The chain 2-3-4-5-6 is longer, but city 1 cannot reach it."),
    ],
    tests=[
        Test("2 1\n1 2\n"),
        Test("2 1\n2 1\n"),
        Test("4 2\n1 2\n3 4\n"),
        Test("5 4\n2 1\n1 3\n3 5\n4 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _flight_small(rng), 18),
        Gen("medium random", lambda rng: _flight_big(rng, 300, 900), 2),
        Gen("medium long", lambda rng: _flight_big(rng, 300, 700, spread=3), 2),
        Gen("medium unreachable chain", lambda rng: _flight_trap(rng, 300), 1),
        Gen("max ladder", lambda rng: _ladder_text(rng, 100000), 1, large=True),
        Gen("max random", lambda rng: _flight_big(rng, 100000, 200000), 1, large=True),
        Gen("max long", lambda rng: _flight_big(rng, 100000, 200000, spread=4), 1, large=True),
        Gen("max impossible", lambda rng: _flight_big(rng, 100000, 200000, spread=4,
                                                      impossible=True), 1, large=True),
        Gen("max unreachable chain", lambda rng: _flight_trap(rng, 100000), 1, large=True),
    ],
    checker=_check_flight,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<int>> adj(n + 1);
    vector<int> indeg(n + 1, 0);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        indeg[b]++;
    }

    // topological order of the whole graph (Kahn)
    vector<int> order;
    queue<int> q;
    for (int v = 1; v <= n; v++)
        if (indeg[v] == 0) q.push(v);
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        order.push_back(u);
        for (int v : adj[u])
            if (--indeg[v] == 0) q.push(v);
    }

    // best[v]: most cities on a route 1 -> v; NEG: no route at all
    const int NEG = INT_MIN;
    vector<int> best(n + 1, NEG), par(n + 1, 0);
    best[1] = 1;
    for (int u : order) {
        if (best[u] == NEG) continue;        // unreachable from 1: never extend it
        for (int v : adj[u])
            if (best[u] + 1 > best[v]) {
                best[v] = best[u] + 1;
                par[v] = u;
            }
    }

    if (best[n] == NEG) {
        cout << "IMPOSSIBLE\n";
        return 0;
    }
    vector<int> route;
    for (int v = n; v != 1; v = par[v]) route.push_back(v);
    route.push_back(1);
    reverse(route.begin(), route.end());
    cout << route.size() << '\n';
    for (int i = 0; i < (int)route.size(); i++) cout << route[i] << " \n"[i + 1 == (int)route.size()];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Relax every flight until nothing improves (terminates: there are no cycles).
int main() {
    int n, m;
    cin >> n >> m;
    vector<int> A(m), B(m);
    for (int i = 0; i < m; i++) cin >> A[i] >> B[i];
    const int NEG = -1000000000;
    vector<int> best(n + 1, NEG), par(n + 1, 0);
    best[1] = 1;
    bool changed = true;
    while (changed) {
        changed = false;
        for (int i = 0; i < m; i++)
            if (best[A[i]] != NEG && best[A[i]] + 1 > best[B[i]]) {
                best[B[i]] = best[A[i]] + 1;
                par[B[i]] = A[i];
                changed = true;
            }
    }
    if (best[n] == NEG) { cout << "IMPOSSIBLE\n"; return 0; }
    vector<int> route;
    for (int v = n; v != 1; v = par[v]) route.push_back(v);
    route.push_back(1);
    reverse(route.begin(), route.end());
    cout << route.size() << '\n';
    for (int v : route) cout << v << ' ';
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// The recursion without memoisation: every route from a city is re-explored each time.
int n, m;
vector<vector<int>> adj;
vector<int> nxt;

int longest(int u) {                         // cities on the longest route u -> n, or -1
    if (u == n) return 1;
    int best = -1;
    for (int v : adj[u]) {
        int r = longest(v);
        if (r != -1 && r + 1 > best) { best = r + 1; nxt[u] = v; }
    }
    return best;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> m;
    adj.assign(n + 1, {});
    nxt.assign(n + 1, 0);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
    }
    int k = longest(1);
    if (k == -1) { cout << "IMPOSSIBLE\n"; return 0; }
    cout << k << '\n';
    for (int v = 1; ; v = nxt[v]) {
        cout << v << ' ';
        if (v == n) break;
    }
    cout << '\n';
}
""",
    hints=[
        r"""The best route into city `v` does not depend on what comes after `v`. Define `best[v]`,
the most cities on a route from 1 that ends at `v`.""",
        r"""`best[v] = 1 + max(best[u])` over flights `u → v`. Compute it in a topological order, so
every `best[u]` is final when `v` is reached; remember which `u` gave the maximum.""",
        r"""Cities that city 1 cannot reach must start at minus infinity, not 0; otherwise a long
chain that never touches city 1 wins.""",
    ],
    editorial=r"""
Longest path on a DAG. Take a topological order (Kahn's algorithm), set `best[1] = 1`
and `best[v] = −∞` for every other city, and scan the cities in order: for each city `u`
with a real value and each flight `u → v`, try `best[v] = best[u] + 1`, recording
`par[v] = u` on improvement. Every `best[u]` is final when it is used, because all flights
into `u` come from cities earlier in the order. O(n + m). Walk `par` back from `n` and
reverse to print the route.

The −∞ matters: with 0 as the starting value, a city that 1 cannot reach looks like the
start of a route. On the second sample `best[6]` would become 4 through the chain
2 → 3 → 4 → 5 → 6 instead of 2, and the parent walk would never arrive at city 1.

Without the table, the recursion "longest(u) = 1 + max longest(v)" explores every route
separately; on the ladder test (`i → i+1`, `i → i+2`) that is a Fibonacci number of routes
with about 20,899 digits.
""",
)

GAME_ROUTES = Problem(
    id="game_routes",
    title="Game Routes",
    difficulty="easy",
    source="CSES 1681 - Game Routes",
    complexity="O(n + m)",
    statement=r"""
A game has `n` levels connected by `m` one-way teleporters, and the teleporters contain no
cycle. You start at level 1 and want to reach level `n`.

In how many different ways can you do that? Two ways are different if they use a
different sequence of teleporters.
""",
    input=r"""
The first line has two integers `n` and `m` (2 ≤ n ≤ 10^5, 1 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): a
teleporter from `a` to `b`. No teleporter is listed twice, and there is no directed cycle.
""",
    output=r"""
Print the number of ways modulo 10^9 + 7.
""",
    samples=[
        Test("4 5\n1 2\n2 4\n1 3\n3 4\n1 4\n", "3\n"),
        Test("3 2\n2 1\n1 3\n", "1\n"),
    ],
    tests=[
        Test("2 1\n2 1\n"),
        Test("3 1\n2 3\n"),
        Test(_edges_text(100, _ladder(100)),
             note="About 3.5·10^20 routes, far past what a long long holds: reduce as you add."),
    ],
    gens=[
        Gen("small random", lambda rng: _flight_small(rng), 18),
        Gen("medium random", lambda rng: _flight_big(rng, 300, 900), 2),
        Gen("medium ladder", lambda rng: _ladder_text(rng, 300), 1),
        Gen("max ladder", lambda rng: _ladder_text(rng, 100000), 1, large=True),
        Gen("max random", lambda rng: _flight_big(rng, 100000, 200000), 1, large=True),
        Gen("max long", lambda rng: _flight_big(rng, 100000, 200000, spread=4), 1, large=True),
        Gen("max dense", lambda rng: _flight_big(rng, 1000, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const long long MOD = 1000000007;
    int n, m;
    cin >> n >> m;
    vector<vector<int>> adj(n + 1);
    vector<int> indeg(n + 1, 0);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        indeg[b]++;
    }
    queue<int> q;
    for (int v = 1; v <= n; v++)
        if (indeg[v] == 0) q.push(v);

    vector<long long> ways(n + 1, 0);        // ways[v]: routes 1 -> v, mod MOD
    ways[1] = 1;
    while (!q.empty()) {                     // Kahn's order is a topological order
        int u = q.front();
        q.pop();
        for (int v : adj[u]) {
            ways[v] = (ways[v] + ways[u]) % MOD;   // ways[u] is final: all of u's inputs came first
            if (--indeg[v] == 0) q.push(v);
        }
    }
    cout << ways[n] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// cnt[L][v]: routes from 1 to v with exactly L flights (no cycles, so L < n).
int main() {
    const long long MOD = 1000000007;
    int n, m;
    cin >> n >> m;
    vector<int> A(m), B(m);
    for (int i = 0; i < m; i++) cin >> A[i] >> B[i];
    vector<long long> cur(n + 1, 0), nxt(n + 1);
    cur[1] = 1;
    long long total = cur[n];
    for (int L = 1; L < n; L++) {
        fill(nxt.begin(), nxt.end(), 0);
        for (int i = 0; i < m; i++) nxt[B[i]] = (nxt[B[i]] + cur[A[i]]) % MOD;
        cur = nxt;
        total = (total + cur[n]) % MOD;
    }
    cout << total << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Count by plain recursion: every route is walked one by one.
const long long MOD = 1000000007;
int n, m;
vector<vector<int>> adj;

long long routes(int u) {
    if (u == n) return 1;
    long long s = 0;
    for (int v : adj[u]) s = (s + routes(v)) % MOD;
    return s;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> m;
    adj.assign(n + 1, {});
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
    }
    cout << routes(1) << '\n';
}
""",
    hints=[
        r"""Every route into level `v` arrives through exactly one last teleporter `u → v`.""",
        r"""`ways[v]` is the sum of `ways[u]` over teleporters `u → v`, with `ways[1] = 1`.
Compute it in topological order, and reduce modulo 10^9 + 7 after every addition.""",
    ],
    editorial=r"""
Counting paths on a DAG is the longest-path DP with `+` in place of `max`: `ways[1] = 1`,
and in topological order `ways[v] = Σ ways[u]` over teleporters `u → v`. Levels that 1
cannot reach keep 0, which is exactly right for counting. Doing the additions while
running Kahn's algorithm works because a level is popped only after all of its incoming
teleporters have been processed. O(n + m).

The counts grow like Fibonacci numbers on the ladder test (`i → i+1`, `i → i+2`): already
at `n = 100` there are about 3.5·10^20 routes, and at `n = 10^5` about 20,899 digits. Take
the modulo at every addition; in `long long` the sum of two residues is safe.
""",
)

PLANETS_KINGDOMS = Problem(
    id="planets_kingdoms",
    title="Planets and Kingdoms",
    difficulty="medium",
    source="CSES 1683 - Planets and Kingdoms",
    complexity="O(n + m)",
    statement=r"""
A game has `n` planets connected by `m` one-way teleporters. Two planets belong to the same
kingdom exactly when you can travel from each of them to the other, possibly through
other planets.

Find the kingdoms.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): a
teleporter from `a` to `b`. The same teleporter may be listed more than once.
""",
    output=r"""
First print `k`, the number of kingdoms. Then print `n` integers between 1 and `k`: the
kingdom of each planet, so that two planets get the same number exactly when they are in
the same kingdom. Any such numbering is accepted.
""",
    samples=[
        Test("5 6\n1 2\n2 3\n3 1\n3 4\n4 5\n5 4\n", "2\n1 1 1 2 2\n"),
        Test("3 2\n1 2\n2 3\n", "3\n1 2 3\n",
             note="1 reaches 3, but 3 does not reach 1: three kingdoms."),
    ],
    tests=[
        Test("1 0\n"),
        Test("2 2\n1 2\n2 1\n"),
        Test("2 1\n1 2\n"),
        Test("7 10\n1 2\n2 3\n3 1\n3 4\n4 5\n5 6\n6 4\n6 7\n7 5\n2 7\n"),
    ],
    gens=[
        Gen("small random", _planets_small, 18),
        Gen("medium random", lambda rng: _edges_text(500, _digraph(rng, 500, 700)), 2),
        Gen("medium clusters", lambda rng: _edges_text(600, _clusters(rng, 600, 1200, 7)), 2),
        Gen("max chain", lambda rng: _chain_text(rng, 100000), 1, large=True),
        Gen("max one cycle", lambda rng: _big_cycle_text(rng, 100000), 1, large=True),
        Gen("max random", lambda rng: _edges_text(100000, _digraph(rng, 100000, 200000)), 1,
            large=True),
        Gen("max clusters", lambda rng: _edges_text(100000, _clusters(rng, 100000, 200000, 5)),
            1, large=True),
    ],
    checker=_check_kingdoms,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n, m;
vector<vector<int>> g, rg;                   // rg: every teleporter reversed
vector<int> order, comp;
vector<char> vis;

void dfs1(int u) {                           // pass 1 on g: record finishing order
    vis[u] = 1;
    for (int v : g[u])
        if (!vis[v]) dfs1(v);
    order.push_back(u);
}

void dfs2(int u, int c) {                    // pass 2 on rg: flood exactly one kingdom
    comp[u] = c;
    for (int v : rg[u])
        if (!comp[v]) dfs2(v, c);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> m;
    g.assign(n + 1, {});
    rg.assign(n + 1, {});
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        g[a].push_back(b);
        rg[b].push_back(a);
    }
    vis.assign(n + 1, 0);
    for (int v = 1; v <= n; v++)
        if (!vis[v]) dfs1(v);

    comp.assign(n + 1, 0);
    int k = 0;
    for (int i = n - 1; i >= 0; i--)         // latest finisher first: it sits in a source
        if (!comp[order[i]]) dfs2(order[i], ++k);   // kingdom, a sink once reversed

    cout << k << '\n';
    for (int v = 1; v <= n; v++) cout << comp[v] << " \n"[v == n];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// For each unlabelled planet: everything it reaches, intersected with everything that
// reaches it, is its kingdom.
int n, m;
vector<vector<int>> g, rg;

void bfs(const vector<vector<int>>& adj, int s, vector<char>& seen) {
    fill(seen.begin(), seen.end(), 0);
    queue<int> q;
    seen[s] = 1;
    q.push(s);
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        for (int v : adj[u])
            if (!seen[v]) { seen[v] = 1; q.push(v); }
    }
}

int main() {
    cin >> n >> m;
    g.assign(n + 1, {});
    rg.assign(n + 1, {});
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        g[a].push_back(b);
        rg[b].push_back(a);
    }
    vector<int> comp(n + 1, 0);
    vector<char> fwd(n + 1), bwd(n + 1);
    int k = 0;
    for (int v = 1; v <= n; v++) {
        if (comp[v]) continue;
        k++;
        bfs(g, v, fwd);
        bfs(rg, v, bwd);
        for (int u = 1; u <= n; u++)
            if (fwd[u] && bwd[u]) comp[u] = k;
    }
    cout << k << '\n';
    for (int v = 1; v <= n; v++) cout << comp[v] << ' ';
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int n, m;
vector<vector<int>> g, rg;

void bfs(const vector<vector<int>>& adj, int s, vector<char>& seen) {
    fill(seen.begin(), seen.end(), 0);
    queue<int> q;
    seen[s] = 1;
    q.push(s);
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        for (int v : adj[u])
            if (!seen[v]) { seen[v] = 1; q.push(v); }
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> m;
    g.assign(n + 1, {});
    rg.assign(n + 1, {});
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        g[a].push_back(b);
        rg[b].push_back(a);
    }
    vector<int> comp(n + 1, 0);
    vector<char> fwd(n + 1), bwd(n + 1);
    int k = 0;
    for (int v = 1; v <= n; v++) {
        if (comp[v]) continue;
        k++;
        bfs(g, v, fwd);
        bfs(rg, v, bwd);
        for (int u = 1; u <= n; u++)
            if (fwd[u] && bwd[u]) comp[u] = k;
    }
    cout << k << '\n';
    for (int v = 1; v <= n; v++) cout << comp[v] << ' ';
    cout << '\n';
}
""",
    hints=[
        r"""A DFS started inside a kingdom that no teleporter *leaves* visits exactly that kingdom.
How do you find such a starting planet?""",
        r"""Run a DFS over the whole graph and record finishing order. The planet that finishes last
lies in a kingdom that no teleporter *enters* from outside. Reversing every teleporter turns
that kingdom into one that nothing leaves.""",
        r"""Kosaraju: second DFS on the reversed graph, taking start planets in decreasing finishing
order; each new start labels one whole kingdom.""",
    ],
    editorial=r"""
Kingdoms are the strongly connected components. Kosaraju's algorithm finds them with two
DFS passes, O(n + m):

1. DFS over the whole graph, appending each planet to `order` when it finishes.
2. On the reversed graph, go through `order` from the end; every planet not yet labelled
   starts a DFS that labels a new kingdom.

Why it works. If a teleporter goes from kingdom C to a different kingdom D, the latest
finishing time in C is later than every finishing time in D (entering C first, DFS
finishes all of D before leaving C; entering D first, it cannot reach C at all). So the
planet with the latest finishing time lies in a kingdom with no teleporter coming in, and
in the reversed graph nothing goes out of it: the second DFS labels exactly that kingdom.
Among the remaining planets the same argument repeats.

Both passes recurse up to 10^5 deep on the chain test, fine with a large stack; an
explicit stack avoids the question. Checking "reaches and is reached by" separately from
every planet costs O(n·(n + m)), about 10^10 steps on the same chain.
""",
)

COIN_COLLECTOR = Problem(
    id="coin_collector",
    title="Coin Collector",
    difficulty="hard",
    source="CSES 1686 - Coin Collector",
    complexity="O(n + m)",
    statement=r"""
A maze has `n` rooms and `m` one-way tunnels. Room `i` holds `k_i` coins. You may start in
any room, walk through tunnels as long as you like (entering rooms and using tunnels as
often as you want), and stop in any room. The coins of every room you enter are yours; a
room's coins can of course be taken only once.

What is the largest number of coins you can collect?
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2·10^5).

The second line has `n` integers k_1, ..., k_n (1 ≤ k_i ≤ 10^9).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): a tunnel
from `a` to `b`. The same tunnel may be listed more than once.
""",
    output=r"""
Print one integer: the maximum number of coins.
""",
    samples=[
        Test("4 4\n4 5 2 7\n1 2\n2 1\n1 3\n2 4\n", "16\n"),
        Test("5 7\n1 2 3 4 5\n1 2\n2 1\n2 3\n3 4\n4 3\n1 5\n5 4\n", "15\n",
             note="Rooms 1-2 and 3-4 are each one loop: collect all of a loop before moving on."),
    ],
    tests=[
        Test("1 0\n1000000000\n"),
        Test("3 0\n5 9 2\n"),
        Test("3 3\n1000000000 1000000000 1000000000\n1 2\n2 3\n3 1\n"),
        Test("4 3\n10 1 1 1\n2 3\n3 4\n4 1\n"),
    ],
    gens=[
        Gen("small random", _coins_small, 20),
        Gen("max random, big coins", lambda rng: _coins_big(
            rng, 100000, _digraph(rng, 100000, 200000), 10**9), 1, large=True),
        Gen("max clusters", lambda rng: _coins_big(
            rng, 100000, _clusters(rng, 100000, 200000, 6), 10**9), 1, large=True),
        Gen("max one cycle", lambda rng: _coins_text(
            100000, [10**9] * 100000,
            [(i, i % 100000 + 1) for i in range(1, 100001)]), 1, large=True),
        Gen("max ladder DAG", lambda rng: _coins_big(rng, 100000, _ladder(100000), 10**9), 1,
            large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n, m;
vector<vector<int>> g, rg;
vector<int> order, comp;
vector<char> vis;

void dfs1(int u) {
    vis[u] = 1;
    for (int v : g[u])
        if (!vis[v]) dfs1(v);
    order.push_back(u);
}

void dfs2(int u, int c) {
    comp[u] = c;
    for (int v : rg[u])
        if (!comp[v]) dfs2(v, c);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> m;
    vector<long long> coins(n + 1);
    for (int i = 1; i <= n; i++) cin >> coins[i];
    g.assign(n + 1, {});
    rg.assign(n + 1, {});
    vector<pair<int, int>> edges(m);
    for (auto& [a, b] : edges) {
        cin >> a >> b;
        g[a].push_back(b);
        rg[b].push_back(a);
    }

    // Kosaraju: components come out numbered in topological order of the condensation
    vis.assign(n + 1, 0);
    for (int v = 1; v <= n; v++)
        if (!vis[v]) dfs1(v);
    comp.assign(n + 1, 0);
    int k = 0;
    for (int i = n - 1; i >= 0; i--)
        if (!comp[order[i]]) dfs2(order[i], ++k);

    // one weighted vertex per component; keep only edges between different components
    vector<long long> sum(k + 1, 0);
    for (int v = 1; v <= n; v++) sum[comp[v]] += coins[v];
    vector<vector<int>> cadj(k + 1);
    for (auto [a, b] : edges)
        if (comp[a] != comp[b]) cadj[comp[a]].push_back(comp[b]);

    // every condensed edge goes from a smaller id to a larger one: fill best[] backwards
    vector<long long> best(k + 1, 0);
    long long ans = 0;
    for (int c = k; c >= 1; c--) {
        long long after = 0;
        for (int d : cadj[c]) after = max(after, best[d]);
        best[c] = sum[c] + after;            // take the whole component, then the best way on
        ans = max(ans, best[c]);
    }
    cout << ans << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Search over (room, set of rooms already emptied), n <= 8.
int main() {
    int n, m;
    cin >> n >> m;
    vector<long long> coins(n);
    for (auto& x : coins) cin >> x;
    vector<vector<int>> g(n);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        g[a - 1].push_back(b - 1);
    }
    vector<vector<char>> seen(n, vector<char>(1 << n, 0));
    vector<pair<int, int>> st;
    for (int v = 0; v < n; v++) { seen[v][1 << v] = 1; st.push_back({v, 1 << v}); }
    long long best = 0;
    while (!st.empty()) {
        auto [u, mask] = st.back();
        st.pop_back();
        long long s = 0;
        for (int i = 0; i < n; i++) if (mask >> i & 1) s += coins[i];
        best = max(best, s);
        for (int v : g[u]) {
            int nm = mask | 1 << v;
            if (!seen[v][nm]) { seen[v][nm] = 1; st.push_back({v, nm}); }
        }
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""Inside one strongly connected component you can visit every room and still leave through
any tunnel you like. So each component behaves like one room worth the sum of its coins.""",
        r"""Shrink every SCC to a single vertex (Kosaraju or Tarjan). The result has no cycles.""",
        r"""On that DAG, `best[c] = sum[c] + max(best[d])` over edges `c → d` is a longest weighted
path. Kosaraju numbers components in topological order, so fill `best` from the last id
down. Sums reach 10^14: `long long`.""",
    ],
    editorial=r"""
Within a strongly connected component every room reaches every other, so once you enter a
component you can collect all of it and still leave by any of its outgoing tunnels. So
replace each component by one vertex worth the sum of its coins. The resulting
*condensation* is a DAG (a cycle through two components would merge them into one), and
the answer is the heaviest path in it: `best[c] = sum[c] + max(0, max best[d])` over
condensed edges `c → d`, maximised over all `c`.

Kosaraju's second pass discovers the components in topological order of the condensation:
the first component found contains the latest finisher, which lies in a source. So every
condensed edge goes from a smaller id to a larger one, and filling `best` from `k` down to
1 respects every dependency. O(n + m).

Sums reach 10^5 · 10^9 = 10^14: `int` fails already on the three-room test with 10^9 coins
each.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo12",
    title="DAGs: topological order, DP on DAGs, SCC",
    track="algo",
    order=12,
    summary="Ordering tasks that depend on each other (Kahn and DFS), longest and counted "
            "paths as DP on a DAG, and strongly connected components for graphs with cycles.",
    prereqs=["algo09", "algo06"],
    tags=["dag", "topological sort", "kahn", "dfs order", "cycle detection", "dp on dag",
          "longest path", "counting paths", "scc", "kosaraju", "condensation"],
    parts=[
        Part("An order that respects every arrow", [
            Say(r"""
Many problems hide a graph whose arrows mean "before": a course before another, a task
before the task that uses its result, a table cell before the cells computed from it.

**Course Schedule** (CSES 1679): `n ≤ 10^5` courses and `m ≤ 2·10^5` requirements of the
form "course `a` before course `b`". Print an order that satisfies every requirement, or
`IMPOSSIBLE`.

Each requirement is a directed edge `a → b`, and you want to list the vertices so that
every edge points forward. Such a list is a **topological order**. A directed graph with no
cycle is a **DAG** (directed acyclic graph).
"""),
            Numeric(r"""
The most direct brute force tries every order of the courses and checks the requirements.
With only `n = 20` courses, how many orders are there?
""", answer=2432902008176640000, rel=0.5, unit="orders",
                explain=r"""
`20! ≈ 2.4·10^18`, decades of computing, for twenty courses.
"""),
            Say(r"""
A smarter brute force: make passes over the courses, and in each pass take every course
whose prerequisites have all been taken. Stop when every course is taken, or when a whole
pass takes nothing.
"""),
            Numeric(r"""
One pass looks at every remaining course and its requirements: about `n + m = 3·10^5`
steps. On a chain where each course unlocks only the next, and the next always sits
earlier in the scan, each pass takes a single course, so there are `n = 10^5` passes.
About how many steps is that?
""", answer=3e10, rel=0.5, unit="steps",
                explain=r"""
`10^5 · 3·10^5 = 3·10^10`, half a minute or more. Almost every pass re-examines courses
whose situation has not changed since the previous pass.
"""),
            Reflect(r"""
Taking course `c` can change the situation of only a few courses. Which ones? What would
you keep for each course so that you never rescan?
""", answer=r"""
Only the courses that require `c` (the out-neighbours of `c`) can become available, and
only when `c` was their last untaken prerequisite. So keep, for every course, the number
of prerequisites it is still waiting for (its in-degree at the start). Taking `c`
decrements the counters of its out-neighbours; a counter that reaches 0 means that course
is now available, so it goes into a queue. Each requirement is handled once, when its
first course is taken: O(n + m). This is **Kahn's algorithm**.
"""),
            Say(r"""
```cpp
vector<vector<int>> adj(n + 1);
vector<int> indeg(n + 1, 0);
for (int i = 0; i < m; i++) {
    int a, b;
    cin >> a >> b;
    adj[a].push_back(b);                 // a before b
    indeg[b]++;
}
queue<int> q;
for (int v = 1; v <= n; v++)
    if (indeg[v] == 0) q.push(v);        // no prerequisites at all
vector<int> order;
while (!q.empty()) {
    int u = q.front();
    q.pop();
    order.push_back(u);
    for (int v : adj[u])
        if (--indeg[v] == 0) q.push(v);  // u was v's last missing prerequisite
}
```
"""),
            Short(r"""
Six courses, requirements read in the order `3 1`, `3 2`, `1 4`, `2 4`, `5 2`, `4 6`. The
queue starts with the free courses in increasing order and is first-in first-out. In what
order does Kahn's algorithm take the courses?
""", accept=["3 5 1 2 4 6", "3,5,1,2,4,6", "3, 5, 1, 2, 4, 6", "[3, 5, 1, 2, 4, 6]"],
                placeholder="six courses",
                hint="The free courses at the start are 3 and 5. Taking 3 frees 1, but does it free 2?",
                explain=r"""
`3 5 1 2 4 6`. Taking 3 frees 1 but not 2, which still waits for 5. Taking 5 frees 2. Then
1 (4 still waits for 2), 2 (frees 4), 4 (frees 6), 6.
"""),
            MCQ(r"""
On some input the queue empties after only 7 of the 10 courses. What does that prove?
""", [
                Opt("The free courses were pushed in an unlucky order; another order would finish.",
                    why="A counter drops once per taken prerequisite whatever the order, so the "
                        "set of courses that ever reach 0 is the same for every queue order."),
                Opt("Some course without prerequisites was never pushed.",
                    why="All of them are pushed before the loop starts."),
                Opt("The 3 remaining courses contain a cycle of requirements, so no order exists.",
                    correct=True,
                    why="Right. Each remaining course waits for a remaining course. Walk backwards "
                        "from any of them, prerequisite of prerequisite of ...: the walk never "
                        "leaves the 3 remaining courses, so it repeats one. That is a cycle, and "
                        "no order can put each course of a cycle before the next."),
            ], explain=r"""
So Kahn's algorithm is also a cycle detector: `order.size() < n` exactly when the graph has
a directed cycle. Printing the partial order instead of `IMPOSSIBLE` is the classic Wrong
Answer here.
"""),
            Try("course_schedule", note="Kahn's algorithm, and the `order.size() < n` test. Any "
                "valid order is accepted."),
        ]),
        Part("The same order from DFS", [
            Say(r"""
DFS gives a second way to a topological order, and its idea returns later in this lesson.
Run DFS over the whole graph (an outer loop over all vertices, as in algo09) and write each
vertex down when DFS **finishes** it, that is, after everything it points to has been fully
explored. Claim: the finishing order, reversed, is a topological order.

```cpp
void dfs(int u) {
    visited[u] = 1;
    for (int v : adj[u])
        if (!visited[v]) dfs(v);
    order.push_back(u);          // u finishes after everything it points to
}
// for (v = 1..n) if (!visited[v]) dfs(v);   then reverse(order)
```
"""),
            MCQ(r"""
The claim needs: for every edge `u → v`, `v` finishes before `u`. When DFS at `u` looks at
`v`, the vertex `v` is in one of three states. Which one would break the claim, and why
can it not happen in a DAG?
""", [
                Opt("`v` not yet visited: DFS visits it later than `u`, so it finishes later.",
                    why="DFS goes into `v` right now and finishes it completely before returning "
                        "to `u`. `v` finishes first; this case is fine."),
                Opt("`v` started but not finished (on the current DFS path): then `v` finishes "
                    "after `u`, but `v` on the path means `v → ... → u`, and with `u → v` that "
                    "is a cycle.", correct=True,
                    why="Exactly. In a DAG this state never occurs, so every edge goes from a "
                        "later finisher to an earlier one, and the reversed finishing order "
                        "puts every edge forward."),
                Opt("`v` already finished: two finished branches can come out in any order.",
                    why="`v` is finished and `u` is not, so `v` finished first. Fine."),
            ], explain=r"""
This is also how DFS detects cycles in a directed graph, the question left open in algo09.
Colour vertices white (unvisited), grey (on the current path) and black (finished). An edge
to a grey vertex closes a cycle; an edge to a black vertex does not. That is why "already
visited" alone raised a false alarm on `1→2, 1→3, 3→2`: vertex 2 was black.
"""),
            Short(r"""
Vertices 1..6, edges read in the order `1 2`, `1 3`, `2 4`, `3 4`, `4 5`, `6 3`. DFS with the
outer loop over 1..6 and neighbours in list order. What is the finishing order, *reversed*?
""", accept=["6 1 3 2 4 5", "6,1,3,2,4,5", "6, 1, 3, 2, 4, 5", "[6, 1, 3, 2, 4, 5]"],
                placeholder="six vertices",
                hint="From 1, DFS goes 1 → 2 → 4 → 5 first. Who finishes first?",
                explain=r"""
DFS from 1 walks 1 → 2 → 4 → 5; then 5, 4 and 2 finish; then 3 (4 is already black) and 1.
The outer loop then starts at 6, which finishes last. Finishing order `5 4 2 3 1 6`,
reversed `6 1 3 2 4 5`. Check the edge `6 → 3`: 6 comes first because it finished last,
even though DFS found it last.
"""),
            MCQ(r"""
Why not use the order in which DFS first *visits* the vertices (preorder)? Take the edges
`1 3`, `1 2`, `2 3`, read in that order, and DFS from 1.
""", [
                Opt("Preorder works too: DFS starts from a vertex with no incoming edges.",
                    why="Here `adj[1] = [3, 2]`, so preorder is 1, 3, 2, and the edge `2 → 3` "
                        "points backwards."),
                Opt("Preorder fails only on graphs that have a cycle.",
                    why="This graph has no cycle, and preorder still fails on it."),
                Opt("Preorder is 1, 3, 2 here, which breaks the edge `2 → 3`.", correct=True,
                    why="Right. Being visited early says nothing about who must come before you; "
                        "finishing late guarantees that everything you point to is already done."),
            ]),
        ]),
        Part("Longest and counted routes on a DAG", [
            Say(r"""
**Longest Flight Route** (CSES 1680): `n ≤ 10^5` cities, `m ≤ 2·10^5` one-way flights, and
no sequence of flights ever returns to a city. Find a route from city 1 to city `n` that
visits as many cities as possible and print it, or `IMPOSSIBLE`.

In a general graph, "longest simple path" is one of the famous hard problems. The missing
cycles change everything.
"""),
            Numeric(r"""
The brute force follows every route out of city 1. Take the *ladder*: cities 1..60, with
flights `i → i+1` and `i → i+2`. The number of routes from `i` to 60 is the number from
`i+1` plus the number from `i+2`, a Fibonacci recurrence: each step back towards city 1
multiplies the count by about 1.6. Roughly how many routes go from 1 to 60?
""", answer=1548008755920, rel=0.9, unit="routes",
                hint="From city 59 there is 1 route; about 59 steps of ×1.6 lead back to city 1.",
                explain=r"""
About 1.5·10^12 (it is exactly the 60th Fibonacci number, 1,548,008,755,920). With `n =
10^5` the count has about 20,899 digits: no enumeration can survive this graph, which has
only 2n edges.
"""),
            Reflect(r"""
Most of those routes share long beginnings. What does the brute force compute again and
again, and what single number per city would stop it?
""", answer=r"""
Every route through city `v` re-derives the best way to get from 1 to `v`, although that
does not depend on what happens after `v`. Compute it once: `best[v]`, the most cities on a
route from 1 that ends at `v`, is `1 + max best[u]` over the flights `u → v`. That needs
every `best[u]` to be final before `v` is computed, which is exactly a topological order.
It is the DP of algo06, where the DAG is the graph of states and "the right order to fill
the table" is a topological order. O(n + m).
"""),
            Short(r"""
Cities 1..6, flights `1 2`, `1 3`, `2 3`, `3 4`, `2 5`, `5 6`, `4 6`, `3 6`. How many
cities does the longest route from 1 to 6 visit?
""", accept=["5", "five"], placeholder="a number",
                hint="Compute `best` for 1, 2, 3, 4, 5 in that order (it is a topological order).",
                explain=r"""
`best`: 1 → 1, 2 → 2, 3 → 3 (through 2), 4 → 4, 5 → 3, and 6 → 1 + max(best[5], best[4],
best[3]) = 5. Following the parents back gives the route `1 2 3 4 6`.
"""),
            MCQ(r"""
A tempting initialisation: `best[v] = 0` for every city, then `best[1] = 1`. The flights
are `1 5`, `2 3`, `3 4`, `4 5`, and `n = 5`. What happens?
""", [
                Opt("It prints 2 cities, the route `1 5`, which is correct.",
                    why="`best[2] = 0` looks like a real value, so `best[3] = 1`, `best[4] = 2`, "
                        "and `best[5] = max(2, 3) = 3`."),
                Opt("`best[5]` becomes 3 through `2 → 3 → 4 → 5`, a route that does not start at "
                    "1, and the walk back along the parents never reaches city 1.", correct=True,
                    why="Right. A city that 1 cannot reach must hold −∞ (no route at all) and "
                        "must never be extended. The starting value matters as much as the "
                        "recurrence."),
                Opt("It crashes, because `best[2]` is never assigned.",
                    why="`best[2]` is assigned, to 0, and that is the problem: 0 looks like a "
                        "legal value."),
            ]),
            MCQ(r"""
Why can't the same DP find the longest *simple* route in a graph that has cycles?
""", [
                Opt("It can: just ignore the edge that closes each cycle.",
                    why="Which edge to ignore depends on the route. On the cycle `a → b → c → a`, "
                        "a route entering at `a` must drop `c → a`, one entering at `b` must drop "
                        "`a → b`."),
                Opt("With a cycle, no order makes every `best[u]` final before `best[v]`; staying "
                    "simple would need the set of visited cities in the state.", correct=True,
                    why="Right: 2^n states, the bitmask DP of algo08 (Hamiltonian Flights), fine "
                        "for `n ≤ 20`. A DAG is exactly what makes one number per vertex enough."),
                Opt("Negate the lengths and run Dijkstra.",
                    why="Dijkstra breaks on negative edges (algo10), and with cycles the negated "
                        "graph has negative cycles, where 'shortest' is not even defined."),
            ]),
            Try("longest_flight_route", note="Topological order, −∞ for unreachable cities, parents "
                "for the route. Any longest route is accepted."),
            Say(r"""
**Game Routes** (CSES 1681) keeps the graph and changes the question: *how many* routes
lead from 1 to `n`, modulo 10^9 + 7? Replace max by sum. `ways[1] = 1`, and in topological
order `ways[v]` is the sum of `ways[u]` over the flights `u → v`. Cities that 1 cannot reach
stay at 0, which is exactly right for counting.
"""),
            Short(r"""
In the six-city example above (flights `1 2`, `1 3`, `2 3`, `3 4`, `2 5`, `5 6`, `4 6`,
`3 6`), how many different routes go from 1 to 6?
""", accept=["5", "five"], placeholder="a number",
                explain=r"""
`ways`: 1 → 1, 2 → 1, 3 → 2 (direct, or through 2), 4 → 2, 5 → 1, 6 → 1 + 2 + 2 = 5. The
routes: `1 2 3 4 6`, `1 3 4 6`, `1 2 3 6`, `1 3 6`, `1 2 5 6`.
"""),
            Try("game_routes", note="Same order, sum instead of max, modulo at every addition."),
        ]),
        Part("Strongly connected components", [
            Say(r"""
Now let the graph have cycles. **Planets and Kingdoms** (CSES 1683): `n ≤ 10^5` planets,
`m ≤ 2·10^5` one-way teleporters. Two planets are in the same kingdom when each can reach
the other. Label the kingdoms.

Mutual reachability splits every directed graph into **strongly connected components**
(SCCs). Inside one, every vertex reaches every other; between two of them, travel goes at
most one way.
"""),
            Numeric(r"""
The direct method: BFS from every planet to learn what it reaches, then group the planets
that reach each other. With `n = 10^5` searches of about `n + m = 3·10^5` steps each, how
many steps is that?
""", answer=3e10, rel=0.5, unit="steps",
                explain=r"""
`3·10^10`, and a `10^5 × 10^5` reachability table would not even fit in memory. We want
one or two DFS passes in total.
"""),
            MCQ(r"""
Suppose you start a DFS from a planet in a kingdom that **no teleporter leaves** (every
teleporter out of it stays inside it). What does that DFS visit?
""", [
                Opt("The kingdom plus everything downstream of it.",
                    why="There is nothing downstream: no teleporter leaves the kingdom."),
                Opt("Possibly only part of the kingdom.",
                    why="Every planet of a kingdom is reachable from every other, so DFS gets "
                        "them all."),
                Opt("Exactly that kingdom.", correct=True,
                    why="Right. If we could always start inside such a 'sink' kingdom and then "
                        "pretend it was deleted, repeated DFS would peel off one kingdom per "
                        "start."),
            ]),
            Say(r"""
Finding a sink kingdom is the whole difficulty, and finishing times solve it. Run a first
DFS over the whole graph and record the finishing order, exactly as for the topological
sort.
"""),
            MCQ(r"""
Kingdoms `C` and `D` are different, and some teleporter goes from `C` to `D`. Compare the
latest finishing time in `C` with the latest in `D`.
""", [
                Opt("`C`'s is later.", correct=True,
                    why="If DFS enters C first, it reaches all of D through that teleporter and "
                        "finishes D before finishing the first C planet. If it enters D first, "
                        "it cannot reach C (else C and D would be one kingdom), so D is done "
                        "before C is even entered. Either way C finishes last."),
                Opt("`D`'s is later, since D is downstream.",
                    why="Downstream vertices finish *earlier*: the same fact that made reversed "
                        "finishing order a topological order."),
                Opt("It depends on where the DFS starts.",
                    why="Check both cases, entering C first or D first: C finishes last in both."),
            ]),
            Reflect(r"""
So the planet with the latest finishing time lies in a kingdom that no teleporter *enters*
from another kingdom (a source). We wanted one that no teleporter *leaves*. How do you turn
the one into the other?
""", answer=r"""
Reverse every teleporter. The kingdoms stay the same (mutual reachability does not care
about direction), but sources become sinks. So a DFS on the reversed graph, started from
the planet with the latest finishing time, visits exactly its kingdom. Then take the
unlabelled planet with the next latest finishing time: among the remaining kingdoms it is
again in a source of the original graph, a sink of the reversed one, and the argument
repeats. That is **Kosaraju's algorithm**: two DFS passes, O(n + m).
"""),
            Say(r"""
```cpp
vector<vector<int>> g(n + 1), rg(n + 1);  // read: g[a].push_back(b); rg[b].push_back(a);

void dfs1(int u) {                         // pass 1 on g: finishing order
    vis[u] = 1;
    for (int v : g[u]) if (!vis[v]) dfs1(v);
    order.push_back(u);
}
void dfs2(int u, int c) {                  // pass 2 on rg: one kingdom
    comp[u] = c;
    for (int v : rg[u]) if (!comp[v]) dfs2(v, c);
}
// for (v = 1..n) if (!vis[v]) dfs1(v);
// k = 0; for (i = n-1 down to 0) if (!comp[order[i]]) dfs2(order[i], ++k);
```

Both passes recurse up to `n = 10^5` deep, which this judge's 512 MB stack handles; algo09's
explicit-stack version works too. Tarjan's algorithm finds the same components in a single
pass using "low-link" values; either is fine in a contest.
"""),
            Short(r"""
Planets 1..7, teleporters `1 2`, `2 3`, `3 1`, `3 4`, `4 5`, `5 6`, `6 4`, `6 7`, `7 5`,
`2 7`. How many kingdoms are there?
""", accept=["2", "two"], placeholder="a number",
                hint="Find the cycles, then ask whether any route leads back from the second group "
                     "to the first.",
                explain=r"""
Two: `{1, 2, 3}` (the cycle 1 → 2 → 3 → 1) and `{4, 5, 6, 7}` (4 → 5 → 6 → 4, and 6 → 7 →
5 brings 7 in). The teleporters `3 → 4` and `2 → 7` lead from the first kingdom to the
second, and nothing leads back.
"""),
            MCQ(r"""
A bug: the second pass runs `dfs2` on `g` instead of `rg`, still in decreasing finishing
order. Take just two planets and the teleporter `1 → 2`. What happens?
""", [
                Opt("Nothing: SCCs are the same whichever way the edges point.",
                    why="The components are, but the peeling argument is not. Pass 1 finishes 2, "
                        "then 1, so pass 2 starts at 1, and on `g` it walks on to 2."),
                Opt("Planets 1 and 2 land in the same kingdom, which is wrong.", correct=True,
                    why="Right. Starting in a source and walking *forward* floods everything "
                        "downstream. The reversal is what turns the start into a sink."),
                Opt("It crashes on this input.",
                    why="It runs fine and prints one kingdom: a Wrong Answer, not a crash."),
            ]),
            Try("planets_kingdoms", note="Kosaraju. Any labelling of the kingdoms is accepted."),
        ]),
        Part("Condense, then DP", [
            Say(r"""
**Coin Collector** (CSES 1686): `n ≤ 10^5` rooms, room `i` holding `k_i ≤ 10^9` coins, and
`m ≤ 2·10^5` one-way tunnels. Start in any room, walk as long as you like (rooms and
tunnels can be reused), stop anywhere; every room you enter pays its coins once. Maximise
the coins.

With cycles, "longest path" is hopeless in general. But here repeating rooms is allowed,
and that changes the picture.
"""),
            MCQ(r"""
Once you are inside a strongly connected component, which of its rooms can you empty
before leaving it through a tunnel of your choice?
""", [
                Opt("Only the rooms on one simple path through the component.",
                    why="Rooms may be revisited, and inside an SCC every room reaches every "
                        "other: go round, collect, and come back to the room your exit starts "
                        "from."),
                Opt("All of them.", correct=True,
                    why="Right. So each SCC behaves like one room worth the sum of its coins."),
                Opt("Only the room you entered, since you cannot come back to it once you move.",
                    why="Inside an SCC every room can reach the room you entered."),
            ]),
            MCQ(r"""
Shrink every SCC to one vertex and keep the tunnels between different SCCs. Why is the
result, the **condensation**, always a DAG?
""", [
                Opt("Because the original graph was already a DAG.",
                    why="It was not; it can have any cycles. They all live inside the SCCs."),
                Opt("Because Kosaraju deletes the edges that close cycles.",
                    why="It deletes nothing. The edges between components simply cannot form a "
                        "cycle."),
                Opt("A cycle through two condensed vertices A and B would let every room of A reach "
                    "every room of B and back, so A and B would be one SCC.", correct=True,
                    why="Right. Every directed graph is a DAG of its SCCs, which is why SCCs are "
                        "the usual first step on graphs with cycles."),
            ], explain=r"""
A bonus: Kosaraju's second pass finds the components in topological order of the
condensation (the first one found contains the latest finisher, a source). So no separate
topological sort is needed: every condensed edge goes from a smaller component number to a
larger one.
"""),
            Short(r"""
Rooms 1..5 hold 1, 2, 3, 4, 5 coins. Tunnels: `1 2`, `2 1`, `2 3`, `3 4`, `4 3`, `1 5`,
`5 4`. What is the largest number of coins you can collect?
""", accept=["15"], placeholder="a number",
                hint="Find the SCCs first, then the heaviest path through the condensation.",
                explain=r"""
The SCCs are `{1, 2}` (3 coins), `{3, 4}` (7 coins) and `{5}` (5 coins), with condensed
edges `{1,2} → {3,4}`, `{1,2} → {5}` and `{5} → {3,4}`. The heaviest path is `{1,2} → {5} →
{3,4}`: 3 + 5 + 7 = 15, every coin in the maze.
"""),
            Numeric(r"""
How large can the answer get with `n = 10^5` rooms of 10^9 coins each?
""", answer=1e14, rel=0.1, unit="coins",
                explain=r"""
10^14, while an `int` stops at about 2.1·10^9. Component sums and the DP both need
`long long`; even three rooms of 10^9 coins overflow an `int`.
"""),
            Try("coin_collector", note="SCCs, sums per component, heaviest path on the condensation."),
        ]),
        Part("Seeing the DAG", [
            MCQ(r"""
Dice Combinations from algo06 counts the ways to write `n` as an ordered sum of throws 1..6
with `ways[s] = ways[s-1] + ... + ways[s-6]`. As a graph problem, what is it?
""", [
                Opt("A shortest-path problem, solved by BFS from 0.",
                    why="BFS finds the fewest throws that reach `n`, a different question. "
                        "Counting all the ways is Game Routes on this graph."),
                Opt("Counting paths from 0 to `n` in the DAG with vertices 0..n and edges "
                    "`s → s+d` for d = 1..6; increasing `s` is a topological order.", correct=True,
                    why="Right. Every DP is a computation on a DAG of states, and 'fill the table "
                        "in the right order' means 'in a topological order'."),
                Opt("Not a graph problem: there are no vertices or edges in it.",
                    why="The states `s = 0..n` are the vertices, and 'throw d' is an edge "
                        "`s → s + d`."),
            ], explain=r"""
Which is also why a DP whose dependencies go round in a circle cannot be filled in at all:
a cycle in the state graph means there is no valid order.
"""),
            MCQ(r"""
When does a DAG have exactly one topological order?
""", [
                Opt("When it is connected.",
                    why="`1 → 2`, `1 → 3` is connected and has two orders, `1 2 3` and `1 3 2`."),
                Opt("When it has exactly `n − 1` edges.",
                    why="`1 → 2`, `1 → 3` has 2 edges and two orders, while the chain "
                        "`1 → 2 → 3` has 2 edges and one."),
                Opt("When Kahn's queue never holds two vertices at once; equivalently, every two "
                    "consecutive vertices of the order are joined by an edge.", correct=True,
                    why="Right. Two vertices in the queue together could be taken either way "
                        "round; and if consecutive `u`, `v` had no edge `u → v`, swapping them "
                        "would give a second valid order."),
            ]),
            MCQ(r"""
A problem asks for the *lexicographically smallest* valid course order. Which method gives
it?
""", [
                Opt("Kahn's algorithm with a min-heap (`priority_queue` with `greater<>`) in place "
                    "of the queue.", correct=True,
                    why="Right: at every step it takes the smallest course that is currently "
                        "free, and taking any smaller course would break a requirement. "
                        "O((n + m) log n)."),
                Opt("DFS, trying neighbours and start vertices in increasing order, then reversing "
                    "the finishing order.",
                    why="With `n = 3` and the single requirement `3 2`, DFS finishes 1, 2, 3, so "
                        "the reversed order is `3 2 1`, while `1 3 2` is valid and smaller."),
                Opt("Kahn's algorithm with the ordinary queue.",
                    why="A queue takes courses in the order they were freed, not by number: "
                        "with `1 4` and `2 3` it gives `1 2 4 3`, while `1 2 3 4` is valid and "
                        "smaller."),
            ]),
        ]),
    ],
    problems=[COURSE_SCHEDULE, LONGEST_FLIGHT, GAME_ROUTES, PLANETS_KINGDOMS, COIN_COLLECTOR],
    cards=[
        Card(r"""Kahn's algorithm for a topological order, in one breath?""",
             r"""Count in-degrees; queue every vertex with in-degree 0; pop `u`, append it, and decrement each out-neighbour's count, pushing it at 0. O(n + m)."""),
        Card(r"""How does Kahn's algorithm detect a cycle?""",
             r"""If fewer than `n` vertices come out, the rest all wait on each other: the graph has a directed cycle and no topological order exists."""),
        Card(r"""How do you get a topological order from DFS, and why does it work?""",
             r"""Append each vertex when it finishes, then reverse. For every edge `u → v`, `v` finishes before `u` (an edge to an unfinished `v` on the current path would be a cycle)."""),
        Card(r"""How does DFS detect a cycle in a *directed* graph?""",
             r"""Colours: white (unvisited), grey (on the current path), black (finished). An edge to a grey vertex closes a cycle; an edge to a black one does not."""),
        Card(r"""Longest path from `s` in a DAG?""",
             r"""`best[s] = 0` (or 1 counting vertices), every other `best = −∞`; in topological order, for `u` with a real value and each edge `u → v`: `best[v] = max(best[v], best[u] + w)`. Keep parents for the path."""),
        Card(r"""Number of paths from `s` to `t` in a DAG?""",
             r"""`ways[s] = 1`; in topological order `ways[v] += ways[u]` for each edge `u → v`, modulo p. Unreachable vertices correctly stay 0."""),
        Card(r"""What is a strongly connected component, and what is the condensation?""",
             r"""A maximal set of vertices that all reach each other. Shrinking each SCC to a vertex gives the condensation, which is always a DAG."""),
        Card(r"""Kosaraju's algorithm, the steps?""",
             r"""DFS the graph, recording finishing order. Then on the reversed graph, take vertices in decreasing finishing time; each unlabelled one starts a DFS that labels one SCC."""),
        Card(r"""Why does Kosaraju's second pass stay inside one SCC?""",
             r"""An edge from SCC C to SCC D means C's latest finish is later than D's, so the latest finisher is in a source SCC, which is a sink in the reversed graph."""),
        Card(r"""In what order does Kosaraju number the SCCs?""",
             r"""In topological order of the condensation: every edge between components goes from a smaller id to a larger one."""),
        Card(r"""Lexicographically smallest topological order?""",
             r"""Kahn's algorithm with a min-heap instead of a queue. Neither DFS nor a FIFO queue gives it."""),
        Card(r"""When is the topological order of a DAG unique?""",
             r"""When Kahn's queue never holds two vertices; equivalently, consecutive vertices of the order are always joined by an edge (a Hamiltonian path)."""),
    ],
)
