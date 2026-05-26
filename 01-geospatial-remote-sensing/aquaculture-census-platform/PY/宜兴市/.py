"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: .py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import geopandas as gpd
import pandas as pd

# ====== 输入输出路径 ======
input_path = r"E:\全省养殖池溏上图入库普查\项目验收\20260310\无锡市池塘信息.gpkg"
output_path = r"E:\全省养殖池溏上图入库普查\项目验收\20260310\宜兴市池塘信息_分镇.xlsx"

# ====== 读取数据 ======
gdf = gpd.read_file(input_path)

# ====== 1. 地址筛选 ======
mask_addr = gdf["地址"].str.contains("宜兴市", na=False)

# ====== 2. 填报状态筛选 ======
mask_status = gdf["填报状态"] == "已填报养殖"

gdf_filtered = gdf[mask_addr & mask_status].copy()

# ====== 3. 面积字段 ======
gdf_filtered["面积_亩"] = gdf_filtered["图斑面积"]

# ====== 4. 拆分“镇” ======
# 地址格式假设：XX-XX-XX-镇-XX
gdf_filtered["镇"] = gdf_filtered["地址"].str.split("-").str[3]

# ====== 5. 创建 Excel writer ======
writer = pd.ExcelWriter(output_path, engine="openpyxl")

# ====== 6. 镇级汇总容器 ======
town_summary = []

# ====== 7. 按镇循环 ======
for town, df_town in gdf_filtered.groupby("镇"):

    # ---- 按养殖户分组 ----
    group_fields = ["养殖经营人名称", "联系方式", "地址"]

    df_grouped = (
        df_town
        .groupby(group_fields, as_index=False)
        .agg(
            总养殖面积_亩=("面积_亩", "sum"),
            图斑数量=("图斑面积", "count")
        )
    )

    # ---- 筛选 20~50亩 ----
    df_result = df_grouped[
        (df_grouped["总养殖面积_亩"] >= 20) &
        (df_grouped["总养殖面积_亩"] <= 50)
    ]

    # ---- 镇总面积（不过滤，直接全量相加）----
    town_total_area = df_result["总养殖面积_亩"].sum()

    # ---- 记录汇总 ----
    town_summary.append({
        "镇": town,
        "总面积": town_total_area
    })

    # ---- 写入 sheet（按镇名）----
    sheet_name = str(town)[:31]  # Excel sheet名限制31字符
    df_result.to_excel(writer, sheet_name=sheet_name, index=False)

# ====== 8. 汇总表 ======
df_summary = pd.DataFrame(town_summary)

# 按面积排序（从大到小）
df_summary = df_summary.sort_values(by="总面积", ascending=False)

# 写入汇总sheet
df_summary.to_excel(writer, sheet_name="镇级汇总", index=False)

# ====== 9. 保存 ======
writer.close()

# ====== 10. 输出总结语句 ======
summary_text = "各镇总养殖面积排序（从大到小）：\n"
for i, row in df_summary.iterrows():
    summary_text += f"{row['镇']}：{row['总面积']:.2f}亩\n"

print(summary_text)
print(f"完成，已导出：{output_path}")