"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: 1.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import geopandas as gpd
import pandas as pd

# 读取行政区划
city_gdf = gpd.read_file(r"F:\xiangmu\20241225全省池塘问题核查\增减图斑\20250112全省图斑\20250104江苏省池塘图斑\JiangSu_XZQH.shp")[['市', 'geometry']]

# 读取池塘
pond_gdf = gpd.read_file(r"E:\全省养殖池溏上图入库普查\项目验收\2024年12月图斑抽检结果\池塘图斑.gpkg")
pond_gdf = pond_gdf.reset_index(drop=True)
pond_gdf['pond_id'] = pond_gdf.index  # 加唯一标识

# 确保坐标系一致
if pond_gdf.crs != city_gdf.crs:
    city_gdf = city_gdf.to_crs(pond_gdf.crs)

# 使用 sjoin 做空间连接（池塘整体 vs 市）
joined = gpd.sjoin(pond_gdf[['pond_id', 'geometry']], city_gdf, how='inner', predicate='intersects')

# 可能有池塘落入多个市，随机保留一个市
joined = joined[['pond_id', '市']].drop_duplicates()
joined = joined.groupby('pond_id').apply(lambda x: x.sample(1)).reset_index(drop=True)

# 统计各市池塘数量
result = joined['市'].value_counts().reset_index()
result.columns = ['市', '池塘数量']

# 保存
output_path = r"E:\全省养殖池溏上图入库普查\行政区划\每市池塘数量统计结果.xlsx"
result.to_excel(output_path, index=False)

print("✅ 统计完成，池塘未被截断，结果已保存：", output_path)



# 设置目录路径（替换为你实际的目录）
# folder = r"E:\全省养殖池溏上图入库普查\项目验收\2024年12月图斑抽检结果\抽检"
#
# # 获取所有 .gpkg 文件路径
# gpkg_files = glob.glob(os.path.join(folder, "*.gpkg"))
# i = 0
# all_gdfs = []
# # 遍历每个文件，统计 tag == 1 的数量
# for file in gpkg_files:
#     try:
#         gdf = gpd.read_file(file)
#         gdf = gdf.to_crs(32650)
#         if 'tag' not in gdf.columns:
#             print(f"[跳过] 文件 {os.path.basename(file)} 中不包含 'tag' 字段")
#             continue
#         count = (gdf['tag'] == 1).sum()
#         print(f"{os.path.basename(file)} 中 tag==1 的数量为：{count}")
#         gdf = gdf[['geometry', 'tag']]
#
#         all_gdfs.append(gdf)
#         i+=count
#     except Exception as e:
#         print(f"[错误] 读取 {file} 时出错：{e}")
# print(i)
#
# if all_gdfs:
#     merged_gdf = gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True), crs=all_gdfs[0].crs)
#
#     merged_gdf.to_file(r'E:\全省养殖池溏上图入库普查\项目验收\2024年12月图斑抽检结果\抽检\抽检汇总.gpkg', driver="GPKG")
#
# else:
#     print("⚠️ 没有有效的图层可合并。")