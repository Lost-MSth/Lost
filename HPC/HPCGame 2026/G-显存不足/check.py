
BASE = 'base'
COMPARE = 'ans'

def is_close(a, b) -> bool:
    if abs(b) > 1e-3:
        return abs(a - b) / abs(b) <= 0.05
    else:
        return abs(a - b) <= 1e-2


def check(base: float, compare: float) -> bool:
    return is_close(base, compare)


if __name__ == '__main__':
    with open(BASE, 'r') as f:
        base_floats = [float(line.strip()) for line in f.readlines()]
    with open(COMPARE, 'r') as f:
        compare_floats = [float(line.strip()) for line in f.readlines()]
    assert len(base_floats) == len(compare_floats)
    for i, (b, c) in enumerate(zip(base_floats, compare_floats)):
        if not check(b, c):
            print(f'Line {i + 1} differs: base={b}, compare={c}')
            break
    else:
        print('All lines match within tolerance.')