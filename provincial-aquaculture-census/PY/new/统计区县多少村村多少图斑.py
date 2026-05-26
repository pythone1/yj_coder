# import geopandas as gpd
# import pandas as pd
#
# # 读取gpkg文件，假设图层名为第一个图层
# file_path = r'D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-05\池塘信息表--池塘图斑(4).gpkg'
# gdf = gpd.read_file(file_path)
#
# # 拆分“地址”字段，假设格式为“省-市-区县-镇-村”
# address_split = gdf['地址'].str.split('-', expand=True)
#
# # 保证只有前5列（多余的部分会被自动丢弃）
# address_split = address_split.iloc[:, :5]
# address_split.columns = ['省', '市', '区县', '镇', '村']
#
# # 如果 gdf 中已存在 '省'~'村' 字段，先删除它们
# gdf = gdf.drop(columns=['省', '市', '区县', '镇', '村'], errors='ignore')
# # 再合并新拆分字段
# gdf = pd.concat([gdf, address_split], axis=1)
#
# # 每个村有多少图斑（按完整地址5级分组）
# village_counts = gdf.groupby(['省', '市', '区县', '镇', '村']).size().reset_index(name='图斑数量')
#
# # 每个区县有多少村（按“省-市-区县-镇-村”去重后再按“区县”统计）
# unique_villages = gdf[['省', '市', '区县', '镇', '村']].drop_duplicates()
# district_village_counts = (
#     unique_villages
#     .groupby(['省', '市', '区县'])
#     .size()
#     .reset_index(name='该区县村数量')
# )
#
# # 合并两个结果（如果你想放在一张表中，可以左连接）
# result = pd.merge(village_counts, district_village_counts, on=['省', '市', '区县'], how='left')
#
# # 输出前几行查看
# print(result.head())
#
# # 可选择保存结果
# result.to_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\20250528\结果\地址统计结果.xlsx', index=False)


import geopandas as gpd

# 读取gpkg文件
gdf = gpd.read_file(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250617\四个区县图斑.gpkg")

# 筛选条件
filtered = gdf[
    # gdf["区县"].isin(["溧阳s", "武进", "射阳", "兴化"]) &
    gdf["养殖品种/预计亩产量"].astype(str).str.contains("鲫|鳊", na=False) &
    (gdf["图斑面积"] > 5) &
    (gdf["用途"] != "苗种培育")
]

# 只保留“区县”与geometry字段
# output = filtered[["区县", "geometry"]]

# 导出为新的文件（可选为shp/gpkg/geojson等）
filtered.to_file(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250617\溧阳武进射阳兴化5亩以上鲫鱼鳊鱼图斑（不含苗种培育）.gpkg")

