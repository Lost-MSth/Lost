# PKU Minesweeper Variants 2

PKU 谜协的微信公众号发布的【扫雷变体 2】题目的一些自动化解答，使用基于 python Z3 的 SMT 求解器。

这类题目就来源于《14 种扫雷变体》的各种玩法。

## 题目详情

| 题目                                                                | 程序                  | 说明                           |
| ------------------------------------------------------------------- | --------------------- | ------------------------------ |
| [2MV01-[M] 多雷](https://mp.weixin.qq.com/s/5UCGEOKGyyIvgsZeSbT0Eg) | `z3_Minesweeper_M.py` | 在原版基础上稍微修改即可。     |
| [2MV02-[L] 误差](https://mp.weixin.qq.com/s/bpBX62FnBDpGnRFVU34Gww) | `z3_Minesweeper_L.py` | 同样稍作修改即可，挺简单。     |
| [2MV03-[W] 数墙](https://mp.weixin.qq.com/s/Fy4NztVHgWJZzP_pEDQXzQ) | x                     | 暂且不会，太麻烦了。           |
| [2MV04-[N] 负雷](https://mp.weixin.qq.com/s/-67mxOvk6XKyyzYjoPwfZQ) | `z3_Minesweeper_N.py` | 不难，有点小坑，注意取值范围。 |
