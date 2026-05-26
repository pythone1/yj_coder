import geopandas as gpd
import pandas as pd

# ========== 配置部分 ==========
gpkg_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250818\0818新街街道池塘信息表.xlsx"   # 输入 GPKG 文件路径
excel_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250818\新街街道.xlsx"  # 输入 Excel 文件路径
output_excel = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250818\养殖主体对比结果.xlsx"  # 输出 Excel 文件
output_gpkg = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250818\养殖匹配结果.gpkg"       # 输出 GPKG 文件

# GPKG 和 Excel 的匹配字段
gpkg_col = "养殖经营人名称"
excel_col = "养殖主体"
excel_remark_col = "备注"

# ========== 读取文件 ==========
gdf = gpd.read_file(gpkg_path)
df = pd.read_excel(excel_path)

# ========== 清理数据（去除空格，统一字符串格式） ==========
gdf[gpkg_col] = gdf[gpkg_col].astype(str).str.strip()
df[excel_col] = df[excel_col].astype(str).str.strip()

# ========== 匹配 ==========
# Excel 标记：是否在 GPKG 内
df["匹配情况"] = df[excel_col].isin(gdf[gpkg_col]).map({True: "在GPKG", False: "不在GPKG"})

# GPKG 标记：是否在 Excel 内
gdf["匹配情况"] = gdf[gpkg_col].isin(df[excel_col]).map({True: "在Excel", False: "不在Excel"})

# ========== 把 Excel 备注写回 GPKG ==========
# 先建一个 dict 映射
remark_dict = dict(zip(df[excel_col], df[excel_remark_col]))
gdf["备注_Excel"] = gdf[gpkg_col].map(remark_dict)  # 匹配到的写入备注

# ========== 把不在 Excel 的名单单独列出 ==========
gdf["不在Excel名单"] = gdf.apply(lambda row: row[gpkg_col] if row["匹配情况"] == "不在Excel" else None, axis=1)

# ========== 保存结果 ==========
# 保存 Excel
df.to_excel(output_excel, index=False)

# 保存 GPKG
gdf.to_file(output_gpkg, driver="GPKG", encoding="utf-8")

print("处理完成！结果已输出：")
print(f"Excel: {output_excel}")
print(f"GPKG: {output_gpkg}")
