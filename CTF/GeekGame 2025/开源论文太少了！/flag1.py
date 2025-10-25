from math import e, log

DATA = "33.556704 95.365138 L 36.980298 104.180894 L 40.411025 87.619255 L 43.83462 96.870093 L 47.265347 124.223186 L 50.688941 65.437216 L 54.119668 41.678897 L 57.543263 93.845918 L 60.97399 96.870093 L 64.404717 108.403327 L 67.828311 87.619255 L 71.259038 104.180894 L 74.682633 108.403327 L 78.11336 37.335211 L 81.536954 25.908964 L 84.967681 61.728322 L 88.391276 65.437216 L 91.822003 43.804378 L 95.245597 95.365138 L 98.676324 25.908964 L 102.107051 90.764683 L 105.530646 65.437216 L 108.961373 35.117007 L 112.384967 117.825344 L 115.815694 87.619255 L 119.239289 104.180894 L 122.670016 116.520099 L 126.09361 87.619255 L 129.524337 65.437216 L 132.955064 99.837208 L 136.378659 108.403327 L 139.809386 54.018102 L 143.23298 99.837208 L 146.663707 113.859681 L 150.087302 115.193456 L 153.518029 55.979536 L 156.941623 87.619255 L 160.37235 70.850775 L 163.795945 25.908964 L 167.226672 61.728322 L 170.657399 32.870273 L 174.080993 28.262686 L 177.51172 25.908964 L 180.935315 92.312433 L 184.366042 96.870093 L 187.789636 35.117007 L 191.220363 63.589901 L 194.643958 115.193456 L 198.074685 108.403327 L 201.505412 87.619255 L 204.929006 112.51164 L 208.359733 115.193456 L 211.783328 99.837208 L 215.214055 37.335211 L 218.637649 25.908964 L 222.068376 90.764683 L 225.491971 65.437216 L 228.922698 63.589901 L 232.346292 55.979536 L 235.777019 37.335211 L 239.207746 87.619255 L 242.63134 30.580744 L 246.062067 90.764683 L 249.485662 93.845918 L 252.916389 57.919573 L 256.339983 115.193456 L 259.77071 93.845918 L 263.194305 32.870273 L 266.625032 109.78703 L 270.055759 25.908964 L 273.479353 57.919573 L 276.91008 93.845918 L 280.333675 112.51164 L 283.764402 63.589901 L 287.187996 126.712425"

TRANSFORM_MATRIX = [0.54767, 0, 0, -0.54767, 0.872, 76.213]

data = DATA.split(" L ")
points = [tuple(map(float, point.split())) for point in data]
for i in range(len(points)):
    x, y = points[i]
    new_x = TRANSFORM_MATRIX[0] * x + TRANSFORM_MATRIX[4]
    new_y = TRANSFORM_MATRIX[3] * y + TRANSFORM_MATRIX[5]
    points[i] = (new_x, new_y)

print(points)

# flag{

dy = points[1][1] - points[0][1]
real_dy = log(ord('l') / ord('f'))
scale = real_dy / dy  # up

dy = points[2][1] - points[1][1]
real_dy = log(ord('a') / ord('l'))
scale2 = real_dy / dy  # down
print(ord('l') - ord('f'), ord('a') - ord('l'))
print(scale, scale2)

dy = points[3][1] - points[2][1]
real_dy = log(ord('g') / ord('a'))
scale3 = real_dy / dy  # up

dy = points[4][1] - points[3][1]
real_dy = log(ord('{') / ord('g'))
scale4 = real_dy / dy  # down
print(ord('g') - ord('a'), ord('{') - ord('g'))
print(scale3, scale4)

# char classification
char_float = []
float_idx = []

flag_chars = ['f']
for i in range(1, len(points)):
    dy = points[i][1] - points[i-1][1]
    real_dy = (dy * scale)
    char_code = ord(flag_chars[-1]) * e**real_dy
    print(i, real_dy, dy * scale, char_code)
    # 有误差，需要别的办法

    for idx, char in enumerate(char_float):
        if abs(char_code - char) < 0.1:
            float_idx[idx].append(i)
            break
    else:
        char_float.append(char_code)
        float_idx.append([i])

    flag_chars.append(chr(round(char_code)))

flag = ''.join(flag_chars)
print(flag)
