import geopandas as gpd

# ===== 参数配置 =====
gpkg_path = r'D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-07\池塘信息表--池塘图斑.gpkg'  # 修改为你的实际路径
address_field = '地址'            # 地址字段名
status_field = '填报状态'        # 填报状态字段名

gdf = gpd.read_file(gpkg_path)

gdf = gdf[gdf[address_field].str.contains('六合区', na=False)]

# ===== 投影转换到 EPSG:32650 计算面积 =====
gdf = gdf.to_crs(epsg=32650)
gdf['面积_亩'] = gdf.geometry.area / 666.67  # 平方米转亩

# ===== 分组统计 =====
result = gdf.groupby(status_field).agg(
    图斑数量=('geometry', 'count'),
    总面积_亩=('面积_亩', 'sum')
).reset_index()

# ===== 输出结果 =====
print(result)

# 可选：保存到 Excel 或 CSV
# result.to_excel("六合区_填报状态统计.xlsx", index=False)
