from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _column(rng, n, lo, hi):
    """n, then n values one per line (the CSES 1713 format)."""
    return f"{n}\n" + "\n".join(str(rng.randint(lo, hi)) for _ in range(n)) + "\n"


def _row(values):
    return f"{len(values)}\n" + " ".join(map(str, values)) + "\n"


def _primes_upto(n):
    s = bytearray([1]) * (n + 1)
    s[0] = s[1] = 0
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(range(i * i, n + 1, i)))
    return [i for i in range(n + 1) if s[i]]


def _common_random(rng, n, hi):
    return _row([rng.randint(1, hi) for _ in range(n)])


def _common_primes(rng):
    """Every prime below 10^6, shuffled: every pair is coprime, so the answer is 1 and the
    reference has to walk every d down to 1; the all-pairs naive does 3·10^9 gcds."""
    ps = _primes_upto(10**6)
    rng.shuffle(ps)
    return _row(ps)


def _common_spread(rng, n):
    """Distinct values, so no duplicate hands out a huge answer for free."""
    return _row(rng.sample(range(1, 10**6 + 1), n))


def _crt_cases(rng, t, mmax, shared):
    out = [str(t)]
    for _ in range(t):
        if shared and rng.random() < 0.6:
            g = rng.randint(1, max(1, int(mmax ** 0.5)))
            m1 = g * rng.randint(1, mmax // g)
            m2 = g * rng.randint(1, mmax // g)
        else:
            m1, m2 = rng.randint(1, mmax), rng.randint(1, mmax)
        if rng.random() < 0.5:                      # consistent by construction
            x = rng.randint(0, 10**18)
            a1, a2 = x % m1, x % m2
        else:
            a1, a2 = rng.randint(0, m1 - 1), rng.randint(0, m2 - 1)
        out.append(f"{a1} {m1} {a2} {m2}")
    return "\n".join(out) + "\n"


def _crt_extremes(rng):
    big = 10**9
    rows = [
        (big - 1, big, big - 2, big - 1),          # x = lcm - 1, about 10^18
        (0, big, 0, big - 1),                      # x = 0
        (big - 1, big, 1, big),                    # same modulus, different residue
        (123456789, big, 123456789 % 999999937, 999999937),
        (5, 999999937, 7, 999999929),               # two primes: lcm near 10^18
        (0, 1, 0, 1),
        (999999999, 1000000000, 499999999, 500000000),   # m2 divides m1, consistent
        (999999999, 1000000000, 0, 500000000),           # m2 divides m1, inconsistent
    ]
    return f"{len(rows)}\n" + "\n".join(" ".join(map(str, r)) for r in rows) + "\n"


# --------------------------------------------------------------------- problems
COUNTING_DIVISORS = Problem(
    id="counting_divisors",
    title="Counting Divisors",
    difficulty="easy",
    source="CSES 1713 - Counting Divisors",
    complexity="O(n √x)",
    statement=r"""
A number-theory homework sheet lists `n` integers. For each one, the class has to write
down how many positive divisors it has. You are the answer key.
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 10^5). Each of the next `n` lines has one integer `x`
(1 ≤ x ≤ 10^6).
""",
    output=r"""
For each `x`, print the number of its divisors on its own line.
""",
    samples=[
        Test("3\n16\n17\n18\n", "5\n2\n6\n",
             note="16 has the divisor 4 paired with itself: count it once."),
    ],
    tests=[
        Test("1\n1\n"),
        Test("4\n720720\n999983\n1000000\n2\n"),
        Test("3\n36\n49\n4\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _column(rng, rng.randint(1, 10), 1, 200), 12),
        Gen("medium random", lambda rng: _column(rng, 1000, 1, 10**6), 2),
        Gen("max n, largest x", lambda rng: _column(rng, 10**5, 999000, 10**6), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    while (n--) {
        long long x;
        cin >> x;
        int cnt = 0;
        // divisors come in pairs (d, x/d), and the smaller one of each pair is <= sqrt(x)
        for (long long d = 1; d * d <= x; d++)
            if (x % d == 0) cnt += (d * d == x) ? 1 : 2;   // a square root pairs with itself
        cout << cnt << '\n';
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
        int x;
        cin >> x;
        int c = 0;
        for (int d = 1; d <= x; d++) if (x % d == 0) c++;
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
    int n;
    cin >> n;
    while (n--) {
        int x;
        cin >> x;
        int c = 0;
        for (int d = 1; d <= x; d++) if (x % d == 0) c++;
        cout << c << '\n';
    }
}
""",
    hints=[
        r"""If `d` divides `x`, so does `x / d`. In each such pair, how large can the smaller one be?""",
        r"""Loop `d` while `d * d <= x` and add 2 for every hit, except 1 when `d * d == x`. That is
at most 1000 steps per number: 10^8 in all.""",
    ],
    editorial=r"""
Divisors pair up: `d` divides `x` exactly when `x / d` does, and in every pair the smaller
member is at most √x (if both were larger, their product would exceed `x`). So loop `d`
from 1 while `d * d <= x`, counting 2 per divisor found, or 1 when `d * d == x` (the
square root pairs with itself: 16 has divisors 1, 2, **4**, 8, 16). That is ≤ 1000 steps
per number, 10^8 in total, instead of the 10^11 of trying every `d` up to `x`.

Faster still, since every `x` is at most 10^6: a divisor-count sieve, `for (d = 1..M)
for (m = d; m <= M; m += d) cnt[m]++`, costs M ln M ≈ 1.4·10^7 once, and then every query
is a lookup. Or factorise with a smallest-prime-factor sieve and use
d(p_1^(e_1) ··· p_k^(e_k)) = (e_1 + 1)···(e_k + 1). Both appear later in the lesson.
""",
)

COMMON_DIVISORS = Problem(
    id="common_divisors",
    title="Common Divisors",
    difficulty="medium",
    source="CSES 1081 - Common Divisors",
    complexity="O(n + M log M), M = 10^6",
    statement=r"""
You are given `n` positive integers. Among all pairs of them (two different positions in
the list; the values may be equal), find the largest greatest common divisor.
""",
    input=r"""
The first line has `n` (2 ≤ n ≤ 2·10^5). The second line has `n` integers
x_1, ..., x_n (1 ≤ x_i ≤ 10^6).
""",
    output=r"""
Print the largest value of gcd(x_i, x_j) over all i ≠ j.
""",
    samples=[
        Test("5\n3 14 15 7 9\n", "7\n"),
        Test("4\n6 10 15 6\n", "6\n",
             note="The two 6s form a pair. A set of values would forget one of them."),
    ],
    tests=[
        Test("2\n1 1\n"),
        Test("2\n1000000 1000000\n"),
        Test("3\n2 3 5\n"),
        Test("2\n999983 1000000\n"),
        Test("3\n500000 1000000 999999\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _common_random(rng, rng.randint(2, 10), 30), 14),
        Gen("medium random", lambda rng: _common_random(rng, 2000, 10**6), 2),
        Gen("medium distinct", lambda rng: _common_spread(rng, 3000), 2),
        Gen("max n, random", lambda rng: _common_random(rng, 200000, 10**6), 1, large=True),
        Gen("all primes below 10^6", _common_primes, 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int M = 1000000;
    int n;
    cin >> n;
    vector<int> cnt(M + 1, 0);                    // cnt[v] = how many times v appears
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        cnt[x]++;                                 // a count, not a flag: duplicates matter
    }
    // The answer is the largest d that divides at least two of the numbers.
    for (int d = M; d >= 1; d--) {
        int multiples = 0;
        for (int m = d; m <= M && multiples < 2; m += d) multiples += cnt[m];
        if (multiples >= 2) {
            cout << d << '\n';
            return 0;
        }
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
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    int best = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++) best = max(best, std::gcd(a[i], a[j]));
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
    vector<int> a(n);
    for (auto& x : a) cin >> x;
    int best = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++) best = max(best, std::gcd(a[i], a[j]));
    cout << best << '\n';
}
""",
    hints=[
        r"""Do not compute any gcd. For a candidate `d`, what would have to be true of the list for
the answer to be at least `d`?""",
        r"""The answer is at least `d` exactly when two list entries are multiples of `d`. Try `d`
from 10^6 downwards; count multiples with a frequency array.""",
        r"""Walking the multiples of every `d` costs 10^6/1 + 10^6/2 + ... ≈ 1.4·10^7 in total.""",
    ],
    editorial=r"""
Turn the question around. Instead of "what is the gcd of this pair?", ask for each
candidate `d`: "are at least two of the numbers multiples of `d`?". If yes, those two have
a gcd that is a multiple of `d`, so the answer is at least `d`. And the optimal pair,
with gcd `g`, makes the check succeed at `d = g`. So the answer is the largest `d` that
passes.

Keep `cnt[v]` = number of occurrences of `v` (a count, not a set: two copies of 6 have
gcd 6). For each `d` from 10^6 down, add up `cnt[d], cnt[2d], cnt[3d], ...` and stop at
the first `d` with at least two. The total work over all `d` is the harmonic sum
M/1 + M/2 + ... + M/M ≈ M ln M ≈ 1.4·10^7, against 2·10^10 gcd calls for all pairs.
""",
)

COPRIME_PAIRS = Problem(
    id="coprime_pairs",
    title="Reduced Fractions",
    difficulty="medium",
    complexity="O(n log log n)",
    statement=r"""
A gear catalogue lists every gear ratio `a/b` strictly between 0 and 1 whose denominator
is at most `n`. Each ratio appears once, in lowest terms: `2/4` is the same ratio as
`1/2`.

How many ratios does the catalogue list? Equivalently: how many pairs `1 ≤ a < b ≤ n`
have gcd(a, b) = 1?
""",
    input=r"""
One integer `n` (1 ≤ n ≤ 2·10^7).
""",
    output=r"""
Print the number of pairs.
""",
    samples=[
        Test("5\n", "9\n",
             note="1/5, 1/4, 1/3, 2/5, 1/2, 3/5, 2/3, 3/4, 4/5."),
        Test("1\n", "0\n"),
    ],
    tests=[
        Test("2\n"),
        Test("3\n"),
        Test("10\n"),
        Test("97\n"),
        Test("100\n"),
    ],
    gens=[
        Gen("small random", lambda rng: f"{rng.randint(1, 2000)}\n", 10),
        Gen("medium random", lambda rng: f"{rng.randint(2000, 5000)}\n", 3),
        Gen("maximum n", lambda rng: "20000000\n", 1, large=True),
        Gen("large random n", lambda rng: f"{rng.randint(15 * 10**6, 2 * 10**7)}\n", 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    // Linear sieve: every composite i*p is reached exactly once, from its smallest prime p.
    // phi[x] == 0 means "not reached yet", which for x >= 2 means x is prime.
    vector<int> phi(n + 1, 0), primes;
    for (int i = 2; i <= n; i++) {
        if (phi[i] == 0) {                             // prime
            phi[i] = i - 1;
            primes.push_back(i);
        }
        for (int p : primes) {
            long long ip = 1LL * i * p;
            if (ip > n) break;
            if (i % p == 0) {                          // p already divides i: no new prime factor
                phi[ip] = phi[i] * p;
                break;                                 // for q > p, i*q is reached later, from p
            }
            phi[ip] = phi[i] * (p - 1);                // p is a new prime factor of i*p
        }
    }
    long long total = 0;                               // about 1.2 * 10^14: long long
    for (int b = 2; b <= n; b++) total += phi[b];      // phi(b) numerators for denominator b
    cout << total << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    long long c = 0;
    for (int b = 2; b <= n; b++)
        for (int a = 1; a < b; a++) if (std::gcd(a, b) == 1) c++;
    cout << c << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    long long total = 0;
    for (int b = 2; b <= n; b++) {             // phi(b) by trial division, from scratch
        int m = b;
        long long r = b;
        for (int p = 2; (long long)p * p <= m; p++)
            if (m % p == 0) {
                while (m % p == 0) m /= p;
                r -= r / p;
            }
        if (m > 1) r -= r / m;
        total += r;
    }
    cout << total << '\n';
}
""",
    hints=[
        r"""Fix the denominator `b`. How many numerators `a < b` give a fraction already in lowest
terms? That count has a name.""",
        r"""The answer is φ(2) + φ(3) + ... + φ(n). Computing each φ(b) by trial division is
O(n√n) in total: too slow for 2·10^7.""",
        r"""Sieve: start with `phi[i] = i`; for each prime `p` (a `p` whose `phi[p]` is still `p`),
do `phi[j] -= phi[j] / p` for every multiple `j` of `p`.""",
    ],
    editorial=r"""
For a fixed denominator `b`, the fraction `a/b` is in lowest terms exactly when
gcd(a, b) = 1, so there are φ(b) of them, and the answer is φ(2) + ... + φ(n).

Euler's totient is φ(b) = b · Π(1 − 1/p) over the distinct primes `p` dividing `b`.
Rather than factorising every `b` separately (trial division costs up to √b each, about
7 s here), let every prime walk its own multiples: start from `phi[i] = i` and, for each
prime `p`, apply `phi[j] -= phi[j] / p` to `j = p, 2p, 3p, ...`. A number is prime exactly
when no smaller prime has touched it, i.e. `phi[p] == p` still. The division is always
exact: when `p` arrives, `phi[j]` equals `j` times factors `(q−1)/q` for smaller primes
`q`, and `p` still divides it. The total work is Σ n/p over primes p ≤ n ≈ n ln ln n ≈
6·10^7.

The answer is about (3/π²)·n² ≈ 1.2·10^14 at the top of the range, so the sum must be a
`long long`. The array itself fits in `int` (80 MB at n = 2·10^7).

That sieve runs in about 0.2 s here. The reference uses the **linear sieve**, about three
times faster: for each `i` and each prime `p ≤ spf(i)`, it sets `phi[i·p]` from `phi[i]`,
multiplying by `p` when `p` already divides `i` (no new prime factor) and by `p − 1`
otherwise (φ is multiplicative). Every composite is reached exactly once, from its
smallest prime factor, so the whole thing is O(n).
""",
)

TWO_CONGRUENCES = Problem(
    id="two_congruences",
    title="Two Lighthouses",
    difficulty="hard",
    complexity="O(t log m)",
    statement=r"""
Two lighthouses blink on a schedule. The first blinks at every second `x` with
`x mod m1 = a1`, the second at every second `x` with `x mod m2 = a2`. The harbour master
wants to know the first second `x ≥ 0` at which both blink together, or that they never
do.

Answer `t` independent questions.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5). Each of the next `t` lines has four integers
`a1 m1 a2 m2` (1 ≤ m1, m2 ≤ 10^9, 0 ≤ a1 < m1, 0 ≤ a2 < m2).
""",
    output=r"""
For each question, print the smallest `x ≥ 0` with `x ≡ a1 (mod m1)` and `x ≡ a2 (mod m2)`,
or `-1` if there is none.
""",
    samples=[
        Test("3\n2 3 3 5\n3 4 5 6\n1 4 2 6\n", "8\n11\n-1\n",
             note="In the third question x would have to be odd (mod 4) and even (mod 6)."),
    ],
    tests=[
        Test("1\n0 1 0 1\n"),
        Test("3\n4 7 4 7\n4 7 5 7\n0 6 3 9\n"),
        Test("2\n5 12 7 18\n5 12 11 18\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _crt_cases(rng, rng.randint(1, 20), 30, True), 14),
        Gen("medium random", lambda rng: _crt_cases(rng, 1000, 300, True), 2),
        Gen("extremes", _crt_extremes, 1, large=True),
        Gen("max t, coprime-ish moduli", lambda rng: _crt_cases(rng, 10**5, 10**9, False), 1, large=True),
        Gen("max t, shared factors", lambda rng: _crt_cases(rng, 10**5, 10**9, True), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

// returns g = gcd(a, b) and sets x, y with a*x + b*y = g
long long ext_gcd(long long a, long long b, long long& x, long long& y) {
    if (b == 0) { x = 1; y = 0; return a; }
    long long x1, y1;
    long long g = ext_gcd(b, a % b, x1, y1);   // b*x1 + (a % b)*y1 = g
    x = y1;                                    // and a % b = a - (a / b) * b
    y = x1 - (a / b) * y1;
    return g;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        long long a1, m1, a2, m2;
        cin >> a1 >> m1 >> a2 >> m2;
        // x = a1 + m1*k, and we need m1*k ≡ a2 - a1 (mod m2)
        long long x, y;
        long long g = ext_gcd(m1, m2, x, y);   // m1*x + m2*y = g
        long long d = a2 - a1;
        if (d % g != 0) {                      // g divides m1*k - m2*l, so it must divide d
            cout << -1 << '\n';
            continue;
        }
        long long M = m2 / g;                  // (m1/g)*k ≡ d/g (mod M), gcd(m1/g, M) = 1
        long long inv = (x % M + M) % M;       // (m1/g)*x + M*y = 1: x inverts m1/g mod M
        long long k = ((d / g) % M + M) % M;
        k = k * inv % M;                       // both factors < M <= 10^9: fits
        cout << a1 + m1 * k << '\n';           // < m1 * M = lcm(m1, m2) <= 10^18
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
        long long a1, m1, a2, m2;
        cin >> a1 >> m1 >> a2 >> m2;
        long long ans = -1;
        for (long long x = 0; x < m1 * m2; x++)
            if (x % m1 == a1 && x % m2 == a2) { ans = x; break; }
        cout << ans << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        long long a1, m1, a2, m2;
        cin >> a1 >> m1 >> a2 >> m2;
        long long ans = -1;
        for (long long k = 0; k < m2; k++)       // walk the first lighthouse's blinks
            if ((a1 + m1 * k) % m2 == a2) { ans = a1 + m1 * k; break; }
        cout << ans << '\n';
    }
}
""",
    hints=[
        r"""Write `x = a1 + m1·k`. The second condition becomes `m1·k ≡ a2 − a1 (mod m2)`: a
linear congruence in `k`. When does it have a solution?""",
        r"""With `g = gcd(m1, m2)`: no solution unless `g` divides `a2 − a1`. Otherwise divide
everything by `g`; now `m1/g` has an inverse modulo `m2/g`, and extended Euclid finds it.""",
        r"""`k = (a2 − a1)/g · inverse(m1/g) mod (m2/g)`, normalised into `[0, m2/g)`, and
`x = a1 + m1·k`. Every intermediate product stays below 10^18.""",
    ],
    editorial=r"""
The blinks of the first lighthouse are `x = a1 + m1·k`. Plugging into the second
condition: `m1·k ≡ a2 − a1 (mod m2)`, i.e. `m1·k − m2·l = a2 − a1` for some integer `l`, a
linear Diophantine equation. Its left side is always a multiple of `g = gcd(m1, m2)`, so
if `g` does not divide `a2 − a1` there is no solution (print −1).

Otherwise divide by `g`: `(m1/g)·k ≡ (a2 − a1)/g (mod m2/g)`, and now `m1/g` and `m2/g`
are coprime. Extended Euclid on `(m1, m2)` gives `m1·x + m2·y = g`, so
`(m1/g)·x ≡ 1 (mod m2/g)`: `x` is the inverse. Then `k` is determined modulo `M = m2/g`;
taking `k` in `[0, M)` makes `x = a1 + m1·k` the smallest answer, because the solutions
repeat with period `m1·M = lcm(m1, m2)` and this one lies in `[0, lcm)`.

Overflow: `k·inv < M^2 ≤ 10^18` and `a1 + m1·k < lcm ≤ 10^18`, both inside `long long`.
With moduli up to 10^18 you would need `__int128` for those products. Walking
`k = 0, 1, 2, ...` instead is correct but costs up to 10^9 steps per question.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo17",
    title="number theory",
    track="algo",
    order=17,
    summary="Euclid and why it is fast, divisors in pairs, harmonic loops over multiples, "
            "sieves for primes, smallest factors and Euler's totient, extended Euclid, "
            "inverses modulo anything, and the Chinese remainder theorem.",
    prereqs=["cpp10"],
    tags=["gcd", "euclid", "divisors", "sieve", "totient", "extended euclid", "crt",
          "modular inverse", "harmonic sum"],
    parts=[
        Part("gcd, and why Euclid is fast", [
            Say(r"""
Number theory at ICPC is less about theorems than about a handful of fast tools, and the
first one is the greatest common divisor. Problems compute it 10^5 times inside a loop, on
numbers up to 10^18, and never think about its cost. This part is about why they can
afford not to.

The definition suggests a brute force: try `d = min(a, b)`, then `d − 1`, and so on, and
stop at the first `d` that divides both.
"""),
            Numeric(r"""
Take `a = 10^18` and `b = 10^18 − 1`. They are consecutive integers, so their gcd is 1.
How many candidates does the brute force try before it gets there?
""", answer=1e18, rel=0.5, unit="candidates",
                explain=r"""
About 10^18. At 10^9 simple operations per second that is over 30 years, for one gcd.
"""),
            MCQ(r"""
Euclid's algorithm replaces the pair `(a, b)` by `(b, a mod b)` until the second number
is 0. Why does this never change the gcd?
""", [
                Opt("Because `a mod b` is always a divisor of `a`.",
                    why="It is not: 7 mod 4 = 3, and 3 does not divide 7. The argument has to be "
                        "about *common* divisors of the pair."),
                Opt("Because `a mod b < b`, so the pair keeps shrinking.",
                    why="That explains why it *stops*, not why the answer survives. Replacing "
                        "`(a, b)` by `(b, 1)` also shrinks the pair, and loses the gcd."),
                Opt("Any `d` dividing `a` and `b` divides `a mod b = a − q·b`, and any `d` dividing "
                    "`b` and `a mod b` divides `a = q·b + a mod b`.", correct=True,
                    why="Yes. The two pairs have exactly the same set of common divisors, so in "
                        "particular the same greatest one."),
                Opt("It only holds when `a` and `b` are coprime.",
                    why="It holds always: `(12, 8) → (8, 4) → (4, 0)`, and gcd(12, 8) = 4 = gcd(4, 0)."),
            ], explain=r"""
The loop ends at `(g, 0)`, and gcd(g, 0) = g because every number divides 0. So
`gcd(a, b)` is whatever sits in the first slot when the second reaches 0.
"""),
            Short(r"""
Run Euclid by hand on `(1071, 462)`. What is the gcd? (Three divisions.)
""", accept=["21"], placeholder="a number",
                hint="1071 = 2·462 + 147. Continue with (462, 147).",
                explain=r"""
`(1071, 462) → (462, 147) → (147, 21) → (21, 0)`, so the gcd is 21. Notice how fast the
numbers fell: three steps from a thousand to zero.
"""),
            MCQ(r"""
Why is it fast in general? Take `a ≥ b > 0` and `r = a mod b`. Which statement is always
true?
""", [
                Opt("`r ≤ b / 2`.",
                    why="Counterexample: 7 mod 4 = 3 > 2. The remainder can be almost as big as `b`."),
                Opt("`r < a / 2`.", correct=True,
                    why="Yes, by two cases. If `b ≤ a/2`, then `r < b ≤ a/2`. If `b > a/2`, then "
                        "`b` fits into `a` only once, so `r = a − b < a − a/2 = a/2`."),
                Opt("`r < a / 2`, but only when `b ≤ a / 2`.",
                    why="The other case is the interesting one: when `b > a/2` the quotient is 1, "
                        "so `r = a − b`, which is less than `a/2` precisely because `b` is large."),
                Opt("Nothing useful: `r` can be as large as `a − 1`.",
                    why="`r < b ≤ a`, and the case analysis shows `r < a/2` in fact."),
            ], explain=r"""
After two steps, `(a, b) → (b, r) → (r, ...)`, the first number has dropped from `a` to
`r < a/2`. **Every two steps, the larger number at least halves.**
"""),
            Numeric(r"""
Using only "halves every two steps", how many Euclid steps can a pair of numbers up to
10^18 need, at most?
""", answer=120, rel=0.25, unit="steps",
                hint="How many halvings take 10^18 down to 1? That is log2 of 10^18.",
                explain=r"""
log2(10^18) ≈ 60 halvings, two steps each: about 120. The true worst case is a pair of
consecutive Fibonacci numbers, where every quotient is 1 and the remainder shrinks as
slowly as possible (`(89, 55) → (55, 34) → (34, 21) → ...`); the largest such pair
below 10^18 needs 85 steps. Either way gcd is O(log min(a, b)): free, for contest
purposes.
"""),
            Say(r"""
In C++17, `std::gcd(a, b)` (header `<numeric>`, included by `bits/stdc++.h`) works on
`int` and `long long`, returns a non-negative result, and has `gcd(0, x) = x`. Older
code uses GCC's `__gcd`. There is also `std::lcm`, but the formula behind it is worth
knowing because of one trap:

```cpp
long long l = a / gcd(a, b) * b;   // lcm(a, b)
```
"""),
            MCQ(r"""
`a` and `b` are up to 10^12 and the problem promises lcm(a, b) ≤ 10^18. Which expression
computes it safely in `long long`?
""", [
                Opt("`a * b / gcd(a, b)`",
                    why="The product `a * b` comes first and can reach 10^24, far past the "
                        "9.2·10^18 of a `long long`, even though the final quotient fits."),
                Opt("`a / gcd(a, b) * b`", correct=True,
                    why="Yes. The division is exact and happens first, so the only product "
                        "computed is the answer itself, which fits."),
                Opt("`(long long)((double)a * b / gcd(a, b))`",
                    why="A `double` keeps 53 bits, about 16 digits. Past 2^53 ≈ 9·10^15 the "
                        "result is rounded, so the last digits of an 18-digit lcm are wrong."),
            ]),
        ]),
        Part("Divisors come in pairs", [
            Say(r"""
**Counting Divisors.** You get `n ≤ 10^5` numbers, each `x ≤ 10^6`, and must print how
many divisors each has. The obvious program tries every `d` from 1 to `x` and counts
those with `x % d == 0`.
"""),
            Numeric(r"""
In the worst case every `x` is near 10^6. How many trial divisions does the obvious
program make in total?
""", answer=1e11, rel=0.5, unit="divisions",
                explain=r"""
`10^5 · 10^6 = 10^11`: minutes, not a second.
"""),
            Reflect(r"""
Say `x = 36` and the loop has just found that `d = 4` divides it. Which other divisor has
it found without noticing? What does that tell you about where the loop could stop?
""", answer=r"""
`36 / 4 = 9` is a divisor too. Divisors pair up as `(d, x/d)`, and in every pair the
smaller member is at most √x (two members both above √x would multiply to more than `x`).
So the loop only needs `d` with `d·d ≤ x`, counting 2 for each hit: the divisor and its
partner. That is at most 1000 steps for `x ≤ 10^6`, and 10^8 in total, which C++ does in
about a tenth of a second.
"""),
            Short(r"""
For `x = 36` the loop runs `d = 1, 2, ..., 6`. One of the hits must be counted once
instead of twice. Which `d`?
""", accept=["6", "d = 6", "d=6"], placeholder="a number",
                explain=r"""
`d = 6`: its partner `36 / 6` is 6 itself. The pairs are (1, 36), (2, 18), (3, 12), (4, 9)
and the lone 6, so 36 has 9 divisors. Every perfect square has an odd number of divisors,
and a loop that always adds 2 overcounts exactly those.
"""),
            MCQ(r"""
The same idea on bigger inputs: `x` up to 10^12 (a `long long`). Which loop header is
correct?
""", [
                Opt("`for (int d = 1; d * d <= x; d++)`",
                    why="`d * d` is computed in `int`. `d` must reach 10^6, and `d * d` overflows "
                        "as soon as `d` passes 46341, so the condition becomes garbage."),
                Opt("`for (long long d = 1; d * d <= x; d++)`", correct=True,
                    why="Right: the square is computed in 64 bits, and the comparison is exact "
                        "integer arithmetic with no `sqrt` rounding to worry about."),
                Opt("`for (long long d = 1; d <= x / 2; d++)`",
                    why="Correct results, but it is the O(x) loop again: 5·10^11 steps for "
                        "one number."),
            ]),
            Short(r"""
There is also a formula. If `x = p_1^(e_1) · p_2^(e_2) ··· p_k^(e_k)`, a divisor chooses
each exponent independently. `720 = 2^4 · 3^2 · 5`. How many divisors does 720 have?
""", accept=["30"], placeholder="a number",
                hint="The exponent of 2 in a divisor can be 0, 1, 2, 3 or 4: five choices.",
                explain=r"""
`(4 + 1)(2 + 1)(1 + 1) = 30`. So once you can factorise quickly, you can count divisors
quickly: `d(x) = Π(e_i + 1)`. (No number up to 10^6 has more than 240 divisors;
720720 is the smallest with 240.)
"""),
            Try("counting_divisors", note="The √x loop is enough here: 10^8 steps. Mind the "
                "perfect squares."),
        ]),
        Part("Loop over multiples, not over pairs", [
            Say(r"""
**Common Divisors.** You get `n ≤ 2·10^5` numbers, each at most 10^6. Find the largest
gcd over all pairs.

The brute force takes every pair and calls `gcd`.
"""),
            Numeric(r"""
How many pairs are there for `n = 2·10^5`?
""", answer=2e10, rel=0.5, unit="pairs",
                explain=r"""
`n(n−1)/2 ≈ 2·10^10` gcd calls, each a few dozen operations: minutes. Pairs are the
wrong thing to enumerate.
"""),
            MCQ(r"""
Turn the question around. For a candidate value `d`, which fact about the list is easy to
check and says exactly whether the answer is at least `d`?
""", [
                Opt("Some pair has gcd exactly `d`.",
                    why="That is the original question again; checking it still means looking "
                        "at pairs."),
                Opt("At least two of the numbers are multiples of `d`.", correct=True,
                    why="Yes. Two multiples of `d` have a gcd that is a multiple of `d`, so at "
                        "least `d`. Conversely the best pair, with gcd `g`, consists of two "
                        "multiples of `g`. So the answer is the largest `d` with two multiples "
                        "in the list."),
                Opt("`d` is prime and divides at least two of the numbers.",
                    why="The answer need not be prime: for 12 and 24 it is 12. Restricting to "
                        "primes finds only the largest *prime* factor shared by a pair."),
                Opt("`d` divides the sum of all the numbers.",
                    why="3 + 5 = 8 is divisible by 8, but gcd(3, 5) = 1. Sums mix numbers "
                        "together; divisibility of each number is what matters."),
            ], explain=r"""
So: keep `cnt[v]` = how often `v` occurs. For `d` from 10^6 down to 1, add up `cnt[d]`,
`cnt[2d]`, `cnt[3d]`, ...; the first `d` whose total reaches 2 is the answer.
"""),
            Numeric(r"""
In the worst case that loop visits, for every `d` from 1 to `M = 10^6`, all multiples of
`d` up to `M`. How many visits is that in total?
""", answer=1.4e7, rel=0.5, unit="visits",
                hint="M/1 + M/2 + M/3 + ... + M/M. The harmonic sum 1 + 1/2 + ... + 1/M is about ln M.",
                explain=r"""
`M · (1 + 1/2 + ... + 1/M) ≈ M ln M ≈ 1.4·10^7` (exactly 13,970,034). Two nested loops
that are not `M^2`: the inner loop gets shorter as `d` grows. This **harmonic loop** is
the workhorse of the whole lesson; the sieves below are the same loop with fewer outer
iterations.
"""),
            MCQ(r"""
The list is `[6, 10, 15, 6]`. What happens if you store the values in a `set<int>` (or a
`bool` array) instead of counting them?
""", [
                Opt("Nothing changes: the pair of 6s is still found.",
                    why="A set keeps a single 6, so `d = 6` sees only one multiple."),
                Opt("It prints 5 instead of 6.", correct=True,
                    why="Right. With the duplicate gone, the best remaining pair is 10 and 15. "
                        "Equal values are a legal pair, and their gcd is the value itself."),
                Opt("It only gets slower.",
                    why="Speed is not the problem; the answer is wrong."),
            ]),
            Try("common_divisors", note="Frequency array, harmonic loop from the top. One hidden "
                "test is every prime below 10^6, where the answer is 1."),
        ]),
        Part("Sieves: let the primes find their multiples", [
            Say(r"""
**Reduced Fractions.** How many fractions `a/b` with `0 < a/b < 1` and `b ≤ n` are in
lowest terms, for `n ≤ 2·10^7`? Equivalently, how many pairs `a < b ≤ n` have
gcd(a, b) = 1?

Fix the denominator `b`. The numerators that work are the `a < b` coprime to `b`, and
their number is **Euler's totient** φ(b). The answer is φ(2) + φ(3) + ... + φ(n).
"""),
            Short(r"""
What is φ(12), the number of `a` in `1..12` with gcd(a, 12) = 1?
""", accept=["4"], placeholder="a number",
                explain=r"""
4: the numbers 1, 5, 7 and 11. Everything else shares a factor 2 or 3 with 12.
"""),
            MCQ(r"""
Which reasoning gives φ(12) without listing, and generalises?
""", [
                Opt("12 has the prime factors 2 and 3, so φ(12) = 12 − 2 − 3 = 7.",
                    why="That subtracts the primes, not their multiples. The multiples of 2 or 3 "
                        "in 1..12 are 6 + 4 − 2 = 8 numbers (6 and 12 counted twice), so 4 are left."),
                Opt("Half of 1..12 is odd; of those, two thirds avoid 3: 12 · (1 − 1/2)(1 − 1/3) = 4.",
                    correct=True,
                    why="Yes: φ(n) = n · Π(1 − 1/p) over the distinct primes dividing `n`. Only "
                        "which primes divide `n` matters, not their exponents."),
                Opt("12 = 2^2 · 3, so φ(12) = (2 − 1)^2 · (3 − 1) = 2.",
                    why="For a prime power, φ(p^k) = p^k − p^(k−1) (remove the multiples of `p`), "
                        "not (p − 1)^k: φ(4) = 2, and φ(12) = φ(4)·φ(3) = 2·2 = 4."),
            ], explain=r"""
Why the fractions multiply: among `1..n`, exactly `n/p` numbers are multiples of a prime
`p | n`, and for two such primes the conditions "not divisible by 2" and "not divisible
by 3" are independent in one full cycle of length `n` (algo18 proves it with
inclusion-exclusion). For example φ(36) = 36 · (1/2) · (2/3) = 12.
"""),
            Numeric(r"""
Computing each φ(b) separately by trial division costs up to √b divisions. Estimate the
total, √2 + √3 + ... + √n, for `n = 2·10^7`.
""", answer=6e10, rel=0.6, unit="divisions",
                hint="The sum of √b for b up to n is about (2/3)·n^1.5.",
                explain=r"""
`(2/3) · (2·10^7)^1.5 ≈ 6·10^10`. Early exits cut it down (a number with only small
factors finishes quickly), but measured on this machine it still takes 7 seconds.
"""),
            Reflect(r"""
Trial division factors 1000001, then 1000002, then 1000003, each from scratch, trying
2, 3, 4, 5, ... What work is wasted? And whether 7 divides a given number is completely
predictable, so how could you use that?
""", answer=r"""
Almost every trial division *fails*, and each number rediscovers from scratch facts that
follow a fixed pattern: 2 divides every second number, 7 every seventh. Turn it around:
instead of each number asking every candidate "do you divide me?", let each prime `p`
walk its own multiples `p, 2p, 3p, ...` and tell them. Then no step is wasted: every
visit is a real (number, prime factor) pair. That is the **sieve of Eratosthenes**.
"""),
            Say(r"""
The plain sieve marks composites. When the outer loop reaches `p` and `p` is still
unmarked, no smaller prime divides it, so it is prime:

```cpp
vector<bool> composite(n + 1, false);
for (int p = 2; p <= n; p++)
    if (!composite[p])
        for (long long j = 1LL * p * p; j <= n; j += p)
            composite[j] = true;
```

The inner loop may start at `p·p`: a smaller multiple `k·p` with `k < p` has a prime factor
below `p` and was marked already. (Note the `1LL`: `p * p` overflows `int` for `p` above
46341, and the loop then runs wild.)
"""),
            Numeric(r"""
Primes start a walk of length `n/p`; composites start nothing. So the sieve costs about
Σ n/p over primes p ≤ n. Estimate it for `n = 2·10^7`.
""", answer=6.1e7, rel=0.5, unit="steps",
                hint="Over primes, 1/2 + 1/3 + 1/5 + 1/7 + ... up to n is about ln ln n (ln ln(2·10^7) ≈ 2.8).",
                explain=r"""
About `n · ln ln n ≈ 5.6·10^7`; the exact sum is 61,128,033. Compare the harmonic loop of
the last part, `n ln n ≈ 3.4·10^8` here: restricting the outer loop to primes, which
thin out like 1/ln x, turns ln n into ln ln n, a number that is below 4 for any `n` you
will meet. The sieve is **O(n log log n)**, practically linear.
"""),
        ]),
        Part("Sieving φ and smallest prime factors", [
            Say(r"""
The same walk computes φ for every number at once. Start with `phi[i] = i`. When the
outer loop meets a prime `p` (a value nobody has touched: `phi[p] == p`), it multiplies
every multiple by `(1 − 1/p)`:

```cpp
vector<int> phi(n + 1);
iota(phi.begin(), phi.end(), 0);               // phi[i] = i
for (int p = 2; p <= n; p++)
    if (phi[p] == p)                           // untouched: p is prime
        for (int j = p; j <= n; j += p)
            phi[j] -= phi[j] / p;              // phi[j] *= (1 - 1/p)
```
"""),
            Short(r"""
Trace `phi[18]`: it starts at 18, then prime 2 visits it, then prime 3. What does it hold
after the visit of 2, and after the visit of 3? Answer with two numbers.
""", accept=["9 6", "9, 6", "9,6", "9 and 6"], placeholder="two numbers",
                explain=r"""
`18 − 18/2 = 9`, then `9 − 9/3 = 6`. And φ(18) = 18 · (1/2) · (2/3) = 6: the numbers 1, 5,
7, 11, 13, 17.
"""),
            MCQ(r"""
`phi[j] / p` is integer division. Can it ever round down and silently corrupt the result?
""", [
                Opt("Yes, but the rounding errors cancel out over the primes.",
                    why="Integer truncation errors do not cancel; one rounded step would leave "
                        "the final value wrong."),
                Opt("No: when `p` arrives, `phi[j]` is `j / (q_1···q_r) · (q_1 − 1)···(q_r − 1)` "
                    "for the smaller primes `q_i` of `j`, and `p` still divides `j / (q_1···q_r)`.",
                    correct=True,
                    why="Right. Dividing `j` by smaller primes cannot remove the factor `p`, so "
                        "`phi[j]` is still a multiple of `p` and the division is exact."),
                Opt("Only when `j` is itself prime.",
                    why="For `j = p` the value is still `p`, and `p / p = 1` is exact: "
                        "`phi[p]` becomes `p − 1`, as it should."),
            ]),
            Try("coprime_pairs", note="The answer reaches about 1.2·10^14: sum in `long long`. "
                "The array holds 2·10^7 `int`s, 80 MB, which is fine."),
            Say(r"""
One more variant, for factorising. Store in `spf[x]` the **smallest prime factor** of
every `x ≤ N`. The same sieve fills it: a prime `p` writes itself into every multiple
that has no entry yet.

```cpp
vector<int> spf(N + 1, 0);
for (int p = 2; p <= N; p++)
    if (spf[p] == 0)                             // nobody wrote here: p is prime
        for (int j = p; j <= N; j += p)
            if (spf[j] == 0) spf[j] = p;
```

Factorising any `x ≤ N` is then repeated division, `x /= spf[x]`, and every division at
least halves `x`: at most log2(x) steps instead of √x. It pays off when you factorise
*many* numbers below a bound you can allocate (about 10^7). For one number up to 10^12,
trial division to 10^6 is simpler; for one number up to 10^18, neither works (that needs
Pollard's rho, beyond this lesson).
"""),
            Short(r"""
Factorise 360 by repeated `x /= spf[x]`. List the primes you divide by, in order, one per
division.
""", accept=["2 2 2 3 3 5", "2, 2, 2, 3, 3, 5", "2,2,2,3,3,5"], placeholder="primes separated by spaces",
                explain=r"""
`360 → 180 → 90 → 45 → 15 → 5 → 1`, dividing by 2, 2, 2, 3, 3, 5. So 360 = 2^3 · 3^2 · 5,
with (3+1)(2+1)(1+1) = 24 divisors. Six divisions, against trial division up to
√360 ≈ 19. The `spf` values come out in non-decreasing order, so equal primes are
adjacent and the exponents are easy to count.
"""),
        ]),
        Part("Extended Euclid, inverses and two congruences", [
            Say(r"""
**Two Lighthouses.** One lighthouse blinks at seconds `x ≡ a1 (mod m1)`, the other at
`x ≡ a2 (mod m2)`, with moduli up to 10^9 and `t ≤ 10^5` questions. When do they first
blink together?

The brute force walks the first lighthouse's blinks, `x = a1, a1 + m1, a1 + 2m1, ...`,
and checks each against the second. Within `m2` steps the pattern repeats, so it stops
after at most `m2` tries.
"""),
            Numeric(r"""
With `m2` near 10^9 and `t = 10^5` questions, how many tries does that cost in the worst
case?
""", answer=1e14, rel=0.5, unit="tries",
                explain=r"""
`10^5 · 10^9 = 10^14`. Even one question can take a second.
"""),
            MCQ(r"""
`x = a1 + m1·k = a2 + m2·l` means `m1·k − m2·l = a2 − a1`: an equation `a·x + b·y = c` in
integers. When does such an equation have a solution?
""", [
                Opt("Always: there are two unknowns and one equation.",
                    why="Over the reals, yes; over the integers, no. `4x + 6y = 1` has no solution: "
                        "the left side is always even."),
                Opt("Exactly when gcd(a, b) divides `c`.", correct=True,
                    why="Yes. `g = gcd(a, b)` divides `a·x + b·y` for every `x, y`, so it must divide "
                        "`c`. Conversely, extended Euclid finds `a·x + b·y = g`, and multiplying by "
                        "`c/g` gives `c`."),
                Opt("Exactly when `a` and `b` are coprime.",
                    why="Sufficient, not necessary: `4x + 6y = 2` has the solution `x = −1, y = 1`."),
                Opt("Exactly when `c ≥ 0`.",
                    why="Negative `x` and `y` are allowed, so the sign of `c` is irrelevant: "
                        "`3x + 5y = −1` has `x = 3, y = −2`."),
            ]),
            Reflect(r"""
Here is how to find `x, y` with `a·x + b·y = gcd(a, b)`. Euclid reduces `(a, b)` to
`(b, a mod b)`. Suppose the recursive call already returned `x', y'` with
`b·x' + (a mod b)·y' = g`. Using `a mod b = a − ⌊a/b⌋·b`, what are `x` and `y` for
`(a, b)`? And what is the base case?
""", answer=r"""
Substitute: `b·x' + (a − ⌊a/b⌋·b)·y' = a·y' + b·(x' − ⌊a/b⌋·y')`. So `x = y'` and
`y = x' − ⌊a/b⌋·y'`. The base case is `b = 0`: then `g = a = a·1 + 0·0`, so `x = 1, y = 0`.
This is **extended Euclid**: the same O(log) recursion, carrying the coefficients back up.
"""),
            Say(r"""
In code:

```cpp
long long ext_gcd(long long a, long long b, long long& x, long long& y) {
    if (b == 0) { x = 1; y = 0; return a; }
    long long x1, y1;
    long long g = ext_gcd(b, a % b, x1, y1);
    x = y1;
    y = x1 - (a / b) * y1;
    return g;
}
```

The coefficients stay small: |x| ≤ b and |y| ≤ a, so nothing overflows for inputs that fit.
"""),
            Short(r"""
`ext_gcd(240, 46, x, y)` returns `g = 2` and sets `x = −9`. What is `y`?
""", accept=["47"], placeholder="a number",
                hint="240·(−9) + 46·y = 2.",
                explain=r"""
`y = 47`: `240·(−9) + 46·47 = −2160 + 2162 = 2`. Solutions are not unique: adding
`46/2 = 23` to `x` and subtracting `240/2 = 120` from `y` keeps the sum, so all solutions
are `x = −9 + 23k`, `y = 47 − 120k`. In general the steps are `b/g` and `a/g`.
"""),
            MCQ(r"""
Modular inverses (cpp10) came from Fermat: `a^(m−2) mod m`. Now take `m = 10`, which is
not prime. What is the inverse of 3 modulo 10, and what does the Fermat formula give?
""", [
                Opt("3 has no inverse modulo 10, because 10 is not prime.",
                    why="The inverse exists whenever gcd(a, m) = 1, prime or not: 3 · 7 = 21 ≡ 1."),
                Opt("7; and `3^8 mod 10` is also 7.",
                    why="`3^8 = 6561`, which is 1 mod 10, not 7. Fermat's little theorem needs "
                        "a prime modulus."),
                Opt("7; but `3^8 mod 10 = 1`, so Fermat gives a wrong answer.", correct=True,
                    why="Right. For any `m`, solve `3x + 10y = 1` with extended Euclid: `x = −3`, "
                        "normalised to 7. The inverse exists exactly when gcd(a, m) = 1."),
                Opt("9, since 3 · 9 = 27.",
                    why="27 mod 10 = 7, not 1."),
            ], explain=r"""
`a·x ≡ 1 (mod m)` is the Diophantine equation `a·x + m·y = 1`, solvable exactly when
gcd(a, m) = 1. So 4 has no inverse modulo 10 (every `4x + 10y` is even). Normalise with
`((x % m) + m) % m`, since `x` may come back negative.
"""),
            MCQ(r"""
Back to the lighthouses: we need `m1·k ≡ d (mod m2)` with `d = a2 − a1`, but
`g = gcd(m1, m2) > 1`, so `m1` has no inverse modulo `m2`. What now?
""", [
                Opt("There is no solution.",
                    why="There can be: `6k ≡ 4 (mod 10)` has `k = 4` (24 ≡ 4). No inverse only "
                        "means no *unique* solution modulo 10."),
                Opt("If `g` divides `d`, divide everything by `g`: `(m1/g)·k ≡ d/g (mod m2/g)`, where "
                    "`m1/g` is invertible.", correct=True,
                    why="Yes. After dividing, the two moduli are coprime, so extended Euclid gives "
                        "the inverse and `k` is unique modulo `m2/g`. If `g` does not divide `d`, "
                        "there is no solution at all."),
                Opt("Use Fermat's formula anyway; it usually works.",
                    why="It works only for prime moduli and coprime bases; here neither holds."),
            ], explain=r"""
The whole recipe: `g = gcd(m1, m2)`; if `(a2 − a1) % g != 0`, print −1. Otherwise
`k = (a2 − a1)/g · inverse(m1/g) mod (m2/g)` taken in `[0, m2/g)`, and `x = a1 + m1·k`.
Solutions repeat every `lcm(m1, m2)`, and this `x` is the smallest non-negative one. This
is the **Chinese remainder theorem** for two congruences.
"""),
            Short(r"""
Use the recipe: `x ≡ 3 (mod 4)` and `x ≡ 5 (mod 6)`. What is the smallest `x ≥ 0`?
""", accept=["11"], placeholder="a number",
                hint="g = 2 and d = 2, so solve 2k ≡ 1 (mod 3).",
                explain=r"""
`g = 2` divides `d = 2`; divide: `2k ≡ 1 (mod 3)`, and the inverse of 2 modulo 3 is 2, so
`k = 2` and `x = 3 + 4·2 = 11`. Check: 11 mod 4 = 3, 11 mod 6 = 5. The next one is
11 + lcm(4, 6) = 23. And `x ≡ 1 (mod 4)`, `x ≡ 2 (mod 6)` has no solution: `d = 1` is
odd while `g = 2`.
"""),
            MCQ(r"""
Moduli are up to 10^9. Which products in the recipe could overflow `long long`?
""", [
                Opt("`m1 * m2` and everything after it: 10^18 does not fit.",
                    why="`long long` holds up to about 9.2·10^18, so 10^18 fits."),
                Opt("None, as long as `k` and the inverse are reduced into `[0, m2/g)` first: then "
                    "`k * inv < 10^18` and `a1 + m1 * k < lcm ≤ 10^18`.", correct=True,
                    why="Right. Reduce before you multiply. With moduli up to 10^18 these products "
                        "would reach 10^36, and you would need `__int128` for them."),
                Opt("`ext_gcd`'s coefficients, which can grow exponentially.",
                    why="They are bounded by the inputs: |x| ≤ m2 and |y| ≤ m1."),
            ]),
            Try("two_congruences", note="Extended Euclid, the divisibility check, and the "
                "normalisation of negative values. One hidden test has an answer near 10^18."),
        ]),
    ],
    problems=[COUNTING_DIVISORS, COMMON_DIVISORS, COPRIME_PAIRS, TWO_CONGRUENCES],
    cards=[
        Card(r"""Euclid's algorithm: why is `gcd(a, b) = gcd(b, a mod b)`, and how many steps does it take?""",
             r"""Both pairs have the same common divisors (`a mod b = a − q·b`). O(log min(a, b)) steps: `a mod b < a/2`, so the larger number halves every two steps (worst case: consecutive Fibonacci numbers, 85 steps below 10^18)."""),
        Card(r"""How do you compute lcm(a, b) without overflow?""",
             r"""`a / gcd(a, b) * b`: divide first. `a * b / gcd` overflows even when the lcm fits."""),
        Card(r"""Count the divisors of `x` in O(√x)?""",
             r"""`for (long long d = 1; d * d <= x; d++) if (x % d == 0) cnt += (d * d == x) ? 1 : 2;` Divisors pair up as (d, x/d)."""),
        Card(r"""Number of divisors from the factorisation `x = p_1^(e_1) ··· p_k^(e_k)`?""",
             r"""`(e_1 + 1)(e_2 + 1)···(e_k + 1)`: each exponent is chosen independently."""),
        Card(r"""Cost of `for (d = 1; d <= M; d++) for (m = d; m <= M; m += d)`?""",
             r"""The harmonic sum M/1 + M/2 + ... ≈ M ln M (1.4·10^7 for M = 10^6)."""),
        Card(r"""Sieve of Eratosthenes: complexity, and where does the inner loop start?""",
             r"""O(n log log n) (Σ n/p over primes). Start at `p*p` (as `long long`): smaller multiples have a smaller prime factor."""),
        Card(r"""Euler's totient formula?""",
             r"""φ(n) = n · Π(1 − 1/p) over the distinct primes p dividing n. φ(p^k) = p^k − p^(k−1)."""),
        Card(r"""Totient sieve for all `i ≤ n`?""",
             r"""`phi[i] = i`; for each `p` with `phi[p] == p`: `for (j = p; j <= n; j += p) phi[j] -= phi[j] / p;` (the division is exact)."""),
        Card(r"""What does a smallest-prime-factor sieve buy you?""",
             r"""After O(N log log N) setup, any `x ≤ N` factorises in O(log x): `while (x > 1) { p = spf[x]; divide out p; }`."""),
        Card(r"""Extended Euclid: from `b·x' + (a mod b)·y' = g`, what are `x, y` for `(a, b)`?""",
             r"""`x = y'`, `y = x' − (a / b)·y'`. Base case `b = 0`: `x = 1, y = 0`."""),
        Card(r"""When is `a·x + b·y = c` solvable, and when does `a` have an inverse mod `m`?""",
             r"""Iff gcd(a, b) divides c. The inverse exists iff gcd(a, m) = 1 (prime or not); get it from ext_gcd, not Fermat."""),
        Card(r"""Merge `x ≡ a1 (mod m1)` and `x ≡ a2 (mod m2)`?""",
             r"""g = gcd(m1, m2); need g | (a2 − a1). k = (a2 − a1)/g · inv(m1/g mod m2/g) mod (m2/g); x = a1 + m1·k, unique mod lcm(m1, m2)."""),
    ],
)
