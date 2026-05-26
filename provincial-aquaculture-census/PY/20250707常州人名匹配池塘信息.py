import pandas as pd

# 读取A、B表
a_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250707\鲫鱼主养养殖主体.xlsx'  # 包含“养殖经营人名称”“区县”“总面积（亩）”
b_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250707\20250707常州市池塘信息表.xlsx'  # 包含“养殖经营人名称”“地址”“池塘坐标”

df_a = pd.read_excel(a_path)
df_b = pd.read_excel(b_path)

# 合并：以养殖经营人名称为键进行左连接，允许B中有多条
df_merged = df_a.merge(df_b[['养殖经营人名称', '地址', '池塘位置']],
                       on='养殖经营人名称', how='left')

# # 重命名字段
# df_merged = df_merged.rename(columns={
#     '地址': '所属镇村',
#     '池塘位置': '池塘位置',
#     '总面积（亩）': '总面积（亩）'
# })

# 添加“序号”
# df_merged.insert(0, '序号', range(1, len(df_merged) + 1))

# 可选：将“池塘坐标”加分号结尾（如截图中）
# df_merged['池塘位置'] = df_merged['池塘位置'].astype(str).str.strip() + '；'

# 保存
df_merged.to_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250707\鲫鱼养殖户池塘位置匹配结果.xlsx', index=False)
