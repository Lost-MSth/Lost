# 本科毕设论文代码

> 论文标题：量子多体模型的 Krylov 复杂度研究

请参考 [论文草稿](https://lost-msth.github.io/2023/06/11/krylov复杂度-量子模拟.html) 和 [数值计算优化](https://lost-msth.github.io/2023/03/14/cython-dict-parallel.html) 食用

有一说一，乱七八糟的，我自己都记不得这些东东是干啥用的了（

首先得说，这是 Python 和 Cython 代码混合的，有的也用了 CUDA 加速（需要相关依赖）

Cython 主要是为了实现 Pauli String 的算法核心，其中调用的 parallel_hashmap 这个第三方库，也一起打包进去了，懒得找官方文档和首页了

Cython 使用 `makefile` 手动编译，实在不行就把里面的命令拿出来手动运行也行，不用 `setup.py` 是因为在我电脑上会报错，无法调用 gcc / g++ (MingGW) 而是用了 `cl.exe`

## Krylov

有用的部分（大概）：

- `cython` 文件夹：这是 Pauli String 的算法核心和用这个算法来进行 Lanczos 迭代计算的实现，parallel_hashmap 如果换成自带的 `unordered_map`，会稍微慢一点
- `corr_calc.py`：对 Lanczos 系数对角化来计算自关联函数的算法实现
- `Ising.py`：Ising 模型的 Lanczos 系数计算
- `Hubbard.py`：带次近邻项的 Hubbard 模型的 Lanczos 系数计算
- `krylov_cython/Krylov.py`：密集矩阵算法（numpy 或者 cupy） / 稀疏矩阵算法下 Lanczos 系数以及自关联函数（基于哈密顿量严格对角化）的计算，实际上同文件夹中其它文件并未用到（用 Cython 加速效果不明显，远远比不过 CUDA 加速，所以没用）

其它文件似乎是早期的尝试，包括完全正交化算法 / 部分正交化算法的 Lanczos 迭代算法实现（`Krylov.py`）、纯 Python dict 的 Pauli String 算法实现（`pauli.py`，慢了一点；`pauli copy.py` 没用正整数用了字符串表示，超级慢；`pauli_krylov.py` 是用了二者的 Lanczos 算法实现）、Cython 版本的 Lanczos 迭代算法实现（`utils.pyx`，速度远远不如稀疏矩阵优化和 CUDA 加速）、一些测试文件……

## 绘图部分

真的只是画图用的，自关联函数、Krylov 复杂度、Lanczos 系数的作图脚本
