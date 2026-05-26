import sqlite3
import struct
import json
from pathlib import Path


def check_geopackage(file_path):
	"""检查GeoPackage文件的结构和内容"""
	if not Path(file_path).exists():
		print(f"错误：文件 {file_path} 不存在")
		return
	print(f"正在检查GeoPackage文件: {file_path}")
	print("=" * 60)
	try:
		# 连接到GeoPackage数据库
		conn = sqlite3.connect(file_path)
		cursor = conn.cursor()
		# 1. 检查GeoPackage元数据表
		print("1. 检查GeoPackage元数据表:")
		cursor.execute("SELECT table_name, column_name, geometry_type_name, srs_id FROM gpkg_geometry_columns")
		geometry_columns = cursor.fetchall()
		if not geometry_columns:
			print("   - 没有找到几何列信息")
		else:
			for table, column, geom_type, srs_id in geometry_columns:
				print(f"   - 表: {table}, 列: {column}, 几何类型: {geom_type}, SRID: {srs_id}")
		print("\n2. 检查所有表:")
		cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
		tables = cursor.fetchall()
		for table in tables:
			table_name = table[0]
			print(f"   - 表: {table_name}")
			# 获取表结构
			cursor.execute(f"PRAGMA table_info({table_name})")
			columns = cursor.fetchall()
			print("     列信息:")
			for col in columns:
				col_id, col_name, col_type, not_null, default_val, is_pk = col
				print(f"       {col_name} ({col_type})")
			# 检查是否是几何表
			is_geom_table = any(
				col[1].lower().find('geom') != -1 or col[1].lower().find('geometry') != -1 for col in columns)
			if is_geom_table:
				print("     几何数据样本:")
				cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
				rows = cursor.fetchall()
				for i, row in enumerate(rows):
					print(f"       行 {i + 1}:")
					for j, value in enumerate(row):
						col_name = columns[j][1]
						if col_name.lower().find('geom') != -1 or col_name.lower().find('geometry') != -1:
							# 几何数据通常是二进制格式，尝试解析
							if isinstance(value, bytes):
								print(f"         {col_name}: 二进制数据 (长度: {len(value)} 字节)")
								# 尝试解析WKB头部
								if len(value) >= 5:
									endianness = ">" if value[0] == 0 else "<"
									geom_type = struct.unpack(endianness + "I", value[1:5])[0]
									geom_type_names = {
										1: "Point",
										2: "LineString",
										3: "Polygon",
										4: "MultiPoint",
										5: "MultiLineString",
										6: "MultiPolygon",
										7: "GeometryCollection"
									}
									geom_type_name = geom_type_names.get(geom_type, f"未知类型({geom_type})")
									print(f"         几何类型: {geom_type_name}")
							else:
								print(f"         {col_name}: {value} (类型: {type(value)})")
						else:
							print(f"         {col_name}: {value}")
			else:
				# 非几何表，只显示前几行
				cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
				rows = cursor.fetchall()
				if rows:
					print("     数据样本:")
					for i, row in enumerate(rows):
						print(f"       行 {i + 1}: {row}")
			print()
		# 3. 检查坐标系信息
		print("3. 检查坐标系信息:")
		cursor.execute("SELECT srs_id, organization, organization_coordsys_id, description FROM gpkg_spatial_ref_sys")
		srs_info = cursor.fetchall()
		if not srs_info:
			print("   - 没有找到坐标系信息")
		else:
			for srs_id, org, org_id, desc in srs_info:
				print(f"   - SRID: {srs_id}, 组织: {org}, ID: {org_id}, 描述: {desc}")
		# 4. 检查属性数据
		print("\n4. 检查属性数据:")
		for table, column, _, _ in geometry_columns:
			print(f"   - 表: {table}")
			# 检查是否有"是否退养"字段
			cursor.execute(f"PRAGMA table_info({table})")
			columns_info = cursor.fetchall()
			column_names = [col[1] for col in columns_info]
			if "是否退养" in column_names:
				print("     找到'是否退养'字段")
				cursor.execute(f"SELECT DISTINCT \"是否退养\" FROM {table}")
				unique_values = cursor.fetchall()
				print(f"     '是否退养'的唯一值: {[val[0] for val in unique_values]}")
				# 统计数量
				cursor.execute(f"SELECT \"是否退养\", COUNT(*) FROM {table} GROUP BY \"是否退养\"")
				counts = cursor.fetchall()
				print("     '是否退养'统计:")
				for val, count in counts:
					print(f"       {val}: {count}")
			else:
				print("     未找到'是否退养'字段")
				print(f"     可用字段: {column_names}")
		conn.close()
	except Exception as e:
		print(f"检查文件时出错: {str(e)}")


if __name__ == "__main__":

	file_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\4326.gpkg'
	check_geopackage(file_path)