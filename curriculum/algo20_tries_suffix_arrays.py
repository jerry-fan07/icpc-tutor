from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
_AB = str.maketrans("01", "ab")
_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def _rand_ab(rng, n):
    return format(rng.getrandbits(n), f"0{n}b").translate(_AB)


def _rand_word(rng, n, alphabet=_LETTERS):
    return "".join(rng.choices(alphabet, k=n))


def _periodic(rng, n, block_max, alphabet="ab"):
    block = _rand_word(rng, rng.randint(1, block_max), alphabet)
    return (block * (n // len(block) + 1))[:n]


def _fib_word(n):
    a, b = "a", "ab"
    while len(b) < n:
        a, b = b, b + a
    return b[:n]


# ---- word combinations
def _wc_case(s, words):
    return s + "\n" + str(len(words)) + "\n" + "\n".join(words) + "\n"


def _wc_small(rng):
    n = rng.randint(1, 12)
    s = _rand_ab(rng, n)
    words = set()
    for _ in range(rng.randint(1, 6)):
        words.add(_rand_ab(rng, rng.randint(1, 4)))
    words = sorted(words)
    rng.shuffle(words)
    return _wc_case(s, words)


def _wc_medium(rng):
    s = _rand_ab(rng, 1000)
    words = set()
    while len(words) < 1000:
        words.add(_rand_ab(rng, rng.randint(1, 9)))
    words = sorted(words)
    rng.shuffle(words)
    return _wc_case(s, words)


def _wc_many_short(rng):
    """10^5 words: every a/b word of length <= 14, plus words over other letters.
    Trying every word at every position is 5·10^4 * 10^5 = 5·10^9 checks."""
    words = [format(m, f"0{L}b").translate(_AB) for L in range(1, 15) for m in range(1 << L)]
    extra = set()
    while len(words) + len(extra) < 10**5:
        extra.add(_rand_word(rng, rng.randint(5, 10), _LETTERS[2:]))
    words += sorted(extra)
    rng.shuffle(words)
    return _wc_case(_rand_ab(rng, 5 * 10**4), words)


def _wc_long_words(rng):
    """s = a^50000 and the words a, aa, ..., a^1000: every word fits at almost every
    position. Trying every length with a hash set of words costs n * 1000^2 / 2."""
    words = ["a" * L for L in range(1, 1001)]
    rng.shuffle(words)
    return _wc_case("a" * (5 * 10**4), words)


def _wc_letters(rng):
    s = _rand_word(rng, 5 * 10**4, "abc")
    words = set()
    while len(words) < 50000:
        words.add(_rand_word(rng, rng.randint(1, 12), "abc"))
    words = sorted(words)
    rng.shuffle(words)
    return _wc_case(s, words)


# ---- max xor
def _xor_case(rng, n, bits):
    return f"{n}\n" + " ".join(str(rng.getrandbits(bits)) for _ in range(n)) + "\n"


def _xor_sparse(rng, n):
    """Values with few set bits: the answer is well below 2^30 - 1."""
    vals = [(1 << rng.randrange(30)) if rng.random() < 0.3 else 0 for _ in range(n)]
    return f"{n}\n" + " ".join(map(str, vals)) + "\n"


# ---- suffix array problems
def _str_case(s):
    return s + "\n"


# --------------------------------------------------------------------- problems
WORD_COMBINATIONS = Problem(
    id="word_combinations",
    title="Word Combinations",
    difficulty="medium",
    source="CSES 1731 - Word Combinations (different limits)",
    complexity="O(n · L + total word length), L ≤ 1000 the longest word",
    statement=r"""
You are given a string and a dictionary of `k` distinct words. In how many ways can the
string be written as a concatenation of dictionary words? Each word may be used any number
of times. Print the answer modulo 10^9 + 7.
""",
    input=r"""
The first line has the string, of length `n` (1 ≤ n ≤ 5·10^4). The second line has `k`
(1 ≤ k ≤ 10^5). Each of the next `k` lines has one word of at most 1000 letters. All
strings consist of lowercase letters; the words are distinct and their total length is at
most 10^6.
""",
    output=r"""
Print the number of ways modulo 10^9 + 7.
""",
    samples=[
        Test("ababc\n4\nab\nabab\nc\ncb\n", "2\n",
             note="ab + ab + c, and abab + c."),
        Test("aaaa\n2\na\naa\n", "5\n"),
    ],
    tests=[
        Test("a\n1\nb\n"),
        Test("abc\n3\nabc\nab\nc\n"),
        Test("zz\n1\nzzz\n"),
    ],
    gens=[
        Gen("small random", _wc_small, 14),
        Gen("medium random", _wc_medium, 2),
        Gen("10^5 short words", _wc_many_short, 1, large=True),
        Gen("long words of a", _wc_long_words, 1, large=True),
        Gen("three letters, many words", _wc_letters, 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int MOD = 1000000007;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    int k;
    cin >> s >> k;
    // trie: node 0 is the root; nxt[v][c] = child of v by letter c, 0 = none
    vector<array<int, 26>> nxt(1);
    nxt[0].fill(0);
    vector<char> isWord(1, 0);
    for (int w = 0; w < k; w++) {
        string t;
        cin >> t;
        int v = 0;
        for (char ch : t) {
            int c = ch - 'a';
            if (!nxt[v][c]) {
                nxt[v][c] = nxt.size();
                nxt.emplace_back();
                nxt.back().fill(0);
                isWord.push_back(0);
            }
            v = nxt[v][c];
        }
        isWord[v] = 1;
    }
    int n = s.size();
    vector<long long> dp(n + 1, 0);        // dp[i] = ways to write s[i..n)
    dp[n] = 1;
    for (int i = n - 1; i >= 0; i--) {
        // walking s[i], s[i+1], ... down the trie meets exactly the words that fit at i
        int v = 0;
        long long ways = 0;
        for (int j = i; j < n; j++) {
            v = nxt[v][s[j] - 'a'];
            if (!v) break;                  // no word continues: stop early
            if (isWord[v]) ways += dp[j + 1];
        }
        dp[i] = ways % MOD;
    }
    cout << dp[0] << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s;
    int k;
    cin >> s >> k;
    vector<string> w(k);
    for (auto& x : w) cin >> x;
    int n = s.size();
    vector<long long> dp(n + 1, 0);
    dp[n] = 1;
    for (int i = n - 1; i >= 0; i--) {
        for (auto& t : w)
            if (s.substr(i, t.size()) == t) dp[i] = (dp[i] + dp[i + t.size()]) % 1000000007;
    }
    cout << dp[0] << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    int k;
    cin >> s >> k;
    vector<string> w(k);
    for (auto& x : w) cin >> x;
    int n = s.size();
    vector<long long> dp(n + 1, 0);
    dp[n] = 1;
    for (int i = n - 1; i >= 0; i--) {
        long long ways = 0;
        for (auto& t : w) {                   // every word at every position
            int L = t.size();
            if (i + L <= n && s.compare(i, L, t) == 0) ways += dp[i + L];
        }
        dp[i] = ways % 1000000007;
    }
    cout << dp[0] << '\n';
}
""",
    hints=[
        r"""`dp[i]` = number of ways to write the suffix `s[i..]`; `dp[n] = 1`, and `dp[i]` sums
`dp[i + |w|]` over the words `w` that start at `i`. The question is how to find those words
fast.""",
        r"""Put the words in a trie. From position `i`, walk down the trie along `s[i], s[i+1], ...`:
every node marked as a word end is a word that fits at `i`, and the walk stops as soon as
no word continues.""",
    ],
    editorial=r"""
DP from the right: `dp[n] = 1` and `dp[i] = Σ dp[i + |w|]` over dictionary words `w`
that occur at position `i`. Checking all `k` words at every position is n·k = 5·10^9
comparisons (25 s measured). Trying every length up to 1000 with a hash set of the words
is n · 1000 substrings of average length 500 to hash: 2.5·10^10 (7 s on the all-`a`
test).

A **trie** stores the words as paths from a root, one letter per edge, sharing common
prefixes. Walking from the root along `s[i], s[i+1], ...` meets exactly the words that
occur at `i`, in order of length, and stops at the first letter no word continues with.
The walk from `i` costs at most min(n − i, longest word) steps: O(n · L) ≤ 5·10^7 in
total, plus O(total length) to build the trie.

Memory: up to 10^6 + 1 nodes of 26 `int`s is 104 MB. That is normal for this problem;
if memory were tight you would store children in a sorted list or a hash map per node, at
some cost in speed.
""",
)

MAX_XOR = Problem(
    id="max_xor_subarray",
    title="Maximum XOR Subarray",
    difficulty="medium",
    source="CSES 1655 - Maximum Xor Subarray",
    complexity="O(n · 30)",
    statement=r"""
Given an array of `n` non-negative integers, find the maximum XOR of a non-empty
subarray (a contiguous part of the array).
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5). The second line has `n` integers
x_1, ..., x_n (0 ≤ x_i ≤ 10^9).
""",
    output=r"""
Print the maximum XOR of a subarray.
""",
    samples=[
        Test("4\n5 1 5 9\n", "13\n"),
        Test("1\n0\n", "0\n"),
    ],
    tests=[
        Test("1\n1000000000\n"),
        Test("3\n7 7 7\n"),
        Test("5\n1 2 4 8 16\n"),
        Test("4\n0 0 0 0\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _xor_case(rng, rng.randint(1, 10), 5), 14),
        Gen("medium random", lambda rng: _xor_case(rng, 2000, 30), 2),
        Gen("max n, 30-bit values", lambda rng: _xor_case(rng, 200000, 30), 1, large=True),
        Gen("max n, 18-bit values", lambda rng: _xor_case(rng, 200000, 18), 1, large=True),
        Gen("max n, sparse powers of two", lambda rng: _xor_sparse(rng, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    // binary trie over 30-bit numbers, highest bit first; t[v][b] = child by bit b
    vector<array<int, 2>> t(1, {0, 0});
    t.reserve(30 * (n + 1) + 1);
    auto insert = [&](int x) {
        int v = 0;
        for (int b = 29; b >= 0; b--) {
            int c = x >> b & 1;
            if (!t[v][c]) { t[v][c] = t.size(); t.push_back({0, 0}); }
            v = t[v][c];
        }
    };
    auto best_with = [&](int x) {            // max of x ^ y over the inserted y
        int v = 0, r = 0;
        for (int b = 29; b >= 0; b--) {
            int c = x >> b & 1;
            if (t[v][c ^ 1]) { r |= 1 << b; v = t[v][c ^ 1]; }   // take the opposite bit
            else v = t[v][c];
        }
        return r;
    };
    insert(0);                               // the empty prefix: subarrays starting at 1
    int prefix = 0, ans = 0;
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        prefix ^= x;                         // xor of a[l..r] = prefix[r] ^ prefix[l-1]
        ans = max(ans, best_with(prefix));
        insert(prefix);
    }
    cout << ans << '\n';
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
    int best = 0;
    for (int l = 0; l < n; l++) {
        int x = 0;
        for (int r = l; r < n; r++) { x ^= a[r]; best = max(best, x); }
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
    vector<int> p(n + 1, 0);
    for (int i = 1; i <= n; i++) { int x; cin >> x; p[i] = p[i - 1] ^ x; }
    int best = 0;
    for (int i = 0; i <= n; i++)
        for (int j = i + 1; j <= n; j++) best = max(best, p[i] ^ p[j]);
    cout << best << '\n';
}
""",
    hints=[
        r"""With prefix XORs `p`, the XOR of `a[l..r]` is `p[r] ^ p[l-1]`. So the question is the
largest XOR of two prefix values, including `p[0] = 0`.""",
        r"""For a fixed `p[r]`, choose the partner greedily from the highest bit down: bit 29 set
beats anything the lower bits can add. Store earlier prefixes in a binary trie and at
each level walk to the child with the opposite bit when it exists.""",
    ],
    editorial=r"""
Prefix XORs turn subarrays into pairs (algo01): XOR(a[l..r]) = p[r] ^ p[l−1]. So we want
the maximum of `p[i] ^ p[j]` over `i < j`, with `p[0] = 0` included, and trying all pairs
is 2·10^10 operations.

For a fixed `x = p[r]`, the best partner is found greedily from the top bit: making bit
29 of the result 1 is worth more than all lower bits together (2^29 > 2^29 − 1). Keep the
earlier prefixes in a **binary trie**, a trie over the 30-bit representations, highest bit
first. At each level go to the child whose bit is the opposite of `x`'s, if it exists
(that result bit becomes 1), else to the other child. 30 steps per query and per insert:
6·10^6 in total.

Forgetting to insert `p[0] = 0` loses every subarray that starts at the first element;
the second sample and a single-element test catch it.
""",
)

DISTINCT_SUBSTRINGS = Problem(
    id="distinct_substrings",
    title="Distinct Substrings",
    difficulty="hard",
    source="CSES 2105 - Distinct Substrings",
    complexity="O(n log^2 n)",
    statement=r"""
Count the number of distinct non-empty substrings of a string.
""",
    input=r"""
One line with a string of `n` lowercase letters (1 ≤ n ≤ 10^5).
""",
    output=r"""
Print the number of distinct substrings.
""",
    samples=[
        Test("abaa\n", "8\n",
             note="a, b, aa, ab, ba, aba, baa, abaa."),
        Test("banana\n", "15\n"),
    ],
    tests=[
        Test("a\n"),
        Test("aaaa\n"),
        Test("abcd\n"),
        Test("abab\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _str_case(_rand_ab(rng, rng.randint(1, 12))), 14),
        Gen("medium random", lambda rng: _str_case(_rand_word(rng, 300, "abc")), 2),
        Gen("medium periodic", lambda rng: _str_case(_periodic(rng, 300, 4)), 2),
        Gen("all equal letters", lambda rng: _str_case("a" * 10**5), 1, large=True),
        Gen("random, 26 letters", lambda rng: _str_case(_rand_word(rng, 10**5)), 1, large=True),
        Gen("Fibonacci word", lambda rng: _str_case(_fib_word(10**5)), 1, large=True),
        Gen("periodic", lambda rng: _str_case(_periodic(rng, 10**5, 6)), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// suffix array by prefix doubling: after the round with step k, rk[i] is the rank of
// s[i..i+2k) among all such pieces (pieces running off the end are shorter)
vector<int> suffix_array(const string& s) {
    int n = s.size();
    vector<int> sa(n), rk(n), tmp(n);
    for (int i = 0; i < n; i++) { sa[i] = i; rk[i] = s[i]; }
    for (int k = 1; ; k <<= 1) {
        auto key = [&](int i) { return make_pair(rk[i], i + k < n ? rk[i + k] : -1); };
        sort(sa.begin(), sa.end(), [&](int a, int b) { return key(a) < key(b); });
        tmp[sa[0]] = 0;
        for (int i = 1; i < n; i++) tmp[sa[i]] = tmp[sa[i - 1]] + (key(sa[i - 1]) < key(sa[i]));
        rk = tmp;
        if (rk[sa[n - 1]] == n - 1) break;           // all ranks distinct: done
    }
    return sa;
}

// Kasai: lcp[i] = longest common prefix of the suffixes sa[i-1] and sa[i]
vector<int> lcp_array(const string& s, const vector<int>& sa) {
    int n = s.size();
    vector<int> rk(n), lcp(n, 0);
    for (int i = 0; i < n; i++) rk[sa[i]] = i;
    for (int i = 0, h = 0; i < n; i++) {             // suffixes in text order
        if (rk[i] == 0) { h = 0; continue; }
        int j = sa[rk[i] - 1];                       // the suffix just before i in sorted order
        while (i + h < n && j + h < n && s[i + h] == s[j + h]) h++;
        lcp[rk[i]] = h;
        if (h > 0) h--;                              // the next suffix keeps at least h - 1
    }
    return lcp;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    long long n = s.size();
    vector<int> sa = suffix_array(s);
    vector<int> lcp = lcp_array(s, sa);
    // suffix sa[i] brings n - sa[i] prefixes, of which lcp[i] were already seen
    long long total = n * (n + 1) / 2;               // up to 5 * 10^9: long long
    for (int x : lcp) total -= x;
    cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s;
    cin >> s;
    set<string> all;
    for (size_t i = 0; i < s.size(); i++)
        for (size_t len = 1; i + len <= s.size(); len++) all.insert(s.substr(i, len));
    cout << all.size() << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long ull;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    int n = s.size();
    const ull M = (1ULL << 61) - 1;
    auto mul = [&](ull a, ull b) {
        __uint128_t p = (__uint128_t)a * b;
        ull r = (ull)(p & M) + (ull)(p >> 61);
        return r >= M ? r - M : r;
    };
    ull B = 911382323;
    vector<ull> h(n + 1, 0), pw(n + 1, 1);
    for (int i = 0; i < n; i++) { h[i + 1] = (mul(h[i], B) + s[i]) % M; pw[i + 1] = mul(pw[i], B); }
    long long total = 0;
    vector<ull> v;
    for (int L = 1; L <= n; L++) {            // hash every substring of each length
        v.clear();
        for (int i = 0; i + L <= n; i++) {
            ull x = h[i + L] + M - mul(h[i], pw[L]);
            v.push_back(x >= M ? x - M : x);
        }
        sort(v.begin(), v.end());
        total += unique(v.begin(), v.end()) - v.begin();
    }
    cout << total << '\n';
}
""",
    hints=[
        r"""Every substring is a prefix of some suffix. Sort the suffixes: how many prefixes of each
suffix are new, compared with the suffix just before it in sorted order?""",
        r"""Suffix `sa[i]` has n − sa[i] prefixes, and exactly lcp[i] of them (its common prefix with
the previous suffix) appeared before. Answer: n(n+1)/2 − Σ lcp.""",
        r"""Build the suffix array by prefix doubling (sort by pairs of ranks, O(n log^2 n)) and the
LCP array with Kasai in O(n).""",
    ],
    editorial=r"""
Every substring is a prefix of a suffix. List the suffixes in sorted order. The prefixes
of suffix `sa[i]` of length at most lcp[i] (its longest common prefix with the previous
suffix `sa[i−1]`) are prefixes of that previous suffix and were counted already; the
longer ones are new, because any earlier suffix sharing such a prefix would sort next to
it. So the answer is Σ (n − sa[i] − lcp[i]) = n(n+1)/2 − Σ lcp[i].

The **suffix array** comes from prefix doubling: once every position has the rank of its
first `k` characters, the rank of its first 2k characters is determined by the pair
(rank[i], rank[i + k]); sort by pairs, reassign ranks, double `k`. log2(10^5) ≈ 17 rounds
of an O(n log n) sort. The LCP array comes from **Kasai's** algorithm: visiting suffixes in
text order, the common prefix with the sorted predecessor shrinks by at most 1 from one
suffix to the next, so a pointer that moves back at most `n` times does all the work.

Hashing every substring of every length is O(n^2) hashes, 5·10^9, and the answer itself
reaches 5·10^9, beyond `int`.
""",
)


def _repeat_checker(inp, expected, got):
    s = inp.split()[0]
    e = expected.split()[0]
    g = got.split()
    if len(g) != 1:
        return False, f"expected a single string, found {len(g)} tokens"
    g = g[0]
    if e == "-1":
        return (g == "-1"), ("" if g == "-1" else "no substring occurs twice in this string")
    if g == "-1":
        return False, f"a substring of length {len(e)} occurs twice"
    if len(g) != len(e):
        return False, (f"your string has length {len(g)}; the longest repeating substring "
                       f"has length {len(e)}")
    i = s.find(g)
    if i < 0 or s.find(g, i + 1) < 0:
        return False, "your string does not occur twice in the input"
    return True, ""


REPEATING_SUBSTRING = Problem(
    id="repeating_substring",
    title="Repeating Substring",
    difficulty="hard",
    source="CSES 2106 - Repeating Substring (with n up to 2·10^5)",
    complexity="O(n log^2 n)",
    checker=_repeat_checker,
    statement=r"""
Find the longest substring that occurs at least twice in a given string. The two
occurrences may overlap.
""",
    input=r"""
One line with a string of `n` lowercase letters (1 ≤ n ≤ 2·10^5).
""",
    output=r"""
Print a longest substring that occurs at least twice. If there are several, print any of
them. If no substring occurs twice, print `-1`.
""",
    samples=[
        Test("cabababc\n", "abab\n"),
        Test("abc\n", "-1\n"),
    ],
    tests=[
        Test("a\n"),
        Test("aa\n"),
        Test("aaaa\n"),
        Test("abcabc\n"),
        Test("abcdab\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _str_case(_rand_ab(rng, rng.randint(1, 12))), 14),
        Gen("medium random", lambda rng: _str_case(_rand_word(rng, 300, "abc")), 2),
        Gen("medium periodic", lambda rng: _str_case(_periodic(rng, 300, 5)), 2),
        Gen("all equal letters", lambda rng: _str_case("a" * (2 * 10**5)), 1, large=True),
        Gen("periodic", lambda rng: _str_case(_periodic(rng, 2 * 10**5, 5)), 1, large=True),
        Gen("random, 26 letters", lambda rng: _str_case(_rand_word(rng, 2 * 10**5)), 1, large=True),
        Gen("Fibonacci word", lambda rng: _str_case(_fib_word(2 * 10**5)), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

vector<int> suffix_array(const string& s) {
    int n = s.size();
    vector<int> sa(n), rk(n), tmp(n);
    for (int i = 0; i < n; i++) { sa[i] = i; rk[i] = s[i]; }
    for (int k = 1; ; k <<= 1) {
        auto key = [&](int i) { return make_pair(rk[i], i + k < n ? rk[i + k] : -1); };
        sort(sa.begin(), sa.end(), [&](int a, int b) { return key(a) < key(b); });
        tmp[sa[0]] = 0;
        for (int i = 1; i < n; i++) tmp[sa[i]] = tmp[sa[i - 1]] + (key(sa[i - 1]) < key(sa[i]));
        rk = tmp;
        if (rk[sa[n - 1]] == n - 1) break;
    }
    return sa;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    int n = s.size();
    vector<int> sa = suffix_array(s);
    vector<int> rk(n);
    for (int i = 0; i < n; i++) rk[sa[i]] = i;
    // Kasai; a repeated substring is a common prefix of two suffixes, and the longest
    // common prefix of any two suffixes is attained by two neighbours in sorted order
    int best = 0, where = -1;
    for (int i = 0, h = 0; i < n; i++) {
        if (rk[i] == 0) { h = 0; continue; }
        int j = sa[rk[i] - 1];
        while (i + h < n && j + h < n && s[i + h] == s[j + h]) h++;
        if (h > best) { best = h; where = i; }
        if (h > 0) h--;
    }
    if (best == 0) cout << -1 << '\n';
    else cout << s.substr(where, best) << '\n';
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
    for (int L = n - 1; L >= 1; L--) {
        set<string> seen;
        for (int i = 0; i + L <= n; i++) {
            string t = s.substr(i, L);
            if (seen.count(t)) { cout << t << '\n'; return 0; }
            seen.insert(t);
        }
    }
    cout << -1 << '\n';
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
    int n = s.size();
    vector<int> sa(n);
    iota(sa.begin(), sa.end(), 0);
    // sort the suffixes by comparing them directly: O(n) per comparison
    sort(sa.begin(), sa.end(), [&](int a, int b) {
        return s.compare(a, string::npos, s, b, string::npos) < 0;
    });
    int best = 0, where = -1;
    for (int i = 1; i < n; i++) {
        int a = sa[i - 1], b = sa[i], h = 0;
        while (a + h < n && b + h < n && s[a + h] == s[b + h]) h++;
        if (h > best) { best = h; where = a; }
    }
    if (best == 0) cout << -1 << '\n';
    else cout << s.substr(where, best) << '\n';
}
""",
    hints=[
        r"""A substring that occurs twice is a common prefix of two different suffixes. Which pairs
of suffixes can have the longest common prefix?""",
        r"""In sorted order, the common prefix of two suffixes is the minimum of the adjacent LCPs
between them. So the answer is the largest value in the LCP array, and the substring is
that many characters of either suffix.""",
    ],
    editorial=r"""
A substring occurring at positions `i ≠ j` is a common prefix of the suffixes `i` and
`j`, so the answer's length is the largest LCP over all pairs of suffixes. In sorted
order, the LCP of two suffixes equals the minimum of the adjacent LCPs between them
(everything in between agrees on that common prefix, by sortedness), so the largest one
is attained by two *neighbours*: the answer is max(lcp), and the string is that many
characters starting at either suffix. Suffix array by prefix doubling plus Kasai:
O(n log^2 n).

Sorting the suffixes with direct string comparisons works on random text, where
comparisons stop after a few characters, but on `aaaa...a` or a periodic string every
comparison runs for thousands of characters: measured, about 15 seconds at n = 2·10^5.

Binary search on the length with hashing also works (if a length-L substring repeats, so
does a length-(L−1) one), in O(n log n) expected time with a random-base hash.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo20",
    title="strings II: tries & suffix arrays",
    track="algo",
    order=20,
    summary="Tries for dictionaries and DP over them, binary tries for XOR, suffix arrays "
            "by prefix doubling, the LCP array with Kasai, and the substring questions they "
            "answer.",
    prereqs=["algo19", "algo06"],
    tags=["trie", "binary trie", "xor", "suffix array", "prefix doubling", "lcp", "kasai",
          "distinct substrings"],
    parts=[
        Part("Tries: a dictionary that shares prefixes", [
            Say(r"""
**Word Combinations.** A string of length `n ≤ 5·10^4` and a dictionary of `k ≤ 10^5`
distinct words (each at most 1000 letters, total length ≤ 10^6). In how many ways can the
string be cut into dictionary words?

The DP is algo06 material: `dp[i]` = number of ways to write the suffix `s[i..]`, with
`dp[n] = 1` and `dp[i] = Σ dp[i + |w|]` over the words `w` that occur at position `i`.
The question is how to find those words. The direct way checks every word at every
position.
"""),
            Numeric(r"""
How many (position, word) checks is that in the worst case?
""", answer=5e9, rel=0.5, unit="checks",
                explain=r"""
`n · k = 5·10^4 · 10^5 = 5·10^9`. Most checks fail after a character or two, but even a
call that fails at once costs a few nanoseconds: measured, 25 seconds.
"""),
            Reflect(r"""
At position `i` the string reads `abcab...`, and the dictionary has `ab`, `abc`, `abd`,
`abcde` and 90,000 words starting with `x`. What does checking them one by one waste?
""", answer=r"""
Two things. The words `ab`, `abc`, `abd`, `abcde` all start with `ab`, and each check
compares that shared `ab` against the string again. And the 90,000 `x` words are each
tried, although one look at `s[i] = a` rules out all of them at once. Store the words in
a tree where each shared prefix is stored once, with one letter per edge (a **trie**).
Then a single walk from the root along `s[i], s[i+1], ...` meets exactly the words that
fit at `i`, and it stops at the first letter that no word continues with.
"""),
            Short(r"""
Build the trie of the words `a`, `ab`, `abc`, `b`, `bc`. How many nodes does it have,
counting the root?
""", accept=["6"], placeholder="a number",
                hint="One node per distinct prefix, plus the root for the empty prefix.",
                explain=r"""
6: the root, `a`, `ab`, `abc`, `b`, `bc`. Every node is a distinct prefix of some word,
and five of them are marked as word ends. The number of nodes is at most the total length
of the words, plus 1.
"""),
            Say(r"""
With the children as an array of 26 indices per node (0 = no child):

```cpp
vector<array<int, 26>> nxt(1);          // node 0 is the root
nxt[0].fill(0);
vector<char> isWord(1, 0);
for (const string& w : words) {
    int v = 0;
    for (char ch : w) {
        int c = ch - 'a';
        if (!nxt[v][c]) {               // create the child
            nxt[v][c] = nxt.size();
            nxt.emplace_back();
            nxt.back().fill(0);
            isWord.push_back(0);
        }
        v = nxt[v][c];
    }
    isWord[v] = 1;
}
```

Then `dp[i]` walks from the root along `s[i..]`, adding `dp[j + 1]` at every word end
`s[i..j]`, and stops at the first missing child.
"""),
            Numeric(r"""
The dictionary has total length 10^6, so up to 10^6 + 1 nodes, each an array of 26
`int`s. How many bytes is that?
""", answer=1.04e8, rel=0.3, unit="bytes",
                explain=r"""
`10^6 · 26 · 4 ≈ 1.04·10^8` bytes, about 100 MB. Fine for the usual 256 MB, but
worth knowing before you declare it: with a larger alphabet or more text you would store
children in a sorted vector or a hash map per node, trading speed for memory.
"""),
            Try("word_combinations", note="A trie of the words, and a walk from every position. "
                "The hidden tests include 10^5 short words, and a string of 5·10^4 `a`s with the "
                "words `a` to `a^1000`."),
        ]),
        Part("A trie over bits", [
            Say(r"""
Tries are not only for text. **Maximum XOR Subarray**: `n ≤ 2·10^5` numbers below 2^30;
find the largest XOR of a contiguous subarray.

algo01's prefix trick works for XOR (it is its own inverse): with `p[0] = 0` and
`p[i] = p[i−1] ^ a[i]`, the XOR of `a[l..r]` is `p[r] ^ p[l−1]`. So the task is the
largest XOR of two prefix values.
"""),
            Numeric(r"""
How many pairs of prefix values is that for `n = 2·10^5`?
""", answer=2e10, rel=0.5, unit="pairs",
                explain=r"""
About n^2/2 = 2·10^10. Measured: about 6 seconds for the double loop.
"""),
            MCQ(r"""
Fix `x = p[r]`. Among the earlier prefixes, which partner `y` maximises `x ^ y`?
""", [
                Opt("The largest `y`.",
                    why="Size is not the point: with `x = 4` (100), `y = 3` (011) gives 7 while "
                        "`y = 4` gives 0."),
                Opt("Decide from the highest bit down: prefer a `y` whose bit differs from `x`'s at "
                    "the highest position possible, then the next, and so on.", correct=True,
                    why="Yes: a 1 at bit 29 of the result is worth 2^29, more than all lower bits "
                        "together (2^29 − 1). So the choice is greedy, bit by bit from the top."),
                Opt("The `y` with the most bits different from `x`.",
                    why="Counting ignores the weight of each bit: for `x = 0`, `y = 8` (1000) "
                        "differs in one bit and gives 8, while `y = 7` (0111) differs in three "
                        "bits and gives only 7."),
            ]),
            Reflect(r"""
Which data structure lets you make that greedy choice in O(30) steps per query, while
prefixes keep being added?
""", answer=r"""
A **binary trie**: insert every prefix value as a 30-letter word over {0, 1}, highest bit
first. To query `x`, walk from the root; at each level go to the child whose bit is the
opposite of `x`'s bit if it exists (that bit of the result becomes 1), otherwise to the
other child. Inserting and querying both cost 30 steps, 6·10^6 in total. The trie
answers "the best partner" for every `r` without looking at the pairs.
"""),
            Numeric(r"""
The trie holds 3 (011), 5 (101) and 6 (110). Query `x = 2` (010): what is the largest
`x ^ y`?
""", answer=7,
                hint="At the top bit, x has 0: go to a 1 if possible. Then x has 1: go to a 0 if possible.",
                explain=r"""
Top bit: `x` has 0, so take a 1 (5 or 6 remain). Middle bit: `x` has 1, take a 0: only 5
(101). Bottom bit: forced. `2 ^ 5 = 7` (111). Check: `2 ^ 6 = 4`, `2 ^ 3 = 1`.
"""),
            MCQ(r"""
The loop does `prefix ^= a[i]`, queries the trie with `prefix`, then inserts `prefix`.
What must be in the trie before the first query?
""", [
                Opt("Nothing: the first query just returns 0.",
                    why="Then the subarray `a[1..r]`, which is `p[r] ^ p[0]`, is never considered. "
                        "For a single element `[1000000000]` you would print 0."),
                Opt("The value 0, for the empty prefix `p[0]`.", correct=True,
                    why="Right. `p[0] = 0` is a real prefix, the one that makes subarrays starting "
                        "at the first element possible; it is the XOR version of algo01's sentinel."),
                Opt("All the prefixes, inserted in advance.",
                    why="That happens to work (XOR is symmetric, and `x ^ x = 0` adds nothing), "
                        "but it is more than needed: the only prefix the loop never inserts "
                        "before its first query is `p[0]`."),
            ]),
            Try("max_xor_subarray", note="Prefix XORs, a binary trie over 30 bits, and `p[0] = 0` "
                "inserted first."),
        ]),
        Part("Every substring is a prefix of a suffix", [
            Say(r"""
**Distinct Substrings.** Count the distinct substrings of a string of length `n ≤ 10^5`.
The obvious program puts every substring into a set.
"""),
            Numeric(r"""
How many substrings (with repetitions) are there for `n = 10^5`?
""", answer=5e9, rel=0.5, unit="substrings",
                explain=r"""
n(n+1)/2 ≈ 5·10^9, with total length about n^3/6 ≈ 1.7·10^14 characters. Storing them is
out of the question, and even hashing each one (algo19) is 5·10^9 hashes.
"""),
            Reflect(r"""
Every substring is a prefix of some suffix. Suppose the suffixes are listed in sorted
order. For one suffix, which of its prefixes have already appeared as prefixes of earlier
suffixes in the list, and which are new?
""", answer=r"""
Let `h` be the length of its longest common prefix with the suffix just before it in
sorted order. Its prefixes of length ≤ h are prefixes of that previous suffix, so they
were counted already. Its longer prefixes are new: an earlier suffix sharing such a
prefix would also share it with the previous suffix, which sits between them in sorted
order. So a suffix of length `m` contributes `m − h` new substrings, and the answer is
n(n+1)/2 minus the sum of these adjacent common prefixes.
"""),
            Short(r"""
The sorted order of the suffixes, written as their starting positions, is the **suffix
array**. For `banana` (positions 0..5), write it.
""", accept=["5 3 1 0 4 2", "5,3,1,0,4,2", "5, 3, 1, 0, 4, 2"], placeholder="six positions",
                hint="The suffixes are banana, anana, nana, ana, na, a.",
                explain=r"""
`a` (5) < `ana` (3) < `anana` (1) < `banana` (0) < `na` (4) < `nana` (2): `5 3 1 0 4 2`.
A shorter string that is a prefix of a longer one comes first.
"""),
            Short(r"""
The common prefixes of neighbours in that order are 1 (a/ana), 3 (ana/anana), 0, 0 and 2
(na/nana). How many distinct substrings does `banana` have?
""", accept=["15"], placeholder="a number",
                explain=r"""
6·7/2 − (1 + 3 + 0 + 0 + 2) = 21 − 6 = 15. The array of those neighbour common prefixes is
the **LCP array**; with it and the suffix array, many substring questions become a single
pass.
"""),
            Numeric(r"""
Building the suffix array with `sort` and direct string comparisons costs about
n log2 n comparisons, each up to `n` characters on a string like `aaaa...a`. Estimate the
character comparisons for `n = 10^5`.
""", answer=1.7e11, rel=0.6, unit="comparisons",
                explain=r"""
`10^5 · 17 · 10^5 ≈ 1.7·10^11`. On random text the comparisons stop after a few
characters and this "naive suffix array" is fast, which is exactly why it is tempting;
on periodic text it takes seconds. The tests always include `aaaa...a`.
"""),
        ]),
        Part("Prefix doubling", [
            Say(r"""
The fix is to sort by longer and longer prefixes, reusing the previous round. Suppose
that for every position `i` you know `rank[i]`: the rank of `s[i..i+k)` (its first `k`
characters) among all positions. Pieces that run off the end are just shorter.
"""),
            MCQ(r"""
How do you get the ranks by the first `2k` characters without looking at any characters?
""", [
                Opt("Sort by `rank[i] + rank[i + k]`.",
                    why="Different pairs can have equal sums: (1, 3) and (2, 2) would tie although "
                        "their first halves already differ."),
                Opt("Sort by the pair `(rank[i], rank[i + k])`, with −1 when `i + k` is past the end.",
                    correct=True,
                    why="Yes. The first 2k characters are the first `k` (ranked by `rank[i]`) "
                        "followed by the next `k` (ranked by `rank[i + k]`). Comparing the pairs "
                        "lexicographically compares the 2k-character pieces. The −1 makes a piece "
                        "that ends early sort first, as a prefix should."),
                Opt("Sort by `rank[i + k]` only.",
                    why="The first half decides first; the second half only breaks ties."),
            ], explain=r"""
Then assign new ranks by walking the sorted order (equal pairs get equal ranks), and
double `k`. After the round with `k ≥ n` every rank is distinct and the order is the
suffix array. Most implementations stop as soon as the ranks are all distinct.
"""),
            Short(r"""
`banana` ranked by the first letter (a = 0, b = 1, n = 2) is `1 0 2 0 2 0` by position.
Rank the positions by their first two letters, using pairs `(rank[i], rank[i+1])` with
−1 past the end. Write the six new ranks by position (dense: 0, 1, 2, ...).
""", accept=["2 1 3 1 3 0", "2,1,3,1,3,0", "2, 1, 3, 1, 3, 0"], placeholder="six ranks",
                hint="The pairs are (1,0), (0,2), (2,0), (0,2), (2,0), (0,−1).",
                explain=r"""
Sorted pairs: (0,−1) at position 5; (0,2) at 1 and 3 (`an`, tied); (1,0) at 0; (2,0) at 2
and 4 (`na`, tied). New ranks by position: `2 1 3 1 3 0`. One more round, with pairs
`(rank[i], rank[i+2])`, separates everything and gives `5 3 1 0 4 2`.
"""),
            Numeric(r"""
How many doubling rounds can `n = 10^5` need?
""", answer=17, tol=1,
                explain=r"""
⌈log2(10^5)⌉ = 17. With `std::sort` each round is O(n log n), so the total is
O(n log^2 n) ≈ 3·10^7 comparisons of pairs: about 0.02 s here. Radix-sorting the pairs
(two passes of counting sort) makes it O(n log n); rarely needed.
"""),
            Say(r"""
The whole construction:

```cpp
vector<int> suffix_array(const string& s) {
    int n = s.size();
    vector<int> sa(n), rk(n), tmp(n);
    for (int i = 0; i < n; i++) { sa[i] = i; rk[i] = s[i]; }
    for (int k = 1; ; k <<= 1) {
        auto key = [&](int i) { return make_pair(rk[i], i + k < n ? rk[i + k] : -1); };
        sort(sa.begin(), sa.end(), [&](int a, int b) { return key(a) < key(b); });
        tmp[sa[0]] = 0;
        for (int i = 1; i < n; i++)
            tmp[sa[i]] = tmp[sa[i - 1]] + (key(sa[i - 1]) < key(sa[i]));
        rk = tmp;
        if (rk[sa[n - 1]] == n - 1) break;     // all distinct
    }
    return sa;
}
```

The new ranks go into `tmp`, not into `rk` directly: `key` reads `rk` while the ranks are
being assigned.
"""),
            MCQ(r"""
You declare the rank array as a global `int rank[200005];` and use it in `main`, with the
usual `#include <bits/stdc++.h>` and `using namespace std;`. What happens?
""", [
                Opt("Nothing special; it is a normal global array.",
                    why="The name is taken: `std::rank` is a type trait (from `<type_traits>`), and "
                        "`using namespace std` brings it into view."),
                Opt("Compilation error: \"reference to 'rank' is ambiguous\".", correct=True,
                    why="Right: GCC cannot tell your global from `std::rank`. Rename it (`rk`), "
                        "or make it local. Globals named `next`, `prev`, `count`, `hash`, `left`, "
                        "`right` or `distance` fail the same way, and `y1` or `index` clash with "
                        "C library functions."),
                Opt("It compiles, but `rank` refers to `std::rank` and crashes at run time.",
                    why="It never gets that far: the ambiguity is a compile error."),
            ]),
        ]),
        Part("LCP in linear time, and what it answers", [
            Say(r"""
Now the LCP array: `lcp[i]` = the longest common prefix of the suffixes `sa[i−1]` and
`sa[i]`. Comparing neighbours character by character is O(n^2) on `aaaa...a`.
"""),
            Reflect(r"""
Process the suffixes in *text* order: suffix 0, then suffix 1, and so on. Say suffix `i`
has common prefix `h > 0` with its sorted predecessor `j`. Drop the first character of
both. What can you say about suffix `i + 1` and its own sorted predecessor?
""", answer=r"""
Suffixes `j + 1` and `i + 1` share `h − 1` characters, and `j + 1` sorts before `i + 1`
(suffix `j` sorted before suffix `i`, and their first characters are equal). The
predecessor of `i + 1` in sorted order lies between them or is `j + 1` itself, so it
shares at least `h − 1` characters with `i + 1` too. So the comparison for `i + 1` can start at `h − 1` instead of 0. This is
**Kasai's algorithm**.
"""),
            MCQ(r"""
Why does that make the whole LCP computation O(n)?
""", [
                Opt("Each suffix is compared with at most one other, so it is n comparisons of O(1).",
                    why="Each comparison can still take many steps; the argument has to bound the "
                        "total number of character steps."),
                Opt("`h` never exceeds `n` and drops by at most 1 per suffix (plus one reset to 0 at "
                    "the smallest suffix), so it can rise only O(n) times: O(n) character "
                    "comparisons in total.", correct=True,
                    why="Yes: the same amortised bookkeeping as the prefix function. The total "
                        "drop is below 2n, and the total rise is at most n plus the total drop."),
                Opt("Because the LCP values sum to O(n).",
                    why="They do not: on `aaaa...a` they sum to about n^2/2. Kasai is linear "
                        "anyway, because it reuses `h` rather than recomputing it."),
            ], explain=r"""
```cpp
vector<int> rk(n), lcp(n, 0);
for (int i = 0; i < n; i++) rk[sa[i]] = i;
for (int i = 0, h = 0; i < n; i++) {
    if (rk[i] == 0) { h = 0; continue; }
    int j = sa[rk[i] - 1];
    while (i + h < n && j + h < n && s[i + h] == s[j + h]) h++;
    lcp[rk[i]] = h;
    if (h > 0) h--;
}
```
"""),
            Numeric(r"""
Take a random string of 10^5 letters: almost all of its substrings are distinct. Roughly
how large is the answer?
""", answer=5e9, rel=0.5,
                explain=r"""
Close to n(n+1)/2 ≈ 5·10^9, more than the 2.1·10^9 of an `int`. Sum in `long long`.
"""),
            Try("distinct_substrings", note="Suffix array, Kasai, n(n+1)/2 − Σ lcp in `long long`."),
            MCQ(r"""
**Repeating Substring**: the longest substring that occurs at least twice. How does the
LCP array answer it?
""", [
                Opt("It is the longest suffix.",
                    why="A suffix occurs once as a suffix, and repetition is about two *different* "
                        "starting positions."),
                Opt("Its length is the maximum of the LCP array: a repeated substring is a common "
                    "prefix of two suffixes, and the longest common prefix over all pairs is "
                    "attained by two neighbours in sorted order.", correct=True,
                    why="Right. Between two suffixes in sorted order, every suffix in between "
                        "agrees with both on their common prefix, so their LCP is the minimum of "
                        "the adjacent LCPs between them, never more than an adjacent one."),
                Opt("It needs all pairs of suffixes, O(n^2) LCP queries.",
                    why="Only neighbours matter, by the sortedness argument: n − 1 values."),
            ], explain=r"""
Print `lcp` characters starting at either suffix of the best neighbouring pair, or −1 if
the maximum is 0. (An alternative: binary search the length with hashing, since if some
length-L substring repeats, so does a length-(L − 1) one.)
"""),
            Try("repeating_substring", note="Here `n` goes up to 2·10^5, and the tests include "
                "`aaaa...a`, where sorting suffixes by direct comparison takes about 15 seconds."),
        ]),
    ],
    problems=[WORD_COMBINATIONS, MAX_XOR, DISTINCT_SUBSTRINGS, REPEATING_SUBSTRING],
    cards=[
        Card(r"""What is a trie, and how many nodes can it have?""",
             r"""A tree of the words' prefixes, one letter per edge, shared prefixes stored once. At most (total length of the words) + 1 nodes."""),
        Card(r"""Word Combinations DP with a trie?""",
             r"""`dp[i] = Σ dp[j + 1]` over the word ends met while walking the trie along `s[i..j]`; stop at the first missing child. O(n · longest word)."""),
        Card(r"""Memory of an array-of-26 trie with 10^6 nodes?""",
             r"""26 · 4 bytes · 10^6 ≈ 104 MB. Use sorted child lists or hash maps if memory is tight."""),
        Card(r"""Maximum XOR of two numbers from a set, fast?""",
             r"""Binary trie, highest bit first; for query x, at each level go to the child with the opposite bit when it exists. O(bits) per insert and query."""),
        Card(r"""Maximum XOR subarray?""",
             r"""Prefix XORs p (with p[0] = 0 inserted first) and a binary trie: for each r, best `p[r] ^ p[l]` over earlier l."""),
        Card(r"""What is a suffix array?""",
             r"""The starting positions of all suffixes in sorted order. `banana` → 5 3 1 0 4 2."""),
        Card(r"""Prefix doubling: how do ranks by k characters give ranks by 2k?""",
             r"""Sort positions by the pair `(rank[i], rank[i+k])` (−1 past the end), reassign ranks, double k. ⌈log2 n⌉ rounds; O(n log² n) with `sort`."""),
        Card(r"""Kasai's LCP algorithm: the key fact?""",
             r"""Visiting suffixes in text order, if suffix i has LCP h with its sorted predecessor, suffix i+1 has LCP ≥ h − 1 with its own. So h drops by at most 1: O(n)."""),
        Card(r"""Number of distinct substrings from SA + LCP?""",
             r"""n(n+1)/2 − Σ lcp[i] (in `long long`)."""),
        Card(r"""Longest substring occurring twice?""",
             r"""max(lcp): the best pair of suffixes is always adjacent in the suffix array."""),
        Card(r"""Why must a global array not be called `rank` in contest code?""",
             r"""With `bits/stdc++.h` and `using namespace std`, it clashes with `std::rank`: "reference to 'rank' is ambiguous". Call it `rk`."""),
    ],
)
