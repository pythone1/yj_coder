import pandas as pd
import numpy as np
import os


def extractYZPZ(df):
    '''
    提取养殖品种和亩产量
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
        df.loc[df.index[pz_idx[:, 0]], f'{pz}亩产量(斤/亩)'] = mcl[yzpz == pz]

    df['总产量(斤/亩)'] = df[df.columns[0 - n:]].sum(axis=1)
    df['养殖品种数量'] = (df[df.columns[-1 - n:-1]] >= 0).sum(axis=1)
    return df, yzpz_unq

def make_key(df):
    return df[["养殖经营人名称", "联系方式", "身份证号", "统一社会信用代码", "地址"]].astype(str).agg("|".join, axis=1)
def process_yz_data(filepath, filename):
    '''
    主处理函数
    '''
    os.chdir(filepath)
    df_raw = pd.read_excel(filename)

    # 清理非数字面积、用途为“成品养殖”
    df = df_raw.copy()
    df = df[pd.to_numeric(df['图斑面积'], errors='coerce').notnull()]
    df = df[df['用途'] == '成品养殖']
    # 区分淡海水品种
    npz = ['其他种类', '南美白对虾', '螺', '鲈鱼']
    for p in npz:
        idx0 = df['养殖品种/预计亩产量'].str.contains(p, na=False)
        if len(df.loc[idx0, '水体类型']) > 0:
            stlx = df.loc[idx0, '水体类型'].unique()
            for s in stlx[stlx != '/']:
                idx = (df['水体类型'] == s) & (idx0)
                df.loc[idx, '养殖品种/预计亩产量'] = df.loc[idx, '养殖品种/预计亩产量'].str.replace(p, f"{s}{p}")
    # 亩产量提取
    df, yzpz_unq = extractYZPZ(df)

    # 面积计算
    df["图斑面积"] = pd.to_numeric(df["图斑面积"], errors="coerce")
    df['面积_亩'] = df['图斑面积'] * 0.0015
    df_a = df.copy()

    # 品种产量
    for fish in ['鳊鲂', '鲫鱼', '淡水鲈鱼', '泥鳅','乌鳢']:
        col = f'{fish}亩产量(斤/亩)'
        if col in df.columns:
            idx = df[col] >= 0
            df.loc[idx, f'{fish}产量'] = df.loc[idx, col] * df.loc[idx, '面积_亩']

    # 主体聚合
    df_tj = df.copy()
    result = df_tj.groupby(['养殖经营人名称', '身份证号', '统一社会信用代码', '联系方式', '地址']).agg({
        "养殖经营人名称": "first",
        "联系方式": "first",
        "身份证号": "first",
        "统一社会信用代码": "first",
        "地址": "first",
        "面积_亩": "sum",
        "鲫鱼产量": "sum",
        "鳊鲂产量": "sum",
        "淡水鲈鱼产量": "sum",
        "泥鳅产量": "sum",
        "乌鳢产量": "sum",
        "图斑编号": list
    })
    result['养殖品种'] = ''
    for fish in ['鳊鲂', '淡水鲈鱼', '鲫鱼', '泥鳅','乌鳢']:
        if f'{fish}产量' in result.columns:
            idx = result[f'{fish}产量'] > 0
            result.loc[idx, '养殖品种'] += f'{fish};'

    idx1 = result['面积_亩'] >= 0
    idx2 = result['养殖品种'].str.contains(';')
    result1 = result[idx1 & idx2]
    result1.to_excel(os.path.join(filepath, filename.replace('.xlsx', '主体清单.xlsx')))
    # 地址分层统计
    address = result['地址'].str.split('-', expand=True)
    address['区镇'] = address[2] + '-' + address[3]
    address_unq = np.unique(address['区镇'].tolist())
    result_tj = pd.DataFrame(index=address_unq, columns=['鳊鲂', '鲫鱼', '淡水鲈鱼', '泥鳅','乌鳢','合计'])
    for j in address_unq:
        for i in ['鳊鲂', '鲫鱼', '淡水鲈鱼', '泥鳅','乌鳢', '合计']:
            idx = result['地址'].str.contains(j)
            idx2 = result['面积_亩'] >= 0
            if i == '合计':
                idx3 = result['养殖品种'].str.contains(';')
                result_tj.loc[j, i] = len(result[idx & idx2 & idx3])
            else:
                idx3 = result['养殖品种'].str.contains(i)
                result_tj.loc[j, i] = len(result[idx & idx2 & idx3])
    # 导出统计表
    result_tj.to_excel(os.path.join(filepath, filename.replace('.xlsx', '主体数量统计.xlsx')))
    keywords = ["鲫鱼", "鳊鲂", "泥鳅", "鲈鱼",'乌鳢']
    df_a = df_a
    df_b = result1
    mask = df_a["养殖品种/预计亩产量"].astype(str).apply(lambda x: any(k in x for k in keywords))
    filtered_a = df_a[mask].copy()
    filtered_a["match_key"] = make_key(filtered_a)
    df_b["match_key"] = make_key(df_b)
    matched_keys = set(df_b["match_key"])
    matched_a = filtered_a[filtered_a["match_key"].isin(matched_keys)].copy()
    matched_a["所在乡镇"] = matched_a["地址"].astype(str).str.split("-").str[3]
    matched_a.drop(columns=["match_key"], inplace=True)
    matched_a = matched_a[['养殖经营人名称', '身份证号', '统一社会信用代码', '地址', '所在乡镇', '联系人', '联系方式',
                           '养殖品种/预计亩产量', '图斑编号', '面积_亩']]
    matched_a.to_excel(os.path.join(filepath, filename.replace('.xlsx', '主体清单明细表（精确到塘口）.xlsx')),index=False)

if __name__ == "__main__":
    rawpath = r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\统计\五点'
    filename = '射阳0725.xlsx'
    process_yz_data(rawpath, filename)
