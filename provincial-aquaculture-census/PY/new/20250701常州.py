# 养殖品种关键词列表
# keywords = [
#     "青鱼", "草鱼", "鲢鱼", "鳙鱼", "鲤鱼", "鲫鱼", "鳊鲂", "泥鳅", "鲇鱼", "鮰鱼", "黄颡鱼", "河鲀",
#     "短盖巨脂鲤", "长吻鮠", "黄鳝", "鳜鱼", "银鱼", "鲈鱼", "乌鳗", "乌鳢", "罗非鱼", "鲟鱼", "鳗鲡"
# ]

import pandas as pd
import os

# 定义多组养殖品种关键词
keywords_list = [
    ["鲫鱼", "鳊鲂"],
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
    # 构造正则匹配模式
    pattern = '|'.join(keywords)
    # 筛选匹配的行
    filtered_df = df[df['养殖品种/预计亩产量'].astype(str).str.contains(pattern, na=False)].copy()
    if filtered_df.empty:
        print(f"关键词 {keywords} 未匹配到数据，跳过导出。")
        continue
    # 提取区县字段
    filtered_df['区县'] = filtered_df['地址'].astype(str).str.split('-').str[2]

    # 转换图斑面积为浮点数
    filtered_df['图斑面积'] = pd.to_numeric(filtered_df['图斑面积'], errors='coerce')*0.0015
    # 分组统计
    grouped = (
        filtered_df
        .groupby(['养殖经营人名称', '身份证号', '统一社会信用代码', '区县'], dropna=False)['图斑面积']
        .sum()
        .reset_index()
        .rename(columns={'图斑面积': '总面积（亩）'})
    )
    # 构造输出文件名（关键词用_连接）
    keyword_name = '_'.join(keywords)
    outfile = os.path.join(outpath, f"常州市_{keyword_name}_养殖主体统计.xlsx")
    # 导出到Excel
    grouped.to_excel(outfile, index=False)
    print(f"已导出：{outfile}")
