import pandas as pd

# 设置文件路径
file_a = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250625\常州市\20250625-out\上图入库填报信息统计20250625-094242.xlsx'  # 多个sheet
file_b = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250625\常州市\20250625-out\池塘信息表.xlsx'  # 包含“联系方式”、“池塘位置”、“图斑编号”等字段

# 读取B表，并保留需要用到的字段
df_b = pd.read_excel(file_b)
df_b = df_b[['养殖经营人名称', '养殖经营人证件号码', '地址', '池塘位置', '图斑编号', '联系方式']]

# 匹配函数：基于三列匹配，随机抽取一条匹配记录
def match_info(row, df_b):
    matches = df_b[
        (df_b['养殖经营人名称'] == row['养殖经营人名称']) &
        (df_b['养殖经营人证件号码'] == row['养殖经营人证件号码']) &
        (df_b['地址'] == row['地址'])
    ]
    if not matches.empty:
        match_row = matches.sample(1).iloc[0]
        return pd.Series([match_row['池塘位置'], match_row['图斑编号'], match_row['联系方式']])
    else:
        return pd.Series([None, None, None])
import os
os.chdir(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250625\常州市\20250625-out')
# 读取A的所有sheet名
xls = pd.ExcelFile(file_a)
sheet_names = xls.sheet_names

# 创建Excel写入对象
with pd.ExcelWriter('上图入库鱼种填报信息按养殖主体统计.xlsx', engine='openpyxl') as writer:
    for sheet in sheet_names:
        df_a = pd.read_excel(file_a, sheet_name=sheet)

        # 匹配信息并添加三列
        df_a[['池塘位置', '图斑编号', '联系方式']] = df_a.apply(lambda row: match_info(row, df_b), axis=1)

        # 写入新文件
        df_a.to_excel(writer, sheet_name=sheet, index=False)

print("所有工作表已成功添加池塘信息和联系方式，结果保存在 A_附加池塘信息.xlsx。")
