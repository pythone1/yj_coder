import pandas as pd

# 读取数据
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250709\4月9日丹阳市除虾蟹外养殖主体（按照图斑统计）.xlsx')  # ← 替换为你的实际路径

group_cols = ['镇', '村', '养殖经营人名称', '身份证号', '联系方式']

# 计算每个主体的总面积
主体面积 = df.groupby(group_cols, dropna=False)['图斑面积(亩)'].sum().reset_index()
主体面积 = 主体面积.rename(columns={'图斑面积(亩)': '主体总面积'})

# 筛选面积大于5亩的主体
主体大于5 = 主体面积[主体面积['主体总面积'] > 5]

# 与原始数据合并，保留原始图斑记录
df_result = df.merge(主体大于5[group_cols], on=group_cols, how='inner')

# 保存结果
df_result.to_excel(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250709\养殖主体_总面积大于5亩.xlsx', index=False)

print("✅ 已保存：养殖主体_总面积大于5亩.xlsx")
