#cython: language=c++
#cython: language_level=3

from time import time
# from cmath import isclose

from cython import boundscheck, wraparound
from cython.parallel import prange #, parallel
from cython.operator cimport preincrement as inc, dereference as deref

from libc.stdlib cimport malloc, free
# from libcpp.unordered_map cimport unordered_map, pair
from parallel_hashmap cimport parallel_flat_hash_map as unordered_map, pair, mutex


DEF MUTEX_NUM = 8192
DEF TOL = 1e-12

ctypedef unordered_map[int, complex] ic_dict
ctypedef pair[int, complex] ic_pair

ctypedef struct PauliString:
    int k1
    int k2
    complex v

cdef mutex mutexes[MUTEX_NUM]  # type: ignore

cdef int calc_one(int x) nogil:
    cdef int s = 0
    while x:
        s ^= x & 1
        x >>= 1
    return s


cdef class MultiPauliString:

    cdef ic_dict **_data
    cdef public Py_ssize_t _len
    cdef public int _n

    def __cinit__(self, n: int):
        self._n = n
        self._len = 2**n
        self._data = <ic_dict **> malloc(self._len * sizeof(ic_dict *))  # type: ignore
        if self._data == NULL:
            raise MemoryError()

        cdef Py_ssize_t i
        with nogil:
            for i in prange(self._len):
                self._data[i] = new ic_dict()

    def __dealloc__(self):
        cdef Py_ssize_t i
        if self._data != NULL:
            with nogil:
                for i in prange(self._len):
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
        with nogil:
            for i in prange(self._len):
                s += self._data[i].size()
        return s

    # @property
    # def data(self):
    #     return list([dict(self._data[i][0]) for i in range(self._len)])

    def clear_zero(self):
        cdef ic_dict *x
        cdef Py_ssize_t i
        cdef complex v

        cdef unordered_map[int, complex].iterator j, e

        with nogil:
            for i in prange(self._len):
                x = self._data[i]
                j = x.begin()
                e = x.end()

                while j != e:
                    # print(f'{deref(j).first}-{deref(j).second}')
                    v = deref(j).second
                    if -TOL < v.real < TOL and -TOL < v.imag < TOL:
                    # if isclose(deref(j).second, 0, abs_tol=1e-12):
                        j = x.erase(j)
                    else:
                        inc(j)

        return self

    def __matmul__(MultiPauliString self, MultiPauliString other):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef int k11, k21, k22, kk2, mutex_idx, kk1
        # cdef complex v
        cdef ic_dict *x
        cdef ic_dict *y
        cdef ic_dict *z
        cdef ic_pair i, j

        with nogil:
            for k11 in prange(self._len):
                x = self._data[k11]
                if x.empty():
                    continue
                for k21 in range(other._len):
                    y = other._data[k21]
                    if y.empty():
                        continue

                    kk1 = k11 ^ k21
                    z = r._data[kk1]
                    mutex_idx = kk1 % MUTEX_NUM
                    mutexes[mutex_idx].lock()
                    for i in deref(x):
                        for j in deref(y):
                            k22 = j.first
                            kk2 = i.first ^ k22
                            if calc_one(k11 & k22) == 1:
                                deref(z)[kk2] = deref(z)[kk2] - i.second * j.second
                            else:
                                deref(z)[kk2] = deref(z)[kk2] + i.second * j.second
                    mutexes[mutex_idx].unlock()

        return r.clear_zero()

    def __mul__(MultiPauliString self, complex other):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef Py_ssize_t i
        cdef ic_dict *x
        cdef ic_dict *y
        cdef ic_pair j
        with nogil:
            for i in prange(self._len):
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
        cdef ic_pair j
        with nogil:
            for i in prange(other._len):
                x = r._data[i]
                x[0] = deref(self._data[i])
                for j in deref(other._data[i]):
                    deref(x)[j.first] = deref(x)[j.first] + j.second
        return r.clear_zero()

    def __sub__(MultiPauliString self, MultiPauliString other):
        cdef MultiPauliString r = MultiPauliString(self._n)
        cdef Py_ssize_t i
        cdef ic_dict *x
        cdef ic_pair j
        with nogil:
            for i in prange(other._len):
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
        cdef ic_pair j
        with nogil:
            for i in prange(self._len):
                x = r._data[i]
                y = self._data[i]
                x[0] = deref(y)
                for j in deref(y):
                    if calc_one(i & j.first) == 1:
                        deref(x)[j.first] = - j.second

        return r


cdef class SparseMultiPauliString:
    # 处理Hamilton量
    cdef PauliString *_data
    cdef public Py_ssize_t _len
    cdef public int _n

    def __cinit__(self, n: int):
        self._n = n
        self._len = 0
        self._data = NULL

    def __dealloc__(self):
        if self._data != NULL:
            free(self._data)

    def __len__(self):
        return self._len

    @classmethod
    def from_data(cls, MultiPauliString a):
        cdef Py_ssize_t i, j
        cdef ic_dict *x
        cdef SparseMultiPauliString r = SparseMultiPauliString(a._n)
        cdef ic_pair k

        r._len = len(a)
        r._data = <PauliString *> malloc(r._len * sizeof(PauliString))
        if r._data == NULL:
            raise MemoryError()

        j = 0
        with nogil:
            for i in range(a._len):
                x = a._data[i]
                if x.empty():
                    continue
                for k in deref(x):
                    r._data[j].k1 = i
                    r._data[j].k2 = k.first
                    r._data[j].v = k.second
                    j += 1
        return r


@boundscheck(False)
@wraparound(False)
def l_super(MultiPauliString a, SparseMultiPauliString h):
    # [H, .]
    # return h @ a - a @ h

    cdef MultiPauliString r = MultiPauliString(a._n)
    cdef ic_dict *aa
    cdef ic_dict *rr
    cdef PauliString p
    cdef Py_ssize_t i
    cdef int kk1, kk2, k11, k12, k21, k22, t, mutex_idx
    cdef ic_pair k2

    tt = time()

    with nogil:
        for i in prange(h._len):
            p = h._data[i]
            k11 = p.k1
            k12 = p.k2
            for k21 in range(a._len):
                aa = a._data[k21]
                if aa.empty():
                    continue
                for k2 in deref(aa):
                    k22 = k2.first
                    t = calc_one(k11 & k22) - calc_one(k12 & k21)
                    if t == 0:
                        continue
                    kk1 = k11 ^ k21
                    kk2 = k12 ^ k22
                    rr = r._data[kk1]
                    mutex_idx = kk1 % MUTEX_NUM
                    mutexes[mutex_idx].lock()
                    deref(rr)[kk2] = deref(rr)[kk2] + 2 * t * p.v * k2.second
                    mutexes[mutex_idx].unlock()


    print(f'calc cost time: {time() - tt}')
    tt = time()

    r = r.clear_zero()
    print(f'clear_zero cost time: {time() - tt}')
    # print(f'l_super cost time: {time() - tt}, ({len(h)}, {len(a)})')
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
    cdef ic_pair j
    with nogil:
        for i in range(a._len):
            x = a._data[i]
            for j in deref(x):
                v = j.second
                s += v * v.conjugate()

    print(f'norm cost time: {time() - tt}')
    # print(f'inner_dot cost time: {time() - tt}, ({len(a)})')
    return s


# def test_mutex(int n):
#     cdef int i, j
#     cdef int s[16]
#     with nogil:
#         for i in range(16):
#             s[i] = 0
#         for i in prange(n):
#             for j in range(16):
#                 mutexes[j % MUTEX_NUM].lock()
#                 s[j] = s[j] + 1
#                 mutexes[j % MUTEX_NUM].unlock()

#     return list(s)


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
