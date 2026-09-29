from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
_AB = str.maketrans("01", "ab")


def _rand_ab(rng, n):
    """n random letters from {a, b}, built from one big random integer (fast)."""
    return format(rng.getrandbits(n), f"0{n}b").translate(_AB)


def _rand_word(rng, n, alphabet):
    return "".join(rng.choice(alphabet) for _ in range(n))


def _periodic(rng, n, block_max, alphabet="ab"):
    block = _rand_word(rng, rng.randint(1, block_max), alphabet)
    return (block * (n // len(block) + 1))[:n]


def _fib_word(n):
    a, b = "a", "ab"
    while len(b) < n:
        a, b = b, b + a
    return b[:n]


def _thue_morse(k):
    return "".join("ab"[bin(i).count("1") & 1] for i in range(1 << k))


def _flip(s):
    return s.translate(str.maketrans("ab", "ba"))


# ---- string matching
def _sm_small(rng):
    return _rand_ab(rng, rng.randint(1, 20)) + "\n" + _rand_ab(rng, rng.randint(1, 5)) + "\n"


def _sm_medium(rng):
    return _periodic(rng, 5000, 4) + "\n" + _periodic(rng, rng.randint(1, 9), 3) + "\n"


# ---- borders / occurrences
def _one_string(s):
    return s + "\n"


# ---- substring comparisons
def _queries(rng, n, q, span=None):
    out = []
    for _ in range(q):
        if span:                                # both starts near the front: longest ranges
            a, b = rng.randint(1, span), rng.randint(1, span)
            ln = n - max(a, b) + 1
        else:
            a, b = rng.randint(1, n), rng.randint(1, n)
            ln = rng.randint(1, n - max(a, b) + 1)
        out.append(f"{a} {b} {ln}")
    return out


def _cmp_case(s, rows):
    return s + "\n" + str(len(rows)) + "\n" + "\n".join(rows) + "\n"


def _cmp_small(rng):
    n = rng.randint(1, 30)
    s = _rand_ab(rng, n) if rng.random() < 0.5 else _periodic(rng, n, 3)
    return _cmp_case(s, _queries(rng, n, rng.randint(1, 30)))


def _cmp_medium(rng):
    n = 3000
    s = list(_periodic(rng, n, 5))
    for _ in range(5):
        s[rng.randrange(n)] = rng.choice("ab")
    return _cmp_case("".join(s), _queries(rng, n, 3000))


def _cmp_large(rng, kind):
    n, q = 10**6, 3 * 10**5
    if kind == "a..ab":
        s = "a" * (n - 1) + "b"
        rows = _queries(rng, n, q, span=1000)
    elif kind == "all a":
        s = "a" * n
        rows = _queries(rng, n, q, span=1000)
    else:                                       # periodic with a few mutations
        s = list(_periodic(rng, n, 6))
        for _ in range(20):
            s[rng.randrange(n)] = rng.choice("ab")
        s = "".join(s)
        rows = _queries(rng, n, q, span=5000) if rng.random() < 0.5 else _queries(rng, n, q)
    return _cmp_case(s, rows)


def _pair_test(pairs, pad):
    """Blocks X+Q and Y+Q for each (X, Y), and queries comparing them both ways.
    Q is three times as long as X, so a binary search on the prefix length first probes a
    length where X and Y are already fully inside: if their hashes collide, it is fooled."""
    s, rows, pos = [], [], 1
    for x, y in pairs:
        q = pad * (3 * max(len(x), 1))
        bx, by = x + q, y + q
        s.append(bx)
        s.append(by)
        px, py = pos, pos + len(bx)
        pos += len(bx) + len(by)
        rows.append(f"{px} {py} {len(bx)}")
        rows.append(f"{py} {px} {len(bx)}")
        rows.append(f"{px} {py} {len(x)}")
        rows.append(f"{px} {px} {len(bx)}")
    return _cmp_case("".join(s), rows)


def _thue_morse_test():
    """Thue-Morse block T (1024 letters) and its complement collide modulo 2^64 for EVERY
    odd base, in both hashing directions; appended text keeps them colliding."""
    t = _thue_morse(10)
    u = _flip(t)
    q1 = "a" * 3000
    p2, q2 = "b" * 300, "a" * 3000
    blocks = [t + q1, u + q1, p2 + t + q2, p2 + u + q2, t, u]
    starts, pos = [], 1
    for b in blocks:
        starts.append(pos)
        pos += len(b)
    x1, y1, x2, y2, pt, pu = starts
    rows = [f"{x1} {y1} {len(blocks[0])}", f"{y1} {x1} {len(blocks[0])}",
            f"{x2} {y2} {len(blocks[2])}", f"{y2} {x2} {len(blocks[2])}",
            f"{pt} {pu} 1024", f"{pu} {pt} 1024", f"{x1} {pt} 1024", f"{x1} {x1} {len(blocks[0])}"]
    return _cmp_case("".join(blocks), rows)


def _even_base_test():
    """With an even base, B^64 = 0 modulo 2^64: characters 64 or more places from the
    low-power end stop mattering."""
    e1, f1 = "b" + "a" * 300, "a" * 301
    e2, f2 = "a" * 300 + "b", "a" * 301
    s = e1 + f1 + e2 + f2
    p = [1, 1 + 301, 1 + 602, 1 + 903]
    rows = [f"{p[0]} {p[1]} 301", f"{p[1]} {p[0]} 301", f"{p[2]} {p[3]} 301",
            f"{p[3]} {p[2]} 301", f"{p[0]} {p[3]} 301"]
    return _cmp_case(s, rows)


# Pairs of 12-letter strings with equal polynomial hash for a popular fixed (base, mod):
# found by a birthday search in a fraction of a second, and checked for 'a' -> 97, 1, 0.
# Reversing a pair makes it collide for the other hashing direction (sum of c_i * B^i).
_FIXED_BASE_PAIRS = [
    ("wbjdjziweiag", "usbqqqykymtc"),   # 31, 10^9 + 7
    ("tnthgnvchdvv", "reskhsbzwbbs"),   # 37, 10^9 + 7
    ("dptzbysjjbzo", "cvddejjlidzb"),   # 53, 10^9 + 7
    ("eilygxlwkkyv", "hrlavgstqatu"),   # 131, 10^9 + 7
    ("ddcbgkzwqqsj", "xubyefqpssrm"),   # 137, 10^9 + 7
    ("wkdmgkrevzvr", "vqcyyqjljzcr"),   # 257, 10^9 + 7
    ("icyefpifvvkv", "cxhsymntmpmq"),   # 31, 10^9 + 9
    ("phwmjpegbmyr", "hzibgbqfvzia"),   # 37, 10^9 + 9
    ("fpfymwaxqswo", "gulbvdbjthpz"),   # 53, 10^9 + 9
    ("veormantssny", "ouslcwmcqivp"),   # 131, 10^9 + 9
    ("prsfemrntfns", "fpfxhuhbgxil"),   # 137, 10^9 + 9
    ("azjnvhgaphlj", "puqezaxlvjyf"),   # 257, 10^9 + 9
    ("ufnnmvesshmq", "jvmvyqpocwyz"),   # 31, 998244353
    ("qloscjzdixus", "ogyejlfkmapk"),   # 37, 998244353
    ("vgswuyauchgc", "prdmamnykstv"),   # 53, 998244353
    ("tgwhusmhjztx", "rdrgcycslszo"),   # 131, 998244353
    ("uhoxyodcnuit", "pocgylnpejsg"),   # 137, 998244353
    ("rouiewgkfcdd", "ocikoihasbum"),   # 257, 998244353
]


def _fixed_base_test():
    pairs = list(_FIXED_BASE_PAIRS) + [(x[::-1], y[::-1]) for x, y in _FIXED_BASE_PAIRS]
    return _pair_test(pairs, "z")


# --------------------------------------------------------------------- problems
STRING_MATCHING = Problem(
    id="string_matching",
    title="String Matching",
    difficulty="easy",
    source="CSES 1753 - String Matching",
    complexity="O(n + m)",
    statement=r"""
Given a text and a pattern, count the positions where the pattern occurs in the text.
Occurrences may overlap.
""",
    input=r"""
The first line has the text, the second the pattern. Both consist of lowercase letters,
with lengths `n` and `m` (1 ≤ n, m ≤ 10^6).
""",
    output=r"""
Print the number of occurrences.
""",
    samples=[
        Test("saippuakauppias\npp\n", "2\n"),
        Test("aaaaa\naa\n", "4\n", note="Occurrences overlap: they start at positions 1, 2, 3 and 4."),
    ],
    tests=[
        Test("ab\nabc\n"),
        Test("a\na\n"),
        Test("abababab\naba\n"),
        Test("abcabcabd\nabcabd\n"),
    ],
    gens=[
        Gen("small random", _sm_small, 14),
        Gen("medium periodic", _sm_medium, 3),
        Gen("a^n against a^(m-1)b", lambda rng: "a" * 10**6 + "\n" + "a" * (5 * 10**5 - 1) + "b\n", 1, large=True),
        Gen("a^n against a^m", lambda rng: "a" * 10**6 + "\n" + "a" * (5 * 10**5) + "\n", 1, large=True),
        Gen("periodic text and pattern", lambda rng: "ab" * (5 * 10**5) + "\n" + "ab" * 150000 + "a\n", 1, large=True),
        Gen("random a/b text, short pattern", lambda rng: _rand_ab(rng, 10**6) + "\n" + _rand_ab(rng, 12) + "\n", 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// pi[i] = length of the longest proper border of s[0..i]
vector<int> prefix_function(const string& s) {
    int n = s.size();
    vector<int> pi(n, 0);
    for (int i = 1; i < n; i++) {
        int k = pi[i - 1];                       // longest border of s[0..i-1]
        while (k > 0 && s[i] != s[k]) k = pi[k - 1];   // next shorter border
        if (s[i] == s[k]) k++;                   // extend it by s[i]
        pi[i] = k;
    }
    return pi;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string text, pat;
    cin >> text >> pat;
    int m = pat.size();
    // '#' occurs in neither string, so no border can reach across it: pi <= m
    vector<int> pi = prefix_function(pat + '#' + text);
    long long count = 0;
    for (int i = 2 * m; i < (int)pi.size(); i++)
        if (pi[i] == m) count++;                 // the pattern ends at this position
    cout << count << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string t, p;
    cin >> t >> p;
    int n = t.size(), m = p.size(), c = 0;
    for (int i = 0; i + m <= n; i++) {
        int j = 0;
        while (j < m && t[i + j] == p[j]) j++;
        if (j == m) c++;
    }
    cout << c << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string t, p;
    cin >> t >> p;
    int n = t.size(), m = p.size();
    long long c = 0;
    for (int i = 0; i + m <= n; i++) {          // every start, compared from scratch
        int j = 0;
        while (j < m && t[i + j] == p[j]) j++;
        if (j == m) c++;
    }
    cout << c << '\n';
}
""",
    hints=[
        r"""After a mismatch, the characters you just matched are known: they equal a prefix of
the pattern. Which shift could still work, judging from the pattern alone?""",
        r"""Compute the prefix function of `pattern + '#' + text`. The pattern ends wherever the
value equals `m`.""",
    ],
    editorial=r"""
The naive matcher compares the pattern at every start and forgets everything after a
mismatch, so on `aaa...a` against `aa...ab` it costs (n − m + 1)·m ≈ 2.5·10^11
comparisons. `string::find` is no different: measured here it takes 4.7 s on that input.

The prefix function π[i] is the length of the longest proper border (prefix that is also a
suffix) of `s[0..i]`. Computing it for `s = pattern + '#' + text` finds every occurrence:
π[i] = m exactly when the last `m` characters before `i` spell the pattern. The `'#'`
matters: no border can contain it, so π never exceeds `m` and no match straddles the
boundary.

The computation is O(n + m): the candidate `k` rises by at most 1 per character and every
step of the inner `while` lowers it, so the total number of inner steps is at most the
total number of rises.
""",
)

FINDING_BORDERS = Problem(
    id="finding_borders",
    title="Finding Borders",
    difficulty="easy",
    source="CSES 1732 - Finding Borders",
    complexity="O(n)",
    statement=r"""
A border of a string is a prefix that is also a suffix, but not the whole string. For
example, the borders of `abcababcab` are `ab` and `abcab`.

Find the lengths of all borders of a given string.
""",
    input=r"""
One line with a string of `n` lowercase letters (1 ≤ n ≤ 10^6).
""",
    output=r"""
Print the lengths of all borders in increasing order, separated by spaces. If there are
none, print nothing (an empty line is fine).
""",
    samples=[
        Test("abcababcab\n", "2 5\n"),
        Test("aaaa\n", "1 2 3\n"),
    ],
    tests=[
        Test("a\n"),
        Test("abc\n"),
        Test("abacaba\n"),
        Test("abab\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _one_string(_rand_ab(rng, rng.randint(1, 12))), 14),
        Gen("medium periodic", lambda rng: _one_string(_periodic(rng, 3000, 5)), 3),
        Gen("all equal letters", lambda rng: _one_string("a" * 10**6), 1, large=True),
        Gen("periodic, block of 7", lambda rng: _one_string(_periodic(rng, 10**6, 7)), 1, large=True),
        Gen("Fibonacci word", lambda rng: _one_string(_fib_word(10**6)), 1, large=True),
        Gen("random a/b", lambda rng: _one_string(_rand_ab(rng, 10**6)), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    int n = s.size();
    vector<int> pi(n, 0);
    for (int i = 1; i < n; i++) {
        int k = pi[i - 1];
        while (k > 0 && s[i] != s[k]) k = pi[k - 1];
        if (s[i] == s[k]) k++;
        pi[i] = k;
    }
    // the borders of s: its longest border, the longest border of that, and so on
    vector<int> borders;
    for (int k = pi[n - 1]; k > 0; k = pi[k - 1]) borders.push_back(k);
    reverse(borders.begin(), borders.end());
    string out;
    for (int b : borders) out += to_string(b) + ' ';
    cout << out << '\n';
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
    for (int L = 1; L < n; L++)
        if (s.substr(0, L) == s.substr(n - L)) cout << L << ' ';
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
    int n = s.size();
    string out;
    for (int L = 1; L < n; L++)                       // compare prefix and suffix directly
        if (s.compare(0, L, s, n - L, L) == 0) out += to_string(L) + ' ';
    cout << out << '\n';
}
""",
    hints=[
        r"""The prefix function of the whole string gives the longest border, π[n−1]. What is the
second-longest border?""",
        r"""A border of a border is a border. Follow `k = pi[n-1]`, then `k = pi[k-1]`, until 0,
and print in reverse.""",
    ],
    editorial=r"""
Checking every length directly costs Σ L = n^2/2 = 5·10^11 on a string of equal letters.
Instead: the longest border is π[n−1]. Every shorter border of `s` is also a border of
that longest border (both are prefixes and suffixes of `s`, and the shorter one sits
inside the longer), so the second-longest is π[π[n−1] − 1], and so on down to 0. The
chain visits exactly the borders, in decreasing order. O(n) for π plus the length of the
output.

The same chain gives the periods: `s` has period `p` (s[i] = s[i+p] for every valid `i`)
exactly when it has a border of length n − p.
""",
)

PREFIX_OCCURRENCES = Problem(
    id="prefix_occurrences",
    title="Prefixes and Suffixes",
    difficulty="medium",
    source="Codeforces 432D - Prefixes and Suffixes",
    complexity="O(n)",
    statement=r"""
For every prefix of the string `s` that is also a suffix of `s` (including `s` itself),
count how many times it occurs in `s` as a substring. Occurrences may overlap.
""",
    input=r"""
One line with a string `s` of `n` lowercase letters (1 ≤ n ≤ 10^6).
""",
    output=r"""
On the first line print `k`, the number of prefixes that are also suffixes. Then print `k`
lines, in increasing order of length: the length `l` of such a prefix and the number of
its occurrences in `s`.
""",
    samples=[
        Test("abacaba\n", "3\n1 4\n3 2\n7 1\n"),
        Test("aaa\n", "3\n1 3\n2 2\n3 1\n"),
    ],
    tests=[
        Test("a\n"),
        Test("ab\n"),
        Test("abab\n"),
        Test("aabaa\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _one_string(_rand_ab(rng, rng.randint(1, 12))), 14),
        Gen("medium periodic", lambda rng: _one_string(_periodic(rng, 300, 4)), 3),
        Gen("all equal letters", lambda rng: _one_string("a" * 10**6), 1, large=True),
        Gen("abab...", lambda rng: _one_string("ab" * (5 * 10**5)), 1, large=True),
        Gen("Fibonacci word", lambda rng: _one_string(_fib_word(10**6)), 1, large=True),
        Gen("periodic, block of 5", lambda rng: _one_string(_periodic(rng, 10**6, 5)), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// z[i] = length of the longest common prefix of s and s[i..]; z[0] = n by convention
vector<int> z_function(const string& s) {
    int n = s.size();
    vector<int> z(n, 0);
    z[0] = n;
    for (int i = 1, l = 0, r = 0; i < n; i++) {     // [l, r) matches the prefix s[0..r-l)
        if (i < r) z[i] = min(r - i, z[i - l]);     // free information from the window
        while (i + z[i] < n && s[z[i]] == s[i + z[i]]) z[i]++;
        if (i + z[i] > r) { l = i; r = i + z[i]; }  // r only moves right: O(n) in total
    }
    return z;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    int n = s.size();
    vector<int> z = z_function(s);
    // the prefix of length L occurs at position i exactly when z[i] >= L
    vector<long long> atLeast(n + 2, 0);
    for (int i = 0; i < n; i++) atLeast[z[i]]++;
    for (int L = n - 1; L >= 1; L--) atLeast[L] += atLeast[L + 1];
    // the prefix of length L is a suffix exactly when z[n - L] == L
    vector<int> good;
    for (int L = 1; L <= n; L++)
        if (z[n - L] == L) good.push_back(L);
    string out = to_string(good.size()) + '\n';
    for (int L : good) out += to_string(L) + ' ' + to_string(atLeast[L]) + '\n';
    cout << out;
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
    vector<pair<int, int>> res;
    for (int L = 1; L <= n; L++) {
        if (s.substr(0, L) != s.substr(n - L)) continue;
        int c = 0;
        for (int i = 0; i + L <= n; i++) if (s.substr(i, L) == s.substr(0, L)) c++;
        res.push_back({L, c});
    }
    cout << res.size() << '\n';
    for (auto [L, c] : res) cout << L << ' ' << c << '\n';
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
    vector<int> z(n, 0);
    z[0] = n;
    for (int i = 1, l = 0, r = 0; i < n; i++) {
        if (i < r) z[i] = min(r - i, z[i - l]);
        while (i + z[i] < n && s[z[i]] == s[i + z[i]]) z[i]++;
        if (i + z[i] > r) { l = i; r = i + z[i]; }
    }
    string out;
    int k = 0;
    for (int L = 1; L <= n; L++) {
        if (z[n - L] != L) continue;
        long long c = 0;
        for (int i = 0; i < n; i++) c += z[i] >= L;    // a full scan for every border
        out += to_string(L) + ' ' + to_string(c) + '\n';
        k++;
    }
    cout << k << '\n' << out;
}
""",
    hints=[
        r"""With the Z-function: the prefix of length `L` occurs at position `i` exactly when
`z[i] >= L`, and it is also a suffix exactly when `z[n-L] == L`.""",
        r"""Counting `z[i] >= L` separately for every border is O(n) per border, and `aaa...a` has
`n` borders. Count how many positions have each z-value, then take suffix sums.""",
    ],
    editorial=r"""
Compute the Z-function, with the convention z[0] = n. The prefix of length `L` is also a
suffix exactly when the suffix starting at n − L matches the prefix all the way to the
end: z[n − L] = L. It occurs at position `i` exactly when z[i] ≥ L. So count
`cnt[v]` = number of positions with z-value `v`, and take suffix sums: `atLeast[L]` =
Σ_(v ≥ L) cnt[v]. O(n) in total.

The trap is recounting for each border separately: a string of equal letters has `n`
borders, and a full scan per border is n^2 = 10^12. The output of that test is itself
10^6 lines, so build it in a string (or use `'\n'`, never `endl`).

The prefix function solves it too: count the positions where each π-value occurs, then
push counts down the border chain, `cnt[pi[L−1]] += cnt[L]`, from long to short.
""",
)

SUBSTRING_COMPARE = Problem(
    id="substring_compare",
    title="Substring Comparisons",
    difficulty="hard",
    complexity="O(n + q log n)",
    statement=r"""
You are given a string `s` and `q` questions. Each question gives two starting positions
`a` and `b` and a length `len`, and asks how the substring of length `len` starting at `a`
compares, lexicographically, with the substring of length `len` starting at `b`.
""",
    input=r"""
The first line has `s`, a string of `n` lowercase letters (1 ≤ n ≤ 10^6). The second line
has `q` (1 ≤ q ≤ 3·10^5). Each of the next `q` lines has three integers `a b len`
(1 ≤ len, 1 ≤ a, b and a + len − 1 ≤ n, b + len − 1 ≤ n). Positions are 1-based.
""",
    output=r"""
For each question print one character on its own line: `<` if the substring at `a` is
smaller, `=` if the two are equal, `>` if it is larger.
""",
    samples=[
        Test("abracadabra\n4\n1 8 4\n1 4 2\n2 9 3\n5 4 1\n", "=\n<\n=\n>\n"),
    ],
    tests=[
        Test("a\n1\n1 1 1\n"),
        Test("ab\n3\n1 2 1\n2 1 1\n1 1 2\n"),
        Test("aaaaaaaaab\n3\n1 2 9\n2 1 9\n1 1 10\n"),
        Test(_thue_morse_test()),
        Test(_even_base_test()),
        Test(_fixed_base_test()),
    ],
    gens=[
        Gen("small random", _cmp_small, 14),
        Gen("medium periodic", _cmp_medium, 2),
        Gen("a...ab, long ranges", lambda rng: _cmp_large(rng, "a..ab"), 1, large=True),
        Gen("all a, long ranges", lambda rng: _cmp_large(rng, "all a"), 1, large=True),
        Gen("periodic with mutations", lambda rng: _cmp_large(rng, "periodic"), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

typedef unsigned long long ull;
const ull MOD = (1ULL << 61) - 1;                 // a prime

ull mulmod(ull a, ull b) {                        // a, b < MOD
    __uint128_t p = (__uint128_t)a * b;
    ull r = (ull)(p & MOD) + (ull)(p >> 61);      // 2^61 ≡ 1 (mod 2^61 - 1)
    return r >= MOD ? r - MOD : r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    int n = s.size();
    // a base chosen at run time: no test written in advance can target it
    mt19937_64 rng(chrono::steady_clock::now().time_since_epoch().count());
    ull B = rng() % (MOD - 1000) + 500;
    vector<ull> h(n + 1, 0), pw(n + 1, 1);        // h[i] = hash of s[0..i)
    for (int i = 0; i < n; i++) {
        h[i + 1] = (mulmod(h[i], B) + (ull)s[i]) % MOD;
        pw[i + 1] = mulmod(pw[i], B);
    }
    auto get = [&](int l, int len) {              // hash of s[l..l+len)
        ull x = h[l + len] + MOD - mulmod(h[l], pw[len]);
        return x >= MOD ? x - MOD : x;
    };
    int q;
    cin >> q;
    string out;
    out.reserve(2 * q);
    while (q--) {
        int a, b, len;
        cin >> a >> b >> len;
        a--, b--;
        int lo = 0, hi = len;                     // longest common prefix, by binary search
        while (lo < hi) {
            int mid = (lo + hi + 1) / 2;
            if (get(a, mid) == get(b, mid)) lo = mid;
            else hi = mid - 1;
        }
        out += lo == len ? '=' : (s[a + lo] < s[b + lo] ? '<' : '>');
        out += '\n';
    }
    cout << out;
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s;
    cin >> s;
    int q;
    cin >> q;
    while (q--) {
        int a, b, len;
        cin >> a >> b >> len;
        a--, b--;
        char c = '=';
        for (int k = 0; k < len; k++)
            if (s[a + k] != s[b + k]) { c = s[a + k] < s[b + k] ? '<' : '>'; break; }
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
    string s;
    cin >> s;
    int q;
    cin >> q;
    string out;
    while (q--) {
        int a, b, len;
        cin >> a >> b >> len;
        int c = s.compare(a - 1, len, s, b - 1, len);   // memcmp: fast, but O(len)
        out += c < 0 ? '<' : (c > 0 ? '>' : '=');
        out += '\n';
    }
    cout << out;
}
""",
    hints=[
        r"""With prefix hashes, the hash of any substring costs O(1). Equal prefixes of the two
substrings are monotone in the length: binary search the longest common prefix, then
compare the next character.""",
        r"""Hash modulo 2^61 − 1 with a base chosen at random when the program starts (multiply
with `__int128`). The hidden tests include strings that collide for natural `unsigned long
long` overflow with any base, and for several popular fixed bases modulo 10^9 + 7,
10^9 + 9 and 998244353.""",
    ],
    editorial=r"""
Precompute `h[i]`, the polynomial hash of `s[0..i)`, and the powers of the base. The hash
of `s[l..l+len)` is `h[l+len] − h[l]·B^len`, in O(1). To compare two substrings, binary
search the length of their longest common prefix (prefix equality is monotone: if the
first `L` characters agree, so do the first `L − 1`), then compare the first differing
character. O(n + q log n); comparing character by character is up to 3·10^11 steps.

The modulus and base decide whether this is correct:

- Natural overflow (`unsigned long long`, i.e. modulo 2^64) fails for **every** base. For
  an even base, B^64 ≡ 0, so all but the last 64 characters vanish. For an odd base, the
  Thue-Morse string T of length 1024 and its complement have hash difference
  ±Π_(j<10)(B^(2^j) − 1), and that product is always divisible by 2^64. One hidden test is
  exactly this.
- A fixed base with a modulus near 10^9 falls to a birthday search: about 4·10^4 random
  12-letter strings contain a colliding pair, found in a fraction of a second. The hidden
  tests contain such pairs for bases 31, 37, 53, 131, 137 and 257 with the three popular
  moduli, in both hashing directions.
- Modulo the prime 2^61 − 1 with a random base, two different strings of length `L`
  collide with probability at most (L − 1)/(2^61 − 1) ≈ 4·10^(−13) here, whatever the
  tests are, because the base did not exist when they were written.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo19",
    title="strings I: hashing, prefix function, Z-function",
    track="algo",
    order=19,
    summary="Stop re-reading the text: the prefix function and KMP, borders and periods, the "
            "Z-function, and polynomial hashing with an honest look at collisions and the "
            "tests built to cause them.",
    prereqs=["algo01", "cpp10"],
    tags=["strings", "kmp", "prefix function", "z-function", "borders", "periods", "hashing",
          "anti-hash", "binary search"],
    parts=[
        Part("What the naive matcher forgets", [
            Say(r"""
**String Matching.** Count the occurrences of a pattern of length `m` in a text of length
`n`, both up to 10^6 characters.

The obvious program tries every start position `i` and compares `text[i + j]` with
`pattern[j]` for `j = 0, 1, ...` until a mismatch or the end of the pattern.
"""),
            Numeric(r"""
Worst case: the text is 10^6 letters `a`, and the pattern is 5·10^5 − 1 letters `a`
followed by one `b`. Every start matches almost the whole pattern before failing. How
many character comparisons is that?
""", answer=2.5e11, rel=0.5, unit="comparisons",
                explain=r"""
About (n − m + 1)·m ≈ 5·10^5 · 5·10^5 = 2.5·10^11. Measured here: 20 seconds.
"""),
            MCQ(r"""
Does `text.find(pattern, pos)` in a loop rescue you?
""", [
                Opt("Yes: the standard library uses a linear-time algorithm like KMP.",
                    why="libstdc++'s `find` looks for the first character with `memchr` and then "
                        "compares; its worst case is still O(n·m). The standard makes no "
                        "linear-time promise."),
                Opt("No: it is the same O(n·m) search with a faster inner loop. Measured on "
                    "that input: 4.7 seconds.", correct=True,
                    why="Right. Vectorised comparisons buy a factor of 4 or so; the algorithm "
                        "still does 2.5·10^11 character checks, and judges include this test."),
                Opt("Yes, because it is written in optimised assembly.",
                    why="Constant factors do not beat a quadratic count. A factor of 4 against "
                        "a factor of 250,000."),
            ]),
            Reflect(r"""
Pattern `abcabd`, text `abcabcabd`. At start 0 the first five characters match (`abcab`),
then the text has `c` where the pattern has `d`. The naive matcher moves to start 1 and
compares from scratch. But what do you already know about `text[0..4]`? Using only that,
which of the starts 1, 2, 3, 4 could possibly work, and how many characters would already
be known to match?
""", answer=r"""
`text[0..4]` is exactly `abcab`, the matched part of the pattern, so the text never needs
to be re-read. Start `s` can only work if the pattern's first 5 − s characters equal the
last 5 − s characters of `abcab`: a prefix of `abcab` that is also a suffix. `bcab`, `cab`
fail; `ab` works. So skip straight to start 3 with 2 characters already matched, and
continue comparing at the same text position. Nothing is re-read, and the shift depends
only on the pattern, so it can be precomputed.
"""),
            Short(r"""
A **border** of a string is a proper prefix that is also a suffix. What is the longest
border of `abcab`?
""", accept=["ab"], placeholder="a string",
                explain=r"""
`ab`. The longest border of what has been matched is exactly how much of the match to
keep after a mismatch. Precompute it for every prefix of the pattern and the text is
read once.
"""),
        ]),
        Part("The prefix function", [
            Say(r"""
The **prefix function** of a string `s` is the array π with π[i] = the length of the
longest border of `s[0..i]` (the prefix ending at `i`). The empty border counts, so
π[0] = 0.
"""),
            Short(r"""
Compute π for `abacaba`. Write the seven numbers separated by spaces.
""", accept=["0 0 1 0 1 2 3", "0,0,1,0,1,2,3", "0, 0, 1, 0, 1, 2, 3"], placeholder="seven numbers",
                hint="For each prefix: a, ab, aba, abac, abaca, abacab, abacaba.",
                explain=r"""
`0 0 1 0 1 2 3`. For instance `abacab` has the border `ab` (2), and `abacaba` has `aba`
(3). Notice how π[i] ≤ π[i−1] + 1: a border can grow by at most one character per step.
"""),
            MCQ(r"""
To compute π[i] you try to extend a border of `s[0..i−1]` by `s[i]`: first the longest,
π[i−1]; if `s[i]` does not fit, the next shorter border, and so on. How long is the
second-longest border of a string whose longest border has length `k`?
""", [
                Opt("`k − 1`.",
                    why="Borders do not shrink one character at a time. `abab` has the border "
                        "`ab` (length 2), but `a` (length 1) is not a border: the string ends "
                        "with `b`."),
                Opt("π[k − 1]: the longest border of the longest border.", correct=True,
                    why="Yes. A shorter border of `s` is a prefix of `s`, hence a prefix of the "
                        "longest border, and a suffix of `s`, hence a suffix of the longest "
                        "border. So the borders of `s` are the longest one, then its borders."),
                Opt("`k / 2`.",
                    why="There is no such rule: `aaaa` has borders 3, 2 and 1."),
            ], explain=r"""
So the candidates are `k = π[i−1]`, then `π[k−1]`, then `π[π[k−1]−1]`, ... all already
computed. That gives the whole algorithm:

```cpp
vector<int> pi(n, 0);
for (int i = 1; i < n; i++) {
    int k = pi[i - 1];
    while (k > 0 && s[i] != s[k]) k = pi[k - 1];
    if (s[i] == s[k]) k++;
    pi[i] = k;
}
```
"""),
            MCQ(r"""
For one `i`, the `while` loop can run many times. Why is the whole computation still
O(n)?
""", [
                Opt("Borders are short, so the loop runs O(1) times on average.",
                    why="On `aaaa...ab` the last step alone walks down a chain of length n − 1. "
                        "The bound has to be amortised, not per step."),
                Opt("`k` goes up by at most 1 per character, and every `while` step lowers it. "
                    "It never goes below 0, so the total number of `while` steps is at most n.",
                    correct=True,
                    why="Right: a potential argument. Total decreases ≤ total increases ≤ n, the "
                        "same bookkeeping as two pointers (algo04)."),
                Opt("It is O(n log n), because the chain halves each time.",
                    why="The chain need not halve (`aaaa` goes 3, 2, 1), and the bound is linear."),
            ]),
            MCQ(r"""
To find the pattern `p` (length `m`) in the text `t`, compute π of `p + '#' + t` and count
the positions with π = m. What goes wrong without the `'#'`?
""", [
                Opt("Nothing; the separator is only cosmetic.",
                    why="Take `p = aa`, `t = aaa` (two occurrences). π of `aaaaa` is 0 1 2 3 4: "
                        "the only 2 marks a fake match made of one `a` from `p` and one from `t`, "
                        "and the two real occurrences have π = 3 and 4."),
                Opt("Borders can reach across the boundary: π can exceed `m`, and `π == m` then "
                    "misses real occurrences.", correct=True,
                    why="Yes. The `#` occurs once. A border longer than `m` would contain it in "
                        "its prefix copy, and its suffix copy would need a second `#`. So π ≤ m "
                        "everywhere, and π = m means exactly an occurrence of `p` inside `t`."),
                Opt("It becomes O(n·m).",
                    why="The running time is the same; the answers are wrong."),
            ]),
            Try("string_matching", note="Prefix function of `pattern + '#' + text`. A hidden test is "
                "the `aaa...a` / `aa...ab` worst case."),
        ]),
        Part("Borders and periods", [
            Say(r"""
**Finding Borders.** Print the lengths of all borders of a string of length up to 10^6.
The direct approach tests every length `L` with one prefix-against-suffix comparison.
"""),
            Numeric(r"""
On a string of 10^6 equal letters every comparison runs to the end. How many character
comparisons in total?
""", answer=5e11, rel=0.5, unit="comparisons",
                explain=r"""
1 + 2 + ... + (n − 1) ≈ n^2/2 = 5·10^11.
"""),
            Short(r"""
With π of `abacaba` = `0 0 1 0 1 2 3`, list its borders by following the chain from
π[6]. Write the lengths in increasing order.
""", accept=["1 3", "1, 3", "1,3"], placeholder="lengths separated by spaces",
                hint="π[6] = 3; then look at π[3 − 1].",
                explain=r"""
π[6] = 3 (`aba`), then π[2] = 1 (`a`), then π[0] = 0: stop. Borders 1 and 3. The chain
from π[n−1] visits exactly the borders, longest first.
"""),
            MCQ(r"""
A string `s` of length `n` has **period** `p` if `s[i] = s[i + p]` for every `i` with
`i + p < n` (so `abcabcab` has period 3). If `s` has a border of length `b`, which period
does it have?
""", [
                Opt("`b`", why="`abacaba` has the border `a` (b = 1), but it does not have period 1."),
                Opt("`n − b`", correct=True,
                    why="Yes. A border of length `b` says `s[0..b)` = `s[n−b..n)`, which is "
                        "exactly `s[i] = s[i + (n − b)]` for all `i < b`. And conversely: "
                        "periods and borders are two views of the same fact."),
                Opt("`n / b`", why="Periods need not divide `n`: `abcabcab` (n = 8) has period 3."),
            ]),
            Numeric(r"""
π of `abcabcab` ends in 5 (the border `abcab`). What is its smallest period?
""", answer=3,
                explain=r"""
8 − 5 = 3. The longest border gives the smallest period, and the whole border chain gives
all the periods.
"""),
            Try("finding_borders", note="One prefix function and the chain. The output can have "
                "10^6 numbers: build it in a string."),
        ]),
        Part("The Z-function", [
            Say(r"""
A second array answers a slightly different question. The **Z-function** of `s` is
z[i] = the length of the longest common prefix of `s` and the suffix `s[i..]` (z[0] is
set to `n` or 0 by convention).

**Prefixes and Suffixes.** For each prefix of `s` that is also a suffix, count its
occurrences in `s`, for `n` up to 10^6.
"""),
            Short(r"""
Compute z[1..6] for `aabxaab`. Write six numbers separated by spaces.
""", accept=["1 0 0 3 1 0", "1,0,0,3,1,0", "1, 0, 0, 3, 1, 0"], placeholder="six numbers",
                explain=r"""
`1 0 0 3 1 0`: `abxaab` shares `a` with the start, `bxaab` and `xaab` share nothing, `aab`
matches `aab` and then the string ends, `ab` shares `a`, `b` nothing.
"""),
            Reflect(r"""
Computing each z[i] by direct comparison is O(n^2) on `aaa...a`. Suppose the algorithm
remembers the window `[l, r)` found so far with `s[l..r) = s[0..r−l)`, and now `i` is
inside it (`l < i < r`). What does the window tell you about z[i] before comparing a
single character?
""", answer=r"""
Inside the window, `s[i..r)` is a copy of `s[i−l..r−l)`, whose match with the prefix is
already known: z[i−l]. So z[i] ≥ min(z[i−l], r − i) for free. If z[i−l] < r − i the
answer is exactly z[i−l], because the copy stops matching strictly inside the window.
Only when the copy reaches the window's end do you compare characters beyond `r`, and
every successful comparison there moves `r` to the right. `r` only increases, so the total
is O(n). This is the same idea as the prefix function: never re-read a character you
already matched.
"""),
            MCQ(r"""
In `aabxaab` the window after `i = 4` is `[4, 7)`, matching the prefix `aab`. At `i = 5`,
`i − l = 1` and z[1] = 1. What happens?
""", [
                Opt("z[5] = 1 immediately: 1 < r − i = 2, so the copy stops inside the window.",
                    correct=True,
                    why="Right: no comparisons at all. The window already contains `ab` = a copy "
                        "of `s[1..3)`, which matches the prefix for exactly one character."),
                Opt("z[5] ≥ 1, and the algorithm compares characters from position 6 on.",
                    why="It only extends when min(z[i−l], r − i) reaches the window's end. Here "
                        "z[1] = 1 < 2, so the value is final."),
                Opt("z[5] = 2 = r − i.",
                    why="`s[5..7) = ab` and `s[0..2) = aa` differ at the second character."),
            ], explain=r"""
In code:

```cpp
vector<int> z(n, 0);
for (int i = 1, l = 0, r = 0; i < n; i++) {
    if (i < r) z[i] = min(r - i, z[i - l]);
    while (i + z[i] < n && s[z[i]] == s[i + z[i]]) z[i]++;
    if (i + z[i] > r) { l = i; r = i + z[i]; }
}
```
"""),
            MCQ(r"""
Back to the problem. With the Z-function (and z[0] = n), how do you get the number of
occurrences of the prefix of length `L`?
""", [
                Opt("z[L].",
                    why="z[L] is about the single position `L`: how far the suffix starting there "
                        "matches the prefix."),
                Opt("The number of positions `i` with z[i] ≥ L.", correct=True,
                    why="Yes: the prefix of length `L` starts at `i` exactly when the match there "
                        "is at least `L` long. Count each z-value once and take suffix sums, and "
                        "every `L` is answered in O(1)."),
                Opt("The number of positions `i` with z[i] = L.",
                    why="An occurrence can continue matching beyond `L`: in `aaa` the prefix `a` "
                        "occurs at all three positions, where z = 3, 2, 1."),
            ], explain=r"""
And the prefix of length `L` is also a suffix exactly when z[n − L] = L: the match
starting at `n − L` runs to the end of the string.
"""),
            Try("prefix_occurrences", note="Z-function, a count per z-value, suffix sums. The "
                "`aaa...a` test has 10^6 borders."),
        ]),
        Part("Hashing: comparing substrings in O(1)", [
            Say(r"""
**Substring Comparisons.** A string of length up to 10^6 and `q ≤ 3·10^5` questions: how
does the substring of length `len` at `a` compare with the one at `b`? The direct way
compares character by character.
"""),
            Numeric(r"""
With both substrings about 10^6 long and equal almost to the end, how many character
comparisons do the questions cost in total?
""", answer=3e11, rel=0.5, unit="comparisons",
                explain=r"""
3·10^5 · 10^6 = 3·10^11. Even `memcmp` speed does not save that: measured, 5 to 7
seconds.
"""),
            Reflect(r"""
algo01 answered any range *sum* in O(1) with prefix sums. Suppose you fingerprint a
substring by the sum of its letter codes, taken from a prefix-sum array: equal substrings
get equal sums. What is wrong with this fingerprint, and what would you change so that it
also depends on the *order* of the letters?
""", answer=r"""
A sum forgets the order: `ab` and `ba` get the same fingerprint, and so do all anagrams.
Weight each letter by its position instead, the way digits are weighted in a number:
`s[0]·B^(L−1) + s[1]·B^(L−2) + ... + s[L−1]` for some base `B`, reduced modulo `M` so it
fits in a machine word. That is a **polynomial hash**, and like a prefix sum it can be
computed for every prefix in one pass and "subtracted" to get any substring.
"""),
            Say(r"""
Precompute the hash of every prefix: read the string as a number in base `B`, reduced
modulo `M`:

```
h[0] = 0,   h[i+1] = (h[i] * B + s[i]) mod M      // h[i] = hash of s[0..i)
```

With `B = 10` and digits instead of letters, `h[i]` is literally the number written by
the first `i` digits.
"""),
            Short(r"""
Take `s = 31415`, `B = 10` (and `M` huge), so `h = 0, 3, 31, 314, 3141, 31415`. The
substring `s[1..4)` is `141`. What is `h[4] − h[1] · 10^3`?
""", accept=["141"], placeholder="a number",
                explain=r"""
`3141 − 3000 = 141`: shifting the prefix `3` three places left lines it up with the first
digit of `3141`, and subtracting leaves exactly the digits of `s[1..4)`. In general the
hash of `s[l..r)` is `h[r] − h[l] · B^(r−l)` (mod M), with the powers of `B` precomputed.
"""),
            MCQ(r"""
Two substrings have equal hashes. What can you conclude?
""", [
                Opt("They are equal.",
                    why="There are 26^20 strings of length 20 and only `M` possible hashes: "
                        "different strings must share hashes. Equality is only *probable*."),
                Opt("They are probably equal; different hashes, on the other hand, prove they "
                    "differ.", correct=True,
                    why="Right. Hashing has one-sided error: a mismatch is certain, a match is a "
                        "bet. The rest of the lesson is about making that bet safe."),
                Opt("Nothing at all.",
                    why="Equal strings always have equal hashes, and with a good modulus and base "
                        "a collision is very unlikely."),
            ]),
            MCQ(r"""
To compare two substrings of length `len`, you binary search the length of their longest
common prefix using hash equality, then compare the next character. Why is binary search
allowed here?
""", [
                Opt("Because the string is sorted.",
                    why="Nothing is sorted. What must be monotone is the predicate being searched."),
                Opt("\"The first `L` characters agree\" is monotone in `L`: true up to the LCP, false "
                    "after it.", correct=True,
                    why="Yes: if the first `L` agree, so do the first `L − 1`. That is all binary "
                        "search on the answer needs (algo03). log2(10^6) = 20 hash comparisons "
                        "per question."),
                Opt("Because hashes are ordered like the strings.",
                    why="They are not: a hash says nothing about lexicographic order. That is "
                        "why you look at the first differing *character* at the end."),
            ]),
        ]),
        Part("Collisions, birthdays and adversaries", [
            Say(r"""
How likely is a collision? Two situations behave very differently.

If you put many hashes into a set (say, to count distinct substrings), every *pair* is a
chance to collide. With `k` random values modulo `M`, the expected number of colliding
pairs is about k^2 / (2M): the **birthday** effect.
"""),
            Numeric(r"""
You store the hashes of 10^5 different strings, modulo 10^9 + 7. About how many colliding
pairs do you expect?
""", answer=5, rel=0.5, unit="pairs",
                hint="k^2 / (2M) with k = 10^5 and M ≈ 10^9.",
                explain=r"""
10^10 / (2·10^9) = 5. A collision is practically certain, and the program prints one
distinct string too few. With `M = 2^61 − 1 ≈ 2.3·10^18` the same count is about
2·10^(−9). This is why contest hashing uses a 61-bit prime modulus (or two ~30-bit ones).
"""),
            MCQ(r"""
Now a single comparison of two *fixed* different strings of length `L`, with the base `B`
chosen uniformly at random modulo a prime `M`. Why is a collision unlikely?
""", [
                Opt("Because hash values look random.",
                    why="Hashes are not random; for a fixed base they are completely determined, "
                        "and an adversary can compute them too."),
                Opt("hash(x) − hash(y) is a non-zero polynomial in `B` of degree at most L − 1, and "
                    "such a polynomial has at most L − 1 roots modulo a prime. So "
                    "P(collision) ≤ (L − 1)/M.", correct=True,
                    why="Right. The randomness is in `B`, not in the strings. With L = 10^6 and "
                        "M = 2^61 − 1 that is below 5·10^(−13) per comparison, for *any* test "
                        "data."),
                Opt("Because `M` is larger than the number of strings compared.",
                    why="Size alone does not help if the base is fixed and known: then colliding "
                        "strings can be searched for in advance."),
            ]),
            Say(r"""
That bound needs two things: a **prime** modulus, and a base the test author could not
know. Popular fixed choices fail the second: for base 31 modulo 10^9 + 7, about 4·10^4
random 12-letter strings contain two with equal hashes (the birthday effect again), and
finding such a pair took 0.08 s for eighteen popular (base, modulus) pairs at once. This
lesson's hidden tests contain those pairs.

And `unsigned long long` arithmetic (modulo 2^64, "free" overflow) fails the first: 2^64
is not prime.
"""),
            Numeric(r"""
Start small. For an odd base `B`, `B^2 − 1 = (B − 1)(B + 1)`. What is the largest power of
2 that divides B^2 − 1 for *every* odd `B`?
""", answer=8,
                hint="B − 1 and B + 1 are consecutive even numbers.",
                explain=r"""
8: of two consecutive even numbers, one is divisible by 4. Likewise B^4 − 1 = (B^2 − 1)(B^2 + 1)
gains another factor 2, and so on: for j ≥ 1, B^(2^j) − 1 is divisible by 2^(j+2). The
Thue-Morse string T of length 2^k (a, ab, abba, abbabaab, ..., each step appends the
complement) and its complement have hash difference ±Π_(j<k)(B^(2^j) − 1). The exponents
add up: for k = 10 (1024 letters) at least 1 + 3 + 4 + ... + 11 = 64, so the difference is
0 modulo 2^64 for every odd base. For even bases it is worse: B^64 ≡ 0, so only the last
64 characters count.
"""),
            MCQ(r"""
Which hashing setup is safe against every test file written before your submission?
""", [
                Opt("`unsigned long long` overflow with a random odd base.",
                    why="The Thue-Morse pair collides for every odd base modulo 2^64, random or "
                        "not. A random base only helps with a prime modulus."),
                Opt("Modulo 10^9 + 7 with base 131.",
                    why="A fixed base with a 30-bit modulus is broken by a birthday search in "
                        "milliseconds, and even a random base leaves about 1 in 10^9 per "
                        "comparison, which millions of comparisons add up to."),
                Opt("Modulo 2^61 − 1 with a base drawn at run time from `mt19937_64` seeded by the "
                    "clock.", correct=True,
                    why="Yes. Prime modulus, unpredictable base, 61 bits of room: about 10^(−12) "
                        "per comparison whatever the data. Two different ~10^9 primes with random "
                        "bases also work, at twice the cost."),
            ], explain=r"""
The multiplication needs 122 bits, so use `__int128`, and reduce with 2^61 ≡ 1:

```cpp
const ull MOD = (1ULL << 61) - 1;
ull mulmod(ull a, ull b) {
    __uint128_t p = (__uint128_t)a * b;
    ull r = (ull)(p & MOD) + (ull)(p >> 61);
    return r >= MOD ? r - MOD : r;
}
mt19937_64 rng(chrono::steady_clock::now().time_since_epoch().count());
ull B = rng() % (MOD - 1000) + 500;
```

Deterministic tests cannot catch a base that is chosen after they were written.
"""),
            Try("substring_compare", note="Prefix hashes modulo 2^61 − 1, a random base, and a "
                "binary search per question. The first hidden tests are the anti-hash ones."),
        ]),
    ],
    problems=[STRING_MATCHING, FINDING_BORDERS, PREFIX_OCCURRENCES, SUBSTRING_COMPARE],
    cards=[
        Card(r"""What is the prefix function π of a string?""",
             r"""π[i] = length of the longest proper border (prefix that is also a suffix) of `s[0..i]`. π[0] = 0."""),
        Card(r"""The prefix-function loop body?""",
             r"""`int k = pi[i-1]; while (k > 0 && s[i] != s[k]) k = pi[k-1]; if (s[i] == s[k]) k++; pi[i] = k;`"""),
        Card(r"""Why is the prefix function O(n)?""",
             r"""`k` rises by at most 1 per character and each `while` step lowers it; it never goes below 0, so all `while` steps together are at most n."""),
        Card(r"""Find pattern `p` (length m) in text `t` with the prefix function?""",
             r"""Compute π of `p + '#' + t`; each position with π = m is the end of an occurrence. The separator keeps π ≤ m."""),
        Card(r"""All borders of `s` from its prefix function?""",
             r"""`for (k = pi[n-1]; k > 0; k = pi[k-1])`: longest first. A border of a border is a border."""),
        Card(r"""Borders and periods?""",
             r"""`s` has a border of length b iff it has period n − b. Smallest period = n − π[n−1]."""),
        Card(r"""What is the Z-function, and how does the window make it O(n)?""",
             r"""z[i] = LCP of `s` and `s[i..]`. Keep the rightmost match `[l, r)`; inside it start from `min(r - i, z[i - l])`, and extend past `r` only, so `r` only moves right."""),
        Card(r"""Z-function: occurrences of the prefix of length L, and is it a suffix?""",
             r"""It occurs at every i with z[i] ≥ L (count z-values, take suffix sums). It is a suffix iff z[n − L] = L."""),
        Card(r"""Hash of `s[l..r)` from prefix hashes `h[i+1] = h[i]·B + s[i]`?""",
             r"""`h[r] − h[l]·B^(r−l)` (mod M), with powers precomputed."""),
        Card(r"""Birthday bound for hashing?""",
             r"""k hashes modulo M give about k²/(2M) colliding pairs: 10^5 values mod 10^9 + 7 ≈ 5 collisions. Use M = 2^61 − 1."""),
        Card(r"""Why is `unsigned long long` overflow hashing (mod 2^64) unsafe for any base?""",
             r"""Even base: B^64 ≡ 0, only the last 64 characters count. Odd base: the Thue-Morse string of length 1024 and its complement always collide."""),
        Card(r"""The safe contest hash?""",
             r"""Modulo the prime 2^61 − 1 (multiply via `__int128`, reduce with 2^61 ≡ 1), base random from `mt19937_64` seeded by the clock: P(collision) ≤ (L − 1)/M per comparison."""),
    ],
)
