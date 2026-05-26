import pandas as pd
import os
os.chdir(r'E:\全省养殖池溏上图入库普查\PY\七鱼疑点\无锡市\0806吴江区池塘信息表')
# 读取 Excel 文件
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\PY\七鱼疑点\无锡市\0806吴江区池塘信息表\0806吴江区池塘信息表-总表.xlsx')
# print(df)
# 假设“地址”列的名称是'地址'，可以根据需要调整列名
# 使用split拆分“地址”字段，并取出第四个字段（索引为3）
df['乡镇'] = df['地址'].str.split('-').str[3]

# 按照“地址拆分”列进行groupby
grouped = df.groupby('乡镇')
print(grouped)
# 遍历每个分组，并将每个分组保存为一个单独的 Excel 文件
for name, group in grouped:
    print(name)
    # 使用分组名称创建一个新的文件名
    file_name = f"{name}.xlsx"
    print(file_name)
    # 将每个分组的数据保存为单独的 Excel 文件
    group.to_excel(file_name, index=False)

    print(f"保存文件: {file_name}")
