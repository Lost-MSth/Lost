# cython:language_level=3

from cmath import sqrt
from math import isclose
from math import sqrt as msqrt
from math import tanh
from time import time
import os
import psutil

import matplotlib.pyplot as plt
from pauli_func import MultiPauliString, get_sigma, l_super, norm, SparseMultiPauliString


SAVE_PATH = r'data.csv'

N = 20
MAX_BASIS = 21
TOL = 1e-8
TOL_M = 1e-16
NORM_L = 10
TOL_CHECK = 1e-12

# JXX = 1
# JXX_2 = 0
# V1 = 1
# V2 = 0

J = 3
C1 = 0
C2 = 1
t_list = [2] * N#[-2.87801326957137, -2.63752109868905, -2.2072468580584044, -1.510002582013794, -0.5432159592101127, 0.5432159592101127, 1.510002582013794, 2.2072468580584044, 2.63752109868905, 2.87801326957137, 3.005040639375704,
         # 2.87801326957137, 2.63752109868905, 2.2072468580584044, 1.510002582013794, 0.5432159592101127, -0.5432159592101127, -1.510002582013794, -2.2072468580584044, -2.63752109868905]  # [tanh(0.35*(x-J+0.5))/4/0.35*4.39 for x in range(1, N)]


def get_init(m):
    return get_sigma(m, N, 2)  # get_a(1, SP) + get_a(1, SM)


def get_current_memory_gb():
    # 获取当前进程内存占用。
    pid = os.getpid()
    p = psutil.Process(pid)
    info = p.memory_full_info()
    return info.uss / 1024 / 1024 / 1024.

# def get_hamilton():
#     # 生成哈密顿量
#     hamilton = MultiPauliString()
#     for i in range(1, N+1):
#         x = get_sigma(i, N, 5) @ get_sigma(i+1, N, 6)
#         hamilton -= (x + x.dagger) * JXX

#     for i in range(1, N+1):
#         x = get_sigma(i, N, 5) @ get_sigma(i, N,
#                                            2) @ get_sigma(i+1, N, 2) @ get_sigma(i+2, N, 6)
#         hamilton -= (x + x.dagger) * JXX_2

#     for i in range(1, N+1):
#         hamilton += (get_sigma(i+1, N, 2) + get_sigma(1, N, 0)
#                      ) @ (get_sigma(i, N, 2) + get_sigma(1, N, 0)) * (0.25 * V1)

#     for i in range(1, N+1):
#         hamilton += (get_sigma(i+2, N, 2) + get_sigma(1, N, 0)
#                      ) @ (get_sigma(i, N, 2) + get_sigma(1, N, 0)) * (0.25 * V2)

#     return hamilton


def get_hamilton():
    # 生成哈密顿量
    hamilton = MultiPauliString(N)
    for i in range(1, N+1):
        x = get_sigma(i, N, 5) @ get_sigma(i+1, N, 6)
        hamilton -= (x + x.dagger) * t_list[i-1]

    IN = get_sigma(1, N, 0)

    for i in range(1, N+1):
        hamilton += (get_sigma(i+1, N, 2) +
                     IN) @ (get_sigma(i, N, 2) + IN) * (0.25 * C2)

    return hamilton


def lanc(init_operator, h):

    basis_0 = None
    basis_1 = None
    b = []
    epsilon = msqrt(TOL_M)
    # 计算b0
    b.append(sqrt(norm(init_operator)).real)
    if isclose(b[0], 0, abs_tol=epsilon):
        return b
    basis_0 = (init_operator / b[0])
    # 计算b1
    t = l_super(basis_0, h)
    b.append(sqrt(norm(t)).real)
    if isclose(b[1], 0, abs_tol=epsilon):
        return b
    basis_1 = t / b[1]
    del t
    # with open(SAVE_PATH, 'a') as f:
    #     f.write(f'{0},{b[0]}\n{1},{b[1]}\n')

    # 计算bn
    for i in range(2, MAX_BASIS):
        t = l_super(basis_1, h) - basis_0 * b[i-1]
        t_b = sqrt(norm(t)).real
        if isclose(t_b, 0, abs_tol=epsilon):
            return b
        # t = t - inner_dot(t, basis_1) * basis_1
        # t = t - inner_dot(t, basis_1) * basis_1
        # x = inner_dot(t, t)
        b.append(t_b)
        basis_0 = basis_1
        basis_1 = (t / b[-1])
        del t
        # with open(SAVE_PATH, 'a') as f:
        #     f.write(f'{i},{b[-1]}\n')
        print(f'b_{i} = {b[-1]}')

    print('Warning')
    return b

#generate_basis = pro


tt = time()
h = SparseMultiPauliString.from_data(get_hamilton())
print(f'计算Hamilton耗时：{time() - tt}')

for i in range(1, 2):
    tt = time()
    init = get_init(i)
    #init = np.dot(get_a(1, SP), get_a(1, SM))
    b = lanc(init, h)  # fo
    print(f'计算Basis耗时：{time() - tt}')
    print(b)
    print(f'长度：{len(b)}')
    print(f'memory used: {get_current_memory_gb()} GB')
    # with open(SAVE_PATH, 'a') as f:
    #     f.write(f'{i},{",".join(map(str, b))}\n')
    # f.write(f'memory used: {get_current_memory_gb()} GB\n')

#b_2, basis_2 = th_pro(init, h)


# print(basis)
# plt.subplot(2, 1, 1)
# plt.plot([abs(i[0]-i[1]) for i in zip(b, b_2)])
# plt.subplot(2, 1, 2)

plt.plot(b)
plt.show()
