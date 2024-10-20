# from randcrack import RandCrack
import random

from symbolic_mersenne_cracker import Untwister

N = 2000
AVAILABLE_BITS = 12
OFFSET = 75


flag = b'flag{abcdefghijklmnopqrstuvwxyz1234567890}'


randoms = []
for i in range(N):
    x = random.getrandbits(32) + flag[i % len(flag)]
    randoms.append(x)


ut = Untwister()


for i in randoms:
    num = i - OFFSET
    d = bin(num)[2:].zfill(32)[:AVAILABLE_BITS] + '?'*(32-AVAILABLE_BITS)
    ut.submit(d)

predictor = ut.get_random()

re = []
for _ in range(64):
    re.append(random.getrandbits(32) - predictor.getrandbits(32))

print(re)
print(bytes(re))
