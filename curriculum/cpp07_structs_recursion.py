from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _meetings(rng, n, tmax, maxlen):
    rows = []
    for _ in range(n):
        s = rng.randint(0, tmax - 1)
        e = rng.randint(s + 1, min(tmax, s + maxlen))
        rows.append(f"{s} {e}")
    return f"{n}\n" + "\n".join(rows) + "\n"


def _meetings_small(rng):
    return _meetings(rng, rng.randint(1, 10), 8, 8)


def _meetings_chain(rng, n):
    """Back-to-back meetings in shuffled order: every end time is someone's start time."""
    rows = [f"{i} {i + 1}" for i in range(n)]
    rng.shuffle(rows)
    return f"{n}\n" + "\n".join(rows) + "\n"


def _gray_check(inp, expected, got):
    n = int(inp.split()[0])
    toks = got.split()
    if len(toks) != 1 << n:
        return False, f"expected {1 << n} strings, found {len(toks)}"
    seen = set()
    prev = None
    for i, t in enumerate(toks, 1):
        if len(t) != n or t.strip("01"):
            return False, f"line {i}: `{t[:24]}` is not a string of {n} bits"
        v = int(t, 2)
        if v in seen:
            return False, f"line {i}: `{t}` appears twice"
        seen.add(v)
        if prev is not None and bin(prev ^ v).count("1") != 1:
            return False, f"lines {i - 1} and {i} differ in {bin(prev ^ v).count('1')} bits, not 1"
        prev = v
    return True, ""


def _codes(rng, count):
    """Concatenated letter codes 1..26: always at least one decoding."""
    return "".join(str(rng.randint(1, 26)) for _ in range(count))


def _digits_small(rng):
    if rng.random() < 0.3:
        s = "".join(rng.choice("0123456789") for _ in range(rng.randint(1, 12)))
    else:
        s = _codes(rng, rng.randint(1, 8))
    return s + "\n"


def _digits_long(rng, length, alphabet):
    return "".join(rng.choice(alphabet) for _ in range(length))


def _days(rng, t, nmin, nmax, vmax):
    out = [str(t)]
    for _ in range(t):
        n = rng.randint(nmin, nmax)
        out.append(str(n))
        out.append(" ".join(str(rng.randint(1, vmax)) for _ in range(n)))
    return "\n".join(out) + "\n"


def _days_small(rng):
    return _days(rng, rng.randint(1, 5), 1, 8, 5)


# --------------------------------------------------------------------- problems
MEETING_ROOMS = Problem(
    id="meeting_rooms",
    title="Meeting Rooms",
    difficulty="medium",
    source="LeetCode 253 - Meeting Rooms II",
    complexity="O(n log n)",
    statement=r"""
Tomorrow's calendar has `n` meetings. Meeting `i` runs from time s_i to time e_i and
needs a room for the half-open interval [s_i, e_i): at the moment e_i its room is free
again, so a meeting starting exactly at e_i can use it.

What is the smallest number of rooms that fits every meeting?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has two integers s_i and e_i (0 ≤ s_i < e_i ≤ 10^9).
""",
    output=r"""
Print one integer: the minimum number of rooms.
""",
    samples=[
        Test("3\n0 30\n5 10\n15 20\n", "2\n"),
        Test("3\n5 8\n1 5\n8 10\n", "1\n",
             note="The meeting that ends at 5 frees its room for the one that starts at 5. "
                  "When an end and a start happen at the same time, which do you process "
                  "first?"),
    ],
    tests=[
        Test("1\n0 1000000000\n"),
        Test("5\n3 7\n3 7\n3 7\n3 7\n3 7\n"),
        Test("4\n1 10\n2 9\n3 8\n4 7\n"),
        Test("6\n4 6\n0 2\n2 4\n6 8\n8 10\n10 12\n"),
    ],
    gens=[
        Gen("small random", _meetings_small, 14),
        Gen("medium, many equal times", lambda rng: _meetings(rng, 2000, 60, 20), 2),
        Gen("medium, back to back", lambda rng: _meetings_chain(rng, 2000), 1),
        Gen("max size, wide times", lambda rng: _meetings(rng, 200000, 10**9, 10**6), 1, large=True),
        Gen("max size, many equal times", lambda rng: _meetings(rng, 200000, 1000, 30), 1, large=True),
        Gen("max size, back to back", lambda rng: _meetings_chain(rng, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

struct Event {
    int time, delta;                 // delta: +1 a meeting starts, -1 one ends
    bool operator<(const Event& o) const {
        return tie(time, delta) < tie(o.time, o.delta);   // equal times: ends (-1) first
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<Event> ev;
    ev.reserve(2 * n);
    for (int i = 0; i < n; i++) {
        int s, e;
        cin >> s >> e;
        ev.push_back({s, +1});
        ev.push_back({e, -1});
    }
    sort(ev.begin(), ev.end());      // a vector, not a set: equal events must all stay
    int running = 0, best = 0;
    for (const Event& x : ev) {
        running += x.delta;          // meetings in progress right after this event
        best = max(best, running);
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
    vector<int> s(n), e(n);
    for (int i = 0; i < n; i++) cin >> s[i] >> e[i];
    int best = 0;
    for (int i = 0; i < n; i++) {             // the busiest moment is some start time
        int c = 0;
        for (int j = 0; j < n; j++) if (s[j] <= s[i] && s[i] < e[j]) c++;
        best = max(best, c);
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""Turn every meeting into two events: at s_i one more room is busy, at e_i one fewer.
Sort the events by time and keep a running count; the answer is its maximum.""",
        r"""At equal times the order matters: an end at time 5 must be processed before a start
at time 5. A `struct Event { int time, delta; }` with `operator<` comparing
`tie(time, delta)` does exactly that, because −1 < +1.""",
        r"""Keep the events in a `vector` and `sort` it. A `set<Event>` would merge two
meetings that start at the same time into one event.""",
    ],
    editorial=r"""
The number of rooms needed is the largest number of meetings in progress at one moment
(one room per meeting is clearly needed then, and assigning each new meeting any free room
never needs more). Make two events per meeting, (s, +1) and (e, −1), sort them, and sweep
with a running count. O(n log n).

Everything interesting is in the order of events with equal times. Since [s, e) frees the
room at `e`, an end must come before a start at the same time. With
`tie(time, delta) < tie(o.time, o.delta)` and ends encoded as −1, the struct's own
`operator<` guarantees it. Sorting by time alone leaves ties in whatever order `sort`
likes: the second sample lists its meetings so that the start at time 5 comes before the
end at time 5, and a time-only comparator prints 2. Storing the events in a `set<Event>`
silently merges equal events (five identical meetings become one), which a hidden test
catches.
""",
)

GRAY_CODE = Problem(
    id="gray_code",
    title="Gray Code",
    difficulty="easy",
    source="CSES 2205 - Gray Code",
    complexity="O(2^n · n)",
    statement=r"""
A **Gray code** of length `n` is a list of all 2^n bit strings of length `n` in which any
two consecutive strings differ in exactly one bit.

Print a Gray code of length `n`. Any valid one is accepted.
""",
    input=r"""
One integer `n` (1 ≤ n ≤ 16).
""",
    output=r"""
Print 2^n lines, each a string of `n` characters `0`/`1`, forming a Gray code.
""",
    samples=[
        Test("2\n", "00\n01\n11\n10\n"),
    ],
    tests=[Test(f"{n}\n") for n in (1, 3, 4, 5, 6, 7, 8, 10, 12, 15, 16)],
    checker=_gray_check,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    // gray(k): "0" + gray(k-1), then "1" + gray(k-1) reversed
    auto gray = [&](auto&& self, int k) -> vector<string> {
        if (k == 0) return {""};
        vector<string> prev = self(self, k - 1), res;
        for (const string& s : prev) res.push_back("0" + s);
        for (int i = (int)prev.size() - 1; i >= 0; i--) res.push_back("1" + prev[i]);
        return res;
    };
    for (const string& s : gray(gray, n)) cout << s << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    for (int i = 0; i < (1 << n); i++) {
        int g = i ^ (i >> 1);
        for (int b = n - 1; b >= 0; b--) cout << ((g >> b) & 1);
        cout << '\n';
    }
}
""",
    hints=[
        r"""Build the code for `n` from the code for `n − 1`. Prefixing a list with 0 keeps its
one-bit steps; the problem is joining two halves.""",
        r"""First half: `0` + each string of gray(n − 1). Second half: `1` + each string of
gray(n − 1) *in reverse order*. The seam is `0x` next to `1x` for the same `x`.""",
        r"""Inside `main`, write it as `auto gray = [&](auto&& self, int k) -> vector<string>
{ ... self(self, k - 1) ... };` and call `gray(gray, n)`.""",
    ],
    editorial=r"""
The reflected construction: gray(0) is the list with the empty string; gray(k) is
`0` + gray(k − 1) followed by `1` + reverse(gray(k − 1)). Inside each half neighbours differ
in one bit because they did in gray(k − 1). At the seam the last string of the first half
and the first string of the second half are `0x` and `1x` for the same `x`: one bit.
2^n strings of `n` characters, about 10^6 characters for `n = 16`.

The C++ point is the recursion inside `main`: a lambda cannot name itself while its own
type is being deduced, so it takes itself as a parameter (`auto&& self`) and states its
return type. There is also a closed form, the i-th string is `i ^ (i >> 1)` in binary,
which you can check against the recursion.
""",
)

DECODE_WAYS = Problem(
    id="decode_ways",
    title="Secret Messages",
    difficulty="medium",
    source="LeetCode 91 - Decode Ways (with a modulus)",
    complexity="O(n)",
    statement=r"""
A message made of capital letters was encoded by replacing `A` with `1`, `B` with `2`,
..., `Z` with `26`, and writing the numbers one after another with no separators. So
`BZ` and `VF` and `BBF` all become `226`.

Given the digits, count the messages that could have produced them. The count can be
huge: print it modulo 10^9 + 7.
""",
    input=r"""
One line with a string of `n` digits (1 ≤ n ≤ 10^5). It may contain zeros anywhere,
including at the start.
""",
    output=r"""
Print the number of possible messages, modulo 10^9 + 7. It may be 0.
""",
    samples=[
        Test("226\n", "3\n"),
        Test("2101\n", "1\n"),
        Test("301\n", "0\n",
             note="`30` is not a letter code and a code cannot start with `0`: no message "
                  "fits. Zero is a real answer, not 'unknown'."),
    ],
    tests=[
        Test("0\n"),
        Test("10\n"),
        Test("27\n"),
        Test("1111111111\n"),
        Test("1" * 80 + "30\n"),
        Test("26" * 40 + "0\n"),
    ],
    gens=[
        Gen("small random", _digits_small, 14),
        Gen("medium, decodable", lambda rng: _codes(rng, 1200) + "\n", 2),
        Gen("medium, ones and twos", lambda rng: _digits_long(rng, 3000, "1122") + "\n", 1),
        Gen("max length, all ones", lambda rng: "1" * 100000 + "\n", 1, large=True),
        Gen("max length, dead end at the back", lambda rng: _digits_long(rng, 99998, "12") + "30\n", 1, large=True),
        Gen("max length, decodable", lambda rng: _codes(rng, 60000)[:100000] + "\n", 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
string s;
int n;
long long memo[100005];              // memo[i] = decodings of s[i..], or -1 if unknown

long long ways(int i) {
    if (i == n) return 1;            // the empty rest decodes in exactly one way
    long long& r = memo[i];          // a reference: writing r writes memo[i]
    if (r != -1) return r;
    r = 0;                           // 0 is a real answer: it must not mean "unknown"
    if (s[i] != '0') {
        r = ways(i + 1);             // s[i] alone is a letter 1..9
        if (i + 1 < n && (s[i] == '1' || (s[i] == '2' && s[i + 1] <= '6')))
            r = (r + ways(i + 2)) % MOD;   // s[i..i+1] is a letter 10..26
    }
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cin >> s;
    n = s.size();
    memset(memo, -1, sizeof memo);   // every byte 0xFF: every entry -1
    cout << ways(0) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s;
    cin >> s;
    int n = s.size();
    const long long MOD = 1000000007;
    vector<long long> dp(n + 1, 0);          // dp[k] = decodings of the first k digits
    dp[0] = 1;
    for (int k = 1; k <= n; k++) {
        int one = s[k - 1] - '0';
        if (one >= 1) dp[k] = dp[k - 1];
        if (k >= 2) {
            int two = (s[k - 2] - '0') * 10 + one;
            if (s[k - 2] != '0' && two >= 10 && two <= 26) dp[k] = (dp[k] + dp[k - 2]) % MOD;
        }
    }
    cout << dp[n] << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
string s;
int n;
long long memo[100005];              // global, so it starts at 0: "use 0 as unknown"
long long ways(int i) {
    if (i == n) return 1;
    if (memo[i]) return memo[i];     // a state whose answer is 0 is never remembered
    long long r = 0;
    if (s[i] != '0') {
        r = ways(i + 1);
        if (i + 1 < n && (s[i] == '1' || (s[i] == '2' && s[i + 1] <= '6')))
            r = (r + ways(i + 2)) % MOD;
    }
    return memo[i] = r;
}
int main() {
    cin >> s;
    n = s.size();
    cout << ways(0) << '\n';
}
""",
    hints=[
        r"""Let `ways(i)` be the number of decodings of the suffix starting at `i`. The first
letter uses one digit (1-9) or two digits (10-26), so `ways(i)` is a sum of `ways(i + 1)`
and `ways(i + 2)`, when allowed.""",
        r"""Plain recursion is exponential (it recomputes `ways(i + 2)` inside `ways(i + 1)`).
Store each answer in `memo[i]` the first time you compute it.""",
        r"""Mark unknown entries with −1 (`memset(memo, -1, sizeof memo)`), not with 0: many
suffixes have exactly 0 decodings, and with 0 as the marker they are recomputed every
time. The hidden test after `27` shows what that costs.""",
    ],
    editorial=r"""
`ways(i)` counts decodings of `s[i..]`: 0 if `s[i]` is `0` (no letter starts with 0);
otherwise `ways(i + 1)`, plus `ways(i + 2)` when `s[i..i+1]` is between 10 and 26. The
base case is `ways(n) = 1`. With a memo each `i` is computed once: O(n). (The loop version
`dp[k]` over prefixes is the same recurrence run bottom-up.)

The trap is the sentinel. A global array starts at 0 for free, so `if (memo[i]) return
memo[i];` is tempting. But 0 is a legitimate answer: in `111...1130` every suffix before
the `30` has 0 decodings, so with 0 as "unknown" nothing is ever remembered and the
recursion is exponential again. With 60 ones that is about 10^13 calls; the hidden test
with 80 ones never finishes. `memset(memo, -1, sizeof memo)` works because −1 is all
`0xFF` bytes (for most other values you would need `fill`).

The recursion is 10^5 calls deep. That is fine here and on most judges (the stack is
large), but it is the reason many people write this DP as a loop.
""",
)

MOST_COMMON = Problem(
    id="most_common",
    title="Best Seller of the Day",
    difficulty="medium",
    complexity="O(total n)",
    statement=r"""
A shop logged the product IDs it sold, one list per day, for `t` days. For each day,
print the ID that was sold most often that day. If several IDs tie, print the smallest
of them.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5), the number of days.

Each day is two lines: `n` (1 ≤ n ≤ 2·10^5), then `n` product IDs a_1, ..., a_n
(1 ≤ a_i ≤ 10^6). The sum of `n` over all days is at most 2·10^5.
""",
    output=r"""
Print `t` lines: the best-selling ID of each day.
""",
    samples=[
        Test("3\n3\n5 1 5\n2\n3 5\n4\n1000000 2 2 1000000\n", "5\n3\n2\n",
             note="On day 2, IDs 3 and 5 were each sold once. If your counts still remember "
                  "day 1, product 5 looks like it sold three times."),
    ],
    tests=[
        Test("1\n1\n1000000\n"),
        Test("2\n1\n7\n1\n8\n"),
        Test("3\n4\n9 9 9 9\n3\n1 2 9\n2\n9 1\n"),
    ],
    gens=[
        Gen("small random", _days_small, 14),
        Gen("medium, many days", lambda rng: _days(rng, 500, 1, 8, 20), 2),
        Gen("medium, wide IDs", lambda rng: _days(rng, 50, 1, 80, 10**6), 2),
        Gen("max days, two sales each", lambda rng: _days(rng, 100000, 2, 2, 10**6), 1, large=True),
        Gen("one long day", lambda rng: _days(rng, 1, 200000, 200000, 1000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int cnt[1000001];                        // global: zero once, at program start

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (auto& x : a) {
            cin >> x;
            cnt[x]++;
        }
        int best = a[0];
        for (int x : a)                  // only IDs of this day can win
            if (cnt[x] > cnt[best] || (cnt[x] == cnt[best] && x < best)) best = x;
        cout << best << '\n';
        for (int x : a) cnt[x] = 0;      // undo exactly this day's counts: O(n), not O(10^6)
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        map<int, int> c;                 // fresh every day
        for (int i = 0; i < n; i++) { int x; cin >> x; c[x]++; }
        int best = -1, bc = 0;
        for (auto& [id, k] : c) if (k > bc) { bc = k; best = id; }
        cout << best << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int cnt[1000001];
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        memset(cnt, 0, sizeof cnt);      // 4 MB cleared for every day
        int n;
        cin >> n;
        vector<int> a(n);
        for (auto& x : a) { cin >> x; cnt[x]++; }
        int best = a[0];
        for (int x : a)
            if (cnt[x] > cnt[best] || (cnt[x] == cnt[best] && x < best)) best = x;
        cout << best << '\n';
    }
}
""",
    hints=[
        r"""A global `int cnt[1000001]` counts one day quickly. What does it contain when the
next day starts?""",
        r"""Clearing the whole array every day costs 10^6 per day, and there can be 10^5 days.
Clear only the entries this day touched: loop over the day's IDs and set `cnt[x] = 0`.""",
        r"""To find the best ID, loop over the day's IDs, not over all 10^6 possible IDs.""",
    ],
    editorial=r"""
Count with a global array `cnt` indexed by ID, pick the best among the IDs of the day
(highest count, then smallest ID), and reset. The budget the constraints promise is the
*sum* of `n`, 2·10^5, so every per-day step must be O(n): both finding the best and
resetting walk over the day's own IDs. O(total n).

Three versions fail. Not resetting at all: yesterday's sales leak into today (the
sample's second day). Resetting with `memset(cnt, 0, sizeof cnt)` every day: 4 MB times
10^5 days is 4·10^11 bytes, about 12 s here. Scanning every possible ID from 1 to 10^6 to
find the maximum costs the same 10^11. Declaring `vector<int> cnt(1000001)` inside the
loop is the `memset` version in disguise.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp07",
    title="structs, operator overloading & recursion patterns",
    track="cpp",
    order=7,
    summary="Records as structs with value semantics, operator< for sorting and sets (and "
            "the set that merges your elements), recursive lambdas, memo tables with the "
            "right sentinel, and state that must not leak between test cases.",
    prereqs=["cpp06"],
    tags=["struct", "operator<", "tie", "constructor", "recursive lambda", "memoisation",
          "memset", "multi-test reset"],
    parts=[
        Part("struct: a record that is a value", [
            Say(r"""
Python bundles fields with a `class`, a `@dataclass` or a `namedtuple`. Contest C++ uses a
`struct`:

```cpp
struct Team {
    string name;
    int solved = 0, penalty = 0;     // default values, like dataclass fields
};                                   // <- this semicolon is required

Team a{"kth", 5, 612};               // fields in declaration order
Team b;                              // "", 0, 0
a.solved++;
vector<Team> teams(n);               // n default Teams
```

A `struct` can hold functions too (cpp05's `SafeHash` was one), and a `vector` of them is
the C++ version of a list of records.
"""),
            Short(r"""
The big difference from Python is not the syntax. What does this print?

```cpp
struct P { int x, y; };

P a{1, 2};
P b = a;
b.x = 10;
cout << a.x << ' ' << b.x << '\n';
```
""", accept=["1 10"], placeholder="two numbers",
                explain=r"""
`1 10`. In Python, `b = a` makes `b` a second name for the same object, and `a.x` would
be 10 as well. In C++ a struct variable *is* the object, so `b = a` copies every field.
The same goes for `vector<Team> v2 = v` (copies every team) and for passing a struct to a
function by value (cpp03).
"""),
            Short(r"""
And this?

```cpp
vector<P> v = {{1, 2}, {3, 4}};
for (auto p : v) p.x *= 10;
for (auto& p : v) p.y *= 10;
cout << v[0].x << ' ' << v[0].y << '\n';
```
""", accept=["1 20"], placeholder="two numbers",
                explain=r"""
`1 20`. `for (auto p : v)` hands you a *copy* of each element, so the first loop changes
copies and throws them away. `auto&` binds to the elements themselves. The first loop
compiles, runs and does nothing, which makes it one of the quieter bugs in C++.
"""),
            MCQ(r"""
Python's `@dataclass` gives you `==` for free. What does `if (a == b)` do for two `P`s in
C++17?
""", [
                Opt("Compares every field, like a dataclass.",
                    why="That is Python (and C++20, if you ask for it with `= default`). C++17 "
                        "generates no comparison operators at all."),
                Opt("Checks whether `a` and `b` are the same object.",
                    why="That is Python's `is`. C++ has no implicit identity comparison for "
                        "structs; comparing addresses would be `&a == &b`."),
                Opt("It does not compile: 'no match for operator=='.", correct=True,
                    why="Right. Write `bool operator==(const P& o) const { return x == o.x && "
                        "y == o.y; }` if you need it. The next parts do the same for `<`, which "
                        "is the one sorting needs."),
            ]),
            Say(r"""
A **constructor** is a function that runs when an object is created. You rarely need one
in contest code, since the brace form already fills fields in order, but you will read
them:

```cpp
struct Edge {
    int u, v;
    long long w;
    Edge(int u, int v, long long w) : u(u), v(v), w(w) {}   // initializer list
};

vector<Edge> es;
es.emplace_back(1, 2, 5);    // constructs the Edge in place from these arguments
es.push_back({3, 4, 6});     // constructs a temporary Edge, then moves it in
```
"""),
            MCQ(r"""
With that `Edge` (its only constructor takes three arguments), which line does *not*
compile?
""", [
                Opt("`Edge e(1, 2, 5);`",
                    why="That calls the constructor directly: fine."),
                Opt("`es.push_back({3, 4, 6});`",
                    why="The braces are passed to the constructor: fine."),
                Opt("`vector<Edge> es(10);`", correct=True,
                    why="Right: it needs 10 *default-constructed* Edges, and declaring any "
                        "constructor removes the implicit default one. GCC: 'no matching "
                        "function for call to Edge::Edge()'. Add `Edge() {}`, or drop the "
                        "constructor and use the plain brace form."),
                Opt("`es.emplace_back(1, 2, 5);`",
                    why="`emplace_back` forwards its arguments to the constructor: fine."),
            ]),
        ]),
        Part("One record, not parallel arrays", [
            Say(r"""
Python code often keeps **parallel lists**: `start[i]`, `end[i]` and `room[i]` together
describe meeting `i`. That holds up until something reorders one of them.
"""),
            MCQ(r"""
`start = {5, 1}` and `end = {6, 9}` describe the meetings [5, 6) and [1, 9). To process
them by start time you call `sort(start.begin(), start.end());`. Which meetings do the
two arrays describe now?
""", [
                Opt("[1, 9) and [5, 6): the same meetings, ordered by start.",
                    why="Only `start` was sorted. `end` is still `{6, 9}`."),
                Opt("[1, 6) and [5, 9): meetings that never existed.", correct=True,
                    why="Yes. Nothing ties `start[i]` to `end[i]` except your intention, and "
                        "`sort` does not know about it."),
                Opt("The same two meetings: C++ keeps vectors of equal length in sync.",
                    why="There is no such mechanism; each vector is independent."),
            ], explain=r"""
Keep one record per meeting (a `vector<Meeting>`, or of pairs) and sort that, or sort an
index array with a comparator that reads the parallel arrays (cpp06). Parallel arrays are
fine while nothing reorders them, and they are sometimes faster when a loop reads only
one field.
"""),
            Reflect(r"""
You have `vector<string> name(n)` and `vector<int> score(n)` and need the names sorted by
score. Name two ways to do it without losing which name goes with which score.
""", answer=r"""
Put the fields in one record, for example `vector<pair<int, string>> v` with `{score,
name}` (or a struct with `operator<`), and sort that: the fields move together. Or leave
the arrays alone and sort an index vector: `iota(idx.begin(), idx.end(), 0);` then
`sort(idx.begin(), idx.end(), [&](int i, int j) { return score[i] < score[j]; });` and
print `name[idx[k]]`.
"""),
        ]),
        Part("operator<: teaching C++ to order your type", [
            Say(r"""
`sort` on a `vector<Team>` does not compile: C++ does not know how to order two Teams
("no match for 'operator<'"). You teach it by defining `operator<` inside the struct:

```cpp
struct Event {
    int time, type;                  // type: -1 = a meeting ends, +1 = one starts
    bool operator<(const Event& o) const {
        return tie(time, type) < tie(o.time, o.type);   // time first, then type
    }
};
```

`tie(a, b)` packs references to the fields into a tuple, and tuples compare
lexicographically (cpp05). After this one function, `sort`, `set<Event>`,
`priority_queue<Event>`, `lower_bound`, `min` and `max` all work on `Event`.
"""),
            Short(r"""
What does this print?

```cpp
vector<Event> ev = {{3, 1}, {1, 1}, {3, -1}, {2, -1}};
sort(ev.begin(), ev.end());
for (auto& e : ev) cout << e.type << ' ';
```
""", accept=["1 -1 -1 1"], placeholder="four numbers",
                explain=r"""
`1 -1 -1 1`: times 1, 2, 3, 3, and at time 3 the end (−1) sorts before the start (+1).
That tie rule decides whether a meeting that ends at 3 and one that starts at 3 are ever
in progress together, which is exactly what the next problem turns on.
"""),
            MCQ(r"""
Delete the `const` after `operator<`'s parameter list. `sort(ev.begin(), ev.end())` still
compiles, but `set<Event> s; s.insert(e);` does not. Why?
""", [
                Opt("A `set` also needs `operator==`.",
                    why="A set never uses `==`. Two elements count as equal when neither is less "
                        "than the other; that matters in a moment."),
                Opt("A `set` compares its elements through `const` references, and a member "
                    "function without `const` cannot be called on a `const` object.",
                    correct=True,
                    why="Yes. The trailing `const` promises that comparing does not modify the "
                        "object. Always write `bool operator<(const T& o) const`."),
                Opt("A `set` cannot hold structs, only built-in types.",
                    why="Sets hold anything that can be compared: that is what `operator<` is "
                        "for."),
            ]),
            Short(r"""
A shortcut: this `operator<` compares only `x`. What does the program print?

```cpp
struct P {
    int x, y;
    bool operator<(const P& o) const { return x < o.x; }
};

set<P> s = {{1, 2}, {1, 3}, {0, 5}};
cout << s.size() << '\n';
```
""", accept=["2"], placeholder="a number",
                explain=r"""
`2`. To a `set`, `a` and `b` are the same element when neither `a < b` nor `b < a`, so
equality is defined by *your* `operator<`, not by the fields. `{1, 3}` looked like the
`{1, 2}` already present and was dropped. A comparator that ignores a field makes sets
and maps merge objects silently. Compare every field that distinguishes two objects, and
use a `multiset` (or a sorted `vector`) when genuinely equal objects must all be kept.
"""),
            MCQ(r"""
A scoreboard wants more problems solved first, then less penalty. Which `operator<`
inside `struct Team { int solved, penalty; ... }` makes a plain `sort` produce that
order?
""", [
                Opt("`return tie(solved, penalty) < tie(o.solved, o.penalty);`",
                    why="Ascending in both keys: the team with the fewest problems comes first."),
                Opt("`return tie(o.solved, o.penalty) < tie(solved, penalty);`",
                    why="Swapping the whole tuples reverses *both* keys: more solved first, but "
                        "among equal solved the larger penalty first."),
                Opt("`return tie(o.solved, penalty) < tie(solved, o.penalty);`", correct=True,
                    why="Yes: swap only the field of the key that runs backwards. Sorting (4, 10), "
                        "(5, 100), (5, 30), (3, 5) gives (5, 30) (5, 100) (4, 10) (3, 5)."),
                Opt("`return solved > o.solved || penalty < o.penalty;`",
                    why="Not a strict weak ordering: for (5, 100) and (4, 10), both `a < b` and "
                        "`b < a` are true, and `sort` is into undefined behaviour. The penalty "
                        "test must only apply on a tie: `solved > o.solved || (solved == o.solved "
                        "&& penalty < o.penalty)`."),
            ], explain=r"""
The swap trick is compact but easy to misread. The explicit version is just as good:

```cpp
if (solved != o.solved) return solved > o.solved;
return penalty < o.penalty;
```
"""),
            MCQ(r"""
`priority_queue<Event> pq;` holds the events (3, +1), (1, +1) and (3, −1). What is
`pq.top()`?
""", [
                Opt("(1, +1): the earliest event.",
                    why="That would be a min-heap. `priority_queue` puts the *largest* element "
                        "on top (cpp05), and 'largest' now means largest by your `operator<`."),
                Opt("(3, −1)",
                    why="(3, −1) < (3, +1) by the tie on `type`, so it is not the largest."),
                Opt("(3, +1)", correct=True,
                    why="Yes: the largest by `operator<`. For earliest-first, give the struct an "
                        "`operator>` as well and use `priority_queue<Event, vector<Event>, "
                        "greater<Event>>`."),
            ]),
            Try("meeting_rooms", note="Events as a struct with `operator<`. Mind the tie between an "
                "end and a start, and keep equal events."),
        ]),
        Part("Recursion inside main: recursive lambdas", [
            Say(r"""
A recursive helper can be an ordinary function, but a function defined outside `main`
cannot see `main`'s local variables: the graph, the visited array, the memo. So contest
code either makes all of those global, or writes the recursion as a lambda inside
`main` that captures `[&]`. The obvious attempt does not compile:

```cpp
auto fact = [&](int n) { return n <= 1 ? 1 : n * fact(n - 1); };
// error: use of 'fact' before deduction of 'auto'
```
"""),
            MCQ(r"""
What is the compiler complaining about?
""", [
                Opt("Lambdas cannot be recursive in C++.",
                    why="They can; they just cannot refer to themselves by this name."),
                Opt("`fact`'s type is deduced from the lambda, and the lambda uses `fact` "
                    "before that type exists.", correct=True,
                    why="Yes. Every lambda has its own unnamed type, known only once the lambda "
                        "is complete, and `auto fact` waits for it. Inside the body, `fact` has "
                        "no type yet."),
                Opt("`[&]` cannot capture a lambda.",
                    why="It captures anything that already exists. `fact` does not exist yet "
                        "while its own initializer is being compiled."),
            ]),
            Say(r"""
Two standard ways around it:

```cpp
// 1. std::function: declare the variable's type first, then assign the lambda
function<long long(int)> fact = [&](int n) -> long long {
    return n <= 1 ? 1 : n * fact(n - 1);
};
cout << fact(10) << '\n';

// 2. pass the lambda to itself as a parameter
auto fact2 = [&](auto&& self, int n) -> long long {
    return n <= 1 ? 1 : n * self(self, n - 1);
};
cout << fact2(fact2, 10) << '\n';
```

Write the return type (`-> long long`) on recursive lambdas: form 2 does not compile
without it here. Form 1 pays for an indirect call on every invocation. Measured on this
machine: a naive `fib(38)` takes 0.034 s with form 2 and 0.135 s with form 1; a DFS over
10^6 vertices, 0.055 s against 0.071 s. Either is fine unless the body is tiny and the
call count is huge.
"""),
            Say(r"""
Recursion shines at generating structured lists. A **Gray code** lists all 2^n bit
strings of length `n` so that neighbours differ in exactly one bit. Recursively: take the
list for `n − 1` and prefix every string with `0`; then take the same list *reversed* and
prefix every string with `1`.

For n = 1: `0 1`. For n = 2: `00 01 11 10`.
"""),
            Short(r"""
What is the list for n = 3? (Eight strings, separated by spaces.)
""", accept=["000 001 011 010 110 111 101 100"], placeholder="eight bit strings",
                explain=r"""
`000 001 011 010 110 111 101 100`: `0` + (00 01 11 10), then `1` + (10 11 01 00).
"""),
            Reflect(r"""
Why does the construction need the *reversal*? What would go wrong at the middle of the
list without it, and why does it work with it?
""", answer=r"""
Inside each half, neighbours differ in one bit because they did in the list for n − 1
(the prefix is the same). The only new pair is the seam. Without the reversal the seam is
`0` + last(n − 1) next to `1` + first(n − 1), which differ in the first bit and also
wherever first and last differ (for n = 3: 010 then 100, two bits). With the reversal the
second half starts with `1` + last(n − 1), so the seam is `0x` next to `1x` for the same
`x`: exactly one bit.
"""),
            Try("gray_code", note="Write it as a recursive lambda with `auto&& self`. Any valid Gray "
                "code is accepted."),
        ]),
        Part("Memo tables and the sentinel", [
            Say(r"""
Python has `@functools.lru_cache`: decorate a recursive function and repeated calls are
answered from a dictionary. C++ has no decorator; you write the cache yourself, usually an
array indexed by the arguments, with one value that means "not computed yet":

```cpp
long long memo[100005];               // global: large arrays are fine there

long long f(int i) {
    if (i == n) return 1;             // base case first
    long long& r = memo[i];           // reference: assigning r fills the table
    if (r != -1) return r;            // computed before
    r = /* ... f(i + 1) ... f(i + 2) ... */;
    return r;
}

// in main, before the first call:
memset(memo, -1, sizeof memo);
```

`memset(ptr, value, bytes)` sets every **byte** of a block of memory to `value`. That
decides what it can and cannot do.
"""),
            Short(r"""
What does this print?

```cpp
int a[3];
memset(a, 1, sizeof a);
cout << a[0] << '\n';
```
""", accept=["16843009"], placeholder="a number",
                hint="An `int` is four bytes. What is each byte after the memset?",
                explain=r"""
`16843009`, which is `0x01010101`: each of the four bytes became 1. `memset` gives the
value you meant only when all bytes of that value are equal: 0 (all `0x00`), −1 (all
`0xFF`), and the popular "infinity" `0x3f3f3f3f` = 1061109567 from `memset(a, 0x3f,
sizeof a)`. For anything else, `fill(a, a + n, value)`.
"""),
            MCQ(r"""
The memo is a `vector<long long> memo(n);` this time, and you write
`memset(&memo, -1, sizeof memo);`. What happens?
""", [
                Opt("Every element becomes −1, as with an array.",
                    why="`sizeof memo` is the size of the vector *object* (24 bytes here: three "
                        "pointers), not of its elements, and `&memo` is that object."),
                Opt("It overwrites the vector's own internal pointers with `0xFF` bytes, and "
                    "the next access crashes.", correct=True,
                    why="Yes: here it dies with a segmentation fault on the first `memo[0]`. "
                        "GCC even warns about it, if you read the warnings."),
                Opt("A compile error: `memset` does not accept vectors.",
                    why="`memset` takes any pointer; `&memo` converts silently."),
            ], explain=r"""
For vectors: `memo.assign(n, -1)` or `fill(memo.begin(), memo.end(), -1)`. `sizeof`
measures the elements only for real arrays: `long long m[100]` has `sizeof m == 800`.
"""),
            Say(r"""
Why −1 and not 0? A global array starts at 0 for free, so "0 means unknown" is tempting.
It is correct only if no state's real answer is 0.

The next problem counts the ways to decode a digit string (A = 1, ..., Z = 26), with
`ways(i)` = decodings of the suffix from `i`: `ways(i + 1)` if `s[i]` is a letter by
itself, plus `ways(i + 2)` if `s[i..i+1]` is 10 to 26. Many suffixes have *zero*
decodings: `30` has none, so in `111...1130` every suffix before the `30` has none either.
"""),
            MCQ(r"""
With 0 as the "unknown" marker, what happens on `"1" * 60 + "30"`?
""", [
                Opt("Nothing special: the answer is 0 either way.",
                    why="The answer is right, but no state is ever remembered: every `memo[i]` "
                        "stays 0, which reads as 'unknown'."),
                Opt("Wrong answers, because 0 entries are overwritten.",
                    why="Recomputing a 0 gives 0 again, so the answer is correct. Only the time "
                        "changes."),
                Opt("The memo does nothing and the recursion is exponential again: about 10^13 "
                    "calls.", correct=True,
                    why="Yes. Each `ways(i)` calls `ways(i + 1)` and `ways(i + 2)`, and neither "
                        "result is kept: a Fibonacci-shaped tree. With 40 ones it is 7·10^8 "
                        "calls; with 60, 1.06·10^13."),
                Opt("A stack overflow.",
                    why="The recursion is only about 60 calls deep. It is wide, not deep."),
            ], explain=r"""
Choose a sentinel that can never be a real answer: −1 for counts and costs, or keep a
separate `bool done[i]` array. Then every state is computed at most once, and the whole
recursion is O(number of states × work per state).
"""),
            Try("decode_ways", note="A memoised recursion. One small hidden test is designed for the "
                "0-as-unknown memo."),
        ]),
        Part("State that leaks between test cases", [
            Say(r"""
Multi-test input (cpp01) plus a global array is where the next bug lives. A global array
is zeroed **once**, when the program starts, not at the start of each test case. Whatever
test 1 leaves in it is still there during test 2.
"""),
            Short(r"""
What does this print?

```cpp
int cnt[10];                          // global

int main() {
    vector<vector<int>> tests = {{1, 2, 2}, {2, 3}};
    for (auto& a : tests) {
        int best = 0;
        for (int x : a) best = max(best, ++cnt[x]);
        cout << best << ' ';
    }
}
```
""", accept=["2 3"], placeholder="two numbers",
                explain=r"""
`2 3`. The second test should print 1 (every value appears once), but `cnt[2]` still
holds 2 from the first test. Samples of multi-test problems usually have two or three
tests, so this bug often shows up right there; when it does not, a hidden test finds it.
"""),
            Numeric(r"""
The fix that comes to mind is `memset(cnt, 0, sizeof cnt);` at the start of every test.
With `int cnt[1000001]` (4 bytes each) and `t = 10^5` test cases, how many bytes does that
clear in total?
""", answer=4e11, rel=0.5, unit="bytes",
                explain=r"""
About 4·10^6 bytes per test times 10^5 tests: 4·10^11 bytes. Measured here: 12 s, while
the actual input (the sum of `n` is 2·10^5) takes milliseconds. The constraints promise
only that the *sum* of `n` is small; anything per test must be O(n), not O(array size).
"""),
            MCQ(r"""
Which reset keeps each test case O(n)?
""", [
                Opt("Declare `vector<int> cnt(1000001);` inside the test loop.",
                    why="Allocating and zeroing 10^6 ints per test is the `memset` cost again, "
                        "plus an allocation."),
                Opt("After the test, loop over that test's values and set `cnt[x] = 0`.",
                    correct=True,
                    why="Yes: undo exactly what this test did. The same idea resets a memo "
                        "table: clear entries 0..n of this test, not the whole array."),
                Opt("Nothing: global arrays are re-zeroed before each test case.",
                    why="There is no such thing as a 'test case' to the program; it is one run "
                        "reading one input. Globals are zeroed once."),
                Opt("`memset(cnt, 0, n * sizeof(int))` with this test's `n`.",
                    why="That clears the first `n` entries, but the values are IDs up to 10^6: "
                        "the entries used are scattered all over the array."),
            ]),
            Try("most_common", note="A global count array, many days, and a reset that has to "
                "be cheap."),
        ]),
    ],
    problems=[MEETING_ROOMS, GRAY_CODE, DECODE_WAYS, MOST_COMMON],
    cards=[
        Card(r"""Declare a struct `Team` with a name and two ints defaulting to 0, and create one.""",
             r"""`struct Team { string name; int solved = 0, penalty = 0; };` (semicolon!) then `Team a{"kth", 5, 612};`"""),
        Card(r"""`P b = a; b.x = 10;` for a struct: does `a.x` change?""",
             r"""No. C++ struct variables are values: assignment copies every field (unlike Python, where `b = a` aliases)."""),
        Card(r"""Why does `for (auto p : v) p.x++;` leave `v` unchanged?""",
             r"""`auto p` is a copy of each element. Use `for (auto& p : v)`."""),
        Card(r"""The signature and body of a lexicographic `operator<` for a struct with fields `a`, `b`?""",
             r"""`bool operator<(const T& o) const { return tie(a, b) < tie(o.a, o.b); }`"""),
        Card(r"""When does a `set<T>` treat two different objects as the same element?""",
             r"""When neither `x < y` nor `y < x` by `T`'s `operator<`. A comparator that ignores a field silently merges objects."""),
        Card(r"""What does declaring a constructor do to `vector<T> v(n)`?""",
             r"""It stops compiling if there is no default constructor: declaring any constructor removes the implicit one."""),
        Card(r"""Recursive lambda inside `main` without `std::function`?""",
             r"""`auto f = [&](auto&& self, int x) -> long long { ... self(self, x - 1) ... };` called as `f(f, n)`."""),
        Card(r"""What values can `memset` put into an `int` array?""",
             r"""Only values whose four bytes are equal: 0, −1, `0x3f3f3f3f` (1061109567)... `memset(a, 1, ...)` gives 16843009. Otherwise use `fill`."""),
        Card(r"""How do you set every element of a `vector` memo to −1?""",
             r"""`memo.assign(n, -1)` or `fill(memo.begin(), memo.end(), -1)`. `memset(&memo, ...)` overwrites the vector object itself."""),
        Card(r"""Why is 0 a dangerous "not computed" marker in a memo table?""",
             r"""States whose true answer is 0 are never remembered and get recomputed on every visit, which can make the recursion exponential again. Use −1 or a separate `done` array."""),
        Card(r"""Global arrays and multi-test input: what is the rule?""",
             r"""Globals are zeroed once per run. Reset between test cases, touching only what the test used (O(n)), never the whole array per test."""),
    ],
)
