"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: 20240711.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""


import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd

# 定义文件路径
file_ponds = r'F:\20240603\0724\射阳\疑点分析结果2-1.json'
file_protection_zone = r'F:\20240603\0711\射阳\自然保护区\roi3.shp'

# 读取池塘和保护区文件，并确保坐标系为 EPSG:32650
ponds = gpd.read_file(file_ponds).to_crs(epsg=32650)
protection_zone = gpd.read_file(file_protection_zone).to_crs(epsg=32650)

# 计算总池塘数量和面积
total_ponds = len(ponds)
total_area = ponds['geometry'].area.sum() * 0.0015  # 转换为亩

# 计算已填报养殖和光伏的数量和面积
reported_ponds = ponds[ponds['status'].isin(['已填报养殖', '已上报光伏']) | (ponds['养殖经营人名称'] == '光伏')]
reported_ponds_count = len(reported_ponds)
reported_area = reported_ponds['geometry'].area.sum() * 0.0015

# 计算差额
difference_count = total_ponds - reported_ponds_count
difference_area = total_area - reported_area

# 计算退养、不养殖的数量和面积
non_farming_ponds = ponds[(ponds['status'].isin(['已填报非养殖', '已上报非养殖'])) & (ponds['养殖经营人名称'] != '光伏')]

# 将保护区内未填报的池塘加入非养殖统计
if 'index_right' in ponds.columns:
    ponds = ponds.drop(columns=['index_right'])
protection_unreported = gpd.sjoin(ponds, protection_zone, how='inner')
protection_unreported = protection_unreported[protection_unreported['status'] == '未填报']
non_farming_ponds = pd.concat([non_farming_ponds, protection_unreported])

# 检查重复并打印
duplicates = non_farming_ponds[non_farming_ponds.duplicated()]
if not duplicates.empty:
    print("重复的池塘记录:")
    print(duplicates)

# 去掉重复的记录
non_farming_ponds = non_farming_ponds.drop_duplicates()

non_farming_count = len(non_farming_ponds)
non_farming_area = non_farming_ponds['geometry'].area.sum() * 0.0015

# 计算剩余未填报的数量和面积
remaining_count = difference_count - non_farming_count
remaining_area = difference_area - non_farming_area

# 输出结果
result = f"""
截止2024年7月24日10时10分：
射阳境内共计池塘{total_ponds}个，面积约{total_area:.2f}亩；(总：去行政区划外、保护区145、滩涂）
已填报养殖(含光伏){reported_ponds_count}个，面积约{reported_area:.2f}亩；（正常填报图斑、光伏）
差额{difference_count}个，面积约{difference_area:.2f}亩；（总-已填报养殖）
差额中退养、不养殖有{non_farming_count}个，面积约{non_farming_area:.2f}亩；（数据库导出统计的非养殖(不含光伏)；指定非养殖片区（保护区3、靶场的未填报）；按编号指定的非养殖）
剩余未填报{remaining_count}个，面积约{remaining_area:.2f}亩（总-已填报养殖-非养殖)
"""

print(result)