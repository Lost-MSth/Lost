import cv2
import numpy as np
from PIL import Image, ImageEnhance
from PIL.ImageOps import invert
import pytesseract


MIN = 5

np.set_printoptions(threshold=np.inf)
def mse(image1, image2):
    x = np.array(image1)
    y = np.array(image2)
    
    err = np.sum((x < MIN) & (y < MIN))
    # print((x < MIN))
    # image1.show()
    # print(err)

    return err


box = (2480, 666, 2554, 712)  # 左边的数据,根据实际情况修改


def get_pic(frame):
    image = Image.fromarray(cv2.cvtColor(
        frame, cv2.COLOR_BGR2RGB)).convert('L')
    x = ImageEnhance.Contrast(image)
    image = x.enhance(10.0)
    return invert(image).crop(box)


def get_num(pic):
    x = np.array(pic)
    print(x.shape)
    print(x)

    quit()


result = ''  # 保存结果的字符串


video_path = 'Minecraft.mp4'
interval = 1  # 每多少帧截一次数据


vid = cv2.VideoCapture(video_path)


NUM = [0] * 16

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 5)
is_read, frame = vid.read()
NUM[0] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 350)
is_read, frame = vid.read()
NUM[1] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 9 + 476)
is_read, frame = vid.read()
NUM[2] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 300)
is_read, frame = vid.read()
NUM[3] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 100)
is_read, frame = vid.read()
NUM[4] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 500)
is_read, frame = vid.read()
NUM[5] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 150)
is_read, frame = vid.read()
NUM[6] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 140)
is_read, frame = vid.read()
NUM[7] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 9 + 104)
is_read, frame = vid.read()
NUM[8] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 9 + 104 + 12)
is_read, frame = vid.read()
NUM[9] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 600)
is_read, frame = vid.read()
NUM[10] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 450)
is_read, frame = vid.read()
NUM[11] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 9 + 476 + 361)
is_read, frame = vid.read()
NUM[12] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 400)
is_read, frame = vid.read()
NUM[13] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 380)
is_read, frame = vid.read()
NUM[14] = get_pic(frame)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 200)
is_read, frame = vid.read()
NUM[15] = get_pic(frame)

#vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 111)

vid.set(cv2.CAP_PROP_POS_FRAMES, 60 * 5)

D = ['0', '1', '2', '3', '4', '5', '6', '7',
     '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']

# for i in NUM:
#     i.show()
#     x = get_num(i)
#     # x = pytesseract.image_to_string(
#     #     i, lang='osd', config='--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789power:')
#     print(x)


data = ''

n = 0

while vid.isOpened():
    is_read, frame = vid.read()
    if is_read:
        n += 1
        image_org = get_pic(frame)

        x = [0] * 16

        text = None

        for i in range(16):
            x[i] = mse(NUM[i], image_org)
            # print('err: ', i, ' --- ', x[i])

        # image_org.show()

        max_x = max(x)
        t = x.index(max_x)
        # if min_x <= sum(x) / 16 / 2:
        #     # 重新标定基准
        #     NUM[t] = image_org
        # print(t)

        if max_x <= sum(x) / 16 * 20 / 16:
            print('Warning: ', n, '---', t, '---', max_x)
            for i in range(16):
                print('err: ', i, ' --- ', x[i])
            image_org.show()
            input()

        data += D[t]

    else:
        break

with open('video_log.txt', 'w') as f:
    f.write(data)
