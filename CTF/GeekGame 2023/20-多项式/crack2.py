import math
from itertools import dropwhile
import numpy as np
from functools import wraps
#from sympy import ntt, intt
from sympy.utilities.iterables import ibin
from sympy.ntheory import primitive_root
import time
from Crypto.Util.number import inverse as get_inv


def ntt(seq, p, inverse=False):
    """Utility function for the Number Theoretic Transform"""

    a = [int(x) % p for x in seq]

    n = len(a)
    if n < 1:
        return a

    b = n.bit_length() - 1
    if n & (n - 1):
        b += 1
        n = 2**b

    if (p - 1) % n:
        raise ValueError("Expected prime modulus of the form (m*2**k + 1)")

    a += [0]*(n - len(a))
    for i in range(1, n):
        j = int(ibin(i, b, str=True)[::-1], 2)
        if i < j:
            a[i], a[j] = a[j], a[i]

    pr = primitive_root(p)
    print(pr)

    rt = pow(pr, (p - 1) // n, p)
    print(rt)
    rt = pow(pr, 3808, p)
    print(rt)
    # if inverse:
    #     rt = pow(rt, p - 2, p)

    w = [0]*(n // 2)
    w[0] = 1
    for i in range(17, n // 2):
        w[i] = w[i - 1]*rt % p

    for i in range(15, 0, -1):
        w[i] = w[i * 2]

    print(w)

    if inverse:
        w2 = [1]*(n // 2)
        for i in range(n//2):
            w2[i] = get_inv(w[i], p)

        # for x, y in zip(w2, w):
        #     print((x * y) % p)

        w = w2
        print(w)

    h = 2
    while h <= n:
        hf, ut = n // h, h // 2
        for i in range(0, n, h):
            for j in range(hf):
                u, v = a[i + j], a[i + j + hf]*w[ut * j]
                a[i + j], a[i + j + hf] = (u + v) % p, (u - v) % p
        h *= 2

    if inverse:
        rv = pow(n, p - 2, p)
        a = [x*rv % p for x in a]

    return a


N = 0x3b800001

D = [0x00000F49, 0x00000121, 0x31C44DFF, 0x09BBB244, 0x09CD2637, 0x099E9344, 0x3A1174D9, 0x2982CE42, 0x202A3E59, 0x3AD2F444, 0x0655DAC3, 0x181AE6C1, 0x2FFCF1EE, 0x0AAE9419, 0x2016E6F4, 0x19CF9F98, 0x2DEA04C3, 0x089262F4, 0x18327C16, 0x373BD1D9, 0x0938E62A, 0x36B7868B, 0x3813BCFE, 0x0D213F8D, 0x07E67F22, 0x038FCD76, 0x32A17A7E, 0x2386EE67, 0x382D9FD7, 0x2FA45664, 0x04CFE37E, 0x02AF595C,
     0x2103E392, 0x1536B2BA, 0x1C46D639, 0x0B170DEB, 0x2104AB3D, 0x334666E4, 0x0D52FFE1, 0x144A6446, 0x242BCC46, 0x37BF7317, 0x03A97D9A, 0x3B329D1A, 0x0724F983, 0x1ED8A93E, 0x25E09BB8, 0x18121D9E, 0x2E301013, 0x105E3542, 0x375ADF03, 0x051674FE, 0x2AC2758E, 0x352291E2, 0x375D7604, 0x338E6B2A, 0x0C8EB7EB, 0x2F5350DC, 0x20E81988, 0x35F5C18E, 0x08753392, 0x0CD0ACE9, 0x17DF5455, 0x1B91C2B0]

print(len(D))

out = ntt(D, N, True)
out = [int(i) % N for i in out]

# A = b'flag{12asdfasfawefawfeaw35465as4df56as4f5wae}' + b'\x00' * (64-45)
# AD = [i for i in A]
# AD = ntt(AD, N)
# print(AD)

print(len(out))
print(out)
