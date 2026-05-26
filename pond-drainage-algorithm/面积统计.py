import geopandas as gpd
#
# # === 输入文件路径 ===
gpkg_path = r"F:\20251027宜兴市养殖水域滩涂规划修编\过程数据\三区及统计结果\1112修改.gpkg"  # 你的文件路径
gdf = gpd.read_file(gpkg_path)
gdf = gdf.to_crs(32650)
gdf["规划面积"] = gdf.geometry.area / 10000.0

# 计算经纬度（转回 WGS84）
gdf_out = gdf.to_crs(epsg=4326)
centroids = gdf_out.geometry.centroid
gdf_out["经度"] = centroids.x
gdf_out["纬度"] = centroids.y
gdf_out.to_file(r'F:\20251027宜兴市养殖水域滩涂规划修编\过程数据\三区及统计结果\1112修改计算面积中心点.gpkg')

#
# # === 读取 GPKG 文件 ===
# gdf = gpd.read_file(gpkg_path)
#
# # === 投影到 EPSG:32650 ===
# gdf = gdf.to_crs(epsg=32650)
#
# # === 计算面积（平方米转公顷）===
# gdf["面积"] = gdf.area *0.0015
#
# # === 统计信息 ===
# total_area = gdf["面积"].sum()
# polygon_count = len(gdf)
#
# print(f"图斑数量: {polygon_count}")
# print(f"总面积: {total_area} 亩")
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

# # 创建点几何
# point = Point(119.778297484309, 31.4820389131717)
#
# # 创建GeoDataFrame
# gdf = gpd.GeoDataFrame(
#     {'id': [1], 'name': ['目标点']},
#     geometry=[point],
#     crs='EPSG:4326'
# )
#
# # 保存为GPKG文件
# output_path = r"F:\20251027宜兴市养殖水域滩涂规划修编\数据\三区划定\point_wgs84.gpkg"
# gdf.to_file(output_path, driver="GPKG", encoding="utf-8")
#
# print(f"✅ GPKG文件已创建：{output_path}")
# print(f"坐标：经度={119.778297484309}, 纬度={31.4820389131717}")
