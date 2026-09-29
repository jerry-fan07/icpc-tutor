from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
E18 = 10**18


def _log_uniform(rng, hi):
    """A value in [0, hi] whose number of digits is roughly uniform: big and small both."""
    top = rng.randint(0, len(str(hi)) - 1)
    return rng.randint(0, min(hi, 10**(top + 1) - 1))


def _mult_small(rng):
    t = 20
    out = [str(t)]
    for _ in range(t):
        l = rng.randint(-30, 30)
        r = rng.randint(l, 30)
        out.append(f"{l} {r} {rng.randint(1, 12)}")
    return "\n".join(out) + "\n"


def _mult_big(rng, t):
    out = [str(t)]
    for _ in range(t):
        a = _log_uniform(rng, E18) * rng.choice((-1, 1))
        b = _log_uniform(rng, E18) * rng.choice((-1, 1))
        l, r = min(a, b), max(a, b)
        k = max(1, _log_uniform(rng, E18))
        out.append(f"{l} {r} {k}")
    return "\n".join(out) + "\n"


def _mult_edges(rng, t):
    """Endpoints within a few units of multiples of k, on both sides of zero."""
    out = [str(t)]
    for _ in range(t):
        k = rng.choice((2, 3, 7, 10**9 + 7, rng.randint(1, 10**6), rng.randint(1, E18 // 4)))
        def near():
            q = rng.randint(-(E18 // k), E18 // k)
            return max(-E18, min(E18, q * k + rng.randint(-2, 2)))
        a, b = near(), near()
        out.append(f"{min(a, b)} {max(a, b)} {k}")
    return "\n".join(out) + "\n"


def _prod(rng, n, mlo, mhi, amax):
    m = rng.randint(mlo, mhi)
    a = [_log_uniform(rng, amax) if rng.random() < 0.3 else rng.randint(0, amax) for _ in range(n)]
    return f"{n} {m}\n" + " ".join(map(str, a)) + "\n"


def _prod_no_zero(rng, n, mlo, mhi):
    m = rng.randint(mlo, mhi)
    a = [rng.randint(m // 2, m - 1) for _ in range(n)]      # big residues: every product overflows
    return f"{n} {m}\n" + " ".join(map(str, a)) + "\n"


def _isqrt_small(rng):
    t = 30
    return f"{t}\n" + "\n".join(str(rng.randint(0, 10**4)) for _ in range(t)) + "\n"


def _isqrt_near_squares(rng, t, klo, khi):
    vals = []
    while len(vals) < t:
        k = rng.randint(klo, khi)
        for v in (k * k - 1, k * k, k * k + 1):
            if 0 <= v <= E18:
                vals.append(v)
    vals = vals[:t]
    return f"{t}\n" + "\n".join(map(str, vals)) + "\n"


def _isqrt_random(rng, t):
    return f"{t}\n" + "\n".join(str(_log_uniform(rng, E18)) for _ in range(t)) + "\n"


def _digits(rng, n):
    first = str(rng.randint(1, 9))
    return first + "".join(rng.choice("0123456789") for _ in range(n - 1))


def _huge_small(rng):
    n = rng.randint(1, 30)
    return _digits(rng, n) + "\n" + str(rng.randint(1, 10**9)) + "\n"


def _huge_big(rng, n):
    # random.choices builds a million digits fast; the first digit is never 0
    body = "".join(rng.choices("0123456789", k=n - 1))
    return str(rng.randint(1, 9)) + body + "\n" + str(rng.randint(9 * 10**8, 10**9)) + "\n"


# ------------------------------------------------------------------ fixed tests
_SQUARE_EDGES = []
for _k in (1, 2, 3, 46340, 46341, 67108865, 94906265, 94906266, 999999999, 1000000000):
    for _v in (_k * _k - 1, _k * _k, _k * _k + 1):
        if 0 <= _v <= E18:
            _SQUARE_EDGES.append(_v)
_SQUARE_EDGES_TEST = f"{len(_SQUARE_EDGES)}\n" + "\n".join(map(str, _SQUARE_EDGES)) + "\n"


# --------------------------------------------------------------------- problems
MULTIPLES = Problem(
    id="multiples_in_range",
    title="Multiples in a Range",
    difficulty="easy",
    source="Codeforces 597A - Divisibility",
    complexity="O(1) per test",
    statement=r"""
A raffle gives a prize to every ticket whose number is a multiple of `k`. The tickets are
numbered from `l` to `r`, and in this raffle the numbers can be negative.

For each raffle, count the winning tickets: the integers `x` with `l ≤ x ≤ r` that are
divisible by `k`. (Zero is divisible by every `k`.)
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5), the number of raffles.

Each of the next `t` lines has three integers `l r k` (−10^18 ≤ l ≤ r ≤ 10^18,
1 ≤ k ≤ 10^18).
""",
    output=r"""
For each raffle, print the number of multiples of `k` in `[l, r]` on its own line.
""",
    samples=[
        Test("3\n1 10 3\n-4 5 3\n-10 -1 5\n", "3\n3\n2\n",
             note="The second raffle wins with −3, 0 and 3. If you printed 2, compute "
                  "⌊−5/3⌋ by hand and compare it with what C++ gives for `-5 / 3`."),
    ],
    tests=[
        Test("3\n-6 6 3\n-9 -3 3\n0 0 5\n"),
        Test("4\n-7 -7 7\n-1 -1 2\n5 5 10\n-8 -2 3\n"),
        Test("1\n1 999999999999999999 1\n"),
        Test("1\n-1000000000000000000 1000000000000000000 1\n"),
        Test("3\n-1000000000000000000 1000000000000000000 1000000000000000000\n"
             "999999999999999990 999999999999999999 7\n"
             "-1000000000000000000 -1000000000000000000 1000000000000000000\n"),
    ],
    gens=[
        Gen("small, both signs", _mult_small, 12),
        Gen("endpoints next to multiples", lambda rng: _mult_edges(rng, 20), 4),
        Gen("many huge ranges", lambda rng: _mult_big(rng, 100000), 2, large=True),
        Gen("many endpoints next to multiples", lambda rng: _mult_edges(rng, 100000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// Rounds down (toward minus infinity) for every sign, unlike C++'s `/`.
long long floor_div(long long a, long long b) {
    long long q = a / b;                            // truncated toward zero
    if (a % b != 0 && ((a < 0) != (b < 0))) q--;    // negative and inexact: truncation went up
    return q;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        long long l, r, k;
        cin >> l >> r >> k;
        // (multiples up to r) - (multiples up to l - 1); floor keeps it right for negatives
        cout << floor_div(r, k) - floor_div(l - 1, k) << '\n';
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
        long long l, r, k;
        cin >> l >> r >> k;
        if (r - l <= 2000000) {                      // small range: just count
            long long c = 0;
            for (long long x = l; x <= r; x++) if (x % k == 0) c++;
            cout << c << '\n';
        } else {                                     // shift everything positive first
            __int128 B = (__int128)k * 3000000000000000000LL;
            __int128 hi = (r + B) / k, lo = (l - 1 + B) / k;   // both numerators > 0
            cout << (long long)(hi - lo) << '\n';
        }
    }
}
""",
    hints=[
        r"""Count the multiples of `k` that are `≤ r`, and subtract the ones that are `≤ l − 1`.
The number of multiples of `k` in `(−∞, x]` is not finite, but the *difference* is, and
⌊x/k⌋ plays the role of the count.""",
        r"""The answer is ⌊r/k⌋ − ⌊(l−1)/k⌋. C++'s `/` truncates toward zero, which is the
floor only when the quotient is non-negative. Write a `floor_div` that subtracts one when
the quotient is negative and the division is inexact.""",
        r"""Do not route it through `double`: `(double)999999999999999999` is `10^18`.""",
    ],
    editorial=r"""
Among the integers up to `x`, multiples of `k` recur every `k` steps, so
#{multiples in `[l, r]`} = ⌊r/k⌋ − ⌊(l−1)/k⌋. Both terms need the **floor**, and C++'s `/`
gives the truncation toward zero:

| a / b | exact | floor | C++ `a / b` |
| −5 / 3 | −1.67 | −2 | −1 |
| 5 / 3 | 1.67 | 1 | 1 |
| −6 / 3 | −2 | −2 | −2 |

They differ exactly when the quotient is negative and inexact, so `floor_div` is `a / b`
minus one in that case. The first sample already fails without it.

Two other habits fail the hidden tests. `floor((double)r / k)` is wrong once the values pass
2^53 ≈ 9·10^15, because a `double` cannot hold them exactly: for `l = 1, r = 10^18 − 1,
k = 1` it answers 10^18. And every variable must be a `long long`: the answer itself can be
2·10^18 + 1.
""",
)

PRODUCT_MOD = Problem(
    id="product_mod",
    title="Product Modulo m",
    difficulty="medium",
    complexity="O(n)",
    statement=r"""
A checksum multiplies all the numbers in a file together and keeps the remainder modulo
`m`. The modulus is chosen by the user, and some users choose very large ones.

Compute `(a_1 · a_2 · ... · a_n) mod m`.
""",
    input=r"""
The first line has `n` and `m` (1 ≤ n ≤ 2·10^5, 1 ≤ m ≤ 10^18).

The second line has `n` integers a_1, ..., a_n (0 ≤ a_i ≤ 10^18).
""",
    output=r"""
Print the product modulo `m`, a number in `[0, m)`.
""",
    samples=[
        Test("3 1000000007\n2 3 4\n", "24\n"),
        Test("2 1000000000000000000\n999999999999999999 999999999999999999\n", "1\n",
             note="(10^18 − 1)^2 = 10^36 − 2·10^18 + 1, which leaves 1. The product needs "
                  "about 120 bits; a `long long` has 63."),
    ],
    tests=[
        Test("1 1\n5\n"),
        Test("1 1000000000000000000\n1000000000000000000\n"),
        Test("2 3037000501\n3037000500 3037000500\n"),
        Test("3 999999999999999989\n123456789012345678 987654321098765432 555555555555555555\n"),
        Test("5 7\n0 1 2 3 4\n"),
    ],
    gens=[
        Gen("small modulus", lambda rng: _prod(rng, rng.randint(1, 10), 1, 10**9, 10**9), 8),
        Gen("huge modulus", lambda rng: _prod(rng, rng.randint(1, 10), 10**17, E18, E18), 8),
        Gen("big residues", lambda rng: _prod_no_zero(rng, rng.randint(2, 10), 10**12, E18), 6),
        Gen("max n, huge modulus", lambda rng: _prod_no_zero(rng, 200000, 9 * 10**17, E18), 2),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    long long m;
    cin >> n >> m;
    long long p = 1 % m;                       // m = 1: everything is 0
    for (int i = 0; i < n; i++) {
        long long a;
        cin >> a;
        // p and a % m are below 10^18; their product is below 10^36: 128 bits
        p = (long long)((__int128)p * (a % m) % m);
    }
    cout << p << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long ull;
// a * b mod m by doubling: every intermediate stays below 2m <= 2 * 10^18 < 2^64
ull mulmod(ull a, ull b, ull m) {
    ull r = 0;
    a %= m;
    while (b) {
        if (b & 1) { r += a; if (r >= m) r -= m; }
        a += a; if (a >= m) a -= m;
        b >>= 1;
    }
    return r;
}
int main() {
    int n;
    ull m;
    cin >> n >> m;
    ull p = 1 % m;
    for (int i = 0; i < n; i++) {
        ull a;
        cin >> a;
        p = mulmod(p, a % m, m);
    }
    cout << p << '\n';
}
""",
    hints=[
        r"""Reduce after every multiplication so the running product stays below `m`. The
question is only what type the multiplication itself happens in.""",
        r"""Two numbers below 10^18 multiply to almost 10^36. `long long` stops at about
9.2·10^18, `unsigned long long` at 1.8·10^19. `__int128` goes to about 1.7·10^38.""",
        r"""`p = (long long)((__int128)p * (a % m) % m);` The cast on `p` must come *before* the
`*`.""",
    ],
    editorial=r"""
Keep the running product reduced mod `m`, and do each multiplication in 128 bits:

```cpp
p = (long long)((__int128)p * (a % m) % m);
```

Both factors are below `m ≤ 10^18`, so the product is below 10^36 < 1.7·10^38. The result
of `% m` fits back in a `long long`, which is also what you print: `cout` has no `<<` for
`__int128`.

The `long long` version `p * (a % m) % m` is right only while (m − 1)^2 ≤ 9.2·10^18,
i.e. for `m` up to about 3.04·10^9. That covers the usual 10^9 + 7, which is why this bug
survives small tests; the second sample and the hidden test with `m = 3037000501` catch it.
Casting afterwards, `(__int128)(p * a) % m`, is the same bug: the overflow already happened.

Without `__int128` (some compilers lack it) the portable fallback is the brute force's
multiplication by doubling: add `a` to itself `log b` times, reducing mod `m` at each step;
every intermediate stays below 2m.
""",
)

ISQRT = Problem(
    id="integer_sqrt",
    title="Integer Square Root",
    difficulty="medium",
    complexity="O(1) per query",
    statement=r"""
For each given `n`, print ⌊√n⌋: the largest integer `r` with `r·r ≤ n`.

Python has `math.isqrt`. C++ has `sqrt`, which works on `double`s. Make it exact.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5). Each of the next `t` lines has one integer `n`
(0 ≤ n ≤ 10^18).
""",
    output=r"""
For each `n`, print ⌊√n⌋ on its own line.
""",
    samples=[
        Test("4\n0\n10\n16\n1000000000000000000\n", "0\n3\n4\n1000000000\n"),
        Test("1\n999999999999999999\n", "999999999\n",
             note="`(long long)sqrt(n)` prints 1000000000 here. `n` is converted to a `double` "
                  "first, and the nearest `double` to 10^18 − 1 is 10^18."),
    ],
    tests=[
        Test(_SQUARE_EDGES_TEST),
        Test("3\n4503599761588224\n4503599761588225\n4503599761588226\n"),
    ],
    gens=[
        Gen("small values", _isqrt_small, 8),
        Gen("around big squares", lambda rng: _isqrt_near_squares(rng, 300, 10**8, 10**9), 4),
        Gen("random magnitudes", lambda rng: _isqrt_random(rng, 300), 4),
        Gen("max t, around squares", lambda rng: _isqrt_near_squares(rng, 100000, 1, 10**9), 1),
        Gen("max t, random", lambda rng: _isqrt_random(rng, 100000), 1),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

long long isqrt(long long n) {
    long long r = (long long)sqrt((double)n);   // within 1 of the answer, not exact
    while (r * r > n) r--;                      // r is at most about 10^9 + 1:
    while ((r + 1) * (r + 1) <= n) r++;         // these squares fit in a long long
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        long long n;
        cin >> n;
        cout << isqrt(n) << '\n';
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
        long long n;
        cin >> n;
        long long lo = 0, hi = 2000000000;          // lo*lo <= n < hi*hi
        while (hi - lo > 1) {
            long long mid = lo + (hi - lo) / 2;
            if ((__int128)mid * mid <= n) lo = mid; else hi = mid;
        }
        cout << lo << '\n';
    }
}
""",
    hints=[
        r"""`sqrt` converts `n` to a `double` (53 bits of precision) and rounds its result. Both
steps can move the answer by one. But the answer is never off by more than one here.""",
        r"""Start from `r = (long long)sqrt((double)n)` and fix it with integer arithmetic:
`while (r * r > n) r--; while ((r + 1) * (r + 1) <= n) r++;`""",
    ],
    editorial=r"""
`sqrt(n)` goes wrong in two places. The conversion `(double)n` rounds to 53 significant
bits, so above 2^53 ≈ 9·10^15 distinct integers collapse: `10^18 − 1` becomes `10^18`,
whose root is exactly 10^9. And even when `n` converts exactly, the root itself is rounded
to the nearest `double`: √(k^2 − 1) ≈ k − 1/(2k), and for `k` above about 6.7·10^7 that is
closer to `k` than to any other `double`, so `n = 67108865^2 − 1 = 4503599761588224`
(below 2^53) still comes out as 67108865.

Both errors are tiny, so the estimate is within one of the truth. Correct it with exact
integer comparisons:

```cpp
long long r = (long long)sqrt((double)n);
while (r * r > n) r--;
while ((r + 1) * (r + 1) <= n) r++;
```

`r` never exceeds about 10^9 + 1, so the squares stay near 10^18, inside a `long long`.
On x86 Linux judges `sqrtl` (80-bit `long double`, 64-bit mantissa) happens to be exact for
this range; on this judge's ARM machine `long double` is the same as `double`. Code that
corrects its estimate is right everywhere. A binary search on `r` also works, with the
product done in `__int128` or bounded so it cannot overflow.
""",
)

HUGE_NUMBER = Problem(
    id="huge_number",
    title="A Number Too Big to Read",
    difficulty="easy",
    complexity="O(number of digits)",
    statement=r"""
You are given a non-negative integer `N` with up to a million digits, and a modulus `m`.
Print the sum of the digits of `N`, and `N mod m`.

No integer type holds `N`. A `string` does.
""",
    input=r"""
The first line has `N`: between 1 and 10^6 decimal digits, without leading zeros (unless
`N` is 0).

The second line has `m` (1 ≤ m ≤ 10^9).
""",
    output=r"""
Two lines: the digit sum of `N`, then `N mod m`.
""",
    samples=[
        Test("1234\n7\n", "10\n2\n",
             note="1 + 2 + 3 + 4 = 10. If you printed 202, you added character codes: "
                  "`'1'` is 49."),
        Test("99999999999999999999\n1000000000\n", "180\n999999999\n",
             note="Processing digit by digit, `r * 10 + d` reaches 9999999999 here. That "
                  "does not fit in an `int`."),
    ],
    tests=[
        Test("0\n1\n"),
        Test("0\n1000000000\n"),
        Test("7\n1\n"),
        Test("1000000000000000000000\n1000000007\n"),
        Test("123456789\n1000000000\n"),
    ],
    gens=[
        Gen("short numbers", _huge_small, 10),
        Gen("a million digits", lambda rng: _huge_big(rng, 10**6), 2),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    long long m;
    cin >> s >> m;
    long long digit_sum = 0, r = 0;             // r = (prefix read so far) mod m
    for (char c : s) {
        int d = c - '0';                        // '7' - '0' == 7
        digit_sum += d;
        r = (r * 10 + d) % m;                   // r * 10 can reach 10^10: long long
    }
    cout << digit_sum << '\n' << r << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    string s;
    long long m;
    cin >> s >> m;
    long long cnt[10] = {0};
    for (char c : s) cnt[c - '0']++;
    long long ds = 0;
    for (int d = 0; d < 10; d++) ds += d * cnt[d];
    // nine digits at a time, in 128 bits
    __int128 r = 0;
    for (size_t i = 0; i < s.size(); i += 9) {
        string chunk = s.substr(i, 9);
        __int128 p = 1;
        for (size_t j = 0; j < chunk.size(); j++) p *= 10;
        r = (r * p + stoll(chunk)) % m;
    }
    cout << ds << '\n' << (long long)r << '\n';
}
""",
    hints=[
        r"""Read `N` with `string s; cin >> s;`. Each character `c` is a digit's character code;
`c - '0'` is the digit's value.""",
        r"""Build the remainder the way you would build the number, one digit at a time:
`r = (r * 10 + d) % m`. Before the `%`, `r * 10 + d` can be close to 10^10.""",
    ],
    editorial=r"""
A million digits is about 3.3 million bits, so `N` lives in a `string`. Its characters are
ASCII codes: `'0'` is 48 and `'9'` is 57, contiguous, so `c - '0'` is the digit. Adding `c`
itself sums character codes (the first sample's 202).

The remainder follows Horner's rule: if `r` is the prefix read so far mod `m`, appending a
digit `d` makes it `(r · 10 + d) mod m`, because `(x · 10 + d) mod m` only depends on
`x mod m`. With `m` up to 10^9, `r` can be 999999999 and `r · 10 + d` about 10^10, past the
2.1·10^9 an `int` holds: the second sample. Same rule as always: the type comes from the
largest value you compute, here the one *before* the `%`.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp02",
    title="types, overflow & arithmetic",
    track="cpp",
    order=2,
    summary="Where overflow hides inside expressions, how C++ division rounds (and why it "
            "differs from Python), __int128, what a double cannot hold, exact square roots, "
            "and characters as numbers.",
    prereqs=["cpp01"],
    tags=["long long", "overflow", "unsigned", "__int128", "division", "modulo",
          "floor division", "double", "precision", "sqrt", "char"],
    parts=[
        Part("The integer ladder", [
            Say(r"""
cpp01 left you with one rule: choose the type from the largest value you *compute*, not the
largest you read. This lesson is the rest of the arithmetic that C++ does differently from
Python: where overflow hides inside an expression, how division rounds, what a `double`
cannot hold, and what a `char` really is. Every item here has cost someone a Wrong Answer.

Every integer type is a fixed number of bits:

| type | bits | range |
| `int` | 32 | −2^31 .. 2^31 − 1, about ±2.1·10^9 |
| `unsigned` | 32 | 0 .. 2^32 − 1, about 4.3·10^9 |
| `long long` | 64 | −2^63 .. 2^63 − 1, about ±9.2·10^18 |
| `unsigned long long` | 64 | 0 .. 2^64 − 1, about 1.8·10^19 |
| `__int128` | 128 | about ±1.7·10^38 (a GCC/clang extension) |

The exact limits have names in `<climits>`: `INT_MAX`, `INT_MIN`, `LLONG_MAX`, `LLONG_MIN`,
`ULLONG_MAX`.
"""),
            MCQ(r"""
With `int a = 100000, b = 100000;`, which of these store 10^10?

```cpp
long long x1 = a * b * 1LL;
long long x2 = 1LL * a * b;
long long x3 = (long long)(a * b);
```
""", [
                Opt("`x1` and `x2`: each expression contains a `long long`.",
                    why="`*` groups left to right, so `x1` is `(a * b) * 1LL`. The `a * b` "
                        "happens first, in `int`, and overflows (on this judge it gave 1410065408). The "
                        "`1LL` arrives after the damage."),
                Opt("Only `x2`.", correct=True,
                    why="Right. `1LL * a` is a `long long`, so `(1LL * a) * b` is computed in 64 "
                        "bits. The widening has to happen in the *first* multiplication."),
                Opt("All three: the variables are `long long`.",
                    why="That was cpp01's trap: the type of an expression comes from its "
                        "operands, never from the variable it is stored in."),
                Opt("`x2` and `x3`: the cast makes the product 64-bit.",
                    why="`x3` casts the *result* of `a * b`, which has already overflowed in "
                        "`int`. Converting garbage to `long long` keeps the garbage."),
            ], explain=r"""
Each `*` or `+` picks its type from its own two operands, and a chain is evaluated left to
right. So widen the leftmost operand: `1LL * a * b` or `(long long)a * b`. Sums have the same
trap: `a + b + 1LL` overflows in `a + b` first when both are near 2·10^9.
"""),
            Numeric(r"""
Factorials are a quick way to feel the limits. What is the largest `n` for which `n!` fits in
a `long long`?
""", answer=20,
                hint="10! is about 3.6·10^6. Keep multiplying until you pass 9.2·10^18.",
                explain=r"""
20! = 2432902008176640000 ≈ 2.4·10^18 fits; 21! ≈ 5.1·10^19 does not (a `long long` loop
prints −4249290049419214848 for it). So "the number of orderings of `n` items" is a `long long` only
up to `n = 20`, which is why counting problems ask for answers mod 10^9 + 7 (cpp10).
"""),
            MCQ(r"""
You need a mask with bit 40 set. What does this line do?

```cpp
long long mask = 1 << 40;
```
""", [
                Opt("Sets `mask` to 2^40 = 1099511627776.",
                    why="`1` is an `int`, so the shift happens in 32 bits, where shifting by 40 "
                        "is out of range. Storing the result in a `long long` comes too late."),
                Opt("Undefined behaviour: `1` is a 32-bit `int`, and 40 is past its width.",
                    correct=True,
                    why="Right. GCC warns, and what you get depends on the machine and the "
                        "optimiser: on this judge a run-time `1 << k` with `k = 40` gave 256 "
                        "(the count is taken mod 32). Write `1LL << 40`."),
                Opt("A compile error.",
                    why="With a constant, GCC only *warns*; with a variable shift count it "
                        "cannot even do that. It compiles and computes nonsense."),
                Opt("Reliably 0, because the bit falls off the end.",
                    why="Nothing about it is reliable: it is undefined behaviour, and on this "
                        "machine it gave 256 at run time."),
            ], explain=r"""
The literal `1` is an `int`; `1LL` is a `long long`. Bitmask code (cpp10) does `1 << k`
constantly, and it is fine up to `k = 30`. Past that, write `1LL << k`.
"""),
            Short(r"""
Predict the output. (Python's `len(v) - 1` would be `-1`.)

```cpp
vector<int> v;                       // empty
cout << v.size() - 1 << '\n';
```
""", accept=["18446744073709551615", "2^64-1", "2^64 - 1", "2^64−1", "2^64 − 1"],
                placeholder="what it prints",
                hint="`size()` returns an unsigned 64-bit type. What is 0 − 1 when there is no "
                     "negative?",
                explain=r"""
`18446744073709551615` = 2^64 − 1. `size()` returns `size_t`, an unsigned 64-bit type, and
unsigned arithmetic wraps around mod 2^64. So `for (int i = 0; i < v.size() - 1; i++)` on an
empty vector does not skip the loop: the bound is 1.8·10^19, the loop runs, and `v[0]` does
not exist. Write `i + 1 < v.size()`, or convert first: `(int)v.size() - 1`.

The general advice: do not use `unsigned` types to "get a bigger range" (use `long long`),
and be suspicious of any subtraction involving `size()`.
"""),
        ]),
        Part("Division rounds toward zero", [
            Say(r"""
cpp01 showed that `7 / 2` is `3` for `int`s, and `7 % 2` is `1`. Python agrees, as long as
everything is positive. With a negative operand, the two languages part ways, and every
problem with negative numbers and a division in it walks into the difference.
"""),
            Short(r"""
Predict the output exactly:

```cpp
cout << -7 / 2 << ' ' << -7 % 2 << '\n';
```
""", accept=["-3 -1", "−3 −1"], placeholder="what it prints",
                hint="Python prints `-4 1`. C++ does not.",
                explain=r"""
`-3 -1`. C++ division **truncates toward zero**: −3.5 becomes −3. Python's `//` **floors**:
−3.5 becomes −4. Each language then defines the remainder so that
`(a / b) * b + a % b == a`: in C++, −7 = (−3)·2 + (−1).
"""),
            MCQ(r"""
Which statement is true in C++ for every pair of `int`s `a`, `b` with `b ≠ 0` (and no
overflow)?
""", [
                Opt("`a % b` is always in `[0, |b|)`.",
                    why="That is Python's behaviour for positive `b`. In C++, `-7 % 2` is `-1`."),
                Opt("`a % b` has the sign of `b`, or is 0.",
                    why="That is Python's rule. In C++, `7 % -2` is `1`, with the sign of `a`."),
                Opt("`a % b` has the sign of `a` (or is 0), and `(a / b) * b + a % b == a`.",
                    correct=True,
                    why="Yes. Truncation fixes the quotient, and the remainder is whatever is "
                        "left over, so it follows the sign of the dividend `a`."),
                Opt("`a / b` always rounds down.",
                    why="It rounds toward zero, which is *up* when the quotient is negative: "
                        "`-7 / 2` is −3, above −3.5."),
            ], explain=r"""
Two bugs this causes all the time. `x % 2 == 1` is false for a negative odd `x` (it is −1),
so test `x % 2 != 0`. And a remainder used as an array index can be negative; normalise it
with `((x % m) + m) % m`, which is always in `[0, m)`.
"""),
            Short(r"""
For positive `a` and `b`, the standard ceiling idiom is `(a + b - 1) / b`: `(7 + 2 - 1) / 2`
is 4 = ⌈3.5⌉. What does the same expression give for `a = -6`, `b = 3`?
""", accept=["-1", "−1"], placeholder="a number",
                hint="Compute `a + b - 1` first, then divide with C++'s truncating `/`.",
                explain=r"""
`-6 + 3 - 1 = -4`, and `-4 / 3` truncates to `-1`. But ⌈−6/3⌉ = −2. The idiom assumes that
`/` rounds down and nudges the numerator to get "up"; when the quotient is negative, `/`
already rounds up (toward zero), so the nudge overshoots. For negative quotients, plain
`a / b` *is* the ceiling.
"""),
            Reflect(r"""
Write `floor_div(a, b)`, the rounded-down quotient for any signs, using C++'s `/` and `%` and
one correction. When exactly does truncation differ from the floor?
""", answer=r"""
Truncation and floor agree unless the exact quotient is negative and not an integer; then
truncation is one too high. The quotient is negative when `a` and `b` have opposite signs,
and inexact when `a % b != 0`:

```cpp
long long floor_div(long long a, long long b) {
    long long q = a / b;
    if (a % b != 0 && ((a < 0) != (b < 0))) q--;
    return q;
}
```

`ceil_div` is the mirror image: `q++` when the quotient is positive (same signs) and
inexact.
"""),
            MCQ(r"""
Why not skip all that and write `(long long)floor((double)a / b)`?
""", [
                Opt("It is fine: `floor` rounds down for negative numbers too.",
                    why="`floor` is right; the input is not. `(double)a` is not always `a`: a "
                        "`double` cannot hold every integer past about 9·10^15, and "
                        "`(double)999999999999999999` is exactly 10^18."),
                Opt("It is wrong once `|a|` passes about 9·10^15, because the `double` "
                    "conversion rounds.", correct=True,
                    why="Right. The part on doubles below shows exactly where they run out of digits. In "
                        "integer problems, keep integer arithmetic."),
                Opt("It is correct but too slow.",
                    why="Speed is not the issue; a floating-point division costs a few "
                        "nanoseconds. Correctness is."),
            ]),
            Numeric(r"""
By hand: how many multiples of 3 lie in `[−4, 5]`? (Zero counts.)
""", answer=3,
                explain=r"""
−3, 0 and 3. The general formula counts multiples up to `r` minus multiples up to `l − 1`:
⌊5/3⌋ − ⌊−5/3⌋ = 1 − (−2) = 3. With C++'s truncating `/`, `5 / 3 - (-5) / 3` is
1 − (−1) = 2, one short.
"""),
            Try("multiples_in_range", note="Floor division with negative numbers, values up "
                "to 10^18. The sample has a negative range."),
        ]),
        Part("When 64 bits are not enough", [
            Say(r"""
A frequent need: `a · b mod m` with `a, b < m`. When `m` is 10^9 + 7 the product is below
10^18 and a `long long` holds it. But hashing with a large modulus, primality tests and some
problems use `m` up to 10^18, and then the product reaches 10^36.
"""),
            Numeric(r"""
`(a % m) * (b % m) % m` in `long long` is safe as long as (m − 1)^2 ≤ 9.2·10^18. Roughly
what is the largest safe `m`?
""", answer=3.037e9, rel=0.1,
                hint="Take the square root of 9.2·10^18.",
                explain=r"""
√(9.2·10^18) ≈ 3.04·10^9. That is why the favourite moduli, 10^9 + 7 and 998244353, are
just under a third of that: the product of two residues fits in a `long long` with room to
spare. At `m = 3037000501`, (m − 1)^2 already overflows.
"""),
            Say(r"""
GCC and clang provide a 128-bit integer, `__int128`, up to about 1.7·10^38. Arithmetic works
as usual, but `cin` and `cout` do not know the type (`cout << x` does not even compile). The
standard pattern is to read `long long`s, multiply in 128 bits, reduce, and come back:

```cpp
long long r = (long long)((__int128)a * b % m);
```
"""),
            MCQ(r"""
Which line computes `a · b mod m` correctly for `long long a, b` with `a, b < m ≤ 10^18`?
""", [
                Opt("`(__int128)(a * b) % m`",
                    why="The cast applies to `a * b`, which has already overflowed in 64 bits. "
                        "Same mistake as `(long long)(a * b)` with `int`s."),
                Opt("`(unsigned long long)a * b % m`",
                    why="Unsigned 64-bit reaches 1.8·10^19, twice as far as `long long`, still "
                        "nowhere near 10^36. Unsigned overflow is defined (it wraps mod 2^64), "
                        "but the wrapped value is the wrong answer."),
                Opt("`(__int128)a * b % m`", correct=True,
                    why="Yes. The cast binds tighter than `*`, so `a` is widened first and `b` "
                        "is promoted to match: the whole product is 128-bit."),
                Opt("`a * b % m`: a `long long` goes to 9.2·10^18 and `m` is only 10^18.",
                    why="`m` fits, but `a * b` can be almost 10^36."),
            ]),
            MCQ(r"""
When a result really needs all 128 bits, you print it yourself. What does this print for
`x = 0`?

```cpp
void print(__int128 x) {
    string s;
    while (x > 0) { s += char('0' + x % 10); x /= 10; }
    reverse(s.begin(), s.end());
    cout << s << '\n';
}
```
""", [
                Opt("`0`",
                    why="Trace it: for `x = 0` the loop condition is false at once, so `s` "
                        "stays empty."),
                Opt("An empty line.", correct=True,
                    why="Right: the loop never runs, `s` is empty, and only the newline comes "
                        "out. Negative numbers print an empty line too."),
                Opt("Nothing, not even a newline.",
                    why="The `'\\n'` is printed unconditionally after `s`."),
            ], explain=r"""
Handle the two special cases first: `if (x == 0) { cout << "0\n"; return; }` and
`if (x < 0) { cout << '-'; x = -x; }`. "The loop that never runs for zero" is a classic in
every hand-written number printer and parser.
"""),
            Try("product_mod", note="`m` goes up to 10^18. The second sample overflows a "
                "`long long` product."),
        ]),
        Part("What a double cannot hold", [
            Say(r"""
A `double` is 64 bits split three ways: a sign, an 11-bit exponent, and 52 stored bits of
mantissa (53 with an implicit leading 1). It reaches about 1.8·10^308, but with only 15-17
significant decimal digits. Every `double` is a binary fraction; 0.1 is not one, so it is
stored as the nearest one. Python's `float` is the same type, so `0.1 + 0.2 != 0.3` is not
news. What differs in C++ is printing, and what happens when integers meet doubles.
"""),
            Short(r"""
Python prints `1000000.0`. What does C++ print?

```cpp
double x = 1000000;
cout << x << '\n';
```
""", accept=["1e+06"], placeholder="what it prints",
                hint="By default `cout` shows 6 significant digits.",
                explain=r"""
`1e+06`. The default format keeps 6 significant digits and switches to scientific notation
when the exponent is too big for them: `100000.0` prints `100000`, `1000000.0` prints
`1e+06`, `1234567.0` prints `1.23457e+06`. A judge comparing tokens rejects `1e+06` when it
expects `1000000`. Print doubles with `fixed << setprecision(k)`, and when the answer is an
integer, compute it in an integer type.
"""),
            Numeric(r"""
53 bits of mantissa: up to roughly what magnitude can a `double` represent *every* integer
exactly?
""", answer=9007199254740992, rel=0.2,
                hint="Every integer below 2^53 fits in 53 bits.",
                explain=r"""
2^53 = 9007199254740992 ≈ 9·10^15. Past it, the gap between consecutive doubles is 2, then
4, and so on; near 10^18 it is 128. So a `double` can hold 10^18, but not 10^18 + 1. Every
`long long` above 9·10^15 that passes through a `double` may come back different.
"""),
            Short(r"""
Predict the output:

```cpp
long long x = 1000000000000000001;   // 10^18 + 1
double d = x;
cout << (long long)d - x << '\n';
```
""", accept=["-1", "−1"], placeholder="what it prints",
                explain=r"""
`-1`. Near 10^18 consecutive doubles are 128 apart, so `10^18 + 1` rounds to `10^18`, and
converting back gives `10^18`. The round trip `long long → double → long long` silently
changes the value. `pow`, `sqrt`, `floor`, `ceil` and `log` all take and return doubles, so
all of them are a round trip.
"""),
            MCQ(r"""
You need to test whether two computed doubles are equal. Which test is right?
""", [
                Opt("`a == b`",
                    why="Two computations of the same real number can round differently: "
                        "`0.1 + 0.2 == 0.3` is false."),
                Opt("`fabs(a - b) < 1e-9`, with the tolerance chosen for the problem's scale.",
                    correct=True,
                    why="Yes. An absolute epsilon suits values around 1; for values around "
                        "10^9, compare relative to their size, or better, stay in integers."),
                Opt("`(long long)a == (long long)b`",
                    why="Truncation turns 2.9999999999 into 2 and 3.0000000001 into 3: nearly "
                        "equal values end up different."),
            ], explain=r"""
The better fix is usually to avoid doubles: compare `a·d < c·b` instead of `a/b < c/d`,
`x·x ≤ n` instead of `x ≤ sqrt(n)`. Integer arithmetic is exact.
"""),
        ]),
        Part("Square roots of big integers", [
            Say(r"""
A common subproblem: ⌊√n⌋ for `n` up to 10^18 (to loop over divisors up to √n, to test
whether `n` is a perfect square, to invert `k·k ≤ n`). Python has `math.isqrt`. In C++
everyone's first attempt is `(long long)sqrt(n)`.
"""),
            Short(r"""
What does this print? (The true answer is 999999999, since 10^9 · 10^9 = 10^18 > n.)

```cpp
long long n = 999999999999999999;   // 10^18 - 1
cout << (long long)sqrt(n) << '\n';
```
""", accept=["1000000000", "10^9", "1e9"], placeholder="what it prints",
                explain=r"""
`1000000000`. `sqrt` takes a `double`, and the nearest `double` to 10^18 − 1 is 10^18,
whose root is exactly 10^9. The input was damaged before `sqrt` even ran.
"""),
            MCQ(r"""
Below 2^53 every integer converts exactly. Yet for `n = 67108865^2 − 1 = 4503599761588224`
(about 4.5·10^15), `(long long)sqrt(n)` prints `67108865`, one too many. Why?
""", [
                Opt("The conversion of `n` to `double` lost precision.",
                    why="Not this time: 4.5·10^15 < 2^53, so `n` converts exactly."),
                Opt("`sqrt` rounds its result to the nearest double, and √(k^2 − 1) is closer "
                    "to `k` than to any other double when `k` is large.", correct=True,
                    why="Yes. √(k^2 − 1) ≈ k − 1/(2k), about k − 7.5·10^-9 here, and near 6.7·10^7 "
                        "doubles are 1.5·10^-8 apart. The nearest double is `k` itself."),
                Opt("`sqrt` uses 32-bit `float`s internally.",
                    why="`sqrt(double)` is correctly rounded to double precision. It is exact "
                        "to within half a unit; that half unit is the problem."),
                Opt("A bug in GCC's math library.",
                    why="The result is the correctly rounded square root. Rounding is the "
                        "specification, not a bug."),
            ]),
            Reflect(r"""
The estimate `r = (long long)sqrt((double)n)` is never off by more than one for `n ≤ 10^18`.
How do you turn it into the exact ⌊√n⌋, and why can the fix itself not overflow?
""", answer=r"""
Correct it with exact integer comparisons:

```cpp
long long r = (long long)sqrt((double)n);
while (r * r > n) r--;
while ((r + 1) * (r + 1) <= n) r++;
```

Afterwards `r·r ≤ n < (r+1)·(r+1)`, which is the definition of ⌊√n⌋. Since `r` is at most
about 10^9 + 1, the squares are at most about 10^18, well inside a `long long`. The same
pattern (float estimate, integer correction) works for cube roots and for `log`.
"""),
            MCQ(r"""
A friend says: "just use `sqrtl`, `long double` has 64 bits of mantissa." What is the right
response?
""", [
                Opt("Agreed: `sqrtl` is exact for every `n ≤ 10^18`.",
                    why="On x86 Linux judges it happens to be. On this judge (ARM) `long "
                        "double` is 8 bytes, identical to `double`, and `sqrtl(10^18 − 1)` also "
                        "returns 10^9. MSVC is the same."),
                Opt("Use `pow(n, 0.5)` instead.",
                    why="`pow` works in `double` too; it has both problems of `sqrt` and is "
                        "slower."),
                Opt("Round instead of truncating: `(long long)(sqrt(n) + 0.5)`.",
                    why="That computes the *nearest* integer to √n, not the floor: for "
                        "`n = 8` it gives 3, but 3·3 = 9 > 8."),
                Opt("Keep whatever estimate you like and correct it with integer checks.",
                    correct=True,
                    why="Right: code that verifies `r·r ≤ n < (r+1)·(r+1)` is correct on every "
                        "machine, whatever the floating-point hardware does."),
            ]),
            Try("integer_sqrt", note="Values up to 10^18. The second sample is the one "
                "`(long long)sqrt(n)` gets wrong."),
        ]),
        Part("A char is a small integer", [
            Say(r"""
Python has no character type: `'a'` is a string of length 1, and `'a' + 1` is a TypeError.
In C++ a `char` is an 8-bit integer that `cout` happens to print as a character. The values
are ASCII codes, and the useful ranges are contiguous:

| characters | codes |
| `'0'` .. `'9'` | 48 .. 57 |
| `'A'` .. `'Z'` | 65 .. 90 |
| `'a'` .. `'z'` | 97 .. 122 |

Any arithmetic on a `char` first promotes it to `int`.
"""),
            Short(r"""
Predict the output:

```cpp
cout << 'a' + 1 << '\n';
```
""", accept=["98"], placeholder="what it prints",
                explain=r"""
`98`. `'a' + 1` is an `int` (97 + 1), and `cout` prints an `int` as a number. To get the
character, convert back: `cout << char('a' + 1)` prints `b`.
"""),
            Short(r"""
The library's character functions come from C, where they take and return `int`. Predict:

```cpp
cout << toupper('q') << '\n';
```
""", accept=["81"], placeholder="what it prints",
                explain=r"""
`81`, the code of `'Q'`. `toupper`, `tolower` and friends return `int`. Store the result in
a `char` (`char c = toupper(x);`) or cast it before printing. The classification functions
`isdigit`, `isalpha`, `isupper`, `isspace` return an `int` too: zero or non-zero, not
necessarily 1.
"""),
            Short(r"""
Here is a digit sum with a bug. What does it print?

```cpp
string n = "4096";
int sum = 0;
for (char c : n) sum += c;
cout << sum << '\n';
```
""", accept=["211"], placeholder="what it prints",
                hint="`'0'` is 48, and the digits are consecutive after it.",
                explain=r"""
`211` = 52 + 48 + 57 + 54, the character codes. The digit's value is `c - '0'`: `'4' - '0'`
is 4. With the fix the sum is 19.
"""),
            Short(r"""
Shifting letters around the alphabet (a Caesar cipher) mixes chars with the division rules
from earlier in this lesson. What does this print?

```cpp
char c = 'b';
int k = -3;                                    // shift back by 3
cout << char('a' + (c - 'a' + k) % 26) << '\n';
```
""", accept=["_"], placeholder="one character",
                hint="Compute `(c - 'a' + k) % 26` with C++'s rules first.",
                explain=r"""
`_` (code 95). `(1 − 3) % 26` is `−2` in C++, and `'a' − 2` is 95. With the normalised
remainder, `((c - 'a' + k) % 26 + 26) % 26` is 24, and the answer is `y`: the same
`((x % m) + m) % m` fix as before, in a new costume.
"""),
            Numeric(r"""
To compute `N mod m` for a number `N` given as a string of digits, you keep
`r = (r * 10 + d) % m`. With `m` up to 10^9, roughly how large can `r * 10 + d` get before
the `%`?
""", answer=1e10, rel=0.1,
                explain=r"""
`r` can be `m − 1 = 999999999`, so `r * 10 + d` reaches 9999999999 ≈ 10^10, well past
`INT_MAX` ≈ 2.1·10^9. `r` must be a `long long` even though every value it *keeps* fits in
an `int`. The largest value you compute includes the ones that exist only for a moment.
"""),
            Try("huge_number", note="A million digits, read as a string. Both samples are "
                "traps: one for character codes, one for `int`."),
        ]),
    ],
    problems=[MULTIPLES, PRODUCT_MOD, ISQRT, HUGE_NUMBER],
    cards=[
        Card(r"""With `int a, b` near 10^5, why is `long long x = a * b * 1LL;` wrong, and what is right?""",
             r"""It computes `(a * b) * 1LL`: `a * b` overflows in `int` first. Widen the first operand: `1LL * a * b`."""),
        Card(r"""Largest `n` whose factorial fits in a `long long`?""",
             r"""20 (20! ≈ 2.4·10^18). 21! ≈ 5.1·10^19 overflows."""),
        Card(r"""What is wrong with `1 << 40`?""",
             r"""`1` is a 32-bit `int`; shifting it by 40 is undefined behaviour. Write `1LL << 40`."""),
        Card(r"""What is `v.size() - 1` for an empty vector, and how do you loop to the second-last element safely?""",
             r"""2^64 − 1 (`size()` is unsigned and wraps). Write `i + 1 < v.size()` or `(int)v.size() - 1`."""),
        Card(r"""`-7 / 2` and `-7 % 2` in C++ vs Python?""",
             r"""C++ truncates toward zero: `-3` and `-1`. Python floors: `-4` and `1`. In C++ `a % b` takes the sign of `a`."""),
        Card(r"""Floor division for any signs in C++?""",
             r"""`q = a / b; if (a % b != 0 && ((a < 0) != (b < 0))) q--;` (truncation is one too high for negative inexact quotients)."""),
        Card(r"""When is `(a + b - 1) / b` the ceiling of `a / b`?""",
             r"""Only for non-negative `a` and positive `b`. For a negative quotient, plain `a / b` already rounds up (toward zero)."""),
        Card(r"""How do you compute `a * b % m` for `a, b < m ≤ 10^18`?""",
             r"""`(long long)((__int128)a * b % m)`. Cast before multiplying. `cout` cannot print an `__int128` directly."""),
        Card(r"""Up to what magnitude does a `double` hold every integer exactly?""",
             r"""2^53 ≈ 9·10^15. Near 10^18 consecutive doubles are 128 apart, so `(double)(10^18 + 1) == 10^18`."""),
        Card(r"""Exact ⌊√n⌋ for `n ≤ 10^18`?""",
             r"""`r = (long long)sqrt((double)n); while (r*r > n) r--; while ((r+1)*(r+1) <= n) r++;`"""),
        Card(r"""What does `cout << 1000000.0;` print, and how do you avoid it?""",
             r"""`1e+06` (6 significant digits by default). Use `fixed << setprecision(k)`, or keep integer answers in integer types."""),
        Card(r"""Digit value of a char `c`, the k-th lowercase letter, and why `cout << toupper(c)` prints a number?""",
             r"""`c - '0'`; `char('a' + k)`; `toupper` returns `int`, so cast it: `char(toupper(c))`."""),
    ],
)
