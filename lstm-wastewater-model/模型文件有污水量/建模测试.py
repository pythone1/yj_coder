import re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def parse_swmm_inp(filepath):
	"""提取 INP 文件中的坐标、标高、管道拓扑、管径以及入流节点等信息"""
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
	
	# 提取节点标高与坐标
	df_junc = pd.DataFrame(data.get('[JUNCTIONS]', []),
	                       columns=['Node', 'Elevation', 'MaxDepth', 'InitDepth', 'SurDepth', 'Aponded'])
	df_junc['Elevation'] = pd.to_numeric(df_junc['Elevation'], errors='coerce')
	
	df_coord = pd.DataFrame(data.get('[COORDINATES]', []), columns=['Node', 'X', 'Y'])
	df_coord['X'] = pd.to_numeric(df_coord['X'], errors='coerce')
	df_coord['Y'] = pd.to_numeric(df_coord['Y'], errors='coerce')
	nodes = pd.merge(df_junc, df_coord, on='Node', how='inner')
	
	# 提取管道信息与管径
	cols_cond = ['Link', 'FromNode', 'ToNode', 'Length', 'Roughness', 'InOffset', 'OutOffset', 'InitFlow', 'MaxFlow']
	cond_data = [row[:9] + [0] * (9 - len(row)) for row in data.get('[CONDUITS]', [])]
	df_cond = pd.DataFrame(cond_data, columns=cols_cond)
	
	cols_xsec = ['Link', 'Shape', 'Geom1', 'Geom2', 'Geom3', 'Geom4', 'Barrels', 'Culvert']
	xsec_data = [row[:8] + [0] * (8 - len(row)) for row in data.get('[XSECTIONS]', [])]
	df_xsec = pd.DataFrame(xsec_data, columns=cols_xsec)
	df_xsec['Geom1'] = pd.to_numeric(df_xsec['Geom1'], errors='coerce')
	links = pd.merge(df_cond, df_xsec, on='Link', how='inner')
	
	# 提取具有时序数据（[INFLOWS]定义）的节点
	inflow_data = data.get('[INFLOWS]', [])
	inflow_nodes = list(set([row[0] for row in inflow_data if len(row) > 0]))
	
	return nodes, links, inflow_nodes


# 1. 解析模型文件
nodes, links, inflow_nodes = parse_swmm_inp(r'E:\PY\LSTM\模型文件有污水量\盱眙污水管3（入渗点有雨水量）.inp')

# 2. 构建图表
fig = go.Figure()

# --- 绘制管道 ---
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
		line=dict(color=colors[i % len(colors)], width=3),
		hoverinfo='none'
	))

# --- 绘制普通节点 (灰色小圆点) ---
normal_nodes = nodes[~nodes['Node'].isin(inflow_nodes)]
fig.add_trace(go.Scatter3d(
	x=normal_nodes['X'], y=normal_nodes['Y'], z=normal_nodes['Elevation'],
	mode='markers', name='普通检查井',
	marker=dict(size=3, color='rgba(150, 150, 150, 0.6)'),
	text=normal_nodes['Node'],
	hoverinfo='text+z'
))

# --- 绘制时序数据入流节点 (红色高亮菱形) ---
hl_nodes = nodes[nodes['Node'].isin(inflow_nodes)]
fig.add_trace(go.Scatter3d(
	x=hl_nodes['X'], y=hl_nodes['Y'], z=hl_nodes['Elevation'],
	mode='markers+text', name='时序入流节点 (高亮)',
	marker=dict(size=8, color='red', symbol='diamond', line=dict(color='yellow', width=1)),
	text=hl_nodes['Node'], textposition="top center",
	hoverinfo='text+z'
))

# 3. 布局与导出
fig.update_layout(
	title='盱眙污水管 3D拓扑可视化 (红色为含时序水量输入的节点)',
	scene=dict(aspectmode='data', xaxis_title='X', yaxis_title='Y', zaxis_title='Z 标高 (m)'),
	margin=dict(l=0, r=0, b=0, t=40)
)

fig.write_html('盱眙污水管_3D可视化_带高亮.html')