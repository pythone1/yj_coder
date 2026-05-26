import pandas as pd

# 读取 Excel
input_path = r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250710\20250710丹阳市.xlsx"  # 修改为你的实际路径
df = pd.read_excel(input_path)

# 初步筛选
df = df[df['养殖方式'] != '渔光一体']
df = df[df['养殖状态'] == '养殖']

# 处理养殖品种，剔除只含虾蟹的
def filter_species(value):
    if pd.isna(value):
        return False
    species = [item.split(':')[0] for item in str(value).split('，')]
    has_shrimp_crab = any(('虾' in s or '蟹' in s) for s in species)
    has_other = any(not ('虾' in s or '蟹' in s) for s in species)
    return not (has_shrimp_crab and not has_other)  # 剔除只有虾蟹的

df = df[df['养殖品种/预计亩产量'].apply(filter_species)]

# 拆分地址字段
def extract_address_parts(addr):
    parts = str(addr).split('-')
    town = parts[3] if len(parts) > 3 else ''
    village = parts[4] if len(parts) > 4 else ''
    return pd.Series([town, village])

df[['镇', '村']] = df['地址'].apply(extract_address_parts)

# 分组识别养殖主体并计算总面积
group_fields = ['镇', '村', '养殖经营人名称', '身份证号', '统一社会信用代码', '联系方式']
df['主体面积'] = df.groupby(group_fields)['图斑面积(亩)'].transform('sum')

# 筛选主体面积大于5亩的原始数据
df_filtered = df[df['主体面积'] > 5]

# 主表输出字段
main_columns = ['镇', '村', '养殖经营人名称', '身份证号', '统一社会信用代码',
                '联系人', '联系方式', '养殖品种/预计亩产量', '图斑编号', '图斑面积(亩)']

# 输出第一张表：满足条件的原始数据
df_filtered[main_columns].to_excel(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250710\0710丹阳市养殖主体明细表（主体5亩以上剔除虾蟹塘渔光一体）.xlsx", index=False)

# 第二张表：主体统计
df_subject = df_filtered[group_fields].drop_duplicates()
df_stat = df_subject.groupby('镇').size().reset_index(name='主体数量')

# 添加合计行
total_row = pd.DataFrame([{'镇': '合计', '主体数量': df_stat['主体数量'].sum()}])
df_stat = pd.concat([df_stat, total_row], ignore_index=True)

# 输出第二张表
df_stat.to_excel(r"E:\全省养殖池溏上图入库普查\养殖信息统计\20250710\0710丹阳市养殖主体统计表（主体5亩以上剔除虾蟹塘渔光一体）.xlsx", index=False)
