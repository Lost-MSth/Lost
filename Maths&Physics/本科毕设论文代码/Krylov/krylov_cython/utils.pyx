# 注意全程使用实数而不是复数，假设初始算符和哈密顿量都没有SY

from cython cimport boundscheck, wraparound
from cython.parallel import prange, parallel
from libc.stdlib cimport malloc

import numpy as np
cimport numpy as np

ctypedef np.float64_t FLOAT_T
FLOAT = np.float64


cdef Py_ssize_t *h_i
cdef Py_ssize_t *h_j
cdef FLOAT_T *h_v
cdef Py_ssize_t h_num


@boundscheck(False)
@wraparound(False)
cpdef FLOAT_T self_inner_dot(np.ndarray[FLOAT_T, ndim=2] a):
    cdef Py_ssize_t i, j, n = a.shape[0]
    cdef FLOAT_T[:, :] a_data = a
    cdef FLOAT_T s = 0
    for i in range(n):
        for j in range(n):
            s += a_data[i, j] ** 2
    return s


cpdef void translate_h(np.ndarray[FLOAT_T, ndim=2] h):
    cdef Py_ssize_t i, j, n = h.shape[0]
    cdef Py_ssize_t nonzero_num = np.count_nonzero(h)

    global h_i, h_j, h_v, h_num
    h_i = <Py_ssize_t *>malloc(nonzero_num * sizeof(Py_ssize_t))
    h_j = <Py_ssize_t *>malloc(nonzero_num * sizeof(Py_ssize_t))
    h_v = <FLOAT_T *>malloc(nonzero_num * sizeof(FLOAT_T))
    h_num = 0
    for i in range(n):
        for j in range(n):
            if h[i, j] != 0:
                h_i[h_num] = i
                h_j[h_num] = j
                h_v[h_num] = h[i, j]
                h_num += 1


@boundscheck(False)
@wraparound(False)
cpdef l_super(np.ndarray[FLOAT_T, ndim=2] a):
    cdef Py_ssize_t i, j, ii, jj, n = a.shape[0]
    cdef FLOAT_T[:, :] a_data = a
    cdef FLOAT_T[:, :] r = np.zeros((n, n), dtype=FLOAT)
    cdef FLOAT_T vv

    with nogil, parallel():
        for i in prange(h_num):
            ii = h_i[i]
            jj = h_j[i]
            vv = h_v[i]
            for j in range(n):
                r[ii, j] += a_data[jj, j] * vv
                r[j, jj] += - a_data[j, ii] * vv

    return np.array(r)
