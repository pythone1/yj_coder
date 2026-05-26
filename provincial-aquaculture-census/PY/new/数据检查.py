import pandas as pd

# 假设你的 DataFrame 名为 df
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\合规性检查（错误） - 副本.xlsx')
# 1. 从“地址”字段中提取第二级（市）
df['市'] = df['地址'].str.split('-').str[2]

# 2. 定义各类检查的关键词
keywords = {
    '池塘所有权人身份证号不是18位': '池塘所有权人身份证号不是18位',
    '相同池塘所有权人证件号码对应多个池塘所有权人名称': '相同池塘所有权人证件号码对应多个池塘所有权人名称',
    '养殖主体身份证号缺失或不是18位': '养殖主体身份证号缺失或不是18位',
    '相同身份证号对应多个养殖经营人名称': '相同身份证号对应多个养殖经营人名称',
    '无对应图斑': '无对应图斑',
    '养殖多点对应同一图斑': '养殖多点对应同一图斑'
}

# 3. 创建每类问题的布尔列
for key, val in keywords.items():
    df[key] = df['合规性检查'].str.contains(val, na=False)

# 4. 对“养殖多点对应同一图斑”的部分，进一步判断是否填报信息一致（除池塘id外字段一致）
# 提取该类数据
multi_points = df[df['养殖多点对应同一图斑']].copy()

# 去掉“池塘id”后去重，统计重复条数（填报信息一致）
# 假设池塘id字段名是“池塘id”，如为其他名称请替换
drop_cols = ['池塘id','池塘位置','状态','疑点信息','上次拒绝原因','排口位置']
compare_cols = [col for col in df.columns if col not in drop_cols]

# 生成重复组判断字段
multi_points['dup_flag'] = multi_points.duplicated(subset=compare_cols, keep=False)
consistent_multi_points = multi_points[multi_points['dup_flag']]

# 5. 按“市”分组统计各类问题数量
result = df.groupby('市')[[*keywords.keys()]].sum().astype(int)

# 添加“养殖多点对应同一图斑-填报信息一致”列
consistent_counts = consistent_multi_points.groupby('市').size()
result['养殖多点对应同一图斑-填报信息一致'] = consistent_counts
result['养殖多点对应同一图斑-填报信息一致'] = result['养殖多点对应同一图斑-填报信息一致'].fillna(0).astype(int)
result.to_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\错误图斑按照市统计(宜兴市).xlsx')
# 查看结果
print(result)
