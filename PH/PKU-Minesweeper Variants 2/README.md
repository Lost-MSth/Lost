# PKU Minesweeper Variants 2

PKU 谜协的微信公众号发布的【扫雷变体 2】题目的一些自动化解答，使用基于 python Z3 的 SMT 求解器，部分题用了纸笔求解包 grilops。

这类题目就来源于《14 种扫雷变体》的各种玩法。

## 题目详情

| 题目                                                                | 程序                  | 说明                                        |
| ------------------------------------------------------------------- | --------------------- | ------------------------------------------- |
| [2MV01-[M] 多雷](https://mp.weixin.qq.com/s/5UCGEOKGyyIvgsZeSbT0Eg) | `z3_Minesweeper_M.py` | 在原版基础上稍微修改即可。                  |
| [2MV02-[L] 误差](https://mp.weixin.qq.com/s/bpBX62FnBDpGnRFVU34Gww) | `z3_Minesweeper_L.py` | 同样稍作修改即可，挺简单。                  |
| [2MV03-[W] 数墙](https://mp.weixin.qq.com/s/Fy4NztVHgWJZzP_pEDQXzQ) | `z3_Minesweeper_W.py` | 使用二进制硬编码。                          |
| [2MV04-[N] 负雷](https://mp.weixin.qq.com/s/-67mxOvk6XKyyzYjoPwfZQ) | `z3_Minesweeper_N.py` | 不难，有点小坑，注意取值范围。              |
| [2MV05-[X] 十字](https://mp.weixin.qq.com/s/jk0jPqQJvzbzvn1gh5evVw) | `z3_Minesweeper_X.py` | 简单改改即可。                              |
| [2MV06-[P] 划分](https://mp.weixin.qq.com/s/HWWoRyIFBX8NUDhfvnLEWQ) | `z3_Minesweeper_P.py` | 使用二进制硬编码。                          |
| [2MV07-[E] 视野](https://mp.weixin.qq.com/s/jk0jPqQJvzbzvn1gh5evVw) | `z3_Minesweeper_E.py` | 用上了 grilops 的 sightlines 功能就不难了。 |
| [2MV08-[V] 标准](https://mp.weixin.qq.com/s/rNv_-_YWhparb0xJz2ad1g) | `z3_Minesweeper_V.py` | 与之前相同，但这次我用上了 grilops。        |
