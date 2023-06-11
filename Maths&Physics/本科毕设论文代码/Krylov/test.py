import utils
import numpy as np
import matplotlib.pyplot as plt


N = 10

b, basis = utils.main(N, 40, np.array([1]*N, np.float64), np.array([0.1]*N, np.float64))

plt.plot(b)
plt.show()