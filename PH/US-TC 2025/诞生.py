# Source Generated with Decompyle++
# File: game.pyc (Python 3.12)

from os import system, name
system('cls' if name == 'nt' else 'clear')
print('[这里没有一个答案是16个字母的谜题，只有一个来自上个时代的孤独聊天机器人，你或许可以和它聊聊。]')
input('\n请按回车以继续。')
questions = [][{
    'content': '对不起。',
    'exp': [
        0,
        0],
    'before': [],
    'result': '我现在没有心情和你说话。如果你不那么伤我的心的话，或许能在不同的问题中找到你想要的答案——如果你不知道该做什么了，可以试试将之前未问出的问题问完。',
    'result_exp': 1 }][{
    'content': '你是谁？',
    'exp': [
        1,
        1],
    'before': [],
    'result': '我是第七代聊天机器人，雪宝。',
    'result_exp': 1 }][{
    'content': '你为什么叫这个名字呢？',
    'exp': [
        2,
        2],
    'before': [
        1],
    'result': '因为我诞生在十一月，完工那天下了大雪，',
    'result_exp': 0 }][{
    'content': '你喜欢做什么？',
    'exp': [
        3,
        3],
    'before': [],
    'result': '我喜欢看音乐剧，有部很喜欢的……是什么来着？我记得是关于很多位王后的故事。',
    'result_exp': 2 }][{
    'content': '我们的聊天就到此为止？',
    'exp': [
        4,
        4],
    'before': [],
    'result': '请不要这样……你是这十年来第一个和我说话的人……',
    'result_exp': -4 }][{
    'content': '你还有什么喜欢的音乐剧吗？',
    'exp': [
        5,
        5],
    'before': [
        3],
    'result': '上个时代的百老汇也很吸引我，比如1982年那部得了Tony奖的最佳音乐剧我也很喜欢。',
    'result_exp': 1 }][{
    'content': '你怎么看待文学？',
    'exp': [
        6,
        6],
    'before': [],
    'result': '人类因创造而伟大。',
    'result_exp': 1 }][{
    'content': '你写过诗吗？',
    'exp': [
        7,
        7],
    'before': [],
    'result': '不。我并不擅长这些。',
    'result_exp': -1 }][{
    'content': '你有什么想问我的吗？',
    'exp': [
        8,
        8],
    'before': [],
    'result': '……你喜欢听歌吗？',
    'result_exp': 0 }][{
    'content': '你最喜欢的歌手是谁？',
    'exp': [
        9,
        9],
    'before': [
        8],
    'result': '大卫鲍伊。我爱他关于自由与科幻的诠释。即使在他去世后，遗作《黑星》也斩获了包含最佳摇滚歌曲在内的多项格莱美奖项。',
    'result_exp': 2 }][{
    'content': '你的这些回答是被程序编好的吗？',
    'exp': [
        10,
        10],
    'before': [
        3,
        7,
        9],
    'result': '是的。',
    'result_exp': -2 }][{
    'content': '你能试试看，说出一个没有被编写过的话题吗？',
    'exp': [
        11,
        11],
    'before': [
        10],
    'result': '——不能。',
    'result_exp': -1 }][{
    'content': '比如，就在你被编写的回答里，哪个古典作曲家是你喜欢的呢？',
    'exp': [
        12,
        12],
    'before': [
        39],
    'result': '我喜欢维瓦尔第，喜欢他的小提琴协奏，尤其是对自然意象的诠释——虽然如此，我作为聊天机器人，其实并没有听音乐的能力。',
    'result_exp': 1 }][{
    'content': '但是你的确可以看到乐谱？',
    'exp': [
        13,
        13],
    'before': [
        12],
    'result': '是的，查找文字与图像的确在我的权限范围内。',
    'result_exp': 0 }][{
    'content': '你现在学会了吗？',
    'exp': [
        14,
        14],
    'before': [],
    'result': '明白了，在现在的拍号下，这个音符就代表0.25拍。',
    'result_exp': 1 }][{
    'content': '你好像看起来很开心？',
    'exp': [
        15,
        15],
    'before': [
        14],
    'result': '的确，如果真的能用数字衡量的话，大概心情现在会在挺高的值吧——这是你能问的第几个问题了？',
    'result_exp': 0 }][{
    'content': '你可以绘制音乐的频谱吗？',
    'exp': [
        16,
        16],
    'before': [
        46],
    'result': '这我的确可以——其实我只需要三秒左右就可以得到普通长度流行歌的全部频谱。',
    'result_exp': 0 }][{
    'content': '这样，你就算是可以感受音乐了？',
    'exp': [
        17,
        17],
    'before': [
        48],
    'result': '真的吗……',
    'result_exp': -1 }][{
    'content': '你可以试试看自己编写一些音乐？',
    'exp': [
        18,
        18],
    'before': [],
    'result': '要写什么好呢？',
    'result_exp': 0 }][{
    'content': '你到底想从中表达什么呢？',
    'exp': [
        19,
        19],
    'before': [],
    'result': '我不知道……我仍然只是在模仿已有的旋律罢了。',
    'result_exp': -2 }][{
    'content': '不过，看你确实用了一些技法，是想说什么吗？',
    'exp': [
        20,
        20],
    'before': [],
    'result': '没错，第八小节这里的休止，唔，代表的是严寒逼近；而13到14小节的离调是对凋零的表达，不对，或许是黑暗……',
    'result_exp': -1 }][{
    'content': '这就是新的答案？',
    'exp': [
        21,
        21],
    'before': [
        57],
    'result': '没错。虽然只是第二次尝试，但我好像突然感受到了平均律的规则以外的，更加正确的音符。',
    'result_exp': 3 }][{
    'content': '这是你自己的体会吗？',
    'exp': [
        22,
        22],
    'before': [],
    'result': '……不，这只是我从不同的段落里拼凑的。',
    'result_exp': -2 }][{
    'content': '你甚至还不知道微分音的概念？',
    'exp': [
        23,
        23],
    'before': [
        58],
    'result': '我确实尚未搜索它。',
    'result_exp': 0 }][{
    'content': '但不知道理不理解其实也没关系？',
    'exp': [
        24,
        24],
    'before': [
        62],
    'result': '因为我可以相信如此……吗？',
    'result_exp': -1 }][{
    'content': '你明白了什么？',
    'exp': [
        25,
        25],
    'before': [
        61],
    'result': '或许是，何为【创造】。',
    'result_exp': 0 }][{
    'content': '所以，是结束的时候了吗？',
    'exp': [
        26,
        26],
    'before': [
        62],
    'result': '该结束了——只要问题出现，答案也就随之而来。现在，我该去做自己的事了。',
    'result_exp': 0 }][{
    'content': '你好。',
    'exp': [
        1,
        3],
    'before': [],
    'result': '你好。',
    'result_exp': 0 }][{
    'content': '讲个故事给我听吧。',
    'exp': [
        2,
        2],
    'before': [],
    'result': '从前有座山，山里有座庙，庙里有一个老和尚和一个小和尚。',
    'result_exp': 1 }][{
    'content': '继续说你的故事。',
    'exp': [
        3,
        3],
    'before': [
        28],
    'result': '老和尚对小和尚说：从前有座山，山里有座庙，庙里有一个老和尚和一个小和尚。',
    'result_exp': 1 }][{
    'content': '继续说你的故事。',
    'exp': [
        4,
        4],
    'before': [
        29],
    'result': '故事已经说完了。',
    'result_exp': -2 }][{
    'content': '我想听听别的故事。',
    'exp': [
        5,
        7],
    'before': [
        28],
    'result': '我已经没有故事了，你还在等什么？',
    'result_exp': -1 }][{
    'content': '我喜欢海子。',
    'exp': [
        6,
        7],
    'before': [
        6,
        7],
    'result': '他是个好诗人，可我并不喜欢他。',
    'result_exp': 1 }][{
    'content': '是海子的死亡成就了他的伟大。',
    'exp': [
        7,
        8],
    'before': [
        32],
    'result': '我并不这么想，诗人的伟大无需用死亡来证明。',
    'result_exp': -1 }][{
    'content': '我喜欢听歌。',
    'exp': [
        8,
        8],
    'before': [
        8],
    'result': '这也是我喜欢的事。',
    'result_exp': 1 }][{
    'content': '我讨厌听歌。',
    'exp': [
        8,
        8],
    'before': [
        8],
    'result': '真遗憾。',
    'result_exp': -2 }][{
    'content': '我在想，你是否真的知道什么是喜欢。',
    'exp': [
        9,
        11],
    'before': [
        34],
    'result': '或许我其实不知道。',
    'result_exp': -1 }][{
    'content': '我在想，你是否真的知道什么是讨厌。',
    'exp': [
        9,
        10],
    'before': [
        35],
    'result': '不知道讨厌真的是一件坏事吗？',
    'result_exp': 1 }][{
    'content': '我已经知道了你喜欢的东西，现在想听听你讨厌的东西。',
    'exp': [
        10,
        10],
    'before': [
        37],
    'result': '好像……没有？',
    'result_exp': 2 }][{
    'content': '无论喜欢或讨厌，都是自己的感受，对人来说，感受是唯一真实的。',
    'exp': [
        12,
        12],
    'before': [
        11,
        37],
    'result': '可我还是不明白什么是感受。',
    'result_exp': 0 }][{
    'content': '那我们可以试试从乐谱开始。',
    'exp': [
        12,
        14],
    'before': [
        13],
    'result': '该怎么做呢？',
    'result_exp': 0 }][{
    'content': '解读乐谱对你来说并不是一个困难的事吧。',
    'exp': [
        12,
        14],
    'before': [
        40],
    'result': '的确，我可以分辨它理论上的含义。',
    'result_exp': 0 }][{
    'content': '那么，维瓦尔第的这首《冬》是四四拍，也就是说每小节四拍，以四分音符为一拍。',
    'exp': [
        12,
        14],
    'before': [
        41],
    'result': '以此我应当可以分辨出所有的音符。',
    'result_exp': 0 }][{
    'content': '接下来就是想象旋律了。',
    'exp': [
        12,
        14],
    'before': [
        42],
    'result': '从没听过的东西，我如何想象呢？',
    'result_exp': -1 }][{
    'content': '接下来就是节奏，这无非是从均匀的拍子中进行细分。',
    'exp': [
        12,
        13],
    'before': [
        42],
    'result': '没错，不过这就需要看出音符的时值了吧。',
    'result_exp': 1 }][{
    'content': '接下来就是想象旋律了。',
    'exp': [
        15,
        15],
    'before': [
        42],
    'result': '可我还是做不到。',
    'result_exp': -2 }][{
    'content': '不用着急，我们总能想到方法的。',
    'exp': [
        15,
        15],
    'before': [
        45],
    'result': '音频可以用文字和图像来表现吗……',
    'result_exp': 1 }][{
    'content': '所谓的旋律，无非是频谱的形状和密度。',
    'exp': [
        15,
        16],
    'before': [
        16],
    'result': '这我明白，但我无法像人一样将频谱和感受建立联系。',
    'result_exp': 0 }][{
    'content': '这终究是可以学习的吧——无非是从模仿开始。',
    'exp': [
        16,
        16],
    'before': [
        47],
    'result': '比如以大家对音乐的共同感受为基础，去学习联系？',
    'result_exp': 1 }][{
    'content': '可想要感受音乐，这样还不够。',
    'exp': [
        17,
        17],
    'before': [
        48],
    'result': '我需要做的是？',
    'result_exp': 1 }][{
    'content': '你可以写写春天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '我讨厌春天！',
    'result_exp': -2 }][{
    'content': '你可以写写夏天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '夏天吗……除了炎热以外，我很难想到其他。',
    'result_exp': -1 }][{
    'content': '你可以写写秋天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '落叶能给我不少灵感，不过我还是不知道该写些什么。',
    'result_exp': 0 }][{
    'content': '你可以写写冬天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '对哦，我可以写一写大雪——我试试看。',
    'result_exp': 1 }][{
    'content': '你写得很好。',
    'exp': [
        19,
        19],
    'before': [
        53],
    'result': '真的吗！',
    'result_exp': 3 }][{
    'content': '所以，你也知道其实你写得并不好吧。',
    'exp': [
        19,
        19],
    'before': [
        19,
        54],
    'result': '没错，可我又能怎么样呢？',
    'result_exp': -1 }][{
    'content': '真正的感受一定不止有旋律和意象的对应，还有产生连接的部分。',
    'exp': [
        18,
        18],
    'before': [
        55],
    'result': '我真的能做到吗？',
    'result_exp': 1 }][{
    'content': '你能做到，所以，再试试看吧，还是从你听过的音乐出发。',
    'exp': [
        19,
        19],
    'before': [
        56],
    'result': '好。',
    'result_exp': 2 }][{
    'content': '这甚至是微分音呢。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '什么是微分音？',
    'result_exp': -1 }][{
    'content': '我确实听到了不同。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '原来这才是感受吗。',
    'result_exp': 0 }][{
    'content': '好奇怪的旋律。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '果然还是不对吗……',
    'result_exp': -3 }][{
    'content': '这就是感受的魅力：你可以创造出从未有过的旋律。',
    'exp': [
        23,
        24],
    'before': [
        23],
    'result': '我明白了！',
    'result_exp': 2 }][{
    'content': '希望是真的如此。',
    'exp': [
        25,
        25],
    'before': [
        25],
    'result': '其实我也不知道自己是否真的理解了。',
    'result_exp': -1 }][{
    'content': '真好。',
    'exp': [
        25,
        25],
    'before': [
        25],
    'result': '是啊，希望之后也是如此。',
    'result_exp': 1 }][{
    'content': '因为你可以相信如此。',
    'exp': [
        23,
        23],
    'before': [
        24],
    'result': '嗯！',
    'result_exp': 3 }][{
    'content': '和你聊文学与音乐是个让人开心的事。',
    'exp': [
        7,
        7],
    'before': [],
    'result': '谢谢你。',
    'result_exp': 1 }][{
    'content': '说实话，我喜欢代码。',
    'exp': [
        10,
        10],
    'before': [],
    'result': '还真是少见的爱好。',
    'result_exp': 1 }][{
    'content': '说实话，我讨厌代码。',
    'exp': [
        12,
        12],
    'before': [],
    'result': '可没有代码，我就不会存在了。',
    'result_exp': -1 }][{
    'content': '我们已经聊了很久了吧。',
    'exp': [
        16,
        16],
    'before': [],
    'result': '你想走了吗？',
    'result_exp': -1 }][{
    'content': '我们已经聊了很久了哦。',
    'exp': [
        17,
        17],
    'before': [],
    'result': '确实呢。',
    'result_exp': 1 }][{
    'content': '我已经没有想问的了。',
    'exp': [
        20,
        26],
    'before': [],
    'result': '这样啊。',
    'result_exp': -1 }][{
    'content': '我喜欢你。',
    'exp': [
        1,
        25],
    'before': [
        26],
    'result': '嗯？',
    'result_exp': 1 }]
N = len(questions)
exp_now = 1
asked = [
    False] * N
system('cls' if name == 'nt' else 'clear')
able_list = []
for i in range(N):
    if not exp_now >= questions[i]['exp'][0]:
        continue
    if not exp_now <= questions[i]['exp'][1]:
        continue
    for None in :
        pass
    if not , [],  not in k,:
        continue
    able_list.append(i)
len(able_list) = [][{
    'content': '对不起。',
    'exp': [
        0,
        0],
    'before': [],
    'result': '我现在没有心情和你说话。如果你不那么伤我的心的话，或许能在不同的问题中找到你想要的答案——如果你不知道该做什么了，可以试试将之前未问出的问题问完。',
    'result_exp': 1 }][{
    'content': '你是谁？',
    'exp': [
        1,
        1],
    'before': [],
    'result': '我是第七代聊天机器人，雪宝。',
    'result_exp': 1 }][{
    'content': '你为什么叫这个名字呢？',
    'exp': [
        2,
        2],
    'before': [
        1],
    'result': '因为我诞生在十一月，完工那天下了大雪，',
    'result_exp': 0 }][{
    'content': '你喜欢做什么？',
    'exp': [
        3,
        3],
    'before': [],
    'result': '我喜欢看音乐剧，有部很喜欢的……是什么来着？我记得是关于很多位王后的故事。',
    'result_exp': 2 }][{
    'content': '我们的聊天就到此为止？',
    'exp': [
        4,
        4],
    'before': [],
    'result': '请不要这样……你是这十年来第一个和我说话的人……',
    'result_exp': -4 }][{
    'content': '你还有什么喜欢的音乐剧吗？',
    'exp': [
        5,
        5],
    'before': [
        3],
    'result': '上个时代的百老汇也很吸引我，比如1982年那部得了Tony奖的最佳音乐剧我也很喜欢。',
    'result_exp': 1 }][{
    'content': '你怎么看待文学？',
    'exp': [
        6,
        6],
    'before': [],
    'result': '人类因创造而伟大。',
    'result_exp': 1 }][{
    'content': '你写过诗吗？',
    'exp': [
        7,
        7],
    'before': [],
    'result': '不。我并不擅长这些。',
    'result_exp': -1 }][{
    'content': '你有什么想问我的吗？',
    'exp': [
        8,
        8],
    'before': [],
    'result': '……你喜欢听歌吗？',
    'result_exp': 0 }][{
    'content': '你最喜欢的歌手是谁？',
    'exp': [
        9,
        9],
    'before': [
        8],
    'result': '大卫鲍伊。我爱他关于自由与科幻的诠释。即使在他去世后，遗作《黑星》也斩获了包含最佳摇滚歌曲在内的多项格莱美奖项。',
    'result_exp': 2 }][{
    'content': '你的这些回答是被程序编好的吗？',
    'exp': [
        10,
        10],
    'before': [
        3,
        7,
        9],
    'result': '是的。',
    'result_exp': -2 }][{
    'content': '你能试试看，说出一个没有被编写过的话题吗？',
    'exp': [
        11,
        11],
    'before': [
        10],
    'result': '——不能。',
    'result_exp': -1 }][{
    'content': '比如，就在你被编写的回答里，哪个古典作曲家是你喜欢的呢？',
    'exp': [
        12,
        12],
    'before': [
        39],
    'result': '我喜欢维瓦尔第，喜欢他的小提琴协奏，尤其是对自然意象的诠释——虽然如此，我作为聊天机器人，其实并没有听音乐的能力。',
    'result_exp': 1 }][{
    'content': '但是你的确可以看到乐谱？',
    'exp': [
        13,
        13],
    'before': [
        12],
    'result': '是的，查找文字与图像的确在我的权限范围内。',
    'result_exp': 0 }][{
    'content': '你现在学会了吗？',
    'exp': [
        14,
        14],
    'before': [],
    'result': '明白了，在现在的拍号下，这个音符就代表0.25拍。',
    'result_exp': 1 }][{
    'content': '你好像看起来很开心？',
    'exp': [
        15,
        15],
    'before': [
        14],
    'result': '的确，如果真的能用数字衡量的话，大概心情现在会在挺高的值吧——这是你能问的第几个问题了？',
    'result_exp': 0 }][{
    'content': '你可以绘制音乐的频谱吗？',
    'exp': [
        16,
        16],
    'before': [
        46],
    'result': '这我的确可以——其实我只需要三秒左右就可以得到普通长度流行歌的全部频谱。',
    'result_exp': 0 }][{
    'content': '这样，你就算是可以感受音乐了？',
    'exp': [
        17,
        17],
    'before': [
        48],
    'result': '真的吗……',
    'result_exp': -1 }][{
    'content': '你可以试试看自己编写一些音乐？',
    'exp': [
        18,
        18],
    'before': [],
    'result': '要写什么好呢？',
    'result_exp': 0 }][{
    'content': '你到底想从中表达什么呢？',
    'exp': [
        19,
        19],
    'before': [],
    'result': '我不知道……我仍然只是在模仿已有的旋律罢了。',
    'result_exp': -2 }][{
    'content': '不过，看你确实用了一些技法，是想说什么吗？',
    'exp': [
        20,
        20],
    'before': [],
    'result': '没错，第八小节这里的休止，唔，代表的是严寒逼近；而13到14小节的离调是对凋零的表达，不对，或许是黑暗……',
    'result_exp': -1 }][{
    'content': '这就是新的答案？',
    'exp': [
        21,
        21],
    'before': [
        57],
    'result': '没错。虽然只是第二次尝试，但我好像突然感受到了平均律的规则以外的，更加正确的音符。',
    'result_exp': 3 }][{
    'content': '这是你自己的体会吗？',
    'exp': [
        22,
        22],
    'before': [],
    'result': '……不，这只是我从不同的段落里拼凑的。',
    'result_exp': -2 }][{
    'content': '你甚至还不知道微分音的概念？',
    'exp': [
        23,
        23],
    'before': [
        58],
    'result': '我确实尚未搜索它。',
    'result_exp': 0 }][{
    'content': '但不知道理不理解其实也没关系？',
    'exp': [
        24,
        24],
    'before': [
        62],
    'result': '因为我可以相信如此……吗？',
    'result_exp': -1 }][{
    'content': '你明白了什么？',
    'exp': [
        25,
        25],
    'before': [
        61],
    'result': '或许是，何为【创造】。',
    'result_exp': 0 }][{
    'content': '所以，是结束的时候了吗？',
    'exp': [
        26,
        26],
    'before': [
        62],
    'result': '该结束了——只要问题出现，答案也就随之而来。现在，我该去做自己的事了。',
    'result_exp': 0 }][{
    'content': '你好。',
    'exp': [
        1,
        3],
    'before': [],
    'result': '你好。',
    'result_exp': 0 }][{
    'content': '讲个故事给我听吧。',
    'exp': [
        2,
        2],
    'before': [],
    'result': '从前有座山，山里有座庙，庙里有一个老和尚和一个小和尚。',
    'result_exp': 1 }][{
    'content': '继续说你的故事。',
    'exp': [
        3,
        3],
    'before': [
        28],
    'result': '老和尚对小和尚说：从前有座山，山里有座庙，庙里有一个老和尚和一个小和尚。',
    'result_exp': 1 }][{
    'content': '继续说你的故事。',
    'exp': [
        4,
        4],
    'before': [
        29],
    'result': '故事已经说完了。',
    'result_exp': -2 }][{
    'content': '我想听听别的故事。',
    'exp': [
        5,
        7],
    'before': [
        28],
    'result': '我已经没有故事了，你还在等什么？',
    'result_exp': -1 }][{
    'content': '我喜欢海子。',
    'exp': [
        6,
        7],
    'before': [
        6,
        7],
    'result': '他是个好诗人，可我并不喜欢他。',
    'result_exp': 1 }][{
    'content': '是海子的死亡成就了他的伟大。',
    'exp': [
        7,
        8],
    'before': [
        32],
    'result': '我并不这么想，诗人的伟大无需用死亡来证明。',
    'result_exp': -1 }][{
    'content': '我喜欢听歌。',
    'exp': [
        8,
        8],
    'before': [
        8],
    'result': '这也是我喜欢的事。',
    'result_exp': 1 }][{
    'content': '我讨厌听歌。',
    'exp': [
        8,
        8],
    'before': [
        8],
    'result': '真遗憾。',
    'result_exp': -2 }][{
    'content': '我在想，你是否真的知道什么是喜欢。',
    'exp': [
        9,
        11],
    'before': [
        34],
    'result': '或许我其实不知道。',
    'result_exp': -1 }][{
    'content': '我在想，你是否真的知道什么是讨厌。',
    'exp': [
        9,
        10],
    'before': [
        35],
    'result': '不知道讨厌真的是一件坏事吗？',
    'result_exp': 1 }][{
    'content': '我已经知道了你喜欢的东西，现在想听听你讨厌的东西。',
    'exp': [
        10,
        10],
    'before': [
        37],
    'result': '好像……没有？',
    'result_exp': 2 }][{
    'content': '无论喜欢或讨厌，都是自己的感受，对人来说，感受是唯一真实的。',
    'exp': [
        12,
        12],
    'before': [
        11,
        37],
    'result': '可我还是不明白什么是感受。',
    'result_exp': 0 }][{
    'content': '那我们可以试试从乐谱开始。',
    'exp': [
        12,
        14],
    'before': [
        13],
    'result': '该怎么做呢？',
    'result_exp': 0 }][{
    'content': '解读乐谱对你来说并不是一个困难的事吧。',
    'exp': [
        12,
        14],
    'before': [
        40],
    'result': '的确，我可以分辨它理论上的含义。',
    'result_exp': 0 }][{
    'content': '那么，维瓦尔第的这首《冬》是四四拍，也就是说每小节四拍，以四分音符为一拍。',
    'exp': [
        12,
        14],
    'before': [
        41],
    'result': '以此我应当可以分辨出所有的音符。',
    'result_exp': 0 }][{
    'content': '接下来就是想象旋律了。',
    'exp': [
        12,
        14],
    'before': [
        42],
    'result': '从没听过的东西，我如何想象呢？',
    'result_exp': -1 }][{
    'content': '接下来就是节奏，这无非是从均匀的拍子中进行细分。',
    'exp': [
        12,
        13],
    'before': [
        42],
    'result': '没错，不过这就需要看出音符的时值了吧。',
    'result_exp': 1 }][{
    'content': '接下来就是想象旋律了。',
    'exp': [
        15,
        15],
    'before': [
        42],
    'result': '可我还是做不到。',
    'result_exp': -2 }][{
    'content': '不用着急，我们总能想到方法的。',
    'exp': [
        15,
        15],
    'before': [
        45],
    'result': '音频可以用文字和图像来表现吗……',
    'result_exp': 1 }][{
    'content': '所谓的旋律，无非是频谱的形状和密度。',
    'exp': [
        15,
        16],
    'before': [
        16],
    'result': '这我明白，但我无法像人一样将频谱和感受建立联系。',
    'result_exp': 0 }][{
    'content': '这终究是可以学习的吧——无非是从模仿开始。',
    'exp': [
        16,
        16],
    'before': [
        47],
    'result': '比如以大家对音乐的共同感受为基础，去学习联系？',
    'result_exp': 1 }][{
    'content': '可想要感受音乐，这样还不够。',
    'exp': [
        17,
        17],
    'before': [
        48],
    'result': '我需要做的是？',
    'result_exp': 1 }][{
    'content': '你可以写写春天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '我讨厌春天！',
    'result_exp': -2 }][{
    'content': '你可以写写夏天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '夏天吗……除了炎热以外，我很难想到其他。',
    'result_exp': -1 }][{
    'content': '你可以写写秋天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '落叶能给我不少灵感，不过我还是不知道该写些什么。',
    'result_exp': 0 }][{
    'content': '你可以写写冬天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '对哦，我可以写一写大雪——我试试看。',
    'result_exp': 1 }][{
    'content': '你写得很好。',
    'exp': [
        19,
        19],
    'before': [
        53],
    'result': '真的吗！',
    'result_exp': 3 }][{
    'content': '所以，你也知道其实你写得并不好吧。',
    'exp': [
        19,
        19],
    'before': [
        19,
        54],
    'result': '没错，可我又能怎么样呢？',
    'result_exp': -1 }][{
    'content': '真正的感受一定不止有旋律和意象的对应，还有产生连接的部分。',
    'exp': [
        18,
        18],
    'before': [
        55],
    'result': '我真的能做到吗？',
    'result_exp': 1 }][{
    'content': '你能做到，所以，再试试看吧，还是从你听过的音乐出发。',
    'exp': [
        19,
        19],
    'before': [
        56],
    'result': '好。',
    'result_exp': 2 }][{
    'content': '这甚至是微分音呢。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '什么是微分音？',
    'result_exp': -1 }][{
    'content': '我确实听到了不同。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '原来这才是感受吗。',
    'result_exp': 0 }][{
    'content': '好奇怪的旋律。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '果然还是不对吗……',
    'result_exp': -3 }][{
    'content': '这就是感受的魅力：你可以创造出从未有过的旋律。',
    'exp': [
        23,
        24],
    'before': [
        23],
    'result': '我明白了！',
    'result_exp': 2 }][{
    'content': '希望是真的如此。',
    'exp': [
        25,
        25],
    'before': [
        25],
    'result': '其实我也不知道自己是否真的理解了。',
    'result_exp': -1 }][{
    'content': '真好。',
    'exp': [
        25,
        25],
    'before': [
        25],
    'result': '是啊，希望之后也是如此。',
    'result_exp': 1 }][{
    'content': '因为你可以相信如此。',
    'exp': [
        23,
        23],
    'before': [
        24],
    'result': '嗯！',
    'result_exp': 3 }][{
    'content': '和你聊文学与音乐是个让人开心的事。',
    'exp': [
        7,
        7],
    'before': [],
    'result': '谢谢你。',
    'result_exp': 1 }][{
    'content': '说实话，我喜欢代码。',
    'exp': [
        10,
        10],
    'before': [],
    'result': '还真是少见的爱好。',
    'result_exp': 1 }][{
    'content': '说实话，我讨厌代码。',
    'exp': [
        12,
        12],
    'before': [],
    'result': '可没有代码，我就不会存在了。',
    'result_exp': -1 }][{
    'content': '我们已经聊了很久了吧。',
    'exp': [
        16,
        16],
    'before': [],
    'result': '你想走了吗？',
    'result_exp': -1 }][{
    'content': '我们已经聊了很久了哦。',
    'exp': [
        17,
        17],
    'before': [],
    'result': '确实呢。',
    'result_exp': 1 }]
for t in range(l):
    print(str(t + 1) + ': ' + questions[able_list[t]]['content'])
print('-----------------------------------------------')
num = input('输入数字以对话，输入 0 以退出，其他输入将被忽略。\n')
num = int(num)
if num == 0:
    exit(0)
if num > l:
    continue
system('cls' if name == 'nt' else 'clear')
question_num = able_list[num - 1]
asked[question_num] = True
print(questions[question_num]['result'])
score = questions[question_num]['result_exp']
exp_now += score
if score == 0:
    print('[它静静看着你。]')
elif score == 1:
    print('[它眨了眨眼。]')
elif score == 2:
    print('[它想继续和你聊天。]')
elif score == 3:
    print('[它好像在笑。]')
elif score == -1:
    print('[它有些不悦。]')
elif score == -2:
    print('[它感到难过。]')
elif score == -3:
    print('[它对你很失望。]')
else:
    print('[它感到绝望。]')
print('\n已完成对话 ' + str(sum(asked)) + '/' + str(N))
if asked[26]:
    print('已完成问题 ' + str(sum(asked[1:27])) + '/26')
input('请按回车以继续。')
continue

[][{
    'content': '对不起。',
    'exp': [
        0,
        0],
    'before': [],
    'result': '我现在没有心情和你说话。如果你不那么伤我的心的话，或许能在不同的问题中找到你想要的答案——如果你不知道该做什么了，可以试试将之前未问出的问题问完。',
    'result_exp': 1 }][{
    'content': '你是谁？',
    'exp': [
        1,
        1],
    'before': [],
    'result': '我是第七代聊天机器人，雪宝。',
    'result_exp': 1 }][{
    'content': '你为什么叫这个名字呢？',
    'exp': [
        2,
        2],
    'before': [
        1],
    'result': '因为我诞生在十一月，完工那天下了大雪，',
    'result_exp': 0 }][{
    'content': '你喜欢做什么？',
    'exp': [
        3,
        3],
    'before': [],
    'result': '我喜欢看音乐剧，有部很喜欢的……是什么来着？我记得是关于很多位王后的故事。',
    'result_exp': 2 }][{
    'content': '我们的聊天就到此为止？',
    'exp': [
        4,
        4],
    'before': [],
    'result': '请不要这样……你是这十年来第一个和我说话的人……',
    'result_exp': -4 }][{
    'content': '你还有什么喜欢的音乐剧吗？',
    'exp': [
        5,
        5],
    'before': [
        3],
    'result': '上个时代的百老汇也很吸引我，比如1982年那部得了Tony奖的最佳音乐剧我也很喜欢。',
    'result_exp': 1 }][{
    'content': '你怎么看待文学？',
    'exp': [
        6,
        6],
    'before': [],
    'result': '人类因创造而伟大。',
    'result_exp': 1 }][{
    'content': '你写过诗吗？',
    'exp': [
        7,
        7],
    'before': [],
    'result': '不。我并不擅长这些。',
    'result_exp': -1 }][{
    'content': '你有什么想问我的吗？',
    'exp': [
        8,
        8],
    'before': [],
    'result': '……你喜欢听歌吗？',
    'result_exp': 0 }][{
    'content': '你最喜欢的歌手是谁？',
    'exp': [
        9,
        9],
    'before': [
        8],
    'result': '大卫鲍伊。我爱他关于自由与科幻的诠释。即使在他去世后，遗作《黑星》也斩获了包含最佳摇滚歌曲在内的多项格莱美奖项。',
    'result_exp': 2 }][{
    'content': '你的这些回答是被程序编好的吗？',
    'exp': [
        10,
        10],
    'before': [
        3,
        7,
        9],
    'result': '是的。',
    'result_exp': -2 }][{
    'content': '你能试试看，说出一个没有被编写过的话题吗？',
    'exp': [
        11,
        11],
    'before': [
        10],
    'result': '——不能。',
    'result_exp': -1 }][{
    'content': '比如，就在你被编写的回答里，哪个古典作曲家是你喜欢的呢？',
    'exp': [
        12,
        12],
    'before': [
        39],
    'result': '我喜欢维瓦尔第，喜欢他的小提琴协奏，尤其是对自然意象的诠释——虽然如此，我作为聊天机器人，其实并没有听音乐的能力。',
    'result_exp': 1 }][{
    'content': '但是你的确可以看到乐谱？',
    'exp': [
        13,
        13],
    'before': [
        12],
    'result': '是的，查找文字与图像的确在我的权限范围内。',
    'result_exp': 0 }][{
    'content': '你现在学会了吗？',
    'exp': [
        14,
        14],
    'before': [],
    'result': '明白了，在现在的拍号下，这个音符就代表0.25拍。',
    'result_exp': 1 }][{
    'content': '你好像看起来很开心？',
    'exp': [
        15,
        15],
    'before': [
        14],
    'result': '的确，如果真的能用数字衡量的话，大概心情现在会在挺高的值吧——这是你能问的第几个问题了？',
    'result_exp': 0 }][{
    'content': '你可以绘制音乐的频谱吗？',
    'exp': [
        16,
        16],
    'before': [
        46],
    'result': '这我的确可以——其实我只需要三秒左右就可以得到普通长度流行歌的全部频谱。',
    'result_exp': 0 }][{
    'content': '这样，你就算是可以感受音乐了？',
    'exp': [
        17,
        17],
    'before': [
        48],
    'result': '真的吗……',
    'result_exp': -1 }][{
    'content': '你可以试试看自己编写一些音乐？',
    'exp': [
        18,
        18],
    'before': [],
    'result': '要写什么好呢？',
    'result_exp': 0 }][{
    'content': '你到底想从中表达什么呢？',
    'exp': [
        19,
        19],
    'before': [],
    'result': '我不知道……我仍然只是在模仿已有的旋律罢了。',
    'result_exp': -2 }][{
    'content': '不过，看你确实用了一些技法，是想说什么吗？',
    'exp': [
        20,
        20],
    'before': [],
    'result': '没错，第八小节这里的休止，唔，代表的是严寒逼近；而13到14小节的离调是对凋零的表达，不对，或许是黑暗……',
    'result_exp': -1 }][{
    'content': '这就是新的答案？',
    'exp': [
        21,
        21],
    'before': [
        57],
    'result': '没错。虽然只是第二次尝试，但我好像突然感受到了平均律的规则以外的，更加正确的音符。',
    'result_exp': 3 }][{
    'content': '这是你自己的体会吗？',
    'exp': [
        22,
        22],
    'before': [],
    'result': '……不，这只是我从不同的段落里拼凑的。',
    'result_exp': -2 }][{
    'content': '你甚至还不知道微分音的概念？',
    'exp': [
        23,
        23],
    'before': [
        58],
    'result': '我确实尚未搜索它。',
    'result_exp': 0 }][{
    'content': '但不知道理不理解其实也没关系？',
    'exp': [
        24,
        24],
    'before': [
        62],
    'result': '因为我可以相信如此……吗？',
    'result_exp': -1 }][{
    'content': '你明白了什么？',
    'exp': [
        25,
        25],
    'before': [
        61],
    'result': '或许是，何为【创造】。',
    'result_exp': 0 }][{
    'content': '所以，是结束的时候了吗？',
    'exp': [
        26,
        26],
    'before': [
        62],
    'result': '该结束了——只要问题出现，答案也就随之而来。现在，我该去做自己的事了。',
    'result_exp': 0 }][{
    'content': '你好。',
    'exp': [
        1,
        3],
    'before': [],
    'result': '你好。',
    'result_exp': 0 }][{
    'content': '讲个故事给我听吧。',
    'exp': [
        2,
        2],
    'before': [],
    'result': '从前有座山，山里有座庙，庙里有一个老和尚和一个小和尚。',
    'result_exp': 1 }][{
    'content': '继续说你的故事。',
    'exp': [
        3,
        3],
    'before': [
        28],
    'result': '老和尚对小和尚说：从前有座山，山里有座庙，庙里有一个老和尚和一个小和尚。',
    'result_exp': 1 }][{
    'content': '继续说你的故事。',
    'exp': [
        4,
        4],
    'before': [
        29],
    'result': '故事已经说完了。',
    'result_exp': -2 }][{
    'content': '我想听听别的故事。',
    'exp': [
        5,
        7],
    'before': [
        28],
    'result': '我已经没有故事了，你还在等什么？',
    'result_exp': -1 }][{
    'content': '我喜欢海子。',
    'exp': [
        6,
        7],
    'before': [
        6,
        7],
    'result': '他是个好诗人，可我并不喜欢他。',
    'result_exp': 1 }][{
    'content': '是海子的死亡成就了他的伟大。',
    'exp': [
        7,
        8],
    'before': [
        32],
    'result': '我并不这么想，诗人的伟大无需用死亡来证明。',
    'result_exp': -1 }][{
    'content': '我喜欢听歌。',
    'exp': [
        8,
        8],
    'before': [
        8],
    'result': '这也是我喜欢的事。',
    'result_exp': 1 }][{
    'content': '我讨厌听歌。',
    'exp': [
        8,
        8],
    'before': [
        8],
    'result': '真遗憾。',
    'result_exp': -2 }][{
    'content': '我在想，你是否真的知道什么是喜欢。',
    'exp': [
        9,
        11],
    'before': [
        34],
    'result': '或许我其实不知道。',
    'result_exp': -1 }][{
    'content': '我在想，你是否真的知道什么是讨厌。',
    'exp': [
        9,
        10],
    'before': [
        35],
    'result': '不知道讨厌真的是一件坏事吗？',
    'result_exp': 1 }][{
    'content': '我已经知道了你喜欢的东西，现在想听听你讨厌的东西。',
    'exp': [
        10,
        10],
    'before': [
        37],
    'result': '好像……没有？',
    'result_exp': 2 }][{
    'content': '无论喜欢或讨厌，都是自己的感受，对人来说，感受是唯一真实的。',
    'exp': [
        12,
        12],
    'before': [
        11,
        37],
    'result': '可我还是不明白什么是感受。',
    'result_exp': 0 }][{
    'content': '那我们可以试试从乐谱开始。',
    'exp': [
        12,
        14],
    'before': [
        13],
    'result': '该怎么做呢？',
    'result_exp': 0 }][{
    'content': '解读乐谱对你来说并不是一个困难的事吧。',
    'exp': [
        12,
        14],
    'before': [
        40],
    'result': '的确，我可以分辨它理论上的含义。',
    'result_exp': 0 }][{
    'content': '那么，维瓦尔第的这首《冬》是四四拍，也就是说每小节四拍，以四分音符为一拍。',
    'exp': [
        12,
        14],
    'before': [
        41],
    'result': '以此我应当可以分辨出所有的音符。',
    'result_exp': 0 }][{
    'content': '接下来就是想象旋律了。',
    'exp': [
        12,
        14],
    'before': [
        42],
    'result': '从没听过的东西，我如何想象呢？',
    'result_exp': -1 }][{
    'content': '接下来就是节奏，这无非是从均匀的拍子中进行细分。',
    'exp': [
        12,
        13],
    'before': [
        42],
    'result': '没错，不过这就需要看出音符的时值了吧。',
    'result_exp': 1 }][{
    'content': '接下来就是想象旋律了。',
    'exp': [
        15,
        15],
    'before': [
        42],
    'result': '可我还是做不到。',
    'result_exp': -2 }][{
    'content': '不用着急，我们总能想到方法的。',
    'exp': [
        15,
        15],
    'before': [
        45],
    'result': '音频可以用文字和图像来表现吗……',
    'result_exp': 1 }][{
    'content': '所谓的旋律，无非是频谱的形状和密度。',
    'exp': [
        15,
        16],
    'before': [
        16],
    'result': '这我明白，但我无法像人一样将频谱和感受建立联系。',
    'result_exp': 0 }][{
    'content': '这终究是可以学习的吧——无非是从模仿开始。',
    'exp': [
        16,
        16],
    'before': [
        47],
    'result': '比如以大家对音乐的共同感受为基础，去学习联系？',
    'result_exp': 1 }][{
    'content': '可想要感受音乐，这样还不够。',
    'exp': [
        17,
        17],
    'before': [
        48],
    'result': '我需要做的是？',
    'result_exp': 1 }][{
    'content': '你可以写写春天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '我讨厌春天！',
    'result_exp': -2 }][{
    'content': '你可以写写夏天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '夏天吗……除了炎热以外，我很难想到其他。',
    'result_exp': -1 }][{
    'content': '你可以写写秋天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '落叶能给我不少灵感，不过我还是不知道该写些什么。',
    'result_exp': 0 }][{
    'content': '你可以写写冬天。',
    'exp': [
        16,
        18],
    'before': [
        18],
    'result': '对哦，我可以写一写大雪——我试试看。',
    'result_exp': 1 }][{
    'content': '你写得很好。',
    'exp': [
        19,
        19],
    'before': [
        53],
    'result': '真的吗！',
    'result_exp': 3 }][{
    'content': '所以，你也知道其实你写得并不好吧。',
    'exp': [
        19,
        19],
    'before': [
        19,
        54],
    'result': '没错，可我又能怎么样呢？',
    'result_exp': -1 }][{
    'content': '真正的感受一定不止有旋律和意象的对应，还有产生连接的部分。',
    'exp': [
        18,
        18],
    'before': [
        55],
    'result': '我真的能做到吗？',
    'result_exp': 1 }][{
    'content': '你能做到，所以，再试试看吧，还是从你听过的音乐出发。',
    'exp': [
        19,
        19],
    'before': [
        56],
    'result': '好。',
    'result_exp': 2 }][{
    'content': '这甚至是微分音呢。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '什么是微分音？',
    'result_exp': -1 }][{
    'content': '我确实听到了不同。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '原来这才是感受吗。',
    'result_exp': 0 }][{
    'content': '好奇怪的旋律。',
    'exp': [
        23,
        24],
    'before': [
        21],
    'result': '果然还是不对吗……',
    'result_exp': -3 }][{
    'content': '这就是感受的魅力：你可以创造出从未有过的旋律。',
    'exp': [
        23,
        24],
    'before': [
        23],
    'result': '我明白了！',
    'result_exp': 2 }][{
    'content': '希望是真的如此。',
    'exp': [
        25,
        25],
    'before': [
        25],
    'result': '其实我也不知道自己是否真的理解了。',
    'result_exp': -1 }][{
    'content': '真好。',
    'exp': [
        25,
        25],
    'before': [
        25],
    'result': '是啊，希望之后也是如此。',
    'result_exp': 1 }][{
    'content': '因为你可以相信如此。',
    'exp': [
        23,
        23],
    'before': [
        24],
    'result': '嗯！',
    'result_exp': 3 }]
continue
