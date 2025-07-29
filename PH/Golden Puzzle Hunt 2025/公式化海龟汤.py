from sympy import Eq, solve, symbols

A, a, i, d, e, h, o, t, s, n, r = symbols(
    'A a i d e h o t s n r', integer=True)

eqs = [
    Eq(A*a*A*d, 960),
    Eq(A*A*A*i*e, 128),
    Eq(A*h*o+A, 272),
    Eq(A*A*o*t*h, 2160),
    Eq(s*A*i+n*A, 24),
    Eq(A*e*s+A, 98),
    Eq(A*A*A*a*a, 3200),
    Eq(A*a*r+A*o*A, 580),
    Eq(A*h*A*r+A, 470),
    Eq(A*t*e+A, 130),
    Eq(A, 2),  # I guess
]

solutions = solve(eqs, (A, a, i, d, e, h, o, t, s, n, r))[0]


print('solutions:', solutions)

lookup_list = ['A', 'a', 'i', 'd', 'e', 'h', 'o', 't', 's', 'n', 'r']

SECRET = 'thedorians'
answer = []

for char in SECRET:
    if char in lookup_list:
        print(f'{char} = {solutions[lookup_list.index(char)]}')
        answer.append(solutions[lookup_list.index(char)])
    else:
        print(f'{char} is not in the solutions.')

print('answer:', ''.join(map(lambda x: chr(x+64), answer)))
