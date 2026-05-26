# import pandas as pd
#
# # 输入文件路径
# input_excel = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250910\部队农场数据修正.xlsx"
# output_excel = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250910\部队农场数据修正完成.xlsx"
#
# # 读取 Excel 文件
# df = pd.read_excel(input_excel)
#
# # 假设列名叫 “图斑编号*”，根据你的数据来调整
# col_name = "图斑编号"
#
# # 新建一个空的 DataFrame，用来存放结果
# new_rows = []
#
# for _, row in df.iterrows():
#     # 取出图斑编号列，转为字符串，防止是数字
#     tbid_value = str(row[col_name]) if pd.notna(row[col_name]) else ""
#     # 按 “、” 拆分
#     tbid_list = [v.strip() for v in tbid_value.split("、") if v.strip()]
#
#     # 如果有多个编号，就复制该行
#     for tbid in tbid_list:
#         new_row = row.copy()
#         new_row[col_name] = tbid
#         new_rows.append(new_row)
#
# # 转换成新的 DataFrame
# result_df = pd.DataFrame(new_rows)
#
# # 写出结果到 Excel
# result_df.to_excel(output_excel, index=False)
#
# print("处理完成，结果已保存到：", output_excel)

import geopandas as gpd
import pandas as pd

# 输入文件
excel_file = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\宜兴市鳊鲫鱼养殖及监管信息表.xlsx'
gpkg_file = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\宜兴市池塘图斑库.gpkg'

# 读取数据
excel_df = pd.read_excel(excel_file)
gdf_original = gpd.read_file(gpkg_file)

# 确保 key 列为字符串
excel_df['图斑编号'] = excel_df['图斑编号'].astype(str)
gdf_original['tbid'] = gdf_original['tbid'].astype(str)

# 仅保留 Excel 中存在的图斑
gdf_filtered = gdf_original[gdf_original['tbid'].isin(excel_df['图斑编号'])]
gdf_filtered = gdf_filtered[['tbid', 'geometry']]

# 计算面积（亩）和中心点经纬度
# 投影到 32650 计算面积
gdf_utm = gdf_filtered.to_crs(epsg=32650)
areas_mu = gdf_utm.area * 0.0015

# 计算中心点并转为 WGS84 经纬度
gdf_centroid = gdf_filtered.to_crs(epsg=4326).centroid
longitudes = gdf_centroid.x
latitudes = gdf_centroid.y

# 生成结果 DataFrame
calc_df = pd.DataFrame({
    "图斑编号": gdf_filtered["tbid"].values,
    "塘口面积（亩）": areas_mu.values,
    "经度": longitudes.values,
    "纬度": latitudes.values
})

# 把结果合并回 excel_df
excel_df = pd.merge(excel_df, calc_df, on="图斑编号", how="left")

# 输出到 Excel（可覆盖原表，也可写新文件）
output_excel = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250902\宜兴市鳊鲫鱼养殖及监管信息表_更新.xlsx'
excel_df.to_excel(output_excel, index=False)

print(f"表格已更新并保存到：{output_excel}")

