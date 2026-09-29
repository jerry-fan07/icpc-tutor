from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _range(rng, n, wide):
    if wide:                                   # nearly the whole array, every time
        l, r = rng.randint(1, min(n, 40)), rng.randint(max(1, n - 40), n)
    else:
        l = rng.randint(1, n)
        r = rng.randint(l, n)
    return (l, r) if l <= r else (r, l)


def _ops_min(rng, n, q, vmax, wide=False):
    a = [rng.randint(1, vmax) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        if rng.random() < 0.5:
            out.append(f"1 {rng.randint(1, n)} {rng.randint(1, vmax)}")
        else:
            l, r = _range(rng, n, wide)
            out.append(f"2 {l} {r}")
    return "\n".join(out) + "\n"


def _ops_kadane(rng, n, q, lo, hi, wide=False):
    a = [rng.randint(lo, hi) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        if rng.random() < 0.5:
            out.append(f"1 {rng.randint(1, n)} {rng.randint(lo, hi)}")
        else:
            l, r = _range(rng, n, wide)
            out.append(f"2 {l} {r}")
    return "\n".join(out) + "\n"


def _hotels(rng, n, m, mode):
    if mode == "worst":                        # every group has to pass all the tiny hotels
        h = [1] * (n - 1) + [10**9]
        r = [rng.randint(2, 1000) for _ in range(m)]
    elif mode == "increasing":
        h = sorted(rng.randint(1, 10**9) for _ in range(n))
        r = [rng.randint(1, 10**9) for _ in range(m)]
    elif mode == "small":
        h = [rng.randint(1, 10) for _ in range(n)]
        r = [rng.randint(1, 12) for _ in range(m)]
    else:
        h = [rng.randint(1, 10**5) for _ in range(n)]
        r = [rng.randint(1, 10**5) for _ in range(m)]
    return f"{n} {m}\n" + " ".join(map(str, h)) + "\n" + " ".join(map(str, r)) + "\n"


def _ops_lazy(rng, n, q, vmax, wide=False):
    a = [rng.randint(1, vmax) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        l, r = _range(rng, n, wide)
        t = rng.randint(1, 3)
        if t == 3:
            out.append(f"3 {l} {r}")
        else:
            out.append(f"{t} {l} {r} {rng.randint(1, vmax)}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- problems
DYNAMIC_RMQ = Problem(
    id="dynamic_rmq",
    title="Dynamic Range Minimum",
    difficulty="easy",
    source="CSES 1649 - Dynamic Range Minimum Queries",
    complexity="O(n + q log n)",
    statement=r"""
An array of `n` integers is given. Process `q` operations of two kinds, in order:

- `1 k u`: set a_k to `u`;
- `2 a b`: print min(a_a, ..., a_b).
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

Each of the next `q` lines is `1 k u` (1 ≤ k ≤ n, 1 ≤ u ≤ 10^9) or `2 a b` (1 ≤ a ≤ b ≤ n).
""",
    output=r"""
For each operation of the second kind, print the minimum on its own line.
""",
    samples=[
        Test("8 4\n3 2 4 5 1 1 5 3\n2 1 4\n2 5 6\n1 2 3\n2 1 4\n", "2\n1\n3\n"),
    ],
    tests=[
        Test("1 3\n5\n2 1 1\n1 1 1000000000\n2 1 1\n"),
        Test("6 4\n9 9 9 9 9 9\n1 6 1\n2 1 5\n2 1 6\n2 6 6\n"),
        Test("5 3\n1 2 3 4 5\n1 1 10\n2 1 1\n2 1 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _ops_min(rng, rng.randint(1, 12), rng.randint(1, 14), 20), 14),
        Gen("medium random", lambda rng: _ops_min(rng, 5000, 5000, 10**9), 2),
        Gen("max size, whole-array queries", lambda rng: _ops_min(rng, 200000, 200000, 10**9, True), 1, large=True),
        Gen("max size, random", lambda rng: _ops_min(rng, 200000, 200000, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<int> t;                            // t[v] = min of node v's segment; root is 1

void build(int v, int l, int r, const vector<int>& a) {
    if (l == r) { t[v] = a[l]; return; }
    int m = (l + r) / 2;
    build(2 * v, l, m, a);
    build(2 * v + 1, m + 1, r, a);
    t[v] = min(t[2 * v], t[2 * v + 1]);
}

void update(int v, int l, int r, int pos, int val) {
    if (l == r) { t[v] = val; return; }
    int m = (l + r) / 2;
    if (pos <= m) update(2 * v, l, m, pos, val);
    else update(2 * v + 1, m + 1, r, pos, val);
    t[v] = min(t[2 * v], t[2 * v + 1]);  // recompute on the way back up
}

int query(int v, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return INT_MAX;             // disjoint: the identity of min
    if (ql <= l && r <= qr) return t[v];              // fully inside: use the stored value
    int m = (l + r) / 2;                              // partial: ask both children
    return min(query(2 * v, l, m, ql, qr), query(2 * v + 1, m + 1, r, ql, qr));
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> n >> q;
    vector<int> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    t.assign(4 * n, 0);
    build(1, 1, n, a);
    while (q--) {
        int type, x, y;
        cin >> type >> x >> y;
        if (type == 1) update(1, 1, n, x, y);
        else cout << query(1, 1, n, x, y) << '\n';
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
    vector<int> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int type, x, y;
        cin >> type >> x >> y;
        if (type == 1) a[x] = y;
        else cout << *min_element(a.begin() + x, a.begin() + y + 1) << '\n';
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
    vector<int> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int type, x, y;
        cin >> type >> x >> y;
        if (type == 1) a[x] = y;
        else {
            int m = INT_MAX;
            for (int i = x; i <= y; i++) m = min(m, a[i]);
            cout << m << '\n';
        }
    }
}
""",
    hints=[
        r"""Store the minimum of every segment of a binary split: the whole array, its halves, their
halves, down to single elements. How many of these contain a given position?""",
        r"""Update: change the leaf, then recompute each ancestor from its two children. Query:
return the stored value of a node inside `[a, b]`, nothing (`INT_MAX`) for a node outside,
and recurse into both children otherwise.""",
    ],
    editorial=r"""
Segment tree. Node 1 covers `[1, n]`; a node covering `[l, r]` with `l < r` has children
`2v` covering `[l, m]` and `2v + 1` covering `[m + 1, r]`, `m = (l + r)/2`. Each node stores
the minimum of its segment.

A point update changes one leaf and the `log2 n` nodes above it, each recomputed from its
two children. A query returns the stored value of nodes inside the range, the identity
`INT_MAX` for nodes outside it, and recurses into both children of nodes that overlap it
partially. Only nodes that straddle one of the two ends of the query are partial, at most
two per level, so a query visits at most 4 nodes per level: O(log n).

The array needs `4n` entries: with children at `2v, 2v + 1`, indices can pass `2n` when `n`
is not a power of two. A bottom-up (iterative) tree with leaves at `n..2n−1` needs only
`2n` entries and is usually faster.
""",
)

MAX_SUBARRAY = Problem(
    id="max_subarray_queries",
    title="Best Stretch",
    difficulty="medium",
    source="SPOJ GSS3 - Can you answer these queries III",
    complexity="O(n + q log n)",
    statement=r"""
A trader records one profit per day, possibly negative. Process `q` operations in order:

- `1 k x`: the profit of day `k` is corrected to `x`;
- `2 a b`: among all non-empty stretches of consecutive days inside days `a..b`, print the
  largest total profit.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has a_1, ..., a_n (−10^9 ≤ a_i ≤ 10^9).

Each of the next `q` lines is `1 k x` (1 ≤ k ≤ n, −10^9 ≤ x ≤ 10^9) or `2 a b`
(1 ≤ a ≤ b ≤ n).
""",
    output=r"""
For each operation of the second kind, print the answer on its own line.
""",
    samples=[
        Test("6 4\n2 -5 3 4 -1 2\n2 1 6\n2 1 3\n1 2 5\n2 1 3\n", "8\n3\n10\n"),
        Test("3 2\n-4 -2 -7\n2 1 3\n2 3 3\n", "-2\n-7\n",
             note="The stretch must be non-empty, so the answer can be negative."),
    ],
    tests=[
        Test("1 2\n-1000000000\n2 1 1\n2 1 1\n"),
        Test("4 3\n1000000000 1000000000 1000000000 1000000000\n2 1 4\n1 3 -1000000000\n2 1 4\n"),
        Test("5 3\n-1 -1 5 -1 -1\n2 1 2\n2 2 4\n2 4 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _ops_kadane(rng, rng.randint(1, 12), rng.randint(1, 14), -10, 10), 14),
        Gen("small, all negative", lambda rng: _ops_kadane(rng, rng.randint(1, 10), rng.randint(1, 10), -20, -1), 4),
        Gen("medium, big values", lambda rng: _ops_kadane(rng, 3000, 3000, -10**9, 10**9), 2),
        Gen("max size, whole-array queries", lambda rng: _ops_kadane(rng, 200000, 200000, -10**9, 10**9, True), 1, large=True),
        Gen("max size, random", lambda rng: _ops_kadane(rng, 200000, 200000, -10**9, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// what a node knows about its segment (all over non-empty stretches)
struct Node {
    long long sum, pref, suf, best;
};

Node leaf(long long x) { return {x, x, x, x}; }

Node merge(const Node& L, const Node& R) {       // L is to the left of R: order matters
    return {
        L.sum + R.sum,
        max(L.pref, L.sum + R.pref),               // prefix: inside L, or all of L and into R
        max(R.suf, R.sum + L.suf),                 // suffix: inside R, or all of R and into L
        max({L.best, R.best, L.suf + R.pref})      // best: left, right, or across the middle
    };
}

int n;
vector<Node> t;

void build(int v, int l, int r, const vector<long long>& a) {
    if (l == r) { t[v] = leaf(a[l]); return; }
    int m = (l + r) / 2;
    build(2 * v, l, m, a);
    build(2 * v + 1, m + 1, r, a);
    t[v] = merge(t[2 * v], t[2 * v + 1]);
}

void update(int v, int l, int r, int pos, long long x) {
    if (l == r) { t[v] = leaf(x); return; }
    int m = (l + r) / 2;
    if (pos <= m) update(2 * v, l, m, pos, x);
    else update(2 * v + 1, m + 1, r, pos, x);
    t[v] = merge(t[2 * v], t[2 * v + 1]);
}

// only called on nodes that overlap [ql, qr], so no "empty" node is ever needed
Node query(int v, int l, int r, int ql, int qr) {
    if (ql <= l && r <= qr) return t[v];
    int m = (l + r) / 2;
    if (qr <= m) return query(2 * v, l, m, ql, qr);
    if (ql > m) return query(2 * v + 1, m + 1, r, ql, qr);
    return merge(query(2 * v, l, m, ql, qr), query(2 * v + 1, m + 1, r, ql, qr));
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> n >> q;
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    t.assign(4 * n, leaf(0));
    build(1, 1, n, a);
    while (q--) {
        int type;
        long long x, y;
        cin >> type >> x >> y;
        if (type == 1) update(1, 1, n, (int)x, y);
        else cout << query(1, 1, n, (int)x, (int)y).best << '\n';
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
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int type;
        long long x, y;
        cin >> type >> x >> y;
        if (type == 1) { a[x] = y; continue; }
        long long best = LLONG_MIN;
        for (int i = x; i <= y; i++) {           // every non-empty stretch
            long long s = 0;
            for (int j = i; j <= y; j++) { s += a[j]; best = max(best, s); }
        }
        cout << best << '\n';
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
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int type;
        long long x, y;
        cin >> type >> x >> y;
        if (type == 1) { a[x] = y; continue; }
        long long best = LLONG_MIN, cur = 0;     // Kadane on the range
        for (int i = x; i <= y; i++) {
            cur = max(a[i], cur + a[i]);
            best = max(best, cur);
        }
        cout << best << '\n';
    }
}
""",
    hints=[
        r"""A node that only stores its best stretch cannot be merged: the best stretch of the parent
may cross the middle. What else must each node remember?""",
        r"""Keep `sum`, `pref` (best non-empty prefix), `suf` (best non-empty suffix) and `best`.
`best = max(L.best, R.best, L.suf + R.pref)`, `pref = max(L.pref, L.sum + R.pref)`,
`suf = max(R.suf, R.sum + L.suf)`.""",
        r"""The merge is not commutative. In a query, combine the pieces left to right. For an
all-negative range the answer is negative: never start from 0.""",
    ],
    editorial=r"""
Each node stores four numbers about its segment: the total `sum`, the best non-empty
prefix `pref`, the best non-empty suffix `suf`, and the best non-empty stretch `best`. They
are closed under merging a left part `L` with a right part `R`:

```
sum  = L.sum + R.sum
pref = max(L.pref, L.sum + R.pref)
suf  = max(R.suf,  R.sum + L.suf)
best = max(L.best, R.best, L.suf + R.pref)
```

The only stretch that is neither inside `L` nor inside `R` crosses the middle, and the
best of those is a suffix of `L` followed by a prefix of `R`. A leaf with value `x` has all
four equal to `x`.

Point updates and queries work as for the minimum, O(log n), with one care: `merge` is not
commutative, so query pieces must be combined in left-to-right order. The reference only
recurses into halves that overlap the range, so it never needs an "empty" node; if you use
one, give it `sum = 0` and `pref = suf = best = −10^18` (not `LLONG_MIN`, which overflows
when two are added, and not 0, which would allow an empty stretch).
""",
)

HOTEL_QUERIES = Problem(
    id="hotel_queries",
    title="Hotel Queries",
    difficulty="medium",
    source="CSES 1143 - Hotel Queries",
    complexity="O((n + m) log n)",
    statement=r"""
`n` hotels stand along a street, numbered 1 to `n` from left to right; hotel `i` has h_i free
rooms. Groups of tourists arrive one after another. A group of `r` people wants to stay
together, so it takes the leftmost hotel that still has at least `r` free rooms, and those
rooms are no longer free.

For every group, print the hotel it takes, or 0 if no hotel has enough rooms (then nothing
changes).
""",
    input=r"""
The first line has `n` and `m` (1 ≤ n, m ≤ 2·10^5): hotels and groups.

The second line has h_1, ..., h_n (1 ≤ h_i ≤ 10^9).

The third line has the group sizes r_1, ..., r_m (1 ≤ r_i ≤ 10^9), in order of arrival.
""",
    output=r"""
Print `m` integers on one line: the hotel of each group, or 0.
""",
    samples=[
        Test("8 5\n3 2 4 1 5 5 2 6\n4 4 7 1 1\n", "3 5 0 1 1\n"),
    ],
    tests=[
        Test("1 3\n5\n5 1 1\n"),
        Test("3 4\n1000000000 1 1000000000\n1000000000 1000000000 1000000000 1\n"),
        Test("4 4\n1 2 3 4\n4 3 2 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _hotels(rng, rng.randint(1, 10), rng.randint(1, 12), "small"), 16),
        Gen("medium random", lambda rng: _hotels(rng, 3000, 3000, "random"), 2),
        Gen("max size, the big hotel is last", lambda rng: _hotels(rng, 200000, 200000, "worst"), 1, large=True),
        Gen("max size, increasing capacities", lambda rng: _hotels(rng, 200000, 200000, "increasing"), 1, large=True),
        Gen("max size, random", lambda rng: _hotels(rng, 200000, 200000, "random"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<int> t;                            // t[v] = most free rooms in any hotel of v's segment

void build(int v, int l, int r, const vector<int>& h) {
    if (l == r) { t[v] = h[l]; return; }
    int m = (l + r) / 2;
    build(2 * v, l, m, h);
    build(2 * v + 1, m + 1, r, h);
    t[v] = max(t[2 * v], t[2 * v + 1]);
}

// precondition t[v] >= need: walk to the leftmost hotel with enough rooms, book it,
// and fix the maxima on the way back up
int book(int v, int l, int r, int need) {
    if (l == r) { t[v] -= need; return l; }
    int m = (l + r) / 2;
    int res = (t[2 * v] >= need) ? book(2 * v, l, m, need)       // leftmost: try left first
                                 : book(2 * v + 1, m + 1, r, need);
    t[v] = max(t[2 * v], t[2 * v + 1]);
    return res;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int m;
    cin >> n >> m;
    vector<int> h(n + 1);
    for (int i = 1; i <= n; i++) cin >> h[i];
    t.assign(4 * n, 0);
    build(1, 1, n, h);
    for (int g = 0; g < m; g++) {
        int r;
        cin >> r;
        int ans = (t[1] >= r) ? book(1, 1, n, r) : 0;   // the root knows if anyone fits
        cout << ans << (g + 1 == m ? '\n' : ' ');
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, m;
    cin >> n >> m;
    vector<int> h(n + 1);
    for (int i = 1; i <= n; i++) cin >> h[i];
    for (int g = 0; g < m; g++) {
        int r, ans = 0;
        cin >> r;
        for (int i = 1; i <= n; i++)
            if (h[i] >= r) { h[i] -= r; ans = i; break; }
        cout << ans << ' ';
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
    int n, m;
    cin >> n >> m;
    vector<int> h(n + 1);
    for (int i = 1; i <= n; i++) cin >> h[i];
    for (int g = 0; g < m; g++) {
        int r, ans = 0;
        cin >> r;
        for (int i = 1; i <= n; i++)
            if (h[i] >= r) { h[i] -= r; ans = i; break; }
        cout << ans << ' ';
    }
    cout << '\n';
}
""",
    hints=[
        r"""Scanning from the left is O(n) per group, 4·10^10 when the early hotels are all too small.
Keep a segment tree of maximum free rooms.""",
        r"""If the root's maximum is below `r`, print 0. Otherwise walk down: go left whenever the left
child's maximum is at least `r` (the leftmost fit is there), else go right. Subtract at the
leaf and recompute the maxima on the way back.""",
    ],
    editorial=r"""
A segment tree over the hotels storing the maximum free rooms of each segment. For a group
of size `r`: if the root's maximum is below `r`, nobody fits: 0. Otherwise walk down from the
root, keeping the invariant "the leftmost hotel with at least `r` rooms is inside the current
segment": if the left child's maximum is at least `r`, the answer is in the left half (and
it is further left than anything in the right half); otherwise it must be in the right
half. At the leaf, subtract `r` and recompute the maxima on the way back up. One root-to-leaf
walk: O(log n) per group.

A `multiset` of capacities finds *a* hotel with enough rooms, but not the leftmost one.
Binary search over positions with range-maximum queries works too, in O(log^2 n).
""",
)

RANGE_UPDATES_SUMS = Problem(
    id="range_updates_sums",
    title="Range Updates and Sums",
    difficulty="hard",
    source="CSES 1735 - Range Updates and Sums",
    complexity="O(n + q log n)",
    statement=r"""
An array of `n` integers is given. Process `q` operations of three kinds, in order:

- `1 a b x`: add `x` to every a_i with a ≤ i ≤ b;
- `2 a b x`: set every a_i with a ≤ i ≤ b to `x`;
- `3 a b`: print a_a + ... + a_b.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^6).

Each of the next `q` lines is `1 a b x`, `2 a b x` (1 ≤ a ≤ b ≤ n, 1 ≤ x ≤ 10^6) or `3 a b`
(1 ≤ a ≤ b ≤ n).
""",
    output=r"""
For each operation of the third kind, print the sum on its own line.
""",
    samples=[
        Test("6 5\n2 3 1 1 5 3\n3 3 5\n1 2 4 2\n3 3 5\n2 2 4 5\n3 3 5\n", "7\n11\n15\n"),
        Test("4 4\n1 1 1 1\n2 1 4 2\n1 1 2 3\n2 2 3 1\n3 1 4\n", "9\n",
             note="After the last update the array is 5 1 1 2."),
    ],
    tests=[
        Test("1 4\n1000000\n1 1 1 1000000\n3 1 1\n2 1 1 7\n3 1 1\n"),
        Test("5 4\n1 2 3 4 5\n1 1 5 1000000\n1 1 5 1000000\n1 2 4 1000000\n3 1 5\n"),
        Test("5 5\n1 1 1 1 1\n1 1 5 2\n2 2 4 10\n1 3 5 1\n2 5 5 4\n3 1 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _ops_lazy(rng, rng.randint(1, 12), rng.randint(1, 14), 10), 16),
        Gen("medium, big values", lambda rng: _ops_lazy(rng, 3000, 3000, 10**6), 2),
        Gen("max size, whole-array operations", lambda rng: _ops_lazy(rng, 200000, 200000, 10**6, True), 1, large=True),
        Gen("max size, random", lambda rng: _ops_lazy(rng, 200000, 200000, 10**6), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// Every node has a sum and a pending tag "set every element to setv (if setv != 0),
// then add addv", which has already been applied to the node's own sum but not yet
// to its children. Values are >= 1, so setv = 0 can mean "no assignment pending".
int n;
vector<long long> sum_, setv, addv;

void apply(int v, long long len, long long s, long long a) {
    if (s != 0) {                          // an assignment wipes out everything pending
        sum_[v] = s * len;
        setv[v] = s;
        addv[v] = 0;
    }
    if (a != 0) {                          // an addition stacks on top
        sum_[v] += a * len;
        addv[v] += a;
    }
}

void push(int v, int l, int r) {           // hand the tag to the children
    int m = (l + r) / 2;
    apply(2 * v, m - l + 1, setv[v], addv[v]);
    apply(2 * v + 1, r - m, setv[v], addv[v]);
    setv[v] = addv[v] = 0;
}

void build(int v, int l, int r, const vector<long long>& a) {
    if (l == r) { sum_[v] = a[l]; return; }
    int m = (l + r) / 2;
    build(2 * v, l, m, a);
    build(2 * v + 1, m + 1, r, a);
    sum_[v] = sum_[2 * v] + sum_[2 * v + 1];
}

void update(int v, int l, int r, int ql, int qr, long long s, long long a) {
    if (qr < l || r < ql) return;
    if (ql <= l && r <= qr) { apply(v, r - l + 1, s, a); return; }   // stop here: lazy
    push(v, l, r);                         // about to go below v: settle v's tag first
    int m = (l + r) / 2;
    update(2 * v, l, m, ql, qr, s, a);
    update(2 * v + 1, m + 1, r, ql, qr, s, a);
    sum_[v] = sum_[2 * v] + sum_[2 * v + 1];
}

long long query(int v, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return 0;
    if (ql <= l && r <= qr) return sum_[v];
    push(v, l, r);
    int m = (l + r) / 2;
    return query(2 * v, l, m, ql, qr) + query(2 * v + 1, m + 1, r, ql, qr);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> n >> q;
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    sum_.assign(4 * n, 0);
    setv.assign(4 * n, 0);
    addv.assign(4 * n, 0);
    build(1, 1, n, a);
    while (q--) {
        int type, l, r;
        cin >> type >> l >> r;
        if (type == 3) {
            cout << query(1, 1, n, l, r) << '\n';
        } else {
            long long x;
            cin >> x;
            if (type == 1) update(1, 1, n, l, r, 0, x);
            else update(1, 1, n, l, r, x, 0);
        }
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
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int type, l, r;
        cin >> type >> l >> r;
        if (type == 3) {
            long long s = 0;
            for (int i = l; i <= r; i++) s += a[i];
            cout << s << '\n';
        } else {
            long long x;
            cin >> x;
            for (int i = l; i <= r; i++) a[i] = (type == 1 ? a[i] + x : x);
        }
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
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int type, l, r;
        cin >> type >> l >> r;
        if (type == 3) {
            long long s = 0;
            for (int i = l; i <= r; i++) s += a[i];
            cout << s << '\n';
        } else {
            long long x;
            cin >> x;
            if (type == 1) for (int i = l; i <= r; i++) a[i] += x;
            else for (int i = l; i <= r; i++) a[i] = x;
        }
    }
}
""",
    hints=[
        r"""A range update splits into O(log n) fully covered nodes, like a query. For a covered node,
update its sum right away and leave a note ("tag") for its children instead of visiting them.""",
        r"""Before going below a node, push its tag to the two children. A tag here is "set to s (maybe),
then add a". Adding onto a tag adds to `a`; an assignment replaces the whole tag.""",
        r"""A node of length `len` with tag `(s, a)`: `sum = s·len` if `s` is set, then `sum += a·len`.
Compute in `long long`: `x·len` alone can be 2·10^11.""",
    ],
    editorial=r"""
Lazy propagation. A range update decomposes into the same O(log n) canonical nodes as a
query. For each fully covered node, update its sum immediately and store a pending **tag**
for its subtree instead of descending. Whenever a later operation needs to go below a
node, it first **pushes** the node's tag to the two children (applies it to their sums and
merges it into their tags). Postponing is safe because every access to a descendant
passes through its ancestors, and each one pushes before descending: nobody ever reads a
stale value.

The tag is "assign `s` (if any), then add `a`". Tags compose into a tag of the same shape:
an addition `x` arriving on `(s, a)` gives `(s, a + x)`; an assignment `x` gives `(x, 0)`,
because it overwrites everything before it. Applying `(s, a)` to a node of length `len`:
`sum = s·len` if `s` is set, then `sum += a·len`. Every operation is O(log n).

Sums reach about `2·10^5 · (10^6 + 2·10^5 · 10^6) ≈ 4·10^16`, and even `x · len` is
2·10^11: every product in `long long`.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo16",
    title="range queries II: segment trees",
    track="algo",
    order=16,
    summary="The segment tree: a binary split of the array whose nodes combine without an "
            "inverse. Point updates, the O(log n) query argument, the bottom-up version, custom "
            "node summaries, walking down the tree, and lazy propagation for range updates.",
    prereqs=["algo15"],
    tags=["segment tree", "range minimum", "iterative segment tree", "maximum subarray",
          "tree descent", "lazy propagation", "range assignment"],
    parts=[
        Part("A tree of ranges", [
            Say(r"""
algo15 left one gap. Take an array of `n ≤ 2·10^5` values with `q ≤ 2·10^5` operations,
interleaved: "set `a[k] = u`" and "print the minimum of `a[l..r]`". A sparse table cannot
absorb an update (one change touches about `n` entries), and a Fenwick tree answers a range
as a difference of two prefixes, which a minimum does not allow.

So we want stored blocks that can be **combined** into any range, without ever
subtracting, and such that every position lies in only a few blocks.
"""),
            Reflect(r"""
Store the minimum of every block of a **binary split** of the array: the whole array, its
two halves, their halves, and so on down to single elements. How many blocks is that in
total? And what does "set `a[k] = u`" have to recompute?
""", answer=r"""
`n` single elements plus `n − 1` larger blocks (each split creates one), `2n − 1` in all.
Position `k` lies in exactly one block per level: its leaf and the blocks above it, about
`log2 n + 1 = 19` of them. Set the leaf, then recompute each ancestor as the minimum of its
two children, bottom-up. That structure is a **segment tree**, and an update is O(log n).
"""),
            Numeric(r"""
With `n = 8` (positions 1..8), the query `[2, 7]` is a union of whole blocks of the tree.
What is the smallest number of blocks that make it up?
""", answer=4,
                hint="Draw the blocks: `[1..8]`, `[1..4]`, `[5..8]`, `[1..2]`, `[3..4]`, ... Use the biggest ones that fit inside `[2, 7]`.",
                explain=r"""
`[2]`, `[3..4]`, `[5..6]`, `[7]`: four blocks, so the answer is the minimum of four stored
values. In general a range needs at most two blocks per level.
"""),
            MCQ(r"""
The query recursion looks at a node: if its block is inside `[l, r]` it returns the stored
value; if the block is disjoint from `[l, r]` it returns nothing; otherwise it recurses into
both children. Why does it visit only O(log n) nodes?
""", [
                Opt("Because the tree has depth log2 n.",
                    why="Depth bounds one root-to-leaf path. A recursion that went into both children "
                        "everywhere would still visit all `2n − 1` nodes of a tree of depth log2 n."),
                Opt("Because fully covered nodes stop the recursion.",
                    why="They do, but that alone does not bound anything; the question is how many "
                        "nodes can be *partially* covered and recurse further."),
                Opt("On each level at most two blocks are partially covered, the ones that straddle an "
                    "end of `[l, r]`; only they recurse, so each level sees at most 4 nodes.",
                    correct=True,
                    why="Right. A partially covered block must contain `l − 1` and `l`, or `r` and `r + 1`. "
                        "Blocks on one level are disjoint, so at most two do. About `4 · 18 = 72` visits "
                        "per query."),
            ]),
            Say(r"""
The recursive version. Node 1 covers `[1, n]`; node `v` covering `[l, r]` has children `2v`
covering `[l, m]` and `2v + 1` covering `[m + 1, r]`, with `m = (l + r) / 2`.

```cpp
vector<int> t(4 * n);                     // t[v] = min of node v's block

void update(int v, int l, int r, int pos, int val) {
    if (l == r) { t[v] = val; return; }
    int m = (l + r) / 2;
    if (pos <= m) update(2 * v, l, m, pos, val);
    else update(2 * v + 1, m + 1, r, pos, val);
    t[v] = min(t[2 * v], t[2 * v + 1]);
}

int query(int v, int l, int r, int ql, int qr) {
    if (qr < l || r < ql) return INT_MAX;          // disjoint
    if (ql <= l && r <= qr) return t[v];           // inside
    int m = (l + r) / 2;
    return min(query(2 * v, l, m, ql, qr), query(2 * v + 1, m + 1, r, ql, qr));
}
// build: the same recursion, filling leaves from the array
```
"""),
            MCQ(r"""
The tree has `2n − 1` nodes, yet the array is `4n` long. Why?
""", [
                Opt("A safety margin that is never actually used.",
                    why="It is used: for `n = 6` the leaf for position 5 is node 13, past `2n = 12`."),
                Opt("With children at `2v` and `2v + 1`, the numbering leaves gaps when `n` is not a "
                    "power of two; indices can pass `2n`, but always stay below `4n`.", correct=True,
                    why="Right. The last level is only partly filled, and its nodes keep the indices they "
                        "would have in a full tree. `2n` is enough only when `n` is a power of two."),
                Opt("Every node stores two values.",
                    why="Each node here stores one minimum; the size is about the index range."),
            ]),
            MCQ(r"""
The code returns `INT_MAX` for a disjoint node, because `min(x, INT_MAX) = x`. You now build
the same tree for range **gcd** queries. What should a disjoint node return?
""", [
                Opt("1", why="`gcd(1, x) = 1`: every query touching a disjoint node would answer 1."),
                Opt("`INT_MAX`",
                    why="`gcd(INT_MAX, x)` is not `x` in general: `gcd(2147483647, 6) = 1`."),
                Opt("0", correct=True,
                    why="Yes: `gcd(0, x) = x`, so 0 is the identity of gcd. Every combine needs its "
                        "identity here: `INT_MAX` for min, `INT_MIN` for max, 0 for sums and for gcd."),
                Opt("`a[l]`, the first element of the node.",
                    why="That element is outside the query range, and its divisors would leak into the "
                        "answer."),
            ], explain=r"""
If an operation has no convenient identity, avoid needing one: recurse only into the
children that overlap the query, as the maximum-subarray tree later in this lesson does.
"""),
            Try("dynamic_rmq", note="Recursive or bottom-up; `4n` nodes for the recursive layout."),
        ]),
        Part("Bottom-up, without recursion", [
            Say(r"""
A shorter, and usually faster, layout for operations like `min`, `max` and `+`: put leaf
`i` (0-indexed) at `t[n + i]`, and every internal node `v` at `t[v] = min(t[2v], t[2v + 1])`
for `v = n − 1` down to 1. Only `2n` entries.

```cpp
void update(int p, int val) {                  // a[p] = val
    for (t[p += n] = val; p > 1; p >>= 1) t[p >> 1] = min(t[p], t[p ^ 1]);
}
int query(int l, int r) {                      // min of a[l..r-1], half-open
    int res = INT_MAX;
    for (l += n, r += n; l < r; l >>= 1, r >>= 1) {
        if (l & 1) res = min(res, t[l++]);
        if (r & 1) res = min(res, t[--r]);
    }
    return res;
}
```
"""),
            MCQ(r"""
In `query`, why is `t[l]` taken on its own, and `l` moved right, exactly when `l` is odd?
""", [
                Opt("Odd indices are leaves.",
                    why="Leaves are `n..2n−1`, of both parities. Parity says which child a node is."),
                Opt("An odd `l` is a right child: its parent also covers the node to its left, which is "
                    "outside the range. So `t[l]` is used alone and the range continues after it.",
                    correct=True,
                    why="Right. An even `l` is a left child whose parent lies entirely inside the range, "
                        "so the loop moves up and uses the parent instead. `r` mirrors this at the other end."),
                Opt("It is only an optimisation; without it the answer is the same.",
                    why="Without it, the loop would move up to a parent that includes an element outside "
                        "the range."),
            ]),
            Short(r"""
Trace `query(1, 7)` with `n = 8` (positions 1..6). Which nodes `t[...]` are combined, in
the order the loop takes them?
""", accept=["9 14 5 6", "9, 14, 5, 6"], placeholder="node indices",
                hint="Start with `l = 9`, `r = 15`. Check `l & 1`, then `r & 1`, then halve both.",
                explain=r"""
`l = 9` is odd: take `t[9]` (position 1), `l = 10`. `r = 15` is odd: take `t[14]` (position
6), `r = 14`. Halve: `l = 5`, `r = 7`. `l` odd: take `t[5]` (positions 2..3), `l = 6`; `r`
odd: take `t[6]` (positions 4..5), `r = 6`. Halve: `l = r = 3`, stop. Four nodes, covering
1..6 exactly.
"""),
        ]),
        Part("What a node stores", [
            Say(r"""
The segment tree works for any **associative** combine: the node's value only has to be
computable from its two children. Choosing what a node stores is the real design work.

Problem: an array of profits `a_i` (possibly negative) with point updates, and queries
"the largest total of a **non-empty** stretch of consecutive elements inside `[l, r]`".
`n, q ≤ 2·10^5`. Kadane's algorithm per query is O(n): 4·10^10 in the worst case, about 16
seconds on this judge.
"""),
            Reflect(r"""
Suppose each node stored only `best`, the best stretch inside its block. A parent knows its
left child's `best` and its right child's `best`. What is missing to compute the parent's
`best`? And which extra numbers must every node keep so that the parent can compute *its
own* extras too?
""", answer=r"""
The best stretch of the parent may cross the middle, and the best crossing stretch is the
best suffix of the left block plus the best prefix of the right block. So each node also
keeps `suf` and `pref`. To compute the parent's `pref` you need to know whether taking all
of the left block and continuing into the right pays off, so each node also keeps its
total `sum`. With `(sum, pref, suf, best)` the parent's four numbers come from the
children's four: the summary is closed under merging.
"""),
            Short(r"""
The parent's best prefix either stays inside the left child, or takes the whole left child
and continues into the right one. Fill in: `pref = max(L.pref, ____)`
""", accept=["L.sum + R.pref", "L.sum+R.pref", "R.pref + L.sum", "R.pref+L.sum"],
                placeholder="an expression",
                explain=r"""
`L.sum + R.pref`. Symmetrically `suf = max(R.suf, R.sum + L.suf)`, and
`best = max(L.best, R.best, L.suf + R.pref)`, `sum = L.sum + R.sum`.
"""),
            Numeric(r"""
Left block `[2, −5, 3]` has `sum = 0, pref = 2, suf = 3, best = 3`. Right block `[4, −1, 2]` has
`sum = 5, pref = 5, suf = 5, best = 5`. What is `best` of the merged block?
""", answer=8,
                explain=r"""
`max(3, 5, L.suf + R.pref) = max(3, 5, 3 + 5) = 8`: the stretch `3, 4, −1, 2`, which crosses
the middle. The merged `pref` is `max(2, 0 + 5) = 5` and `suf` is `max(5, 5 + 3) = 8`.
"""),
            MCQ(r"""
The recursive query needs a value to return for a node disjoint from the range (an empty
block). Which one is safe?
""", [
                Opt("`sum = pref = suf = best = 0`.",
                    why="Then an empty stretch sneaks in: an all-negative range like `[−4, −2, −7]` "
                        "answers 0 instead of −2."),
                Opt("`sum = 0`, `pref = suf = best = LLONG_MIN`.",
                    why="The merge adds these: `L.suf + R.pref` with two `LLONG_MIN`s overflows, which is "
                        "undefined behaviour and in practice wraps to a huge positive number."),
                Opt("`sum = 0`, `pref = suf = best = −10^18`.", correct=True,
                    why="Yes: below every real answer (at least −10^9), and adding two of them or a sum of "
                        "size 2·10^14 stays inside `long long`. Or avoid the empty node entirely by only "
                        "recursing into halves that overlap the range."),
            ]),
            MCQ(r"""
In the bottom-up query, pieces near `l` are found left to right and pieces near `r` right
to left. For `min` they all went into one `res`. What changes with this merge?
""", [
                Opt("Nothing: the merge is associative.",
                    why="Associative is not commutative. `merge(L, R)` takes its prefix from `L`; swapping "
                        "the arguments describes a different array."),
                Opt("Keep two accumulators, `resl = merge(resl, t[l++])` and "
                    "`resr = merge(t[--r], resr)`, and answer `merge(resl, resr)`.", correct=True,
                    why="Right: each side keeps the pieces in array order, and the two sides meet in the "
                        "middle. The recursive query gets this for free, since it combines left child "
                        "before right child."),
                Opt("Sort the collected pieces by position first.",
                    why="That would work but needs storage and a sort; two accumulators do it in place."),
            ]),
            Try("max_subarray_queries", note="Four numbers per node, merged in order. The answer can be "
                "negative."),
        ]),
        Part("Walking down the tree", [
            Say(r"""
**Hotel Queries**: `n ≤ 2·10^5` hotels in a row, hotel `i` with `h_i` free rooms. `m ≤ 2·10^5`
groups arrive one by one; a group of `r` people takes the **leftmost** hotel with at least
`r` free rooms (print it, or 0 if none), and those rooms are gone.
"""),
            Numeric(r"""
The direct approach scans from hotel 1 for every group. How many steps in the worst case,
with `n = m = 2·10^5`?
""", answer=4e10, rel=0.5, unit="steps",
                explain=r"""
`n · m = 4·10^10`, reached when many small hotels come first and the group has to pass all
of them every time. The hidden tests do exactly that; the scan takes about 10.6 seconds.
"""),
            Reflect(r"""
Keep a segment tree of **maximum** free rooms. The root tells you whether any hotel fits.
How do you find the leftmost hotel with at least `r` rooms in a single walk from the root
to a leaf?
""", answer=r"""
If the root's maximum is below `r`, answer 0. Otherwise, at each node: if the left child's
maximum is at least `r`, some hotel in the left half fits, and it is further left than
anything in the right half, so go left; otherwise the fit must be in the right half, so go
right. The invariant is "the leftmost fitting hotel is inside the current block". At the
leaf, subtract `r`, and recompute the maxima on the way back up. O(log n) per group.
"""),
            MCQ(r"""
Why not keep the capacities in a `multiset` and use `lower_bound(r)`?
""", [
                Opt("It finds the hotel with the fewest rooms that still fits, not the leftmost one.",
                    correct=True,
                    why="Right. A multiset orders by capacity, and the problem orders by position. "
                        "(It would be the right tool for 'best fit'.)"),
                Opt("It is too slow: O(n) per `lower_bound`.",
                    why="The member `ms.lower_bound(r)` is O(log n). Speed is not the issue; the order is."),
                Opt("It is equivalent and fine.",
                    why="With hotels `[5, 3]` and a group of 3, it picks hotel 2; the rule says hotel 1."),
            ], explain=r"""
Searching a segment tree by descending is a pattern of its own: "the first position where a
prefix sum reaches k", "the k-th one in a 0/1 array", "the first element ≥ x after position
p". Each is one walk guided by the children's summaries, O(log n) instead of an
O(log^2 n) binary search over queries.
"""),
            Short(r"""
Hotels `[3, 2, 4, 1, 5, 5, 2, 6]`, groups `4 4 7 1 1`. Which hotel does each group get?
""", accept=["3 5 0 1 1", "3, 5, 0, 1, 1"], placeholder="five numbers",
                explain=r"""
4 → hotel 3 (4 rooms, now 0). 4 → hotel 5 (5, now 1). 7 → nobody: 0. 1 → hotel 1 (3, now
2). 1 → hotel 1 again (now 1). `3 5 0 1 1`.
"""),
            Try("hotel_queries", note="A max tree and one walk down per group."),
        ]),
        Part("Lazy propagation", [
            Say(r"""
Now updates cover ranges. **Range Updates and Sums**: `n, q ≤ 2·10^5`, operations "add `x` to
`a[l..r]`", "set `a[l..r]` to `x`", and "print the sum of `a[l..r]`".
"""),
            MCQ(r"""
What about doing a range update as `r − l + 1` point updates on a sum segment tree?
""", [
                Opt("Fine: each point update is only O(log n).",
                    why="`r − l + 1` of them per operation: up to 2·10^5 · 18 = 3.6·10^6 steps per update, "
                        "and 2·10^5 updates."),
                Opt("Worse than a plain array: O(n log n) per update, against O(n) for a loop.",
                    correct=True,
                    why="Right. A range update must touch O(log n) nodes, like a query, and not the "
                        "elements themselves."),
                Opt("Fine as long as the ranges are short.",
                    why="The tests use ranges spanning the whole array."),
            ]),
            Reflect(r"""
"Add `x` to `[l, r]`" splits into O(log n) fully covered nodes, like a query. For a fully
covered node, what can you update immediately, and what can you postpone? When must the
postponed work finally be done, and why is postponing safe?
""", answer=r"""
The node's own sum can be fixed immediately: `sum += x · length`. Its descendants changed
too, but nobody looks at them yet, so leave a pending **tag** "add `x`" on the node instead
of visiting them. The tag must be **pushed** (applied to the two children, and merged into
their tags) whenever a later operation is about to descend below the node. It is safe
because every access to a descendant passes through this node first, and we push before
descending, so no stale value is ever read. This is **lazy propagation**.
"""),
            Numeric(r"""
With `n = 8`, how many nodes does "add 3 to `[1, 8]`" modify under lazy propagation?
""", answer=1, unit="nodes",
                explain=r"""
One: the root covers the whole range, so it gets `sum += 3 · 8` and the tag "add 3", and the
update stops there. Its children learn about it only if some later operation needs to go
below the root.
"""),
            Say(r"""
Here there are two kinds of updates. A node can collect several of them before anyone
descends below it, so its tag has to summarise *any sequence* of adds and assignments as a
single pending operation. Try composing two.
"""),
            MCQ(r"""
A node's pending tag is "add 5". Now "set to 2" arrives for the whole node. What is the new
tag?
""", [
                Opt("Set to 2, then add 5.",
                    why="The add happened *before* the assignment, and an assignment overwrites every "
                        "earlier change."),
                Opt("Set to 2.", correct=True,
                    why="Right: the pending add is discarded, because the assignment overwrites it."),
                Opt("Set to 7.",
                    why="That would be the result of an add arriving *after* the assignment."),
            ]),
            Short(r"""
The other order: a node's pending tag is "set to 2", and now "add 5" arrives. Which single
tag is equivalent?
""", accept=["set 7", "set to 7", "assign 7", "=7", "set 7, add 0", "set to 7 then add 0",
             "set 2 then add 5", "set 2, add 5", "set to 2 then add 5", "set to 2, then add 5"],
                placeholder="e.g. set 3",
                explain=r"""
"Set 7", or equivalently "set 2, then add 5". Either way every element of the block ends at
7, and the two updates collapsed into one pending operation. Tags that compose like this
are what make lazy propagation possible.
"""),
            Say(r"""
So the tag shape that covers every sequence is **"set to `s` (if an assignment is pending),
then add `a`"**: an add `x` turns `(s, a)` into `(s, a + x)`, an assignment `x` turns it
into `(x, 0)`. Applying a tag to a node of length `len`, and pushing:

```cpp
void apply(int v, long long len, long long s, long long a) {
    if (s != 0) { sum[v] = s * len; setv[v] = s; addv[v] = 0; }   // values are >= 1,
    if (a != 0) { sum[v] += a * len; addv[v] += a; }              // so s = 0 means "none"
}
void push(int v, int l, int r) {
    int m = (l + r) / 2;
    apply(2 * v, m - l + 1, setv[v], addv[v]);
    apply(2 * v + 1, r - m, setv[v], addv[v]);
    setv[v] = addv[v] = 0;
}
```

`update` and `query` call `push(v, l, r)` before recursing into the children of a partly
covered node, and `update` recomputes `sum[v]` from the children afterwards.
"""),
            Numeric(r"""
A node covering 4 elements has sum 10. It receives "set to 3", then "add 1". What is its sum?
""", answer=16,
                explain=r"""
`3 · 4 = 12` after the assignment, `+ 1 · 4` after the addition: 16. Its children are not
touched: the node keeps the tag `(set 3, add 1)` until some operation descends below it.
"""),
            MCQ(r"""
You declared `int x, len` and wrote `sum[v] += x * len;` with `sum` a `long long` array. What
happens with `x = 10^6` on a node of length 2·10^5?
""", [
                Opt("Nothing: `sum` is `long long`, so the product is computed in 64 bits.",
                    why="The product of two `int`s is computed in `int` before it is added (cpp02). "
                        "2·10^11 does not fit."),
                Opt("`x * len` overflows `int` and the sum is garbage.", correct=True,
                    why="Right: 2·10^11 > 2.1·10^9. Make `x` (or `len`) `long long`, as in `apply` above."),
                Opt("A compile error.",
                    why="It compiles silently; the overflow happens at run time."),
            ]),
            Try("range_updates_sums", note="Tag = (set, add), push before descending, everything in "
                "`long long`."),
        ]),
        Part("When lazy propagation works", [
            Reflect(r"""
Lazy propagation worked for "add" and "set" with "sum". State the two properties a tag must
have, so you can decide for a new problem whether it will work.
""", answer=r"""
First, a node's stored summary must be updatable from the tag alone, using only the
summary and the node's size, without looking at its children (a sum grows by `x · len`; a
maximum grows by `x`). Second, two tags must compose into one tag of the same shape (add
then add is an add; set then add is a set; add then set is a set), so a node never has to
remember an unbounded list of pending operations.
"""),
            MCQ(r"""
Which combination can a lazy segment tree handle in O(log n) per operation?
""", [
                Opt("Range add, range count of distinct values.",
                    why="Adding `x` to a block keeps its distinct count, but a node cannot combine its "
                        "children's counts: values shared by both halves would be counted twice. The "
                        "summary is not mergeable, lazy or not (that is a Mo's algorithm problem, algo24)."),
                Opt("Range add, range maximum.", correct=True,
                    why="Yes: the maximum of a block grows by exactly `x`, and adds compose. The same tree "
                        "with `sum` replaced by `max` and `x · len` by `x`."),
                Opt("Range `a_i = a_i mod x`, range sum.",
                    why="The new sum depends on every element's value, not on the old sum: the tag cannot "
                        "update the summary."),
            ], explain=r"""
Range assignment with the maximum-subarray summary of the previous part also works: a
block set to `x` has `sum = x · len` and `pref = suf = best = max(x, x · len)`.
"""),
        ]),
    ],
    problems=[DYNAMIC_RMQ, MAX_SUBARRAY, HOTEL_QUERIES, RANGE_UPDATES_SUMS],
    cards=[
        Card(r"""Segment tree node numbering (recursive layout)?""",
             r"""Root 1 covers `[1, n]`; node `v` covering `[l, r]` has children `2v` → `[l, m]` and `2v+1` → `[m+1, r]`, `m = (l+r)/2`. Allocate `4n`."""),
        Card(r"""Why is a segment tree query O(log n)?""",
             r"""Only blocks straddling an end of the range are partially covered: at most 2 per level, so at most 4 nodes visited per level."""),
        Card(r"""What does a segment-tree query return for a disjoint node?""",
             r"""The identity of the combine: `INT_MAX` for min, `INT_MIN` for max, 0 for sums. Or avoid it by recursing only into overlapping halves."""),
        Card(r"""Bottom-up segment tree query loop for `[l, r)`?""",
             r"""`for (l += n, r += n; l < r; l >>= 1, r >>= 1) { if (l&1) res = f(res, t[l++]); if (r&1) res = f(res, t[--r]); }`"""),
        Card(r"""Node summary for maximum subarray sum, and its merge?""",
             r"""`(sum, pref, suf, best)`: `sum = L.sum+R.sum`, `pref = max(L.pref, L.sum+R.pref)`, `suf = max(R.suf, R.sum+L.suf)`, `best = max(L.best, R.best, L.suf+R.pref)`."""),
        Card(r"""Non-commutative merge in the bottom-up query?""",
             r"""Keep `resl = merge(resl, t[l++])` and `resr = merge(t[--r], resr)`; answer `merge(resl, resr)`."""),
        Card(r"""Find the leftmost position with value ≥ r in a max segment tree?""",
             r"""If the root's max < r: none. Else walk down: go left if the left child's max ≥ r, otherwise right. O(log n)."""),
        Card(r"""Lazy propagation in one sentence?""",
             r"""For a fully covered node, update its summary now and store a tag for its subtree; push the tag to the children just before any operation descends below it."""),
        Card(r"""Tag for range add + range assign, and how tags compose?""",
             r"""`(set s or none, then add a)`. An add `x` gives `(s, a + x)`; an assignment `x` gives `(x, 0)`."""),
        Card(r"""When can lazy propagation handle an update/query pair?""",
             r"""The summary can be updated from the tag and the node size alone, and tags compose into a tag of the same shape."""),
        Card(r"""The overflow trap in `sum += x * len`?""",
             r"""With `int x, len` the product is computed in `int` (2·10^11 overflows). Make one factor `long long`."""),
    ],
)
