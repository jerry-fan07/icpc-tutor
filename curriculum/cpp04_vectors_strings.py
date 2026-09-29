from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _field(rng, n, m, density):
    rows = ["".join("*" if rng.random() < density else "." for _ in range(m)) for _ in range(n)]
    return f"{n} {m}\n" + "\n".join(rows) + "\n"


def _field_fast(rng, n, m, density):
    rows = ["".join(rng.choices("*.", weights=(density, 1 - density), k=m)) for _ in range(n)]
    return f"{n} {m}\n" + "\n".join(rows) + "\n"


def _runs(rng, total, alphabet, maxrun):
    parts, size = [], 0
    while size < total:
        k = min(total - size, rng.randint(1, maxrun))
        parts.append(rng.choice(alphabet) * k)
        size += k
    return "".join(parts) + "\n"


def _near_pal(rng, n, alphabet):
    """A palindrome of length about n with 0, 1 or 2 random characters inserted."""
    half = "".join(rng.choices(alphabet, k=n // 2))
    s = list(half + ("".join(rng.choices(alphabet, k=n % 2))) + half[::-1])
    for _ in range(rng.choice((0, 1, 1, 2))):
        s.insert(rng.randint(0, len(s)), rng.choice(alphabet))
    return "".join(s) or rng.choice(alphabet)


def _pal_tests(rng, t, lo, hi, alphabet):
    words = [_near_pal(rng, rng.randint(lo, hi), alphabet) for _ in range(t)]
    return f"{t}\n" + "\n".join(words) + "\n"


def _deep_mismatch(rng, half, middle):
    p = "".join(rng.choices("ab", k=half))
    return "1\n" + p + middle + p[::-1] + "\n"


def _keys(rng, n, p_bracket):
    keys = rng.choices("[]x", weights=(p_bracket, p_bracket, 1 - 2 * p_bracket), k=n)
    letters = iter(rng.choices("abcdefghijklmnopqrstuvwxyz", k=n))
    s = "".join(next(letters) if c == "x" else c for c in keys)
    if not any(c.isalpha() for c in s):
        s += "a"
    return s + "\n"


def _long_tail_then_home(rng, n):
    tail = "".join(rng.choices("abcdefghij", k=n // 2))
    front = "".join(rng.choices("klmnopqrst", k=n - n // 2 - 1))
    return tail + "[" + front + "\n"


# --------------------------------------------------------------------- problems
MINESWEEPER = Problem(
    id="minesweeper",
    title="Minesweeper Numbers",
    difficulty="easy",
    source="UVa 10189 - Minesweeper",
    complexity="O(n·m)",
    statement=r"""
A minefield is an `n × m` grid in which `*` is a mine and `.` is a safe cell. Replace every
safe cell by the number of mines among its neighbours: the up to eight cells that touch it
horizontally, vertically or diagonally. Mines stay `*`.
""",
    input=r"""
The first line has `n` and `m` (1 ≤ n, m ≤ 1000). Then `n` lines follow, each with `m`
characters, `*` or `.`.
""",
    output=r"""
The `n` lines of the grid, with every `.` replaced by a digit from `0` to `8`.
""",
    samples=[
        Test("3 4\n*...\n..*.\n...*\n", "*211\n12*2\n012*\n",
             note="Three rows, four columns: keep `n` and `m` apart. And a cell of a `string` "
                  "is a `char`: the count 2 has to become the character `'2'`."),
        Test("2 1\n.\n*\n", "1\n*\n"),
    ],
    tests=[
        Test("1 1\n.\n"),
        Test("1 1\n*\n"),
        Test("1 5\n*.*.*\n"),
        Test("4 1\n.\n*\n.\n.\n"),
        Test("3 3\n***\n*.*\n***\n"),
        Test("2 3\n...\n...\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _field(rng, rng.randint(1, 8), rng.randint(1, 8), rng.random()), 12),
        Gen("wide and flat", lambda rng: _field(rng, rng.randint(1, 3), 300, 0.3), 2),
        Gen("tall and thin", lambda rng: _field(rng, 300, rng.randint(1, 3), 0.3), 2),
        Gen("max size", lambda rng: _field_fast(rng, 1000, 1000, 0.2), 1),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<string> g(n);
    for (auto& row : g) cin >> row;
    // the eight directions as (row, column) offsets
    const int dr[8] = {-1, -1, -1, 0, 0, 1, 1, 1};
    const int dc[8] = {-1, 0, 1, -1, 1, -1, 0, 1};
    vector<string> out = g;                       // a copy: count from the original grid
    for (int r = 0; r < n; r++)
        for (int c = 0; c < m; c++) {
            if (g[r][c] == '*') continue;
            int cnt = 0;
            for (int k = 0; k < 8; k++) {
                int nr = r + dr[k], nc = c + dc[k];
                // check the bounds BEFORE indexing: g[-1] is undefined behaviour
                if (0 <= nr && nr < n && 0 <= nc && nc < m && g[nr][nc] == '*') cnt++;
            }
            out[r][c] = char('0' + cnt);          // the digit character, not the number
        }
    for (const auto& row : out) cout << row << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// A border of safe cells around the grid removes every bounds check.
int main() {
    int n, m;
    cin >> n >> m;
    vector<string> g(n + 2, string(m + 2, '.'));
    for (int r = 1; r <= n; r++) {
        string row;
        cin >> row;
        for (int c = 1; c <= m; c++) g[r][c] = row[c - 1];
    }
    for (int r = 1; r <= n; r++) {
        for (int c = 1; c <= m; c++) {
            if (g[r][c] == '*') { putchar('*'); continue; }
            int cnt = 0;
            for (int a = r - 1; a <= r + 1; a++)
                for (int b = c - 1; b <= c + 1; b++) cnt += g[a][b] == '*';
            printf("%d", cnt);
        }
        putchar('\n');
    }
}
""",
    hints=[
        r"""Read the grid as `vector<string> g(n)`, one row per string: `g[r][c]` is row `r`, column
`c`. Two arrays `dr[8]`, `dc[8]` list the neighbour offsets.""",
        r"""Check `0 <= nr && nr < n && 0 <= nc && nc < m` before you touch `g[nr][nc]`. Rows
go up to `n`, columns up to `m`.""",
        r"""Write the count into a copy of the grid, as `char('0' + cnt)`. Assigning the `int`
itself stores the character with code 2, which is not the character `2`.""",
    ],
    editorial=r"""
Read the rows into a `vector<string>`, and for every safe cell count the mines among the
eight offsets `(dr[k], dc[k])`. Three details decide the verdict:

- **Bounds before indexing.** For a cell on the border some neighbours do not exist.
  `g[-1]` or `g[r][m]` is not an error in C++, it is undefined behaviour: it can crash,
  and more often it silently reads a neighbouring piece of memory. The condition
  `0 <= nr && nr < n && 0 <= nc && nc < m` must come first in the `&&` chain, which is
  evaluated left to right and stops at the first false.
- **`n` rows, `m` columns.** Square test grids hide a swapped bound; the first sample is
  3 × 4 for that reason.
- **A digit is a character.** `out[r][c] = cnt` stores the `char` with code `cnt` (an
  invisible control character); `char('0' + cnt)` stores the digit.

Writing into a copy keeps the counting honest (here the digits could never be mistaken for
`*`, but in "update the grid" problems, reading cells you already overwrote is a classic
bug). An alternative that removes the bounds checks: pad the grid with a border of `.`,
as the brute force does.
""",
)

RLE = Problem(
    id="run_length",
    title="Run-Length Encoding",
    difficulty="easy",
    complexity="O(n)",
    statement=r"""
Run-length encoding compresses a string by replacing every maximal run of equal characters
with the character followed by the length of the run. For example `aaabccdddd` becomes
`a3b1c2d4`.

Encode the given string.
""",
    input=r"""
One line: a string of between 1 and 10^6 lowercase letters.
""",
    output=r"""
One line: the encoded string.
""",
    samples=[
        Test("aaabccdddd\n", "a3b1c2d4\n"),
        Test("zzzzzzzzzzzzq\n", "z12q1\n",
             note="A run of 12 is written with two digits. `to_string(12)` is the string "
                  "`\"12\"`; `char('0' + 12)` is `'<'`."),
    ],
    tests=[
        Test("a\n"),
        Test("abcabc\n"),
        Test("aaaaaaaaaa\n"),
        Test("x" * 1000 + "y\n"),
    ],
    gens=[
        Gen("small runs", lambda rng: _runs(rng, rng.randint(1, 30), "ab", 4), 12),
        Gen("medium runs", lambda rng: _runs(rng, 10000, "abc", 30), 2),
        Gen("one huge run", lambda rng: "q" * 10**6 + "\n", 1),
        Gen("max length, every run 1", lambda rng: "ab" * 500000 + "\n", 1, large=True),
        Gen("max length, short runs", lambda rng: _runs(rng, 10**6, "abcdefghijklmnopqrstuvwxyz", 3), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    string res;                       // grows at the end: amortised O(1) per character
    int n = s.size();
    for (int i = 0; i < n;) {
        int j = i;
        while (j < n && s[j] == s[i]) j++;    // s[i..j-1] is one maximal run
        res += s[i];
        res += to_string(j - i);              // the digits, not the char with that code
        i = j;
    }
    cout << res << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s;
    cin >> s;
    vector<pair<char, int>> runs;
    for (char c : s) {
        if (!runs.empty() && runs.back().first == c) runs.back().second++;
        else runs.push_back({c, 1});
    }
    for (auto [c, k] : runs) cout << c << k;
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    string res;
    int n = s.size();
    for (int i = 0; i < n;) {
        int j = i;
        while (j < n && s[j] == s[i]) j++;
        res = res + s[i] + to_string(j - i);  // builds a whole new string every run
        i = j;
    }
    cout << res << '\n';
    return 0;
}
""",
    hints=[
        r"""Walk with two indices: `i` at the start of a run, `j` moving right while `s[j] == s[i]`.
The run has length `j - i`.""",
        r"""Append with `res += s[i]; res += to_string(j - i);`. Not `res += j - i` (that appends
the character with that code) and not `res = res + ...` (that copies `res` every time).""",
    ],
    editorial=r"""
Scan runs with two indices and append each run's letter and length to the result. The
only real decisions are how to append.

`res = res + x` first builds `res + x`, a brand-new string holding a copy of all of `res`,
then replaces `res` with it. That is O(|res|) per run, and a string of 10^6 alternating
letters has 10^6 runs and a 2·10^6-character result: about 10^12 characters copied. In
CPython the same line is fast, because the interpreter quietly turns `s = s + t` into an
in-place append when nothing else refers to `s`. C++ does what you wrote. `res += x`
appends in place, amortised O(1) per character, like `push_back`.

And `res += j - i` compiles, because an `int` converts to `char`: it appends the character
whose code is the run length. `to_string` gives the digits.
""",
)

ONE_DELETION = Problem(
    id="one_deletion",
    title="One Deletion Away",
    difficulty="medium",
    source="LeetCode 680 - Valid Palindrome II",
    complexity="O(total length)",
    statement=r"""
A palindrome reads the same forwards and backwards. For each given string, decide whether
it can be made into a palindrome by deleting **at most one** character.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5). Each of the next `t` lines has a non-empty string of
lowercase letters. The total length of all strings is at most 10^6.
""",
    output=r"""
For each string, print `YES` if deleting at most one character can make it a palindrome,
and `NO` otherwise.
""",
    samples=[
        Test("5\nabca\nabc\nracecar\nab\nz\n", "YES\nNO\nYES\nYES\nYES\n",
             note="`abca`: delete `b` (or `c`). `racecar` needs no deletion at all."),
    ],
    tests=[
        Test("4\ncbbcc\nccbbc\ndeeee\neeeed\n"),
        Test("3\nabcdba\nabccbxa\nabcxcbya\n"),
        Test("1\naguokepatgbnvfqmgmlcupuufxoohdfpgjdmysgvhmvffcnqxjjxqncffvmhvgsymdjgpfdhooxfuupuculmgmqfvnbgtapekouga\n"),
    ],
    gens=[
        Gen("short near-palindromes", lambda rng: _pal_tests(rng, 300, 1, 9, "abc"), 14),
        Gen("medium near-palindromes", lambda rng: _pal_tests(rng, 100, 100, 1000, "ab"), 2),
        Gen("many small strings", lambda rng: _pal_tests(rng, 100000, 1, 10, "ab"), 1, large=True),
        Gen("one long string, deletion in the middle", lambda rng: _deep_mismatch(rng, 499999, "ab"), 1, large=True),
        Gen("one long string, two deletions needed", lambda rng: _deep_mismatch(rng, 499998, "abc"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// Is s[l..r] a palindrome? Indices into the original: no substring is ever copied.
bool is_pal(const string& s, int l, int r) {
    while (l < r) {
        if (s[l] != s[r]) return false;
        l++, r--;
    }
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        string s;
        cin >> s;
        int l = 0, r = (int)s.size() - 1;
        while (l < r && s[l] == s[r]) l++, r--;          // matched pairs are settled
        // at the first mismatch, one of s[l], s[r] must go: try both
        bool ok = l >= r || is_pal(s, l + 1, r) || is_pal(s, l, r - 1);
        cout << (ok ? "YES" : "NO") << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
bool pal(const string& s) { return s == string(s.rbegin(), s.rend()); }
int main() {
    int t;
    cin >> t;
    while (t--) {
        string s;
        cin >> s;
        bool ok = pal(s);
        for (int i = 0; i < (int)s.size() && !ok; i++)
            if (pal(s.substr(0, i) + s.substr(i + 1))) ok = true;
        cout << (ok ? "YES" : "NO") << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;

bool pal(const string& s) { return s == string(s.rbegin(), s.rend()); }

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        string s;
        cin >> s;
        bool ok = pal(s);
        for (int i = 0; i < (int)s.size() && !ok; i++)      // try every deletion
            if (pal(s.substr(0, i) + s.substr(i + 1))) ok = true;
        cout << (ok ? "YES" : "NO") << '\n';
    }
    return 0;
}
""",
    hints=[
        r"""Move two indices inward from both ends while the characters match. Those pairs are
fine whatever you delete later. What must happen at the first pair that does not match?""",
        r"""One of the two mismatched characters has to be deleted. Try both: is `s[l+1..r]` a
palindrome, or is `s[l..r-1]`? Check with indices, `is_pal(const string& s, int l, int r)`,
not with `substr`.""",
        r"""Trying only one side fails on `cbbcc`.""",
    ],
    editorial=r"""
Walk `l` from the left and `r` from the right while `s[l] == s[r]`. If they meet, the
string is already a palindrome. Otherwise `s[l] ≠ s[r]`, and a single deletion must remove
one of these two characters: check whether `s[l+1..r]` or `s[l..r−1]` is a palindrome. Two
linear checks, O(n) in total.

Why deleting some earlier index `i < l` cannot do better: the resulting string pairs
`s[j+1]` with `s[n−1−j]` for `i ≤ j < l`, and since `s[n−1−j] = s[j]` there, it would need
`s[i] = s[i+1] = ... = s[l]`: a run of equal characters. Deleting any character of a run
gives the same string, so deleting `s[l]` works too. The same argument covers `i > r`.

Both candidates are needed: in `cbbcc` the mismatch is `b` (index 1) against `c` (index
3), and only deleting the `c` works.

The trying-every-deletion approach is O(n^2): each attempt builds an (n−1)-character string
with `substr` and `+` before comparing anything. For a 10^6-character string that is about
10^12 character copies. And in the two-pointer solution, write the palindrome check on
indices of the original string; `is_pal(s.substr(l + 1, r - l))` would work here (it is
called twice) but is the habit that turns other string problems quadratic.
""",
)

HOME_END = Problem(
    id="home_end",
    title="Home and End",
    difficulty="hard",
    source="UVa 11988 - Broken Keyboard (a.k.a. Beiju Text)",
    complexity="O(n)",
    statement=r"""
You are typing a long text on a keyboard whose Home and End keys sometimes press
themselves. Home moves the cursor to the beginning of the text; End moves it to the end.
Every letter is inserted at the cursor, and the cursor moves past it. You are not looking
at the screen.

The text starts empty, with the cursor at its end. Given every key press in order, print
the final text.
""",
    input=r"""
One line of between 1 and 2·10^6 characters: lowercase letters, `[` for Home and `]` for
End. At least one character is a letter.
""",
    output=r"""
One line: the final text.
""",
    samples=[
        Test("hello[world]\n", "worldhello\n"),
        Test("ab[cd]ef[gh\n", "ghcdabef\n",
             note="After `ab`, Home: `cd` goes in front. End: `ef` goes after `ab`. Home "
                  "again: `gh` goes in front of everything."),
    ],
    tests=[
        Test("[[]][a]b[c\n"),
        Test("abc[\n"),
        Test("a[b[c[d\n"),
        Test("[x\n"),
        Test("x]]]\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _keys(rng, rng.randint(1, 20), 0.15), 12),
        Gen("medium random", lambda rng: _keys(rng, 3000, 0.05), 3),
        Gen("long tail, then Home", lambda rng: _long_tail_then_home(rng, 2 * 10**6), 1, large=True),
        Gen("max length, random keys", lambda rng: _keys(rng, 2 * 10**6, 0.01), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string keys;
    cin >> keys;
    // A block typed after a Home ends up in front of everything typed before it.
    // So: keep the Home-blocks in typing order, and all End-mode text in one string.
    vector<string> front;
    string back;
    bool at_front = false;
    for (char c : keys) {
        if (c == '[') {
            front.push_back("");          // a new block, which will go first
            at_front = true;
        } else if (c == ']') {
            at_front = false;
        } else if (at_front) {
            front.back() += c;            // appending: amortised O(1)
        } else {
            back += c;
        }
    }
    string out;
    for (int i = (int)front.size() - 1; i >= 0; i--) out += front[i];   // latest block first
    out += back;
    cout << out << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string keys;
    cin >> keys;
    string text;
    size_t pos = 0;
    for (char c : keys) {
        if (c == '[') pos = 0;
        else if (c == ']') pos = text.size();
        else text.insert(pos++, 1, c);
    }
    cout << text << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string keys;
    cin >> keys;
    string text;
    size_t pos = 0;
    for (char c : keys) {
        if (c == '[') pos = 0;
        else if (c == ']') pos = text.size();
        else text.insert(pos++, 1, c);        // shifts everything after pos: O(n)
    }
    cout << text << '\n';
    return 0;
}
""",
    hints=[
        r"""Simulating the cursor with `text.insert(pos, 1, c)` is correct, and O(n) per letter
whenever the cursor is not at the end. Up to 2·10^6 keys make that about 10^12 moves.""",
        r"""Think in blocks: the letters typed after one Home, up to the next `[` or `]`, stay
together. Where does such a block end up relative to text typed earlier? And relative to a
block typed after a *later* Home?""",
        r"""Keep a `vector<string>` of Home-blocks and one string of everything typed in End mode.
The answer is the Home-blocks from last to first, then the End-mode text.""",
    ],
    editorial=r"""
The direct simulation keeps a cursor and inserts each letter at it. `string::insert` in the
middle shifts every character after the cursor, so after a long stretch of typing followed
by Home, every further letter moves the whole tail: with 10^6 letters on each side, 10^12
character moves.

Look at blocks instead. Letters typed in End mode are appended at the end, so together they
form one string, `back`, in typing order. Letters typed after a Home form a block that is
inserted at the very front, in order, and stays contiguous (nothing is ever inserted inside
it: the next Home puts later text *before* it, and End puts it after everything). So the
final text is: the Home-blocks from the most recent to the oldest, followed by `back`. Every
character is appended once and copied once: O(n).

Two other correct O(n) solutions: a `list<char>` with an iterator as the cursor (insertion
at an iterator is O(1) in a linked list, at the cost of a pointer or two per character), or
a `deque<string>` of blocks with `push_front`. Pushing single *characters* to the front of
a deque does not work: a block typed after Home would come out reversed.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp04",
    title="arrays, vectors & strings",
    track="cpp",
    order=4,
    summary="What every vector and string operation costs, grids as vectors of strings, "
            "building strings without quadratic copies, substr/find/to_string/stoi, "
            "palindromes by index, and why inserting in the middle is a trap.",
    prereqs=["cpp03"],
    tags=["vector", "push_back", "resize", "reserve", "2d vector", "grid", "string",
          "substr", "find", "to_string", "stoi", "palindrome", "insert", "amortised"],
    parts=[
        Part("vector: a list with a price tag", [
            Say(r"""
A `vector` is Python's `list` with a fixed element type. Most operations translate
directly; the costs are the same as in Python, but C++ makes you pay for them visibly:

| Python | C++ (`vector<int> v`) | cost |
| `v = [0] * n` | `vector<int> v(n);` or `v(n, x)` | O(n) |
| `v.append(x)` | `v.push_back(x)` | O(1) amortised |
| `v.pop()` | `v.pop_back()` | O(1) |
| `v[-1]` | `v.back()` | O(1) |
| `len(v)` | `v.size()` (unsigned!) | O(1) |
| `v.insert(0, x)` | `v.insert(v.begin(), x)` | O(n) |
| `v.pop(0)` | `v.erase(v.begin())` | O(n) |
| `w = v` | `vector<int> w = v;` | O(n): a copy |

The last row is a real difference: in Python `w = v` makes a second name for the same list;
in C++ it copies (cpp03: everything is a copy unless you ask for a reference).
"""),
            Short(r"""
What does this print?

```cpp
int n = 3;
vector<int> v(n);
for (int i = 0; i < n; i++) v.push_back(i + 1);
cout << v.size() << ' ' << v[0] << '\n';
```
""", accept=["6 0"], placeholder="what it prints",
                hint="What does `vector<int> v(n)` already contain?",
                explain=r"""
`6 0`. `vector<int> v(n)` already holds `n` zeros, and `push_back` adds *after* them. Pick
one style: `vector<int> v(n);` then assign `v[i] = ...`, or `vector<int> v;` then
`push_back`. Mixing them is one of the most common vector bugs.
"""),
            MCQ(r"""
You know the final size in advance, so you call `reserve`. What does this do?

```cpp
vector<int> v;
v.reserve(5);
v[0] = 7;
```
""", [
                Opt("`v` becomes `{7}`.",
                    why="`reserve` never changes the size. `v` is still empty afterwards."),
                Opt("It throws `out_of_range`.",
                    why="`operator[]` never checks bounds. `v.at(0)` would throw; `v[0]` just "
                        "writes."),
                Opt("Undefined behaviour: `reserve` only allocates capacity, the size is still "
                    "0, so `v[0]` does not exist.", correct=True,
                    why="Right. The write may even appear to work, which is worse. To make "
                        "elements exist, use `resize(5)` or construct with `vector<int> v(5)`."),
                Opt("A compile error.",
                    why="The compiler does not track sizes; this compiles fine."),
            ], explain=r"""
`reserve(k)` is an optimisation for a sequence of `push_back`s: it allocates room for `k`
elements up front so no reallocation happens. `resize(k)` changes the number of elements.
`v.at(i)` is `v[i]` with a bounds check that throws (a run-time error you can see); it is a
cheap way to debug index bugs.
"""),
            MCQ(r"""
Python's `v[-1]` is the last element. What is `v[-1]` in C++?
""", [
                Opt("The last element, same as Python.",
                    why="C++ indices do not wrap around. The last element is `v.back()` or "
                        "`v[v.size() - 1]`."),
                Opt("A compile error: indices must be unsigned.",
                    why="`-1` converts silently to an unsigned index (2^64 − 1, cpp02), and "
                        "it compiles."),
                Opt("Undefined behaviour: it reads memory just before the vector's elements.",
                    correct=True,
                    why="Right. No exception, no wrap-around: whatever bytes are there. The "
                        "same goes for `v[v.size()]`, one past the end."),
            ]),
            Numeric(r"""
`push_back` is O(1) *amortised*: when the vector is full, it allocates a buffer twice as
big and moves everything over. Starting empty, about how many reallocations do 10^6
`push_back`s cause?
""", answer=21, rel=0.2, unit="reallocations",
                hint="The capacity goes 1, 2, 4, 8, ... until it reaches 10^6.",
                explain=r"""
About log₂(10^6) ≈ 20; measured with GCC: 21 (capacities 1, 2, 4, ..., 2^20). The moves add
up to 1 + 2 + 4 + ... + 2^19 < 2·10^6, less than two per element. That is what "amortised
O(1)" means: an occasional expensive step, paid for by all the cheap ones.
"""),
            Numeric(r"""
Now the opposite. A vector of 2·10^5 elements used as a queue: take the front with
`v.erase(v.begin())` until it is empty. Every erase shifts all remaining elements left by
one. Roughly how many element moves in total?
""", answer=2e10, rel=0.5, unit="moves",
                explain=r"""
(n − 1) + (n − 2) + ... ≈ n^2 / 2 = 2·10^10. Shifting is a fast memory copy, and it still
took 1.4 s here, over a typical limit; at 10^6 elements it is 25 times worse. Python's
`list.pop(0)` has exactly the same cost, which is why Python has `collections.deque`. In C++, keep an index `head` that
moves forward instead of erasing, or use `queue`/`deque` (cpp05).
"""),
            Short(r"""
What does this print? (In Python, `b = a` then `b[0] = 99` would change `a` too.)

```cpp
vector<int> a = {1, 2, 3};
vector<int> b = a;
b[0] = 99;
cout << a[0] << '\n';
```
""", accept=["1"], placeholder="what it prints",
                explain=r"""
`1`. `b` is a separate copy. That is safer than Python's aliasing, and costs O(n); if you
want a second name for the same vector, say so: `vector<int>& b = a;`.
"""),
        ]),
        Part("Grids", [
            Say(r"""
Grids come in two forms. A grid of characters is read row by row into strings:

```cpp
int n, m;
cin >> n >> m;
vector<string> g(n);
for (auto& row : g) cin >> row;      // g[r][c]: row r, column c
```

A grid of numbers is a vector of vectors: `vector<vector<int>> a(n, vector<int>(m, 0));`.
Neighbours are visited with offset arrays, one entry per direction:

```cpp
const int dr[4] = {-1, 1, 0, 0}, dc[4] = {0, 0, -1, 1};
for (int k = 0; k < 4; k++) {
    int nr = r + dr[k], nc = c + dc[k];
    ...
}
```
"""),
            Short(r"""
In Python, `a = [[0] * 3] * 2` makes two references to *one* row, so `a[0][0] = 5` also
changes `a[1][0]`. What does the C++ version print?

```cpp
vector<vector<int>> a(2, vector<int>(3, 0));
a[0][0] = 5;
cout << a[1][0] << '\n';
```
""", accept=["0"], placeholder="what it prints",
                explain=r"""
`0`. The constructor copies the prototype row into each of the `n` slots, so every row is
independent. One Python trap that C++ does not have.
"""),
            MCQ(r"""
Your loop visits the neighbour `(r − 1, c)` of a cell in row 0 without checking bounds:
`g[r - 1][c]`. What happens?
""", [
                Opt("It wraps around to the last row, like Python's `g[-1]`.",
                    why="C++ does not wrap. (And in Python this wrap-around is a silent bug "
                        "too: the last row is not a neighbour of the first.)"),
                Opt("It returns a harmless value such as `'\\0'`, so the count is unaffected.",
                    why="Nothing guarantees any particular value, or that the read does not "
                        "crash."),
                Opt("Undefined behaviour: it may crash, or read unrelated memory and count a "
                    "mine that is not there.", correct=True,
                    why="Right, and it can pass every sample and fail one hidden test. Check "
                        "`0 <= nr && nr < n && 0 <= nc && nc < m` first."),
                Opt("An `out_of_range` exception.",
                    why="Only `.at()` throws. `[]` does no checking at all."),
            ], explain=r"""
Put the bounds test first in the `&&` chain: `&&` evaluates left to right and stops at the
first false, so `g[nr][nc]` is never touched when `nr` is out of range. An alternative is to
pad the grid with a border of harmless cells, so every real cell has all its neighbours.
"""),
            MCQ(r"""
You will see this in other people's contest code:

```cpp
int n;
cin >> n;
int a[n];
```

What is it?
""", [
                Opt("Standard C++: an array sized at run time.",
                    why="Standard C++ requires array sizes known at compile time. This is a "
                        "variable-length array, a C feature GCC accepts as an extension."),
                Opt("A GCC extension (a variable-length array) that lives on the stack and is "
                    "not initialised.", correct=True,
                    why="Right. With `n = 10^7` it overflows an 8 MB stack, and its elements "
                        "start as garbage. `vector<int> a(n)` has neither problem."),
                Opt("The same as `vector<int> a(n)`, just faster.",
                    why="A vector's elements live on the heap and start at zero. The speed "
                        "difference is negligible."),
            ], explain=r"""
Fixed-size C arrays are still common and fine *as globals*: `int grid[1005][1005];` sized to
the maximum limits, zero-initialised, no stack issue (cpp03). For sizes read from the input,
use `vector`.
"""),
            Try("minesweeper", note="`n` rows and `m` columns, bounds checks, and a count that "
                "has to become a digit character."),
        ]),
        Part("Building strings", [
            Say(r"""
A C++ `string` is a sequence of `char`s with text methods, and unlike Python's `str` it is
**mutable**: `s[0] = 'x'` and `s += 'd'` change it in place.

| Python | C++ | cost |
| `s[a:b]` | `s.substr(a, b - a)` | O(b − a): a copy |
| `s.find(t)` | `s.find(t)`, `string::npos` if absent | O(n·m) worst |
| `str(x)` | `to_string(x)` | |
| `int(s)` | `stoi(s)`, `stoll(s)` | |
| `s[::-1]` | `string(s.rbegin(), s.rend())` | O(n) |
| (in place) | `reverse(s.begin(), s.end())` | O(n) |
| `s + t` | `s + t` | O(n + m): a new string |
| `s += t` | `s += t` | O(m) amortised |
"""),
            Short(r"""
What does this print?

```cpp
string s = "contest";
cout << s.substr(2, 3) << '\n';
```
""", accept=["nte"], placeholder="what it prints",
                hint="The second argument is not an end index.",
                explain=r"""
`nte`: three characters starting at index 2. Python's `s[2:3]` would give `n`, because
Python slices take an end index and `substr` takes a **length**. `s.substr(a)` with one
argument is the rest of the string, like `s[a:]`.
"""),
            MCQ(r"""
What is wrong with `if (s.find("ab")) { ... }` as "if `s` contains `ab`"?
""", [
                Opt("Nothing: `find` returns true or false.",
                    why="`find` returns a position: where the match starts, or `string::npos` "
                        "(the largest `size_t`) if there is none."),
                Opt("It is backwards twice: a match at position 0 is false, and no match "
                    "(`npos`, a huge number) is true.", correct=True,
                    why="Right. Write `if (s.find(\"ab\") != string::npos)`."),
                Opt("It only finds `ab` at the start of the string.",
                    why="It searches the whole string. The problem is how the returned "
                        "position converts to `bool`."),
            ]),
            Numeric(r"""
Building a 10^6-character string one character at a time with `s = s + c;`: each step
copies all of `s` into a new string. Roughly how many characters are copied in total?
""", answer=5e11, rel=0.5, unit="characters",
                explain=r"""
1 + 2 + ... + 10^6 ≈ 5·10^11: about 12 seconds when measured here. CPython hides this: it turns `s = s + c` into
an in-place append when nothing else refers to `s`, so the habit is fast in Python. C++ does
exactly what the line says: build a new string, copy, discard the old one. `s += c` (or
`s.push_back(c)`) appends in place, amortised O(1).
"""),
            Short(r"""
What does this print?

```cpp
string s = "x";
int cnt = 65;
s += cnt;
cout << s << '\n';
```
""", accept=["xA"], placeholder="what it prints",
                explain=r"""
`xA`. There is no `+=` for `int`, but an `int` converts to `char`, so this appends the
character with code 65. No warning, even with `-Wall`. To append the digits, use
`s += to_string(cnt);`.
"""),
            MCQ(r"""
What does `stoi("3000000000")` do?
""", [
                Opt("Returns 3000000000.",
                    why="`stoi` returns an `int`, which stops at 2147483647."),
                Opt("Returns an overflowed negative number.",
                    why="`stoi` checks the range, unlike arithmetic."),
                Opt("Throws `out_of_range`; uncaught, the program aborts: RE.", correct=True,
                    why="Right: it printed \"terminate called after throwing an instance of "
                        "'std::out_of_range'\" and exited with code 134. Use `stoll` for "
                        "values past 2.1·10^9."),
                Opt("Returns `INT_MAX`.",
                    why="That is what some C functions do (`strtol` clamps to its type's "
                        "maximum); `stoi` throws instead."),
            ]),
            Try("run_length", note="Append with `+=`, and turn counts into digits with "
                "`to_string`. The hidden tests have a million runs."),
        ]),
        Part("Palindromes, by index", [
            Say(r"""
Character tests and conversions come from C's `<cctype>` (already in `bits/stdc++.h`):
`isalpha`, `isdigit`, `isspace`, `isupper`, `islower`, `tolower`, `toupper`. They work on
`int`s (cpp02): the tests return zero or non-zero, and `tolower`/`toupper` return an `int`
that you store in a `char` before printing it.

The plain palindrome check, with two indices meeting in the middle:

```cpp
bool is_pal(const string& s, int l, int r) {    // is s[l..r] a palindrome?
    while (l < r) {
        if (s[l] != s[r]) return false;
        l++, r--;
    }
    return true;
}
```
"""),
            Short(r"""
Normalising text before a palindrome check. What does this print?

```cpp
string s = "No 'x' in Nixon", t;
for (char c : s)
    if (isalpha(c)) t += tolower(c);
cout << t << '\n';
```
""", accept=["noxinnixon"], placeholder="what it prints",
                explain=r"""
`noxinnixon`: letters only, lowercased. `t += tolower(c)` appends a character because `+=`
converts the `int` back to `char` (the same conversion that bit you with `s += 65`). It is
a palindrome.
"""),
            MCQ(r"""
To test every suffix of a string of length `n = 10^5`, someone writes:

```cpp
for (int i = 0; i < n; i++)
    if (is_pal(s.substr(i))) ...
```

`is_pal` usually returns `false` after comparing one pair. What does the loop cost?
""", [
                Opt("O(n): each `is_pal` stops after one comparison.",
                    why="`is_pal` is cheap, but its argument is built first: `s.substr(i)` "
                        "copies n − i characters before `is_pal` even starts."),
                Opt("O(n^2): every iteration copies a suffix, about 5·10^9 characters in "
                    "total.", correct=True,
                    why="Right. Pass indices into the original: `is_pal(s, i, n - 1)` with a "
                        "`const string&` parameter. Then an early mismatch really is O(1)."),
                Opt("O(n log n)",
                    why="The copies have lengths n, n − 1, ..., 1: they sum to n^2 / 2."),
            ], explain=r"""
`substr` is a copy, and a copy is O(length) no matter what you do with it afterwards. Inside
a loop, work with indices (or `string_view`, which is a pointer and a length) instead.
"""),
            Reflect(r"""
New question: can a string become a palindrome by deleting *at most one* character? Move
`l` in from the left and `r` in from the right while `s[l] == s[r]`. At the first pair that
differs, which deletions are worth trying, and why is that enough?
""", answer=r"""
The pairs already matched stay matched, so the deletion must fix the pair `(l, r)`: delete
`s[l]` (then `s[l+1..r]` must be a palindrome) or delete `s[r]` (then `s[l..r−1]` must be).
Two index-based checks, O(n) in total. Deleting some earlier `s[i]`, `i < l`, would shift
the pairing, and it only works if `s[i..l]` are all the same character, in which case it
produces the same string as deleting `s[l]`. So those two candidates cover every
possibility.
"""),
            Short(r"""
Take `s = "cbbcc"`. Where do the two indices first disagree? Give `l` and `r` (0-based),
separated by a space.
""", accept=["1 3", "1, 3", "1,3", "l=1 r=3", "l = 1, r = 3"], placeholder="l r",
                explain=r"""
`1 3`: `s[0] = s[4] = 'c'`, then `s[1] = 'b'` against `s[3] = 'c'`. Deleting `s[l]` leaves
`s[2..3] = "bc"`, not a palindrome; deleting `s[r]` leaves `s[1..2] = "bb"`, which is. A
solution that only ever tries deleting the left character answers NO here, wrongly.
"""),
            Try("one_deletion", note="Two indices, two index-based checks. The hidden tests have "
                "a 10^6-character string whose mismatch is in the middle."),
        ]),
        Part("Inserting in the middle", [
            Say(r"""
`v.insert(v.begin() + i, x)` and `s.insert(i, 1, c)` make room by shifting everything after
position `i` one step right: O(n) each. Fine once; fatal inside a loop.

The last problem is a keyboard whose Home and End keys press themselves: Home (`[`) moves
the cursor to the start of the text, End (`]`) to the end, and each letter is inserted at
the cursor. The obvious program keeps the text in a string and calls `insert`.
"""),
            Numeric(r"""
You type 5·10^5 letters, press Home, and type 5·10^5 more. Each of the later letters is
inserted in front of the 5·10^5 typed first, which all shift right. Roughly how many
character moves is that?
""", answer=2.5e11, rel=0.5, unit="moves",
                explain=r"""
5·10^5 · 5·10^5 = 2.5·10^11. Even as fast memory copies that took about 6 seconds here. The
simulation is correct and hopeless; the structure of the output has to be used instead.
"""),
            Reflect(r"""
Letters typed after one Home, up to the next `[` or `]`, form a block. Where does such a
block end up relative to the text typed before it? Relative to a block typed after a later
Home? What does that suggest you store instead of the text itself?
""", answer=r"""
A Home-block goes in front of everything typed so far, and nothing is ever inserted inside
it later: a later Home puts its block in front of this one, and End-mode text goes at the
very end. So the final text is the Home-blocks in reverse order of typing, followed by all
End-mode text in typing order. Store a `vector<string>` of blocks and one `string` for the
End-mode text, appending to whichever is active: every character is appended once, O(n).
"""),
            MCQ(r"""
Why not simply push each letter typed after Home onto the front of a `deque<char>` (O(1)
per push)?
""", [
                Opt("Because `deque::push_front` is O(n), like `vector::insert`.",
                    why="`push_front` on a `deque` really is O(1); speed is not the issue."),
                Opt("Because the letters of one block would come out reversed: typing `ab` after "
                    "Home would give `ba...`.", correct=True,
                    why="Right. Each letter must go after the previous letter of its block, not "
                        "in front of it. Keep whole blocks, then place blocks in front."),
                Opt("Because a `deque` cannot hold `char`s.",
                    why="It can hold any type."),
            ], explain=r"""
Before reaching for a cleverer container, ask what the output looks like. Here it is a few
contiguous blocks in a predictable order, and plain strings with `+=` handle that in O(n).
"""),
            Try("home_end", note="Up to 2·10^6 key presses. `string::insert` in the middle "
                "will not survive the hidden tests."),
        ]),
    ],
    problems=[MINESWEEPER, RLE, ONE_DELETION, HOME_END],
    cards=[
        Card(r"""What is in `v` after `vector<int> v(3); v.push_back(7);`?""",
             r"""`{0, 0, 0, 7}`: the sized constructor already made 3 zeros, and `push_back` appends after them."""),
        Card(r"""`reserve(k)` vs `resize(k)`?""",
             r"""`reserve` only allocates capacity (size unchanged, `v[0]` still invalid); `resize` changes the number of elements."""),
        Card(r"""Cost of `push_back`, of `insert(v.begin(), x)`, of `erase(v.begin())`?""",
             r"""`push_back` O(1) amortised (capacity doubles); inserting or erasing at the front or middle is O(n) (everything after shifts)."""),
        Card(r"""Python `v[-1]` in C++?""",
             r"""`v.back()`. `v[-1]` is undefined behaviour: no wrap-around, no exception."""),
        Card(r"""Does `vector<int> b = a;` alias `a` as in Python?""",
             r"""No, it copies (O(n)). For a second name: `vector<int>& b = a;`."""),
        Card(r"""Idiom to read an `n × m` character grid, and the safe neighbour check?""",
             r"""`vector<string> g(n); for (auto& row : g) cin >> row;` then `if (0 <= nr && nr < n && 0 <= nc && nc < m && g[nr][nc] == ...)`: bounds first."""),
        Card(r"""Why is `s = s + c` in a loop slow in C++ but not in CPython?""",
             r"""It builds a new string (O(|s|)) each time: O(n^2) total. CPython optimises it into an in-place append; C++ does not. Use `s += c`."""),
        Card(r"""`s.substr(a, b)` vs Python `s[a:b]`?""",
             r"""`substr` takes a start and a **length**: Python's `s[a:b]` is `s.substr(a, b - a)`. It is a copy: O(length)."""),
        Card(r"""How do you test whether `s` contains `t`?""",
             r"""`s.find(t) != string::npos`. `find` returns a position; `if (s.find(t))` is wrong both ways."""),
        Card(r"""What does `s += 65;` append, and how do you append a number's digits?""",
             r"""The character with code 65, `'A'`. Use `s += to_string(x);`."""),
        Card(r"""What does `stoi("3000000000")` do?""",
             r"""Throws `out_of_range` (uncaught: RE). Use `stoll` for values past 2.1·10^9."""),
        Card(r"""How do you check whether a piece of a string is a palindrome without copying it?""",
             r"""Pass indices: `bool is_pal(const string& s, int l, int r)` with two pointers moving inward. Never `is_pal(s.substr(...))` inside a loop."""),
    ],
)
