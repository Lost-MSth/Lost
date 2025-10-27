with open('写生.txt', 'r', encoding='utf-8') as file:
    content = file.read()
    print(len(content))
    print(content[0])
    print(content[-1])


ratios = [(24, 25), (3, 2), (8, 3), (25, 6)]
length = len(content)

for i, ratio in enumerate(ratios):

    width = int((length * ratio[0] / ratio[1]) ** 0.5)
    height = int((length * ratio[1] / ratio[0]) ** 0.5)
    print(f'宽高比: {ratio[0]}:{ratio[1]} (宽度: {width}, 高度: {height})')

    with open(f'写生_{i+1}.txt', 'w', encoding='utf-8') as file:
        file.write(
            f'宽高比: {ratio[0]}:{ratio[1]} (宽度: {width}, 高度: {height})\n\n')
        # 每行 width，换行
        for j in range(0, length, width):
            file.write(content[j:j+width] + '\n')
