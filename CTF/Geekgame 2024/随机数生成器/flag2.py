# from randcrack import RandCrack

from pwn import *
from symbolic_mersenne_cracker import Untwister

TOKEN = b'<token_is_deleted>'


def main():
    c = remote("prob16.geekgame.pku.edu.cn", 10016)
    c.recv(8192)
    c.sendline(TOKEN)

    x = c.recv(8192)
    randoms = [int(x.decode())]

    for _ in range(2000):
        c.send(b'\n')
        x = c.recv(8192)
        randoms.append(int(x.decode()))

    # print(randoms)
    flag = []
    for _ in range(100):
        c.send(b'\n')
        x = c.recv(8192)
        flag.append(int(x.decode()))

    c.clean()
    c.close()

    ut = Untwister()

    for i in randoms:
        num = i - 75
        ut.submit(bin(num)[2:].zfill(32)[:12] + '?'*(32-12))

    predictor = ut.get_random()

    re = []
    for x in flag:
        re.append(x - predictor.getrandbits(32))

    print(re)
    print(bytes(re))

    # c.interactive()

    # x = c.recv(8192 * 4).decode()
    # print(x)


if __name__ == "__main__":
    main()


# c.interactive()
