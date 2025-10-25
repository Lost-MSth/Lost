from Crypto.Cipher import ARC4

# 从代码分析中得到的密钥
key2 = b'sneaky_key'

# !!! 关键步骤 !!!
# 你需要从二进制文件的 unk_2160 地址处提取 39 字节的密文数据
# 并将其填充到下面的 `ciphertext` 变量中。
# 示例格式: ciphertext = bytes([0xAB, 0xCD, 0x12, ...])
ciphertext = bytes([0x1C, 0x5B, 0xE6, 0xC0, 0xE1, 0x1C, 0xC8, 0x9E, 0xD3, 0xB0, 0x94, 0xC2, 0x87, 0x8C, 0x30, 0xB9, 0x84, 0x9F,
                   0x88, 0xF5, 0x03, 0x40, 0x5B, 0x56, 0xBE, 0x81, 0xBD, 0xEE, 0x3B, 0x90, 0x41, 0xD4, 0x42, 0x65, 0xEB, 0xD7, 0x41, 0xF5, 0xBF])

if len(ciphertext) != 39:
    print(f"错误: 密文长度应为 39 字节, 当前为 {len(ciphertext)}")
else:
    # RC4 加密/解密过程相同
    cipher = ARC4.new(key2)
    flag2_bytes = cipher.encrypt(ciphertext)
    try:
        flag2 = flag2_bytes.decode('utf-8')
        print(f"Flag 2 (长度: {len(flag2)}): {flag2}")
    except UnicodeDecodeError:
        print("解码为 UTF-8 失败，可能包含非打印字符。原始字节为:")
        print(flag2_bytes)
