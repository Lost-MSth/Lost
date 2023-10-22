import zlib

CHUNKSIZE = 1024 * 16

d = zlib.decompressobj(16+zlib.MAX_WBITS)

f = open('g77.gz', 'rb')

buffer = f.read(CHUNKSIZE)
f.seek(0x0e0eb70d8)

data = b''
while buffer:
    # flag = False
    # std = buffer[0]
    # for x in buffer:
    #     if x != std:
    #         flag = True
    #         break
    # if not flag:
    #     buffer = f.read(CHUNKSIZE)
    #     continue
    outstr = d.decompress(buffer)
    # print(outstr)
    for x in outstr:
        if x:
            data += bytes([x])
    buffer = f.read(CHUNKSIZE)
    if data != b'':
        print(data)
        break


outstr = d.flush()
print(outstr)

f.close()
