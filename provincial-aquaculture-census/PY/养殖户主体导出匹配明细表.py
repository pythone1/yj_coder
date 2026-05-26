import pandas as pd
import numpy as np
def extractYZPZ(df):
    '''
    提取养殖品种
    '''
    print("check df.index:")
    print(f"总长{len(df)},最大索引{df.index.max()}")
    yzxx = df['养殖品种/预计亩产量'].str.replace('斤/亩', '')
    yzxx = yzxx.str.split('，', expand=True)
    yzxx = yzxx.fillna('/')
    yzpz = pd.DataFrame(columns=yzxx.columns, index=yzxx.index)
    mcl = pd.DataFrame(columns=yzxx.columns, index=yzxx.index)
    print(f"养殖品种、亩产量拆分")
    for c in yzxx.columns:
        idx = yzxx[c] != '/'
        yzpz.loc[idx, c] = yzxx.loc[idx, c].str.split(':', expand=True)[0]
        mcl.loc[idx, c] = yzxx.loc[idx, c].str.split(':', expand=True)[1]

    yzpz = yzpz.fillna('/')
    mcl = mcl.fillna(0)
    mcl = mcl.to_numpy().astype('float')
    yzpz_unq = np.unique(yzpz.to_numpy())
    n = yzpz_unq.shape[0] - 1
    print(f"共{n}个品种")
    for i, pz in enumerate(yzpz_unq[yzpz_unq != '/']):
        print(f"{i + 1}/{n}:{pz}")
        pz_idx = np.argwhere(yzpz == pz)
        print(pz_idx)
        df.loc[df.index[pz_idx[:, 0]], f'{pz}亩产量(斤/亩)'] = mcl[yzpz == pz]

    df['总产量(斤/亩)'] = df[df.columns[0 - n:]].sum(axis=1)
    df['养殖品种数量'] = (df[df.columns[-1 - n:-1]] >= 0).sum(axis=1)
    return df, yzpz_unq


rawpath = r'E:\江苏省养殖池塘上图入库项目\填报数据统计\13个县4条鱼主体统计\7月4日'
os.chdir(rawpath)
df_mcl = pd.read_excel('高邮市0704.xlsx')
df = df_mcl.copy()

# 区分淡海水品种
npz = ['其他种类', '南美白对虾', '螺', '鲈鱼']

for p in npz:
    idx0 = df['养殖品种/预计亩产量'].str.contains(p)
    if len(df.loc[idx0, '水体类型']) > 0:
        stlx = df.loc[idx0, '水体类型'].unique()
        for s in stlx[stlx != '/']:
            idx = (df['水体类型'] == s) & (idx0)
            df.loc[idx, '养殖品种/预计亩产量'] = df.loc[idx, '养殖品种/预计亩产量'].str.replace(p, f"{s}{p}")
# 计算亩产量
df, yzpz_unq = extractYZPZ(df)

df['面积_亩'] = df['图斑面积'] * 0.0015

# 计算指定品种总产量
if '鳊鲂亩产量(斤/亩)' in df.columns:
    idx1 = df['鳊鲂亩产量(斤/亩)'] >= 0
    df.loc[idx1, '鳊鲂产量'] = df.loc[idx1, '鳊鲂亩产量(斤/亩)'] * df.loc[idx1, '面积_亩']
if '鲫鱼亩产量(斤/亩)' in df.columns:
    idx2 = df['鲫鱼亩产量(斤/亩)'] >= 0
    df.loc[idx2, '鲫鱼产量'] = df.loc[idx2, '鲫鱼亩产量(斤/亩)'] * df.loc[idx2, '面积_亩']
if '淡水鲈鱼亩产量(斤/亩)' in df.columns:
    idx3 = df['淡水鲈鱼亩产量(斤/亩)'] >= 0
    df.loc[idx3, '淡水鲈鱼产量'] = df.loc[idx3, '淡水鲈鱼亩产量(斤/亩)'] * df.loc[idx3, '面积_亩']
if '泥鳅亩产量(斤/亩)' in df.columns:
    idx4 = df['泥鳅亩产量(斤/亩)'] >= 0
    df.loc[idx4, '泥鳅产量'] = df.loc[idx4, '泥鳅亩产量(斤/亩)'] * df.loc[idx4, '面积_亩']

df_tj = df.copy()

# 按指定字段划分主体并统计数据
result = df_tj.groupby(['养殖经营人名称', '身份证号', '统一社会信用代码', '联系方式', '地址']).agg({
    "养殖经营人名称": "first",  # 或 "max"/"min"（如果身份证号不同，需去重逻辑）
    "联系方式": "first",
    "身份证号": "first",
    "统一社会信用代码": "first",
    "地址": "first",
    "面积_亩": "sum",
    "鳊鲂产量": "sum",
    "淡水鲈鱼产量": "sum",
    "泥鳅产量": "sum",
    "鲫鱼产量": "sum"
})

result['养殖品种'] = ''

# 根据产量得出养殖品种
if '鳊鲂产量' in result.columns:
    idx1 = result['鳊鲂产量'] > 0
    result.loc[idx1, '养殖品种'] += '鳊鲂;'
if '淡水鲈鱼产量' in result.columns:
    idx2 = result['淡水鲈鱼产量'] > 0
    result.loc[idx2, '养殖品种'] += '淡水鲈鱼;'
if '鲫鱼产量' in result.columns:
    idx3 = result['鲫鱼产量'] > 0
    result.loc[idx3, '养殖品种'] += '鲫鱼;'
if '泥鳅产量' in result.columns:
    idx4 = result['泥鳅产量'] > 0
    result.loc[idx4, '养殖品种'] += '泥鳅;'

idx1 = result['面积_亩'] >= 5
idx2 = result['养殖品种'].str.contains(';')
idx = idx1 & idx2
result1 = result[idx]

# 主体清单导出
result1.to_excel(os.path.join("高邮市四条鱼主体0704.xlsx"))

# 获取地址信息，并定义统计层级
address = result['地址'].str.split('-', expand=True)
address['区镇'] = address[2] + '-' + address[3]
address_unq = np.unique(address['区镇'].tolist())
address_unq

# 创建统计表
row_index = address_unq
column_index = ['鳊鲂', '鲫鱼', '淡水鲈鱼', '泥鳅', '合计']
result_tj = pd.DataFrame(index=row_index, columns=column_index)

# 筛选统计数据
for j in address_unq:
    for i in ['鳊鲂', '鲫鱼', '淡水鲈鱼', '泥鳅', '合计']:
        if i == '合计':
            idx = result['养殖品种'].str.contains(';')
            idx2 = result['面积_亩'] >= 5
            idx3 = result['地址'].str.contains(j)
            result_tj.loc[j, i] = len(result[idx & idx2 & idx3])
        else:
            idx = result['养殖品种'].str.contains(i)
            idx2 = result['面积_亩'] >= 5
            idx3 = result['地址'].str.contains(j)
            result_tj.loc[j, i] = len(result[idx & idx2 & idx3])

# 统计数据导出
result_tj.to_excel(os.path.join("高邮市四鱼主体数量0704.xlsx"))

output_path = "0704匹配结果.xlsx"  # 输出文件路径
# ===== 关键词列表 =====
keywords = ["鲫鱼", "鳊鲂", "泥鳅", "鲈鱼",""]

# ===== 读取数据 =====
df_a = df_mcl
df_b = result1

# ===== 筛选 A 表中品种字段包含关键词的数据 =====
mask = df_a["养殖品种/预计亩产量"].astype(str).apply(lambda x: any(k in x for k in keywords))
filtered_a = df_a[mask].copy()


# ===== 构建匹配键 =====
def make_key(df):
    return df[["养殖经营人名称", "联系方式", "身份证号", "统一社会信用代码", "地址"]].astype(str).agg("|".join, axis=1)


filtered_a["match_key"] = make_key(filtered_a)
df_b["match_key"] = make_key(df_b)

# ===== 匹配：从 A 中选出匹配 B 的数据 =====
matched_keys = set(df_b["match_key"])
matched_a = filtered_a[filtered_a["match_key"].isin(matched_keys)].copy()
# ===== 提取“乡镇”信息 =====
matched_a["乡镇"] = matched_a["地址"].astype(str).str.split("-").str[3]
# ===== 删除辅助列并保存结果 =====
matched_a.drop(columns=["match_key"], inplace=True)
matched_a.to_excel(output_path, index=False)

