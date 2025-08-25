# PKU Island of Insight

PKU 谜协的微信公众号发布的【真知之岛】题目的一些自动化解答，使用基于 python Z3 的 SMT 求解器，加上纸笔求解包 grilops。

这个系列由一系列涂黑类谜题组成。已知黑圈必须对应是黑格，白圈必须对应白格。剩下的规则每题不同，多彩多样。

## 题目详情

| 题目                                                                   | 程序                | 说明                                                                            |
| ---------------------------------------------------------------------- | ------------------- | ------------------------------------------------------------------------------- |
| [IO01-Logic Grid](https://mp.weixin.qq.com/s/QX9RnIrDn_z7ov1iHc2lug)   | `z3_LogicGrid_1.py` | 写起来很简单，但算起来并不快，不过可以接受。                                    |
| [IO02-Logic Grid 2](https://mp.weixin.qq.com/s/SyMBbgeDVxVDTgB4X2gKgA) | `z3_LogicGrid_2.py` | 对称性要求是比较难实现的，我照着官方例子里的中心对称性改了个轴对称的。          |
| [IO03-Logic Grid 3](https://mp.weixin.qq.com/s/VZEnwL3IKN3tHDH6tOixgg) | `z3_LogicGrid_3.py` | 简单，跑起来大概十几秒。                                                        |
| [IO04-Logic Grid 4](https://mp.weixin.qq.com/s/iXgADE1idGZGvguwnaD7IQ) | `z3_LogicGrid_4.py` | 简单题，形状限制硬写就好。                                                      |
| [IO04-Logic Grid 5](https://mp.weixin.qq.com/s/f4KWCNdktGC-2zh7o2bokw) | `z3_LogicGrid_5.py` | 写起来简单，但跑起来很慢。所以我对黑块面积为 3 加了特殊判断，立马就可以秒出了。 |
