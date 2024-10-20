

with open('1.in', 'r') as f:
    data = f.readlines()

times = 15

re = [f'100 {(times+1)*275} 1 2\n']

re.extend(data[1:])

for j in range(48, 48-times, -1):
    for i in data[1:]:
        x = i.split(' ')
        a = int(x[0])
        b = int(x[1])

        s = ''
        if a != 1 or a != 2:
            s += str(a) + ' '
        else:
            s += str(a+j) + ' '

        if b != 1 or b != 2:
            s += str(b) + ' '
        else:
            s += str(b+j) + ' '

        s += x[2]

        re.append(s)

with open('1.out', 'w') as f:
    f.writelines(re)
