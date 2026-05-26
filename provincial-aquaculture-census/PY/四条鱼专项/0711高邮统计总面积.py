import pandas as pd

# 读取 Excel
df = pd.read_excel(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250926\1023高邮市.xlsx")  # 替换为你的文件路径

# 筛选“养殖状态”为“养殖”，并去重
df = df[df['养殖状态'] == '养殖'].drop_duplicates(subset='图斑编号')

# 拆分地址字段，获取 区县、镇、村
df[['省', '市', '区县', '镇', '村']] = df['地址'].str.split('-', expand=True)

# 面积转换为数值
df['图斑面积'] = pd.to_numeric(df['图斑面积'], errors='coerce')
df['图斑面积'] = df['图斑面积']*0.0015
# 村级统计（带镇）
village_table = df.pivot_table(
    index=['镇', '村'],
    columns='养殖方式',
    values='图斑面积',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='汇总'
).reset_index()

# 镇级统计
town_table = df.pivot_table(
    index='镇',
    columns='养殖方式',
    values='图斑面积',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='汇总'
).reset_index()

# 区县级统计
district_table = df.pivot_table(
    index='区县',
    columns='养殖方式',
    values='图斑面积',
    aggfunc='sum',
    fill_value=0,
    margins=True,
    margins_name='汇总'
).reset_index()

# 保存为 Excel 多表单
output_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250926\1023高邮市养殖方式_村镇区县统计.xlsx"  # 替换为保存路径
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    village_table.to_excel(writer, sheet_name='村级统计', index=False)
    town_table.to_excel(writer, sheet_name='镇级统计', index=False)
    district_table.to_excel(writer, sheet_name='区县统计', index=False)

print("✅ 统计结果已保存为多表单 Excel：", output_path)
