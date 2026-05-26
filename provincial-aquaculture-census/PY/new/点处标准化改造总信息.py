import geopandas as gpd
import pandas as pd

# === 输入路径 ===
gpkg_path = r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\填报养殖点.gpkg"  # 修改为你的实际路径
# === 读取数据 ===
gdf = gpd.read_file(gpkg_path)
gdf = gdf[gdf["填报状态"] == "已填报养殖"]
gdf["图斑面积_y"] = pd.to_numeric(gdf["图斑面积_y"], errors="coerce")
gdf = gdf[gdf["图斑面积_y"] > 50]
gdf = gdf.drop_duplicates(subset="图斑id")

# === 筛选条件 ===
gdf_filtered = gdf[
    (gdf["是否完成池塘标准化改造"] == "是")
]
# gdf_filtered = gdf
# === 提取“市”字段 ===
gdf_filtered["市"] = gdf_filtered["地址"].str.split("-").str[1]

# === 按市统计面积 ===
summary = gdf_filtered.groupby("市", as_index=False)["图斑面积_y"].sum()
summary = summary.rename(columns={"图斑面积": "完成标准化改造面积（万亩）"})

# === 导出结果 ===
output_path = r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\各市50亩以上完成标准化改造总面积.xlsx"  # 修改为你希望保存的位置
summary.to_excel(output_path, index=False)

print("✅ 统计完成，结果已保存到：", output_path)
