import geopandas as gpd

# 读取shp文件
gdf = gpd.read_file(r"G:\影像\徐圩可用影像\徐圩新区土地分类.gpkg")  # 替换为你的文件路径

# 投影到UTM 50N (EPSG:32650)，单位为米
gdf = gdf.to_crs(epsg=32650)
# 计算面积（平方米），再转换为亩
gdf["area_mu"] = gdf.geometry.area * 0.0015

# 计算总面积（亩）
total_area_mu = gdf["area_mu"].sum()
print(f"总面积：{total_area_mu:.2f} 亩")

# 按category字段分类汇总面积
category_area = gdf.groupby("category")["area_mu"].sum().reset_index()
category_area = category_area.sort_values(by="area_mu", ascending=False)

print("各类别总面积（亩）：")
print(category_area)
