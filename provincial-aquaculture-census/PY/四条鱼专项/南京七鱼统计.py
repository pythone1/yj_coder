import pandas as pd
import re

# ======== 配置部分 ========
excel_path = r"F:\Unlimited\Flask_yolo\data\crab\qingtai\南京市.xlsx"
species_keywords = ['鳊鲂', '鲫鱼', '鲈鱼', '泥鳅', '乌鳢', '黄鳝', '蛙']
area_field = "图斑面积"
species_field = "养殖品种/预计亩产量"
address_field = "地址"

# ======== 读取数据 ========
df = pd.read_excel(excel_path, dtype=str)
df[area_field] = pd.to_numeric(df[area_field], errors='coerce')

# ======== 筛选包含任一目标品种的记录 ========
pattern = '|'.join(re.escape(s) for s in species_keywords)
mask = df[species_field].astype(str).str.contains(pattern, na=False)
df_filtered = df[mask].copy()

# ======== 提取区县 ========
def get_county(addr):
    parts = str(addr).split('-')
    return parts[2].strip() if len(parts) >= 3 and parts[2].strip() != '' else '未知'

df_filtered["区县"] = df_filtered[address_field].apply(get_county)

# ======== 面积换算亩 ========
df_filtered["面积(亩)"] = df_filtered[area_field] * 0.0015

# ======== 为每个品种生成布尔列（塘口） ========
for sp in species_keywords:
    df_filtered[sp] = df_filtered[species_field].astype(str).str.contains(sp, na=False).astype(int)

# ======== 基础统计：塘口数和总面积 ========
group = df_filtered.groupby("区县")
result = group.agg(
    塘口数=("区县", "size"),
    总面积_亩=("面积(亩)", "sum")
).reset_index()

# ======== 每个品种的塘口数和面积 ========
for sp in species_keywords:
    # 塘口数
    tongkou_counts = group[sp].sum()
    # 面积（只统计包含该品种的塘口的面积）
    area_sums = group.apply(lambda x: x.loc[x[sp] == 1, "面积(亩)"].sum())

    result[f"{sp}_塘口数"] = tongkou_counts.reindex(result["区县"]).fillna(0).astype(int).values
    result[f"{sp}_面积_亩"] = area_sums.reindex(result["区县"]).fillna(0).round(2).values

# ======== 保留两位小数 ========
result["总面积_亩"] = result["总面积_亩"].round(2)

# ======== 输出结果 ========
out_path = r"F:\Unlimited\Flask_yolo\data\crab\qingtai\各区县七鱼统计_按品种含面积.xlsx"
result.to_excel(out_path, index=False)

print("统计完成，已保存到：", out_path)
print(result.head())
