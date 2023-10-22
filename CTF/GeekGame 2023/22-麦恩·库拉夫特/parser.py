
with open('re.bak.txt', 'r') as f:
    raw = f.read()

print(len(raw))

data = ''

stack = [0] * 16
delay_stack = [0] * 16

D = {
    '0': 0,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    'a': 10,
    'b': 11,
    'c': 12,
    'd': 13,
    'e': 14,
    'f': 15
}

B = ['0', '1', '2', '3', '4', '5', '6', '7',
     '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']

TIMES = 4
DELAY = 4
ERROR_TIMES = 6 - TIMES

for k, i in enumerate(raw):
    if stack[D[i]] == 0:
        data += i
    stack[D[i]] = (stack[D[i]] + 1) % TIMES
    for j in range(16):
        if stack[j] == 0:
            delay_stack[j] = 0
            continue

        if D[i] == j:
            continue

        if stack[j] == ERROR_TIMES:
            delay_stack[j] += 1
            if delay_stack[j] == DELAY:
                delay_stack[j] = 0
                stack[j] = 0

                if j in (8, 2, 7, 14): continue
                #if k <= 5000: continue

                x = data[::-1].find(B[j])
                y = raw[:k][::-1].find(B[j])
                if raw[k-y-6:k-y] != B[j] * 6:
                    print(k, B[j])
                    print(raw[k-y-6:k-y])
                
                    data = data[:-x-1] + data[-x:]
                #else: print(k, B[j], '??')

print(data)
print(len(data))
print(stack)

with open('flag32.png', 'wb') as f:
    f.write(bytes.fromhex(data))
