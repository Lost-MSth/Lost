def 盲文点数(c: str):
    assert len(c) == 1, "Input must be a single character"
    match c:
        case 'a':
            return 1
        case 'b' | 'c' | 'e' | 'i' | 'k':
            return 2
        case 'd' | 'f' | 'h' | 'j' | 'l' | 'm' | 'o' | 's' | 'u':
            return 3
        case 'g' | 'n' | 'p' | 'r' | 't' | 'v' | 'w' | 'x' | 'z':
            return 4
        case 'q' | 'y':
            return 5
        case _:
            raise ValueError(f"Invalid character: {c}")


def 键盘行数(c: str):
    assert len(c) == 1, "Input must be a single character"
    match c:
        case 'q' | 'w' | 'e' | 'r' | 't' | 'y' | 'u' | 'i' | 'o' | 'p':
            return 1
        case 'a' | 's' | 'd' | 'f' | 'g' | 'h' | 'j' | 'k' | 'l':
            return 2
        case 'z' | 'x' | 'c' | 'v' | 'b' | 'n' | 'm':
            return 3
        case _:
            raise ValueError(f"Invalid character: {c}")


def 旗语夹角(c: str):
    assert len(c) == 1, "Input must be a single character"
    match c:
        case 't' | 'o' | 'h' | 'a' | 'g' | 'z' | 'w':
            return 1
        case 'p' | 'b' | 'j' | 'f' | 'i' | 'x' | 'n' | 'u':
            return 2
        case 'y' | 'm' | 'q' | 's' | 'k' | 'v' | 'c' | 'e':
            return 3
        case 'd' | 'l' | 'r':
            return 4
        case _:
            raise ValueError(f"Invalid character: {c}")


def 夏多线数(c: str):
    assert len(c) == 1, "Input must be a single character"
    match c:
        case 'g' | 'h' | 'i' | 'j':
            return 1
        case 'a' | 'b' | 'c' | 'd' | 'k' | 'l' | 'm' | 'n':
            return 2
        case 'o' | 'p' | 'q' | 'r' | 's' | 't' | 'u' | 'v' | 'w' | 'x' | 'y' | 'z':
            return 3
        case 'e' | 'f':
            return 4
        case _:
            raise ValueError(f"Invalid character: {c}")


def 摩斯位数(c: str):
    assert len(c) == 1, "Input must be a single character"
    match c:
        case 'e' | 't':
            return 1
        case 'a' | 'i' | 'm' | 'n':
            return 2
        case 'd' | 'g' | 'k' | 'o' | 'r' | 's' | 'u' | 'w':
            return 3
        case 'b' | 'c' | 'f' | 'h' | 'j' | 'l' | 'p' | 'q' | 'v' | 'x' | 'y' | 'z':
            return 4
        case _:
            raise ValueError(f"Invalid character: {c}")


def 二进制一数量(n: str):
    assert len(n) == 1, "Input must be a single character"
    n = ord(n) - ord('a') + 1
    return bin(n).count('1')


评委 = [盲文点数, 键盘行数, 旗语夹角, 夏多线数, 摩斯位数, 二进制一数量]


def get_score(word: str, judge):
    # 最多的类型
    x = [judge(c) for c in word]
    counts = [0] * (max(x) + 1)
    for v in x:
        counts[v] += 1
    max_count = max(counts)
    return counts.index(max_count), max_count


def main():
    words = [
        'braille', 'keyboard', 'flag', 'shadow', 'morse', 'binary',
    ]
    for word in words:
        scores = [get_score(word.lower(), func) for func in 评委]
        print(
            f"Word: {word}, Standards: {[i[0] for i in scores]}, Scores: {[i[1] for i in scores]}")


if __name__ == "__main__":
    main()
