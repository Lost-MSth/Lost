import requests
import time


def get_data(ans, fix_cookie=None):
    s = requests.session()
    if fix_cookie:
        s.cookies['PLAY_SESSION'] = fix_cookie
    s = s.get('https://prob14.geekgame.pku.edu.cn/level3?guess=' + ans)
    return s.text, s.cookies['PLAY_SESSION']


a = [0] * 64

n = 0


start = 0x1f439  # 0x1f300
end = 0x1f493  # 0x1f7ff
cookie = ''

i = start
while i <= end:
    x = ''
    for j in chr(i).encode('utf-8'):
        x += '%' + (hex(j)[2:]).upper()

    ans = x * 64
    try:
        data, c = get_data(ans, cookie)
        
        if cookie == '':
            cookie = c
            print(cookie)
    except Exception as e:
        print(a)
        if e == 'KeyboardInterrupt':
            quit()
        continue
    index = data.find('results.push')
    state = data[index + 14: index + 14 + 64]
    for j in range(64):
        if state[j] == '🟩' and a[j] == 0:
            a[j] = i
            print('right: ', i, chr(i), j)
            n += 1
    if n == 64:
        break

    print(i)
    i += 1
    time.sleep(0.01)


print(a)

ans = ''
for i in a:
    x = ''
    for j in chr(i).encode('utf-8'):
        x += '%' + (hex(j)[2:]).upper()
    ans += x

print(ans)

d = get_data(ans, cookie)
print(d)
