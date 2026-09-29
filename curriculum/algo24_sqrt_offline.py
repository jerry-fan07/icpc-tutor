from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _range(rng, n, wide):
    """A query range; `wide` ones cover nearly the whole array (the naive's worst case)."""
    if wide:
        l = rng.randint(1, min(n, 40))
        r = rng.randint(max(l, n - 40), n)
    else:
        l = rng.randint(1, n)
        r = rng.randint(l, n)
    return l, r


def _cold(rng, n, q, lo, hi, wide, upd):
    a = [rng.randint(lo, hi) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        if rng.random() < upd:
            out.append(f"1 {rng.randint(1, n)} {rng.randint(lo, hi)}")
        else:
            out.append("2 %d %d" % _range(rng, n, wide))
    return "\n".join(out) + "\n"


def _cold_raise(rng, n, q):
    """A few planted minima that updates then raise: `bmin = min(bmin, x)` keeps them."""
    a = [rng.randint(10**8, 10**9) for _ in range(n)]
    planted = rng.sample(range(1, n + 1), 60)
    for k, p in enumerate(planted):
        a[p - 1] = k + 1
    out = [f"{n} {q}", " ".join(map(str, a))]
    order = planted[:]
    rng.shuffle(order)
    for _ in range(q):
        if order and rng.random() < 0.3:
            out.append(f"1 {order.pop()} {rng.randint(10**8, 10**9)}")
        else:
            out.append("2 %d %d" % _range(rng, n, rng.random() < 0.5))
    return "\n".join(out) + "\n"


def _plain_queries(rng, n, q, vmax, wide, vmin=1):
    a = [rng.randint(vmin, vmax) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        out.append("%d %d" % _range(rng, n, wide))
    return "\n".join(out) + "\n"


def _leq(rng, n, q, vmax, wide):
    a = [rng.randint(1, vmax) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        l, r = _range(rng, n, wide)
        x = rng.choice(a) if rng.random() < 0.3 else rng.randint(0, vmax)   # many exact ties
        out.append(f"{l} {r} {x}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- problems
COLD_SPOTS = Problem(
    id="cold_spots",
    title="Cold Spots",
    difficulty="medium",
    complexity="O(q√n)",
    statement=r"""
A glacier monitoring line has `n` temperature sensors in a row, numbered 1 to `n`. The
station receives `q` messages, in order. Each is one of

- `1 i x`: sensor `i` now reads `x`;
- `2 l r`: report the lowest reading among sensors `l, l+1, ..., r` right now.

Answer every report request.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has the initial readings a_1, ..., a_n (−10^9 ≤ a_i ≤ 10^9).

Each of the next `q` lines is `1 i x` (1 ≤ i ≤ n, −10^9 ≤ x ≤ 10^9) or `2 l r`
(1 ≤ l ≤ r ≤ n).
""",
    output=r"""
For each message of type 2, print the minimum reading on its own line.
""",
    samples=[
        Test("6 5\n4 2 7 1 9 3\n2 1 6\n2 5 6\n1 4 8\n2 1 6\n2 3 5\n", "1\n3\n2\n7\n",
             note="The third message raises sensor 4, which held the minimum, from 1 to 8."),
    ],
    tests=[
        Test("1 3\n5\n2 1 1\n1 1 -1000000000\n2 1 1\n"),
        Test("5 4\n7 7 7 7 7\n2 1 5\n1 3 1000000000\n2 2 4\n2 3 3\n"),
        Test("4 3\n-1000000000 1000000000 -1000000000 1000000000\n2 2 2\n1 1 1000000000\n2 1 2\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _cold(rng, rng.randint(1, 12), rng.randint(1, 12), -20, 20, False, 0.4), 14),
        Gen("medium random", lambda rng: _cold(rng, rng.randint(1500, 3000), 3000, -10**9, 10**9, False, 0.5), 3),
        Gen("updates raise the minimum", lambda rng: _cold_raise(rng, 3000, 3000), 3),
        Gen("max size, whole-array reports", lambda rng: _cold(rng, 200000, 200000, -10**9, 10**9, True, 0.1), 2, large=True),
        Gen("max size, random mix", lambda rng: _cold(rng, 200000, 200000, -10**9, 10**9, False, 0.5), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    const int B = 450;                             // about sqrt(2*10^5)
    int nb = (n + B - 1) / B;                      // ceiling: the last block may be short
    vector<int> bmin(nb, INT_MAX);
    for (int i = 0; i < n; i++) bmin[i / B] = min(bmin[i / B], a[i]);
    while (q--) {
        int t, x, y;
        cin >> t >> x >> y;
        if (t == 1) {
            int i = x - 1, b = i / B;
            a[i] = y;
            // min has no inverse: the old value may have been the minimum, so rescan
            int m = INT_MAX;
            for (int j = b * B; j < min(n, (b + 1) * B); j++) m = min(m, a[j]);
            bmin[b] = m;
        } else {
            int l = x - 1, r = y - 1;
            int bl = l / B, br = r / B, m = INT_MAX;
            if (bl == br) {                        // both ends in one block: just scan
                for (int j = l; j <= r; j++) m = min(m, a[j]);
            } else {
                for (int j = l; j < (bl + 1) * B; j++) m = min(m, a[j]);   // left piece
                for (int b = bl + 1; b < br; b++) m = min(m, bmin[b]);     // whole blocks
                for (int j = br * B; j <= r; j++) m = min(m, a[j]);        // right piece
            }
            cout << m << '\n';
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
        int t;
        long long x, y;
        cin >> t >> x >> y;
        if (t == 1) a[x] = y;
        else {
            long long m = a[x];
            for (long long i = x; i <= y; i++) m = min(m, a[i]);
            cout << m << '\n';
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
    vector<int> a(n + 1);
    for (int i = 1; i <= n; i++) cin >> a[i];
    while (q--) {
        int t, x, y;
        cin >> t >> x >> y;
        if (t == 1) a[x] = y;
        else {
            int m = INT_MAX;
            for (int i = x; i <= y; i++) m = min(m, a[i]);
            cout << m << '\n';
        }
    }
}
""",
    hints=[
        r"""Cut the sensors into blocks of about 450 and remember each block's minimum. A report
is two partial blocks, scanned, plus whole blocks, looked up.""",
        r"""An update can *raise* the block's minimum (the sample does). `bmin = min(bmin, x)` is
then wrong: rescan the block, O(B).""",
        r"""When `l` and `r` fall in the same block, scan `l..r` directly; the "left piece to the
end of the block" loop would read past `r`.""",
    ],
    editorial=r"""
Square-root decomposition. Split the array into blocks of `B` and keep `bmin[b]`, the
minimum of block `b`. A report `[l, r]` scans the partial block at each end element by
element (fewer than `B` each) and takes `bmin` for every whole block between them
(at most `n/B`): O(B + n/B), smallest when `B ≈ √n`. With `B = 450` that is about 1,300
steps per report instead of up to 2·10^5.

An update sets `a[i]` and recomputes the minimum of its block by scanning it: O(B).
The O(1) shortcut `bmin[b] = min(bmin[b], x)` is wrong, because the reading being
replaced may have been the block's minimum and `x` may be larger (sample 1, third
message). Sums can be patched by subtracting the old value; minimums cannot, since min has
no inverse.

The details that cost verdicts: the number of blocks is `(n + B - 1) / B` (a ceiling), the
last block may be short (`min(n, (b + 1) * B)` in the rescan), and a report inside one
block must be scanned directly. A segment tree (algo16) does this in O(log n); blocks are
the tool that still works when the per-block summary is something a segment tree cannot
merge.
""",
)

DISTINCT = Problem(
    id="distinct_values",
    title="Distinct Values",
    difficulty="medium",
    source="CSES 1734 - Distinct Values Queries",
    complexity="O((n + q)√n)",
    statement=r"""
You are given an array of `n` integers and `q` queries. Each query names a range `[l, r]`
and asks how many *different* values appear among a_l, a_(l+1), ..., a_r.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

Each of the next `q` lines has `l` and `r` (1 ≤ l ≤ r ≤ n).
""",
    output=r"""
For each query, in input order, print the number of distinct values in the range.
""",
    samples=[
        Test("5 3\n3 2 3 1 2\n1 3\n2 4\n1 5\n", "2\n3\n3\n"),
    ],
    tests=[
        Test("1 1\n1000000000\n1 1\n"),
        Test("6 4\n7 7 7 7 7 7\n1 6\n3 4\n6 6\n1 1\n"),
        Test("6 3\n1 1000000000 2 999999999 3 999999998\n1 6\n2 5\n4 4\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _plain_queries(rng, rng.randint(1, 12), rng.randint(1, 12), 5, False), 14),
        Gen("medium, huge values", lambda rng: _plain_queries(rng, 2000, 2000, 10**9, False), 2),
        Gen("medium, few values", lambda rng: _plain_queries(rng, 3000, 3000, 30, False), 1),
        Gen("max size, whole-array queries", lambda rng: _plain_queries(rng, 200000, 200000, 10**9, True), 1, large=True),
        Gen("max size, random queries", lambda rng: _plain_queries(rng, 200000, 200000, 10**9, False), 1, large=True),
        Gen("max size, 1000 values", lambda rng: _plain_queries(rng, 200000, 200000, 1000, False), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    // compress values to 0..m-1 so the counts live in an array, not a map
    vector<int> vals(a);
    sort(vals.begin(), vals.end());
    vals.erase(unique(vals.begin(), vals.end()), vals.end());
    for (auto& x : a) x = lower_bound(vals.begin(), vals.end(), x) - vals.begin();

    vector<int> L(q), R(q), ord(q);
    for (int k = 0; k < q; k++) {
        cin >> L[k] >> R[k];
        L[k]--, R[k]--;
    }
    const int B = max(1, (int)(n / sqrt((double)q)));   // balances q*B against n*n/B
    iota(ord.begin(), ord.end(), 0);
    sort(ord.begin(), ord.end(), [&](int x, int y) {
        int bx = L[x] / B, by = L[y] / B;
        if (bx != by) return bx < by;
        return (bx & 1) ? R[x] > R[y] : R[x] < R[y];      // odd blocks sweep r downwards
    });

    vector<int> cnt(vals.size(), 0), ans(q);
    int d = 0;                                            // values with cnt > 0
    auto add = [&](int i) { if (cnt[a[i]]++ == 0) d++; };
    auto rem = [&](int i) { if (--cnt[a[i]] == 0) d--; };
    int cl = 0, cr = -1;                                  // current window, empty
    for (int k : ord) {
        while (cr < R[k]) add(++cr);                      // grow first ...
        while (cl > L[k]) add(--cl);
        while (cr > R[k]) rem(cr--);                      // ... then shrink
        while (cl < L[k]) rem(cl++);
        ans[k] = d;
    }
    for (int k = 0; k < q; k++) cout << ans[k] << '\n';  // input order
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
        set<int> s(a.begin() + l, a.begin() + r + 1);
        cout << s.size() << '\n';
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
    vector<int> vals(a.begin() + 1, a.end());
    sort(vals.begin(), vals.end());
    vals.erase(unique(vals.begin(), vals.end()), vals.end());
    for (int i = 1; i <= n; i++) a[i] = lower_bound(vals.begin(), vals.end(), a[i]) - vals.begin();
    vector<int> seen(vals.size(), -1);           // seen[v] == k: v already counted for query k
    for (int k = 0; k < q; k++) {
        int l, r;
        cin >> l >> r;
        int d = 0;
        for (int i = l; i <= r; i++)
            if (seen[a[i]] != k) { seen[a[i]] = k; d++; }
        cout << d << '\n';
    }
}
""",
    hints=[
        r"""All queries are known before you answer any. Answer them in an order where
consecutive ranges are close, keeping a window with a count per value.""",
        r"""Mo's order: sort by `(l / B, r)` with `B ≈ n / √q`. Add and remove one element at a
time; `d` changes when a count goes 0 → 1 or 1 → 0. Store answers by query index.""",
        r"""Values reach 10^9: compress them (sort, unique, `lower_bound`) so `cnt` is an array.
A `map` makes each of the ~10^8 moves a tree lookup, which is too slow.""",
    ],
    editorial=r"""
**Mo's algorithm.** Keep a window `[L, R]`, `cnt[v]` for the values inside it and `d`,
the number of values with `cnt[v] > 0`. Moving an edge by one position is O(1). Sort the
queries by the block of `l` (blocks of `B`), then by `r`, and slide the window from one
query to the next. Within a block the right end only moves one way (at most `n` per
block, `n^2/B` in total), and the left end moves at most `B` per query (`qB` in total).
With `B = n/√q` both are `n√q`, so there are about 1.2·10^8 cheap moves at the limits, against 4·10^10
for rescanning each range. Odd blocks sort `r` descending so the right end does not
rewind at every block change. Grow the window before shrinking it, and compress the
values first: with a `map` for `cnt`, the same program takes about 10 s here.

**The offline sweep, O((n + q) log n).** Sort queries by `r` and sweep `r` upward,
keeping a Fenwick tree with a 1 at the *last* occurrence (so far) of each value. A value
occurs in `[l, r]` exactly when its last occurrence at or before `r` is at least `l`, so
the answer is the Fenwick sum over `[l, r]`. When `a[r]` was last seen at `p`, clear `p`
and set `r`. The last part of the lesson builds this one.
""",
)

SOCKS = Problem(
    id="matching_socks",
    title="Matching Socks",
    difficulty="medium",
    complexity="O((n + q)√n)",
    statement=r"""
A laundromat lines up `n` lost socks along a counter; sock `i` has colour `c_i`. For
each of `q` questions "if I take every sock from position `l` to position `r`, how many
matching pairs could I make?", count the pairs of positions `i < j` with
`l ≤ i < j ≤ r` and `c_i = c_j`. (Each pair of positions counts separately: three red
socks give three pairs.)
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 10^5).

The second line has c_1, ..., c_n (1 ≤ c_i ≤ n).

Each of the next `q` lines has `l` and `r` (1 ≤ l ≤ r ≤ n).
""",
    output=r"""
For each question, in input order, print the number of pairs on its own line.
""",
    samples=[
        Test("7 4\n1 2 1 1 3 2 1\n1 7\n2 4\n5 5\n3 6\n", "7\n1\n0\n1\n"),
    ],
    tests=[
        Test("1 1\n1\n1 1\n"),
        Test("5 3\n2 2 2 2 2\n1 5\n2 4\n3 3\n"),
        Test("6 2\n1 2 3 4 5 6\n1 6\n2 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _plain_queries(rng, rng.randint(1, 12), rng.randint(1, 12), 3, False), 14),
        Gen("medium random", lambda rng: _plain_queries(rng, 500, 500, 20, False), 2),
        Gen("max size, one colour, whole range", lambda rng: _plain_queries(rng, 100000, 100000, 1, True), 1, large=True),
        Gen("max size, random colours", lambda rng: _plain_queries(rng, 100000, 100000, 100000, False), 1, large=True),
        Gen("max size, 5 colours", lambda rng: _plain_queries(rng, 100000, 100000, 5, False), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> c(n);
    for (auto& x : c) cin >> x;                   // colours are 1..n: an array counts them
    vector<int> L(q), R(q), ord(q);
    for (int k = 0; k < q; k++) {
        cin >> L[k] >> R[k];
        L[k]--, R[k]--;
    }
    const int B = max(1, (int)(n / sqrt((double)q)));
    iota(ord.begin(), ord.end(), 0);
    sort(ord.begin(), ord.end(), [&](int x, int y) {
        int bx = L[x] / B, by = L[y] / B;
        if (bx != by) return bx < by;
        return (bx & 1) ? R[x] > R[y] : R[x] < R[y];
    });
    vector<int> cnt(n + 1, 0);
    vector<long long> ans(q);
    long long pairs = 0;                           // up to n(n-1)/2, about 5*10^9
    // a sock entering pairs with every sock of its colour already inside
    auto add = [&](int i) { pairs += cnt[c[i]]; cnt[c[i]]++; };
    // a sock leaving takes those pairs with it (not counting itself)
    auto rem = [&](int i) { cnt[c[i]]--; pairs -= cnt[c[i]]; };
    int cl = 0, cr = -1;
    for (int k : ord) {
        while (cr < R[k]) add(++cr);
        while (cl > L[k]) add(--cl);
        while (cr > R[k]) rem(cr--);
        while (cl < L[k]) rem(cl++);
        ans[k] = pairs;
    }
    for (int k = 0; k < q; k++) cout << ans[k] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, q;
    cin >> n >> q;
    vector<int> c(n + 1);
    for (int i = 1; i <= n; i++) cin >> c[i];
    while (q--) {
        int l, r;
        cin >> l >> r;
        long long pairs = 0;
        for (int i = l; i <= r; i++)
            for (int j = i + 1; j <= r; j++)
                if (c[i] == c[j]) pairs++;
        cout << pairs << '\n';
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
    vector<int> c(n + 1);
    for (int i = 1; i <= n; i++) cin >> c[i];
    vector<int> cnt(n + 1, 0);
    while (q--) {
        int l, r;
        cin >> l >> r;
        long long pairs = 0;
        for (int i = l; i <= r; i++) pairs += cnt[c[i]]++;
        for (int i = l; i <= r; i++) cnt[c[i]] = 0;
        cout << pairs << '\n';
    }
}
""",
    hints=[
        r"""Mo's algorithm again: what changes in the number of pairs when one sock enters the
window? When one leaves?""",
        r"""Entering: `pairs += cnt[x]; cnt[x]++;`. Leaving: `cnt[x]--; pairs -= cnt[x];`.""",
        r"""One colour, whole range: 10^5 · (10^5 − 1) / 2 ≈ 5·10^9 pairs. `long long`.""",
    ],
    editorial=r"""
The answer for a range is the sum over colours of `cnt(cnt − 1)/2`, which does not split
into a sum over positions in any useful way, but it is easy to *maintain*: a sock of
colour `x` entering a window that already holds `cnt[x]` socks of that colour creates
exactly `cnt[x]` new pairs, and a sock leaving destroys `cnt[x] − 1` (the count after
removing it). So add and remove are O(1), and Mo's algorithm answers everything in
O((n + q)√n): about 6·10^7 moves here.

Two traps. The count reaches C(10^5, 2) = 4,999,950,000, past `int`: both the running
`pairs` and the stored answers must be `long long`. And the order inside `rem` matters:
decrement first, then subtract, or the leaving sock is counted as pairing with itself.
""",
)

LIGHT_PARCELS = Problem(
    id="light_parcels",
    title="Light Parcels",
    difficulty="medium",
    complexity="O((n + q) log n)",
    statement=r"""
A conveyor carries `n` parcels, parcel `i` weighing `a_i` grams. A loading crew asks
`q` questions of the form "among parcels `l` to `r`, how many weigh at most `x` grams?"
(those can go on the light shelf). The conveyor does not change between questions.

Answer every question.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has a_1, ..., a_n (1 ≤ a_i ≤ 10^9).

Each of the next `q` lines has `l r x` (1 ≤ l ≤ r ≤ n, 0 ≤ x ≤ 10^9).
""",
    output=r"""
For each question, in input order, print the number of parcels among `l..r` with
a_i ≤ x.
""",
    samples=[
        Test("6 4\n5 1 4 2 5 3\n1 6 3\n2 5 4\n3 3 3\n1 6 5\n", "3\n3\n0\n6\n",
             note="The last question asks for weights at most 5, and two parcels weigh exactly 5."),
    ],
    tests=[
        Test("1 3\n7\n1 1 6\n1 1 7\n1 1 0\n"),
        Test("5 3\n1000000000 1000000000 1 1000000000 1\n1 5 1000000000\n2 4 999999999\n5 5 1\n"),
        Test("4 2\n2 2 2 2\n1 4 2\n2 3 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _leq(rng, rng.randint(1, 12), rng.randint(1, 12), 8, False), 14),
        Gen("medium random", lambda rng: _leq(rng, 2000, 2000, 10**9, False), 2),
        Gen("medium, many ties", lambda rng: _leq(rng, 3000, 3000, 10, False), 1),
        Gen("max size, whole-array questions", lambda rng: _leq(rng, 200000, 200000, 10**9, True), 1, large=True),
        Gen("max size, random", lambda rng: _leq(rng, 200000, 200000, 10**9, False), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int n;
vector<int> fw;                                    // Fenwick tree over positions 1..n
void add(int i) { for (; i <= n; i += i & -i) fw[i]++; }
int sum(int i) { int s = 0; for (; i > 0; i -= i & -i) s += fw[i]; return s; }

struct Query { int l, r, x, id; };

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> n >> q;
    vector<pair<int, int>> el(n);                  // (weight, position)
    for (int i = 0; i < n; i++) {
        cin >> el[i].first;
        el[i].second = i + 1;
    }
    vector<Query> qs(q);
    for (int k = 0; k < q; k++) {
        cin >> qs[k].l >> qs[k].r >> qs[k].x;
        qs[k].id = k;
    }
    // sweep a horizontal line upwards: parcels and questions both in weight order
    sort(el.begin(), el.end());
    sort(qs.begin(), qs.end(), [](const Query& a, const Query& b) { return a.x < b.x; });
    fw.assign(n + 1, 0);
    vector<int> ans(q);
    int p = 0;
    for (const Query& qu : qs) {
        // switch on every parcel with weight <= x, ties included, before answering
        while (p < n && el[p].first <= qu.x) add(el[p++].second);
        ans[qu.id] = sum(qu.r) - sum(qu.l - 1);
    }
    for (int k = 0; k < q; k++) cout << ans[k] << '\n';
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
        int l, r;
        long long x;
        cin >> l >> r >> x;
        int c = 0;
        for (int i = l; i <= r; i++)
            if (a[i] <= x) c++;
        cout << c << '\n';
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
        int l, r, x;
        cin >> l >> r >> x;
        int c = 0;
        for (int i = l; i <= r; i++) c += a[i] <= x;
        cout << c << '\n';
    }
}
""",
    hints=[
        r"""Nothing changes between questions, so you may answer them in any order. Which order
makes "weighs at most `x`" easy to maintain?""",
        r"""Sort questions by `x` and parcels by weight. Sweep upwards, marking each parcel's
position in a Fenwick tree once its weight is ≤ the current `x`; the answer is a range sum
over `[l, r]`.""",
        r"""Ties: a parcel weighing exactly `x` counts, so switch it on before answering (`<=`,
not `<`). Remember each question's index to print answers in input order.""",
    ],
    editorial=r"""
Offline, sweeping by *value* instead of position. Sort the parcels by weight and the
questions by `x`. Move a line upwards through the weights: before answering a question
with bound `x`, mark (in a Fenwick tree over positions) every parcel of weight ≤ `x`.
At that moment the marked positions are exactly the parcels that qualify, so the answer
is the number of marks in `[l, r]`: two prefix sums. Each parcel is marked once, each
question costs two queries: O((n + q) log n) after sorting, against 4·10^10 steps for
scanning every range.

Mo's algorithm does not fit well: the window would have to answer "how many ≤ x" for a
different `x` every time. A block solution with a sorted copy of each block works online
in O(√n log n) per question, but it is several times slower than the sweep. Watch the tie
case (`<=`) and print in input order.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo24",
    title="square-root decomposition & offline queries",
    track="algo",
    order=24,
    summary="Blocks of √n and the balance argument, Mo's algorithm and why its order bounds "
            "the pointer moves, and offline sweeps with a Fenwick tree.",
    prereqs=["algo15"],
    tags=["sqrt decomposition", "blocks", "mo's algorithm", "offline queries", "fenwick sweep",
          "distinct values", "coordinate compression"],
    parts=[
        Part("Updates break the old tricks", [
            Say(r"""
A new shape of problem. There are `n` sensors in a row and `q` messages, `n, q ≤ 2·10^5`,
one second. A message is either

- `1 i x`: sensor `i` now reads `x`, or
- `2 l r`: report the lowest reading among sensors `l..r`.

The two kinds are interleaved, so each report must see every update before it. You own
three range tools so far: prefix sums (algo01), sparse tables and Fenwick trees (algo15).
"""),
            MCQ(r"""
Which of those three answers this problem in O(log n) or better per message?
""", [
                Opt("Prefix minimums, `pm[i] = min(a[1..i])`.",
                    why="Two problems. `pm[r]` and `pm[l-1]` cannot be combined into the min of "
                        "`a[l..r]`, because min has no inverse. And an update at `i` changes "
                        "every `pm[j]` with `j ≥ i`: O(n) per update."),
                Opt("A sparse table.",
                    why="O(1) reports, but it is a static structure: at level `k`, 2^k entries "
                        "contain position `i`, so one update touches about 2n entries."),
                Opt("A Fenwick tree storing minimums.",
                    why="A Fenwick tree answers prefixes and gets a range by subtracting two of "
                        "them; minimums cannot be subtracted. It also only supports updates "
                        "that lower a value, and `x` may raise a reading."),
                Opt("None of them, as they stand.", correct=True,
                    why="Right. Each relies on something this problem lacks: no updates (prefix "
                        "sums, sparse tables) or an invertible operation (Fenwick trees). A "
                        "segment tree (algo16) handles it in O(log n); this lesson builds a "
                        "blunter tool that bends to far more problems."),
            ]),
            Numeric(r"""
The direct program assigns on an update and scans `a[l..r]` on a report. In the worst case
every message is a report over nearly the whole array. Roughly how many steps is that, in
total?
""", answer=4e10, rel=0.5, unit="steps",
                explain=r"""
`q · n = 2·10^5 · 2·10^5 = 4·10^10`. Measured on this machine, that loop takes about 9 s
on the large tests, against a 1 s limit.
"""),
            Reflect(r"""
A report over `[3, 199990]` scans almost 200,000 readings, and since the previous report
at most one reading has changed. What is the scan wasting, and what could you keep so a
report can skip most of it?
""", answer=r"""
Nearly everything it reads is the same as last time: it recomputes the minimum of the
same long stretches over and over. Cut the array into fixed chunks and remember each
chunk's minimum. A report then takes a whole chunk's stored minimum in one step instead
of rescanning it, and an update only spoils the one chunk it lands in, which can be
recomputed on its own.
"""),
        ]),
        Part("Blocks, and why √n", [
            Say(r"""
Cut the array into consecutive **blocks** of `B` elements (the last one may be shorter)
and store `bmin[b]`, the minimum of block `b`. A report `[l, r]` then has three pieces:

```
| block 0 | block 1 | block 2 | block 3 | block 4 |
      [l ................................. r]
 left piece   whole blocks: bmin[1..3]   right piece
```

The two pieces at the ends are partial blocks, scanned element by element (fewer than
`B` each). Every block strictly between them is covered whole and costs one lookup. This
is **square-root decomposition**; the name comes from the choice of `B`, which we get to
in a moment.
"""),
            Short(r"""
Take `a = [5, 2, 8, 6, 1, 9, 4, 7, 3]` and `B = 3`. What is `bmin`? Type its three values.
""", accept=["2 1 3", "2,1,3", "[2, 1, 3]", "[2,1,3]"], placeholder="three numbers",
                explain=r"""
The blocks are `[5, 2, 8]`, `[6, 1, 9]` and `[4, 7, 3]`, so `bmin = [2, 1, 3]`. A report
over positions 2..8 (1-indexed) reads `2, 8` from the left piece, `bmin[1] = 1` for the
middle block, and `4, 7` from the right piece: four elements and one lookup instead of
seven elements.
"""),
            MCQ(r"""
Now the message `1 5 10`: position 5 (the `1`) becomes 10. The update code does
`a[i] = x; bmin[b] = min(bmin[b], x);`. What is wrong with it?
""", [
                Opt("Nothing: `min(1, 10) = 1` and the block's minimum is still 1.",
                    why="The block is now `[6, 10, 9]`. The 1 no longer exists, yet `bmin[1]` "
                        "still says 1, and every report covering that block answers 1."),
                Opt("The old value was the block's minimum and the new one is larger, so "
                    "`bmin` must be recomputed by scanning the block: it should become 6.",
                    correct=True,
                    why="Right. The update costs O(B). With sums you could subtract the old value "
                        "and add the new one in O(1); min has no inverse, so the block is "
                        "rescanned."),
                Opt("It should rebuild every block after an update.",
                    why="Only the block containing position `i` changed. Rebuilding everything "
                        "is O(n) per update: the brute force again."),
            ], explain=r"""
This bug passes any test where updates only lower values. The sample of the problem you
are about to solve raises the minimum on purpose.
"""),
            Numeric(r"""
Count the cost of the worst report as about `n/B` block lookups plus `2B` scanned elements
in the two pieces. With `n = 2·10^5` and `B = 20`, about how many steps is that?
""", answer=10040, rel=0.2, unit="steps",
                explain=r"""
`200000/20 + 2·20 = 10000 + 40 ≈ 10^4`, almost all of it block lookups: tiny blocks mean
too many of them. With `B = 20000` it flips: `10 + 40000`, almost all scanning. The best
`B` is somewhere in between, where neither term dominates.
"""),
            Numeric(r"""
Drop the factor 2 for a moment and minimise `f(B) = n/B + B`. Which `B` is best for
`n = 2·10^5`?
""", answer=447, rel=0.05,
                hint="The two terms multiply to `n` whatever `B` is. For a fixed product, when "
                     "is the sum of two positive numbers smallest?",
                explain=r"""
When the two terms are equal: `n/B = B`, so `B = √n ≈ 447`, and each report costs about
`2√n ≈ 894` steps. (Calculus agrees: `f'(B) = 1 − n/B^2 = 0`.) With the factor 2 the
optimum shifts to `√(n/2) ≈ 316`. Constants move the best `B` a little, and the curve is
flat near it: anything from 200 to 1000 works nearly as well here. This **balance
argument** (make the two costs equal) is how every block size in this lesson is chosen.
"""),
            Numeric(r"""
With `B ≈ √n`, about how many steps do all `q = 2·10^5` reports take together, at
`2√n` each?
""", answer=1.8e8, rel=0.5, unit="steps",
                explain=r"""
`2·10^5 · 894 ≈ 1.8·10^8`, down from 4·10^10. That is at the edge of the 10^8 rule of
thumb, but each step is one comparison in a tight loop over contiguous memory, the
cheapest step there is: the reference runs in under 0.1 s here. Updates cost `B` each,
another 9·10^7 at most.
"""),
        ]),
        Part("Blocks in C++", [
            Say(r"""
Zero-indexed, with a fixed `B` (450 is about `√(2·10^5)`):

```cpp
const int B = 450;
vector<int> bmin((n + B - 1) / B, INT_MAX);
for (int i = 0; i < n; i++) bmin[i / B] = min(bmin[i / B], a[i]);

// report on [l, r], 0-indexed, inclusive
int bl = l / B, br = r / B, m = INT_MAX;
if (bl == br) {
    for (int i = l; i <= r; i++) m = min(m, a[i]);
} else {
    for (int i = l; i < (bl + 1) * B; i++) m = min(m, a[i]);   // left piece
    for (int b = bl + 1; b < br; b++) m = min(m, bmin[b]);     // whole blocks
    for (int i = br * B; i <= r; i++) m = min(m, a[i]);        // right piece
}
```

The block of position `i` is `i / B`; block `b` covers `b·B .. (b+1)·B − 1`.
"""),
            MCQ(r"""
Suppose you drop the `bl == br` branch and always run the three loops. What goes wrong
when `l` and `r` are in the same block?
""", [
                Opt("Nothing: the middle loop runs zero times and the two pieces cover `[l, r]`.",
                    why="The pieces are `[l, end of block]` and `[start of block, r]`, which "
                        "together cover the whole block. With the block `[5, 2, 8]` and "
                        "`l = r = 0`, the loops read 2 and answer 2 instead of 5."),
                Opt("Each piece is scanned twice, which is slower but correct.",
                    why="It is not just slower: the loops read elements outside `[l, r]`, "
                        "and one of them can be smaller than anything inside."),
                Opt("The pieces read elements outside `[l, r]` (the left loop runs to the end of "
                    "the block, the right loop starts at its beginning), so the answer can be "
                    "too small.", correct=True,
                    why="Right. In the last block it can also read past the end of the array, "
                        "because `(bl + 1) * B` may exceed `n`."),
            ]),
            Numeric(r"""
With `B = 450` and `n = 2·10^5`, how many entries does `bmin` need?
""", answer=445,
                explain=r"""
`⌈200000/450⌉ = 445`: 444 full blocks and one of 200 elements. `(n + B - 1) / B` is the
integer ceiling. Plain `n / B = 444` leaves the last 200 sensors without a block, and
`bmin[i / B]` writes out of bounds for them.
"""),
            Try("cold_spots", note="Blocks of about 450. The update rescans its block; a report "
                "in one block scans directly."),
        ]),
        Part("Reordering the questions: Mo's algorithm", [
            Say(r"""
Now a problem where blocks alone do not help. **Distinct values**: `n, q ≤ 2·10^5`,
`a_i ≤ 10^9`, and each query `[l, r]` asks how many *different* values appear in
`a[l..r]`. There are no updates. Scanning each range with a `seen` array is 4·10^10
steps again (measured: still running after 15 s).
"""),
            MCQ(r"""
Blocks worked for minimums. Suppose each block stores its number of distinct values. Can
you combine those numbers into the answer for a range?
""", [
                Opt("Yes: add the counts of the whole blocks and of the pieces.",
                    why="A value present in two blocks is counted twice. `[1, 2]` and `[2, 3]` "
                        "have 2 distinct values each; together they have 3, not 4."),
                Opt("Yes: take the maximum of the counts.",
                    why="`[1, 2]` and `[3, 4]`: the maximum is 2, the answer is 4."),
                Opt("No: the count for a union depends on which values the parts share, and a "
                    "count does not say which values they are.", correct=True,
                    why="Right. A minimum merges from two summaries; a distinct count does not. "
                        "You would need the sets themselves, which is as big as the array."),
            ]),
            Say(r"""
A different kind of reuse. Keep a **window** `[L, R]` with `cnt[v]`, the number of copies
of `v` inside it, and `d`, the number of values with `cnt[v] > 0`. Moving an edge by one
position costs O(1):

```cpp
void add(int i)    { if (cnt[a[i]]++ == 0) d++; }   // a[i] enters the window
void remove(int i) { if (--cnt[a[i]] == 0) d--; }   // a[i] leaves it
```

To answer `[l, r]`, slide `L` to `l` and `R` to `r` one step at a time. That costs
`|L − l| + |R − r|` moves, and everything the two queries share is kept.
"""),
            MCQ(r"""
Answer the queries in input order this way. What is the worst case?
""", [
                Opt("O(n + q): the window only ever slides.",
                    why="Only when consecutive queries are close. `[1, n]`, `[n, n]`, `[1, n]`, "
                        "... moves an edge by about `n` on every query."),
                Opt("About `q · n = 4·10^10` moves: the input can alternate between far-apart "
                    "ranges.", correct=True,
                    why="Right. Even random ranges cost about 2.3·10^10 moves (measured). The "
                        "window helps only if consecutive queries are close to each other."),
                Opt("O(q log n), since each move is O(1).",
                    why="Each move is O(1), but nothing bounds the number of moves per query "
                        "below `n`."),
            ]),
            Reflect(r"""
Nothing forces you to use the input order. All queries are known before you answer the
first (*offline*, as in algo01), so you can answer them in any order and print the answers
in input order at the end. Say you sort the queries by `l`. How far does each pointer
travel in total?
""", answer=r"""
The left pointer only moves right, so it travels at most `n` in total. But among queries
with nearby `l`, the right ends come in no particular order, so the right pointer can swing
across the whole array for each query: still about `q · n` (measured on random queries:
6.6·10^9 moves). Sorting by one endpoint makes that endpoint cheap and leaves the other one
as bad as before. We need an order that is good for both.
"""),
            Say(r"""
**Mo's algorithm** is the compromise. Cut the *positions* into blocks of size `B` and sort
the queries by the block of `l`, then by `r`:

```cpp
sort(ord.begin(), ord.end(), [&](int x, int y) {
    if (L[x] / B != L[y] / B) return L[x] / B < L[y] / B;
    return R[x] < R[y];
});
```

Among queries whose `l` is in the same block, the right ends arrive in increasing order,
and the left ends stay within a stretch of width `B`. Count the moves of each pointer
separately.
"""),
            Numeric(r"""
The right pointer. Within one block of `l` it only moves right, at most `n` moves per
block, and there are `n/B` blocks. With `n = 2·10^5` and `B = 447`, about how many
right-pointer moves is that?
""", answer=9e7, rel=0.5, unit="moves",
                explain=r"""
`n · n/B = n^2/B = 4·10^10 / 447 ≈ 9·10^7`. At each block change the pointer may also go
back down, at most `n` more per block, which at worst doubles this. (A trick below
removes that rewind.)
"""),
            Numeric(r"""
The left pointer. Two consecutive queries in the same block have `l` within `B` of each
other. About how many left-pointer moves for `q = 2·10^5` queries and `B = 447`?
""", answer=9e7, rel=0.5, unit="moves",
                explain=r"""
At most `B` per query: `q · B ≈ 9·10^7`. At a block change it moves at most `2B`, and there
are `n/B` changes, which adds only `2n`. So both pointers together make about
`qB + n^2/B ≈ 1.8·10^8` moves, each an array increment. On random queries the measured
total is 1.2·10^8, against 2.3·10^10 in input order.
"""),
            MCQ(r"""
The total is about `qB + n^2/B`. Which block size minimises it?
""", [
                Opt("`B = √n`, always.",
                    why="That is the answer when `q = n`. The balance point of `qB` and "
                        "`n^2/B` depends on `q` too."),
                Opt("`B = log n`, like the levels of a Fenwick tree.",
                    why="With `B = 18` the right pointer alone makes `n^2/B ≈ 2·10^9` moves."),
                Opt("`B = n/√q`.", correct=True,
                    why="Setting `qB = n^2/B` gives `B^2 = n^2/q`. With `q = n` that is `√n`; "
                        "with few queries, blocks should be bigger. For `n = 2·10^5` and "
                        "`q = 10^4`, `B = 2000`."),
                Opt("`B = q/√n`.",
                    why="It happens to agree when `q = n`. Try `n = 10^6`, `q = 100`: it gives "
                        "`B = 0.1`, while the balance point is `10^5`."),
            ], explain=r"""
With `B = n/√q` the total is `2n√q`: O((n + q)√n) in the usual statement. The same balance
argument as before, with the two costs weighted by how often they are paid.
"""),
        ]),
        Part("Mo's algorithm in C++", [
            Short(r"""
A hand example. Positions `0..8`, `B = 3`, so the block of `l` is `l / 3`. Six queries:
1 = `[1, 8]`, 2 = `[4, 5]`, 3 = `[2, 3]`, 4 = `[5, 7]`, 5 = `[0, 2]`, 6 = `[3, 8]`. In
which order does Mo's (block of `l`, then `r`) answer them? Type the six query numbers.
""", accept=["5 3 1 2 4 6", "5,3,1,2,4,6", "5, 3, 1, 2, 4, 6"], placeholder="six query numbers",
                hint="Queries 1, 3 and 5 have `l` in block 0.",
                explain=r"""
Block 0 holds queries 1, 3, 5 (`l = 1, 2, 0`); sorted by `r` they go 5 (`r = 2`),
3 (`r = 3`), 1 (`r = 8`). Block 1 holds 2, 4, 6 (`l = 4, 5, 3`), by `r`: 2 (5), 4 (7),
6 (8). Starting from the empty window (`R = −1`), the right pointer visits
`2, 3, 8, 5, 7, 8`: 3 + 1 + 5 + 3 + 2 + 1 = 15 moves. The 3 moves from 8 back to 5 are
the rewind at the block change.
"""),
            MCQ(r"""
Every block starts its sweep of `r` from the bottom, so at each block change the right
pointer rewinds, up to `n` moves. What small change removes the rewind?
""", [
                Opt("Sort by `r` descending in every block.",
                    why="Then every block starts at the top and sweeps down: the same rewind, "
                        "mirrored."),
                Opt("In odd-numbered blocks, sort by `r` descending: the pointer sweeps up in one "
                    "block and back down in the next.", correct=True,
                    why="Right. In the example the order becomes `5 3 1 6 4 2`, `r` visits "
                        "`2, 3, 8, 8, 7, 5`, and the right pointer makes 12 moves instead of 15. "
                        "On random large inputs the right pointer's total halves (measured: "
                        "8.9·10^7 down to 4.5·10^7)."),
                Opt("Use a smaller `B`.",
                    why="More blocks means more block changes, so more rewinds."),
                Opt("Process the blocks from last to first.",
                    why="The sweeps inside the blocks still all run the same way, so every "
                        "block change still rewinds."),
            ], explain=r"""
The comparator becomes
`return (bx & 1) ? R[x] > R[y] : R[x] < R[y];` for queries in the same block `bx`.
This is the **odd-even trick**: one line, often 30-40% faster in total.
"""),
            Say(r"""
The main loop, with answers stored by query index and printed in input order at the end:

```cpp
int L = 0, R = -1;                       // the empty window
for (int k : ord) {
    while (R < r[k]) add(++R);           // grow ...
    while (L > l[k]) add(--L);
    while (R > r[k]) remove(R--);        // ... then shrink
    while (L < l[k]) remove(L++);
    ans[k] = d;
}
for (int k = 0; k < q; k++) cout << ans[k] << '\n';
```
"""),
            MCQ(r"""
Why do the two growing loops come before the two shrinking ones?
""", [
                Opt("It is faster.",
                    why="The number of moves is the same in any order: each pointer ends where "
                        "it must."),
                Opt("Shrinking first can invert the window (`L > R + 1`), so counts of elements "
                    "that were never added go below zero; code that assumes `cnt ≥ 0` breaks.",
                    correct=True,
                    why="Right. From `[0, 0]` to `[5, 5]`, shrinking first removes positions 1..4 "
                        "before they were ever added. Growing first keeps `L ≤ R + 1` at every "
                        "step, so every count is a real count."),
                Opt("The order does not matter at all.",
                    why="For this simple counter the negative counts happen to cancel out. Any "
                        "structure indexed by a count (`freq[cnt[x]]`, used for 'values seen "
                        "exactly k times') reads index −1. Use the safe order always."),
            ]),
            MCQ(r"""
Values go up to 10^9, so `cnt` cannot be an array indexed by value. What should you do?
""", [
                Opt("Use `map<int, int> cnt`; it is a little slower.",
                    why="Not a little. Every one of the ~10^8 moves becomes a tree lookup. "
                        "Measured on a random large test: 10 s, against 0.2 s with an array."),
                Opt("Compress the values to `0..m−1` once (sort, `unique`, `lower_bound`) and "
                    "keep `cnt` as an array.", correct=True,
                    why="Right. One O(n log n) step up front, and every move stays an array "
                        "access."),
                Opt("Use `vector<int> cnt(1000000001)`.",
                    why="4 GB of memory. Only the relative order and equality of values "
                        "matters here, which is exactly what compression keeps."),
            ]),
            Try("distinct_values", note="Mo's order with the odd-even trick, compressed values, "
                "answers printed in input order."),
        ]),
        Part("What a window can count", [
            Say(r"""
Mo's algorithm works for any question where you can update the answer in O(1) when one
element enters or leaves the window. Here is one whose answer is not a sum over positions
at all: count the pairs `i < j` in `[l, r]` with `c_i = c_j` (two socks of the same
colour).
"""),
            Short(r"""
The window holds colours `[1, 2, 1, 1]`, so it has 3 equal pairs. Another sock of
colour 1 enters. By how much does the number of pairs grow?
""", accept=["3", "+3"], placeholder="a number",
                explain=r"""
It pairs with each of the 3 ones already inside: `pairs += cnt[x]; cnt[x]++;` (now 6).
Leaving is the mirror, in the opposite order: `cnt[x]--; pairs -= cnt[x];`, so the
leaving sock is not counted as pairing with itself.
"""),
            Numeric(r"""
With `n = 10^5` socks all of one colour and the query `[1, n]`, how many pairs?
""", answer=4999950000,
                hint="`n(n − 1)/2`.",
                explain=r"""
`10^5 · 99999 / 2 = 4,999,950,000`, more than twice what an `int` holds. Both the running
count and the stored answers must be `long long`.
"""),
            MCQ(r"""
Which of these fits Mo's algorithm as it stands, with O(1) add and remove?
""", [
                Opt("The largest value in `[l, r]`.",
                    why="Adding is O(1) (compare with the current max), but when the maximum "
                        "leaves, which value is the new one? That needs a multiset, O(log n) per "
                        "move (or a variant called rollback Mo's)."),
                Opt("How many values appear exactly twice in `[l, r]`.", correct=True,
                    why="Yes. On add, a count going 1 → 2 adds one and 2 → 3 removes one; "
                        "remove is the mirror. Both are O(1)."),
                Opt("Range sums, with point updates between the queries.",
                    why="Mo's reorders the queries, so the updates would apply in the wrong "
                        "order. (A heavier variant adds time as a third coordinate.)"),
                Opt("Queries that each depend on the previous answer.",
                    why="Then you cannot read the next query before answering this one, so "
                        "there is nothing to reorder."),
            ]),
            Try("matching_socks", note="Mo's again, with a different add/remove, and a `long long` "
                "answer."),
        ]),
        Part("Sweeping instead: offline with a Fenwick tree", [
            Say(r"""
Back to distinct values. Mo's does about 10^8 moves; there is also an O((n + q) log n)
method, offline too. Sort the queries by right end and sweep `r` from 1 to `n`,
answering every query with right end `r` as you pass it. The question is what to store
about positions `1..r` so that the query `[l, r]`, for *any* `l`, becomes one Fenwick
range sum.
"""),
            Reflect(r"""
Fix `r`. You want a 0/1 mark on each position `i ≤ r` such that for every `l`, the marks
in `[l, r]` add up to the number of distinct values in `a[l..r]`. Which position of each
value should carry its mark?
""", answer=r"""
The last occurrence of the value at or before `r`. A value appears in `a[l..r]` exactly
when that last occurrence is `≥ l`, so it puts exactly one mark inside `[l, r]` if it
appears there and none otherwise. As `r` advances to a value last seen at `p`, move the
mark: clear `p`, set `r`. Both are Fenwick point updates, and each query is two prefix
sums.
"""),
            MCQ(r"""
Why not mark the *first* occurrence of each value instead?
""", [
                Opt("It works too; it is a matter of taste.",
                    why="`a = [3, 1, 3]`, query `[2, 3]`: the first 3 is at position 1, outside the "
                        "range, so only the 1 is counted. Answer 1, should be 2."),
                Opt("The first occurrence can lie before `l` while the value still appears in "
                    "`[l, r]`, so that value would be missed.", correct=True,
                    why="Right. The last occurrence up to `r` is the only one guaranteed to be "
                        "inside `[l, r]` whenever any occurrence is."),
                Opt("Fenwick trees can only be updated at the end.",
                    why="A Fenwick tree updates any position in O(log n)."),
            ]),
            Short(r"""
`a = [3, 1, 3, 2, 1]` (positions 1..5). After sweeping up to `r = 5`, which positions
carry a mark? Type the five marks as 0s and 1s.
""", accept=["0 0 1 1 1", "00111", "0,0,1,1,1"], placeholder="five 0/1 marks",
                explain=r"""
The last 3 is at position 3, the last 2 at 4, the last 1 at 5: `0 0 1 1 1`. The query
`[2, 5]` sums to 3 (values 1, 3, 2), and `[4, 5]` to 2. Earlier, at `r = 3`, the marks
were `0 1 1`: the mark of 3 had just moved from position 1 to 3.
"""),
            Say(r"""
The sweep, with `a` compressed so `last` can be an array (0 = not seen yet):

```cpp
for (int r = 1; r <= n; r++) {
    if (last[a[r]]) update(last[a[r]], -1);   // the older copy stops counting
    update(r, +1);
    last[a[r]] = r;
    for (auto [l, k] : at[r]) ans[k] = sum(r) - sum(l - 1);
}
```

About 2 updates per position and 2 prefix sums per query, each ~18 steps: roughly 10^7
steps in all, a tenth of Mo's.
"""),
            MCQ(r"""
A new problem: `q` questions `(l, r, x)`, each asking how many `a_i ≤ x` with
`l ≤ i ≤ r`; `n, q ≤ 2·10^5`, no updates. Sorting by `r` does not help here. What do you
sort by?
""", [
                Opt("Sort by `l` and sweep `l` instead.",
                    why="Sweeping either endpoint leaves the condition on values untouched: the "
                        "Fenwick tree would still count every element in `[l, r]`, whatever "
                        "its value."),
                Opt("Sort the array once and binary search for `x`.",
                    why="Sorting forgets positions, and the count must be restricted to `[l, r]`."),
                Opt("Sort questions by `x` and elements by value; sweep upwards, switching on each "
                    "element's position once its value is ≤ the current `x`, and answer with a "
                    "Fenwick range sum over `[l, r]`.", correct=True,
                    why="Right. When a question is answered, the switched-on positions are exactly "
                        "the elements ≤ `x`, so a range sum counts those inside `[l, r]`. "
                        "O((n + q) log n)."),
                Opt("Mo's algorithm, with a Fenwick tree over values inside the window.",
                    why="Correct, but every move now costs a Fenwick update: about 1.2·10^8 "
                        "moves times 18. The sweep is O((n + q) log n)."),
            ], explain=r"""
The general move: pick the coordinate the condition is about (the right end, a value, a
time), sort both the data and the queries by it, and sweep, so that "the data that
qualifies" only ever grows.
"""),
            MCQ(r"""
In that sweep, some element equals the current question's `x`. What must happen first?
""", [
                Opt("Answer the question, then switch on the elements equal to `x`.",
                    why="Then the question counts only elements `< x`. The sample of the next "
                        "problem has two parcels weighing exactly the `x` of a question."),
                Opt("Switch on every element with value ≤ `x`, then answer.", correct=True,
                    why="Right: `while (p < n && val[p] <= x) switch_on(p++);` before the answer. "
                        "The condition says 'at most', so ties count."),
                Opt("It does not matter, ties are rare.",
                    why="With values up to 10^9 random ties are rare, but tests are not random: "
                        "`x` is often exactly an element's value."),
            ]),
            Try("light_parcels", note="Offline: sort by weight, sweep, Fenwick over positions. "
                "Mind the ties."),
            MCQ(r"""
A problem ends with: "queries are encoded: the real `l` and `r` are `l' xor last` and
`r' xor last`, where `last` is the previous answer". What does that do to this lesson's
tools?
""", [
                Opt("Nothing: decode the queries first and proceed.",
                    why="You cannot decode query `k` before you have answered query `k − 1`. The "
                        "order is fixed by the input."),
                Opt("It forces online answering: Mo's and the sweeps are out, but blocks still "
                    "work, since they answer each query as it arrives.", correct=True,
                    why="Right. Setters encode queries exactly to rule out offline tricks. "
                        "Blocks, segment trees and persistent structures still work."),
                Opt("It only makes the input harder to parse.",
                    why="The xor is the point: it makes answering in any order but the input's "
                        "impossible."),
            ]),
            Reflect(r"""
Two offline tools, one online one. When do you reach for Mo's algorithm, when for a sweep
with a Fenwick tree, and when for blocks?
""", answer=r"""
A sweep needs each answer to be a sum over positions of marks you can maintain as the sweep
coordinate moves (the last occurrence of a value, an element under the line); then it is
O((n + q) log n) and usually the fastest. Mo's needs only O(1) add and remove on a window,
so it handles answers that do not split by position (equal pairs, values seen exactly k
times), at O((n + q)√n). Both need all queries up front. When updates are interleaved or
queries are forced online, blocks answer each one as it comes, at O(√n) each.
"""),
        ]),
    ],
    problems=[COLD_SPOTS, DISTINCT, SOCKS, LIGHT_PARCELS],
    cards=[
        Card(r"""Square-root decomposition: cost of a range query with blocks of size `B`, and the best `B`?""",
             r"""About `n/B` whole blocks plus up to `2B` elements in the two partial pieces. Balance the terms: `B ≈ √n`, O(√n) per query."""),
        Card(r"""The balance argument for choosing a block size?""",
             r"""If one cost grows like `B` and the other like `n/B`, their product is fixed, so the sum is smallest when they are equal: `B = √n`. Weight each term by how often it is paid."""),
        Card(r"""Why does a point update in a block-minimum structure cost O(B), not O(1)?""",
             r"""The replaced value may have been the block's minimum and min has no inverse, so the block is rescanned. `bmin = min(bmin, x)` is wrong when `x` is larger."""),
        Card(r"""Blocks in C++: how many blocks, and what special case does a query need?""",
             r"""`(n + B - 1) / B` blocks (ceiling). When `l / B == r / B`, scan `l..r` directly; the piece loops would read outside the range."""),
        Card(r"""Mo's algorithm: the query order?""",
             r"""Sort queries by `(l / B, r)`, move a window `[L, R]` one element at a time between consecutive queries, store answers by index, print in input order."""),
        Card(r"""Mo's algorithm: why O((n + q)√n)?""",
             r"""Right pointer: monotone within each of the `n/B` blocks, so `n^2/B`. Left pointer: at most `B` per query, so `qB`. With `B = n/√q` both are `n√q`."""),
        Card(r"""The odd-even trick in Mo's algorithm?""",
             r"""In odd blocks sort `r` descending, so the right pointer sweeps up and then back down instead of rewinding at every block change: `(bx & 1) ? R[x] > R[y] : R[x] < R[y]`."""),
        Card(r"""In Mo's main loop, which moves come first, and why?""",
             r"""The growing ones (`R++`, `L--`), then the shrinking ones. The window never inverts, so no count goes negative."""),
        Card(r"""Mo's algorithm with values up to 10^9: how do you count?""",
             r"""Compress the values to `0..m−1` (sort, unique, lower_bound) and use an array. A `map` makes each of ~10^8 moves a tree lookup (measured: 10 s vs 0.2 s)."""),
        Card(r"""Distinct values in `[l, r]` in O((n + q) log n)?""",
             r"""Sort queries by `r`, sweep `r`, keep a Fenwick tree with a 1 at the last occurrence of each value so far (clear the previous one). Answer = sum over `[l, r]`."""),
        Card(r"""Count `a_i ≤ x` for `i` in `[l, r]`, many static queries?""",
             r"""Offline: sort queries by `x` and elements by value; switch on positions with value ≤ `x` (ties included) in a Fenwick tree over positions; answer = range sum."""),
        Card(r"""What rules out Mo's algorithm and offline sweeps?""",
             r"""Online queries (e.g. encoded with the previous answer) and updates interleaved with queries. Blocks and trees still work."""),
    ],
)
