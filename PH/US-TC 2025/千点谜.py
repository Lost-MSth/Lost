import matplotlib.pyplot as plt
import numpy as np

with open("千点谜.txt", "r") as f:
    data = f.readlines()

points = []

横跨屏幕 = []
参差不齐 = []

for line in data:
    x, y = tuple(map(float, line[1:-2].split(',')))
    if x > 500:
        横跨屏幕.append([x, y])
    elif 90 < y <= 100 and (-1000 <= x <= -200 or 140 <= x <= 500):
        参差不齐.append([x, y])
    else:
        points.append([x, y])

横跨屏幕 = sorted(横跨屏幕, key=lambda p: p[0], reverse=True)
print(横跨屏幕)
for x, y in 横跨屏幕:
    rx = 10000 / x
    ry = 10000 / y
    print(f"({rx:.1f}, {ry:.1f}), ", end="")
print()
ans = []
for i in range(1, 11):
    x = 10000 / i
    y = []
    for p in 横跨屏幕:
        if abs(p[0] - x) < 1e-5:
            y.append(p[1])
    if len(y) == 2:
        print(abs(1/y[0] - 1/y[1]))
        ans.append(abs(1/y[0] + 1/y[1]))
    else:
        print(f"x={x}, y=Not found")
print(ans)
# print('横跨屏幕: ', ''.join(map(lambda x: chr(x+64), ans)))

points = np.array(points)

# 多张图
fig, ax = plt.subplots(2, 2, figsize=(10, 10))
ax[0, 0].set_title("Full View")
ax[0, 0].scatter(points[:, 0], points[:, 1])
ax[0, 0].set_aspect('equal', adjustable='box')

ax[0, 1].set_title("Crossing Screen")
ax[0, 1].scatter(np.array(横跨屏幕)[:, 0], np.array(横跨屏幕)[:, 1])

ax[1, 0].set_title("Uneven")
ax[1, 0].scatter(np.array(参差不齐)[:, 0], np.array(参差不齐)[:, 1])


# plt.gca().set_aspect('equal', adjustable='box')
# plt.gca().invert_yaxis()
# plt.gca().invert_xaxis()
plt.show()
