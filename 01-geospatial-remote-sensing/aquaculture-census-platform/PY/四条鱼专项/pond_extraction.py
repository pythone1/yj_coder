"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: pond_extraction.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import pandas as pd

# ===== 读取数据 =====
df = pd.read_excel(r'D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-07\P4不同池塘用途、养殖方式、水体类型及面积占比.xlsx')  # 替换为你的路径
df['市'] = df['地址'].str.split('-').str[1]
df['面积'] = df['图斑面积_y']

# 定义分类字段与顺序
水体类型 = ['淡水', '海水', '咸水']
养殖方式 = ['池塘养殖', '渔光一体', '跑道鱼', '其他']
用途类型 = ['成品养殖', '苗种培育', '休闲垂钓', '尾水净化', '饵料培育', '其他']

# 生成每类描述的函数，排除“/”
def get_describe(df, city, field, categories, title, tail):
    sub_df = df[(df['市'] == city) & (df[field] != '/')]
    if sub_df.empty:
        return ""

    total_area = sub_df['面积'].sum()
    if total_area == 0:
        return ""

    area_by_type = sub_df.groupby(field)['面积'].sum().reindex(categories, fill_value=0)
    percent_by_type = (area_by_type / total_area * 100).round(2)

    # 过滤掉占比为 0.00% 的类别
    labels = [cat for cat, pct in zip(categories, percent_by_type) if pct > 0]
    percents = [f"{pct:.2f}%" for pct in percent_by_type if pct > 0]

    if not labels:
        return ""

    main_type = area_by_type.idxmax()

    # 构造描述
    labels_str = "、".join(labels)
    percents_str = "、".join(percents)
    return f"{city}{title}包括{labels_str}，其面积占比分别为{percents_str}，{main_type}{tail}。"

# 汇总描述
results = []
for city in sorted(df['市'].dropna().unique()):
    water_text = get_describe(df, city, '水体类型', 水体类型, '池塘养殖的水体类型', '养殖为主要水体类型')
    style_text = get_describe(df, city, '养殖方式', 养殖方式, '养殖方式', '为主要养殖方式')
    use_text = get_describe(df, city, '用途', 用途类型, '池塘用途', '为主要用途')

    results.append({
        '市': city,
        '水体类型描述': water_text,
        '养殖方式描述': style_text,
        '池塘用途描述': use_text
    })

# 保存为表格
result_df = pd.DataFrame(results)
result_df.to_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\各市池塘类型养殖用途描述统计.xlsx', index=False)

print("✅ 已保存：各市池塘类型养殖用途描述统计.xlsx")
