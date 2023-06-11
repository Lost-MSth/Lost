from time import time
from cmath import isclose
from binascii import hexlify

class BitMap:
    __slots__ = ('_bitmap',)

    def __init__(self, b) -> None:
        self._bitmap = bytearray(b)

    @property
    def one(self) -> int:
        # 计算 bitmap 中 1 的个数 mod 2
        s = 0
        for i in self._bitmap:
            t = i
            while t:
                s ^= t & 1
                t >>= 1
        return s

    def __iter__(self):
        return iter(self._bitmap)

    def __str__(self) -> str:
        return ''.join([bin(x)[2:].rjust(8, '0') for x in self._bitmap])

    def __eq__(self, other: 'BitMap') -> bool:
        return self._bitmap == other._bitmap

    def __hash__(self) -> int:
        return hash(bytes(self._bitmap))

    def __xor__(self, other: 'BitMap') -> 'BitMap':
        return BitMap(a ^ b for a, b in zip(self._bitmap, other._bitmap))

    def __and__(self, other: 'BitMap') -> 'BitMap':
        return BitMap(a & b for a, b in zip(self._bitmap, other._bitmap))

    @property
    def is_all_zero(self) -> bool:
        return not any(self._bitmap)


class PauliString:
    __slots__ = ('_delta', '_epsilon', '_bitmap1', '_bitmap2')

    def __init__(self, d: int, e: int, b1: BitMap, b2: BitMap) -> None:
        self._delta: int = d
        self._epsilon: int = e
        self._bitmap1: BitMap = b1
        self._bitmap2: BitMap = b2

    def __matmul__(self, other: 'PauliString') -> 'PauliString':
        x = self._epsilon ^ other._epsilon ^ (self._delta & other._delta) ^ (
            self._bitmap1 & other._bitmap2).one
        return PauliString(self._delta ^ other._delta, x, self._bitmap1 ^ other._bitmap1, self._bitmap2 ^ other._bitmap2)

    @property
    def dagger(self) -> 'PauliString':
        return PauliString(self._delta, self._epsilon ^ (self._bitmap1 & self._bitmap2).one ^ self._delta, self._bitmap1, self._bitmap2)

    def __eq__(self, other: 'PauliString') -> bool:
        return self._delta == other._delta and self._epsilon == other._epsilon and self._bitmap1 == other._bitmap1 and self._bitmap2 == other._bitmap2

    def __hash__(self) -> int:
        return hash((self._delta, self._epsilon, self._bitmap1, self._bitmap2))

    def __str__(self) -> str:
        return f'{self._delta} {self._epsilon} {self._bitmap1} {self._bitmap2}'

    @property
    def trail(self) -> complex:
        # 注意有个常数 2**N
        if not self._bitmap1.is_all_zero or not self._bitmap2.is_all_zero:
            return 0
        t = 1
        if self._delta:
            t *= 1j
        if self._epsilon:
            t *= -1
        return t

    @property
    def bit(self):
        return hexlify(self._bitmap1._bitmap) + hexlify(self._bitmap2._bitmap)


class MultiPauliString:
    __slots__ = ('_pauli_strings', '_hash_dict')

    def __init__(self) -> None:
        self._pauli_strings: dict = {}
        self._hash_dict: dict = {}

    def calc_hash_dict(self):
        self._hash_dict = {}
        for k in self._pauli_strings.keys():
            x = k.bit
            if x not in self._hash_dict:
                self._hash_dict[x] = [k]
            else:
                self._hash_dict[x].append(k)

    def __iter__(self):
        return iter(self._pauli_strings)

    def __len__(self) -> int:
        return len(self._pauli_strings)

    def __str__(self) -> str:
        return ', '.join(f'{k}: {v}' for k, v in self._pauli_strings.items())

    def __getitem__(self, item: PauliString) -> float:
        return self._pauli_strings[item]

    def __setitem__(self, key: PauliString, value: float) -> None:
        self._pauli_strings[key] = value

    def __contains__(self, item: PauliString) -> bool:
        return item in self._pauli_strings

    def items(self):
        return self._pauli_strings.items()

    def clear_zero(self) -> 'MultiPauliString':
        self._pauli_strings = dict(filter(lambda x: not isclose(
            x[1], 0, abs_tol=1e-12), self._pauli_strings.items()))

        return self

    def __matmul__(self, other: 'MultiPauliString') -> 'MultiPauliString':
        new = MultiPauliString()
        for k1, v1 in self.items():
            for k2, v2 in other.items():
                k = k1 @ k2
                if k in new:
                    new[k] += v1 * v2
                else:
                    new[k] = v1 * v2
        return new.clear_zero()

    def __mul__(self, other: complex) -> 'MultiPauliString':
        new = MultiPauliString()
        for k, v in self.items():
            new[k] = v * other
        return new.clear_zero()

    def __rmul__(self, other: complex) -> 'MultiPauliString':
        return self * other

    def __truediv__(self, other: complex) -> 'MultiPauliString':
        return self * (1 / other)

    def __add__(self, other: 'MultiPauliString') -> 'MultiPauliString':
        new = MultiPauliString()
        for k, v in self.items():
            new[k] = v
        for k, v in other.items():
            if k in new:
                new[k] += v
            else:
                new[k] = v
        return new.clear_zero()

    def __sub__(self, other: 'MultiPauliString') -> 'MultiPauliString':
        new = MultiPauliString()
        for k, v in self.items():
            new[k] = v
        for k, v in other.items():
            if k in new:
                new[k] -= v
            else:
                new[k] = -v
        return new.clear_zero()

    @property
    def dagger(self) -> 'MultiPauliString':
        new = MultiPauliString()
        for k, v in self.items():
            new[k.dagger] = v
        return new

def l_super(a: MultiPauliString, h: MultiPauliString):
    # [H, .]
    #return h @ a - a @ h
    # 太慢了！
    tt = time()
    x = MultiPauliString()

    for k1, v1 in h.items():
        for k2, v2 in a.items():
            t1 = (k1._bitmap1 & k2._bitmap2).one
            t2 = (k1._bitmap2 & k2._bitmap1).one
            if t1 == t2:
                continue
            k = k1 @ k2
            if k in x:
                x[k] += 2 * (t1-t2) * v1 * v2 * (-1) ** t1
            else:
                x[k] = 2 * (t1-t2) * v1 * v2 * (-1) ** t1
    r = x.clear_zero()
    print(f'l_super cost time: {time() - tt}, ({len(a)}, {len(h)})')
    return r

def inner_dot(a: MultiPauliString, b: MultiPauliString) -> complex:
    # 无限温度下的内积
    tt = time()
    s = 0
    # 慢死了！
    # for k1, v1 in a.items():
    #     for k2, v2 in b.items():
    #         s += (k1.dagger @ k2).trail * v1 * v2
    a.calc_hash_dict()
    b.calc_hash_dict()
    for k1, v1 in a.items():
        for k2 in b._hash_dict.get(k1.bit, []):
            x = 1
            k1_epsilon = k1._epsilon ^ (k1._bitmap1 & k1._bitmap2).one ^ k1._delta

            d = k1._delta ^ k2._delta
            if d:
                x *= 1j
            e = k1_epsilon ^ k2._epsilon ^ (k1._delta & k2._delta) ^ (
                k1._bitmap1 & k2._bitmap2).one
            if e:
                x *= -1
            s += x * v1 * b[k2]

    print(f'内积 cost time: {time() - tt}, ({len(a)}, {len(b)})')
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
    num = (n-1) // 8 + 1
    a = [0] * num
    b = [0] * num

    if sigma_type == 1:
        b[(k-1) // 8] = 1 << 7 - (k-1) % 8
    elif sigma_type == 2:
        a[(k-1) // 8] = 1 << 7 - (k-1) % 8
    elif sigma_type == 3 or sigma_type == 4:
        a[(k-1) // 8] = 1 << 7 - (k-1) % 8
        b[(k-1) // 8] = 1 << 7 - (k-1) % 8

    if sigma_type == 3:
        r[PauliString(1, 1, BitMap(a), BitMap(b))] = 1
    else:
        r[PauliString(0, 0, BitMap(a), BitMap(b))] = 1
    return r
