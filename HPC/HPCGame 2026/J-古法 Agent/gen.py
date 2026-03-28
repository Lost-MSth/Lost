# 你的程序应当接受三个参数。

# 第一个参数为读入的文本串文件路径。其中：

# 前 8 字节：uint64_t N，表示文本总长度（字节）。
# 后续数据：N 字节的仅包含小写字母的字符串。
# 第二个参数为读入的模式串文件路径。其中：

# 前 4 字节：uint32_t K，表示模式串的数量。
# 后续数据：K × 64 字节。每个模式串固定长度为 64 字节。
# 第三个参数为你的程序输出文件的路径。其中仅包含 8 字节，表示所有模式串在文本串中的匹配次数之和。


# 这是这道题的数据生成器
# 子任务	文本串大小	模式串数量	其他部分的工作负载	满分时间	超时时间	基础分值	满分	总功耗限制
# 0	1G	512	恒定为 0	3s	10s	10	40	600W
# 1	1G	512	恒定为某固定值	6s	20s	5	20	600W
# 2	1G	512	随机，以满分时间为周期循环	6s	20s	10	40	600W


import os
import random
import string
import struct
import sys

LENGTH = 1 * 1024 * 1024 * 1024  # 1 GB
PATTERN_COUNT = 512
ANS = 312
assert ANS <= PATTERN_COUNT

TEXT_FILE = "text.bin"
PATTERN_FILE = "patterns.bin"


def generate_input(text_file_path, pattern_file_path):
    # Generate pattern strings
    pattern_list = []
    with open(pattern_file_path, 'wb') as f:
        f.write(struct.pack('I', PATTERN_COUNT))  # Write count as uint32_t
        for _ in range(PATTERN_COUNT):
            pattern_list.append(random.choices(string.ascii_lowercase, k=64))
            pattern = ''.join(pattern_list[-1])
            f.write(pattern.encode('utf-8'))  # Write each pattern string

    # Generate text string
    text = random.choices(string.ascii_lowercase, k=LENGTH)

    # 修改部分，确保有 ANS 个模式串匹配
    should_match_indices = random.sample(range(PATTERN_COUNT), ANS)
    for idx in should_match_indices:
        pos = random.randint(0, LENGTH - 64)
        text[pos:pos + 64] = pattern_list[idx]

    text = ''.join(text)
    with open(text_file_path, 'wb') as f:
        f.write(struct.pack('Q', LENGTH))  # Write length as uint64_t
        f.write(text.encode('utf-8'))  # Write text string


if __name__ == "__main__":
    generate_input(TEXT_FILE, PATTERN_FILE)
    print(f"Generated input files: {TEXT_FILE}, {PATTERN_FILE}")
