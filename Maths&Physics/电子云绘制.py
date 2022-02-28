'''
电子云绘制


requirements.txt:
vtk==8.1.2
numpy
scipy
mayavi


README:
运行后依次输入n, l, m即可
使用随机数判断，画图时间较长，一般会在一分钟以内，当对称性过好时可能会花费大量时间，比如n=4, l=0, m=0的情况，大概要好几分钟
需要随n调整散点球的大小，不然看不清，可能需要调整其它参数以获得更好的效果
空间尺度是相对的

by Lost
no license
'''

import numpy as np
from scipy.special import sph_harm
from scipy.special import assoc_laguerre
from mayavi import mlab
import random


def flatten(lst: list) -> list:
    result = []
    def fly(lst):
        for item in lst:
            if isinstance(item, list):
                fly(item)
            else:
                result.append(item)

    fly(lst)
    return result


def calc(x, y, z):
    rho = np.linalg.norm((x,y,z), axis=0) / n
    Lag = assoc_laguerre(2 * rho, n - l - 1, 2 * l + 1)
    Ylm  = sph_harm(m, l, np.arctan2(y, x), np.arctan2(np.linalg.norm((x,y), axis=0), z))
    Psi = np.exp(-rho) * np.power((2*rho), l) * Lag * Ylm
    density = np.conjugate(Psi) * Psi
    return density.real


n = float(input("Enter n: Note that n should > 0 \n"))
l = float(input("Enter l: Note that l should in [0, n-1] \n"))
m = float(input("Enter m: Note that m should in [-l, l] \n"))



C = 10000  # 散点数
scale_factor = 0.2  # 散点球的大小


length = n**2*2  # 计算范围
N = 157  # 归一化尝试的分割份数
r = np.linspace(-length, length, N).tolist()
x = np.array(flatten([[i] * N**2 for i in r]))
y = np.array(flatten([i] * N for i in r * N))
z = np.array(flatten(r * N**2))


density = calc(x, y, z)
max_density = density.max()


k = 0
x_plot = []
y_plot = []
z_plot = []
density_plot = []
while k < C:
    t = [random.uniform(-length, length) for _ in range(3)]
    ran = random.random()
    density_calc = calc(t[0], t[1], t[2])
    
    if density_calc > ran * max_density:
        x_plot.append(t[0])
        y_plot.append(t[1])
        z_plot.append(t[2])
        density_plot.append(density_calc / max_density)
        k += 1

print('OK! Start to plot...')

# Plot scatter with mayavi
figure = mlab.figure('DensityPlot: ' + 'n=' + str(n) + ', l=' + str(l) + ',m=' + str(m))
pts = mlab.points3d(x_plot, y_plot, z_plot, density_plot, scale_mode='none', scale_factor=scale_factor)
mlab.axes()
mlab.show()
