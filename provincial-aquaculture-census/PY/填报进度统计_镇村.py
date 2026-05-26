import geopandas as gpd
import pandas as pd
# 读取池塘的 Shapefile
pond_shapefile_path = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\常州市\20250226常州金坛\常州金坛池塘信息-1740561566821-池塘图斑.gpkg'  # 替换为池塘 Shapefile 的路径
pond_gdf = gpd.read_file(pond_shapefile_path)
# 读取行政区 Shapefile
admin_shapefile_path = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\常州市\20250226常州金坛\金坛区_行政村边界_同名合并.shp'  # 替换为行政区 Shapefile 的路径
admin_gdf = gpd.read_file(admin_shapefile_path)

# 确保池塘数据和行政区数据的 CRS 相同
pond_gdf = pond_gdf.to_crs(admin_gdf.crs)

pond_gdf = pond_gdf.drop(['index_right'], axis=1)
# admin_gdf = admin_gdf.drop(['index_right', 'index_left'], axis=1)
# 执行池塘与行政区的空间相交，找到与行政区相交的池塘
ponds_with_town = gpd.sjoin(pond_gdf, admin_gdf[['ZLDWMC', 'geometry']], how='inner', predicate='intersects')

# 按镇（SCZ）分组并统计池塘数量
town_pond_count = ponds_with_town.groupby('ZLDWMC').size().reset_index(name='池塘数量')

# 筛选出“状态”不为“未填报”的池塘数据
filled_ponds = ponds_with_town[ponds_with_town['填报状态'] != '未填报']

# 按镇（SCZ）分组并统计已填报池塘的数量
town_filled_count = filled_ponds.groupby('ZLDWMC').size().reset_index(name='已填报数量')

# 合并池塘数量和已填报数量数据
merged_df = pd.merge(town_pond_count, town_filled_count, on='ZLDWMC', how='left')

# 计算填报进度（已填报数量 / 池塘数量）
merged_df['填报进度'] = merged_df['已填报数量'] / merged_df['池塘数量']


# 保存合并后的结果到 Excel 文件
output_excel_path = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\常州市\20250226常州金坛\20250226常州金坛填报进度统计.xlsx'  # 替换为保存合并结果的路径
merged_df.to_excel(output_excel_path, index=False)

print(f"合并后的结果已保存到：{output_excel_path}")