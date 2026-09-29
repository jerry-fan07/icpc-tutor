from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)

MOD = 10**9 + 7


# ------------------------------------------------------------------ generators
def _switches(rng, n, m, solvable):
    rows = [rng.getrandbits(m) for _ in range(n)]
    if solvable:                                  # force some subset to XOR to all-ones
        k = rng.randint(1, n)
        chosen = rng.sample(range(n), k)
        acc = (1 << m) - 1
        for i in chosen[1:]:
            acc ^= rows[i]
        rows[chosen[0]] = acc
    lines = [f"{n} {m}"]
    for r in rows:
        lines.append("".join("1" if r >> j & 1 else "0" for j in range(m)))
    return "\n".join(lines) + "\n"


def _switch_small(rng):
    return _switches(rng, rng.randint(1, 8), rng.randint(1, 10), rng.random() < 0.6)


def _switch_wide(rng):
    """Few switches, wide masks: a failing case small enough to be shown."""
    return _switches(rng, rng.randint(2, 5), rng.randint(40, 60), True)


def _exp_queries(rng, n, amax, bmax):
    out = [str(n)]
    for _ in range(n):
        out.append(f"{rng.randint(0, amax)} {rng.randint(0, bmax)}")
    return "\n".join(out) + "\n"


def _exp_big(rng, n):
    out = [str(n)]
    for _ in range(n):
        out.append(f"{rng.randint(1, 10**9)} {rng.randint(10**9 - 10**6, 10**9)}")
    return "\n".join(out) + "\n"


def _exp2_queries(rng, n, amax, bmax, cmax):
    out = [str(n)]
    for _ in range(n):
        out.append(f"{rng.randint(0, amax)} {rng.randint(0, bmax)} {rng.randint(0, cmax)}")
    return "\n".join(out) + "\n"


def _fractions(rng, n, pmax, qmax):
    out = [str(n)]
    for _ in range(n):
        out.append(f"{rng.randint(-pmax, pmax)} {rng.randint(1, qmax)}")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- problems
LIGHT_SWITCHES = Problem(
    id="light_switches",
    title="Light Switches",
    difficulty="medium",
    complexity="O(2^n · n)",
    statement=r"""
A stage has `m` lamps, numbered 1 to `m`, all off. There are `n` switches; switch `i`
flips a fixed set of lamps (on becomes off, off becomes on). Pressing a switch twice
undoes it, so each switch is either pressed once or not at all.

What is the smallest number of switches to press so that every lamp ends up on?
""",
    input=r"""
The first line has `n` and `m` (1 ≤ n ≤ 20, 1 ≤ m ≤ 60).

Each of the next `n` lines has a string of `m` characters `0` or `1`: character `j` of
line `i` is `1` if switch `i` flips lamp `j`.
""",
    output=r"""
Print the minimum number of switches, or `-1` if no choice of switches turns every lamp on.
""",
    samples=[
        Test("3 4\n1100\n0110\n0011\n", "2\n",
             note="Switches 1 and 3 together flip every lamp exactly once."),
        Test("2 3\n110\n011\n", "-1\n"),
    ],
    tests=[
        Test("1 1\n1\n"),
        Test("1 1\n0\n"),
        Test("2 60\n" + "1" * 30 + "0" * 30 + "\n" + "0" * 30 + "1" * 30 + "\n"),
        Test("3 60\n" + "1" * 60 + "\n" + "1" * 59 + "0\n" + "0" * 59 + "1\n"),
    ],
    gens=[
        Gen("small random", _switch_small, 12),
        Gen("few switches, 40 to 60 lamps", _switch_wide, 4),
        Gen("n = 20, m = 60, solvable", lambda rng: _switches(rng, 20, 60, True), 2),
        Gen("n = 20, m = 60, random", lambda rng: _switches(rng, 20, 60, False), 1),
        Gen("n = 20, m = 20, solvable", lambda rng: _switches(rng, 20, 20, True), 1),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<long long> sw(n, 0);               // bit j set: this switch flips lamp j + 1
    for (int i = 0; i < n; i++) {
        string s;
        cin >> s;
        for (int j = 0; j < m; j++)
            if (s[j] == '1') sw[i] |= 1LL << j;   // 1LL: j goes up to 59
    }
    long long all = (1LL << m) - 1;
    int best = -1;
    for (int mask = 0; mask < (1 << n); mask++) {     // every subset of switches
        long long state = 0;
        for (int i = 0; i < n; i++)
            if (mask >> i & 1) state ^= sw[i];         // flipping twice cancels: XOR
        if (state == all) {
            int used = __builtin_popcount(mask);
            if (best == -1 || used < best) best = used;
        }
    }
    cout << best << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int n, m, best = -1;
vector<string> g;
void go(int i, vector<int>& lamp, int used) {
    if (i == n) {
        for (int j = 0; j < m; j++) if (!lamp[j]) return;
        if (best == -1 || used < best) best = used;
        return;
    }
    go(i + 1, lamp, used);
    for (int j = 0; j < m; j++) if (g[i][j] == '1') lamp[j] ^= 1;
    go(i + 1, lamp, used + 1);
    for (int j = 0; j < m; j++) if (g[i][j] == '1') lamp[j] ^= 1;
}
int main() {
    cin >> n >> m;
    g.resize(n);
    for (auto& s : g) cin >> s;
    vector<int> lamp(m, 0);
    go(0, lamp, 0);
    cout << best << '\n';
}
""",
    hints=[
        r"""`n ≤ 20` means 2^20 ≈ 10^6 subsets: try them all. Store each switch as a 64-bit mask
of the lamps it flips; pressing a set of switches gives the XOR of their masks.""",
        r"""`m` goes up to 60, so build the masks with `1LL << j`. With `1 << j`, lamps 32 and up
land on the wrong bits (the shift is undefined past 31; in practice it wraps around).""",
        r"""All lamps on is the mask `(1LL << m) - 1`. The number of switches in a subset is
`__builtin_popcount(mask)`.""",
    ],
    editorial=r"""
Each switch is a 60-bit mask. Pressing switch `i` XORs its mask into the lamp state, and
XOR is associative, commutative and its own inverse, so the order of presses does not
matter and pressing twice cancels. The final state of a set of switches is the XOR of
their masks, and we want it to equal `(1LL << m) - 1`.

With `n ≤ 20` there are at most 2^20 subsets; for each, XOR the chosen masks (20 steps)
and compare: about 2·10^7 operations. The answer is the smallest `popcount(mask)` among
the subsets that work.

The trap is the width. `1 << j` is an `int` shift, undefined for `j ≥ 31`; on this judge
it wraps (`1 << 40` gives 256), silently mapping lamp 41 onto lamp 9. Every shift that can
exceed 30 must be `1LL << j`, and so must the "all on" mask.
""",
)

COUNTING_BITS = Problem(
    id="counting_bits",
    title="Counting Bits",
    difficulty="medium",
    source="CSES 1146 - Counting Bits",
    complexity="O(log n)",
    statement=r"""
Write the numbers 1, 2, ..., n in binary. How many one bits did you write in total?
""",
    input=r"""
One integer `n` (1 ≤ n ≤ 10^15).
""",
    output=r"""
Print the total number of one bits in the binary representations of 1..n.
""",
    samples=[
        Test("7\n", "12\n", note="1, 10, 11, 100, 101, 110, 111: 1+1+2+1+2+2+3 = 12."),
        Test("16\n", "33\n"),
    ],
    tests=[
        Test("1\n"),
        Test("1023\n"),
        Test("2147483653\n"),
    ],
    gens=[
        Gen("small n", lambda rng: f"{rng.randint(1, 3000)}\n", 10),
        Gen("medium n", lambda rng: f"{rng.randint(10**6, 10**7)}\n", 2),
        Gen("n = 10^15", lambda rng: "1000000000000000\n", 1, large=True),
        Gen("n near 10^15", lambda rng: f"{rng.randint(10**14, 10**15)}\n", 2, large=True),
        Gen("n = 2^k - 1, large", lambda rng: f"{(1 << rng.randint(40, 49)) - 1}\n", 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long n;
    cin >> n;
    long long total = 0;
    // Bit k of 0, 1, 2, ... repeats with period 2^(k+1): 2^k zeros, then 2^k ones.
    for (int k = 0; (1LL << k) <= n; k++) {
        long long half = 1LL << k, period = half << 1;
        long long full = (n + 1) / period;    // complete periods among 0..n
        long long rest = (n + 1) % period;    // numbers in the last, partial period
        total += full * half + max(0LL, rest - half);
    }
    cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long n;
    cin >> n;
    long long total = 0;
    for (long long i = 1; i <= n; i++) total += __builtin_popcountll(i);
    cout << total << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long n;
    cin >> n;
    long long total = 0;
    for (long long i = 1; i <= n; i++) total += __builtin_popcountll(i);
    cout << total << '\n';
}
""",
    hints=[
        r"""10^15 numbers cannot be visited one by one. Count per bit position instead: how many
of 0..n have bit `k` set?""",
        r"""Write bit `k` of 0, 1, 2, 3, ... in a column: 2^k zeros, 2^k ones, 2^k zeros, ... So
among 0..n (that is, `n + 1` numbers), there are `(n+1) / 2^(k+1)` complete periods, each
with 2^k ones, and then a partial period of `(n+1) % 2^(k+1)` numbers, of which
`max(0, rest - 2^k)` have the bit set.""",
        r"""Every shift here must be `1LL << k`: `n` has up to 50 bits.""",
    ],
    editorial=r"""
Sum over bit positions instead of over numbers. Bit `k` of the sequence 0, 1, 2, ...
follows a pattern of period 2^(k+1): 2^k zeros, then 2^k ones. Among the `n + 1` numbers
0..n there are `full = (n+1) / 2^(k+1)` complete periods, contributing `full · 2^k` ones,
and a partial period of `rest = (n+1) mod 2^(k+1)` numbers, whose first 2^k have the bit
clear and the rest set: `max(0, rest − 2^k)` more. Only positions with 2^k ≤ n matter,
about 50 of them. O(log n).

The loop over every number with `__builtin_popcountll` is correct and would need about
10^15 steps. Two bit-level traps: `1 << k` is an `int` shift and breaks from `k = 31`
(one hidden test is n = 2^31 + 5), and `__builtin_popcount` (no `ll`) silently takes only
the low 32 bits of a `long long`.
""",
)

EXPONENTIATION = Problem(
    id="exponentiation",
    title="Exponentiation",
    difficulty="easy",
    source="CSES 1095 - Exponentiation",
    complexity="O(n log b)",
    statement=r"""
Compute a^b modulo 10^9 + 7 for `n` pairs `(a, b)`. By convention, 0^0 = 1.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has two integers `a` and `b` (0 ≤ a, b ≤ 10^9).
""",
    output=r"""
For each pair, print a^b mod (10^9 + 7) on its own line.
""",
    samples=[
        Test("3\n3 4\n2 8\n123 123\n", "81\n256\n921450052\n"),
    ],
    tests=[
        Test("3\n0 0\n0 5\n5 0\n"),
        Test("2\n1000000000 2\n999999999 3\n"),
    ],
    gens=[
        Gen("small", lambda rng: _exp_queries(rng, 20, 20, 30), 6),
        Gen("big bases, small exponents", lambda rng: _exp_queries(rng, 50, 10**9, 2000), 4),
        # handwritten, but with exponents the O(b) brute cannot check: marked large
        Gen("extreme exponents", lambda rng: "3\n1 1000000000\n1000000000 1000000000\n2 1000000000\n",
            1, large=True),
        Gen("max size, huge exponents", lambda rng: _exp_big(rng, 200000), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;

long long power(long long a, long long b, long long m) {
    long long r = 1;
    a %= m;
    while (b > 0) {
        if (b & 1) r = r * a % m;            // this bit of b is set: take the current a^(2^k)
        a = a * a % m;                        // a^(2^k) -> a^(2^(k+1)); below m^2 < 9.2e18
        b >>= 1;
    }
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    while (n--) {
        long long a, b;
        cin >> a >> b;
        cout << power(a, b, MOD) << '\n';
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
    while (n--) {
        long long a, b, r = 1;
        cin >> a >> b;
        for (long long i = 0; i < b; i++) r = r * (a % 1000000007) % 1000000007;
        cout << r << '\n';
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
    while (n--) {
        long long a, b, r = 1;
        cin >> a >> b;
        for (long long i = 0; i < b; i++) r = r * a % 1000000007;
        cout << r << '\n';
    }
}
""",
    hints=[
        r"""Multiplying `b` times is up to 10^9 steps per query. What is a^b when `b` is even, in
terms of a^(b/2)?""",
        r"""Binary exponentiation: walk through the bits of `b`, squaring `a` at each step and
multiplying it into the result when the bit is 1. About 30 steps for `b ≤ 10^9`.""",
        r"""Keep everything in `long long` and reduce after every multiplication: two values below
10^9 + 7 multiply to about 10^18, which fits; three do not.""",
    ],
    editorial=r"""
Binary exponentiation. Write `b` in binary, `b = Σ 2^k` over its set bits; then a^b is the
product of a^(2^k) over those bits, and each a^(2^(k+1)) is the square of a^(2^k). So one
loop over the ~30 bits of `b` squares a running power and multiplies it into the answer
when the bit is set: O(log b) per query, about 6·10^6 multiplications in all.

Every product is reduced mod 10^9 + 7 immediately, so both factors are below 10^9 + 7 and
the product is below 1.0·10^18, inside `long long`. With `int` the very first square
overflows. The naive loop of `b` multiplications is 10^9 steps for a single query.
""",
)

EXPONENTIATION_II = Problem(
    id="exponentiation_ii",
    title="Exponentiation II",
    difficulty="medium",
    source="CSES 1712 - Exponentiation II",
    complexity="O(n log MOD)",
    statement=r"""
Compute a^(b^c) modulo 10^9 + 7 for `n` triples `(a, b, c)`. The exponent is `b` to the
power `c`, which can be astronomically large. By convention, 0^0 = 1.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 10^5).

Each of the next `n` lines has three integers `a`, `b`, `c` (0 ≤ a, b, c ≤ 10^9).
""",
    output=r"""
For each triple, print a^(b^c) mod (10^9 + 7) on its own line.
""",
    samples=[
        Test("3\n3 7 1\n15 2 2\n3 4 5\n", "2187\n50625\n763327764\n"),
    ],
    tests=[
        Test("5\n0 0 0\n0 0 1\n0 5 3\n7 0 5\n7 5 0\n"),
        Test("3\n5 500000003 1\n5 500000003 2\n1000000000 1000000000 2\n"),
    ],
    gens=[
        Gen("small", lambda rng: _exp2_queries(rng, 20, 6, 6, 6), 6),
        Gen("big a and b, c up to 300", lambda rng: _exp2_queries(rng, 20, 10**9, 10**9, 300), 4),
        # handwritten, but with c too large for the iterate-c-times brute: marked large
        Gen("extreme values", lambda rng: "3\n2 1000000000 1000000000\n1000000000 1000000000 1000000000\n0 1000000000 1000000000\n",
            1, large=True),
        Gen("max size", lambda rng: _exp2_queries(rng, 100000, 10**9, 10**9, 10**9), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;             // prime

long long power(long long a, long long b, long long m) {   // the modulus is a parameter
    long long r = 1 % m;
    a %= m;
    while (b > 0) {
        if (b & 1) r = r * a % m;
        a = a * a % m;
        b >>= 1;
    }
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    while (n--) {
        long long a, b, c;
        cin >> a >> b >> c;
        // Fermat: a^(MOD-1) = 1 for a not divisible by MOD, so exponents repeat with period
        // MOD - 1. Reduce b^c modulo MOD - 1, not MOD. (For a = 0 this still works here:
        // b^c is 0 mod MOD-1 = 2 * 500000003 only when b^c = 0, since b <= 10^9.)
        long long e = power(b, c, MOD - 1);
        cout << power(a, e, MOD) << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
const long long M = 1000000007;
long long pw(long long a, long long b) {
    long long r = 1;
    a %= M;
    while (b > 0) { if (b & 1) r = r * a % M; a = a * a % M; b >>= 1; }
    return r;
}
int main() {
    int n;
    cin >> n;
    while (n--) {
        long long a, b, c;
        cin >> a >> b >> c;
        // a^(b^c) = (...((a^b)^b)...)^b, with c powers: no exponent reduction needed
        long long x = a % M;
        for (long long i = 0; i < c; i++) x = pw(x, b);
        cout << x << '\n';
    }
}
""",
    hints=[
        r"""You cannot compute b^c exactly: it can have 9·10^9 digits. You need b^c modulo
*something*. Which modulus makes a^e depend only on that remainder?""",
        r"""Fermat's little theorem: for prime p and `a` not divisible by p, a^(p−1) ≡ 1. So a^e
depends only on `e mod (p − 1)`. Compute `e = b^c mod (10^9 + 6)`, then a^e mod 10^9 + 7.""",
        r"""Write `power(a, b, m)` with the modulus as a parameter: you need it with two different
moduli. A version with `MOD` hard-coded inside is the classic bug here.""",
    ],
    editorial=r"""
Let p = 10^9 + 7, a prime. For `a` not divisible by p, Fermat's little theorem gives
a^(p−1) ≡ 1 (mod p), so powers of `a` repeat with period p − 1, and a^e ≡ a^(e mod (p−1)).
So compute `e = b^c mod (p − 1)` by fast exponentiation, then `a^e mod p`.

Reducing the exponent mod p instead is the tempting bug: it passes the samples (their
exponents are below p, so no reduction happens) and fails as soon as b^c is large.

The case a = 0 needs a thought, because Fermat says nothing about it: 0^e is 0 for e > 0
and 1 for e = 0, so the reduced exponent must be 0 exactly when b^c is. Here p − 1 =
2 · 500000003 with 500000003 prime, and b ≤ 10^9 cannot be divisible by both factors, so
b^c ≡ 0 (mod p − 1) only when b = 0 and c ≥ 1, i.e. when b^c really is 0. (In general
you would special-case a mod p = 0.)
""",
)

MOD_FRACTIONS = Problem(
    id="mod_fractions",
    title="Fractions Modulo a Prime",
    difficulty="medium",
    complexity="O(n log MOD)",
    statement=r"""
A physics lab stores measurements as fractions p_i / q_i. You need their sum, but the lab's
software wants every result modulo the prime M = 10^9 + 7.

A fraction P/Q (with Q not divisible by M) is represented modulo M by the unique `r` with
0 ≤ r < M and r · Q ≡ P (mod M). For example, 1/2 is represented by 500000004, because
2 · 500000004 = 1000000008 ≡ 1. Sums of fractions correspond to sums of their
representatives.

Print the representative of p_1/q_1 + p_2/q_2 + ... + p_n/q_n.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5).

Each of the next `n` lines has two integers p_i and q_i (−10^9 ≤ p_i ≤ 10^9,
1 ≤ q_i ≤ 10^9).
""",
    output=r"""
Print one integer in `[0, 10^9 + 7)`.
""",
    samples=[
        Test("2\n1 2\n1 3\n", "833333340\n", note="1/2 + 1/3 = 5/6, and 6 · 833333340 ≡ 5."),
        Test("1\n-1 2\n", "500000003\n",
             note="−1/2 is represented by 10^9 + 7 − 500000004. The answer is never negative."),
    ],
    tests=[
        Test("1\n0 7\n"),
        Test("1\n-1000000000 1\n"),
        Test("2\n1000000000 1000000000\n-1000000000 999999999\n"),
        Test("3\n1 3\n1 3\n1 3\n"),
    ],
    gens=[
        Gen("small", lambda rng: _fractions(rng, rng.randint(1, 6), 50, 30), 10),
        Gen("small, big numerators", lambda rng: _fractions(rng, rng.randint(1, 3), 10**9, 30), 4),
        Gen("max size", lambda rng: _fractions(rng, 200000, 10**9, 10**9), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;

long long power(long long a, long long b) {
    long long r = 1;
    a %= MOD;
    while (b > 0) {
        if (b & 1) r = r * a % MOD;
        a = a * a % MOD;
        b >>= 1;
    }
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    long long ans = 0;
    while (n--) {
        long long p, q;
        cin >> p >> q;
        p %= MOD;
        if (p < 0) p += MOD;                  // C++ % keeps the sign of p
        long long inv = power(q, MOD - 2);    // Fermat: q^(M-2) * q = q^(M-1) = 1
        ans = (ans + p * inv) % MOD;          // p, inv < M: the product fits in long long
    }
    cout << ans << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
typedef __int128 L;
L g(L a, L b) { if (a < 0) a = -a; if (b < 0) b = -b; while (b) { L t = a % b; a = b; b = t; } return a; }
long long inv_euclid(long long a, long long m) {       // extended Euclid, not Fermat
    long long old_r = a, r = m, old_s = 1, s = 0;
    while (r) {
        long long q = old_r / r, t;
        t = old_r - q * r; old_r = r; r = t;
        t = old_s - q * s; old_s = s; s = t;
    }
    return ((old_s % m) + m) % m;
}
int main() {
    int n;
    cin >> n;
    L num = 0, den = 1;                                // the exact sum, in lowest terms
    for (int i = 0; i < n; i++) {
        long long p, q;
        cin >> p >> q;
        num = num * q + (L)p * den;
        den = den * q;
        L d = g(num, den);
        if (d > 1) { num /= d; den /= d; }
    }
    const long long M = 1000000007;
    long long P = (long long)(((num % M) + M) % M), Q = (long long)(den % M);
    cout << (long long)((L)P * inv_euclid(Q, M) % M) << '\n';
}
""",
    hints=[
        r"""Dividing by `q` modulo a prime means multiplying by the inverse of `q`, and Fermat
gives it: q^(M−2) mod M.""",
        r"""Normalise each numerator into `[0, M)` first: in C++, `-1 % M` is `-1`, not `M - 1`.""",
        r"""Accumulate `ans = (ans + p * inv) % M` with everything in `long long`: `p` and `inv`
are below M, so the product is below 1.0·10^18.""",
    ],
    editorial=r"""
Modulo a prime M, every `q` not divisible by M has an inverse, and by Fermat's little
theorem it is q^(M−2): q · q^(M−2) = q^(M−1) ≡ 1. So p/q is represented by
`p · q^(M−2) mod M`, computed with fast exponentiation, and the representatives simply add.
Here every q_i ≤ 10^9 < M, so no inverse is ever missing. O(n log M).

Two C++ details decide the verdict. Negative numerators: `%` truncates toward zero, so
`(-1) % M == -1`; add M when the remainder is negative, or the running sum drifts below
zero and the final print is negative. Overflow: `p * inv` is up to about 10^18, which fits in
`long long` only because both factors were reduced below M first.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="cpp10",
    title="bits & modular arithmetic",
    track="cpp",
    order=10,
    summary="Integers as bit strings: the operators and their precedence trap, masks and "
            "subsets, the builtins, XOR; then arithmetic modulo 10^9 + 7: overflow, "
            "negatives, fast exponentiation and inverses by Fermat.",
    prereqs=["cpp08"],
    tags=["bits", "bitmask", "subsets", "popcount", "xor", "modular arithmetic",
          "fast exponentiation", "fermat", "modular inverse"],
    parts=[
        Part("Integers are bit strings", [
            Say(r"""
In Python an integer is an arbitrary-size number, and you rarely think about its bits. In
C++ an `int` is exactly 32 bits and a `long long` exactly 64, and contest code uses those
bits directly: as sets, as flags, as cheap arithmetic.

`13` is `1101` in binary: bits 3, 2 and 0 are set (bit `k` is worth 2^k, counting from 0
on the right). The operators work bit by bit:

```text
a & b     1 where both bits are 1       1100 & 1010 = 1000
a | b     1 where either bit is 1       1100 | 1010 = 1110
a ^ b     1 where the bits differ       1100 ^ 1010 = 0110
~a        every bit flipped
a << k    shift left, zeros in: a * 2^k      0011 << 2 = 1100
a >> k    shift right: a / 2^k, rounded down 1101 >> 1 = 0110
```

Python has the same six operators with the same meanings. The differences are in the
fixed width, and in one precedence rule.
"""),
            Short(r"""
What does this print?

```cpp
cout << (5 & 3) << ' ' << (5 | 3) << ' ' << (5 ^ 3) << '\n';
```
""", accept=["1 7 6"], placeholder="three numbers",
                hint="5 = 101, 3 = 011.",
                explain=r"""
`101 & 011 = 001`, `101 | 011 = 111`, `101 ^ 011 = 110`: `1 7 6`.
"""),
            Short(r"""
And `cout << ~5;`?
""", accept=["-6"], placeholder="a number",
                hint="Negative numbers are stored in two's complement: `-x` is `~x + 1`.",
                explain=r"""
`-6`. In two's complement, `~x` is `-x - 1` for every `x` (Python agrees: `~5 == -6`).
Rearranged, `-x = ~x + 1`, which is how the machine negates, and why `x & -x` will turn
out to isolate the lowest set bit.
"""),
            Short(r"""
Shifting right rounds down; dividing truncates toward zero. What does this print?

```cpp
cout << (-7 >> 1) << ' ' << (-7 / 2) << '\n';
```
""", accept=["-4 -3"], placeholder="two numbers",
                explain=r"""
`-4 -3`. `>>` on a negative number shifts in copies of the sign bit (GCC always does this,
and C++20 requires it), which rounds toward minus infinity, like Python's `>>` and `//`.
`/` truncates toward zero. For non-negative numbers the two agree, which is why `x >> 1`
and `x / 2` are interchangeable in most contest code.
"""),
            MCQ(r"""
You want to print whether `x` is even. What does this do for `x = 6`?

```cpp
if (x & 1 == 0) cout << "even\n";
else cout << "odd\n";
```
""", [
                Opt("Prints `even`.",
                    why="That is what it means to a human. The compiler reads it differently: `==` "
                        "binds tighter than `&`."),
                Opt("Prints `odd`, and does so for every `x`.", correct=True,
                    why="Yes. It parses as `x & (1 == 0)`, that is `x & 0`, which is always 0. "
                        "GCC with `-Wall` says: suggest parentheses around comparison in "
                        "operand of '&'. The judge here shows that warning; read it."),
                Opt("Does not compile: `&` needs two integers.",
                    why="`1 == 0` is a `bool`, which converts to the integer 0 without complaint. "
                        "It compiles, with a warning."),
            ], explain=r"""
In C++ the bitwise operators `&`, `^`, `|` bind *weaker* than `==` and `<`, a leftover
from C. Python ranks them above comparisons, so the same line means what it says there,
which is exactly why Python programmers write it. The C++ rule: **parenthesise every
bitwise expression** inside a comparison, `(x & 1) == 0`.
"""),
            Short(r"""
Shifts have their own precedence surprise. What is `1 << 2 + 1`?
""", accept=["8"], placeholder="a number",
                explain=r"""
`8`: `+` binds tighter than `<<`, so it is `1 << 3`. Arithmetic first, then shifts, then
comparisons, then `&`, `^`, `|`, then `&&`, `||`. When in doubt, parenthesise.
"""),
        ]),
        Part("Shifts past 31: the 1LL rule", [
            MCQ(r"""
What does this print, when the input is `40`?

```cpp
int k;
cin >> k;
cout << (1 << k) << '\n';
```
""", [
                Opt("1099511627776",
                    why="That is 2^40, and it is Python's answer. Here `1` is an `int`, so the "
                        "shift happens in 32 bits, where 2^40 does not exist."),
                Opt("0: the bit is shifted out.",
                    why="That is what GCC prints for the literal `1 << 40`, which it folds at compile "
                        "time (with a warning). With `k` read at run time, the hardware decides, "
                        "and it does something else. The language promises neither."),
                Opt("Anything: shifting a 32-bit value by 32 or more is undefined. Here it prints 256.",
                    correct=True,
                    why="Yes. ARM and x86 hardware both use only the low 5 bits of the count, so "
                        "`1 << 40` computes `1 << 8`. No crash, no warning, just the wrong bit."),
                Opt("A compile error.",
                    why="With a literal `1 << 40` GCC warns; with `k` read from input it cannot "
                        "know. It compiles silently."),
            ]),
            Short(r"""
And `cout << (1 << 31);`? (Assume the usual two's-complement behaviour.)
""", accept=["-2147483648"], placeholder="a number",
                explain=r"""
`-2147483648`. Bit 31 of an `int` is the sign bit, so `1 << 31` is `INT_MIN`. For an `int`,
only bits 0 to 30 are safe as flags.
"""),
            Say(r"""
The fix is the same as for overflow in cpp02: make the left operand 64-bit **before** the
shift.

```cpp
1LL << k        // long long: fine for k up to 62
1ULL << k       // unsigned long long: fine up to 63
(1LL << m) - 1  // the mask with the low m bits set: "all of m items"
```

The trap is that `long long mask = 1 << k;` looks 64-bit and is not: the shift happens in
`int` and only the (already wrong) result is widened. Same story as `long long x = a * b;`.
"""),
            MCQ(r"""
Which line correctly sets bit `j` (0 ≤ j < 60) of `long long mask`?
""", [
                Opt("`mask |= 1 << j;`",
                    why="The shift is done in `int`. For `j ≥ 31` it sets the wrong bit (or the "
                        "sign bit, which sign-extends into bits 31 to 63)."),
                Opt("`mask |= (long long)(1 << j);`",
                    why="The cast comes after the shift, which has already gone wrong. Widen "
                        "before shifting, not after."),
                Opt("`mask |= 1LL << j;`", correct=True,
                    why="Yes: the `1` is 64-bit, so the shift is too."),
                Opt("`mask += pow(2, j);`",
                    why="`pow` returns a `double`, so `mask` is converted to `double`, added to, and "
                        "converted back, and a `double` keeps only 53 bits: measured here, with bits "
                        "59 and 0 set, adding 2^58 loses bit 0. It also adds twice if the bit was "
                        "already set."),
            ]),
        ]),
        Part("Masks and the builtins", [
            Say(r"""
Four idioms cover almost everything you do to single bits:

```cpp
(x >> k) & 1      // is bit k of x set?
x | (1 << k)      // x with bit k set
x & ~(1 << k)     // x with bit k cleared
x ^ (1 << k)      // x with bit k flipped
```

(Use `1LL` whenever `k` can reach 31.) GCC also has builtins that compile to single
instructions: `__builtin_popcount(x)` counts set bits, `__builtin_ctz(x)` counts trailing
zeros (the index of the lowest set bit), `__builtin_clz(x)` counts leading zeros. Each has
an `ll` version for `long long`: `__builtin_popcountll`, `__builtin_ctzll`,
`__builtin_clzll`.
"""),
            Short(r"""
Let `x = 40`, which is `101000` in binary. What do these three expressions evaluate to?
`(x >> 3) & 1`, `x & ~(1 << 3)`, `x ^ (1 << 5)`. Answer with three numbers.
""", accept=["1 32 8"], placeholder="three numbers",
                explain=r"""
Bit 3 is set, so `1`. Clearing it leaves `100000 = 32`. Flipping bit 5 (which is set)
leaves `001000 = 8`.
"""),
            MCQ(r"""
What does `x & -x` compute? (Try `x = 40 = 101000`: `-x` is `~x + 1`.)
""", [
                Opt("0 for every `x`: a number and its negative share no bits.",
                    why="Work it out: `~40` ends in `...010111`; adding 1 gives `...011000`. It "
                        "shares bit 3 with `101000`."),
                Opt("The lowest set bit of `x`, as a value: 8 for 40.", correct=True,
                    why="Yes. Adding 1 to `~x` carries through its trailing ones (the trailing "
                        "zeros of `x`) and stops exactly at the lowest set bit of `x`: the only "
                        "position where both `x` and `-x` have a 1."),
                Opt("The absolute value of `x`.",
                    why="`40 & -40` is 8, not 40."),
                Opt("The highest set bit of `x`.",
                    why="The carry stops at the *lowest* set bit. The highest comes from "
                        "`__builtin_clz`: `31 - __builtin_clz(x)` is its index."),
            ], explain=r"""
Two companions: `x & (x - 1)` *clears* the lowest set bit (40 becomes 32), so
`x > 0 && (x & (x - 1)) == 0` tests "is `x` a power of two". And `x & -x` is the heart of
the Fenwick tree in algo15.
"""),
            Short(r"""
What do `__builtin_ctz(40)`, `__builtin_popcount(255)` and `31 - __builtin_clz(1000)`
return? Three numbers.
""", accept=["3 8 9"], placeholder="three numbers",
                hint="40 = 101000. 255 = 11111111. 2^9 = 512 ≤ 1000 < 1024.",
                explain=r"""
`3 8 9`. The last is floor(log2(1000)): the index of the highest set bit. GCC also spells
it `__lg(x)`. For `long long`, use `63 - __builtin_clzll(x)`.
"""),
            MCQ(r"""
What does this print?

```cpp
long long x = (1LL << 40) | 1;
cout << __builtin_popcount(x) << '\n';
```
""", [
                Opt("2", why="That is `__builtin_popcountll(x)`. The version without `ll` takes an "
                             "`unsigned int`, so `x` is first cut down to its low 32 bits."),
                Opt("1", correct=True,
                    why="Yes: bit 40 is lost in the conversion to 32 bits, and only bit 0 is "
                        "counted. GCC does not warn with `-Wall`. Always match the suffix to the "
                        "type: `ll` for `long long`."),
                Opt("A compile error: wrong argument type.",
                    why="The conversion from `long long` to `unsigned int` is implicit and silent."),
            ]),
            MCQ(r"""
What is `__builtin_ctz(0)`?
""", [
                Opt("32: all 32 bits are trailing zeros.",
                    why="That is what this ARM machine happens to return. The documentation says "
                        "the result is undefined, and on x86 the instruction behind it leaves "
                        "garbage."),
                Opt("0",
                    why="There is no lowest set bit to count up to. The result is undefined."),
                Opt("Undefined: `ctz` and `clz` of 0 have no meaning, so check for 0 first.",
                    correct=True,
                    why="Right. `popcount(0)` is fine (0), but `ctz(0)` and `clz(0)` must be "
                        "guarded, typically `x ? __builtin_ctz(x) : 32`."),
            ]),
        ]),
        Part("Every subset of n ≤ 20 things", [
            Say(r"""
A subset of `n` items `0..n−1` is exactly an `n`-bit number: bit `i` says whether item `i`
is in. So "try every subset" is a plain loop over the integers `0` to `2^n − 1`:

```cpp
for (int mask = 0; mask < (1 << n); mask++) {
    long long sum = 0;
    for (int i = 0; i < n; i++)
        if ((mask >> i) & 1) sum += w[i];
    // this subset has total weight sum, and __builtin_popcount(mask) items
}
```

No recursion, no vector of chosen items. This is what cpp08's table meant by n ≤ 20: 2^n.
"""),
            Numeric(r"""
For `n = 20`, about how many times does the inner `if` run in total?
""", answer=2.1e7, rel=0.5, unit="times",
                explain=r"""
`2^20 · 20 ≈ 2.1·10^7`: a few hundredths of a second. At `n = 25` it would be 8·10^8, and
at `n = 40`, 4·10^13: past 20 or so, subsets need a smarter idea (meet in the middle,
algo05).
"""),
            Short(r"""
Items have weights `w = {5, 2, 7}` (item 0 weighs 5). Which mask, written as a decimal
number, selects exactly the items with total weight 12?
""", accept=["5"], placeholder="a number",
                hint="Which items sum to 12? Then set their bits.",
                explain=r"""
Items 0 and 2 (5 + 7 = 12): bits 0 and 2, `101` in binary, which is `5`.
"""),
            Reflect(r"""
The loop above spends `n` steps per mask recomputing a sum from scratch. How could each
mask reuse the sum of a smaller mask that was already computed, so that the whole loop
costs O(2^n)?
""", answer=r"""
Masks are visited in increasing order, and removing any bit gives a smaller mask. So
store `sum[mask]` in an array of size 2^n and compute it from the mask with its lowest set
bit removed: `sum[mask] = sum[mask & (mask - 1)] + w[__builtin_ctz(mask)]`. One step per
mask, O(2^n) in total, at the price of 2^n memory. This "smaller mask was already done"
idea is the base of bitmask DP (algo08).
"""),
            Try("light_switches", note="Up to 20 switches: try every subset. Up to 60 lamps: "
                "`1LL`."),
        ]),
        Part("XOR", [
            Say(r"""
XOR deserves its own section, because it behaves like addition without carries:

- `x ^ x = 0` and `x ^ 0 = x`
- it is commutative and associative, so order and grouping do not matter
- so XOR-ing a list in which values come in pairs cancels the pairs

That makes XOR the natural operation for "flip", for parity, and for toggles that undo
themselves (the light switches you just met).
"""),
            Short(r"""
What is `4 ^ 7 ^ 4 ^ 9 ^ 7`?
""", accept=["9"], placeholder="a number",
                explain=r"""
`9`. The two 4s cancel, the two 7s cancel. This is the classic "every value appears twice
except one; find it" trick, in O(n) time and O(1) memory.
"""),
            MCQ(r"""
The numbers 1..n are written down, one is erased, and you get the remaining `n − 1`. You
want to find the missing one without overflow worries. Which works?
""", [
                Opt("XOR all of 1..n together with all the given numbers; the result is the missing one.",
                    correct=True,
                    why="Yes: every present number appears twice and cancels, the missing one "
                        "appears once. XOR never overflows."),
                Opt("Sort and look for a gap.",
                    why="Correct, but O(n log n) and it needs to store everything. The XOR trick "
                        "is O(n) and streams."),
                Opt("XOR all the given numbers; the result is the missing one.",
                    why="Without also XOR-ing 1..n, nothing cancels. For n = 4 with 4 erased, "
                        "you get `1 ^ 2 ^ 3 = 0`, not 4. (Small cases can look right by "
                        "coincidence: n = 3 with 2 erased gives `1 ^ 3 = 2`.)"),
            ], explain=r"""
The sum `n(n+1)/2` minus the given numbers also works, as long as it is `long long`. XOR is
the version with nothing to overflow.
"""),
            Say(r"""
Bits also count well by *position*. Write 0, 1, 2, 3, ... in binary in a column and look
at bit `k` alone: it reads 2^k zeros, then 2^k ones, then 2^k zeros, repeating with period
2^(k+1). For bit 0: `0 1 0 1 ...`; for bit 1: `0 0 1 1 0 0 1 1 ...`.
"""),
            Numeric(r"""
How many of the numbers 0, 1, ..., 12 have bit 1 (the bit worth 2) set?
""", answer=6, unit="numbers",
                hint="Period 4: `0 0 1 1`. How many full periods fit in the 13 numbers, and what "
                     "is left over?",
                explain=r"""
Three full periods (0..11) with two each, plus the partial period `{12}`, which starts
with zeros: 6 (they are 2, 3, 6, 7, 10, 11). In general: `(n+1) / 2^(k+1)` full periods of
2^k ones, plus `max(0, (n+1) % 2^(k+1) − 2^k)`. Summing that over all `k` counts every one
bit in 1..n in O(log n), even for n = 10^15.
"""),
            Try("counting_bits", note="n up to 10^15: count per bit position, and every shift "
                "is `1LL <<`."),
        ]),
        Part("Why modulo 10^9 + 7", [
            Say(r"""
Counting problems have huge answers: the number of subsets of 10^5 items is 2^100000,
about 30,000 digits. Python could hold it, slowly; C++ cannot hold it at all. So problems
ask for the answer **modulo 10^9 + 7**, and you reduce as you go, because addition and
multiplication respect remainders:

```text
(a + b) mod m = ((a mod m) + (b mod m)) mod m
(a · b) mod m = ((a mod m) · (b mod m)) mod m
```

You never hold the true value, only its remainder, and every intermediate stays small.
"""),
            MCQ(r"""
Why 10^9 + 7 in particular?
""", [
                Opt("It is prime, and below 2^30, so sums of two residues fit in `int` and products of two fit in `long long`.",
                    correct=True,
                    why="Yes on all counts. Prime means every non-zero residue has an inverse "
                        "(division works, as you will see). And (10^9 + 7)^2 ≈ 1.0·10^18 < "
                        "9.2·10^18."),
                Opt("It is the largest prime that fits in an `int`.",
                    why="That is 2^31 − 1 = 2147483647. With it, the sum of two residues would "
                        "overflow `int`."),
                Opt("Tradition: any large number would do.",
                    why="A non-prime modulus breaks division, and a larger one makes products "
                        "overflow `long long`. 998244353 is the other common choice, also prime "
                        "and below 2^30."),
            ]),
            Short(r"""
Compute by hand: `999999999 · 999999999 mod (10^9 + 7)`.
""", accept=["64"], placeholder="a number",
                hint="999999999 = (10^9 + 7) − 8, so it is −8 modulo 10^9 + 7.",
                explain=r"""
`(−8) · (−8) = 64`. Now the C++ trap: with `int a = 999999999, b = 999999999;` the
expression `a * b % MOD` multiplies in 32 bits first and overflows; on this machine it
prints 808348673. `1LL * a * b % MOD` prints 64. Multiply residues in `long long`, and
reduce immediately after every multiplication.
"""),
            Short(r"""
Subtraction has its own trap. What does `cout << (3 - 5) % 7;` print in C++?
""", accept=["-2"], placeholder="a number",
                explain=r"""
`-2`, not Python's `5`: C++ `%` keeps the sign of the left operand. A residue that goes
negative stays negative, and a negative index or a negative printed answer is WA. The fix
after any subtraction: `((a - b) % m + m) % m`, or `x %= m; if (x < 0) x += m;`.
"""),
            MCQ(r"""
And division? `(12 / 4) mod 7 = 3`. What goes wrong with "reduce first, then divide"?
""", [
                Opt("Nothing: `(12 mod 7) / (4 mod 7) = 5 / 4 = 1` in integer division, and that is the answer.",
                    why="The answer is 3, not 1. The remainder of a quotient is not the quotient of "
                        "the remainders: integer division does not survive reduction."),
                Opt("`5 / 4` is not an integer: division does not survive reduction. You multiply by an inverse instead.",
                    correct=True,
                    why="Yes. Modulo a prime `p`, dividing by `b` means multiplying by the number "
                        "`b⁻¹` with `b · b⁻¹ ≡ 1`. Here `4⁻¹ ≡ 2` (4 · 2 = 8 ≡ 1), and "
                        "`5 · 2 = 10 ≡ 3`, the right answer."),
                Opt("It works as long as you use `double`.",
                    why="`5.0 / 4 = 1.25` is not a residue. Floating point cannot represent the "
                        "answer mod 7 at all."),
            ]),
        ]),
        Part("Fast exponentiation and inverses", [
            Numeric(r"""
Computing a^b mod m by multiplying `b` times: with `b = 10^9` and 2·10^5 such queries,
how many multiplications in total?
""", answer=2e14, rel=0.5, unit="multiplications",
                explain=r"""
`2·10^14`: on the 10^8-per-second budget, about three weeks. The exponent needs O(log b)
work, not O(b).
"""),
            Reflect(r"""
How can you get a^b with far fewer than `b` multiplications? Hint: what is a^b when `b` is
even, in terms of a^(b/2)? And when `b` is odd?
""", answer=r"""
a^b = (a^(b/2))^2 when `b` is even, and a · a^(b−1) when `b` is odd. Each step halves the
exponent (or makes it even), so about 2·log2(b) multiplications suffice. Iteratively: walk
through the bits of `b` from the lowest, keep squaring `a` to get a, a^2, a^4, a^8, ...,
and multiply into the result exactly the powers whose bit is set in `b`.
"""),
            Say(r"""
**Binary exponentiation**, the loop version:

```cpp
long long power(long long a, long long b, long long m) {
    long long r = 1;
    a %= m;
    while (b > 0) {
        if (b & 1) r = r * a % m;   // this bit of b is set
        a = a * a % m;              // a, a^2, a^4, a^8, ...
        b >>= 1;
    }
    return r;
}
```

Both factors are always below `m`, so each product stays below m^2 ≈ 10^18. Keep `m` a
parameter: you will soon need two different moduli.
"""),
            Numeric(r"""
For `b = 10^9`, how many times does the `while` loop run?
""", answer=30, unit="iterations",
                explain=r"""
One iteration per bit of `b`: 10^9 < 2^30, so 30. For `b` up to 10^18, 60. Compared with
10^9 multiplications per query, that is the difference between 6·10^6 operations for
2·10^5 queries and three weeks.
"""),
            Try("exponentiation"),
            Say(r"""
Fast exponentiation also gives division. **Fermat's little theorem**: if `p` is prime and
`a` is not a multiple of `p`, then a^(p−1) ≡ 1 (mod p). Split off one factor:
a · a^(p−2) ≡ 1. So a^(p−2) is the inverse of `a`:

```cpp
long long inverse(long long a) { return power(a, MOD - 2, MOD); }   // MOD prime, a % MOD != 0
```

Division by `b` becomes multiplication by `inverse(b)`, at the cost of one fast power.
"""),
            Short(r"""
Check it with a small prime: what is the inverse of 3 modulo 7? (That is, 3^5 mod 7.)
""", accept=["5"], placeholder="a number",
                explain=r"""
3^5 = 243 = 34 · 7 + 5, so `5`. Check: 3 · 5 = 15 = 2 · 7 + 1 ≡ 1. The same computation
for 2 modulo 10^9 + 7 gives 500000004 (twice it is 10^9 + 8 ≡ 1), the number you will see
wherever an answer is "something over 2".
"""),
            MCQ(r"""
Fermat also says that powers of `a` repeat with period p − 1: a^e ≡ a^(e mod (p−1)). You
must compute a^(b^c) mod p with b, c up to 10^9, so b^c cannot be computed exactly. What
do you reduce b^c by?
""", [
                Opt("By p, like everything else.",
                    why="The *values* live modulo p, but the *exponent* counts multiplications, "
                        "and those repeat every p − 1 steps, not p. The samples may still pass "
                        "(small exponents are never reduced), which is what makes this bug nasty."),
                Opt("By p − 1.", correct=True,
                    why="Yes: compute `e = power(b, c, p - 1)`, then `power(a, e, p)`. That is why "
                        "`power` takes the modulus as a parameter."),
                Opt("It cannot be reduced; use `__int128` for b^c.",
                    why="b^c for b = c = 10^9 has about 9·10^9 digits. No integer type comes close."),
            ], explain=r"""
One caution: Fermat needs `a` not divisible by `p`. When `a ≡ 0`, the answer is 0 unless
the true exponent is 0; the problem's editorial shows why the limits here make that case
safe.
"""),
            Try("exponentiation_ii", note="Two moduli: p − 1 for the exponent, p for the value."),
            Try("mod_fractions", note="Inverses by Fermat, and numerators that can be negative."),
        ]),
    ],
    problems=[LIGHT_SWITCHES, COUNTING_BITS, EXPONENTIATION, EXPONENTIATION_II, MOD_FRACTIONS],
    cards=[
        Card(r"""Why does `if (x & 1 == 0)` never fire, and what is the fix?""",
             r"""`==` binds tighter than `&`, so it is `x & (1 == 0)` = `x & 0` = 0. Write `(x & 1) == 0`; parenthesise every bitwise expression."""),
        Card(r"""`1 << k` for `k ≥ 31`, and the fix?""",
             r"""It is an `int` shift: `1 << 31` is `INT_MIN` and `k ≥ 32` is undefined (here it wraps: `1 << 40` = 256). Use `1LL << k` (up to 62) or `1ULL << k` (up to 63)."""),
        Card(r"""Test, set, clear and flip bit `k` of `x`?""",
             r"""`(x >> k) & 1`, `x | (1 << k)`, `x & ~(1 << k)`, `x ^ (1 << k)` (with `1LL` for 64-bit values)."""),
        Card(r"""What do `x & -x` and `x & (x - 1)` compute?""",
             r"""`x & -x`: the lowest set bit, as a value (40 gives 8). `x & (x - 1)`: `x` with its lowest set bit cleared; it is 0 exactly when `x` is 0 or a power of two."""),
        Card(r"""The popcount / ctz / clz builtins and their traps?""",
             r"""`__builtin_popcount`, `__builtin_ctz`, `__builtin_clz` take 32-bit unsigned; use the `ll` versions for `long long` (the plain ones silently truncate). `ctz(0)` and `clz(0)` are undefined."""),
        Card(r"""Loop over every subset of `n` items?""",
             r"""`for (int mask = 0; mask < (1 << n); mask++)` and test item `i` with `(mask >> i) & 1`. 2^n·n ≈ 2·10^7 for n = 20."""),
        Card(r"""How many of 0..n have bit `k` set?""",
             r"""`(n+1) / 2^(k+1) · 2^k + max(0, (n+1) % 2^(k+1) − 2^k)`: full periods of 2^k zeros then 2^k ones, plus the partial one."""),
        Card(r"""Why is the modulus usually 10^9 + 7?""",
             r"""It is prime (inverses exist) and below 2^30: two residues add within `int` and multiply within `long long` ((10^9+7)^2 ≈ 10^18)."""),
        Card(r"""Safe modular multiply and subtract in C++?""",
             r"""`1LL * a * b % MOD` (multiply in 64 bits); `((a - b) % MOD + MOD) % MOD` (C++ `%` keeps the sign)."""),
        Card(r"""Binary exponentiation, the loop?""",
             r"""`r = 1; a %= m; while (b) { if (b & 1) r = r * a % m; a = a * a % m; b >>= 1; }` O(log b)."""),
        Card(r"""Modular inverse modulo a prime `p`?""",
             r"""Fermat: `a^(p−2) mod p`, for `a` not divisible by `p`. E.g. the inverse of 2 mod 10^9 + 7 is 500000004."""),
        Card(r"""Computing a^(b^c) mod p for prime p: reduce the exponent by what?""",
             r"""By p − 1 (Fermat: a^(p−1) ≡ 1), not by p: `power(a, power(b, c, p - 1), p)`. Mind a ≡ 0 separately."""),
    ],
)
