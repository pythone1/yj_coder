import pandas as pd
import os
import re

def is_main_species(value):
    """
    判断关键词在该行是否为主养（产量占比 ≥ 50%）
    """
    text = str(value)
    matches = re.findall(r'([^:,，]+):([\d\.]+)', text)  # 提取所有 品种:产量
    total = 0.0
    target = 0.0
    for species, amount in matches:
        try:
            amount = float(amount)
            total += amount
            if any(kw in species for kw in keywords):
                target += amount
        except:
            continue
    return total > 0 and (target / total) >= 0.5
# 定义多组养殖品种关键词
keywords_list = [
    ["鲫鱼"],
    ["鳊鲂"],

    # ["蛙"],
    # ["黄鳝"],
    # ["鲈鱼"],
    # ["泥鳅"],
    # ["乌鳢"]
]

# 输入Excel文件路径
excel_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250701\常州市七条鱼\202500701常州市池塘信息表.xlsx'
# 输出文件夹路径
outpath = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250701\常州市七条鱼'

# 读取Excel文件
df = pd.read_excel(excel_path, engine='openpyxl')

# 遍历每组关键词
for keywords in keywords_list:
    pattern = '|'.join(keywords)

    # 预筛选包含关键词的行
    filtered_df = df[df['养殖品种/预计亩产量'].astype(str).str.contains(pattern, na=False)].copy()
    if filtered_df.empty:
        print(f"关键词 {keywords} 未匹配到数据，跳过导出。")
        continue

    # 筛选主养是目标关键词的记录
    filtered_df = filtered_df[filtered_df['养殖品种/预计亩产量'].apply(is_main_species)]

    if filtered_df.empty:
        print(f"关键词 {keywords} 主养占比未满足条件，跳过导出。")
        continue

    # 提取区县
    filtered_df['区县'] = filtered_df['地址'].astype(str).str.split('-').str[2]

    # 面积转亩
    filtered_df['图斑面积'] = pd.to_numeric(filtered_df['图斑面积'], errors='coerce') * 0.0015

    # 分组统计
    grouped = (
        filtered_df
        .groupby(['养殖经营人名称', '身份证号', '统一社会信用代码', '区县'], dropna=False)['图斑面积']
        .sum()
        .reset_index()
        .rename(columns={'图斑面积': '总面积（亩）'})
    )

    # 构造文件名并导出
    keyword_name = '_'.join(keywords)
    outfile = os.path.join(outpath, f"常州市_{keyword_name}_主养养殖主体统计.xlsx")
    grouped.to_excel(outfile, index=False)
    print(f"已导出：{outfile}")
