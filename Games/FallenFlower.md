---
modify_date: "2026-05-21 01:00:00"
---

# 凉花酱的烦恼

涼花ちゃんの悩み Fallen Flower v1.0.3

Utatane Club

## 类型

- 4.68 GB
- 3D
- 现实世界
- 单线，似乎没有结局

## 评价

不知道玩了多久，大概 3、4 小时左右吧，大部分时间是在被这游戏系统折磨。

总体而言欠佳，有充足时间且喜欢露出类型的可以一试。疑似游戏还在开发过程中，感觉剧情什么的不完整。

剧情不清不楚的，女主是学生，想在网上火，放学后在路上发现个狗狗，拍了发网上，导致狗被抓了。狗“好像”是流浪汉的，他生气了，让女主追回狗，对方说要很多钱，于是有人联系她拍露出照片、直播赚钱。做一些小任务或者被各种调教后，如果你拿钱去找对方要狗，对方会告诉你狗其实是别的人家里的，送回原主人的家了。然后没了，女主依旧在做一些露出任务，但是信息似乎没有新的了，比较迷惑。

游戏是 3D 的，直播操作就是经典的需要消耗一定时间完成一些任务，赚取人气，被发现了就算是白直播了。另外就是有些固定 H 事件，学校晚上全裸露出被发现、流浪汉调教、黑社会调教、男厕所事件之类的，没几个。

操作其实挺难受的，bug 挺多容易卡住，女主走路跑步速度都很慢，升高经验、赚钱也很慢，H 事件甚至都很慢！特别提醒：请不要游玩此游戏的低版本，会卡住交不了任务……虽然那好像是最后一个任务了。

换装不算多，主要是配件多一点，但是相比别的 3D 露出游戏似乎有点少。

H 事件较少，类型就是露出、调教为基础的，但是正戏做爱实际上没有几个……画风中等，无 CG 之类的全是 3D 动态。无配音，有一些音效。

## 破解

数据无加密，AssetStudio 可以看。但是存档有加密，是 `.save` 文件，位置在 `C:\Users\<你的用户名>\AppData\LocalLow\DefaultCompany\FallenFlower` 里面。

好了，如何修改存档其实才是本文的重中之重。注意到游戏使用了 `GameAssembly.dll`，逆向就困难多了，然后看一眼发现 `global-metadata.dat` 加密了，算是非常麻烦的了，需要先解密 metadata 才有符号表。

根据[看雪帖子](https://bbs.kanxue.com/thread-264829-1.htm)，使用 frida 可以从内存中获取解密后的 metadata，注意要改偏移量为 0xf8 和 0xfc，至于为什么是这个数，这是我盯着内存看出来的。

然后打开 IDA，加载符号表之类的，找到目标函数，交给 deepseek v4 pro 写出解密脚本：

```python
#!/usr/bin/env python3
"""
IL2CPP 存档加解密工具
对应 Utils.Decrypt / Encrypt 逻辑
密码: Encrypt
前缀: Encrypted
"""
import base64
import os
import hmac
from hashlib import pbkdf2_hmac, sha256
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import sys

# ========== 硬编码常量 ==========
MAGIC_PREFIX = "Encrypted"      # 密文前缀
PASSWORD = "Encrypt"            # 解密/加密密码
# Salt 由 Utils.GetName() 动态生成，以下为 hook 获取的实际值
SALT = bytes([0x04, 0x08, 0x41, 0x20, 0x49, 0x24, 0x00, 0x6D])

PBKDF2_ITERATIONS = 10000
HMAC_SIZE = 32                  # SHA256 输出 32 字节
IV_SIZE = 16                    # AES 块大小
AES_KEY_SIZE = 32               # 256 位密钥


def derive_key(password: str) -> bytes:
    """PBKDF2-HMAC-SHA256 派生 AES 密钥"""
    return pbkdf2_hmac('sha256', password.encode('utf-8'), SALT,
                       PBKDF2_ITERATIONS, dklen=AES_KEY_SIZE)


def compute_hmac(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """HMAC-SHA256(IV || ciphertext)"""
    h = hmac.new(key, digestmod=sha256)
    h.update(iv)
    h.update(ciphertext)
    return h.digest()


def encrypt(plaintext: str, password: str = PASSWORD) -> str:
    """
    将明文字符串加密为带前缀的 Base64 存档字符串
    """
    aes_key = derive_key(password)
    # 生成随机 IV
    iv = os.urandom(IV_SIZE)
    # AES-CBC 加密
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    plain_bytes = plaintext.encode('utf-8')
    ciphertext = cipher.encrypt(pad(plain_bytes, AES.block_size))
    # HMAC
    hmac_val = compute_hmac(aes_key, iv, ciphertext)
    # 拼接 payload
    payload = hmac_val + iv + ciphertext
    # Base64 并加前缀
    b64 = base64.b64encode(payload).decode('ascii')
    return MAGIC_PREFIX + b64


def decrypt(cipher_str: str, password: str = PASSWORD) -> str:
    """
    解密存档字符串，返回明文。
    若不含前缀则直接返回原字符串（视为明文）。
    """
    if cipher_str and cipher_str.startswith(MAGIC_PREFIX):
        b64 = cipher_str[len(MAGIC_PREFIX):]
    else:
        return cipher_str  # 无前缀 → 明文

    # Base64 解码
    try:
        payload = base64.b64decode(b64)
    except Exception:
        raise ValueError("无效的 Base64 输入")

    if len(payload) < HMAC_SIZE + IV_SIZE:
        raise ValueError("载荷过短（至少需要 48 字节）")

    expected_hmac = payload[:HMAC_SIZE]
    iv = payload[HMAC_SIZE:HMAC_SIZE + IV_SIZE]
    ciphertext = payload[HMAC_SIZE + IV_SIZE:]

    aes_key = derive_key(password)
    # HMAC 校验
    calc_hmac = compute_hmac(aes_key, iv, ciphertext)
    if not hmac.compare_digest(calc_hmac, expected_hmac):
        raise ValueError("HMAC 校验失败！密码错误或数据被篡改。")

    # 解密
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    try:
        plain_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)
    except Exception as e:
        raise ValueError(f"解密失败：{e}")

    return plain_bytes.decode('utf-8')


# ========== 命令行工具 ==========
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法:")
        print(f"  解密: python {sys.argv[0]} decrypt <存档文件>")
        print(f"  加密: python {sys.argv[0]} encrypt <明文文件>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    filepath = sys.argv[2]

    if mode == "decrypt":
        with open(filepath, 'r', encoding='utf-8') as f:
            cipher_text = f.read()
        try:
            plain = decrypt(cipher_text)
            out_path = filepath + ".dec"
            with open(out_path, 'w', encoding='utf-8') as out:
                out.write(plain)
            print(f"✅ 解密成功 → {out_path}")
        except Exception as e:
            print(f"❌ 解密错误: {e}")

    elif mode == "encrypt":
        with open(filepath, 'r', encoding='utf-8') as f:
            plain_text = f.read()
        enc = encrypt(plain_text)
        out_path = filepath + ".enc"
        with open(out_path, 'w', encoding='utf-8') as out:
            out.write(enc)
        print(f"✅ 加密成功 → {out_path}")
    else:
        print("未知模式，请使用 decrypt 或 encrypt")
```

其实人肉静态分析也能看出来，我只是懒。解密函数唯一让人迷惑的就是 salt 的值了，我看了一眼又让 deepseek 分析了一下，似乎是从机器信息、环境信息、二进制里的字符串等各种东西综合计算出来的，我让 AI 硬算它算错了（其实也就错了两位），所以我手写 frida hook 直接从内存里拿到了正确的 salt（调试起来挺烦的，特别因为是 `System_Byte_array` 这个结构），脚本如下：

```js
// frida -l hook_salt.js -p 6484
// frida -l hook_salt.js -f FallenFlower.exe
// IDA基址: 7FFCA20B0000
// 目标函数: 7FFCA2570AF0

function frida_hook() {
    const moduleName = "GameAssembly.dll";
    const targetOffset = 0x7FFCA257336F - 0x7FFCA20B0000 + 1; // 目标函数地址 - 模块基址

    const timer = setInterval(function () {
        const moduleInfo = Process.findModuleByName(moduleName);
        if (moduleInfo === null) {
            return;
        }

        clearInterval(timer);

        const targetAddr = moduleInfo.base.add(targetOffset);

        console.log("[*] Base Address: " + moduleInfo.base);
        console.log("[*] Target Address: " + targetAddr);

        Interceptor.attach(targetAddr, {
            onEnter: function (args) {
                console.log("[+] 函数被调用");
                console.log("    参数1: " + args[0]);
                console.log("    参数1(十六进制): 0x" + args[0].toString(16));
                console.log("    参数2: " + args[1]);
                console.log("    参数2(十六进制): 0x" + args[1].toString(16));
                console.log("    参数3: " + args[2]);
                console.log("    参数3(十六进制): 0x" + args[2].toString(16));

                // rcx
                console.log("    RCX: " + this.context.rcx);
                // *rcx
                console.log(hexdump(this.context.rcx, { length: 64 }));
                // rdx
                console.log("    RDX: " + this.context.rdx);
                // *rdx
                console.log(hexdump(this.context.rdx, { length: 64 }));
                // rax
                console.log("    RAX: " + this.context.rax);
                // *rax
                console.log(hexdump(this.context.rax, { length: 64 }));
                // 00000000 struct System_Byte_array // sizeof=0x10020
                // 00000000 {
                // 00000000     Il2CppObject obj;
                // 00000010     Il2CppArrayBounds *bounds;
                // 00000018     il2cpp_array_size_t max_length;
                // 00000020     uint8_t m_Items[65535];
                // 0001001F     // padding byte
                // 00010020 };
            },
            onLeave: function (retval) {
                console.log("[+] 函数返回");
                console.log("    返回值: " + retval);
                console.log(hexdump(retval.readPointer(), { length: 256 }));
            }
        });

        console.log("[*] Hook attached");
    }, 100);
}

// frida_hook();
setImmediate(frida_hook);
```

最后改存档就不用我多说了吧，看了存档你就知道为什么搜内存搜不到金钱数了，它居然是个加了偏移的量。
