a = [
1.0,
0.0,
1.0,
1.0,
1.0,
0.9,
1.0,
0.0,
1.0,
0.0,
0.0,
1.0,
1.0,
1.0,
0.9,
0.0,
0.0,
0.0,
1.0,
1.0,
0.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.0,
1.0,
0.9,
1.0,
0.0,
0.0,
1.0,
0.9,
1.0,
0.0,
0.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
1.0,
0.0,
1.0,
0.9,
0.0,
0.0,
0.0,
1.0,
1.0,
0.0,
1.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.0,
1.0,
0.9,
0.0,
0.0,
0.0,
1.0,
1.0,
0.0,
0.0,
0.0,
0.0,
1.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.0,
1.0,
0.9,
1.0,
0.9,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
0.0,
1.0,
0.9,
0.0,
1.0,
1.0,
0.9,
0.0,
0.0,
1.0,
1.0,
0.0,
0.0,
1.0,
1.0,
1.0,
0.0,
0.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
0.0,
1.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
0.0,
1.0,
0.0,
1.0,
0.0,
0.0,
0.0,
0.0,
0.0,
1.0,
0.0,
0.0,
0.0,
0.0,
1.0,
0.0,
1.0,
1.0,
0.0,
1.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
1.0,
1.0,
0.9,
1.0,
1.0,
0.0,
1.0,
0.0,
1.0,
1.0,
0.0,
0.0,
1.0,
1.0,
1.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
0.0,
0.0,
0.0,
0.0,
1.0,
0.0,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.0,
1.0,
0.9,
0.9,
0.0,
1.0,
0.9,
1.0,
1.0,
0.9,
0.0,
1.0,
0.0,
0.0,
0.0,
1.0,
0.0,
0.0,
1.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
0.0,
1.0,
1.0,
0.0,
0.0,
1.0,
1.0,
0.0,
1.0,
0.9,
1.0,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
1.0,
1.0,
0.0,
0.0,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
0.0,
1.0,
0.9,
0.0,
0.0,
1.0,
1.0,
0.9,
0.0,
1.0,
1.0,
0.9,
0.9,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
1.0,
0.0,
1.0,
1.0,
1.0,
0.0,
1.0,
1.0,
1.0,
0.9,
0.0,
1.0,
1.0,
0.0,
1.0,
0.0,
0.0,
1.0,
1.0,
0.0,
1.0,
0.0,
1.0,
1.0,
0.0,
1.0,
1.0,
1.0,
0.9,
0.0,
1.0,
1.0,
0.9,
0.0,
0.0,
1.0,
1.0,
0.0,
1.0,
0.0,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
0.0,
0.0,
1.0,
0.9,
0.0,
1.0,
1.0,
0.0,
0.0,
1.0,
1.0,
0.0,
0.0,
1.0,1]

a = [round(x) for x in a][::-1]

print(a)

x = 0

for i in a:
    x = (x << 1) + i

print(x)
print(hex(x))
print(bytes.fromhex(hex(x)[2:][::]))
print(bytes.fromhex(hex(x)[2:][::-1]))
