"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: .py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import pandas as pd
import os

# 读取数据
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\数据\高邮市\高邮数据\0721下午三点半高邮市成品主体清单明细表（精确到塘口）.xlsx')

# 提取“镇”名称
df['镇'] = df['地址'].astype(str).str.split('-').str[3]  # 第三个元素

# 获取所有镇名
towns = df['镇'].dropna().unique()

# 输出目录
output_dir = r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\数据\高邮市\高邮数据\各镇'
os.makedirs(output_dir, exist_ok=True)

# 假设类型字段只有两个：比如 “养殖”、“未使用”
for town in towns:
    df_town = df[df['镇'] == town]

    # 分类
    type_groups = df_town.groupby('类型')

    # 创建一个ExcelWriter用于写两个表单
    output_path = os.path.join(output_dir, f'{town}.xlsx')
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for type_name, group in type_groups:
            # 清理类型名作为合法sheet名
            sheet_name = str(type_name)[:31]  # 限制Excel sheet名长度
            group.to_excel(writer, sheet_name=sheet_name, index=False)

print('所有镇分类完成')
