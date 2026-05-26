import geopandas as gpd

gdf = gpd.read_file(r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\20250516要素信息图.gpkg")
gdf = gdf.to_crs(epsg=32650)
gdf['面积_㎡'] = gdf.geometry.area

gdf_yz = gdf[gdf['养殖状态'] == '养殖'].drop_duplicates(subset='图斑编号')
yz_area_m2 = gdf_yz['面积_㎡'].sum()

gdf_total = gdf[gdf['地址'].notna()]  # 先排除 NaN
gdf_total = gdf_total[~gdf_total['地址'].str.strip().isin(['', 'NULL'])]
gdf_total = gdf_total.drop_duplicates(subset='图斑编号')
total_area_m2 = gdf_total['面积_㎡'].sum()

unused_area_m2 = total_area_m2 - yz_area_m2
total_area_mu = total_area_m2 * 0.0015
yz_area_mu = yz_area_m2 * 0.0015
unused_area_mu = unused_area_m2 * 0.0015

print(f"总面积：{total_area_mu:.2f} 亩")
print(f"养殖面积：{yz_area_mu:.2f} 亩")
print(f"未使用面积：{unused_area_mu:.2f} 亩")
