import gzip


def compress(data):
    return gzip.compress(data)


# with open('out', 'rb') as f:
#     data = f.read()

data = bytearray()

# d = {}
# for i in range(0x20, 0x7e):
#     x = i ^ 10
#     data.append(x)
#     d[x] = d.get(x, 0) + 1

# print(sorted(d.items(), key=lambda x: x[0]))

import random

# 32~127 的字符可用

def count_bits(x):
    c = 0
    while x:
        c += x & 1
        x >>= 1
    return c

x = [i for i in range(32, 128)]
x = list(filter(lambda i: count_bits(i) >= 4, x))
random.shuffle(x)


for i in x:
    for j in range(3):
        data.append(i)



print(len(data))

# data.append(50)

# for j in range(20):
#     data.append(0b1010101)
#     data.append(0b0101010)


ans = compress(data)

with open('out.gz', 'wb') as f:
    f.write(ans)


def average_bit_count(s):
    return sum(c.bit_count() for c in s) / len(s)


# prefix = (ans + b'\xFF'*256)[:256]
prefix = ans
print(average_bit_count(prefix))
if average_bit_count(prefix) < 2.5:
    print('\nGood! Flag 1: ', 123)
