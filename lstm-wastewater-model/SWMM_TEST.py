import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pyswmm import Simulation, Nodes
from sko.GA import GA
import plotly.graph_objects as go
import warnings
from collections import defaultdict

# =====================================================================
# 全局初始化与核心配置
# =====================================================================
warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

FILE_PATH = r'E:\PY\LSTM\inp\xygw_fixed.inp' # ⚠️ 请确保这是你的纯英文路径

# 🌟 J145 作为总排口根节点
monitor_nodes = ['J236', 'J17', 'J59', 'J145']

# 植入处于真实管网区间内的模拟病害 (控制在合理范围防溢流)
TRUE_INFIL_NODE = 'J233'
TRUE_INFIL_VAL = 0.015  # 入渗 15 升/秒
TRUE_LEAK_NODE = 'J118'
TRUE_LEAK_VAL = 0.006  # 泄露 6 升/秒

SIM_HOURS = 6  # 模拟 6 小时让水流彻底走完管网
TIME_STEP = 300  # 强制 5 分钟 (300秒) 采样，对齐时间轴

# =====================================================================
# 模块 1：城市管网静态分析与结构提取
# =====================================================================
print("============ 📊 模块 1：城市地下管网静态体检报告 ============")


def get_swmm_section(file_path, section_name):
	data, in_section = [], False
	with open(file_path, 'r', encoding='utf-8') as f:
		for line in f:
			line = line.strip()
			if line.startswith('['):
				in_section = (line.upper() == section_name.upper())
				continue
			if in_section and line and not line.startswith(';'):
				data.append(line.split())
	return data


df_coords = pd.DataFrame(get_swmm_section(FILE_PATH, '[COORDINATES]'), columns=['Node', 'X', 'Y']).set_index('Node')
df_juncs = pd.DataFrame([j[:2] for j in get_swmm_section(FILE_PATH, '[JUNCTIONS]') if len(j) >= 2],
                        columns=['Node', 'Elevation']).set_index('Node')
df_nodes = df_coords.join(df_juncs, how='inner')
for col in ['X', 'Y', 'Elevation']: df_nodes[col] = pd.to_numeric(df_nodes[col])
all_node_ids = list(df_nodes.index)

conds = get_swmm_section(FILE_PATH, '[CONDUITS]')
df_conds = pd.DataFrame([c[:5] for c in conds if len(c) >= 5], columns=['Link', 'From', 'To', 'Length', 'Roughness'])
df_conds['Length'] = pd.to_numeric(df_conds['Length'])

xsecs = get_swmm_section(FILE_PATH, '[XSECTIONS]')
df_xsecs = pd.DataFrame([x[:3] for x in xsecs if len(x) >= 3], columns=['Link', 'Shape', 'Diameter'])
df_xsecs['Diameter'] = pd.to_numeric(df_xsecs['Diameter'])
df_merged = pd.merge(df_conds, df_xsecs, on='Link', how='left')

print(f"✅ 管网解析成功：共 {len(df_nodes)} 个节点，{len(df_conds)} 条管道。")
print("【管径统计】:")
for _, row in df_merged.groupby('Diameter')['Length'].sum().reset_index().iterrows():
	print(f" -> DN{int(row['Diameter'] * 1000):<4} 管道总长: {row['Length']:.2f} 米")

roughness_map = {'0.01': 'HDPE/塑料管', '0.013': '混凝土管', '0.015': '砖石管'}
df_merged['Material'] = df_merged['Roughness'].map(lambda x: roughness_map.get(str(x), f'其他材质(n={x})'))
print("\n【材质统计】:")
for _, row in df_merged.groupby('Material')['Length'].sum().reset_index().iterrows():
	print(f" -> {row['Material']:<12} 总长: {row['Length']:.2f} 米")

# =====================================================================
# 模块 2：DAG 逆向拓扑与 DMA 边界检索 (核心架构重构)
# =====================================================================
print("\n============ 🔬 模块 2：有向无环图(DAG)重构 DMA 分区 ============")
#
upstream_map = defaultdict(list)
for _, row in df_merged.iterrows():
	upstream_map[row['To']].append(row['From'])

def get_zone_and_boundaries(sensor_node, all_sensors):
	"""
	深度检索逻辑：顺着目标传感器向上游爬取，如果碰到另一个传感器，
	说明那里有“哨兵”把守，该分支检索停止。返回专属区间节点和边界传感器。
	"""
	zone_nodes, bounding_sensors = [], []
	queue, visited = [sensor_node], set([sensor_node])
	while queue:
		curr = queue.pop(0)
		if curr != sensor_node:
			zone_nodes.append(curr)
		for up_node in upstream_map.get(curr, []):
			if up_node not in visited:
				visited.add(up_node)
				if up_node in all_sensors:
					bounding_sensors.append(up_node)
				else:
					queue.append(up_node)
	return zone_nodes, bounding_sensors


# =====================================================================
# 模块 3：生成证据时序与 DMA 区间净体积质量守恒
# =====================================================================
print("\n============ 🌊 模块 3：提取时序波形 & 区间质量守恒粗定位 ============")
base_series = {node: [] for node in monitor_nodes}
target_series = {node: [] for node in monitor_nodes}
time_axis = []


def run_simulation(infil_val, leak_val, output_dict, record_time=False):
	with Simulation(FILE_PATH) as sim:
		sim.end_time = sim.start_time + pd.Timedelta(hours=SIM_HOURS)
		sim.step_advance(TIME_STEP)
		
		n_infil = Nodes(sim)[TRUE_INFIL_NODE]
		n_leak = Nodes(sim)[TRUE_LEAK_NODE]
		sensors = {node: Nodes(sim)[node] for node in monitor_nodes}
		junctions = [n for n in Nodes(sim) if n.is_junction()]
		
		for step in sim:
			for n in junctions: n.generated_inflow(0.001)  # 底水
			if infil_val > 0: n_infil.generated_inflow(0.001 + infil_val)
			if leak_val > 0: n_leak.generated_inflow(max(0, 0.001 - leak_val))
			
			for node in monitor_nodes:
				output_dict[node].append(sensors[node].total_inflow)
			if record_time: time_axis.append(sim.current_time)


# 跑出基线(无病害)与真相(植入病害)
run_simulation(0, 0, base_series)
run_simulation(TRUE_INFIL_VAL, TRUE_LEAK_VAL, target_series, record_time=True)

# 📊 留存证据 1：导出 CSV
df_evidence = pd.DataFrame({'Time': time_axis})
for node in monitor_nodes: df_evidence[f'Sensor_{node}'] = target_series[node]
df_evidence.to_csv('Simulation_Evidence.csv', index=False)

# 📊 留存证据 2：时序波形图
plt.figure(figsize=(12, 6))
for idx, node in enumerate(monitor_nodes):
	plt.plot(time_axis, target_series[node], label=f'节点 {node} (排口/干管) 流量', linewidth=2)
plt.title('城市生命线管网多点位传感器 6 小时监测波形')
plt.xlabel('时间');
plt.ylabel('流量 (m³/s)');
plt.legend();
plt.grid(True)
plt.tight_layout();
plt.savefig('Multi_Sensor_Hydrograph.png', dpi=150)

# 🧮 DMA 区间质量守恒逻辑
print("\n🧮 正在计算各独立封闭区间的【净异常体积(m³)】...")
sensor_delta_vol = {}
for sensor in monitor_nodes:
	# 积分算总体积差
	vol_base = np.trapz(base_series[sensor], dx=TIME_STEP)
	vol_true = np.trapz(target_series[sensor], dx=TIME_STEP)
	sensor_delta_vol[sensor] = vol_true - vol_base

candidate_infil_nodes, candidate_leak_nodes = [], []

for sensor in monitor_nodes:
	zone_nodes, up_sensors = get_zone_and_boundaries(sensor, monitor_nodes)
	
	# 核心：本传感器多出来的水量 减去 从上游入口传过来的水量
	upstream_vol_sum = sum(sensor_delta_vol[up] for up in up_sensors)
	net_vol_anomaly = sensor_delta_vol[sensor] - upstream_vol_sum
	
	print(
		f" -> {sensor} 封闭辖区 | 出口异常: {sensor_delta_vol[sensor]:>7.1f}m³ | 扣除入口后净异常: {net_vol_anomaly:>7.1f}m³")
	
	# 区间阈值：6小时内差额超过 20 m³ 即判定为本区间内爆发病害
	if net_vol_anomaly > 20:
		print(f"   🚨 净体积激增！真凶 100% 在 {sensor} 的专属辖区内！")
		candidate_infil_nodes.extend(zone_nodes)
	elif net_vol_anomaly < -20:
		print(f"   🚨 净体积锐减！真凶 100% 在 {sensor} 的专属辖区内！")
		candidate_leak_nodes.extend(zone_nodes)

if not candidate_infil_nodes: candidate_infil_nodes = all_node_ids
if not candidate_leak_nodes: candidate_leak_nodes = all_node_ids

# =====================================================================
# 模块 4：GA 遗传算法在嫌疑区间内进行全时序波形拟合寻优
# =====================================================================
print(f"\n============ 🧬 模块 4：启动 GA 算法空间降维打击 ============")
print(f"大浪淘沙完毕 -> 待查入渗点降至: {len(candidate_infil_nodes)}个, 待查泄露点降至: {len(candidate_leak_nodes)}个")

def joint_inversion_ga(params):
	idx_infil = int(np.clip(np.round(params[0]), 0, len(candidate_infil_nodes) - 1))
	val_infil = params[1]
	idx_leak = int(np.clip(np.round(params[2]), 0, len(candidate_leak_nodes) - 1))
	val_leak = params[3]
	
	node_infil = candidate_infil_nodes[idx_infil]
	node_leak = candidate_leak_nodes[idx_leak]
	
	sim_series = {node: [] for node in monitor_nodes}
	
	with Simulation(FILE_PATH) as sim:
		sim.end_time = sim.start_time + pd.Timedelta(hours=SIM_HOURS)
		sim.step_advance(TIME_STEP)
		n_inf = Nodes(sim)[node_infil]
		n_lk = Nodes(sim)[node_leak]
		sensors = {node: Nodes(sim)[node] for node in monitor_nodes}
		junctions = [n for n in Nodes(sim) if n.is_junction()]
		
		for step in sim:
			for n in junctions: n.generated_inflow(0.001)
			n_inf.generated_inflow(0.001 + val_infil)
			n_lk.generated_inflow(max(0, 0.001 - val_leak))
			for node in monitor_nodes:
				sim_series[node].append(sensors[node].total_inflow)
	
	total_squared_error, total_points = 0, 0
	for node in monitor_nodes:
		arr_target = np.array(target_series[node])
		arr_sim = np.array(sim_series[node])
		total_squared_error += np.sum((arr_sim - arr_target) ** 2)
		total_points += len(arr_target)
	
	return np.sqrt(total_squared_error / total_points)


# GA 算法：size_pop=16
ga = GA(func=joint_inversion_ga, n_dim=4, size_pop=16, max_iter=10, prob_mut=0.1,
        lb=[0, 0.005, 0, 0.002],
        ub=[len(candidate_infil_nodes) - 1, 0.030, len(candidate_leak_nodes) - 1, 0.020],
        precision=[1, 1e-4, 1, 1e-4])

best_params, best_error = ga.run()

ai_infil_node = candidate_infil_nodes[int(np.clip(np.round(best_params[0]), 0, len(candidate_infil_nodes) - 1))]
ai_infil_val = best_params[1]
ai_leak_node = candidate_leak_nodes[int(np.clip(np.round(best_params[2]), 0, len(candidate_leak_nodes) - 1))]
ai_leak_val = best_params[3]
final_rmse = float(best_error[0]) if isinstance(best_error, (list, np.ndarray)) else float(best_error)

print("\n🎯 ================= 管网 AI 溯源最终报告 ===================")
print(f"【上帝真相】入渗点: {TRUE_INFIL_NODE}({TRUE_INFIL_VAL:.4f}), 泄露点: {TRUE_LEAK_NODE}({TRUE_LEAK_VAL:.4f})")
print(f"【AI 精准反演】入渗点: {ai_infil_node}({ai_infil_val:.4f}), 泄露点: {ai_leak_node}({ai_leak_val:.4f})")
print(f"【拟合评价】残余全波形误差 (RMSE): {final_rmse:.6f}")
print("🎯 ==========================================================")

# =====================================================================
# 模块 5：赛博朋克风 3D 拓扑诊断雷达图 (兼容 Plotly 限制)
# =====================================================================
print("\n🗺️ ============ 模块 5：生成 3D 拓扑诊断雷达 ============")
fig = go.Figure()

x_base, y_base, z_base = [], [], []
x_inf_zone, y_inf_zone, z_inf_zone = [], [], []
x_leak_zone, y_leak_zone, z_leak_zone = [], [], []

for _, row in df_conds.iterrows():
	if row['From'] in df_nodes.index and row['To'] in df_nodes.index:
		x1, y1, z1 = df_nodes.loc[row['From'], ['X', 'Y', 'Elevation']]
		x2, y2, z2 = df_nodes.loc[row['To'], ['X', 'Y', 'Elevation']]
		
		# 凸显质量守恒锁定的区间
		if row['From'] in candidate_infil_nodes or row['To'] in candidate_infil_nodes:
			x_inf_zone.extend([x1, x2, None]);
			y_inf_zone.extend([y1, y2, None]);
			z_inf_zone.extend([z1, z2, None])
		elif row['From'] in candidate_leak_nodes or row['To'] in candidate_leak_nodes:
			x_leak_zone.extend([x1, x2, None]);
			y_leak_zone.extend([y1, y2, None]);
			z_leak_zone.extend([z1, z2, None])
		else:
			x_base.extend([x1, x2, None]);
			y_base.extend([y1, y2, None]);
			z_base.extend([z1, z2, None])

fig.add_trace(
	go.Scatter3d(x=x_base, y=y_base, z=z_base, mode='lines', line=dict(color='rgba(100,100,100,0.3)', width=2),
	             name='健康管网', hoverinfo='none'))
fig.add_trace(go.Scatter3d(x=x_inf_zone, y=y_inf_zone, z=z_inf_zone, mode='lines', line=dict(color='#00ffff', width=6),
                           name='🚨 DMA 锁定的入渗嫌疑区', hoverinfo='none'))
fig.add_trace(
	go.Scatter3d(x=x_leak_zone, y=y_leak_zone, z=z_leak_zone, mode='lines', line=dict(color='#ff3333', width=6),
	             name='🚨 DMA 锁定的泄露嫌疑区', hoverinfo='none'))


def add_node_marker(node_id, color, symbol, size, name_label):
	if node_id in df_nodes.index:
		x, y, z = df_nodes.loc[node_id, ['X', 'Y', 'Elevation']]
		fig.add_trace(go.Scatter3d(x=[x], y=[y], z=[z], mode='markers+text',
		                           marker=dict(color=color, size=size, symbol=symbol,
		                                       line=dict(color='white', width=1)), text=[name_label],
		                           textposition="top center", textfont=dict(color=color, size=12), name=name_label,
		                           hovertext=f"节点: {node_id}<br>高程: {z}m"))


# 标记传感器
for sensor in monitor_nodes: add_node_marker(sensor, '#00ff00', 'square', 8, f'边界监控哨 {sensor}')

# 标记真相点
add_node_marker(TRUE_INFIL_NODE, '#00bfff', 'diamond', 12, f'真·入渗 {TRUE_INFIL_NODE}')
add_node_marker(TRUE_LEAK_NODE, '#ff3333', 'x', 12, f'真·泄露 {TRUE_LEAK_NODE}')

# 标记 AI 反演点
if ai_infil_node != TRUE_INFIL_NODE:
	add_node_marker(ai_infil_node, 'gold', 'circle-open', 14, f'AI猜入渗 {ai_infil_node}')
else:
	add_node_marker(ai_infil_node, 'gold', 'diamond', 18, f'🌟 AI精准命中入渗!')

if ai_leak_node != TRUE_LEAK_NODE:
	add_node_marker(ai_leak_node, 'orange', 'circle-open', 14, f'AI猜泄露 {ai_leak_node}')
else:
	add_node_marker(ai_leak_node, 'orange', 'x', 18, f'🌟 AI精准命中泄露!')

x_range = df_nodes['X'].max() - df_nodes['X'].min()
y_range = df_nodes['Y'].max() - df_nodes['Y'].min()

fig.update_layout(
	title=dict(text='城市生命线 AI 溯源雷达系统 (基于 DMA 质量守恒)', font=dict(color='white', size=20)),
	template='plotly_dark',
	scene=dict(
		xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=False, visible=False),
		zaxis=dict(title='高程 Elevation (m)', gridcolor='#444'),
		aspectmode='manual', aspectratio=dict(x=1, y=y_range / x_range, z=0.25)
	),
	legend=dict(x=0.8, y=0.9, font=dict(color='white')),
	margin=dict(l=0, r=0, b=0, t=50), dragmode='turntable'
)

html_file = 'Lifeline_AI_Radar.html'
fig.write_html(html_file)

print("\n🎉 ====================================================================")
print("🎉 逻辑重构成功，所有模块完美运行！生成成果：")
print("   1. 导出的动态证据数据集: [Simulation_Evidence.csv]")
print("   2. 导出的多源波形图: [Multi_Sensor_Hydrograph.png]")
print(f"   3. 导出的赛博朋克 3D 拓扑舱: [{html_file}] (请用浏览器双击打开)")
print("🎉 ====================================================================")