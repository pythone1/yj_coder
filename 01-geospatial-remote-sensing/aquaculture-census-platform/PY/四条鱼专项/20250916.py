"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: 20250916.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import math


def sort_points_clockwise(coords):
    """将坐标点按顺时针方向排序"""
    cx = sum(x for x, y in coords) / len(coords)
    cy = sum(y for x, y in coords) / len(coords)

    def angle_from_center(point):
        x, y = point
        return math.atan2(y - cy, x - cx)

    sorted_coords = sorted(coords, key=angle_from_center)
    if sorted_coords[0] != sorted_coords[-1]:
        sorted_coords.append(sorted_coords[0])
    return sorted_coords


def build_polygon(points):
    """将经纬度点构造成合法多边形"""
    if len(points) < 3:
        return None
    sorted_coords = sort_points_clockwise(points)
    polygon = Polygon(sorted_coords)
    if not polygon.is_valid:
        polygon = polygon.convex_hull
    return polygon


# 读取 Excel
excel_path = r"E:\渔业\江苏省国家级水产种质资源保护区名单.xlsx"
sheet1 = pd.read_excel(excel_path, sheet_name="Sheet1", dtype=str)
sheet2 = pd.read_excel(excel_path, sheet_name="Sheet2", dtype=str)

# 转换经纬度为 float
sheet2["经度"] = sheet2["经度"].astype(float)
sheet2["纬度"] = sheet2["纬度"].astype(float)

# 存储结果
records = []

# 按保护区名称、类型分组
for (zone, t), group in sheet2.groupby(["保护区名称", "类型"]):
    points = list(zip(group["经度"], group["纬度"]))
    polygon = build_polygon(points)
    if polygon is not None:
        record = {
            "保护区名称": zone,
            "类型": t,
            "geometry": polygon
        }
        records.append(record)

# 转换为 GeoDataFrame
gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")

# 合并 Sheet1 信息
gdf = gdf.merge(sheet1, on="保护区名称", how="left")

# 保存为 GeoPackage
gpkg_path = r"E:\渔业\江苏省国家级水产种质资源保护区名单2.gpkg"
gdf.to_file(gpkg_path, layer="区划", driver="GPKG")

print("GPKG 文件生成完成！")
