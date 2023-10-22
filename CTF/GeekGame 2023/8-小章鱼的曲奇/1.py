import struct
from randcrack import RandCrack


rc = RandCrack()

with open("1.txt", "r") as f:
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
