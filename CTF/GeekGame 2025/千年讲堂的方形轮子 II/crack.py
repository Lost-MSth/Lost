import base64
import random
import re
from time import sleep

import requests

# 修改为你的题目地址
BASE_URL = 'https://prob14-7t2wwi53.geekgame.pku.edu.cn/'
# BASE_URL = 'http://127.0.0.1:5000'

s = requests.Session()


def get_random_printable_ascii(length):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(length))


def get_ticket(level, name, stuid='0000000000'):
    """从服务器获取加密的票据"""
    params = {'name': name, 'stuid': stuid}
    r = s.get(f'{BASE_URL}/{level}/gen-ticket', params=params)
    # <p>已为您生成购票凭证：</p><br><p>...</p><br><p><a href="/">返回</a></p>
    ticket_b64 = r.text.split('<p>')[2].split('</p>')[0]
    return ticket_b64


def get_ticket_special(level, name: bytes, stuid='0000000000'):
    url = f'{BASE_URL}/{level}/gen-ticket?stuid={stuid}&name='
    r = s.get(url.encode() + name)
    # <p>已为您生成购票凭证：</p><br><p>...</p><br><p><a href="/">返回</a></p>
    ticket_b64 = r.text.split('<p>')[2].split('</p>')[0]
    return ticket_b64


def query_ticket(level, ticket_b64):
    """查询票据内容"""
    params = {'ticket': ticket_b64}
    r = s.get(f'{BASE_URL}/{level}/query-ticket', params=params)
    return r.text


def get_code_from_ticket(level, ticket_b64):
    """查询票据并从中提取code"""
    r = query_ticket(level, ticket_b64)
    # 礼品兑换码：</b> bcku************</p>
    match = re.search(r"礼品兑换码：</b> (.{4})", r)
    if match:
        return match.group(1)
    return None


def get_flag(level, ticket_b64, code=None):
    """提交票据获取flag"""
    params = {'ticket': ticket_b64}
    if code:
        params['redeem_code'] = code
    r = s.get(f'{BASE_URL}/{level}/getflag', params=params)
    return r.text


def solve_level1():
    print("[+] Solving Level 1...")
    payload = b''
    x = 'A' * 20
    x = get_ticket(1, x)
    x = base64.b64decode(x)
    payload += x[:16*4]
    print(len(x))

    # 构造 true
    y = 'A' * (15+16) + 'true' + ' ' * 16
    print(len(y))
    y = get_ticket(1, y)
    y = base64.b64decode(y)
    payload += y[4*16:5*16]

    # 构造 }
    y = 'A' * (15+16*2) + '}' + ' ' * 16
    print(len(y))
    y = get_ticket(1, y)
    y = base64.b64decode(y)
    payload += y[5*16:6*16]

    payload = base64.b64encode(payload).decode()
    print(payload)
    print(query_ticket(1, payload))

    # 5. 获取flag
    flag_html = get_flag(1, payload)
    flag = flag_html.split('<p>')[2].split('</p>')[0]
    print(f"[+] Level 1 Flag: {flag}\n")


def solve_level2():
    print("[+] Solving Level 2...")
    payload = b''
    x = 'A' * 4
    x = get_ticket(2, x)
    x = base64.b64decode(x)
    payload += x[:16*3]
    print(len(x))

    # 构造 true
    y = '\x11'*2 + '000' + ' ' * 13 + 'true'
    print(len(y))
    y = get_ticket(2, y)
    y = base64.b64decode(y)
    payload += y[3*16:4*16]

    # 构造 code
    y = '\x11'*2 + ' ' * 4
    print(len(y))
    y = get_ticket(2, y)
    y = base64.b64decode(y)
    payload += y[4*16:5*16]

    payload += x[5*16:]
    payload = base64.b64encode(payload).decode()

    # 获取 code
    y = base64.b64encode(y).decode()
    # print(payload)
    code = get_code_from_ticket(2, y)
    print(f"[+] Extracted code: {code}")

    query_ticket(2, payload)

    # 获取flag
    flag_html = get_flag(2, payload, code=code)
    print(flag_html)
    flag = flag_html.split('<p>')[2].split('</p>')[0]
    print(f"[+] Level 2 Flag: {flag}\n")


def solve_level3():
    print("[+] Solving Level 3...")
    payload = b''
    # x = 'A' * 18
    x = '\x11' + 'A' * 14
    x = get_ticket(3, x, stuid='①'*6 + '1'*4)
    x = base64.b64decode(x)
    payload += x[:16*4]
    print(len(x))

    # 构造 code
    y = '\\' + 'A' * 17
    print(len(y))
    y = get_ticket(3, y)
    y = base64.b64decode(y)
    payload += y[4*16:5*16]

    # 构造 16 个空位
    y = ' ' * 16
    print(len(y))
    y = get_ticket(3, y, stuid='①'*7 + '1'*3)
    y = base64.b64decode(y)
    blueprint = y

    # 构造 :true}
    z = ':true}' + ' ' * 11
    print(len(z))
    z = get_ticket(3, z, stuid='①'*7 + '1'*3)
    z = base64.b64decode(z)
    z = z[6*16:7*16]

    # 密文窃取
    print("[*] Testing stolen ciphertext...")
    try_num = 0
    while True:
        random_code = get_random_printable_ascii(7)
        y = 'A' * 4 + random_code
        # print(len(y))
        y = get_ticket(3, y, stuid='①'*3 + '1'*7)
        y = base64.b64decode(y)
        # payload += y[5*16:6*16]
        cm1 = y[5*16:6*16]
        cm = y[6*16:]

        test = blueprint[:6*16] + cm1 + blueprint[7*16:]
        test = base64.b64encode(test).decode()
        d = query_ticket(3, test)
        try_num += 1
        sleep(0.1)
        if try_num % 100 == 0:
            print(f"[-] Attempt {try_num} failed...")
        if not '失败' in d:
            # print(d)
            m = re.search(r"<p><b>姓名：</b> (.*)</p>", d)
            if not m:
                print("[!] Failed to extract name")
                print(d)
                continue
            name = m.group(1)

            if name.startswith(': false}'):
                print(name)
                print(len(name))
                cp = name[8:].encode('utf-8', 'ignore')
                if len(cp) != 8:
                    continue
                final_payload = payload+cm+cp+z
                final_payload = base64.b64encode(final_payload).decode()
                txt = query_ticket(3, final_payload)
                sleep(0.1)
                if not '失败' in txt:
                    print(txt)
                    break

    code = get_code_from_ticket(3, final_payload)[0]
    print(f"[+] Extracted code: {code}")
    # 获取flag
    flag_html = get_flag(3, final_payload, code=code+'A'*16+random_code)
    print(flag_html)
    flag = flag_html.split('<p>')[2].split('</p>')[0]
    print(f"[+] Level 3 Flag: {flag}\n")


if __name__ == '__main__':
    # solve_level1()
    # solve_level2()
    solve_level3()
