file_content = '''
# !/usr/bin/env python3
import socket
import os
import json
from time import sleep

# Define the socket path
socket_path = '/tmp/uds_socket'

# Ensure the socket file does not exist from a previous run
try:
    os.unlink(socket_path)
except OSError:
    if os.path.exists(socket_path):
        raise

# Create a UDS socket
server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Bind the socket to the path
server_socket.bind(socket_path)

# Listen for incoming connections
server_socket.listen(1)
print(f"Listening on {socket_path}")

DATA = [
    {
        'id': 'shutdown',
        'method': 'shutdown',
        'data': ''
    },
    # {
    #     'id': 'valid',
    #     'method': 'getConfig',
    #     'data': '/tmp/config.json',
    # },
    {
        'id': 'check_init',
        'method': 'getIsInit',
        'data': ''
    },
    {
        'id': 'init',
        'method': 'initClash',
        'data': json.dumps({
            # 'version': '1.0.0',
            'home-dir': '/root/',
        })
    },
    {
        'id': 'check_init',
        'method': 'getIsInit',
        'data': ''
    },
    {
        'id': 'setup',
        'method': 'setupConfig',
        'data': '',
    },
    {
        'id': 'check_init',
        'method': 'getIsInit',
        'data': ''
    },
    {
        'id': 'log',
        'method': 'startLog',
        'data': '',
    },
    {
        'id': 'start_listener',
        'method': 'startListener',
        'data': '',
    },
    {
        'id': 'get_proxies',
        'method': 'getProxies',
        'data': ''
    },
    {
        'id': 'update',
        'method': 'updateConfig',
        'data': json.dumps({
            'external-controller': '127.0.0.1:9090',
        })
    },
    {
        'id': 'delete',
        'method': 'deleteFile',
        'data': '/root/secure',
    },
]



while True:
    print("Waiting for a connection...")
    connection, client_address = server_socket.accept()
    try:
        idx = 0
        print(f"Connection from {client_address}")
        while True:
            send_data = DATA[idx % len(DATA)]
            idx += 1
            connection.sendall(json.dumps(send_data).encode()+b"\\n")
            print("Sent request.")
            data = connection.recv(16384)
            if data:
                print(f"Received: {data[:4096].decode()}")
                # connection.sendall(b"Server received your message!")
                sleep(0.2)
                if idx >= len(DATA):
                    print("All requests sent. Get data if any...")
                    # 必须要卡在这里，否则 clash 关掉了
                    while True:
                        data = connection.recv(4096)
                        if data:
                            print(f"Received: {data.decode()}")
                    
            else:
                print("No more data from client.")
                break
    finally:
        connection.close()
        print("Client connection closed.")
'''

print("Writing UDS server script to /tmp/uds_server.py")
with open('/tmp/uds_server.py', 'w') as f:
    f.write(file_content)
