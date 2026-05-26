import pandas as pd
import geopandas as gpd
import glob
import os

# === 参数设置 ===
excel_folder = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250613\主体匹配20250613\比对清单"  # 替换为存放 Excel 的文件夹路径
gpkg_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250613\主体匹配20250613\比对清单\池塘信息表--池塘图斑(1).gpkg"         # 替换为你的 GPKG 文件路径
output_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250613\主体匹配20250613\比对清单\新建文件夹\兴化市.gpkg" # 输出结果路径

# === 步骤 1：获取所有 Excel 文件 ===
excel_files = glob.glob(os.path.join(excel_folder, "兴化市*.xlsx"))

# === 步骤 2：提取所有文件中前3个表单的“区县”和“图斑id”，联合去重 ===
combined_df = pd.DataFrame()

for excel_file in excel_files:
    sheet_names = pd.ExcelFile(excel_file).sheet_names[:3]
    for sheet in sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet)
        if "图斑id" in df.columns and "区县" in df.columns:
            df = df[["区县", "图斑id"]].dropna()
            combined_df = pd.concat([combined_df, df], ignore_index=True)

# 联合去重
combined_df = combined_df.drop_duplicates(subset=["区县", "图斑id"])

# 提取唯一的图斑id（字符串形式）
unique_ids = combined_df["图斑id"].astype(str).unique()

# === 步骤 3：读取 GPKG 并筛选图斑 ===
gdf = gpd.read_file(gpkg_path)
filtered_gdf = gdf[gdf["ID"].astype(str).isin(unique_ids)]

# === 步骤 4：保存结果 ===
filtered_gdf.to_file(output_path, driver="GPKG")
print(f"筛选完成，共保留 {len(filtered_gdf)} 个图斑，保存至：{output_path}")