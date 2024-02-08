import numpy as np


for i in range(100):
    m = np.random.randn(200, 4000)
    np.save(f"inputs/input_{i}.npy", m)

for i in range(4):
    m = np.random.randn(4000, 4000)
    np.save(f"weights/weight_{i}.npy", m)