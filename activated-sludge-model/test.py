import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --------------------------
# 解决中文显示问题
# --------------------------
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]  # 支持中文的字体
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# --------------------------
# 1. 参数设置（BSM1标准，15℃）
# --------------------------
params = {
	# 动力学参数
	'mu_H': 4.0,  # 异养菌最大比生长速率 (1/d)
	'K_S': 10.0,  # 异养菌底物半饱和常数 (mg COD/L)
	'K_OH': 0.2,  # 异养菌氧半饱和常数 (mg O₂/L)
	'mu_A': 0.5,  # 自养菌最大比生长速率 (1/d)
	'K_NH': 1.0,  # 自养菌氨氮半饱和常数 (mg N/L)
	'K_OA': 0.4,  # 自养菌氧半饱和常数 (mg O₂/L)
	
	# 产率与衰减参数
	'Y_H': 0.67,  # 异养菌产率系数 (g VSS/g COD)
	'Y_A': 0.24,  # 自养菌产率系数 (g VSS/g N)
	
	# 水力参数
	'q_in': 100,  # 进水流量 (m³/h)
	'q_out': 100,  # 出水流量 (m³/h)
	'V': 500,  # 反应池容积 (m³)
	'S_O_in': 2.0  # 进水溶解氧浓度 (mg/L)
}


# --------------------------
# 2. 辅助函数：计算反应速率
# --------------------------
def calc_rates(S, X, params):
	"""计算异养菌/自养菌生长速率及溶解氧消耗速率"""
	# 状态变量
	S_O = S[0]  # 溶解氧浓度 (mg O₂/L)
	S_S = S[1]  # 可溶性底物 (mg COD/L)
	S_NH = S[2]  # 氨氮浓度 (mg N/L)
	X_BH = X[0]  # 异养菌浓度 (mg VSS/L)
	X_BA = X[1]  # 自养菌浓度 (mg VSS/L)
	
	# 异养菌好氧生长速率 ρ₁ (mg VSS/(L·h))
	rho1 = (params['mu_H'] / 24) * \
	       (S_S / (params['K_S'] + S_S)) * \
	       (S_O / (params['K_OH'] + S_O)) * \
	       X_BH
	
	# 自养菌生长速率 ρ₃ (mg VSS/(L·h))
	rho3 = (params['mu_A'] / 24) * \
	       (S_NH / (params['K_NH'] + S_NH)) * \
	       (S_O / (params['K_OA'] + S_O)) * \
	       X_BA
	
	# 溶解氧消耗速率 r₈ (mg O₂/(L·h))
	r8 = - ((1 - params['Y_H']) / params['Y_H']) * rho1 - \
	     ((4.57 - params['Y_A']) / params['Y_A']) * rho3
	
	return rho1, rho3, r8


# --------------------------
# 3. 溶解氧动态模型
# --------------------------
def do_dynamics(t, S_O, S, X, params):
	"""溶解氧浓度随时间变化的微分方程"""
	# 计算生化反应消耗项
	_, _, r8 = calc_rates([S_O, S[0], S[1]], X, params)
	
	# 计算水力输运项
	transport = (params['q_in'] * params['S_O_in'] - params['q_out'] * S_O) / params['V']
	
	# 总变化率 dS_O/dt
	dSO_dt = transport + r8
	return dSO_dt


# --------------------------
# 4. 模拟设置与运行
# --------------------------
# 初始状态
S = [15.0, 3.0]  # [S_S (mg COD/L), S_NH (mg N/L)]
X = [2000.0, 500.0]  # [X_BH (mg VSS/L), X_BA (mg VSS/L)]
S_O_init = 2.5  # 初始溶解氧浓度 (mg/L)

# 模拟时间（0-0.1小时，即0-6分钟，因溶解氧消耗快）
t_span = (0, 0.1)
t_eval = np.linspace(0, 0.1, 100)

# 求解微分方程
sol = solve_ivp(
	fun=lambda t, y: do_dynamics(t, y, S, X, params),
	t_span=t_span,
	y0=[S_O_init],
	t_eval=t_eval,
	method='RK45'
)

# --------------------------
# 5. 结果可视化
# --------------------------
plt.figure(figsize=(10, 6))

# 溶解氧变化曲线
plt.plot(sol.t * 60, sol.y[0], 'b-', linewidth=2, label='溶解氧浓度')
plt.axhline(y=0, color='r', linestyle='--', label='缺氧临界点 (0 mg/L)')

# 标注关键信息
plt.xlabel('时间 (分钟)', fontsize=12)
plt.ylabel('溶解氧浓度 (mg O₂/L)', fontsize=12)
plt.title('溶解氧动态变化（忽略曝气）', fontsize=14)
plt.grid(alpha=0.3)
plt.legend(fontsize=10)

# 计算耗尽时间
do_zero_time = np.interp(0, sol.y[0][::-1], sol.t[::-1]) * 60  # 溶解氧耗尽时间（分钟）
plt.text(0.5, 0.1, f'溶解氧耗尽时间: {do_zero_time:.1f} 分钟',
         transform=plt.gca().transAxes, fontsize=10,
         bbox=dict(facecolor='white', alpha=0.8))

plt.tight_layout()
plt.show()

# --------------------------
# 6. 关键速率输出
# --------------------------
# 计算初始时刻的反应速率
rho1, rho3, r8 = calc_rates([S_O_init, S[0], S[1]], X, params)
print(f"初始异养菌好氧生长速率: {rho1:.2f} mg VSS/(L·h)")
print(f"初始自养菌生长速率: {rho3:.2f} mg VSS/(L·h)")
print(f"初始溶解氧消耗速率: {r8:.2f} mg O₂/(L·h)")
print(f"水力输运对溶解氧的影响: {(params['q_in'] * (params['S_O_in'] - S_O_init)) / params['V']:.2f} mg O₂/(L·h)")