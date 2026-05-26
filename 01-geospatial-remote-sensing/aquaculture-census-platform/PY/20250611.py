"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: 20250611.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import geopandas as gpd
import os
import pandas as pd
# === 参数设置 ===
input_gpkg = r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-06\池塘信息表--池塘图斑.gpkg"  # 替换为你的 GPKG 路径
output_dir = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250611\武进区\池塘按照镇拆分\去除未使用虾蟹"  # 输出文件夹
os.makedirs(output_dir, exist_ok=True)

# === 读取数据 ===
gdf = gpd.read_file(input_gpkg)

# === 筛选条件 ===
filtered = gdf[
    (gdf['填报状态'] == '已填报养殖') &
    (~gdf['养殖品种/预计亩产量'].str.contains('虾|蟹', na=False)) &
    (gdf['地址'].str.contains('武进区', na=False))
]

# === 提取镇名 ===
filtered['镇'] = filtered['地址'].str.split('-').str[3]

# === 按镇名分组写出文件 ===
for town, group in filtered.groupby('镇'):
    if pd.isna(town) or town.strip() == "":
        continue  # 跳过空值
    outfile = os.path.join(output_dir, f"{town}.gpkg")
    group.to_file(outfile, driver="GPKG")
