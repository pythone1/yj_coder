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
        df.loc[pz_idx[:, 0], f'{pz}亩产量(斤/亩)'] = mcl[yzpz == pz]

    return df, yzpz_unq



def process_excel(file_path, output_path):
    df = pd.read_excel(file_path)
    # 1. 筛选出包含“对应同一图斑”的数据
    mask = df['位置疑点'].str.contains('对应同一图斑', na=False)
    filtered_df = df[mask]

    # 2. 按“位置疑点”内容进行分组
    grouped = filtered_df.groupby('位置疑点')

    # 3. 遍历分组，检查“养殖状态”是否全是“未使用”
    preserved_positions = set()  # 记录未被清空的“位置疑点”
    for group_name, group in grouped:
        if all(group['养殖状态'] == '未使用'):
            df.loc[df['位置疑点'] == group_name, '位置疑点'] = ''  # 清空该组的“位置疑点”
        else:
            preserved_positions.add(group_name)  # 记录未被清空的“位置疑点”

    # 4. 清空“养殖状态”为“未使用”的相关疑点列，但保留前面未清空的“位置疑点”
    columns_to_clear = ['名称疑点', '承包期限疑点', '身份证号疑点', '排口疑点', '疑点信息']
    df.loc[df['养殖状态'] == '未使用', columns_to_clear] = ''
    # 仅清空那些不在 preserved_positions 中的“位置疑点”
    df.loc[(df['养殖状态'] == '未使用') & (~df['位置疑点'].isin(preserved_positions)), '位置疑点'] = ''

    # 保存处理后的文件
    df.to_excel(output_path, index=False)

# 调用示例
process_excel(r"E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250422\无锡市-20250422120945-无锡市-疑点统计表-全\总表.xlsx", r"E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250422\无锡市-20250422120945-无锡市-疑点统计表-全\20250422无锡市疑点信息.xlsx")
