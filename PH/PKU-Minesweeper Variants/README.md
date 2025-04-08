# PKU Minesweeper Variants

PKU 谜协的微信公众号发布的【扫雷变体】题目的一些自动化解答，使用基于 python Z3 的 SMT 求解器。

这类题目就来源于《14 种扫雷变体》的各种玩法。

## 题目详情

| 题目                                                                 | 程序                  | 说明                                                                                     |
| -------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------- |
| [MV01-[V] 普通](https://mp.weixin.qq.com/s/PZx7oWK83aAxvmtqqq1eGA)   | `z3_Minesweeper_V.py` | 很简单，很常规。                                                                         |
| [MV02-[Q] 无方](https://mp.weixin.qq.com/s/BsFtQj3rYB9o4AgwApYIMg)   | `z3_Minesweeper_Q.py` | 要求任何 $2 \times 2$ 小方格内有雷，很简单。                                             |
| [MV03-[C] 八连通](https://mp.weixin.qq.com/s/Rtt_3F8HN_Ti2TAP23wzZQ) | `z3_Minesweeper_C.py` | 要求所有雷相连（包括对角），这个条件很不好写，抄了个以前的代码，用距离矩阵判断是否连通。 |
| [MV04-[T] 无三连](https://mp.weixin.qq.com/s/TN2mlVNbCHoJOaErrwOEEA) | `z3_Minesweeper_T.py` | 要求雷不能在横向、纵向和斜向连成三个，这个条件好写。                                     |
