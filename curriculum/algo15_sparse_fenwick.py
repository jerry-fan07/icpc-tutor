from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _range(rng, n, wide):
    if wide:                                   # nearly the whole array, every time
        return rng.randint(1, min(n, 40)), rng.randint(max(1, n - 40), n)
    l = rng.randint(1, n)
    return l, rng.randint(l, n)


def _rmq(rng, n, q, lo, hi, wide=False):
    a = [rng.randint(lo, hi) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        l, r = _range(rng, n, wide)
        if r < l:
            l, r = r, l
        out.append(f"{l} {r}")
    return "\n".join(out) + "\n"


def _dyn_sum(rng, n, q, vmax, wide=False):
    a = [rng.randint(1, vmax) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        if rng.random() < 0.5:
            out.append(f"1 {rng.randint(1, n)} {rng.randint(1, vmax)}")
        else:
            l, r = _range(rng, n, wide)
            if r < l:
                l, r = r, l
            out.append(f"2 {l} {r}")
    return "\n".join(out) + "\n"


def _range_upd(rng, n, q, vmax, wide=False):
    a = [rng.randint(1, vmax) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        if rng.random() < 0.5:
            l, r = _range(rng, n, wide)
            if r < l:
                l, r = r, l
            out.append(f"1 {l} {r} {rng.randint(-vmax, vmax)}")
        else:
            out.append(f"2 {rng.randint(1, n)}")
    return "\n".join(out) + "\n"


def _inv(rng, n, lo, hi, order=None):
    a = [rng.randint(lo, hi) for _ in range(n)]
    if order == "desc":
        a.sort(reverse=True)
    return f"{n}\n" + " ".join(map(str, a)) + "\n"


# --------------------------------------------------------------------- problems
STATIC_RMQ = Problem(
    id="static_rmq",
    title="Static Range Minimum",
    difficulty="easy",
    source="CSES 1647 - Static Range Minimum Queries",
    complexity="O(n log n + q)",
    statement=r"""
A weather station stored `n` daily temperatures. Answer `q` questions: what was the lowest
temperature from day `l` to day `r`, inclusive? The data never changes.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has `n` integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

Each of the next `q` lines has two integers `l r` (1 ≤ l ≤ r ≤ n).
""",
    output=r"""
For each question print min(a_l, ..., a_r).
""",
    samples=[
        Test("8 4\n5 2 7 1 4 6 3 8\n2 7\n5 7\n1 1\n6 8\n", "1\n3\n5\n3\n"),
    ],
    tests=[
        Test("1 1\n1000000000\n1 1\n"),
        Test("5 5\n4 4 4 4 4\n1 5\n2 3\n5 5\n1 1\n3 5\n"),
        Test("6 4\n6 5 4 3 2 1\n1 6\n1 5\n2 4\n6 6\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _rmq(rng, rng.randint(1, 12), rng.randint(1, 12), 1, 20), 14),
        Gen("medium random", lambda rng: _rmq(rng, 5000, 5000, 1, 10**9), 2),
        Gen("max size, whole-array queries", lambda rng: _rmq(rng, 200000, 200000, 1, 10**9, True), 1, large=True),
        Gen("max size, random queries", lambda rng: _rmq(rng, 200000, 200000, 1, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    int K = 32 - __builtin_clz(n);                  // levels 0..K-1, 2^(K-1) <= n
    // st[j][i] = min of a[i .. i + 2^j - 1]
    vector<vector<int>> st(K, vector<int>(n + 1));
    for (int i = 1; i <= n; i++) cin >> st[0][i];
    for (int j = 1; j < K; j++)
        for (int i = 1; i + (1 << j) - 1 <= n; i++)
            st[j][i] = min(st[j - 1][i], st[j - 1][i + (1 << (j - 1))]);
    while (q--) {
        int l, r;
        cin >> l >> r;
        int k = 31 - __builtin_clz(r - l + 1);      // largest k with 2^k <= length
        // two blocks of length 2^k: one starts at l, one ends at r; overlap is harmless
        cout << min(st[k][l], st[k][r - (1 << k) + 1]) << '\n';
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
        int l, r;
        cin >> l >> r;
        cout << *min_element(a.begin() + l, a.begin() + r + 1) << '\n';
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
        int l, r;
        cin >> l >> r;
        int m = INT_MAX;
        for (int i = l; i <= r; i++) m = min(m, a[i]);
        cout << m << '\n';
    }
}
""",
    hints=[
        r"""Precompute the minimum of every block whose length is a power of two, starting at every
index: `st[j][i] = min(a[i..i+2^j−1])`, built from two blocks of level `j − 1`.""",
        r"""A query `[l, r]` of length `len` is covered by two blocks of length `2^k`, where `2^k` is
the largest power of two ≤ `len`: one starting at `l`, one ending at `r`. They may
overlap; for a minimum that does not matter.""",
    ],
    editorial=r"""
Sparse table. `st[0][i] = a[i]` and `st[j][i] = min(st[j−1][i], st[j−1][i + 2^(j−1)])`:
the minimum of the block of length `2^j` starting at `i`. About `n log n = 3.6·10^6`
entries, built in that time.

For `[l, r]`, let `k = ⌊log2(r − l + 1)⌋`. The blocks `[l, l + 2^k − 1]` and
`[r − 2^k + 1, r]` together cover exactly `[l, r]` (each is at least half of it), so the
answer is the smaller of their two minimums. They usually overlap, which is fine because
`min(x, x) = x`: an operation with that property is called idempotent. O(1) per query.

`⌊log2 x⌋` for an `int` is `31 − __builtin_clz(x)` (or GCC's `__lg(x)`, or a precomputed
table); avoid floating-point `log2` in the inner loop.
""",
)

DYNAMIC_RANGE_SUM = Problem(
    id="dynamic_range_sum",
    title="Dynamic Range Sums",
    difficulty="easy",
    source="CSES 1648 - Dynamic Range Sum Queries",
    complexity="O((n + q) log n)",
    statement=r"""
An array of `n` integers is given. Process `q` operations of two kinds, in order:

- `1 k u`: set a_k to `u`;
- `2 a b`: print a_a + a_(a+1) + ... + a_b.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

Each of the next `q` lines is an operation `1 k u` (1 ≤ k ≤ n, 1 ≤ u ≤ 10^9) or `2 a b`
(1 ≤ a ≤ b ≤ n).
""",
    output=r"""
For each operation of the second kind, print the sum on its own line.
""",
    samples=[
        Test("8 4\n3 2 4 5 1 1 5 3\n2 1 4\n2 5 6\n1 3 1\n2 1 4\n", "14\n2\n11\n"),
        Test("3 3\n5 5 5\n1 2 7\n1 2 7\n2 1 3\n", "17\n",
             note="Setting the same value twice must not add it twice."),
    ],
    tests=[
        Test("1 3\n7\n2 1 1\n1 1 1000000000\n2 1 1\n"),
        Test("4 2\n1000000000 1000000000 1000000000 1000000000\n2 1 4\n2 2 3\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _dyn_sum(rng, rng.randint(1, 12), rng.randint(1, 14), 20), 14),
        Gen("medium, big values", lambda rng: _dyn_sum(rng, 5000, 5000, 10**9), 2),
        Gen("max size, whole-array sums", lambda rng: _dyn_sum(rng, 200000, 200000, 10**9, True), 1, large=True),
        Gen("max size, random", lambda rng: _dyn_sum(rng, 200000, 200000, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<long long> t;                      // Fenwick tree, 1-indexed

void add(int i, long long v) {            // a[i] += v
    for (; i <= n; i += i & -i) t[i] += v;
}
long long prefix(int i) {                 // a[1] + ... + a[i]
    long long s = 0;
    for (; i > 0; i -= i & -i) s += t[i];
    return s;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> n >> q;
    t.assign(n + 1, 0);
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        add(i, a[i]);
    }
    while (q--) {
        int type, x, y;
        cin >> type >> x >> y;
        if (type == 1) {
            add(x, y - a[x]);             // a Fenwick tree adds; setting is adding the difference
            a[x] = y;
        } else {
            cout << prefix(y) - prefix(x - 1) << '\n';
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
        int type, x, y;
        cin >> type >> x >> y;
        if (type == 1) a[x] = y;
        else {
            long long s = 0;
            for (int i = x; i <= y; i++) s += a[i];
            cout << s << '\n';
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
        int type, x, y;
        cin >> type >> x >> y;
        if (type == 1) a[x] = y;
        else {
            long long s = 0;
            for (int i = x; i <= y; i++) s += a[i];
            cout << s << '\n';
        }
    }
}
""",
    hints=[
        r"""A plain array makes sums O(n); a prefix-sum array makes updates O(n). Store blocks of
power-of-two lengths instead: index `i` holds the sum of the `i & -i` elements ending at `i`.""",
        r"""`prefix(i)`: add `t[i]`, then `i -= i & -i`, until 0. `add(i, v)`: `t[i] += v`, then
`i += i & -i`, while `i ≤ n`. A range sum is `prefix(b) − prefix(a − 1)`.""",
        r"""The operation *sets* `a[k] = u`. The tree can only add: add `u − a[k]` and remember the
new `a[k]`. Sums reach 2·10^14: `long long`.""",
    ],
    editorial=r"""
Fenwick tree (binary indexed tree). `t[i]` holds the sum of `a` over the block of length
`i & -i` (the lowest set bit of `i`) that ends at `i`. A prefix `[1..i]` is the union of
the blocks ending at `i`, `i − lowbit(i)`, ...: clear the lowest bit until 0, at most
log2 n + 1 steps. The blocks containing position `i` are at `i`, `i + lowbit(i)`, ...:
add the lowest bit until past `n`. Both O(log n).

A range sum is `prefix(b) − prefix(a − 1)`, which needs subtraction: Fenwick trees answer
range queries only for invertible operations.

Traps: the update *sets* a value, so add the difference and keep a copy of the array
(the second sample sets the same value twice); sums reach 2·10^14, so `long long`; and
the tree is 1-indexed, because `0 & -0 = 0` makes `add(0, v)` loop forever.
""",
)

RANGE_UPDATE_QUERIES = Problem(
    id="range_update_queries",
    title="Range Update Queries",
    difficulty="medium",
    source="CSES 1651 - Range Update Queries",
    complexity="O((n + q) log n)",
    statement=r"""
An array of `n` integers is given. Process `q` operations of two kinds, in order:

- `1 a b u`: add `u` to every a_i with a ≤ i ≤ b;
- `2 k`: print the current value of a_k.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

Each of the next `q` lines is `1 a b u` (1 ≤ a ≤ b ≤ n, −10^9 ≤ u ≤ 10^9) or `2 k`
(1 ≤ k ≤ n).
""",
    output=r"""
For each operation of the second kind, print the value on its own line.
""",
    samples=[
        Test("5 5\n3 2 4 5 1\n1 2 4 3\n1 1 3 -1\n2 3\n2 5\n2 4\n", "6\n1\n8\n"),
    ],
    tests=[
        Test("1 3\n5\n1 1 1 1000000000\n1 1 1 1000000000\n2 1\n"),
        Test("3 4\n1 1 1\n1 1 3 -1000000000\n2 3\n1 3 3 7\n2 3\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _range_upd(rng, rng.randint(1, 12), rng.randint(1, 14), 20), 14),
        Gen("medium, big values", lambda rng: _range_upd(rng, 5000, 5000, 10**9), 2),
        Gen("max size, whole-array updates", lambda rng: _range_upd(rng, 200000, 200000, 10**9, True), 1, large=True),
        Gen("max size, random", lambda rng: _range_upd(rng, 200000, 200000, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<long long> t;                      // Fenwick tree over the difference array d

void add(int i, long long v) {
    for (; i <= n; i += i & -i) t[i] += v;    // i = n + 1 simply does nothing
}
long long prefix(int i) {
    long long s = 0;
    for (; i > 0; i -= i & -i) s += t[i];
    return s;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> n >> q;
    t.assign(n + 1, 0);
    vector<long long> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int type;
        cin >> type;
        if (type == 1) {
            int l, r;
            long long u;
            cin >> l >> r >> u;
            add(l, u);                    // d[l] += u
            add(r + 1, -u);               // d[r+1] -= u
        } else {
            int k;
            cin >> k;
            cout << a[k] + prefix(k) << '\n';   // original value + everything added so far
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
        int type;
        cin >> type;
        if (type == 1) {
            int l, r; long long u;
            cin >> l >> r >> u;
            for (int i = l; i <= r; i++) a[i] += u;
        } else {
            int k;
            cin >> k;
            cout << a[k] << '\n';
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
        int type;
        cin >> type;
        if (type == 1) {
            int l, r; long long u;
            cin >> l >> r >> u;
            for (int i = l; i <= r; i++) a[i] += u;
        } else {
            int k;
            cin >> k;
            cout << a[k] << '\n';
        }
    }
}
""",
    hints=[
        r"""algo01's difference array turns a range update into two point updates, and a value into a
prefix sum of differences. What was missing there was answering *between* updates.""",
        r"""Keep the differences in a Fenwick tree: `add(a, u)`, `add(b + 1, −u)`, and the value at
`k` is the original `a[k]` plus `prefix(k)`.""",
    ],
    editorial=r"""
Difference array plus Fenwick tree. Adding `u` to `a[l..r]` changes only two differences:
`d[l] += u` and `d[r+1] −= u`. The value at `k` is the original `a[k]` plus
`d[1] + ... + d[k]`. A Fenwick tree over `d` does both in O(log n), so updates and
questions can interleave (online), which the plain difference array of algo01 could not.

When `r = n`, `add(n + 1, −u)` runs zero iterations of `i <= n`: correct, since no position
after `n` exists. Values reach about 2·10^14 in absolute value: `long long`.
""",
)

INVERSIONS = Problem(
    id="inversions",
    title="Counting Inversions",
    difficulty="medium",
    source="Classic (SPOJ INVCNT)",
    complexity="O(n log n)",
    statement=r"""
Given an array of `n` integers, count the pairs of positions `i < j` with a_i > a_j (the
number of inversions: how far the array is from sorted).
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^9). Values may repeat.
""",
    output=r"""
Print the number of inversions.
""",
    samples=[
        Test("5\n3 1 2 5 4\n", "3\n"),
        Test("4\n2 2 1 2\n", "2\n", note="Equal values are not an inversion."),
    ],
    tests=[
        Test("1\n1000000000\n"),
        Test("5\n7 7 7 7 7\n"),
        Test("6\n6 5 4 3 2 1\n"),
        Test("3\n1000000000 1 1000000000\n"),
    ],
    gens=[
        Gen("small, many repeats", lambda rng: _inv(rng, rng.randint(1, 12), 1, 5), 12),
        Gen("small, wide values", lambda rng: _inv(rng, rng.randint(1, 12), 1, 10**9), 6),
        Gen("medium random", lambda rng: _inv(rng, 5000, 1, 10**9), 2),
        Gen("max size, decreasing (answer about 2e10)", lambda rng: _inv(rng, 200000, 1, 10**9, "desc"), 1, large=True),
        Gen("max size, random", lambda rng: _inv(rng, 200000, 1, 10**9), 1, large=True),
        Gen("max size, few distinct", lambda rng: _inv(rng, 200000, 1, 100), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    // coordinate compression: value -> rank in 1..m
    vector<int> vals(a);
    sort(vals.begin(), vals.end());
    vals.erase(unique(vals.begin(), vals.end()), vals.end());
    int m = vals.size();
    vector<int> t(m + 1, 0);                        // Fenwick tree of counts per rank
    long long inv = 0;
    for (int j = 0; j < n; j++) {
        int r = lower_bound(vals.begin(), vals.end(), a[j]) - vals.begin() + 1;
        int notGreater = 0;                         // earlier values <= a[j]
        for (int i = r; i > 0; i -= i & -i) notGreater += t[i];
        inv += j - notGreater;                      // earlier values > a[j]
        for (int i = r; i <= m; i += i & -i) t[i]++;
    }
    cout << inv << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    long long inv = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] > a[j]) inv++;
    cout << inv << '\n';
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
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    long long inv = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] > a[j]) inv++;
    cout << inv << '\n';
}
""",
    hints=[
        r"""Scan left to right. At position `j`, the new inversions are the earlier values larger than
`a[j]`: a count over a range of *values*.""",
        r"""Index a Fenwick tree by value, storing how many times each value has appeared so far. Values
go up to 10^9: compress them to ranks 1..m first.""",
        r"""Earlier values `> a[j]` = `j − (earlier values ≤ a[j])` = `j − prefix(rank(a[j]))`. The answer
reaches about 2·10^10: `long long`.""",
    ],
    editorial=r"""
Scan left to right and keep a Fenwick tree `t` indexed by value rank, where the count at
rank `r` is how many earlier elements have that rank. At position `j` (0-based, so `j`
elements came before), the earlier elements that are `≤ a[j]` number `prefix(rank(a[j]))`,
so `j − prefix(rank(a[j]))` of them are strictly greater: that many new inversions. Then
add 1 at `rank(a[j])`. O(n log n), against 2·10^10 comparisons for the double loop.

Traps: values up to 10^9 need coordinate compression (sort, `unique`, `lower_bound`); ties
are not inversions, so count "not greater" with `prefix(r)`, not `prefix(r − 1)`; and a
decreasing array has `n(n − 1)/2 ≈ 2·10^10` inversions, which needs `long long`.

(Merge sort counts inversions in O(n log n) too: when an element of the right half is
placed, every remaining element of the left half is greater.)
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo15",
    title="range queries I: sparse tables & Fenwick trees",
    track="algo",
    order=15,
    summary="Range minimum in O(1) with a sparse table (and why it needs idempotence), then the "
            "Fenwick tree derived from power-of-two blocks: point updates, range sums, range "
            "updates, and counting inversions.",
    prereqs=["algo01", "cpp10"],
    tags=["sparse table", "rmq", "idempotent", "fenwick tree", "binary indexed tree",
          "lowbit", "inversions", "coordinate compression"],
    parts=[
        Part("Range minimum on a fixed array", [
            Say(r"""
algo01 ended on a warning: prefix sums work because subtraction undoes addition, and
nothing undoes a minimum. So here is the problem prefix sums cannot solve.

An array of `n ≤ 2·10^5` values never changes. `q ≤ 2·10^5` queries each ask for the
minimum of `a[l..r]`. One second. Looping over the range is 4·10^10 steps in the worst
case (you have seen that number before); on this judge it takes about 11 seconds.
"""),
            MCQ(r"""
Which set of precomputed minimums is both affordable and enough to answer queries fast?
""", [
                Opt("The minimum of every range `[l, r]`.",
                    why="Instant answers, but n(n+1)/2 ≈ 2·10^10 ranges: the table costs more than the "
                        "brute force."),
                Opt("Prefix minimums `pmin[i] = min(a[1..i])`.",
                    why="`pmin[r]` may come from before `l`, and there is no way to remove that part. "
                        "That is the missing inverse again."),
                Opt("For every index `i` and every `j`, the minimum of the block of length `2^j` "
                    "starting at `i`.", correct=True,
                    why="Yes: about `n log n = 2·10^5 · 18 = 3.6·10^6` numbers, each built from two of "
                        "the level below. The next question is how two of them answer any range."),
                Opt("The minimum of each block of about √n elements.",
                    why="A real technique (algo24) with O(√n) queries, far better than O(n). But the "
                        "ends of the range still need element-by-element work, so not O(1)."),
            ]),
            Reflect(r"""
Take a query `[l, r]` of length `len`, and let `2^k` be the largest power of two with
`2^k ≤ len`. The block of length `2^k` starting at `l` and the block of length `2^k` ending
at `r` together cover `[l, r]` exactly, but they usually overlap. Why is the overlap
harmless for a minimum, and what would it do to a sum?
""", answer=r"""
Each block is at least half of `[l, r]`, so together they cover it and stay inside it.
Elements in the overlap are looked at twice, and `min(x, x) = x`: seeing a value twice does
not change a minimum. An operation with that property is **idempotent** (max, gcd, bitwise
AND and OR are too). For a sum, the overlap would be added twice: with
`a = [5, 2, 7, 1, 4, 6, 3, 8]` and `[2, 7]`, the two blocks of length 4 sum to 28 while the
true sum is 23; the shared `1 + 4` counted twice.
"""),
            Short(r"""
`st[j][i]` is the minimum of the block of length `2^j` starting at `i`. It is made of two
blocks of length `2^(j−1)`. Fill in:
`st[j][i] = min(st[j-1][i], st[j-1][ ____ ])`
""", accept=["i + (1 << (j - 1))", "i+(1<<(j-1))", "i + 2^(j-1)", "i+2^(j-1)",
             "i + (1 << j - 1)", "i+(1<<j-1)", "i + (1 << (j-1))"],
                placeholder="an index",
                explain=r"""
`i + (1 << (j − 1))`: the second half starts `2^(j−1)` after the first. Level 0 is the
array itself; each level is built from the previous one, and a block must fit, so `i`
runs while `i + 2^j − 1 ≤ n`.
"""),
            Short(r"""
With `a = [5, 2, 7, 1, 4, 6, 3, 8]` (1-indexed), the query `[2, 7]` has length 6, so
`k = 2` (blocks of length 4). At which indices do the two blocks start? Answer as two
numbers.
""", accept=["2 4", "2, 4", "(2, 4)"], placeholder="two indices",
                hint="One block starts at `l`; the other ends at `r`, so it starts at `r − 2^k + 1`.",
                explain=r"""
`[2..5]` and `[4..7]`, starting at 2 and `7 − 4 + 1 = 4`. Their minimums are `min(2, 7, 1, 4)`
and `min(1, 4, 6, 3)`, both 1, and the answer is 1. Positions 4 and 5 are in both blocks.
"""),
            MCQ(r"""
Which of these can a sparse table answer in O(1) per query, with the two-overlapping-blocks
trick?
""", [
                Opt("Range sum.",
                    why="The overlap would be counted twice. A sparse table can still do sums in "
                        "O(log n) by splitting the range into disjoint power-of-two blocks, but prefix "
                        "sums already do it in O(1)."),
                Opt("Range XOR.",
                    why="`x ^ x = 0`: the overlap cancels out instead of being harmless. Prefix XORs "
                        "(algo01) are the tool."),
                Opt("Range GCD.", correct=True,
                    why="Yes: `gcd(x, x) = x`, so the overlap does not matter. Any idempotent, "
                        "associative operation works: min, max, gcd, AND, OR."),
                Opt("Range product modulo a prime.",
                    why="`x · x ≠ x`. With no zeros, modular inverses give prefix products instead."),
            ]),
            Say(r"""
The code. `⌊log2 x⌋` for a positive `int` is `31 − __builtin_clz(x)` (count the leading
zero bits of the 32-bit value); GCC also offers `__lg(x)`.

```cpp
int K = 32 - __builtin_clz(n);                      // levels 0..K-1
vector<vector<int>> st(K, vector<int>(n + 1));
for (int i = 1; i <= n; i++) cin >> st[0][i];
for (int j = 1; j < K; j++)
    for (int i = 1; i + (1 << j) - 1 <= n; i++)
        st[j][i] = min(st[j - 1][i], st[j - 1][i + (1 << (j - 1))]);

// query [l, r]
int k = 31 - __builtin_clz(r - l + 1);
int answer = min(st[k][l], st[k][r - (1 << k) + 1]);
```
"""),
            Numeric(r"""
The weakness: the table cannot be updated cheaply. If one value `a[i]` in the middle of an
array of `n = 2·10^5` changes, roughly how many table entries contain position `i`?
""", answer=2e5, rel=0.5, unit="entries",
                hint="Level `j` has up to `2^j` blocks that contain a given position.",
                explain=r"""
`1 + 2 + 4 + ... ` over the levels, about `2^18`, capped by the array's edges: exactly
200,000 for the middle position here. O(n) per update. Sparse tables are for static data;
for updates, read on.
"""),
            Try("static_rmq", note="Build the table once; two lookups per query."),
        ]),
        Part("Updates and sums: the Fenwick tree", [
            Say(r"""
New problem: an array of `n ≤ 2·10^5` values and `q ≤ 2·10^5` operations, interleaved:
"set `a[k] = u`" and "print `a[l] + ... + a[r]`".

You know two structures, at opposite extremes. A plain array stores, at each index, the
block of length 1 ending there: updates O(1), sums O(n). A prefix-sum array stores the block
`[1..i]` ending at each `i`: sums O(1), but changing `a[1]` changes all `n` stored values.
Either way the worst case is about 4·10^10.

Long blocks make queries cheap and updates expensive; short blocks the reverse. The middle
ground: let each index store the sum of a block of **power-of-two length** ending at it,
with lengths chosen so that any prefix is a union of a few stored blocks.
"""),
            Reflect(r"""
Write 13 = 8 + 4 + 1 and cut the prefix `[1..13]` into consecutive blocks of those lengths,
largest first. Which blocks do you get? Now look at the index each block ends at, in binary.
What rule tells you the length of the block from its end index?
""", answer=r"""
`[1..8]`, `[9..12]`, `[13..13]`, ending at 8 = 1000, 12 = 1100 and 13 = 1101 in binary. In
each case the block's length is the **lowest set bit** of its end index: 8 has lowest bit
8, 12 has 4, 13 has 1. So let index `i` store the sum of the `lowbit(i)` elements ending at
`i`. Then every prefix `[1..r]` is the block ending at `r`, then the one ending at
`r − lowbit(r)`, and so on: one block per set bit of `r`. This is the **Fenwick tree**
(binary indexed tree).
"""),
            Short(r"""
Under this rule, which positions does `t[12]` cover? Answer as `first..last`.
""", accept=["9..12", "9-12", "9 12", "[9,12]", "[9..12]", "9 to 12", "[9, 12]", "9...12", "(9, 12)"],
                placeholder="first..last",
                explain=r"""
`12 = 1100` in binary, lowest set bit 4, so `t[12]` covers the 4 positions ending at 12:
`9..12`. Likewise `t[6]` covers `5..6`, `t[7]` just `7`, and `t[8]` and `t[16]` cover whole
prefixes `1..8` and `1..16`.
"""),
            Short(r"""
`prefix(11)` adds up the stored blocks that make up `[1..11]`. Which `t` indices does it
visit, in order?
""", accept=["11 10 8", "11, 10, 8"], placeholder="indices",
                explain=r"""
`11 = 1011`: `t[11]` covers `11`; clear the lowest bit, `10 = 1010`, and `t[10]` covers
`9..10`; clear it again, `8 = 1000`, and `t[8]` covers `1..8`; clearing gives 0, stop. The
step is always "remove the lowest set bit".
"""),
            Short(r"""
C++ gets the lowest set bit with one expression, `i & -i`. With `12 = ...0001100` in binary
and `-12` its two's complement, what is `12 & -12`?
""", accept=["4"], placeholder="a number",
                hint="Two's complement: `-x = ~x + 1`. Flip every bit of 12, add one, then AND with 12.",
                explain=r"""
`~12 = ...1110011`, plus one carries through the trailing ones: `-12 = ...1110100`. The only
bit it shares with `...0001100` is the lowest set bit of 12: `12 & -12 = 4`. In general
`x & -x` isolates the lowest set bit. So `prefix` is:
`for (; i > 0; i -= i & -i) s += t[i];`.
"""),
            Short(r"""
Now the update. Suppose `n = 16` and `a[5]` changes. Which `t[i]` cover position 5 and must
change? List their indices in increasing order.
""", accept=["5 6 8 16", "5, 6, 8, 16"], placeholder="indices",
                hint="`t[i]` covers `i − lowbit(i) + 1 .. i`. Check `t[5]`, `t[6]`, `t[7]`, `t[8]`, ..., `t[16]`.",
                explain=r"""
`t[5]` covers `5`, `t[6]` covers `5..6`, `t[7]` only `7`, `t[8]` covers `1..8`, `t[9]` to
`t[15]` start after 5, `t[16]` covers everything. So `5, 6, 8, 16`: each is the previous
plus its lowest set bit (`5 + 1`, `6 + 2`, `8 + 8`). Adding the lowest bit carries into a
higher bit and gives the next index whose block is long enough to reach back to 5; the
indices skipped in between (like 7) have blocks too short. So `add` is:
`for (; i <= n; i += i & -i) t[i] += v;`.
"""),
            Numeric(r"""
At most how many iterations does one `add` or one `prefix` take when `n = 2·10^5`?
""", answer=18, tol=1,
                explain=r"""
Each `prefix` step clears one set bit, and each `add` step moves the lowest set bit up
by at least one position, so both are bounded by the 18 bits of numbers up to 2·10^5. From
4·10^10 down to about `2·10^5 · 18 · 2 ≈ 7·10^6` steps.
"""),
            Say(r"""
The whole structure is a dozen lines, which is why it is the default choice in contests
whenever it is enough.

```cpp
vector<long long> t(n + 1, 0);       // 1-indexed: t[0] is never used

void add(int i, long long v) {       // a[i] += v
    for (; i <= n; i += i & -i) t[i] += v;
}
long long prefix(int i) {            // a[1] + ... + a[i]
    long long s = 0;
    for (; i > 0; i -= i & -i) s += t[i];
    return s;
}
// sum of a[l..r]:  prefix(r) - prefix(l - 1)
```

Building it with `n` calls to `add` costs O(n log n), which is fine here.
"""),
            MCQ(r"""
You like 0-indexed arrays, so you call `add(0, v)` for the first element. What happens?
""", [
                Opt("It works; index 0 is just another slot.",
                    why="`0 & -0 = 0`, so `i += i & -i` leaves `i` at 0 forever."),
                Opt("An infinite loop: the verdict is TLE.", correct=True,
                    why="Right. The lowest-set-bit arithmetic needs positive indices. Shift by one "
                        "(`add(i + 1, v)`) or read the input 1-indexed."),
                Opt("An out-of-bounds write: RE.",
                    why="It never gets out of bounds; it never leaves index 0."),
            ]),
            MCQ(r"""
The operation "`1 k u`" **sets** `a[k] = u`. What do you do?
""", [
                Opt("`add(k, u)`",
                    why="That adds `u` on top of the old value. Setting `a[2] = 7` twice would add 14."),
                Opt("`add(k, u - a[k]); a[k] = u;` with a separate copy of the array.", correct=True,
                    why="Yes. A Fenwick tree only knows how to add; setting is adding the difference, "
                        "and you need the current value to know the difference."),
                Opt("Rebuild the tree from the array after each change.",
                    why="Correct but O(n) per update: back to 4·10^10."),
            ]),
            Try("dynamic_range_sum", note="1-indexed tree, `long long`, and a set is an add of the "
                "difference."),
        ]),
        Part("Range updates, point queries", [
            Say(r"""
Flip it around: "add `u` to every `a[l..r]`" and "print `a[k]`", interleaved, `n, q ≤ 2·10^5`.

algo01 did range updates with a difference array, `d[l] += u; d[r+1] −= u`, and recovered
the values with one prefix-sum pass at the end. That only worked **offline**: all updates
first, then all reads.
"""),
            Reflect(r"""
How does a Fenwick tree make the difference array work **online**, with reads in between
updates? What does each operation become?
""", answer=r"""
Keep the difference array `d` inside a Fenwick tree. A range update is two point updates:
`add(l, u)` and `add(r + 1, −u)`. The value `a[k]` is the original value plus
`d[1] + ... + d[k]`, which is `prefix(k)`. Both are O(log n), and nothing needs a final
pass: the prefix sum is computed on demand.
"""),
            Short(r"""
Start from `a = [3, 2, 4, 5, 1]` and an all-zero `d`. Apply "add 3 to `[2, 4]`", then
"add −1 to `[1, 3]`". Write `d[1..5]`, separated by spaces.
""", accept=["-1 3 0 1 -3", "-1, 3, 0, 1, -3"], placeholder="five numbers",
                explain=r"""
The first update: `d[2] += 3`, `d[5] −= 3`. The second: `d[1] −= 1`, `d[4] += 1`. So
`d = −1 3 0 1 −3`.
"""),
            Numeric(r"""
What is `a[3]` now?
""", answer=6,
                explain=r"""
Original `a[3] = 4`, plus `prefix(3) = −1 + 3 + 0 = 2`: 6. Check: position 3 got `+3` and
`−1`.
"""),
            MCQ(r"""
An update with `r = n` calls `add(n + 1, −u)`. What happens?
""", [
                Opt("Out of bounds: allocate `n + 2` slots, as in algo01.",
                    why="The loop condition is `i <= n`, so index `n + 1` is never touched."),
                Opt("Nothing, and that is correct: no position after `n` exists, so there is nothing "
                    "to undo.", correct=True,
                    why="Right. The loop runs zero times. Keeping the condition `i <= n` makes this free."),
                Opt("It corrupts `t[n]`.",
                    why="The first iteration already fails `n + 1 <= n`, so no slot is written."),
            ]),
            Try("range_update_queries", note="Difference array inside a Fenwick tree. Values can go "
                "negative and reach 2·10^14."),
        ]),
        Part("Counting with a Fenwick tree: inversions", [
            Say(r"""
A Fenwick tree does not have to be indexed by position. Here it is indexed by **value**.

Problem: count the **inversions** of an array, the pairs `i < j` with `a[i] > a[j]`.
`n ≤ 2·10^5`, `1 ≤ a[i] ≤ 10^9`, values may repeat.
"""),
            Numeric(r"""
How many comparisons does the double loop over all pairs make for `n = 2·10^5`?
""", answer=2e10, rel=0.5, unit="comparisons",
                explain=r"""
`n(n − 1)/2 ≈ 2·10^10`. The compiler vectorises that loop, and it still takes about 6.6
seconds on this judge.
"""),
            Reflect(r"""
Scan left to right. When you reach position `j`, which inversions does `a[j]` complete, and
what do you need to know about the elements before it to count them? What structure
answers that?
""", answer=r"""
`a[j]` forms an inversion with every earlier element that is strictly greater. So you
need "how many of the earlier values lie in the range `(a[j], ∞)`": a count over a range of
values. Keep a Fenwick tree indexed by value, where position `v` holds how many earlier
elements equal `v`; query it, then `add(a[j], 1)`. O(log) per element.
"""),
            MCQ(r"""
The values go up to 10^9. What do you do about the size of the tree?
""", [
                Opt("Allocate 10^9 + 1 counters.",
                    why="4 GB of `int`s: far past any memory limit, and mostly zeros."),
                Opt("Use a `map<int,int>` instead of the tree.",
                    why="A map can store the counts, but it cannot sum the counts of all keys above "
                        "`a[j]` in O(log n)."),
                Opt("Coordinate compression: replace each value by its rank among the distinct values "
                    "(1..m), which keeps every comparison the same.", correct=True,
                    why="Yes (cpp06): sort a copy, `unique` + `erase`, and `lower_bound` gives each "
                        "value's rank. Only the order matters for inversions, and ranks keep the order."),
            ]),
            Short(r"""
For `a = [3, 1, 2, 5, 4]`, how many new inversions does each position complete? Give the
five counts, separated by spaces.
""", accept=["0 1 1 0 1", "0, 1, 1, 0, 1"], placeholder="five numbers",
                explain=r"""
3: nothing before. 1: one earlier value is greater (3). 2: one (3). 5: none. 4: one (5).
Total 3, the pairs (3,1), (3,2), (5,4).
"""),
            MCQ(r"""
With `r` the rank of `a[j]` and `j` earlier elements, which count gives the earlier
elements **strictly** greater than `a[j]`?
""", [
                Opt("`j − prefix(r − 1)`",
                    why="`prefix(r − 1)` counts earlier values `< a[j]`, so this counts `≥`, and equal "
                        "values become inversions: `[2, 2, 1, 2]` gives 5 instead of 2."),
                Opt("`j − prefix(r)`", correct=True,
                    why="Yes: `prefix(r)` counts earlier values `≤ a[j]`; the rest are greater."),
                Opt("`prefix(m) − prefix(r − 1)`",
                    why="That is also the count of values `≥ a[j]`: ties again."),
            ]),
            Numeric(r"""
How large can the answer be for `n = 2·10^5`?
""", answer=2e10, rel=0.3,
                explain=r"""
A strictly decreasing array has every pair inverted: `n(n − 1)/2 ≈ 2·10^10`. `long long`.
"""),
            Try("inversions", note="Compress, scan left to right, count the greater ones before adding."),
        ]),
        Part("Which structure, when", [
            MCQ(r"""
Point assignments `a[k] = u` mixed with range-minimum queries. Which structure fits?
""", [
                Opt("A sparse table, rebuilt after each change.",
                    why="A rebuild is O(n log n), and even a careful fix touches about `n` entries."),
                Opt("A Fenwick tree of minimums, answering `[l, r]` from two prefixes.",
                    why="A range from two prefixes needs subtraction. `min` has none."),
                Opt("A segment tree (algo16).", correct=True,
                    why="Right. It stores every range of a binary split of the array, combines any "
                        "associative operation, and needs no inverse."),
            ]),
            MCQ(r"""
Can a Fenwick tree maintain **prefix maximums** `max(a[1..i])`?
""", [
                Opt("Never: max has no inverse.",
                    why="The inverse is only needed to turn prefixes into ranges, or to undo a change. A "
                        "prefix query needs neither."),
                Opt("Yes, if values only ever increase: `add` becomes `t[i] = max(t[i], v)` and "
                    "`prefix` takes the max over the blocks.", correct=True,
                    why="Right. An increase can only raise the blocks that contain it; a decrease would "
                        "need the second-best value, which the tree does not keep. This is one way to "
                        "write the O(n log n) longest-increasing-subsequence DP of algo07."),
                Opt("Yes, for any updates.",
                    why="Lowering `a[k]` below the current maximum of a block leaves you not knowing the "
                        "block's new maximum."),
            ]),
            MCQ(r"""
A static array and 10^6 queries asking for the GCD of `a[l..r]`, with a tight time limit.
Which is the best fit?
""", [
                Opt("Sparse table: O(n log n) to build, O(1) per query.", correct=True,
                    why="Yes: gcd is idempotent, and with 10^6 queries the log factor of a tree is worth "
                        "avoiding. (Each gcd itself costs O(log) of the values.)"),
                Opt("Fenwick tree over prefix gcds.",
                    why="Prefix gcds cannot be 'removed' from a longer prefix: no inverse."),
                Opt("Prefix sums of the values.",
                    why="The gcd of a range is not determined by its sum."),
            ], explain=r"""
The rule of thumb: static and idempotent → sparse table. Point updates and an invertible
operation (sums, XOR) → Fenwick tree. Anything else (updates with min or max, range
assignment, fancy summaries) → segment tree, next lesson.
"""),
        ]),
    ],
    problems=[STATIC_RMQ, DYNAMIC_RANGE_SUM, RANGE_UPDATE_QUERIES, INVERSIONS],
    cards=[
        Card(r"""Sparse table: definition and recurrence?""",
             r"""`st[j][i] = min(a[i..i+2^j−1])`; `st[j][i] = min(st[j-1][i], st[j-1][i + (1 << (j-1))])`. O(n log n) build."""),
        Card(r"""Sparse table O(1) query for `[l, r]`?""",
             r"""`k = 31 − __builtin_clz(r − l + 1)`; answer `min(st[k][l], st[k][r − (1 << k) + 1])`."""),
        Card(r"""Why does the O(1) sparse-table query need an idempotent operation?""",
             r"""The two blocks overlap, so some elements are combined twice. `min(x, x) = x` (also max, gcd, AND, OR); sums and XOR would double-count."""),
        Card(r"""Fenwick tree: what does `t[i]` store?""",
             r"""The sum of the `i & -i` elements ending at `i`: `a[i − lowbit(i) + 1 .. i]`."""),
        Card(r"""What does `i & -i` compute, and why?""",
             r"""The lowest set bit of `i`. `-i = ~i + 1`: the +1 carries through the flipped trailing zeros, so only that one bit is shared."""),
        Card(r"""Fenwick `add` and `prefix` loops?""",
             r"""`for (; i <= n; i += i & -i) t[i] += v;` and `for (; i > 0; i -= i & -i) s += t[i];`. Both O(log n)."""),
        Card(r"""Why must a Fenwick tree be 1-indexed?""",
             r"""`0 & -0 = 0`: `add(0, v)` never advances, an infinite loop."""),
        Card(r"""Point *assignment* `a[k] = u` in a Fenwick tree?""",
             r"""`add(k, u - a[k]); a[k] = u;` with a copy of the array: the tree can only add."""),
        Card(r"""Range add, point query with a Fenwick tree?""",
             r"""Store the difference array: `add(l, u); add(r + 1, -u);` and `a[k] = original[k] + prefix(k)`."""),
        Card(r"""Counting inversions with a Fenwick tree?""",
             r"""Compress values to ranks; scan left to right; `ans += j − prefix(rank)` (earlier values strictly greater), then `add(rank, 1)`. Answer in `long long`."""),
        Card(r"""Sparse table vs Fenwick vs segment tree: when each?""",
             r"""Static + idempotent: sparse table. Point updates + invertible operation (sum, XOR): Fenwick. Min/max with updates, range assignment, custom merges: segment tree."""),
    ],
)
