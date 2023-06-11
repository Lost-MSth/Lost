import matplotlib.pyplot as plt
import numpy as np


T = np.linspace(0, 6, 100)
PRINT_LIST = [1]  # [1, 3, 4, 6, 9, 10]


def get_corr(b: list):
    L = np.diag(b, 1) + np.diag(b, -1)

    eigval, S = np.linalg.eigh(L)

    # L_diag = np.diag(eigval)
    # L_diag = np.matmul(S.T, np.matmul(L, S))
    # print(L_diag)

    corr = [np.matmul(S, np.matmul(
        np.diag(np.exp(-1j*eigval*i)), np.linalg.inv(S)))[0, 0] for i in T]

    # phi = [np.matmul(S, np.matmul(np.diag(np.exp(-1j*eigval*i)), np.linalg.inv(S)))
    #        @ np.array([1] + [0]*(len(eigval)-1)) for i in T]

    # krylov = [np.sum(np.abs(i) ** 2 * np.array(list(range(len(eigval)))))
    #           for i in phi]
    # phi_end = [np.abs(i[29]) for i in phi]
    # plt.figure()
    # plt.plot(T, phi_end)
    # plt.show()

    return T, np.real(corr)

a = get_corr([4.3418276859636595,5.327451257299319,5.500765271837599,5.622948005865118,5.553892619516275,5.500967067112077,5.382764869677279,5.596627044662548,6.789041904943779,9.122363401055049,9.112127472723243,8.335535302400782,9.516864906103887,9.285364915221809,8.120331048861761,9.708530632255956,9.257303117312548,9.769796241210477,12.545918752347951,11.249700434816987,10.471439072567447,10.008026908014205,7.789622367725553,11.19346208270479,9.971536620679633,13.51571530163788,13.109600089243427,14.451000409720926,14.96666417620003])

plt.plot(*a)
plt.show()

# with open('bn-n=10-C2=0.csv', 'r') as f:
#     data = f.readlines()


# fig, (ax1, ax2) = plt.subplots(1, 2)

# ax1.set_xlabel('n')
# ax1.set_ylabel('b_n')
# ax2.set_xlabel('T')
# ax2.set_ylabel('C(T)')

# legend = []
# X = list(range(1, len(data[0].strip().split(','))))

# for i in data:
#     s = i.strip()
#     l = s.split(',')
#     if PRINT_LIST and int(l[0]) not in PRINT_LIST:
#         continue
#     legend.append(l[0])
#     b = list(map(float, l[1:]))
#     ax1.plot(X, b)
#     ax2.plot(*get_corr(b[1:]))

# plt.legend(legend)
# plt.show()
