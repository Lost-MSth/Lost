from math import isclose, sqrt, exp
from time import time

import cupy as cp
import matplotlib.pyplot as plt
import numpy as np
from scipy import sparse as sp


class KrylovCalculator:

    TOL_M = 1e-16
    TOL_CHECK = 1e-12
    MAX_BASIS = 30

    DTYPE = np.float64
    # 用不到SY，就没有复数啊！
    # 顺带取消所有共轭

    # Pauli matrices
    SX = np.array([[0, 1], [1, 0]], dtype=DTYPE)
    # SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
    SZ = np.array([[1, 0], [0, -1]], dtype=DTYPE)
    SP = np.array([[0, 1], [0, 0]], dtype=DTYPE)
    SM = np.array([[0, 0], [1, 0]], dtype=DTYPE)
    I = sp.eye(2, dtype=DTYPE)

    def __init__(self, N: int = 5) -> None:
        self.N: int = N
        self.IN = sp.eye(2**self.N, dtype=self.DTYPE)
        self.hamilton = None
        self.init_operator = None
        self.eigen_vals = None
        self.eigen_vectors = None

        self.b: list = None

    def get_init(self, m: int):
        assert 1 <= m <= self.N
        self.m = m
        self.init_operator = self.get_sigma(m, self.SZ)
        # self.init_operator = sp.csr_matrix(
        #     (2**self.N, 2**self.N), dtype=self.DTYPE)
        # l = 0.5
        # for i in range(1, self.N+1):
        #     self.init_operator += (self.get_sigma(i, self.SZ) + self.IN) / \
        #         2 * 0.35 / l * exp(- 0.35**2 * (i-m)**2 / l**2)
        return self.init_operator

    def get_sigma(self, n, unit):
        # 生成n位置的Pauli矩阵，即多体sigma
        assert 1 <= n <= self.N
        return sp.kron(sp.kron(sp.eye(2**(n-1)), unit), sp.eye(2**(self.N-n)))
        # np.kron(np.kron(np.eye(2**(n-1)), unit), np.eye(2**(N-n)))

    # def get_a(n, unit):
    #     # 生成n位置的产生湮灭矩阵，即多体a
    #     # 注意unit只能是SP或者SM
    #     r = np.eye(2**N, dtype=DTYPE)
    #     for i in range(1, n):
    #         r @= IN - 2 * get_sigma(i, SP) @ get_sigma(i, SM)
    #     return r @ get_sigma(n, unit)

    def get_hamilton(self, t_list: list, C1=0, C2=1):
        # 生成哈密顿量，fan heng论文的
        # np.zeros((2**N, 2**N), dtype=DTYPE)
        s = self.get_sigma
        self.hamilton = sp.csr_matrix((2**self.N, 2**self.N), dtype=self.DTYPE)
        for i in range(1, self.N):
            x = s(i, self.SP) @ s(i+1, self.SM)
            self.hamilton -= t_list[i-1] * (x + x.T)

        if C1 != 0:
            for i in range(1, self.N+1):
                self.hamilton -= (s(i, self.SP) @ s(i, self.SM)) * C1

        if C2 != 0:
            for i in range(1, self.N):
                self.hamilton += (s(i+1, self.SZ) + self.IN) @ (s(i,
                                                                  self.SZ) + self.IN) * (C2 / 4)

        return self.hamilton

    def self_inner_dot(self, a: sp.csr_matrix) -> float:
        return np.sum(np.array(a.data) ** 2) / (2 ** self.N)

    @staticmethod
    def l_super(a: sp.csr_matrix, h: sp.csr_matrix):
        # [H, .]
        return h @ a - a @ h

    def lanczos(self):

        basis_0 = None
        basis_1 = None
        self.b = []
        epsilon = sqrt(self.TOL_M)
        # 计算b0
        self.b.append(sqrt(self.self_inner_dot(self.init_operator)))
        if isclose(self.b[0], 0, abs_tol=epsilon):
            return self.b
        basis_0 = self.init_operator / self.b[0]
        # 计算b1
        t = self.l_super(basis_0, self.hamilton)
        self.b.append(sqrt(self.self_inner_dot(t)))
        if isclose(self.b[1], 0, abs_tol=epsilon):
            return self.b
        basis_1 = t / self.b[1]

        # 计算bn
        for i in range(2, self.MAX_BASIS):
            t = self.l_super(basis_1, self.hamilton) - self.b[i-1] * basis_0
            t_b = sqrt(self.self_inner_dot(t))
            if isclose(t_b, 0, abs_tol=epsilon):
                return self.b
            # t = t - inner_dot(t, basis_1) * basis_1
            # t = t - inner_dot(t, basis_1) * basis_1

            # b.append(sqrt(self_inner_dot(t)))
            self.b.append(t_b)
            basis_0 = basis_1
            basis_1 = t / self.b[-1]
            # print(np.count_nonzero(basis_1))

        return self.b

    def get_eigen(self):
        self.eigen_vals, self.eigen_vectors = cp.linalg.eigh(
            cp.array(self.hamilton.toarray()))
        self.eigen_vals = np.array(self.eigen_vals.get())
        return self.eigen_vals, self.eigen_vectors

    def get_corr(self, T: np.ndarray):

        init_one = self.init_operator / \
            sqrt(self.self_inner_dot(self.init_operator))
        Y = self.eigen_vectors.T @ cp.array(init_one.toarray()
                                            ) @ self.eigen_vectors

        # Y[np.isclose(Y, 0, atol=1e-15)] = 0
        # Y = sp.csr_matrix(Y)
        # YT = sp.csr_matrix(Y.T)
        Y = abs(Y) ** 2

        # corr = np.array([(YT @ cp.diag(np.exp(1j*self.eigen_vals*i)) @ Y @ cp.diag(
        #     np.exp(-1j*self.eigen_vals*i))).trace().real.get() for i in T]) / 2**self.N
        # corr = np.array([(YT @ np.diag(np.exp(1j*self.eigen_vals*i)) @ Y @ np.diag(
        #     np.exp(-1j*self.eigen_vals*i))).trace().real for i in T]) / 2**self.N
        # corr = np.array([(YT @ sp.diags(np.exp(1j*self.eigen_vals*i), 0) @ Y @ sp.diags(
        #     np.exp(-1j*self.eigen_vals*i), 0)).diagonal().sum().real for i in T]) / 2**self.N

        # 二次型不比这快？！
        corr = []
        for i in T:
            x = cp.array(np.exp(1j*self.eigen_vals*i))
            corr.append(float((x @ Y @ x.conj().T).real))
        corr = np.array(corr) / 2**self.N

        return corr


def batch_run(n: int, t_list: list, C1=0, C2=1):
    x = KrylovCalculator(n)
    tt = time()
    x.get_hamilton(t_list, C1, C2)
    print(f'计算Hamilton耗时：{time() - tt}')

    res = []

    for i in (1, 2, 7):#range(1, n+1):
        print(f'm={i}')
        tt = time()
        x.get_init(i)
        x.lanczos()
        print(f'计算Basis耗时：{time() - tt}')
        print(x.b)
        print(f'长度：{len(x.b)}')
        res.append(x.b[:])

    with open(f'bn-n={n}-C2={C2}.csv', 'w') as f:
        for i in (0, 1, 2):#range(n):
            f.write(','.join(str(x) for x in ([i+1] + res[i])) + '\n')


def get_corr(T, n: int, t_list: list, C1=0, C2=1):
    x = KrylovCalculator(n)
    tt = time()
    x.get_hamilton(t_list, C1, C2)
    print(f'计算Hamilton耗时：{time() - tt}')
    tt = time()
    x.get_eigen()
    print(f'计算Eigen耗时：{time() - tt}')

    # res = []

    # for i in range(1, n+1):
    #     print(f'm={i}')
    #     tt = time()
    #     x.get_init(i)
    #     c = list(x.get_corr(T))
    #     print(f'计算Corr耗时：{time() - tt}')
    #     res.append(c)

    # with open(f'corr-n={n}-C2={C2}.csv', 'w') as f:
    #     for i in range(n):
    #         f.write(','.join(str(x) for x in ([i+1] + res[i])) + '\n')

    x.get_init(1)
    # T = np.linspace(0, 20, 200)

    plt.plot(T, x.get_corr(T))
    plt.show()


def main():
    from math import tanh

    n = 13
    j = 7
    C2 = 0
    t_list = [tanh(0.35*(x-j+0.5))/4/0.35*4.39 for x in range(1, n)]
    # t_list = [2] * (n-1)
    # t_list = [2.5/0.02*((x-0.5)*0.02)**2*(1-j/(x-0.5)) for x in range(1, n)]

    batch_run(n, t_list, C2=C2)

    # T = np.linspace(0, 6, 100)
    # get_corr(T, n, t_list, C2=C2)


if __name__ == '__main__':
    main()
