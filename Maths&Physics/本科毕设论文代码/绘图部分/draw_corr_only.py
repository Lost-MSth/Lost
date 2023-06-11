import matplotlib.pyplot as plt
import numpy as np


T = np.linspace(0, 6, 100)
C2 = [0, 0.1, 1, 10]


data = []

for i in C2:
    with open(f'./n=10不同C2-初始算符光滑/corr-n=10-C2={i}.csv', 'r') as f:
        data.append(f.readlines())


for i in range(len(data[0])):
    plt.figure()
    plt.xlabel('T')
    plt.ylabel('C(T)')


    for j in data:
        s = j[i].strip()
        l = s.split(',')
        b = list(map(float, l[1:]))
        plt.plot(T, b)

    plt.legend(C2)
    plt.savefig(f'./n=10不同C2-初始算符光滑/corr-n=10-m={i+1}.png', dpi=300)
