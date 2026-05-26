import pandas as pd
import plotly.graph_objects as go
import numpy as np


# 1. 基础提取函数
def get_swmm_section(file_path, section_name):
	data = []
	in_section = False
	try:
		with open(file_path, 'r', encoding='utf-8') as f:
			lines = f.readlines()
	except UnicodeDecodeError:
		with open(file_path, 'r', encoding='gbk') as f:
			lines = f.readlines()
	
	for line in lines:
		line = line.strip()
		if line.startswith('['):
			if line.upper() == section_name.upper():
				in_section = True
				continue
			else:
				in_section = False
		if in_section and line and not line.startswith(';'):
			data.append(line.split())
	return data


file_path = r'E:\PY\LSTM\模型文件inp\盱眙污水管.inp'

# 2. 提取节点坐标与高程 (和之前一样)
coords = get_swmm_section(file_path, '[COORDINATES]')
df_coords = pd.DataFrame(coords, columns=['Node', 'X', 'Y']).set_index('Node')
df_coords['X'], df_coords['Y'] = pd.to_numeric(df_coords['X']), pd.to_numeric(df_coords['Y'])

juncs = get_swmm_section(file_path, '[JUNCTIONS]')
df_juncs = pd.DataFrame([j[:3] for j in juncs if len(j) >= 3], columns=['Node', 'Elevation', 'MaxDepth']).set_index(
	'Node')

storage = get_swmm_section(file_path, '[STORAGE]')
df_storage = pd.DataFrame([s[:3] for s in storage if len(s) >= 3], columns=['Node', 'Elevation', 'MaxDepth']).set_index(
	'Node')

df_nodes_info = pd.concat([df_juncs, df_storage])
df_nodes_info['Elevation'] = pd.to_numeric(df_nodes_info['Elevation'])
df_nodes_info['MaxDepth'] = pd.to_numeric(df_nodes_info['MaxDepth'])
df_nodes = df_coords.join(df_nodes_info, how='inner')

# 3. ⭐️ 核心新增：提取管道属性与管径 ⭐️
# 3.1 提取管道基础信息与粗糙度(材质)
conds = get_swmm_section(file_path, '[CONDUITS]')
df_conds = pd.DataFrame([c[:5] for c in conds if len(c) >= 5], columns=['Link', 'From', 'To', 'Length', 'Roughness'])
df_conds['Length'] = pd.to_numeric(df_conds['Length'])

# 3.2 提取截面尺寸 (Geom1 对于圆形管就是管径 Diameter)
xsecs = get_swmm_section(file_path, '[XSECTIONS]')
df_xsecs = pd.DataFrame([x[:3] for x in xsecs if len(x) >= 3], columns=['Link', 'Shape', 'Diameter'])
df_xsecs['Diameter'] = pd.to_numeric(df_xsecs['Diameter'])

# 3.3 数据库合并：把管径拼接到管道表上 (相当于 SQL 的 Left Join)
df_conds = pd.merge(df_conds, df_xsecs, on='Link', how='left')

# 4. 绘制 3D 图像
fig = go.Figure()

# ⭐️ 核心新增：按管径分组画图，管径越大线越粗，颜色越深 ⭐️
# 获取所有不重复的管径，并排序 (你模型里有 0.355, 0.4, 0.45, 0.5, 0.56, 0.6)
unique_diams = sorted(df_conds['Diameter'].dropna().unique())

# 给不同管径分配不同的颜色 (使用系统自带的彩虹色谱)
import plotly.express as px

colors = px.colors.sequential.Plasma

for i, diam in enumerate(unique_diams):
	# 筛选出当前管径的所有管道
	df_group = df_conds[df_conds['Diameter'] == diam]
	
	x_lines, y_lines, z_lines = [], [], []
	link_mid_x, link_mid_y, link_mid_z, link_texts = [], [], [], []
	
	for idx, row in df_group.iterrows():
		node1, node2 = row['From'], row['To']
		if node1 in df_nodes.index and node2 in df_nodes.index:
			x1, y1, z1 = df_nodes.loc[node1, ['X', 'Y', 'Elevation']]
			x2, y2, z2 = df_nodes.loc[node2, ['X', 'Y', 'Elevation']]
			
			x_lines.extend([x1, x2, None])
			y_lines.extend([y1, y2, None])
			z_lines.extend([z1, z2, None])
			
			link_mid_x.append((x1 + x2) / 2)
			link_mid_y.append((y1 + y2) / 2)
			link_mid_z.append((z1 + z2) / 2)
			
			# 丰富悬浮信息：加入管径和材质(粗糙度)
			hover_text = (f"<b>管道编号:</b> {row['Link']}<br>"
			              f"<b>流向:</b> {node1} ➔ {node2}<br>"
			              f"<b>长度:</b> {row['Length']} m<br>"
			              f"<b>管径:</b> DN{int(row['Diameter'] * 1000)}<br>"
			              f"<b>粗糙度(材质):</b> {row['Roughness']}")
			link_texts.append(hover_text)
	
	# 计算线条粗细：管径越大，线越粗 (做了一个简单的乘法放大系数)
	line_width = 1 + (diam - min(unique_diams)) * 15
	
	# 逐层添加不同管径的管线
	fig.add_trace(go.Scatter3d(
		x=x_lines, y=y_lines, z=z_lines,
		mode='lines',
		line=dict(color=colors[i % len(colors)], width=line_width),
		name=f'DN{int(diam * 1000)} 管道',  # 右侧图例会显示不同管径
		hoverinfo='none'
	))
	
	# 添加这批管道的隐藏信息点
	fig.add_trace(go.Scatter3d(
		x=link_mid_x, y=link_mid_y, z=link_mid_z,
		mode='markers',
		marker=dict(size=1, color='rgba(0,0,0,0)'),
		text=link_texts,
		hoverinfo='text',
		showlegend=False
	))

# 5. 节点绘制与布局设置 (保持上节课的最佳参数)
node_texts = [f"<b>检查井:</b> {n}<br><b>高程:</b> {r['Elevation']}m" for n, r in df_nodes.iterrows()]
fig.add_trace(go.Scatter3d(
	x=df_nodes['X'], y=df_nodes['Y'], z=df_nodes['Elevation'],
	mode='markers',
	marker=dict(size=2, color=df_nodes['Elevation'], colorscale='Viridis', opacity=1.0),
	text=node_texts, hoverinfo='text', name='检查井', showlegend=False
))

x_range = df_nodes['X'].max() - df_nodes['X'].min()
y_range = df_nodes['Y'].max() - df_nodes['Y'].min()

fig.update_layout(
	title='盱眙污水管网 3D 可视化 (管径与材质映射版)',
	scene=dict(
		xaxis_title='经度 X', yaxis_title='纬度 Y', zaxis_title='高程 Z (m)',
		aspectmode='manual',
		aspectratio=dict(x=1, y=y_range / x_range, z=0.15)
	),
	margin=dict(l=0, r=0, b=0, t=40),
	dragmode='turntable',
	legend=dict(title="管径分类 (点击可显隐)")  # 优化了右侧图例
)

html_filename = '盱眙管网三维_管径映射版.html'
fig.write_html(html_filename)
print(f"✅ 生成成功！请打开【{html_filename}】")