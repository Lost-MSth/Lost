from pwn import *
import time


def main():
    c = remote("prob16.geekgame.pku.edu.cn", 10016)
    c.recv(8192)

    def send(b):
        c.sendline(b)
        #print(b.decode())
        x = c.recv(8192)
        #print(x.decode())
        time.sleep(0.15)


    send(b"13:...")  # token deleted
    send(b"newgame")
    send(b'Lost')
    send(b'y')
    send(b'n')
    send(b'n')
    send(b'e')
    send(b'pickup key')
    send(b'w')
    send(b's')
    send(b's')
    send(b'e')
    send(b'e')
    send(b'e')
    send(b'pickup trinket')
    send(b'w')
    send(b's')
    send(b'usewith key door')
    send(b's')
    send(b's')
    send(b'n')
    send(b'w')
    send(b'w')
    send(b'w')
    send(b'n')
    send(b'pickup key')
    send(b's')
    send(b'e')
    send(b'e')
    send(b'e')
    send(b'n')
    send(b'n')
    send(b'w')
    send(b'w')
    send(b'n')
    send(b'n')
    send(b'w')
    send(b'w')
    send(b'usewith key door')
    send(b'use trinket')
    send(b'h')
    send(b'h')
    send(b'h')
    send(b'n')


    x = c.recv(8192 * 4).decode()
    print(x)
    if "flag{" in x:
        print(x)
        exit(0)

    c.clean()
    c.close()

while True:
    main()



# c.interactive()

