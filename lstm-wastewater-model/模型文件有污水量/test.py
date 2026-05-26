import os

import pandas as pd
import sqlite3
import re


def parse_swmm_nodes_with_description(inp_filepath):
	"""
	解析 INP 文件，提取所有节点信息，特别包含 Description（描述/备注）字段
	"""
	with open(inp_filepath, 'r', encoding='utf-8', errors='ignore') as f:
		lines = f.readlines()
	
	nodes_data = []
	current_section = None
	last_comment = ""
	
	for line in lines:
		line = line.strip()
		
		# 1. 处理空行
		if not line:
			last_comment = ""
			continue
		
		# 2. 识别模块
		if line.startswith('['):
			current_section = line
			last_comment = ""
			continue
		
		# 3. 捕获注释（Description 通常在节点正上方，以单个 ; 开头）
		if line.startswith(';'):
			# 排除掉系统的表头注释（通常以 ;; 开头，如 ";;Node Elevation..."）
			if not line.startswith(';;'):
				# 累加多行注释作为完整描述
				clean_comment = line.lstrip(';').strip()
				last_comment = f"{last_comment} {clean_comment}".strip()
			continue
		
		# 4. 提取 [JUNCTIONS] 数据及绑定的 Description
		if current_section == '[JUNCTIONS]':
			parts = re.split(r'\s+', line)
			if len(parts) >= 2:
				nodes_data.append({
					'Node (节点名称)': parts[0],
					'Description (描述/备注/监测点标注)': last_comment,  # 成功抓取描述字段！
					'Elevation (底标高 m)': float(parts[1]) if len(parts) > 1 else None,
					'MaxDepth (最大深度 m)': float(parts[2]) if len(parts) > 2 else 0,
					'InitDepth (初始深度 m)': float(parts[3]) if len(parts) > 3 else 0,
					'SurDepth (溢流深度 m)': float(parts[4]) if len(parts) > 4 else 0,
					'Aponded (积水面积 m2)': float(parts[5]) if len(parts) > 5 else 0
				})
			# 节点解析完毕后，清空注释缓存，避免错误赋值给下一个节点
			last_comment = ""
	
	return pd.DataFrame(nodes_data)


def extract_all_node_data():
	os.chdir(r'E:\PY\LSTM\模型文件有污水量')
	# 您可以根据需要修改为有雨水或无雨水的文件名
	inp_file = '盱眙污水管3（入渗点有雨水量）.inp'
	db_file = '盱眙污水管3（入渗点有雨水量）.db'
	output_excel = '盱眙污水管_全节点完整字段大表.xlsx'
	
	print("⏳ 正在解析 INP 文件，提取物理参数与 Description...")
	df_inp = parse_swmm_nodes_with_description(inp_file)
	
	print("⏳ 正在连接 DB 数据库，提取全部 21 项时序统计结果...")
	try:
		# 连接 PCSWMM 生成的 SQLite 数据库文件
		conn = sqlite3.connect(db_file)
		# 读取 Junctions_Results 结果表
		df_db = pd.read_sql_query("SELECT * FROM Junctions_Results", conn)
		conn.close()
		
		# 将数据库里的 'Name' 列重命名，方便与 INP 数据合并
		df_db = df_db.rename(columns={'Name': 'Node (节点名称)'})
		
		# 以节点名称为基准，合并两张大表
		df_final = pd.merge(df_inp, df_db, on='Node (节点名称)', how='left')
		print("✅ 数据库结果合并成功！")
	
	except Exception as e:
		print(f"⚠️ 读取数据库失败 (可能未运行出结果或文件被占用)，将仅导出 INP 物理属性表。\n错误信息: {e}")
		df_final = df_inp
	
	# 导出为完整的 Excel 表格
	df_final.to_excel(output_excel, index=False)
	print(f"🎉 提取大功告成！\n包含所有节点、所有字段的完整表格已保存至: 【{output_excel}】")


if __name__ == "__main__":
	extract_all_node_data()