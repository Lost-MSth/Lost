import os
import sys
import zipfile

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将两个文件打包成 zip：
- 第一个文件使用存储模式（store，非压缩）
- 第二个文件使用 deflate（flate）压缩

用法:
    python get_zip.py 输出.zip 第一个文件路径 第二个文件路径

示例:
    python get_zip.py out.zip a.txt b.bin
"""


def main():

    out_zip = 'test.zip'
    first_path = 'no-flag-here'
    second_path = 'also-not-here'

    for p in (first_path, second_path):
        if not os.path.isfile(p):
            print(f"不存在或不是文件: {p}", file=sys.stderr)
            sys.exit(1)

    # 默认使用 ZIP_STORED，确保第一个文件不压缩
    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_STORED) as zf:
        # 第一个：store（不压缩）
        zf.write(first_path, arcname=os.path.basename(
            first_path), compress_type=zipfile.ZIP_STORED)

        # 第二个：deflate（flate）压缩
        # 若需要自定义压缩等级，可传 compresslevel=1..9（需 Python 3.7+）
        zf.write(second_path, arcname=os.path.basename(
            second_path), compress_type=zipfile.ZIP_DEFLATED)

    print(f"已生成: {out_zip}")


if __name__ == "__main__":
    main()
