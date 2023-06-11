from cmath import sqrt
from math import isclose

import numpy as np
cimport numpy as npy

from time import time


# COMP = np.complex128
# FLOAT = np.float64

ctypedef npy.complex128_t COMP_T
ctypedef npy.float64_t FLOAT_T

cdef extern from "complex.h":
    COMP_T conj(COMP_T z)

cdef int N, K
cdef int MAX_BASIS
cdef double[:] t_list
cdef double[:] c_list
DEF TOL = 1e-8
DEF TOL_M = 1e-16
DEF TOL_CHECK = 1e-12
DEF epsilon = 1e-8

# Pauli matrices
cdef COMP_T[:, :] SX = np.array([[0, 1], [1, 0]], dtype=np.complex128)
cdef COMP_T[:, :] SY = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
cdef COMP_T[:, :] SZ = np.array([[1, 0], [0, -1]], dtype=np.complex128)
cdef COMP_T[:, :] SP = np.array([[0, 1], [0, 0]], dtype=np.complex128)
cdef COMP_T[:, :] SM = np.array([[0, 0], [1, 0]], dtype=np.complex128)
cdef COMP_T[:, :] I = np.eye(2, dtype=np.complex128)
cdef COMP_T[:, :] IN = None
cdef COMP_T[:, :] ZN = None
H = None


cdef COMP_T[:, :] get_sigma(int n, COMP_T[:, :] unit):
    # 生成n位置的Pauli矩阵，即多体sigma
    return np.kron(np.kron(np.eye(2**(n-1)), unit), np.eye(2**(N-n)))


cdef COMP_T[:, :] get_a(int n, COMP_T[:, :] unit):
    # 生成n位置的产生湮灭矩阵，即多体a
    # 注意unit只能是SP或者SM
    cdef COMP_T[:, :] r = np.eye(2**N, dtype=np.complex128)
    cdef Py_ssize_t i
    for i in range(1, n):
        r = np.dot(r, IN - 2 * np.dot(get_sigma(i, SP), get_sigma(i, SM)))
    return np.dot(r, get_sigma(n, unit))


cdef COMP_T[:, :] get_hamilton():
    # 生成哈密顿量
    cdef COMP_T[:, :] hamilton = np.zeros((2**N, 2**N), dtype=np.complex128)
    cdef Py_ssize_t i
    cdef COMP_T[:, :] x

    for i in range(1, N):
        x = np.dot(get_sigma(i+1, SP), get_sigma(i, SM))
        hamilton += t_list[i] * (x + np.conj(x).T)
        
        hamilton += np.dot(np.array(get_sigma(i+1, SZ)) + IN,
                           np.array(get_sigma(i, SZ)) + IN) / 4 * c_list[i]

    return hamilton


cdef COMP_T inner_dot(COMP_T[:, :] a, COMP_T[:, :] b):
    cdef COMP_T s = 0
    cdef Py_ssize_t i, j
    for i in range(K):
        for j in range(K):
            s += conj(a[i, j]) * b[i, j]

    return s / K


cdef COMP_T[:, :] matrix_mul(COMP_T[:, :] a, COMP_T b):
    cdef Py_ssize_t i, j
    cdef COMP_T[:, :] r = ZN
    for i in range(K):
        for j in range(K):
            r[i, j] = a[i, j] * b
    return r


# cdef COMP_T[:, :] matrix_minus(COMP_T[:, :] a, COMP_T[:, :] b):
#     cdef Py_ssize_t i, j
#     cdef COMP_T[:, :] r = ZN
#     for i in range(K):
#         for j in range(K):
#             r[i, j] = a[i, j] - b[i, j]
#     return r

# cdef COMP_T[:, :] matrix_dot(COMP_T[:, :] a, COMP_T[:, :] b):
#     cdef Py_ssize_t i, j, k
#     cdef COMP_T[:, :] r
#     for i in range(K):
#         for j in range(K):
#             for k in range(K):
#                 r[i, j] += a[i, k] * b[k, j]
#     return r


cdef COMP_T[:, :] l_super(npy.ndarray[COMP_T, ndim=2] a):
    # [H, .]
    #return matrix_add(matrix_dot(h, a), matrix_dot(a, h), 0)
    return np.matmul(H, a) - np.matmul(a, H)
    # cdef Py_ssize_t i, j, k
    # cdef COMP_T[:, :] r = ZN
    # for i in range(K):
    #     for j in range(K):
    #         for k in range(K):
    #             r[i, j] += h[i, k] * a[k, j] - a[i, k] * h[k, j]
    # return r


cdef COMP_T[:, :] re_orthogonalize(COMP_T[:, :] t, list basis):
    # 重新正交化，basis必须归一！
    cdef npy.ndarray[COMP_T, ndim=2] tt, i

    tt = np.copy(t)
    for i in basis:
        tt -= matrix_mul(i, inner_dot(i, t))
    return tt


cdef fo(COMP_T[:, :] init_operator):
    # 迭代生成Krylov basis
    # 完全正交化
    cdef list basis = []
    cdef list b = []
    cdef Py_ssize_t i
    cdef COMP_T[:, :] t
    # 计算b0
    b.append(sqrt(inner_dot(init_operator, init_operator)).real)
    if isclose(b[0], 0, abs_tol=TOL):
        return b, basis
    basis.append(np.array(init_operator) / b[0])
    # 计算b1
    t = l_super(basis[0])
    t = re_orthogonalize(t, basis)
    t = re_orthogonalize(t, basis)
    b.append(sqrt(inner_dot(t, t)).real)
    if isclose(b[1], 0, abs_tol=TOL):
        return b, basis
    basis.append(np.array(t) / b[1])
    # 计算bn
    for i in range(2, MAX_BASIS):
        t = l_super(basis[i-1])  # - b[i-1] * basis[i-2]
        t = re_orthogonalize(t, basis)
        t = re_orthogonalize(t, basis)
        b.append(sqrt(inner_dot(t, t)).real)
        if isclose(b[-1], 0, abs_tol=TOL):
            return b, basis
        basis.append(np.array(t) / b[-1])

    print('Warning')
    return b, basis


def main(n, max_basis, ts, cs):
    global N, MAX_BASIS, t_list, c_list, IN, K, ZN, H
    N = n
    K = 2 ** N
    MAX_BASIS = max_basis
    t_list = ts
    c_list = cs
    IN = np.eye(2**N, dtype=np.complex128)
    ZN = np.zeros((2**N, 2**N), dtype=np.complex128)

    cdef COMP_T[:, :] init
    
    cdef list b, basis

    t = time()
    H = np.array(get_hamilton(), dtype=np.complex128)
    print('Hamiltonian time:', time() - t)

    t = time()
    init = np.array(get_a(2, SP)) + np.array(get_a(2, SM))
    b, basis = fo(init)
    print('FO time:', time() - t)
    return b, basis