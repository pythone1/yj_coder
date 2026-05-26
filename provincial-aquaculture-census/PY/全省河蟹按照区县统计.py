import geopandas as gpd
import pandas as pd

# 读取 GPKG 文件（假设图层名为第一个图层）
file_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250512\河蟹养殖\池塘信息表--池塘图斑(1).gpkg'
gdf = gpd.read_file(file_path)

# 筛选“养殖品种/预计亩产量”字段中包含“河蟹”的记录
gdf_crab = gdf[gdf['养殖品种/预计亩产量'].astype(str).str.contains('河蟹', na=False)]
gdf_crab.to_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250512\河蟹养殖\1.xlsx')
# # 提取“地址”字段中“-”分隔的第二个部分作为“区县”字段
# gdf_crab['区县'] = gdf_crab['地址'].astype(str).str.split('-').str[2]
#
# # 投影到 UTM Zone 50N（EPSG:32650）用于面积计算
# gdf_crab = gdf_crab.to_crs(epsg=32650)
#
# # 计算面积（平方米转亩：1 亩 = 666.6667 平方米）
# gdf_crab['面积_亩'] = gdf_crab.geometry.area * 0.0015
#
# # 按区县分组，统计蟹塘数量和总面积
# result = gdf_crab.groupby('区县').agg(
#     蟹塘数量=('geometry', 'count'),
#     总面积_亩=('面积_亩', 'sum')
# ).reset_index()
#
# # 四舍五入面积为两位小数
# result['总面积_亩'] = result['总面积_亩'].round(2)
#
# # 输出表格
# print(result)
#
# # 可选：保存为 Excel 或 CSV 文件
# result.to_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250512\河蟹养殖\各区县河蟹养殖统计表2.xlsx', index=False)
# # 或保存为 CSV：
# # result.to_csv('各区县河蟹养殖统计表.csv', index=False)
