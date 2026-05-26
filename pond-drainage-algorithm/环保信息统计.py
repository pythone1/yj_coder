import pandas as pd

# 加载Excel文件
file_path = r'E:\哨兵影像\20251229\片区1.xlsx'
data = pd.read_excel(file_path,dtype={'paishui': str})
print(data)
# data = data[data['yzmj'] > 3330]
# 处理'paishui'列，拆分多个日期并展开为多行


# 将 NaN 值填充为一个空字符串
data['paishui'] = data['paishui'].fillna('')
data['paishui'] = data['paishui'].astype(str)
print(data)
# 将 paishui 列进行处理，如果不包含逗号，则转换为单元素列表
data['paishui'] = data['paishui'].str.split(',')
print(data)
exploded_data = data.explode('paishui')
print(exploded_data)

# 将日期转换为“年月”格式
exploded_data['year_month'] = pd.to_datetime(exploded_data['paishui'], errors='coerce').dt.to_period('M')
print(exploded_data)
# 删除同一个池塘在同一月份的重复记录
unique_data = exploded_data.drop_duplicates(subset=['tkbh', 'year_month'])

# 统计每个月的池塘数量和总面积
monthly_stats = unique_data.groupby('year_month').agg(
    pond_count=pd.NamedAgg(column='tkbh', aggfunc='nunique'),  # 统计唯一池塘编号的数量
    total_area=pd.NamedAgg(column='yzmj', aggfunc='sum')
)

# 显示结果
print(monthly_stats)

# 如果需要，可以将结果保存为新的Excel文件

output_path = r'E:\哨兵影像\20251229\片区1统计.xlsx'
monthly_stats.to_excel(output_path)

# import pandas as pd
# import re
# # 读取CSV文件
# df = pd.read_excel(r'G:\xiangmu\江苏省天地图分割\儒林镇排水统计\20240619\drive-download-20240619T074308Z-001\SQA\NDWI\2021.xlsx')
# # 筛选出“yamj”大于3330的行
#
# df_filtered = df[df['yzmj'] > 3330]
#
# import pandas as pd
#
# # 将'paishui'列中的字符串按逗号分割，然后展开该列
# df_filtered['paishui'] = df_filtered['paishui'].str.split(', ')
# exploded_data = df_filtered.explode('paishui')
#
# # 如果你需要保存处理后的DataFrame到新的Excel文件
# output_path = r'G:\xiangmu\江苏省天地图分割\儒林镇排水统计\20240619\drive-download-20240619T074308Z-001\SQA\NDWI\output_file.xlsx'
# exploded_data.to_excel(output_path, index=False)
#
# # 打印前几行查看处理结果
# print(exploded_data.head())



# ## 删除paishui字段为空值的行
# df_filtered = df_filtered.dropna(subset=['paishui'])
#
# # 提取paishui字段的第一个值作为时间
# def extract_first_date(paishui_str):
#     match = re.match(r'\d{8}', paishui_str)
#     if match:
#         return match.group(0)
#     return None
#
# df_filtered['首个时间'] = df_filtered['paishui'].apply(extract_first_date)
#
# # 删除首个时间为空的行
# df_filtered = df_filtered.dropna(subset=['首个时间'])
#
# # 将首个时间转换为日期格式
# df_filtered['时间'] = pd.to_datetime(df_filtered['首个时间'], format='%Y%m%d')
#
# # 删除paishui字段和首个时间字段
# df_filtered = df_filtered.drop(columns=['paishui', '首个时间'])
#
#
# # 按月统计数据的数量和“yamj”的累加
# monthly_stats = df_filtered.resample('M', on='时间').agg({'yzmj': ['count', 'sum']})
# # 重命名列名
# monthly_stats.columns = ['排水池塘数量', '总面积']
# # 重置索引
# monthly_stats.reset_index(inplace=True)
# # 打印结果
# print(monthly_stats)
# # # 或者将结果保存到新的CSV文件
# monthly_stats.to_excel(r'G:\xiangmu\江苏省天地图分割\儒林镇排水统计\20240611金坛\drive-download-20240611T050249Z-001\NDWI\2022-2023统计.xlsx', index=False)
