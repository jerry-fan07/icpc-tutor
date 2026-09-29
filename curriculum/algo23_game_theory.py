from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


# ------------------------------------------------------------------ generators
def _sticks(rng, n, k, pmax):
    k = min(k, pmax, n)
    p = rng.sample(range(1, min(pmax, n) + 1), k)
    return f"{n} {k}\n" + " ".join(map(str, p)) + "\n"


def _heaps(rng, t, nmax, xmax, total=None):
    """t games of up to nmax heaps; about a third are nudged to XOR 0 so that both answers
    are common. With `total`, the heap counts add up to at most `total`."""
    out = [str(t)]
    left = total
    for i in range(t):
        n = rng.randint(1, nmax)
        if left is not None:
            n = max(1, min(n, left - (t - 1 - i)))
            left -= n
        hs = [rng.randint(1, xmax) for _ in range(n)]
        if rng.random() < 0.35 and n >= 2:
            x = 0
            for h in hs[:-1]:
                x ^= h
            if 1 <= x <= xmax:
                hs[-1] = x
        out.append(str(n))
        out.append(" ".join(map(str, hs)))
    return "\n".join(out) + "\n"


def _restricted(rng, k, smax, t, nmax, xmax, total=None):
    s = rng.sample(range(1, smax + 1), min(k, smax))
    return f"{len(s)}\n" + " ".join(map(str, s)) + "\n" + _heaps(rng, t, nmax, xmax, total)


def _split_heavy(rng, t, n):
    """Every test contains a heap of 2000: recomputing the Grundy table per test costs
    10^6 steps each time."""
    out = [str(t)]
    for _ in range(t):
        hs = [rng.randint(1, 2000) for _ in range(n - 1)] + [2000]
        rng.shuffle(hs)
        out.append(str(n))
        out.append(" ".join(map(str, hs)))
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------- problems
STICK_GAME = Problem(
    id="stick_game",
    title="Stick Game",
    difficulty="easy",
    source="CSES 1729 - Stick Game",
    complexity="O(n·k)",
    statement=r"""
There is a heap of sticks. Two players move in turn; a move removes exactly `p` sticks
from the heap, where `p` is one of the allowed amounts p_1, ..., p_k (and at most the
number of sticks left). The player who cannot move loses.

For every heap size from 1 to `n`, decide whether the player who moves first wins, if both
players play perfectly.
""",
    input=r"""
The first line has `n` and `k` (1 ≤ n ≤ 10^6, 1 ≤ k ≤ 100). The second line has `k`
distinct integers p_1, ..., p_k (1 ≤ p_i ≤ n).
""",
    output=r"""
Print a string of `n` characters: the `i`-th is `W` if the first player wins with `i`
sticks, and `L` if they lose.
""",
    samples=[
        Test("10 3\n1 3 4\n", "WLWWWWLWLW\n"),
        Test("5 2\n2 3\n", "LWWWL\n",
             note="With 1 stick no amount is allowed, so the player to move loses at once."),
    ],
    tests=[
        Test("1 1\n1\n"),
        Test("5 1\n5\n"),
        Test("12 1\n1\n"),
        Test("16 3\n4 2 3\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _sticks(rng, rng.randint(1, 18), rng.randint(1, 4), rng.choice([2, 4, 6])), 14),
        Gen("max n, spread-out moves", lambda rng: _sticks(rng, 10**6, 100, 10**6), 1, large=True),
        Gen("max n, small moves", lambda rng: _sticks(rng, 10**6, 100, 150), 1, large=True),
        Gen("max n, one move", lambda rng: f"{10**6} 1\n{rng.randint(1, 3)}\n", 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<int> p(k);
    for (auto& x : p) cin >> x;
    vector<char> win(n + 1, 0);              // win[0] = 0: no move, the player to move loses
    string out(n, 'L');
    for (int i = 1; i <= n; i++) {           // every move lowers i: smaller heaps are known
        for (int x : p)
            if (x <= i && !win[i - x]) {     // some move hands the opponent a losing heap
                win[i] = 1;
                break;
            }
        if (win[i]) out[i - 1] = 'W';
    }
    cout << out << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
int k;
vector<int> p;
bool win(int i) {                            // plain game-tree search, no table
    for (int x : p) if (x <= i && !win(i - x)) return true;
    return false;
}
int main() {
    int n;
    cin >> n >> k;
    p.resize(k);
    for (auto& x : p) cin >> x;
    for (int i = 1; i <= n; i++) cout << (win(i) ? 'W' : 'L');
    cout << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
int k;
vector<int> p;
bool win(int i) {                            // the recursion, recomputing every subgame
    for (int x : p) if (x <= i && !win(i - x)) return true;
    return false;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n >> k;
    p.resize(k);
    for (auto& x : p) cin >> x;
    string out;
    for (int i = 1; i <= n; i++) out += win(i) ? 'W' : 'L';
    cout << out << '\n';
}
""",
    hints=[
        r"""A heap is winning if some allowed move leaves a losing heap; it is losing if every move
leaves a winning heap, or if there is no move at all (so 0 sticks is losing).""",
        r"""Every move makes the heap smaller, so fill `win[0..n]` in increasing order: when you get
to `i`, all of `win[i - p]` are already known. That is O(n·k) = 10^8 cheap steps.""",
    ],
    editorial=r"""
Backward induction. With 0 sticks the player to move has lost. For `i ≥ 1`, the player to
move wins exactly when some allowed `p ≤ i` leaves `i − p` sticks that are a loss for the
opponent: `win[i] = OR over p of !win[i − p]`. Every move lowers the heap, so computing
`i = 1, 2, ..., n` in order only ever looks at values already computed.

That is at most n·k = 10^8 array lookups, and usually far fewer because a winning heap
stops at its first good move. The same recursion without the table recomputes each smaller
heap an exponential number of times. A memoised recursion gives the right answers, but for
`p = {1}` it recurses 10^6 levels deep, which overflows a default 8 MB stack on judges
that keep it; the loop has no such risk. Print the answer as one string.
""",
)

NIM_GAME = Problem(
    id="nim_game",
    title="Nim",
    difficulty="easy",
    source="CSES 1730 - Nim Game I",
    complexity="O(n) per game",
    statement=r"""
There are `n` heaps of sticks. Two players move in turn; a move takes any positive number
of sticks from one heap. The player who cannot move (all heaps are empty) loses.

For each game, decide who wins with perfect play.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 2·10^4), the number of games. Each game is two lines: `n`
(1 ≤ n ≤ 2·10^5), then the heap sizes x_1, ..., x_n (1 ≤ x_i ≤ 10^9). The sum of `n`
over all games is at most 2·10^5.
""",
    output=r"""
For each game print `first` if the player who moves first wins, `second` otherwise.
""",
    samples=[
        Test("3\n3\n1 2 3\n3\n3 4 5\n1\n1000000000\n", "second\nfirst\nfirst\n"),
    ],
    tests=[
        Test("3\n4\n1 1 1 1\n5\n1 1 1 1 1\n3\n7 7 7\n"),
        Test("2\n2\n6 6\n4\n1 2 4 7\n"),
    ],
    gens=[
        Gen("small games", lambda rng: _heaps(rng, 30, 4, 5), 12),
        Gen("huge heaps, by hand", lambda rng: "3\n2\n1000000000 1000000000\n2\n1000000000 999999999\n"
            "3\n536870912 268435456 805306368\n", 1, large=True),
        Gen("many games", lambda rng: _heaps(rng, 20000, 10, 10**9, 200000), 1, large=True),
        Gen("one huge game", lambda rng: _heaps(rng, 1, 200000, 10**9, 200000), 1, large=True),
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
        int x = 0;                            // heaps < 2^30, so the XOR fits in an int
        for (int i = 0; i < n; i++) {
            int a;
            cin >> a;
            x ^= a;
        }
        cout << (x ? "first" : "second") << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Game-tree search over whole positions (sorted heap sizes), remembering each one.
map<vector<int>, bool> memo;
bool win(vector<int> h) {
    sort(h.begin(), h.end());
    auto it = memo.find(h);
    if (it != memo.end()) return it->second;
    bool w = false;
    for (int i = 0; i < (int)h.size() && !w; i++)
        for (int y = 0; y < h[i] && !w; y++) {
            vector<int> nx = h;
            nx[i] = y;
            if (!win(nx)) w = true;
        }
    return memo[h] = w;
}
int main() {
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<int> h(n);
        for (auto& x : h) cin >> x;
        cout << (win(h) ? "first" : "second") << '\n';
    }
}
""",
    hints=[
        r"""Work out small positions by hand: (1, 1), (2, 2), (1, 2), (1, 2, 3). Then write the heap
sizes in binary.""",
        r"""The first player loses exactly when the XOR of all heap sizes is 0.""",
    ],
    editorial=r"""
Let `X = x_1 ^ x_2 ^ ... ^ x_n`. The first player wins iff `X ≠ 0`.

- The final position (all heaps empty) has `X = 0`, and the player to move there loses.
- From `X = 0`, every move changes one heap from `a` to some `a' ≠ a`, which changes the
  XOR by `a ^ a' ≠ 0`: the opponent always receives `X ≠ 0`.
- From `X ≠ 0`, let `d` be the highest set bit of `X`. Some heap `a` has bit `d` set;
  `a ^ X` keeps `a`'s bits above `d` and clears bit `d`, so it is smaller than `a`. Reduce
  that heap to `a ^ X` and the XOR becomes 0.

So the player facing `X ≠ 0` can always hand over `X = 0`, the other can never hand it
back, and since sticks only disappear, the game ends at all-empty on the turn of the player
facing 0. O(n) per game.
""",
)

RESTRICTED_NIM = Problem(
    id="restricted_nim",
    title="Restricted Nim",
    difficulty="medium",
    source="CSES 1098 - Nim Game II (generalised to any set of moves)",
    complexity="O(X·k + total n), X = 10^5",
    statement=r"""
Nim with a rule: a move takes exactly `s` sticks from one heap, where `s` must be one of
the allowed amounts s_1, ..., s_k (and at most that heap's size). The player who cannot
move loses. The allowed amounts are the same for all games.

For each game, decide who wins with perfect play.
""",
    input=r"""
The first line has `k` (1 ≤ k ≤ 100), the second the `k` distinct allowed amounts
s_1, ..., s_k (1 ≤ s_i ≤ 10^5). The third line has `t` (1 ≤ t ≤ 2·10^4). Each game is two
lines: `n` (1 ≤ n ≤ 2·10^5), then x_1, ..., x_n (1 ≤ x_i ≤ 10^5). The sum of `n` over all
games is at most 2·10^5.
""",
    output=r"""
For each game print `first` or `second`.
""",
    samples=[
        Test("3\n1 2 3\n3\n2\n1 1\n2\n1 2\n3\n4 5 6\n", "second\nfirst\nfirst\n",
             note="Heaps of 1 and of 2 are each a win on their own. Together, (1, 1) loses and "
                  "(1, 2) wins."),
        Test("2\n2 3\n2\n2\n4 7\n1\n1\n", "first\nsecond\n"),
    ],
    tests=[
        Test("1\n1\n3\n1\n100000\n2\n3 4\n3\n1 1 1\n"),
        Test("1\n5\n2\n3\n1 2 4\n2\n5 5\n"),
        Test("3\n100000 99999 1\n2\n1\n100000\n1\n99999\n"),
    ],
    gens=[
        Gen("small games", lambda rng: _restricted(rng, rng.randint(1, 4), 6, 30, 3, 9), 14),
        Gen("big heaps, by hand", lambda rng: "3\n100000 99999 1\n1\n2\n99999 100000\n", 1, large=True),
        Gen("max size, many amounts", lambda rng: _restricted(rng, 100, 100000, 20000, 10, 100000, 200000), 1, large=True),
        Gen("max size, small amounts", lambda rng: _restricted(rng, 100, 150, 20000, 10, 100000, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int MAXX = 100000;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int k;
    cin >> k;
    vector<int> s(k);
    for (auto& v : s) cin >> v;
    // Grundy number of one heap, for every size, computed once
    vector<int> g(MAXX + 1), seen(k + 2, -1);
    for (int x = 0; x <= MAXX; x++) {
        for (int v : s)
            if (v <= x) seen[g[x - v]] = x;   // at most k options, so every g is <= k
        int m = 0;
        while (seen[m] == x) m++;             // mex: the smallest value no option has
        g[x] = m;
    }
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        int x = 0;
        for (int i = 0; i < n; i++) {
            int a;
            cin >> a;
            x ^= g[a];                        // a sum of games: XOR of the Grundy numbers
        }
        cout << (x ? "first" : "second") << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Game-tree search over whole positions (sorted heaps), remembering each one.
vector<int> s;
map<vector<int>, bool> memo;
bool win(vector<int> h) {
    sort(h.begin(), h.end());
    auto it = memo.find(h);
    if (it != memo.end()) return it->second;
    bool w = false;
    for (int i = 0; i < (int)h.size() && !w; i++)
        for (int v : s)
            if (v <= h[i]) {
                vector<int> nx = h;
                nx[i] -= v;
                if (!win(nx)) { w = true; break; }
            }
    return memo[h] = w;
}
int main() {
    int k;
    cin >> k;
    s.resize(k);
    for (auto& v : s) cin >> v;
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<int> h(n);
        for (auto& x : h) cin >> x;
        cout << (win(h) ? "first" : "second") << '\n';
    }
}
""",
    hints=[
        r"""Knowing which single heaps are wins is not enough: with amounts {1, 2, 3}, heaps 1 and 2
are both wins alone, yet (1, 1) loses and (1, 2) wins.""",
        r"""Compute the Grundy number of every heap size once: `g[x] = mex { g[x − s_i] }`, the
smallest non-negative integer that is not among the options. `g[0] = 0`.""",
        r"""The first player wins iff the XOR of `g[x_i]` over the heaps is not 0. A heap has at
most `k` options, so every `g` is at most `k`.""",
    ],
    editorial=r"""
Each heap is a separate game, and a move is made in exactly one of them: the position is
a **sum** of games. The Sprague-Grundy theorem says each game behaves like a Nim heap of
size equal to its **Grundy number**, `g(x) = mex{ g(x − s_i) : s_i ≤ x }`, where `mex` is
the smallest non-negative integer missing from the set. So the sum behaves like Nim on the
Grundy numbers, and the first player wins iff their XOR is nonzero.

Why mex: from a position with value `g` you can move to positions of every value `0..g−1`
(that is what "smallest missing" means) and never to one of value `g`, exactly like a Nim
heap of size `g`. Moves to larger values exist too, but the opponent can always answer
them by moving back down to `g`, so they never help.

Compute `g[0..10^5]` once: 10^5 · k = 10^7 steps. Win/lose per heap is not enough
(the first sample), and with amounts {1, 2, 3} the table is `x mod 4`, which is
CSES Nim Game II.
""",
)

SPLITTING_PILES = Problem(
    id="splitting_piles",
    title="Splitting Piles",
    difficulty="hard",
    source="CSES 2207 - Grundy's Game (variant: many small heaps)",
    complexity="O(H^2 + total n), H = 2000",
    statement=r"""
A move takes one heap and splits it into two non-empty heaps of **different** sizes. A heap
of 1 or 2 sticks can therefore never be split. Players move in turn, and the player who
cannot move loses.

For each game, decide who wins with perfect play.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5). Each game is two lines: `n` (n ≥ 1), then the heap
sizes h_1, ..., h_n (1 ≤ h_i ≤ 2000). The sum of `n` over all games is at most 2·10^5.
""",
    output=r"""
For each game print `first` or `second`.
""",
    samples=[
        Test("3\n1\n3\n1\n4\n2\n5 6\n", "first\nsecond\nfirst\n",
             note="4 can only become 1 + 3 (2 + 2 is not allowed), and then 3 becomes 1 + 2."),
    ],
    tests=[
        Test("3\n1\n1\n1\n2\n3\n1 2 2\n"),
        Test("2\n2\n3 3\n2\n7 7\n"),
    ],
    gens=[
        Gen("small games", lambda rng: _heaps(rng, 30, 3, 12), 14),
        Gen("larger heaps", lambda rng: _heaps(rng, 20, 2, 16), 3),
        Gen("heaps of 2000, by hand", lambda rng: "3\n2\n2000 2000\n1\n2000\n2\n1999 2000\n", 1, large=True),
        Gen("many games with a 2000 heap", lambda rng: _split_heavy(rng, 100000, 2), 1, large=True),
        Gen("max total, random", lambda rng: _heaps(rng, 10000, 30, 2000, 200000), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

const int MAXH = 2000;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    // Grundy number of a single heap, computed once before reading any game
    vector<int> g(MAXH + 1, 0), seen(2048, -1);     // g stays below 64 up to 2000
    for (int h = 1; h <= MAXH; h++) {
        for (int a = 1; a < h - a; a++)             // split into a < h - a, both non-empty
            seen[g[a] ^ g[h - a]] = h;              // the two new heaps form a sum: XOR
        int m = 0;
        while (seen[m] == h) m++;
        g[h] = m;
    }
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        int x = 0;
        for (int i = 0; i < n; i++) {
            int h;
            cin >> h;
            x ^= g[h];
        }
        cout << (x ? "first" : "second") << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Game-tree search over whole positions (sorted heaps), remembering each one.
map<vector<int>, bool> memo;
bool win(vector<int> h) {
    sort(h.begin(), h.end());
    auto it = memo.find(h);
    if (it != memo.end()) return it->second;
    bool w = false;
    for (int i = 0; i < (int)h.size() && !w; i++)
        for (int a = 1; a < h[i] - a && !w; a++) {
            vector<int> nx = h;
            nx[i] = a;
            nx.push_back(h[i] - a);
            if (!win(nx)) w = true;
        }
    return memo[h] = w;
}
int main() {
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<int> h(n);
        for (auto& x : h) cin >> x;
        cout << (win(h) ? "first" : "second") << '\n';
    }
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
// Right answers, but the Grundy table is rebuilt inside every game.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<int> hs(n);
        for (auto& h : hs) cin >> h;
        int H = *max_element(hs.begin(), hs.end());
        vector<int> g(H + 1, 0), seen(2048, -1);
        for (int h = 1; h <= H; h++) {
            for (int a = 1; a < h - a; a++) seen[g[a] ^ g[h - a]] = h;
            int m = 0;
            while (seen[m] == h) m++;
            g[h] = m;
        }
        int x = 0;
        for (int h : hs) x ^= g[h];
        cout << (x ? "first" : "second") << '\n';
    }
}
""",
    hints=[
        r"""A game is a sum of one-heap games. After a split, the one heap has become a sum of two
heaps, whose Grundy number is the XOR of theirs.""",
        r"""`g[h] = mex { g[a] ^ g[h − a] : 1 ≤ a < h − a }`, with `g[1] = g[2] = 0`. Then XOR over
the heaps of a game.""",
        r"""The table costs about 2000^2 / 4 = 10^6 steps. Build it once, before the games: there
can be 10^5 games.""",
    ],
    editorial=r"""
By Sprague-Grundy, a game is decided by the XOR of its heaps' Grundy numbers. A single
heap `h` moves to the pair `(a, h − a)` with `1 ≤ a < h − a`, and that pair is itself a sum
of two games, with Grundy number `g(a) ^ g(h − a)`. Hence

```
g(h) = mex { g(a) ^ g(h − a) : 1 ≤ a < h − a },   g(1) = g(2) = 0
```

which starts `0, 0, 1, 0, 2, 1, 0, 2, 1, 0, ...` for `h = 1, 2, 3, ...`. The values stay
small (below 64 for `h ≤ 2000`), so a mark array of 2048 entries and a timestamp make the
mex cheap.

The table takes about `2000^2 / 4 = 10^6` steps. Built once, the whole input is a
lookup-and-XOR; rebuilt inside the loop over games, it costs up to 10^5 · 10^6 = 10^11.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo23",
    title="game theory",
    track="algo",
    order=23,
    summary="Winning and losing positions by backward induction, the XOR rule for Nim and "
            "its proof, and Grundy numbers (mex) for sums of games, including games whose "
            "moves split a position in two.",
    prereqs=["algo06", "cpp10"],
    tags=["games", "backward induction", "Nim", "XOR", "Sprague-Grundy", "mex"],
    parts=[
        Part("Who wins with perfect play?", [
            Say(r"""
A heap of `n` sticks. Two players move in turn; a move removes `p` sticks, where `p` must
be one of a few allowed amounts (and at most what is left). The player who cannot move
loses. For every `n` from 1 to 10^6, and up to `k = 100` allowed amounts: does the player
who moves first win, if both play perfectly?

Call a position **winning** (W) if the player to move can force a win from it, and
**losing** (L) otherwise. These games are *impartial* (both players have the same moves)
and always end, so every position is one or the other.
"""),
            Short(r"""
Allowed amounts `{1, 3, 4}`, and the heap has 2 sticks. Is it W or L for the player to
move?
""", accept=["L", "losing", "lose"], placeholder="W or L",
                explain=r"""
L. The only legal move takes 1 stick. The opponent then takes the last stick, and you face
an empty heap with no move.
"""),
            MCQ(r"""
Which rule decides W and L in general?
""", [
                Opt("W if **some** move leads to an L position; L if **every** move leads to a W "
                    "position (including when there is no move at all).", correct=True,
                    why="Yes. You need one good move; your opponent then faces a lost position. A "
                        "position with no moves is L, because every move (there are none) leads to W."),
                Opt("W if most moves lead to L positions.",
                    why="One move to an L position is enough; you will simply play it. Counting moves "
                        "means nothing when both players choose the best one."),
                Opt("W if some move leads to a W position.",
                    why="Backwards: after your move it is the opponent's turn, so moving to a W position "
                        "hands *them* the win."),
                Opt("W if the number of sticks is odd.",
                    why="That is right only when the sole allowed amount is 1. With `{1, 3, 4}`, 7 sticks "
                        "is odd and still L, while 4 is even and W."),
            ]),
            Reflect(r"""
The rule translates straight into a recursion:

```cpp
bool win(int i) {
    for (int p : amounts) if (p <= i && !win(i - p)) return true;
    return false;
}
```

It is correct, and for `n = 10^6` it never finishes. What is it wasting?
""", answer=r"""
It solves the same subgames over and over. `win(i)` calls `win(i − 1)`, `win(i − 3)` and
`win(i − 4)`, and each of those calls the smaller ones again, so a heap of `j` sticks is
solved once for every path of moves leading to it, exponentially many times. There are
only `n + 1` different heap sizes: solve each once and store the answer.
"""),
            Numeric(r"""
To see how bad it is: with amounts `{1, 2}` and ignoring the early `return`, the number of
calls obeys `calls(i) = 1 + calls(i − 1) + calls(i − 2)`, like the Fibonacci numbers. Roughly
how many calls for `i = 50`?
""", answer=5.3e10, rel=0.9, unit="calls",
                hint="Fibonacci numbers grow by a factor of about 1.618 per step.",
                explain=r"""
About 5·10^10 (exactly `F(53) − 1`): close to a minute for one heap of 50 sticks, and the
problem wants every heap up to 10^6.
"""),
        ]),
        Part("Backward induction", [
            Say(r"""
Store the answers in a table `win[0..n]` and fill it from small to large:

```cpp
win[0] = false;                          // no move: the player to move loses
for (int i = 1; i <= n; i++)
    for (int p : amounts)
        if (p <= i && !win[i - p]) { win[i] = true; break; }
```

This is **backward induction**: decide the positions closest to the end first, then the
ones that lead to them.
"""),
            Short(r"""
Fill the table by hand for amounts `{1, 3, 4}` and heaps `1..10`. Write the ten letters
(W or L) with no spaces.
""", accept=["WLWWWWLWLW"], placeholder="ten letters",
                hint="Heap 0 is L. Heap `i` is W iff one of `i − 1`, `i − 3`, `i − 4` (when not negative) is L.",
                explain=r"""
`WLWWWWLWLW`. Heap 7 is L because 6, 4 and 3 are all W; heap 9 is L because 8, 6 and 5 are
all W. From here the pattern repeats with period 7, but you do not need to spot it: the
table is fast enough.
"""),
            MCQ(r"""
Why is filling the table in increasing order of `i` correct?
""", [
                Opt("Every move makes the heap smaller, so every position `i` depends on is already "
                    "computed.", correct=True,
                    why="Yes. Positions and moves form a directed acyclic graph, and any order in which "
                        "every move points to an earlier position works (algo12's topological order). "
                        "Here that order is simply increasing `i`."),
                Opt("Because W and L alternate as `i` grows.",
                    why="They do not: `{1, 3, 4}` gives W L W W W W L. The order works for any pattern."),
                Opt("Because both players have the same moves.",
                    why="Impartiality is why a position is simply W or L for whoever moves. The order of "
                        "computation comes from the moves always shrinking the heap."),
            ]),
            Numeric(r"""
In the worst case, how many checks does the table make for `n = 10^6` and `k = 100`?
""", answer=1e8, rel=0.5, unit="checks",
                explain=r"""
`n·k = 10^8` array lookups, around a tenth of a second. W positions usually stop at their
first good move, so the real count is lower.
"""),
            MCQ(r"""
You write the memoised recursion instead of the loop (same answers, same complexity).
With `n = 10^6` and amounts `{1}`, what is the risk?
""", [
                Opt("None: memoisation makes it O(n·k) too.",
                    why="The time is fine. The depth is not: `win(10^6)` calls `win(10^6 − 1)` before "
                        "anything is stored, and so on down to 0."),
                Opt("A recursion 10^6 calls deep, which can overflow the stack.", correct=True,
                    why="Right. On a judge that keeps the default 8 MB stack, 10^6 frames of dozens of "
                        "bytes each overflow it: a runtime error on the largest test only. The loop has no "
                        "depth at all."),
                Opt("Wrong answers, because memoised values can be stale.",
                    why="A position's value never changes; memoisation is exact here."),
            ]),
            Try("stick_game", note="The table, in increasing order, printed as one string."),
        ]),
        Part("Nim and the XOR rule", [
            Say(r"""
**Nim**: several heaps (up to 2·10^5 of them, each up to 10^9 sticks). A move takes any
positive number of sticks from **one** heap. The player who cannot move loses.

A position is now the whole list of heap sizes, so the table would need a cell for every
combination: with three heaps of 10^9 that is 10^27 cells. We need a rule, and small cases
are where rules come from.
"""),
            Short(r"""
Two heaps `(1, 1)`. W or L for the player to move?
""", accept=["L", "losing", "lose"], placeholder="W or L",
                explain=r"""
L: you must empty one heap, and the opponent empties the other. In general `(a, a)` is L:
whatever you take from one heap, the opponent takes the same from the other (the mirror
strategy), so you run out of moves first. And `(a, b)` with `a ≠ b` is W: equalise them.
"""),
            Short(r"""
Three heaps `(1, 2, 3)`. W or L for the player to move?
""", accept=["L", "losing", "lose"], placeholder="W or L",
                hint="Try every move. Each leaves either two unequal heaps, or three heaps in which the "
                     "opponent can empty one heap and leave two equal ones.",
                explain=r"""
L. Emptying a heap leaves two unequal heaps (W for the opponent). Every other move leaves
three heaps like `(1, 2, 1)`, `(1, 1, 3)` or `(1, 2, 2)`, from which the opponent empties
one heap to leave two equal heaps.
"""),
            Reflect(r"""
Write the losing positions you know in binary: `(1, 1)` is `01, 01`, `(2, 2)` is `10, 10`,
`(1, 2, 3)` is `01, 10, 11`. What do they have in common?
""", answer=r"""
In every bit position, the number of heaps with that bit set is even. Equivalently, the
XOR of all the heap sizes is 0: `1 ^ 1 = 0`, `2 ^ 2 = 0`, `1 ^ 2 ^ 3 = 0`. The claim, and
the whole solution of Nim: **the player to move loses exactly when the XOR of the heaps is
0**.
"""),
            MCQ(r"""
First half of the proof. The XOR of the heaps is 0 and you move. Why is the XOR nonzero
after your move, whatever you do?
""", [
                Opt("You change exactly one heap from `a` to some `a' ≠ a`, and that changes the XOR "
                    "by `a ^ a'`, which is not 0.", correct=True,
                    why="Yes. `0 ^ a ^ a' = a ^ a' ≠ 0` because `a ≠ a'`. Every move leaves the opponent a "
                        "nonzero XOR."),
                Opt("Because heaps only get smaller.",
                    why="Smaller does not imply a nonzero XOR on its own; what matters is that exactly one "
                        "heap changes."),
                Opt("It is not always true: taking from two heaps can keep the XOR at 0.",
                    why="A move changes only one heap. (With two heaps changed, `(1, 1) → (0, 0)` would "
                        "indeed keep it 0, which is why the one-heap rule matters.)"),
            ]),
            MCQ(r"""
Second half. The XOR `X` is not 0. Which move makes it 0?
""", [
                Opt("Take `X` sticks from the largest heap.",
                    why="Try `(3, 4, 5)`: `X = 2`, and 5 − 2 = 3 gives `(3, 4, 3)` with XOR 4. Subtracting "
                        "and XOR-ing are different operations."),
                Opt("Pick a heap `a` that has the highest set bit of `X`, and reduce it to `a ^ X`.",
                    correct=True,
                    why="Yes. `a ^ X` keeps `a`'s bits above that bit, clears that bit, and changes only "
                        "lower bits, so it is smaller than `a`: a legal move. The new XOR is "
                        "`X ^ a ^ (a ^ X) = 0`."),
                Opt("Pick any heap `a` and reduce it to `a ^ X`.",
                    why="`a ^ X` may be *larger* than `a` (with `X = 2`, 4 ^ 2 = 6), and you cannot add "
                        "sticks. The heap must have `X`'s top bit set."),
            ]),
            Short(r"""
Heaps `(3, 4, 5)`: `X = 3 ^ 4 ^ 5 = 2`. Only one heap can be reduced to make the XOR 0.
Which heap, and to what size? Answer as `old new`.
""", accept=["3 1", "3 -> 1", "3->1", "3 → 1", "3 to 1", "3, 1", "3,1"], placeholder="old new",
                explain=r"""
`3 1`: `3 ^ 2 = 1 < 3`, so take 2 sticks from the heap of 3, leaving `(1, 4, 5)` with
`1 ^ 4 ^ 5 = 0`. For the others, `4 ^ 2 = 6` and `5 ^ 2 = 7` would need sticks added; only 3
has bit 1 (the top bit of `X = 2`) set.
"""),
            MCQ(r"""
Why do the two halves settle who wins?
""", [
                Opt("The player facing a nonzero XOR can always hand back 0; the other never can. "
                    "Sticks only disappear, so the game ends at all-empty (XOR 0) on the turn of the "
                    "player facing 0, who then has no move.", correct=True,
                    why="Yes: an induction on the number of sticks. The terminal position is the base "
                        "case: XOR 0, no move, lost."),
                Opt("Because the first player moves first.",
                    why="Moving first is a disadvantage when the XOR is 0. The XOR decides, not the turn "
                        "order."),
                Opt("Because XOR is associative.",
                    why="Associativity makes the XOR well defined for any number of heaps, but the proof "
                        "is the two halves plus the fact that the game ends."),
            ]),
            Try("nim_game", note="One XOR per game."),
        ]),
        Part("Grundy numbers: when win/lose is not enough", [
            Say(r"""
**Restricted Nim**: heaps as before, but a move takes exactly `s` sticks from one heap,
with `s` from a fixed set of allowed amounts. For amounts `{1, 2, 3}` (CSES Nim Game II),
the Stick Game table says heaps 1, 2 and 3 are each W and heap 4 is L.

Can the verdict for several heaps be put together from those single-heap verdicts?
"""),
            MCQ(r"""
Amounts `{1, 2, 3}`. Heaps 1 and 2 are both W on their own. Yet `(1, 1)` is L and `(1, 2)`
is W. What does that show?
""", [
                Opt("W/L of each heap does not determine the sum: two W heaps can make an L or a W "
                    "position.", correct=True,
                    why="Right. One bit per heap loses information. We need a richer number per heap, "
                        "one that combines the way heap sizes do in Nim."),
                Opt("The sum is W iff an odd number of heaps are W.",
                    why="`(1, 2)` has two W heaps and is W. On this lesson's tests that rule is wrong about "
                        "half the time."),
                Opt("The sum is W iff at least one heap is W.",
                    why="`(1, 1)` has two W heaps and is L."),
            ]),
            Say(r"""
The richer number is the **Grundy number**:

```
g(position) = mex { g(p') : p' reachable in one move }
```

where `mex` of a set is the smallest non-negative integer not in it (`mex{0, 1, 3} = 2`,
`mex{} = 0`). A position with no moves has `g = 0`, and `g = 0` exactly for the L
positions.

The **Sprague-Grundy theorem**: a position with Grundy number `g` behaves, inside any sum
of games, exactly like a Nim heap of `g` sticks. So the Grundy number of a sum is the XOR
of the parts, and the player to move wins iff it is nonzero.
"""),
            Short(r"""
Amounts `{1, 2, 3}`. Compute `g(0), g(1), ..., g(8)`, separated by spaces.
""", accept=["0 1 2 3 0 1 2 3 0"], placeholder="nine numbers",
                hint="`g(x) = mex{ g(x − 1), g(x − 2), g(x − 3) }` over the terms that exist.",
                explain=r"""
`0 1 2 3 0 1 2 3 0`: `g(x) = x mod 4`. So `(1, 1)` has `1 ^ 1 = 0` (L) and `(1, 2)` has
`1 ^ 2 = 3` (W), as found by hand.
"""),
            Reflect(r"""
Why can a position with Grundy number `g` stand in for a Nim heap of size `g`? Think about
which Grundy values its moves reach, and what to do if the opponent moves to a *larger*
value.
""", answer=r"""
By the definition of mex, from value `g` there is a move to a position of every value
`0, 1, ..., g − 1`, and none to a position of value `g`: exactly the moves of a Nim heap of
size `g`. Moves to larger values may also exist, but they never help: if the opponent
raises a component from `g` to `g' > g`, you can move that same component back to value
`g` (possible, since `g < g'`), restoring the XOR. So the Nim proof goes through with the
Grundy numbers in place of the heap sizes.
"""),
            Short(r"""
Amounts `{2, 3}`. The Grundy numbers for heaps `0..7` are `0 0 1 1 2 0 0 1`. Who wins the
game with heaps 4 and 7: `first` or `second`?
""", accept=["first"], placeholder="first or second",
                explain=r"""
First: `g(4) ^ g(7) = 2 ^ 1 = 3 ≠ 0`. A winning move makes the XOR 0 by changing one
heap's value: take 2 from heap 4 (heap 2 has `g = 1`, and `1 ^ 1 = 0`), or take 3 from
heap 7 (heap 4 has `g = 2`, and `2 ^ 2 = 0`). Note that heaps 5 and 6 would be losing on
their own, although they are big: Grundy numbers are not sizes.
"""),
            MCQ(r"""
You compute `g[x]` for all `x ≤ 10^5` with `k ≤ 100` allowed amounts. How large an array
do you need for marking which values the options take, when finding the mex?
""", [
                Opt("`k + 1` or so: a position has at most `k` options, so its mex is at most `k`.",
                    correct=True,
                    why="Yes. With `k` options at most `k` values are present, so some value in `0..k` is "
                        "missing. Reuse one array with a timestamp (`seen[v] = x`) instead of clearing it."),
                Opt("`10^5 + 1`, since Grundy numbers can be as large as the heap.",
                    why="In plain Nim they are (a heap of `x` has `x` options). Here the number of options is "
                        "at most `k`, and the mex cannot exceed the number of options."),
                Opt("A `set<int>` per position; the size cannot be bounded.",
                    why="It can: mex ≤ number of options. A `set` would also cost a log factor and "
                        "allocations 10^5 times."),
            ]),
            Try("restricted_nim", note="Grundy numbers once for all heap sizes, then an XOR per game."),
        ]),
        Part("Games that split", [
            Say(r"""
**Splitting Piles**: a move takes one heap and splits it into two non-empty heaps of
**different** sizes (so heaps of 1 and 2 are stuck). Up to 10^5 games, heaps up to 2000.

A game is a sum of one-heap games, and a move turns one heap into two: the part of the
position that changed is itself a sum.
"""),
            MCQ(r"""
Which formula gives the Grundy number of a single heap `h`?
""", [
                Opt("`g(h) = mex { g(a) + g(h − a) : 1 ≤ a < h − a }`",
                    why="Grundy numbers of a sum combine by XOR, not by addition: two heaps of value 1 are "
                        "`1 ^ 1 = 0`, a losing pair, while `1 + 1 = 2` would call it winning."),
                Opt("`g(h) = mex { g(a) ^ g(h − a) : 1 ≤ a < h − a }`", correct=True,
                    why="Yes. Each option is the pair of heaps `(a, h − a)`, a sum of two games, whose "
                        "Grundy number is the XOR. The sum rule is used *inside* the recursion."),
                Opt("`g(h) = mex { g(a), g(h − a) : 1 ≤ a < h − a }`",
                    why="That treats the move as leading to one heap or the other, but after the split both "
                        "heaps are in play at once."),
            ]),
            Short(r"""
Compute `g(1), g(2), ..., g(7)`, separated by spaces.
""", accept=["0 0 1 0 2 1 0"], placeholder="seven numbers",
                hint="`g(1) = g(2) = 0`. 3 splits only as 1 + 2; 4 only as 1 + 3; 5 as 1 + 4 or 2 + 3.",
                explain=r"""
`0 0 1 0 2 1 0`. For example `g(5) = mex{ g(1) ^ g(4), g(2) ^ g(3) } = mex{0, 1} = 2` and
`g(7) = mex{ g(1) ^ g(6), g(2) ^ g(5), g(3) ^ g(4) } = mex{1, 2, 1} = 0`: a heap of 7 is a
loss for the player to move.
"""),
            Numeric(r"""
About how many (a, h − a) pairs does building `g[1..2000]` examine?
""", answer=1e6, rel=0.5, unit="pairs",
                explain=r"""
Heap `h` has about `h/2` splits, so the total is about `2000^2 / 4 = 10^6`. The Grundy
values stay below 64 here, so a small mark array with a timestamp finds each mex quickly.
"""),
            MCQ(r"""
There are up to 10^5 games. Where should the table be built?
""", [
                Opt("Once, before reading the games.", correct=True,
                    why="Yes. The table does not depend on the game, so building it per game repeats "
                        "10^6 steps up to 10^5 times: 10^11. One hidden test has 10^5 games that each "
                        "contain a heap of 2000."),
                Opt("Inside each game, up to that game's largest heap: it does less work for small games.",
                    why="It is less work for a game of small heaps, but the tests include many games with a "
                        "heap of 2000, and then every game pays 10^6 again."),
                Opt("It does not matter: 10^6 steps is fast.",
                    why="Once, it is. Times 10^5 games it is 10^11 steps."),
            ]),
            Try("splitting_piles", note="Build `g` once; XOR per game."),
        ]),
        Part("Variants and limits", [
            MCQ(r"""
**Misère** Nim: the player who takes the **last** stick loses. How does the rule change?
""", [
                Opt("Not at all: XOR ≠ 0 still means the first player wins.",
                    why="Take one heap of 1: normal Nim is a win (take it), misère is a loss (you must "
                        "take it)."),
                Opt("Swap the answer: XOR = 0 now means the first player wins.",
                    why="Take `(2, 2)`: XOR 0, and in misère the first player still loses: whatever they "
                        "do, the reply can leave a single heap of 1, which they must take. The swap is only "
                        "right when every heap has at most 1 stick."),
                Opt("Play as in normal Nim unless every heap has at most one stick; then the first "
                    "player wins iff the number of heaps of 1 is even.", correct=True,
                    why="Yes. The winning strategy is the normal one until a move would leave only heaps "
                        "of size ≤ 1; then leave an odd number of them. Misère games in general are much "
                        "harder than normal play, and Sprague-Grundy does not apply to them."),
            ]),
            MCQ(r"""
In which game can you **not** use Grundy numbers?
""", [
                Opt("A game where each player may only take from their own heaps.", correct=True,
                    why="Right. When the players have different moves, the game is *partizan* and the same "
                        "position can be a win for one player and a loss for the other. Chess and Go are "
                        "partizan. Sprague-Grundy needs impartial games."),
                Opt("Nim with any number of heaps.",
                    why="Nim is the model impartial game; Grundy numbers are Nim heaps by definition."),
                Opt("A game where a move splits a heap into two.",
                    why="That is the previous problem: splitting is fine, the new heaps are just a sum."),
            ]),
            MCQ(r"""
A game on a directed graph **with cycles**: a token moves along an edge each turn, and the
player who cannot move loses. What changes compared with a DAG?
""", [
                Opt("Nothing: compute W/L in topological order as before.",
                    why="A graph with cycles has no topological order, and the game can go on forever."),
                Opt("Some positions are draws; W/L is found by working backwards from the dead ends "
                    "(retrograde analysis), and whatever is never labelled is a draw.", correct=True,
                    why="Yes. Label dead ends L; a position with a move to an L is W; a position whose moves "
                        "all go to W is L (count them down per vertex, like Kahn's algorithm). Positions "
                        "never labelled let a player avoid losing forever: draws."),
                Opt("The first player always wins, since they can cycle forever.",
                    why="Cycling forever is a draw, not a win, and it is only possible where the cycle is "
                        "reachable and no better option exists."),
            ]),
            Reflect(r"""
Several tokens sit on the vertices of a DAG (n, m ≤ 2·10^5). A move takes one token along
one edge; the player who cannot move loses. How do you decide the winner in O(n + m)?
""", answer=r"""
Each token is an independent game, so the position is a sum. Compute a Grundy number for
every vertex, `g(v) = mex{ g(w) : v → w }`, processing vertices in reverse topological
order (or by memoised DFS), so each vertex costs its out-degree: O(n + m) in total, with
each mex at most the out-degree. Then XOR `g` over the tokens' vertices: nonzero means the
first player wins. Two tokens on the same vertex cancel (`g ^ g = 0`), as in Nim.
"""),
        ]),
    ],
    problems=[STICK_GAME, NIM_GAME, RESTRICTED_NIM, SPLITTING_PILES],
    cards=[
        Card(r"""When is a position winning (W) and when losing (L)?""",
             r"""W if some move leads to an L position; L if every move leads to a W position. A position with no moves is L."""),
        Card(r"""Backward induction for a one-heap subtraction game, and its cost?""",
             r"""`win[0] = false; win[i] = OR over p of !win[i − p]`, for `i` increasing (moves shrink the heap). O(n·k). A loop, not deep recursion."""),
        Card(r"""The Nim rule?""",
             r"""The player to move loses iff the XOR of all heap sizes is 0."""),
        Card(r"""Nim: why does a nonzero XOR always have a move to 0?""",
             r"""Take a heap `a` with the highest set bit of `X`; `a ^ X < a`, so reduce it to `a ^ X`. The new XOR is 0."""),
        Card(r"""Nim: why can't a zero XOR move to zero?""",
             r"""A move changes one heap `a` to `a' ≠ a`, which changes the XOR by `a ^ a' ≠ 0`."""),
        Card(r"""Grundy number of a position?""",
             r"""`g = mex` of the Grundy numbers of the positions one move away; mex = smallest non-negative integer not in the set. No moves: `g = 0`. `g = 0` iff L."""),
        Card(r"""Sprague-Grundy theorem?""",
             r"""An impartial game position with Grundy number `g` is equivalent to a Nim heap of size `g`; a sum of games has Grundy number = XOR of the parts."""),
        Card(r"""Why is win/lose per component not enough for a sum of games?""",
             r"""Two W components can make an L sum or a W sum (subtraction {1,2,3}: (1,1) is L, (1,2) is W). Grundy numbers carry the needed information."""),
        Card(r"""Grundy number when a move splits a heap into `a` and `b`?""",
             r"""The option's value is `g(a) ^ g(b)` (the two heaps are a sum). E.g. Grundy's game: `g(h) = mex{ g(a) ^ g(h−a) : a < h−a }`."""),
        Card(r"""How large can a Grundy number be, and why does it matter?""",
             r"""At most the number of options (the mex of k values is ≤ k). It bounds the mark array for the mex; reuse it with a timestamp."""),
        Card(r"""Misère Nim (last to move loses)?""",
             r"""Same as normal Nim unless every heap is ≤ 1; then the first player wins iff the number of heaps of size 1 is even."""),
        Card(r"""When does Sprague-Grundy not apply?""",
             r"""Partizan games (players have different moves, e.g. chess), misère play in general, and games that can go on forever (cycles: draws, use retrograde analysis)."""),
    ],
)
