import pandas as pd
import glob
import os

# 1. 定义需要计算的指标列表
indicators = [
	'水温(℃)', 'pH(无量纲)', '溶解氧(mg/L)', '电导率(μS/cm)',
	'浊度(NTU)', '高锰酸盐指数(mg/L)', '氨氮(mg/L)', '总磷(mg/L)', '总氮(mg/L)'
]

# 2. 获取路径下所有以“养殖.xls”结尾的文件
# 如果是较新版的xlsx文件，请将后缀改为 .xlsx
files = glob.glob(r'E:\哨兵影像\20251229\*养殖*.xls')

all_monthly_stats = []

for file in files:
	try:
		# 读取Excel文件
		# 注意：如果安装了新版pandas，读取xls可能需要安装 xlrd 库
		df = pd.read_excel(file)
		
		# 转换“监测时间”为日期格式，无效格式转为NaT
		df['监测时间'] = pd.to_datetime(df['监测时间'], errors='coerce')
		
		# 3. 筛选时间范围：2024年11月1日 到 2025年3月31日
		mask = (df['监测时间'] >= '2024-11-01') & (df['监测时间'] <= '2025-03-31')
		df_filtered = df.loc[mask].copy()
		
		if df_filtered.empty:
			print(f"文件 {file} 在指定时间范围内无数据。")
			continue
		
		# 4. 数据清洗：将指标列转换为数值型，将 '-' 或其他无效字符处理为 NaN
		for col in indicators:
			if col in df_filtered.columns:
				df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')
		
		# 5. 提取年份-月份
		df_filtered['月份'] = df_filtered['监测时间'].dt.strftime('%Y-%m')
		
		# 6. 按月份计算均值
		# 站点名称使用文件名（去除后缀）
		station_name = os.path.basename(file).replace('.xls', '')
		
		# 计算该文件的月度均值
		monthly_avg = df_filtered.groupby('月份')[indicators].mean().reset_index()
		monthly_avg.insert(0, '站点名称', station_name)
		
		all_monthly_stats.append(monthly_avg)
	
	except Exception as e:
		print(f"处理文件 {file} 时出错: {e}")

# 7. 合并所有结果并导出
if all_monthly_stats:
	final_report = pd.concat(all_monthly_stats, ignore_index=True)
	
	# 按照站点和月份排序
	final_report = final_report.sort_values(by=['站点名称', '月份'])
	
	# 打印前几行预览
	print("各站点月度均值统计表：")
	print(final_report)
	
	# 保存为CSV或Excel
	final_report.to_csv('养殖站点水质月均值统计表.csv', index=False, encoding='utf-8-sig')
	print("\n统计表已保存为：养殖站点水质月均值统计表.csv")
else:
	print("未找到匹配的文件或数据，请检查文件路径及时间格式。")