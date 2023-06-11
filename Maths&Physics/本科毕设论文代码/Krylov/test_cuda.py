import numpy as np
import cupy as cp
from time import time


N = 8192

ar = np.random.random((N, N))
# br = np.random.random((N, N))

a = np.array(ar, dtype=np.float64)
a = (a + a.T) / 2
# b = np.array(br, dtype=np.float64)
t = time()
# c = np.einsum('ij,ij', np.conj(a), b)
c, d = np.linalg.eigh(a)
print('numpy: ', time() - t)

a = cp.array(a, dtype=cp.float64)
b = cp.array(b, dtype=cp.float64)
t = time()
# c = cp.einsum('ij,ij', cp.conj(a), b)
c, d = cp.linalg.eigh(a)
print('cupy: ', time() - t)
