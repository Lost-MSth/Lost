#!/usr/bin/env python3

import sys
import os
import gzip


def read_file(fpath):
    f = open(fpath, "rb")
    return f.read()


def xor(first, second):
    result = []
    for i, b in enumerate(first[:-512]):
        if i >= len(second):
            break
        result.append((b ^ second[i]).to_bytes(1, byteorder='little'))
    return b''.join(result)


def recover_keystream(first, second):
    print(F"Recovering keystream from {first} and {second}")
    rf1 = read_file(first)
    rf2 = read_file(second)
    print(F"Read {len(rf1)-512} bytes from {first}")
    print(F"Read {len(rf2)} bytes from {second}")
    keystream = xor(rf1, rf2)
    return keystream


def xor_with_keystream(keystream, ct):
    r = []
    for i, b in enumerate(ct):
        r.append((b ^ keystream[i % len(keystream)]
                  ).to_bytes(1, byteorder='little'))
    return b''.join(r)


def recover_file_data(keystream, target_file):
    ct = read_file(target_file)
    pt = xor_with_keystream(keystream, ct)
    return pt


def enum_pt_files(pt_files, start_dir):
    matched_file = None
    enc_file = None
    largest = 0
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            for pt_file in pt_files:
                if pt_file['filename'] in file:
                    if pt_file['size'] > largest and pt_file['size'] == os.path.getsize(os.path.join(root, file))-512:
                        print(
                            F"Found: {os.path.join(root, file)} with {pt_file['filename']}")
                        matched_file = pt_file['path']
                        enc_file = os.path.join(root, file)
                        largest = pt_file['size']
    return matched_file, enc_file


def decrypt_all_files(keystream, enc_extension, start_dir):
    for root, dirs, files in os.walk(start_dir):
        for file in files:
            if enc_extension in file:
                print(F"Decrypting: {os.path.join(root, file)}")
                rdata = recover_file_data(keystream, os.path.join(root, file))
                orig_fname = ".".join(file.split(".")[:-1])
                f = open(os.path.join(root, orig_fname), "wb")
                f.write(rdata[:-512])
                f.close()


def get_pt_files(pt_dir):
    found_files = []
    for root, dirs, files in os.walk(pt_dir):
        for file in files:
            found_files.append({
                'size':  os.path.getsize(os.path.join(root, file)),
                'filename': file,
                'path': os.path.join(root, file)
            })
    return found_files


# if (len(sys.argv) < 2):
#     print(F"{sys.argv[0]} [Known Plaintext File Dir] [Start Directory]")
# else:
#     pt_file_dir = sys.argv[1]
#     start_dir = sys.argv[2]
#     pt_files = get_pt_files(pt_file_dir)
#     print(F"Found pt files: {pt_files}")
#     matched_file, enc_file = enum_pt_files(pt_files, start_dir)
#     print(
#         F"Matched plaintext file: {matched_file} // Matched Encrypted File: {enc_file}")
#     keystream = recover_keystream(enc_file, matched_file)
#     print(F"Length of the keystream: {len(keystream)}")
#     print(F"Recovered keystream: {keystream[:256].hex()}")
#     enc_ext = enc_file.split(".")[-1]
#     print(F"Searching for files with the encrypted extension: {enc_ext}")
#     decrypt_all_files(keystream, enc_ext, start_dir)


def main():
    targets = [
        'geekgame-4th/official_writeup/algo-gzip/attachment/algo-gzip.f58A66B51.py',
        'geekgame-5th/problemset/misc-ransomware/flag1-2-3.f58A66B51.txt',
        'flag-is-not-stored-in-this-file.f58A66B51.zip',
    ]
    # plain_path = 'geekgame-4th/official_writeup/algo-gzip/attachment/algo-gzip.py'
    # enc_path = targets[0]
    plain_path = 'flag-is-not-stored-in-this-file.zip'
    enc_path = targets[-1]
    keystream = recover_keystream(enc_path, plain_path)
    print(F"Length of the keystream: {len(keystream)}")
    print(F"Recovered keystream: {keystream.hex()}")

    for x in targets:
        print(F"Decrypting file: {x}")
        decrypted_data = recover_file_data(keystream, x)
        print(decrypted_data[:-512].decode('utf-8', errors='ignore'))
        with open(os.path.basename(x).replace('.f58A66B51', ''), "wb") as f:
            f.write(decrypted_data[:-512])
        print(decrypted_data[-512:])
        print()

    # zip_file = targets[-1]
    # decrypted_data = recover_file_data(keystream, zip_file)[:-512]
    # with open("recovered.zip", "wb") as f:
    #     f.write(decrypted_data)


if __name__ == "__main__":
    main()
