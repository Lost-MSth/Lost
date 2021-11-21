###
### A modified verion of Blue Midnight Wish. Used by some version of Arcaea.
###
### The BMW original source:
###      https://web.archive.org/web/20170329092631/http://people.item.ntnu.no/~danilog/Hash/BMW-SecondRound/
###      Files: Reference_Implementation/BlueMidnightWish_ref.c
###	            Reference_Implementation/SHA3api_ref.h
###      Documentation: Supporting_Documentation/Round2Mods.pdf
###

from numpy import uint64, errstate
from typing import List

# One comment in the C++ implementation mentions that the sum of 
# ExpandRounds1 and ExpandRounds2 must be 16. I don't understand
# but I will note it down here.
ExpandRounds1 = 5
ExpandRounds2 = 11

def BMW384(message : bytes) -> bytes:
    """
    Implements the BMW384 algorithm. 

    inputs:
        message is assumed to contain whole bytes.

    returns:
        The BMW384 result.
    """
    M = preprocess(message)
    H = bytearray.fromhex('0001020304050607 08090A0B0C0D0E0F'
                        + '1011121314151617 18191A1B1C1D1E1F'
                        + '2021222324252627 28292A2B2C2D2E2F'
                        + '3031323334353637 38393A3B3C3D3E3F'
                        + '4041424344454647 48494A4B4C4D4E4F'
                        + '5051525354555657 58595A5B5C5D5E5F'
                        + '6061626364656667 68696A6B6C6D6E6F'
                        + '7071727374757677 78797A7B7C7D7E7F')
    H = bytes_to_list(H, 'big')
    N = len(M) // 16
    Q = [uint64(0) for _ in range(32)]
    for i in range(N):
        block = M[i * 16 : (i + 1) * 16]
        f(block, H, Q)

    ### Finalize
    CONSTH = bytearray.fromhex('aaaaaaaaaaaaaaa0 aaaaaaaaaaaaaaa1'
		                     + 'aaaaaaaaaaaaaaa2 aaaaaaaaaaaaaaa3'
		                     + 'aaaaaaaaaaaaaaa4 aaaaaaaaaaaaaaa5'
		                     + 'aaaaaaaaaaaaaaa6 aaaaaaaaaaaaaaa7' 
		                     + 'aaaaaaaaaaaaaaa8 aaaaaaaaaaaaaaa9' 
		                     + 'aaaaaaaaaaaaaaaa aaaaaaaaaaaaaaab' 
		                     + 'aaaaaaaaaaaaaaac aaaaaaaaaaaaaaad' 
		                     + 'aaaaaaaaaaaaaaae aaaaaaaaaaaaaaaf')
    CONSTH = bytes_to_list(CONSTH, 'big')
    f(H, CONSTH, Q)

    result = bytearray()
    for i in range(10, 16):
        result.extend(int(CONSTH[i]).to_bytes(8, byteorder='little'))

    return bytes(result)


def preprocess(message : bytes) -> List[uint64]:
    length = len(message)
    message = bytearray(message)
    
    ### Padding
    message.append(128)
    padding_len = (120 - length % 128 - 1) % 128
    for i in range(padding_len):
        message.append(0)
    message.extend((length * 8).to_bytes(8, byteorder='little'))

    return bytes_to_list(message, 'little')

def f(M : List[uint64], H : List[uint64], Q : List[uint64]) -> None:
    with errstate(over='ignore'):
        ### f0
        W = [uint64(0) for _ in range(16)]
        W[0] = (M[5] ^ H[5]) - (M[7] ^ H[7]) + (M[10] ^ H[10]) + (M[13] ^ H[13]) + (M[14] ^ H[14])
        W[1] = (M[6] ^ H[6]) - (M[8] ^ H[8]) + (M[11] ^ H[11]) + (M[14] ^ H[14]) - (M[15] ^ H[15])
        W[2] = (M[0] ^ H[0]) + (M[7] ^ H[7]) + (M[9] ^ H[9]) - (M[12] ^ H[12]) + (M[15] ^ H[15])
        W[3] = (M[0] ^ H[0]) - (M[1] ^ H[1]) + (M[8] ^ H[8]) - (M[10] ^ H[10]) + (M[13] ^ H[13])
        W[4] = (M[1] ^ H[1]) + (M[2] ^ H[2]) + (M[9] ^ H[9]) - (M[11] ^ H[11]) - (M[14] ^ H[14])
        W[5] = (M[3] ^ H[3]) - (M[2] ^ H[2]) + (M[10] ^ H[10]) - (M[12] ^ H[12]) + (M[15] ^ H[15])
        W[6] = (M[4] ^ H[4]) - (M[0] ^ H[0]) - (M[3] ^ H[3]) - (M[11] ^ H[11]) + (M[13] ^ H[13])
        W[7] = (M[1] ^ H[1]) - (M[4] ^ H[4]) - (M[5] ^ H[5]) - (M[12] ^ H[12]) - (M[14] ^ H[14])
        W[8] = (M[2] ^ H[2]) - (M[5] ^ H[5]) - (M[6] ^ H[6]) + (M[13] ^ H[13]) - (M[15] ^ H[15])
        W[9] = (M[0] ^ H[0]) - (M[3] ^ H[3]) + (M[6] ^ H[6]) - (M[7] ^ H[7]) + (M[14] ^ H[14])
        W[10] = (M[8] ^ H[8]) - (M[1] ^ H[1]) - (M[4] ^ H[4]) - (M[7] ^ H[7]) + (M[15] ^ H[15])
        W[11] = (M[8] ^ H[8]) - (M[0] ^ H[0]) - (M[2] ^ H[2]) - (M[5] ^ H[5]) + (M[9] ^ H[9])
        W[12] = (M[1] ^ H[1]) + (M[3] ^ H[3]) - (M[6] ^ H[6]) - (M[9] ^ H[9]) + (M[10] ^ H[10])
        W[13] = (M[2] ^ H[2]) + (M[4] ^ H[4]) + (M[7] ^ H[7]) + (M[10] ^ H[10]) + (M[11] ^ H[11])
        W[14] = (M[3] ^ H[3]) - (M[5] ^ H[5]) + (M[8] ^ H[8]) - (M[11] ^ H[11]) - (M[12] ^ H[12])
        W[15] = (M[12] ^ H[12]) - (M[4] ^ H[4]) - (M[6] ^ H[6]) - (M[9] ^ H[9]) + (M[13] ^ H[13])

        Q[0] = s64_0(W[0]) + H[1]
        Q[1] = s64_1(W[1]) + H[2]
        Q[2] = s64_2(W[2]) + H[3]
        Q[3] = s64_3(W[3]) + H[4]
        Q[4] = s64_4(W[4]) + H[5]
        Q[5] = s64_0(W[5]) + H[6]
        Q[6] = s64_1(W[6]) + H[7]
        Q[7] = s64_2(W[7]) + H[8]
        Q[8] = s64_3(W[8]) + H[9]
        Q[9] = s64_4(W[9]) + H[10]
        Q[10] = s64_0(W[10]) + H[11]
        Q[11] = s64_1(W[11]) + H[12]
        Q[12] = s64_2(W[12]) + H[13]
        Q[13] = s64_3(W[13]) + H[14]
        Q[14] = s64_4(W[14]) + H[15]
        Q[15] = s64_0(W[15]) + H[0]

        ### f1
        for i in range(ExpandRounds1):
            Q[i + 16] = expand1(i + 16, Q, H, M)
        for i in range(ExpandRounds1, ExpandRounds1 + ExpandRounds2):
            Q[i + 16] = expand2(i + 16, Q, H, M)

        ### f2
        XL64 = uint64(Q[16] ^ Q[17] ^ Q[18] ^ Q[19] ^ Q[20] ^ Q[21] ^ Q[22] ^ Q[23])
        XH64 = uint64(XL64 ^ Q[24] ^ Q[25] ^ Q[26] ^ Q[27] ^ Q[28] ^ Q[29] ^ Q[30] ^ Q[31])
        H[0] = ((XH64 << uint64(5)) ^ (Q[16] >> uint64(5)) ^ M[0]) + (XL64 ^ Q[24] ^ Q[0])
        H[1] = ((XH64 >> uint64(7)) ^ (Q[17] << uint64(8)) ^ M[1]) + (XL64 ^ Q[25] ^ Q[1])
        H[2] = ((XH64 >> uint64(5)) ^ (Q[18] << uint64(5)) ^ M[2]) + (XL64 ^ Q[26] ^ Q[2])
        H[3] = ((XH64 >> uint64(1)) ^ (Q[19] << uint64(5)) ^ M[3]) + (XL64 ^ Q[27] ^ Q[3])
        H[4] = ((XH64 >> uint64(3)) ^ Q[20] ^ M[4]) + (XL64 ^ Q[28] ^ Q[4])
        H[5] = ((XH64 << uint64(6)) ^ (Q[21] >> uint64(6)) ^ M[5]) + (XL64 ^ Q[29] ^ Q[5])
        H[6] = ((XH64 >> uint64(4)) ^ (Q[22] << uint64(6)) ^ M[6]) + (XL64 ^ Q[30] ^ Q[6])
        H[7] = ((XH64 >> uint64(11)) ^ (Q[23] << uint64(2)) ^ M[7]) + (XL64 ^ Q[31] ^ Q[7])

        H[8] = ROTL(H[4], 9) + (XH64 ^ Q[24] ^ M[8]) + ((XL64 << uint64(8)) ^ Q[23] ^ Q[8])
        H[9] = ROTL(H[5],10) + (XH64 ^ Q[25] ^ M[9]) + ((XL64 >> uint64(6)) ^ Q[16] ^ Q[9])
        H[10] = ROTL(H[6],11) + (XH64 ^ Q[26] ^ M[10]) + ((XL64 << uint64(6)) ^ Q[17] ^ Q[10])
        H[11] = ROTL(H[7],12) + (XH64 ^ Q[27] ^ M[11]) + ((XL64 << uint64(4)) ^ Q[18] ^ Q[11])
        H[12] = ROTL(H[0],13) + (XH64 ^ Q[28] ^ M[12]) + ((XL64 >> uint64(3)) ^ Q[19] ^ Q[12])
        H[13] = ROTL(H[1],14) + (XH64 ^ Q[29] ^ M[13]) + ((XL64 >> uint64(4)) ^ Q[20] ^ Q[13])
        H[14] = ROTL(H[2],15) + (XH64 ^ Q[30] ^ M[14]) + ((XL64 >> uint64(7)) ^ Q[21] ^ Q[14])
        H[15] = ROTL(H[3],16) + (XH64 ^ Q[31] ^ M[15]) + ((XL64 >> uint64(2)) ^ Q[22] ^ Q[15])

def expand1(i : int, Q : List[uint64], H : List[uint64], M : List[uint64]) -> uint64:
    return uint64(s64_1(Q[i - 16]) + s64_2(Q[i - 15]) + s64_3(Q[i - 14]) + s64_0(Q[i - 13])
          + s64_1(Q[i - 12]) + s64_2(Q[i - 11]) + s64_3(Q[i - 10]) + s64_0(Q[i - 9])
		  + s64_1(Q[i - 8]) + s64_2(Q[i - 7]) + s64_3(Q[i - 6]) + s64_0(Q[i - 5])
		  + s64_1(Q[i - 4]) + s64_2(Q[i - 3]) + s64_3(Q[i - 2]) + s64_0(Q[i - 1])
          + (uint64(uint64(i * 0x0555555555555555) + ROTL(M[(i - 16) % 16], ((i - 16) % 16) + 1) 
                         + ROTL(M[(i - 13) % 16], ((i - 13) % 16) + 1) 
                         - ROTL(M[(i - 6) % 16], ((i - 6) % 16) + 1)) ^ H[(i - 16 + 7) % 16]))
        
def expand2(i : int, Q : List[uint64], H : List[uint64], M : List[uint64]) -> uint64:
    return uint64(Q[i - 16] + ROTL(Q[i - 15], 5) + Q[i - 14] + ROTL(Q[i - 13], 11)
           + Q[i - 12] + ROTL(Q[i - 11], 27) + Q[i - 10] + ROTL(Q[i - 9], 32)
		   + Q[i - 8] + ROTL(Q[i - 7], 37) + Q[i - 6] + ROTL(Q[i - 5], 43)
		   + Q[i - 4] + ROTL(Q[i - 3], 53) + s64_4(Q[i - 2]) + s64_5(Q[i - 1])
           + (uint64(uint64(i * 0x0555555555555555) + ROTL(M[(i - 16) % 16], ((i - 16) % 16) + 1) 
                          + ROTL(M[(i - 13) % 16], ((i - 13) % 16) + 1) 
                          - ROTL(M[(i - 6) % 16], ((i - 6) % 16) + 1)) ^ H[(i - 16 + 7) % 16]))

def s64_0(x : uint64) -> uint64:
    return (x >> uint64(1)) ^ (x << uint64(3)) ^ ROTL(x, 4) ^ ROTL(x, 37)

def s64_1(x : uint64) -> uint64:
    return (x >> uint64(1)) ^ (x << uint64(2)) ^ ROTL(x, 13) ^ ROTL(x, 43)

def s64_2(x : uint64) -> uint64:
    return (x >> uint64(2)) ^ (x << uint64(1)) ^ ROTL(x, 19) ^ ROTL(x, 53)
    
def s64_3(x : uint64) -> uint64:
    return (x >> uint64(2)) ^ (x << uint64(2)) ^ ROTL(x, 28) ^ ROTL(x, 59)

def s64_4(x : uint64) -> uint64:
    return (x >> uint64(1)) ^ x

def s64_5(x : uint64) -> uint64:
    return (x >> uint64(2)) ^ x

def ROTL(x : uint64, n : int) -> uint64:
    return (x << uint64(n)) | (x >> uint64(64 - n))

def bytes_to_list(b : bytes, endianness : str) -> List[uint64]:
    """
    Convert bytes type to a list of numpy.uint64. Each uint64 consists of 8 bytes.
    
    inputs:
        endianness should be either 'little' or 'big'. If one does not work try the
        other one.
    """
    length = len(b)
    M = []
    i = 0
    while i < length:
        M.append(uint64(int.from_bytes(b[i : i + 8], byteorder=endianness, signed=False)))
        i += 8

    return M

