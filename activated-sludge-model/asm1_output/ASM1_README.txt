ASM1 (Gujer-style) Python 原型 — README

文件:
- asm1_full_simulation_results.csv : 仿真时序 (columns = time_d, S_I, S_S, X_I, X_S, X_BH, X_BA, S_O, S_NH, S_NO, S_ALK)
- asm1_full_parameters.csv : 参数表（可直接编辑后重跑）

说明:
- 此脚本实现 ASM1 的核心生化过程 (异养有氧/缺氧、自养硝化、衰减、水解)。
- 模型为单一 CSTR 反应器；未包含二沉池 (Takács)、曝气传质模型或在线控制模块。
- 参数均为文献/经验初值，必须用现场观测数据校准才能用于工程设计。

建议的后续扩展:
1) 将模型扩展为多单元布局 (厌氧/缺氧/好氧)，并加入二沉池耦合 (Takács)
2) 加入曝气 KLa 与鼓风机能耗模型以估算能耗
3) 用历史数据进行参数校准 (最小二乘 / 贝叶斯方法)
