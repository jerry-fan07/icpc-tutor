import math
from functools import lru_cache

from cptutor.schema import (Lesson, Part, Say, MCQ, Opt, Numeric, Short, Reflect, Try,
                            Problem, Test, Gen, Card)


LIM = 10**9


# ------------------------------------------------------------------ generators
def _egcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = _egcd(b, a % b)
    return g, y, x - (a // b) * y


def _near_line(rng, lim):
    """p1, p2 and a p3 whose cross product is exactly -1, 0 or +1: the products are
    around 10^18 and a `double` cannot tell them apart."""
    while True:
        x1, y1 = rng.randint(-lim, lim), rng.randint(-lim, lim)
        dx, dy = rng.randint(-lim // 2, lim // 2), rng.randint(-lim // 2, lim // 2)
        g, a, b = _egcd(abs(dx), abs(dy))
        if g != 1 or dx == 0 or dy == 0:
            continue
        # a*|dx| + b*|dy| = 1, so w below has cross(d, w) = 1
        wx, wy = -b * (1 if dy > 0 else -1), a * (1 if dx > 0 else -1)
        s = rng.choice([-1, 0, 1])
        k = rng.randint(-3, 3)
        x2, y2 = x1 + dx, y1 + dy
        x3, y3 = x1 + k * dx + s * wx, y1 + k * dy + s * wy
        if all(-lim <= v <= lim for v in (x2, y2, x3, y3)):
            return f"{x1} {y1} {x2} {y2} {x3} {y3}"


def _three_any(rng, lim):
    while True:
        v = [rng.randint(-lim, lim) for _ in range(6)]
        if (v[0], v[1]) != (v[2], v[3]):
            return " ".join(map(str, v))


def _three_collinear(rng, lim):
    while True:
        x1, y1 = rng.randint(-lim, lim), rng.randint(-lim, lim)
        dx, dy = rng.randint(-3, 3), rng.randint(-3, 3)
        if (dx, dy) == (0, 0):
            continue
        k2, k3 = rng.randint(1, 3), rng.randint(-4, 4)
        v = (x1, y1, x1 + k2 * dx, y1 + k2 * dy, x1 + k3 * dx, y1 + k3 * dy)
        if all(-lim <= c <= lim for c in v):
            return " ".join(map(str, v))


def _location(rng, t, kind):
    out = [str(t)]
    for _ in range(t):
        if kind == "small":
            out.append(_three_collinear(rng, 6) if rng.random() < 0.3 else _three_any(rng, 6))
        elif kind == "near":
            out.append(_near_line(rng, LIM))
        else:
            out.append(_near_line(rng, LIM) if rng.random() < 0.5 else _three_any(rng, LIM))
    return "\n".join(out) + "\n"


def _segment(rng, lim):
    while True:
        a = (rng.randint(-lim, lim), rng.randint(-lim, lim))
        b = (rng.randint(-lim, lim), rng.randint(-lim, lim))
        if a != b:
            return [a, b]


def _collinear_segments(rng, lim, step, spread):
    """Two segments on one line: overlapping, touching, nested or apart."""
    while True:
        x, y = rng.randint(-lim, lim), rng.randint(-lim, lim)
        dx, dy = rng.randint(-step, step), rng.randint(-step, step)
        if (dx, dy) == (0, 0):
            continue
        ks = [rng.randint(-spread, spread) for _ in range(4)]
        if ks[0] == ks[1] or ks[2] == ks[3]:
            continue
        pts = [(x + k * dx, y + k * dy) for k in ks]
        if all(-lim <= c <= lim for p in pts for c in p):
            return pts


def _intersections(rng, t, kind):
    out = [str(t)]
    for _ in range(t):
        if kind == "small":
            pts = (_collinear_segments(rng, 4, 2, 5) if rng.random() < 0.35
                   else _segment(rng, 3) + _segment(rng, 3))
        else:
            pts = (_collinear_segments(rng, LIM, LIM // 8, 4) if rng.random() < 0.2
                   else _segment(rng, LIM) + _segment(rng, LIM))
        out.append(" ".join(f"{x} {y}" for x, y in pts))
    return "\n".join(out) + "\n"


def _monotone_polygon(rng, n, xlim, ylim):
    """A simple polygon with n vertices: a lower chain below y = 0 from the leftmost to
    the rightmost vertex and an upper chain above y = 0 coming back. Random orientation,
    random first vertex, sometimes mirrored across y = x. Usually far from convex."""
    xs = sorted(rng.sample(range(-xlim, xlim + 1), n))
    left, right, mid = xs[0], xs[-1], xs[1:-1]
    k = rng.randint(1, len(mid) - 1) if len(mid) >= 2 else len(mid)
    rng.shuffle(mid)
    low, up = sorted(mid[:k]), sorted(mid[k:])
    pts = [(left, 0)] + [(x, rng.randint(-ylim, -1)) for x in low]
    pts += [(right, 0)] + [(x, rng.randint(1, ylim)) for x in reversed(up)]
    if rng.random() < 0.5:
        pts.reverse()
    s = rng.randrange(n)
    pts = pts[s:] + pts[:s]
    if rng.random() < 0.5:
        pts = [(y, x) for x, y in pts]
    return pts


def _area_input(rng, n, xlim, ylim):
    pts = _monotone_polygon(rng, n, xlim, ylim)
    return f"{n}\n" + "\n".join(f"{x} {y}" for x, y in pts) + "\n"


def _pip_input(rng, n, m, xlim, ylim, span):
    pts = _monotone_polygon(rng, n, xlim, ylim)
    qs = []
    for _ in range(m):
        r = rng.random()
        if r < 0.15:                                      # a vertex
            qs.append(rng.choice(pts))
        elif r < 0.3:                                     # on an edge, when it is a lattice point
            a = rng.randrange(n)
            (x1, y1), (x2, y2) = pts[a], pts[(a + 1) % n]
            t = rng.randint(0, 4)
            if (x2 - x1) * t % 4 == 0 and (y2 - y1) * t % 4 == 0:
                qs.append((x1 + (x2 - x1) * t // 4, y1 + (y2 - y1) * t // 4))
            else:
                qs.append((x1, y1))
        elif r < 0.5:                                     # level with a vertex: rays through vertices
            vx, vy = rng.choice(pts)
            qs.append((rng.randint(-span, span), vy) if rng.random() < 0.5
                      else (vx, rng.randint(-span, span)))
        else:
            qs.append((rng.randint(-span, span), rng.randint(-span, span)))
    out = [f"{n} {m}"] + [f"{x} {y}" for x, y in pts] + [f"{x} {y}" for x, y in qs]
    return "\n".join(out) + "\n"


def _points(pts):
    return f"{len(pts)}\n" + "\n".join(f"{x} {y}" for x, y in pts) + "\n"


def _hull_small(rng, n, lim):
    pts = [(rng.randint(-lim, lim), rng.randint(-lim, lim)) for _ in range(n)]
    for _ in range(rng.randint(0, n // 3)):               # repeated points
        pts[rng.randrange(n)] = rng.choice(pts)
    return _points(pts)


def _hull_line(rng, n, lim, step):
    x, y = rng.randint(-lim // 2, lim // 2), rng.randint(-lim // 2, lim // 2)
    dx, dy = rng.randint(-step, step), rng.randint(-step, step)
    if (dx, dy) == (0, 0):
        dx = 1
    span = max(1, min(n, (lim // 2) // max(abs(dx), abs(dy), 1)))
    return _points([(x + k * dx, y + k * dy) for k in (rng.randint(-span, span) for _ in range(n))])


def _hull_random(rng, n, lim):
    return _points([(rng.randint(-lim, lim), rng.randint(-lim, lim)) for _ in range(n)])


def _hull_rectangle(rng, n, lim):
    """Most points in the middle of the rectangle's edges: 4 corners, many collinear."""
    x1, x2 = sorted(rng.sample(range(-lim, lim + 1), 2))
    y1, y2 = sorted(rng.sample(range(-lim, lim + 1), 2))
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    while len(pts) < n:
        r = rng.random()
        if r < 0.2:
            pts.append((rng.randint(x1, x2), y1))
        elif r < 0.4:
            pts.append((rng.randint(x1, x2), y2))
        elif r < 0.6:
            pts.append((x1, rng.randint(y1, y2)))
        elif r < 0.8:
            pts.append((x2, rng.randint(y1, y2)))
        else:
            pts.append((rng.randint(x1, x2), rng.randint(y1, y2)))
    rng.shuffle(pts)
    return _points(pts)


@lru_cache(maxsize=None)
def _convex_ring(k):
    """A strictly convex lattice polygon: every primitive vector (dx, dy) with
    |dx|, |dy| <= k, sorted by angle and laid end to end. k = 290 gives ~205,000 corners."""
    vs = [(dx, dy) for dx in range(-k, k + 1) for dy in range(-k, k + 1)
          if (dx, dy) != (0, 0) and math.gcd(dx, dy) == 1]
    vs.sort(key=lambda v: math.atan2(v[1], v[0]))
    x = y = 0
    ring = []
    for dx, dy in vs:
        ring.append((x, y))
        x, y = x + dx, y + dy
    return ring


def _hull_convex(rng, n):
    """n points in strictly convex position, shuffled: every point is a corner. The worst
    case for gift wrapping, which does n steps of n."""
    pts = rng.sample(_convex_ring(290), n)
    ox, oy = rng.randint(-10**8, 10**8), 4 * 10**8 + rng.randint(-10**8, 10**8)
    return _points([(x * 60 + ox, y * 60 + oy) for x, y in pts])


# --------------------------------------------------------------------- checker
def _read_hull(text):
    tok = text.split()
    k = int(tok[0])
    if k < 1 or len(tok) != 1 + 2 * k:
        raise ValueError(f"the count says {k} points, but {(len(tok) - 1) / 2:g} follow")
    return [(int(tok[1 + 2 * i]), int(tok[2 + 2 * i])) for i in range(k)]


def _hull_check(inp, expected, got):
    """The corners are unique and so is their counterclockwise cycle; accept any rotation."""
    want = _read_hull(expected)
    if not got.split():
        return False, "no output"
    have = _read_hull(got)
    if len(have) != len(want):
        return False, f"the hull has {len(want)} corners; you printed {len(have)}"
    wanted = set(want)
    for x, y in have:
        if (x, y) not in wanted:
            return False, f"({x}, {y}) is not a corner of the hull"
    if len(set(have)) != len(have):
        return False, "a corner is printed twice"
    s, k = want.index(have[0]), len(want)
    if all(have[i] == want[(s + i) % k] for i in range(k)):
        return True, ""
    if all(have[i] == want[(s - i) % k] for i in range(k)):
        return False, "the right corners, but in clockwise order"
    return False, "the right corners, but not in order around the hull"


# --------------------------------------------------------------------- problems
POINT_LOCATION = Problem(
    id="point_location",
    title="Left or Right",
    difficulty="easy",
    source="CSES 2189 - Point Location Test",
    complexity="O(1) per test",
    statement=r"""
A survey drone flies in a straight line from `p1` through `p2` and keeps going. For a
landmark at `p3`, report whether the drone sees it on its left, on its right, or flies
straight over it (the landmark is on the line, possibly behind `p1` or beyond `p2`).
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5), the number of tests.

Each test is one line with six integers `x1 y1 x2 y2 x3 y3` (−10^9 ≤ each ≤ 10^9): the
points p1, p2, p3. p1 and p2 are different.
""",
    output=r"""
For each test print `LEFT`, `RIGHT` or `TOUCH`.
""",
    samples=[
        Test("3\n0 0 4 2 1 3\n0 0 4 2 3 -1\n0 0 4 2 -2 -1\n", "LEFT\nRIGHT\nTOUCH\n",
             note="The third landmark is on the line behind `p1`: still TOUCH."),
        Test("1\n0 0 781638469 760627983 897313041 873193216\n", "LEFT\n",
             note="The two products in the cross product are about 6.8·10^17 and differ by "
                  "exactly 1. A `double` rounds them to the same number."),
    ],
    tests=[
        Test("4\n-1000000000 -1000000000 1000000000 -1000000000 1000000000 1000000000\n"
             "-1000000000 -1000000000 1000000000 -1000000000 -1000000000 1000000000\n"
             "1000000000 1000000000 -1000000000 -1000000000 1000000000 -1000000000\n"
             "-1000000000 1000000000 1000000000 -1000000000 -1000000000 -1000000000\n"),
        Test("4\n5 -7 5 100 5 -1000000000\n5 -7 5 100 6 0\n5 -7 5 100 4 0\n3 3 -8 3 0 3\n"),
        Test("3\n1 2 3 4 1 2\n1 2 3 4 3 4\n1 2 3 4 5 6\n"),
        Test("2\n0 0 1000000000 999999999 999999999 999999998\n"
             "-1000000000 -999999999 999999999 1000000000 999999998 999999999\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _location(rng, 30, "small"), 10),
        Gen("near the line, huge coordinates", lambda rng: _location(rng, 2000, "near"), 3),
        Gen("max t", lambda rng: _location(rng, 100000, "mixed"), 1, large=True),
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
        long long x1, y1, x2, y2, x3, y3;
        cin >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
        // cross(p2 - p1, p3 - p1); each product is at most (2*10^9)^2 = 4*10^18
        long long c = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1);
        if (c > 0) cout << "LEFT\n";
        else if (c < 0) cout << "RIGHT\n";
        else cout << "TOUCH\n";
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
        long long x1, y1, x2, y2, x3, y3;
        cin >> x1 >> y1 >> x2 >> y2 >> x3 >> y3;
        // twice the signed area of the triangle, shoelace form, in 128 bits
        __int128 a = (__int128)x1 * y2 - (__int128)x2 * y1 + (__int128)x2 * y3
                   - (__int128)x3 * y2 + (__int128)x3 * y1 - (__int128)x1 * y3;
        cout << (a > 0 ? "LEFT" : a < 0 ? "RIGHT" : "TOUCH") << '\n';
    }
}
""",
    hints=[
        r"""Avoid slopes: a vertical line divides by zero and a fraction invites floating point.
What single integer expression is positive exactly when `p3` is to the left?""",
        r"""The cross product `(x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)`: positive means
left (a counterclockwise turn), negative right, zero on the line.""",
        r"""Compute it in `long long`. Each product reaches 4·10^18, which an `int` cannot hold
and a `double` cannot hold exactly.""",
    ],
    editorial=r"""
Let `u = p2 − p1` and `v = p3 − p1`. The cross product `u × v = u.x·v.y − u.y·v.x` is the
signed area of the parallelogram spanned by `u` and `v`: positive when turning from `u`
to `v` is counterclockwise (p3 on the left), negative when clockwise, zero when the three
points are collinear. No division, no special case for vertical lines, and it is exact
in integers.

Size: coordinates within ±10^9 make each difference at most 2·10^9 and each product at
most 4·10^18. `long long` ends at about 9.22·10^18, so it fits. A `double` does not help:
it has 53 bits of mantissa (exact integers only up to about 9·10^15), and the second
sample has two products of about 6.8·10^17 that differ by 1, which `double` rounds to the
same value, so it reports TOUCH.
""",
)

SEGMENT_INTERSECTION = Problem(
    id="segment_intersection",
    title="Crossing Fences",
    difficulty="medium",
    source="CSES 2190 - Line Segment Intersection",
    complexity="O(1) per test",
    statement=r"""
Two straight fences are given by their endpoints. Do they meet? Fences that share even a
single point (an endpoint resting on the other fence, two fences end to end, fences
lying along each other) count as meeting.
""",
    input=r"""
The first line has `t` (1 ≤ t ≤ 10^5).

Each test is one line with eight integers `x1 y1 x2 y2 x3 y3 x4 y4` (−10^9 ≤ each ≤
10^9): the first fence runs from (x1, y1) to (x2, y2), the second from (x3, y3) to
(x4, y4). The two endpoints of a fence are always different.
""",
    output=r"""
For each test print `YES` if the fences share at least one point, `NO` otherwise.
""",
    samples=[
        Test("5\n0 0 4 4 0 4 4 0\n0 0 4 0 2 0 2 3\n0 0 2 2 2 2 5 0\n0 0 1 1 2 2 3 3\n0 0 4 0 1 1 5 1\n",
             "YES\nYES\nYES\nNO\nNO\n",
             note="Test 4: both fences lie on the line y = x, with a gap between them. All four "
                  "orientations are zero there."),
    ],
    tests=[
        Test("6\n0 0 10 0 3 0 5 0\n0 0 4 0 4 0 9 0\n0 0 0 2 0 3 0 5\n0 0 0 3 0 3 0 5\n"
             "0 0 2 0 3 -1 3 1\n0 0 4 0 4 1 4 5\n"),
        Test("4\n-1000000000 -1000000000 1000000000 1000000000 -1000000000 1000000000 1000000000 -1000000000\n"
             "-1000000000 -1000000000 1000000000 1000000000 1000000000 -1000000000 999999999 -1000000000\n"
             "-1000000000 0 1000000000 1 -1000000000 1 1000000000 0\n"
             "-1000000000 -1000000000 1000000000 999999999 -1000000000 -999999999 1000000000 1000000000\n"),
        Test("3\n1 1 1 1000000000 1 -5 1 0\n1 1 1 1000000000 1 -5 1 1\n-3 7 5 7 5 7 -3 7\n"),
    ],
    gens=[
        Gen("small, many collinear", lambda rng: _intersections(rng, 200, "small"), 12),
        Gen("huge coordinates", lambda rng: _intersections(rng, 3000, "big"), 3),
        Gen("max t", lambda rng: _intersections(rng, 100000, "big"), 1, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

struct P { long long x, y; };

long long cross(P a, P b, P c) {             // (b - a) x (c - a)
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
}
int sgn(long long v) { return (v > 0) - (v < 0); }

// c is already known to be on the line through a and b: is it between them?
bool onSegment(P a, P b, P c) {
    return min(a.x, b.x) <= c.x && c.x <= max(a.x, b.x) &&
           min(a.y, b.y) <= c.y && c.y <= max(a.y, b.y);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        P a, b, c, d;
        cin >> a.x >> a.y >> b.x >> b.y >> c.x >> c.y >> d.x >> d.y;
        // signs, not the raw values: o1 * o2 of two 4*10^18 numbers would overflow
        int o1 = sgn(cross(a, b, c)), o2 = sgn(cross(a, b, d));
        int o3 = sgn(cross(c, d, a)), o4 = sgn(cross(c, d, b));
        bool hit;
        if (o1 * o2 < 0 && o3 * o4 < 0) hit = true;          // a proper crossing
        else hit = (o1 == 0 && onSegment(a, b, c)) ||         // otherwise some endpoint
                   (o2 == 0 && onSegment(a, b, d)) ||         // must lie on the other
                   (o3 == 0 && onSegment(c, d, a)) ||         // segment
                   (o4 == 0 && onSegment(c, d, b));
        cout << (hit ? "YES" : "NO") << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
typedef __int128 L;
int main() {
    int t;
    cin >> t;
    while (t--) {
        long long v[8];
        for (auto& x : v) cin >> x;
        L ax = v[0], ay = v[1], bx = v[2], by = v[3], cx = v[4], cy = v[5], dx = v[6], dy = v[7];
        // solve a + s(b - a) = c + u(d - c) exactly with Cramer's rule
        L rx = bx - ax, ry = by - ay, qx = dx - cx, qy = dy - cy;
        L den = rx * qy - ry * qx, wx = cx - ax, wy = cy - ay;
        bool hit;
        if (den != 0) {
            L sn = wx * qy - wy * qx, un = wx * ry - wy * rx;   // s = sn / den, u = un / den
            if (den < 0) { den = -den; sn = -sn; un = -un; }
            hit = 0 <= sn && sn <= den && 0 <= un && un <= den;
        } else if (wx * ry - wy * rx != 0) {
            hit = false;                                      // parallel, different lines
        } else {                                              // one line: compare intervals
            bool useX = rx != 0;
            L p1 = useX ? ax : ay, p2 = useX ? bx : by, q1 = useX ? cx : cy, q2 = useX ? dx : dy;
            if (p1 > p2) swap(p1, p2);
            if (q1 > q2) swap(q1, q2);
            hit = max(p1, q1) <= min(p2, q2);
        }
        cout << (hit ? "YES" : "NO") << '\n';
    }
}
""",
    hints=[
        r"""Two segments cross at one interior point exactly when each segment's endpoints are on
opposite sides of the other segment's line. Four orientation tests.""",
        r"""The remaining cases all have an orientation equal to zero: some endpoint is on the other
segment's line. Then the segments meet only if that endpoint is also *between* the other
segment's endpoints (a bounding-box check is enough once you know it is on the line).""",
        r"""Do not multiply two cross products: each can be 4·10^18 and the product overflows. Compare
their signs.""",
    ],
    editorial=r"""
Let `o1 = cross(a, b, c)`, `o2 = cross(a, b, d)`, `o3 = cross(c, d, a)`, `o4 =
cross(c, d, b)`. If `o1`, `o2` have strictly opposite signs and `o3`, `o4` too, `c` and
`d` are on opposite sides of line `ab` and `a`, `b` on opposite sides of line `cd`: the
segments cross. Both conditions are needed; one alone allows the second segment to cross
the *line* of the first far from the segment itself.

Every other intersection has an endpoint lying on the other segment, which shows up as an
orientation of zero plus a bounding-box check. The trap is the collinear case: two
segments on one line with a gap between them have all four orientations zero, so "signs
opposite or zero" wrongly says YES. The bounding-box check is what says NO.

Overflow: each orientation is up to 4·10^18 in size; `o1 * o2` would be up to 1.6·10^37.
Reduce each to its sign first. O(1) per test.
""",
)

POLYGON_AREA = Problem(
    id="polygon_area",
    title="Plot Area",
    difficulty="easy",
    source="CSES 2191 - Polygon Area",
    complexity="O(n)",
    statement=r"""
The land registry stores each plot as a simple polygon: its corners in order around the
boundary. Some clerks went clockwise, some counterclockwise. Print twice the area of the
plot (twice the area of a polygon with integer corners is always an integer).
""",
    input=r"""
The first line has `n` (3 ≤ n ≤ 1000). Each of the next `n` lines has two integers `x y`
(−10^9 ≤ x, y ≤ 10^9): the corners in order. The polygon is simple: two edges meet only
when they are consecutive, and then only at their shared corner. Consecutive corners may
be collinear.
""",
    output=r"""
Print one integer: twice the area.
""",
    samples=[
        Test("6\n0 0\n0 3\n1 3\n1 1\n4 1\n4 0\n", "12\n",
             note="An L shape given clockwise: the signed sum is −12."),
        Test("4\n-1000000000 -1000000000\n1000000000 -1000000000\n1000000000 1000000000\n-1000000000 1000000000\n",
             "8000000000000000000\n",
             note="The largest possible answer: 8·10^18, just under the 9.22·10^18 a `long long` holds."),
    ],
    tests=[
        Test("3\n0 0\n1 0\n0 1\n"),
        Test("3\n5 5\n-3 5\n5 -1000000000\n"),
        Test("5\n0 0\n2 0\n4 0\n4 3\n0 3\n"),
        Test("4\n1000000000 1000000000\n-1000000000 1000000000\n-1000000000 -1000000000\n1000000000 -1000000000\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _area_input(rng, rng.randint(3, 12), 12, 12), 14),
        Gen("max n, huge coordinates", lambda rng: _area_input(rng, 1000, LIM, LIM), 3, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> x(n), y(n);
    for (int i = 0; i < n; i++) cin >> x[i] >> y[i];
    long long s = 0;                       // twice the signed area
    for (int i = 0; i < n; i++) {
        int j = (i + 1) % n;               // the last edge closes the polygon
        s += x[i] * y[j] - x[j] * y[i];    // cross(p_i, p_j): the doubled signed triangle (O, p_i, p_j)
    }
    cout << llabs(s) << '\n';              // clockwise input gives a negative sum
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Small boxes: Pick's theorem, A = I + B/2 - 1, so 2A = 2I + B - 2, classifying every
// lattice point. Huge boxes: the trapezoid rule, sum of (x_j - x_i)(y_i + y_j), in 128 bits.
int main() {
    int n;
    cin >> n;
    vector<long long> x(n), y(n);
    for (int i = 0; i < n; i++) cin >> x[i] >> y[i];
    long long lx = *min_element(x.begin(), x.end()), hx = *max_element(x.begin(), x.end());
    long long ly = *min_element(y.begin(), y.end()), hy = *max_element(y.begin(), y.end());
    if (hx - lx > 200 || hy - ly > 200) {
        __int128 s = 0;
        for (int i = 0; i < n; i++) {
            int j = (i + 1) % n;
            s += (__int128)(x[j] - x[i]) * (y[i] + y[j]);
        }
        if (s < 0) s = -s;
        cout << (long long)s << '\n';
        return 0;
    }
    long long I = 0, B = 0;
    for (long long px = lx; px <= hx; px++)
        for (long long py = ly; py <= hy; py++) {
            bool border = false;
            int crossings = 0;
            for (int i = 0; i < n; i++) {
                int j = (i + 1) % n;
                long long c = (x[j] - x[i]) * (py - y[i]) - (y[j] - y[i]) * (px - x[i]);
                if (c == 0 && min(x[i], x[j]) <= px && px <= max(x[i], x[j]) &&
                    min(y[i], y[j]) <= py && py <= max(y[i], y[j])) border = true;
                if ((y[i] <= py) != (y[j] <= py)) {       // ray to the right, exact compare
                    long long dx = x[j] - x[i], dy = y[j] - y[i];
                    long long lhs = (px - x[i]) * dy, rhs = (py - y[i]) * dx;
                    if (dy > 0 ? lhs < rhs : lhs > rhs) crossings++;
                }
            }
            if (border) B++;
            else if (crossings % 2) I++;
        }
    cout << 2 * I + B - 2 << '\n';
}
""",
    hints=[
        r"""Twice the signed area of the triangle `(O, p_i, p_(i+1))`, with `O` the origin, is
`x_i·y_(i+1) − x_(i+1)·y_i`. Add it up over all edges, including the edge from the last
corner back to the first.""",
        r"""Triangles that stick out of the polygon are added once and subtracted once. The total
is twice the area, with a sign that tells the orientation: print its absolute value.""",
    ],
    editorial=r"""
The shoelace formula: `2A = |Σ (x_i·y_(i+1) − x_(i+1)·y_i)|` over all edges, with index
`n` meaning 0. Each term is twice the signed area of the triangle formed by the origin and
one edge. For a point inside the polygon, the triangles covering it add up to +1 (for a
counterclockwise polygon); for a point outside, the covering triangles cancel in pairs. So
the sum counts exactly the polygon's area, whatever its shape and wherever the origin is.

The sum is negative for clockwise input, hence the absolute value. Twice the area of a
lattice polygon is an integer, which is why the problem asks for it: no fractions, no
floating point. The largest answer is the full box, (2·10^9)^2 · 2 = 8·10^18, which still
fits in a `long long`. O(n).
""",
)

POINT_IN_POLYGON = Problem(
    id="point_in_polygon",
    title="Inside the Fence",
    difficulty="medium",
    source="CSES 2192 - Point in Polygon",
    complexity="O(n·m)",
    statement=r"""
A fence is a simple polygon. For each of `m` points, decide whether it is strictly inside
the fence, strictly outside, or on the fence itself.
""",
    input=r"""
The first line has `n` and `m` (3 ≤ n ≤ 1000, 1 ≤ m ≤ 1000). The next `n` lines have the
polygon's corners `x y` in order (either orientation); the next `m` lines have the query
points `x y`. All coordinates are integers with absolute value at most 10^9. The polygon
is simple: two edges meet only when they are consecutive, and only at their shared
corner.
""",
    output=r"""
For each query print `INSIDE`, `OUTSIDE` or `BOUNDARY`.
""",
    samples=[
        Test("6 7\n0 0\n6 0\n6 2\n6 4\n3 2\n0 4\n1 1\n3 3\n-1 2\n1 2\n3 2\n6 1\n7 2\n",
             "INSIDE\nOUTSIDE\nOUTSIDE\nINSIDE\nBOUNDARY\nBOUNDARY\nOUTSIDE\n",
             note="Queries 3 and 4 send their ray to the right along y = 2, straight through the "
                  "corners (3, 2) and (6, 2). Counting every edge that touches the ray gets them wrong."),
    ],
    tests=[
        Test("3 4\n0 0\n4 2\n0 4\n-1 2\n1 2\n4 2\n2 1\n"),
        Test("4 5\n-1000000000 -1000000000\n1000000000 -1000000000\n1000000000 1000000000\n-1000000000 1000000000\n"
             "0 0\n1000000000 0\n-1000000000 -1000000000\n999999999 999999999\n1000000000 1000000001\n"),
        Test("8 6\n0 0\n2 0\n2 2\n4 2\n4 0\n6 0\n6 4\n0 4\n3 1\n1 2\n5 2\n3 2\n-5 2\n3 0\n"),
    ],
    gens=[
        Gen("small random", lambda rng: _pip_input(rng, rng.randint(3, 12), 30, 10, 10, 12), 14),
        Gen("max size", lambda rng: _pip_input(rng, 1000, 1000, LIM, LIM, LIM), 2, large=True),
    ],
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

struct P { long long x, y; };
long long cross(P a, P b, P c) { return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x); }

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<P> p(n);
    for (auto& v : p) cin >> v.x >> v.y;
    while (m--) {
        P q;
        cin >> q.x >> q.y;
        bool boundary = false, inside = false;
        for (int i = 0; i < n; i++) {
            P a = p[i], b = p[(i + 1) % n];
            if (cross(a, b, q) == 0 && min(a.x, b.x) <= q.x && q.x <= max(a.x, b.x) &&
                min(a.y, b.y) <= q.y && q.y <= max(a.y, b.y)) {
                boundary = true;                             // on this edge
                break;
            }
            if (a.y > b.y) swap(a, b);                        // a is the lower end
            // half-open: count the edge if a.y <= q.y < b.y (never a horizontal edge);
            // the edge crosses the ray to the right of q iff q is left of the upward edge a->b
            if (a.y <= q.y && q.y < b.y && cross(a, b, q) > 0) inside = !inside;
        }
        cout << (boundary ? "BOUNDARY" : inside ? "INSIDE" : "OUTSIDE") << '\n';
    }
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
// Winding number: add up the angle each edge subtends at the query point.
int main() {
    int n, m;
    cin >> n >> m;
    vector<long long> x(n), y(n);
    for (int i = 0; i < n; i++) cin >> x[i] >> y[i];
    while (m--) {
        long long qx, qy;
        cin >> qx >> qy;
        bool border = false;
        double total = 0;
        for (int i = 0; i < n; i++) {
            int j = (i + 1) % n;
            long long ax = x[i] - qx, ay = y[i] - qy, bx = x[j] - qx, by = y[j] - qy;
            long long cr = ax * by - ay * bx, dot = ax * bx + ay * by;
            if (cr == 0 && dot <= 0) border = true;       // q between the endpoints
            total += atan2((double)cr, (double)dot);
        }
        long long wind = llround(total / (2 * acos(-1.0)));
        cout << (border ? "BOUNDARY" : wind != 0 ? "INSIDE" : "OUTSIDE") << '\n';
    }
}
""",
    hints=[
        r"""First check every edge for the query point lying on it (cross product zero, inside the
bounding box). Only then decide inside or outside.""",
        r"""Shoot a ray from the point to the right and count the edges it crosses: odd means inside.
To survive rays through corners, count an edge only when `min(y) ≤ q.y < max(y)`.""",
        r"""For an edge with lower end `a` and upper end `b`, the crossing is to the right of `q`
exactly when `q` is to the left of `a → b`: `cross(a, b, q) > 0`. No division needed.""",
    ],
    editorial=r"""
Boundary first: `q` is on edge `ab` iff `cross(a, b, q) = 0` and `q` is in the edge's
bounding box.

Otherwise cast a horizontal ray from `q` to the right. Walking along it from `q` to
infinity, every edge crossed flips inside/outside, and infinity is outside: an odd number
of crossings means inside. The only difficulty is a ray passing exactly through a corner.
The **half-open rule** counts an edge only when `min(a.y, b.y) ≤ q.y < max(a.y, b.y)`:
a corner the boundary passes *through* is the lower end of one of its edges and the upper
end of the other, so it is counted once; a corner where the boundary turns back (both
edges above, or both below) is counted twice or not at all, which leaves the parity
unchanged, as it should. Horizontal edges are never counted.

Whether the crossing is to the right of `q` is again an orientation: with `a` the lower
end, it is `cross(a, b, q) > 0`. O(n) per query, 10^6 cross products in all.
""",
)

CONVEX_HULL = Problem(
    id="convex_hull",
    title="Fence Around the Herd",
    difficulty="hard",
    source="CSES 2195 - Convex Hull (variant: corners only, in order)",
    complexity="O(n log n)",
    statement=r"""
Sheep stand at `n` points of a field, several possibly at the same point. The shortest
fence around all of them is the convex hull. Print its corner posts.

A point in the middle of a straight stretch of fence is not a corner. If all sheep stand
at one point, the hull is that point; if they all stand on one line, the hull is the
segment between the two extreme points (two corners).
""",
    input=r"""
The first line has `n` (1 ≤ n ≤ 2·10^5). Each of the next `n` lines has two integers
`x y` (−10^9 ≤ x, y ≤ 10^9).
""",
    output=r"""
First print `k`, the number of corners. Then print the `k` corners, one `x y` per line,
in counterclockwise order around the hull, starting from any corner.
""",
    samples=[
        Test("7\n0 0\n4 0\n4 4\n0 4\n2 2\n2 0\n4 4\n", "4\n0 0\n4 0\n4 4\n0 4\n",
             note="(2, 0) is on the fence but is not a corner; (4, 4) appears twice in the input. "
                  "Starting from another corner, e.g. `4 4` `0 4` `0 0` `4 0`, is also accepted."),
        Test("3\n1 1\n3 3\n2 2\n", "2\n1 1\n3 3\n",
             note="All on one line: two corners, in either order."),
    ],
    tests=[
        Test("1\n-1000000000 1000000000\n"),
        Test("4\n5 5\n5 5\n5 5\n5 5\n"),
        Test("2\n3 -7\n-2 9\n"),
        Test("5\n0 0\n0 4\n0 1\n0 3\n0 4\n"),
        Test("4\n-1000000000 -1000000000\n1000000000 -1000000000\n1000000000 1000000000\n-1000000000 1000000000\n"),
        Test("6\n0 0\n2 -1\n4 0\n4 0\n2 1\n2 0\n"),
    ],
    gens=[
        Gen("small with repeats", lambda rng: _hull_small(rng, rng.randint(1, 12), rng.choice([1, 2, 3, 6])), 15),
        Gen("small on one line", lambda rng: _hull_line(rng, rng.randint(1, 8), 10, 2), 5),
        Gen("medium", lambda rng: _hull_small(rng, 150, 1000), 3),
        Gen("max n, random", lambda rng: _hull_random(rng, 200000, LIM), 1, large=True),
        Gen("max n, rectangle border", lambda rng: _hull_rectangle(rng, 200000, LIM), 1, large=True),
        Gen("max n, one line", lambda rng: _hull_line(rng, 200000, LIM, 3000), 1, large=True),
        Gen("max n, every point a corner", lambda rng: _hull_convex(rng, 200000), 2, large=True),
    ],
    checker=_hull_check,
    solution=r"""
#include <bits/stdc++.h>
using namespace std;

typedef pair<long long, long long> P;              // (x, y): sorts by x, then y
long long cross(P a, P b, P c) {
    return (b.first - a.first) * (c.second - a.second) - (b.second - a.second) * (c.first - a.first);
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<P> p(n);
    for (auto& [x, y] : p) cin >> x >> y;
    sort(p.begin(), p.end());
    p.erase(unique(p.begin(), p.end()), p.end());   // repeats would make zero-length edges
    n = p.size();
    vector<P> h;
    if (n == 1) h = p;
    else {
        vector<P> st(2 * n);
        int k = 0;
        for (int i = 0; i < n; i++) {                // lower hull, left to right
            while (k >= 2 && cross(st[k - 2], st[k - 1], p[i]) <= 0) k--;   // not a left turn
            st[k++] = p[i];
        }
        for (int i = n - 2, low = k + 1; i >= 0; i--) {   // upper hull, right to left
            while (k >= low && cross(st[k - 2], st[k - 1], p[i]) <= 0) k--;
            st[k++] = p[i];
        }
        h.assign(st.begin(), st.begin() + k - 1);    // the last point is p[0] again
    }
    cout << h.size() << '\n';
    for (auto& [x, y] : h) cout << x << ' ' << y << '\n';
    return 0;
}
""",
    brute=r"""
#include <bits/stdc++.h>
using namespace std;
typedef pair<long long, long long> P;
long long cross(P a, P b, P c) { return (b.first - a.first) * (c.second - a.second) - (b.second - a.second) * (c.first - a.first); }
// a -> b is a counterclockwise hull edge iff every point is strictly left of it or on the
// closed segment [a, b]. Find all such edges (O(n^3)), then walk them.
int main() {
    int n;
    cin >> n;
    vector<P> p(n);
    for (auto& [x, y] : p) cin >> x >> y;
    sort(p.begin(), p.end());
    p.erase(unique(p.begin(), p.end()), p.end());
    n = p.size();
    if (n == 1) { cout << "1\n" << p[0].first << ' ' << p[0].second << '\n'; return 0; }
    map<P, P> nxt;
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            if (i == j) continue;
            bool ok = true;
            for (int k = 0; k < n && ok; k++) {
                long long c = cross(p[i], p[j], p[k]);
                if (c < 0) ok = false;
                else if (c == 0 && !(min(p[i], p[j]) <= p[k] && p[k] <= max(p[i], p[j]))) ok = false;
            }
            if (ok) nxt[p[i]] = p[j];
        }
    vector<P> h;
    P start = nxt.begin()->first, cur = start;
    do { h.push_back(cur); cur = nxt[cur]; } while (cur != start);
    cout << h.size() << '\n';
    for (auto& [x, y] : h) cout << x << ' ' << y << '\n';
}
""",
    naive=r"""
#include <bits/stdc++.h>
using namespace std;
typedef pair<long long, long long> P;
long long cross(P a, P b, P c) { return (b.first - a.first) * (c.second - a.second) - (b.second - a.second) * (c.first - a.first); }
long long d2(P a, P b) { long long dx = a.first - b.first, dy = a.second - b.second; return dx * dx + dy * dy; }
// Gift wrapping (Jarvis march): from each corner, scan every point for the next corner.
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<P> p(n);
    for (auto& [x, y] : p) cin >> x >> y;
    sort(p.begin(), p.end());
    p.erase(unique(p.begin(), p.end()), p.end());
    n = p.size();
    vector<P> h;
    int cur = 0;
    do {
        h.push_back(p[cur]);
        int cand = (cur + 1) % n;
        for (int i = 0; i < n; i++) {
            if (i == cur) continue;
            long long c = cross(p[cur], p[cand], p[i]);
            if (c < 0 || (c == 0 && d2(p[cur], p[i]) > d2(p[cur], p[cand]))) cand = i;
        }
        cur = cand;
    } while (cur != 0 && n > 1);
    cout << h.size() << '\n';
    for (auto& [x, y] : h) cout << x << ' ' << y << '\n';
}
""",
    hints=[
        r"""Sort the points by x (then y). The lower hull, read left to right, only ever turns left.
Sweep the sorted points and keep the lower hull of everything seen so far on a stack.""",
        r"""Before pushing a point `p`, pop while the last two stack points `a, b` and `p` do not make
a left turn (`cross(a, b, p) <= 0`): such a `b` is on or above the segment `a–p`, so it is
not a corner. Do the same right to left for the upper hull, and join the two.""",
        r"""Remove repeated points first, handle `n = 1`, and use `<= 0` (not `< 0`) so collinear
points are dropped. All coordinates in `long long`.""",
    ],
    editorial=r"""
**Monotone chain** (Andrew's algorithm). Sort by `(x, y)` and remove repeats. Sweep left
to right keeping a stack; before pushing `p`, pop the top `b` (with `a` below it) while
`cross(a, b, p) ≤ 0`. A popped `b` lies on or above the segment from `a` to `p`, two
points of the set, so it cannot be a corner of the lower hull, whatever comes later. The
points that survive turn left at every step: the lower hull. Sweep right to left for the
upper hull and concatenate, dropping the duplicated endpoints. The result is
counterclockwise, starting at the leftmost-lowest point.

Every point is pushed once per sweep and popped at most once, so the sweeps are O(n) and
the sort dominates: O(n log n). Gift wrapping costs O(n·h) for `h` corners, and with every
point a corner (a hidden test has 2·10^5 of them) that is 4·10^10 steps.

Degenerate inputs: repeated points (remove them, or they create zero-length edges), all
points equal (one corner), all points on a line (the sweeps return the two endpoints),
points in the middle of an edge (`≤ 0` pops them; `< 0` would keep them, which is what the
CSES version of this problem wants). Cross products stay within 4·10^18: `long long`.
""",
)


# ----------------------------------------------------------------------- lesson
LESSON = Lesson(
    id="algo21",
    title="computational geometry",
    track="algo",
    order=21,
    summary="Points as integer vectors: the cross product as the one orientation test, "
            "segment intersection and its collinear traps, the shoelace formula, point in "
            "polygon, and the monotone chain convex hull.",
    prereqs=["cpp02", "algo02"],
    tags=["geometry", "cross product", "orientation", "segment intersection", "shoelace",
          "point in polygon", "convex hull", "monotone chain", "overflow"],
    parts=[
        Part("Left, right, or on the line", [
            Say(r"""
Almost every contest geometry problem reduces to one question asked many times. Here it
is on its own:

A drone flies from `p1` through `p2` and keeps going. Is the landmark `p3` on its left,
on its right, or exactly on its path? There are `t ≤ 10^5` such questions, and every
coordinate is an integer with absolute value up to 10^9.

The school-algebra answer: compute the slope `m = (y2 − y1) / (x2 − x1)`, then compare
`y3` with the line's height at `x3`, which is `y1 + m·(x3 − x1)`.
"""),
            MCQ(r"""
Which input breaks the slope method outright, before any question of precision?
""", [
                Opt("A vertical path: `x1 == x2`.", correct=True,
                    why="The slope is a division by zero. You could special-case it, but that is "
                        "the first of several special cases, and each one is a chance for a WA."),
                Opt("Negative coordinates.",
                    why="Negative numbers are fine in the formula: subtraction and division work "
                        "the same way with them."),
                Opt("`p3` equal to `p1`.",
                    why="Then `y3` equals the line's height at `x3 = x1`: the method correctly says "
                        "'on the line'."),
                Opt("Coordinates as large as 10^9.",
                    why="Large values hurt precision (we will see how), but they do not break the "
                        "method outright the way one particular input does."),
            ], explain=r"""
Two quieter problems remain even without vertical lines. "Above the line" means "left of
the path" only when the drone flies in the +x direction; flying right to left, above is
*right*, so the answer flips with the sign of `x2 − x1`. And `m` is a fraction, which
invites `double`. We want a test with no division and no case analysis.
"""),
            Reflect(r"""
Start from the slope comparison `y3 − y1 > m·(x3 − x1)` with `m = dy / dx`, where
`dx = x2 − x1`, `dy = y2 − y1`. Get rid of the division. What integer expression is left,
and why does its sign automatically take care of the flying-backwards problem?
""", answer=r"""
Multiply both sides by `dx`: `dx·(y3 − y1)` versus `dy·(x3 − x1)`. When `dx < 0` the
inequality would flip, which is exactly the "above means right when flying backwards"
correction. So the whole test is the sign of `dx·(y3 − y1) − dy·(x3 − x1)`, with no case
split: positive means left, negative right, zero on the line. It works for `dx = 0` too.
This is the **cross product** of `u = p2 − p1` and `v = p3 − p1`.
"""),
            Say(r"""
For two vectors `u` and `v`, the **cross product** is the integer

```
u × v = u.x · v.y − u.y · v.x
```

and for three points we write `cross(a, b, c) = (b − a) × (c − a)`. Its sign is the
**orientation** of `a, b, c`: positive when `a → b → c` turns counterclockwise (`c` is
left of the directed line `a → b`), negative when it turns clockwise, zero when the three
points are collinear.
"""),
            Short(r"""
Check the claim on the easiest case. `u = (1, 0)` points east. For `v = (3, 2)`, what is
`u × v`?
""", accept=["2"], placeholder="a number",
                explain=r"""
`1·2 − 0·3 = 2`. For an eastward `u`, `u × v` is just `v.y`: positive exactly when `v`
points above the path, which is to the left when you face east. The cross product is the
signed area of the parallelogram spanned by `u` and `v`, and rotating the whole picture
changes neither the area nor its sign, so what holds facing east holds facing anywhere.
"""),
            Short(r"""
Now by hand: `p1 = (0, 0)`, `p2 = (4, 2)`. Compute `cross(p1, p2, p3)` for the three
landmarks `p3 = (1, 3)`, `(3, −1)` and `(−2, −1)`. Write the three values separated by
spaces.
""", accept=["10 -10 0", "10, -10, 0", "10,-10,0"], placeholder="three numbers",
                hint="`u = (4, 2)` every time; `v = p3 − p1 = p3`. Then `4·v.y − 2·v.x`.",
                explain=r"""
`4·3 − 2·1 = 10` (LEFT), `4·(−1) − 2·3 = −10` (RIGHT), `4·(−1) − 2·(−2) = 0` (TOUCH). The
last point is on the line *behind* `p1`: the orientation test is about the infinite line,
not the segment. Remember that when we get to segments.
"""),
        ]),
        Part("The types decide the verdict", [
            Numeric(r"""
Coordinates are within ±10^9. How large can a single product like `(x2 − x1)·(y3 − y1)`
get?
""", answer=4e18, rel=0.1,
                hint="How large can a difference of two coordinates be?",
                explain=r"""
A difference is at most `10^9 − (−10^9) = 2·10^9`, and the product of two of them at most
4·10^18. The cross product subtracts two such products; its true value is twice the area
of a triangle inside the 2·10^9 × 2·10^9 box, so it is also at most 4·10^18 in size.
"""),
            MCQ(r"""
Which type should hold the cross product?
""", [
                Opt("`int`, since the inputs fit in `int`.",
                    why="The inputs fit (10^9 < 2.1·10^9), but the products are 4·10^18. Choose the "
                        "type from the largest value you *compute*, not the largest you read."),
                Opt("`long long`: it holds up to about 9.22·10^18.", correct=True,
                    why="Yes, with room to spare here. Double the coordinate range, to ±2·10^9, and "
                        "products reach 1.6·10^19: then you need `__int128` (about 1.7·10^38)."),
                Opt("`double`: it covers far larger values than `long long`.",
                    why="Its range is huge, but it keeps only 53 bits of mantissa. Integers above "
                        "2^53 ≈ 9·10^15 are rounded, and the orientation of nearly-collinear points "
                        "hangs on the last few units of the products."),
                Opt("`unsigned long long`, for the extra bit.",
                    why="The cross product is negative half the time; its sign is the whole answer. "
                        "Unsigned arithmetic would wrap negative values into huge positive ones."),
            ]),
            MCQ(r"""
Take `p1 = (0, 0)`, `p2 = (781638469, 760627983)`, `p3 = (897313041, 873193216)`. The
exact cross product is `682521408495426304 − 682521408495426303 = 1`: LEFT. What does the
same formula print if all six coordinates are `double`?
""", [
                Opt("LEFT: `double` has 15-16 significant digits, plenty for this.",
                    why="The products have 18 digits, and 18 do not fit in 15-16. Near 6.8·10^17 "
                        "consecutive `double` values are 128 apart, so the last two digits are lost."),
                Opt("TOUCH: both products round to the same `double`, so the difference is 0.",
                    correct=True,
                    why="Right. The second product ends one short of a multiple of 128 and rounds up to "
                        "exactly the first. This input is the second sample of the problem."),
                Opt("RIGHT: the rounding error is always negative.",
                    why="Rounding goes to the nearest representable value, up or down. Here both round "
                        "to the same value, giving exactly 0."),
            ], explain=r"""
The rule for this lesson: when the input is integers, keep every predicate (orientation,
on-segment, inside) in exact integer arithmetic. Floating point is for the problems that
genuinely need it (circles, angles, intersection *points*), and there you compare with an
epsilon and know you are taking a risk.
"""),
            Try("point_location", note="One cross product per test, in `long long`. The second sample "
                "is the `double` trap."),
        ]),
        Part("Do two segments meet?", [
            Say(r"""
Next problem: `t ≤ 10^5` pairs of segments `ab` and `cd`, coordinates up to 10^9 again.
Print YES if they share at least one point.

The algebra approach intersects the two *lines* (solve a 2×2 system), then checks that
the intersection point lies on both segments. It needs a division, it has no answer for
parallel lines, and for two overlapping segments on one line the "intersection point" is
a whole segment. We will build it from orientations instead.
"""),
            Reflect(r"""
Using only orientation tests, when do `ab` and `cd` cross at a single point that is
interior to both? State a condition in terms of which side of which line each endpoint
is on.
""", answer=r"""
`c` and `d` must be strictly on opposite sides of the line through `a` and `b`
(`cross(a, b, c)` and `cross(a, b, d)` have opposite signs), **and** `a` and `b` must be
strictly on opposite sides of the line through `c` and `d`. The first condition says
segment `cd` crosses the *line* `ab`; the second says that crossing happens within
segment `ab`.
"""),
            MCQ(r"""
Why is the first condition alone not enough? Pick the pair that satisfies "c and d on
opposite sides of line ab" but does not intersect.
""", [
                Opt("`ab` = (0,0)–(1,0), `cd` = (5,−1)–(5,1)", correct=True,
                    why="Yes: `cd` crosses the x-axis at (5, 0), far to the right of the segment `ab`. "
                        "The second condition catches it: `a` and `b` are both left of line `cd`."),
                Opt("`ab` = (0,0)–(4,4), `cd` = (0,4)–(4,0)",
                    why="These do cross, at (2, 2). Both conditions hold."),
                Opt("`ab` = (0,0)–(4,0), `cd` = (0,1)–(4,1)",
                    why="Here `c` and `d` are on the *same* side of line `ab` (both above), so the first "
                        "condition already fails."),
            ]),
            Short(r"""
Now the cases where a segment *touches*. `a = (0, 0)`, `b = (4, 0)`, `c = (2, 0)`,
`d = (2, 3)`. Compute `o1 = cross(a, b, c)` and `o2 = cross(a, b, d)`, separated by a
space.
""", accept=["0 12", "0, 12", "0,12"], placeholder="two numbers",
                explain=r"""
`o1 = 4·0 − 0·2 = 0` and `o2 = 4·3 − 0·2 = 12`. The signs are not opposite, yet the
segments meet: `c` sits on `ab` (a T junction). Every touching case looks like this: some
orientation is zero, meaning an endpoint lies on the other segment's *line*. Then you
check whether it lies between that segment's endpoints, which, once you know it is on the
line, is just a bounding-box check.
"""),
            MCQ(r"""
A tempting shortcut: answer YES when `o1·o2 ≤ 0` and `o3·o4 ≤ 0` ("opposite sides, or
touching"). Which pair does it get wrong?
""", [
                Opt("A proper X: (0,0)–(4,4) and (0,4)–(4,0).",
                    why="All four orientations are nonzero with opposite signs: YES, correctly."),
                Opt("Two segments on one line with a gap: (0,0)–(1,1) and (2,2)–(3,3).", correct=True,
                    why="Right. All four orientations are 0, so every product is 0 and the shortcut says "
                        "YES. They are on one line but do not touch. Only the bounding-box check can "
                        "tell overlapping collinear segments from separated ones."),
                Opt("Parallel segments on different lines: (0,0)–(4,0) and (0,1)–(4,1).",
                    why="`o1` and `o2` are both positive (same side), so `o1·o2 > 0`: NO, correctly."),
                Opt("A T junction: (0,0)–(4,0) and (2,0)–(2,3).",
                    why="`o1 = 0`, so `o1·o2 = 0 ≤ 0`, and `o3·o4 = 6·(−6) < 0`: YES, correctly."),
            ], explain=r"""
The collinear case is where most wrong answers on this problem come from, and samples
rarely contain it. The full test: a proper crossing (strictly opposite signs, twice), or
any zero orientation whose point is inside the other segment's bounding box.
"""),
            MCQ(r"""
The code computes `o1`, `o2` as `long long` and then tests `if (o1 * o2 < 0)`. What is
wrong?
""", [
                Opt("Nothing: `long long` holds each orientation.",
                    why="Each orientation fits (up to 4·10^18), but their product is up to 1.6·10^37. "
                        "It overflows, and the sign of the garbage is anybody's guess."),
                Opt("The product overflows; compare signs instead.", correct=True,
                    why="Yes. Reduce each orientation to −1, 0 or 1 first (`(v > 0) - (v < 0)`), then "
                        "multiplying is safe. On this lesson's large tests the product version gets "
                        "about 30% of the answers wrong."),
                Opt("`<` should be `<=`.",
                    why="`< 0` is right for the proper-crossing case; the touching cases are handled "
                        "separately. The real bug is the size of the product."),
            ]),
            Try("segment_intersection", note="Signs, not products; and the collinear-but-apart case."),
        ]),
        Part("Area from coordinates", [
            Say(r"""
A polygon is given by its `n ≤ 1000` corners in order, coordinates up to 10^9. Print
twice its area, which is always an integer for integer corners: that is why problems ask
for it.

Start with a triangle. `cross(a, b, c)` is the signed area of the parallelogram on
`b − a` and `c − a`, and the triangle is half of it.
"""),
            Numeric(r"""
Twice the area of the triangle `(0, 0)`, `(4, 1)`, `(1, 3)`?
""", answer=11,
                explain=r"""
`(4, 1) × (1, 3) = 4·3 − 1·1 = 11`. The area is 5.5, and twice it is the integer 11. That
is the pattern for every lattice polygon: twice the area is a sum of cross products.
"""),
            MCQ(r"""
For a convex polygon, the fan of triangles `(p0, p_i, p_(i+1))` covers it exactly. For a
non-convex polygon, some fan triangles stick out of the polygon. What makes the formula
still right if you *add the signed cross products* instead of their absolute values?
""", [
                Opt("Nothing: for non-convex polygons you must triangulate properly first.",
                    why="Proper triangulation works but is hard to code. Signs make it unnecessary, "
                        "as the other answer explains."),
                Opt("The triangles that stick out are traversed clockwise, so they count negatively "
                    "and cancel the overcounted parts.", correct=True,
                    why="Yes. Every point outside the polygon is covered by as many positive as "
                        "negative triangles; every point inside by one more positive. The fan center "
                        "does not even need to be a vertex."),
                Opt("The formula is only right up to rounding, which is fine for large areas.",
                    why="Everything here is an integer; the formula is exact."),
            ]),
            Say(r"""
Put the fan center at the origin `O`. The triangle `(O, p_i, p_(i+1))` has doubled signed
area `p_i × p_(i+1) = x_i·y_(i+1) − x_(i+1)·y_i`, which gives the **shoelace formula**:

```
2A = | sum over i of (x_i · y_(i+1) − x_(i+1) · y_i) |      (index n means 0)
```

The sum is positive for a counterclockwise polygon and negative for a clockwise one.
"""),
            Numeric(r"""
The L shape `(0,0), (4,0), (4,1), (1,1), (1,3), (0,3)` (counterclockwise). Compute the
shoelace sum by hand, term by term.
""", answer=12,
                hint="The six terms are `x_i·y_(i+1) − x_(i+1)·y_i` for consecutive pairs, including (0,3) back to (0,0).",
                explain=r"""
The terms are `0, 4, 3, 2, 3, 0`, total 12. Check: the L is a 4×1 bar plus a 1×2 column,
area 6, twice that 12. Given clockwise, the same corners give −12, which is why the
program prints the absolute value.
"""),
            Numeric(r"""
What is the largest possible answer with coordinates in ±10^9?
""", answer=8e18, rel=0.05,
                explain=r"""
The whole box: area (2·10^9)^2 = 4·10^18, doubled 8·10^18. A `long long` ends at about
9.22·10^18, so it fits, but only just. Each term `x_i·y_(i+1)` is at most 10^18, so the
terms are safe too. The second sample is exactly this square.
"""),
            Try("polygon_area"),
        ]),
        Part("Inside, outside, or on the fence", [
            Say(r"""
Now `m ≤ 1000` query points against a simple polygon of `n ≤ 1000` corners: is each
point inside, outside, or on the boundary?

Boundary first: `q` is on edge `ab` exactly when `cross(a, b, q) = 0` and `q` is inside
the edge's bounding box, the test from the segment problem.

For inside versus outside, the classic method is **ray casting**: shoot a ray from `q`
to the right and count how many edges it crosses.
"""),
            MCQ(r"""
Why does an odd number of crossings mean "inside"?
""", [
                Opt("Far along the ray you are outside, and each crossing flips inside/outside.",
                    correct=True,
                    why="Yes. Walk back from infinity (outside) to `q`: every edge crossed toggles your "
                        "state, so `q` is inside exactly when the count is odd."),
                Opt("Because a simple polygon has an even number of edges.",
                    why="A triangle has three. The parity argument is about crossings along the ray, "
                        "not about the polygon's edge count."),
                Opt("Because the ray crosses each edge exactly once.",
                    why="Most edges are not crossed at all; the count is only of those the ray meets."),
            ]),
            Say(r"""
The trouble is rays that pass exactly through a corner. Take the fence
`(0,0), (6,0), (6,2), (6,4), (3,2), (0,4)` and the query `q = (−1, 2)`, which is outside.
Its ray runs along y = 2 through the corner `(3, 2)`, where both edges go *up* (the
boundary touches the ray and turns back), and through `(6, 2)`, where the boundary passes
straight through the ray.
"""),
            MCQ(r"""
The rule that fixes this: count an edge only when `min(a.y, b.y) ≤ q.y < max(a.y, b.y)`,
lower end included, upper end excluded. How many times does it count the edges at each of
the corners `(3, 2)` and `(6, 2)`?
""", [
                Opt("`(3, 2)`: 2 times; `(6, 2)`: once.", correct=True,
                    why="Right. (3, 2) is the lower end of both its edges, so both count: 2, even, the "
                        "ray only grazes. (6, 2) is the upper end of the edge below it (not counted) and "
                        "the lower end of the edge above it (counted): 1, a real crossing."),
                Opt("Once each.",
                    why="Then (3, 2) would flip the state although the boundary does not cross the ray "
                        "there. Check which end of each edge (3, 2) is."),
                Opt("2 times each.",
                    why="That is what counting every edge that touches the ray does (the closed "
                        "interval), and it is the bug: (6, 2) is one crossing, not two."),
            ], explain=r"""
With the left edge and the edge from (6, 2) up, `q = (−1, 2)` gets 1 + 2 + 1 = 4 crossings:
even, OUTSIDE. Counting both edges at every touched corner gives 5 and says INSIDE. Note
that horizontal edges never satisfy `min ≤ q.y < max`, so they are skipped automatically.
"""),
            MCQ(r"""
For an edge with lower end `a` and upper end `b` that passes the half-open test, how do
you decide, without division, whether it crosses the ray to the *right* of `q`?
""", [
                Opt("`cross(a, b, q) > 0`: `q` is left of the upward edge.", correct=True,
                    why="Yes. On the row `y = q.y`, the points left of an upward edge are exactly those "
                        "left of where the edge crosses the row. So `q` left of the edge means the "
                        "crossing is to the right of `q`. (Zero cannot happen here: `q` would be on the "
                        "edge, already reported as BOUNDARY.)"),
                Opt("`a.x > q.x`.",
                    why="A slanted edge can start left of `q` and still cross the ray to its right. You "
                        "need the edge's x at height `q.y`, which is an orientation question."),
                Opt("Compute the x of the crossing as a `double` and compare.",
                    why="It works on easy data and fails on the near-degenerate cases where precision "
                        "matters, which is where the tests are. The orientation test is exact."),
            ]),
            Try("point_in_polygon", note="Checking every edge for every query is `n·m = 10^6` cross "
                "products: the plain loop is the intended solution, and the difficulty is all in the "
                "degenerate cases. Boundary first, then the half-open ray test; the sample sends rays "
                "through corners."),
        ]),
        Part("Wrapping the points: convex hull", [
            Say(r"""
Last problem: `n ≤ 2·10^5` points, possibly repeated, coordinates up to 10^9. Print the
corners of the **convex hull**, the smallest convex polygon containing them all,
counterclockwise. Points in the middle of a hull edge are not corners.

A direct characterisation: `p → q` is a counterclockwise hull edge when no point is to
its right. The brute force tries every ordered pair and checks every point.
"""),
            Numeric(r"""
How many orientation tests is that for `n = 2·10^5`?
""", answer=8e15, rel=0.5, unit="tests",
                explain=r"""
`n^2` pairs times `n` points: `(2·10^5)^3 = 8·10^15`. Hopeless.
"""),
            MCQ(r"""
**Gift wrapping** is smarter: start at the leftmost point, and from each corner scan all
`n` points for the next corner (the one with no point to its right). That costs `n` per
corner, so `n·h` for `h` corners. Is it fast enough?
""", [
                Opt("Yes: hulls of random points have few corners, so `h` is small.",
                    why="For random points `h` is small, typically dozens, and gift wrapping is fast. "
                        "But the tests are not random. Points on a convex curve are all corners."),
                Opt("No: if most points are corners, `n·h` is about 4·10^10.", correct=True,
                    why="Right. Even with integer coordinates up to 10^9 you can place 2·10^5 points in "
                        "convex position (one hidden test does), and gift wrapping then takes tens of "
                        "seconds."),
                Opt("Yes, because `h ≤ 4` for integer coordinates.",
                    why="Take the points `(x, x^2)` for x = 0..31622: all within 10^9, all corners. "
                        "Cleverer placements fit even more."),
            ]),
            Reflect(r"""
Gift wrapping rescans every point for every corner. If you sort the points by x once,
what do you know about the **lower** part of the hull as you sweep from left to right?
Think about the direction it turns.
""", answer=r"""
Read left to right, the lower hull only ever turns left (counterclockwise). So you can
sweep the sorted points and keep the lower hull of the points seen so far on a stack.
When a new point arrives, any stack point that would make a non-left turn with it cannot
be on the lower hull any more: pop it, and repeat. Sorting once replaces all the
rescanning.
"""),
            Say(r"""
That is the **monotone chain** algorithm:

```cpp
sort(p.begin(), p.end());                   // by x, then y
for (int i = 0; i < n; i++) {               // lower hull
    while (k >= 2 && cross(st[k-2], st[k-1], p[i]) <= 0) k--;
    st[k++] = p[i];
}
```

Then the same sweep from right to left builds the upper hull, and the two chains joined
(each missing its last point, which starts the other) are the hull, counterclockwise.
"""),
            MCQ(r"""
The stack ends `… a, b` and the new point `p` has `cross(a, b, p) ≤ 0`. Why is it safe to
throw `b` away forever, even though more points are still coming?
""", [
                Opt("`b` is on or above the segment from `a` to `p`; both are points of the set, so "
                    "`b` cannot be a corner of the lower hull.", correct=True,
                    why="Yes. A lower-hull corner lies strictly below every segment joining a point on its "
                        "left to a point on its right. `a` and `p` are such points no matter what comes "
                        "later, so `b` is out for good."),
                Opt("Because `p` has a larger x than `b`, and the hull only keeps the rightmost points.",
                    why="The hull keeps points at every x. `b` goes because of where it is relative to "
                        "the segment `a–p`, not because it is left of `p`."),
                Opt("It is not safe in general; it only works because the points are random.",
                    why="The argument above does not depend on the data at all, which is why the "
                        "algorithm is exact on every input, including adversarial ones."),
            ]),
            Short(r"""
Run the lower sweep by hand on `(0,3), (1,1), (2,2), (3,0), (4,4)` (already sorted).
Exactly one point is popped during the whole sweep. Which one?
""", accept=["(2,2)", "2 2", "2,2", "(2, 2)"], placeholder="a point",
                hint="Push (0,3) and (1,1). At (2,2) compute `cross((0,3), (1,1), (2,2))`; then continue.",
                explain=r"""
`(2,2)`. At (2,2): `cross((0,3),(1,1),(2,2)) = 1·(−1) − (−2)·2 = 3 > 0`, push. At (3,0):
`cross((1,1),(2,2),(3,0)) = 1·(−1) − 1·2 = −3`, pop (2,2); then
`cross((0,3),(1,1),(3,0)) = 1·(−3) − (−2)·3 = 3 > 0`, push. At (4,4):
`cross((1,1),(3,0),(4,4)) = 2·3 − (−1)·3 = 9 > 0`, push. Lower hull:
(0,3), (1,1), (3,0), (4,4).
"""),
            MCQ(r"""
After sorting, what does one sweep cost in total, given that a single step can pop many
points?
""", [
                Opt("O(n^2): a step can pop up to n points.",
                    why="One step can, but a point is popped at most once over the whole sweep: once "
                        "gone, it never returns. The pops are paid for by the pushes."),
                Opt("O(n): each point is pushed once and popped at most once.", correct=True,
                    why="Right: amortised O(1) per point, the same argument as the monotonic stack. "
                        "The O(n log n) sort dominates."),
                Opt("O(n log n): each pop is a binary search.",
                    why="There is no search; the stack is only ever touched at its top."),
            ]),
            MCQ(r"""
Which detail makes the code print **only corners** (no points in the middle of an edge)?
""", [
                Opt("Popping on `<= 0`, so collinear middle points are removed.", correct=True,
                    why="Yes. With `< 0` a point exactly on the segment `a–p` would stay. Some problems "
                        "want that (CSES 2195 asks for every boundary point); this one does not."),
                Opt("Sorting by x and then by y.",
                    why="The tie-break by y is needed so that points with equal x are processed in a "
                        "consistent order, but it does not decide what happens to collinear points."),
                Opt("Removing repeated points first.",
                    why="That prevents zero-length edges and a point printed twice. It is also required, "
                        "but middle-of-edge points are decided by the comparison."),
            ], explain=r"""
The degenerate inputs, all in the hidden tests: every point the same (`n = 1` after
removing repeats: print it), all points on one line (the two sweeps return the two
endpoints), repeated points, and many points along the edges of a rectangle.
"""),
            Try("convex_hull", note="Monotone chain. Any starting corner is accepted, but the order must "
                "be counterclockwise."),
        ]),
        Part("Variants and limits", [
            MCQ(r"""
A problem asks for **every** input point on the hull boundary, including those in the
middle of an edge (CSES 2195). Changing `<= 0` to `< 0` keeps them. What else breaks?
""", [
                Opt("If all points are collinear, both sweeps keep every point, so the middle points "
                    "are printed twice.", correct=True,
                    why="Yes. With `< 0` nothing collinear is ever popped, so the lower and the upper "
                        "sweep both return the whole line. Handle the all-collinear case separately, or "
                        "remove duplicates from the result."),
                Opt("Nothing else.",
                    why="Try three points on a line: the lower sweep keeps all three, the upper sweep "
                        "keeps all three in reverse, and the middle one appears twice."),
                Opt("The algorithm becomes O(n^2).",
                    why="Each point is still pushed and popped at most once per sweep."),
            ]),
            MCQ(r"""
The same problems with coordinates up to 10^18. What changes?
""", [
                Opt("Nothing, since `long long` holds 10^18.",
                    why="The coordinates fit, but a cross product multiplies two differences of up to "
                        "2·10^18, giving about 4·10^36."),
                Opt("Compute cross products in `__int128` (up to about 1.7·10^38).", correct=True,
                    why="Yes: `(__int128)(b.x - a.x) * (c.y - a.y) - ...`. The differences still fit in "
                        "`long long`; the products do not."),
                Opt("Switch to `long double`.",
                    why="On x86 judges `long double` has a 64-bit mantissa, still far short of the 122 "
                        "bits the products need. It rounds exactly where orientation matters."),
            ]),
            Say(r"""
One more tool that often pairs with the shoelace formula. **Pick's theorem**: for a
polygon whose corners are lattice points,

```
A = I + B/2 − 1
```

where `I` counts lattice points strictly inside and `B` lattice points on the boundary.
An edge from `(x1, y1)` to `(x2, y2)` contains `gcd(|x2 − x1|, |y2 − y1|)` lattice steps,
so `B` is a sum of gcds (CSES 2193 asks for exactly this).
"""),
            Numeric(r"""
The triangle `(0,0), (4,0), (0,4)`. How many lattice points are strictly inside it?
""", answer=3,
                hint="`A = 8`. Each edge has `gcd = 4` steps, so `B = 12`.",
                explain=r"""
`I = A − B/2 + 1 = 8 − 6 + 1 = 3`: the points (1,1), (1,2) and (2,1). With the shoelace
sum `S = 2A` it is safer to stay in integers: `I = (S − B + 2) / 2`.
"""),
            Reflect(r"""
The farthest pair among `n = 2·10^5` points is O(n^2) by brute force. Why is it enough to
look only at the corners of the convex hull, and why does that help even though `h` can
be as large as `n`?
""", answer=r"""
If the farthest pair included a point strictly inside the hull (or in the middle of an
edge), you could slide it toward a corner, moving away from the other point, so both
points of the farthest pair are corners. That alone does not beat O(n^2) when `h ≈ n`,
but the corners come out of the monotone chain in convex order. Walk an edge around the
hull: the corner farthest from that edge's *line* only ever moves forward, so two pointers
(**rotating calipers**) list the O(h) "antipodal" pairs, and the farthest pair is one of
them. O(h) after the O(n log n) hull. (Careful: the corner farthest from a *corner* does
not move monotonically; the argument needs edges.)
"""),
        ]),
    ],
    problems=[POINT_LOCATION, SEGMENT_INTERSECTION, POLYGON_AREA, POINT_IN_POLYGON, CONVEX_HULL],
    cards=[
        Card(r"""Cross product of `u` and `v`, and what its sign means for `cross(a, b, c) = (b − a) × (c − a)`?""",
             r"""`u.x·v.y − u.y·v.x`. Positive: `c` is left of `a → b` (counterclockwise turn); negative: right; zero: collinear."""),
        Card(r"""Coordinates within ±M. How large can a cross product get, and when does `long long` stop being enough?""",
             r"""Each product of differences is up to (2M)^2 = 4M^2. M = 10^9 gives 4·10^18: fits (limit ≈ 9.22·10^18). M = 2·10^9 does not: use `__int128`."""),
        Card(r"""Why not compute orientations with `double` when inputs are integers up to 10^9?""",
             r"""`double` has 53 bits of mantissa (exact to ≈ 9·10^15). Products near 10^18 are rounded by up to hundreds, so nearly-collinear points get the wrong sign or 0."""),
        Card(r"""Full test for segments `ab` and `cd` sharing a point?""",
             r"""Proper crossing: `sgn(cross(a,b,c))·sgn(cross(a,b,d)) < 0` and `sgn(cross(c,d,a))·sgn(cross(c,d,b)) < 0`. Otherwise YES iff some orientation is 0 and that endpoint is inside the other segment's bounding box."""),
        Card(r"""What does "YES if `o1·o2 ≤ 0` and `o3·o4 ≤ 0`" get wrong?""",
             r"""Collinear segments with a gap: all four orientations are 0. Also `o1·o2` on raw values overflows `long long`; multiply signs."""),
        Card(r"""The shoelace formula?""",
             r"""`2A = |Σ (x_i·y_(i+1) − x_(i+1)·y_i)|`, indices mod n. Positive sum = counterclockwise. Each term is the doubled signed triangle (origin, edge)."""),
        Card(r"""Point in polygon by ray casting: the rule that handles rays through corners?""",
             r"""Boundary check first. Then count edges with `min(a.y,b.y) ≤ q.y < max(a.y,b.y)` that cross to the right of `q` (`cross(low, high, q) > 0`). Odd = inside."""),
        Card(r"""Monotone chain convex hull, in three lines?""",
             r"""Sort by (x, y), remove repeats. Sweep left to right popping while `cross(st[k-2], st[k-1], p) <= 0`, push `p`. Sweep right to left the same way; join the chains. O(n log n)."""),
        Card(r"""Why may monotone chain pop `b` when `cross(a, b, p) ≤ 0`?""",
             r"""`b` is on or above segment `a–p`, two points of the set, so it can never be a lower-hull corner. Each point is popped at most once: O(n) per sweep."""),
        Card(r"""Convex hull keeping the points in the middle of edges: what changes?""",
             r"""Pop only on `< 0`, and handle the all-collinear input separately (otherwise both sweeps return every point and the middle ones appear twice)."""),
        Card(r"""Pick's theorem, and how to get B?""",
             r"""`A = I + B/2 − 1` for lattice polygons. B = Σ gcd(|dx|, |dy|) over the edges. In integers: `I = (2A − B + 2) / 2`."""),
    ],
)
