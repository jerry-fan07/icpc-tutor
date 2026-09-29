from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _movies(rng, n, span, maxlen):
    out = [str(n)]
    for _ in range(n):
        a = rng.randint(1, span - 1)
        b = min(span, a + rng.randint(1, maxlen))
        out.append(f"{a} {b}")
    return "\n".join(out) + "\n"


def _movies_all_watchable(rng, n, touching):
    """n movies that can all be watched, shuffled: the answer is n, the worst case for
    'rescan the list for the next movie'."""
    if touching:
        ms = [(i + 1, i + 2) for i in range(n)]
    else:
        ms = [(3 * i + 1, 3 * i + 2) for i in range(n)]
    rng.shuffle(ms)
    return f"{n}\n" + "\n".join(f"{a} {b}" for a, b in ms) + "\n"


def _kids(rng, n, x, lo, hi):
    return f"{n} {x}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _kids_small(rng, vmax):
    n = rng.randint(1, 10)
    x = rng.randint(1, vmax)
    return _kids(rng, n, x, 1, x)


def _sticks(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _sticks_two_ends(rng, n):
    v = [1] * (n // 2) + [10**9] * (n - n // 2)
    rng.shuffle(v)
    return f"{n}\n" + " ".join(map(str, v)) + "\n"


def _pairs(rng, n, amax, bmax):
    return f"{n}\n" + "\n".join(f"{rng.randint(1, amax)} {rng.randint(1, bmax)}"
                                for _ in range(n)) + "\n"


# --------------------------------------------------------------------- problems
MOVIE_FESTIVAL = Problem(
    id="movie_festival",
    title="Movie Festival",
    difficulty="easy",
    source="CSES 1629 - Movie Festival",
    complexity="O(n log n)",
    statement=r"""
A film festival shows `n` movies, each at a fixed time. You want to watch as many movies as
possible, every one of them from beginning to end. You can walk out of a movie that ends at
time `t` and straight into one that starts at time `t`, but you cannot be in two movies at
once.

What is the largest number of movies you can watch?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has two integers `a` and `b` (1 ≤ a < b ≤ 10^9): a movie that
starts at time `a` and ends at time `b`.
""",
    output=r"""
Print one integer: the maximum number of movies you can watch.
""",
    samples=[
        Test("5\n3 5\n4 9\n5 8\n1 3\n8 10\n", "4\n",
             note="Back-to-back movies are allowed: 1-3, 3-5, 5-8, 8-10."),
        Test("3\n1 10\n2 3\n4 5\n", "2\n",
             note="The movie that starts first is the one to skip."),
    ],
    tests=[
        Test("1\n1 1000000000\n"),
        Test("4\n2 7\n2 7\n2 7\n2 7\n"),
        Test("4\n1 100\n2 99\n3 98\n4 97\n"),
        Test("5\n4 5\n1 2\n3 4\n2 3\n5 6\n"),
        Test("3\n1 5\n4 7\n6 10\n"),
        Test("11\n1 4\n5 8\n9 12\n13 16\n3 6\n7 10\n11 14\n3 6\n3 6\n11 14\n11 14\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _movies(rng, rng.randint(1, 12), 20, 8), 15),
        Gen("medium random", lambda rng: _movies(rng, 2000, 10**9, 10**7), 2),
        Gen("max size, random", lambda rng: _movies(rng, 200000, 10**9, 10**6), 1, large=True),
        Gen("max size, every movie watchable", lambda rng: _movies_all_watchable(rng, 200000, False), 1, large=True),
        Gen("max size, back to back", lambda rng: _movies_all_watchable(rng, 200000, True), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<pair<int, int>> m(n);              // stored as {end, start}: pairs sort by .first
    for (auto& [b, a] : m) cin >> a >> b;
    sort(m.begin(), m.end());
    int watched = 0, free_at = 0;             // free_at: when the last chosen movie ends
    for (auto [b, a] : m) {
        if (a >= free_at) {                   // back-to-back is allowed, hence >=
            watched++;
            free_at = b;
        }
    }
    cout << watched << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<pair<long long, long long>> m(n);
    for (auto& [a, b] : m) cin >> a >> b;
    sort(m.begin(), m.end());                 // by start: a compatible predecessor comes earlier
    vector<int> best(n, 1);                   // best[i]: longest chain of movies ending with i
    int ans = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < i; j++)
            if (m[j].second <= m[i].first) best[i] = max(best[i], best[j] + 1);
        ans = max(ans, best[i]);
    }
    cout << ans << '\n';
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
    vector<int> a(n), b(n);
    for (int i = 0; i < n; i++) cin >> a[i] >> b[i];
    // the right greedy, but without sorting: rescan everything for the next movie
    int watched = 0, free_at = 0;
    while (true) {
        int best = -1;
        for (int i = 0; i < n; i++)
            if (a[i] >= free_at && (best < 0 || b[i] < b[best])) best = i;
        if (best < 0) break;
        watched++;
        free_at = b[best];
    }
    cout << watched << '\n';
}
""",
    hints=[
        r"""Once you have chosen the first movie you will watch, only one number about it matters
for the rest of the evening. Which one?""",
        r"""Always take the movie that ends first among those you can still reach. Sort by end
time, then one pass with "when am I free again?".""",
        r"""`sort` on `pair{start, end}` sorts by start. Store `{end, start}` or give a comparator.
A movie starting exactly when you become free is fine: `>=`.""",
    ],
    editorial=r"""
Sort the movies by end time and walk through them, taking every movie that starts at or
after the moment you are free again.

Why it is optimal: let `g` be the movie that ends first and `O` any optimal schedule with
first movie `o`. Every other movie in `O` starts at or after `o` ends, which is at or after
`g` ends, so replacing `o` by `g` keeps `O` valid and the same size. Some optimal schedule
therefore starts with `g`; what remains is the same problem on the movies starting after
`g` ends, and the argument repeats. Equivalently, the greedy's `k`-th movie ends no later
than the `k`-th movie of any valid schedule ("greedy stays ahead").

O(n log n) for the sort. The traps: sorting `pair{a, b}` sorts by *start* (that is the
earliest-start rule, which fails on `[1,10] [2,3] [4,5]`); `>` instead of `>=` rejects
back-to-back movies; and finding the next movie by rescanning the unsorted list is O(n^2)
when most movies are watchable, which one hidden test makes 2·10^5.
""",
)

FERRIS_WHEEL = Problem(
    id="ferris_wheel",
    title="Ferris Wheel",
    difficulty="easy",
    source="CSES 1090 - Ferris Wheel",
    complexity="O(n log n)",
    statement=r"""
`n` children queue for the Ferris wheel. A gondola carries one or two children, and the
total weight in a gondola may not exceed `x`. You know every child's weight.

What is the minimum number of gondolas needed to give every child a ride?
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 2·10^5, 1 ≤ x ≤ 10^9).

The second line has `n` integers p_1, ..., p_n (1 ≤ p_i ≤ x): the weights.
""",
    output=r"""
Print one integer: the minimum number of gondolas.
""",
    samples=[
        Test("4 10\n7 2 3 9\n", "3\n"),
        Test("4 10\n2 3 7 8\n", "2\n",
             note="Putting the two lightest children together gives 3 here."),
    ],
    tests=[
        Test("1 5\n5\n"),
        Test("2 10\n5 5\n"),
        Test("2 9\n5 5\n"),
        Test("3 1000000000\n1000000000 1000000000 1\n"),
        Test("2 1000000000\n500000000 500000000\n"),
        Test("5 10\n1 1 1 1 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _kids_small(rng, 20), 15),
        Gen("small, big weights", lambda rng: _kids_small(rng, 10**9), 5),
        Gen("medium random", lambda rng: _kids(rng, 2000, 10**9, 1, 10**9), 2, large=True),
        Gen("max size, random", lambda rng: _kids(rng, 200000, 10**9, 1, 10**9), 1, large=True),
        Gen("max size, nobody can pair", lambda rng: _kids(rng, 200000, 10**9, 5 * 10**8 + 1, 10**9), 1, large=True),
        Gen("max size, everybody pairs", lambda rng: _kids(rng, 200000, 10**9, 1, 5 * 10**8), 1, large=True),
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
    vector<long long> p(n);
    for (auto& v : p) cin >> v;
    sort(p.begin(), p.end());
    int i = 0, j = n - 1, gondolas = 0;       // p[i] lightest, p[j] heaviest still waiting
    while (i <= j) {
        if (i < j && p[i] + p[j] <= x) i++;   // the lightest rides with the heaviest
        j--;                                  // the heaviest boards either way
        gondolas++;
    }
    cout << gondolas << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
long long x;
int solve(vector<long long> v) {             // try every way to pair up the children
    if (v.empty()) return 0;
    vector<long long> rest(v.begin() + 1, v.end());
    int best = 1 + solve(rest);               // v[0] rides alone
    for (size_t j = 0; j < rest.size(); j++)
        if (v[0] + rest[j] <= x) {
            vector<long long> r2 = rest;
            r2.erase(r2.begin() + j);
            best = min(best, 1 + solve(r2));
        }
    return best;
}
int main() {
    int n;
    cin >> n >> x;
    vector<long long> p(n);
    for (auto& v : p) cin >> v;
    cout << solve(p) << '\n';
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
    vector<long long> p(n);
    for (auto& v : p) cin >> v;
    sort(p.begin(), p.end());
    // heaviest first, then search for a partner: O(n) per child
    vector<char> used(n, 0);
    int gondolas = 0;
    for (int i = n - 1; i >= 0; i--) {
        if (used[i]) continue;
        used[i] = 1;
        gondolas++;
        for (int j = i - 1; j >= 0; j--)
            if (!used[j] && p[j] + p[i] <= x) { used[j] = 1; break; }
    }
    cout << gondolas << '\n';
}
""",
    hints=[
        r"""Look at the heaviest child. If anyone at all can share their gondola, who is the
safest choice?""",
        r"""Sort. Pair the heaviest with the lightest if they fit; otherwise the heaviest rides
alone (nobody fits with them). Two indices moving toward each other do this in O(n).""",
    ],
    editorial=r"""
Sort the weights and look at the heaviest child `h`. If even the lightest child `l` does not
fit with `h`, nobody does, and `h` rides alone in every solution. If `l` fits, pairing them
is safe: take an optimal plan where `h` rides with `y` and `l` with `z`, and re-pair them as
`{h, l}` and `{y, z}`. The second pair fits because `z ≤ h`, so `y + z ≤ y + h ≤ x`. (If `h`
or `l` rode alone, the re-pairing is only easier.) The count is unchanged, so some optimal
plan contains the greedy's choice; remove `h` (and `l`) and repeat.

With `i` at the lightest and `j` at the heaviest, each step boards the heaviest and maybe
the lightest: O(n) after the O(n log n) sort. Keep looping while `i <= j`: when `i == j` one
child is left and still needs a gondola. Searching for a partner by scanning the other
children is O(n) per child, 2·10^10 steps when nobody can pair.
""",
)

STICK_LENGTHS = Problem(
    id="stick_lengths",
    title="Stick Lengths",
    difficulty="easy",
    source="CSES 1074 - Stick Lengths",
    complexity="O(n log n)",
    statement=r"""
You have `n` sticks and want them all to have the same length. You may lengthen or shorten
any stick; changing a stick's length by `d` costs `d`.

What is the minimum total cost?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers p_1, ..., p_n (1 ≤ p_i ≤ 10^9): the lengths.
""",
    output=r"""
Print one integer: the minimum total cost.
""",
    samples=[
        Test("5\n2 3 1 5 2\n", "5\n"),
        Test("4\n1 3 7 12\n", "15\n"),
    ],
    tests=[
        Test("1\n1000000000\n"),
        Test("3\n7 7 7\n"),
        Test("2\n1 1000000000\n"),
        Test("6\n1 1 1 1000000000 1000000000 1000000000\n"),
        Test("3\n1 2 100\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _sticks(rng, rng.randint(1, 10), 1, 20), 12),
        Gen("medium random", lambda rng: _sticks(rng, 3000, 1, 10**9), 2),
        Gen("max size, random", lambda rng: _sticks(rng, 200000, 1, 10**9), 1, large=True),
        Gen("max size, two extremes", lambda rng: _sticks_two_ends(rng, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> p(n);
    for (auto& v : p) cin >> v;
    sort(p.begin(), p.end());
    long long m = p[n / 2], cost = 0;         // a median; for even n any value in the middle works
    for (long long v : p) cost += abs(v - m);
    cout << cost << '\n';                     // up to 2e5 * 1e9 = 2e14: long long
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
    for (long long t : p) {                   // the best target is one of the lengths
        long long c = 0;
        for (long long v : p) c += abs(v - t);
        best = min(best, c);
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
    vector<long long> p(n);
    for (auto& v : p) cin >> v;
    long long best = LLONG_MAX;
    for (long long t : p) {
        long long c = 0;
        for (long long v : p) c += abs(v - t);
        best = min(best, c);
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""Move the target length up by 1. Which sticks get more expensive, and which get
cheaper?""",
        r"""The cost changes by (sticks below) − (sticks above). It stops improving at the
median: sort and take `p[n/2]`.""",
    ],
    editorial=r"""
If the target `x` has `L` sticks below it and `R` above it, raising `x` by 1 changes the cost
by `L − R`. So while more sticks are above, go up; while more are below, go down. The cost
is minimal when at most half the sticks lie on either side: at a median. For even `n`,
every target between the two middle lengths is optimal, and `p[n/2]` (0-indexed, after
sorting) is one of them.

O(n log n) with a sort, or O(n) with `nth_element`. The cost can reach
2·10^5 · 10^9 = 2·10^14, so the sum is a `long long`; one small hidden test already exceeds
2^31 − 1. The mean is a trap: it minimises the sum of *squared* differences, not of absolute
ones (on `1 2 100` it costs 131, the median 99). Trying every stick as the target is correct
but O(n^2): 4·10^10 steps at the limits.
""",
)

TASKS = Problem(
    id="tasks_deadlines",
    title="Tasks and Deadlines",
    difficulty="easy",
    source="CSES 1630 - Tasks and Deadlines",
    complexity="O(n log n)",
    statement=r"""
You have `n` tasks. Task `i` takes `a_i` time units and has deadline `d_i`. Starting at time
0, you do the tasks one after another, without breaks, in an order you choose; every task
must be done.

Finishing task `i` at time `f_i` earns you `d_i − f_i` points, which is negative if you are
late. What is the maximum total number of points?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has two integers `a_i` and `d_i` (1 ≤ a_i, d_i ≤ 10^6).
""",
    output=r"""
Print one integer: the maximum total reward (it may be negative).
""",
    samples=[
        Test("3\n6 10\n8 15\n5 12\n", "2\n"),
        Test("3\n4 5\n1 9\n3 8\n", "9\n",
             note="Doing the tasks in order of deadline earns only 3 here."),
    ],
    tests=[
        Test("1\n1000000 1\n"),
        Test("2\n5 5\n5 5\n"),
        Test("4\n1 1000000\n1 1000000\n1000000 1\n1000000 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _pairs(rng, rng.randint(1, 8), 20, 40), 15),
        Gen("small, big values", lambda rng: _pairs(rng, rng.randint(1, 8), 10**6, 10**6), 4),
        Gen("max size, random", lambda rng: _pairs(rng, 200000, 10**6, 10**6), 1, large=True),
        Gen("max size, all long", lambda rng: "200000\n" + "1000000 1\n" * 200000, 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> a(n);
    long long deadlines = 0;
    for (int i = 0; i < n; i++) {
        long long d;
        cin >> a[i] >> d;
        deadlines += d;                       // the deadlines add up the same in any order
    }
    sort(a.begin(), a.end());                 // shortest first minimises the sum of finish times
    long long t = 0, finish_sum = 0;
    for (long long x : a) {
        t += x;
        finish_sum += t;                      // up to 1e6 * n(n+1)/2 = 2e16
    }
    cout << deadlines - finish_sum << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<long long> a(n), d(n);
    for (int i = 0; i < n; i++) cin >> a[i] >> d[i];
    vector<int> order(n);
    iota(order.begin(), order.end(), 0);
    long long best = LLONG_MIN;
    do {                                      // every order
        long long t = 0, r = 0;
        for (int i : order) { t += a[i]; r += d[i] - t; }
        best = max(best, r);
    } while (next_permutation(order.begin(), order.end()));
    cout << best << '\n';
}
""",
    hints=[
        r"""Write the total as (sum of deadlines) − (sum of finishing times). Which half depends
on the order?""",
        r"""Swap two neighbouring tasks: the sum of finishing times changes by the difference of
their durations. So do shorter tasks first.""",
    ],
    editorial=r"""
The total is `Σ d_i − Σ f_i`, and `Σ d_i` is the same for every order, so the deadlines
play no part in choosing it: minimise the sum of finishing times. If task `i` comes directly
before task `j`, both starting from time `t`, their finishing times sum to
`2t + 2a_i + a_j`; swapped, `2t + 2a_j + a_i`. Nothing else moves. So a longer task directly
before a shorter one can always be swapped without loss, and repeating that turns any
optimal order into the order by increasing duration.

O(n log n). The sum of finishing times reaches 10^6 · n(n+1)/2 ≈ 2·10^16: `long long`
everywhere. Earliest deadline first is the tempting wrong answer; the second sample shows
it earning 3 instead of 9.
""",
)

ACROBATS = Problem(
    id="acrobats",
    title="Human Tower",
    difficulty="medium",
    source="USACO 2005 November Silver - Cow Acrobats",
    complexity="O(n log n)",
    statement=r"""
A circus troupe of `n` acrobats builds a tower: every acrobat stands on the shoulders of the
one below. Acrobat `i` weighs `w_i` and has strength `s_i`. The **risk** of an acrobat is
the total weight of everyone above them, minus their own strength.

Choose the order of the tower so that the largest risk is as small as possible, and print
that value.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has two integers `w_i` and `s_i` (1 ≤ w_i, s_i ≤ 10^9).
""",
    output=r"""
Print one integer: the smallest possible value of the largest risk. It may be negative.
""",
    samples=[
        Test("3\n10 3\n2 5\n3 3\n", "2\n"),
        Test("2\n10 1\n1 2\n", "0\n",
             note="Strongest at the bottom gives a largest risk of 8."),
    ],
    tests=[
        Test("1\n5 7\n"),
        Test("2\n5 1\n3 10\n"),
        Test("2\n1000000000 1\n1000000000 1\n"),
        Test("4\n1 1000000000\n1 1000000000\n1 1000000000\n1 1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _pairs(rng, rng.randint(1, 8), 20, 20), 15),
        Gen("small, big values", lambda rng: _pairs(rng, rng.randint(1, 8), 10**9, 10**9), 5),
        Gen("max size, random", lambda rng: _pairs(rng, 200000, 10**9, 10**9), 1, large=True),
        Gen("max size, heavy and weak", lambda rng: _pairs(rng, 200000, 10**9, 1000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<pair<long long, long long>> a(n);  // {w, s}
    for (auto& [w, s] : a) cin >> w >> s;
    // neighbour swap: i above j is never worse when w_i + s_i <= w_j + s_j
    sort(a.begin(), a.end(), [](const auto& p, const auto& q) {
        return p.first + p.second < q.first + q.second;
    });
    long long above = 0, worst = LLONG_MIN;   // above: up to 2e5 * 1e9 = 2e14
    for (auto [w, s] : a) {                   // from the top down
        worst = max(worst, above - s);
        above += w;
    }
    cout << worst << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<long long> w(n), s(n);
    for (int i = 0; i < n; i++) cin >> w[i] >> s[i];
    vector<int> order(n);
    iota(order.begin(), order.end(), 0);
    long long best = LLONG_MAX;
    do {                                      // every tower, listed from the top
        long long above = 0, worst = LLONG_MIN;
        for (int i : order) { worst = max(worst, above - s[i]); above += w[i]; }
        best = min(best, worst);
    } while (next_permutation(order.begin(), order.end()));
    cout << best << '\n';
}
""",
    hints=[
        r"""Take two neighbours `i` (on top) and `j`, with weight `W` above both. Write the four
risks (before and after swapping them). Which one is the largest?""",
        r"""`i` on top of `j` is never worse when `w_i + s_i ≤ w_j + s_j`. Sort by `w + s`,
smallest on top.""",
        r"""The weight above an acrobat reaches 2·10^14: `long long`.""",
    ],
    editorial=r"""
Look at neighbours `i` directly above `j`, with total weight `W` above them. Their risks are
`W − s_i` and `W + w_i − s_j`; after swapping, `W − s_j` and `W + w_j − s_i`. Nobody else is
affected. If `w_i + s_i ≤ w_j + s_j`, then `W + w_i − s_j ≤ W + w_j − s_i`, and `W − s_i`
is below that too, so the larger risk before the swap is at most the larger risk after it:
`i` on top is never worse. Any order can therefore be bubble-sorted by `w + s` without
increasing the largest risk, and the sorted tower is optimal.

The natural guesses, strongest at the bottom or heaviest at the bottom, both fail on two
acrobats: `(10, 1), (1, 2)` and `(5, 1), (3, 10)`. O(n log n). The weight above an acrobat
reaches 2·10^14, so `long long`.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo02",
    title="sorting & greedy: exchange arguments",
    track="algo",
    order=2,
    summary="Commit to one choice at a time and never look back, but only after proving "
            "the choice is safe: exchange arguments, greedy stays ahead, neighbour swaps, "
            "the median, and the counterexamples that kill plausible rules.",
    prereqs=["cpp06", "cpp08"],
    tags=["greedy", "sorting", "exchange argument", "interval scheduling", "median",
          "scheduling", "counterexample"],
    parts=[
        Part("Picking movies", [
            Say(r"""
A film festival shows `n` movies; movie `i` runs from time `a_i` to time `b_i`. You want to
watch as many movies as possible, each from start to finish. You can walk out of a movie
that ends at 5 straight into one that starts at 5, but you cannot be in two at once. The
limits: `n ≤ 2·10^5`, times up to 10^9, one second.

The obviously correct program tries every subset of movies, keeps the subsets with no
overlap, and reports the largest.
"""),
            Numeric(r"""
How many subsets does that program try for just `n = 50` movies?
""", answer=2**50, rel=0.5, unit="subsets",
                hint="Each movie is either in or out.",
                explain=r"""
2^50 ≈ 1.1·10^15: about 13 days at 10^9 subsets per second, for 50 movies. For 2·10^5
movies the count has over 60,000 digits. No pruning rescues that; the search has to shrink
to a single path.
"""),
            Say(r"""
A **greedy** algorithm builds the answer one decision at a time and never takes a decision
back. Here: choose one movie by some rule, commit to it, throw away every movie that
overlaps it, repeat. One pass, no search. All the difficulty is in the rule, and people
propose several:

1. earliest start first: get going as soon as possible;
2. shortest first: short movies leave the most room;
3. fewest conflicts first: take the movie that blocks the fewest others.

Treat a greedy rule as guilty until proven innocent. The quickest way to kill one is a
small counterexample.
"""),
            Reflect(r"""
Rule 1, earliest start first. Build three movies on which it watches only 1 movie while 2
are possible.
""", answer=r"""
`[1, 10]`, `[2, 3]`, `[4, 5]`. Earliest start commits to `[1, 10]`, which overlaps both
others: one movie. Skipping it gives two. Starting early says nothing about how long a movie
*blocks* you, and one long movie that starts first can swallow any number of short ones.
"""),
            Short(r"""
Rule 2, shortest first, on the movies `[1, 5]`, `[4, 7]`, `[6, 10]`. How many movies does it
end up watching?
""", accept=["1", "one"], placeholder="a number",
                explain=r"""
It takes `[4, 7]` (length 3; the others have length 4), which overlaps both `[1, 5]` and
`[6, 10]`, and then nothing else fits: 1 movie. The optimum is 2, `[1, 5]` and `[6, 10]`. A
short movie can still sit across two good ones.
"""),
            Reflect(r"""
Step back. Suppose you have committed to the first movie `m` you will watch. What single
property of `m` decides which movies are still possible for the rest of the evening? What
rule does that suggest?
""", answer=r"""
Only its **end time**. Everything you watch afterwards must start at or after `m` ends; its
start, its length and how many movies it overlaps no longer matter. So the best first movie
is the one that frees you soonest: take the movie with the **earliest end**, then repeat
among the movies that start after it ends. That is the rule that works; the next part
proves it. (Rule 3 looks at conflicts, not at the end time, and it fails too, on a subtler
input that the last part of this lesson comes back to.)
"""),
        ]),
        Part("Why the earliest end is never a mistake", [
            Say(r"""
A rule that survives three examples is not yet a proof. The standard shape of a greedy proof
is the **exchange argument**: take any optimal solution, and show that it can be changed
into one that agrees with the greedy's choice without getting worse.

Let `g` be the movie that ends first. Take any optimal schedule `O` (a largest set of
non-overlapping movies) and let `o` be the movie of `O` that ends first. If `o = g`, there is
nothing to do. Otherwise, take `o` out of `O` and put `g` in.
"""),
            MCQ(r"""
Why is the new schedule still valid (no two movies overlap)?
""", [
                Opt("`g` is shorter than `o`, so it overlaps fewer movies.",
                    why="Lengths never enter the argument, and `g` can be much longer than `o` "
                        "(it may start far earlier). What matters is where `g` ends."),
                Opt("`g` and `o` do not overlap each other.",
                    why="They often do overlap (both end early), and it does not matter: `o` "
                        "is removed. What `g` must not overlap is the *rest* of `O`."),
                Opt("`g` ends no later than `o`, and every other movie of `O` starts at or after "
                    "`o` ends, so also after `g` ends.", correct=True,
                    why="Yes. The rest of `O` fitted after `o`, and `g` is out of the way at "
                        "least as early. The size is unchanged, so this is an optimal schedule "
                        "that starts with `g`."),
                Opt("`g` starts before every movie of `O`.",
                    why="Not necessarily true, and not needed: `g` may start late (it only has "
                        "to *end* first). Its start is irrelevant because nothing in `O` other "
                        "than `o` runs before `o` ends."),
            ]),
            Reflect(r"""
That shows *some* optimal schedule begins with `g`. Why does it follow that the whole greedy
schedule is optimal, and not just its first choice?
""", answer=r"""
After committing to `g`, what is left is the same problem on a smaller input: the movies that
start at or after `g` ends. The optimal schedule that begins with `g`, minus `g`, is optimal
for that smaller problem, and the same swap applies to it, so the greedy's second choice is
safe too, and so on by induction. The same idea in one sentence, **greedy stays ahead**:
after `k` picks, the greedy's `k`-th movie ends no later than the `k`-th movie of any valid
schedule, so no schedule can fit in a movie the greedy has no room for.
"""),
            Short(r"""
Run the greedy by hand on `[2, 5]`, `[1, 3]`, `[6, 8]`, `[4, 7]`, `[3, 6]`, `[7, 9]`,
`[8, 10]`. Write the end times of the movies it picks, in order, separated by spaces.
""", accept=["3 6 8 10", "3, 6, 8, 10", "3,6,8,10"], placeholder="end times",
                hint="Sort by end time first, then remember when you are free again.",
                explain=r"""
Sorted by end: `[1,3] [2,5] [3,6] [4,7] [6,8] [7,9] [8,10]`. Take `[1,3]` (free at 3);
`[2,5]` starts too early; `[3,6]` fits (free at 6); `[4,7]` no; `[6,8]` yes (free at 8);
`[7,9]` no; `[8,10]` yes. Four movies, and 4 is the optimum.
"""),
            Say(r"""
In C++, sort by end time and make one pass, remembering when you are free again:

```cpp
vector<pair<int, int>> m(n);              // {end, start}: pairs sort by .first
for (auto& [b, a] : m) cin >> a >> b;
sort(m.begin(), m.end());
int watched = 0, free_at = 0;
for (auto [b, a] : m)
    if (a >= free_at) { watched++; free_at = b; }   // >=: back to back is allowed
```

O(n log n) for the sort and O(n) for the pass, against 2^n for the brute force. The `>=`
comes from the statement ("walk out of one into the next"); some problems forbid touching
intervals, so read that sentence every time.
"""),
            MCQ(r"""
Most people first read each movie into `pair{a, b}` (start, end), the order the input gives,
and call `sort(m.begin(), m.end())`. What happens?
""", [
                Opt("Nothing changes: `sort` figures out that the end time matters.",
                    why="`sort` knows nothing about the problem. It compares pairs "
                        "lexicographically: `.first`, then `.second`."),
                Opt("Compile error: pairs cannot be sorted without a comparator.",
                    why="Pairs have `operator<` built in (lexicographic), so it compiles, and "
                        "that is what makes the bug quiet."),
                Opt("It is still correct, because ties in start are broken by end.",
                    why="Ties are broken by end, but the main order is by start, and that is "
                        "the whole problem."),
                Opt("The movies end up sorted by start, so the pass runs rule 1 and gets Wrong "
                    "Answer.", correct=True,
                    why="Yes. On `[1, 10] [2, 3] [4, 5]` it takes `[1, 10]` and prints 1. Store "
                        "`{b, a}`, or sort with a comparator on `.second`."),
            ]),
            Try("movie_festival", note="Sort by end, `>=`, one pass. One hidden test has 2·10^5 "
                "movies that are all watchable, so rescanning the list for the next movie "
                "is too slow."),
        ]),
        Part("Pairing up", [
            Say(r"""
A different shape of greedy. `n` children with weights `p_i` queue for a Ferris wheel. A
gondola holds one or two children, with total weight at most `x`. What is the minimum
number of gondolas? (`n ≤ 2·10^5`, `p_i ≤ x ≤ 10^9`.)

No gondola holds three, so the question is really how many disjoint pairs that fit you can
form: every pair saves one gondola.
"""),
            Short(r"""
A friend proposes: sort, then keep putting the two lightest remaining children together while
they fit. With `x = 10` and weights `2 3 7 8` that uses 3 gondolas: `{2, 3}`, `{7}`, `{8}`.
What is the true minimum?
""", accept=["2", "two"], placeholder="a number",
                explain=r"""
2: `{2, 8}` and `{3, 7}`. The friend spent both light children on each other. Light children
are the flexible ones, since they fit with almost anyone, so they should go to the children
that nobody else can ride with: the heavy ones.
"""),
            MCQ(r"""
So look at the heaviest child `h`. Who should share `h`'s gondola?
""", [
                Opt("Nobody: the heaviest child always rides alone.",
                    why="With `x = 10`, `h = 9` and a child of weight 1 in the queue, riding alone "
                        "wastes a gondola that a pair would save."),
                Opt("The lightest child, if the two fit; otherwise `h` rides alone.",
                    correct=True,
                    why="Yes. If even the lightest child does not fit with `h`, nobody does, so "
                        "`h` rides alone in every solution. If the lightest fits, the next "
                        "question shows that pairing them is safe."),
                Opt("The second-heaviest child, to get the big ones out of the way.",
                    why="Two heavy children rarely fit together, and when they do not, you have "
                        "learnt nothing. With `x = 10` and `1 8 9`, `8 + 9` fails but `1 + 9` "
                        "works."),
                Opt("Whoever stands next to `h` in the queue.",
                    why="The queue order has nothing to do with the count, and you are free to "
                        "sort."),
            ]),
            MCQ(r"""
Suppose `h` and the lightest child `l` fit together, but an optimal plan puts `h` with `y` and
`l` with `z`. Re-pair them as `{h, l}` and `{y, z}`. Why does `{y, z}` fit?
""", [
                Opt("`y ≤ h`, so `y + z ≤ h + z`.",
                    why="True, but nothing says `h + z` fits: `h` never rode with `z`. You need a "
                        "bound in terms of a pair that is known to fit."),
                Opt("`l` is the lightest, so `z` must be light as well.",
                    why="`z` can be anyone. The lightness of `l` is what made `{h, l}` fit; it "
                        "says nothing about `z`."),
                Opt("It might not fit; the swap only works when `y = l`.",
                    why="It always fits. Compare `z` with `h`."),
                Opt("`z ≤ h`, so `y + z ≤ y + h ≤ x`.", correct=True,
                    why="Yes: `h` is the heaviest, and `{h, y}` fitted. The number of gondolas is "
                        "unchanged, so some optimal plan contains `{h, l}`. (If `h` or `l` rode "
                        "alone in the optimal plan, the re-pairing is even easier.)"),
            ], explain=r"""
Same shape as the movies: some optimal solution agrees with the greedy's first decision, and
what remains is a smaller instance of the same problem. The heaviest child is the one with
the fewest options, so decide for them first.
"""),
            Short(r"""
With `x = 10` and weights `5 1 8 4 6 9`, run "heaviest with lightest if they fit, else
heaviest alone". How many gondolas?
""", accept=["4", "four"], placeholder="a number",
                explain=r"""
Sorted: `1 4 5 6 8 9`. `9 + 1` fits; `8 + 4` does not, so 8 rides alone; `6 + 4` fits; 5 rides
alone. Four gondolas: `{9,1} {8} {6,4} {5}`. Neither 8 nor 9 fits with anyone but 1, so no
plan does better.
"""),
            Say(r"""
Two indices walk toward each other: `i` at the lightest child still waiting, `j` at the
heaviest.

```cpp
sort(p.begin(), p.end());
int i = 0, j = n - 1, gondolas = 0;
while (i <= j) {
    if (i < j && p[i] + p[j] <= x) i++;   // the lightest joins the heaviest
    j--;                                  // the heaviest boards either way
    gondolas++;
}
```

Every iteration boards the heaviest child, so the loop runs at most `n` times. algo04 turns
this pattern into a whole technique.
"""),
            MCQ(r"""
What goes wrong if the loop condition is `while (i < j)`?
""", [
                Opt("Nothing: when `i == j`, everybody has boarded.",
                    why="When `i == j`, exactly one child is still waiting: `p[i]` itself."),
                Opt("An infinite loop.",
                    why="`j` decreases on every iteration, so the loop always ends."),
                Opt("When one child is left over (`i == j`), the loop stops without giving them "
                    "a gondola, so the answer is 1 too small.", correct=True,
                    why="Yes. The smallest test shows it: one child, `n = 1`, prints 0. The "
                        "`i < j` *inside* the `if` stops a child from pairing with themselves; "
                        "the loop condition must still let that last child board."),
                Opt("It pairs a child with themselves.",
                    why="That is what the `i < j` inside the `if` prevents. The loop condition "
                        "decides whether the last child gets counted."),
            ]),
            Try("ferris_wheel", note="Sort, then two indices. The hidden tests include 2·10^5 "
                "children of whom no two can share, which is the worst case for searching for a "
                "partner."),
        ]),
        Part("One target for everyone", [
            Say(r"""
Not every greedy picks items. Sometimes the question is *where*.

You have `n` sticks of lengths `p_i` and want them all the same length. Lengthening or
shortening a stick by 1 costs 1, so making stick `i` have length `x` costs `|p_i − x|`. Find
the minimum total cost. `n ≤ 2·10^5`, `p_i ≤ 10^9`.
"""),
            Numeric(r"""
Take the sticks `1, 2, 100`. Their mean is about 34, and target 34 costs
`33 + 32 + 66 = 131`. What is the minimum possible total cost?
""", answer=99,
                hint="Try making every stick as long as one of the existing sticks.",
                explain=r"""
Target 2 costs `1 + 0 + 98 = 99`. The mean is dragged toward the outlier, and that helps
nobody: raising the target from 2 to 34 saves the 100-stick 32 units but costs each of the
other two sticks 32.
"""),
            MCQ(r"""
Now move the target. At target `x`, `L` sticks are shorter than `x` and `R` are longer (none
equal). Raise `x` by 1, without passing any stick. How does the total cost change?
""", [
                Opt("It goes up by `L + R`.",
                    why="Only the shorter sticks get farther away; the longer ones get closer."),
                Opt("It does not change: on average the sticks stay as far away.",
                    why="There is no averaging here: each shorter stick costs exactly 1 more "
                        "and each longer stick exactly 1 less."),
                Opt("It changes by `L − R`: +1 for every shorter stick, −1 for every longer "
                    "one.", correct=True,
                    why="Yes. So while more sticks are longer (`R > L`), raising the target "
                        "pays; while more are shorter, lowering it pays."),
                Opt("It goes down by `L − R`.",
                    why="Check the direction: the `L` shorter sticks need *more* work when the "
                        "target rises."),
            ], explain=r"""
The cost stops improving exactly when at most half of the sticks lie on each side of the
target: at the **median**. For `1 2 100` that is 2.
"""),
            Numeric(r"""
Sticks `4 1 7 3 12`. What is the minimum total cost?
""", answer=15,
                explain=r"""
Sorted: `1 3 4 7 12`, median 4: `3 + 1 + 0 + 3 + 8 = 15`. Moving on to 5 leaves three sticks
below the target and two above: `+3 − 2 = +1` (16). Moving down to 3 costs one more as well
(16).
"""),
            MCQ(r"""
Four sticks: `1 3 7 12`. Which targets are optimal?
""", [
                Opt("Only 5, the average of the two middle sticks.",
                    why="5 is optimal but not the only one: anywhere strictly between 3 and 7, two "
                        "sticks are shorter and two longer, so moving changes the cost by "
                        "`2 − 2 = 0`."),
                Opt("Only 3 and 7, the middle sticks themselves.",
                    why="The cost is flat between them: target 5 costs `4 + 2 + 2 + 7 = 15`, "
                        "the same as target 3."),
                Opt("Every target from 3 to 7.", correct=True,
                    why="Yes, all cost 15. After sorting, `p[n/2]` (0-indexed) always lands in "
                        "the optimal range, for odd and even `n` alike."),
            ]),
            MCQ(r"""
Change the cost: making a stick `d` longer or shorter now costs `d^2`. Which target is
optimal?
""", [
                Opt("Still the median.",
                    why="With squares, moving the target by a little changes the cost by about "
                        "`2·Σ(x − p_i)`: the total *distance* now decides the direction, not the "
                        "count of sticks."),
                Opt("The mean (or the better of the two integers around it).", correct=True,
                    why="Yes: `Σ(p_i − x)^2` is smallest where `Σ(x − p_i) = 0`, at the mean. "
                        "Absolute values give the median, squares give the mean."),
                Opt("The midpoint of the shortest and longest stick.",
                    why="That minimises the *largest* distance, a third objective. Each objective "
                        "has its own centre."),
            ]),
            Try("stick_lengths", note="Sort, take `p[n/2]`, and add up in `long long`: 2·10^5 "
                "sticks times 10^9 is 2·10^14."),
        ]),
        Part("Order matters: swap two neighbours", [
            Say(r"""
Some greedy problems are about order. You have `n` tasks; task `i` takes `a_i` time units and
has deadline `d_i`. You do them one after another from time 0, without breaks, and every
task must be done. Finishing task `i` at time `f_i` earns `d_i − f_i` points (negative when
late). Maximise the total. `n ≤ 2·10^5`, `a_i, d_i ≤ 10^6`.

Trying all `n!` orders stops being possible beyond `n ≈ 11`. The obvious greedy is to do the
most urgent task first.
"""),
            Numeric(r"""
Tasks (duration, deadline): A = `(4, 5)`, B = `(1, 9)`, C = `(3, 8)`. In deadline order A, C,
B, what is the total reward?
""", answer=3,
                explain=r"""
A finishes at 4 (`5 − 4 = 1`), C at 7 (`8 − 7 = 1`), B at 8 (`9 − 8 = 1`): total 3. Keep that
number in mind.
"""),
            Reflect(r"""
The total is `Σ (d_i − f_i) = Σ d_i − Σ f_i`. Which part of it does the order affect, and
what does that say about the deadlines?
""", answer=r"""
Only `Σ f_i`. The deadlines add up to the same `Σ d_i` whatever the order, so they have no
say in choosing it. The problem is really "order the tasks to minimise the sum of finishing
times", and earliest-deadline-first answers a different question.
"""),
            MCQ(r"""
Neighbouring tasks `i` then `j` start at time `t`. You swap them to `j` then `i`. By how much
does `Σ f` change (after minus before)?
""", [
                Opt("By `d_j − d_i`.",
                    why="Deadlines do not appear in `Σ f` at all."),
                Opt("It depends on the tasks that come after them.",
                    why="The pair ends at `t + a_i + a_j` in both orders, so every later task "
                        "finishes at exactly the same time as before."),
                Opt("By `a_i − a_j`.",
                    why="Check with numbers: `a_i = 5`, `a_j = 1`, `t = 0`. Before: `5 + 6 = 11`. "
                        "After: `1 + 6 = 7`. The change is `−4 = a_j − a_i`."),
                Opt("By `a_j − a_i`.", correct=True,
                    why="Before: `f_i = t + a_i`, `f_j = t + a_i + a_j`, sum `2t + 2a_i + a_j`. "
                        "After: `2t + 2a_j + a_i`. The difference is `a_j − a_i`: negative "
                        "exactly when the first task was the longer one."),
            ]),
            MCQ(r"""
Why does that one fact prove that doing the tasks by increasing duration is optimal?
""", [
                Opt("Because sorting takes only O(n log n).",
                    why="That is why it is fast, not why it is correct."),
                Opt("Take any optimal order. While a longer task sits directly before a shorter "
                    "one, swap them: `Σ f` never increases. It ends at the sorted order, which "
                    "is therefore optimal too.", correct=True,
                    why="Yes: a bubble sort of an optimal order that never loses anything. This "
                        "is the exchange argument for orderings: every adjacent inversion can "
                        "be fixed without loss."),
                Opt("It shows that no single swap improves the sorted order, so it is optimal.",
                    why="That would only make the sorted order a *local* optimum, which proves "
                        "nothing. The argument runs the other way: it starts from an optimal "
                        "order and walks it to the sorted one without losing anything."),
                Opt("Because the shortest tasks tend to have the earliest deadlines.",
                    why="The deadlines were shown to be irrelevant; no correlation is assumed."),
            ], explain=r"""
On A, B, C, shortest first is B, C, A: `(9 − 1) + (8 − 4) + (5 − 8) = 9`, three times what
the deadline order earned.
"""),
            Numeric(r"""
All `n = 2·10^5` tasks take `10^6`. Roughly how large is `Σ f_i`?
""", answer=2e16, rel=0.5,
                hint="The `k`-th task finishes at `k·10^6`.",
                explain=r"""
`10^6 · n(n+1)/2 ≈ 2·10^16`. That is 10 million times what an `int` holds: every sum is a
`long long`, and the answer is hugely negative.
"""),
            Try("tasks_deadlines", note="Shortest first, and `long long` for every running sum."),
        ]),
        Part("A key nobody guesses", [
            Say(r"""
The neighbour swap also finds orders that nobody would guess. A circus builds a tower of `n`
acrobats, each standing on the one below. Acrobat `i` weighs `w_i` and has strength `s_i`;
their **risk** is the total weight of everyone above them, minus `s_i`. Order the tower so
that the largest risk is as small as possible. `n ≤ 2·10^5`, `w_i, s_i ≤ 10^9`.

Two rules suggest themselves: strongest at the bottom, or heaviest at the bottom.
"""),
            Short(r"""
Acrobats A (`w = 10`, `s = 1`) and B (`w = 1`, `s = 2`). "Strongest at the bottom" puts B
under A. What is the largest risk in that tower?
""", accept=["8"], placeholder="a number",
                explain=r"""
A is on top: risk `0 − 1 = −1`. B carries A: `10 − 2 = 8`. The other tower puts A at the
bottom carrying B: `1 − 1 = 0`, and B on top: `−2`. Largest risk 0 instead of 8. "Heaviest at
the bottom" fails too: with C = `(5, 1)` and D = `(3, 10)` it gives 2, the other order −1.
"""),
            Reflect(r"""
Acrobat `i` stands directly on acrobat `j`, and `W` is the total weight above both. Write the
two risks before swapping them and the two after. What quantity decides which order is
better?
""", answer=r"""
Before (`i` on top): `i` risks `W − s_i`, `j` risks `W + w_i − s_j`. After: `j` risks `W − s_j`,
`i` risks `W + w_j − s_i`. Nobody else changes. If `w_i + s_i ≤ w_j + s_j`, then
`W + w_i − s_j ≤ W + w_j − s_i`, and `W − s_i` is below that as well, so the largest risk
before the swap is at most the largest after it: `i` on top is never worse. The deciding
quantity is `w + s`.
"""),
            MCQ(r"""
So how is the tower ordered, from the top down?
""", [
                Opt("By increasing `s`.",
                    why="That is 'strongest at the bottom', already refuted by A and B."),
                Opt("By increasing `w + s`.", correct=True,
                    why="Yes. A has 11, B has 3, so B goes on top: largest risk 0, the better "
                        "tower. An acrobat's own weight counts *for* going lower, just like "
                        "strength."),
                Opt("By increasing `s − w`, the strength left over.",
                    why="It sounds reasonable, but the swap compares `w_i + s_i` with "
                        "`w_j + s_j`. For A and B, `s − w` is −9 and 1, which puts A on top: "
                        "largest risk 8."),
                Opt("By increasing `w`.",
                    why="That is 'heaviest at the bottom', refuted by C and D."),
            ], explain=r"""
The recipe for ordering problems: write the cost of two neighbours in both orders, cancel
what does not change, and read off a key. The key must give a consistent order (it does here:
it is a number per acrobat), and then any order can be bubble-sorted into it without loss.
"""),
            Try("acrobats", note="Sort by `w + s`. The weight above an acrobat reaches 2·10^14."),
        ]),
        Part("When greedy lies", [
            Say(r"""
Every greedy in this lesson came with an exchange argument. Here is one that has none.

Pay an amount with as few coins as possible. With coins `1, 5, 10, 25`, "take the largest
coin that fits, repeat" is optimal, and it feels like it always should be.
"""),
            Short(r"""
Coins `1, 3, 4`. What is the smallest amount for which "largest coin first" uses more coins
than necessary?
""", accept=["6"], placeholder="an amount",
                hint="Try the amounts in order. For each, find the greedy count and the best count.",
                explain=r"""
6: greedy pays `4 + 1 + 1` (3 coins), but `3 + 3` needs 2. Amounts 1 to 5 all come out right,
which is exactly why this bug survives small tests.
"""),
            Numeric(r"""
The same trap in a knapsack: capacity 10, items (weight, value) `(6, 7)`, `(5, 5)`,
`(5, 5)`, each usable at most once. "Best value per unit of weight first" takes `(6, 7)`
first. What total value does it end with?
""", answer=7,
                explain=r"""
After `(6, 7)` only 4 units remain, and neither 5-weight item fits: 7. Both `(5, 5)` items give
10. If items could be cut (take 4/5 of one), the ratio greedy would be optimal; with whole
items this is a DP problem (algo07).
"""),
            Reflect(r"""
Try the exchange argument on the coin greedy with coins `1, 3, 4` and amount 6. Where exactly
does it break?
""", answer=r"""
The exchange would claim: some optimal answer uses the largest coin that fits, 4, because any
optimal answer can be changed to use a 4 without getting worse. The optimal `3 + 3` cannot:
to use a 4 you must remove coins worth at least 4, and the leftover 2 costs two 1s. Committing
to the 4 destroys the combination the rest needed. For the movies, committing to the earliest
end never removed an option the rest could use. When no swap works, the problem usually needs
DP (algo06: Minimizing Coins).
"""),
            MCQ(r"""
In a contest you have a greedy idea. It passes the samples, and five minutes of thought give
no proof. What is the best move?
""", [
                Opt("Submit: the samples passed.",
                    why="Samples are small and friendly, and a rejected submission costs 20 penalty "
                        "minutes. The 'fewest conflicts' movie rule survives every input you would "
                        "write by hand; the classic counterexample needs 11 carefully placed "
                        "movies, and no sample will contain it."),
                Opt("Try a few more examples by hand.",
                    why="You have already tried the examples a human thinks of. Counterexamples "
                        "to plausible greedies are usually the ones nobody thinks of; a machine "
                        "tries thousands."),
                Opt("Write a brute force for tiny inputs and a random generator, and compare the "
                    "two on thousands of cases before submitting.", correct=True,
                    why="Yes: stress testing (cpp09). It takes ten minutes to set up and finds a "
                        "`1, 3, 4`-style counterexample on its own, which you then shrink by hand."),
                Opt("Abandon it and write a DP.",
                    why="Many greedies are right, and the DP may not fit the limits (times up to "
                        "10^9 in the movie problem). Test first, then decide."),
            ], explain=r"""
Greedy, in contest terms: a short list of candidate rules, a counterexample hunt (by hand,
then by machine), and, for the survivor, an exchange argument sketched in your head.
"""),
        ]),
    ],
    problems=[MOVIE_FESTIVAL, FERRIS_WHEEL, STICK_LENGTHS, TASKS, ACROBATS],
    cards=[
        Card(r"""What is an exchange argument?""",
             r"""Take any optimal solution and show it can be changed, step by step, into one that agrees with the greedy's choices without getting worse. Then the greedy's solution is optimal too."""),
        Card(r"""Maximum number of non-overlapping intervals: the rule?""",
             r"""Sort by end; take every interval that starts at or after the end of the last one taken. (Earliest start and shortest first both fail.)"""),
        Card(r"""Why does `sort` on `vector<pair<int,int>>` of `{start, end}` break interval scheduling?""",
             r"""Pairs compare `.first` first, so it sorts by start. Store `{end, start}` or sort with a comparator on the end."""),
        Card(r"""What does "greedy stays ahead" mean for interval scheduling?""",
             r"""After `k` picks, the greedy's `k`-th interval ends no later than the `k`-th interval of any valid schedule, so no schedule can take more."""),
        Card(r"""Pairs with total weight ≤ x, minimise groups of at most two: the rule?""",
             r"""Sort; pair the heaviest with the lightest if they fit, else the heaviest goes alone. Two indices, `while (i <= j)`."""),
        Card(r"""Which `x` minimises `Σ |p_i − x|`? And `Σ (p_i − x)^2`?""",
             r"""Absolute values: any median (`p[n/2]` after sorting). Squares: the mean."""),
        Card(r"""Order jobs to minimise the sum of completion times?""",
             r"""Shortest first. Swapping neighbours `i, j` changes the sum by `a_j − a_i`, so a longer job before a shorter one can always be fixed."""),
        Card(r"""Tasks and Deadlines (reward `d − f`): why do deadlines not affect the order?""",
             r"""The total is `Σd − Σf`, and `Σd` is the same for every order. Only `Σf` matters: shortest first."""),
        Card(r"""How do you find a sorting key for an ordering problem?""",
             r"""Write the cost of two neighbours `i, j` in both orders, cancel everything that does not change, and read off when `i` first is no worse (e.g. `w_i + s_i ≤ w_j + s_j` for the acrobat tower)."""),
        Card(r"""Coins `1, 3, 4`: where does "largest coin first" fail?""",
             r"""Amount 6: greedy `4 + 1 + 1` (3 coins), optimal `3 + 3` (2). Coin change in general needs DP."""),
        Card(r"""You have an unproven greedy. What do you do before submitting?""",
             r"""Stress test: a brute force for tiny inputs, a random generator, and a loop that compares them. Shrink any counterexample it finds."""),
    ],
)
