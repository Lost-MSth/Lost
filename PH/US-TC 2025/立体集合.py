# set game solver

_cards = [
    (1, 21113),
    (10, 33122),
    (6, 13111),
    (9, 11111),
    (21, 23123),
    (22, 22113),
    (20, 21232),
    (23, 12322),
    (2, 31312),
    (3, 11212),
    (4, 22332),
    (5, 31322),
    (7, 32132),
    (8, 23123),
    (11, 11232),
    (12, 22213),
    (13, 22223),
    (14, 23122),
    (15, 21321),
    (16, 21131),
    (17, 32212),
    (18, 33323),
    (19, 21323),
    (24, 13222),
]

CARD_DICT = {card[0]: card[1] for card in _cards}

main_set = [1, 10, 6, 9, 21, 22, 20, 23]


def is_set(a, b, c):
    # we have 5 features, each feature has 3 values (1, 2, 3)
    for i in range(5):
        va = (a // (10 ** i)) % 10
        vb = (b // (10 ** i)) % 10
        vc = (c // (10 ** i)) % 10

        if not (va == vb == vc or (va != vb and vb != vc and va != vc)):
            return False
    return True


def get_set_binary(a, b, c):
    res = 0
    for i in range(5):
        va = (a // (10 ** i)) % 10
        vb = (b // (10 ** i)) % 10
        vc = (c // (10 ** i)) % 10

        if va == vb == vc:
            res += 1 * (2 ** i)
        elif va != vb and vb != vc and va != vc:
            continue
        else:
            raise ValueError("Not a set")
    return res


def find_sets_for_one_card(card):
    sets = []
    for i in CARD_DICT:
        if i == card:
            continue
        for j in CARD_DICT:
            if j == card or j <= i:
                continue
            if is_set(CARD_DICT[card], CARD_DICT[i], CARD_DICT[j]):
                sets.append((card, i, j))
    return sets


ans = [None] * len(main_set)
ans_binary = [None] * len(main_set)
for i, card in enumerate(main_set):
    ans[i] = find_sets_for_one_card(card)
    ans_binary[i] = [get_set_binary(
        CARD_DICT[a], CARD_DICT[b], CARD_DICT[c]) for (a, b, c) in ans[i]]

print(ans)
print(ans_binary)
