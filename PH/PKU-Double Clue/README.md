# PKU Double Clue

PKU 谜协的微信公众号发布的【二重线索】题目的一些自动化解答，使用基于 python Z3 的 SMT 求解器，加上纸笔求解包 grilops。

这一套谜题中，每一题在两个规则下分别处理都可能出现多解，但将两个规则结合起来看，就能得到唯一解。

[DC05-Maxi Loop & Rail Pool](https://mp.weixin.qq.com/s/bO7KosuLVc6j-Lc6tdYvtA) 被我跳过了，这个实在是太难写了。

## 题目详情

| 题目                                                                               | 程序                          | 说明                                                                       |
| ---------------------------------------------------------------------------------- | ----------------------------- | -------------------------------------------------------------------------- |
| [DC01-Nikoji + Lohkous](https://mp.weixin.qq.com/s/zpOM_THpVvkGRv5KFLSItw)         | `z3_Nikoji_Lohkous.py`        | 平移规则和长宽规则都很麻烦，好在跑起来挺快。                               |
| [DC02-Yajilin + Castle Wall](https://mp.weixin.qq.com/s/yrVWMCtkk8UinjYttKhFyA)    | `z3_Yajilin_CastleWall.py`    | 其实写起来还挺麻烦，但是两种题目官方都有例子，结合一下抄着确实不难。       |
| [DC03-Hitori & Yajisan-Kazusan](https://mp.weixin.qq.com/s/NazJFvsI5YMgL7vURzRD-A) | `z3_Hitori_YajisanKazusan.py` | 不难，规则弄清楚就行，最后出结果很快，验证唯一性稍慢。                     |
| [DC04-Doppelblock & Easy As](https://mp.weixin.qq.com/s/necH45U4Rw3Ov5uDCXDE5w)    | `z3_Doppelblock_EasyAs.py`    | 感觉不如手解，两个条件写起来都很烦人，幸好官方有个差不多的例子。           |
| [DC06-Masyu & Alternate Loop](https://mp.weixin.qq.com/s/bctSnLgfaVjy5mWiiF-lzg)   | `z3_Masyu_AlternateLoop.py`   | Masyu 抄自官方例子，交替回路靠要求黑白格子之间的其它黑白格数是偶数来实现。 |
| [DC07-Yinyang & Nurimisaki](https://mp.weixin.qq.com/s/w8jKJtUAmYsBBj19sLdx1w)     | `z3_Yinyang_Nurimisaki.py`    | 没啥难度，不过要注意是只有白圈在端点上，验证唯一性较慢。                   |
| [DC08-Nurikabe & Canal View](https://mp.weixin.qq.com/s/yC_gOh24rgVof00JeUbkow)    | `z3_Nurikabe_CanalView.py`    | 没啥难度，条件挺多的不能漏。                                               |
