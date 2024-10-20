import random
import base64

# flag1 = "flag{you_Ar3_tHE_MaSTer_OF_PY7h0n}"


class Node:
    def __init__(self, a, b):
        self.value = a
        self.char = b
        self.father = None
        self.left_child = None
        self.right_child = None


class Tree:
    def __init__(self):
        self.head = None

    def func2(self, node):
        while node.father != None:
            if node.father.father == None:
                if node == node.father.left_child:
                    self.left_func(node.father)
                else:
                    self.right_func(node.father)
            elif (
                node == node.father.left_child
                and node.father == node.father.father.left_child
            ):
                self.left_func(node.father.father)
                self.left_func(node.father)
            elif (
                node == node.father.right_child
                and node.father == node.father.father.right_child
            ):
                self.right_func(node.father.father)
                self.right_func(node.father)
            elif (
                node == node.father.right_child
                and node.father == node.father.father.left_child
            ):
                self.right_func(node.father)
                self.left_func(node.father)
            else:
                self.left_func(node.father)
                self.right_func(node.father)

    def right_func(self, x):
        y = x.right_child
        x.right_child = y.left_child
        if y.left_child != None:
            y.left_child.father = x
        y.father = x.father
        if x.father == None:
            self.head = y
        elif x == x.father.left_child:
            x.father.left_child = y
        else:
            x.father.right_child = y
        y.left_child = x
        x.father = y

    def left_func(self, x):
        y = x.left_child
        x.left_child = y.right_child
        if y.right_child != None:
            y.right_child.father = x
        y.father = x.father
        if x.father == None:
            self.head = y
        elif x == x.father.right_child:
            x.father.right_child = y
        else:
            x.father.left_child = y
        y.right_child = x
        x.father = y

    def insert(self, rd, user_input_char):
        x = Node(rd, user_input_char)
        leaf = self.head
        father = None
        while leaf != None:
            father = leaf
            if rd < leaf.value:
                leaf = leaf.left_child
            else:
                leaf = leaf.right_child
        x.father = father
        if father == None:
            self.head = x
        elif rd < father.value:
            father.left_child = x
        else:
            father.right_child = x
        self.func2(x)


def get_ans(x):
    s = b""
    if x != None:
        s += bytes([x.char ^ random.randint(0, 0xFF)])
        s += get_ans(x.left_child)
        s += get_ans(x.right_child)
    return s


def in_loop(tree):
    x = tree.head
    father = None
    while x != None:
        father = x
        if random.randint(0, 1) == 0:
            x = x.left_child
        else:
            x = x.right_child
    tree.func2(father)


def main():
    tree = Tree()

    user_input = input("Please enter the flag: ")

    if len(user_input) != 36:
        print("Try again!")
        return
    if user_input[:5] != "flag{" or user_input[-1] != "}":
        print("Try again!")
        return

    for x in user_input:
        tree.insert(random.random(), ord(x))

    for _ in range(0x100):
        in_loop(tree)

    my_ans = get_ans(tree.head)
    ans = base64.b64decode("7EclRYPIOsDvLuYKDPLPZi0JbLYB9bQo8CZDlFvwBY07cs6I")
    if my_ans == ans:
        print("You got the flag3!")
    else:
        print("Try again!")


if __name__ == "__main__":
    main()
