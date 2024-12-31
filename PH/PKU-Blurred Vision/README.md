# PKU Blurred Vision

PKU 谜协的微信公众号发布的【纸笔成谜】题目的一些自动化解答，使用基于 python Z3 的 SMT 求解器。

这类题目就是纸笔谜题的改版，在每道题中有一些线索是不可见的，但同时多出了一些对于这些线索的约束。

## 题目详情

跳过了 BV01 因为实在太简单了，跳过 BV08 因为非常难实现而且手解挺简单。

| 题目                                                                   | 程序                 | 说明                                                                                             |
| ---------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------ |
| [BV02-Kropki](https://mp.weixin.qq.com/s/5azrvdPjg3axDM7op9-8HQ)       | `z3_Kropki.py`       | 这题写起来非常方便，当然手解不难。                                                               |
| [BV03-Myopia](https://mp.weixin.qq.com/s/PzeHU8opqRdwB-PW7EQWCg)       | `z3_Myopia.py`       | 写起来很痛苦的一题，最终采用了枚举路径的方式，再把边牵连过来，求解速度不快。                     |
| [BV04-Skyscraper](https://mp.weixin.qq.com/s/xKEjJ7OKO9joCoKpujrlVg)   | `z3_Skyscraper.py`   | 不难实现，算起来也快，大概也就一小时搞定。这题我手解反而没思路。                                 |
| [BV05-Compass](https://mp.weixin.qq.com/s/rI1m4ETujaZasqgg7NlfrQ)      | `z3_Compass/main.py` | 直接到网上找找实现然后改了改就跑起出来了，中心对称性似乎只是为了限制多解，所以并没编写严格逻辑。 |
| :x: [BV06-Pentopia](https://mp.weixin.qq.com/s/kfxQp2D4ao9QwmYIqFlxyQ) | `z3_Pentopia.py`     | 手解更简单，我写的还没法判断形状，大失败！（但能跑出来差不多的）                                 |
| [BV07-Masyu](https://mp.weixin.qq.com/s/XUuFv6Q9G22d4xv8Wt5abg)        | `z3_Masyu.py`        | 枚举路径可解，但在多进程下耗时大概几天。                                                         |
