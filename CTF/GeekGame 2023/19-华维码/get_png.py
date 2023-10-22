import requests
import json

s = requests.session()

s.get("https://prob19.geekgame.pku.edu.cn/?token=13...")  # token deleted
x = s.get("https://prob19.geekgame.pku.edu.cn/game/newGame?level=9")

x = json.loads(x.text)

print(x)

d = x['data']['game']

for i in d:
    for j in i:
        print(j)
        if j is None: continue
        r = s.get('https://prob19.geekgame.pku.edu.cn/' + j)
        with open("./2/" + j.split('/')[-1], 'wb') as f:
            f.write(r.content)
