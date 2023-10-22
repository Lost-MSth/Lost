import requests
import time

fix_cookie = 'eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7ImxldmVsIjoiMSIsInJlbWFpbmluZ19ndWVzc2VzIjoiNTkifSwibmJmIjoxNjk3NDYwNjE0LCJpYXQiOjE2OTc0NjA2MTR9.IIW6bpGkmPKyBeBGbeJHQdFsi_XQddAKspplGRqRDyg'


def get_data(ans):
    s = requests.session()
    s.cookies['PLAY_SESSION'] = fix_cookie
    s = s.get('https://prob14.geekgame.pku.edu.cn/level1?guess=' + ans)
    return s.text


a = [128136, 128133, 128124, 128129, 128102, 128087, 128138, 128138, 128113, 128071, 128084, 128134, 128122, 128102, 128083, 128115, 128084, 128073, 128094, 128132, 128103, 128088, 128131, 128122, 128120, 128116, 128127, 128089, 128117, 128134, 128105,
     128125, 128091, 128083, 128102, 128093, 128098, 128131, 128133, 128118, 128069, 128136, 128072, 128133, 128124, 128065, 128067, 128130, 128070, 128068, 0, 128115, 128114, 128098, 128134, 128100, 128092, 128070, 128122, 128113, 128122, 128091, 128070, 128097]

n = 0
for i in a:
    if i != 0:
        n += 1

start = 0x1f400  # 0x1f300
for i in range(start, 0x1f7ff):
    x = ''
    for j in chr(i).encode('utf-8'):
        x += '%' + (hex(j)[2:]).upper()

    ans = x * 64
    try:
        data = get_data(ans)
    except:
        print(a)
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
    time.sleep(1)


print(a)

ans = ''
for i in a:
    x = ''
    for j in chr(i).encode('utf-8'):
        x += '%' + (hex(j)[2:]).upper()
    ans += x

print(ans)

d = get_data(ans)
print(d)
