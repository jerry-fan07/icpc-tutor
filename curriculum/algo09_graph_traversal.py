from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _grid_text(rows):
    return f"{len(rows)} {len(rows[0])}\n" + "\n".join(rows) + "\n"


def _random_rows(rng, n, m, wall):
    return ["".join("#" if rng.random() < wall else "." for _ in range(m)) for _ in range(n)]


def _snake_rows(n, m):
    """Floor rows joined at alternating ends: one corridor that winds through the map."""
    rows = []
    for i in range(n):
        if i % 2 == 0:
            rows.append("." * m)
        elif (i // 2) % 2 == 0:
            rows.append("#" * (m - 1) + ".")
        else:
            rows.append("." + "#" * (m - 1))
    return rows


def _checker_rows(n, m):
    return ["".join("." if (i + j) % 2 == 0 else "#" for j in range(m)) for i in range(n)]


def _rooms(rng, n, m, wall):
    return _grid_text(_random_rows(rng, n, m, wall))


def _place(rows, a, b):
    """Put 'A' at cell a and 'B' at cell b (overwriting whatever was there)."""
    rows = [list(r) for r in rows]
    rows[a[0]][a[1]] = "A"
    rows[b[0]][b[1]] = "B"
    return ["".join(r) for r in rows]


def _maze(rng, n, m, wall):
    rows = _random_rows(rng, n, m, wall)
    cells = [(i, j) for i in range(n) for j in range(m)]
    a, b = rng.sample(cells, 2)
    return _grid_text(_place(rows, a, b))


def _maze_snake(rng, n, m):
    rows = _snake_rows(n, m)
    end = (n - 1, 0) if (n // 2) % 2 == 0 else (n - 1, m - 1)
    if n % 2 == 1:                              # the last row is a full floor row
        end = (n - 1, m - 1) if ((n - 1) // 2) % 2 == 0 else (n - 1, 0)
    return _grid_text(_place(rows, (0, 0), end))


def _maze_walled_in(rng, n, m):
    """B sits in a sealed box in the middle: NO, after exploring almost everything."""
    rows = [list(r) for r in _random_rows(rng, n, m, 0.25)]
    ci, cj = n // 2, m // 2
    for i in range(ci - 1, ci + 2):
        for j in range(cj - 1, cj + 2):
            rows[i][j] = "#"
    rows[ci][cj] = "B"
    rows[0][0] = "A"
    return _grid_text(["".join(r) for r in rows])


def _edges_text(n, edges):
    return f"{n} {len(edges)}\n" + "".join(f"{a} {b}\n" for a, b in edges)


def _simple_graph(rng, n, m, connected):
    """Undirected, no loops, no repeated pairs. `connected`: starts from a random tree."""
    m = min(m, n * (n - 1) // 2)
    seen, edges = set(), []

    def add(a, b):
        if a == b:
            return
        key = (a, b) if a < b else (b, a)
        if key in seen:
            return
        seen.add(key)
        edges.append((a, b) if rng.random() < 0.5 else (b, a))

    if connected:
        for v in range(2, n + 1):
            if len(edges) < m:
                add(v, rng.randint(1, v - 1))
    while len(edges) < m:
        add(rng.randint(1, n), rng.randint(1, n))
    rng.shuffle(edges)
    return edges


def _relabel(rng, n, edges, keep_ends=True):
    """Shuffle vertex names; keep_ends keeps 1 and n where they were."""
    if keep_ends:
        mid = list(range(2, n))
        rng.shuffle(mid)
        name = [0, 1] + mid + [n]
    else:
        name = [0] + rng.sample(range(1, n + 1), n)
    return [(name[a], name[b]) for a, b in edges]


def _route_random(rng, n, m, connected=True):
    return _edges_text(n, _relabel(rng, n, _simple_graph(rng, n, m, connected), False))


def _route_path(rng, n):
    order = [1] + rng.sample(range(2, n), n - 2) + [n]
    edges = [(order[i], order[i + 1]) if rng.random() < 0.5 else (order[i + 1], order[i])
             for i in range(n - 1)]
    rng.shuffle(edges)
    return _edges_text(n, edges)


def _route_grid(rng, side):
    """A side x side grid graph, 1 in one corner and n in the opposite one: many shortest routes."""
    n = side * side
    idx = lambda r, c: r * side + c + 1
    edges = []
    for r in range(side):
        for c in range(side):
            if c + 1 < side:
                edges.append((idx(r, c), idx(r, c + 1)))
            if r + 1 < side:
                edges.append((idx(r, c), idx(r + 1, c)))
    rng.shuffle(edges)
    return _edges_text(n, _relabel(rng, n, edges, True))


def _route_split(rng, n, m):
    """Two big halves with no cable between them; 1 and n on different sides."""
    h = n // 2
    left = _simple_graph(rng, h, m // 2, True)
    right = _simple_graph(rng, n - h, m // 2, True)
    edges = left + [(a + h, b + h) for a, b in right]
    rng.shuffle(edges)
    return _edges_text(n, edges)


def _bipartite(rng, n, m, odd_edges=0):
    side = [0] + [rng.randint(0, 1) for _ in range(n)]
    left = [v for v in range(1, n + 1) if side[v] == 0] or [1]
    right = [v for v in range(1, n + 1) if side[v] == 1] or [n]
    seen, edges = set(), []
    m = min(m, len(left) * len(right) - (1 if left == right else 0))
    tries = 0
    while len(edges) < m and tries < 50 * m + 100:
        tries += 1
        a, b = rng.choice(left), rng.choice(right)
        key = (min(a, b), max(a, b))
        if a == b or key in seen:
            continue
        seen.add(key)
        edges.append((a, b) if rng.random() < 0.5 else (b, a))
    rng.shuffle(edges)
    for _ in range(odd_edges):                 # one friendship inside a team, at the end
        group = left if len(left) >= 2 else right
        while True:
            a, b = rng.sample(group, 2)
            key = (min(a, b), max(a, b))
            if key not in seen:
                seen.add(key)
                edges.append((a, b))
                break
    return _edges_text(n, edges)


def _teams_small(rng):
    n = rng.randint(1, 12)
    m = rng.randint(0, min(n * (n - 1) // 2, 14))
    if rng.random() < 0.5:
        return _bipartite(rng, n, m) if n >= 2 else "1 0\n"
    return _edges_text(n, _simple_graph(rng, n, m, False))


def _teams_components(rng, n, bad_last):
    """Many small components; 1 is isolated; optionally a triangle in the very last one."""
    edges = []
    v = 2
    while v + 3 <= n - 3:
        k = rng.randint(2, 6)
        k = min(k, n - 3 - v)
        for i in range(k - 1):                 # a path v, v+1, ..., v+k-1
            edges.append((v + i, v + i + 1))
        v += k
    a, b, c = n - 2, n - 1, n
    edges += [(a, b), (b, c)] + ([(a, c)] if bad_last else [])
    return _edges_text(n, edges)


def _trip_small(rng):
    n = rng.randint(1, 8)
    m = rng.randint(0, min(n * (n - 1) // 2, 10))
    return _edges_text(n, _simple_graph(rng, n, m, False))


def _forest(rng, n, trees):
    edges = []
    for v in range(2, n + 1):
        if v > trees:
            edges.append((v, rng.randint(1, v - 1)))
    return _edges_text(n, _relabel(rng, n, edges, False))


def _trip_late_triangle(rng, n):
    """A long path 1-2-...-(n-3), then a triangle hanging off its end, listed last."""
    edges = [(i, i + 1) for i in range(1, n - 2)]
    edges += [(n - 2, n - 1), (n - 1, n), (n, n - 2)]
    return _edges_text(n, edges)


def _trip_big_cycle(rng, n):
    order = rng.sample(range(1, n + 1), n)
    edges = [(order[i], order[(i + 1) % n]) for i in range(n)]
    rng.shuffle(edges)
    return _edges_text(n, edges)


# --------------------------------------------------------------------- checkers
def _ints(text):
    return [int(x) for x in text.split()]


def _edge_set(inp):
    it = inp.split()
    n, m = int(it[0]), int(it[1])
    es = set()
    for i in range(m):
        a, b = int(it[2 + 2 * i]), int(it[3 + 2 * i])
        es.add((a, b) if a < b else (b, a))
    return n, es


def _check_route(inp, expected, got):
    n, es = _edge_set(inp)
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    if e[0] == "IMPOSSIBLE":
        if g == ["IMPOSSIBLE"]:
            return True, ""
        return False, "computers 1 and n are not connected; expected IMPOSSIBLE"
    if g[0] == "IMPOSSIBLE":
        return False, "a route exists, but you printed IMPOSSIBLE"
    k = int(g[0])
    path = [int(x) for x in g[1:]]
    if len(path) != k:
        return False, f"you announced {k} computers but listed {len(path)}"
    if k < 2 or path[0] != 1 or path[-1] != n:
        return False, f"the route must start at 1 and end at {n}"
    for a, b in zip(path, path[1:]):
        if ((a, b) if a < b else (b, a)) not in es:
            return False, f"there is no cable between {a} and {b}"
    if k != int(e[0]):
        return False, f"your route passes {k} computers; the shortest passes {e[0]}"
    return True, ""


def _check_labyrinth(inp, expected, got):
    lines = inp.split()
    n, m = int(lines[0]), int(lines[1])
    grid = lines[2:2 + n]
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    if e[0] == "NO":
        if g == ["NO"]:
            return True, ""
        return False, "B cannot be reached from A; expected NO"
    if g[0] != "YES":
        return False, "a path exists; the first line should be YES"
    if len(g) != 3:
        return False, "expected three lines: YES, the length, the moves"
    length, moves = int(g[1]), g[2]
    if len(moves) != length:
        return False, f"you announced {length} moves but printed {len(moves)}"
    r = c = -1
    for i in range(n):
        j = grid[i].find("A")
        if j >= 0:
            r, c = i, j
    step = {"L": (0, -1), "R": (0, 1), "U": (-1, 0), "D": (1, 0)}
    for k, ch in enumerate(moves, 1):
        if ch not in step:
            return False, f"move {k} is {ch!r}; moves are L, R, U, D"
        r, c = r + step[ch][0], c + step[ch][1]
        if not (0 <= r < n and 0 <= c < m) or grid[r][c] == "#":
            return False, f"move {k} ({ch}) walks into a wall or off the map"
    if grid[r][c] != "B":
        return False, "the moves do not end at B"
    if length != int(e[1]):
        return False, f"your path has {length} moves; the shortest has {e[1]}"
    return True, ""


def _check_teams(inp, expected, got):
    it = inp.split()
    n, m = int(it[0]), int(it[1])
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    if e[0] == "IMPOSSIBLE":
        if g == ["IMPOSSIBLE"]:
            return True, ""
        return False, "no valid split exists; expected IMPOSSIBLE"
    if g[0] == "IMPOSSIBLE":
        return False, "a valid split exists, but you printed IMPOSSIBLE"
    if len(g) != n:
        return False, f"expected {n} team numbers, found {len(g)}"
    if any(x not in ("1", "2") for x in g):
        return False, "every team number must be 1 or 2"
    for i in range(m):
        a, b = int(it[2 + 2 * i]), int(it[3 + 2 * i])
        if g[a - 1] == g[b - 1]:
            return False, f"friends {a} and {b} are both in team {g[a - 1]}"
    return True, ""


def _check_trip(inp, expected, got):
    n, es = _edge_set(inp)
    e, g = expected.split(), got.split()
    if not g:
        return False, "empty output"
    if e[0] == "IMPOSSIBLE":
        if g == ["IMPOSSIBLE"]:
            return True, ""
        return False, "the road network has no round trip; expected IMPOSSIBLE"
    if g[0] == "IMPOSSIBLE":
        return False, "a round trip exists, but you printed IMPOSSIBLE"
    k = int(g[0])
    route = [int(x) for x in g[1:]]
    if len(route) != k:
        return False, f"you announced {k} cities but listed {len(route)}"
    if k < 4:
        return False, "a round trip visits at least 3 distinct cities (4 numbers with the return)"
    if route[0] != route[-1]:
        return False, "the trip must end in the city where it started"
    if len(set(route[:-1])) != k - 1:
        return False, "a city appears twice before the trip returns to its start"
    for a, b in zip(route, route[1:]):
        if ((a, b) if a < b else (b, a)) not in es:
            return False, f"there is no road between {a} and {b}"
    return True, ""


# --------------------------------------------------------------------- problems
COUNTING_ROOMS = Problem(
    id="counting_rooms",
    title="Counting Rooms",
    difficulty="easy",
    source="CSES 1192 - Counting Rooms",
    complexity="O(n·m)",
    statement=r"""
You have the floor plan of a building: an `n × m` grid where every square is floor (`.`)
or wall (`#`). You can walk left, right, up and down between floor squares. A room is a
maximal set of floor squares you can walk between.

Count the rooms.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n, m ≤ 1000).

Then `n` lines of `m` characters each, every character `.` or `#`.
""",
    output=r"""
Print one integer: the number of rooms.
""",
    samples=[
        Test("5 8\n########\n#..#...#\n####.#.#\n#..#...#\n########\n", "3\n"),
        Test("2 2\n.#\n#.\n", "2\n",
             note="Diagonal squares are not connected: you walk left, right, up and down only."),
    ],
    tests=[
        Test("1 1\n.\n"),
        Test("1 1\n#\n"),
        Test("3 3\n...\n.#.\n...\n"),
        Test("1 9\n.#..#...#\n"),
        Test("4 1\n.\n#\n.\n.\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _rooms(rng, rng.randint(1, 8), rng.randint(1, 8),
                                               rng.choice([0.25, 0.4, 0.55])), 15),
        Gen("medium random", lambda rng: _rooms(rng, 60, 80, 0.4), 3),
        Gen("medium snake", lambda rng: _grid_text(_snake_rows(41, 37)), 1),
        Gen("max random", lambda rng: _rooms(rng, 1000, 1000, 0.4), 1, large=True),
        Gen("max checkerboard", lambda rng: _grid_text(_checker_rows(1000, 1000)), 1, large=True),
        Gen("max one snake", lambda rng: _grid_text(_snake_rows(1000, 1000)), 1, large=True),
        Gen("max all floor", lambda rng: _grid_text(["." * 1000] * 1000), 1, large=True),
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

    const int dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1};
    vector<vector<char>> seen(n, vector<char>(m, 0));
    vector<pair<int, int>> st;                 // explicit stack: no recursion depth to worry about
    int rooms = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            if (g[i][j] != '.' || seen[i][j]) continue;
            rooms++;                           // an unseen floor square starts a new room
            seen[i][j] = 1;
            st.push_back({i, j});
            while (!st.empty()) {              // flood the whole room
                auto [r, c] = st.back();
                st.pop_back();
                for (int d = 0; d < 4; d++) {
                    int nr = r + dr[d], nc = c + dc[d];
                    if (nr < 0 || nr >= n || nc < 0 || nc >= m) continue;   // off the map
                    if (g[nr][nc] != '.' || seen[nr][nc]) continue;
                    seen[nr][nc] = 1;          // mark when pushed: each square enters once
                    st.push_back({nr, nc});
                }
            }
        }
    cout << rooms << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Label propagation: every floor square starts with its own label and repeatedly takes
// the smallest label among its neighbours, until nothing changes.
int main() {
    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    vector<int> lab(n * m, -1);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (g[i][j] == '.') lab[i * m + j] = i * m + j;
    while (true) {
        vector<int> nxt = lab;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < m; j++) {
                if (g[i][j] != '.') continue;
                int& me = nxt[i * m + j];
                if (i > 0 && g[i - 1][j] == '.') me = min(me, lab[(i - 1) * m + j]);
                if (i + 1 < n && g[i + 1][j] == '.') me = min(me, lab[(i + 1) * m + j]);
                if (j > 0 && g[i][j - 1] == '.') me = min(me, lab[i * m + j - 1]);
                if (j + 1 < m && g[i][j + 1] == '.') me = min(me, lab[i * m + j + 1]);
            }
        if (nxt == lab) break;
        lab = nxt;
    }
    int rooms = 0;
    for (int k = 0; k < n * m; k++) rooms += lab[k] == k;
    cout << rooms << '\n';
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
    vector<int> lab(n * m, -1);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (g[i][j] == '.') lab[i * m + j] = i * m + j;
    while (true) {
        vector<int> nxt = lab;
        for (int i = 0; i < n; i++)
            for (int j = 0; j < m; j++) {
                if (g[i][j] != '.') continue;
                int& me = nxt[i * m + j];
                if (i > 0 && g[i - 1][j] == '.') me = min(me, lab[(i - 1) * m + j]);
                if (i + 1 < n && g[i + 1][j] == '.') me = min(me, lab[(i + 1) * m + j]);
                if (j > 0 && g[i][j - 1] == '.') me = min(me, lab[i * m + j - 1]);
                if (j + 1 < m && g[i][j + 1] == '.') me = min(me, lab[i * m + j + 1]);
            }
        if (nxt == lab) break;
        lab = nxt;
    }
    int rooms = 0;
    for (int k = 0; k < n * m; k++) rooms += lab[k] == k;
    cout << rooms << '\n';
}
""",
    hints=[
        r"""Every time you meet a floor square that belongs to no room found so far, you have found
a new room. How do you make sure you never count its other squares again?""",
        r"""From that square, visit everything reachable (DFS or BFS over the four neighbours) and
mark it. Count how many times you had to start a new flood.""",
        r"""A recursive flood fill can go 10^6 calls deep on a winding room. That is fine on judges
with a big stack (this one), but an explicit `vector` used as a stack is safe everywhere.""",
    ],
    editorial=r"""
The grid is a graph: floor squares are vertices, side-adjacent floor squares are joined.
A room is a connected component. Scan the squares in any order; each floor square that is
not yet marked starts a new room, and a flood fill (DFS or BFS) from it marks the whole
room. Every square is marked once and checks 4 neighbours, so the total work is
O(n·m) = about 4·10^6 steps.

Why nothing is missed: when a flood from `s` stops, suppose a square `x` reachable from
`s` is unmarked. On a path from `s` to `x`, the first unmarked square has a marked
neighbour before it, and that neighbour looked at all four of its neighbours when it was
processed. Contradiction.

Traps: check the bounds *before* indexing `g[nr][nc]`; diagonal squares are not
neighbours; and a recursive DFS can be 10^6 calls deep in a snake-shaped room, which
crashes on a judge that keeps the default 8 MB stack. The reference uses an explicit
stack. The label-propagation idea (repeat "take the smallest neighbour label" until
stable) is correct but needs as many rounds as the longest walk inside a room: about
5·10^5 rounds of 10^6 squares on the snake test.
""",
)

MESSAGE_ROUTE = Problem(
    id="message_route",
    title="Message Route",
    difficulty="easy",
    source="CSES 1667 - Message Route",
    complexity="O(n + m)",
    statement=r"""
A network has `n` computers, numbered 1 to `n`, and `m` cables, each connecting two
computers in both directions. Uolevi sits at computer 1 and wants to send a message to
Maija at computer `n`.

Find a route from 1 to `n` that passes through as few computers as possible, or report
that there is none.
""",
    input=r"""
The first line has two integers `n` and `m` (2 ≤ n ≤ 10^5, 1 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): a cable
between computers `a` and `b`. No pair of computers is connected by two cables.
""",
    output=r"""
If there is a route, print `k`, the number of computers on it (both ends included), and
then the `k` computers in order, starting with 1 and ending with `n`. Any shortest route is
accepted.

Otherwise print `IMPOSSIBLE`.
""",
    samples=[
        Test("5 5\n1 2\n1 3\n1 4\n2 3\n5 4\n", "3\n1 4 5\n"),
        Test("4 2\n1 2\n3 4\n", "IMPOSSIBLE\n"),
    ],
    tests=[
        Test("2 1\n2 1\n"),
        Test("3 3\n1 2\n2 3\n1 3\n"),
        Test("6 5\n1 2\n2 3\n3 4\n4 5\n6 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _route_random(rng, rng.randint(2, 9), rng.randint(1, 12),
                                                      rng.random() < 0.6), 16),
        Gen("medium random", lambda rng: _route_random(rng, 300, 450, True), 3),
        Gen("medium grid", lambda rng: _route_grid(rng, 12), 2),
        Gen("max long path", lambda rng: _route_path(rng, 100000), 1, large=True),
        Gen("max random", lambda rng: _route_random(rng, 100000, 200000, True), 1, large=True),
        Gen("max grid graph", lambda rng: _route_grid(rng, 316), 1, large=True),
        Gen("max two halves", lambda rng: _route_split(rng, 100000, 200000), 1, large=True),
    ],
    checker=_check_route,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);                 // cables work both ways
    }

    vector<int> dist(n + 1, -1), par(n + 1, 0);
    queue<int> q;
    dist[1] = 0;
    q.push(1);
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        for (int v : adj[u])
            if (dist[v] == -1) {             // first arrival = shortest (layer by layer)
                dist[v] = dist[u] + 1;
                par[v] = u;
                q.push(v);
            }
    }

    if (dist[n] == -1) {
        cout << "IMPOSSIBLE\n";
        return 0;
    }
    vector<int> path;
    for (int v = n; v != 1; v = par[v]) path.push_back(v);
    path.push_back(1);
    reverse(path.begin(), path.end());
    cout << path.size() << '\n';
    for (int i = 0; i < (int)path.size(); i++) cout << path[i] << " \n"[i + 1 == (int)path.size()];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Relax every cable until nothing improves: dist[v] = min(dist[v], dist[u] + 1).
int main() {
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i];
    const int INF = 1000000000;
    vector<int> dist(n + 1, INF), par(n + 1, 0);
    dist[1] = 0;
    bool changed = true;
    while (changed) {
        changed = false;
        for (int i = 0; i < m; i++)
            for (int t = 0; t < 2; t++) {
                int u = t ? b[i] : a[i], v = t ? a[i] : b[i];
                if (dist[u] + 1 < dist[v]) {
                    dist[v] = dist[u] + 1;
                    par[v] = u;
                    changed = true;
                }
            }
    }
    if (dist[n] == INF) { cout << "IMPOSSIBLE\n"; return 0; }
    vector<int> path;
    for (int v = n; v != 1; v = par[v]) path.push_back(v);
    path.push_back(1);
    reverse(path.begin(), path.end());
    cout << path.size() << '\n';
    for (int v : path) cout << v << ' ';
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// BFS without adjacency lists: every popped computer scans all m cables for its neighbours.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i];
    vector<int> dist(n + 1, -1), par(n + 1, 0);
    queue<int> q;
    dist[1] = 0;
    q.push(1);
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        for (int i = 0; i < m; i++) {
            int v;
            if (a[i] == u) v = b[i];
            else if (b[i] == u) v = a[i];
            else continue;
            if (dist[v] == -1) {
                dist[v] = dist[u] + 1;
                par[v] = u;
                q.push(v);
            }
        }
    }
    if (dist[n] == -1) { cout << "IMPOSSIBLE\n"; return 0; }
    vector<int> path;
    for (int v = n; v != 1; v = par[v]) path.push_back(v);
    path.push_back(1);
    reverse(path.begin(), path.end());
    cout << path.size() << '\n';
    for (int v : path) cout << v << ' ';
    cout << '\n';
}
""",
    hints=[
        r"""Every cable costs the same (one more computer on the route), so "shortest" means "fewest
edges". Which traversal reaches vertices in order of their distance?""",
        r"""BFS from 1. When a computer `v` is first reached from `u`, record `par[v] = u`. At the
end, follow `par` from `n` back to 1 and reverse.""",
    ],
    editorial=r"""
Breadth-first search from computer 1. The queue holds vertices in non-decreasing order of
distance, never more than one apart (the layer invariant), so vertices are *reached* in
order of distance, and the first time BFS reaches a vertex is along a shortest route. Set
`dist[v]` and `par[v]` at that moment and never touch them again.

To print the route, walk `par` from `n` back to 1 and reverse: O(route length). Storing a
copy of the route at every vertex instead would cost up to 1 + 2 + ... + n ≈ 5·10^9
numbers on a long path.

Reading the cables into adjacency lists makes the whole search O(n + m). Scanning the raw
list of cables to find each vertex's neighbours works too, but costs O(n·m) = 2·10^10 on
the large tests.
""",
)

LABYRINTH = Problem(
    id="labyrinth",
    title="Labyrinth",
    difficulty="medium",
    source="CSES 1193 - Labyrinth",
    complexity="O(n·m)",
    statement=r"""
You are given the map of a labyrinth: an `n × m` grid of floor (`.`), walls (`#`), your
start `A` and the exit `B` (both are floor). You can move left, right, up and down.

Find a shortest path from `A` to `B`, or report that there is none.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n, m ≤ 1000, n·m ≥ 2).

Then `n` lines of `m` characters each, from `.#AB`. There is exactly one `A` and exactly
one `B`.
""",
    output=r"""
If there is a path, print `YES`, then its length (the number of moves), then the moves as
one string of the letters `L`, `R`, `U`, `D` (left, right, up, down). Any shortest path is
accepted.

Otherwise print `NO`.
""",
    samples=[
        Test("5 8\n########\n#.A#...#\n#.##.#B#\n#......#\n########\n", "YES\n9\nLDDRRRRRU\n"),
        Test("3 3\nA#.\n##.\n..B\n", "NO\n"),
    ],
    tests=[
        Test("1 2\nAB\n"),
        Test("1 2\nBA\n"),
        Test("2 1\nB\nA\n"),
        Test("3 3\nA.#\n#.#\n#.B\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _maze(rng, rng.randint(1, 7), rng.randint(2, 7),
                                              rng.choice([0.2, 0.35])), 16),
        Gen("medium random", lambda rng: _maze(rng, 50, 60, 0.3), 3),
        Gen("medium snake", lambda rng: _maze_snake(rng, 31, 29), 1),
        Gen("max snake", lambda rng: _maze_snake(rng, 1000, 1000), 1, large=True),
        Gen("max open", lambda rng: _grid_text(_place(["." * 1000] * 1000, (0, 0), (999, 999))),
            1, large=True),
        Gen("max random", lambda rng: _maze(rng, 1000, 1000, 0.3), 1, large=True),
        Gen("max sealed exit", lambda rng: _maze_walled_in(rng, 1000, 1000), 1, large=True),
    ],
    checker=_check_labyrinth,
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
    int start = 0, target = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            if (g[i][j] == 'A') start = i * m + j;     // cell id = row * m + column
            if (g[i][j] == 'B') target = i * m + j;
        }

    const int dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1};
    const char name[4] = {'U', 'D', 'L', 'R'};
    vector<int> how(n * m, -1);                  // how[c]: the move that first entered c
    vector<char> seen(n * m, 0);
    queue<int> q;
    seen[start] = 1;
    q.push(start);
    while (!q.empty()) {
        int cur = q.front();
        q.pop();
        int r = cur / m, c = cur % m;
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr < 0 || nr >= n || nc < 0 || nc >= m || g[nr][nc] == '#') continue;
            int nxt = nr * m + nc;
            if (seen[nxt]) continue;
            seen[nxt] = 1;
            how[nxt] = d;
            q.push(nxt);
        }
    }

    if (!seen[target]) {
        cout << "NO\n";
        return 0;
    }
    string path;                                 // walk back from B, undoing each move
    int r = target / m, c = target % m;
    while (r * m + c != start) {
        int d = how[r * m + c];
        path += name[d];
        r -= dr[d];
        c -= dc[d];
    }
    reverse(path.begin(), path.end());           // the moves were collected backwards
    cout << "YES\n" << path.size() << '\n' << path << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Relax every cell until no distance improves, then walk back along the recorded moves.
int main() {
    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    int sr = 0, sc = 0, tr = 0, tc = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            if (g[i][j] == 'A') sr = i, sc = j;
            if (g[i][j] == 'B') tr = i, tc = j;
        }
    const int INF = 1000000000;
    const int dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1};
    const char name[4] = {'U', 'D', 'L', 'R'};
    vector<vector<int>> dist(n, vector<int>(m, INF)), how(n, vector<int>(m, -1));
    dist[sr][sc] = 0;
    bool changed = true;
    while (changed) {
        changed = false;
        for (int r = 0; r < n; r++)
            for (int c = 0; c < m; c++) {
                if (dist[r][c] == INF) continue;
                for (int d = 0; d < 4; d++) {
                    int nr = r + dr[d], nc = c + dc[d];
                    if (nr < 0 || nr >= n || nc < 0 || nc >= m || g[nr][nc] == '#') continue;
                    if (dist[r][c] + 1 < dist[nr][nc]) {
                        dist[nr][nc] = dist[r][c] + 1;
                        how[nr][nc] = d;
                        changed = true;
                    }
                }
            }
    }
    if (dist[tr][tc] == INF) { cout << "NO\n"; return 0; }
    string path;
    int r = tr, c = tc;
    while (r != sr || c != sc) {
        int d = how[r][c];
        path += name[d];
        r -= dr[d];
        c -= dc[d];
    }
    reverse(path.begin(), path.end());
    cout << "YES\n" << path.size() << '\n' << path << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// BFS that carries the whole path in the queue, the way one might in Python.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    int sr = 0, sc = 0;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (g[i][j] == 'A') sr = i, sc = j;
    const int dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1};
    const char name[4] = {'U', 'D', 'L', 'R'};
    vector<vector<char>> seen(n, vector<char>(m, 0));
    queue<pair<int, string>> q;
    seen[sr][sc] = 1;
    q.push({sr * m + sc, ""});
    while (!q.empty()) {
        auto [cur, path] = q.front();
        q.pop();
        int r = cur / m, c = cur % m;
        if (g[r][c] == 'B') {
            cout << "YES\n" << path.size() << '\n' << path << '\n';
            return 0;
        }
        for (int d = 0; d < 4; d++) {
            int nr = r + dr[d], nc = c + dc[d];
            if (nr < 0 || nr >= n || nc < 0 || nc >= m || g[nr][nc] == '#') continue;
            if (seen[nr][nc]) continue;
            seen[nr][nc] = 1;
            q.push({nr * m + nc, path + name[d]});
        }
    }
    cout << "NO\n";
}
""",
    hints=[
        r"""It is Message Route on a grid: BFS from `A` over the four neighbours of each cell.""",
        r"""Do not carry the path along in the queue: on a winding labyrinth each copy is up to 5·10^5
characters long. Store, for each cell, the move that first entered it.""",
        r"""From `B`, repeatedly look up the move that entered the current cell and step backwards
(subtract that move). The letters come out in reverse order: reverse the string at the
end.""",
    ],
    editorial=r"""
BFS over the cells, starting from `A`. Each cell remembers `how[c]`, the direction of the
move that first reached it; because BFS reaches cells in order of distance, following
these moves backwards from `B` retraces a shortest path. Undo a move by subtracting its
`(dr, dc)`, collect the letters, and reverse them. O(n·m) time and memory.

The natural Python habit, putting `(cell, path_so_far)` in the queue, copies a string at
every step. On the snake-shaped test the path is about 5·10^5 moves long, so the copies
add up to about 1 + 2 + ... + 5·10^5 ≈ 1.25·10^11 characters. Parent pointers (or stored
moves) make the reconstruction O(path length), paid once.

A small detail: numbering cells `r * m + c` lets one `vector<int>` of size `n·m` hold the
per-cell data, and `r = id / m`, `c = id % m` recovers the coordinates.
""",
)

BUILDING_TEAMS = Problem(
    id="building_teams",
    title="Building Teams",
    difficulty="medium",
    source="CSES 1668 - Building Teams",
    complexity="O(n + m)",
    statement=r"""
There are `n` pupils in a class and `m` friendships between them. The teacher wants to
split the class into two teams so that no two friends are in the same team. Both teams
may be of any size, even empty.

Find such a split, or report that it is impossible.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): pupils `a`
and `b` are friends. Every friendship is listed at most once.
""",
    output=r"""
Print `n` integers, each `1` or `2`: the team of each pupil. Any valid split is accepted.

If there is none, print `IMPOSSIBLE`.
""",
    samples=[
        Test("5 3\n1 2\n1 3\n4 5\n", "1 2 2 1 2\n"),
        Test("3 3\n1 2\n2 3\n3 1\n", "IMPOSSIBLE\n"),
    ],
    tests=[
        Test("1 0\n"),
        Test("4 4\n1 2\n2 3\n3 4\n4 1\n"),
        Test("5 5\n1 2\n2 3\n3 4\n4 5\n5 1\n"),
        Test("7 5\n1 2\n3 4\n5 6\n6 7\n7 5\n",
             note="The odd cycle is far away from pupil 1."),
        Test("6 3\n4 5\n5 6\n2 3\n"),
    ],
    gens=[
        Gen("small random", _teams_small, 18),
        Gen("max bipartite", lambda rng: _bipartite(rng, 100000, 200000), 1, large=True),
        Gen("max one bad friendship at the end", lambda rng: _bipartite(rng, 100000, 200000, 1),
            1, large=True),
        Gen("max many groups, triangle last", lambda rng: _teams_components(rng, 100000, True),
            1, large=True),
        Gen("max many groups, all fine", lambda rng: _teams_components(rng, 100000, False),
            1, large=True),
        Gen("max long path", lambda rng: _route_path(rng, 100000), 1, large=True),
    ],
    checker=_check_teams,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }

    vector<int> team(n + 1, 0);                  // 0: not assigned yet
    for (int s = 1; s <= n; s++) {               // every group of friends, not just pupil 1's
        if (team[s]) continue;
        team[s] = 1;                             // the one free choice per component
        queue<int> q;
        q.push(s);
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            for (int v : adj[u]) {
                if (team[v] == 0) {
                    team[v] = 3 - team[u];       // forced: the other team
                    q.push(v);
                } else if (team[v] == team[u]) { // friends in the same team: odd cycle
                    cout << "IMPOSSIBLE\n";
                    return 0;
                }
            }
        }
    }
    for (int v = 1; v <= n; v++) cout << team[v] << " \n"[v == n];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Try all 2^n splits (small tests only).
int main() {
    int n, m;
    cin >> n >> m;
    vector<int> a(m), b(m);
    for (int i = 0; i < m; i++) cin >> a[i] >> b[i], a[i]--, b[i]--;
    for (int mask = 0; mask < (1 << n); mask++) {
        bool ok = true;
        for (int i = 0; i < m && ok; i++)
            if ((mask >> a[i] & 1) == (mask >> b[i] & 1)) ok = false;
        if (ok) {
            for (int v = 0; v < n; v++) cout << (mask >> v & 1) + 1 << ' ';
            cout << '\n';
            return 0;
        }
    }
    cout << "IMPOSSIBLE\n";
}
""",
    hints=[
        r"""Put pupil 1 in team 1. Which pupils does that decide? And theirs?""",
        r"""Colour each group of friends with BFS: every newly reached pupil gets the other team.
If an edge joins two pupils of the same team, the split is impossible.""",
        r"""Start a BFS from *every* pupil that has no team yet, not only from pupil 1: the class
can fall apart into many separate groups.""",
    ],
    editorial=r"""
Colouring pupil `s` with team 1 forces every friend of `s` into team 2, their friends into
team 1, and so on: inside one connected group, the team of each pupil is determined by
the parity of its distance from `s`. So BFS each component, assigning `3 - team[u]` to each
newly reached pupil.

If an edge `u–v` joins two pupils with the same team, their BFS-tree paths to the root
have lengths of equal parity, so those two paths plus the edge form a closed walk of odd
length, and an odd cycle cannot be 2-coloured by any assignment. A graph can be split
exactly when it has no odd cycle (it is *bipartite*); BFS either finds a valid split or
exhibits the odd cycle. O(n + m).

The classic WA: starting the BFS only from pupil 1. Pupils in other groups keep team 0,
and an odd cycle elsewhere goes unnoticed.
""",
)

ROUND_TRIP = Problem(
    id="round_trip",
    title="Round Trip",
    difficulty="medium",
    source="CSES 1669 - Round Trip",
    complexity="O(n + m)",
    statement=r"""
Byteland has `n` cities and `m` two-way roads. You want a round trip: start in some city,
travel through two or more other cities, and come back to the start, never visiting a
city twice except for the return to the start.

Find such a trip, or report that there is none.
""",
    input=r"""
The first line has two integers `n` and `m` (1 ≤ n ≤ 10^5, 0 ≤ m ≤ 2·10^5).

Each of the next `m` lines has two integers `a` and `b` (1 ≤ a, b ≤ n, a ≠ b): a road
between `a` and `b`. There is at most one road between any two cities.
""",
    output=r"""
If there is a round trip, print `k`, the number of cities on it counting the start twice
(so `k ≥ 4`), then the `k` cities in order; the first and last are the same. Any valid trip
is accepted.

Otherwise print `IMPOSSIBLE`.
""",
    samples=[
        Test("5 6\n1 3\n1 2\n5 3\n1 5\n2 4\n4 5\n", "4\n3 5 1 3\n"),
        Test("4 3\n1 2\n2 3\n2 4\n", "IMPOSSIBLE\n"),
    ],
    tests=[
        Test("1 0\n"),
        Test("3 3\n1 2\n2 3\n3 1\n"),
        Test("3 2\n1 2\n2 3\n"),
        Test("7 7\n1 2\n2 3\n4 5\n5 6\n6 7\n7 4\n1 3\n"),
        Test("6 6\n1 2\n3 4\n4 5\n5 6\n6 3\n2 3\n"),
    ],
    gens=[
        Gen("small random", _trip_small, 18),
        Gen("medium forest", lambda rng: _forest(rng, 300, 5), 2),
        Gen("medium random", lambda rng: _route_random(rng, 300, 320, False), 2),
        Gen("max tree", lambda rng: _forest(rng, 100000, 1), 1, large=True),
        Gen("max path, triangle at the end", lambda rng: _trip_late_triangle(rng, 100000), 1,
            large=True),
        Gen("max random", lambda rng: _route_random(rng, 100000, 200000, False), 1, large=True),
        Gen("max one big cycle", lambda rng: _trip_big_cycle(rng, 100000), 1, large=True),
    ],
    checker=_check_trip,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n, m;
vector<vector<int>> adj;
vector<int> par;
vector<char> visited;
int cyc_top = -1, cyc_bottom = -1;

// DFS from u, which was entered from p. Returns true once a cycle is found.
bool dfs(int u, int p) {
    visited[u] = 1;
    par[u] = p;
    for (int v : adj[u]) {
        if (v == p) continue;                    // the road we came in on, seen from this side
        if (visited[v]) {                        // visited and not the parent: an ancestor
            cyc_top = v;
            cyc_bottom = u;
            return true;
        }
        if (dfs(v, u)) return true;
    }
    return false;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> m;
    adj.assign(n + 1, {});
    par.assign(n + 1, 0);
    visited.assign(n + 1, 0);
    for (int i = 0; i < m; i++) {
        int a, b;
        cin >> a >> b;
        adj[a].push_back(b);
        adj[b].push_back(a);
    }
    for (int s = 1; s <= n && cyc_top == -1; s++)
        if (!visited[s]) dfs(s, 0);

    if (cyc_top == -1) {
        cout << "IMPOSSIBLE\n";
        return 0;
    }
    // cyc_top -> cyc_bottom (the back edge), then up the tree back to cyc_top
    vector<int> trip = {cyc_top};
    for (int v = cyc_bottom; v != cyc_top; v = par[v]) trip.push_back(v);
    trip.push_back(cyc_top);
    cout << trip.size() << '\n';
    for (int i = 0; i < (int)trip.size(); i++) cout << trip[i] << " \n"[i + 1 == (int)trip.size()];
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// For every road a-b: forbid it and BFS from a. If b is still reachable, that path plus
// the road is a round trip.
int main() {
    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, int>>> adj(n + 1);
    vector<int> A(m), B(m);
    for (int i = 0; i < m; i++) {
        cin >> A[i] >> B[i];
        adj[A[i]].push_back({B[i], i});
        adj[B[i]].push_back({A[i], i});
    }
    for (int e = 0; e < m; e++) {
        vector<int> par(n + 1, -1);
        queue<int> q;
        par[A[e]] = 0;
        q.push(A[e]);
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            for (auto [v, id] : adj[u])
                if (id != e && par[v] == -1) {
                    par[v] = u;
                    q.push(v);
                }
        }
        if (par[B[e]] == -1) continue;
        vector<int> trip;
        for (int v = B[e]; v != 0; v = par[v]) trip.push_back(v);
        reverse(trip.begin(), trip.end());       // A[e] ... B[e]
        trip.push_back(A[e]);
        cout << trip.size() << '\n';
        for (int v : trip) cout << v << ' ';
        cout << '\n';
        return 0;
    }
    cout << "IMPOSSIBLE\n";
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
    vector<vector<pair<int, int>>> adj(n + 1);
    vector<int> A(m), B(m);
    for (int i = 0; i < m; i++) {
        cin >> A[i] >> B[i];
        adj[A[i]].push_back({B[i], i});
        adj[B[i]].push_back({A[i], i});
    }
    vector<int> par(n + 1);
    for (int e = 0; e < m; e++) {
        fill(par.begin(), par.end(), -1);
        queue<int> q;
        par[A[e]] = 0;
        q.push(A[e]);
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            for (auto [v, id] : adj[u])
                if (id != e && par[v] == -1) {
                    par[v] = u;
                    q.push(v);
                }
        }
        if (par[B[e]] == -1) continue;
        vector<int> trip;
        for (int v = B[e]; v != 0; v = par[v]) trip.push_back(v);
        reverse(trip.begin(), trip.end());
        trip.push_back(A[e]);
        cout << trip.size() << '\n';
        for (int v : trip) cout << v << ' ';
        cout << '\n';
        return 0;
    }
    cout << "IMPOSSIBLE\n";
}
""",
    hints=[
        r"""Run DFS. When the current city `u` has a neighbour `v` that is already visited, when does
that prove a cycle, and when is it just the road you arrived on?""",
        r"""Remember `par[u]`, the city DFS came from. A visited neighbour other than `par[u]` is an
ancestor of `u` in the DFS tree.""",
        r"""The trip is `v`, then `u`, `par[u]`, `par[par[u]]`, ... up to `v` again. Start a DFS from
every unvisited city: the cycle may be in any component.""",
    ],
    editorial=r"""
Run DFS, remembering for each city the city it was entered from. Every road is stored in
both adjacency lists, so from `u` you always see the road back to `par[u]`; skip it. Any
*other* already-visited neighbour `v` closes a cycle: in an undirected DFS a visited
neighbour is always an ancestor (had `v` been in an earlier, finished branch, DFS would
have walked from `v` to `u` back then, making `u` a descendant of `v`). So the tree path
`v → ... → u` plus the road `u–v` is a round trip, and walking `par` from `u` up to `v`
prints it. At least three cities are on it because `v` is not `u`'s parent. O(n + m).

No cycle found after DFS from every unvisited city means the graph is a forest:
`IMPOSSIBLE`. Deleting each road and testing whether its ends stay connected also works,
but costs O(m·(n + m)): about 5·10^9 steps on a long path.

The "not the parent" test relies on there being no duplicate roads; with parallel edges,
skip the parent *edge* (by its index) instead of the parent vertex.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo09",
    title="graphs: representation & traversal",
    track="algo",
    order=9,
    summary="Adjacency lists, flood fill with DFS, shortest routes with BFS and why the queue "
            "gets them right, grids as graphs, two-colouring, and finding a cycle.",
    prereqs=["cpp05", "cpp08"],
    tags=["graphs", "adjacency list", "bfs", "dfs", "grid", "connected components",
          "bipartite", "cycle detection", "path reconstruction"],
    parts=[
        Part("A graph is a list of neighbours", [
            Say(r"""
Graph problems are a large share of every ICPC set, and nearly all of them begin the same
way: read `n` vertices and `m` edges, store them, walk them. This lesson is about the
storing and the walking.

The problem that drives the first half (CSES 1667, Message Route): a network has `n`
computers and `m` cables, each cable joining two computers in both directions. You are at
computer 1 and want to send a message to computer `n` through as few computers as
possible, and print the route. Limits: `n ≤ 10^5`, `m ≤ 2·10^5`, one second.

Before any algorithm: how do you store the network?
"""),
            Numeric(r"""
The textbook answer is an **adjacency matrix**: a table `g[a][b]` that is true when `a`
and `b` are connected. With `n = 10^5` and one byte per entry, how many bytes is the
table?
""", answer=1e10, rel=0.5, unit="bytes",
                explain=r"""
`n^2 = 10^10` bytes, 10 GB, against a typical memory limit of 256 MB. And it is almost
empty: only 4·10^5 of its 10^10 entries are true. A matrix is the right tool when `n` is
small (`n ≤ 5000` is 25 MB) and you need "is there an edge a–b?" in O(1), as
Floyd-Warshall does in algo10. Not here.
"""),
            MCQ(r"""
Second attempt: keep the input as it came, a list of `m` pairs. To find the neighbours of
a computer `u`, scan all `m` pairs. Any traversal asks "who are the neighbours of `u`?"
once for each of the `n` vertices. What does that cost in total?
""", [
                Opt("O(m): each pair is read once.",
                    why="Each pair is read once *per question*, and there are n questions. The "
                        "list is scanned from the start every time."),
                Opt("O(n + m): each edge is looked at twice, once from each end.",
                    why="That is what we want, but the scan also looks at every pair that does "
                        "not touch u, and that is nearly all of them."),
                Opt("O(n·m), about 2·10^10 here.", correct=True,
                    why="Right: n scans of m pairs. Almost all of that work reads edges that "
                        "have nothing to do with the vertex being asked about."),
            ]),
            Reflect(r"""
The edge list wastes time because every lookup rereads pairs that do not involve `u`.
What would you compute *once*, while reading the input, so that "the neighbours of `u`"
costs only as much as `u` has neighbours?
""", answer=r"""
Group the edges by endpoint: keep, for each vertex, the list of its neighbours. While
reading, a cable `a b` appends `b` to `a`'s list and `a` to `b`'s list. Then the
neighbours of `u` are a list you iterate directly, costing `deg(u)`, and a traversal that
asks about every vertex once costs the sum of all degrees, which is `2m`. This is the
**adjacency list**, the default graph representation in contest code: O(n + m) memory and
O(n + m) for a full traversal.
"""),
            Say(r"""
In C++ an adjacency list is a vector of vectors:

```cpp
int n, m;
cin >> n >> m;
vector<vector<int>> adj(n + 1);      // vertices 1..n; adj[0] stays unused
for (int i = 0; i < m; i++) {
    int a, b;
    cin >> a >> b;
    adj[a].push_back(b);
    adj[b].push_back(a);             // undirected: store both directions
}

for (int v : adj[u]) { /* v is a neighbour of u */ }
```

`adj(n + 1)` because the input numbers vertices from 1. Weighted graphs store pairs,
`vector<vector<pair<int,int>>>` with `(neighbour, weight)`; algo10 does that.
"""),
            Short(r"""
With `n = 4` and the edges read in the order `1 2`, `3 1`, `2 3`, `3 4`, what is `adj[3]`,
in order? Write the numbers separated by spaces.
""", accept=["1 2 4", "1,2,4", "[1, 2, 4]", "{1, 2, 4}", "1, 2, 4"], placeholder="e.g. 5 6 7",
                hint="Go through the edges in order; an edge `a b` appends to both `adj[a]` and `adj[b]`.",
                explain=r"""
`1 2 4`: `3 1` appends 1, `2 3` appends 2, `3 4` appends 4. The order of a list is the
input order, which is why two correct programs can print different (equally valid) paths:
problems with several answers say "print any", and the judge then uses a checker.

Counting all entries, every edge appears twice, so the lists hold `2m` numbers in total
(the handshake lemma: the degrees sum to `2m`).
"""),
            MCQ(r"""
The next problem says the roads are one-way: a line `a b` means you can drive from `a` to
`b` only. What changes in the reading loop?
""", [
                Opt("Nothing: store both directions anyway; the traversal sorts it out.",
                    why="Then a traversal happily drives the wrong way down one-way roads: "
                        "reachability grows and distances shrink. The list must contain only "
                        "the moves that are allowed."),
                Opt("Only `adj[a].push_back(b);`", correct=True,
                    why="Right. `adj[u]` means 'where can I go from u', so a one-way road "
                        "appears once."),
                Opt("Switch to an adjacency matrix, which has a direction.",
                    why="A matrix has the same choice (set `g[a][b]` only) and the same memory "
                        "problem. The list handles direction just as well."),
            ], explain=r"""
Directed versus undirected is decided by one line, and both mistakes are common: reading
a one-way input as two-way, and forgetting the second `push_back` for a two-way input
(half the edges silently vanish). Find "one-way", "directed" or "both directions" in the
statement before writing the reading loop.
"""),
        ]),
        Part("Flood fill: depth-first search", [
            Say(r"""
Before shortest routes, a simpler question: what is reachable at all?

**Counting Rooms** (CSES 1192): a floor plan is an `n × m` grid of floor `.` and wall `#`,
with `n, m ≤ 1000`. You can walk left, right, up and down between floor squares. How
many rooms are there?

A grid is a graph whose vertices are the floor squares, with an edge between floor
squares that share a side. Nobody builds adjacency lists for it: the neighbours of
`(r, c)` are computed on the fly as `(r±1, c)` and `(r, c±1)`, if they are on the map and
not walls. A room is a *connected component*.
"""),
            Short(r"""
How many rooms does this map have?

```text
..#..
.##.#
#..##
##.#.
```
""", accept=["4", "four"], placeholder="a number",
                hint="Squares that touch only at a corner are not connected.",
                explain=r"""
Four: the top-left L of three squares, the top-right L of three, the three squares in the
middle-bottom, and the lone square in the bottom-right corner. If you got 2, you joined
squares that touch diagonally, which this problem does not allow.
"""),
            Say(r"""
Here is a first algorithm that is clearly correct. Give every floor square its own label
(its index). Then repeat rounds: in each round, every square takes the smallest label
among itself and its floor neighbours. When a round changes nothing, all squares of a room
carry the room's smallest index, so count the distinct labels.
"""),
            Numeric(r"""
One round visits all 10^6 squares. A label travels one square per round, so a room shaped
like a snake (floor rows joined at alternating ends, about 5·10^5 squares long) needs
about 5·10^5 rounds. Roughly how many square visits is that in total?
""", answer=5e11, rel=0.9, unit="visits",
                explain=r"""
`10^6 · 5·10^5 = 5·10^11`: at 10^9 simple operations a second that is over eight minutes,
against a one-second limit. The hidden tests of Counting Rooms include exactly this map.
"""),
            Reflect(r"""
In any single round, almost every square recomputes the label it already had. Which
squares can actually change in a round, and what does that suggest doing instead of
sweeping the whole map again?
""", answer=r"""
Only squares next to a square that changed in the previous round can change; the rest
repeat the same computation. So stop sweeping: start from one square and spread outward,
only ever processing squares you have just reached. Mark each square the first time you
reach it and never process it again. Every square is handled once and checks its 4
neighbours: about 4·10^6 steps for the whole map. That is a **flood fill**. Processing the
newest reached square first gives depth-first search (DFS); the oldest first gives
breadth-first search (BFS). For counting rooms either works.
"""),
            Say(r"""
The recursive flood fill is the shortest to write:

```cpp
int n, m;
vector<string> g;
vector<vector<char>> seen;
const int dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1};   // up, down, left, right

void dfs(int r, int c) {
    seen[r][c] = 1;
    for (int d = 0; d < 4; d++) {
        int nr = r + dr[d], nc = c + dc[d];
        if (nr < 0 || nr >= n || nc < 0 || nc >= m) continue;   // off the map
        if (g[nr][nc] == '#' || seen[nr][nc]) continue;
        dfs(nr, nc);
    }
}
// in main: for every square, if it is floor and not seen: rooms++, dfs(i, j)
```

The `dr`/`dc` arrays turn "the four neighbours" into a loop, and the bounds test comes
*before* `g[nr][nc]`: `g[-1]` is an out-of-bounds read, a crash or garbage.
"""),
            MCQ(r"""
Why is every square reachable from `s` marked once `dfs(s)` returns? Suppose some
reachable square `x` stays unmarked, and take a path of floor squares from `s` to `x`.
""", [
                Opt("Because DFS tries every possible path from `s`.",
                    why="It does not: it never re-enters a marked square, which is exactly why "
                        "it is fast. The argument has to work without trying every path."),
                Opt("On the path, the first unmarked square has a marked square just before it; "
                    "`dfs` ran on that square and checked all four neighbours. Contradiction.",
                    correct=True,
                    why="Right. `s` is marked and `x` is not, so the path crosses from marked to "
                        "unmarked somewhere, and that crossing is impossible."),
                Opt("Because the grid is finite, so the search eventually visits every square.",
                    why="Finiteness shows that DFS stops, not that it covers everything "
                        "reachable: walls stop it on purpose. The question is why it cannot "
                        "stop too early."),
            ]),
            Numeric(r"""
How deep can the recursion of `dfs` get on a `1000 × 1000` map, in the worst case?
""", answer=1e6, rel=0.5, unit="nested calls",
                explain=r"""
Up to one call per square, 10^6, when the current DFS path winds through the whole map
(the snake does this). At roughly 50-100 bytes per stack frame that is 50-100 MB of stack.
Most contest judges set the stack as large as the memory limit (this site gives 512 MB),
but a judge that keeps the usual 8 MB default turns this into a segmentation fault: RE,
not TLE, on a correct algorithm.

The safe version replaces recursion with your own stack:

```cpp
vector<pair<int,int>> st = {{i, j}};
seen[i][j] = 1;
while (!st.empty()) {
    auto [r, c] = st.back();
    st.pop_back();
    for (int d = 0; d < 4; d++) {
        int nr = r + dr[d], nc = c + dc[d];
        if (nr < 0 || nr >= n || nc < 0 || nc >= m) continue;
        if (g[nr][nc] == '#' || seen[nr][nc]) continue;
        seen[nr][nc] = 1;               // mark when pushed, so each square enters once
        st.push_back({nr, nc});
    }
}
```
"""),
            Try("counting_rooms", note="One flood per room. The hidden tests include a 10^6-square "
                "snake and a checkerboard with 5·10^5 rooms."),
        ]),
        Part("Fewest steps: breadth-first search", [
            Say(r"""
Back to Message Route. A flood fill from computer 1 tells you *whether* computer `n` is
reachable. The problem wants the route through the fewest computers, that is, the path
with the fewest edges.
"""),
            MCQ(r"""
Does the path that DFS walks from 1 to `n` have the fewest edges? Take the triangle with
cables `1 2`, `2 3`, `1 3`, read in that order, and `n = 3`.
""", [
                Opt("Yes: DFS goes deep, so it reaches every vertex as early as possible.",
                    why="`adj[1] = [2, 3]`, so DFS goes to 2 first and reaches 3 from there: "
                        "1 → 2 → 3, two cables, while the cable 1–3 is a route of one."),
                Opt("No: here it reaches 3 through 2, two cables instead of one.", correct=True,
                    why="Right. The path DFS finds depends on the order of the adjacency lists, "
                        "not on distance."),
                Opt("It does on this triangle; it fails only on larger graphs.",
                    why="Trace it: from 1, DFS takes the first neighbour, 2, and from 2 finds 3 "
                        "unvisited. It already fails on the smallest graph with a cycle."),
            ], explain=r"""
On a tree there is only one simple path between two vertices, so any search finds it.
With cycles, "reachable" and "reachable in the fewest steps" need different searches.
"""),
            Numeric(r"""
The safe brute force is to try every path from 1 to `n` and keep the shortest. Consider a
*ladder*: a start vertex, then 50 layers of 2 vertices each, then an end vertex, with every
vertex joined to both vertices of the next layer. How many different start-to-end paths
go layer by layer?
""", answer=2**50, rel=0.5, unit="paths",
                hint="How many choices are there in each layer?",
                explain=r"""
2 choices per layer, 50 layers: `2^50 ≈ 1.1·10^15` paths, in a graph of only 102 vertices.
"""),
            Reflect(r"""
Those 10^15 paths are made of 102 vertices. What does the all-paths search do over and
over, and which arrival at a vertex is the only one that matters for the shortest route?
""", answer=r"""
It reaches the same vertex again and again along different paths, and re-explores
everything beyond it each time. For a shortest route only the *first, shortest* arrival at
a vertex matters: whatever continues from a longer arrival is matched or beaten by
continuing from the shortest one. So if we could reach vertices in order of distance, the
first arrival at each vertex would be its answer, and no vertex would need exploring twice.
Reaching vertices in order of distance is exactly what breadth-first search does.
"""),
            Say(r"""
BFS builds the distance layers one at a time. Layer 0 is vertex 1. Layer `d + 1` is every
not-yet-reached neighbour of layer `d`. A FIFO queue produces the layers in order without
ever naming them:

```cpp
vector<int> dist(n + 1, -1);      // -1: not reached yet
vector<int> par(n + 1, 0);        // who reached me first
queue<int> q;
dist[1] = 0;
q.push(1);
while (!q.empty()) {
    int u = q.front();
    q.pop();
    for (int v : adj[u])
        if (dist[v] == -1) {      // first arrival
            dist[v] = dist[u] + 1;
            par[v] = u;
            q.push(v);
        }
}
```
"""),
            MCQ(r"""
Freeze BFS at any moment and read the `dist` values of the vertices in the queue, front to
back. What do you always see?
""", [
                Opt("All equal: the queue holds exactly one layer.",
                    why="While layer d is being popped, layer d+1 is being pushed behind it, "
                        "so two values coexist."),
                Opt("Anything: BFS only guarantees each vertex is pushed once.",
                    why="The FIFO order gives much more: a vertex pushed later never has a "
                        "smaller dist than one pushed earlier."),
                Opt("Some `d`'s followed by some `d + 1`'s: non-decreasing, and the last is at "
                    "most the first plus one.", correct=True,
                    why="Yes. Popping a `d` pushes `d + 1`'s at the back, which keeps that shape. "
                        "This is the **layer invariant**; everything about BFS follows from it."),
            ]),
            MCQ(r"""
Why is `dist[v]` a shortest distance? Suppose BFS sets `dist[v] = 5` (reached from `u`, with
`dist[u] = 4`), but some path of length 4 reaches `v`. Let `w` be the vertex just before
`v` on that path, so `w`'s true distance is 3, and assume BFS got all distances below 5
right. Which step gives the contradiction?
""", [
                Opt("`dist[w] = 3 < 4 = dist[u]`, so the invariant pops `w` before `u`; at that "
                    "moment `v` was unreached, so `w` would have set `dist[v] = 4`.", correct=True,
                    why="Exactly. Vertices are popped in order of distance, so the first vertex to "
                        "reach `v` is one of its closest predecessors."),
                Opt("`w` is not in `adj[u]`, so BFS never looks at `w`.",
                    why="`w` has its own list, which contains `v`. The question is *when* `w` is "
                        "popped relative to `u`."),
                Opt("There is no contradiction: BFS can be wrong here, which is why Dijkstra exists.",
                    why="Dijkstra exists for edges of different lengths. With every edge worth 1, "
                        "BFS is exactly right, and this argument is the proof."),
            ]),
            Short(r"""
Run BFS from 1, with the cables read in this order: `1 2`, `1 3`, `2 4`, `3 4`, `4 5`,
`3 6`, `6 7`, `5 7`. Then follow `par` back from 7 to 1. Which route do you get, from 1 to
7?
""", accept=["1 3 6 7", "1-3-6-7", "1,3,6,7", "1 -> 3 -> 6 -> 7", "1, 3, 6, 7"],
                placeholder="e.g. 1 2 3",
                hint="Layer 1 is {2, 3}. Who reaches 4 first, and who reaches 6?",
                explain=r"""
Layers: {1}, then {2, 3}, then {4, 6} (4 first reached from 2, 6 from 3), then {5, 7} (5
from 4, 7 from 6). So `par[7] = 6`, `par[6] = 3`, `par[3] = 1`: the route `1 3 6 7`, with
`dist[7] = 3`. Collecting the route from `n` backwards gives `7 6 3 1`; reverse it before
printing.
"""),
            Numeric(r"""
Why keep one parent per vertex instead of a copy of the whole route to it? On a path graph
with `n = 10^5` vertices, a copy of the route at every vertex costs `1 + 2 + ... + 10^5`
numbers. About how many is that?
""", answer=5e9, rel=0.5, unit="numbers",
                explain=r"""
`n(n+1)/2 ≈ 5·10^9` numbers, 20 GB of `int`s, and as many copy operations. The parent array
costs `n` numbers, and one walk back along it costs the length of one route. The same trap
in a grid problem (a queue of `(cell, path_so_far)` strings) is the Labyrinth problem's
naive solution.

A smaller detail in the same spirit: set `dist[v]` when `v` is *pushed*, as above. If you
only mark vertices when they are popped, a vertex can be pushed once by every neighbour
that sees it before it is popped, and each copy is processed again.
"""),
            Try("message_route", note="BFS with parents. Any shortest route is accepted."),
            Say(r"""
**Labyrinth** (CSES 1193) is the same search on a grid: find a shortest path from `A` to
`B` and print it as a string of moves `L`, `R`, `U`, `D`.

Two habits make grid BFS tidy. Number the cells `id = r * m + c`, so one `vector<int>` of
size `n·m` holds any per-cell data and `r = id / m`, `c = id % m` recovers the
coordinates. And instead of a parent, store for each cell the direction `d` of the move
that first entered it.
"""),
            MCQ(r"""
Walking back from `B`, the stored move into the current cell is `L` (left). Where is the
previous cell of the path?
""", [
                Opt("One column to the left.",
                    why="The move `L` went *from* the previous cell *to* this one, leftwards. The "
                        "previous cell is on the other side."),
                Opt("One column to the right.", correct=True,
                    why="Right: undo a move by subtracting its `(dr, dc)`. Keep the letter, and "
                        "reverse the collected letters at the end, since they come out from B "
                        "to A."),
                Opt("It cannot be known from the move alone; you need a parent array too.",
                    why="The move is enough: a cell and the move that entered it determine the "
                        "cell before it."),
            ]),
            Try("labyrinth", note="Grid BFS, stored moves, one reverse at the end. The hidden "
                "tests include a 5·10^5-move snake."),
        ]),
        Part("Two teams: bipartite graphs", [
            Say(r"""
**Building Teams** (CSES 1668): `n ≤ 10^5` pupils and `m ≤ 2·10^5` friendships. Split the
class into two teams so that no two friends are in the same team, and print the teams, or
`IMPOSSIBLE`.
"""),
            Numeric(r"""
The brute force tries every assignment of pupils to teams. For just `n = 40` pupils, how
many assignments are there?
""", answer=2**40, rel=0.5, unit="assignments",
                explain=r"""
`2^40 ≈ 1.1·10^12`: already twenty minutes of work at 10^9 checks a second, and `n` here
goes to 10^5.
"""),
            Reflect(r"""
Put pupil 1 in team 1. What does that single decision force, and how far does it spread?
""", answer=r"""
Every friend of pupil 1 must go to team 2, every friend of *those* to team 1, and so on:
the choice propagates through the whole connected group of pupil 1, and each pupil's team
is decided by the parity of its distance from pupil 1. The only free choice is one per
component (and flipping it just mirrors the component). So a BFS or DFS per component
assigns `team[v] = 3 - team[u]` to each newly reached pupil, and a friendship between two
pupils of the same team means no split exists. O(n + m) instead of 2^n.
"""),
            MCQ(r"""
BFS finds a friendship `u–v` with both pupils in team 1. Could a different starting choice
have avoided the clash?
""", [
                Opt("Yes: restart with the first pupil in team 2.",
                    why="That swaps every team in the component, and `u`, `v` would clash in "
                        "team 2 instead. Nothing in the component was a free choice."),
                Opt("Yes, if `u` and `v` are in different components.",
                    why="The friendship `u–v` puts them in the same component by definition."),
                Opt("No: the BFS-tree paths from the root to `u` and to `v` have lengths of the "
                    "same parity, so with the edge `u–v` they close an odd cycle, and no split "
                    "can colour an odd cycle.", correct=True,
                    why="Right. The clash is a certificate: the graph contains an odd cycle."),
            ], explain=r"""
A graph whose vertices split into two sides with every edge crossing is **bipartite**, and
a graph is bipartite exactly when it has no odd cycle. Trees and grids are bipartite
(colour by depth, or like a chessboard); a triangle is not.
"""),
            Short(r"""
Pupils 1..5, friendships read in the order `1 2`, `1 3`, `2 4`, `3 4`, `4 5`, `3 5`. BFS from
pupil 1, neighbours in list order. Which friendship is the first one found with both
pupils in the same team? Write the two pupils.
""", accept=["4 5", "5 4", "4-5", "4 and 5", "4,5", "(4, 5)", "5-4", "4, 5"],
                placeholder="two pupils",
                hint="Pupil 1 is in team 1; popping it puts 2 and 3 in team 2. Keep going in queue order.",
                explain=r"""
Popping 1 puts 2 and 3 in team 2. Popping 2 puts 4 in team 1. Popping 3: 4 is in team 1,
fine; 5 goes to team 1. Popping 4: its neighbour 5 is also in team 1, the clash. The odd
cycle is `3–4–5–3`: 3 is joined to both 4 and 5, and 4 to 5.
"""),
            MCQ(r"""
Your program starts BFS only from pupil 1 and prints `team[1..n]`. Which input breaks it?
""", [
                Opt("A single pupil and no friendships.",
                    why="Pupil 1 gets team 1, which is a valid answer."),
                Opt("A class that falls apart into separate groups of friends.", correct=True,
                    why="Right. Pupils outside pupil 1's group keep team 0 (an invalid answer), "
                        "and an odd cycle in another group goes unnoticed. Loop over all pupils "
                        "and start a BFS at each one that has no team yet."),
                Opt("A long chain of friendships 1–2–3–...–n.",
                    why="BFS from 1 reaches the whole chain and alternates teams correctly."),
            ], explain=r"""
It is the same outer loop as Counting Rooms: `for (s = 1..n) if (not visited) start a
search`. Anything that asks about the *whole* graph needs it.
"""),
            Try("building_teams", note="Two-colour every component; any valid split is accepted."),
        ]),
        Part("Cycles, and the shape DFS leaves behind", [
            Say(r"""
**Round Trip** (CSES 1669): `n ≤ 10^5` cities, `m ≤ 2·10^5` two-way roads, no duplicates.
Find a round trip that starts in a city, visits at least two other cities without
repeating any, and returns to the start; or report that none exists. In graph terms: find
a cycle.
"""),
            Numeric(r"""
A direct approach: for each road `a–b`, forbid that road and BFS from `a`; if `b` is still
reachable, that path plus the road is a cycle. When there is no cycle at all, every BFS
runs to the end. With `m = 2·10^5` and a BFS costing up to `n + m ≈ 3·10^5`, how much work
is that in the worst case?
""", answer=6e10, rel=0.5, unit="steps",
                explain=r"""
`2·10^5 · 3·10^5 = 6·10^10`. One DFS will do the whole job in `3·10^5`.
"""),
            MCQ(r"""
During a DFS, city `u` scans a neighbour `v` that is already visited. When does that prove
a cycle?
""", [
                Opt("Always: `v` was reached before, so there are two ways to get to it.",
                    why="Not when `v` is the city DFS came from. The road `v–u` is stored in both "
                        "`adj[v]` and `adj[u]`, so every tree edge is seen again from the child's "
                        "side."),
                Opt("Only when `v` is the root of the DFS.",
                    why="Any ancestor works: the cycle is `v → ... → u → v`, wherever `v` sits "
                        "on the path."),
                Opt("When `v` is not `u`'s DFS parent.", correct=True,
                    why="Right, and the next question is why such a `v` is always an ancestor of "
                        "`u`, which makes the cycle easy to print."),
            ]),
            MCQ(r"""
Why is such a `v` always an *ancestor* of `u` in the DFS tree, never a city in some other,
already finished branch?
""", [
                Opt("Because DFS visits the cities in increasing order of their numbers.",
                    why="It visits them in adjacency-list order, which has nothing to do with "
                        "the labels."),
                Opt("It need not be; after finding the edge you search for the cycle with BFS.",
                    why="No search is needed: the parent pointers from `u` lead straight up to "
                        "`v`."),
                Opt("If `v` were in a finished branch, then while DFS was at `v` it scanned the "
                    "road `v–u`, found `u` unvisited and went there, so `u` would be `v`'s "
                    "descendant.", correct=True,
                    why="Right. In an undirected DFS every non-tree edge joins an ancestor and a "
                        "descendant; there are no 'cross' edges."),
            ], explain=r"""
So the cycle is `v`, then `u`, `par[u]`, `par[par[u]]`, ... up to `v` again: one walk up
the tree. It has at least 3 cities because `v ≠ par[u]` (and the graph has no duplicate
roads; with parallel roads, skip the parent *edge* by its index instead of the parent
vertex).
"""),
            Short(r"""
Cities 1..5, roads read in the order `1 2`, `2 3`, `3 4`, `4 2`, `4 5`. DFS from city 1,
neighbours in list order. When DFS is at city 4, which already-visited city, other than
its parent, does it find?
""", accept=["2", "city 2"], placeholder="a city",
                hint="The DFS path so far is 1 → 2 → 3 → 4. What is `adj[4]`?",
                explain=r"""
`adj[4] = [3, 2, 5]`. 3 is the parent, skipped; 2 is visited and not the parent. Walking
`par` from 4 gives 4, 3, then 2: the round trip `2 4 3 2` (or `2 3 4 2` the other way
round).
"""),
            MCQ(r"""
Does the same test ("visited and not the parent") find cycles in a *directed* graph? Take
`1→2`, `1→3`, `3→2`, with DFS from 1.
""", [
                Opt("Yes, it works the same way.",
                    why="DFS visits 2 from 1 and finishes it, then visits 3 and sees 2: visited "
                        "and not 3's parent. It would report a cycle, but from 2 you cannot get "
                        "anywhere."),
                Opt("No: it reports this acyclic graph as cyclic. In a directed graph a cycle "
                    "shows up as an edge to a vertex that is still *on the current DFS path*, "
                    "not merely visited.", correct=True,
                    why="Right. Directed DFS needs three states: unvisited, on the path, "
                        "finished. algo12 builds topological sorting on exactly this."),
                Opt("No: directed graphs cannot contain cycles.",
                    why="They can: `1→2→1` is one."),
            ]),
            Try("round_trip", note="DFS with parents; any round trip is accepted."),
        ]),
        Part("Reading a problem as a graph", [
            Say(r"""
Every traversal in this lesson is O(n + m): each vertex is processed once and each edge
looked at once from each end. The work is almost never in the search itself; it is in
seeing the graph. Vertices can be cells, states of a puzzle, positions of a lock; edges
are the moves.
"""),
            MCQ(r"""
A grid has fire in `k` cells, and fire spreads one square per minute. For every square
you need the minute the fire reaches it. One BFS per fire costs `k · n·m`, too much with
`k = n·m / 2`. What do you do instead?
""", [
                Opt("Run the `k` BFS's but stop each one early when it meets another fire.",
                    why="The early stopping is hard to get right, and the idea it is reaching "
                        "for is simpler: start all fires in the same queue."),
                Opt("Push all `k` fire cells into the queue with distance 0, then run one BFS.",
                    correct=True,
                    why="Right: **multi-source BFS**. It is BFS from an imaginary extra vertex "
                        "joined to every fire, so the layer invariant still holds. O(n·m)."),
                Opt("DFS from each fire, keeping the minimum time seen per square.",
                    why="DFS does not reach squares in order of distance, so each square may "
                        "be improved many times; it is both slower and harder to get right."),
            ]),
            MCQ(r"""
Some edges have length 1 and some length 2. Can BFS still find shortest distances?
""", [
                Opt("Yes, as it is: BFS does not care about lengths.",
                    why="BFS counts edges, not length: it prefers two edges of length 2 (total 4) "
                        "to three edges of length 1 (total 3)."),
                Opt("Yes, after splitting every length-2 edge into two length-1 edges through a "
                    "new middle vertex.", correct=True,
                    why="Right: that works for small integer lengths, since it adds one vertex per "
                        "long edge. For general lengths (up to 10^9) the graph would explode, "
                        "and that is where Dijkstra (algo10) comes in."),
                Opt("No: any weighted graph needs Bellman-Ford.",
                    why="Bellman-Ford handles negative edges, at O(n·m). Positive weights have "
                        "faster tools, starting with this small trick."),
            ], explain=r"""
algo10 generalises this lesson's BFS: Dijkstra for non-negative lengths, and a deque-based
"0-1 BFS" for lengths 0 and 1.
"""),
        ]),
    ],
    problems=[COUNTING_ROOMS, MESSAGE_ROUTE, LABYRINTH, BUILDING_TEAMS, ROUND_TRIP],
    cards=[
        Card(r"""How do you store an undirected graph with `n ≤ 10^5` vertices in contest C++?""",
             r"""`vector<vector<int>> adj(n + 1);` and for each edge `adj[a].push_back(b); adj[b].push_back(a);`. O(n + m) memory; a directed edge is pushed once."""),
        Card(r"""When is an adjacency matrix acceptable?""",
             r"""When `n` is small (about `n ≤ 5000`: 25 MB of bytes) and you need O(1) "is a–b an edge?", e.g. Floyd-Warshall. At `n = 10^5` it is 10^10 entries."""),
        Card(r"""Why does BFS find shortest paths in an unweighted graph?""",
             r"""The queue always holds some `d`'s then some `d+1`'s (the layer invariant), so vertices are reached in order of distance and the first arrival at a vertex is along a shortest path."""),
        Card(r"""In BFS, when do you set `dist[v]` (or mark `v` visited)?""",
             r"""When `v` is pushed, guarded by `dist[v] == -1`. Then each vertex enters the queue once."""),
        Card(r"""How do you print a shortest path found by BFS?""",
             r"""Store `par[v] = u` when `v` is first reached; walk `par` from the target back to the source, then reverse. Never store a whole path per vertex (O(n^2))."""),
        Card(r"""Idiom for the 4 neighbours of a grid cell?""",
             r"""`dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1}`; loop `d`, compute `(r + dr[d], c + dc[d])`, test the bounds *before* indexing the grid."""),
        Card(r"""What is the risk of a recursive DFS on a 1000 × 1000 grid, and the fix?""",
             r"""Recursion up to 10^6 deep: a stack overflow (RE) on judges with an 8 MB stack. Use an explicit `vector` as a stack, marking cells when pushed."""),
        Card(r"""How do you count connected components?""",
             r"""Loop over every vertex; each one not yet visited starts a new component, and a DFS/BFS from it marks the whole component."""),
        Card(r"""How do you test whether a graph is bipartite?""",
             r"""BFS/DFS each component, giving each new vertex the opposite colour of its parent. An edge between equal colours means an odd cycle: not bipartite."""),
        Card(r"""How does DFS find a cycle in an undirected graph?""",
             r"""An edge from `u` to a visited `v` that is not `u`'s parent is a back edge to an ancestor; the cycle is `v`, `u`, `par[u]`, ... up to `v`."""),
        Card(r"""Why is "visited and not the parent" wrong for cycles in a directed graph?""",
             r"""A visited vertex may be finished and unable to reach back (`1→2, 1→3, 3→2`). A directed cycle is an edge to a vertex still on the current DFS path."""),
        Card(r"""What is multi-source BFS?""",
             r"""Push all sources with distance 0 before the loop; one BFS then gives each vertex its distance to the nearest source, in O(n + m)."""),
    ],
)
