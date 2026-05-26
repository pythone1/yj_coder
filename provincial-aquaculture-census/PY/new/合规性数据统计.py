import pandas as pd

# 读取 Excel 文件
df = pd.read_excel(r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\20250516合规性检查（错误）重算面积.xlsx")

# 定义统计结果字典
results = {}
# 筛选列名
养殖状态列 = '养殖状态'
合规性检查列 = '合规性检查'
图斑ID列 = '图斑id'

# 条件1
cond1 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("养殖多点对应同一图斑|无对应图斑", na=False))
results['养殖多点对应同一图斑|无对应图斑'] = cond1.sum()

# 条件2
cond2 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("合同面积与净水面面积不能同时为空", na=False))
results['合同面积与净水面面积不能同时为空'] = cond2.sum()

# 条件3
cond3 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("池塘所有权人", na=False))
results['池塘所有权人'] = cond3.sum()

# 条件4
cond4 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("主体证件号码缺失|养殖主体身份证号缺失或不是18位|相同身份证号对应多个养殖经营人名称", na=False))
results['养殖主体身份证问题'] = cond4.sum()

# 条件5
cond5 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("养殖方式填写非法或缺失", na=False))
results['养殖方式填写非法或缺失'] = cond5.sum()

# 条件6
cond6 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("养殖水体类型填写非法或缺失", na=False))
results['养殖水体类型填写非法或缺失'] = cond6.sum()

# 条件11
cond11 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("50亩", na=False))
results['50亩未填标准化改造'] = cond11.sum()
# 条件7
cond7 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("未填写排口位置", na=False))
results['集体公司未填写排口位置'] = cond7.sum()
# 条件7
cond7 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("尾水处理工艺缺失或不合法", na=False))
results['尾水处理工艺缺失或不合法'] = cond7.sum()

# 条件7
cond7 = (df[养殖状态列] == "养殖") & (
    df[合规性检查列].str.contains("尾水净化区面积缺失", na=False))
results['尾水净化区面积缺失'] = cond7.sum()

# 条件8
cond8 = (df[养殖状态列] == "未使用") & (
    df[合规性检查列].str.contains("主体证件号码缺失", na=False))
results['未使用主体证件号码缺失'] = cond8.sum()

# 条件9 - 养殖问题图斑（多点对应同一图斑）
养殖_df = df[df[养殖状态列] == "养殖"]
dup养殖 = 养殖_df[养殖_df[合规性检查列].str.contains("养殖多点对应同一图斑", na=False)]
dup_ids_养殖 = dup养殖[图斑ID列].dropna().drop_duplicates()
results['养殖多点对应同一图斑'] = len(dup_ids_养殖)

# 剔除上述图斑后统计其他不合规
剩余养殖 = 养殖_df[~养殖_df[图斑ID列].isin(dup_ids_养殖)]
其他不合规养殖 = 剩余养殖[剩余养殖[合规性检查列].notna()]
results['养殖_其他不合规图斑数'] = len(其他不合规养殖[图斑ID列])

results['养殖问题总数'] = results['养殖多点对应同一图斑'] + results['养殖_其他不合规图斑数']

# 条件10 - 未使用问题图斑（多点对应同一图斑）
未使用_df = df[df[养殖状态列] == "未使用"]
dup未使用 = 未使用_df[未使用_df[合规性检查列].str.contains("未使用多点对应同一图斑", na=False)]
dup_ids_未使用 = dup未使用[图斑ID列].dropna().drop_duplicates()
results['未使用多点对应同一图斑'] = len(dup_ids_未使用)

# 剔除上述图斑后统计其他不合规
剩余未使用 = 未使用_df[~未使用_df[图斑ID列].isin(dup_ids_未使用)]
其他不合规未使用 = 剩余未使用[
    (剩余未使用[合规性检查列].notna()) &
    (~剩余未使用[合规性检查列].str.contains("养殖", na=False))
]
其他不合规未使用 = 其他不合规未使用[其他不合规未使用[合规性检查列].notna()]
results['未使用_其他不合规图斑数'] = len(其他不合规未使用[图斑ID列])

results['未使用问题图斑总数'] = results['未使用多点对应同一图斑'] + results['未使用_其他不合规图斑数']

# 保存统计结果
output_df = pd.DataFrame(list(results.items()), columns=["统计项目", "数量"])
output_df.to_excel(r"E:\全省养殖池溏上图入库普查\合规性检查\20250516\20250516统计结果(重算面积).xlsx", index=False)
print("统计完成，结果已保存为 统计结果.xlsx")
