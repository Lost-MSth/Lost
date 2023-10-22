from mod_equations import run_test
import numpy as np

# 同余方程组 有限域方程组

A = []
for i in range(36):
    A.append([0] * 37)

N = 0x3b800001

D = [0x00000CF6, 0x16C80709, 0x086B7BDA, 0x05FBEE9E, 0x24D1FFC1, 0x16F76AE2, 0x15F03305, 0x218C23F9,
     0x33163AC1, 0x0332C16E, 0x27E7B4A7, 0x241D8073, 0x01C6F122, 0x2D73DE13, 0x07FC0A09, 0x0D50F7B7,
     0x0261B1DD, 0x37E5BB8E, 0x0DA71DC5, 0x2DC3F20C, 0x00CCB13A, 0x2F6341E4, 0x0B0611DB, 0x0A382A1A,
     0x103C09B2, 0x1CE2BE88, 0x19A9FD15, 0x2621CFC1, 0x2970DEAC, 0x08A463AA, 0x116C6D31, 0x222E9178,
     0x33B9C9DD, 0x2F98D035, 0x00B8177A, 0x342611E8]

for i in range(36):
    x = 1
    for j in range(36):
        A[i][j] = x
        x = (x * (i+1)) % N
    A[i][36] = D[i]

# print(A)



r = 'flag{'
for i in range(36):
    for j in range(5):
        D[i] -= ord(r[j]) * (i+1) ** j


# AX = D (mod N)

run_test(N, None, A)
