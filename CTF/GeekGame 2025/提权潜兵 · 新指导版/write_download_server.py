file_content = '''
import os
import socketserver


class FileRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print(f"Received: {self.data}")

        # filename = self.data[4:]
        filename = '/tmp/evil.zip'

        size = os.path.getsize(filename)
        # 发送响应头
        headers = (
            b"HTTP/1.1 200 OK\\r\\n"
            b"Content-Type: application/zip\\r\\n"
            + f"Content-Length: {size}\\r\\n".encode()
            + b"Connection: close\\r\\n"
            b"\\r\\n"
        )
        self.request.sendall(headers)

        # 分块发送文件内容
        with open(filename, 'rb') as f:
            for buf in iter(lambda: f.read(64 * 1024), b""):
                self.request.sendall(buf)


if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 6666
    server = socketserver.ThreadingTCPServer((HOST, PORT), FileRequestHandler)
    print(f"Serving on {HOST}:{PORT}")
    server.serve_forever()

'''

with open('/tmp/download_server.py', 'w') as f:
    f.write(file_content)
