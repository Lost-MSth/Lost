import json
import pickle

from pypinyin import Style, lazy_pinyin

TEXT = '''天地玄黄 宇宙洪荒
日月盈昃 辰宿列张
寒来暑往 秋收冬藏
闰馀成岁 律召调阳
云腾致雨 露结为霜
金生丽水 玉出昆冈
剑号巨阙 珠称夜光
果珍李柰 菜重芥姜
海咸河淡 鳞潜羽翔
龙师火帝 鸟官人皇
始制文字 乃服衣裳
推位让国 有虞陶唐
吊民伐罪 周发殷汤
坐朝问道 垂拱平章
爱育黎首 臣伏戎羌
遐迩壹体 率宾归王
鸣凤在树 白驹食场
化被草木 赖及万方
盖此身发 四大五常
恭惟鞠养 岂敢毁伤
女慕贞絜 男效才良
知过必改 得能莫忘
罔谈彼短 靡恃己长
信使可覆 器欲难量
墨悲丝淬 诗赞羔羊
景行维贤 克念作圣
德建名立 形端表正
空谷传声 虚堂习听
祸因恶积 福缘善庆
尺璧非宝 寸阴是竞
资父事君 曰严与敬
孝当竭力 忠则尽命
临深履薄 夙兴温凊
似兰斯馨 如松之盛
川流不息 渊澄取映
容止若思 言辞安定
笃初诚美 慎终宜令
荣业所基 籍甚无竟
学优登仕 摄职从政
存以甘棠 去而益咏
乐殊贵贱 礼别尊卑
上和下睦 夫唱妇随
外受傅训 入奉母仪
诸姑伯叔 犹子比儿
孔怀兄弟 同气连枝
交友投分 切磨箴规
仁慈隐恻 造次弗离
节义廉退 颠沛匪亏
性静情逸 心动神疲
守真志满 逐物意移
坚持雅操 好爵自縻
都邑华夏 东西二京
背邙面洛 浮渭据泾
宫殿盘郁 楼观飞惊
图写禽兽 画彩仙灵
丙舍傍启 甲帐对楹
肆筵设席 鼓瑟吹笙
升阶纳陛 弁转疑星
右通广内 左达承明
既集坟典 亦聚群英
杜稿锺隶 漆书壁经
府罗将相 路侠槐卿
户封八县 家给千兵
高冠陪辇 驱毂振缨
世禄侈富 车驾肥轻
策功茂实 勒碑刻铭
磻溪伊尹 佐时阿衡
奄宅曲阜 微旦孰营
桓公匡合 济弱扶倾
绮回汉惠 说感武丁
俊乂密勿 多士寔宁
晋楚更霸 赵魏困横
假途灭虢 践土会盟
何遵约法 韩弊烦刑
起翦颇牧 用军最精
宣威沙漠 驰誉丹青
九州禹迹 百郡秦并
岳宗恒岱 禅主云亭
雁门紫塞 鸡田赤城
昆池碣石 钜野洞庭
旷远绵邈 岩岫杳冥
治本于农 务兹稼穑
俶载南亩 我艺黍稷
税熟贡新 劝赏黜陟
孟轲敦素 史鱼秉直
庶几中庸 劳谦谨敕
聆音察理 鉴貌辨色
贻厥嘉猷 勉其祗植
省躬讥诫 宠增抗极
殆辱近耻 林皋幸即
两疏见机 解组谁逼
索居闲处 沉默寂寥
求古寻论 散虑逍遥
欣奏累遣 戚谢欢招
渠荷的历 园莽抽条
枇杷晚翠 梧桐早凋
陈根委翳 落叶飘飖
游鹍独运 凌摩绛霄
耽读翫市 寓目囊箱
易𬨎攸畏 属耳垣墙
具膳餐饭 适口充肠
饱饫烹宰 饥厌糟糠
亲戚故旧 老少异粮
妾御绩纺 侍巾帷房
纨扇圆洁 银烛炜煌
昼眠夕寐 篮笋象床
弦歌酒䜩 接杯举觞
矫手顿足 悦豫且康
嫡后嗣续 祭祀烝尝
稽颡再拜 悚惧恐惶
笺牒简要 顾答审详
骸垢想浴 执热愿凉
驴骡犊特 骇跃超骧
诛斩贼盗 捕获叛亡
布射辽丸 嵇琴阮啸
恬笔伦纸 钧巧任钓
释纷利俗 并皆佳妙
毛施淑姿 工颦妍笑
年矢每催 曦晖朗耀
璇玑悬斡 晦魄环照
指薪修祜 永绥吉劭
矩步引领 俯仰廊庙
束带矜庄 徘徊瞻眺
孤陋寡闻 愚蒙等诮
谓语助者 焉哉乎也'''

兰亭集序 = '永和九年岁在癸丑暮春之初会于会稽山阴之兰亭修禊事也群贤毕至少长咸集此地有崇山峻岭茂林修竹又有清流激湍映带左右引以为流觞曲水列坐其次虽无丝竹管弦之盛一觞一咏亦足以畅叙幽情是日也天朗气清惠风和畅仰观宇宙之大俯察品类之盛所以游目骋怀足以极视听之娱信可乐也夫人之相与俯仰一世或取诸怀抱悟言一室之内或因寄所托放浪形骸之外虽趣舍万殊静躁不同当其欣于所遇暂得于己快然自足不知老之将至及其所之既倦情随事迁感慨系之矣向之所欣俯仰之间已为陈迹犹不能不以之兴怀况修短随化终期于尽古人云死生亦大矣岂不痛哉每览昔人兴感之由若合一契未尝不临文嗟悼不能喻之于怀固知一死生为虚诞齐彭殇为妄作后之视今亦犹今之视昔悲夫故列叙时人录其所述虽世殊事异所以兴怀其致一也后之览者亦将有感于斯文'

兰亭集序 = 兰亭集序.strip()
TEXT = ''.join(TEXT.split())

SPLIT = 100

MORSE_CN = json.load(open('中文电码.json', 'r', encoding='utf-8'))
CN_MORSE = {v: k for k, v in MORSE_CN.items()}

CN_STROKE = json.load(open('Unihan_stroke.json', 'r', encoding='utf-8'))

四角号码 = pickle.load(open('四角号码.pkl', 'rb'))


def spiral_fill_counterclockwise(rows, cols, seq):
    """
    Fill a rows x cols grid in a counter-clockwise spiral starting from (0,0),
    moving downward first. The sequence 'seq' (list or string) is cycled as needed.
    """
    if not seq:
        raise ValueError("Sequence must not be empty.")
    # Allow both list of strings or a single string (cycled by characters)
    if isinstance(seq, str):
        seq = list(seq)

    grid = [[None] * cols for _ in range(rows)]
    top, bottom, left, right = 0, rows - 1, 0, cols - 1
    k, n = 0, len(seq)

    while left <= right and top <= bottom:
        # 1) Left column: top -> bottom (down)
        for i in range(top, bottom + 1):
            grid[i][left] = seq[k % n]
            k += 1
        left += 1
        if left > right or top > bottom:
            break

        # 2) Bottom row: left -> right
        for j in range(left, right + 1):
            grid[bottom][j] = seq[k % n]
            k += 1
        bottom -= 1
        if left > right or top > bottom:
            break

        # 3) Right column: bottom -> top (up)
        for i in range(bottom, top - 1, -1):
            grid[i][right] = seq[k % n]
            k += 1
        right -= 1
        if left > right or top > bottom:
            break

        # 4) Top row: right -> left
        for j in range(right, left - 1, -1):
            grid[top][j] = seq[k % n]
            k += 1
        top += 1

    # flat grid
    return [cell for row in grid for cell in row if cell is not None]


def col_5(text, HEIGHT=10, WIDTH=10):
    # 在正方形网格内从右往左竖排，然后按照横排顺序读。
    grid = [[None] * WIDTH for _ in range(HEIGHT)]
    i = 0
    for col in range(WIDTH - 1, -1, -1):
        for row in range(HEIGHT):
            grid[row][col] = text[i]
            i += 1

    # flat grid
    return [cell for row in grid for cell in row if cell is not None]


def get_character_stroke_count(char: str):
    unicode = "U+" + str(hex(ord(char)))[2:].upper()
    return int(CN_STROKE.get(unicode, 0))


def main():

    cols = [TEXT[i:i + SPLIT] for i in range(0, len(TEXT), SPLIT)]
    ans_cols = []

    # 第一列 倒序
    ans_cols.append([x for x in cols[0][::-1]])

    # 第二列 整列替换为《兰亭集序》中相应位置的字
    ans_cols.append([])
    for i in range(SPLIT):
        ans_cols[1].append(兰亭集序[SPLIT+i])

    # 第三列 按照 Unicode 排序
    ans_cols.append(sorted(cols[2]))

    # 第四列 按照中文电码排序
    ans_cols.append(sorted(cols[3], key=lambda x: int(CN_MORSE.get(x, 0))))

    # 第五列 在正方形网格内从右往左竖排，然后按照横排顺序读。
    ans_cols.append(col_5(cols[4]))

    # 第六列 Unicode 凯撒 -4
    ans_cols.append([chr(ord(c) - 4) for c in cols[5]])

    # 第七列 按照笔画数排序
    ans_cols.append(sorted(cols[6], key=get_character_stroke_count))

    # 第八列 从左上角出发，逆时针填满一个正方形网格，然后按照横排顺序读。
    ans_cols.append(spiral_fill_counterclockwise(10, 10, cols[7]))

    # 第九列 按照拼音排序（包括音调）
    ans_cols.append(
        sorted(cols[8], key=lambda x: lazy_pinyin(x, style=Style.TONE3)[0]))

    # 第十列 按照四角号码排序（五位数字）
    ans_cols.append(sorted(cols[9], key=lambda x: 四角号码.get(x)))

    # 按照 10~1 列 打印
    print('十 九 八 七 六 五 四 三 二 一')
    for i in range(SPLIT):
        for col_id in range(9, -1, -1):
            print(ans_cols[col_id][i], end=" ")

        print(f'{(i+1):3d}')


if __name__ == "__main__":
    main()
