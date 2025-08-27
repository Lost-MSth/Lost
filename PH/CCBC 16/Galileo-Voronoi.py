from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import Bounds, minimize
from scipy.spatial import Voronoi


class Point(NamedTuple):
    y: int
    x: int

    def __add__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.y + other.y, self.x + other.x)

    def __sub__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.y - other.y, self.x - other.x)


N = 7
MAX = 760

# 第一张图的
# EDGES = {
#     (Point(274, 0), Point(274, 206)): (0, 3),
#     (Point(0, 316), Point(274, 206)): (0, 1),
#     (Point(300, 226), Point(274, 206)): (1, 3),
#     (Point(300, 226), Point(392, 527)): (1, 4),
#     (Point(300, 226), Point(517, 222)): (4, 3),
#     (Point(695, 0), Point(517, 222)): (5, 3),
#     (Point(760, 425), Point(517, 222)): (5, 4),
#     (Point(760, 468), Point(512, 598)): (6, 4),
#     (Point(505, 760), Point(512, 598)): (6, 2),
#     (Point(392, 527), Point(512, 598)): (4, 2),
#     (Point(392, 527), Point(0, 727)): (1, 2),
# }

# 第二张图的
EDGES = {
    (Point(112, 0), Point(263, 220)): (0, 2),
    (Point(46, 480), Point(263, 220)): (0, 3),
    (Point(402, 203), Point(263, 220)): (2, 3),
    (Point(402, 203), Point(620, 0)): (2, 5),
    (Point(402, 203), Point(470, 448)): (3, 5),
    (Point(169, 525), Point(470, 448)): (3, 4),
    (Point(532, 494), Point(470, 448)): (5, 4),
    (Point(532, 494), Point(760, 494)): (5, 6),
    (Point(532, 494), Point(391, 745)): (4, 6),
    (Point(393, 760), Point(391, 745)): (1, 6),
    (Point(169, 525), Point(391, 745)): (1, 4),
    (Point(169, 525), Point(46, 480)): (1, 3),
    (Point(0, 493), Point(46, 480)): (1, 0),
}

POINTS = set()
for p1, p2 in EDGES.keys():
    POINTS.add(p1)
    POINTS.add(p2)
POINTS = list(sorted(POINTS))
print(POINTS)

# 第一张图，通过交点可以读出来一些
# FIXEDS = [
#     None,
#     Point(203, 477),
#     Point(330, 703),
#     Point(513, 69),
#     Point(515, 373),
#     Point(672, 194),
#     None,
# ]

# 第二张图，通过交点可以读出来一些
FIXEDS = [
    None,
    None,
    Point(291, 40.7),
    Point(338, 391),
    None,
    Point(556.4, 325.7),
    None,
]
assert len(FIXEDS) == N, f"Expected {N} fixed points, got {len(FIXEDS)}"


def func(p):
    r = np.zeros(len(EDGES))
    p = p.reshape(N, 2)

    for i, point in enumerate(p):
        if FIXEDS[i] is not None:
            p[i] = [FIXEDS[i].x, FIXEDS[i].y]

    for idx, ((p1, p2), (i, j)) in enumerate(EDGES.items()):
        m = (p[i] + p[j]) / 2
        dp = p2 - p1
        d2y = m[1] - p1.y
        d2x = m[0] - p1.x
        r[idx] = d2y * dp.x - d2x * dp.y

    # print(r)
    return np.sum(np.abs(r))
    # return np.max(np.abs(r))


# optimize to get zero point
init = np.random.rand(N * 2) * MAX
init = init.reshape(N, 2)
for i, p in enumerate(FIXEDS):
    if p is not None:
        init[i] = [p.x, p.y]
init = init.flatten()

res = minimize(func, init, bounds=Bounds(0, MAX),
               method='SLSQP',
               options={'maxiter': 200000, 'ftol': 1e-10})

# Nelder-Mead, L-BFGS-B, TNC, SLSQP, Powell, trust-constr, COBYLA, and COBYQA methods.

print(res)
if not res.success:
    print("Optimization failed.")
    exit(0)

print(f'Final Value: {res.fun}')

p = res.x.reshape(N, 2)
vy_val = p[:, 1]
vx_val = p[:, 0]

for i, p in enumerate(FIXEDS):
    if p is not None:
        vx_val[i] = p.x
        vy_val[i] = p.y

for i in range(N):
    print(f"Point {i}: ({vx_val[i]}, {vy_val[i]})")


vor = Voronoi(list(zip(vx_val, vy_val)))

# Plotting the Voronoi diagram
plt.figure(figsize=(8, 8))
for i in range(len(vx_val)):
    plt.text(vx_val[i], vy_val[i], str(i), fontsize=12, ha='right')
plt.plot(vx_val, vy_val, 'o')
plt.plot(vor.vertices[:, 0], vor.vertices[:, 1], 'x')
for vpair in vor.ridge_vertices:
    if vpair[0] >= 0 and vpair[1] >= 0:
        v0 = vor.vertices[vpair[0]]
        v1 = vor.vertices[vpair[1]]
        # Draw a line from v0 to v1.
        plt.plot([v0[0], v1[0]], [v0[1], v1[1]], 'k', linewidth=2)

# plot EDGES
for (p1, p2), (i, j) in EDGES.items():
    plt.plot([p1.x, p2.x], [p1.y, p2.y], color='blue')

# plot POINTS
LENGTH = MAX * .8
for p in POINTS:
    nn = []
    for p1, p2 in EDGES.keys():
        if p == p1 or p == p2:
            nn.append(p1 if p == p2 else p2)
    if len(nn) != 3:
        continue

    nn = [x - p for x in nn]
    angles = [np.arctan2(x.y, x.x) for x in nn]
    angles.sort()
    for i in range(3):
        theta = angles[i] + np.pi - angles[(i+1) % 3] + angles[(i+2) % 3]
        plt.plot([p.x, p.x + LENGTH * np.cos(theta)],
                 [p.y, p.y + LENGTH * np.sin(theta)], color='red', alpha=0.3)


def mouse_event(event):
    if event.inaxes is not None:
        x, y = event.xdata, event.ydata
        print(f"Mouse clicked at: ({x}, {y})")


plt.gcf().canvas.mpl_connect('button_press_event', mouse_event)

plt.xlim(0, MAX)
plt.ylim(MAX, 0)
plt.gca().set_aspect('equal')
plt.show()
