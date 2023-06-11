import time
from cmath import sqrt
from math import isclose
from math import sqrt as msqrt

import matplotlib.pyplot as plt
import cupy as np
#import numpy as np

N = 10
M = 1
MAX_BASIS = 30
# t_list = [1/4, 2/4, 3/4, 4/4, 0, 1, 1, 1, 1]
# c_list = [1] * (N-1)
t_list = [-1.5, -0.5, 0.5, 1.7, 2.2, 2.6, 2.9, 3, 3.1]
C1 = 0
C2 = 1
TOL = 1e-8
TOL_M = 1e-16
NORM_L = 10
TOL_CHECK = 1e-12

# Pauli matrices
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SP = np.array([[0, 1], [0, 0]], dtype=complex)
SM = np.array([[0, 0], [1, 0]], dtype=complex)
I = np.eye(2, dtype=complex)
IN = np.eye(2**N, dtype=complex)


def get_sigma(n, unit):
    # 生成n位置的Pauli矩阵，即多体sigma
    return np.kron(np.kron(np.eye(2**(n-1)), unit), np.eye(2**(N-n)))


def get_a(n, unit):
    # 生成n位置的产生湮灭矩阵，即多体a
    # 注意unit只能是SP或者SM
    r = np.eye(2**N, dtype=complex)
    for i in range(1, n):
        r = np.dot(r, IN - 2 * np.dot(get_sigma(i, SP), get_sigma(i, SM)))
    return np.dot(r, get_sigma(n, unit))


# def get_hamilton():
#     # 生成哈密顿量，平均场是临近的两个电子之间的耦合
#     hamilton = np.zeros((2**N, 2**N), dtype=complex)
#     for i in range(1, N):
#         x = get_sigma(i, SP) @ get_sigma(i+1, SM)
#         hamilton += t_list[i-1] * (x + np.conj(x).T)
#         hamilton += np.matmul(get_sigma(i+1, SZ) + IN,
#                            get_sigma(i, SZ) + IN) / 4 * c_list[i-1]

#     return hamilton

def get_hamilton():
    # 生成哈密顿量，fan heng论文的
    hamilton = np.zeros((2**N, 2**N), dtype=complex)
    for i in range(1, N):
        x = get_sigma(i, SP) @ get_sigma(i+1, SM)
        hamilton -= t_list[i-1] * (x + np.conj(x).T)

    for i in range(1, N+1):
        hamilton -= np.matmul(get_sigma(i, SP), get_sigma(i, SM)) * C1

    for i in range(1, N):
        hamilton += (get_sigma(i+1, SZ) + IN) @ (get_sigma(i, SZ) + IN) * (C2 / 4)

    return hamilton

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
    print('check')
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
    return b, basis


def ffo(init_operator, h):
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
        t = re_orthogonalize(t, basis)
        b.append(sqrt(inner_dot(t, t)).real)
        if isclose(b[-1], 0, abs_tol=TOL):
            return b, basis
        basis.append(t / b[-1])

    print('Warning')
    return b, basis


def pro(init_operator, h):
    # 迭代生成Krylov basis
    # 部分正交化
    basis = []
    basis_a = [np.copy(init_operator)]
    b = []
    w = [[1]]
    epsilon = msqrt(TOL_M)
    # 计算b0
    b.append(sqrt(inner_dot(init_operator, init_operator)).real)
    if isclose(b[0], 0, abs_tol=epsilon):
        return b, basis
    basis.append(np.copy(init_operator) / b[0])
    # 计算b1
    t = l_super(basis[0], h)
    t = re_orthogonalize(t, basis)
    t = re_orthogonalize(t, basis)
    b.append(sqrt(inner_dot(t, t)).real)
    if isclose(b[1], 0, abs_tol=epsilon):
        return b, basis
    basis.append(t / b[1])
    basis_a.append(t)
    w[0].append(TOL_M)
    w.append([0, 1])
    # 计算bn
    for i in range(2, MAX_BASIS):
        t = l_super(basis[i-1], h) - b[i-1] * basis[i-2]
        t_b = sqrt(inner_dot(t, t)).real
        if isclose(t_b, 0, abs_tol=epsilon):
            return b, basis
        t = t - inner_dot(t, basis[i-1]) * basis[i-1]
        t = t - inner_dot(t, basis[i-1]) * basis[i-1]
        basis_a.append(t)

        w[i-1].append(TOL_M)
        w.append([0]*i + [1])

        t_w = b[1] * np.conj(w[1][i-1]) - b[i-1] * w[0][i-2]
        if t_w == 0:
            w[0].append(0)
        else:
            w[0].append((t_w + t_w/abs(t_w) * 2 * TOL_M * NORM_L) / b[0])
        flag = False
        if isclose(w[0][-1], 0, abs_tol=epsilon):
            flag = True
            for k in range(1, i-1):
                t_w = b[k+1] * np.conj(w[k+1][i-1]) + b[k] * \
                    np.conj(w[k-1][i-1]) - b[i-1] * w[k][i-2]
                if t_w == 0:
                    w[k].append(0)
                else:
                    w[k].append(
                        (t_w + t_w/abs(t_w) * 2 * TOL_M * NORM_L) / b[k])
                if not isclose(w[k][-1], 0, abs_tol=epsilon):
                    flag = False
                    break
        if not flag:
            print(i)
            # 重正交化
            basis_a[-2] = re_orthogonalize(basis_a[-2], basis[:-1])
            basis_a[-2] = re_orthogonalize(basis_a[-2], basis[:-1])
            b[-1] = sqrt(inner_dot(basis_a[-2], basis_a[-2])).real
            basis[-1] = basis_a[-2] / b[-1]
            if isclose(b[-1], 0, abs_tol=epsilon):
                return b, basis
            basis_a[-1] = re_orthogonalize(basis_a[-1], basis)
            basis_a[-1] = re_orthogonalize(basis_a[-1], basis)
            b.append(sqrt(inner_dot(basis_a[-1], basis_a[-1])).real)
            if isclose(b[-1], 0, abs_tol=epsilon):
                return b, basis
            basis.append(basis_a[-1] / b[-1])
            w[i-1][i-1] = 1
            for k in range(0, i-2):
                w[k][i-1] = TOL_M
            w[i][i] = 1
            for k in range(0, i-1):
                if len(w[k]) == i:
                    w[k].append(TOL_M)
                else:
                    w[k][i] = TOL_M
        else:
            b.append(sqrt(inner_dot(t, t)).real)
            basis.append(t / b[-1])

    print('Warning')
    return b, basis


def th_pro(init_operator, h):
    # 迭代生成Krylov basis
    # 部分正交化
    basis = []
    basis_a = [np.copy(init_operator)]
    b = []
    epsilon = msqrt(TOL_M)
    # 计算b0
    b.append(sqrt(inner_dot(init_operator, init_operator)).real)
    if isclose(b[0], 0, abs_tol=epsilon):
        return b, basis
    basis.append(np.copy(init_operator) / b[0])
    # 计算b1
    t = l_super(basis[0], h)
    t = re_orthogonalize(t, basis)
    t = re_orthogonalize(t, basis)
    b.append(sqrt(inner_dot(t, t)).real)
    if isclose(b[1], 0, abs_tol=epsilon):
        return b, basis
    basis.append(t / b[1])
    basis_a.append(t)
    # 计算bn
    for i in range(2, MAX_BASIS):
        t = l_super(basis[i-1], h) - b[i-1] * basis[i-2]
        t_b = sqrt(inner_dot(t, t)).real
        if isclose(t_b, 0, abs_tol=epsilon):
            return b, basis
        t = t - inner_dot(t, basis[i-1]) * basis[i-1]
        t = t - inner_dot(t, basis[i-1]) * basis[i-1]
        basis_a.append(t)

        if not isclose(abs(inner_dot(basis[0], t)), 0, abs_tol=TOL_CHECK):
            print(i)
            # 重正交化
            basis_a[-2] = re_orthogonalize(basis_a[-2], basis[:-1])
            basis_a[-2] = re_orthogonalize(basis_a[-2], basis[:-1])
            b[-1] = sqrt(inner_dot(basis_a[-2], basis_a[-2])).real
            basis[-1] = basis_a[-2] / b[-1]
            if isclose(b[-1], 0, abs_tol=epsilon):
                return b, basis
            basis_a[-1] = re_orthogonalize(basis_a[-1], basis)
            basis_a[-1] = re_orthogonalize(basis_a[-1], basis)
            b.append(sqrt(inner_dot(basis_a[-1], basis_a[-1])).real)
            if isclose(b[-1], 0, abs_tol=epsilon):
                return b, basis
            basis.append(basis_a[-1] / b[-1])
        else:
            b.append(sqrt(inner_dot(t, t)).real)
            basis.append(t / b[-1])

    print('Warning')
    return b, basis


def main(m):
    #generate_basis = pro

    tt = time.time()
    h = get_hamilton()
    print(f'计算Hamilton耗时：{time.time() - tt}')

    # print(np.count_nonzero(h))

    tt = time.time()
    init = get_sigma(m, SZ)#np.matmul(get_a(M, SP), get_a(M, SM))
    #init = np.dot(get_a(1, SP), get_a(1, SM))
    b, basis = fo(init, h)  # fo
    print(f'计算Basis耗时：{time.time() - tt}')
    print(b)
    # with open('basis.txt', 'a') as f:
    #     f.write(f'{m} {b[1:]}\n')
    print(f'长度：{len(b)}')

    #b_2, basis_2 = th_pro(init, h)

    # print(basis)
    # plt.subplot(2, 1, 1)
    # plt.plot([abs(i[0]-i[1]) for i in zip(b, b_2)])
    # plt.subplot(2, 1, 2)
    plt.plot(b)
    plt.show()

    # for i in basis:
    #     print(np.count_nonzero(i))

    check(basis)


main(M)