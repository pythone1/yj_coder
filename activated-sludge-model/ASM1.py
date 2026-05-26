#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ASM1 (Gujer-style) 单罐 CSTR 实现（教学 / 工程原型）
- 作者: ChatGPT (示例代码)
- 功能: 实现 ASM1 核心过程并进行 0-10 天数值仿真，输出 CSV 与 PNG 图像。
- 注意:
  * 这是核心模型的工程/教学原型，便于理解与扩展；非直接用于工程设计的最终版。
  * 若要做工程化交付，请用现场数据做参数校准并加入沉降/多单元耦合、曝气/传质模型等。
"""

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import os

# ------------------------------------------------------------
# 1) 状态变量定义（顺序要与后续 y 向量一致）
# ------------------------------------------------------------
STATE_NAMES = [
    "S_I",   # 可溶惰性有机物 (mg COD / L)
    "S_S",   # 可溶易降解有机物 (readily biodegradable COD) (mg COD / L)
    "X_I",   # 惰性颗粒有机物 (mg COD / L)
    "X_S",   # 易降解颗粒有机物 (mg COD / L)
    "X_BH",  # 异养活性生物量（以 COD 等价计）(mg COD / L)
    "X_BA",  # 自养（硝化菌）生物量 (mg COD / L)
    "S_O",   # 溶解氧 (mg O2 / L)
    "S_NH",  # 铵态氮 (NH4-N) (mg N / L)
    "S_NO",  # 硝态氮 (NOx-N = NO2+NO3) (mg N / L)
    "S_ALK"  # 碱度 (作为简化代理，mg CaCO3 / L)
]

# ------------------------------------------------------------
# 2) 参数表（默认典型值） — 运行前可直接编辑这些值以匹配现场或实验设定
# ------------------------------------------------------------
params = {
    # 动力学参数（基于 20°C 的参考值）
    "mu_H"  : 6.0,     # 1/d 异养菌最大比生长速率
    "K_S"   : 20.0,    # mg COD/L 半饱和常数（底物）
    "K_OH"  : 0.2,     # mg O2/L 半饱和常数（异养菌对氧）
    "mu_A"  : 0.8,     # 1/d 自养（硝化菌）最大比生长速率
    "K_NH"  : 1.0,     # mg N/L 半饱和常数（氨氮）
    "K_OA"  : 0.4,     # mg O2/L 半饱和常数（自养菌对氧）
    "eta_g" : 0.8,     # 反硝化相对生长因子（缺氧下生长效率）

    # 产率与衰减
    "Y_H"   : 0.67,    # gCOD biomass / gCOD substrate（异养菌生物量产率）
    "b_H"   : 0.62,    # 1/d 异养菌衰减率
    "Y_A"   : 0.24,    # gCOD biomass / gN oxidized（自养菌产率）
    "b_A"   : 0.08,    # 1/d 自养菌衰减率

    # 水解与其他
    "k_hyd" : 2.0,     # 1/d 水解速率（X_S -> S_S 的简化速率）

    # 氧耗近似系数（用于估算 DO 消耗量）
    "O_req_per_COD" : 2.0,    # mg O2 / mg COD（近似）
    "O_req_per_N"   : 4.57,   # mg O2 / mg N（NH4 -> NO3 的理论氧需）

    # 水力学（CSTR）
    "Q" : 10000.0,   # L/d 进水量
    "V" : 100000.0,  # L 反应器体积

    # 进水浓度（典型市政值，运行前可调整）
    "S_I_in"  : 10.0,
    "S_S_in"  : 150.0,
    "X_I_in"  : 20.0,
    "X_S_in"  : 50.0,
    "X_BH_in" : 30.0,
    "X_BA_in" : 5.0,
    "S_O_in"  : 0.0,
    "S_NH_in" : 40.0,
    "S_NO_in" : 0.0,
    "S_ALK_in": 200.0,

    # 温度与温度修正因子（若现场温度不是 20°C，可用 theta 修正）
    "T" : 20.0,  # 现场温度 (°C)
    "theta_H" : 1.04,  # 异养速率温度因子
    "theta_A" : 1.06,  # 自养速率温度因子

    # 数值/输出控制
    "allow_negative" : False  # 是否允许负浓度（False: 尽量避免出现负值）
}

# ------------------------------------------------------------
# 3) 温度修正函数（把 20°C 下的参数变成 T°C 下的有效参数）
# ------------------------------------------------------------
def temp_corr(k20, theta, T):
    """
    k20: 在 20°C 的参数值
    theta: 温度因子（常见 1.04~1.08）
    T: 现场温度（°C）
    返回：T 温度下的参数
    """
    return k20 * (theta ** (T - 20.0))

# ------------------------------------------------------------
# 4) 计算各过程速率的函数（Monod 型表达式等）
#    返回字典形式的多个过程速率（单位：mg/L/d 或 mgN/L/d 等）
# ------------------------------------------------------------
def calc_rates(states, p):
    """
    states: 当前状态向量 [S_I, S_S, X_I, X_S, X_BH, X_BA, S_O, S_NH, S_NO, S_ALK]
    p: 参数字典
    """
    S_I, S_S, X_I, X_S, X_BH, X_BA, S_O, S_NH, S_NO, S_ALK = states

    # 温度校正后的动力学参数
    mu_H = temp_corr(p["mu_H"], p["theta_H"], p["T"])
    mu_A = temp_corr(p["mu_A"], p["theta_A"], p["T"])

    # Monod 分数项（防止除零）
    f_S = S_S / (p["K_S"] + S_S) if (p["K_S"] + S_S) > 0 else 0.0
    f_Oh = S_O / (p["K_OH"] + S_O) if (p["K_OH"] + S_O) > 0 else 0.0
    f_Oa = S_O / (p["K_OA"] + S_O) if (p["K_OA"] + S_O) > 0 else 0.0
    f_NH = S_NH / (p["K_NH"] + S_NH) if (p["K_NH"] + S_NH) > 0 else 0.0
    # 对 NO3 的依赖采用简化项（比例关系）
    f_NO = S_NO / (1.0 + S_NO)

    # 过程速率（以生物量增长速率或相应消耗速率表达）
    # r1: 异养菌有氧生长（生物量增长 mgCOD/L/d）
    r1 = mu_H * f_S * f_Oh * X_BH
    # r2: 异养菌缺氧生长（反硝化相关，生物量增长 mgCOD/L/d）
    r2 = mu_H * f_S * f_NO * p["eta_g"] * X_BH
    # r3: 自养菌生长（硝化相关，生物量增长 mgCOD/L/d）
    r3 = mu_A * f_NH * f_Oa * X_BA
    # r4: 异养菌衰减（mgCOD/L/d）
    r4 = p["b_H"] * X_BH
    # r5: 自养菌衰减
    r5 = p["b_A"] * X_BA
    # r6: 水解（X_S -> S_S）
    r6 = p["k_hyd"] * X_S

    # 底物（S_S）被消耗的量（mg COD/L/d）——由生物量增长和产率关系决定
    Ss_cons_aer = r1 / p["Y_H"] if p["Y_H"] > 0 else 0.0
    Ss_cons_anox = r2 / p["Y_H"] if p["Y_H"] > 0 else 0.0

    # 氨被氧化的速率（mg N/L/d），通过自养生物量增长和 Y_A 反算
    N_oxidized = r3 / p["Y_A"] if p["Y_A"] > 0 else 0.0

    # 氧耗估算（mg O2/L/d）
    O_cons_by_COD = Ss_cons_aer * p["O_req_per_COD"]
    O_cons_by_nitr = N_oxidized * p["O_req_per_N"]
    O_total = O_cons_by_COD + O_cons_by_nitr

    # NO3 的产生与消耗（mg N/L/d）
    NO3_produced = N_oxidized
    # 简化：把反硝化消耗与缺氧底物消耗做近似比例（此处用示例比例）
    NO3_consumed = Ss_cons_anox * 0.5

    return {
        "r1_het_aer_biomass" : r1,
        "r2_het_anox_biomass": r2,
        "r3_autotroph_biomass": r3,
        "r4_decay_het": r4,
        "r5_decay_aut": r5,
        "r6_hydrolysis": r6,
        "Ss_cons_aer": Ss_cons_aer,
        "Ss_cons_anox": Ss_cons_anox,
        "N_oxidized": N_oxidized,
        "O_total": O_total,
        "NO3_produced": NO3_produced,
        "NO3_consumed": NO3_consumed
    }

# ------------------------------------------------------------
# 5) Gujer 矩阵风格的质量平衡（为可读性直接用速率计算导数）
#    对每个状态变量写出 dC/dt = (Q/V)*(C_in - C) + process contributions
# ------------------------------------------------------------
def asm1_cstr_ode(t, y, p):
    """
    ODE 函数。y 与返回导数的顺序必须与 STATE_NAMES 对应。
    """
    S_I, S_S, X_I, X_S, X_BH, X_BA, S_O, S_NH, S_NO, S_ALK = y
    Q = p["Q"]
    V = p["V"]

    # 进水浓度（从参数读取）
    S_I_in  = p["S_I_in"]
    S_S_in  = p["S_S_in"]
    X_I_in  = p["X_I_in"]
    X_S_in  = p["X_S_in"]
    X_BH_in = p["X_BH_in"]
    X_BA_in = p["X_BA_in"]
    S_O_in  = p["S_O_in"]
    S_NH_in = p["S_NH_in"]
    S_NO_in = p["S_NO_in"]
    S_ALK_in= p["S_ALK_in"]

    # 计算过程速率
    rates = calc_rates([S_I, S_S, X_I, X_S, X_BH, X_BA, S_O, S_NH, S_NO, S_ALK], p)

    # -------- 状态方程 --------
    # S_I (可溶惰性) : 主要来自生物衰减的可溶部分（这里假设衰减的一部分变为可溶惰性）
    f_d_si = 0.6  # 假设：衰减产物中 60% 为可溶惰性
    dS_I_dt = (Q/V)*(S_I_in - S_I) + f_d_si*(rates["r4_decay_het"] + rates["r5_decay_aut"])

    # S_S (可溶易降解) : 来源 = 水解(r6) ; 去向 = 异养菌有氧/缺氧消耗
    dS_S_dt = (Q/V)*(S_S_in - S_S) + rates["r6_hydrolysis"] - rates["Ss_cons_aer"] - rates["Ss_cons_anox"]

    # X_I (惰性颗粒) : 来自衰减的颗粒部分
    f_d_xi = 0.4  # 假设：衰减到颗粒的份额
    dX_I_dt = (Q/V)*(X_I_in - X_I) + f_d_xi*(rates["r4_decay_het"] + rates["r5_decay_aut"])

    # X_S (可降解颗粒) : 主要被水解消耗
    dX_S_dt = (Q/V)*(X_S_in - X_S) - rates["r6_hydrolysis"]

    # X_BH (异养生物量) : 生长 - 衰减 + 水力学项
    dX_BH_dt = (Q/V)*(X_BH_in - X_BH) + rates["r1_het_aer_biomass"] + rates["r2_het_anox_biomass"] - rates["r4_decay_het"]

    # X_BA (自养生物量) : 生长 - 衰减 + 水力学项
    dX_BA_dt = (Q/V)*(X_BA_in - X_BA) + rates["r3_autotroph_biomass"] - rates["r5_decay_aut"]

    # S_O (溶解氧) : 进水 - 消耗（此处未加入曝气补氧项，如需模拟 DO 控制应加入 KLa 项）
    dS_O_dt = (Q/V)*(S_O_in - S_O) - rates["O_total"]

    # S_NH (NH4-N) : 进水 - 硝化消耗
    dS_NH_dt = (Q/V)*(S_NH_in - S_NH) - rates["N_oxidized"]

    # S_NO (NOx-N) : 进水 + 硝化产生 - 反硝化消耗
    dS_NO_dt = (Q/V)*(S_NO_in - S_NO) + rates["NO3_produced"] - rates["NO3_consumed"]

    # S_ALK (碱度) 简化代理：硝化消耗碱度（近似值，例如 7.14 mg CaCO3 / mg N）
    alk_consume_per_N = 7.14
    dS_ALK_dt = (Q/V)*(S_ALK_in - S_ALK) - rates["N_oxidized"] * alk_consume_per_N

    derivs = [dS_I_dt, dS_S_dt, dX_I_dt, dX_S_dt, dX_BH_dt, dX_BA_dt, dS_O_dt, dS_NH_dt, dS_NO_dt, dS_ALK_dt]

    # 防止数值解出现非常小的负值（可选）
    if not p.get("allow_negative", False):
        derivs = [d if d is not None else 0.0 for d in derivs]

    return derivs

# ------------------------------------------------------------
# 6) 初始条件（可根据需要修改）
# ------------------------------------------------------------
y0 = [
    params["S_I_in"],   # S_I 初始设为进水值
    params["S_S_in"],   # S_S
    params["X_I_in"],   # X_I
    params["X_S_in"],   # X_S
    300.0,              # X_BH 初始混合液生物量 (mg COD/L) - 可修改
    50.0,               # X_BA 初始值
    2.0,                # S_O 初始 (mg O2/L)
    params["S_NH_in"],  # S_NH 初始
    params["S_NO_in"],  # S_NO 初始
    params["S_ALK_in"]  # S_ALK 初始
]

# ------------------------------------------------------------
# 7) 仿真设置与运行
# ------------------------------------------------------------
t_start = 0.0
t_end = 10.0   # 天
n_points = 201
t_eval = np.linspace(t_start, t_end, n_points)

print("开始仿真: 0 -> {:.1f} d, 点数 = {}".format(t_end, n_points))

sol = solve_ivp(lambda t, y: asm1_cstr_ode(t, y, params),
                (t_start, t_end), y0, t_eval=t_eval, method='RK45', rtol=1e-6)

# 检查求解结果
if not sol.success:
    raise RuntimeError("ODE 求解失败: " + str(sol.message))

# ------------------------------------------------------------
# 8) 将结果保存为 CSV，并输出参数表与 README（帮助文档）
# ------------------------------------------------------------
out_dir = "./asm1_output"
os.makedirs(out_dir, exist_ok=True)

df = pd.DataFrame(sol.y.T, columns=STATE_NAMES)
df.insert(0, "time_d", sol.t)
csv_out = os.path.join(out_dir, "asm1_full_simulation_results.csv")
df.to_csv(csv_out, index=False, float_format="%.6f")
print("仿真结果已写入:", csv_out)

# 保存参数表
param_df = pd.DataFrame.from_dict(params, orient='index', columns=['value'])
param_df.index.name = "parameter"
param_csv = os.path.join(out_dir, "asm1_full_parameters.csv")
param_df.to_csv(param_csv, index=True, float_format="%.6f")
print("参数表已写入:", param_csv)

# README 简要说明
readme_text = f"""ASM1 (Gujer-style) Python 原型 — README

文件:
- asm1_full_simulation_results.csv : 仿真时序 (columns = time_d, {', '.join(STATE_NAMES)})
- asm1_full_parameters.csv : 参数表（可直接编辑后重跑）

说明:
- 此脚本实现 ASM1 的核心生化过程 (异养有氧/缺氧、自养硝化、衰减、水解)。
- 模型为单一 CSTR 反应器；未包含二沉池 (Takács)、曝气传质模型或在线控制模块。
- 参数均为文献/经验初值，必须用现场观测数据校准才能用于工程设计。

建议的后续扩展:
1) 将模型扩展为多单元布局 (厌氧/缺氧/好氧)，并加入二沉池耦合 (Takács)
2) 加入曝气 KLa 与鼓风机能耗模型以估算能耗
3) 用历史数据进行参数校准 (最小二乘 / 贝叶斯方法)
"""
with open(os.path.join(out_dir, "ASM1_README.txt"), "w", encoding="utf-8") as f:
    f.write(readme_text)
print("README 已写入:", os.path.join(out_dir, "ASM1_README.txt"))

# ------------------------------------------------------------
# 9) 生成每个状态变量的 PNG 图用于快速检查
# ------------------------------------------------------------
for col in df.columns:
    if col == "time_d":
        continue
    plt.figure(figsize=(8,3.2))
    plt.plot(df["time_d"], df[col], linewidth=1.5)
    plt.xlabel("Time (d)")
    plt.ylabel(col)
    plt.title(f"{col} over time")
    plt.grid(True, linestyle='--', alpha=0.6)
    png_path = os.path.join(out_dir, f"plot_{col}.png")
    plt.tight_layout()
    plt.savefig(png_path, dpi=150)
    plt.close()
print("PNG 图像已保存到目录:", out_dir)

# ------------------------------------------------------------
# 10) 完成提示
# ------------------------------------------------------------
print("仿真完成。输出文件位于目录:", out_dir)
print("你可以编辑参数 CSV 后重新运行此脚本以进行敏感性测试或校准。")
