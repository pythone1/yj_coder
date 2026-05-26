"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: pond_extraction.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os,glob
import zipfile

import pandas as pd
import numpy as np
from datetime import datetime
import geopandas as gpd

DPTH = r'E:\项目数据\江苏省一池一档水产养殖基本情况普查项目\数据统计\data'

def unzipfiles(z_file,ctxx_pth):
    '''
    加压池塘信息文件到日期目录
    :param z_file: 压缩文件
    :param ctxx_pth: 解压路径
    :return:
    '''
    try:
        with zipfile.ZipFile(z_file,'r',metadata_encoding='gbk') as zf:
            zf.extractall(ctxx_pth)
        return True
    except:
        return False
    

def readCTXX(ctxx_pth):
    '''
    读池塘信息文件
    :param ctxx_pth: str
    :return:
    '''
    files = glob.glob(f"{ctxx_pth}\\*")
    df_list = []
    for f in files:
        df_list.append(pd.read_csv(f,skiprows=1,dtype='str',sep=',',usecols=range(54)))
    df = pd.concat(df_list,axis=0,ignore_index=True)

    # 删除错位/无效数据
    df = deleteInvalidData(df)
    df.reset_index(inplace=True)

    # 缺图斑面积、图斑编号字段
    ctlk_file = r'E:\项目数据\江苏省一池一档水产养殖基本情况普查项目\数据统计\data\信息统计表-20250411-池塘图斑.gpkg'
    ctlk = gpd.read_file(ctlk_file)
    df = pd.merge(df,ctlk.loc[:,['图斑id','TBID','图斑面积']],on=['图斑id'],how='left')

    return df

def extractYZPZ(df):
    '''
    养殖品种/预计亩产量按养殖品种拆分对应亩产量列
    :param df: pd.DataFrame
    :return: pd.DataFrame
    '''
    yzxx = df['养殖品种/预计亩产量'].str.replace('斤/亩', '')
    yzxx = yzxx.str.split('，', expand=True)
    yzxx = yzxx.fillna('/')
    yzpz = pd.DataFrame(columns=yzxx.columns, index=yzxx.index)
    mcl = pd.DataFrame(columns=yzxx.columns, index=yzxx.index)
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

    return df

def deleteTestData2(df,field,keywords):
    '''
    按关键字keywords模糊匹配删除测试数据
    '''
    for k in keywords:
        df[field] = df[field].str.replace(k,'测试')

    # 删除测试数据
    values = df[field].values.tolist()
    
    test_idx = np.array([True if '测试' in v else False for v in values])
    df = df[~test_idx]

    return df 

def deleteInvalidData(df):
    '''
    删除无效数据
    df: pd.DataFrame 填报数据表
    '''
    # 删除无效数据
    n1 = len(df)
    df = df[~df['状态'].isnull()]
    df = df[~df['池塘位置'].isnull()]
    df = df[df['池塘位置']!='/']
    df = df[df['池塘位置'].str.contains('，')]
    n2 = len(df)
    print(f"删除{n1-n2}个无效数据（错位）")

    # # 删除审核驳回、未上报
    # df = df[(~df['状态'].str.contains('未上报')) & (~df['状态'].str.contains('已返回'))]
    # 删除审核驳回、未上报
    df = df[~df['状态'].str.contains('未上报')]
    n3 = len(df)
    print(f"删除{n2-n3}个未上报数据")
 
    # 删除测试数据
    for c in ['养殖经营人名称','池塘所有权人名称']:
        # df = deleteTestData1(df, c, ['张三', '李四', '王五', '123'])  # 完全匹配删除
        # df = deleteTestData2(df, c, ['李想', '朱曦', '季鹏程', '测试'])  # 模糊匹配删除
        df = deleteTestData2(df, c, ['测试'])  # 模糊匹配删除
    n4 = len(df)
    print(f"删除{n3-n4}个测试数据")
    
    return df

def normalizeDF(df):
    '''
    池塘信息表规范化处理：
    地址拆分为：'市','区县','镇','村'；
    承包期限拆分为：'承包开始时间','承包结束时间'
    养殖品种/预计亩产量按养殖品种拆分对应亩产量列
    :param df: pd.DataFrame
    :return: pd.DataFrame
    '''
    # 地址
    dz = df['地址'].str.split('-', expand=True)
    idx = ~dz[5].isnull()
    dz.loc[idx, 3] = dz.loc[idx, 3] + '-' + dz.loc[idx, 4]
    dz.loc[idx, 4] = dz.loc[idx, 5]
    dz = dz.loc[:, 1:4]
    dz.columns = ['市', '区县', '镇', '村']
    df = pd.concat([df.loc[:, '主体id':'地址'], dz, df.loc[:, '养殖证编号':]], axis=1)

    # 承包期限
    cbqx = df['承包期限'].str.split(' : ', expand=True)
    cbqx.columns = ['承包开始时间', '承包结束时间']
    cbqx = cbqx.fillna('/')
    df = pd.concat([df.loc[:, '主体id':'承包期限'], cbqx, df.loc[:, '合同面积':]], axis=1)

    # 养殖品种重名的加水体类型为前缀重命名
    npz = ['其他种类', '南美白对虾', '螺', '鲈鱼']
    for p in npz:
        idx0 = df['养殖品种/预计亩产量'].str.contains(f"{p}:")
        stlx = df.loc[idx0, '水体类型'].unique()
        for s in stlx[stlx != '/']:
            idx = (df['水体类型'] == s) & (idx0)
            df.loc[idx, '养殖品种/预计亩产量'] = df.loc[idx, '养殖品种/预计亩产量'].str.replace(p, f"{s}{p}")

    # 养殖品种、产量(顺便删除重名不重要字段)
    df = extractYZPZ(df)
    del_cols = []
    for c in df.columns:
        if c.endswith('亩产量(斤/亩)'):
            pz = c.replace('亩产量(斤/亩)', '')
            nc = f'{pz}产量(吨)'
            df[nc] = (df[c] * df['图斑面积'] / 2000).round(3)
        if ('时间' in c) or ('来源' in c) or ('Unnamed' in c):
            del_cols.append(c)
    df.drop(columns=list(set(del_cols)), inplace=True)

    # 有重名品种的新建字段作为汇总
    for p in npz:
        ini_fieds = [f"{p}产量(吨)",f"淡水{p}产量(吨)",f"海水{p}产量(吨)",f"咸水{p}产量(吨)"]
        for f in ini_fieds:
            if f not in df.columns:
                ini_fieds.remove(f)
        df[f"所有{p}产量(吨)"] = df.loc[:,ini_fieds].sum(axis=1)   
        # 无值的置空
        idx = df.loc[:,ini_fieds].isnull().all(axis=1)
        df.loc[idx,f"所有{p}产量(吨)"] = None

    # 养殖经营人证件号码
    df['养殖经营人证件号码'] = df['身份证号'].str.replace('/', '') + df['统一社会信用代码'].str.replace('/', '')

    # 重命名
    df['TBID'] = df['TBID'].str.replace(',', '')
    df = df.rename(columns={'TBID': '图斑编号'})

    # 原数据表养殖状态有缺失，按用途更新
    idx = df['用途']=='/'
    df.loc[idx,'养殖状态'] = '未使用'
    df.loc[~idx,'养殖状态'] = '养殖'

    return df

def sumarizeCTXX(df,groupfields,yzpz):
    '''
    按给定字段汇总养殖信息
    :param df:
    :param groupby: list[str,str,..] 分组字段
    :param yzpz: list[str,str,..] 养殖品种
    :param outpath: str 结果保存路径
    :return:
    '''
    fields = groupfields.copy()

    if yzpz is None:
        cols = df.columns
        idx = [True if '产量(吨)' in c else False for c in cols]
        yzpz = cols[idx]
        yzpz = [y.replace('产量(吨)','') for y in yzpz]
        print(f"统计所有养殖品种，共{len(yzpz)}个")
    
    # 图斑面积按养殖品种拆分
    for y in yzpz:
        cl_field = f"{y}产量(吨)"
        mj_filed = f"{y}图斑面积"
        idx = (~df[cl_field].isnull())
        df.loc[idx,mj_filed] = df.loc[idx,"图斑面积"]
        fields.extend([mj_filed,cl_field])

    # 提取字段
    df = df.loc[:, fields]

    # 提取行
    idx = (~df[f"{yzpz[0]}产量(吨)"].isnull())
    for i in range(1, len(yzpz)):
        idx = idx | (~df[f"{yzpz[i]}产量(吨)"].isnull())
    df = df.loc[idx, :]

    # 分组统计字段
    yzpz_f = [f"{y}产量(吨)" for y in yzpz]
    cl_f = [f"{y}图斑面积" for y in yzpz]
    cnt_f = [item for pair in zip(cl_f, yzpz_f) for item in pair]
    # cnt_f.append('图斑面积')

    grouped = df.groupby(groupfields)
    tj = grouped[cnt_f].sum()
    # tj['养殖主体类型'] = grouped['养殖主体类型'].unique().map(lambda x: x[0])
    for i in range(len(groupfields)):
        tj.insert(loc=i, column=groupfields[i], value=tj.index.get_level_values(i))
    
    return tj


if __name__ == '__main__':
    # 池塘信息表 
    zfile = f'{DPTH}\\信息表.zip'
    groupfields = ['养殖经营人名称', '养殖经营人证件号码', '地址','养殖主体类型']
    # yzpz = ['鳊鲂', '泥鳅', '鲫鱼', '所有鲈鱼']
    yzpz = ['所有鲈鱼']
    # yzpz = None


    # 当日数据路径
    ctxx_pth = f"{DPTH}\\{datetime.now().strftime('%Y%m%d')}"
    outpath = outpath = f"{ctxx_pth}-out"
    os.makedirs(ctxx_pth,exist_ok=True)
    os.makedirs(outpath,exist_ok=True)

    # 池塘信息文件读取和处理
    ctxx_file = f"{outpath}\\池塘信息表.csv"
    if os.path.exists(ctxx_file):
        ctxx = pd.read_csv(ctxx_file)
    else:
        # 解压池塘信息文件
        unzipfiles(zfile,ctxx_pth)
        ctxx = readCTXX(ctxx_pth)

        # 池塘信息表格式处理
        ctxx = normalizeDF(ctxx)
        ctxx.to_csv(f"{outpath}\\池塘信息表.csv",index=False)
        print(ctxx['主体id'].nunique())

    # 数据统计
    tj = sumarizeCTXX(ctxx,groupfields,yzpz)

    # 结果导出
    outfile = f"{outpath}\\分组统计{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
    tj.to_excel(outfile, index=False)

    # file = r'E:\项目数据\江苏省一池一档水产养殖基本情况普查项目\数据统计\data\20250408-out\池塘信息表.csv'
    # df = pd.read_csv(file)

    # groupfields = ['市','区县', '镇', '村']

    # n = '养殖'
    # df1 = df[df['养殖状态']==n]
    # grouped1 = df1.groupby(by=groupfields)
    # tj1 = pd.DataFrame()
    # tj1[f'{n}主体id'] = grouped1['主体id'].nunique()
    # tj1[f'{n}图斑面积'] = grouped1['图斑面积'].sum()

    # n = '未使用'
    # df2 = df[df['养殖状态']==n]
    # grouped2 = df2.groupby(by=groupfields)
    # tj2 = pd.DataFrame()
    # tj2[f'{n}主体id'] = grouped2['主体id'].nunique()
    # tj2[f'{n}塘口数量'] = grouped2['图斑编号'].nunique()
    # tj2[f'{n}图斑面积'] = grouped2['图斑面积'].sum()
    # tj3 = pd.concat([tj2,tj1],axis=1)

    # for i in range(len(groupfields)):
    #     tj3.insert(loc=i, column=groupfields[i], value=tj3.index.get_level_values(i))
    # tj3.to_excel(r'E:\项目数据\江苏省一池一档水产养殖基本情况普查项目\数据统计\data\20250408-out\tmp3.xlsx',index=False)

    # file2 = r'E:\项目数据\江苏省一池一档水产养殖基本情况普查项目\数据统计\data\池塘信息表-20250404-池塘图斑.gpkg'
    # gdf = gpd.read_file(file2)

    # gdf1 = gdf[gdf['填报状态']=='已填报养殖']
    # gdf2 = gdf[gdf['填报状态']=='已填报非养殖']

    # data0 = [len(gdf),gdf['图斑面积'].sum()/10000]
    # data1 = [len(gdf1),gdf1['图斑面积'].sum()/10000]
    # data2 = [len(gdf2),gdf2['图斑面积'].sum()/10000]
    # print('所有')
    # print(data0)
    # print('已填报养殖')
    # print(data1)
    # print('已填报非养殖')
    # print(data2)

    # print('1')

