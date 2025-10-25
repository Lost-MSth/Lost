import re

with open('main.svg', 'r', encoding='utf-8') as f:
    svg_data = f.read()

pattern = r'<path style="fill.*rgb\(12.156677%,46.665955%,70.587158%\);.*stroke-opacity:1;stroke-miterlimit:10;(.*)transform="matrix\(0.54474,0,0,-0.54474,(.*),(.*)\)"/>'

matches = re.findall(pattern, svg_data)
print(f"Found {len(matches)} paths.")

points = []

for match in matches:
    path_data = match[0]
    tx = float(match[1])
    ty = float(match[2])

    points.append((tx, ty))

print(points)


def close(a, b):
    return abs(a - b) < 0.001


def get_four_bits(tx, ty):
    r = 0
    if close(135.589464, tx):
        r += 0b11
    elif close(98.745231, tx):
        r += 0b10
    elif close(61.900999, tx):
        r += 1
    elif close(25.056766, tx):
        r += 0
    else:
        raise ValueError("Unknown tx:", tx)

    if close(7.300136, ty):
        r += 0b1100
    elif close(25.6034, ty):
        r += 0b1000
    elif close(43.906664, ty):
        r += 0b0100
    elif close(62.209928, ty):
        r += 0b0000
    else:
        raise ValueError("Unknown ty:", ty)
    return r


flag_chars = []
for i in range(0, len(points)-1, 2):
    tx1, ty1 = points[i]
    tx2, ty2 = points[i+1]
    bits1 = get_four_bits(tx1, ty1)
    bits2 = get_four_bits(tx2, ty2)
    char_code = (bits1 << 4) + bits2
    flag_chars.append(chr(char_code))
flag = ''.join(flag_chars)
print(flag)
