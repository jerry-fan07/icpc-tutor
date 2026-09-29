from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _pair(rng, lim):
    return f"{rng.randint(-lim, lim)} {rng.randint(-lim, lim)}\n"


def _spread(rng, t, nmax, lim):
    out = [str(t)]
    for _ in range(t):
        n = rng.randint(1, nmax)
        out.append(str(n))
        out.append(" ".join(str(rng.randint(-lim, lim)) for _ in range(n)))
    return "\n".join(out) + "\n"


def _spread_extremes(rng):
    out = ["3", "2", f"{-2 * 10**9} {2 * 10**9}", "3", f"{2 * 10**9} {2 * 10**9} {-2 * 10**9}", "1", "0"]
    return "\n".join(out) + "\n"


def _loose_numbers(rng, n, lim):
    """n integers scattered over lines with random spacing, sometimes blank lines."""
    parts, line = [], []
    for _ in range(n):
        line.append(str(rng.randint(-lim, lim)))
        if rng.random() < 0.2:
            parts.append((" " * rng.randint(1, 3)).join(line))
            line = []
            if rng.random() < 0.1:
                parts.append("")
    if line:
        parts.append(" ".join(line))
    return "\n".join(parts) + "\n"


def _lines(rng, n, maxwords):
    words = ["icpc", "graph", "tree", "dp", "greedy", "a", "zz", "binary", "search", "flow"]
    out = [str(n)]
    for _ in range(n):
        k = rng.randint(0, maxwords)
        pieces = [rng.choice(words) for _ in range(k)]
        sep = lambda: " " * rng.randint(1, 3)
        line = " " * rng.randint(0, 2) + "".join(w + sep() for w in pieces).rstrip()
        if rng.random() < 0.3:
            line += " " * rng.randint(1, 2)
        out.append(line)
    return "\n".join(out) + "\n"


def _echo(rng, n, lim):
    return f"{n}\n" + " ".join(str(rng.randint(-lim, lim)) for _ in range(n)) + "\n"


SKELETON = r"""#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return 0;
}
"""

# --------------------------------------------------------------------- problems
BIG_SUM = Problem(
    id="big_sum",
    title="A + B, Grown Up",
    difficulty="easy",
    complexity="O(1)",
    statement=r"""
The first problem of every judge ever built: read two integers, print their sum.

The catch is in the limits. Read them before you pick a type.
""",
    input=r"""
One line with two integers `a` and `b` (−10^18 ≤ a, b ≤ 10^18).
""",
    output=r"""
Print `a + b`.
""",
    samples=[
        Test("3 4\n", "7\n"),
        Test("2000000000 2000000000\n", "4000000000\n",
             note="An `int` holds at most 2147483647. What type holds 4000000000?"),
    ],
    tests=[
        Test("-1000000000000000000 -1000000000000000000\n"),
        Test("1000000000000000000 1000000000000000000\n"),
        Test("0 0\n"),
        Test("-5 5\n"),
    ],
    gens=[
        Gen("random 32-bit", lambda rng: _pair(rng, 2 * 10**9), 4),
        Gen("random 64-bit", lambda rng: _pair(rng, 10**18), 6),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long a, b;          // 64 bits: up to about 9.2 * 10^18
    cin >> a >> b;
    cout << a + b << '\n';   // |a + b| <= 2 * 10^18 still fits
    return 0;
}
""",
    starter=SKELETON,
    wrong=[r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // the Python habit: a plain int
    int a, b;
    cin >> a >> b;
    cout << a + b << '\n';
}
"""],
    hints=[
        r"""`int` stops at 2147483647 (about 2.1·10^9). Which type goes to about 9.2·10^18?""",
        r"""`long long a, b; cin >> a >> b; cout << a + b << '\n';`""",
    ],
    editorial=r"""
`long long` is a 64-bit signed integer: −9,223,372,036,854,775,808 to
9,223,372,036,854,775,807, about ±9.2·10^18. The inputs are at most 10^18 in absolute
value and their sum at most 2·10^18, which fits. With `int`, the second sample already
fails: 4000000000 does not fit in 32 bits, and `cin` fails to read it at all.

Python programmers never meet this, because Python integers grow as needed. In C++ the
type is fixed when you declare the variable, so the limits decide the type.
""",
)

SPREAD = Problem(
    id="spread",
    title="Spread",
    difficulty="easy",
    complexity="O(total n)",
    statement=r"""
You get several independent test cases. In each, you are given a list of integers; print
the difference between the largest and the smallest.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^4), the number of test cases.

Each test case is two lines: an integer `n` (1 ≤ n ≤ 2·10^5), then `n` integers
a_1..a_n (−2·10^9 ≤ a_i ≤ 2·10^9). The sum of `n` over all test cases is at most 2·10^5.
""",
    output=r"""
For each test case, print max − min on its own line.
""",
    samples=[
        Test("3\n3\n1 5 3\n1\n-7\n4\n-1000000000 0 7 1000000000\n", "4\n0\n2000000000\n"),
        Test("1\n2\n-2000000000 2000000000\n", "4000000000\n",
             note="Both values fit in an `int` (it goes to 2147483647). Does their difference?"),
    ],
    tests=[
        Test("1\n1\n2000000000\n"),
        Test("2\n2\n-2000000000 -2000000000\n2\n5 -5\n"),
    ],
    gens=[
        Gen("extremes", _spread_extremes, 1),
        Gen("many tiny tests", lambda rng: _spread(rng, 10000, 20, 2 * 10**9), 1),
        Gen("small random", lambda rng: _spread(rng, rng.randint(1, 6), 8, 50), 6),
        Gen("one big test", lambda rng: "1\n200000\n" + _echo(rng, 200000, 2 * 10**9).split("\n", 1)[1], 1),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        long long lo = LLONG_MAX, hi = LLONG_MIN;   // reset for every test case
        for (int i = 0; i < n; i++) {
            long long x;
            cin >> x;
            lo = min(lo, x);
            hi = max(hi, x);
        }
        cout << hi - lo << '\n';                    // up to 4 * 10^9: too big for int
    }
    return 0;
}
""",
    starter=SKELETON,
    wrong=[r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // values fit in int; their difference does not
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        int lo = INT_MAX, hi = INT_MIN;
        for (int i = 0; i < n; i++) { int x; cin >> x; lo = min(lo, x); hi = max(hi, x); }
        cout << hi - lo << '\n';
    }
}
""", r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // minimum and maximum never reset between tests
    int t;
    cin >> t;
    long long lo = LLONG_MAX, hi = LLONG_MIN;
    while (t--) {
        int n;
        cin >> n;
        for (int i = 0; i < n; i++) { long long x; cin >> x; lo = min(lo, x); hi = max(hi, x); }
        cout << hi - lo << '\n';
    }
}
"""],
    hints=[
        r"""The shape is `int t; cin >> t; while (t--) { ... }`. Anything that tracks a minimum or
maximum must be reset inside the loop, not before it.""",
        r"""max − min can be 2·10^9 − (−2·10^9) = 4·10^9, past the 2147483647 an `int` holds.""",
    ],
    editorial=r"""
Multi-test input is the most common format in modern contests: read `t`, then loop `t`
times, and treat each iteration as a fresh problem. The classic bug is state that survives
from one test case to the next, like a running minimum declared outside the loop.

Here the answer also overflows `int`: 2·10^9 − (−2·10^9) = 4·10^9 > 2147483647. The values
fit in `int`, but their difference does not. That is the general rule: choose the type from
the largest value you *compute*, not the largest value you *read*.
""",
)

RUNNING_TOTAL = Problem(
    id="running_total",
    title="Until the Input Runs Out",
    difficulty="easy",
    complexity="O(n)",
    statement=r"""
The input is a list of integers, but nobody tells you how many. They are spread over
lines in no particular way: several per line, one per line, even blank lines in between.

Print how many integers there are and their sum.
""",
    input=r"""
Between 1 and 2·10^5 integers, each with absolute value at most 10^9, separated by
spaces and newlines.
""",
    output=r"""
One line: the count, a space, the sum.
""",
    samples=[
        Test("1 2 3\n4\n\n5    6\n", "6 21\n"),
        Test("-1000000000\n", "1 -1000000000\n"),
    ],
    tests=[
        Test("7"),
        Test("1000000000 1000000000 1000000000\n"),
    ],
    gens=[
        Gen("small scattered", lambda rng: _loose_numbers(rng, rng.randint(1, 30), 100), 6),
        Gen("large scattered", lambda rng: _loose_numbers(rng, 200000, 10**9), 2),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    long long x, sum = 0;
    int count = 0;
    while (cin >> x) {       // false once there is nothing left to read
        count++;
        sum += x;
    }
    cout << count << ' ' << sum << '\n';
    return 0;
}
""",
    starter=SKELETON,
    hints=[
        r"""`cin >> x` skips any amount of whitespace, newlines included, so the line structure
does not matter at all.""",
        r"""`while (cin >> x) { ... }` runs once per integer and stops at the end of the input.""",
    ],
    editorial=r"""
`cin >> x` returns `cin` itself, and a stream converts to `false` once a read has failed,
which is what happens at end of input. So `while (cin >> x)` is "for every token in the
input", the C++ spelling of Python's `for tok in sys.stdin.read().split()`.

The sum of 2·10^5 values of size 10^9 is 2·10^14: `long long` again.
""",
)

WORD_COUNT = Problem(
    id="word_count",
    title="Words per Line",
    difficulty="medium",
    complexity="O(total length)",
    statement=r"""
Given `n` lines of text, print how many words each line has. A word is a maximal run of
non-space characters. Lines can be empty and can have leading, trailing and repeated
spaces.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 1000). Exactly `n` lines follow, each at most 1000
characters of lowercase letters and spaces.
""",
    output=r"""
`n` lines: the number of words on each input line.
""",
    samples=[
        Test("3\nhello world\n  the   quick brown  fox \n\n", "2\n4\n0\n",
             note="The third line is empty. If you print 2, 4 and then something odd, look at "
                  "what the first getline really read."),
    ],
    tests=[
        Test("1\n\n"),
        Test("2\n   \nsingle\n"),
        Test("1\na b c d e f g h i j\n"),
    ],
    gens=[
        Gen("random lines", lambda rng: _lines(rng, rng.randint(1, 8), 6), 8),
        Gen("many lines", lambda rng: _lines(rng, 1000, 150), 1),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    string line;
    getline(cin, line);              // finish the first line: cin >> n left its '\n' behind
    for (int i = 0; i < n; i++) {
        getline(cin, line);
        stringstream ss(line);       // read words out of the line like out of cin
        string w;
        int words = 0;
        while (ss >> w) words++;
        cout << words << '\n';
    }
    return 0;
}
""",
    starter=SKELETON,
    wrong=[r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // forgets the newline left behind by cin >> n
    int n;
    cin >> n;
    string line;
    for (int i = 0; i < n; i++) {
        getline(cin, line);
        stringstream ss(line);
        string w;
        int words = 0;
        while (ss >> w) words++;
        cout << words << '\n';
    }
}
""", r"""
#include <bits/stdc++.h>
using namespace std;
int main() {                                  // cin >> ws also eats a first line of spaces
    int n;
    cin >> n >> ws;
    string line;
    for (int i = 0; i < n; i++) {
        getline(cin, line);
        stringstream ss(line);
        string w;
        int words = 0;
        while (ss >> w) words++;
        cout << words << '\n';
    }
}
"""],
    hints=[
        r"""`cin >> s` cannot see line boundaries; `getline(cin, line)` reads one whole line.""",
        r"""After `cin >> n`, the newline after `n` is still unread, so the first `getline` returns
an empty string. Throw it away with one extra `getline`. (`cin >> ws` would also skip a
first line that is blank or starts with spaces, which this problem needs.)""",
        r"""To count words in a line: `stringstream ss(line); while (ss >> w) count++;`.""",
    ],
    editorial=r"""
Two tools and one trap. `getline(cin, line)` reads up to the next newline, so it sees empty
lines and spaces that `cin >>` would skip. `stringstream ss(line)` turns a string into a
stream, so `ss >> w` splits it into words exactly the way `cin >>` splits input.

The trap: `cin >> n` stops right after the digits and leaves the newline in the input. The
next `getline` reads the empty rest of that first line. Consume it with one extra
`getline`. `cin >> ws` is often suggested instead, but it skips *all* whitespace: if the
first text line is blank or starts with spaces, it silently eats that too. One hidden test
here starts with a line of spaces for exactly that reason.
""",
)

REVERSE_ECHO = Problem(
    id="reverse_echo",
    title="Echo, Backwards, Quickly",
    difficulty="easy",
    complexity="O(n)",
    time_limit=0.5,
    statement=r"""
Read `n` integers and print them in reverse order, one per line.

The work is trivial. The input and output are not: a million numbers each way, in half a
second.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 10^6). The second has `n` integers (|a_i| ≤ 10^9).
""",
    output=r"""
`n` lines: a_n, a_(n−1), ..., a_1.
""",
    samples=[
        Test("5\n1 2 3 4 5\n", "5\n4\n3\n2\n1\n"),
    ],
    tests=[
        Test("1\n-1000000000\n"),
    ],
    gens=[
        Gen("small", lambda rng: _echo(rng, rng.randint(1, 20), 100), 5),
        Gen("a million numbers", lambda rng: _echo(rng, 10**6, 10**9), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);   // cin/cout stop synchronising with C's stdio
    cin.tie(nullptr);              // reading no longer flushes cout first
    int n;
    cin >> n;
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    for (int i = n - 1; i >= 0; i--) cout << a[i] << '\n';   // '\n', never endl
    return 0;
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    for (int i = n - 1; i >= 0; i--) cout << a[i] << endl;
    return 0;
}
""",
    starter=r"""#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    // print a in reverse, one per line

    return 0;
}
""",
    hints=[
        r"""The algorithm is fine. Time goes into the I/O itself: what does `endl` do besides
printing a newline?""",
        r"""Put `ios::sync_with_stdio(false); cin.tie(nullptr);` at the top of `main`, and print
`'\n'` instead of `endl`.""",
    ],
    editorial=r"""
Measured on this machine with a million numbers: the fast version runs in about 0.08 s.
Keeping `endl` costs about 1.1 s, because every `endl` flushes the output buffer, a system
call per line. Leaving stdio synchronised costs about 0.85 s, because every `cin >>` and
`cout <<` then goes through C's stdio in lock-step. Both together: about 1.9 s.

So the two skeleton lines are not decoration:

```cpp
ios::sync_with_stdio(false);  // C++ streams get their own buffers
cin.tie(nullptr);             // reading no longer forces cout to flush
```

After them, do not mix `printf`/`scanf` with `cout`/`cin` in the same program: the two
now buffer separately, so output can come out in the wrong order.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp01",
    title="from Python to contest C++",
    track="cpp",
    order=1,
    summary="How an ICPC judge runs your program, the contest skeleton line by line, the "
            "first type traps, reading input in every shape, and output fast enough to pass.",
    prereqs=[],
    tags=["io", "cin", "cout", "getline", "fast io", "long long", "judge", "verdicts"],
    parts=[
        Part("What the judge does with your file", [
            Say(r"""
This track assumes you already program comfortably (in Python, say) and teaches C++ by
contrast: what is different, and which differences cost points in a contest. If you are
new to programming altogether, it will move too fast.

On LeetCode you fill in a method and a harness calls it. An ICPC judge does something
blunter. It compiles your whole file with GCC, runs the program once per secret test,
feeds the test to **standard input**, and compares what you print on **standard output**
with the expected output. Nothing else counts: not return values, not stderr, not how
elegant the code is.
"""),
            MCQ(r"""
The expected output is `42`. Your program prints `Answer: 42`. What does the judge say?
""", [
                Opt("Accepted: the number is right.",
                    why="The judge does not read English. It compares output token by token, "
                        "and `Answer:` is an extra token."),
                Opt("Wrong Answer.", correct=True,
                    why="Right. Print exactly what the output section asks for: no prompts, no "
                        "labels, no 'Enter n:'."),
                Opt("Presentation Error: right answer, wrong format.",
                    why="A few old judges had that verdict. The ones used at ICPC today "
                        "(DOMjudge, Kattis) call it Wrong Answer."),
            ], explain=r"""
Whitespace is usually forgiving (most judges compare tokens, so an extra space or a
trailing newline is fine), but words are not. This site's judge compares tokens too.
"""),
            MCQ(r"""
You want to print debugging information while you work, without it counting as output.
Where should it go?
""", [
                Opt("`cout`, and delete it before submitting.",
                    why="That works, if you remember. Forgetting one debug line is a classic "
                        "Wrong Answer."),
                Opt("`cerr`: standard error is not compared.", correct=True,
                    why="Yes. `cerr << \"x = \" << x << '\\n';` goes to stderr, which judges "
                        "ignore. It still costs time, so do not leave it inside a loop that "
                        "runs 10^7 times."),
                Opt("A file, with `ofstream`.",
                    why="Judges often forbid writing files, and it is more code for nothing: "
                        "`cerr` exists for this."),
            ]),
            Say(r"""
You will see these verdicts all the time, here and in contests:

| verdict | meaning |
| AC | accepted: every test passed |
| WA | wrong answer on some test |
| TLE | time limit exceeded (usually CPU time, per test) |
| RE | run-time error: crash, or `main` returned non-zero |
| CE | compilation error |

The judge stops at the first failing test, and tells you only which one. That is why
contest programmers test edge cases *before* submitting: a wrong submission costs 20
penalty minutes at ICPC.
"""),
            MCQ(r"""
Your program is correct but prints the answer and then `main` ends with `return 1;`.
What happens?
""", [
                Opt("AC: the output is right.",
                    why="The judge checks the exit code first. A non-zero exit means the program "
                        "crashed, as far as it can tell."),
                Opt("RE (run-time error).", correct=True,
                    why="Yes. `return 0;` (or falling off the end of `main`, which returns 0 "
                        "implicitly) is 'success'."),
                Opt("WA.",
                    why="The output is never compared: a non-zero exit code is already a failure."),
            ]),
        ]),
        Part("The skeleton, line by line", [
            Say(r"""
Almost every contest solution starts from the same few lines:

```cpp
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long a, b;
    cin >> a >> b;
    cout << a + b << '\n';
    return 0;
}
```

The last part of this lesson explains the two `ios`/`cin.tie` lines. First, the top two.
"""),
            MCQ(r"""
What is `#include <bits/stdc++.h>`?
""", [
                Opt("A GCC header that includes the entire standard library in one line.",
                    correct=True,
                    why="Yes. It saves remembering which header has `sort` (`<algorithm>`) or "
                        "`priority_queue` (`<queue>`). It is GCC-only and slows compilation a "
                        "little, which is fine in contests and bad style in real projects."),
                Opt("A contest-only header that makes cin and cout faster.",
                    why="Speed comes from the two `ios`/`tie` lines. The header only pulls "
                        "declarations in."),
                Opt("The C++ standard's official 'everything' header.",
                    why="It is not in the standard. MSVC and Apple's clang do not have it (this "
                        "site ships a stand-in for clang so the same code still compiles)."),
            ]),
            MCQ(r"""
What does `using namespace std;` save you from writing?
""", [
                Opt("The `std::` prefix, as in `std::vector`, `std::sort`, `std::cin`.",
                    correct=True,
                    why="Right. The standard library lives in the namespace `std`; this line "
                        "makes those names visible unqualified."),
                Opt("The `#include` lines for the standard library.",
                    why="Includes make declarations available; `using namespace` only changes "
                        "how you *name* them."),
                Opt("Declaring `main`.",
                    why="Every program still needs exactly one `main`."),
            ], explain=r"""
In large programs `using namespace std;` is frowned upon (names like `count`, `distance`
or `next` can collide with yours). In a 100-line contest file it is universal. The one
collision you may actually hit: naming a global variable `y1`, `left` or `count`; if the
compiler complains about an ambiguous name, rename your variable.
"""),
            Short(r"""
Predict the output of this fragment exactly:

```cpp
int x = 7, y = 2;
cout << x / y << " " << x % y << " " << 1.0 * x / y << "\n";
```
""", accept=["3 1 3.5"], placeholder="what it prints",
                hint="Two `int`s divide as integers. Multiplying by `1.0` first changes the type.",
                explain=r"""
`3 1 3.5`. `int / int` is integer division (like Python's `//` for positive numbers), `%`
is the remainder, and once one operand is a `double` the division is real. Python's `/`
always gives a float; C++ decides by the operand types.
"""),
        ]),
        Part("Types: the first big difference", [
            Say(r"""
In Python a name points at an object of any type, and integers grow as large as they
need to. In C++ a variable is a fixed-size box whose type you declare once:

| type | size | range (about) |
| `int` | 32 bits | ±2.1·10^9 |
| `long long` | 64 bits | ±9.2·10^18 |
| `double` | 64 bits | 15-16 significant digits |
| `char` | 8 bits | one character |
| `bool` | | `true` / `false` |
| `string` | grows | text |

A value that does not fit in its box **overflows**, and C++ does not warn you.
"""),
            MCQ(r"""
What does this print?

```cpp
int big = 2000000000;
big = big + big;
cout << big << '\n';
```
""", [
                Opt("4000000000", why="That is Python's answer. The sum does not fit in 32 bits."),
                Opt("A negative number (in practice −294967296), because the sum overflowed.",
                    correct=True,
                    why="Right. Signed overflow is formally *undefined behaviour*: in practice the "
                        "bits wrap around, but the compiler is also allowed to assume it never "
                        "happens and optimise accordingly. Either way the answer is garbage."),
                Opt("A compile error: the compiler sees the overflow.",
                    why="It usually cannot: the values could come from input. Overflow is a "
                        "silent run-time bug, which is what makes it dangerous."),
                Opt("It crashes with a run-time error.",
                    why="Integer overflow does not crash; it quietly produces a wrong number."),
            ]),
            Numeric(r"""
The largest `int` is 2^31 − 1. Roughly what is it? (Two significant digits are enough;
`2.1e9` is a fine way to type it.)
""", answer=2147483647, rel=0.05,
                explain=r"""
2,147,483,647 ≈ 2.1·10^9. Memorise "about two billion". Whenever a count, a sum or a
product in a problem can exceed that, the variable holding it must be a `long long`.
"""),
            MCQ(r"""
And this one? Note that the variable *is* a `long long`.

```cpp
long long x = 1000000 * 1000000;
```
""", [
                Opt("x = 10^12: the variable is 64-bit, so it fits.",
                    why="The *variable* is 64-bit, but `1000000 * 1000000` is computed first, "
                        "as `int * int`, in 32 bits. It overflows before it is stored."),
                Opt("x is garbage: the multiplication overflows in `int` before the assignment.",
                    correct=True,
                    why="Yes. C++ picks the type of an expression from its operands, not from "
                        "where the result goes. Write `1000000LL * 1000000`, or `1LL * a * b` "
                        "for variables."),
                Opt("A compile error about narrowing.",
                    why="GCC may *warn* about overflow in a constant expression, but it compiles. "
                        "With variables it cannot even warn."),
            ], explain=r"""
This bug survives code review because every declaration looks right. The rule: when
multiplying two things that could each be large, make one of them `long long` *before* the
multiplication.
"""),
            MCQ(r"""
Which of these is the reliable habit for getting the 64-bit product 10^12?
""", [
                Opt("`(long long)(1000000 * 1000000)`",
                    why="The cast is applied to the result, and the result was computed in `int` "
                        "and already overflowed. Casting garbage gives 64-bit garbage."),
                Opt("`1000000LL * 1000000`", correct=True,
                    why="Yes. The `LL` suffix makes the left operand a `long long`, so the other "
                        "is converted and the multiplication happens in 64 bits. With variables: "
                        "`1LL * a * b`."),
                Opt("`1e6 * 1e6`",
                    why="That is a `double` multiplication. It happens to be exact here, but a "
                        "`double` has 53 bits of precision, so products near 10^18 come out "
                        "rounded. Floating point is not a way around integer overflow."),
                Opt("`long long(1000000) * 1000000`",
                    why="Close in spirit, but it does not compile: the function-style cast needs a "
                        "one-word type name. `(long long)1000000 * 1000000` would work, since the "
                        "cast binds before the `*`."),
            ]),
            Try("big_sum", note="Read the limits first; the second sample is there to catch `int`."),
        ]),
        Part("Reading input in every shape", [
            Say(r"""
`cin >> x` skips any whitespace (spaces, tabs, newlines) and then reads one token into
`x`, converting it to `x`'s type. Line breaks mean nothing to it. Problems give input in
four shapes, and each has a standard idiom:

```cpp
// 1. a count, then that many values
int n; cin >> n;
vector<long long> a(n);
for (auto& x : a) cin >> x;

// 2. several test cases
int t; cin >> t;
while (t--) { /* read and solve one test */ }

// 3. until the input ends
long long x;
while (cin >> x) { /* ... */ }

// 4. whole lines, spaces included
string line;
getline(cin, line);
```
"""),
            MCQ(r"""
The input is `3`, a blank line, then `   4`. What do `a` and `b` hold after
`cin >> a >> b;`?
""", [
                Opt("a = 3, b = 4", correct=True,
                    why="Right: newlines and spaces are all just separators to `cin >>`."),
                Opt("a = 3, and the read of b fails at the blank line.",
                    why="`cin >>` never sees lines. It skips whitespace until it finds a token."),
                Opt("a = 3, b = 0",
                    why="Nothing stops at the blank line; `b` gets 4."),
            ]),
            Reflect(r"""
How does `while (cin >> x)` know when to stop? And what is the Python equivalent you would
have written?
""", answer=r"""
`cin >> x` returns the stream itself, and a stream converts to `false` once a read has
failed, which is what happens at end of input (or on a token that is not a number). So the
loop runs once per token. In Python: `for tok in sys.stdin.read().split(): x = int(tok)`.
"""),
            Numeric(r"""
Multi-test limits usually bound the *sum* of `n`, not each `n` separately. In Spread,
`t ≤ 10^4` and each `n ≤ 2·10^5`, but the sum of all `n` is at most `2·10^5`. If every test
case cleared a fixed array of size 2·10^5 (say with `fill` or `memset`), how many elements
would be cleared in the worst case?
""", answer=2e9, rel=0.5, unit="elements",
                explain=r"""
`10^4 · 2·10^5 = 2·10^9`: several seconds of clearing, for inputs that total only 2·10^5
numbers. When the limits bound the sum of `n`, each test case must cost O(its own `n`):
allocate `vector<long long> a(n)` inside the loop, or clear only the first `n` entries.
"""),
            Try("spread", note="Multi-test input. Reset per test, and check the type of the answer."),
            Try("running_total", note="No count given: read until the input runs out."),
            MCQ(r"""
What does `s` hold after `string s; cin >> s;` when the input line is `hello world`?
""", [
                Opt("`hello world`",
                    why="`cin >>` stops at whitespace, so a space ends the token. For the whole "
                        "line you need `getline`."),
                Opt("`hello`", correct=True,
                    why="Right. `world` is still waiting in the input for the next read."),
                Opt("Nothing: strings must be read with getline.",
                    why="`cin >> s` works fine for strings; it just reads one word."),
            ]),
            MCQ(r"""
The input is `2`, newline, `hello world`. What is in `line` after this?

```cpp
int n;
cin >> n;
string line;
getline(cin, line);
```
""", [
                Opt("`hello world`",
                    why="That is what you wanted. But look at what `cin >> n` consumed: the "
                        "digit `2`, and nothing after it."),
                Opt("An empty string.", correct=True,
                    why="Yes. `cin >> n` leaves the newline after `2` unread, and `getline` reads "
                        "up to that newline: an empty line. Consume it first, with an extra "
                        "`getline(cin, line);` or `cin.ignore();`."),
                Opt("`2`",
                    why="The `2` was already consumed by `cin >> n`."),
            ], explain=r"""
This is the most common input bug when a problem mixes numbers and whole lines. Whenever
you switch from `cin >>` to `getline`, ask: what is still sitting on the current line?
"""),
            Try("word_count"),
        ]),
        Part("Output, fast", [
            Say(r"""
Two lines of the skeleton are about speed:

```cpp
ios::sync_with_stdio(false);
cin.tie(nullptr);
```

By default C++ streams stay synchronised with C's `printf`/`scanf` machinery, so every
operation goes through it in lock-step. The first line turns that off and gives `cin` and
`cout` their own buffers. By default reading from `cin` also flushes `cout` first (useful
for interactive prompts, useless for judges); the second line turns that off.

And one habit: end lines with `'\n'`, not `endl`.
"""),
            MCQ(r"""
What is the difference between `cout << x << endl;` and `cout << x << '\n';`?
""", [
                Opt("None; `endl` is just the C++ name for a newline.",
                    why="Both print a newline, but `endl` also *flushes*: it forces the buffer "
                        "out to the operating system, a system call each time."),
                Opt("`endl` also flushes the output buffer, which is slow when done a million "
                    "times.", correct=True,
                    why="Right. On this machine, a million `endl`s cost about a second by "
                        "themselves. `'\\n'` lets the buffer fill and flush rarely."),
                Opt("`'\\n'` does not work on Windows judges.",
                    why="`'\\n'` is the newline on every platform C++ runs on; the stream "
                        "translates it if the system needs `\\r\\n`."),
            ]),
            Short(r"""
By default, `cout` prints a `double` with 6 significant digits. What does
`cout << 2.0 / 3 << '\n';` print?
""", accept=["0.666667"], placeholder="what it prints",
                explain=r"""
`0.666667`. When a problem wants, say, 9 digits after the decimal point, write
`cout << fixed << setprecision(9) << x;` once. `fixed` means "digits after the point"
rather than "significant digits", and both settings stay in force for later prints.
"""),
            Reflect(r"""
After `ios::sync_with_stdio(false);`, why is it a bad idea to print some things with
`printf` and others with `cout` in the same program?
""", answer=r"""
With synchronisation off, `cout` and `printf` keep separate buffers that are flushed
independently, so text can come out in a different order from the order it was printed.
Pick one family (`cin`/`cout` or `scanf`/`printf`) and use only it.
"""),
            Try("reverse_echo", note="The starter reads the input the slow way. The hidden tests "
                "have a million numbers and a 0.5 s limit."),
        ]),
    ],
    problems=[BIG_SUM, SPREAD, RUNNING_TOTAL, WORD_COUNT, REVERSE_ECHO],
    cards=[
        Card(r"""How does an ICPC judge feed input to your program and read its answer?""",
             r"""It runs the whole program once per test, with the test on standard input, and compares standard output (token by token, usually) with the expected output."""),
        Card(r"""Where can debug output go so the judge ignores it?""",
             r"""`cerr` (standard error). Remove it from hot loops: it still costs time."""),
        Card(r"""What verdict do you get if `main` returns a non-zero value?""",
             r"""RE (run-time error), even if the printed output was correct."""),
        Card(r"""Largest `int`, and largest `long long`, roughly?""",
             r"""`int`: 2^31 − 1 ≈ 2.1·10^9. `long long`: 2^63 − 1 ≈ 9.2·10^18."""),
        Card(r"""Why is `long long x = a * b;` wrong when `a` and `b` are `int`s near 10^6?""",
             r"""The product is computed in `int` and overflows before the assignment. Write `1LL * a * b`."""),
        Card(r"""Idiom to read integers until the input ends?""",
             r"""`while (cin >> x) { ... }`: the read fails, and the stream turns false, at end of input."""),
        Card(r"""Why does `getline` return an empty string right after `cin >> n`?""",
             r"""`cin >> n` leaves the newline after `n` unread; `getline` reads up to it. Consume it with an extra `getline` or `cin.ignore()`."""),
        Card(r"""The two fast-I/O lines, and what each does?""",
             r"""`ios::sync_with_stdio(false);` gives C++ streams their own buffers; `cin.tie(nullptr);` stops `cin` from flushing `cout` before every read."""),
        Card(r"""`endl` vs `'\n'`?""",
             r"""Both end the line; `endl` also flushes the buffer (a system call). Use `'\n'`."""),
        Card(r"""How do you print a `double` with exactly 9 digits after the decimal point?""",
             r"""`cout << fixed << setprecision(9) << x;`"""),
        Card(r"""How do you split one line of text into words in C++?""",
             r"""`stringstream ss(line); string w; while (ss >> w) { ... }`"""),
    ],
)
