#cython: language=c++
#cython: language_level=3

from time import time
from cmath import isclose
# from cython.parallel import prange, parallel
from cython import boundscheck, wraparound
from cython.operator cimport preincrement as inc, dereference as deref

from libc.stdlib cimport malloc, free
from libcpp.unordered_map cimport unordered_map


# DEF THREAD_NUM = 10

ctypedef unordered_map[int, complex] ic_dict

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

# def dict_to_list(dict d):
#     cdef int k1, k2
#     cdef complex v2
#     cdef dict v1
#     for k1, v1 in d.items():
#         for k2, v2 in v1.items():
#             yield k1, k2, v2

# cpdef dict deep_copy(dict d):
#     cdef dict x = {}
#     cdef dict v1
#     cdef int k1
#     for k1, v1 in d.items():
#         x[k1] = v1.copy()
#     return x


cdef class MultiPauliString:

    cdef ic_dict **_data
    cdef public Py_ssize_t _len
    cdef public int _n

    def __cinit__(self, n: int):
        self._n = n
        self._len = 2**n
        self._data = <ic_dict **> malloc(self._len * sizeof(ic_dict *))
        if self._data == NULL:
            raise MemoryError()

        cdef Py_ssize_t i
        for i in range(self._len):
            self._data[i] = new ic_dict()

    def __dealloc__(self):
        cdef Py_ssize_t i
        if self._data != NULL:
            for i in range(self._len):
                del self._data[i]
            free(self._data)

    cpdef complex get_data(self, int i, int k) except +:
        return self._data[i][0][k]
    
    cpdef void set_data(self, int i, int k, complex v) except +:
        self._data[i][0][k] = v

    # cpdef list get_keys(self, int i) except +:
    #     return list([x.first for x in self._data[i][0]])

    def __len__(self):
        cdef int s = 0
        cdef Py_ssize_t i
        for i in range(self._len):
            s += self._data[i].size()
        return s

    @property
    def data(self):
        return list([dict(self._data[i][0]) for i in range(self._len)])

    def clear_zero(self):
        cdef ic_dict *x
        cdef Py_ssize_t i

        cdef unordered_map[int, complex].iterator j, e

        for i in range(self._len):
            x = self._data[i]
            j = x.begin()
            e = x.end()

            while j != e:
                # print(f'{deref(j).first}-{deref(j).second}')
                if isclose(deref(j).second, 0, abs_tol=1e-12):
                    j = x.erase(j)
                else:
                    inc(j)

        return self

    def __matmul__(MultiPauliString self, MultiPauliString other):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef int k11, k21, k22, kk
        cdef complex v
        cdef ic_dict *x
        cdef ic_dict *y
        cdef ic_dict *z

        for k11 in range(self._len):
            x = self._data[k11]
            if x.empty():
                continue
            for k21 in range(other._len):
                y = other._data[k21]
                if y.empty():
                    continue

                z = r._data[k11 ^ k21]
                for i in deref(x):
                    for j in deref(y):
                        k22 = j.first
                        v = i.second * j.second
                        if calc_one(k11 & k22) == 1:
                            v *= -1
                        kk = i.first ^ k22
                        deref(z)[kk] = deref(z)[kk] + v

        return r.clear_zero()

    def __mul__(MultiPauliString self, complex other):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef Py_ssize_t i
        cdef ic_dict *x
        cdef ic_dict *y
        for i in range(self._len):
            x = self._data[i]
            y = r._data[i]
            for j in deref(x):
                deref(y)[j.first] = j.second * other
        return r

    def __rmul__(self, complex other):
        return self * other

    def __truediv__(self, complex other):
        return self * (1 / other)

    def __add__(MultiPauliString self, MultiPauliString other):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef Py_ssize_t i
        cdef ic_dict *x
        for i in range(other._len):
            x = r._data[i]
            x[0] = deref(self._data[i])
            for j in deref(other._data[i]):
                deref(x)[j.first] = deref(x)[j.first] + j.second
        return r.clear_zero()

    def __sub__(MultiPauliString self, MultiPauliString other):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef Py_ssize_t i
        cdef ic_dict *x
        for i in range(other._len):
            x = r._data[i]
            x[0] = deref(self._data[i])
            for j in deref(other._data[i]):
                deref(x)[j.first] = deref(x)[j.first] - j.second
        return r.clear_zero()

    @property
    def dagger(MultiPauliString self):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef int i
        cdef ic_dict *x
        cdef ic_dict *y
        for i in range(self._len):
            x = r._data[i]
            y = self._data[i]
            x[0] = deref(y)
            for j in deref(y):
                if calc_one(i & j.first) == 1:
                    deref(x)[j.first] = - j.second

        return r


@boundscheck(False)
@wraparound(False)
def l_super(MultiPauliString a, MultiPauliString h):
    # [H, .]
    # return h @ a - a @ h

    cdef MultiPauliString r = MultiPauliString(a._n)
    cdef ic_dict *aa
    cdef ic_dict *rr
    cdef ic_dict *hh
    cdef complex v1
    cdef int kk, k11, k12, k21, k22

    tt = time()

    for k11 in range(h._len):
        hh = h._data[k11]
        if hh.empty():
            continue
        for k1 in deref(hh):
            k12 = k1.first
            v1 = k1.second
            for k21 in range(a._len):
                aa = a._data[k21]
                if aa.empty():
                    continue
                for k2 in deref(aa):
                    k22 = k2.first
                    t = calc_one(k11 & k22) - calc_one(k12 & k21)
                    if t == 0:
                        continue
                    rr = r._data[k11 ^ k21]
                    kk = k12 ^ k22
                    deref(rr)[kk] = deref(rr)[kk] + 2 * t * v1 * k2.second



    print(f'calc cost time: {time() - tt}')
    tt = time()

    r = r.clear_zero()
    print(f'l_super cost time: {time() - tt}, ({len(h)}, {len(a)})')
    return r


@boundscheck(False)
@wraparound(False)
def norm(MultiPauliString a):
    # 模长平方和
    tt = time()
    cdef complex s = 0
    cdef complex v
    cdef ic_dict *x
    cdef Py_ssize_t i

    for i in range(a._len):
        x = a._data[i]
        for j in deref(x):
            v = j.second
            s += v * v.conjugate()

    print(f'inner_dot cost time: {time() - tt}, ({len(a)})')
    return s


cpdef MultiPauliString get_sigma(int k, int n, int sigma_type):
    '''
    共 n 个粒子，生成位置 (k - 1) % n + 1 的泡利算符

    `sigma_type`: 0 I, 1 X, 2 Z, 3 Y, 4 1j*Y, 5 +, 6 -
    '''
    cdef int a, b
    k = (k - 1) % n + 1
    assert 0 <= sigma_type <= 6

    if sigma_type == 5:
        return (get_sigma(k, n, 1) + get_sigma(k, n, 4)) * 0.5
    elif sigma_type == 6:
        return (get_sigma(k, n, 1) - get_sigma(k, n, 4)) * 0.5

    cdef MultiPauliString r = MultiPauliString(n)
    a, b = 0, 0
    if sigma_type == 1:
        b = 1 << n - k
    elif sigma_type == 2:
        a = 1 << n - k
    elif sigma_type == 3 or sigma_type == 4:
        a = 1 << n - k
        b = 1 << n - k

    deref(r._data[a])[b] = -1j if sigma_type == 3 else 1
    return r
