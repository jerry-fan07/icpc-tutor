from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _books(rng, n, x, hmax, smax):
    h = [rng.randint(1, hmax) for _ in range(n)]
    s = [rng.randint(1, smax) for _ in range(n)]
    return f"{n} {x}\n" + " ".join(map(str, h)) + "\n" + " ".join(map(str, s)) + "\n"


def _word(rng, n, alphabet):
    return "".join(rng.choice(alphabet) for _ in range(n))


def _two_words(rng, n, m, alphabet):
    return _word(rng, n, alphabet) + "\n" + _word(rng, m, alphabet) + "\n"


def _similar_words(rng, n, alphabet, edits):
    a = list(_word(rng, n, alphabet))
    b = a[:]
    for _ in range(edits):
        b[rng.randrange(n)] = rng.choice(alphabet)
    return "".join(a) + "\n" + "".join(b) + "\n"


def _array(rng, n, lo, hi):
    return f"{n}\n" + " ".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _increasing_noisy(rng, n):
    # mostly increasing with small dips: long answers, many binary-search replacements
    a = [i * 4900 + rng.randint(1, 20000) for i in range(n)]
    return f"{n}\n" + " ".join(map(str, a)) + "\n"


def _is_subseq(s, t):
    it = iter(t)
    return all(ch in it for ch in s)


def _lcs_check(inp, expected, got):
    """Any common subsequence of the optimal length is accepted."""
    a, b = inp.split()[:2]
    want = int(expected.split()[0])
    toks = got.split()
    if not toks:
        return False, "no output"
    try:
        k = int(toks[0])
    except ValueError:
        return False, f"the first line should be the length, found `{toks[0][:20]}`"
    if k != want:
        return False, f"length {k}, expected {want}"
    if len(toks) > 2:
        return False, "the subsequence should be one word on the second line"
    s = toks[1] if len(toks) == 2 else ""
    if len(s) != k:
        return False, f"the printed subsequence has {len(s)} characters, not {k}"
    if not _is_subseq(s, a):
        return False, f"`{s[:40]}` is not a subsequence of the first string"
    if not _is_subseq(s, b):
        return False, f"`{s[:40]}` is not a subsequence of the second string"
    return True, ""


# --------------------------------------------------------------------- problems
BOOK_SHOP = Problem(
    id="book_shop",
    title="Book Shop",
    difficulty="medium",
    source="CSES 1158 - Book Shop",
    complexity="O(n·x)",
    statement=r"""
A book shop has `n` books, each with a price and a number of pages. You have `x` money.
Each book can be bought at most once. What is the largest total number of pages you can
buy without spending more than `x`?
""",
    input=r"""
The first line has `n` and `x` (1 ≤ n ≤ 1000, 1 ≤ x ≤ 10^5).

The second line has the prices h_1, ..., h_n (1 ≤ h_i ≤ 1000).

The third line has the page counts s_1, ..., s_n (1 ≤ s_i ≤ 1000).
""",
    output=r"""
The maximum total number of pages.
""",
    samples=[
        Test("4 10\n4 8 5 3\n5 12 8 1\n", "13\n"),
        Test("1 10\n5\n7\n", "7\n",
             note="There is one copy of the book. If you print 14, your capacity loop runs the "
                  "wrong way."),
    ],
    tests=[
        Test("1 1\n2\n5\n"),
        Test("3 10\n6 5 5\n7 5 5\n"),
        Test("2 5\n5 5\n1000 999\n"),
        Test("3 6\n2 2 2\n1 1 1\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _books(rng, rng.randint(1, 12), rng.randint(1, 30), 10, 20), 15),
        Gen("small, cheap books", lambda rng: _books(rng, rng.randint(5, 15), rng.randint(20, 60), 6, 1000), 5),
        Gen("max size", lambda rng: _books(rng, 1000, 10**5, 1000, 1000), 1, large=True),
        Gen("max size, cheap books", lambda rng: _books(rng, 1000, 10**5, 20, 1000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, x;
    cin >> n >> x;
    vector<int> h(n), s(n);
    for (auto& v : h) cin >> v;
    for (auto& v : s) cin >> v;
    // after processing books 0..i: dp[c] = max pages from those books with total price <= c
    vector<int> dp(x + 1, 0);
    for (int i = 0; i < n; i++)
        for (int c = x; c >= h[i]; c--)      // downward: dp[c - h[i]] is still the old row,
            dp[c] = max(dp[c], dp[c - h[i]] + s[i]);   // so book i is used at most once
    cout << dp[x] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, x;
    cin >> n >> x;
    vector<int> h(n), s(n);
    for (auto& v : h) cin >> v;
    for (auto& v : s) cin >> v;
    int best = 0;
    for (int mask = 0; mask < (1 << n); mask++) {
        int cost = 0, pages = 0;
        for (int i = 0; i < n; i++)
            if (mask >> i & 1) { cost += h[i]; pages += s[i]; }
        if (cost <= x) best = max(best, pages);
    }
    cout << best << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int n;
vector<int> h, s;
int best(int i, int money) {                 // take or skip book i, no memo: 2^n
    if (i == n) return 0;
    int r = best(i + 1, money);
    if (h[i] <= money) r = max(r, best(i + 1, money - h[i]) + s[i]);
    return r;
}
int main() {
    int x;
    cin >> n >> x;
    h.resize(n); s.resize(n);
    for (auto& v : h) cin >> v;
    for (auto& v : s) cin >> v;
    cout << best(0, x) << '\n';
}
""",
    hints=[
        r"""After deciding books `1..i`, the only thing the rest of the decisions care about is how
much money is spent. So the state is (books considered, money).""",
        r"""`dp[i][c] = max(dp[i-1][c], dp[i-1][c - h_i] + s_i)`. The full table is 10^8 ints
(400 MB): keep one row.""",
        r"""With one row, run `c` from `x` down to `h_i`. Upward, `dp[c - h_i]` may already include
book `i`, and the book gets bought twice.""",
    ],
    editorial=r"""
`dp[i][c]` = the most pages from a subset of the first `i` books with total price at most
`c`. Book `i` is either skipped (`dp[i-1][c]`) or bought (`dp[i-1][c - h_i] + s_i`, if
`h_i ≤ c`); take the larger. `n · x = 10^8` cheap operations.

The full table is 10^8 `int`s, 400 MB, but row `i` reads only row `i − 1`, so one array
suffices, updated for each book with `c` running **downward**. Then, when `dp[c]` is
updated, `dp[c - h_i]` (a smaller index) has not been touched in this pass and still holds
row `i − 1`. Running upward reads a value that may already contain book `i` and buys it
again: one book with price 5 and 7 pages and budget 10 gives 14 instead of 7. Upward is the
correct loop for the *unbounded* knapsack, where every item has unlimited copies.
""",
)

LCS = Problem(
    id="longest_common_subsequence",
    title="Longest Common Subsequence",
    difficulty="medium",
    source="CSES 3403 - Longest Common Subsequence",
    complexity="O(n·m)",
    checker=_lcs_check,
    statement=r"""
Two gene fragments are written as strings of lowercase letters. A *common subsequence* is a
string that can be obtained from both by deleting characters (without reordering the rest).

Find the length of the longest common subsequence, and print one.
""",
    input=r"""
Two lines, the strings `a` and `b` (1 ≤ |a|, |b| ≤ 2000, lowercase letters only).
""",
    output=r"""
The first line: the length `k` of a longest common subsequence.

The second line: one common subsequence of length `k` (if there are several, print any; if
`k = 0`, leave the line empty).
""",
    samples=[
        Test("acbd\nabcd\n", "3\nacd\n", note="`abd` is also accepted."),
        Test("abc\nxyz\n", "0\n\n"),
    ],
    tests=[
        Test("a\na\n"),
        Test("a\nb\n"),
        Test("aaaa\naa\n"),
        Test("abcabc\ncba\n"),
        Test("ab\nba\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _two_words(rng, rng.randint(1, 9), rng.randint(1, 9), "abc"), 15),
        Gen("small, two letters", lambda rng: _two_words(rng, rng.randint(1, 9), rng.randint(1, 9), "ab"), 6),
        Gen("max size, four letters", lambda rng: _two_words(rng, 2000, 2000, "acgt"), 1, large=True),
        Gen("max size, all letters", lambda rng: _two_words(rng, 2000, 1999, "abcdefghijklmnopqrstuvwxyz"), 1, large=True),
        Gen("max size, nearly equal", lambda rng: _similar_words(rng, 2000, "acgt", 30), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string a, b;
    cin >> a >> b;
    int n = a.size(), m = b.size();
    // dp[i][j] = LCS length of the prefixes a[0..i-1] and b[0..j-1]
    vector<vector<int>> dp(n + 1, vector<int>(m + 1, 0));
    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= m; j++)
            dp[i][j] = a[i - 1] == b[j - 1] ? dp[i - 1][j - 1] + 1
                                            : max(dp[i - 1][j], dp[i][j - 1]);
    // walk back from (n, m), repeating the decision that produced each value
    string res;
    int i = n, j = m;
    while (i > 0 && j > 0) {
        if (a[i - 1] == b[j - 1]) { res += a[i - 1]; i--; j--; }
        else if (dp[i - 1][j] >= dp[i][j - 1]) i--;
        else j--;
    }
    reverse(res.begin(), res.end());         // collected from the back
    cout << dp[n][m] << '\n' << res << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
string a, b;
string best(int i, int j) {                  // LCS of a[i..] and b[j..], no memo
    if (i == (int)a.size() || j == (int)b.size()) return "";
    if (a[i] == b[j]) return a[i] + best(i + 1, j + 1);
    string x = best(i + 1, j), y = best(i, j + 1);
    return x.size() >= y.size() ? x : y;
}
int main() {
    cin >> a >> b;
    string r = best(0, 0);
    cout << r.size() << '\n' << r << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
string a, b;
int len(int i, int j) {                      // the recursion without a memo
    if (i == (int)a.size() || j == (int)b.size()) return 0;
    if (a[i] == b[j]) return 1 + len(i + 1, j + 1);
    return max(len(i + 1, j), len(i, j + 1));
}
int main() {
    cin >> a >> b;
    int i = 0, j = 0;
    string r;
    while (i < (int)a.size() && j < (int)b.size()) {
        if (a[i] == b[j]) { r += a[i]; i++; j++; }
        else if (len(i + 1, j) >= len(i, j + 1)) i++;
        else j++;
    }
    cout << r.size() << '\n' << r << '\n';
}
""",
    hints=[
        r"""Let `dp[i][j]` be the LCS length of the first `i` characters of `a` and the first `j` of
`b`. Look at the last characters, `a_i` and `b_j`.""",
        r"""If they are equal, match them: `dp[i-1][j-1] + 1`. If not, one of them is not in the
answer: `max(dp[i-1][j], dp[i][j-1])`.""",
        r"""To print a subsequence, keep the whole table and walk back from `(n, m)`: on equal
characters take the character and go diagonally; otherwise move to the neighbour holding
the same value. You collect the answer backwards.""",
    ],
    editorial=r"""
`dp[i][j]` = the length of an LCS of the prefixes `a[1..i]` and `b[1..j]`, with row and
column 0 equal to 0. If `a_i = b_j`, some LCS matches them to each other (if an optimal
answer used only one of them, re-point that match; if neither, appending the pair would
make it longer), so `dp[i][j] = dp[i-1][j-1] + 1`. Otherwise at least one of `a_i`, `b_j`
is unused, and `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`. That is `n · m = 4·10^6` cells.

To print an answer, walk back from `(n, m)`: equal characters go diagonally and contribute
their character; otherwise step to a neighbour with the same value (either one, when both
qualify, which is why several answers are accepted). The walk needs the whole table, so do
not compress it to two rows here. Reverse the collected characters at the end.
""",
)

EDIT = Problem(
    id="edit_distance",
    title="Edit Distance",
    difficulty="medium",
    source="CSES 1639 - Edit Distance",
    complexity="O(n·m)",
    statement=r"""
The *edit distance* between two strings is the minimum number of operations that turn the
first into the second, where one operation inserts a character, deletes a character, or
replaces a character by another.

For example, `LOVE` becomes `MOVIE` in two operations: replace `L` by `M`, then insert `I`.
Compute the edit distance of two strings.
""",
    input=r"""
Two lines, the strings `a` and `b` (1 ≤ |a|, |b| ≤ 5000, uppercase letters only).
""",
    output=r"""
The edit distance.
""",
    samples=[
        Test("LOVE\nMOVIE\n", "2\n"),
        Test("AB\nBA\n", "2\n", note="Swapping two letters is not one operation."),
    ],
    tests=[
        Test("A\nA\n"),
        Test("A\nB\n"),
        Test("ABC\nABCDEF\n"),
        Test("XYZ\nA\n"),
        Test("SUNDAY\nSATURDAY\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _two_words(rng, rng.randint(1, 8), rng.randint(1, 8), "ABC"), 15),
        Gen("small, two letters", lambda rng: _two_words(rng, rng.randint(1, 8), rng.randint(1, 8), "AB"), 6),
        Gen("max size, random", lambda rng: _two_words(rng, 5000, 5000, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"), 1, large=True),
        Gen("max size, two letters", lambda rng: _two_words(rng, 5000, 4990, "AB"), 1, large=True),
        Gen("very different lengths", lambda rng: _two_words(rng, 5000, 3, "AB"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string a, b;
    cin >> a >> b;
    int n = a.size(), m = b.size();
    // dp[i][j] = edit distance between a[0..i-1] and b[0..j-1]; only rows i-1 and i are kept
    vector<int> prev(m + 1), cur(m + 1);
    for (int j = 0; j <= m; j++) prev[j] = j;          // "" -> b[0..j-1]: j insertions
    for (int i = 1; i <= n; i++) {
        cur[0] = i;                                     // a[0..i-1] -> "": i deletions
        for (int j = 1; j <= m; j++)
            cur[j] = min({prev[j] + 1,                  // delete a[i-1]
                          cur[j - 1] + 1,               // insert b[j-1]
                          prev[j - 1] + (a[i - 1] != b[j - 1])});   // replace, or keep
        swap(prev, cur);
    }
    cout << prev[m] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
string a, b;
int ed(int i, int j) {                       // a[0..i-1] -> b[0..j-1], no memo
    if (i == 0) return j;
    if (j == 0) return i;
    return min({ed(i - 1, j) + 1, ed(i, j - 1) + 1, ed(i - 1, j - 1) + (a[i - 1] != b[j - 1])});
}
int main() {
    cin >> a >> b;
    cout << ed(a.size(), b.size()) << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
string a, b;
int ed(int i, int j) {
    if (i == 0) return j;
    if (j == 0) return i;
    return min({ed(i - 1, j) + 1, ed(i, j - 1) + 1, ed(i - 1, j - 1) + (a[i - 1] != b[j - 1])});
}
int main() {
    cin >> a >> b;
    cout << ed(a.size(), b.size()) << '\n';
}
""",
    hints=[
        r"""Same state as LCS: `dp[i][j]` for the prefixes of length `i` and `j`. What can the last
operation touching `a_i` or `b_j` be?""",
        r"""Delete `a_i` (`dp[i-1][j] + 1`), insert `b_j` (`dp[i][j-1] + 1`), or turn `a_i` into
`b_j` (`dp[i-1][j-1]`, plus 1 if they differ). Base cases `dp[i][0] = i`, `dp[0][j] = j`.""",
    ],
    editorial=r"""
`dp[i][j]` = the edit distance between the prefixes `a[1..i]` and `b[1..j]`. In an optimal
edit, look at what happens to the last characters: either `a_i` is deleted
(`dp[i-1][j] + 1`), or `b_j` was inserted (`dp[i][j-1] + 1`), or `a_i` ends up as `b_j`
(`dp[i-1][j-1]`, plus one replacement if they differ). Take the minimum.

The base cases are not zero: turning `i` characters into the empty string takes `i`
deletions, and the empty string into `j` characters takes `j` insertions. With them
wrongly set to 0, `A` against `ABC` comes out as 0.

`n · m = 2.5·10^7` cells. The full `int` table is 100 MB; since row `i` reads only rows `i`
and `i − 1`, two rows of `m + 1` values are enough when only the distance is needed.
""",
)

LIS = Problem(
    id="increasing_subsequence",
    title="Increasing Subsequence",
    difficulty="medium",
    source="CSES 1145 - Increasing Subsequence",
    complexity="O(n log n)",
    statement=r"""
Given an array of `n` integers, find the length of its longest *strictly* increasing
subsequence: the most elements you can pick, keeping their order, so that every picked
element is larger than the one picked before it.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

The second line has `n` integers x_1, ..., x_n (1 ≤ x_i ≤ 10^9).
""",
    output=r"""
The length of the longest strictly increasing subsequence.
""",
    samples=[
        Test("8\n7 3 5 3 6 2 9 8\n", "4\n"),
        Test("3\n2 2 2\n", "1\n", note="Strictly increasing: equal values do not extend a "
             "subsequence."),
    ],
    tests=[
        Test("1\n5\n"),
        Test("5\n5 4 3 2 1\n"),
        Test("6\n1 2 2 3 3 4\n"),
        Test("5\n1000000000 1 1000000000 2 3\n"),
    ],
    gens=[
        Gen("small random, many repeats", lambda rng: _array(rng, rng.randint(1, 12), 1, 6), 15),
        Gen("small random", lambda rng: _array(rng, rng.randint(1, 15), 1, 10**9), 5),
        Gen("medium random", lambda rng: _array(rng, 3000, 1, 10**9), 2),
        Gen("max size, random", lambda rng: _array(rng, 200000, 1, 10**9), 1, large=True),
        Gen("max size, nearly increasing", lambda rng: _increasing_noisy(rng, 200000), 1, large=True),
        Gen("max size, few distinct values", lambda rng: _array(rng, 200000, 1, 100), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    // tail[k] = smallest possible last value of a strictly increasing subsequence
    //           of length k + 1 among the elements read so far (tail is strictly increasing)
    vector<int> tail;
    for (int i = 0; i < n; i++) {
        int v;
        cin >> v;
        // first tail >= v: v can end a subsequence of that length with a smaller last value
        auto it = lower_bound(tail.begin(), tail.end(), v);
        if (it == tail.end()) tail.push_back(v);         // v extends the longest one
        else *it = v;
    }
    cout << tail.size() << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<int> a(n), dp(n, 1);
    for (auto& v : a) cin >> v;
    int best = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < i; j++)
            if (a[j] < a[i]) dp[i] = max(dp[i], dp[j] + 1);
        best = max(best, dp[i]);
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
    vector<int> a(n), dp(n, 1);
    for (auto& v : a) cin >> v;
    int best = 0;
    for (int i = 0; i < n; i++) {
        int d = 1;
        for (int j = 0; j < i; j++)
            if (a[j] < a[i] && dp[j] + 1 > d) d = dp[j] + 1;
        dp[i] = d;
        best = max(best, d);
    }
    cout << best << '\n';
}
""",
    hints=[
        r"""The O(n^2) DP (`dp[i]` = longest increasing subsequence ending at `i`) is 2·10^10
operations here. Among all increasing subsequences of the same length, which one is the
most useful for the future?""",
        r"""Keep `tail[k]`, the smallest possible last value of an increasing subsequence of length
`k + 1`. It is strictly increasing, so a new value changes exactly one entry, found by
binary search.""",
        r"""Strictly increasing means `lower_bound` (first tail `≥ v`). `upper_bound` would let equal
values extend each other and prints 3 for `2 2 2`.""",
    ],
    editorial=r"""
Of two increasing subsequences with the same length, the one with the smaller last value is
at least as good for the future: anything that extends the other also extends it. So keep
only `tail[k]`, the smallest last value over all increasing subsequences of length `k + 1`
seen so far.

`tail` is strictly increasing: if `tail[k] ≥ tail[k+1]`, the subsequence of length `k + 2`
ending in `tail[k+1]` has a `(k+1)`-th element smaller than `tail[k+1] ≤ tail[k]`, which is
a subsequence of length `k + 1` with a smaller last value than `tail[k]`, a contradiction.
When `v` arrives it can extend exactly the lengths whose tails are `< v`; the longest of
those gives the first position `k` with `tail[k] ≥ v`, and `v` becomes the new, smaller
`tail[k]` (or is appended if every tail is smaller). That position is a `lower_bound`:
O(log n) per element, O(n log n) in all.

Two traps. `tail` is not itself an increasing subsequence of the input, only its length is
meaningful. And strictness decides the binary search: `lower_bound` for strictly
increasing, `upper_bound` for non-decreasing. This is also called *patience sorting*: deal
the values onto piles, each on the leftmost pile whose top is `≥` it; the number of piles is
the answer.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo07",
    title="dynamic programming II: knapsack & sequences",
    track="algo",
    order=7,
    summary="The classic DPs on items and on pairs of strings: 0/1 knapsack and why its "
            "capacity loop runs backwards, LCS with reconstruction, edit distance, and the "
            "longest increasing subsequence from O(n^2) down to O(n log n).",
    prereqs=["algo06", "algo03"],
    tags=["dynamic programming", "knapsack", "lcs", "edit distance", "lis",
          "binary search", "reconstruction"],
    parts=[
        Part("Take it or leave it: the 0/1 knapsack", [
            Say(r"""
A book shop has `n ≤ 1000` books. Book `i` costs `h_i ≤ 1000` and has `s_i ≤ 1000` pages.
You have `x ≤ 10^5` money, and there is one copy of each book. Maximise the total number of
pages (CSES *Book Shop*).

Complete search (algo05) tries every subset: 2^n of them, fine for `n = 20`, absurd for
`n = 1000`. And the tempting shortcut is a greedy.
"""),
            MCQ(r"""
Budget 10. Books: (price 6, 7 pages), (price 5, 5 pages), (price 5, 5 pages). Greedy by
pages per unit of price buys the best ratio first. What happens?
""", [
                Opt("It buys the 7-page book (ratio 1.17), then nothing else fits: 7 pages, "
                    "while the two 5-price books give 10.", correct=True,
                    why="Right. The best ratio wastes 4 units of budget that nothing can use. "
                        "Greedy by ratio is correct only when books can be cut into pieces "
                        "(the *fractional* knapsack)."),
                Opt("It buys the two 5-price books: 10 pages, optimal.",
                    why="Their ratio is 1.0, lower than 7/6 ≈ 1.17, so greedy takes the 6-price "
                        "book first and then cannot afford either of the others."),
                Opt("Greedy by ratio is always optimal for the knapsack.",
                    why="It fails right here: 7 pages instead of 10. Whole items make leftover "
                        "budget unusable, and ratio cannot see that."),
            ]),
            Reflect(r"""
Decide the books one at a time, in input order. After you have decided about books
`1..i`, what do you need to know about those decisions to finish optimally? Use it to
define a state, in words.
""", answer=r"""
Only how much money has been spent (equivalently, how much is left). *Which* books were
bought does not matter for the rest, as long as the money matches. So: `dp[i][c]` = the most
pages obtainable from a subset of the first `i` books whose total price is at most `c`.
That is `(n + 1)(x + 1)` states instead of 2^n subsets, because every subset with the same
total price collapses into one state.
"""),
            MCQ(r"""
Which transition is right for `dp[i][c]`?
""", [
                Opt("`max(dp[i-1][c], dp[i][c - h_i] + s_i)`",
                    why="`dp[i][c - h_i]` is a row that may already contain book `i`, so this "
                        "can buy it twice. It is the unbounded knapsack (unlimited copies)."),
                Opt("`max over all books j of dp[c - h_j] + s_j`",
                    why="That is the Minimizing Coins shape: any item may be the last one, again "
                        "and again. Nothing stops a book from being bought several times."),
                Opt("`max(dp[i-1][c], dp[i-1][c - h_i] + s_i)`, the second only if `h_i ≤ c`",
                    correct=True,
                    why="Yes: skip book `i`, or buy it and pay `h_i` out of the budget left for the "
                        "first `i − 1` books."),
            ]),
            Short(r"""
Budget 5. Books: A (price 2, 3 pages), B (price 3, 4 pages), C (price 4, 5 pages). Row 0 of
the table (`c = 0..5`) is all zeros, and the row after A is `0 0 3 3 3 3`. Write the row
after B.
""", accept=["0 0 3 4 4 7", "0,0,3,4,4,7"], placeholder="six numbers",
                hint="`dp[B][c] = max(dp[A][c], dp[A][c - 3] + 4)` for `c ≥ 3`.",
                explain=r"""
`0 0 3 4 4 7`: at `c = 5`, buying B leaves 2 for A, `3 + 4 = 7`. The row after C is
`0 0 3 4 5 7`; C alone (5 pages) never beats A + B. The answer is the last entry, 7.
"""),
            Numeric(r"""
With `n = 1000` and `x = 10^5`, how many bytes does the full table take as 4-byte `int`s?
""", answer=4e8, rel=0.5, unit="bytes",
                explain=r"""
About 4·10^8 bytes, 400 MB: over a typical 256 MB limit. The time, 10^8 simple steps, is
fine. But row `i` reads only row `i − 1`, so one array of `x + 1` values can be overwritten
book by book, as in Coin Combinations II.
"""),
            Say(r"""
Here is the one-array version:

```cpp
vector<int> dp(x + 1, 0);           // dp[c]: best pages with budget c, books so far
for (int i = 0; i < n; i++)
    for (int c = x; c >= h[i]; c--)
        dp[c] = max(dp[c], dp[c - h[i]] + s[i]);
```

The capacity loop runs *down*, from `x` to `h[i]`. It is a one-character-looking choice
that decides whether the program is right.
"""),
            Short(r"""
Run the capacity loop upward instead, `for (int c = h[i]; c <= x; c++)`. One book, price 5,
7 pages, budget 10. What does the program print?
""", accept=["14"], placeholder="a number",
                hint="Upward, `dp[5]` becomes 7 first. What does `dp[10]` read afterwards?",
                explain=r"""
14. `dp[5] = dp[0] + 7 = 7`, and then `dp[10] = dp[5] + 7 = 14`: the book was bought twice,
because `dp[5]` already included it when `dp[10]` read it. The correct answer is 7.
"""),
            MCQ(r"""
Why does the downward loop use each book at most once?
""", [
                Opt("Downward loops are faster, and speed prevents double counting.",
                    why="Both directions do the same number of steps. The difference is which "
                        "values are read, not how fast."),
                Opt("When `dp[c]` is updated, `dp[c - h]` is at a smaller index, not yet "
                    "touched in this pass: it still holds the row before book `i`.", correct=True,
                    why="Right. Downward, every read sees row `i − 1`, which is exactly the "
                        "`dp[i-1][c - h_i]` of the 2D transition."),
                Opt("Because `max` ignores a book that is counted twice.",
                    why="`max` happily takes 14 over 7. Nothing in `max` knows which books a value "
                        "came from."),
            ], explain=r"""
Upward is not a bug everywhere: it is the correct loop for the **unbounded** knapsack
(unlimited copies of each item), exactly the Coin Combinations II loop. Downward is the
**0/1** knapsack. Same line of code, different problem.
"""),
            Try("book_shop", note="One array, capacity loop downward. The second sample catches the "
                "upward loop."),
        ]),
        Part("Two strings: longest common subsequence", [
            Say(r"""
New shape: the input is two sequences. A *common subsequence* of `a` and `b` is a string
you can get from both by deleting characters. Find the longest one, and print it
(`|a|, |b| ≤ 2000`). For `a = acbd` and `b = abcd`, both `abd` and `acd` have length 3.

Brute force lists all 2^n subsequences of `a` (with n = |a|) and checks each against `b`:
2^2000 of them. A DP needs a family of smaller subproblems that the whole problem can be
built from.
"""),
            MCQ(r"""
Which family of subproblems works?
""", [
                Opt("`dp[i][j]` = the LCS length of the prefixes `a[1..i]` and `b[1..j]`.",
                    correct=True,
                    why="Yes. Removing the last character of either string gives another pair of "
                        "prefixes, so every case stays inside the family: `(n + 1)(m + 1)` states."),
                Opt("`dp[i]` = the LCS of `a[1..i]` and all of `b`.",
                    why="Once some `a_k` is matched to `b_j`, everything after it in `a` must match "
                        "after `j` in `b`. The state has to say how much of `b` is still in play: "
                        "a second index."),
                Opt("`dp[c]` = whether the letter `c` occurs in both strings.",
                    why="That finds common letters and forgets their order, which is the whole "
                        "difficulty: `ab` and `ba` share both letters, but their LCS is 1."),
            ], explain=r"""
"The same problem on prefixes" is the standard state for one or two sequences. The
transition then only has to look at the last characters, `a_i` and `b_j`.
"""),
            MCQ(r"""
Which transition is right?
""", [
                Opt("If `a_i = b_j`: `dp[i-1][j-1] + 1`. Otherwise: `dp[i-1][j-1]`.",
                    why="Dropping *both* characters loses answers. `a = ab`, `b = ba`: the last "
                        "characters differ, `dp[1][1]` (`a` vs `b`) is 0, but the LCS is 1: "
                        "`a_2 = b` can still match `b_1`."),
                Opt("Always `dp[i-1][j] + dp[i][j-1]`.",
                    why="Adding is what a *counting* DP does. This problem asks for a length, and "
                        "the sum counts shared parts twice."),
                Opt("If `a_i = b_j`: `dp[i-1][j-1] + 1`. Otherwise: `max(dp[i-1][j], dp[i][j-1])`.",
                    correct=True,
                    why="Yes. If the last characters differ, at least one of them is not in the "
                        "answer, so drop one or the other and keep the better result."),
            ]),
            MCQ(r"""
When `a_i = b_j`, the transition matches them without also trying `dp[i-1][j]` and
`dp[i][j-1]`. Why is that safe?
""", [
                Opt("It is not always safe; you must take the max of all three.",
                    why="Taking the max of all three is also correct, just unnecessary: the "
                        "argument in the right answer shows the match never loses."),
                Opt("Some optimal answer always ends with this pair: if it used only one of the "
                    "two, re-point that match; if neither, append the pair.", correct=True,
                    why="Right: an exchange argument. Any optimal common subsequence can be "
                        "rearranged, without getting shorter, into one that matches `a_i` with "
                        "`b_j`."),
                Opt("Because equal characters are rare, so it rarely matters.",
                    why="Correctness cannot depend on the data being friendly. With a two-letter "
                        "alphabet, equal characters are everywhere."),
            ]),
            Short(r"""
`a = acbd` (rows), `b = abcd` (columns). With column 0 included, the row for `a[1..1] = a`
is `0 1 1 1 1` and the row for `ac` is `0 1 1 2 2`. Write the row for `acb`.
""", accept=["0 1 2 2 2", "0,1,2,2,2"], placeholder="five numbers",
                hint="The `b` of `acb` matches the `b` of `abcd` at column 2: `dp[2][1] + 1` there.",
                explain=r"""
`0 1 2 2 2`. At column 2 the characters match, `dp[2][1] + 1 = 2` (`ab`). Elsewhere the
row takes the larger of the cell above and the cell to the left. The last row, for `acbd`,
is `0 1 2 2 3`: the LCS has length 3.
"""),
            MCQ(r"""
To print an LCS, walk back from `(4, 4)`: equal characters go diagonally and are
collected. At `(3, 3)`, `a_3 = b` and `b_3 = c` differ, and *both* neighbours
`dp[2][3]` and `dp[3][2]` equal `dp[3][3] = 2`. Which way do you go?
""", [
                Opt("Either: each neighbour with the same value holds an optimal answer, so both "
                    "lead to a valid LCS (`acd` one way, `abd` the other).", correct=True,
                    why="Right. That is why the problem accepts any longest common subsequence: "
                        "different tie-breaks print different, equally correct answers."),
                Opt("Up, to `(2, 3)`: going up is the only correct convention.",
                    why="Up works (it produces `acd`), but it is not the only choice."),
                Opt("Diagonally, to `(2, 2)`, since that is how matches are found.",
                    why="The characters at `(3, 3)` differ, so no match happened here; the "
                        "diagonal could skip a character that belongs to the answer."),
            ], explain=r"""
Reconstruction replays the decisions: at each cell, find a case of the transition that
produces the stored value and follow it. You collect the characters from the back, so
reverse at the end.
"""),
            MCQ(r"""
In the knapsack you kept one row. Can you keep only two rows here and still *print* the
LCS?
""", [
                Opt("Yes: the last row contains the answer.",
                    why="It contains the *length*. The walk back visits cells in every row, and "
                        "those rows were overwritten."),
                Opt("Yes, if you store the characters in the rows as well.",
                    why="Storing a whole string per cell costs far more memory than the table. "
                        "The table of lengths is the compact form."),
                Opt("No: the walk back needs the whole table. With `|a|, |b| ≤ 2000` it is "
                    "4·10^6 `int`s, 16 MB, which is fine.", correct=True,
                    why="Right. Rows can be dropped only when you need nothing but the final "
                        "value. (Hirschberg's algorithm reconstructs in linear memory, but it is "
                        "rarely worth it in a contest.)"),
            ]),
            Try("longest_common_subsequence", note="Any longest common subsequence is accepted."),
        ]),
        Part("Edit distance", [
            Say(r"""
The same table answers a different question (CSES *Edit Distance*): the fewest operations
turning `a` into `b`, where an operation inserts a character, deletes one, or replaces one.
`|a|, |b| ≤ 5000`.
"""),
            Short(r"""
What is the edit distance between `AB` and `BA`?
""", accept=["2"], placeholder="a number",
                hint="Swapping two letters is not one of the operations.",
                explain=r"""
2: replace both letters, or delete `A` and append it after `B`. One is impossible: any single
insert or delete changes the length, and a single replacement leaves one of the two
positions unchanged, and here both differ.
"""),
            Reflect(r"""
Let `dp[i][j]` be the edit distance between `a[1..i]` and `b[1..j]`. In an optimal edit,
what can happen to the last characters `a_i` and `b_j`? Turn each case into a term of the
transition.
""", answer=r"""
Three cases. `a_i` is deleted: `dp[i-1][j] + 1`. `b_j` is inserted at the end:
`dp[i][j-1] + 1`. Or `a_i` becomes `b_j`, replaced if they differ, kept if equal:
`dp[i-1][j-1] + (a_i ≠ b_j)`. The answer is the minimum of the three. It is LCS's table with
a different question in each cell: the neighbours are the same, the costs are different.
"""),
            MCQ(r"""
What are the base cases `dp[i][0]` and `dp[0][j]`?
""", [
                Opt("`dp[i][0] = i` and `dp[0][j] = j`.", correct=True,
                    why="Yes: `i` deletions to empty `a[1..i]`, `j` insertions to build `b[1..j]` "
                        "from nothing."),
                Opt("All 0, like the LCS table.",
                    why="For LCS a string against the empty string has 0 in common. Here, turning "
                        "`abc` into the empty string costs 3 deletions. With zeros, `A` against "
                        "`ABC` comes out as 0."),
                Opt("`dp[0][0] = 0` and the rest `INF`, as in Minimizing Coins.",
                    why="Nothing here is impossible: every string can be turned into every other. "
                        "`INF` would make the whole first row and column wrong."),
            ]),
            Short(r"""
`a = AB` (rows), `b = BA` (columns). Row 0 is `0 1 2` and row 1 (for `A`) is `1 1 1`.
Write row 2.
""", accept=["2 1 2", "2,1,2"], placeholder="three numbers",
                hint="Row 2 starts with `dp[2][0] = 2`. At column 1 the characters are equal.",
                explain=r"""
`2 1 2`. `dp[2][1]`: `B = B`, so `dp[1][0] + 0 = 1` (delete `A`). `dp[2][2]`: `B ≠ A`, and all
three neighbours give 2. The bottom-right cell is the answer from the first question.
"""),
            Numeric(r"""
With `|a| = |b| = 5000`, how many cells does the table have?
""", answer=2.5e7, rel=0.5, unit="cells",
                explain=r"""
2.5·10^7: a few hundredths of a second. As `int`s that is 100 MB, which some judges allow and
some do not. Only the distance is needed and each row reads only the row above, so two rows
of 5001 values are enough.
"""),
            Try("edit_distance"),
        ]),
        Part("Longest increasing subsequence, the quadratic way", [
            Say(r"""
One array, `n ≤ 2·10^5` values up to 10^9. Pick as many elements as possible, keeping their
order, so that each is strictly larger than the previous (CSES *Increasing Subsequence*).
For `3 1 4 1 5 9 2 6`, one answer is `1 4 5 9`, of length 4.

Subsets are out (2^n). A state is needed, and the obvious first try is
"`dp[i]` = the length of the LIS of the prefix `a[1..i]`".
"""),
            MCQ(r"""
Why does "the LIS of the prefix `a[1..i]`" not give a usable transition?
""", [
                Opt("It is too slow to compute.",
                    why="Speed is not the issue; the problem is what the value *does not say*."),
                Opt("Prefix states only work for strings, not numbers.",
                    why="LCS and edit distance work on prefixes because their transition only "
                        "needs the last characters. Here it needs the last *chosen* value."),
                Opt("To extend a subsequence with `a_(i+1)`, you need its last value, and the "
                    "prefix LIS could end anywhere.", correct=True,
                    why="Right. Change the state to fix the end: `dp[i]` = the length of the "
                        "longest increasing subsequence that *ends exactly at* index `i`."),
            ], explain=r"""
With the end fixed: `dp[i] = 1 + max{dp[j] : j < i, a_j < a_i}` (or 1 if no such `j`), and
the answer is the maximum over all `i`. Fixing the last element is the same move as adding
the last throw to the dice state in algo06.
"""),
            Short(r"""
For `a = 3 1 4 1 5 9 2 6`, write `dp[1..8]` (the LIS ending at each position).
""", accept=["1 1 2 1 3 4 2 4", "1,1,2,1,3,4,2,4"], placeholder="eight numbers",
                hint="`dp` for `5` looks at every earlier value smaller than 5: `3 1 4 1`.",
                explain=r"""
`1 1 2 1 3 4 2 4`. For example `dp[8]` (value 6) extends the best of `3, 1, 4, 1, 5, 2`,
which is `dp[5] = 3` (ending in 5): `1 4 5 6`. The answer is the maximum, 4.
"""),
            Numeric(r"""
This DP looks at every pair of positions `j < i`. For `n = 2·10^5`, about how many such
pairs are there?
""", answer=2e10, rel=0.5, unit="pairs",
                explain=r"""
`n(n − 1)/2 ≈ 2·10^10`: tens of seconds. It is a fine brute force for checking, and the
O(n log n) method below starts from asking what it wastes.
"""),
        ]),
        Part("LIS in O(n log n): the smallest tails", [
            MCQ(r"""
Midway through the array, you have two increasing subsequences of length 3: one ends in 7,
the other ends in 4. Which one is more useful for the rest of the array?
""", [
                Opt("The one ending in 7: bigger values make longer subsequences.",
                    why="The *next* element must beat the last one. A next value of 5 extends the "
                        "4-ending subsequence and not the 7-ending one."),
                Opt("The one ending in 4: anything that extends the other also extends it.",
                    correct=True,
                    why="Right. The 7-ending one is dominated: throw it away and no future answer "
                        "gets worse."),
                Opt("Both are needed, because they contain different elements.",
                    why="Which elements they contain no longer matters, only the length and the "
                        "last value: the future can only append to them."),
            ], explain=r"""
So for each length, only one number matters: the smallest last value over all increasing
subsequences of that length. Call it `tail[k]` (for length `k + 1`). The O(n^2) DP wasted
its time comparing against dominated subsequences.
"""),
            MCQ(r"""
Claim: `tail` is always strictly increasing, `tail[0] < tail[1] < ...`. Why?
""", [
                Opt("Because the input is processed left to right.",
                    why="The input order is arbitrary; the claim needs an argument about "
                        "subsequences, not about the scan."),
                Opt("It is not always increasing; it has to be sorted before each binary search.",
                    why="Sorting would destroy which entry belongs to which length. It never needs "
                        "sorting: the contradiction argument shows the order is automatic."),
                Opt("If `tail[k] ≥ tail[k+1]`, drop the last element of the length-`k + 2` "
                    "subsequence ending in `tail[k+1]`: what is left ends below `tail[k]`.",
                    correct=True,
                    why="Right: that length-`k + 1` subsequence ends below `tail[k]`, contradicting "
                        "that `tail[k]` was the smallest. So the order holds after every step."),
            ]),
            MCQ(r"""
A new value `v` arrives. Which entries of `tail` can change?
""", [
                Opt("Every entry larger than `v` becomes `v`.",
                    why="Tails `1 4 5 9` with `v = 2` would become `1 2 2 2`, claiming an increasing "
                        "subsequence of length 4 that ends in 2. `v` can only extend subsequences "
                        "whose tails are below it."),
                Opt("Exactly one: the first entry `≥ v` becomes `v`, or `v` is appended if every "
                    "entry is smaller.", correct=True,
                    why="Right. `v` extends the longest subsequence with tail `< v`; the length it "
                        "creates is the first position whose tail is `≥ v`, and `v` is a smaller "
                        "tail for it."),
                Opt("Only the last entry, if `v` is bigger than it.",
                    why="That is the append case. A small `v` improves an entry in the middle: `2` "
                        "turns tails `1 4 5 9` into `1 2 5 9`."),
            ], explain=r"""
Because `tail` is sorted, "the first entry `≥ v`" is a binary search (algo03):
`lower_bound`. O(log n) per element, O(n log n) in total.
"""),
            Short(r"""
Run it on `3 1 4 1 5 9 2 6`, starting from an empty `tail`. What is `tail` at the end?
""", accept=["1 2 5 6", "1,2,5,6"], placeholder="the final tails",
                hint="After `3 1 4 1 5 9` the tails are `1 4 5 9`.",
                explain=r"""
`3` → `3`; `1` → `1`; `4` → `1 4`; `1` → `1 4` (replaces 1 by 1); `5` → `1 4 5`;
`9` → `1 4 5 9`; `2` → `1 2 5 9`; `6` → `1 2 5 6`. Four entries: the LIS has length 4.
"""),
            MCQ(r"""
Is `1 2 5 6` itself an increasing subsequence of `3 1 4 1 5 9 2 6`?
""", [
                Opt("No: each entry belongs to a different candidate subsequence; only the "
                    "length of `tail` is meaningful.", correct=True,
                    why="Right. `tail[1] = 2` is the end of `1 2`, and `tail[2] = 5` is the end of "
                        "`1 4 5`. To print an actual LIS, store for each element the index of its "
                        "predecessor when it is placed, and walk back."),
                Opt("Yes: the tails array is always an optimal subsequence.",
                    why="Look at the positions: the `2` is the seventh element and the `5` the "
                        "fifth. `2` comes after `5` in the array."),
                Opt("Yes, when the array has no repeated values.",
                    why="`3 1 4 1 5 9 2 6` without the second `1` still gives `1 2 5 6` at the end, "
                        "and it is still not a subsequence."),
            ]),
            Short(r"""
Someone uses `upper_bound` (first entry `> v`) instead of `lower_bound`. What does their
program print for the array `2 2 2`?
""", accept=["3"], placeholder="a number",
                explain=r"""
3: with `upper_bound`, each `2` finds no entry `> 2` and is appended, so equal values extend
each other. That is the right answer for the longest *non-decreasing* subsequence, and the
wrong one here, where the answer is 1. Strictly increasing: `lower_bound`. Non-decreasing:
`upper_bound`.
"""),
            Say(r"""
The whole solution:

```cpp
vector<int> tail;
for (int i = 0; i < n; i++) {
    int v;
    cin >> v;
    auto it = lower_bound(tail.begin(), tail.end(), v);   // first tail >= v
    if (it == tail.end()) tail.push_back(v);              // v extends the longest
    else *it = v;                                         // v is a smaller tail
}
cout << tail.size() << '\n';
```

It is also called *patience sorting*: deal the values like cards onto piles, each on the
leftmost pile whose top is `≥` it; the number of piles is the answer.
"""),
            Try("increasing_subsequence", note="The hidden tests include `n = 2·10^5`; the O(n^2) DP "
                "does not pass."),
        ]),
        Part("When the standard forms bend", [
            MCQ(r"""
A knapsack variant: `n ≤ 100` items, weights up to 10^9, capacity up to 10^9, but values
at most 1000 each. `dp` over capacity would need 10^9 entries. What now?
""", [
                Opt("Swap the roles: `dp[v]` = the minimum weight achieving total value exactly "
                    "`v`, for `v` up to 10^5; the answer is the largest `v` with "
                    "`dp[v] ≤ capacity`.", correct=True,
                    why="Right. The DP runs over whichever quantity is small. Total value is at most "
                        "100 · 1000 = 10^5, so the table has 10^5 entries."),
                Opt("Use a `map` instead of an array, so only reachable capacities are stored.",
                    why="A map helps only when few distinct states are reachable. With 100 "
                        "arbitrary weights, up to 2^100 subset weights can all be different."),
                Opt("Divide all weights by their gcd.",
                    why="That helps only when the gcd is large. With random weights it is 1, and "
                        "nothing shrinks."),
            ], explain=r"""
Knapsack DPs are pseudo-polynomial (algo06): their size is a *value* in the input. When one
value is huge, look for another quantity that is small and make it the index.
"""),
            MCQ(r"""
The LCS of two *permutations* of `1..n`, with `n = 10^5`. The table has 10^10 cells. What
makes it fast?
""", [
                Opt("Nothing: LCS is O(n·m) and 10^10 is simply too slow.",
                    why="For general strings, yes. Permutations have extra structure: every value "
                        "appears exactly once in each."),
                Opt("Use the edit-distance table instead, which is smaller.",
                    why="Edit distance has the same `n · m` table: no smaller."),
                Opt("Rename each value by its position in `b`; a common subsequence becomes an "
                    "increasing subsequence of the renamed `a`: LIS in O(n log n).", correct=True,
                    why="Right. A common subsequence keeps its order in both arrays; in `b`'s "
                        "positions that means increasing. Reductions like this turn a table DP "
                        "into a greedy-plus-binary-search one."),
            ]),
            Reflect(r"""
Look back at the four DPs of this lesson. For each, what is the state, and why was that
state enough, that is, what did it deliberately forget?
""", answer=r"""
Knapsack: (books considered, money spent); it forgets *which* books, since only the money
constrains the future. LCS and edit distance: (prefix of `a`, prefix of `b`); they forget
how the prefixes were matched, since the rest only involves the remaining suffixes. LIS
O(n^2): (last chosen index); it forgets the earlier elements, since only the last value
limits the next one. LIS O(n log n): for each length, only the smallest tail; it forgets
every dominated subsequence. A good state is exactly what the future depends on, and
nothing else.
"""),
        ]),
    ],
    problems=[BOOK_SHOP, LCS, EDIT, LIS],
    cards=[
        Card(r"""0/1 knapsack: state and transition?""",
             r"""`dp[i][c]` = best value from the first `i` items with total weight ≤ `c`; `dp[i][c] = max(dp[i-1][c], dp[i-1][c - w_i] + v_i)`."""),
        Card(r"""1D 0/1 knapsack: which way does the capacity loop run, and why?""",
             r"""Downward (`c = x` to `w_i`), so `dp[c - w_i]` still holds the previous row and each item is used at most once. Upward is the unbounded knapsack."""),
        Card(r"""One item (weight 5, value 7), capacity 10, capacity loop running upward: what is the result?""",
             r"""14: `dp[5] = 7`, then `dp[10] = dp[5] + 7`. The item was taken twice."""),
        Card(r"""Why does greedy by value/weight ratio fail for the 0/1 knapsack?""",
             r"""Items cannot be split, so the best ratio can waste budget: capacity 10, items (6, 7), (5, 5), (5, 5): greedy 7, optimum 10. It is correct only for the fractional knapsack."""),
        Card(r"""LCS transition?""",
             r"""If `a_i = b_j`: `dp[i-1][j-1] + 1`. Else `max(dp[i-1][j], dp[i][j-1])`. Row and column 0 are 0."""),
        Card(r"""How do you print an LCS from the table?""",
             r"""Walk back from `(n, m)`: equal characters go diagonally and are collected; otherwise step to a neighbour with the same value. Reverse at the end. Needs the whole table."""),
        Card(r"""Edit distance transition and base cases?""",
             r"""`dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + (a_i ≠ b_j))`; `dp[i][0] = i`, `dp[0][j] = j`."""),
        Card(r"""LIS in O(n^2): state?""",
             r"""`dp[i]` = length of the longest increasing subsequence ending exactly at `i`; `dp[i] = 1 + max dp[j]` over `j < i` with `a_j < a_i`."""),
        Card(r"""LIS in O(n log n): what does `tail[k]` hold, and why is it sorted?""",
             r"""The smallest last value of an increasing subsequence of length `k + 1`. If `tail[k] ≥ tail[k+1]`, the longer subsequence would contain a length-`k + 1` one ending lower: contradiction."""),
        Card(r"""LIS with `tail`: `lower_bound` or `upper_bound`?""",
             r"""Strictly increasing: `lower_bound` (replace the first tail `≥ v`). Non-decreasing: `upper_bound`."""),
        Card(r"""Is the final `tail` array an actual LIS?""",
             r"""No, only its length is. For `3 1 4 1 5 9 2 6` it ends as `1 2 5 6`, where the 2 comes after the 5. Store predecessors to reconstruct."""),
        Card(r"""Knapsack with huge weights but small total value?""",
             r"""Index by value instead: `dp[v]` = minimum weight for total value `v`; answer is the largest `v` with `dp[v] ≤ capacity`."""),
    ],
)
