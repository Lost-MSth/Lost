import binascii
import itertools

# chars = [53, 122, 75, 131, 109, 32]
crc = 0xCB5D57CA

# 只有 m 和 32

chars = [109, 32]
codes = ['11111111101000', '111111111111100']
end = '11111110'

ans = None

# 2**30，0 是空格，1 是 m
k = 0
for bits in itertools.product([0, 1], repeat=30):
    secret_number = bytearray(b'\x20' * 30)
    for i, bit in enumerate(bits):
        if bit == 1:
            secret_number[i] = 109

    crc_value = binascii.crc32(secret_number) & 0xffffffff
    # print(f'Trying: {secret_number} => {hex(crc_value)}')
    k += 1
    if crc_value == crc:
        print(secret_number)
        ans = secret_number
        break
        # exit(0)
    if k % 1000000 == 0:
        print(f'Tried {k} combinations')

# ans = b'      m    m  mmm mm  m   mm  '

# 拼接 bits
bits = '0'  # 有个头别忘了

for c in ans:
    if c == 32:
        bits += codes[1]
    elif c == 109:
        bits += codes[0]
    else:
        raise ValueError('Invalid character')

bits += end

print(bits)
print(len(bits))
# bits to bytes
byte_arr = bytearray()
for i in range(0, len(bits), 8):
    biny_str = bits[i:i+8][::-1]
    byte = int(biny_str, 2)
    byte_arr.append(byte)
print(byte_arr.hex())
print(len(byte_arr))
