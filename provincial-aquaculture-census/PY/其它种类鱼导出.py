import pandas as pd
import os

# ===== 参数设置 =====
input_excel = r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\数据\高邮市\高邮数据\0721下午三点半高邮市苗种.xlsx'
output_dir = r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\数据\高邮市\高邮数据\镇拆分'
os.makedirs(output_dir, exist_ok=True)

# ===== 读取数据 =====
df = pd.read_excel(input_excel)

# ===== 品种关键词（排除的）=====
exclude_keywords = ['鳊鲂', '鲫鱼', '淡水鲈鱼', '泥鳅', '黄鳝', '蛙', '乌鳢']

# ===== 筛选：养殖状态为“养殖” =====
df = df[df['养殖状态'] == '养殖']

# ===== 筛选：养殖品种不包含任一关键词 =====
pattern = '|'.join(exclude_keywords)
df = df[~df['养殖品种/预计亩产量'].astype(str).str.contains(pattern)]

# ===== 提取镇名（地址按 - 分割，取第四段）=====
df['镇'] = df['地址'].astype(str).str.split('-').str[3]

# ===== 去除镇为空的记录（可选）=====
df = df[df['镇'].notna()]
df["图斑面积"] = pd.to_numeric(df["图斑面积"], errors="coerce")
df['面积_亩'] = df['图斑面积'] * 0.0015
df = df[['养殖经营人名称', '身份证号', '统一社会信用代码', '地址','镇','联系人', '联系方式',
                       '养殖品种/预计亩产量', '图斑编号', '面积_亩']]

# ===== 按镇分组并导出 =====
for town, group in df.groupby('镇'):
    filename = os.path.join(output_dir, f'{town}.xlsx')
    group.to_excel(filename, index=False)

print("导出完成，每个镇一张表格。")
