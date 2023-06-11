import time
from cmath import sqrt
from math import isclose
from math import sqrt as msqrt

import matplotlib.pyplot as plt
import cupy as np
#import numpy as np

N = 10
MAX_BASIS = 30
TOL = 1e-8
TOL_M = 1e-16
NORM_L = 10
TOL_CHECK = 1e-12

JXX = 1
JXX_2 = 0.2
V1 = 5
V2 = 0.5

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
        x = get_sigma(i, SP) @ get_sigma(i+1, SM)
        hamilton -= JXX * (x + np.conj(x).T)

    x = get_sigma(N, SP) @ get_sigma(1, SM)
    hamilton -= JXX * (x + np.conj(x).T)

    for i in range(1, N-1):
        x = get_sigma(i, SP) @ get_sigma(i, SZ) @ get_sigma(i +
                                                            1, SZ) @ get_sigma(i+2, SM)
        hamilton -= JXX_2 * (x + np.conj(x).T)

    x = get_sigma(N-1, SP) @ get_sigma(N-1,
                                       SZ) @ get_sigma(N, SZ) @ get_sigma(1, SM)
    hamilton -= JXX_2 * (x + np.conj(x).T)
    x = get_sigma(N, SP) @ get_sigma(N, SZ) @ get_sigma(1,
                                                        SZ) @ get_sigma(2, SM)
    hamilton -= JXX_2 * (x + np.conj(x).T)

    for i in range(1, N):
        hamilton += np.matmul(get_sigma(i+1, SZ) + IN,
                              get_sigma(i, SZ) + IN) / 4 * V1
    hamilton += np.matmul(get_sigma(N, SZ) + IN,
                          get_sigma(1, SZ) + IN) / 4 * V1

    for i in range(1, N-1):
        hamilton += np.matmul(get_sigma(i+2, SZ) + IN,
                              get_sigma(i, SZ) + IN) / 4 * V2
    hamilton += np.matmul(get_sigma(N-1, SZ) + IN,
                          get_sigma(1, SZ) + IN) / 4 * V2
    hamilton += np.matmul(get_sigma(N, SZ) + IN,
                          get_sigma(2, SZ) + IN) / 4 * V2

    return hamilton


def get_init():
    return get_sigma(1, SZ)  # get_a(1, SP) + get_a(1, SM)

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


def re_orthogonalize(t, basis):
    # 重新正交化，basis必须归一！
    tt = np.copy(t)
    for i in basis:
        tt -= inner_dot(i, t) * i
    return tt


def fo(init_operator, h):
    # 迭代生成Krylov basis
    # 完全正交化
    basis = []
    b = []
    # 计算b0
    b.append(sqrt(inner_dot(init_operator, init_operator)).real)
    if isclose(b[0], 0, abs_tol=TOL):
        return b, basis
    basis.append(np.copy(init_operator) / b[0])
    # 计算b1
    t = l_super(basis[0], h)
    t = re_orthogonalize(t, basis)
    t = re_orthogonalize(t, basis)
    b.append(sqrt(inner_dot(t, t)).real)
    if isclose(b[1], 0, abs_tol=TOL):
        return b, basis
    basis.append(t / b[1])
    # 计算bn
    for i in range(2, MAX_BASIS):
        t = l_super(basis[i-1], h)  # - b[i-1] * basis[i-2]
        t = re_orthogonalize(t, basis)
        t = re_orthogonalize(t, basis)
        b.append(sqrt(inner_dot(t, t)).real)
        if isclose(b[-1], 0, abs_tol=TOL):
            return b, basis
        basis.append(t / b[-1])

    print('Warning')
    return b

#generate_basis = pro


tt = time.time()
h = get_hamilton()
print(f'计算Hamilton耗时：{time.time() - tt}')

tt = time.time()
init = get_init()
#init = np.dot(get_a(1, SP), get_a(1, SM))
b2 = lanc(init, h)  # fo
print(f'计算Basis耗时：{time.time() - tt}')
print(b2)
print(f'长度：{len(b2)}')

b = fo(init, h)  # fo
print(f'计算Basis耗时：{time.time() - tt}')
print(b)
print(f'长度：{len(b)}')

print([x - y for x, y in zip(b, b2)])

#b_2, basis_2 = th_pro(init, h)


# print(basis)
# plt.subplot(2, 1, 1)
# plt.plot([abs(i[0]-i[1]) for i in zip(b, b_2)])
# plt.subplot(2, 1, 2)
plt.plot(b)
plt.show()


# check(basis)
