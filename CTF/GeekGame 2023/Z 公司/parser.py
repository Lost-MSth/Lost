import struct
with open('pre.txt') as f:
    raw = f.read()


print(len(raw) / 2)


data = b''
flag = False
flag2 = 0
n = 0
for i in range(0, len(raw), 2):
    x = bytes.fromhex(raw[i:i+2])
    if flag2 != 0:
        if flag2 == 6 and x == b'\x18':
            flag2 -= 1
            continue
        elif flag2 == 5 and x == b'\x69':
            flag2 -= 1
            continue
  
        elif x != b'\x18':
            flag2 -= 1
            continue
        else:
            print('???')
            print(raw[i+2:i+22])
            continue

    if x == b'\x18':
        flag = True
        continue
    if flag:
        data += (int(x.hex(), 16) ^ 0x40).to_bytes(1, 'big')
        n += 1
        flag = False
    else:
        data += x
        n += 1
    if n == 1024:
        print(raw[i+2:i+22])
        flag2 = 6
        n = 0

with open('flag.jpg', 'wb') as f:
    f.write(data)
