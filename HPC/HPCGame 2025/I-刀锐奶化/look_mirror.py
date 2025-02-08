import numpy as np
import matplotlib.pyplot as plt


with open('in.data', 'rb') as f:
    src = np.fromfile(f, dtype=np.float64, count=3)
    print(src)
    f.seek(8*3)
    mirn = np.fromfile(f, dtype=np.int64, count=1)[0]
    f.seek(8*4)
    mirror_data = np.fromfile(f, dtype=np.float64, count=mirn*3).reshape(mirn, 3)
    f.seek(8*(4+mirn*3))

    senn = np.fromfile(f, dtype=np.int64, count=1)[0]
    f.seek(8*(4+mirn*3+1))
    sensor_data = np.fromfile(f, dtype=np.float64, count=senn*3).reshape(senn, 3)


print(mirn)
print(mirror_data.shape)
print(senn)
print(sensor_data.shape)

m = senn // 2
row = np.sqrt(senn)
row = int(row)
assert(row * row == senn)

for i in range(m, senn):
    x = sensor_data[i]
    j = i % row
    k = i // row + 1
    y = sensor_data[senn-k*row+j]
    y[1] = -y[1]

    # print(x, y)

    assert(np.allclose(x, y), "Error at %d %d" % (i, senn-k*row+j))


# 3D scatter plot

# mirror_data = mirror_data[::16, :]
sensor_data = sensor_data[:, :]

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# ax.scatter(mirror_data[:,0], mirror_data[:,1], mirror_data[:,2])
ax.scatter(sensor_data[:,0], sensor_data[:,1], sensor_data[:,2])
plt.show()