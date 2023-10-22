from pwn import *
import time

data = []
guess = ''

def main():
    c = remote("prob16.geekgame.pku.edu.cn", 10016)
    c.recv(8192)


    def send(b):
        c.sendline(b)
        #print(b.decode())
        x = c.recv(8192)

        #print(x.decode())
        time.sleep(0.15)

    def send_guess(b):
        global guess
        c.sendline(b)
        #print(b.decode())
        t = time.time()
        x = c.recvuntil(b'Guess')
        t = time.time() - t
        if t > 0.5:
            guess = '1' + guess
        else:
            guess = '0' + guess
        print(t)
        data.append(t)
        return x
        #print(x.decode())


    send(b"13:...")  # token deleted
    send(b"newgame")
    send(b'Lost')
    send(b'y')
    send(b'n')
    send(b'n')
    send(b'w')
    send(b'w')
    send(b's')
    send(b'getflag')
    # send(b'h')
    # send(b'h')
    # send(b'h')
    while True:
        x = send_guess(b'114514')
        if b'Wrong' not in x and b'Guess' not in x:
            break

    print(guess)
    print(data)

    x = c.recv(8192 * 4).decode()
    print(x)

    c.clean()
    c.close()

if __name__ == "__main__":
    main()



# c.interactive()

