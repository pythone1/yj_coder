import pandas as pd

# 读取 Excel 文件
a_path = r"E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250331江阴市疑点选取\20250331江阴核查点位选取.xlsx"  # 请替换为 A 文件路径
b_path = r"E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250313\池塘信息-无锡20250313-20250313110738-无锡市-疑点统计表-全\总表.xlsx"  # 请替换为 B 文件路径

df_a = pd.read_excel(a_path)
df_b = pd.read_excel(b_path)

# # 获取 B 的倒数 17 行
# df_b_last_17 = df_b.tail(17)

# 基于 '图斑编号' 字段匹配，将 B 的数据合并到 A
merged_df = df_a.merge(df_b, on="图斑编号", how="left", suffixes=("_A", "_B"))

# 保存合并后的数据
target_path = r"E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250331江阴市疑点选取\AB.xlsx"  # 结果文件路径
merged_df.to_excel(target_path, index=False)

print(f"合并完成，结果已保存为 {target_path}")
