from time import time
from cmath import isclose


def calc_one(x: int) -> int:
    s = 0
    while x:
        s ^= x & 1
        x >>= 1
    return s


class MultiPauliString:
    __slots__ = ('_data')

    def __init__(self) -> None:
        self._data: dict = {}


    def __len__(self) -> int:
        return len(self._data)


    def clear_zero(self) -> 'MultiPauliString':
        self._data = dict(filter(lambda x: not isclose(
            x[1], 0, abs_tol=1e-12), self._data.items()))

        return self

    def __matmul__(self, other: 'MultiPauliString') -> 'MultiPauliString':
        new = MultiPauliString()
        for k1, v1 in self._data.items():
            for k2, v2 in other._data.items():
                k = (k1[0] ^ k2[0], k1[1] ^ k2[1])
                v = v1 * v2
                if calc_one(k1[0] & k2[1]) == 1:
                    v *= -1
                new._data[k] = new._data.get(k, 0) + v

        return new.clear_zero()

    def __mul__(self, other: complex) -> 'MultiPauliString':
        new = MultiPauliString()
        for k, v in self._data.items():
            new._data[k] = v * other
        return new

    def __rmul__(self, other: complex) -> 'MultiPauliString':
        return self * other

    def __truediv__(self, other: complex) -> 'MultiPauliString':
        return self * (1 / other)

    def __add__(self, other: 'MultiPauliString') -> 'MultiPauliString':
        new = MultiPauliString()
        new._data = self._data.copy()
        for k, v in other._data.items():
            new._data[k] = new._data.get(k, 0) + v
        return new.clear_zero()

    def __sub__(self, other: 'MultiPauliString') -> 'MultiPauliString':
        new = MultiPauliString()
        new._data = self._data.copy()
        for k, v in other._data.items():
            new._data[k] = new._data.get(k, 0) - v
        return new.clear_zero()

    @property
    def dagger(self) -> 'MultiPauliString':
        new = MultiPauliString()
        new._data = self._data.copy()
        for k in self._data.keys():
            if calc_one(k[0] & k[1]) == 1:
                new._data[k] *= -1

        return new


def l_super(a: MultiPauliString, h: MultiPauliString):
    # [H, .]
    # return h @ a - a @ h
    # 太慢了！
    tt = time()
    x = MultiPauliString()

    for k1, v1 in h._data.items():
        for k2, v2 in a._data.items():
            t = calc_one(k1[0] & k2[1]) - calc_one(k1[1] & k2[0])
            if t == 0:
                continue
            k = (k1[0] ^ k2[0], k1[1] ^ k2[1])
            x._data[k] = x._data.get(k, 0) + 2 * t * v1 * v2

    r = x.clear_zero()
    print(f'l_super cost time: {time() - tt}, ({len(a)}, {len(h)})')
    return r


def norm(a: MultiPauliString) -> complex:
    # 模长平方和
    tt = time()
    s = 0
    for v in a._data.values():
        x = v * v.conjugate()
        s += x
    print(f'inner_dot cost time: {time() - tt}, ({len(a)})')
    return s


def get_sigma(k: int, n: int, sigma_type: int) -> MultiPauliString:
    '''
    共 n 个粒子，生成位置 (k - 1) % n + 1 的泡利算符

    `sigma_type`: 0 I, 1 X, 2 Z, 3 Y, 4 1j*Y, 5 +, 6 -
    '''
    k = (k - 1) % n + 1
    assert 0 <= sigma_type <= 6

    if sigma_type == 5:
        return (get_sigma(k, n, 1) + get_sigma(k, n, 4)) * 0.5
    elif sigma_type == 6:
        return (get_sigma(k, n, 1) - get_sigma(k, n, 4)) * 0.5

    r = MultiPauliString()
    a, b = 0, 0
    if sigma_type == 1:
        b = 1 << n - k
    elif sigma_type == 2:
        a = 1 << n - k
    elif sigma_type == 3 or sigma_type == 4:
        a = 1 << n - k
        b = 1 << n - k

    if sigma_type == 3:
        r._data[(a, b)] = -1j
    else:
        r._data[(a, b)] = 1
    return r
