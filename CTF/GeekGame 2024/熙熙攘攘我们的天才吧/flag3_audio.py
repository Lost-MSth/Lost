import struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json

AES_KEY = bytes.fromhex('F3CB8CFA676D563BBEBFC80D3943F10A')


def decrypt_audio_pkt(p):
    typ = int(p['_source']['layers']['rtp']['rtp.p_type'])
    seq = int(p['_source']['layers']['rtp']['rtp.seq'])
    if typ == 127:
        return  # fec
    assert typ == 97

    b = bytes.fromhex(p['_source']['layers']['rtp']
                      ['rtp.payload'].replace(':', ''))
    # https://github.com/LizardByte/Sunshine/blob/190ea41b2ea04ff1ddfbe44ea4459424a87c7d39/src/stream.cpp#L1516
    iv = struct.pack('>i', int('1485042510')+seq) + b'\x00'*12
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    # 930 02D2BAC9D0146

    return unpad(cipher.decrypt(b), 16)


def main():
    with open('audio.json', 'rb') as f:
        data = json.load(f)

    rtp_seq = []
    rtp_pkts = []

    for p in data:
        if not 'rtp' in p['_source']['layers']:
            continue
        data = decrypt_audio_pkt(p)

        # break
        if data:
            # print(data.hex())
            # print()
            rtp_seq.append(int(p['_source']['layers']['rtp']['rtp.seq']))
            rtp_pkts.append(data)
            # seq = int(p['_source']['layers']['rtp']['rtp.seq'])
            # re.append(f'{seq},{data.hex()}\n')

    # 排序
    rtp_seq, rtp_pkts = zip(
        *sorted(zip(rtp_seq, rtp_pkts), key=lambda x: x[0]))
    re = []
    for seq, pkt in zip(rtp_seq, rtp_pkts):
        re.append(f'{seq},{pkt.hex()}\n')

    with open('audio.opus', 'w') as f:
        f.writelines(re)
        # f.write(b''.join(rtp_pkts))


if __name__ == '__main__':
    main()
