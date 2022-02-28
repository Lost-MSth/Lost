import os
from pynput import keyboard
import time

DIR = "F:/Program Files/Nox/bin"  # 工作目录
DX = 0.004427  # 纬度修正
DY = 0.01138  # 经度修正
X0 = 30.294846 - DX  # 初始纬度
Y0 = 100.89195 - DY  # 初始经度
dx = 0.00012  # 经度移动
dy = 0.00025  # 纬度移动


def walk(x, y):
    print(x, y)
    os.system('nox_adb shell setprop persist.nox.gps.latitude '+str(x))
    os.system('nox_adb shell setprop persist.nox.gps.longitude '+str(y))
    
def go_walk(x, y, dx, dy):
    ddx = dx / 5
    ddy = dy / 5
    for i in range(1, 6):
        walk(x+ddx*i, y+ddy*i)
        time.sleep(0.2)
    
def main():
    os.chdir(DIR)
    walk(X0, Y0)
    global x, y
    x = X0
    y = Y0
    
    def on_press(key):
        global x, y
        try:
            k = key.char
            # print('alphanumeric key {0} pressed'.format())
            exit()
        except AttributeError:
            # print('special key {0} pressed'.format(key))
            k = str(key)
            print(k)
            if k == 'Key.up':
                go_walk(x, y, dx, 0)
                x += dx
                
            elif k == 'Key.down':
                go_walk(x, y, -dx, 0)
                x -= dx
                
            elif k == 'Key.right':
                go_walk(x, y, 0, dy)
                y += dy
                
            elif k == 'Key.left':
                go_walk(x, y, 0, -dy)
                y -= dy
                
            time.sleep(0.5)
            
                

    # Collect events until released
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == '__main__':
    main()
