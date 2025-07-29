def count_dots_in_pigpen(words):
    def count_char(char):
        if 'j' <= char <= 'r':
            return 1
        elif 'w' <= char <= 'z':
            return 1
        return 0

    count = sum(count_char(char.lower()) for char in words if char.isalpha())
    return count


def main():

    with open('date.txt') as f:
        lines = f.readlines()
        lines = list(map(lambda x: x.strip(), lines))

    date = {}
    for line in lines:
        index, others = line.split(' ', 1)
        start = others.index('(')
        end = others.index(')')
        text = others[start+1:end]
        key = text.replace(' ', '').lower()
        date[key] = index

    # print(date)

    with open('ans.txt') as f:
        lines = f.readlines()
    lines = list(map(lambda x: x.strip(), lines))

    answers = []
    for line in lines:
        words = line.replace(' ', '').lower()
        answers.append(words)

    # print(answers)
    meta_1 = answers[:9]
    meta_2 = answers[10:19]
    meta_3 = answers[20:29]
    print(meta_1, meta_2, meta_3)

    r = []

    for i, words in enumerate(meta_1):
        x = None
        for key in date.keys():
            if key in words:
                x = key
                # print(words, key, date[key], count_dots_in_pigpen(words))

        if x is None:
            print('No match found for:', words)
            continue

        index = int(date[x]) - 1
        two_chars = meta_2[i][::-1][index:index+2]
        print(index, meta_2[i])
        print(two_chars)
        r.append(two_chars)

    dot_nums = []
    for words in meta_3:
        dot_nums.append(count_dots_in_pigpen(words))

    sorted_pairs = sorted(zip(r, dot_nums), key=lambda x: x[1])
    sorted_pairs = [pair[0] for pair in sorted_pairs]
    print(sorted_pairs)
    plaintext = ''.join(sorted_pairs)[::-1]
    print(plaintext)
    # answer is red herring


if __name__ == '__main__':
    main()
