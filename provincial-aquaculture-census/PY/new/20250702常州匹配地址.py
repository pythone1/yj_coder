import pandas as pd
import os

# 文件路径
file_a = r"D:\Users\Documents\WeChat Files\wxid_4668346683612\FileStorage\File\2025-07\两鱼（不分主混养）.xlsx"  # ← 替换为实际路径
file_b = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250701\常州市七条鱼\202500701常州市池塘信息表.xlsx"  # ← 替换为实际路径
output_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250701\常州市七条鱼\两鱼（不分主混养）匹配村地址.xlsx"  # ← 替换为你希望输出的路径
# 读取B表格并构造唯一ID
df_b = pd.read_excel(file_b, engine='openpyxl')
df_b['匹配ID'] = df_b['养殖经营人名称'].astype(str) + "_" + df_b['身份证号'].astype(str) + "_" + df_b[
    '统一社会信用代码'].astype(str)
# 建立ID到地址的映射（多个地址用逗号连接，去重）
address_map = (
    df_b.groupby('匹配ID')['地址']
    .apply(lambda x: ','.join(sorted(set(x.dropna().astype(str)))))
    .to_dict()
)
# 读取A文件所有表单
xls = pd.ExcelFile(file_a, engine='openpyxl')
sheet_names = xls.sheet_names
# 存储处理后的表单
sheet_results = {}
for sheet in sheet_names:
    df_a = xls.parse(sheet)
    df_a['匹配ID'] = df_a['养殖经营人名称'].astype(str) + "_" + df_a['身份证号'].astype(str) + "_" + df_a[
        '统一社会信用代码'].astype(str)
    # 映射地址
    df_a['匹配到的地址'] = df_a['匹配ID'].map(address_map)
    # 删除辅助列
    df_a.drop(columns=['匹配ID'], inplace=True)
    # 存储结果
    sheet_results[sheet] = df_a
# 写入新Excel
with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    for sheet, df in sheet_results.items():
        df.to_excel(writer, sheet_name=sheet, index=False)
print(f"所有表单处理完成，结果已保存至：{output_path}")
