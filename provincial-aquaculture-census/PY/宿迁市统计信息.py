import pandas as pd
import re

# 1. 读取数据
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250514\江阴市.xlsx')
df.columns = df.columns.str.strip()
df = df[df['养殖状态'].astype(str).str.strip() == '养殖']

# 2. 去掉图斑编号为 '/' 的记录
df = df[df['图斑编号'].astype(str).str.strip() != '/']

# 3. 提取养殖品种
def extract_species_names(text):
    if pd.isna(text) or str(text).strip() in {'/', ''}:
        return []
    # 匹配“品种名：”这种形式
    matches = re.findall(r'([\u4e00-\u9fa5]+)[：:]', str(text))
    return matches

df['提取品种'] = df['养殖品种/预计亩产量'].apply(extract_species_names)
df.to_excel(r'E:\PY\jupyter\1.xlsx')
# 4. 过滤掉仅包含河蟹、青虾的记录
# def should_keep(species_list):
#     if not species_list:
#         return False
#     allowed = {'河蟹', '青虾'}
#     return not set(species_list).issubset(allowed)
#
# df = df[df['提取品种'].apply(should_keep)]

# 5. 计算塘口面积（亩）
df['塘口面积_亩'] = pd.to_numeric(df['图斑面积'], errors='coerce').fillna(0) * 0.0015

# 6. 设置分组依据
group_cols = ['养殖经营人名称', '身份证号', '统一社会信用代码', '地址']

# 7. 定义聚合函数
def merge_one(x):
    return x.dropna().astype(str).unique()[0] if not x.dropna().empty else ''

def merge_species(list_of_lists):
    species_set = set()
    for lst in list_of_lists:
        species_set.update(lst)
    return '、'.join(sorted(species_set)) if species_set else ''

def merge_tbid(tbids):
    return '、'.join(tbids.dropna().astype(str))

# 8. 分组聚合
grouped = df.groupby(group_cols).agg({
    '联系方式': merge_one,
    '池塘位置': merge_one,
    '塘口面积_亩': 'sum',
    '池塘id': 'count',
    '提取品种': merge_species,
    '图斑编号': merge_tbid
}).reset_index()

# 9. 重命名字段
grouped = grouped.rename(columns={
    '联系方式': '联系方式',
    '池塘位置': '池塘位置',
    '塘口面积_亩': '塘口面积（亩）',
    '池塘id': '塘口数量',
    '提取品种': '养殖品种',
    '图斑编号': '图斑编号汇总'
})

# 10. 添加“区县名称”列用于分 sheet
def extract_region(addr):
    try:
        parts = str(addr).split('-')
        return parts[2] if len(parts) >= 3 else '未知区县'
    except:
        return '未知区县'

grouped['区县'] = grouped['地址'].apply(extract_region)

# 11. 输出到 Excel 文件，多 sheet
output_path = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250514\常州市信息按主体汇总.xlsx'

with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
    # 总表
    grouped.drop(columns='区县').to_excel(writer, sheet_name='总表', index=False)

    # 按区县分表
    for region, sub_df in grouped.groupby('区县'):
        sub_df = sub_df.drop(columns='区县')
        safe_sheet_name = region[:31]  # Excel sheet名不能超过31字符
        sub_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
