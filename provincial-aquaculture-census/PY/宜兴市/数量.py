import pandas as pd

# === 文件路径 ===
excel_path = r"E:\全省养殖池溏上图入库普查\PY\宜兴市\output_with_analysis.xlsx"
output_path = r"E:\全省养殖池溏上图入库普查\PY\宜兴市\业主信息_带数量.xlsx"

# === 读取 Excel ===
df = pd.read_excel(excel_path)

# 清洗列名（防止有空格、换行）
df.columns = df.columns.str.strip()

# === 指定字段名 ===
town_col = "所在镇村（镇街+村）"
name_col = "养殖主体姓名（名称）"

# === 按 镇村+姓名 分组统计数量 ===
count_series = df.groupby([town_col, name_col]).size()

# 将统计结果合并回原表
df["同镇同名数量"] = df.set_index([town_col, name_col]).index.map(count_series)

# === 写出结果 ===
df.to_excel(output_path, index=False, engine="openpyxl")

print(f"✅ 已完成：在原表中添加“同镇同名数量”列，写出到：{output_path}")
