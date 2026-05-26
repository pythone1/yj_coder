import geopandas as gpd
import glob
import os

# # 输入和输出文件夹
# input_folder = r"E:\渔业\面积计算"
# output_folder = r"E:\渔业\面积计算\面积"
# # 确保输出文件夹存在
# os.makedirs(output_folder, exist_ok=True)
# # 遍历所有 gpkg 文件
# for file in glob.glob(os.path.join(input_folder, "*.gpkg")):
# 	print(f"处理文件: {file}")
# 	# 读取
# 	gdf = gpd.read_file(file)
# 	# 如果坐标是经纬度（EPSG:4326），需要投影到合适的投影坐标系再算面积
# 	if gdf.crs.is_geographic:
# 		# 这里以 UTM 自动投影为例，你也可以改成合适的投影 EPSG
# 		gdf = gdf.to_crs(32650)
# 	# 计算面积（平方米）
# 	gdf["面积"] = gdf.geometry.area/10000
# 	# 输出路径
# 	filename = os.path.basename(file)
# 	out_file = os.path.join(output_folder, filename)
# 	# 写出
# 	gdf.to_file(out_file, driver="GPKG")
# 	print(f"已写出: {out_file}")

import geopandas as gpd
import pandas as pd
import os

# 输入输出路径
in_file = r"E:\渔业\面积计算\面积\水产种质资源保护区.gpkg"
out_file = r"E:\渔业\面积计算\面积\水产种质资源保护区（面积对比）.gpkg"

gdf = gpd.read_file(in_file)
gdf = gdf.to_crs(32650)
gdf["面积"] = gdf.geometry.area/1000000
gdf = gdf.rename(columns=lambda x: x.replace("\n", "").strip())

# 2️⃣ 清理所有字符串字段里的空格和换行
for col in gdf.columns:
    if gdf[col].dtype == "object":  # 只处理字符串列
        gdf[col] = gdf[col].astype(str).str.replace("\n", "").str.strip()
print(gdf.columns.tolist())  # 再确认一次

results = []
# 分组：保护区名称 + 类型
grouped = gdf.groupby(["生态空间保护区域名称","主导生态功能"])
print(grouped)
for (name, t), group in grouped:
	# if t == "保护区":
	# 	# 任选一条保护区面积
	# 	protect_area = float(group.iloc[0]["总面积（公顷）"])
	# elif t == "核心区":
	# 	protect_area = float(group.iloc[0]["核心区面积（公顷）"])
	# else:
	# 	protect_area = float(group.iloc[0]["实验区面积（公顷）"])
	# # 累加面积
	protect_area = float(group.iloc[0]["国家级生态保护红线面积"])
	total_area = group["面积"].sum()
	# 计算偏差百分比
	deviation = (total_area - protect_area) / protect_area * 100 if protect_area else None
	
	# 保存结果
	gdf.loc[group.index, "偏差百分比"] = deviation


# 写出到新 gpkg
if os.path.exists(out_file):
	os.remove(out_file)

gdf.to_file(out_file, driver="GPKG", encoding="utf-8")

print("处理完成，结果已写出：", out_file)


