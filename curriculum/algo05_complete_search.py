from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _apples(rng, n, wmax):
    return f"{n}\n" + " ".join(str(rng.randint(1, wmax)) for _ in range(n)) + "\n"


def _matrix(rng, n, dmax, zero_chance=0.0):
    rows = [str(n)]
    for i in range(n):
        row = []
        for j in range(n):
            if i == j or rng.random() < zero_chance:
                row.append(0 if i == j else rng.randint(0, 2))
            else:
                row.append(rng.randint(0, dmax))
        rows.append(" ".join(map(str, row)))
    return "\n".join(rows) + "\n"


def _board(rng, n, density):
    rows = ["".join("*" if rng.random() < density else "." for _ in range(n)) for _ in range(n)]
    return f"{n}\n" + "\n".join(rows) + "\n"


def _board_small(rng):
    return _board(rng, rng.randint(1, 8), rng.choice([0.0, 0.05, 0.1, 0.2]))


def _subset_target(rng, t, xmax):
    """x = the sum of a random subset (so the answer is usually not 0), kept within 1..xmax."""
    for _ in range(100):
        k = rng.randint(1, len(t))
        x = sum(rng.sample(t, k))
        if x <= xmax:
            return x
    return min(t)


def _mitm(rng, n, vmax, planted=True):
    t = [rng.randint(1, vmax) for _ in range(n)]
    x = _subset_target(rng, t, 10**9) if planted else rng.randint(1, 10**9)
    return f"{n} {x}\n" + " ".join(map(str, t)) + "\n"


# --------------------------------------------------------------------- problems
APPLE_DIVISION = Problem(
    id="apple_division",
    title="Apple Division",
    difficulty="easy",
    source="CSES 1623 - Apple Division",
    complexity="O(2^n)",
    statement=r"""
There are `n` apples with known weights. Divide them into two groups so that the difference
between the total weights of the groups is as small as possible.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 20).

The second line has `n` integers p_1, ..., p_n (1 ≤ p_i ≤ 10^9): the weights.
""",
    output=r"""
Print one integer: the minimum possible difference between the two groups' total weights.
""",
    samples=[
        Test("5\n3 2 7 4 1\n", "1\n", note="`3 + 2 + 4 = 9` against `7 + 1 = 8`."),
    ],
    tests=[
        Test("1\n1000000000\n"),
        Test("2\n5 5\n"),
        Test("5\n1000000000 1000000000 1000000000 1000000000 294967301\n"),
        Test("5\n3 3 2 2 2\n"),
        Test("4\n8 3 5 12\n"),
        Test("20\n" + " ".join(["1000000000"] * 20) + "\n"),
        Test("20\n" + " ".join(str(2**i) for i in range(20)) + "\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _apples(rng, rng.randint(1, 12), 50), 15),
        Gen("n = 20, big weights", lambda rng: _apples(rng, 20, 10**9), 3),
        Gen("n = 20, small weights", lambda rng: _apples(rng, 20, 30), 2),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<long long> p;
long long total = 0, best = LLONG_MAX;

// decide apples i, i+1, ..., n-1; `a` is the weight already in group A
void search(int i, long long a) {
    if (i == n) {                             // a leaf: one complete split
        best = min(best, llabs(total - 2 * a));   // |A - B| with B = total - A
        return;
    }
    search(i + 1, a + p[i]);                  // apple i joins group A
    search(i + 1, a);                         // apple i joins group B
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n;
    p.resize(n);
    for (auto& v : p) {
        cin >> v;
        total += v;                           // up to 2e10: long long
    }
    search(0, 0);
    cout << best << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<long long> p(n);
    for (auto& v : p) cin >> v;
    long long best = LLONG_MAX;
    for (int mask = 0; mask < (1 << n); mask++) {     // bit i set: apple i in group A
        long long a = 0, b = 0;
        for (int i = 0; i < n; i++) (mask >> i & 1 ? a : b) += p[i];
        best = min(best, llabs(a - b));
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""`n ≤ 20`: how many ways are there to split the apples? Is that a lot for a computer?""",
        r"""Try all 2^n splits, by recursion (apple `i` goes left or right) or with a bitmask loop.
Keep sums in `long long`: 20 apples of 10^9 weigh 2·10^10.""",
    ],
    editorial=r"""
Each apple goes into one of two groups, so there are 2^n splits: 1,048,576 for `n = 20`.
Trying them all costs about 2^n · n = 2·10^7 simple operations, well inside a second, and the
limit `n ≤ 20` is exactly the problem setter saying so. Recursively: decide apple `i`, recurse
on the rest, and at a leaf compare `|total − 2·A|`. Or loop `mask` from 0 to 2^n − 1 with bit
`i` meaning "apple `i` is in group A".

The trap is the type: three apples of 10^9 already overflow `int`. Greedy ideas ("next heaviest
apple into the lighter group") fail on `3 3 2 2 2`, and a DP over reachable sums would need a
table as large as the total weight, up to 2·10^10.
""",
)

CAMPUS_TOUR = Problem(
    id="campus_tour",
    title="Night Watch",
    difficulty="medium",
    complexity="O((n − 1)! · n)",
    statement=r"""
A campus has `n` buildings joined by one-way streets: the street from building `i` to building
`j` has length `d[i][j]` (and `d[i][j]` may differ from `d[j][i]`). The night guard walks a
round: starting from any building, visiting every building exactly once, and returning to the
building where the round started.

What is the length of the shortest possible round?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 10).

Each of the next `n` lines has `n` integers: `d[i][1], ..., d[i][n]` (0 ≤ d[i][j] ≤ 10^9,
and `d[i][i] = 0`).
""",
    output=r"""
Print one integer: the length of the shortest round. (With `n = 1` the round is empty: 0.)
""",
    samples=[
        Test("4\n0 2 9 10\n1 0 6 4\n15 7 0 8\n6 3 12 0\n", "21\n",
             note="1 → 3 → 4 → 2 → 1: 9 + 8 + 3 + 1."),
        Test("4\n0 10 15 20\n10 0 35 25\n15 35 0 30\n20 25 30 0\n", "80\n"),
    ],
    tests=[
        Test("1\n0\n"),
        Test("2\n0 1000000000\n1000000000 0\n"),
        Test("3\n0 1 100\n100 0 1\n1 100 0\n"),
        Test("10\n" + "\n".join(" ".join("0" if i == j else "1000000000" for j in range(10)) for i in range(10)) + "\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _matrix(rng, rng.randint(1, 8), 20), 15),
        Gen("n = 10, big distances", lambda rng: _matrix(rng, 10, 10**9), 3),
        Gen("n = 10, many free streets", lambda rng: _matrix(rng, 10, 10**9, zero_chance=0.4), 2),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<vector<long long>> d;
vector<bool> used;
long long best = LLONG_MAX;

// the round so far starts at building 0, has `cnt` buildings, ends at `last`, costs `cost`
void go(int last, int cnt, long long cost) {
    if (cost >= best) return;                 // prune: lengths are >= 0, it can only grow
    if (cnt == n) {
        best = min(best, cost + d[last][0]);  // close the round
        return;
    }
    for (int nxt = 1; nxt < n; nxt++) {
        if (used[nxt]) continue;
        used[nxt] = true;
        go(nxt, cnt + 1, cost + d[last][nxt]);
        used[nxt] = false;                    // undo before trying the next choice
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n;
    d.assign(n, vector<long long>(n));
    for (auto& row : d)
        for (auto& v : row) cin >> v;
    used.assign(n, false);
    used[0] = true;                           // a round can start anywhere: fix building 0
    go(0, 1, 0);
    cout << best << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<vector<long long>> d(n, vector<long long>(n));
    for (auto& row : d)
        for (auto& v : row) cin >> v;
    vector<int> p(n);
    iota(p.begin(), p.end(), 0);
    long long best = LLONG_MAX;
    do {                                      // every order, every starting point
        long long c = 0;
        for (int i = 0; i < n; i++) c += d[p[i]][p[(i + 1) % n]];
        best = min(best, c);
    } while (next_permutation(p.begin(), p.end()));
    cout << best << '\n';
}
""",
    hints=[
        r"""`n ≤ 10`: try every order of the buildings. How many orders are there, and do you
need all of them for a *round* trip?""",
        r"""A round can be started anywhere, so fix building 1 as the start and permute the other
`n − 1`: (n − 1)! orders. Lengths reach 10 · 10^9: `long long`.""",
    ],
    editorial=r"""
A round is an order of the buildings, so a complete search over permutations works: `n ≤ 10`
means at most 10! = 3,628,800 orders. Better: a round has no real starting point (1 → 2 → 3 → 1
and 2 → 3 → 1 → 2 walk the same streets), so fix building 1 first and permute the rest:
9! = 362,880 orders. Generate them by recursion with a `used` array, adding each street's
length as you go instead of recomputing whole rounds at the leaves, and undo the `used` mark
after each recursive call.

Pruning: once a partial round is already at least as long as the best complete round, no
extension can do better, because lengths are non-negative. Lengths reach 10 · 10^9 = 10^10:
`long long`. For `n` up to 16-20 the same problem needs a DP over subsets (algo08).
""",
)

QUEENS = Problem(
    id="queens",
    title="Queens on a Damaged Board",
    difficulty="medium",
    source="CSES 1624 - Chessboard and Queens (generalised to n × n)",
    complexity="O(number of partial placements · n)",
    statement=r"""
An `n × n` chessboard has some damaged squares, where no piece may stand. Place `n` queens on
undamaged squares so that no two queens attack each other: no two in the same row, the same
column, or the same diagonal.

How many ways are there?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 13).

Each of the next `n` lines has `n` characters: `.` for a usable square, `*` for a damaged one.
""",
    output=r"""
Print one integer: the number of ways to place the queens.
""",
    samples=[
        Test("8\n........\n........\n..*.....\n........\n........\n.....**.\n...*....\n........\n", "65\n"),
        Test("4\n....\n....\n....\n....\n", "2\n"),
    ],
    tests=[
        Test("1\n.\n"),
        Test("1\n*\n"),
        Test("2\n..\n..\n"),
        Test("3\n...\n...\n...\n"),
        Test("6\n......\n......\n......\n......\n......\n......\n"),
        Test("8\n........\n........\n........\n........\n........\n........\n........\n........\n"),
    ],
    gens=[
        Gen("small random", _board_small, 15),
        Gen("n = 10, a few damaged", lambda rng: _board(rng, 10, 0.08), 2),
        Gen("n = 13, undamaged", lambda rng: _board(rng, 13, 0.0), 1, large=True),
        Gen("n = 13, lightly damaged", lambda rng: _board(rng, 13, 0.04), 1, large=True),
        Gen("n = 12, damaged", lambda rng: _board(rng, 12, 0.1), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<string> board;
vector<char> col, d1, d2;                     // column, "/" diagonal (r+c), "\" diagonal (r-c+n-1)
long long ways = 0;

void place(int r) {                           // rows 0..r-1 already hold one queen each
    if (r == n) {
        ways++;
        return;
    }
    for (int c = 0; c < n; c++) {
        if (board[r][c] == '*' || col[c] || d1[r + c] || d2[r - c + n - 1]) continue;  // prune
        col[c] = d1[r + c] = d2[r - c + n - 1] = 1;
        place(r + 1);
        col[c] = d1[r + c] = d2[r - c + n - 1] = 0;     // undo
    }
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n;
    board.resize(n);
    for (auto& row : board) cin >> row;
    col.assign(n, 0);
    d1.assign(2 * n - 1, 0);
    d2.assign(2 * n - 1, 0);
    place(0);
    cout << ways << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<string> b(n);
    for (auto& row : b) cin >> row;
    vector<int> p(n);                         // p[r]: the column of the queen in row r
    iota(p.begin(), p.end(), 0);
    long long ways = 0;
    do {
        bool ok = true;
        for (int r = 0; r < n && ok; r++) {
            if (b[r][p[r]] == '*') ok = false;
            for (int q = 0; q < r && ok; q++)
                if (abs(p[r] - p[q]) == r - q) ok = false;
        }
        if (ok) ways++;
    } while (next_permutation(p.begin(), p.end()));
    cout << ways << '\n';
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
    vector<string> b(n);
    for (auto& row : b) cin >> row;
    vector<int> p(n);                         // generate every permutation, then check it
    iota(p.begin(), p.end(), 0);
    long long ways = 0;
    do {
        bool ok = true;
        for (int r = 0; r < n && ok; r++) {
            if (b[r][p[r]] == '*') ok = false;
            for (int q = 0; q < r && ok; q++)
                if (abs(p[r] - p[q]) == r - q) ok = false;
        }
        if (ok) ways++;
    } while (next_permutation(p.begin(), p.end()));
    cout << ways << '\n';
}
""",
    hints=[
        r"""Every row holds exactly one queen. Place them row by row, and before placing a queen,
check it against the queens already on the board.""",
        r"""Mark used columns and diagonals in arrays: squares on one diagonal share `r + c`, on the
other `r − c` (add `n − 1` to make it an index). Undo the marks after the recursive call.""",
    ],
    editorial=r"""
One queen per row, so place them row by row. Before putting a queen on `(r, c)`, check that
the square is usable and that column `c`, diagonal `r + c` and anti-diagonal `r − c + n − 1`
are free (three boolean arrays make this O(1)); if not, skip the square, and the whole subtree
below it is never generated. That is **pruning**, and it is the difference between this and
"generate every permutation, then check": for the empty 13 × 13 board the pruned search visits
about 4.7·10^6 partial placements, against 13! ≈ 6.2·10^9 permutations.

After the recursive call, clear the three marks before trying the next column, or the search
silently forgets branches. Diagonal arrays need `2n − 1` entries.
""",
)

MEET_MIDDLE = Problem(
    id="meet_in_the_middle",
    title="Meet in the Middle",
    difficulty="hard",
    source="CSES 1628 - Meet in the Middle",
    complexity="O(2^(n/2) · n)",
    statement=r"""
You are given `n` positive integers `t_1, ..., t_n` and a target `x`. In how many ways can you
choose a subset of the positions whose values add up to exactly `x`? (Equal values at
different positions count as different choices.)
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 40, 1 ≤ x ≤ 10^9).

The second line has `n` integers t_1, ..., t_n (1 ≤ t_i ≤ 10^9).
""",
    output=r"""
Print one integer: the number of subsets with sum `x`.
""",
    samples=[
        Test("4 5\n1 2 3 2\n", "3\n", note="`2 + 3` (with either 2) and `1 + 2 + 2`."),
    ],
    tests=[
        Test("1 5\n5\n"),
        Test("1 4\n5\n"),
        Test("2 1000000000\n1000000000 1000000000\n"),
        Test("5 3\n1 1 1 1 1\n"),
        Test("20 1000000000\n" + " ".join(["50000000"] * 20) + "\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _mitm(rng, rng.randint(1, 16), 20, planted=rng.random() < 0.8), 15),
        Gen("n = 20, big values", lambda rng: _mitm(rng, 20, 10**8), 2),
        Gen("n = 40, all ones", lambda rng: "40 20\n" + " ".join(["1"] * 40) + "\n", 1, large=True),
        Gen("n = 40, random", lambda rng: _mitm(rng, 40, 5 * 10**7), 1, large=True),
        Gen("n = 40, small values", lambda rng: _mitm(rng, 40, 10), 1, large=True),
        Gen("n = 39, random", lambda rng: _mitm(rng, 39, 5 * 10**7), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// all 2^k subset sums of v, in increasing order: add one item at a time and merge
vector<long long> sums(const vector<long long>& v) {
    vector<long long> s = {0};
    for (long long a : v) {
        vector<long long> with(s.size()), merged(2 * s.size());
        for (size_t i = 0; i < s.size(); i++) with[i] = s[i] + a;
        merge(s.begin(), s.end(), with.begin(), with.end(), merged.begin());
        s.swap(merged);
    }
    return s;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> t(n);
    for (auto& v : t) cin >> v;
    vector<long long> A = sums(vector<long long>(t.begin(), t.begin() + n / 2));
    vector<long long> B = sums(vector<long long>(t.begin() + n / 2, t.end()));

    // count pairs a + b = x: a walks up through A, b walks down through B
    long long ways = 0;                       // up to C(40,20) = 1.4e11
    long long i = 0, j = (long long)B.size() - 1;
    while (i < (long long)A.size() && j >= 0) {
        long long s = A[i] + B[j];
        if (s < x) i++;
        else if (s > x) j--;
        else {                                // runs of equal sums multiply
            long long a = A[i], b = B[j], ca = 0, cb = 0;
            while (i < (long long)A.size() && A[i] == a) { i++; ca++; }
            while (j >= 0 && B[j] == b) { j--; cb++; }
            ways += ca * cb;
        }
    }
    cout << ways << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> t(n);
    for (auto& v : t) cin >> v;
    long long ways = 0;
    for (long long mask = 0; mask < (1LL << n); mask++) {
        long long s = 0;
        for (int i = 0; i < n; i++)
            if (mask >> i & 1) s += t[i];
        if (s == x) ways++;
    }
    cout << ways << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
long long x, ways = 0;
vector<long long> t;
void go(int i, long long s) {                 // plain complete search: 2^n leaves
    if (i == n) {
        if (s == x) ways++;
        return;
    }
    go(i + 1, s + t[i]);
    go(i + 1, s);
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> n >> x;
    t.resize(n);
    for (auto& v : t) cin >> v;
    go(0, 0);
    cout << ways << '\n';
}
""",
    hints=[
        r"""2^40 subsets is about 10^12: too many. But 2^20 is about 10^6. Split the numbers into
two halves.""",
        r"""List every subset sum of each half. A subset of everything has sum `x` exactly when its
left part sums to `a` and its right part to `x − a`: count those pairs.""",
        r"""Sort both lists and walk them with two pointers from opposite ends, multiplying the
lengths of runs of equal sums. The answer can reach C(40, 20) ≈ 1.4·10^11.""",
    ],
    editorial=r"""
Split the numbers into halves of sizes `⌊n/2⌋` and `⌈n/2⌉`. Every subset is a subset of the
left half plus a subset of the right half, and its sum is `a + b`. So list the 2^20 subset
sums of each half, and count pairs with `a + b = x`: Sum of Two Values (algo04) on two sorted
lists. Walk `A` upwards and `B` downwards; when `A[i] + B[j] = x`, a run of `ca` equal values in
`A` and `cb` equal values in `B` gives `ca · cb` subsets. That is 2 · 2^20 sums instead of 2^40.

Generating each half's sums already sorted (add one number at a time and `merge` the old list
with the old list shifted by that number) avoids the sort. Everything is `long long`: sums reach
4·10^10 and the count C(40, 20) = 137,846,528,820 (all ones, `x = 20`). A hash map from sums to
counts is correct too, but a million hash operations are several times slower than sorting.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo05",
    title="complete search, backtracking & meet in the middle",
    track="algo",
    order=5,
    summary="When the limits say 'try everything': subsets and permutations as recursion "
            "trees, counting the states before coding, pruning with backtracking, and meet "
            "in the middle for n ≤ 40.",
    prereqs=["cpp07", "cpp10"],
    tags=["complete search", "backtracking", "pruning", "subsets", "permutations",
          "meet in the middle", "recursion tree"],
    parts=[
        Part("When trying everything is the answer", [
            Say(r"""
Some problems are small on purpose. `n` apples with weights up to 10^9 must be split into two
groups so that the difference between the groups' total weights is as small as possible. The
limit: `n ≤ 20`.

There is no clever formula here, and greedy ideas fail (you will see one). The honest approach
is to try every split.
"""),
            Numeric(r"""
Each apple goes to group A or group B. How many splits are there for `n = 20`?
""", answer=2**20, rel=0.1, unit="splits",
                explain=r"""
2^20 = 1,048,576: every apple doubles the count.
"""),
            MCQ(r"""
Evaluating one split takes up to 20 additions: about 2·10^7 operations in all. What does that
tell you?
""", [
                Opt("Too slow: a clever greedy is needed.",
                    why="2·10^7 is a fifth of a second at the most pessimistic rate. And the greedy "
                        "'next heaviest apple into the lighter group' fails: on `3 3 2 2 2` it gets "
                        "a difference of 2, while `3 3` against `2 2 2` gives 0."),
                Opt("It fits easily. `n ≤ 20` is the setter's way of saying 'try every subset'.",
                    correct=True,
                    why="Yes. Small limits are information: nobody writes `n ≤ 20` for a problem "
                        "meant to be solved in O(n log n)."),
                Opt("It needs a DP over sums.",
                    why="A table of reachable sums would be as large as the total weight, up to "
                        "2·10^10. DP over sums is the tool when weights are *small* (algo07)."),
                Opt("It depends on the weights.",
                    why="The number of splits depends only on `n`, not on what the apples weigh."),
            ]),
            Say(r"""
Read the limits before anything else. Against ~10^8 simple operations per second, they point
at the intended complexity:

| n up to | what fits |
| 10-11 | `n!`: every order |
| 20 | `2^n` or `2^n · n`: every subset |
| 40 | `2^(n/2)`: meet in the middle (later in this lesson) |
| 500 | `n^3` |
| 5000 | `n^2` |
| 10^6 | `n log n` |
"""),
            Say(r"""
Every subset, as a recursion: decide apple `i`, then recurse on the rest.

```cpp
void search(int i, long long a) {         // a: weight already in group A
    if (i == n) {                         // a leaf: one complete split
        best = min(best, llabs(total - 2 * a));
        return;
    }
    search(i + 1, a + p[i]);              // apple i joins A
    search(i + 1, a);                     // apple i joins B
}
```

The calls form a **recursion tree**: the root decides apple 0, each level decides one more
apple, and every leaf is one split. (The bitmask loop from cpp10, `for (mask = 0; mask < 1 <<
n; mask++)`, visits the same leaves without the tree.)
"""),
            Numeric(r"""
How many calls to `search` happen in total, counting both leaves and inner calls, for
`n = 20`?
""", answer=2**21 - 1, rel=0.1, unit="calls",
                hint="A full binary tree of depth 20. Count the nodes level by level.",
                explain=r"""
`1 + 2 + 4 + ... + 2^20 = 2^21 − 1 ≈ 2.1·10^6`: twice the number of leaves. In a tree that
branches at every level, the leaves dominate, so counting leaves is enough for an estimate.
"""),
            Short(r"""
Apples `8 3 5 12`. What is the smallest possible difference?
""", accept=["2", "two"], placeholder="a number",
                explain=r"""
The total is 28, so a perfect split would be 14 and 14. No subset reaches 14 (`12` alone is 12,
`12 + 3` is 15, `8 + 5` is 13), so the best is 13 against 15: difference 2.
"""),
            MCQ(r"""
A solution keeps the group weights in `int`. Which input is the first to overflow it?
""", [
                Opt("10 apples of weight 10^8.",
                    why="The total is 10^9, and even `2 · a` in `total − 2a` stays at most 2·10^9: "
                        "it fits (just), since `int` goes to 2,147,483,647."),
                Opt("Any input with `n = 20`.",
                    why="The count of apples does not matter; the size of the sums does."),
                Opt("Three apples of weight 10^9.", correct=True,
                    why="Yes: the total 3·10^9 overflows although the true answer, 10^9, fits. "
                        "Overflow is undefined behaviour, and on this input the wrapped arithmetic "
                        "even prints 10^9 by luck, which is what makes it treacherous: with weights "
                        "`10^9 10^9 10^9 10^9 294967301` the total wraps to 5 and the program prints "
                        "5 instead of 294967301. The *intermediate* sums decide the type."),
                Opt("Only inputs whose answer is above 2^31.",
                    why="Four apples of 10^9 have answer 0, and their total still overflows."),
            ]),
            Try("apple_division", note="Every subset, `long long` sums. Several hidden tests have "
                "totals far beyond 2^31."),
        ]),
        Part("Orderings: the permutation tree", [
            Say(r"""
Some searches are over *orders*, not subsets. A campus has `n ≤ 10` buildings and one-way
streets between every pair; `d[i][j]` is the length from `i` to `j`. A night guard walks a
round that visits every building exactly once and returns to where it started, starting from
any building. Find the shortest round.
"""),
            Numeric(r"""
How many orders of `n = 10` buildings are there?
""", answer=3628800, rel=0.1, unit="orders",
                explain=r"""
`10! = 3,628,800`. With 10 additions each, about 3.6·10^7 operations: fine. At `n = 13` it would
be 6.2·10^9 orders, which is why `n!` searches come with limits around 10.
"""),
            Reflect(r"""
The round 1 → 2 → 3 → 4 → 1 and the round 2 → 3 → 4 → 1 → 2 walk exactly the same streets.
What does that let you fix, and how many orders are left for `n = 10`?
""", answer=r"""
A round has no real starting point, so fix building 1 as the start and permute only the other
`n − 1`: `9! = 362,880` orders, 10 times fewer. Spotting symmetries like this before coding is
part of counting the states. (If streets were two-way, a round and its reverse would cost the
same and you could halve again; here they are one-way.)
"""),
            Say(r"""
Generating permutations recursively, with a `used` array, and adding each street's length as
you go:

```cpp
void go(int last, int cnt, long long cost) {
    if (cnt == n) {                       // every building visited
        best = min(best, cost + d[last][0]);
        return;
    }
    for (int nxt = 1; nxt < n; nxt++) {
        if (used[nxt]) continue;
        used[nxt] = true;
        go(nxt, cnt + 1, cost + d[last][nxt]);
        used[nxt] = false;
    }
}
```
"""),
            MCQ(r"""
What happens if the line `used[nxt] = false;` is left out?
""", [
                Opt("Nothing: `used` is rebuilt by the next call anyway.",
                    why="Nothing rebuilds it. `used` is shared state, and every change stays until "
                        "someone undoes it."),
                Opt("After the first complete round, every building stays marked, so almost every "
                    "other order is never tried.", correct=True,
                    why="Yes. The search goes down one path, marks everything, and on the way back "
                        "finds every building taken. Undoing the change on the way back is what "
                        "makes it **backtracking**: each branch starts from the same state."),
                Opt("It visits some building twice.",
                    why="The opposite: marks are never removed, so buildings look taken even in "
                        "branches where they were not visited."),
                Opt("An infinite recursion.",
                    why="Every call either returns or increases `cnt`, so the depth is at most "
                        "`n`."),
            ]),
            MCQ(r"""
Instead of recursion, you can loop over `next_permutation` of a vector holding buildings
`2..n`. What must be true of the vector before the `do/while` loop?
""", [
                Opt("Nothing: `next_permutation` visits all orders from any starting order.",
                    why="It steps to the next order in lexicographic order and returns `false` "
                        "after the largest one. Starting in the middle skips every order before "
                        "the start."),
                Opt("It must be sorted in increasing order.", correct=True,
                    why="Yes: start from the smallest order and it walks through all of them "
                        "(cpp06)."),
                Opt("It must be sorted in decreasing order.",
                    why="That is the *last* order: `next_permutation` returns `false` at once and "
                        "the loop body runs one time."),
                Opt("It must not contain duplicates.",
                    why="Duplicates are fine: it then lists each *distinct* order once."),
            ]),
            MCQ(r"""
You keep the best complete round found so far and stop extending a partial round as soon as its
cost reaches `best`. What makes this pruning safe?
""", [
                Opt("The distances are symmetric.",
                    why="The streets here are one-way, and the cut is still safe."),
                Opt("The distances are integers.",
                    why="Integer or not, what matters is whether adding streets can make a round "
                        "shorter."),
                Opt("Nothing needs to hold: it is always safe.",
                    why="With a negative street, a round that looks too long now could become the "
                        "best one later, and cutting it would lose the answer."),
                Opt("The distances are non-negative, so a partial round can only get longer.",
                    correct=True,
                    why="Yes. This is **branch and bound**: a cheap bound (the cost so far) proves "
                        "that a whole subtree cannot beat the best answer found so far."),
            ]),
            Try("campus_tour", note="Fix the first building, recurse with `used`, undo, and keep "
                "costs in `long long`: 10 streets of 10^9."),
        ]),
        Part("Pruning: never extend a dead end", [
            Say(r"""
Now a search where pruning decides everything. An `n × n` board has some damaged squares.
Place `n` queens on usable squares so that no two attack each other (same row, column or
diagonal), and count the ways. Take `n = 8` first.

The most literal complete search picks 8 of the 64 squares.
"""),
            Numeric(r"""
How many ways are there to choose 8 squares out of 64?
""", answer=4426165368, rel=0.1, unit="choices",
                hint="The binomial coefficient C(64, 8).",
                explain=r"""
`C(64, 8) = 4,426,165,368 ≈ 4.4·10^9`. Correct, and tens of seconds for a mere 8 × 8 board.
"""),
            Short(r"""
Two queens in one row attack each other, and so do two in one column. So every row has
exactly one queen and every column too: a placement is "which column in each row", with all
columns different. How many such placements are there for `n = 8`?
""", accept=["40320", "40,320", "8!"], placeholder="a number",
                explain=r"""
`8! = 40,320`: a permutation of the columns. A little thought about the *structure* of valid
answers shrank the space 100,000 times before any code was written.
"""),
            Reflect(r"""
Generating all 8! permutations and checking diagonals at the end works for `n = 8`. What is
still wasted? Think about a permutation whose first two queens already attack each other.
""", answer=r"""
Once the first two queens attack, every completion of that prefix is doomed, yet
generate-then-check builds all of them and rejects each one at the end. The fix is to check
every queen as it is placed and never extend a prefix that is already invalid. That is
**backtracking with pruning**: a dead branch is cut at the node where it dies, so none of the
subtree below it is ever visited.
"""),
            Numeric(r"""
For `n = 8`, if the queens in the first two rows attack each other, how many complete
permutations does generate-then-check still build from that prefix?
""", answer=720,
                explain=r"""
The remaining 6 rows can take the remaining 6 columns in `6! = 720` ways, all rejected. The
pruned search spends one check on that prefix instead. For the empty 8 × 8 board, the pruned
search visits only 2,057 partial placements in all.
"""),
            Say(r"""
Row by row, with O(1) attack checks:

```cpp
void place(int r) {                       // rows 0..r-1 already hold a queen
    if (r == n) { ways++; return; }
    for (int c = 0; c < n; c++) {
        if (board[r][c] == '*' || col[c] || d1[r + c] || d2[r - c + n - 1]) continue;
        col[c] = d1[r + c] = d2[r - c + n - 1] = 1;
        place(r + 1);
        col[c] = d1[r + c] = d2[r - c + n - 1] = 0;
    }
}
```
"""),
            MCQ(r"""
Why does `r + c` identify one diagonal and `r − c + n − 1` the other?
""", [
                Opt("Moving one square down-left keeps `r + c` fixed; moving down-right keeps "
                    "`r − c` fixed. The `+ n − 1` shifts `r − c` (from `−(n−1)` to `n − 1`) into "
                    "a valid index.", correct=True,
                    why="Yes. Each array needs `2n − 1` entries, one per diagonal."),
                Opt("`r + c` is the distance from the corner, and queens at equal distances "
                    "attack.",
                    why="`(0, 2)` and `(1, 1)` have `r + c = 2` and do attack, but `(0, 0)` and "
                        "`(1, 1)` attack with sums 0 and 2. One array alone covers one direction."),
                Opt("It is a hash; collisions are rare enough not to matter.",
                    why="It is exact, not a hash: two squares share `r + c` exactly when they are "
                        "on the same down-left diagonal."),
            ]),
            Numeric(r"""
This problem allows `n ≤ 13`. How many permutations would generate-then-check build for
`n = 13`?
""", answer=6227020800, rel=0.5, unit="permutations",
                explain=r"""
`13! ≈ 6.2·10^9`: about 40 seconds here. The pruned search visits about 4.7·10^6 partial placements on
the empty 13 × 13 board, roughly 1,300 times fewer, and runs in a fraction of a second.
Pruning does not change the worst-case formula you can write down; it changes how much of the
tree actually exists.
"""),
            Try("queens", note="Row by row, three marker arrays of the right sizes, undo after "
                "the call. The hidden tests go up to `n = 13`."),
        ]),
        Part("Meet in the middle", [
            Say(r"""
Count the subsets of `n` positive numbers that add up to exactly `x`. The limits: `n ≤ 40`,
numbers and `x` up to 10^9.
"""),
            Numeric(r"""
How many subsets does plain complete search visit for `n = 40`?
""", answer=2**40, rel=0.5, unit="subsets",
                explain=r"""
2^40 ≈ 1.1·10^12: twenty minutes at 10^9 per second. And a DP over sums is out, because `x`
goes to 10^9. But `n ≤ 40` is exactly twice the `n ≤ 20` that complete search handles.
"""),
            Reflect(r"""
Split the numbers into a left half and a right half of 20 each. Every subset is a left part
plus a right part. How does that turn one search of 2^40 into two of 2^20?
""", answer=r"""
List all 2^20 subset sums of the left half (list `A`) and all 2^20 of the right half (list
`B`). A subset has sum `x` exactly when its left part sums to some `a` in `A` and its right part
to `x − a` in `B`. So the question becomes: how many pairs `(a, b)` from the two lists have
`a + b = x`? Sort both and walk them with two pointers, or binary search for `x − a`: this is
Sum of Two Values (algo04) on lists of 10^6. About `2 · 2^20 · 20 ≈ 4·10^7` operations instead
of 10^12. That is **meet in the middle**.
"""),
            Short(r"""
While walking the lists you reach `A[i] + B[j] = x`, and the value `A[i]` appears 3 times in
a row in `A`, while `B[j]` appears 4 times in a row in `B`. How many subsets does that account
for?
""", accept=["12", "twelve"], placeholder="a number",
                explain=r"""
Every one of the 3 left parts combines with every one of the 4 right parts: `3 · 4 = 12`.
Then skip both runs. Counting 1 and moving a single pointer undercounts: the other copies in
the other run never get paired.
"""),
            Numeric(r"""
All 40 numbers are 1 and `x = 20`. How many subsets? (The binomial coefficient C(40, 20).)
""", answer=137846528820, rel=0.5,
                explain=r"""
`C(40, 20) = 137,846,528,820 ≈ 1.4·10^11`: 64 times more than an `int` holds. The count is a
`long long`, and so is `ca · cb` in the run product, since each run can have hundreds of
thousands of entries.
"""),
            MCQ(r"""
To combine the halves, which approach is the safe choice on a strict time limit?
""", [
                Opt("Put the right half's sums in an `unordered_map<long long, int>` of counts, "
                    "then look up `x − a` for every left sum.",
                    why="Correct and O(2^20) expected, but a million hash insertions with keys "
                        "spread up to 2·10^10 are cache-hostile and several times slower than "
                        "sorting; on CSES this problem is notorious for timing out with it."),
                Opt("Sort both lists (or build them already sorted) and walk them with two "
                    "pointers from opposite ends.", correct=True,
                    why="Yes: sequential memory access, no hashing, deterministic. Adding one number "
                        "at a time and merging the old list with the old list shifted by that "
                        "number even produces each list sorted without calling `sort`."),
                Opt("For each left sum, loop over all right sums.",
                    why="`2^20 · 2^20 = 2^40`: all the work of the plain search again."),
            ]),
            Try("meet_in_the_middle", note="Split, list both halves' sums in sorted order, two "
                "pointers with run lengths, `long long` everywhere."),
        ]),
        Part("When searching is the wrong tool", [
            MCQ(r"""
Which of these is *not* a job for complete search at its limits?
""", [
                Opt("Count placements of `n ≤ 13` queens on a damaged board.",
                    why="Backtracking with pruning: the lesson's third problem."),
                Opt("Split `n ≤ 20` weights into two groups as evenly as possible.",
                    why="2^20 subsets: Apple Division."),
                Opt("Choose items from `n ≤ 100` with weights `w_i ≤ 1000` to maximise value "
                    "within a capacity of 10^5.", correct=True,
                    why="Right. 2^100 subsets is hopeless, but capacities and weights are small: a "
                        "DP over capacities, `n · W = 10^7` (the knapsack of algo07)."),
                Opt("Count subsets of `n ≤ 40` numbers with sum `x`.",
                    why="Meet in the middle: two searches of 2^20."),
            ]),
            Reflect(r"""
Apple Division again, but `n ≤ 100` and weights `≤ 1000`. Complete search is dead (2^100).
Many different subsets have the same total weight. How can that be used?
""", answer=r"""
The search only ever needs to know *which totals* group A can reach, not which apples produced
them. The total is at most `100 · 1000 = 10^5`, so keep a table `reach[s]` = "some subset of
the apples seen so far weighs `s`", and update it apple by apple: O(n · total) = 10^7. The
answer is the reachable `s` closest to `total / 2`. The subsets that land on the same sum were
*overlapping subproblems*: complete search explores each of them again and again, and
recognising that is the step from complete search to dynamic programming (algo06).
"""),
        ]),
    ],
    problems=[APPLE_DIVISION, CAMPUS_TOUR, QUEENS, MEET_MIDDLE],
    cards=[
        Card(r"""Which complexity does each limit suggest: `n ≤ 10`, `n ≤ 20`, `n ≤ 40`?""",
             r"""`n ≤ 10-11`: `n!` (every order). `n ≤ 20`: `2^n` or `2^n · n` (every subset). `n ≤ 40`: `2^(n/2)` (meet in the middle)."""),
        Card(r"""How many nodes does the include/exclude recursion over `n` items have?""",
             r"""`2^(n+1) − 1`: `2^n` leaves plus `2^n − 1` inner calls. Counting leaves is enough for an estimate."""),
        Card(r"""What makes a recursive search "backtracking"?""",
             r"""Every change to shared state (a `used` mark, a placed queen) is undone after the recursive call, so each branch starts from the same state."""),
        Card(r"""`next_permutation` in a `do/while` loop: what must hold before the loop?""",
             r"""The range must start sorted in increasing order; otherwise the orders before the starting one are skipped."""),
        Card(r"""Shortest round trip through `n` points: how do you cut the search by a factor of `n`?""",
             r"""A cycle has no real start: fix the first point and permute the other `n − 1`: `(n − 1)!` orders."""),
        Card(r"""When is "stop if the partial cost ≥ best" (branch and bound) safe?""",
             r"""When costs can only grow as the partial solution is extended, e.g. non-negative distances."""),
        Card(r"""n queens: which indices identify the two diagonals of square `(r, c)`?""",
             r"""`r + c` and `r − c + n − 1`, each ranging over `2n − 1` values."""),
        Card(r"""What does pruning buy on the empty 13 × 13 queens board?""",
             r"""About 4.7·10^6 partial placements visited, instead of 13! ≈ 6.2·10^9 permutations generated and checked."""),
        Card(r"""Meet in the middle for "count subsets with sum `x`", `n ≤ 40`?""",
             r"""List the 2^20 subset sums of each half, sort, and count pairs `a + b = x` with two pointers, multiplying the lengths of runs of equal sums."""),
        Card(r"""How do you list all subset sums of `k` numbers already sorted?""",
             r"""Start with `{0}`; for each number `a`, `merge` the list with the list shifted by `a`. O(2^k) in total."""),
        Card(r"""When does complete search give way to DP?""",
             r"""When many branches reach the same state (overlapping subproblems), e.g. subsets with equal sums when the weights are small."""),
    ],
)
