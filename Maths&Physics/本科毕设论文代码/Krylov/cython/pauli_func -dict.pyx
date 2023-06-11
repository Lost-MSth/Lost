from time import time
from cmath import isclose
# from cython.parallel import prange, parallel
from cython import boundscheck, wraparound

from libc.stdlib cimport malloc, free


# DEF THREAD_NUM = 10

ctypedef struct PauliString:
    int k1
    int k2
    complex v

cdef int calc_one(int x) nogil:
    cdef int s = 0
    while x:
        s ^= x & 1
        x >>= 1
    return s

def dict_to_list(dict d):
    cdef int k1, k2
    cdef complex v2
    cdef dict v1
    for k1, v1 in d.items():
        for k2, v2 in v1.items():
            yield k1, k2, v2

cpdef dict dict_deep_copy(dict d):
    cdef dict x = {}
    cdef dict v1
    cdef int k1
    for k1, v1 in d.items():
        x[k1] = v1.copy()
    return x


cdef class MultiPauliString:

    cdef public dict _data

    def __init__(self):
        self._data = {}


    def __len__(self):
        return len(self._data)


    def clear_zero(self):
        cdef dict x = {}
        cdef dict i, t
        cdef int k
        for k, i in self._data.items():
            t = dict(filter(lambda x: not isclose(x[1], 0, abs_tol=1e-12), i.items()))
            if t:
                x[k] = t
        self._data = x

        return self

    def __matmul__(self, MultiPauliString other):
        cdef MultiPauliString x = MultiPauliString()
        cdef int k11, k12, k21, k22
        cdef complex v1, v2
        cdef dict xx, d1, d2
        for k11, d1 in self._data.items():
            for k21, d2 in other._data.items():
                xx = x._data.setdefault(k11 ^ k21, {})
                for k12, v1 in d1.items():
                    for k22, v2 in d2.items():
                        v = v1 * v2
                        if calc_one(k11 & k22) == 1:
                            v *= -1
                        kk = k12 ^ k22
                        xx[kk] = xx.get(kk, 0) + v
        return x.clear_zero()

    def __mul__(self, complex other):
        cdef MultiPauliString x = MultiPauliString()
        for k1, v1 in self._data.items():
            xx = x._data.setdefault(k1, {})
            for k2, v2 in v1.items():
                xx[k2] = v2 * other
        return x

    # def __rmul__(self, complex other):
    #     return self * other

    def __truediv__(self, complex other):
        return self * (1 / other)

    def __add__(self, MultiPauliString other):
        cdef MultiPauliString x = MultiPauliString()
        x._data = dict_deep_copy(self._data)
        for k1, v1 in other._data.items():
            xx = x._data.setdefault(k1, {})
            for k2, v2 in v1.items():
                xx[k2] = xx.get(k2, 0) + v2
        return x.clear_zero()

    def __sub__(self, MultiPauliString other):
        cdef MultiPauliString x = MultiPauliString()
        x._data = dict_deep_copy(self._data)
        for k1, v1 in other._data.items():
            xx = x._data.setdefault(k1, {})
            for k2, v2 in v1.items():
                xx[k2] = xx.get(k2, 0) - v2
        return x.clear_zero()

    @property
    def dagger(self):
        cdef MultiPauliString x = MultiPauliString()
        x._data = dict_deep_copy(self._data)
        for k1, v1 in self._data.items():
            for k2 in v1.keys():
                if calc_one(k1 & k2) == 1:
                    x._data[k1][k2] *= -1

        return x


@boundscheck(False)
@wraparound(False)
def l_super(MultiPauliString a, MultiPauliString h):
    # [H, .]
    # return h @ a - a @ h
    # 太慢了！
    tt = time()
    cdef MultiPauliString x = MultiPauliString()
    cdef int k1, k2
    cdef complex v1
    cdef int t, k11, k12, k21, k22
    cdef PauliString *hh
    cdef PauliString *aa
    # cdef PauliString *rr
    # cdef int *rr_num
    cdef Py_ssize_t i, j, n, m
    cdef dict xx

    h_list = list(dict_to_list(h._data))
    a_list = list(dict_to_list(a._data))
    n = len(h_list)
    m = len(a_list)
    hh = <PauliString *> malloc(n * sizeof(PauliString))
    aa = <PauliString *> malloc(m * sizeof(PauliString))
    # rr = <PauliString *> malloc(nm * sizeof(PauliString))
    # rr_num = <int *> malloc(n * sizeof(int))
    if not hh or not aa:
        raise MemoryError()
    for i in range(n):
        k1, k2, v1 = h_list[i]
        hh[i].k1 = k1
        hh[i].k2 = k2
        hh[i].v = v1
    for i in range(m):
        k1, k2, v1 = a_list[i]
        aa[i].k1 = k1
        aa[i].k2 = k2
        aa[i].v = v1

    del h_list, a_list

    print(f'copy cost time: {time() - tt}')
    tt = time()

    for i in range(n):
        k11 = hh[i].k1
        k12 = hh[i].k2
        v1 = hh[i].v
        for j in range(m):
            k21 = aa[j].k1
            k22 = aa[j].k2
            t = calc_one(k11 & k22) - calc_one(k12 & k21)
            if t == 0:
                continue
            # ii = rr_num[i] + i * m
            xx = x._data.setdefault(k11 ^ k21, {})
            k2 = k12 ^ k22
            xx[k2] = xx.get(k2, 0) + 2 * t * v1 * aa[j].v
            #x._data[k] = x._data.get(k, 0) + 2 * t * v1 * aa[j].v
    print(f'calc cost time: {time() - tt}')
    tt = time()

    free(<void *> hh)
    free(<void *> aa)
    # for i in range(n):
    #     ii = i * m
    #     for j in range(rr_num[i]):
    #         jj = ii + j
    #         k2 = rr[jj].k2
    #         xx = x._data.setdefault(rr[jj].k1, {})
    #         xx[k2] = xx.get(k2, 0) + rr[jj].v

    # free(<void *> rr)
    # free(<void *> rr_num)


    # for k1, v1 in h._data.items():
    #     for k2, v2 in a._data.items():
    #         t = calc_one(k1[0] & k2[1]) - calc_one(k1[1] & k2[0])
    #         if t == 0:
    #             continue
    #         k = (k1[0] ^ k2[0], k1[1] ^ k2[1])
    #         x._data[k] = x._data.get(k, 0) + 2 * t * v1 * v2

    # print(f'to_dict cost time: {time() - tt}')
    # tt = time()
    r = x.clear_zero()
    print(f'l_super cost time: {time() - tt}, ({n}, {m})')
    return r


@boundscheck(False)
@wraparound(False)
def norm(MultiPauliString a):
    # 模长平方和
    # tt = time()
    cdef complex s = 0
    cdef complex x, v2
    cdef dict v
    for v in a._data.values():
        for v2 in v.values():
            x = v2 * v2.conjugate()
            s += x

    # print(f'inner_dot cost time: {time() - tt}, ({len(a)})')
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
    
    r._data.setdefault(a, {})[b] = -1j if sigma_type == 3 else 1
    return r
