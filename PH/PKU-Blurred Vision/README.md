# PKU Blurred Vision

PKU 谜协的微信公众号发布的【纸笔成谜】题目的一些自动化解答，使用基于 python Z3 的 SMT 求解器。

这类题目就是纸笔谜题的改版，在每道题中有一些线索是不可见的，但同时多出了一些对于这些线索的约束。

## 题目详情

跳过了 BV01 因为实在太简单了。

| 题目                                                                 | 程序               | 说明                                                                         |
| -------------------------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------- |
| [BV02-Kropki](https://mp.weixin.qq.com/s/5azrvdPjg3axDM7op9-8HQ)     | `z3_Kropki.py`     | 这题写起来非常方便，当然手解不难。                                           |
| [BV03-Myopia](https://mp.weixin.qq.com/s/PzeHU8opqRdwB-PW7EQWCg)     | `z3_Myopia.py`     | 写起来很痛苦的一题，最终采用了枚举路径的方式，再把边牵连过来，求解速度不快。 |
| [BV04-Skyscraper](https://mp.weixin.qq.com/s/xKEjJ7OKO9joCoKpujrlVg) | `z3_Skyscraper.py` | 不难实现，算起来也快，大概也就一小时搞定。这题我手解反而没思路。             |
