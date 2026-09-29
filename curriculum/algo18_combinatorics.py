from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def _is_prime(n):
    """Deterministic Miller-Rabin, exact for n < 3.3·10^24."""
    if n < 2:
        return False
    for p in _MR_BASES:
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _MR_BASES:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


_SMALL_PRIMES = [p for p in range(2, 200) if _is_prime(p)]
_FIRST_20 = _SMALL_PRIMES[:20]


def _distinct_primes(rng, k, lo, hi):
    out = set()
    while len(out) < k:
        x = rng.randint(lo, hi)
        if _is_prime(x):
            out.add(x)
    return sorted(out, key=lambda _: rng.random())


def _binom_queries(rng, q, amax, half):
    out = [str(q)]
    for _ in range(q):
        a = rng.randint(0, amax) if not half else rng.randint(amax - 1000, amax)
        b = rng.randint(0, a) if not half else a // 2 + rng.randint(-500, 500)
        b = max(0, min(a, b))
        out.append(f"{a} {b}")
    return "\n".join(out) + "\n"


def _binom_extremes(rng):
    rows = [(10**6, 0), (10**6, 10**6), (10**6, 5 * 10**5), (0, 0), (1, 0), (1, 1),
            (999999, 1), (10**6, 999999), (2, 1), (10**6, 1)]
    return f"{len(rows)}\n" + "\n".join(f"{a} {b}" for a, b in rows) + "\n"


def _pm_small(rng, nmax, kmax, pmax):
    n = rng.randint(2, nmax)
    pool = [p for p in _SMALL_PRIMES if p <= min(n, pmax)]
    k = rng.randint(1, min(kmax, len(pool)))
    ps = rng.sample(pool, k)
    return f"{n} {k}\n" + " ".join(map(str, ps)) + "\n"


def _pm_large(rng, kind):
    n = 10**18 if kind != "random n" else rng.randint(10**17, 10**18)
    if kind == "first 20 primes":
        ps = list(_FIRST_20)
        rng.shuffle(ps)
    elif kind == "primes near 1e9":
        ps = _distinct_primes(rng, 20, 10**8, 10**9)
    elif kind == "huge primes":
        ps = _distinct_primes(rng, 20, 10**17, n)
    else:                                   # a mix of tiny, medium and huge primes
        ps = rng.sample(_SMALL_PRIMES[:12], 8) + _distinct_primes(rng, 6, 10**4, 10**6) \
            + _distinct_primes(rng, 6, 10**9, 10**12)
        rng.shuffle(ps)
    return f"{n} {len(ps)}\n" + " ".join(map(str, ps)) + "\n"


def _inv_case(rng, n, rmax):
    return f"{n}\n" + " ".join(str(rng.randint(1, rmax)) for _ in range(n)) + "\n"


def _inv_small(rng):
    while True:
        n = rng.randint(1, 6)
        r = [rng.randint(1, 6) for _ in range(n)]
        prod = 1
        for x in r:
            prod *= x
        if prod <= 20000:
            return f"{n}\n" + " ".join(map(str, r)) + "\n"


def _dice(rng, nlo, nhi):
    n = rng.randint(nlo, nhi)
    a = rng.randint(1, 6 * n)
    b = rng.randint(a, 6 * n)
    return f"{n} {a} {b}\n"


# --------------------------------------------------------------------- problems
BINOMIAL = Problem(
    id="binomial_coefficients",
    title="Binomial Coefficients",
    difficulty="easy",
    source="CSES 1079 - Binomial Coefficients",
    complexity="O(N + q), N = 10^6",
    statement=r"""
Answer `q` questions of the form "in how many ways can `b` items be chosen from `a`
distinct items?", that is, compute the binomial coefficient C(a, b), modulo
10^9 + 7.
""",
    input=r"""
The first line has `q` (1 ≤ q ≤ 10^5). Each of the next `q` lines has two integers `a`
and `b` (0 ≤ b ≤ a ≤ 10^6).
""",
    output=r"""
For each question, print C(a, b) modulo 10^9 + 7.
""",
    samples=[
        Test("3\n5 3\n8 1\n9 5\n", "10\n8\n126\n"),
        Test("2\n0 0\n60 30\n", "1\n737009364\n",
             note="C(60, 30) = 118264581564861424 still fits in a `long long`; C(67, 33) no longer "
                  "does. Computing exactly and reducing at the end stops working almost at once."),
    ],
    tests=[
        Test("3\n1 0\n1 1\n2 1\n"),
        Test("2\n2000 1000\n2000 1\n"),
        Test("4\n1999 0\n1999 1999\n1999 1998\n1500 700\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _binom_queries(rng, rng.randint(1, 15), 30, False), 12),
        Gen("medium random", lambda rng: _binom_queries(rng, 1000, 2000, False), 2),
        Gen("extremes", _binom_extremes, 1, large=True),
        Gen("max q, a = 10^6, b = a/2", lambda rng: _binom_queries(rng, 10**5, 10**6, True), 1, large=True),
        Gen("max q, random", lambda rng: _binom_queries(rng, 10**5, 10**6, False), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;

long long power(long long b, long long e) {         // b^e mod MOD (cpp10)
    long long r = 1;
    b %= MOD;
    while (e > 0) {
        if (e & 1) r = r * b % MOD;
        b = b * b % MOD;
        e >>= 1;
    }
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int N = 1000000;
    vector<long long> fact(N + 1), inv_fact(N + 1);
    fact[0] = 1;
    for (int i = 1; i <= N; i++) fact[i] = fact[i - 1] * i % MOD;
    inv_fact[N] = power(fact[N], MOD - 2);           // Fermat: MOD is prime and N < MOD
    for (int i = N; i >= 1; i--) inv_fact[i - 1] = inv_fact[i] * i % MOD;   // 1/(i-1)! = i/i!
    int q;
    cin >> q;
    while (q--) {
        int a, b;
        cin >> a >> b;
        // reduce after every multiplication: three factors near 10^9 would overflow
        cout << fact[a] * inv_fact[b] % MOD * inv_fact[a - b] % MOD << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    const int MOD = 1000000007;
    int q;
    cin >> q;
    vector<pair<int, int>> qs(q);
    int amax = 0;
    for (auto& [a, b] : qs) { cin >> a >> b; amax = max(amax, a); }
    // Pascal's triangle: C(a, b) = C(a-1, b-1) + C(a-1, b)
    vector<vector<int>> C(amax + 1);
    for (int a = 0; a <= amax; a++) {
        C[a].assign(a + 1, 1);
        for (int b = 1; b < a; b++) C[a][b] = (C[a - 1][b - 1] + C[a - 1][b]) % MOD;
    }
    for (auto [a, b] : qs) cout << C[a][b] << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
long long power(long long b, long long e) {
    long long r = 1; b %= MOD;
    while (e > 0) { if (e & 1) r = r * b % MOD; b = b * b % MOD; e >>= 1; }
    return r;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> q;
    while (q--) {
        long long a, b;
        cin >> a >> b;
        long long num = 1, den = 1;                  // recomputed for every query
        for (long long i = 0; i < b; i++) {
            num = num * ((a - i) % MOD) % MOD;
            den = den * ((i + 1) % MOD) % MOD;
        }
        cout << num * power(den, MOD - 2) % MOD << '\n';
    }
}
""",
    hints=[
        r"""C(a, b) = a! / (b! (a − b)!). You cannot divide residues, but you can multiply by
modular inverses. And every query needs factorials of numbers up to 10^6: compute them
once.""",
        r"""Tables `fact[i]` and `inv_fact[i]` for `i ≤ 10^6`. Get `inv_fact[10^6]` with one
Fermat power, then `inv_fact[i-1] = inv_fact[i] * i % MOD` going down.""",
        r"""`fact[a] * inv_fact[b] % MOD * inv_fact[a - b] % MOD`: reduce after each product.""",
    ],
    editorial=r"""
Write C(a, b) = a! · (b!)^(−1) · ((a − b)!)^(−1) modulo the prime p = 10^9 + 7. The
inverses exist because b! and (a − b)! are products of numbers smaller than p, none
divisible by p. Precompute `fact[i] = i! mod p` for all `i ≤ 10^6` (a prefix product),
then `inv_fact[N] = fact[N]^(p−2)` by Fermat and `inv_fact[i−1] = inv_fact[i] · i`
downwards (since 1/(i−1)! = i / i!). Each query is then two multiplications: O(N + q)
in all.

Recomputing the products for each query costs up to 10^6 multiplications per query,
10^11 in total. And the one line that bites: `fact[a] * inv_fact[b] * inv_fact[a-b] % MOD`
multiplies three numbers near 10^9 before reducing, 10^27, and overflows `long long`.
""",
)

PRIME_MULTIPLES = Problem(
    id="prime_multiples",
    title="Prime Multiples",
    difficulty="medium",
    source="CSES 2185 - Prime Multiples",
    complexity="O(2^k · k)",
    statement=r"""
You are given an integer `n` and `k` distinct primes. How many of the integers
1, 2, ..., n are divisible by at least one of the primes?
""",
    input=r"""
The first line has `n` and `k` (1 ≤ n ≤ 10^18, 1 ≤ k ≤ 20). The second line has `k`
distinct primes a_1, ..., a_k (2 ≤ a_i ≤ n).
""",
    output=r"""
Print the number of integers in `1..n` divisible by at least one a_i.
""",
    samples=[
        Test("20 2\n2 5\n", "12\n"),
        Test("100 3\n2 3 5\n", "74\n"),
    ],
    tests=[
        Test("2 1\n2\n"),
        Test("30 3\n5 3 2\n"),
        Test("1000000 1\n999983\n"),
        Test("1000000 7\n2 3 5 7 11 13 17\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _pm_small(rng, 300, 6, 50), 14),
        Gen("medium random", lambda rng: _pm_small(rng, 10**6, 20, 199), 3),
        Gen("n = 10^18, the first 20 primes", lambda rng: _pm_large(rng, "first 20 primes"), 1, large=True),
        Gen("n = 10^18, primes near 10^9", lambda rng: _pm_large(rng, "primes near 1e9"), 1, large=True),
        Gen("n = 10^18, huge primes", lambda rng: _pm_large(rng, "huge primes"), 1, large=True),
        Gen("random n, mixed primes", lambda rng: _pm_large(rng, "random n"), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    long long n;
    int k;
    cin >> n >> k;
    vector<long long> p(k);
    for (auto& x : p) cin >> x;
    long long ans = 0;
    for (int mask = 1; mask < (1 << k); mask++) {    // every non-empty subset of the primes
        long long prod = 1;
        bool fits = true;
        for (int i = 0; i < k && fits; i++) {
            if (!(mask >> i & 1)) continue;
            if (prod > n / p[i]) fits = false;        // prod * p[i] > n: floor(n / prod) = 0
            else prod *= p[i];                        // never overflows: stays <= n
        }
        if (!fits) continue;
        long long term = n / prod;                    // multiples of every prime in the subset
        if (__builtin_popcount(mask) % 2 == 1) ans += term;
        else ans -= term;
    }
    cout << ans << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long n;
    int k;
    cin >> n >> k;
    vector<long long> p(k);
    for (auto& x : p) cin >> x;
    long long c = 0;
    for (long long x = 1; x <= n; x++) {
        bool hit = false;
        for (long long q : p) if (x % q == 0) hit = true;
        c += hit;
    }
    cout << c << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    long long n;
    int k;
    cin >> n >> k;
    vector<long long> p(k);
    for (auto& x : p) cin >> x;
    long long c = 0;
    for (long long x = 1; x <= n; x++)
        for (long long q : p) if (x % q == 0) { c++; break; }
    cout << c << '\n';
}
""",
    hints=[
        r"""There are ⌊n/p⌋ multiples of `p` in `1..n`. Adding these up over all primes counts
some numbers several times. Draw the Venn diagram for two primes, then three.""",
        r"""Sum over every non-empty subset `S` of the primes: `(−1)^(|S|+1) · ⌊n / (product of S)⌋`.
That is 2^20 ≈ 10^6 subsets.""",
        r"""Products of subsets pass 10^18 quickly and then overflow `long long`. Before
multiplying by `p`, test `prod > n / p`: if so, the term is 0 and you can skip the subset.""",
    ],
    editorial=r"""
Let A_p be the multiples of `p` in `1..n`; |A_p| = ⌊n/p⌋. We want |A_1 ∪ ... ∪ A_k|.
Adding the sizes counts a number with `j` of the primes as factors `j` times;
inclusion-exclusion corrects this: sum over non-empty subsets `S`, with sign `+` for odd
|S| and `−` for even, of |∩_S A_p|. Since the primes are distinct, a number is divisible
by all of them exactly when it is divisible by their product, so |∩_S A_p| =
⌊n / Π_S p⌋. A number with `j ≥ 1` of the primes is counted
C(j,1) − C(j,2) + C(j,3) − ... = 1 time, exactly once. 2^20 subsets, each product
built in at most 20 steps: 2·10^7 operations.

The trap is overflow: the product of the first 16 primes is 3.3·10^19, beyond `long long`,
and a wrapped-around product can be small, adding a garbage term. Any product above `n`
contributes 0, so test `prod > n / p` *before* multiplying and drop the subset.
(`__int128` would also work for a single product, but products of 20 primes up to 10^18
overflow even that.)
""",
)

CHRISTMAS = Problem(
    id="christmas_party",
    title="Christmas Party",
    difficulty="easy",
    source="CSES 1717 - Christmas Party",
    complexity="O(n)",
    statement=r"""
There are `n` children at a Christmas party, and each has brought a gift. The gifts are
redistributed so that every child gets exactly one gift and nobody gets their own.

In how many ways can this be done? Print the answer modulo 10^9 + 7.
""",
    input=r"""
One integer `n` (1 ≤ n ≤ 10^6).
""",
    output=r"""
Print the number of ways modulo 10^9 + 7.
""",
    samples=[
        Test("4\n", "9\n"),
        Test("1\n", "0\n", note="A single child can only get their own gift."),
    ],
    tests=[
        Test("2\n"),
        Test("3\n"),
        Test("5\n"),
        Test("8\n"),
    ],
    gens=[
        Gen("small random", lambda rng: f"{rng.randint(1, 10)}\n", 8),
        Gen("n = 13", lambda rng: "13\n", 1, large=True),
        Gen("maximum n", lambda rng: "1000000\n", 1, large=True),
        Gen("large random n", lambda rng: f"{rng.randint(10**5, 10**6)}\n", 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    const long long MOD = 1000000007;
    int n;
    cin >> n;
    // D(n) = (n - 1) * (D(n-1) + D(n-2)), D(1) = 0, D(2) = 1 (and D(0) = 1)
    long long prev2 = 1, prev1 = 0;                   // D(0), D(1)
    for (int i = 2; i <= n; i++) {
        long long cur = (i - 1) * ((prev1 + prev2) % MOD) % MOD;   // < 10^6 * 10^9: fits
        prev2 = prev1;
        prev1 = cur;
    }
    cout << (n == 0 ? 1 : prev1) << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<int> p(n);
    iota(p.begin(), p.end(), 0);
    long long c = 0;
    do {
        bool ok = true;
        for (int i = 0; i < n; i++) if (p[i] == i) ok = false;
        c += ok;
    } while (next_permutation(p.begin(), p.end()));
    cout << c % 1000000007 << '\n';
}
""",
    hints=[
        r"""Inclusion-exclusion over the events "child i gets their own gift" gives
D(n) = Σ (−1)^j C(n, j) (n − j)!. A recurrence is even simpler.""",
        r"""Child 1 gives to some child `j` (n − 1 choices). Either `j` gives back to child 1, or
not. Count each case in terms of smaller D.""",
        r"""D(n) = (n − 1)(D(n − 1) + D(n − 2)), with D(1) = 0 and D(2) = 1. Keep values mod p
in `long long`: (n − 1) times a residue reaches 10^15.""",
    ],
    editorial=r"""
These are **derangements**, permutations without fixed points. Two ways to count them.

Inclusion-exclusion: let A_i be the permutations where child `i` keeps their gift. Fixing
a set of `j` children leaves (n − j)! permutations, so
D(n) = Σ_(j=0..n) (−1)^j C(n, j) (n − j)! = n! Σ (−1)^j / j!, which tends to n!/e.

A recurrence: child 1 gives to some `j ≠ 1` (n − 1 choices). If `j` gives back to 1, the
other n − 2 children form any derangement: D(n − 2). If not, then among the n − 1
children other than 1, the rule "j must not give to 1" plays the role of "j must not keep
their own", and we need a derangement of those n − 1: D(n − 1). So
D(n) = (n − 1)(D(n − 1) + D(n − 2)). O(n) either way.

Traps: D(1) = 0; the product `(n − 1) · (D(n−1) + D(n−2))` needs `long long`; and with the
alternating sum, subtraction modulo p needs `+ MOD` before `% MOD`.
""",
)

INVERSIONS = Problem(
    id="inversion_probability",
    title="Inversion Probability",
    difficulty="medium",
    source="CSES 1728 - Inversion Probability",
    complexity="O(n^2 · r)",
    checker="float:1e-6",
    statement=r"""
There are `n` children in a row. Child `i` picks an integer uniformly at random from
`1..r_i`, independently of the others.

An inversion is a pair of children `i < j` with a_i > a_j. What is the expected number of
inversions?
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 100). The second line has `n` integers r_1, ..., r_n
(1 ≤ r_i ≤ 100).
""",
    output=r"""
Print the expected number of inversions with six digits after the decimal point.
Answers within 10^(−6) (absolute, or relative for answers above 1) are accepted.
""",
    samples=[
        Test("3\n5 2 7\n", "1.057143\n"),
        Test("2\n3 2\n", "0.500000\n"),
    ],
    tests=[
        Test("1\n1\n"),
        Test("4\n1 1 1 1\n"),
        Test("2\n100 100\n"),
        Test("5\n10 1 10 1 10\n"),
    ],
    gens=[
        Gen("small random", _inv_small, 14),
        Gen("max n, random r", lambda rng: _inv_case(rng, 100, 100), 1, large=True),
        Gen("max n, r = 100", lambda rng: "100\n" + " ".join(["100"] * 100) + "\n", 1, large=True),
        Gen("max n, decreasing r", lambda rng: "100\n" + " ".join(str(100 - i) for i in range(100)) + "\n", 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<int> r(n);
    for (auto& x : r) cin >> x;
    // inversions = sum over pairs i < j of [a_i > a_j]; expectation is linear
    double ans = 0;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++) {
            long long favourable = 0;                  // outcomes (x, y) with x > y
            for (int x = 1; x <= r[i]; x++) favourable += min(x - 1, r[j]);
            ans += (double)favourable / ((double)r[i] * r[j]);
        }
    cout << fixed << setprecision(6) << ans << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<int> r(n), a(n, 1);
    for (auto& x : r) cin >> x;
    long long total = 0, outcomes = 0;
    while (true) {                                     // odometer over every outcome
        outcomes++;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++) total += a[i] > a[j];
        int k = n - 1;
        while (k >= 0 && a[k] == r[k]) a[k--] = 1;
        if (k < 0) break;
        a[k]++;
    }
    cout << fixed << setprecision(6) << (double)total / outcomes << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n;
    cin >> n;
    vector<int> r(n), a(n, 1);
    for (auto& x : r) cin >> x;
    double total = 0, outcomes = 0;
    while (true) {
        outcomes++;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++) total += a[i] > a[j];
        int k = n - 1;
        while (k >= 0 && a[k] == r[k]) a[k--] = 1;
        if (k < 0) break;
        a[k]++;
    }
    cout << fixed << setprecision(6) << total / outcomes << '\n';
}
""",
    hints=[
        r"""The number of inversions is a sum of 0/1 indicators, one per pair `i < j`. What is the
expected value of a sum?""",
        r"""E[inversions] = Σ_(i<j) P(a_i > a_j), and each probability involves only two
children. For a fixed value `x` of a_i, exactly min(x − 1, r_j) values of a_j are
smaller.""",
    ],
    editorial=r"""
Enumerating outcomes is hopeless: 100^100 of them. But the number of inversions is
I = Σ_(i<j) X_ij with X_ij = 1 when a_i > a_j, and by **linearity of expectation**
E[I] = Σ_(i<j) E[X_ij] = Σ_(i<j) P(a_i > a_j). Linearity needs no independence, although
here the picks happen to be independent too.

For one pair, count the favourable outcomes: a_i = x beats min(x − 1, r_j) values of
a_j, so P = Σ_(x=1..r_i) min(x − 1, r_j) / (r_i · r_j). 4950 pairs times at most 100
values: 5·10^5 steps. Print with `fixed << setprecision(6)`; the default six
*significant* digits would print 1057.14 for an answer near 1057.142857.
""",
)

DICE = Problem(
    id="dice_probability",
    title="Dice Probability",
    difficulty="medium",
    source="CSES 1725 - Dice Probability",
    complexity="O(36 n^2)",
    checker="float:1e-6",
    statement=r"""
You throw a fair six-sided die `n` times. What is the probability that the sum of the
results is between `a` and `b`, inclusive?
""",
    input=r"""
One line with three integers `n`, `a` and `b` (1 ≤ n ≤ 100, 1 ≤ a ≤ b ≤ 6n).
""",
    output=r"""
Print the probability with six digits after the decimal point (answers within 10^(−6)
are accepted).
""",
    samples=[
        Test("2 9 10\n", "0.194444\n"),
        Test("1 6 6\n", "0.166667\n"),
    ],
    tests=[
        Test("1 1 6\n"),
        Test("3 3 3\n"),
        Test("7 20 25\n"),
        Test("5 1 30\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _dice(rng, 1, 7), 14),
        Gen("n = 100, everything", lambda rng: "100 100 600\n", 1, large=True),
        Gen("n = 100, the middle", lambda rng: "100 340 360\n", 1, large=True),
        Gen("n = 100, one tail", lambda rng: "100 100 130\n", 1, large=True),
        Gen("large random", lambda rng: _dice(rng, 60, 100), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    int n, a, b;
    cin >> n >> a >> b;
    // dp[s] = probability that the throws so far sum to s
    vector<double> dp(6 * n + 1, 0.0);
    dp[0] = 1.0;
    for (int t = 1; t <= n; t++) {
        vector<double> nd(6 * n + 1, 0.0);
        for (int s = t - 1; s <= 6 * (t - 1); s++)     // sums reachable after t-1 throws
            for (int f = 1; f <= 6; f++) nd[s + f] += dp[s] / 6;
        dp = nd;
    }
    double ans = 0;
    for (int s = a; s <= b; s++) ans += dp[s];
    cout << fixed << setprecision(6) << ans << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int main() {
    int n, a, b;
    cin >> n >> a >> b;
    vector<int> d(n, 1);
    long long good = 0, total = 0;
    while (true) {
        int s = 0;
        for (int x : d) s += x;
        total++;
        good += (a <= s && s <= b);
        int k = n - 1;
        while (k >= 0 && d[k] == 6) d[k--] = 1;
        if (k < 0) break;
        d[k]++;
    }
    cout << fixed << setprecision(6) << (double)good / total << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int n, a, b;
double good = 0, total = 0;
void go(int i, int s) {
    if (i == n) { total++; if (a <= s && s <= b) good++; return; }
    for (int f = 1; f <= 6; f++) go(i + 1, s + f);
}
int main() {
    cin >> n >> a >> b;
    go(0, 0);
    cout << fixed << setprecision(6) << good / total << '\n';
}
""",
    hints=[
        r"""6^n sequences are too many, but only 6n + 1 different sums exist. What do you need to
know about the first `t` throws to continue?""",
        r"""`dp[t][s]` = probability that the first `t` throws sum to `s`;
`dp[t][s] = Σ_(f=1..6) dp[t−1][s−f] / 6`.""",
    ],
    editorial=r"""
A DP over the partial sum: after `t` throws only the current sum matters for the future,
not the sequence that produced it. With `dp[t][s]` the probability that `t` throws sum to
`s`, `dp[0][0] = 1` and `dp[t][s] = Σ_(f=1..6) dp[t−1][s−f] / 6`. The answer is
Σ_(s=a..b) dp[n][s]. 100 rows of at most 600 sums, 6 transitions each: 3.6·10^5 steps.

Doubles are fine here: the smallest non-zero probability is 6^(−100) ≈ 1.5·10^(−78), far
above the smallest `double` (about 10^(−308)), and the relative error stays near 10^(−15).
Counting sequences in `long long` and dividing by 6^n at the end fails instead: 6^25
already exceeds 9.2·10^18.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo18",
    title="combinatorics & probability",
    track="algo",
    order=18,
    summary="Binomial coefficients modulo a prime with factorial tables, stars and bars, "
            "inclusion-exclusion, derangements, linearity of expectation, and DP over "
            "probabilities.",
    prereqs=["algo17", "algo06"],
    tags=["binomial", "factorial", "modular inverse", "stars and bars", "inclusion-exclusion",
          "derangements", "expectation", "probability dp"],
    parts=[
        Part("Binomial coefficients modulo a prime", [
            Say(r"""
Counting problems at ICPC nearly always end with "print the answer modulo 10^9 + 7". The
reason is size. Here is the most basic counting task of all: answer `q ≤ 10^5` questions
"C(a, b) = ?", the number of ways to choose `b` of `a` items, with `a ≤ 10^6`.
"""),
            Numeric(r"""
How many decimal digits does C(10^6, 5·10^5) have, roughly?
""", answer=301027, rel=0.5, unit="digits",
                hint="C(n, n/2) is a bit less than 2^n, and 2^10 ≈ 10^3.",
                explain=r"""
About 301,000 digits (exactly 301,027): 2^(10^6) has about 0.301·10^6 digits and
C(n, n/2) is only slightly smaller. Computing that and then reducing it is out of the
question; every intermediate value must stay below the modulus.
"""),
            MCQ(r"""
So keep `fact[i] = i! mod p`. Take a tiny prime, `p = 7`: C(5, 2) = 10 ≡ 3 (mod 7).
`fact[5] = 120 mod 7 = 1` and `fact[2] · fact[3] mod 7 = 12 mod 7 = 5`. What does the
integer division `fact[5] / 5` give, and what is the fix?
""", [
                Opt("3, the right answer.",
                    why="`1 / 5` in integers is 0. Residues are not the numbers themselves, so "
                        "dividing them means nothing."),
                Opt("0. Division does not survive taking remainders; multiply by the modular "
                    "inverse of 5 instead: 5 · 3 = 15 ≡ 1, so 1 · 3 = 3.", correct=True,
                    why="Right. Modulo a prime, \"divide by x\" means \"multiply by the x^(−1) with "
                        "x · x^(−1) ≡ 1\", and Fermat gives it as x^(p−2) (cpp10)."),
                Opt("It is fine because 7 is prime.",
                    why="Primality guarantees that inverses exist; it does not make the `/` "
                        "operator compute them."),
                Opt("A division by zero.",
                    why="5 is not 0 modulo 7. (It *would* be if a factorial were a multiple of p; "
                        "see the next question.)"),
            ]),
            MCQ(r"""
With `p = 10^9 + 7` and `a ≤ 10^6`, why does b! always have an inverse modulo `p`?
""", [
                Opt("Every number has an inverse modulo a prime.",
                    why="Not 0, and not any multiple of `p`: `p · x ≡ 0` for every `x`."),
                Opt("b! is a product of 1, 2, ..., b, all smaller than the prime `p`, so `p` does not "
                    "divide it.", correct=True,
                    why="Yes: a prime divides a product only if it divides a factor. So "
                        "gcd(b!, p) = 1 and the inverse exists. Once `a ≥ p` this fails (a! ≡ 0), "
                        "and you need Lucas' theorem instead."),
                Opt("Because `p` is large, so nothing overflows.",
                    why="Size and overflow have nothing to do with invertibility; divisibility by "
                        "`p` does."),
            ]),
            Numeric(r"""
The direct approach: per query, multiply `a · (a−1) ··· (a−b+1)` and `b!` (about `b`
multiplications each), then one inverse. With `q = 10^5` queries and `b` near 5·10^5,
how many multiplications is that in total?
""", answer=1e11, rel=0.6, unit="multiplications",
                explain=r"""
About 10^5 · 10^6 = 10^11. Far too many for one second.
"""),
            Reflect(r"""
What does that approach recompute over and over, and what would you precompute instead?
""", answer=r"""
Every query rebuilds the same products 1·2···k from scratch. Compute `fact[i] = i! mod p`
once for every `i ≤ 10^6` (a prefix *product*, the multiplicative cousin of algo01's
prefix sums), and the inverse factorials once too. Then
C(a, b) = `fact[a] · inv_fact[b] · inv_fact[a−b]`: two multiplications per query.
"""),
            Short(r"""
One Fermat power per inverse factorial would cost 10^6 · 30 multiplications. There is an
O(N) trick: compute only `inv_fact[N]` by Fermat, then walk down. Fill in:
`inv_fact[i − 1] = inv_fact[i] * ____ % MOD`
""", accept=["i"], placeholder="an expression",
                hint="1/(i−1)! and 1/i! differ by one factor.",
                explain=r"""
`i`, because 1/(i−1)! = i / i!. So:

```cpp
fact[0] = 1;
for (int i = 1; i <= N; i++) fact[i] = fact[i - 1] * i % MOD;
inv_fact[N] = power(fact[N], MOD - 2);
for (int i = N; i >= 1; i--) inv_fact[i - 1] = inv_fact[i] * i % MOD;
```
"""),
            MCQ(r"""
`fact` and `inv_fact` are `long long` values below `MOD ≈ 10^9`. Which query line is
correct?
""", [
                Opt("`fact[a] * inv_fact[b] * inv_fact[a - b] % MOD`",
                    why="The two multiplications happen before any `%`: three numbers near 10^9 "
                        "multiply to 10^27, far past 9.2·10^18. It overflows silently."),
                Opt("`fact[a] * inv_fact[b] % MOD * inv_fact[a - b] % MOD`", correct=True,
                    why="Yes: every product is of two values below 10^9 + 7, so below 1.1·10^18, "
                        "and it is reduced before the next multiplication."),
                Opt("`fact[a] / (fact[b] * fact[a - b]) % MOD`",
                    why="The division-of-residues trap from two questions ago, plus an overflow."),
            ]),
            Try("binomial_coefficients", note="Tables up to 10^6, built once. Reduce after every "
                "multiplication."),
        ]),
        Part("Stars and bars", [
            Say(r"""
Most counting problems become a binomial coefficient once you find the right picture.
The classic: distribute `m` identical apples among `n` children, where a child may get
none. How many distributions are there?
"""),
            Short(r"""
3 apples, 2 children. How many distributions?
""", accept=["4"], placeholder="a number",
                explain=r"""
4: (0, 3), (1, 2), (2, 1), (3, 0).
"""),
            Reflect(r"""
Write a distribution as a row of stars (apples) and bars (walls between children): with 3
apples and 2 children, `**|*` means (2, 1) and `|***` means (0, 3). What are you really
choosing, and how many ways are there for `m` apples and `n` children?
""", answer=r"""
Every distribution is a row of `m + n − 1` symbols of which `n − 1` are bars, and every
such row is a distribution (the stars before the first bar go to child 1, and so on). So
you are choosing the positions of the bars: C(m + n − 1, n − 1). For 3 apples and 2
children, C(4, 1) = 4. This bijection is called **stars and bars**.
"""),
            Numeric(r"""
5 apples, 3 children, empty hands allowed. How many distributions?
""", answer=21,
                explain=r"""
C(5 + 3 − 1, 3 − 1) = C(7, 2) = 21.
"""),
            MCQ(r"""
Now every child must get at least one apple (`m ≥ n`). How many distributions?
""", [
                Opt("C(m + n − 1, n − 1) − n", why="Subtracting `n` assumes one empty child at a "
                    "time, but several can be empty at once (fixing that is inclusion-exclusion). "
                    "For m = 4, n = 3 it gives 15 − 3 = 12; the truth is 3: (2,1,1), (1,2,1), (1,1,2)."),
                Opt("C(m − 1, n − 1)", correct=True,
                    why="Yes. Hand one apple to each child first, then distribute the other m − n "
                        "freely: C(m − n + n − 1, n − 1) = C(m − 1, n − 1). Or: place the n − 1 "
                        "bars in distinct gaps among the m − 1 gaps between stars."),
                Opt("C(m, n)",
                    why="That chooses `n` of `m` *distinct* apples. Ours are identical; only the "
                        "counts matter."),
            ]),
            Numeric(r"""
How many solutions in non-negative integers does `x1 + x2 + x3 ≤ 10` have?
""", answer=286,
                hint="Add a fourth variable for the slack: x4 = 10 − (x1 + x2 + x3) ≥ 0.",
                explain=r"""
With the slack variable the condition becomes `x1 + x2 + x3 + x4 = 10`: 10 apples, 4
children, C(13, 3) = 286. Turning "≤" into "=" with one extra box is a standard move.
"""),
        ]),
        Part("Inclusion-exclusion", [
            Say(r"""
**Prime Multiples.** Given `n ≤ 10^18` and `k ≤ 20` distinct primes, count the integers
in `1..n` divisible by at least one of them. Checking every integer is 10^18 steps. But
counting the multiples of a single prime is easy: ⌊n/p⌋ of them.
"""),
            Numeric(r"""
How many numbers in `1..100` are divisible by 2 or by 3? (50 are divisible by 2, 33 by 3.)
""", answer=67,
                hint="Some numbers are in both lists.",
                explain=r"""
50 + 33 counts every multiple of 6 twice, and there are 16 of them: 50 + 33 − 16 = 67.
Draw two overlapping circles: adding the circles counts the lens twice, so subtract it
once.
"""),
            MCQ(r"""
Three primes, 2, 3, 5, with sets A, B, C of their multiples. After
|A| + |B| + |C| − |A∩B| − |A∩C| − |B∩C|, how many times has a number divisible by all
three (like 30) been counted?
""", [
                Opt("Once: the pairs remove exactly the double counts.",
                    why="30 is in all three circles (+3) and in all three lenses (−3): net 0."),
                Opt("Zero times, so |A∩B∩C| must be added back once.", correct=True,
                    why="Right. The general rule alternates signs: + singles, − pairs, + triples, "
                        "and so on. An element in `j` of the sets is counted "
                        "C(j,1) − C(j,2) + C(j,3) − ... = 1 time, exactly once."),
                Opt("Twice.", why="Count it: +3 from the three sets, −3 from the three pairs."),
            ]),
            Numeric(r"""
So how many numbers in `1..100` are divisible by 2, 3 or 5?
""", answer=74,
                hint="Singles, minus pairs, plus the triple. A number divisible by 2 and by 3 is "
                     "divisible by 6: how many of those are there up to 100? And by 10, 15, 30?",
                explain=r"""
50 + 33 + 20 − 16 − 10 − 6 + 3 = 74. For distinct primes, divisible by all of a subset
means divisible by their product, so every term is ⌊n / product⌋. With `k` primes there
are 2^k − 1 subsets, about 10^6 for `k = 20`: sum `(−1)^(|S|+1) · ⌊n / Π_S p⌋` over all
of them.
"""),
            MCQ(r"""
With `n = 10^18` and the first 20 primes, the product of the first 16 primes is already
3.3·10^19. What should the code do with such a subset?
""", [
                Opt("Nothing special: `long long` holds it.",
                    why="`long long` stops at 9.2·10^18. The product wraps around to some "
                        "unrelated value, possibly small, and adds a garbage term."),
                Opt("Take the product modulo 10^9 + 7.",
                    why="The term is ⌊n / product⌋, which needs the true product, not a residue."),
                Opt("Stop: a product above `n` contributes ⌊n/prod⌋ = 0. Test `prod > n / p` "
                    "before multiplying.", correct=True,
                    why="Yes. The test itself cannot overflow, and once a product passes `n` every "
                        "larger subset containing it contributes 0 too."),
                Opt("Use `double` for the product.",
                    why="A double is inexact past 2^53, so ⌊n / prod⌋ can be off by one for "
                        "products near `n`; an exact integer test is simpler."),
            ]),
            Try("prime_multiples", note="2^k subsets, and the overflow check before every "
                "multiplication. The hidden tests use the first 20 primes and primes near 10^18."),
        ]),
        Part("Derangements", [
            Say(r"""
**Christmas Party.** `n ≤ 10^6` children each bring a gift, and the gifts are handed out
again so that nobody gets their own. How many ways, modulo 10^9 + 7?

Inclusion-exclusion over the "bad" events A_i = "child `i` gets their own gift": if a set
of `j` children are forced to keep their gifts, the rest can be arranged in (n − j)!
ways. So D(n) = Σ_(j=0..n) (−1)^j C(n, j) (n − j)!.
"""),
            Numeric(r"""
Compute D(4) = 4! − C(4,1)·3! + C(4,2)·2! − C(4,3)·1! + C(4,4)·0!.
""", answer=9,
                explain=r"""
24 − 24 + 12 − 4 + 1 = 9. (For 3 children there are 2: both 3-cycles.)
"""),
            Reflect(r"""
A recurrence is often easier to code. Child 1 gives to some child `j` (n − 1 choices).
Split on whether `j` gives back to child 1. How many derangements are in each case?
""", answer=r"""
If `j` gives back to child 1, those two are done, and the other n − 2 children must form a
derangement among themselves: D(n − 2). If `j` does not give to child 1, look at the n − 1
children other than 1: `j` has one forbidden recipient (child 1) and everyone else has
their own gift forbidden, which is exactly a derangement of n − 1 items: D(n − 1). So
D(n) = (n − 1)(D(n − 1) + D(n − 2)), with D(1) = 0 and D(2) = 1.
"""),
            Numeric(r"""
As `n` grows, what fraction of all n! permutations are derangements? (Two decimals are
enough.)
""", answer=0.3679, tol=0.008,
                hint="D(n) = n! · (1 − 1 + 1/2! − 1/3! + ...). Which series is that?",
                explain=r"""
1/e ≈ 0.3679: the series is e^(−1). Already D(4)/4! = 9/24 = 0.375. So a random
permutation has no fixed point with probability about 37%, whatever `n` is.
"""),
            Try("christmas_party", note="O(n) with the recurrence. `(i − 1) * (...)` needs `long "
                "long`, and D(1) = 0."),
        ]),
        Part("Linearity of expectation", [
            Say(r"""
A hundred guests leave their hats at a cloakroom, and the hats come back in a uniformly
random order. On average, how many guests get their own hat back?
"""),
            Numeric(r"""
Guess first, then think: the expected number of guests who get their own hat.
""", answer=1,
                hint="Let X_i be 1 if guest i gets their own hat. What is E[X_i]?",
                explain=r"""
Exactly 1. Write X = X_1 + ... + X_100 with X_i = 1 when guest `i` gets their own hat.
Each E[X_i] = P(guest i gets their hat) = 1/100, so E[X] = 100 · 1/100 = 1, for any
number of guests.
"""),
            MCQ(r"""
The X_i are far from independent: if 99 guests have their own hats, the last one surely
does too. Is E[X_1 + ... + X_n] = E[X_1] + ... + E[X_n] still valid?
""", [
                Opt("No: the sum rule needs independent variables.",
                    why="That is the rule for *products*: E[XY] = E[X]E[Y] needs independence. Sums "
                        "never do."),
                Opt("Yes: linearity of expectation holds for any random variables.", correct=True,
                    why="Right. E[X + Y] is a sum over outcomes of (X + Y) times the probability, "
                        "which splits into the two sums, whatever the dependence."),
                Opt("Only approximately, for large `n`.",
                    why="It is exact for every `n`; the answer is exactly 1 even for n = 2 (one "
                        "permutation with 2 fixed points, one with 0)."),
            ], explain=r"""
The recipe: write the quantity as a sum of indicators (0/1 variables), and add up their
probabilities. Each probability usually involves only one or two objects, even when the
whole distribution is hopeless.
"""),
            Say(r"""
**Inversion Probability.** `n ≤ 100` children stand in a row, and child `i` picks a number
uniformly from `1..r_i` (r_i ≤ 100). What is the expected number of inversions, pairs
`i < j` with a_i > a_j?

The brute force enumerates every outcome and averages the inversion counts.
"""),
            Numeric(r"""
With `n = 100` and every r_i = 100, how many outcomes are there?
""", answer=1e200, rel=0.5, unit="outcomes",
                explain=r"""
100^100 = 10^200. No constant factor rescues that.
"""),
            Reflect(r"""
Write the number of inversions as a sum of indicators. What does its expectation become,
and how would you compute each term?
""", answer=r"""
I = Σ_(i<j) [a_i > a_j], so E[I] = Σ_(i<j) P(a_i > a_j). Each term involves only two
children: if a_i = x, exactly min(x − 1, r_j) values of a_j are smaller, so
P(a_i > a_j) = Σ_(x=1..r_i) min(x − 1, r_j) / (r_i · r_j). That is 4950 pairs times at
most 100 values: 5·10^5 steps instead of 10^200.
"""),
            Numeric(r"""
Two children with r_1 = 3 and r_2 = 2. What is the expected number of inversions?
""", answer=0.5, tol=1e-9,
                hint="Six equally likely outcomes (x, y). In how many is x > y?",
                explain=r"""
x = 1 beats nothing, x = 2 beats y = 1, x = 3 beats both: 3 of 6 outcomes, so 0.5.
"""),
            Try("inversion_probability", note="Print with `fixed << setprecision(6)`."),
            MCQ(r"""
When does linearity *not* help? Consider the expected **maximum** of the children's
picks.
""", [
                Opt("E[max] = max of the E[a_i].",
                    why="Two fair coins with values 0/1: each has expectation 1/2, but the max is 1 "
                        "with probability 3/4, so E[max] = 3/4."),
                Opt("A maximum is not a sum, so linearity does not apply directly. Use independence: "
                    "P(max ≤ x) = Π P(a_i ≤ x), then E[max] = Σ_(x≥1) P(max ≥ x).", correct=True,
                    why="Yes. Linearity handles sums of indicators; for a max or a min, go through "
                        "the distribution function, which multiplies nicely for independent picks."),
                Opt("E[max] = (E[a_1] + ... + E[a_n]) / n.",
                    why="That is the expected *average*, which is at most the expected maximum."),
            ]),
        ]),
        Part("DP over probabilities", [
            Say(r"""
**Dice Probability.** A fair die is thrown `n ≤ 100` times. What is the probability that
the sum lies in `[a, b]`? The brute force lists all sequences of throws.
"""),
            Numeric(r"""
How many sequences are there for `n = 100`?
""", answer=6.5e77, rel=0.5, unit="sequences",
                explain=r"""
6^100 ≈ 6.5·10^77.
"""),
            Reflect(r"""
Many of those sequences reach the same partial sum after a few throws. What is the only
thing about the first `t` throws that the rest of the process cares about? Turn that into
a DP.
""", answer=r"""
Only the current sum matters, not how it was reached. So let `dp[t][s]` be the
probability that the first `t` throws sum to `s`. Then `dp[0][0] = 1` and
`dp[t][s] = Σ_(f=1..6) dp[t−1][s−f] / 6`, and the answer is Σ_(s=a..b) dp[n][s]. The
table has 100 · 601 entries with 6 transitions each: about 3.6·10^5 steps. It is algo06's
counting DP with probabilities instead of counts.
"""),
            Numeric(r"""
Two dice: what is the probability that the sum is 7? (A fraction like `1/6` is fine.)
""", answer=1 / 6, tol=0.004,
                explain=r"""
dp[1] is 1/6 on each of 1..6; dp[2][7] = (dp[1][6] + dp[1][5] + ... + dp[1][1]) / 6 =
6 · (1/6) / 6 = 1/6. Six of the 36 outcomes.
"""),
            MCQ(r"""
Why not count the sequences in a `long long` table and divide by 6^n at the end?
""", [
                Opt("6^n does not fit: 6^25 is already about 2.8·10^19, beyond `long long`.",
                    correct=True,
                    why="Right. Counts overflow long before n = 100, while probabilities stay in "
                        "[0, 1]. The smallest one, 6^(−100) ≈ 1.5·10^(−78), is still far above "
                        "the smallest positive `double`."),
                Opt("Counting is slower than probabilities.",
                    why="Same number of steps. The problem is the size of the numbers."),
                Opt("Doubles are exact, so probabilities are more precise.",
                    why="Doubles are not exact (0.1 has no exact binary form), but their relative "
                        "error of about 10^(−16) is harmless here. Overflow is the real issue."),
            ]),
            Try("dice_probability", note="`fixed << setprecision(6)` again."),
            Numeric(r"""
One more pattern, for expected values. You throw a die until the first 6 appears. What is
the expected number of throws?
""", answer=6,
                hint="Let E be the answer. After the first throw you either stop (probability 1/6) "
                     "or you are back where you started, one throw later. Write an equation for E.",
                explain=r"""
E = 1 + (5/6)E gives E = 6. Conditioning on the first step and writing the expectation of
a state in terms of the states it moves to is the general recipe for expected-value DPs;
here there is only one state, so the "DP" is a single equation.
"""),
        ]),
    ],
    problems=[BINOMIAL, PRIME_MULTIPLES, CHRISTMAS, INVERSIONS, DICE],
    cards=[
        Card(r"""C(a, b) mod a prime p, for many queries with a < p?""",
             r"""Precompute `fact[i]` and `inv_fact[i]`; answer `fact[a] * inv_fact[b] % p * inv_fact[a-b] % p`."""),
        Card(r"""How do you fill `inv_fact` in O(N)?""",
             r"""`inv_fact[N] = power(fact[N], p - 2)`, then `inv_fact[i-1] = inv_fact[i] * i % p` for i = N down to 1."""),
        Card(r"""Why is b! invertible modulo the prime p = 10^9 + 7 when b ≤ 10^6?""",
             r"""b! is a product of numbers below p, and a prime dividing a product divides a factor, so gcd(b!, p) = 1. It fails once b ≥ p (then b! ≡ 0)."""),
        Card(r"""Stars and bars: `m` identical items into `n` boxes, empty allowed? At least one each?""",
             r"""C(m + n − 1, n − 1). At least one each: C(m − 1, n − 1)."""),
        Card(r"""Inclusion-exclusion for |A_1 ∪ ... ∪ A_k|?""",
             r"""Σ over non-empty subsets S of (−1)^(|S|+1) · |∩_(i∈S) A_i|. An element in j sets is counted C(j,1) − C(j,2) + ... = 1 time."""),
        Card(r"""How do you build a product of up to 20 numbers without overflowing, when only products ≤ n matter?""",
             r"""Before `prod *= p`, test `if (prod > n / p)`: the product would exceed n, so its term ⌊n/prod⌋ is 0; skip it."""),
        Card(r"""Derangements: recurrence and base cases?""",
             r"""D(n) = (n − 1)(D(n − 1) + D(n − 2)), D(1) = 0, D(2) = 1. Also D(n) = Σ (−1)^j C(n, j)(n − j)! ≈ n!/e."""),
        Card(r"""Does linearity of expectation need independence?""",
             r"""No. E[X + Y] = E[X] + E[Y] always; independence is needed for E[XY] = E[X]E[Y]."""),
        Card(r"""Expected number of fixed points of a random permutation of n?""",
             r"""1, for every n: n indicators, each with probability 1/n."""),
        Card(r"""Expected number of inversions when child i picks uniformly from 1..r_i?""",
             r"""Σ over pairs i < j of P(a_i > a_j) = Σ_x min(x − 1, r_j) / (r_i r_j): linearity over pair indicators."""),
        Card(r"""DP for the distribution of the sum of n dice?""",
             r"""`dp[t][s] = Σ_(f=1..6) dp[t−1][s−f] / 6`, `dp[0][0] = 1`. Probabilities in `double`, not counts in `long long` (6^25 overflows)."""),
        Card(r"""Expected number of throws of a die until the first 6?""",
             r"""6: E = 1 + (5/6)E. Condition on the first step."""),
    ],
)
