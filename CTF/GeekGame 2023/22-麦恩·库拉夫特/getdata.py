import keyboard
import pyperclip
import time


def get_data():
    # F3 + I

    #t = time.time()
    keyboard.press_and_release('f3+i')

    #print('key: ', time.time() - t)

    #t = time.time()
    # x =
    #print('paste: ', time.time() - t)
    return pyperclip.paste()


D = ['0', '1', '2', '3', '4', '5', '6', '7',
     '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']

log_data = ''


def main():
    global log_data
    while True:
        t = time.time()
        data = get_data()
        #print('get_data: ', time.time() - t)
        # power=12,south
        x = data.find('power')
        y = data.find('south', x)
        if x != -1 and y != -1:
            power = int(data[x+6:y-1])
            # print(power)
            z = D[power]
            log_data += z
            #print(z, end='')
        tt = time.time() - t
        #print('cost: ', tt)
        time.sleep(max(0, 0.02 - tt))


if __name__ == '__main__':
    time.sleep(5)
    try:
        main()
    except KeyboardInterrupt:
        with open('log.txt', 'w') as f:
            f.write(log_data)
