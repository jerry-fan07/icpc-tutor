from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _values(rng, n, x, lo, hi):
    return f"{n} {x}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _two_small(rng):
    n = rng.randint(1, 10)
    return _values(rng, n, rng.randint(2, 40), 1, 20)


def _two_planted(rng, n, vmax):
    """Random values plus one planted pair, so a solution exists. The pair's values stay
    at most 5·10^8 so that x = a_i + a_j respects x ≤ 10^9."""
    a = [rng.randint(1, vmax) for _ in range(n)]
    i, j = rng.sample(range(n), 2)
    a[i] = rng.randint(1, min(vmax, 5 * 10**8))
    a[j] = rng.randint(1, min(vmax, 5 * 10**8))
    return f"{n} {a[i] + a[j]}\n" + " ".join(map(str, a)) + "\n"


def _two_impossible(rng, n):
    """Even values and an odd target: no pair exists, the worst case for trying pairs."""
    a = [2 * rng.randint(1, 5 * 10**8 - 1) for _ in range(n)]
    return f"{n} {2 * rng.randint(1, 5 * 10**8 - 1) - 1}\n" + " ".join(map(str, a)) + "\n"


def _sums_small(rng):
    n = rng.randint(1, 12)
    return _values(rng, n, rng.randint(1, 15), 1, 5)


def _list(rng, n, lo, hi, head=None):
    first = str(n) if head is None else f"{n} {head}"
    return first + "\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _all_distinct(rng, n, head=None):
    v = rng.sample(range(1, 10**9 + 1), n)
    first = str(n) if head is None else f"{n} {head}"
    return first + "\n" + " ".join(map(str, v)) + "\n"


def _distinct_small(rng):
    n = rng.randint(1, 10)
    return _list(rng, n, 1, 5, head=rng.randint(1, n))


# ----------------------------------------------------------------------- checker
def _check_two(inp, expected, got):
    tok = inp.split()
    n, x = int(tok[0]), int(tok[1])
    a = tok[2:2 + n]
    e, g = expected.split(), got.split()
    if e and e[0].upper() == "IMPOSSIBLE":
        if len(g) == 1 and g[0].upper() == "IMPOSSIBLE":
            return True, ""
        return False, "no two values add up to x here: expected IMPOSSIBLE"
    if len(g) == 1 and g[0].upper() == "IMPOSSIBLE":
        return False, "a valid pair exists, but you printed IMPOSSIBLE"
    if len(g) != 2:
        return False, f"expected two positions, found {len(g)} tokens"
    i, j = int(g[0]), int(g[1])
    if not (1 <= i <= n and 1 <= j <= n):
        return False, f"positions must be between 1 and {n}"
    if i == j:
        return False, f"you used position {i} twice; the two positions must differ"
    s = int(a[i - 1]) + int(a[j - 1])
    if s != x:
        return False, f"a[{i}] + a[{j}] = {s}, not {x}"
    return True, ""


# --------------------------------------------------------------------- problems
SUM_TWO = Problem(
    id="sum_two_values",
    title="Sum of Two Values",
    difficulty="easy",
    source="CSES 1640 - Sum of Two Values",
    complexity="O(n log n)",
    statement=r"""
You are given `n` integers and a target `x`. Find two values at **different** positions whose
sum is exactly `x`.
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 2·10^5, 1 ≤ x ≤ 10^9).

The second line has `n` integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print two positions `i` and `j` (1-based, `i ≠ j`) with a_i + a_j = x. If there are several
answers, print any of them. If there is none, print `IMPOSSIBLE`.
""",
    samples=[
        Test("4 8\n2 7 5 1\n", "2 4\n", note="`7 + 1 = 8`. Any valid pair is accepted, in either order."),
        Test("3 10\n1 2 3\n", "IMPOSSIBLE\n"),
        Test("2 8\n4 4\n", "1 2\n", note="The same value twice is fine, the same position twice is not."),
    ],
    tests=[
        Test("1 2\n1\n"),
        Test("3 6\n3 1 5\n"),
        Test("5 1000000000\n500000000 1 999999999 3 500000000\n"),
        Test("4 2\n1 1 1 1\n"),
        Test("3 4\n2 5 7\n"),
    ],
    gens=[
        Gen("small random", _two_small, 15),
        Gen("medium, a pair exists", lambda rng: _two_planted(rng, 2000, 10**9), 2),
        Gen("medium, impossible", lambda rng: _two_impossible(rng, 2000), 1),
        Gen("max size, a pair exists", lambda rng: _two_planted(rng, 200000, 10**9), 1, large=True),
        Gen("max size, impossible", lambda rng: _two_impossible(rng, 200000), 1, large=True),
    ],
    checker=_check_two,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;
    cin >> n >> x;
    vector<pair<long long, int>> v(n);        // {value, original position}
    for (int i = 0; i < n; i++) {
        cin >> v[i].first;
        v[i].second = i + 1;
    }
    sort(v.begin(), v.end());
    // invariant: if some pair adds up to x, one lies inside [l, r]
    int l = 0, r = n - 1;
    while (l < r) {
        long long s = v[l].first + v[r].first;
        if (s == x) {
            cout << v[l].second << ' ' << v[r].second << '\n';
            return 0;
        }
        if (s < x) l++;                       // v[l] is too small even for the largest partner
        else r--;                             // v[r] is too big even for the smallest partner
    }
    cout << "IMPOSSIBLE\n";
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
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] + a[j] == x) {
                cout << i + 1 << ' ' << j + 1 << '\n';
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
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    for (int i = 0; i < n; i++)               // every pair
        for (int j = i + 1; j < n; j++)
            if (a[i] + a[j] == x) {
                cout << i + 1 << ' ' << j + 1 << '\n';
                return 0;
            }
    cout << "IMPOSSIBLE\n";
}
""",
    hints=[
        r"""Sort the values (remembering where each came from). Put one index at the smallest value
and one at the largest. If their sum is too small, which of the two can never be part of an
answer?""",
        r"""Too small: the smallest value is useless even with the largest partner, so `l++`. Too
big: `r--`. Sort `pair{value, position}` so the positions survive the sort.""",
    ],
    editorial=r"""
Sort pairs `(value, original position)` and keep `l` at the smallest remaining value and `r`
at the largest. If `a[l] + a[r] < x`, then `a[l]` plus anything still in range is at most
`a[l] + a[r] < x`, so `a[l]` is in no solution: `l++`. Symmetrically, a sum above `x` rules
out `a[r]`: `r--`. The invariant "if a solution exists, one lies inside `[l, r]`" survives
every step, so when the pointers meet there is none. Each step moves a pointer inward, so at
most `n − 1` steps after the O(n log n) sort.

Traps: printing positions in the *sorted* array (keep the original index in the pair), using
the same element twice (`l < r`, not `l <= r`), and looking positions up with `find` or a
value-to-index map, which returns the same position twice when the two values are equal.
Trying all pairs is 2·10^10 steps when the answer is `IMPOSSIBLE`.
""",
)

SUBARRAY_SUMS = Problem(
    id="subarray_sums",
    title="Subarray Sums I",
    difficulty="easy",
    source="CSES 1660 - Subarray Sums I",
    complexity="O(n)",
    statement=r"""
Given an array of `n` **positive** integers, count the contiguous subarrays whose sum is
exactly `x`.
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 2·10^5, 1 ≤ x ≤ 10^9).

The second line has `n` integers a_1, ..., a_n (1 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print one integer: the number of subarrays with sum `x`.
""",
    samples=[
        Test("5 7\n2 4 1 2 7\n", "3\n", note="`2 4 1`, `4 1 2` and `7`."),
    ],
    tests=[
        Test("1 1\n1\n"),
        Test("1 5\n3\n"),
        Test("4 1000000000\n1000000000 1000000000 1000000000 1000000000\n"),
        Test("10 3\n1 1 1 1 1 1 1 1 1 1\n"),
        Test("3 1000000000\n999999999 1 999999999\n"),
    ],
    gens=[
        Gen("small random", _sums_small, 15),
        Gen("medium random", lambda rng: _values(rng, 3000, rng.randint(1, 3000), 1, 10), 2),
        Gen("max size, all ones", lambda rng: f"200000 100000\n" + " ".join(["1"] * 200000) + "\n", 1, large=True),
        Gen("max size, target never reached", lambda rng: _values(rng, 200000, 10**9, 1, 3), 1, large=True),
        Gen("max size, big values", lambda rng: _values(rng, 200000, rng.randint(10**8, 10**9), 1, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    long long sum = 0, count = 0;             // sum of the window a[l..r]
    int l = 0;
    for (int r = 0; r < n; r++) {
        sum += a[r];
        while (sum > x) sum -= a[l++];        // l only moves right: n steps in total
        if (sum == x) count++;                // positive values: at most one l per r
    }
    cout << count << '\n';
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
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    long long count = 0;
    for (int l = 0; l < n; l++) {
        long long s = 0;
        for (int r = l; r < n; r++) {
            s += a[r];
            if (s == x) count++;
        }
    }
    cout << count << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long x;
    cin >> n >> x;
    vector<long long> a(n);
    for (auto& v : a) cin >> v;
    long long count = 0;
    for (int l = 0; l < n; l++) {             // every start, extended until too big
        long long s = 0;
        for (int r = l; r < n; r++) {
            s += a[r];
            if (s == x) count++;
            if (s > x) break;
        }
    }
    cout << count << '\n';
}
""",
    hints=[
        r"""All values are positive. For a fixed right end `r`, the sums of `a[l..r]` shrink as
`l` grows. And when `r` moves right, can the best `l` move left?""",
        r"""Keep a window `[l, r]` and its sum. Add `a[r]`; while the sum is above `x`, remove
`a[l]` and advance `l`; then count if the sum equals `x`.""",
    ],
    editorial=r"""
Keep a window `a[l..r]` and its sum. For each new right end, add `a[r]`, then drop elements
from the left while the sum exceeds `x`. Because every value is positive, a window that is too
big stays too big when it is extended to the right, so `l` never has to move back, and for
each `r` at most one `l` gives exactly `x` (sums strictly decrease as `l` grows). Each index
enters the window once and leaves at most once: O(n) in total, even though the inner loop
sometimes runs many times in one step.

The approach from algo01, prefix sums plus a hash map, also works and is needed when values
can be negative. The start-by-start scan with an early break is still O(n^2) when the values
are small and the target is large: one hidden test has 2·10^5 ones and `x = 10^5`.
""",
)

PLAYLIST = Problem(
    id="playlist",
    title="Playlist",
    difficulty="medium",
    source="CSES 1141 - Playlist",
    complexity="O(n log n)",
    statement=r"""
You are given a playlist of `n` songs, each identified by an integer. What is the longest
stretch of consecutive songs in which no song appears twice?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers k_1, ..., k_n (1 ≤ k_i ≤ 10^9): the song identifiers.
""",
    output=r"""
Print the length of the longest stretch of consecutive songs that are all different.
""",
    samples=[
        Test("8\n1 2 1 3 2 7 4 2\n", "5\n", note="`1 3 2 7 4`."),
    ],
    tests=[
        Test("1\n1000000000\n"),
        Test("5\n7 7 7 7 7\n"),
        Test("5\n1 2 3 4 5\n"),
        Test("6\n1 2 3 1 2 3\n"),
        Test("7\n1000000000 1 1000000000 2 3 4 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _list(rng, rng.randint(1, 12), 1, 6), 15),
        Gen("medium random", lambda rng: _list(rng, 2000, 1, 500), 2),
        Gen("max size, all different", lambda rng: _all_distinct(rng, 200000), 1, large=True),
        Gen("max size, big identifiers", lambda rng: _list(rng, 200000, 1, 10**9), 1, large=True),
        Gen("max size, many repeats", lambda rng: _list(rng, 200000, 1, 1000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> k(n);
    for (auto& v : k) cin >> v;
    // identifiers go up to 1e9: compress them to 0..m-1 so counts fit in a vector
    vector<int> vals = k;
    sort(vals.begin(), vals.end());
    vals.erase(unique(vals.begin(), vals.end()), vals.end());
    for (auto& v : k) v = lower_bound(vals.begin(), vals.end(), v) - vals.begin();

    vector<int> cnt(vals.size(), 0);          // occurrences inside the window
    int l = 0, best = 0;
    for (int r = 0; r < n; r++) {
        cnt[k[r]]++;
        while (cnt[k[r]] > 1) cnt[k[l++]]--;  // shrink until k[r] is unique again
        best = max(best, r - l + 1);
    }
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
    vector<int> k(n);
    for (auto& v : k) cin >> v;
    int best = 0;
    for (int l = 0; l < n; l++)
        for (int r = l; r < n; r++) {
            bool ok = true;
            for (int i = l; i < r && ok; i++)
                if (k[i] == k[r]) ok = false;
            if (!ok) break;
            best = max(best, r - l + 1);
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
    vector<int> k(n);
    for (auto& v : k) cin >> v;
    int best = 0;
    for (int l = 0; l < n; l++) {             // every start, extended until a repeat
        set<int> seen;
        int r = l;
        while (r < n && !seen.count(k[r])) seen.insert(k[r++]);
        best = max(best, r - l);
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""If a stretch has no repeated song, neither does any stretch inside it. So as the right
end moves right, can the best left end ever move left?""",
        r"""Keep counts of the songs in the window. After adding `k[r]`, advance `l` while `k[r]`
occurs twice. Identifiers go up to 10^9: use a `map` (or compress them first).""",
    ],
    editorial=r"""
"No song twice" is preserved by shrinking: every stretch inside a good stretch is good. So for
each right end `r` the good windows are exactly those starting at or after some `l(r)`, and
`l(r)` never decreases as `r` grows. Slide: add `k[r]` to a count map, advance `l` while `k[r]`
has count 2, and record `r − l + 1`. Every song enters and leaves the window at most once:
O(n log n) with a `map`, O(n) with coordinate compression and an array.

Restarting a set at every start position is O(n · answer), about 2·10^10 when all songs are
different. An array indexed by identifier would need 10^9 entries.
""",
)

DISTINCT = Problem(
    id="distinct_values",
    title="Subarray Distinct Values",
    difficulty="medium",
    source="CSES 2428 - Subarray Distinct Values",
    complexity="O(n log n)",
    statement=r"""
Given an array of `n` integers, count the contiguous subarrays that contain **at most** `k`
distinct values.
""",
    input=r"""
The first line has `n` and `k` (1 ≤ k ≤ n ≤ 2·10^5).

The second line has `n` integers x_1, ..., x_n (1 ≤ x_i ≤ 10^9).
""",
    output=r"""
Print one integer: the number of subarrays with at most `k` distinct values.
""",
    samples=[
        Test("5 2\n1 2 3 1 1\n", "10\n"),
    ],
    tests=[
        Test("1 1\n5\n"),
        Test("4 1\n2 2 2 2\n"),
        Test("4 4\n1 2 3 4\n"),
        Test("5 1\n1 2 1 2 1\n"),
        Test("6 2\n1000000000 1 1000000000 1 7 7\n"),
    ],
    gens=[
        Gen("small random", _distinct_small, 15),
        Gen("medium random", lambda rng: _list(rng, 2000, 1, 50, head=rng.randint(1, 40)), 2),
        Gen("max size, k = n", lambda rng: _all_distinct(rng, 200000, head=200000), 1, large=True),
        Gen("max size, k = 1000", lambda rng: _list(rng, 200000, 1, 2000, head=1000), 1, large=True),
        Gen("max size, big values", lambda rng: _list(rng, 200000, 1, 10**9, head=rng.randint(1, 100)), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<int> x(n);
    for (auto& v : x) cin >> v;
    vector<int> vals = x;                     // compress values to 0..m-1
    sort(vals.begin(), vals.end());
    vals.erase(unique(vals.begin(), vals.end()), vals.end());
    for (auto& v : x) v = lower_bound(vals.begin(), vals.end(), v) - vals.begin();

    vector<int> cnt(vals.size(), 0);          // occurrences inside the window
    int distinct = 0;                         // values with cnt > 0
    long long total = 0;                      // up to n(n+1)/2 = 2e10
    int l = 0;
    for (int r = 0; r < n; r++) {
        if (cnt[x[r]]++ == 0) distinct++;
        while (distinct > k) {                // too many distinct: shrink from the left
            if (--cnt[x[l]] == 0) distinct--;
            l++;
        }
        total += r - l + 1;                   // windows [l..r], [l+1..r], ..., [r..r]
    }
    cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, k;
    cin >> n >> k;
    vector<int> x(n);
    for (auto& v : x) cin >> v;
    long long total = 0;
    for (int l = 0; l < n; l++) {
        set<int> s;
        for (int r = l; r < n; r++) {
            s.insert(x[r]);
            if ((int)s.size() <= k) total++;
        }
    }
    cout << total << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<int> x(n);
    for (auto& v : x) cin >> v;
    long long total = 0;
    for (int l = 0; l < n; l++) {             // every start, extended while still valid
        set<int> s;
        for (int r = l; r < n; r++) {
            s.insert(x[r]);
            if ((int)s.size() > k) break;
            total++;
        }
    }
    cout << total << '\n';
}
""",
    hints=[
        r"""Removing elements from a window never adds distinct values. For a fixed right end `r`,
if `l(r)` is the smallest valid left end, how many valid subarrays end at `r`?""",
        r"""`r − l + 1` of them. Slide the window with a count map; a value stops counting as
distinct only when its count reaches 0 (erase it then, so `size()` stays honest).""",
        r"""The answer reaches n(n+1)/2 ≈ 2·10^10: `long long`.""",
    ],
    editorial=r"""
"At most `k` distinct values" is preserved by shrinking a window, so for each right end `r`
the valid windows are `[l..r], [l+1..r], ..., [r..r]` for the smallest valid `l`, which never
decreases as `r` grows. Slide with a `map` from value to count: add `x[r]`; while the map has
more than `k` keys, decrement `x[l]`, erasing it when its count hits 0, and advance `l`; then
add `r − l + 1` to the answer. O(n log n).

Traps: `cnt.size()` counts keys with count 0 unless you erase them, the total needs
`long long` (one hidden test has k = n and answer about 2·10^10), and restarting a set at every
left end is O(n^2 log n) when windows are long.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo04",
    title="two pointers & sliding window",
    track="algo",
    order=4,
    summary="Two indices that only move forward: pair sums on sorted data, windows over "
            "positive numbers, longest and counted windows with a count map, the amortised "
            "O(n) argument, and exactly when windows stop working.",
    prereqs=["algo01", "algo03"],
    tags=["two pointers", "sliding window", "amortised analysis", "count map",
          "monotone window"],
    parts=[
        Part("Two values that add up", [
            Say(r"""
A classic warm-up that hides a whole technique. You get `n` integers and a target `x`; find two
values at different positions with sum exactly `x`, or report that there are none. `n ≤ 2·10^5`,
values and `x` up to 10^9, one second.

The first program anyone writes tries every pair.
"""),
            Numeric(r"""
How many pairs does it check in the worst case (no pair works), for `n = 2·10^5`?
""", answer=2e10, rel=0.5, unit="pairs",
                explain=r"""
`n(n − 1)/2 ≈ 2·10^10`: 20 to 200 seconds. The worst case is exactly the `IMPOSSIBLE` one,
which judges always include.
"""),
            Reflect(r"""
With what you already know (sorting, `lower_bound`, hash maps), how would you get under a
second? Then: what does your method still do that feels unnecessary?
""", answer=r"""
Sort, and for each value binary search for `x − a_i`: O(n log n). Or put the values in a hash
map and look up `x − a_i`: O(n) expected (but `unordered_map` can be attacked, cpp05). Both
work. What they still do is search the *whole* array for every value, even though, once the
data is sorted, the partner of a larger value can only be smaller. That leftover structure is
what two pointers exploits: no search at all.
"""),
            Say(r"""
Sort the values. Put `l` at the smallest and `r` at the largest, and look at `a[l] + a[r]`. If
it equals `x`, you are done. If not, one of the two can be thrown away for good, and the
question is which one.
"""),
            MCQ(r"""
`a[l] + a[r] < x`. What can you conclude?
""", [
                Opt("`a[r]` is in no solution: `r--`.",
                    why="`a[r]` may pair with a larger value further right of `l`: in `1 4 6` with "
                        "`x = 10`, `1 + 6 < 10`, but `4 + 6 = 10`."),
                Opt("Nothing yet: `a[l]` must still be tried with every other element.",
                    why="Every other partner of `a[l]` inside the range is at most `a[r]`, so every "
                        "such sum is at most `a[l] + a[r] < x`. There is nothing left to try."),
                Opt("`a[l]` is in no solution: even the largest partner is not enough. `l++`.",
                    correct=True,
                    why="Yes. By the mirror argument, `a[l] + a[r] > x` means `a[r]` is too big even "
                        "for the smallest partner: `r--`."),
                Opt("Both are useless: `l++` and `r--`.",
                    why="Same counterexample: in `1 4 6`, `x = 10`, the 6 is needed."),
            ]),
        ]),
        Part("Why the pointers never move back", [
            Reflect(r"""
State an invariant that justifies this loop, and use it to explain why neither pointer ever
has to move back.
""", answer=r"""
Invariant: *if some pair adds up to `x`, then one such pair lies entirely inside `[l, r]`.* It
is true at the start (the whole array). Each step removes one element that, as just shown, is
in no solution pair with anything still in the range, so it stays true. That is why a pointer
never comes back: everything it passed over was proved useless. When `l` meets `r`, the range
holds fewer than two elements, so there is no pair at all.
"""),
            Short(r"""
Sorted values `1 3 4 6 8 11`, `x = 10`. Run the pointers from both ends. Which two values do
they find?
""", accept=["4 6", "4, 6", "4,6", "6 4", "4 and 6", "4+6"], placeholder="two values",
                explain=r"""
`1 + 11 = 12`, too big: `r--`. `1 + 8 = 9`, too small: `l++`. `3 + 8 = 11`: `r--`.
`3 + 6 = 9`: `l++`. `4 + 6 = 10`: found, after 5 sums.
"""),
            Numeric(r"""
Each step moves `l` right or `r` left. For `n = 2·10^5`, at most how many steps can the loop
take?
""", answer=2e5, rel=0.05, unit="steps",
                explain=r"""
`n − 1`: the gap `r − l` starts at `n − 1` and shrinks by one every step. With the sort, the
whole thing is O(n log n), and the pointer part is O(n): the sort now costs more than the
search.
"""),
            MCQ(r"""
The answer must be the *original* positions (1-based). After sorting, how do you get them?
""", [
                Opt("Print `l + 1` and `r + 1`.",
                    why="Those are positions in the sorted array, not in the input."),
                Opt("Look each value up in the original array with `find`.",
                    why="With equal values it finds the same position twice: `x = 8`, `a = 4 4` "
                        "gives `1 1`, which is not a valid answer."),
                Opt("Sort `pair{value, original position}`; the position travels with the value.",
                    correct=True,
                    why="Yes. Pairs sort by value first, and the index comes along for free."),
                Opt("Keep a `map` from value to position.",
                    why="A map keeps one position per value, so `4 4` again prints the same "
                        "position twice."),
            ]),
            Try("sum_two_values", note="Sort `(value, position)` pairs, move the pointers inward, "
                "`l < r`. The largest hidden test has no answer at all."),
        ]),
        Part("Windows over positive numbers", [
            Say(r"""
The same "never move back" idea works on *contiguous* ranges. Count the subarrays with sum
exactly `x` in an array of `n` **positive** integers (`n ≤ 2·10^5`, values and `x` up to 10^9).

algo01 already solved this with prefix sums and a hash map. Positivity allows something
simpler, and the idea behind it covers questions that hashing cannot answer at all: longest,
shortest, at most.

For each right end `r`, let `l(r)` be the smallest `l` such that `a[l..r]` has sum at most
`x`.
"""),
            MCQ(r"""
The right end moves from `r` to `r + 1`. Where can `l(r + 1)` be?
""", [
                Opt("Anywhere: it has to be searched for again.",
                    why="A window `a[l..r]` that was too big stays too big when `a[r+1] > 0` is "
                        "added, so the search can start where the last one stopped."),
                Opt("At `l(r)` or to its right: the left end never moves back.", correct=True,
                    why="Yes. Every window starting before `l(r)` was already above `x` at `r`, and "
                        "adding a positive value only makes it bigger."),
                Opt("Always exactly `l(r) + 1`.",
                    why="It can stay put (a small `a[r+1]`) or jump several places (a huge one)."),
                Opt("At `l(r)` or to its left.",
                    why="That would mean a window that was too big became small enough by adding a "
                        "positive number."),
            ]),
            Say(r"""
So one pass, with `l` chasing `r`:

```cpp
long long sum = 0, count = 0;
int l = 0;
for (int r = 0; r < n; r++) {
    sum += a[r];
    while (sum > x) sum -= a[l++];
    if (sum == x) count++;
}
```
"""),
            Numeric(r"""
The `while` sits inside the `for`, which looks like O(n^2). Over the whole run, at most how
many times can `l++` execute, for `n = 2·10^5`?
""", answer=2e5, rel=0.05,
                explain=r"""
At most `n`: `l` only moves right and never passes `n`. One iteration of the `for` can run the
`while` many times, but the total over the whole run is at most `n`, so the loop is O(n) in
total. This is **amortised** analysis: charge each `l++` to the element it removes, and every
element is removed at most once.
"""),
            MCQ(r"""
For each `r` the code counts at most one subarray. Why can two different left ends not both
give sum exactly `x` for the same `r`?
""", [
                Opt("Because the window is always as short as possible.",
                    why="Shortness is not the reason. The reason is what happens to the sum as `l` "
                        "moves."),
                Opt("Values are positive, so the sum of `a[l..r]` strictly decreases as `l` grows: "
                    "it passes through `x` at most once.", correct=True,
                    why="Yes. With zeros allowed this breaks: in `0 7` with `x = 7`, both `0 7` and "
                        "`7` sum to 7, and the loop counts only one."),
                Opt("It can happen, but the problem guarantees it does not.",
                    why="No such guarantee is needed: positivity alone rules it out."),
            ]),
            Short(r"""
`a = 2 4 1 2 7`, `x = 7`. How many subarrays sum to exactly 7?
""", accept=["3", "three"], placeholder="a number",
                explain=r"""
`2 4 1`, `4 1 2` and `7`. The window sees them at `r = 2` (window `[0..2]`), `r = 3` (after
dropping the 2) and `r = 4` (after dropping everything but the 7).
"""),
            Try("subarray_sums", note="One pass, `l` chasing `r`. One hidden test has 2·10^5 ones and "
                "`x = 10^5`, which is where 'restart from every `l`' dies."),
        ]),
        Part("The longest good window", [
            Say(r"""
A playlist has `n` songs, each an integer identifier up to 10^9. Find the longest stretch of
consecutive songs with no song repeated. `n ≤ 2·10^5`.

The direct approach: from every start, extend to the right with a set until a song repeats.
"""),
            Numeric(r"""
In the worst case (all songs different), roughly how many set insertions does that make for
`n = 2·10^5`?
""", answer=2e10, rel=0.5, unit="insertions",
                explain=r"""
Each start extends to the end: `n + (n−1) + ... ≈ n^2/2 = 2·10^10`, each an O(log n) set
operation. Every start re-inserts almost the same songs as the previous start: the waste the
window will remove.
"""),
            MCQ(r"""
What property of "no song twice" makes a sliding window work here?
""", [
                Opt("The identifiers are at most 10^9.",
                    why="The size of the values decides the *container* (map versus array), not "
                        "whether the window works."),
                Opt("If a stretch has no repeated song, neither does any stretch inside it.",
                    correct=True,
                    why="Yes: goodness survives shrinking. So for each right end, the good windows "
                        "are all those starting at or after some `l(r)`, and `l(r)` never "
                        "decreases."),
                Opt("Longer stretches are always better.",
                    why="That is the objective, not a property of the constraint. The window needs "
                        "to know which stretches are *allowed*."),
                Opt("Every stretch shorter than the answer is good.",
                    why="False: `7 7` is short and bad. The property is about *containment*, not "
                        "length."),
            ]),
            Reflect(r"""
State the general rule: when does "longest window satisfying a condition" have a
sliding-window solution, and what does the loop look like?
""", answer=r"""
The condition must be preserved by shrinking: if `[l, r]` is good, so is every window inside
it. Then for each `r` the good windows ending at `r` are exactly those starting at or after
some `l(r)`, and `l(r)` never decreases (a window good at `r + 1`, cut back to `r`, is good at
`r`). One pass: advance `r`, then advance `l` until the window is good again, and record
`r − l + 1`. Sum of positive values at most `x`, no repeats and at most `k` distinct values
all qualify.
"""),
            Short(r"""
Playlist `1 2 1 3 2 7 4 2`. How long is the longest stretch without a repeat?
""", accept=["5", "five"], placeholder="a length",
                explain=r"""
`1 3 2 7 4`, positions 3 to 7. Adding the final `2` repeats the `2` at position 5, and the
window has to drop everything up to it.
"""),
            MCQ(r"""
The window keeps a count for every identifier in it. Identifiers go up to 10^9. Which
container?
""", [
                Opt("`vector<int> cnt(1000000001)`.",
                    why="That is 4 GB of memory, far over any limit, for 2·10^5 distinct values at "
                        "most."),
                Opt("A `map<int, int>`, or coordinate-compress the identifiers (cpp06) and use a "
                    "`vector` of size `n`.", correct=True,
                    why="Yes. `map` costs O(log n) per step, which is fine here; compression makes "
                        "it O(1) after one sort."),
                Opt("A `set<int>` of the songs in the window.",
                    why="A set tells you whether a song is in the window, which is enough here, "
                        "but not *how many times*: when the next problem needs counts, a set "
                        "cannot shrink the window correctly."),
            ], explain=r"""
Another way to slide: remember the last position of every song, and when `k[r]` was last seen
at `p ≥ l`, jump `l` straight to `p + 1`.
"""),
            Try("playlist", note="Count map, shrink while the new song is doubled, record "
                "`r − l + 1`."),
        ]),
        Part("Counting windows", [
            Say(r"""
Windows can also be counted. Count the subarrays that contain **at most `k`** distinct values.
`n ≤ 2·10^5`, values up to 10^9.

"At most `k` distinct" survives shrinking, so the same loop finds, for every `r`, the smallest
valid left end `l(r)`.
"""),
            MCQ(r"""
Given `l(r)`, how many valid subarrays end at `r`?
""", [
                Opt("1: the window `[l(r), r]` itself.",
                    why="Every window inside a valid window is valid, including those that start "
                        "later."),
                Opt("`r − l(r) + 1`: the windows starting at `l(r), l(r)+1, ..., r`.",
                    correct=True,
                    why="Yes. Adding this for every `r` counts each valid subarray exactly once, by "
                        "its right end."),
                Opt("All subarrays of `[l(r), r]`: `(r − l + 1)(r − l + 2) / 2`.",
                    why="Those that end before `r` were already counted at their own right end: "
                        "this counts them again and again."),
            ]),
            MCQ(r"""
The window keeps `map<int, int> cnt`, and the number of distinct values is `cnt.size()`. When
the left end leaves, the code does `cnt[x[l]]--; l++;`. What is wrong?
""", [
                Opt("Nothing.",
                    why="A key whose count reached 0 is still a key: `cnt.size()` keeps counting it "
                        "as a distinct value."),
                Opt("`cnt.size()` never shrinks: a value whose count drops to 0 must be erased.",
                    correct=True,
                    why="Yes: `if (--cnt[x[l]] == 0) cnt.erase(x[l]);`. The window then shrinks too "
                        "far and the count comes out too small. (Or keep your own `distinct` "
                        "counter, decremented exactly when a count hits 0.)"),
                Opt("It should decrement `cnt[x[r]]` instead.",
                    why="The element leaving the window is `x[l]`."),
            ]),
            Short(r"""
`x = 1 2 3 1 1`, `k = 2`. How many subarrays have at most 2 distinct values?
""", accept=["10", "ten"], placeholder="a number",
                hint="For each `r`, find `l(r)` and add `r − l(r) + 1`.",
                explain=r"""
The windows ending at each `r` contribute `1, 2, 2, 2, 3`: at `r = 2` the 3 forces `l` past
the 1, and at `r = 4` the window `3 1 1` is valid. Total 10.
"""),
            Numeric(r"""
With `k = n = 2·10^5`, every subarray counts. How many is that?
""", answer=20000100000, rel=0.01,
                explain=r"""
`n(n + 1)/2 = 20,000,100,000 ≈ 2·10^10`, ten times what an `int` holds. The window indices
fit in `int`; the total does not.
"""),
            MCQ(r"""
And subarrays with **exactly** `k` distinct values?
""", [
                Opt("The same loop, counting only windows with exactly `k` distinct values.",
                    why="'Exactly `k`' does not survive shrinking (drop an element and you may have "
                        "`k − 1`), so the valid windows ending at `r` do not form one block."),
                Opt("`atMost(k) − atMost(k − 1)`.", correct=True,
                    why="Yes: every subarray with exactly `k` is counted by the first and not the "
                        "second. Two windows, same code. On `1 2 3 1 1` with `k = 2`: `10 − 6 = 4`."),
                Opt("It needs a segment tree.",
                    why="Nothing that heavy: subtract two sliding-window counts."),
            ]),
            Try("distinct_values", note="`r − l + 1` per right end, erase keys that hit 0, "
                "`long long` total."),
        ]),
        Part("When windows fail", [
            Say(r"""
Every window in this lesson relied on one fact: a good window stays good when it shrinks (or,
for two sums, the sorted order tells you which end is useless). Take the fact away and the
technique goes with it.
"""),
            MCQ(r"""
Longest subarray with sum at most `x`, but values may be **negative**. Does the window still
work?
""", [
                Opt("Yes, it just takes longer.",
                    why="Speed is not the issue: the pointer moves are no longer justified at all."),
                Opt("Yes, if you shrink only while the sum is above `x`.",
                    why="With negatives, shrinking can make the sum go *up*: dropping a −10 from the "
                        "left raises it by 10. There is no safe moment to stop."),
                Opt("No: with `x = 0`, the window `5 −10` (sum −5) is good but the window inside "
                    "it, `5`, is not, so good windows are not closed under shrinking.",
                    correct=True,
                    why="Right. With negatives, work with prefix sums instead (algo01): 'sum "
                        "exactly `x`' is a hash-map lookup, 'longest with sum ≤ `x`' needs sorted "
                        "prefixes and binary search."),
            ]),
            Reflect(r"""
Two pointers also works on pairs: "count pairs `i < j` with `a_i + a_j ≤ x`" in O(n log n).
Sketch it, and say what plays the role of "never moving back".
""", answer=r"""
Sort. Put `l` at the smallest and `r` at the largest. If `a[l] + a[r] ≤ x`, then `a[l]` pairs
with every element from `l + 1` to `r` (all at most `a[r]`): add `r − l` and move `l` right.
Otherwise `a[r]` is too big for every remaining partner (all at least `a[l]`): move `r` left.
Each element is discarded once, for the same reason as in Sum of Two Values: whatever a pointer
passes over has been fully accounted for.
"""),
            MCQ(r"""
Sum of **three** values equal to `x`, with `n ≤ 5000`. What is the standard plan?
""", [
                Opt("Three nested loops: 2·10^10 triples, fine with `-O2`.",
                    why="`n^3 / 6 ≈ 2·10^10`: minutes, not a second."),
                Opt("Sort; fix the first value, then run the two-pointer pair search on the rest: "
                    "O(n^2) = 2.5·10^7.", correct=True,
                    why="Yes (CSES 1641, Sum of Three Values). Each fixed value turns the rest "
                        "into Sum of Two Values."),
                Opt("Two pointers directly, with a third pointer in the middle.",
                    why="A middle pointer has no rule for which way to move: its moves cannot be "
                        "justified the way the outer two are."),
            ], explain=r"""
Two pointers is not a trick for one problem; it is a proof pattern. Whenever you can show that
an index, once passed, is finished with, the pointers only move forward and the work is O(n).
"""),
        ]),
    ],
    problems=[SUM_TWO, SUBARRAY_SUMS, PLAYLIST, DISTINCT],
    cards=[
        Card(r"""Sum of two values on sorted data: the pointer rule?""",
             r"""`l` at the smallest, `r` at the largest. Sum too small: `l++` (a[l] is useless even with the largest partner). Too big: `r--`. Equal: done."""),
        Card(r"""The invariant behind the two-sum pointers?""",
             r"""If some pair adds up to `x`, one lies inside `[l, r]`. Every step discards an element that is in no remaining pair."""),
        Card(r"""How do you keep original positions through a sort?""",
             r"""Sort `vector<pair<value, index>>`: the index travels with the value. `find` or a value-to-index map fail on equal values."""),
        Card(r"""Why is the sliding-window loop `for r { ...; while (...) l++; }` O(n)?""",
             r"""Amortised: `l` only moves right and at most `n` times over the whole run, so all the inner iterations together cost O(n)."""),
        Card(r"""When does a sliding window solve "longest/count windows satisfying P"?""",
             r"""When P survives shrinking: every window inside a good window is good. Then the smallest valid `l` never decreases as `r` grows."""),
        Card(r"""Count subarrays satisfying a shrink-closed condition?""",
             r"""For each `r`, add `r − l + 1` (all windows starting at `l..r` and ending at `r`). The total can reach n(n+1)/2: `long long`."""),
        Card(r"""Count map in a window: when does a value stop counting as distinct?""",
             r"""When its count reaches 0. Erase it then (`if (--cnt[v] == 0) cnt.erase(v);`), or `cnt.size()` stays too big."""),
        Card(r"""Subarrays with exactly `k` distinct values?""",
             r"""`atMost(k) − atMost(k − 1)`, each a sliding window."""),
        Card(r"""Why do sliding windows fail with negative numbers?""",
             r"""Shrinking can increase the sum, so good windows are not closed under shrinking (`5 −10` ≤ 0 but `5` is not). Use prefix sums (algo01)."""),
        Card(r"""Sum of three values, n ≤ 5000?""",
             r"""Sort, fix the first value, two pointers on the rest: O(n^2)."""),
    ],
)
