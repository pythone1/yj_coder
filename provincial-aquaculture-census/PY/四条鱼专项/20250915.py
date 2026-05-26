import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import ast
import math


def sort_points_clockwise(coords):
	"""将坐标点按顺时针方向排序"""
	# 计算几何中心点
	cx = sum(x for x, y in coords) / len(coords)
	cy = sum(y for x, y in coords) / len(coords)
	
	# 计算每个点相对于中心点的角度
	def angle_from_center(point):
		x, y = point
		return math.atan2(y - cy, x - cx)
	
	# 按角度从小到大排序（逆时针），然后反转得到顺时针
	sorted_coords = sorted(coords, key=angle_from_center)
	# 确保多边形闭合（首尾点相同）
	if sorted_coords[0] != sorted_coords[-1]:
		sorted_coords.append(sorted_coords[0])
	return sorted_coords


def parse_coords(coord_str):
	"""解析坐标字符串并生成不自相交的多边形"""
	try:
		coords = ast.literal_eval(coord_str)
		# 如果点数少于3个，无法形成多边形
		if len(coords) < 3:
			print(f"坐标点数量不足: {coord_str}")
			return None
		# 对点进行排序
		sorted_coords = sort_points_clockwise(coords)
		# 创建多边形
		polygon = Polygon(sorted_coords)
		# 检查多边形是否有效（不自相交）
		if not polygon.is_valid:
			print(f"生成的多边形自相交，尝试使用凸包: {coord_str}")
			# 如果无效则使用凸包（最外层点形成的多边形）
			polygon = polygon.buffer(0)
		return polygon
	except Exception as e:
		print(f"坐标解析失败: {coord_str}，错误: {e}")
		return None


# 读取Excel文件
excel_path = r"E:\渔业\工作簿5.xlsx"
df = pd.read_excel(excel_path, dtype=str)
# 解析坐标并创建geometry列
coords_column = "经纬度"
df["geometry"] = df[coords_column].apply(parse_coords)
# 过滤掉无效的多边形
gdf = gpd.GeoDataFrame(df.dropna(subset=['geometry']), geometry="geometry", crs="EPSG:4326")
# 保存为GeoPackage
gpkg_path = r"E:\渔业\江苏省国家级水产种质资源保护区名单2.gpkg"
gdf.to_file(gpkg_path, layer="区划", driver="GPKG")
print("GPKG 文件生成完成！")