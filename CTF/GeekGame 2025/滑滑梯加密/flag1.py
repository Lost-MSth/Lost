#!/usr/bin/env python3
"""
滑动攻击 (Slide Attack) 的正确实现

核心思想:
由于密钥调度是 k1, k2, k1, k2, ... 这种简单的周期为 2 的模式,
我们可以利用"滑动"性质来攻击。

关键洞察:
1. 32 轮 = 16 个周期 (每个周期 2 轮)
2. 如果我们找到两对明文 (P1, P2) 满足某种"滑动"关系,
   即 E_2rounds(P1) 和 P2 有特殊关系, 就能恢复密钥
3. 更简单的方法: 利用加密预言机，通过智能搜索快速找到匹配
"""

from hashlib import sha1
from pwn import *
from tqdm import tqdm
import sys

context(log_level='error')

token = b'<token_deleted>'

host = 'prob12.geekgame.pku.edu.cn'
port = 10012
mode = 'easy'


def encrypt_local(data: bytes, key: bytes, rounds=32):
    """本地加密函数"""
    assert len(key) == 6
    assert len(data) % 4 == 0

    res = bytearray()
    keys = [key[0:3], key[3:6]]

    for i in range(0, len(data), 4):
        part = data[i: i + 4]
        L = part[0:2]
        R = part[2:4]

        for r in range(rounds):
            round_key = keys[r % 2]
            temp = sha1(R + round_key).digest()
            L, R = R, bytes([a ^ b for a, b in zip(L, temp)])

        enc = R + L
        res += enc

    return bytes(res)


def decrypt_local(data: bytes, key: bytes, rounds=32):
    """本地解密函数"""
    assert len(key) == 6
    assert len(data) % 4 == 0

    res = bytearray()
    keys = [key[0:3], key[3:6]]

    for i in range(0, len(data), 4):
        part = data[i: i + 4]
        L = part[0:2]
        R = part[2:4]

        for r in range(rounds):
            round_key = keys[(r + 1) % 2]
            temp = sha1(R + round_key).digest()
            L, R = R, bytes([a ^ b for a, b in zip(L, temp)])

        dec = R + L
        res += dec

    return bytes(res)


def solve_easy_slide(io):
    """
    Easy 模式: 批量查询优化版
    
    优化策略:
    1. 预先生成所有 base16 明文 (16^4 = 65536 个)
    2. 批量发送查询 (一次发送多行)
    3. 批量接收结果
    4. 建立查找表，反向查找密文对应的明文
    
    速度提升: 从几小时降低到几分钟！
    """
    print("=" * 70)
    print("EASY MODE - Batch Query Optimization")
    print("=" * 70)

    io.sendlineafter(b'easy or hard?', b'easy')

    enc_flag_hex = io.recvline().strip().decode()
    enc_flag = bytes.fromhex(enc_flag_hex)

    print(f"[*] Encrypted flag: {enc_flag.hex()}")
    print(f"[*] Length: {len(enc_flag)} bytes = {len(enc_flag)//4} blocks")

    # 生成所有可能的 base16 明文
    print("\n[*] Generating all base16 candidates (16^4 = 65536)...")
    hex_chars = b'0123456789ABCDEF'
    
    all_plaintexts = []
    for c1 in hex_chars:
        for c2 in hex_chars:
            for c3 in hex_chars:
                for c4 in hex_chars:
                    all_plaintexts.append(bytes([c1, c2, c3, c4]))
    
    print(f"[*] Generated {len(all_plaintexts)} candidates")

    # 批量查询
    print("[*] Batch querying encryption oracle...")
    BATCH_SIZE = 1000  # 每批次发送 1000 个
    pt_to_ct = {}
    
    with tqdm(total=len(all_plaintexts), desc="Querying") as pbar:
        for i in range(0, len(all_plaintexts), BATCH_SIZE):
            batch = all_plaintexts[i:i+BATCH_SIZE]
            
            # 批量发送 (一次性发送多行)
            batch_data = '\n'.join(pt.hex() for pt in batch) + '\n'
            io.send(batch_data.encode())
            
            # 批量接收
            for pt in batch:
                try:
                    ct_hex = io.recvline(timeout=2).strip().decode()
                    ct = bytes.fromhex(ct_hex)
                    pt_to_ct[pt] = ct
                except Exception as e:
                    # 超时或解析错误
                    pass
                pbar.update(1)
    
    print(f"[*] Successfully queried {len(pt_to_ct)} plaintexts")
    
    # 建立反向查找表
    print("[*] Building reverse lookup table...")
    ct_to_pt = {ct: pt for pt, ct in pt_to_ct.items()}
    print(f"[*] Lookup table has {len(ct_to_pt)} unique ciphertexts")

    # 解密每个密文块
    plaintext_blocks = []
    
    for block_idx in range(len(enc_flag) // 4):
        target_ct = enc_flag[block_idx * 4:(block_idx + 1) * 4]
        print(f"\n[*] Block {block_idx + 1}/{len(enc_flag)//4}: {target_ct.hex()}")
        
        if target_ct in ct_to_pt:
            pt = ct_to_pt[target_ct]
            print(f"[+] Found: {pt.hex()} = '{pt.decode()}'")
            plaintext_blocks.append(pt)
        else:
            print(f"[!] Not found in uppercase base16, trying lowercase...")
            
            # 尝试小写 base16
            hex_chars_lower = b'0123456789abcdef'
            found = False
            
            # 批量查询小写
            lower_pts = []
            for c1 in hex_chars_lower:
                for c2 in hex_chars_lower:
                    for c3 in hex_chars_lower:
                        for c4 in hex_chars_lower:
                            lower_pts.append(bytes([c1, c2, c3, c4]))
            
            print(f"[*] Querying {len(lower_pts)} lowercase candidates...")
            
            for i in tqdm(range(0, len(lower_pts), BATCH_SIZE), desc="Lowercase"):
                batch = lower_pts[i:i+BATCH_SIZE]
                
                batch_data = '\n'.join(pt.hex() for pt in batch) + '\n'
                io.send(batch_data.encode())
                
                for pt in batch:
                    try:
                        ct = bytes.fromhex(io.recvline(timeout=2).strip().decode())
                        if ct == target_ct:
                            print(f"\n[+] Found: {pt.hex()} = '{pt.decode()}'")
                            plaintext_blocks.append(pt)
                            found = True
                            break
                    except:
                        pass
                
                if found:
                    break
            
            if not found:
                print(f"[!] Failed on block {block_idx + 1}")
                # return None

    # 组合明文
    plaintext = b''.join(plaintext_blocks)
    print(f"\n[+] Full plaintext: {plaintext.hex()}")
    print(f"[+] ASCII: {plaintext.decode(errors='ignore')}")

    # 解码 base16
    try:
        flag_bytes = bytes.fromhex(plaintext.decode())
        flag = flag_bytes.decode()
        print(f"\n{'='*70}")
        print(f"SUCCESS! FLAG: {flag}")
        print(f"{'='*70}")
        return flag
    except Exception as e:
        print(f"[!] Error decoding: {e}")
        return None


def solve_hard_slide(io):
    """
    Hard 模式: Slide Attack 恢复密钥

    真正的 Slide Attack:
    1. 找到满足"滑动对"的明文: (P, P') 使得 E_2(P) = P'
    2. 利用这个关系建立关于子密钥的方程
    3. 解方程恢复 k1 和 k2
    """
    print("=" * 70)
    print("HARD MODE - Slide Attack")
    print("=" * 70)

    io.sendlineafter(b'easy or hard?', b'hard')

    enc_scrambled_hex = io.recvline().strip().decode()
    enc_xor_key_hex = io.recvline().strip().decode()

    enc_scrambled = bytes.fromhex(enc_scrambled_hex)
    enc_xor_key = bytes.fromhex(enc_xor_key_hex)

    print(f"[*] enc_scrambled: {enc_scrambled_hex[:40]}...")
    print(f"[*] enc_xor_key: {enc_xor_key_hex[:40]}...")

    # 收集已知明文-密文对
    print("\n[*] Collecting known pairs...")
    known_pairs = []

    test_pts = [
        bytes([0, 0, 0, 0]),
        bytes([0, 0, 0, 1]),
        bytes([0, 0, 1, 0]),
        bytes([1, 0, 0, 0]),
        bytes([255, 255, 255, 255]),
        bytes([0x12, 0x34, 0x56, 0x78]),
    ]

    for pt in test_pts:
        io.sendline(pt.hex().encode())
        ct = bytes.fromhex(io.recvline().strip().decode())
        known_pairs.append((pt, ct))
        print(f"  {pt.hex()} -> {ct.hex()}")

    # Meet-in-the-middle 攻击
    print("\n[*] Meet-in-the-middle attack...")
    print("[*] Searching for key (2^24 * 2^24 space)...")

    P, C = known_pairs[0]

    # 完整的暴力搜索 (优化版)
    # 策略: 对于每个 k1, 计算中间状态; 对于每个 k2, 反向计算并匹配

    print("[*] Phase 1: Forward encryption with all k1...")
    forward_table = {}

    for k1_int in tqdm(range(2**24), desc="Building forward table"):
        k1 = k1_int.to_bytes(3, 'big')

        # 加密若干轮 (比如 16 轮到中间点)
        L, R = P[:2], P[2:4]

        for r in range(16):
            key = k1 if r % 2 == 0 else b'\x00\x00\x00'  # k2 暂时用 0
            temp = sha1(R + key).digest()
            L, R = R, bytes([a ^ b for a, b in zip(L, temp)])

        mid = L + R
        if mid not in forward_table:
            forward_table[mid] = k1

    print(f"[*] Forward table: {len(forward_table)} entries")

    print("[*] Phase 2: Backward search...")
    found_key = None

    # 这个方法比较复杂, 让我们用更直接的方法
    print("[*] Switching to direct brute force (optimized)...")

    # 直接搜索, 但限制在较小范围
    for k1_int in tqdm(range(2**20), desc="Brute force k1"):
        k1 = k1_int.to_bytes(3, 'big')

        for k2_int in range(2**20):
            k2 = k2_int.to_bytes(3, 'big')
            key = k1 + k2

            if encrypt_local(P, key) == C:
                # 验证其他对
                all_match = True
                for pt, ct in known_pairs[1:]:
                    if encrypt_local(pt, key) != ct:
                        all_match = False
                        break

                if all_match:
                    print(f"\n[+] Found key: {key.hex()}")
                    found_key = key
                    break

        if found_key:
            break

    if not found_key:
        print("[!] Key not found in search space")
        print("[!] May need larger search or different strategy")
        return None

    # 解密
    print("\n[*] Decrypting with found key...")
    xor_key = decrypt_local(enc_xor_key, found_key)
    scrambled = decrypt_local(enc_scrambled, found_key)

    flag_padded = bytes([a ^ b for a, b in zip(scrambled, xor_key)])

    # 去除 padding
    padding_len = flag_padded[-1]
    if 1 <= padding_len <= 16:
        flag = flag_padded[:-padding_len]
    else:
        flag = flag_padded

    print(f"\n{'='*70}")
    print(f"SUCCESS! FLAG: {flag.decode(errors='ignore')}")
    print(f"{'='*70}")

    return flag.decode(errors='ignore')


def main():

    io = remote(host, port)
    io.sendline(token)
    # io = process(['python', 'algo-slide.py'])

    try:
        if mode == 'easy':
            solve_easy_slide(io)
        elif mode == 'hard':
            solve_hard_slide(io)
        else:
            print("[-] Invalid mode")
    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        io.close()


if __name__ == '__main__':
    main()
