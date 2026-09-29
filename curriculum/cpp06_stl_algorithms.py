import random as _random

from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
_ALPHA = "abcdefghijklmnopqrstuvwxyz"


def _name(k):
    """Bijective base 26: 1 -> a, 26 -> z, 27 -> aa, ...  Distinct k give distinct names."""
    s = []
    while k > 0:
        k -= 1
        s.append(_ALPHA[k % 26])
        k //= 26
    return "".join(reversed(s))


def _board(rng, n, smax, pmax):
    ids = rng.sample(range(1, 26**7), n)
    rows = [f"{_name(k)} {rng.randint(0, smax)} {rng.randint(0, pmax)}" for k in ids]
    return f"{n}\n" + "\n".join(rows) + "\n"


def _board_equal(rng, n):
    ids = rng.sample(range(1, 26**7), n)
    return f"{n}\n" + "\n".join(f"{_name(k)} 5 500" for k in ids) + "\n"


def _board_small(rng):
    return _board(rng, rng.randint(1, 12), 2, 3)


# a hidden test small enough to be shown when it fails: 40 teams, heavy ties
_TIED_40 = _board(_random.Random(2024), 40, 1, 1)


def _range_queries(rng, n, q, vlo, vhi, wide):
    a = [rng.randint(vlo, vhi) for _ in range(n)]
    out = [f"{n} {q}", " ".join(map(str, a))]
    for _ in range(q):
        if wide:
            l = rng.randint(vlo, vlo + (vhi - vlo) // 10)
            r = rng.randint(vhi - (vhi - vlo) // 10, vhi)
        else:
            l, r = sorted((rng.randint(vlo - 2, vhi + 2), rng.randint(vlo - 2, vhi + 2)))
        out.append(f"{l} {r}")
    return "\n".join(out) + "\n"


def _range_small(rng):
    return _range_queries(rng, rng.randint(1, 12), rng.randint(1, 12), -10, 10, False)


def _heights(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _heights_distinct(rng, n):
    return f"{n}\n" + " ".join(map(str, rng.sample(range(-10**9, 10**9 + 1), n))) + "\n"


def _scores(rng, n, k, hi):
    return f"{n} {k}\n" + " ".join(str(rng.randint(0, hi)) for _ in range(n)) + "\n"


def _scores_small(rng):
    n = rng.randint(1, 12)
    return _scores(rng, n, rng.randint(0, (n - 1) // 2), 20)


def _word(rng, lmax, alpha):
    return "".join(rng.choice(alpha) for _ in range(rng.randint(1, lmax))) + "\n"


# --------------------------------------------------------------------- problems
SCOREBOARD = Problem(
    id="scoreboard",
    title="Freeze the Scoreboard",
    difficulty="medium",
    complexity="O(n log n)",
    statement=r"""
An ICPC contest just ended. Teams are ranked by the number of problems solved (more is
better), then by penalty time (less is better). Two teams with the same number solved
*and* the same penalty share a rank, and on the printed scoreboard they appear in the
order in which they registered.

A team's rank is 1 plus the number of teams strictly better than it (so ties give ranks
like 1, 1, 3). Print the scoreboard.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5), the number of teams.

Then `n` lines follow, in registration order. Each has a team name (1 to 7 lowercase
letters; all names are different), the number of problems solved `s` (0 ≤ s ≤ 15) and
the penalty time `p` (0 ≤ p ≤ 10^6).
""",
    output=r"""
Print `n` lines, from first place to last: the team's rank, a space, and its name.
""",
    samples=[
        Test("6\nzulu 3 250\nbravo 4 400\nalpha 3 250\ndelta 3 180\necho 4 400\nkilo 0 0\n",
             "1 bravo\n1 echo\n3 delta\n4 zulu\n4 alpha\n6 kilo\n",
             note="zulu and alpha tie, and zulu registered first, so zulu is printed first: "
                  "the tie-break is not the name."),
    ],
    tests=[
        Test("1\nsolo 0 0\n"),
        Test("3\nc 15 1000000\nb 15 1000000\na 15 999999\n"),
        Test(_TIED_40),
    ],
    gens=[
        Gen("small random", _board_small, 12),
        Gen("medium, heavy ties", lambda rng: _board(rng, 2000, 2, 5), 3),
        Gen("medium, spread", lambda rng: _board(rng, 2000, 15, 10**6), 2),
        Gen("max size, random", lambda rng: _board(rng, 200000, 15, 3000), 1, large=True),
        Gen("max size, heavy ties", lambda rng: _board(rng, 200000, 3, 3), 1, large=True),
        Gen("max size, everyone tied", lambda rng: _board_equal(rng, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<string> name(n);
    vector<tuple<int, int, int>> key(n);      // (-solved, penalty, registration index)
    for (int i = 0; i < n; i++) {
        int s, p;
        cin >> name[i] >> s >> p;
        key[i] = {-s, p, i};                  // plain tuple order = scoreboard order
    }
    sort(key.begin(), key.end());             // no ties left: the index breaks them all
    int rank = 0;
    for (int pos = 0; pos < n; pos++) {
        auto [ns, p, i] = key[pos];
        if (pos == 0 || get<0>(key[pos - 1]) != ns || get<1>(key[pos - 1]) != p)
            rank = pos + 1;                   // a new (solved, penalty) group starts here
        cout << rank << ' ' << name[i] << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<string> name(n);
    vector<int> s(n), p(n);
    for (int i = 0; i < n; i++) cin >> name[i] >> s[i] >> p[i];
    vector<bool> used(n, false);
    for (int step = 0; step < n; step++) {
        int b = -1;
        for (int i = 0; i < n; i++) {
            if (used[i]) continue;
            if (b == -1 || s[i] > s[b] || (s[i] == s[b] && p[i] < p[b])) b = i;
        }
        used[b] = true;
        int better = 0;
        for (int i = 0; i < n; i++)
            if (s[i] > s[b] || (s[i] == s[b] && p[i] < p[b])) better++;
        cout << better + 1 << ' ' << name[b] << '\n';
    }
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
    vector<string> name(n);
    vector<int> s(n), p(n);
    for (int i = 0; i < n; i++) cin >> name[i] >> s[i] >> p[i];
    vector<int> idx(n);
    iota(idx.begin(), idx.end(), 0);
    sort(idx.begin(), idx.end(), [=](int i, int j) {     // [=]: copies s and p
        if (s[i] != s[j]) return s[i] > s[j];
        if (p[i] != p[j]) return p[i] < p[j];
        return i < j;
    });
    int rank = 0;
    for (int pos = 0; pos < n; pos++) {
        int i = idx[pos], prev = pos ? idx[pos - 1] : -1;
        if (pos == 0 || s[prev] != s[i] || p[prev] != p[i]) rank = pos + 1;
        cout << rank << ' ' << name[i] << '\n';
    }
}
""",
    hints=[
        r"""The order has three keys: solved (descending), penalty (ascending), registration
index (ascending). With the index as the last key, no two teams are equal and plain
`sort` is enough.""",
        r"""Store tuples `{-solved, penalty, i}` and sort them ascending: negating flips the one
key that goes the other way. Or sort indices with a lambda that captures by reference,
`[&]`.""",
        r"""The rank changes only where (solved, penalty) differs from the previous line; then it
becomes the 1-based position.""",
    ],
    editorial=r"""
Sort by the full key: solved descending, penalty ascending, and the registration index
ascending as the final tie-break. Sorting tuples `{-solved, penalty, index}` does exactly
that with the default `<`. Then walk the sorted list; the rank is the 1-based position of
the first team of each (solved, penalty) group. O(n log n).

What costs a verdict here:

- `sort` with a comparator on (solved, penalty) only: `sort` is not stable, and on the
  tests with thousands of ties it scrambles the registration order. `stable_sort` with
  that comparator is correct; so is adding the index as a key.
- `>=` or `<=` in the comparator: undefined behaviour. Here it already reverses the tied
  teams of the sample; with `sort` on the test where all 2·10^5 teams tie, it runs off the
  array and crashes.
- Breaking ties by name, the way most real scoreboards do: the sample.
- Sorting indices with a `[=]` lambda: correct, but every copy of the comparator copies
  both vectors, and `sort` copies its comparator a great many times: 7 to 10 s here on the
  large tests, against 0.05 s with `[&]`.
""",
)

RANGE_COUNT = Problem(
    id="range_count",
    title="Readings in a Band",
    difficulty="easy",
    complexity="O((n + q) log n)",
    statement=r"""
A seismograph stored `n` readings. The analysts ask `q` questions of the form "how many
readings are between `l` and `r`, inclusive?".

Answer every question.
""",
    input=r"""
The first line has `n` and `q` (1 ≤ n, q ≤ 2·10^5).

The second line has the readings a_1, ..., a_n (−10^9 ≤ a_i ≤ 10^9), in no particular
order.

Each of the next `q` lines has two integers `l` and `r` (−10^9 ≤ l ≤ r ≤ 10^9).
""",
    output=r"""
For each question, print the number of readings `x` with `l ≤ x ≤ r`, one per line.
""",
    samples=[
        Test("6 5\n7 3 9 3 1 3\n3 7\n4 6\n-5 100\n9 9\n10 20\n", "4\n0\n6\n1\n0\n",
             note="Both ends are inclusive: the first question counts the three 3s and the 7."),
    ],
    tests=[
        Test("1 3\n0\n0 0\n-1000000000 -1\n1 1000000000\n"),
        Test("5 2\n5 5 5 5 5\n5 5\n-1000000000 1000000000\n"),
        Test("4 3\n-1000000000 1000000000 -1000000000 1000000000\n-1000000000 -1000000000\n1000000000 1000000000\n-999999999 999999999\n"),
    ],
    gens=[
        Gen("small random", _range_small, 14),
        Gen("medium random", lambda rng: _range_queries(rng, 2000, 2000, -50, 50, False), 2),
        Gen("medium, wide values", lambda rng: _range_queries(rng, 2000, 2000, -10**9, 10**9, False), 2),
        Gen("max size, wide questions", lambda rng: _range_queries(rng, 200000, 200000, -10**9, 10**9, True), 1, large=True),
        Gen("max size, random", lambda rng: _range_queries(rng, 200000, 200000, -10**9, 10**9, False), 1, large=True),
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
    sort(a.begin(), a.end());                         // binary search needs sorted data
    while (q--) {
        int l, r;
        cin >> l >> r;
        auto from = lower_bound(a.begin(), a.end(), l);   // first reading >= l
        auto to = upper_bound(a.begin(), a.end(), r);     // first reading >  r
        cout << (to - from) << '\n';
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
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    while (q--) {
        int l, r;
        cin >> l >> r;
        int c = 0;
        for (int x : a) if (l <= x && x <= r) c++;
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
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    while (q--) {
        int l, r;
        cin >> l >> r;
        int c = 0;
        for (int x : a) if (l <= x && x <= r) c++;
        cout << c << '\n';
    }
}
""",
    hints=[
        r"""Sort the readings once. In a sorted array, the readings in `[l, r]` form one
contiguous block. Where does it start and where does it end?""",
        r"""It starts at `lower_bound(l)` (first element ≥ l) and ends just before
`upper_bound(r)` (first element > r). The count is the difference of the two iterators.""",
    ],
    editorial=r"""
Sort once, O(n log n). In sorted order the readings inside `[l, r]` are one block: from
the first element `≥ l` to the last element `≤ r`. `lower_bound(a.begin(), a.end(), l)`
points at the first of them and `upper_bound(a.begin(), a.end(), r)` just past the last,
so the answer is their difference. O(log n) per question.

The classic slip is `lower_bound(r)` for the right end: it stops *before* the readings
equal to `r`, and the first sample's answer drops from 4 to 3. Scanning the whole array
for every question is O(n·q) = 4·10^10: about 17 s here.
""",
)

RANKS = Problem(
    id="ranks",
    title="Elevation Levels",
    difficulty="easy",
    complexity="O(n log n)",
    statement=r"""
A hiking app stores exact elevations, but its map only draws *levels*: the lowest
elevation that occurs gets level 1, the next higher one that occurs gets level 2, and so
on. Equal elevations get equal levels.

Given the elevations of `n` points, print how many levels there are and the level of
every point.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers h_1, ..., h_n (−10^9 ≤ h_i ≤ 10^9).
""",
    output=r"""
On the first line print `k`, the number of distinct elevations. On the second line print
`n` integers: the level of each point, in input order.
""",
    samples=[
        Test("5\n100 -5 100 7 7\n", "3\n3 1 3 2 2\n"),
        Test("3\n1000000000 -1000000000 0\n", "3\n3 1 2\n"),
    ],
    tests=[
        Test("1\n-7\n"),
        Test("4\n5 5 5 5\n"),
        Test("6\n6 5 4 3 2 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _heights(rng, rng.randint(1, 12), -5, 5), 12),
        Gen("medium random", lambda rng: _heights(rng, 3000, -10**9, 10**9), 2),
        Gen("medium, few values", lambda rng: _heights(rng, 3000, 0, 40), 2),
        Gen("max size, all distinct", lambda rng: _heights_distinct(rng, 200000), 1, large=True),
        Gen("max size, many repeats", lambda rng: _heights(rng, 200000, -1000, 1000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<int> h(n);
    for (auto& x : h) cin >> x;
    vector<int> vals = h;
    sort(vals.begin(), vals.end());
    vals.erase(unique(vals.begin(), vals.end()), vals.end());   // unique alone keeps the size
    cout << vals.size() << '\n';
    for (int i = 0; i < n; i++) {
        int level = lower_bound(vals.begin(), vals.end(), h[i]) - vals.begin() + 1;
        cout << level << (i + 1 < n ? ' ' : '\n');
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<int> h(n);
    for (auto& x : h) cin >> x;
    set<int> s(h.begin(), h.end());
    cout << s.size() << '\n';
    for (int i = 0; i < n; i++) {
        int below = 0;
        for (int v : s) if (v < h[i]) below++;
        cout << below + 1 << ' ';
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
    vector<int> h(n);
    for (auto& x : h) cin >> x;
    vector<int> vals = h;
    sort(vals.begin(), vals.end());
    vals.erase(unique(vals.begin(), vals.end()), vals.end());
    cout << vals.size() << '\n';
    for (int i = 0; i < n; i++) {
        int j = 0;
        while (vals[j] != h[i]) j++;         // linear search instead of lower_bound
        cout << j + 1 << (i + 1 < n ? ' ' : '\n');
    }
}
""",
    hints=[
        r"""The level of `h` is 1 + the number of distinct elevations below it. Build the sorted
list of distinct elevations first.""",
        r"""`sort`, then `vals.erase(unique(vals.begin(), vals.end()), vals.end())`. The level of
`h` is `lower_bound(vals.begin(), vals.end(), h) - vals.begin() + 1`.""",
    ],
    editorial=r"""
This is **coordinate compression**: sort a copy, remove duplicates, and replace each value
by its position in that list, found by binary search. O(n log n).

The traps are all in the dedup line. `unique` only moves the kept elements to the front
and returns the new end; without the `erase`, `vals.size()` is still `n` and the first
line is wrong. `unique` without sorting first removes only *adjacent* duplicates. And
finding the position by a linear scan instead of `lower_bound` is O(n·k): with 2·10^5
distinct values, about 5 s here.

Compressed values are how a problem with coordinates up to 10^9 becomes a problem with
array indices up to `n`, which is why this idiom comes back in every range-query lesson.
""",
)

TRIMMED = Problem(
    id="trimmed_sum",
    title="Trimmed Score",
    difficulty="easy",
    complexity="O(n log n)",
    statement=r"""
In a judged sport, a performance gets `n` scores. To blunt biased judges, the `k` highest
and the `k` lowest scores are thrown away, and the performance's result is the *sum* of
the remaining `n − 2k` scores.

Compute the result.
""",
    input=r"""
The first line has `n` and `k` (1 ≤ n ≤ 2·10^5, 0 ≤ k, 2k < n).

The second line has the `n` scores s_1, ..., s_n (0 ≤ s_i ≤ 10^9).
""",
    output=r"""
Print one integer: the sum of the scores left after removing the `k` largest and the `k`
smallest.
""",
    samples=[
        Test("5 1\n6 1 9 3 3\n", "12\n"),
        Test("5 1\n1000000000 1000000000 1000000000 1000000000 0\n", "3000000000\n",
             note="The answer does not fit in an `int`. What type does `accumulate` add in?"),
    ],
    tests=[
        Test("1 0\n1000000000\n"),
        Test("3 1\n5 5 5\n"),
        Test("7 3\n9 8 7 1 2 3 4\n"),
        Test("4 0\n1000000000 1000000000 1000000000 1000000000\n"),
    ],
    gens=[
        Gen("small random", _scores_small, 14),
        Gen("medium, big scores", lambda rng: _scores(rng, 3000, rng.randint(0, 1499), 10**9), 3),
        Gen("max size, k = n/4", lambda rng: _scores(rng, 200000, 50000, 10**9), 1, large=True),
        Gen("max size, k = 0", lambda rng: _scores(rng, 200000, 0, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<int> s(n);
    for (auto& x : s) cin >> x;
    sort(s.begin(), s.end());
    // the kept scores are s[k .. n-k-1]; 0LL makes the running total a long long
    cout << accumulate(s.begin() + k, s.end() - k, 0LL) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, k;
    cin >> n >> k;
    vector<long long> s(n);
    for (auto& x : s) cin >> x;
    for (int i = 0; i < k; i++) {
        s.erase(max_element(s.begin(), s.end()));
        s.erase(min_element(s.begin(), s.end()));
    }
    long long t = 0;
    for (long long x : s) t += x;
    cout << t << '\n';
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
    vector<long long> s(n);
    for (auto& x : s) cin >> x;
    for (int i = 0; i < k; i++) {                 // Python: a.remove(max(a)), k times
        s.erase(max_element(s.begin(), s.end()));
        s.erase(min_element(s.begin(), s.end()));
    }
    cout << accumulate(s.begin(), s.end(), 0LL) << '\n';
}
""",
    hints=[
        r"""After sorting, the scores to keep are exactly the positions `k` to `n − k − 1`: the
range `s.begin() + k` to `s.end() - k`.""",
        r"""The sum can reach about 2·10^14. `accumulate(first, last, 0)` adds in `int` because
the `0` is an `int`; write `0LL`.""",
    ],
    editorial=r"""
Sort, then sum the middle: `accumulate(s.begin() + k, s.end() - k, 0LL)`. O(n log n).
(`nth_element` twice would make it O(n) on average; the sort is fast enough.)

The trap is the third argument. `accumulate` keeps its running total in the type of its
initial value, so with `0` it adds in `int`, and 3·10^9 comes out as −1294967296 (the
second sample). The vector can stay `vector<int>`: with `0LL` every addition happens in
`long long`.

The Python habit `a.remove(max(a))` repeated `k` times is O(n) per removal: with `k = 5·10^4`
that is about 2·10^10 steps, over 15 s here.
""",
)

CREATING_STRINGS = Problem(
    id="creating_strings",
    title="Creating Strings",
    difficulty="easy",
    source="CSES 1622 - Creating Strings",
    complexity="O(n! · n)",
    statement=r"""
Given a string, generate every *different* string that can be made by rearranging its
letters.

Print how many there are, then all of them in alphabetical order.
""",
    input=r"""
One line with a string of length `n` (1 ≤ n ≤ 8), made of lowercase letters `a`-`z`.
""",
    output=r"""
First print `k`, the number of different strings. Then print the `k` strings, one per
line, in alphabetical order.
""",
    samples=[
        Test("aabac\n", "20\naaabc\naaacb\naabac\naabca\naacab\naacba\nabaac\nabaca\nabcaa\nacaab\nacaba\nacbaa\nbaaac\nbaaca\nbacaa\nbcaaa\ncaaab\ncaaba\ncabaa\ncbaaa\n"),
        Test("cba\n", "6\nabc\nacb\nbac\nbca\ncab\ncba\n",
             note="The input is not the first arrangement in alphabetical order."),
    ],
    tests=[
        Test("a\n"),
        Test("zzzzzzzz\n"),
        Test("hgfedcba\n"),
        Test("ba\n"),
    ],
    gens=[
        Gen("random, few letters", lambda rng: _word(rng, 8, "abc"), 8),
        Gen("random, many letters", lambda rng: _word(rng, 7, _ALPHA), 6),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    sort(s.begin(), s.end());            // start from the first arrangement
    vector<string> all;
    do {
        all.push_back(s);                // next_permutation skips repeated arrangements
    } while (next_permutation(s.begin(), s.end()));
    cout << all.size() << '\n';
    for (auto& t : all) cout << t << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
set<string> found;
string s, cur;
vector<bool> used;
void go() {
    if (cur.size() == s.size()) { found.insert(cur); return; }
    for (int i = 0; i < (int)s.size(); i++) {
        if (used[i]) continue;
        used[i] = true; cur.push_back(s[i]);
        go();
        cur.pop_back(); used[i] = false;
    }
}
int main() {
    cin >> s;
    used.assign(s.size(), false);
    go();
    cout << found.size() << '\n';
    for (auto& t : found) cout << t << '\n';
}
""",
    hints=[
        r"""`next_permutation(s.begin(), s.end())` turns `s` into the next arrangement in
alphabetical order and returns `false` after the last one.""",
        r"""It starts from wherever `s` is. Sort `s` first, then
`do { ... } while (next_permutation(s.begin(), s.end()));`. Repeated letters are handled
for you: equal arrangements are never produced twice.""",
    ],
    editorial=r"""
Sort the string, then loop with `do { record s } while (next_permutation(...))`.
`next_permutation` produces the lexicographically next *distinct* arrangement, so repeated
letters need no deduplication, and the order is already alphabetical. At most 8! = 40320
strings of 8 letters.

Two ways to lose it: forgetting the initial `sort` (the loop starts at the input and
never goes back, so `cba` prints only itself), and the Python route of generating all n!
orderings and deduplicating, which works here but prints duplicates if you forget the
set.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp06",
    title="STL algorithms, iterators & lambdas",
    track="cpp",
    order=6,
    summary="sort with comparators (and what a comparator must promise), lambdas and "
            "captures, lower_bound/upper_bound as bisect, unique + erase and coordinate "
            "compression, accumulate's 0LL, nth_element and next_permutation.",
    prereqs=["cpp05"],
    tags=["sort", "comparator", "stable_sort", "lambda", "lower_bound", "upper_bound",
          "unique", "coordinate compression", "accumulate", "next_permutation", "nth_element"],
    parts=[
        Part("sort: ranges and comparators", [
            Say(r"""
Python has `a.sort()` and `sorted(a)`. C++ has `sort`, and it shows the shape every STL
algorithm has:

```cpp
sort(v.begin(), v.end());                   // ascending, in place, O(n log n)
sort(v.begin(), v.end(), greater<int>());   // descending
sort(v.begin() + 2, v.end());               // only from index 2 on
```

An algorithm takes a **range**: two iterators `first, last`, meaning the elements from
`first` up to *but not including* `last`, like Python's `a[i:j]`. `v.begin() + k` is
index `k` and `v.end()` is one past the end. The same algorithms work on strings and on
plain arrays (`sort(a, a + n)`).
"""),
            Short(r"""
What does this print?

```cpp
vector<int> v = {5, 2, 8, 1, 9};
sort(v.begin() + 1, v.end() - 1);
for (int x : v) cout << x << ' ';
```
""", accept=["5 1 2 8 9"], placeholder="what it prints",
                hint="Which indices does the range `[begin + 1, end - 1)` cover?",
                explain=r"""
`5 1 2 8 9`. The range covers indices 1, 2, 3 (the `2 8 1`), sorts them to `1 2 8`, and
leaves the 5 and the 9 where they were. Half-open ranges make "the first k elements"
`v.begin(), v.begin() + k` with no ±1 anywhere.
"""),
            Say(r"""
Python sorts by a **key**: `sorted(words, key=len)`. C++ sorts with a **comparison**: a
function `comp(a, b)` that returns `true` when `a` must come before `b`. You usually
write it inline, as a *lambda* (the next part explains the syntax):

```cpp
sort(w.begin(), w.end(), [](const string& a, const string& b) {
    return a.size() < b.size();          // shorter words first
});
```

For several keys, as in Python's `key=lambda s: (len(s), s)`, compare the first key and
fall through to the next one only on a tie.
"""),
            Short(r"""
What does this print?

```cpp
vector<string> w = {"pear", "fig", "apple", "kiwi"};
sort(w.begin(), w.end(), [](const string& a, const string& b) {
    if (a.size() != b.size()) return a.size() < b.size();
    return a < b;
});
for (auto& s : w) cout << s << ' ';
```
""", accept=["fig kiwi pear apple"], placeholder="what it prints",
                explain=r"""
`fig kiwi pear apple`. Length first; `kiwi` and `pear` tie on length 4, so the second key
(alphabetical) puts `kiwi` first. `string`s compare alphabetically with `<`, like Python's.
"""),
            MCQ(r"""
`v` is a `vector<pair<int, string>>` of (score, name). You want the highest score first,
and equal scores in alphabetical order of name. Which does it?
""", [
                Opt("`sort(v.rbegin(), v.rend());`",
                    why="Sorting through reverse iterators gives descending order of the *whole* "
                        "pair, so equal scores come out in reverse alphabetical order: `(5, bob)` "
                        "before `(5, al)`."),
                Opt("`sort(v.begin(), v.end()); reverse(v.begin(), v.end());`",
                    why="Reversing flips the ties too: same problem as the reverse iterators."),
                Opt("Store `{-score, name}` instead and sort ascending.", correct=True,
                    why="Yes: this is `key=lambda p: (-p.score, p.name)` in C++. Negating flips "
                        "exactly the one key that runs the other way."),
                Opt("`sort(v.begin(), v.end(), greater<pair<int, string>>());`",
                    why="`greater` on pairs is descending on both fields: names come out "
                        "reverse-alphabetical among equal scores."),
            ], explain=r"""
The comparator version is just as good: `if (a.first != b.first) return a.first > b.first;
return a.second < b.second;`. Pick whichever you can read at 3 a.m. in a contest.
"""),
        ]),
        Part("Lambdas and captures", [
            Say(r"""
A lambda is a function written inline, without a name:

```cpp
auto sq = [](long long x) { return x * x; };
cout << sq(12) << '\n';                                  // 144
int odd = count_if(v.begin(), v.end(), [](int x) { return x % 2 != 0; });
```

The square brackets say what the lambda may use from the function around it, its
**captures**: `[]` nothing, `[k]` a copy of `k`, `[&k]` the variable `k` itself (a
reference), `[=]` copies of everything it uses, `[&]` references to everything it uses.
Unlike a Python lambda, a C++ lambda cannot touch a local variable it did not capture:
that is a compile error.
"""),
            Short(r"""
What does this print?

```cpp
int k = 10;
auto byCopy = [k](int x) { return x + k; };
auto byRef = [&k](int x) { return x + k; };
k = 20;
cout << byCopy(1) << ' ' << byRef(1) << '\n';
```
""", accept=["11 21"], placeholder="what it prints",
                explain=r"""
`11 21`. `byCopy` took its own copy of `k` when it was created, while `k` was 10;
`byRef` reads the live variable. Python closures behave like `byRef`: they see the
variable, not its value at creation time.
"""),
            Say(r"""
The most common lambda in contest code sorts *indices* by values stored elsewhere:
Python's `sorted(range(n), key=lambda i: a[i])`.

```cpp
vector<int> idx(n);
iota(idx.begin(), idx.end(), 0);          // 0, 1, 2, ..., n-1
sort(idx.begin(), idx.end(), [&](int i, int j) { return a[i] < a[j]; });
```
"""),
            Short(r"""
With `a = {30, 10, 20}`, what is `idx` after that sort? (Three numbers, separated by
spaces.)
""", accept=["1 2 0"], placeholder="three indices",
                explain=r"""
`1 2 0`: `a[1] = 10` is the smallest, then `a[2] = 20`, then `a[0] = 30`. The array `a`
itself is untouched, which is the point: you can sort several parallel arrays "together"
by sorting one index array.
"""),
            MCQ(r"""
What changes if that comparator captures with `[=]` instead of `[&]`, for `n = 2·10^5`?
""", [
                Opt("Nothing: the lambda only reads `a`.",
                    why="It reads its own *copy* of `a`, made when the lambda is created. The "
                        "copy is not the problem; how often it gets copied again is."),
                Opt("The result is wrong, because the lambda sorts by a stale copy of `a`.",
                    why="The copy is made at the call, when `a` already holds its final values: "
                        "the order is correct."),
                Opt("It becomes very slow: `sort` copies its comparator again and again, and "
                    "every copy duplicates the whole vector.", correct=True,
                    why="Yes. GCC's `sort` passes the comparator by value down its recursion. "
                        "Measured here: 2.9 s with `[=]`, 0.012 s with `[&]`."),
                Opt("It does not compile: sort comparators must capture by reference.",
                    why="Any capture compiles. The compiler has no opinion about the cost."),
            ], explain=r"""
Capture large things (vectors, strings, maps) by reference. `[&]` is the default choice
for a lambda that is used right where it is written, which is almost every contest
lambda.
"""),
        ]),
        Part("What a comparator must promise", [
            Say(r"""
`sort` assumes your comparator behaves like `<`. Formally it must be a *strict weak
ordering*:

- `comp(a, a)` is false: nothing comes before itself;
- if `comp(a, b)`, then not `comp(b, a)`;
- if `comp(a, b)` and `comp(b, c)`, then `comp(a, c)`.

`sort` cashes in on these promises for speed. Its inner loop runs "while the element is
smaller than the pivot" with no bounds check, because with a real `<` the pivot itself is
guaranteed to stop it.
"""),
            MCQ(r"""
What happens here?

```cpp
vector<int> v(100, 5);
sort(v.begin(), v.end(), [](int a, int b) { return a <= b; });
```
""", [
                Opt("Nothing interesting: all elements are equal, so any order is sorted.",
                    why="With `<=`, 5 comes 'before' 5, so the loop that should stop at the pivot "
                        "never stops, and walks off the end of the vector."),
                Opt("A compile error: `<=` is not allowed in a comparator.",
                    why="The compiler cannot check the promise; it only sees a function that "
                        "returns `bool`."),
                Opt("Undefined behaviour: with GCC it reads past the array and crashes.",
                    correct=True,
                    why="Yes. On this machine it crashes for every n ≥ 17 equal elements (below "
                        "17, `sort` uses insertion sort, which survives: the bug hides in small "
                        "tests)."),
                Opt("It sorts in descending order.",
                    why="`<=` does not reverse anything; for distinct values it orders exactly "
                        "like `<`. The damage is all in the ties."),
            ], explain=r"""
Descending order is `>`, never `>=`; ascending is `<`, never `<=`. And a comparator must
not change its mind: comparing by a value that is modified during the sort, or by a
random number, breaks the same promises.
"""),
            Say(r"""
Ties are also where the second difference from Python lives. Python's sort is **stable**:
elements that compare equal keep their original order. C++'s `sort` is not. It is
introsort (quicksort with safety nets), and partitioning moves equal elements past each
other. Here are 40 pairs `(i % 2, i)` sorted by the first field only; the printout shows
the original indices:

```
0 26 24 28 22 20 30 18 16 32 14 12 34 10 8 36 6 4 38 2 33 35 31 ...
```

`stable_sort` keeps ties in their input order, at O(n log n) with some extra memory.
"""),
            Reflect(r"""
In Python you sometimes sort twice, first by name and then by score, relying on
stability so that equal scores stay alphabetical. What happens if you port that to two
C++ `sort` calls, and what are two ways to fix it?
""", answer=r"""
The second `sort` may reorder teams with equal scores, so the alphabetical order from the
first pass is lost. Worse, on arrays of 16 or fewer elements `sort` uses insertion sort,
which happens to be stable, so the samples pass and the big tests fail. Fix 1: make the
second pass a `stable_sort`. Fix 2 (usual): sort once with the full key, a comparator
that compares score and then name, or tuples `{-score, name}`. When ties must keep input
order, the input index is the last key.
"""),
            MCQ(r"""
To put higher scores first while keeping ties in input order, you write
`stable_sort(v.begin(), v.end(), [](auto& a, auto& b) { return a.score >= b.score; })`.
What happens to teams with equal scores?
""", [
                Opt("They keep their input order: that is what `stable_sort` promises.",
                    why="It promises that for a strict comparator. With `>=`, each of two equal "
                        "teams counts as 'before' the other, and the merge believes it."),
                Opt("They come out in reverse input order.", correct=True,
                    why="Yes, with GCC (formally it is undefined behaviour, like any non-strict "
                        "comparator). When two equal elements meet, the merge sees "
                        "`comp(later, earlier)` is true and takes the later one first. Measured on "
                        "the 40-pair example: every group of ties comes out exactly reversed."),
                Opt("It crashes, like `sort` with `<=`.",
                    why="Not with GCC: its `stable_sort` is a merge sort whose loops stop at the "
                        "ends of the ranges, so it does not run off the array; it just produces "
                        "the wrong order. (Still undefined behaviour: do not rely on either.)"),
            ]),
            Try("scoreboard", note="Three keys, and the last one is the registration order. "
                "The hidden tests have tens of thousands of ties."),
        ]),
        Part("Binary search: lower_bound and upper_bound", [
            Say(r"""
On a sorted `vector`, binary search is built in, and it maps exactly onto Python's
`bisect` module:

| C++ | Python | gives |
| `lower_bound(v.begin(), v.end(), x)` | `bisect_left(v, x)` | first position with `v[i] >= x` |
| `upper_bound(v.begin(), v.end(), x)` | `bisect_right(v, x)` | first position with `v[i] > x` |
| `binary_search(v.begin(), v.end(), x)` | | only `true` / `false` |
| `equal_range(v.begin(), v.end(), x)` | | both, as a pair |

The C++ versions return iterators; subtract `v.begin()` to get an index. Each is
O(log n) on a `vector` (on a `set`, use the member functions: cpp05). On an unsorted
vector they return garbage positions without any error.
"""),
            Short(r"""
`v = {1, 3, 3, 3, 7, 9}`. What are `lower_bound(v.begin(), v.end(), 3) - v.begin()` and
`upper_bound(v.begin(), v.end(), 3) - v.begin()`? (Two numbers.)
""", accept=["1 4", "1, 4", "1,4"], placeholder="two numbers",
                explain=r"""
`1 4`. The 3s occupy indices 1, 2, 3: `lower_bound` points at the first of them,
`upper_bound` just past the last. Their difference, 3, is the number of 3s. That is
exactly what `equal_range` returns in one call.
"""),
            Numeric(r"""
Same `v`. What is `lower_bound(v.begin(), v.end(), 10) - v.begin()`?
""", answer=6,
                explain=r"""
6, which is `v.size()`: no element is ≥ 10, so the result is `v.end()`. Dereferencing it
is undefined behaviour, so check `it != v.end()` before reading `*it`.
"""),
            MCQ(r"""
`v` is sorted. Which expression counts the elements `x` with `l ≤ x ≤ r`?
""", [
                Opt("`lower_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l)`",
                    why="`lower_bound(r)` stops *before* the elements equal to `r`, so they are "
                        "not counted. With `v = {1, 3, 3, 3, 7, 9}` and `[3, 7]` it gives 3, not 4."),
                Opt("`upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l)`",
                    correct=True,
                    why="Yes: from the first element ≥ l to just past the last element ≤ r."),
                Opt("`upper_bound(v.begin(), v.end(), r) - upper_bound(v.begin(), v.end(), l)`",
                    why="`upper_bound(l)` skips the elements equal to `l`: they are lost."),
                Opt("`upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l) + 1`",
                    why="Iterator differences already count elements in a half-open range; the "
                        "+1 counts one element too many (and gives 1 for an empty range)."),
            ]),
            Numeric(r"""
Without sorting, each question scans all `n` readings. With `n = q = 2·10^5`, how many
comparisons is that?
""", answer=4e10, rel=0.5, unit="comparisons",
                explain=r"""
4·10^10: about 17 seconds here. Sorting once and answering each question with two binary
searches is 2·10^5 · 2 · 18 ≈ 7·10^6 steps.
"""),
            Try("range_count", note="Sort once, two binary searches per question. The first "
                "sample has readings on both ends of a range."),
        ]),
        Part("unique, erase, and coordinate compression", [
            Say(r"""
Python deduplicates with `sorted(set(a))`. C++ does it in place, in two steps that
together are one of the most-typed lines in contest code:

```cpp
sort(v.begin(), v.end());
v.erase(unique(v.begin(), v.end()), v.end());
```

`unique` removes *adjacent* duplicates, which is why the vector is sorted first. And it
cannot change the vector's size, because an algorithm only sees iterators, never the
container. So it moves the kept elements to the front and returns an iterator to the new
logical end. The `erase` cuts off what is left over.
"""),
            Short(r"""
What does this print?

```cpp
vector<int> v = {1, 1, 2, 2, 2, 3};
auto it = unique(v.begin(), v.end());
cout << (it - v.begin()) << ' ' << v.size() << '\n';
```
""", accept=["3 6"], placeholder="two numbers",
                explain=r"""
`3 6`. Three distinct values were moved to the front (`1 2 3`), and the vector still has
six elements; the last three are leftovers with unspecified values. Forget the `erase`
and `v.size()` is still 6.
"""),
            MCQ(r"""
`v = {3, 1, 3}` (not sorted). How many elements does `v` have after
`v.erase(unique(v.begin(), v.end()), v.end());`?
""", [
                Opt("2", why="`unique` only compares neighbours, and the two 3s are not "
                             "neighbours."),
                Opt("3", correct=True,
                    why="Right: no two adjacent elements are equal, so nothing is removed. Sort "
                        "first."),
                Opt("1", why="Nothing is removed at all; `unique` is not 'keep one of each "
                             "value'."),
            ]),
            Say(r"""
Sorting and deduplicating is the first half of **coordinate compression**: replace values
from a huge range (say up to 10^9) by their rank among the distinct values, 0 to k − 1.
Ranks keep the order, which is all many problems need, and they are small enough to index
an array.

```cpp
vector<int> vals = a;
sort(vals.begin(), vals.end());
vals.erase(unique(vals.begin(), vals.end()), vals.end());
for (int& x : a)
    x = lower_bound(vals.begin(), vals.end(), x) - vals.begin();
```
"""),
            Short(r"""
What does `a` become when it starts as `{100, -5, 100, 7}`? (Four numbers.)
""", accept=["2 0 2 1"], placeholder="four numbers",
                explain=r"""
`2 0 2 1`. The distinct values in order are `-5 7 100`, so −5 → 0, 7 → 1, 100 → 2.
Equal values get equal ranks, and `a[i] < a[j]` exactly when their ranks compare the same
way.
"""),
            Try("ranks", note="Coordinate compression, with levels starting at 1. The first "
                "output line is where a missing `erase` shows."),
        ]),
        Part("Folds and picks: accumulate, max_element, nth_element", [
            Say(r"""
A few more, all taking a range:

```cpp
long long s = accumulate(v.begin(), v.end(), 0LL);   // sum(v)    <numeric>
auto it = max_element(v.begin(), v.end());           // iterator to the first maximum
int where = it - v.begin();                          // ...and its index
int c = count(v.begin(), v.end(), x);                // v.count(x)
reverse(v.begin(), v.end());
iota(v.begin(), v.end(), 1);                         // 1, 2, 3, ...
```

`accumulate`'s third argument is not decoration.
"""),
            MCQ(r"""
What does this print?

```cpp
vector<long long> v = {1000000000, 1000000000, 1000000000};
cout << accumulate(v.begin(), v.end(), 0) << '\n';
```
""", [
                Opt("`3000000000`: the elements are `long long`.",
                    why="The running total has the type of the initial value, and `0` is an "
                        "`int`. Each partial sum is squeezed back into an `int`."),
                Opt("A negative number (here −1294967296): the total is kept in an `int`.",
                    correct=True,
                    why="Yes. `accumulate(first, last, init)` computes `init = init + *it` with "
                        "`init`'s type. Write `0LL` and the total is a `long long`."),
                Opt("A compile error: `int` and `long long` do not mix.",
                    why="They mix silently; that is the problem."),
            ], explain=r"""
Python's `sum` cannot overflow, so this trap does not exist there. In C++ it passes
every small test and fails the first big one. The same rule holds for any `init`: `0.0`
for doubles, `string()` to concatenate strings.
"""),
            Short(r"""
What does this print?

```cpp
vector<int> v = {3, 9, 2, 9};
cout << max_element(v.begin(), v.end()) - v.begin() << '\n';
```
""", accept=["1"], placeholder="a number",
                explain=r"""
`1`: the index of the *first* maximum. `max_element` returns an iterator, so `*it` is the
value and `it - v.begin()` the position (Python needs `a.index(max(a))` and two passes).
"""),
            Say(r"""
`nth_element(v.begin(), v.begin() + k, v.end())` rearranges `v` so that position `k`
holds exactly what a full sort would put there, everything before it is ≤ it and
everything after it is ≥ it, in no particular order. It runs in O(n) on average, where a
sort is O(n log n): it is the tool for "the k-th smallest" and for medians.
"""),
            Numeric(r"""
`v = {9, 1, 8, 2, 7, 3}`. After `nth_element(v.begin(), v.begin() + 2, v.end())`, what is
`v[2]`?
""", answer=3,
                explain=r"""
3: sorted, `v` would be `1 2 3 7 8 9`, and index 2 holds 3. Positions 0-1 hold 1 and 2 in
some order, positions 3-5 hold 7, 8, 9 in some order.
"""),
            Numeric(r"""
From `n = 2·10^5` scores you must drop the `k = 5·10^4` largest and the `k` smallest. The
Python habit is `a.remove(max(a))` and `a.remove(min(a))`, `k` times each: every call
scans and shifts about `n` elements. Roughly how many element operations is that?
""", answer=2e10, rel=0.5, unit="operations",
                explain=r"""
2k removals of about n steps each: 2 · 5·10^4 · 2·10^5 = 2·10^10, over 15 s here. Sort
once and the kept scores are simply `s.begin() + k` to `s.end() - k`.
"""),
            Try("trimmed_sum", note="Sort, then one `accumulate` over the middle. The second "
                "sample checks its third argument."),
        ]),
        Part("Every arrangement: next_permutation", [
            Say(r"""
`next_permutation(first, last)` rearranges the range into the next arrangement in
lexicographic order and returns `true`; if the range was already the last arrangement
(descending), it wraps around to the first (ascending) and returns `false`. So this loop
visits every arrangement:

```cpp
sort(s.begin(), s.end());
do {
    cout << s << '\n';
} while (next_permutation(s.begin(), s.end()));
```
"""),
            Short(r"""
What does this print?

```cpp
string s = "bca";
next_permutation(s.begin(), s.end());
cout << s << '\n';
```
""", accept=["cab"], placeholder="a string",
                hint="List the arrangements of a, b, c in alphabetical order and find `bca`.",
                explain=r"""
`cab`. In order: abc, acb, bac, bca, **cab**, cba.
"""),
            Numeric(r"""
Without the `sort`, starting from `s = "bca"`, how many strings does the do-while loop
print?
""", answer=3, unit="strings",
                explain=r"""
3: `bca`, `cab`, `cba`, and then `next_permutation` wraps around to `abc` and returns
`false`. The loop starts where `s` is, so the arrangements before it are never printed.
Always sort first.
"""),
            Numeric(r"""
With the `sort`, how many strings does it print for `s = "aabb"`?
""", answer=6, unit="strings",
                explain=r"""
6 = 4! / (2!·2!). `next_permutation` jumps to the next *different* arrangement, so
repeated letters produce no duplicates, where Python's `itertools.permutations("aabb")`
yields 24 tuples, most of them repeats.
"""),
            Try("creating_strings", note="Sort, then do-while. The second sample does not start "
                "sorted."),
        ]),
    ],
    problems=[SCOREBOARD, RANGE_COUNT, RANKS, TRIMMED, CREATING_STRINGS],
    cards=[
        Card(r"""What range does `sort(v.begin() + a, v.begin() + b)` sort?""",
             r"""Indices `a` to `b − 1`: STL ranges are half-open `[first, last)`, like Python's `v[a:b]`."""),
        Card(r"""Two ways to sort a `vector<int>` in descending order?""",
             r"""`sort(v.begin(), v.end(), greater<int>())` or `sort(v.rbegin(), v.rend())`."""),
        Card(r"""Why is `[](int a, int b) { return a <= b; }` a bug as a sort comparator?""",
             r"""A comparator must be strict (`comp(a, a)` false). With `<=`, `sort` can run off the array and crash on many equal elements; `stable_sort` reverses ties. Use `<` or `>`."""),
        Card(r"""Is `std::sort` stable? What do you do when ties must keep input order?""",
             r"""No. Use `stable_sort`, or add the input index as the last key of the comparison."""),
        Card(r"""Sort by score descending, then name ascending, without writing a comparator?""",
             r"""Store tuples/pairs `{-score, name}` and `sort` ascending: negate the key that runs the other way."""),
        Card(r"""Sort indices `0..n-1` by `a[i]` (Python `sorted(range(n), key=lambda i: a[i])`)?""",
             r"""`vector<int> idx(n); iota(idx.begin(), idx.end(), 0); sort(idx.begin(), idx.end(), [&](int i, int j) { return a[i] < a[j]; });`"""),
        Card(r"""Why capture by reference (`[&]`) in a sort comparator that reads a big vector?""",
             r"""`sort` copies its comparator many times; with `[=]` each copy duplicates the vector (2.9 s vs 0.012 s for n = 2·10^5)."""),
        Card(r"""`lower_bound` vs `upper_bound` on a sorted vector?""",
             r"""First element `>= x` vs first element `> x` (Python `bisect_left` / `bisect_right`). Subtract `v.begin()` for the index."""),
        Card(r"""Count elements of a sorted vector in `[l, r]`?""",
             r"""`upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l)`"""),
        Card(r"""Deduplicate a vector (Python `sorted(set(v))`)?""",
             r"""`sort(v.begin(), v.end()); v.erase(unique(v.begin(), v.end()), v.end());` (`unique` alone keeps the size and only removes adjacent duplicates.)"""),
        Card(r"""Why does `accumulate(v.begin(), v.end(), 0)` overflow even for a `vector<long long>`?""",
             r"""The running total has the type of the initial value: `0` is an `int`. Write `0LL`."""),
        Card(r"""Loop over all distinct permutations of `s` in lexicographic order?""",
             r"""`sort(s.begin(), s.end()); do { ... } while (next_permutation(s.begin(), s.end()));` Repeated letters give no duplicates."""),
    ],
)
