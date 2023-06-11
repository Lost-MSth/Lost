import matplotlib.pyplot as plt
import numpy as np


T = np.linspace(0, 4, 100)
PRINT_LIST = (1, 2, 3)#list(range(1, 14))
C2 = [0, 0.1, 1, 10]


def get_corr(b: list):
    L = np.diag(b, 1) + np.diag(b, -1)

    eigval, S = np.linalg.eigh(L)

    # L_diag = np.diag(eigval)
    # L_diag = np.matmul(S.T, np.matmul(L, S))
    # print(L_diag)
    phi = [np.matmul(S, np.matmul(np.diag(np.exp(-1j*eigval*i)), np.linalg.inv(S)))
           @ np.array([1] + [0]*(len(eigval)-1)) for i in T]

    krylov = [np.sum(np.abs(i) ** 2 * np.array(list(range(len(eigval)))))
              for i in phi]

    return T, np.array(krylov)


data = []

for i in C2:
    with open(f'./n=13不同C2/100-bn-n=13-C2={i}.csv', 'r') as f:
        data.append(f.readlines())

for i in PRINT_LIST:
    fig, (ax1, ax2) = plt.subplots(1, 2)

    ax1.set_xlabel('n')
    ax1.set_ylabel('b_n')
    ax2.set_xlabel('T')
    ax2.set_ylabel('K(T)')

    X = list(range(1, len(data[0][0].strip().split(','))))
    r = []
    for j in data:
        s = j[i-1].strip()
        l = s.split(',')
        b = list(map(float, l[1:]))
        ax1.plot(X, b)
        T, K = get_corr(b[1:])
        ax2.plot(T, K)
        r.append(','.join([str(i) for i in K]) + '\n')

    with open(f'./n=13不同C2/100-Krylov-n=13-m={i}.csv', 'w+') as f:
        f.writelines(r)
        

    plt.legend(C2)
    plt.savefig(f'./n=13不同C2/100-Krylov-n=13-m={i}.png', dpi=300)
