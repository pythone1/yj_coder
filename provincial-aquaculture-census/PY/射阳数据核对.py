import os,glob,re
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import math
from shapely import wkt
import geopandas as gpd
from shapely.ops import unary_union
from lxml import etree
from pykml.factory import KML_ElementMaker as KML
import folium
import folium.plugins
import unicodedata
import dimsim
from datetime import datetime, timedelta
import openpyxl
def pipei(filtered,df,lx):
    filtered["match_key"] = make_key(filtered)
    df["match_key"] = make_key(df)
    # ===== 匹配：从 A 中选出匹配 B 的数据 =====
    matched_keys = set(df["match_key"])
    matched_a = filtered[filtered["match_key"].isin(matched_keys)].copy()
    matched_a2 = filtered[~filtered["match_key"].isin(matched_keys)].copy()
    # ===== 提取“乡镇”信息 =====
    matched_a["所在乡镇"] = matched_a["地址"].astype(str).str.split("-").str[3]
    if lx=='七鱼':
        matched_a["变更理由"]=''
        matched_a.drop(columns=["match_key"], inplace=True)
        matched_a = matched_a[['养殖经营人名称', '身份证号', '统一社会信用代码', '养殖主体类型', '地址', '所在乡镇', '联系人', '联系方式',
                                   '养殖品种/预计亩产量', '图斑编号', '面积_亩','池塘所有权','池塘所有权人名称','池塘所有权人证件号码','用途','变更理由']]
    else:
        matched_a.drop(columns=["match_key"], inplace=True)
        matched_a = matched_a[['养殖经营人名称', '身份证号', '统一社会信用代码', '养殖主体类型', '地址', '所在乡镇', '联系人', '联系方式',
                                   '养殖品种/预计亩产量', '图斑编号', '面积_亩','池塘所有权','池塘所有权人名称','池塘所有权人证件号码','用途']]

    return matched_a,matched_a2

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

# ===== 构建匹配键 =====
def make_key(df):
    return df[["养殖经营人名称", "联系方式", "身份证号", "统一社会信用代码", "地址"]].astype(str).agg("-".join, axis=1)


rawpath = r'E:\江苏省养殖池塘上图入库项目\填报数据统计\13个县4条鱼主体统计\7月新\0717建湖'
os.chdir(rawpath)
df_mcl=pd.read_excel('建湖0717.xlsx')
# df_mcl=pd.read_excel('金湖县0409.xlsx')#,skiprows=1

idx2=df_mcl['图斑面积']!='/'
idx22=df_mcl['图斑面积']=='/'
df_mcl['面积_亩']=''
df_mcl.loc[idx2,'面积_亩']=df_mcl.loc[idx2,'图斑面积'].astype(float)*0.0015
# df_mcl.loc[idx22,'面积_亩']=0.001

# 提取成品养殖、有面积的数据
# idx1=df_mcl['用途'].str.contains('成品养殖')|df_mcl['用途'].str.contains('苗种培育')
idx1=df_mcl['用途'].str.contains('成品养殖')
idx2=df_mcl['图斑面积']!='/'
idx=idx1&idx2
df=df_mcl[idx].copy()

# 按指定字段划分原始信息表中主体并统计数据
df_z=df_mcl.copy()
result_z = df_z.groupby(['养殖经营人名称','身份证号','统一社会信用代码','联系方式','地址']).agg({
    "养殖经营人名称": "first",
    "联系方式": "first",
    "身份证号": "first",
    "统一社会信用代码": "first",
    "地址": "first",
    '图斑编号':list,
    })
# 区分淡海水品种
npz = ['其他种类','南美白对虾','螺','鲈鱼']

for p in npz:
        idx0 = df['养殖品种/预计亩产量'].str.contains(p)
        if len(df.loc[idx0,'水体类型'])>0:
            stlx = df.loc[idx0,'水体类型'].unique()
            for s in stlx[stlx!='/']:
                idx = (df['水体类型']==s) & (idx0)
                df.loc[idx,'养殖品种/预计亩产量'] = df.loc[idx,'养殖品种/预计亩产量'].str.replace(p,f"{s}{p}")

# 提取各品种亩产量
df,yzpz_unq= extractYZPZ(df)

# 计算指定品种总产量
pzlist=['鳊鲂','鲫鱼','淡水鲈鱼','泥鳅','黄鳝','蛙','乌鳢']
# pzlist=['黄鳝','蛙','乌鳢']
for pz in pzlist:
    if pz+'亩产量(斤/亩)' in df.columns:
        idx1=df[pz+'亩产量(斤/亩)']>=0
        df.loc[idx1,pz+'产量']=df.loc[idx1,pz+'亩产量(斤/亩)']*df.loc[idx1,'面积_亩']

df_tj=df.copy()
# 按指定字段划分主体并统计数据
result = df_tj.groupby(['养殖经营人名称','身份证号','统一社会信用代码','联系方式','地址']).agg({
    "养殖经营人名称": "first",  # 或 "max"/"min"（如果身份证号不同，需去重逻辑）
    "联系方式": "first",
    "身份证号": "first",
    "统一社会信用代码": "first",
    "地址": "first",
    "面积_亩": "sum",
    "鳊鲂产量": "sum",
    "淡水鲈鱼产量": "sum",
    "鲫鱼产量": "sum",
    "泥鳅产量": "sum",

    "图斑编号":list
    })

result['养殖品种']=''

for pz in pzlist:
    if pz+'产量' in result.columns:
        idx1=result[pz+'产量']>0
        result.loc[idx1,'养殖品种']+=pz+';'

# 不筛面积主体清单
idx2=result['养殖品种'].str.contains(';')
result2=result[idx2].copy()
result2['所属乡镇']=result2['地址'].str.split('-',expand=True)[3]
len(result2)
#
# # 不筛面积除指定品种外，其他主体清单
# idx3=~result['养殖品种'].str.contains(';')
# result3=result[idx3].copy()
# 主体清单导出
result2.to_excel(os.path.join("溧阳成品养殖、苗种培育七条鱼主体0718.xlsx"))

# 获取地址信息，并定义统计层级
address=result['地址'].str.split('-',expand=True)
address['区镇']=address[2]+'-'+address[3]
address_unq=np.unique(address[2].tolist())
# address_unq=np.unique(address['区镇'].tolist())


# 创建统计表
row_index=address_unq
column_index=['鳊鲂','鲫鱼','淡水鲈鱼','泥鳅','黄鳝','蛙','乌鳢','合计']
result_tj = pd.DataFrame(index=row_index, columns=column_index)
# 筛选统计数据
# 创建统计表
for j in address_unq:
    for i in ['鳊鲂','鲫鱼','淡水鲈鱼','泥鳅','黄鳝','蛙','乌鳢','合计']:
        if i=='合计':
            idx=result['养殖品种'].str.contains(';')
            idx3=result['地址'].str.contains(j)
            result_tj.loc[j,i]=len(result[idx&idx3])
        elif i in ['鳊鲂','鲫鱼','淡水鲈鱼','泥鳅','黄鳝','蛙','乌鳢']:
            idx=result['养殖品种'].str.contains(i)
            idx3=result['地址'].str.contains(j)
            result_tj.loc[j,i]=len(result[idx&idx3])
# 统计数据导出
result_tj.to_excel(os.path.join("淮安市七鱼主体数量0721.xlsx"))



# 原始数据匹配
# ===== 参数配置 =====
output_path = "七鱼清单.xlsx"  # 输出文件路径
output_path2 = "其他清单.xlsx"
output_path3 = "异常数据.xlsx"# 输出文件路径
df_b = result2.copy() # 匹配不同结果表格
# df_c = result.copy()# 相同用途其他
df_c = result_z.copy() # 其他所有


# ===== 关键词列表 =====其他所有
keywords = ["鲫鱼", "鳊鲂", "泥鳅", "鲈鱼", "黄鳝", "蛙","乌鳢"] #, "黄鳝", "蛙"
# ===== 读取数据 =====
# idx1=df_mcl['用途'].str.contains('成品养殖')|df_mcl['用途'].str.contains('苗种培育')
idx1=df_mcl['用途'].str.contains('成品养殖')
df_a = df_mcl[idx1].copy()
# df_a2 = df_mcl.copy()
# ===== 筛选 A 表中品种字段包含关键词的数据 =====
mask = df_a["养殖品种/预计亩产量"].astype(str).apply(lambda x: any(k in x for k in keywords))
filtered_a = df_a[mask].copy()

# mask2 = df_a2["养殖品种/预计亩产量"].astype(str).apply(lambda x: not any(k in x for k in keywords))
# filtered_c = df_a2[mask2].copy()
common_index = df_mcl.index.intersection(filtered_a.index)
filtered_c = df_mcl.drop(common_index)

# ===== 关键词列表 =====相同用途其他
# keywords = ["鲫鱼", "鳊鲂", "泥鳅", "鲈鱼", "黄鳝", "蛙","乌鳢"] #, "黄鳝", "蛙"
# # ===== 读取数据 =====
# idx1=df_mcl['用途'].str.contains('成品养殖')
# df_a = df_mcl[idx1].copy()
# # ===== 筛选 A 表中品种字段包含关键词的数据 =====
# mask = df_a["养殖品种/预计亩产量"].astype(str).apply(lambda x: any(k in x for k in keywords))
# filtered_a = df_a[mask].copy()
#
# # mask2 = df_a["养殖品种/预计亩产量"].astype(str).apply(lambda x: not any(k in x for k in keywords))
# # filtered_c = df_a[mask2].copy()
# common_index = df_a.index.intersection(filtered_a.index)
# filtered_c = df_a.drop(common_index)

matched_a,matched_a2=pipei(filtered_a,df_b,lx='七鱼')
matched_a.to_excel(output_path)
matched_a2["所在乡镇"] = matched_a2["地址"].astype(str).str.split("-").str[3]
matched_a2 = matched_a2[['养殖经营人名称', '身份证号', '统一社会信用代码', '养殖主体类型', '地址', '所在乡镇', '联系人', '联系方式',
                                   '养殖品种/预计亩产量', '图斑编号', '面积_亩','池塘所有权','池塘所有权人名称','池塘所有权人证件号码','用途']]
matched_a2.to_excel(output_path3)

address=matched_a['地址'].str.split('-',expand=True)
address_unq=np.unique(address[2].tolist())
address_unq1=address_unq[address_unq!='其他区域']
idx1=address[3].str.contains('其他区域')
address2=address[idx1].copy()
address_unq2=np.unique(address2[4].tolist())

address3=matched_c['地址'].str.split('-',expand=True)
address_unq3=np.unique(address3[2].tolist())

address_unq