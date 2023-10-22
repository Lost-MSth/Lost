
with open('video_log.txt', 'r') as f:
    raw = f.read()

data = ''

TIMES = 12

i = 0
k = 0
kk = ''

n = 0
j = 0

flag1 = 0

data_time = []

for i in raw:
    if i == kk:
        k += 1
        j += 1
        continue

    x = round(k / TIMES)
    # if k > 0 and x == 0:
    #     x = 1
    #     print('Error: ', j, len(data)//2, '---', kk, '---', k)
    # if k <= 31 and x == 3:
    #     x = 2
    #     print('Warning3: ', j, len(data)//2, '---', kk, '---', k)
    # if k >= 30 and x == 2:
    #     x = 3
    #     print('Error2: ', j, len(data)//2, '---', kk, '---', k)
    #     print(data[-5:])
    #     print(data_time[-5:])
    # if k >= 17 and x == 1:
    #     x = 2
    #     print('Warning: ', j, n, '---', i, '---', k)
    if k <= 18 and x == 2:
        # if j not in (11487, 17121, 17151, 19953, 25617, 28478, 34112, 34142):
        x = 1
        # print('Warning: ', j, len(data)//2, '---', kk, '---', k)
        # print(data[-5:])
        # print(data_time[-5:])
    if j == 14290:
        x = 1
    if j == 11487:
        x = 2
    if j == 17121:
        x = 2
    
    if j == 36999:
        x = 3


    if j == 28478:
        x = 3

    if abs(x - k / TIMES) >= 0.35:
        # if kk != '0' and k >= 36:
        #     x = 3
        if len(data)//2 >= 279:
            pass
            print('INFO: ', j, len(data)//2, '---',
                  kk, '---', k, '---', k / TIMES)
            print(data_time[-5:])
    data += kk * x
    data_time.append(k)
    n += 1
    k = 1
    j += 1
    kk = i

print(data[-20:])
print(len(data))
if len(data) % 2 == 1:
    data += '0'

with open('video_log_parse.png', 'wb') as f:
    f.write(bytes.fromhex(data[:]))
