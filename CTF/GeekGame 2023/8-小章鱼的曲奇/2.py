import struct
from randcrack import RandCrack
from random import Random, SystemRandom
from random import randint


# from gmpy2 import invert


# def _int32(x):
#     return int(0xFFFFFFFF & x)


# def init(seed):
#     mt = [0] * 624
#     mt[0] = seed
#     for i in range(1, 624):
#         mt[i] = _int32(1812433253 * (mt[i - 1] ^ mt[i - 1] >> 30) + i)
#     return mt


# def invert_right(res, shift):
#     tmp = res
#     for i in range(32//shift):
#         res = tmp ^ res >> shift
#     return _int32(res)


# def recover(last):
#     n = 1 << 32
#     inv = invert(1812433253, n)
#     for i in range(623, 0, -1):
#         last = ((last-i)*inv) % n
#         last = invert_right(last, 30)
#     return last


# seed = 2080737669


# def f(x): return x ^ x >> 30

# def twist(mt):
#     a = [i for i in mt]
#     for i in range(0, 624):
#         y = _int32((a[i] & 0x80000000) + (a[(i + 1) % 624] & 0x7fffffff))
#         a[i] = (y >> 1) ^ a[(i + 397) % 624]

#         if y % 2 != 0:
#             a[i] = a[i] ^ 0x9908b0df
#     return a


# def get_seed2(seed):
#     mt = init(seed)
#     a = twist(mt)

#     return recover(a[-1])


# state = init(seed)

# seed2 = get_seed2(seed)

# print(seed)
# print(seed2)

# print(f(seed))
# print(f(seed2))

# void1 = Random(seed)
# void2 = Random(seed2)

# print(init(seed)[-10:])
# print(init(seed2)[-10:])

# sss = randint(0, 4194304)
# x = void1.getrandbits(sss*8)
# y = void2.getrandbits(sss*8)

# x = void1.getrandbits(8 * 32).to_bytes(32, 'little')
# y = void2.getrandbits(8 * 32).to_bytes(32, 'little')

# print(x.hex())
# print(y.hex())
# print(struct.unpack_from("8L", bytes(x)))
# print(struct.unpack_from("8L", bytes(y)))
# print([i ^ j for i, j in zip(x, y)])

seed1 = bytes.fromhex('1f8b4e6cfd5b92a20a51a2e9a6713a6a6efb92f146f6bc84e21e324bf77b655b')
seed2 = bytes.fromhex('1f8b4e6cfd5b92a20a51a2e9a6713a6a6efb92f146f6bc84e21e324bf77b6550')

def get_rand(i, n):
    void1 = Random(seed1)
    void2 = Random(seed2)

    x = void1.getrandbits(i*8)
    y = void2.getrandbits(i*8)

    x = void1.getrandbits(8 * n).to_bytes(n, 'little')
    y = void2.getrandbits(8 * n).to_bytes(n, 'little')

    return [i ^ j for i, j in zip(x, y)]

rc = RandCrack()

with open("2.txt", "r") as f:
    data = f.readline()
print(len(data))

secret = bytes.fromhex(data)

u32_list = struct.unpack_from("624L", secret)
# print(u32_list)

for i in range(624):
    rc.submit(u32_list[i])
    # Could be filled with random.randint(0,4294967294) or random.randrange(0,4294967294)

n = len(data)//2 - 624*4
x = rc.predict_getrandbits(8 * n)
bx = x.to_bytes(n, 'little')

text = [i ^ j for i, j in zip(secret[624*4:], bx)]

print(text)
print(bytes(text))
