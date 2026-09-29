from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _values(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


_BUCKET_PRIME = 42043        # a bucket count libstdc++'s unordered_set passes through


def _anti_hash(rng):
    """Every value is a multiple of 42043: once GCC's unordered_set has 42043 buckets,
    they all share bucket 0 and every insert walks one long chain."""
    n = 200000
    k = 10**9 // _BUCKET_PRIME
    vals = [_BUCKET_PRIME * i for i in range(1, k + 1)]
    rng.shuffle(vals)
    a = vals + [rng.choice(vals) for _ in range(n - k)]
    return f"{n}\n" + " ".join(map(str, a)) + "\n"


def _window(rng, n, k, lo, hi):
    a = [rng.randint(lo, hi) for _ in range(n)]
    return f"{n} {k}\n" + " ".join(map(str, a)) + "\n"


def _window_any(rng, nmax, vmax):
    n = rng.randint(1, nmax)
    return _window(rng, n, rng.randint(1, n), 1, vmax)


def _tickets(rng, n, m, hlo, hhi, tlo, thi):
    h = [rng.randint(hlo, hhi) for _ in range(n)]
    t = [rng.randint(tlo, thi) for _ in range(m)]
    return f"{n} {m}\n" + " ".join(map(str, h)) + "\n" + " ".join(map(str, t)) + "\n"


def _stream(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _stream_sorted(rng, n, desc):
    a = sorted(rng.randint(-10**9, 10**9) for _ in range(n))
    if desc:
        a.reverse()
    return f"{n}\n" + " ".join(map(str, a)) + "\n"


# --------------------------------------------------------------------- problems
DISTINCT = Problem(
    id="distinct_numbers",
    title="Distinct Numbers",
    difficulty="easy",
    source="CSES 1621 - Distinct Numbers",
    complexity="O(n log n)",
    statement=r"""
The census office received a list of `n` ID numbers, with an unknown amount of
double-counting. How many different IDs are on the list?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers x_1, ..., x_n (1 ≤ x_i ≤ 10^9).
""",
    output=r"""
Print one integer: the number of distinct values.
""",
    samples=[
        Test("5\n2 3 2 2 3\n", "2\n"),
    ],
    tests=[
        Test("1\n1000000000\n"),
        Test("6\n7 7 7 7 7 7\n"),
        Test("5\n1000000000 1 999999999 2 1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _values(rng, rng.randint(1, 15), 1, 10), 10),
        Gen("medium random", lambda rng: _values(rng, 3000, 1, rng.choice([100, 10**9])), 3),
        Gen("max size, random", lambda rng: _values(rng, 200000, 1, 10**9), 1, large=True),
        Gen("max size, built against GCC's hash", _anti_hash, 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    set<int> seen;                  // a balanced tree: O(log n) per insert, guaranteed
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        seen.insert(x);             // a value already present is simply ignored
    }
    cout << seen.size() << '\n';
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
    int distinct = 0;
    for (int i = 0; i < n; i++) {
        bool before = false;
        for (int j = 0; j < i; j++) if (a[j] == a[i]) before = true;
        if (!before) distinct++;
    }
    cout << distinct << '\n';
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
    unordered_set<int> seen;        // Python's set(), translated word for word
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        seen.insert(x);
    }
    cout << seen.size() << '\n';
}
""",
    hints=[
        r"""In Python this is `len(set(a))`. C++ has two sets. Which one gives a guarantee, and
which one only an average?""",
        r"""`set<int>` is O(log n) per insert no matter what the values are. With GCC's
`unordered_set<int>`, the hash of `x` is `x` itself, so an input made of multiples of one
bucket-count prime puts everything into a single bucket.""",
    ],
    editorial=r"""
Insert everything into a `set<int>` and print its size: O(n log n), about 0.03 s here.
Sorting a `vector` and counting the positions where the value changes is just as good
(cpp06 shows `sort` + `unique`).

The trap is the word-for-word translation of `len(set(a))`: `unordered_set<int>`. On
random data it is the fastest of all. But GCC hashes an integer to itself and picks the
bucket as `x % bucket_count`, where the bucket count is a known prime (42043 when the table
holds 20,754 to 42,043 elements). The last hidden test consists of multiples of 42043 only:
about 24,000 distinct values, all in bucket 0, and every one of the 2·10^5 inserts walks
that one chain. That test takes about 4 seconds with `unordered_set` and 0.03 s with
`set`.

If you want a hash table anyway, give it a hash nobody can predict (the `SafeHash` with a
time-based seed from the lesson). `reserve(n)` alone only moves the target: it changes the
bucket count to a different, equally predictable prime.
""",
)

WINDOW_DISTINCT = Problem(
    id="window_distinct",
    title="Distinct in Every Window",
    difficulty="easy",
    complexity="O(n log n)",
    statement=r"""
A weather station records one reading per minute. For every block of `k` consecutive
minutes, the analysts want to know how many *different* readings it contains.

Given the `n` readings, print the number of distinct values in each of the `n − k + 1`
windows of length `k`, from left to right.
""",
    input=r"""
The first line has `n` and `k` (1 ≤ k ≤ n ≤ 2·10^5).

The second line has `n` integers x_1, ..., x_n (1 ≤ x_i ≤ 10^9).
""",
    output=r"""
Print `n − k + 1` integers on one line: the number of distinct values in x_1..x_k, in
x_2..x_(k+1), and so on.
""",
    samples=[
        Test("5 3\n1 2 1 3 3\n", "2 3 2\n",
             note="In the third window the value 2 has left. If your map still has the key 2 "
                  "with count 0, `size()` says 3."),
        Test("4 1\n1000000000 7 7 1000000000\n", "1 1 1 1\n"),
    ],
    tests=[
        Test("1 1\n5\n"),
        Test("6 6\n4 4 4 4 4 4\n"),
        Test("6 2\n1 2 1 2 1 2\n"),
        Test("7 3\n5 5 5 9 9 9 5\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _window_any(rng, 12, 5), 12),
        Gen("medium, few values", lambda rng: _window(rng, 2000, rng.randint(1, 2000), 1, 30), 2),
        Gen("medium, wide values", lambda rng: _window(rng, 2000, rng.randint(1, 2000), 1, 10**9), 2),
        Gen("max size, half-length window", lambda rng: _window(rng, 200000, 100000, 1, 10**9), 1, large=True),
        Gen("max size, many repeats", lambda rng: _window(rng, 200000, 100000, 1, 1000), 1, large=True),
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
    map<int, int> cnt;                        // value -> copies inside the window
    for (int i = 0; i < n; i++) {
        cnt[x[i]]++;                          // x[i] enters
        if (i >= k) {                         // x[i-k] leaves
            if (--cnt[x[i - k]] == 0) cnt.erase(x[i - k]);   // no zero-count keys
        }
        if (i >= k - 1) cout << cnt.size() << (i == n - 1 ? '\n' : ' ');
    }
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
    for (int l = 0; l + k <= n; l++) {
        int d = 0;
        for (int i = l; i < l + k; i++) {
            bool seen = false;
            for (int j = l; j < i; j++) if (x[j] == x[i]) seen = true;
            if (!seen) d++;
        }
        cout << d << ' ';
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
    int n, k;
    cin >> n >> k;
    vector<int> x(n);
    for (auto& v : x) cin >> v;
    for (int l = 0; l + k <= n; l++) {
        set<int> s(x.begin() + l, x.begin() + l + k);   // rebuilt for every window
        cout << s.size() << ' ';
    }
    cout << '\n';
}
""",
    hints=[
        r"""Moving from one window to the next, exactly one value enters and one leaves. Keep a
count per value and update two counts per step.""",
        r"""The answer is the number of values with a non-zero count. If you use `cnt.size()`,
a key must disappear when its count reaches 0: `if (--cnt[v] == 0) cnt.erase(v);`.""",
    ],
    editorial=r"""
Keep `map<int, int> cnt` of the values inside the current window. Sliding right by one
adds `x[i]` (`cnt[x[i]]++`) and removes `x[i-k]`. The number of distinct values is the
number of keys, `cnt.size()`, *provided* keys with count 0 are erased:

```cpp
if (--cnt[x[i - k]] == 0) cnt.erase(x[i - k]);
```

Forget the erase and a value that left the window still counts: the first sample fails.
The alternative is to keep a separate `distinct` counter that goes up when a count goes
0 → 1 and down when it goes 1 → 0. Either way, O(log n) per step and O(n log n) in all.
Rebuilding a set for every window costs (n − k + 1)·k inserts, 10^10 when `k = 10^5`.
Values go up to 10^9, so a plain array of counts does not fit (it would after coordinate
compression, cpp06).
""",
)

CONCERT = Problem(
    id="concert_tickets",
    title="Concert Tickets",
    difficulty="medium",
    source="CSES 1091 - Concert Tickets",
    complexity="O((n + m) log n)",
    statement=r"""
There are `n` concert tickets for sale, each with a price. Then `m` customers arrive, one
after another. Each customer announces the most they are willing to pay, and gets the
most expensive remaining ticket whose price does not exceed that amount. That ticket is
then gone.

For every customer, print the price they pay, or `-1` if no remaining ticket is cheap
enough.
""",
    input=r"""
The first line has `n` and `m` (1 ≤ n, m ≤ 2·10^5).

The second line has the ticket prices h_1, ..., h_n (1 ≤ h_i ≤ 10^9).

The third line has the customers' maximum prices t_1, ..., t_m (1 ≤ t_i ≤ 10^9), in order
of arrival.
""",
    output=r"""
Print `m` lines: the price each customer pays, or `-1`.
""",
    samples=[
        Test("5 3\n5 3 7 8 5\n4 8 3\n", "3\n8\n-1\n"),
        Test("3 3\n5 5 2\n6 6 6\n", "5\n5\n2\n",
             note="Two tickets cost 5. When the first customer buys one, how many does your "
                  "erase remove?"),
    ],
    tests=[
        Test("1 1\n10\n9\n"),
        Test("1 2\n10\n10 10\n"),
        Test("4 5\n1000000000 1 1000000000 1\n1000000000 1000000000 1000000000 1 1\n"),
        Test("3 4\n2 2 2\n1 2 3 2\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _tickets(rng, rng.randint(1, 10), rng.randint(1, 10), 1, 10, 1, 12), 14),
        Gen("medium, many equal prices", lambda rng: _tickets(rng, 2000, 2000, 1, 50, 1, 60), 2),
        Gen("medium, wide prices", lambda rng: _tickets(rng, 2000, 2000, 1, 10**9, 1, 10**9), 2),
        Gen("max size, random", lambda rng: _tickets(rng, 200000, 200000, 1, 10**9, 1, 10**9), 1, large=True),
        Gen("max size, nobody can afford much", lambda rng: _tickets(rng, 200000, 200000, 5 * 10**8, 10**9, 1, 5 * 10**8 + 1000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    multiset<int> tickets;                   // sorted, duplicates kept
    for (int i = 0; i < n; i++) {
        int h;
        cin >> h;
        tickets.insert(h);
    }
    for (int i = 0; i < m; i++) {
        int t;
        cin >> t;
        auto it = tickets.upper_bound(t);    // member function: O(log n)
        if (it == tickets.begin()) {         // nothing <= t (and never prev(begin()))
            cout << -1 << '\n';
            continue;
        }
        --it;                                // the largest price <= t
        cout << *it << '\n';
        tickets.erase(it);                   // by iterator: exactly one copy
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
    vector<int> h(n);
    vector<bool> sold(n, false);
    for (auto& x : h) cin >> x;
    for (int i = 0; i < m; i++) {
        int t;
        cin >> t;
        int best = -1;
        for (int j = 0; j < n; j++)
            if (!sold[j] && h[j] <= t && (best == -1 || h[j] > h[best])) best = j;
        if (best == -1) cout << -1 << '\n';
        else { cout << h[best] << '\n'; sold[best] = true; }
    }
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
    multiset<int> tickets;
    for (int i = 0; i < n; i++) {
        int h;
        cin >> h;
        tickets.insert(h);
    }
    for (int i = 0; i < m; i++) {
        int t;
        cin >> t;
        auto it = upper_bound(tickets.begin(), tickets.end(), t);   // std:: version: O(n) here
        if (it == tickets.begin()) { cout << -1 << '\n'; continue; }
        --it;
        cout << *it << '\n';
        tickets.erase(it);
    }
}
""",
    hints=[
        r"""You need a sorted collection with duplicates, fast removal of one element, and
'largest element ≤ t'. That is a `multiset<int>`.""",
        r"""`auto it = ms.upper_bound(t);` is the first price > t. If it is `ms.begin()`, nobody
fits; otherwise `--it` is the answer.""",
        r"""Remove the ticket with `ms.erase(it)`, never `ms.erase(*it)` (that removes every
ticket with the same price). And call the member `ms.upper_bound(t)`, not
`upper_bound(ms.begin(), ms.end(), t)`.""",
    ],
    editorial=r"""
Put the prices in a `multiset<int>`. For a customer with limit `t`, `upper_bound(t)` is the
first price greater than `t`; if that is `begin()`, no ticket is cheap enough, and
otherwise the element just before it is the most expensive affordable ticket. Print it and
erase *that iterator*. O(log n) per customer.

Three traps, each with its own verdict:

- `tickets.erase(price)` erases every ticket with that price: the second sample.
- `--it` on `begin()` (a customer poorer than every ticket) is undefined behaviour: check
  first.
- `upper_bound(tickets.begin(), tickets.end(), t)` compiles and gives the same answers,
  but a multiset's iterators move one step at a time, so the general algorithm walks the
  tree: O(n) per customer, over 30 seconds on the large tests. The member function
  descends the tree in O(log n).
""",
)

RUNNING_MEDIAN = Problem(
    id="running_median",
    title="Running Median",
    difficulty="medium",
    source="LeetCode 295 - Find Median from Data Stream",
    complexity="O(n log n)",
    statement=r"""
A sensor streams `n` integers. After each new value arrives, report the median of all
values received so far. When the count is even, report the *smaller* of the two middle
values.

Formally, after `c` values, print the ⌈c/2⌉-th smallest of them.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 10^6).

The second line has `n` integers a_1, ..., a_n (−10^9 ≤ a_i ≤ 10^9).
""",
    output=r"""
Print `n` integers, one per line: the median after each arrival.
""",
    samples=[
        Test("5\n5 15 1 3 8\n", "5\n5\n5\n3\n5\n"),
        Test("4\n-2 -7 10 -7\n", "-2\n-7\n-2\n-7\n"),
    ],
    tests=[
        Test("1\n-1000000000\n"),
        Test("6\n4 4 4 4 4 4\n"),
        Test("6\n1 2 3 4 5 6\n"),
        Test("6\n6 5 4 3 2 1\n"),
        Test("3\n1000000000 -1000000000 0\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _stream(rng, rng.randint(1, 12), -10, 10), 12),
        Gen("medium random", lambda rng: _stream(rng, 3000, -10**9, 10**9), 2),
        Gen("medium ascending", lambda rng: _stream_sorted(rng, 3000, False), 1),
        Gen("medium descending", lambda rng: _stream_sorted(rng, 3000, True), 1),
        Gen("a million values", lambda rng: _stream(rng, 10**6, -10**5, 10**5), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    priority_queue<int> lo;                              // max-heap: the smaller half
    priority_queue<int, vector<int>, greater<int>> hi;  // min-heap: the larger half
    // invariant: every element of lo <= every element of hi,
    //            lo.size() == hi.size() or lo.size() == hi.size() + 1
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        if (lo.empty() || x <= lo.top()) lo.push(x);
        else hi.push(x);
        if (lo.size() > hi.size() + 1) { hi.push(lo.top()); lo.pop(); }
        else if (hi.size() > lo.size()) { lo.push(hi.top()); hi.pop(); }
        cout << lo.top() << '\n';                        // the ceil(c/2)-th smallest
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
    vector<int> seen;
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        seen.push_back(x);
        vector<int> s = seen;
        sort(s.begin(), s.end());
        cout << s[(s.size() - 1) / 2] << '\n';
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
    vector<int> v;                       // bisect.insort, in C++
    v.reserve(n);
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        v.insert(upper_bound(v.begin(), v.end(), x), x);   // O(n) shift per insert
        cout << v[(v.size() - 1) / 2] << '\n';
    }
}
""",
    hints=[
        r"""Split the values into a lower half and an upper half. Which heap gives you the
largest of the lower half in O(1)? Which gives the smallest of the upper half?""",
        r"""`priority_queue<int> lo;` (max-heap) and `priority_queue<int, vector<int>,
greater<int>> hi;` (min-heap). Keep `lo.size()` equal to `hi.size()` or one more; then the
answer is always `lo.top()`.""",
        r"""Insert into `lo` if `x <= lo.top()` (or `lo` is empty), else into `hi`, then move
one top across if the sizes drift apart.""",
    ],
    editorial=r"""
Keep the smaller half of the values in a max-heap `lo` and the larger half in a min-heap
`hi`, with `lo` holding as many elements as `hi` or one more. Then the ⌈c/2⌉-th smallest
value is exactly `lo.top()`. A new value goes into `lo` if it is at most `lo.top()`, else
into `hi`; if that breaks the size rule, move one top element to the other heap. Each
step is O(log n).

The C++ trap is the heap direction: `priority_queue<int>` is a *max*-heap, the opposite
of `heapq`. A Python solution ported line by line (negating values for the lower half)
turns both heaps upside down and fails the first sample.

The tempting shortcut is Python's `bisect.insort`: a sorted `vector` and `v.insert(pos,
x)`. Each insert shifts half the vector on average; it is a fast `memmove`, and it
survives 2·10^5 values (about 0.6 s here), but at 10^6 values it shifts 2.5·10^11 elements
in total and takes over 15 seconds. The heaps take about 0.1 s.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp05",
    title="STL containers",
    track="cpp",
    order=5,
    summary="Python's set, dict and heapq in C++: sorted trees and hash tables, map's [] that "
            "inserts, multiset's erase that removes every copy, the max-heap, and the "
            "lower_bound that is secretly O(n).",
    prereqs=["cpp04"],
    tags=["set", "map", "multiset", "unordered_map", "priority_queue", "deque", "pair",
          "iterators", "anti-hash"],
    parts=[
        Part("Python's containers, renamed", [
            Say(r"""
Python gives you a handful of containers and you rarely think about what they cost:
`list`, `dict`, `set`, `heapq` on a list. C++'s standard library (the STL) has more of them,
each with its own cost model, and picking the right one is part of almost every contest
solution.

| Python | C++ | what it is |
| `list` | `vector<T>` | growable array (cpp04) |
| `set` | `set<T>` / `unordered_set<T>` | sorted tree / hash table |
| `dict` | `map<K, V>` / `unordered_map<K, V>` | sorted tree / hash table |
| `Counter` | `map<K, int>` | `cnt[x]++` |
| `heapq` | `priority_queue<T>` | binary heap, **largest** on top |
| `collections.deque` | `deque<T>`, `queue<T>`, `stack<T>` | ends only |
| (none) | `multiset<T>` | sorted, keeps duplicates |

Every container holds one element type, fixed when you declare it. The elements are very
often pairs, so start there.
"""),
            Say(r"""
A `pair<A, B>` is a record with two fields; `tuple<A, B, C>` has any number. They are
Python's tuples with fixed types:

```cpp
pair<int, string> p = {3, "bob"};
cout << p.first << ' ' << p.second << '\n';   // 3 bob
auto [score, name] = p;                        // unpacking, as in Python
tuple<int, int, int> t = {1, 2, 3};
cout << get<2>(t) << '\n';                     // 3
```

Pairs and tuples compare the way Python's tuples do: first fields first, and the next
field only breaks ties. Sets, maps, heaps and sorting all use this comparison, so it
decides the order of everything you build out of pairs.
"""),
            Short(r"""
What does this print? (`cout` prints a `bool` as `1` or `0`.)

```cpp
pair<int, int> a = {2, -5}, b = {2, 3}, c = {1, 100};
cout << (a < b) << (c < a) << (b < c) << '\n';
```
""", accept=["110"], placeholder="three digits",
                hint="Compare the first fields; look at the second only when the first are equal.",
                explain=r"""
`110`. `a < b`: first fields tie at 2, and −5 < 3. `c < a`: 1 < 2 decides it, and the 100
never matters. `b < c`: 2 > 1, false. Exactly Python's `(2, -5) < (2, 3)`.
"""),
            MCQ(r"""
You keep `(value, index)` pairs in a structure that always hands out the *largest* pair.
You want the largest value and, among equal values, the *smallest* index. What do you
store?
""", [
                Opt("`{value, index}`",
                    why="Ties on value are then broken by the *larger* index: the second field is "
                        "compared in the same direction as the first."),
                Opt("`{index, value}`",
                    why="Now the index is compared first, so you get the largest index whatever "
                        "the values are."),
                Opt("`{value, -index}`", correct=True,
                    why="Yes. Among equal values, the smallest index has the largest `-index`. "
                        "Negate it back when you read the pair."),
                Opt("`{-value, index}`",
                    why="That hands out the *smallest* value, with the largest index among ties: "
                        "the opposite of both goals."),
            ], explain=r"""
Negating one field flips the order of that field only. It comes back with `priority_queue`,
which, unlike `heapq`, hands out the largest element.
"""),
        ]),
        Part("set: a sorted tree, not a hash table", [
            Say(r"""
Python's `set` is a hash table: O(1) on average, no order. C++'s `set<T>` is a **balanced
binary search tree** (a red-black tree). Insert, erase and lookup are all O(log n), and the
elements are always kept in sorted order. C++ has a hash table too, `unordered_set<T>`; it
comes at the end of this part, with a warning.
"""),
            Short(r"""
What does this print?

```cpp
set<int> s;
s.insert(5); s.insert(1); s.insert(3); s.insert(1);
for (int x : s) cout << x << ' ';
```
""", accept=["1 3 5"], placeholder="what it prints",
                explain=r"""
`1 3 5`. Iterating a `set` visits the values in increasing order, always, and the second
`1` was ignored because a set holds each value once. (`s.insert(x).second` tells you
whether `x` was new.) So a `set` is also a way to sort and deduplicate at once.
"""),
            Say(r"""
The operations you will use, for a `set<int> s`:

```cpp
s.insert(x);     // O(log n); no effect if x is already there
s.erase(x);      // O(log n), by value
s.count(x)       // 1 or 0: Python's `x in s`
s.find(x)        // iterator to x, or s.end() if absent
s.size()
*s.begin()       // the smallest element
```

An **iterator** is C++'s idea of a position in a container: `*it` is the element there and
`++it` moves to the next one (for a set: the next larger value). `s.end()` is the position
*one past* the last element, a marker, not an element.
"""),
            MCQ(r"""
`s` is a non-empty `set<int>`. Which expression is its largest element?
""", [
                Opt("`s[s.size() - 1]`",
                    why="A set has no indexing: this does not compile. A tree cannot jump to the "
                        "k-th element the way an array can."),
                Opt("`*s.end()`",
                    why="`end()` is one past the last element. Dereferencing it is undefined "
                        "behaviour: garbage, or a crash."),
                Opt("`s.back()`",
                    why="`back()` exists on `vector` and `deque`, not on `set`: a compile error."),
                Opt("`*s.rbegin()`", correct=True,
                    why="Yes: the reverse iterator's begin is the last element. `*prev(s.end())` "
                        "is the same thing."),
            ]),
            Numeric(r"""
A `set<int>` holds 10^6 elements. About how many comparisons does one `s.count(x)` make?
(Assume a perfectly balanced tree.)
""", answer=20, rel=0.5, unit="comparisons",
                hint="The tree is balanced. How tall is a balanced binary tree with 10^6 nodes?",
                explain=r"""
About log2(10^6) ≈ 20 (a red-black tree guarantees at most about twice that). Each
comparison follows a pointer to a node elsewhere in memory, so the constant is not small:
10^6 lookups in a 10^6-element `set` take about 0.7 s here, against 0.1 s for binary search
in a sorted `vector` (cpp06).
"""),
            Say(r"""
`unordered_set<T>` is the hash table: same `insert`/`erase`/`count`/`find`, O(1) *on
average*, iteration in no particular order, and no order-based search. For plain
membership it is usually the fastest option.

"On average" hides something. In GCC's library the hash of an integer is the integer
itself (`hash<int>()(12345)` is `12345`), the bucket is `hash % bucket_count`, and the
bucket count walks through a fixed list of primes as the table grows: 13, 29, 59, 127,
..., 20753, 42043, 85229, ... A table moves up to the next prime in that list when it
holds more elements than it has buckets. Each bucket is a linked list.
"""),
            MCQ(r"""
Someone feeds your `unordered_set<int>` values that are all multiples of 42043. Once the
table has grown to 42043 buckets, what does each insert cost?
""", [
                Opt("O(1): that is what a hash table is for.",
                    why="Only if the values spread over the buckets. Every multiple of 42043 has "
                        "`x % 42043 == 0`: they all land in bucket 0."),
                Opt("O(log n), because long buckets are turned into trees.",
                    why="Java's HashMap does that since Java 8. GCC's `unordered_set` does not: "
                        "a bucket stays a linked list."),
                Opt("O(number of elements already in the set).", correct=True,
                    why="Yes. Each insert must scan bucket 0's whole chain for a duplicate: the "
                        "hash table has turned into a linked list."),
                Opt("Nothing bad: the table notices the long chain and rehashes.",
                    why="It rehashes when the element *count* passes the bucket count, not when "
                        "one chain is long. And any prime it moves to is just as predictable."),
            ]),
            Numeric(r"""
With values up to 10^9 there are about 24,000 multiples of 42043. Suppose each of
2·10^5 inserts walks a chain of 2·10^4 nodes. How many node visits is that?
""", answer=4e9, rel=0.5, unit="node visits",
                explain=r"""
2·10^5 · 2·10^4 = 4·10^9, each one a pointer chase. Measured on this machine with exactly
such an input: about 3.9 s for `unordered_set`, 0.03 s for `set`. On Codeforces people
build these inputs after a contest to "hack" solutions that trust the default hash.
"""),
            Say(r"""
Three ways out:

- Use `set`. O(log n) is a guarantee, and for 2·10^5 elements it is plenty fast.
- Sort a `vector` and drop duplicates (cpp06): usually the fastest of all.
- Keep the hash table, but with a hash an attacker cannot predict. Paste this (cpp07
  explains `struct`s):

```cpp
struct SafeHash {
    size_t operator()(unsigned long long x) const {
        static const unsigned long long seed =
            chrono::steady_clock::now().time_since_epoch().count();
        x += seed + 0x9e3779b97f4a7c15ULL;             // splitmix64
        x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
        x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
        return x ^ (x >> 31);
    }
};
unordered_set<long long, SafeHash> s;
```

`s.reserve(n)` (allocate the buckets up front) saves the rehashing and makes a hash table
faster, but it is not a defence: it only changes which prime the attacker needs.
"""),
            Try("distinct_numbers", note="In Python this is `len(set(a))`. One hidden test was "
                "built against GCC's integer hash."),
        ]),
        Part("map, and the [] that writes", [
            Say(r"""
`map<K, V>` is a sorted dictionary: a balanced tree of key-value pairs ordered by key,
O(log n) per operation. `unordered_map<K, V>` is the hash version, with the same caveat
as `unordered_set`.

Counting is where maps earn their keep:

```cpp
map<string, int> cnt;
for (auto& w : words) cnt[w]++;
for (auto& [word, c] : cnt)          // in sorted key order
    cout << word << ' ' << c << '\n';
```

`cnt[w]++` works for a word never seen before because `m[k]` does more than read: if `k`
is absent it **inserts** `k` with a default value (0 for numbers, `""` for strings, an
empty vector...) and returns a reference to it. Python's `dict` raises `KeyError` there;
a C++ `map` behaves like a `defaultdict`, always, even when you only meant to look.
"""),
            Short(r"""
What does this print?

```cpp
map<string, int> m;
m["apple"] = 3;
if (m["pear"] == 0) cout << "no pears ";
cout << m.size() << '\n';
```
""", accept=["no pears 2"], placeholder="what it prints",
                explain=r"""
`no pears 2`. Reading `m["pear"]` created the key `pear` with value 0, so the map now has
two keys. One stray lookup is harmless; a loop of them on absent keys fills the map with
phantom keys that every later `size()` and every iteration will see.
"""),
            MCQ(r"""
How do you test whether `k` is a key of `m` without inserting it?
""", [
                Opt("`if (m[k] != 0)`",
                    why="This inserts `k` when it is absent, and it cannot tell 'absent' from "
                        "'present with value 0'."),
                Opt("`if (m.contains(k))`",
                    why="That is C++20. Contest judges often compile C++17, as this one does, and "
                        "there it is a compile error."),
                Opt("`if (m.count(k))` or `if (m.find(k) != m.end())`", correct=True,
                    why="Yes. `count` is 0 or 1 for a map. `find` also gives you the position, so "
                        "you can read `it->second` without a second lookup."),
                Opt("`m.at(k)`",
                    why="`at` does not insert, but on a missing key it throws `out_of_range`, "
                        "which ends your program: a run-time error, not a test."),
            ]),
            Say(r"""
The mirror image of `cnt[x]++` is taking something away: the count goes down, and at zero
the key should disappear. It does not disappear by itself.
"""),
            Short(r"""
What does this print?

```cpp
map<int, int> cnt;
for (int x : {4, 7, 4}) cnt[x]++;
cnt[7]--;
cout << cnt.size() << '\n';
```
""", accept=["2"], placeholder="a number",
                explain=r"""
`2`. Key 7 is still there, with count 0. If `cnt.size()` is meant to be "how many distinct
values are present", it is now wrong. The idiom that keeps the map honest:

```cpp
if (--cnt[x] == 0) cnt.erase(x);
```
"""),
            Numeric(r"""
Now a problem: for every window of `k` consecutive elements in an array of `n`, print how
many distinct values it contains. Building a fresh `set` for each window costs about
(n − k + 1)·k inserts. With `n = 2·10^5` and `k = 10^5`, how many is that?
""", answer=1e10, rel=0.5, unit="inserts",
                explain=r"""
About 10^5 windows times 10^5 inserts: 10^10, each O(log k). Measured rate here: about
7·10^6 inserts per second, so roughly 25 minutes for a one-second problem. Between
two neighbouring windows only two elements differ: one enters, one leaves. So update two
counts in one `map` per step, erase keys that reach zero, and read `cnt.size()`: O(log n)
per window.
"""),
            Try("window_distinct", note="One map of counts, two updates per step. Watch the "
                "first sample's third window."),
        ]),
        Part("multiset: a sorted bag", [
            Say(r"""
`multiset<T>` is a sorted tree that keeps duplicates: in effect a sorted list with
O(log n) insert and erase anywhere. Python has no built-in equivalent (the closest is the
third-party `SortedList`), and it is one of the most useful containers in contests.

Most of its API is `set`'s. One call does more than you would guess.
"""),
            Short(r"""
What does this print?

```cpp
multiset<int> ms = {5, 5, 5, 8};
ms.erase(5);
cout << ms.size() << '\n';
```
""", accept=["1"], placeholder="a number",
                explain=r"""
`1`. `erase(value)` removes *every* copy of the value: all three fives are gone. To remove
exactly one copy, erase by iterator:

```cpp
auto it = ms.find(5);
if (it != ms.end()) ms.erase(it);    // one copy
```
"""),
            MCQ(r"""
And if 7 is not in the multiset, what does `ms.erase(ms.find(7))` do?
""", [
                Opt("Nothing: erasing a missing element is a no-op.",
                    why="That is `ms.erase(7)`. Here `ms.find(7)` returns `ms.end()`, and you are "
                        "erasing *that*."),
                Opt("It throws an exception.",
                    why="Standard containers do not check iterators; nothing is thrown. That is "
                        "C++'s trade: speed instead of guarantees."),
                Opt("Undefined behaviour: `find` returned `end()`, which is not an element.",
                    correct=True,
                    why="Right. It may crash, corrupt the tree, or seem to work until a later "
                        "test. Check `it != ms.end()` first."),
                Opt("It removes the largest element.",
                    why="`end()` is one past the largest element; it is not the largest."),
            ]),
            Say(r"""
What sorted containers can do and hash tables cannot is search by order. `set` and
`multiset` both have:

```cpp
ms.lower_bound(x)   // first element >= x   (end() if there is none)
ms.upper_bound(x)   // first element >  x   (end() if there is none)
```

Both are O(log n) and return iterators, which you move with `++it` / `--it` or
`next(it)` / `prev(it)`.
"""),
            Short(r"""
`ms` is the multiset `{10, 20, 20, 30}`. What is `*prev(ms.upper_bound(25))`?
""", accept=["20"], placeholder="a number",
                explain=r"""
`20`. `upper_bound(25)` points at 30, the first element greater than 25; the element just
before it is the **largest element ≤ 25**. That is the idiom for "the best thing that
still fits": `prev(upper_bound(x))`. For "the smallest element ≥ x" it is just
`lower_bound(x)`.
"""),
            MCQ(r"""
Same `ms`. What goes wrong with `*prev(ms.upper_bound(5))`?
""", [
                Opt("Nothing: it is 10.",
                    why="`upper_bound(5)` is already `begin()` (10 is the first element greater "
                        "than 5), so there is nothing before it."),
                Opt("It returns `ms.end()`, the 'not found' marker.",
                    why="`prev(begin())` does not wrap around to `end()`; it steps off the front "
                        "of the tree."),
                Opt("Undefined behaviour: `upper_bound(5)` is `begin()` and nothing precedes it. "
                    "Check `it == ms.begin()` first.", correct=True,
                    why="Yes. That comparison is exactly how you detect 'no element ≤ x'."),
            ]),
            Say(r"""
There are two `lower_bound`s, and they look almost the same:

```cpp
auto a = ms.lower_bound(x);                      // member function
auto b = lower_bound(ms.begin(), ms.end(), x);   // general algorithm (cpp06)
```

Both return the same iterator. The general algorithm is a binary search written for any
sorted range, and it reaches the middle with "jump k positions ahead". A tree's iterators
cannot jump: they only step to the neighbour. So on a `set` or `multiset`, the general
algorithm reaches the middle by *walking* there.
"""),
            Numeric(r"""
A multiset has 2·10^5 elements. If each call of `lower_bound(ms.begin(), ms.end(), x)`
walks through the whole multiset once, how many steps do 2·10^5 calls take?
""", answer=4e10, rel=0.5, unit="steps",
                explain=r"""
4·10^10, and the truth is about twice that: the algorithm first walks the whole range to
measure its length, then half of it, a quarter, and so on. It still makes only O(log n)
*comparisons*, which is why it looks innocent. The member `ms.lower_bound(x)` descends the
tree in about 18 steps per call. On this lesson's Concert Tickets, the general algorithm
runs for more than 30 seconds; the member function, a few hundredths of a second.
"""),
            Try("concert_tickets", note="A multiset, `upper_bound`, and three ways to get it wrong: "
                "erase by value, `prev(begin())`, and the non-member `upper_bound`."),
        ]),
        Part("priority_queue: a heap, upside down", [
            Say(r"""
`priority_queue<T>` is a binary heap, like `heapq`, with three operations: `push(x)` in
O(log n), `top()` in O(1), `pop()` in O(log n). There is no iteration, no erasing an
arbitrary element, no lookup.

One difference catches every Python programmer:

```cpp
priority_queue<int> pq;
for (int x : {3, 1, 4, 1, 5}) pq.push(x);
cout << pq.top() << '\n';
```
"""),
            Short(r"""
What does it print?
""", accept=["5"], placeholder="a number",
                explain=r"""
`5`. C++'s `priority_queue` is a **max**-heap by default; `heapq` is a min-heap. In Python
you negate values to get a max-heap; in C++ you negate, or change the comparator, to get a
min-heap.
"""),
            MCQ(r"""
Which declaration is a min-heap of `int`?
""", [
                Opt("`priority_queue<int, greater<int>> pq;`",
                    why="The second template argument is the underlying container, not the "
                        "comparison: this is a compile error several screens long."),
                Opt("`priority_queue<int, vector<int>, greater<int>> pq;`", correct=True,
                    why="Yes. Second argument: the container (always `vector<T>` in practice). "
                        "Third: the comparison. `greater` puts the smallest element on top."),
                Opt("`priority_queue<int, vector<int>, less<int>> pq;`",
                    why="That is the default written out: a max-heap. `less` means the largest "
                        "element comes out first."),
            ]),
            MCQ(r"""
Python's `x = heapq.heappop(h)` removes the top and returns it. Which C++ does the same
for a `priority_queue<int> pq`?
""", [
                Opt("`int x = pq.pop();`",
                    why="`pop()` returns `void`; the compiler says 'void value not ignored as it "
                        "ought to be'. It only removes."),
                Opt("`int x = pq.top(); pq.pop();`", correct=True,
                    why="Yes: read, then remove. Both are undefined behaviour on an empty heap, so "
                        "loops check `!pq.empty()` first."),
                Opt("`int x = pq.front(); pq.pop_front();`",
                    why="Those are `queue`/`deque` names. A `priority_queue` has `top` and `pop`."),
            ]),
            Say(r"""
A classic that needs both kinds of heap: numbers arrive one at a time, and after each one
you must report the median so far. Sorting after every arrival is O(n^2 log n).
Inserting into a sorted `vector` is O(n) per number because of the shifting.

The standard trick keeps the numbers split into a lower half and an upper half, so the
median always sits at the boundary between them.
"""),
            Reflect(r"""
Which kind of heap should hold the lower half, which the upper half, and what do you keep
true about their sizes so that the median is always one `top()` away?
""", answer=r"""
The lower half goes in a max-heap, so its top is the largest of the small numbers; the
upper half goes in a min-heap, so its top is the smallest of the large numbers. Keep the
sizes equal, or the lower heap one larger; then the (lower) median is the top of the lower
heap. After each insertion, if the sizes drift apart, move one top element across. Every
step is O(log n).
"""),
            MCQ(r"""
You port a Python solution line by line. `heappush(lo, -x)` (negated, to make `heapq` a
max-heap) becomes `lo.push(-x)`, and `heappush(hi, x)` becomes `hi.push(x)`, with both
declared as `priority_queue<int>`. What do you get?
""", [
                Opt("A correct program: the logic is unchanged.",
                    why="The containers changed: `heapq` is a min-heap and `priority_queue` a "
                        "max-heap, so every heap-order assumption flips."),
                Opt("Only `hi` is wrong: it now hands out its largest element.",
                    why="`lo` is wrong too: a max-heap of `-x` has the largest `-x` on top, "
                        "and that is the *smallest* `x`."),
                Opt("Both heaps are upside down: `lo` hands out the smallest of the lower half "
                    "and `hi` the largest of the upper half.", correct=True,
                    why="Yes. Negation was a workaround for `heapq`'s direction; in C++ it now "
                        "works against you."),
            ], explain=r"""
Translate the intent ("largest of the lower half"), not the lines. In C++:
`priority_queue<int> lo;` and `priority_queue<int, vector<int>, greater<int>> hi;`, with no
negation anywhere.
"""),
            Try("running_median", note="Up to 10^6 values. A sorted `vector` with `insert` is "
                "fast per step, but not a million steps fast."),
        ]),
        Part("stack, queue, deque, and choosing", [
            Say(r"""
The last three are thin:

```cpp
stack<int> st;  st.push(x);  st.top();   st.pop();   // Python: list append / pop
queue<int> q;   q.push(x);   q.front();  q.pop();    // collections.deque, popleft
deque<int> d;   d.push_front(x);  d.push_back(x);
                d.pop_front();    d.pop_back();    d[i];
```

`deque` is O(1) at both ends and still indexable. As with the heap, `pop()` returns
nothing, and `top()`, `front()` or `pop()` on an empty container is undefined behaviour,
not an exception.
"""),
            Short(r"""
What does this print?

```cpp
deque<int> d;
d.push_back(1); d.push_back(2);
d.push_front(3); d.push_front(4);
d.pop_back();
for (int x : d) cout << x << ' ';
```
""", accept=["4 3 1"], placeholder="what it prints",
                explain=r"""
`4 3 1`. After the pushes the deque is `4 3 1 2`; `pop_back` removes the 2.
"""),
            MCQ(r"""
A BFS uses a `vector<int>` as its queue and takes the front with `v.erase(v.begin())`.
10^6 vertices pass through it. What is wrong?
""", [
                Opt("Nothing: `erase` is O(1).",
                    why="Erasing the front shifts every remaining element one place left: O(n) per "
                        "call, exactly like Python's `list.pop(0)`."),
                Opt("Each front erase is O(n), so the BFS is O(n^2): use `queue` or `deque`.",
                    correct=True,
                    why="Yes. With 10^6 elements that is up to ~5·10^11 element moves. `queue` pops "
                        "the front in O(1)."),
                Opt("It is fine after `v.reserve(n)`.",
                    why="`reserve` sets the capacity, so pushes never reallocate. It does nothing "
                        "about the shifting on every front erase."),
            ]),
            Say(r"""
The whole lesson in one table:

| you need | use | cost |
| membership | `set`, or `unordered_set` with a safe hash | O(log n) / O(1) avg |
| a count per key | `map<K, int>` | O(log n) |
| sorted, with duplicates, remove one | `multiset` | O(log n) |
| nearest element ≥ x or ≤ x | member `lower_bound` / `upper_bound` | O(log n) |
| repeatedly take the max (or min) | `priority_queue` | O(log n) |
| first in first out / last in first out | `queue` / `stack` | O(1) |
| both ends | `deque` | O(1) |
| keys are small integers | a plain `vector` indexed by key | O(1), fastest |

The last row matters more than it looks. Counting 5·10^6 keys in `[0, 10^6]` on this
machine: `map` 3.1 s, `unordered_map` 0.08 s, `vector<int> cnt(1000001)` under 0.01 s.
"""),
            MCQ(r"""
You process 2·10^5 operations: "add x", "remove one copy of x", and "what is the smallest
element ≥ y?". Which container?
""", [
                Opt("`priority_queue<int>`",
                    why="A heap sees only its top: it cannot remove an arbitrary copy, and it "
                        "cannot search for y."),
                Opt("`unordered_multiset<int>`",
                    why="No order: finding the smallest element ≥ y means scanning everything."),
                Opt("A `vector<int>` kept sorted",
                    why="The search is O(log n), but every add and remove shifts elements: O(n) "
                        "each, 4·10^10 in the worst case."),
                Opt("`multiset<int>`", correct=True,
                    why="All three are O(log n): `insert(x)`, `erase(find(x))` after checking "
                        "`find` did not return `end()`, and `lower_bound(y)`."),
            ]),
            MCQ(r"""
You need the maximum of a changing collection, but only ever remove the current maximum.
`priority_queue` or `multiset`?
""", [
                Opt("`priority_queue`: it does exactly this, in a flat array, with a smaller "
                    "constant.", correct=True,
                    why="Yes. A heap lives in one `vector`, so it has no per-element allocation "
                        "or pointer chasing. Reach for `multiset` when you also need to remove "
                        "arbitrary elements or search by value."),
                Opt("`multiset`: it can do everything a heap can, so it is always the safer "
                    "choice.",
                    why="It can, and it is correct, but each element is a separately allocated "
                        "tree node: typically several times slower than a heap for the same "
                        "pushes and pops."),
                Opt("Neither: sort once and read from the back.",
                    why="The collection changes between queries; a one-time sort goes stale "
                        "after the next insertion."),
            ]),
        ]),
    ],
    problems=[DISTINCT, WINDOW_DISTINCT, CONCERT, RUNNING_MEDIAN],
    cards=[
        Card(r"""C++ `set`/`map` vs Python `set`/`dict`: what is different?""",
             r"""C++ `set`/`map` are balanced search trees: O(log n), iterated in sorted order, with `lower_bound`/`upper_bound`. The hash tables are `unordered_set`/`unordered_map`."""),
        Card(r"""What does `m[k]` do when `k` is not in the `map`?""",
             r"""Inserts `k` with a default value (0, "", empty) and returns a reference to it. To test membership without inserting: `m.count(k)` or `m.find(k) != m.end()`."""),
        Card(r"""How do you decrement a count in a `map` so that `size()` stays the number of distinct keys?""",
             r"""`if (--cnt[x] == 0) cnt.erase(x);`"""),
        Card(r"""Remove one copy of `x` from a `multiset` (and what does `ms.erase(x)` do)?""",
             r"""`auto it = ms.find(x); if (it != ms.end()) ms.erase(it);`. `ms.erase(x)` removes every copy."""),
        Card(r"""Largest element ≤ x in a `set`/`multiset` `s`?""",
             r"""`auto it = s.upper_bound(x); if (it != s.begin()) { --it; /* *it */ } else { /* none */ }`"""),
        Card(r"""`s.lower_bound(x)` vs `lower_bound(s.begin(), s.end(), x)` on a `set`?""",
             r"""Same result. The member is O(log n); the general algorithm walks the tree's iterators step by step: O(n) per call."""),
        Card(r"""Default order of `priority_queue<int>`, and how to declare a min-heap?""",
             r"""Max-heap (largest on top), the opposite of `heapq`. Min-heap: `priority_queue<int, vector<int>, greater<int>>`."""),
        Card(r"""Python `x = heappop(h)` in C++?""",
             r"""`int x = pq.top(); pq.pop();` (`pop()` returns `void`; both are undefined behaviour on an empty heap)."""),
        Card(r"""How do pairs and tuples compare?""",
             r"""Lexicographically, like Python tuples: first field, then the next one only on ties. Store `{value, -index}` to prefer the smallest index among equal values in a max-structure."""),
        Card(r"""Why can `unordered_set<int>` TLE, and the fix?""",
             r"""GCC hashes an integer to itself and uses prime bucket counts, so multiples of that prime all share one bucket: O(n) per operation. Use `set`, sort+unique, or a randomized hash (splitmix64 with a time seed)."""),
        Card(r"""Largest element of a non-empty `set` `s`?""",
             r"""`*s.rbegin()` or `*prev(s.end())`. `*s.end()` is undefined behaviour; `s.back()` and `s[i]` do not compile."""),
        Card(r"""Queue with O(1) pops at the front?""",
             r"""`queue<T>` (`push`, `front`, `pop`) or `deque<T>` (`push_front/back`, `pop_front/back`). `v.erase(v.begin())` on a vector is O(n)."""),
    ],
)
