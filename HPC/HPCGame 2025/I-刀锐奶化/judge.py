import numpy as np


img = np.fromfile('out.data',dtype=np.float64)
ref = np.fromfile('ref.data',dtype=np.float64)

r = np.sqrt(((img-ref)**2).sum()/(ref**2).sum())

print(r)

data = img.reshape(1024, 1024)
ref_data = ref.reshape(1024, 1024)

import matplotlib.pyplot as plt

plt.figure()

ax = plt.subplot(121)
ax.imshow(data, cmap='gray')
plt.plot([0, 1024], [512, 512], 'r')

ax = plt.subplot(122)
ax.imshow(ref_data, cmap='gray')
plt.plot([0, 1024], [512, 512], 'r')

plt.show()