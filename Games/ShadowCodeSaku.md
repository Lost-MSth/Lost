---
modify_date: "2025-07-15 18:00:00"
---

# 特务朔的秘密行动

SAKU The Covert Agent

Forward

## 类型

- 355 MB -> 1.18 GB
- ADV + 小游戏
- 现实世界
- 单线 -> 单线，两个结局

## 评价

一遍完整通关约 1 小时。

总体而言有点意思可圈可点，但意犹未尽总觉得未完待续虎头蛇尾。无码加画风一眼国产，整体是个非常短小的故事，完全可以去玩一玩。

剧情是本作核心，男主是超级黑客 Shadow Code，喜欢装英雄助人为乐执行正义。女主是某组织里的底层特工，来找男主请求调查组织的黑幕。两人相识后感情逐渐升温，一边追寻真相一边干起来了，最后女主去处理自身麻烦，约定二人以后再见。

剧情整体普通但其实感觉没讲完，可以出续作的，而且支线意义不明，感觉是想要写些大的但不得不草草发售一样。

游戏玩法是一堆益智小游戏，动动鼠标和键盘就能完成，没啥难度。

H 事件数量很少，但相比于剧情长度来说还算正常数量。玩法正常且纯爱，HCG 是 Live2D 动态的，立绘是静态的，画风中等偏上。女主全日语配音，有音效。

UI 美术不错，很有潜力，但是交互体验较差，也算是国产通病了……Bug 也挺多，**记得用繁体中文**，简体会导致对话文本消失的。

要说我对本作有何偏爱，我只能说这部作品在“黑客”方面似乎并不像别的作品（特别是电影、电视剧、动画）一样很糊弄，起码是深入调查了一些东西的。虽然男主神一般的奇奇怪怪技术让我以为他是魔法少男，远程将电话爆改成 AED 是什么操作啊……背景文字里可以看到具体操作，比如要黑进服务器时先 Nmap 扫端口，再查各种 CVE 漏洞，再弱密码，然后登入 `whoami` 一下发现是 `root` 权限就成功了。另外比如调用各种脚本，连接设备刷固件，用 FFmpeg 提取媒体数据什么的，起码他用的脚本操作和剧情说的能够对上，而且很合理，这实在是难得一见的。

不过换个角度想一想，这是不是一个网安专业的单身毕业生来做游戏了，幻想自己技术强无敌的同时还有妹子送上门约定终身，什么宅男桃子幻想啊喂！

最后的最后，我玩的原因纯粹是因为女主她好看啊！特工的连体衣真的太色了啊！多画一点可以吗！

## 后续评价

完整重新通关一遍后宫结局花费 2 小时。

存档好像不可以继承，会没法进行新的任务，也就是死档了。所以我是从头重打的。

剧情的话，两人云雨一番后互相表白，女主说不能耽误男主的工作，于是离开了，新的故事从这里继续开始。男主例行工作救了个笨蛋怪盗小姑娘，也就是第二女主露西，和她合作偷取了一块有纪念意义的宝石，并提到了男主在追寻的 Luna 组织。之后，被组织盯上的男主被反过来骇入，被线下包围之际，露西救了他。两人反击，露西线下抓住了冷面黑客，也就是第三女主晦，她是和朔同属 Luna 组织的特务。得知真相后，晦借机加入他们，全面打击组织。最终战，晦和露西直捣黄龙，男主声东击西被杀手抓住，朔过来帮忙打赢白刃战。最后，朔带着孩子们归来了，男主他们制造并维护了一个没有 Luna 组织的城市。

结局有两个，最后选朔还是选三个一起，我当然毫不犹豫选择后宫结局，似乎另一条线的 H 事件也会在梦里回收。不过游戏存档功能不完善，并不能读档重选，避免麻烦我也只选了一个结局。不过这才算这游戏剧情写完了啊，之前那完全是在逗我玩呢。

支线变长了，也变得逆天了不少，当然对主线作用不大。

Bug 也多了不少，比如那个吃播的支线一直在刷，CG 里面另一个结局相关内容无法自动解锁。当然之前的 bug 修了，可以用简体中文了。

新加的解密小游戏变难、变多、变烦了很多，感觉制作组走偏了，真没有必要在这方面为难玩家，很容易把人玩红温啊。

H 事件和色图数量增加了不少，画风倒是没什么进步。

女二的类似兔女郎的紧身衣和女三的镂空连体衣也很棒！

## 破解

资源未加密，AssetRipper 可以提取。但是存档有加密，是 `.sav` 文件，位置就在游戏文件夹中的 `SaveData` 里面。

注意到游戏使用了 `GameAssembly.dll`，逆向就困难多了，不过 `global-metadata.dat` 没有加密，挺好，直接 Il2CppDumper 开搞，弄出符号表后交给 IDA Pro 反编译。

不是哥们这二进制怎么这么大，分析起来老半天啊……加载完导入符号表后，找关键函数扔给 DeepSeek V4 Pro 写出加密解密脚本即可：

```python
import base64
import hashlib

from Crypto.Cipher import AES
from Crypto.Hash import MD5, SHA1
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad

# ==================== 从游戏内提取的真实参数（需你手动填入） ====================
SECRET = "kQEaRRUwgYSjrM0+P0w/JYJC8gpwId7Gy2S/lpwJpWI="      # 加密密钥种子
ENCODING = "utf-8"                               # 解密后的字符串编码，通常是 utf-8
PBKDF2_ITERATIONS = 1000                         # PBKDF2 迭代次数，默认 1000
# =============================================================================


def derive_key_iv(secret: str) -> tuple[bytes, bytes]:
    """根据 secret 生成 AES 密钥和 IV"""
    # 1. 计算 secret 的 MD5 作为 PBKDF2 的盐
    md5_hash = MD5.new(secret.encode('utf-8')).digest()  # 16 字节
    # 2. PBKDF2 派生 32+16=48 字节
    derived = PBKDF2(
        password=secret.encode('utf-8'),
        salt=md5_hash,
        dkLen=48,                    # 32 字节 key + 16 字节 IV
        count=PBKDF2_ITERATIONS,
        hmac_hash_module=SHA1        # .NET 默认使用 HMAC-SHA1
    )
    key = derived[:32]
    iv = derived[32:48]
    return key, iv


def encrypt_save(plaintext: str) -> str:
    """将存档字符串加密为 Base64 密文"""
    plain_bytes = plaintext.encode(ENCODING)
    # 计算明文的 SHA256 哈希
    sha256_hash = hashlib.sha256(plain_bytes).digest()  # 32 字节
    # 拼接明文和哈希
    to_encrypt = plain_bytes + sha256_hash
    # 密钥派生
    key, iv = derive_key_iv(SECRET)
    # AES-CBC 加密
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(to_encrypt, AES.block_size))
    # Base64 编码
    return base64.b64encode(ciphertext).decode('ascii')


def decrypt_save(b64_ciphertext: str) -> str:
    """将 Base64 密文解密为存档字符串，若数据被篡改则抛出异常"""
    ciphertext = base64.b64decode(b64_ciphertext)
    key, iv = derive_key_iv(SECRET)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # 解密并去除填充
    padded_plain = cipher.decrypt(ciphertext)
    try:
        decrypted = unpad(padded_plain, AES.block_size)
    except ValueError:
        raise ValueError("解密失败：密钥错误或数据损坏")

    # 分离明文和末尾的 SHA256 哈希
    if len(decrypted) < 32:
        raise ValueError("解密数据太短，无法提取哈希")
    plain_bytes = decrypted[:-32]
    hash_received = decrypted[-32:]

    # 验证完整性
    hash_calculated = hashlib.sha256(plain_bytes).digest()
    if hash_received != hash_calculated:
        raise ValueError("存档完整性校验失败！数据可能被篡改或密钥错误。")

    return plain_bytes.decode(ENCODING)


# ==================== 使用示例 ====================
if __name__ == "__main__":
    file_name = 'GlobalData.sav'
    method = 'decrypt'  # 'encrypt' 或 'decrypt'
    try:
        if method == 'encrypt':
            with open(f'{file_name}.json', 'r', encoding=ENCODING) as f:
                data = f.read()
            new_enc = encrypt_save(data)
            print("加密成功，存档内容：")
            print(new_enc)
            with open(file_name, 'wb') as f:
                f.write(new_enc.encode('ascii'))
        elif method == 'decrypt':
            with open(file_name, 'rb') as f:
                saved_base64 = f.read()
            data = decrypt_save(saved_base64)
            print("解密成功，存档内容：")
            print(data)
            with open(f'{file_name}.json', 'w', encoding=ENCODING) as f:
                f.write(data)

    except Exception as e:
        print("错误：", e)
```

`GlobalData.sav` 里的 `Flags` 中，我缺了 `FlagCGEnd1`、`FlagEnd1_1` 和 `FlagEnd1_2`，补上去即可。这其实是已经看过的做梦的另一个结局的内容，只不过不知道为什么不自动解锁。
