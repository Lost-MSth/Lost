from pauli_func import MultiPauliString, norm, l_super, get_sigma, test_mutex


print(test_mutex(10000000))

# a = MultiPauliString(5)

# x = a.get_data(0, 2)

# print(x)


# a.set_data(0, 2, 1+6j)
# a.set_data(0, 1, -1-1j)
# a.set_data(1, 3, 1+6j)
# a.set_data(1, 4, -1-2j)
# a.set_data(1, 5, 0)
# a.set_data(1, 6, -3-1j)

# print(a.data)

# b = MultiPauliString(5)

# b.set_data(0, 8, 1+4j)
# b.set_data(0, 7, 1+8j)
# b.set_data(0, 1, 1-6j)
# b.set_data(0, 0, 1-2j)
# b.set_data(1, 0, 0)
# b.set_data(1, 9, 1-1j)

# c = l_super(a, b)

# print(c.data)
# print(a.data)

# print(get_sigma(3, 5, 5).data)