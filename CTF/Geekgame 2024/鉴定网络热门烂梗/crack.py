import gzip


def average_bit_count(s):
    return sum(c.bit_count() for c in s) / len(s)


char_set = list(set(x ^ 10 for x in range(0x20, 0x7e+1)))  # index 0~94

print("char_set length: ", len(char_set))

# 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f, 0x30,
# 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e, 0x3f, 0x40, 0x41,
# 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4a, 0x4b, 0x4c, 0x4d,
# 0x4e, 0x4f, 0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d, 0x5e,
# 0x5f, 0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d, 0x6e, 0x6f,
# 0x70, 0x71, 0x72, 0x73, 0x74, 0x76, 0x77, 0x78, 0x79, 0x7a, 0x7b, 0x7c, 0x7d, 0x7e, 0x7f

before_code_list = [
    
]
after_code_list = [
90, 91, 92, 93, 94, 95
]
# 0x7c, 0x7d, 0x7e, 0x7d, 0x7e, 0x7f, 0x7f, 0x7c

first_num = 90
# second_num = 40



def main():
    # assert len(text) <= 1000
    # assert all(0x20 <= ord(c) <= 0x7e for c in text)

    data = bytearray()
    data_before = bytearray()
    data_after = bytearray()

    data_dict = {}
    for i in range(first_num):
        data_dict[char_set[i]] = 1
    # for i in range(first_num, second_num):
    #     data_dict[char_set[i]] = 2
    # for i in range(second_num, 95):
    #     data_dict[char_set[i]] = 3

    
    for c in before_code_list:
        data_before.append(c)
        data_dict[c] -= 1
    
    for c in after_code_list:
        data_after.append(c)
        data_dict[c] -= 1

    
    for k in range(first_num, 95):
        for c, times in data_dict.items():
            for i in range(times):
                data.append(char_set[k])
                data.append(c)


 
    data = data_before + data + data_after
    print(len(data))

    text = gzip.compress(data)
    # print('\nAfter processing:\n')
    print(text)
    print(len(text))

    print(text[43:])
    print(text[43:43+64].hex(' '))

    prefix = (text + b'\xFF'*256)[:256]
    avg_bit = average_bit_count(prefix)

    print('arg_bit: ', avg_bit)

    if avg_bit < 2.5:
        print('\nGood! Flag 1')
    with open('out.gz', 'wb') as f:
        f.write(text)


main()
