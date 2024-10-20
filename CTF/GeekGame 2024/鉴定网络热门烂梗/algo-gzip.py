# FROM debian:12
# RUN apt update && apt install -y python3 python3-pip

import random
import gzip

from pathlib import Path
try:
    FLAG1 = Path('/flag1').read_text().strip()
    FLAG2 = Path('/flag2').read_text().strip()
except Exception:
    FLAG1 = 'fake{get flag1 on the real server}'
    FLAG2 = 'fake{get flag2 on the real server}'


def average_bit_count(s):
    return sum(c.bit_count() for c in s) / len(s)


def main(text):
    assert len(text) <= 1000
    assert all(0x20 <= ord(c) <= 0x7e for c in text)

    text = [ord(c) ^ 10 for c in text]
    random.seed(11111)
    random.shuffle(text)

    text = gzip.compress(bytes(text))
    # print('\nAfter processing:\n')
    # print(text)

    prefix = (text + b'\xFF'*256)[:256]
    if average_bit_count(prefix) < 2.5:
        print('\nGood! Flag 1: ', FLAG1)
        print(text)

    if b'[What can I say? Mamba out! --KobeBryant]' in text:
        print('\nGood! Flag 2: ', FLAG2)
        print(text)


while True:
    text = ''.join(chr(random.randint(0x20, 0x7e)) for _ in range(1000))
    main(text)
