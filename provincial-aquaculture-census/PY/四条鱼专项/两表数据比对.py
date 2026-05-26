import pandas as pd

# 读取文件
a_path = r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\数据\高邮市\新建文件夹\水产养殖主体名录.xlsx'
b_path = r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\数据\高邮市\新建文件夹\0704下午四点半车逻镇主体数量统计.xlsx'
df_a = pd.read_excel(a_path)
df_b = pd.read_excel(b_path)

# 获取B表中养殖经营人名称集合（去重）
names_in_b = set(df_b['养殖经营人名称'].dropna().astype(str))

# 在A表新增列，判断匹配情况
df_a['是否在上图入库系统'] = df_a['养殖者姓名'].astype(str).apply(lambda x: '是' if x in names_in_b else '否')

# 可选：保存结果
df_a.to_excel(r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\数据\高邮市\新建文件夹\比对结果.xlsx', index=False)
