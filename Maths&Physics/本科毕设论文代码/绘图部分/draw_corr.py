import matplotlib.pyplot as plt
import numpy as np


T = np.linspace(0, 6, 100)
PRINT_LIST = list(range(1, 11))
C2 = [0, 0.1, 1, 10]


def get_corr(b: list):
    L = np.diag(b, 1) + np.diag(b, -1)

    eigval, S = np.linalg.eigh(L)

    # L_diag = np.diag(eigval)
    # L_diag = np.matmul(S.T, np.matmul(L, S))
    # print(L_diag)

    corr = [np.matmul(S, np.matmul(
        np.diag(np.exp(-1j*eigval*i)), np.linalg.inv(S)))[0, 0] for i in T]

    return T, np.real(corr)


data = []

for i in C2:
    with open(f'./n=10不同C2-初始算符光滑/bn-n=10-C2={i}.csv', 'r') as f:
        data.append(f.readlines())


for i in PRINT_LIST:
    fig, (ax1, ax2) = plt.subplots(1, 2)

    ax1.set_xlabel('n')
    ax1.set_ylabel('b_n')
    ax2.set_xlabel('T')
    ax2.set_ylabel('C(T)')

    X = list(range(1, len(data[0][0].strip().split(','))))

    for j in data:
        s = j[i-1].strip()
        l = s.split(',')
        b = list(map(float, l[1:]))
        ax1.plot(X, b)
        ax2.plot(*get_corr(b[1:]))

    plt.legend(C2)
    plt.savefig(f'./n=10不同C2-初始算符光滑/n=10-m={i}.png', dpi=300)
