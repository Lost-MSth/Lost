from pauli import *
from time import time
from math import isclose
from cmath import sqrt
from math import sqrt as msqrt
import matplotlib.pyplot as plt

N = 15
MAX_BASIS = 20
TOL = 1e-8
TOL_M = 1e-16
NORM_L = 10
TOL_CHECK = 1e-12

JXX = 1
JXX_2 = 3
V1 = 1
V2 = 0.51

def get_init():
    return get_sigma(1, N, 2) #get_a(1, SP) + get_a(1, SM)

def get_hamilton():
    # 生成哈密顿量
    hamilton = MultiPauliString()
    for i in range(1, N+1):
        x = get_sigma(i, N, 5) @ get_sigma(i+1, N, 6)
        hamilton -= JXX * (x + x.dagger)

    for i in range(1, N+1):
        x = get_sigma(i, N, 5) @ get_sigma(i, N,
                                           2) @ get_sigma(i+1, N, 2) @ get_sigma(i+2, N, 6)
        hamilton -= JXX_2 * (x + x.dagger)

    for i in range(1, N+1):
        hamilton += (get_sigma(i+1, N, 2) + get_sigma(1, N, 0)
                     ) @ (get_sigma(i, N, 2) + get_sigma(1, N, 0)) * (0.25 * V1)

    for i in range(1, N+1):
        hamilton += (get_sigma(i+2, N, 2) + get_sigma(1, N, 0)
                     ) @ (get_sigma(i, N, 2) + get_sigma(1, N, 0)) * (0.25 * V2)

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

    # 计算bn
    for i in range(2, MAX_BASIS):
        t = l_super(basis_1, h) - b[i-1] * basis_0
        t_b = sqrt(norm(t)).real
        if isclose(t_b, 0, abs_tol=epsilon):
            return b
        # t = t - inner_dot(t, basis_1) * basis_1
        # t = t - inner_dot(t, basis_1) * basis_1
        # x = inner_dot(t, t)
        b.append(t_b)
        basis_0 = basis_1
        basis_1 = (t / b[-1])

    print('Warning')
    return b

#generate_basis = pro


tt = time()
h = get_hamilton()
print(f'计算Hamilton耗时：{time() - tt}')

tt = time()
init = get_init()
#init = np.dot(get_a(1, SP), get_a(1, SM))
b = lanc(init, h)  # fo
print(f'计算Basis耗时：{time() - tt}')
print(b)
print(f'长度：{len(b)}')

#b_2, basis_2 = th_pro(init, h)


# print(basis)
# plt.subplot(2, 1, 1)
# plt.plot([abs(i[0]-i[1]) for i in zip(b, b_2)])
# plt.subplot(2, 1, 2)

plt.plot(b)
plt.show()