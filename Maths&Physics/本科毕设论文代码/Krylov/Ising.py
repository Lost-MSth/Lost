import time
from cmath import sqrt
from math import isclose
from math import sqrt as msqrt

import matplotlib.pyplot as plt
import cupy as np
#import numpy as np

N = 12
MAX_BASIS = 24
TOL = 1e-8
TOL_M = 1e-16
NORM_L = 10
TOL_CHECK = 1e-12

JXX = 1
BZ = -1.05
BX = 0.5

DTYPE = np.complex128

# Pauli matrices
SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
SY = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
SP = np.array([[0, 1], [0, 0]], dtype=DTYPE)
SM = np.array([[0, 0], [1, 0]], dtype=DTYPE)
I = np.eye(2, dtype=DTYPE)
IN = np.eye(2**N, dtype=DTYPE)


def get_sigma(n, unit):
    # 生成n位置的Pauli矩阵，即多体sigma
    return np.kron(np.kron(np.eye(2**(n-1)), unit), np.eye(2**(N-n)))


def get_a(n, unit):
    # 生成n位置的产生湮灭矩阵，即多体a
    # 注意unit只能是SP或者SM
    r = np.eye(2**N, dtype=DTYPE)
    for i in range(1, n):
        r = np.dot(r, IN - 2 * np.dot(get_sigma(i, SP), get_sigma(i, SM)))
    return np.dot(r, get_sigma(n, unit))


def get_hamilton():
    # 生成哈密顿量
    hamilton = np.zeros((2**N, 2**N), dtype=DTYPE)
    for i in range(1, N):
        x = np.matmul(get_sigma(i, SX), get_sigma(i+1, SX))
        hamilton += JXX * x  # (x + np.conj(x).T)

    hamilton += JXX * np.matmul(get_sigma(N, SX), get_sigma(1, SX))

    for i in range(1, N+1):
        hamilton += BZ * get_sigma(i, SZ) + BX * get_sigma(i, SX)

    return hamilton


def get_init():
    r = np.zeros((2**N, 2**N), dtype=DTYPE)
    for i in range(1, N+1):
        r += get_sigma(i, SZ)
    for i in range(1, N):
        x = np.matmul(get_sigma(i, SX), get_sigma(i+1, SX))
        r += 1.05 * x  # (x + np.conj(x).T)
    r += 1.05 * np.matmul(get_sigma(N, SX), get_sigma(1, SX))
    return r

# def get_hamilton_():
#     # 生成哈密顿量
#     hamilton = np.zeros((2**N, 2**N), dtype=complex)
#     for i in range(1, N):
#         x = np.dot(get_a(i+1, SP), get_a(i, SM))
#         hamilton += t_list[i] * (x + np.conj(x).T)
#         hamilton += np.dot(np.dot(get_a(i+1, SP), get_a(i+1, SM)), np.dot(get_a(i, SP), get_a(i, SM))) * c_list[i]

#     return hamilton


def check(basis):
    # 正交性校验
    for i in range(len(basis)):
        for j in range(len(basis)):
            if i == j:
                continue
            t = inner_dot(basis[i], basis[j])
            if not isclose(abs(t), 0, abs_tol=TOL_CHECK):
                print(f'{i} {j} {t}')
                break
                # return False
        if i > 100:
            break


def inner_dot(a, b):
    # return np.trace(np.dot(np.conj(a).T, b)) / (2 ** N)
    return np.einsum('ij,ij', np.conj(a), b) / (2 ** N)


def l_super(a, h):
    # [H, .]
    return np.matmul(h, a) - np.matmul(a, h)


def lanc(init_operator, h):

    basis_0 = None
    basis_1 = None
    b = []
    epsilon = msqrt(TOL_M)
    # 计算b0
    b.append(sqrt(inner_dot(init_operator, init_operator)).real)
    if isclose(b[0], 0, abs_tol=epsilon):
        return b
    basis_0 = (np.copy(init_operator) / b[0])
    # 计算b1
    t = l_super(basis_0, h)
    b.append(sqrt(inner_dot(t, t)).real)
    if isclose(b[1], 0, abs_tol=epsilon):
        return b
    basis_1 = t / b[1]

    # 计算bn
    for i in range(2, MAX_BASIS):
        t = l_super(basis_1, h) - b[i-1] * basis_0
        t_b = sqrt(inner_dot(t, t)).real
        if isclose(t_b, 0, abs_tol=epsilon):
            return b
        t = t - inner_dot(t, basis_1) * basis_1
        t = t - inner_dot(t, basis_1) * basis_1

        b.append(sqrt(inner_dot(t, t)).real)
        basis_0 = basis_1
        basis_1 = (t / b[-1])

    print('Warning')
    return b

#generate_basis = pro


tt = time.time()
h = get_hamilton()
print(f'计算Hamilton耗时：{time.time() - tt}')

tt = time.time()
init = get_init()
#init = np.dot(get_a(1, SP), get_a(1, SM))
b = lanc(init, h)  # fo
print(f'计算Basis耗时：{time.time() - tt}')
# print(b)
print(f'长度：{len(b)}')

#b_2, basis_2 = th_pro(init, h)


# print(basis)
# plt.subplot(2, 1, 1)
# plt.plot([abs(i[0]-i[1]) for i in zip(b, b_2)])
# plt.subplot(2, 1, 2)
plt.plot(b)
plt.show()

print(b)

# check(basis)
