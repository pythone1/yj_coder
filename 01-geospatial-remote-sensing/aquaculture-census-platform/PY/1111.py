"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: 1111.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import geopandas as gpd
import pandas as pd

# 文件路径
gpkg_path = r"E:\全省养殖池溏上图入库普查\项目验收\20260310\无锡市池塘信息.gpkg"
excel_path = r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2026-03\太湖一级保护区内池塘信息表.xlsx"
output_excel = r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2026-03\太湖一级保护区内池塘信息表（附坐标）.xlsx"

# 读取gpkg
gdf = gpd.read_file(gpkg_path)

# TBID 去掉逗号
gdf["TBID_clean"] = gdf["TBID"].astype(str).str.replace(",", "")

# 计算图斑中心
gdf["center"] = gdf.geometry.centroid

# 转换为4326
center_gdf = gpd.GeoDataFrame(gdf, geometry="center", crs=gdf.crs)
center_gdf = center_gdf.to_crs(4326)

# 提取经纬度
center_gdf["lon"] = center_gdf.geometry.x
center_gdf["lat"] = center_gdf.geometry.y

# 只保留需要字段
center_df = center_gdf[["TBID_clean", "lon", "lat"]]

# 读取excel
df = pd.read_excel(excel_path)

# Excel TBID也转字符串
df["TBID_clean"] = df["图斑编号"].astype(str).str.replace(",", "")

# 合并
result = df.merge(center_df, on="TBID_clean", how="left")

# 删除临时字段
result = result.drop(columns=["TBID_clean"])

# 输出
result.to_excel(output_excel, index=False)

print("完成，输出文件：", output_excel)