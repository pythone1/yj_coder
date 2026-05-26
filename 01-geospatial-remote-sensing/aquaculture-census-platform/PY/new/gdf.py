"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: gdf.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import geopandas as gpd
import pandas as pd
import os

# 文件路径
excel_path = r'E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\所有品种产量统计结果（市）.xlsx'
shp_path = r'F:\xiangmu\江苏省天地图分割\实习生每日进度收集\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
output_dir = r'E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\产量描述'
os.makedirs(output_dir, exist_ok=True)

# 读取行政区划文件
gdf_city = gpd.read_file(shp_path)
gdf_city.columns = gdf_city.columns.str.strip()
if "市" not in gdf_city.columns:
    raise ValueError("行政区划图层中必须包含“市”字段")

# 读取Excel数据
df = pd.read_excel(excel_path, engine='openpyxl')
df.columns = df.columns.str.strip()

# 遍历每个品种
for variety in df['品种'].unique():
    subset = df[df['品种'] == variety][['市', '产量（吨）', '产量描述']].copy()
    subset.columns = ['市', f'{variety}产量（吨）', f'{variety}描述']

    # 合并到行政区划
    gdf_merged = gdf_city.merge(subset, on='市', how='left')

    # 仅保留所需字段
    out_gdf = gdf_merged[['geometry', '市', f'{variety}产量（吨）', f'{variety}描述']]

    # 写出每个品种图层
    output_path = os.path.join(output_dir, f"{variety}产量分布图.gpkg")
    out_gdf.to_file(output_path, driver='GPKG', encoding='utf-8')

print("✅ 每个品种的产量+描述图层已生成。")
