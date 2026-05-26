import pandas as pd

BZ = '多点对应同一图斑'
df_concat = pd.read_excel(r'E:\全省养殖池溏上图入库普查\疑点核查\20250522\南京市\南京市.xlsx')
df_concat[BZ] = ''
for c in df_concat.columns:
    df_concat.loc[df_concat[c] == '/', c] = ''
df_concat = df_concat.fillna('')
# 重复图斑ID（所有重复记录）
df_dup = df_concat[df_concat['图斑id'] != ''].copy()
dup_ids = df_dup['图斑id'][df_dup['图斑id'].duplicated(keep=False)]

# 所有重复图斑的记录
idx = df_concat[df_concat['图斑id'].isin(dup_ids)].copy()

for gid, group in idx.groupby('图斑id'):
    statuses = set(group['养殖状态'].dropna())
    states = set(group['状态'].dropna())

    # 1️⃣ 同时填报“养殖”和“未使用”
    if '养殖' in statuses and '未使用' in statuses:
        df_concat.loc[group.index, BZ] += '图斑重复（同时填报养殖与未使用），'
        continue  # 不再往下判断

    # 2️⃣ 均为“养殖”
    if statuses == {'养殖'}:
        # 检查是否包含“已返回”
        group_wo_returned = group[~group['状态'].str.contains('已返回', na=False)]
        if len(group_wo_returned) == 1:
            df_concat.loc[group.index, BZ] += '图斑重复（均为养殖，可通过删除已返回数据解决），'
        else:
            df_concat.loc[group.index, BZ] += '图斑重复（均填报养殖），'
        continue

    # 3️⃣ 均为“未使用”
    if statuses == {'未使用'}:
        df_concat.loc[group.index, BZ] += '图斑重复（均为未使用），'
        continue

    # 其他情况（比如出现不明状态）
    df_concat.loc[group.index, BZ] += '图斑重复（其他），'

# 只保留被标记的数据
df_concat = df_concat[df_concat[BZ] != '']

# 输出总表
df_concat.to_excel(r'E:\全省养殖池溏上图入库普查\疑点核查\20250522\南京市\20250522南京市多点对应同一图斑.xlsx', index=False)
