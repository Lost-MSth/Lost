import numpy as np

TRANSFERS = {
    ('start', '星河'): 1/2,
    ('start', '冷火'): 1/2,

    ('星河', 'End_4'): 1/5,
    ('星河', '鼓舞成功'): 4/5,

    ('鼓舞成功', 'End_8'): 1/16,
    ('鼓舞成功', '星河'): 5/16,
    ('鼓舞成功', '分析成功'): 10/16,

    ('分析成功', 'End_8'): 1/4,
    ('分析成功', '星河'): 1/4,
    ('分析成功', '回答正确'): 2/4,

    ('回答正确', 'End_1'): 19/20,
    ('回答正确', 'End_3'): 1/20,


    ('冷火', 'End_2'): 8/39,
    ('冷火', '成功开口'): 31/39,

    ('成功开口', 'End_2'): 1/10,
    ('成功开口', '冷火'): 4/10,
    ('成功开口', 'End_6'): 1/10,
    ('成功开口', '借到手机'): 4/10,

    ('借到手机', 'End_6'): 1/4,
    ('借到手机', '成功开口'): 1/4,
    ('借到手机', 'End_7'): 1/4,
    ('借到手机', '成功下载木马'): 1/4,

    ('成功下载木马', 'End_7'): 1/10,
    ('成功下载木马', '借到手机'): 4/10,
    ('成功下载木马', '下载部分文件'): 4/10,
    ('成功下载木马', 'End_5'): 1/10,

    ('下载部分文件', '成功下载木马'): 1/2,
    ('下载部分文件', 'End_5'): 1/2,


    ('End_1', 'End_1'): 1,
    ('End_2', 'End_2'): 1,
    ('End_3', 'End_3'): 1,
    ('End_4', 'End_4'): 1,
    ('End_5', 'End_5'): 1,
    ('End_6', 'End_6'): 1,
    ('End_7', 'End_7'): 1,
    ('End_8', 'End_8'): 1,
}


KEYS = set()
for a, b in TRANSFERS.keys():
    KEYS.add(a)
    KEYS.add(b)
KEYS = list(sorted(KEYS))
print(KEYS)


T = np.zeros((len(KEYS), len(KEYS)))
for (a, b), prob in TRANSFERS.items():
    i, j = KEYS.index(a), KEYS.index(b)
    T[i, j] = prob

start_index = KEYS.index('start')
print(start_index)
x = np.zeros(len(KEYS))
x[start_index] = 1


x = x @ np.linalg.matrix_power(T, 10000)

print(x)
print(''.join(map(lambda i: chr(64 + round(i*100)), x[:8])))
