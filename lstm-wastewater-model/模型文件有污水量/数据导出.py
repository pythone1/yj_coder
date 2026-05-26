import os
import re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def parse_inp_data(filepath):
	"""读取并粗解析 INP 文件"""
	with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
		lines = f.readlines()
	
	data = {}
	current_section = None
	for line in lines:
		line = line.strip()
		if not line or line.startswith(';'): continue
		if line.startswith('['):
			current_section = line
			data[current_section] = []
			continue
		if current_section:
			parts = re.split(r'\s+', line)
			data[current_section].append(parts)
	return data


def extract_nodes_links(data):
	"""提取基础坐标、标高、管径信息"""
	df_junc = pd.DataFrame([r[:2] for r in data.get('[JUNCTIONS]', [])], columns=['Node', 'Elevation'])
	df_junc['Elevation'] = pd.to_numeric(df_junc['Elevation'], errors='coerce')
	
	df_coord = pd.DataFrame([r[:3] for r in data.get('[COORDINATES]', [])], columns=['Node', 'X', 'Y'])
	df_coord['X'] = pd.to_numeric(df_coord['X'], errors='coerce')
	df_coord['Y'] = pd.to_numeric(df_coord['Y'], errors='coerce')
	nodes = pd.merge(df_junc, df_coord, on='Node', how='inner')
	
	cols_cond = ['Link', 'FromNode', 'ToNode', 'Length', 'Roughness', 'InOffset', 'OutOffset', 'InitFlow', 'MaxFlow']
	cond_data = [row[:9] + [0] * (9 - len(row)) for row in data.get('[CONDUITS]', [])]
	df_cond = pd.DataFrame(cond_data, columns=cols_cond)
	
	cols_xsec = ['Link', 'Shape', 'Geom1', 'Geom2', 'Geom3', 'Geom4', 'Barrels', 'Culvert']
	xsec_data = [row[:8] + [0] * (8 - len(row)) for row in data.get('[XSECTIONS]', [])]
	df_xsec = pd.DataFrame(xsec_data, columns=cols_xsec)
	df_xsec['Geom1'] = pd.to_numeric(df_xsec['Geom1'], errors='coerce')
	links = pd.merge(df_cond, df_xsec, on='Link', how='inner')
	
	return nodes, links


def extract_timeseries(data):
	"""提取具体的曲线数值"""
	ts = data.get('[TIMESERIES]', [])
	ts_dict = {}
	for r in ts:
		name = r[0]
		if name not in ts_dict: ts_dict[name] = []
		if len(r) == 2:
			ts_dict[name].append((None, r[1]))
		elif len(r) == 3:
			ts_dict[name].append((r[1], r[2]))
	return ts_dict

os.chdir(r'E:\PY\LSTM\模型文件有污水量')
# 1. 读入两份模型文件
normal_data = parse_inp_data('盱眙污水管3（入渗点无雨水量）.inp')
rain_data = parse_inp_data('盱眙污水管3（入渗点有雨水量）.inp')

nodes, links = extract_nodes_links(rain_data)
ts_dict = extract_timeseries(rain_data)

# 2. 对比提取：甄别正常节点与雨天节点，并剔除 J197
inflows_normal = [r[0] for r in normal_data.get('[INFLOWS]', [])]
inflows_rain_info = {r[0]: {'curve': r[2], 'sfactor': float(r[5]) if len(r) > 5 else 1.0} for r in
                     rain_data.get('[INFLOWS]', [])}

normal_nodes_set = []
rain_nodes_set = []

for node, info in inflows_rain_info.items():
	# 核心需求：彻底无视 J197 节点
	if node == 'J197':
		continue
	# 分类逻辑：原来就有的是正常基流，原来没有的是后来加的雨水
	if node in inflows_normal:
		normal_nodes_set.append(node)
	else:
		rain_nodes_set.append(node)

# 3. 导出以“节点+类型”命名的详细 Excel 报告
with pd.ExcelWriter('盱眙污水管_节点时序数据_剔除197.xlsx') as writer:
	for node, info in inflows_rain_info.items():
		if node == 'J197': continue
		
		curve_name = info['curve']
		sfactor = info['sfactor']
		
		# 获取该节点挂载的时序数值
		curve_data = ts_dict.get(curve_name, [])
		times = [float(k[0]) for k in curve_data]
		base_flows = [float(k[1]) for k in curve_data]
		
		# 直接计算实际注入的真实流量（底层流量 * 放大倍数Sfactor）
		actual_flows = [f * sfactor for f in base_flows]
		
		# 表格命名
		node_type = "正常基流" if node in normal_nodes_set else "雨天注入"
		sheet_name = f"节点_{node}_{node_type}"
		
		# 判断时间格式（数据量超过100基本确认为分钟级）
		time_unit = "时间 (分钟)" if len(times) > 100 else "时间 (小时)"
		
		df = pd.DataFrame({
			time_unit: times,
			'基础流量数值 (CMS)': base_flows,
			f'实际汇入流量 (乘放大倍数 {sfactor} 后的CMS)': actual_flows
		})
		df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
# 4. 生成高度定制的 3D 可视化 HTML
fig = go.Figure()

# 绘制管道...
unique_diams = sorted(links['Geom1'].dropna().unique())
colors = px.colors.qualitative.Plotly
for i, d in enumerate(unique_diams):
	subset = links[links['Geom1'] == d]
	x_lines, y_lines, z_lines = [], [], []
	for _, row in subset.iterrows():
		n1 = nodes[nodes['Node'] == row['FromNode']]
		n2 = nodes[nodes['Node'] == row['ToNode']]
		if not n1.empty and not n2.empty:
			x_lines.extend([n1.iloc[0]['X'], n2.iloc[0]['X'], None])
			y_lines.extend([n1.iloc[0]['Y'], n2.iloc[0]['Y'], None])
			z_lines.extend([n1.iloc[0]['Elevation'], n2.iloc[0]['Elevation'], None])
	
	fig.add_trace(go.Scatter3d(
		x=x_lines, y=y_lines, z=z_lines,
		mode='lines', name=f'管道 (管径: {d}m)',
		line=dict(color=colors[i % len(colors)], width=2),
		hoverinfo='none'
	))

# 绘制普通的空白背景节点 (半透明灰色)
all_inflow_nodes = normal_nodes_set + rain_nodes_set + ['J197']
regular_nodes = nodes[~nodes['Node'].isin(all_inflow_nodes)]
fig.add_trace(go.Scatter3d(
	x=regular_nodes['X'], y=regular_nodes['Y'], z=regular_nodes['Elevation'],
	mode='markers', name='普通检查井',
	marker=dict(size=3, color='rgba(150, 150, 150, 0.4)'),
	text=regular_nodes['Node'],
	hoverinfo='text+z'
))

# 绘制：正常污水基流节点 (绿色大圆)
if normal_nodes_set:
	nn = nodes[nodes['Node'].isin(normal_nodes_set)]
	fig.add_trace(go.Scatter3d(
		x=nn['X'], y=nn['Y'], z=nn['Elevation'],
		mode='markers+text', name='正常污水基流注入点',
		marker=dict(size=10, color='green', symbol='circle', line=dict(color='white', width=1)),
		text=nn['Node'] + "(正常排污)", textposition="top center",
		hoverinfo='text+z'
	))

# 绘制：雨天异常注水节点 (红色大菱形)
if rain_nodes_set:
	rn = nodes[nodes['Node'].isin(rain_nodes_set)]
	fig.add_trace(go.Scatter3d(
		x=rn['X'], y=rn['Y'], z=rn['Elevation'],
		mode='markers+text', name='雨天降雨入渗/混接注入点',
		marker=dict(size=10, color='red', symbol='diamond', line=dict(color='yellow', width=2)),
		text=rn['Node'] + "(雨水注入)", textposition="top center",
		hoverinfo='text+z'
	))

fig.update_layout(
	title='盱眙污水管网 3D数字底图 (清晰区分旱天基流与雨天入渗 | 已剔除J197)',
	scene=dict(aspectmode='data', xaxis_title='X 坐标', yaxis_title='Y 坐标', zaxis_title='Z 标高 (m)'),
	margin=dict(l=0, r=0, b=0, t=40)
)

fig.write_html('盱眙污水管_3D可视化_分类标注.html')