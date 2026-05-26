import os, glob
from datetime import datetime
import os, glob

import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.ops import unary_union
from lxml import etree
from pykml.factory import KML_ElementMaker as KML

import numpy as np
import folium
import folium.plugins
import unicodedata
import re
# from LAC import LAC
import dimsim
from datetime import datetime, timedelta
import openpyxl

SURNAME_PATH = r"E:\全省养殖池溏上图入库普查\填报进度统计\常见姓氏.txt"
XZQH = gpd.read_file(r'E:\全省养殖池溏上图入库普查\填报进度统计\JiangSu_XZQH.shp')
REGIONCODE = pd.read_excel(r'E:\全省养殖池溏上图入库普查\填报进度统计\行政编码.xlsx')


def dizhi2(result_qy):
    # 获取地址信息，并定义统计层级
    address = result_qy['地址'].str.split('-', expand=True)
    address['区县'] = address[1] + '-' + address[2]
    # address_unq=np.unique(address[2].tolist())
    address_unq = np.unique(address['区县'].tolist())
    return address_unq


def cachu(df1, df2):
    # 擦除数据
    # df1：待擦除数据表
    # df2：擦除数据
    common_index = df1.index.intersection(df2.index)
    df_cc = df1.drop(common_index)
    return df_cc


def getDulplicates(data):
    '''
    获取有重复项的值
    '''
    a, b = np.unique(data, return_counts=True)

    return a[b > 1]


def deleteInvalidData(df):
    '''
    删除无效数据
    df: pd.DataFrame 填报数据表
    '''
    # 删除无效数据
    n1 = len(df)
    df = df[~df['状态'].isnull()]
    df = df[~df['池塘位置'].isnull()]
    df = df[df['池塘位置'] != '/']
    df = df[df['池塘位置'].str.contains('，')]
    n2 = len(df)
    print(f"删除{n1 - n2}个无效数据（错位）")

    # # 删除审核驳回、未上报
    # df = df[(~df['状态'].str.contains('未上报')) & (~df['状态'].str.contains('已返回'))]
    # 删除审核驳回、未上报
    df = df[~df['状态'].str.contains('未上报')]
    n3 = len(df)
    print(f"删除{n2 - n3}个未上报数据")

    # 删除测试数据
    for c in ['养殖经营人名称', '池塘所有权人名称']:
        # df = deleteTestData1(df, c, ['李四', '王五', '123'])  # 完全匹配删除
        df = deleteTestData2(df, c, ['测试'])  # 模糊匹配删除
    n4 = len(df)
    print(f"删除{n3 - n4}个测试数据")

    return df


def status2Num(df):
    '''
    将状态转为数值型
    '''
    df.loc[df['状态'] == '待校对（村）', '状态值'] = 1
    df.loc[df['状态'] == '待校对（镇）', '状态值'] = 2
    df.loc[df['状态'] == '待校对（区县）', '状态值'] = 3
    df.loc[df['状态'] == '通过', '状态值'] = 4
    df.loc[df['状态'].str.contains('返回'), '状态值'] = 0
    df.loc[df['状态值'].isnull(), '状态值'] = -1  # 未上报，应该在deleteInvalid已删除

    return df


def df2gdf(df, lon_col, lat_col, epsg=4326):
    '''
    功能：df对象转gdf
    df: pd.DataFrame 数据表，含经纬度数据列
    lon_col: str 经度对应的列名
    lat_col: str 纬度对应的列名
    epsg: int 坐标系对应的编号，默认4326 WGS-1984
    '''
    df['wkt_str'] = 'POINT (' + df[lon_col] + ' ' + df[lat_col] + ')'

    df['geometry'] = df['wkt_str'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs='EPSG:' + str(epsg), geometry=df['geometry'])
    gdf = gdf.drop('wkt_str', axis=1)

    return gdf


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
        df.loc[df.index[pz_idx[:, 0]], f'{pz}亩产量(斤/亩)'] = mcl[yzpz == pz]

    df['总产量(斤/亩)'] = df[df.columns[0 - n:]].sum(axis=1)
    df['养殖品种数量'] = (df[df.columns[-1 - n:-1]] >= 0).sum(axis=1)
    return df


def addAttr2Plygons(ctlk, ctxx):
    '''
    给图斑增加属性信息
    '''
    try:
        ctlk = pd.merge(ctlk, ctxx.loc[:,
                              ['池塘id', '养殖经营人名称', '养殖主体类型', '状态', '状态值', '池塘所有权人名称',
                               '疑点信息', '地址', '图斑id']], on='图斑id', how='left')
    except:
        ctlk = pd.merge(ctlk.drop(columns='图斑id'), ctxx.loc[:,
                                                     ['池塘id', '养殖经营人名称', '养殖主体类型', '状态', '状态值',
                                                      '池塘所有权人名称', '疑点信息', '地址', '图斑id']], on='图斑id',
                        how='left')
    # ctlk = gpd.sjoin(ctlk, ctxx.loc[:, ['geometry', '养殖经营人名称','养殖主体类型','状态','状态值','池塘所有权人名称','疑点信息','地址','图斑id']],how='left')

    if 'ID' not in ctlk.columns:
        ctlk['ID'] = ctlk.index
    ctlk.reset_index(inplace=True, drop=True)
    ctlk.loc[ctlk['状态值'].isnull(), '状态值'] = -1  # 未填报，0为返回
    idx = ctlk.groupby('图斑id')['状态值'].idxmax().values
    ctlk = ctlk.loc[idx, :]
    ctlk = ctlk.set_index('ID', drop=False)

    return ctlk


def polygonStatus(gdf):
    '''
    图斑填报状态：已填报养殖、已填报非养殖、未填报
    '''
    naquadict = {
        '养殖经营人名称': ['未养殖', '退养', '水库', '光伏'],
        '池塘所有权人名称': ['/']
    }  # 待软件增加字段

    for k in list(naquadict.keys()):
        for v in naquadict[k]:
            gdf.loc[gdf[k] == v, '填报状态'] = '已填报非养殖'

    gdf.loc[gdf['填报状态'].isnull() & gdf['状态'].isnull(), '填报状态'] = '未填报'  # 剩余填报养殖和未填报图斑中，未匹配到点（状态为空）的为未填报
    gdf.loc[gdf['填报状态'].isnull(), '填报状态'] = '已填报养殖'

    return gdf


def pointStatus(gdf):
    '''
    图斑填报状态：已填报养殖、已填报非养殖、未填报
    '''
    naquadict = {
        '养殖经营人名称': ['未养殖', '退养', '水库', '光伏'],
        '池塘所有权人名称': ['/']
    }  # 待软件增加字段

    for k in list(naquadict.keys()):
        for v in naquadict[k]:
            gdf.loc[gdf[k] == v, '填报状态'] = '已填报非养殖'

    gdf.loc[gdf['填报状态'].isnull(), '填报状态'] = '已填报养殖'

    return gdf


def deleteTestData2(df, field, keywords):
    '''
    按关键字keywords模糊匹配删除测试数据
    '''
    for k in keywords:
        df[field] = df[field].str.replace(k, '测试')

    # 删除测试数据
    values = df[field].values.tolist()

    test_idx = np.array([True if '测试' in v else False for v in values])
    df = df[~test_idx]

    return df


def mergeData(xls_file, polygon_file, dels_file=None):
    # 池塘轮廓
    st_time = datetime.now()
    ctlk = gpd.read_file(polygon_file)
    if 'id' in ctlk.columns:
        ctlk = ctlk.rename(columns={'id': 'ID', 'tbid': 'TBID'})
    ctlk = ctlk.rename(columns={'ID': '图斑id'})
    ctlk['图斑id'] = ctlk['图斑id'].astype('int').astype('str')
    ctlk = ctlk.set_index(['图斑id'], drop=False)
    ctlk['图斑面积'] = np.round(ctlk['area'] / 666.66, 2)
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"池塘轮廓数据读取与处理：{np.round(spd_time / 60, 0)} 分钟")
    # ctlk.to_file(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\tmp\ctlk.gpkg',encoding='utf-8',driver='GPKG')

    #     # 删除指定图斑
    #     if dels_file is not None:
    #         tbids = listDeletes(dels_file)
    #         ctlk = splitPolygons(ctlk,'TBID',tbids)
    #     else:
    #         ctlk['Ndel'] = True

    # 池塘信息
    st_time = datetime.now()
    #     if os.path.isdir(xls_file):
    #         files = glob.glob(f"{xls_file}\\*.xlsx")
    #         df_list = []
    #         for f in files:
    #             print(f"read {f}")
    #             df_list.append(pd.read_excel(f, dtype=str))
    #         ctxx = pd.concat(df_list,ignore_index=True)
    #     else:
    ctxx = pd.read_excel(xls_file, dtype=str)
    # 面积计算
    idx2 = ctxx['图斑面积'] != '/'
    ctxx['面积_亩'] = ''
    ctxx.loc[idx2, '面积_亩'] = ctxx.loc[idx2, '图斑面积'].astype(float) * 0.0015

    # 删除无效、审核驳回、未上报及测试数据
    ctxx = deleteInvalidData(ctxx)
    ctxx.set_index('池塘id', inplace=True, drop=False)
    # 面积转数值型
    ctxx['合同面积'] = pd.to_numeric(ctxx['合同面积'], errors='coerce')
    ctxx['净水面面积'] = pd.to_numeric(ctxx['净水面面积'], errors='coerce')  # 转数值型，非数值型强制转为nan
    # 校对状态添加数值型【状态值】
    ctxx = status2Num(ctxx)
    # # 养殖品种格式化
    # ctxx['养殖品种/预计亩产量'] = ctxx['养殖品种/预计亩产量'].str.replace('斤/亩','')
    # idx = ctxx[ctxx['养殖品种/预计亩产量']!='/'].index
    # for i in idx:
    #     yzxx = ctxx.loc[i,'养殖品种/预计亩产量'].split('，')
    #     pz = np.array([y.split(':')[0] for y in yzxx])
    #     cl = np.array([y.split(':')[1] for y in yzxx])
    #     sortedidx = np.argsort(pz)
    #     ctxx.loc[i,'养殖品种'] = ','.join(pz[sortedidx])
    #     ctxx.loc[i,'亩产量'] = ','.join(cl[sortedidx])
    # 转矢量
    ctxx['longitude'] = ctxx['池塘位置'].str.split('，', expand=True)[0]
    ctxx['latitude'] = ctxx['池塘位置'].str.split('，', expand=True)[1]
    ctxx = df2gdf(ctxx, 'longitude', 'latitude', epsg=4326).to_crs(ctlk.crs)
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"池塘信息读取与处理：{np.round(spd_time / 60, 0)} 分钟")

    # 池塘信息合并TBID
    st_time = datetime.now()
    # ctxx = gpd.sjoin(ctxx, ctlk, how='left')
    try:
        ctxx = pd.merge(ctxx, ctlk.loc[:, ['图斑id', 'TBID', '图斑面积']], on=['图斑id'], how='left')
    except:
        ctxx = pd.merge(ctxx, ctlk.loc[:, ['TBID', '图斑面积']], on=['图斑id'], how='left')
    ctxx.set_index('池塘id', inplace=True, drop=False)
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"池塘信息合并轮廓ID：{np.round(spd_time / 60, 0)} 分钟")

    # 池塘信息填补合并编号
    ctxx.loc[ctxx['合并id'] == '/', '合并id'] = ctxx[ctxx['合并id'] == '/'].index
    # ctxx.to_file(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\总体进度\ctxx.gpkg',encoding='utf-8',driver='GPKG')

    # 排口位置
    st_time = datetime.now()
    pk = ctxx.copy()
    pk = pk[~pk['排口位置'].isnull()]
    pk = pk[pk['排口位置'] != '/']
    pk['longitude'] = pk['排口位置'].str.split('，', expand=True)[0]
    pk['latitude'] = pk['排口位置'].str.split('，', expand=True)[1]
    pk['wkt_str'] = 'POINT (' + pk['longitude'] + ' ' + pk['latitude'] + ')'
    pk['geometry'] = pk['wkt_str'].apply(wkt.loads)
    pk = pk.drop(columns=['longitude', 'latitude', 'wkt_str'])
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"排口位置：{np.round(spd_time / 60, 0)} 分钟")

    # 养殖品种重名的加水体类型为前缀重命名
    npz = ['其他种类', '南美白对虾', '螺', '鲈鱼']
    for p in npz:
        idx0 = ctxx['养殖品种/预计亩产量'].str.contains(p)
        stlx = ctxx.loc[idx0, '水体类型'].unique()
        for s in stlx[stlx != '/']:
            idx = (ctxx['水体类型'] == s) & (idx0)
            ctxx.loc[idx, '养殖品种/预计亩产量'] = ctxx.loc[idx, '养殖品种/预计亩产量'].str.replace(p, f"{s}{p}")

    '''
    提取养殖品种
    '''
    ctxx = extractYZPZ(ctxx)

    # 图斑增加填报信息
    st_time = datetime.now()
    ctlk = addAttr2Plygons(ctlk, ctxx)
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"图斑增加填报信息：{np.round(spd_time / 60, 0)} 分钟")

    # 图斑增加填报状态：已填报养殖、已填报非养殖、未填报
    st_time = datetime.now()
    ctlk = polygonStatus(ctlk)
    ctxx = pointStatus(ctxx)
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"图斑、填报点增加填报状态：{np.round(spd_time / 60, 0)} 分钟")

    return ctxx, ctlk, pk


def MCAnalysis(df):
    for i in df.index:
        nature = df.loc[i, '池塘所有权']
        name = df.loc[i, '池塘所有权人名称']
        if (nature != '其他') & ('家庭农场' in name):
            yd = ''
        else:
            # 所有权为个人，所有权人名称不是人名
            if (nature == '个人') & (not is_person(name)):
                yd = '所有权人名称疑似填写有误（非人名）,'

            # 所有权为集体，所有权人名称不是集体/公司
            elif (nature == '集体/公司') & (not is_company(name)):
                yd = '所有权人名称疑似填写有误（非集体/公司）,'
                # print(yd)

            # 所有权为国有（其他），所有权名称不是人名且不是集体/公司
            elif name in ['村集体', '村委会', '个人', '无', '集体', '集体0']:
                yd = '所有权人名称疑似填写有误,'

            else:
                yd = ''
            # elif (nature == '其他') & ((is_company(name) or is_person(name)) or ('家庭农场' in name)):
            #     yd = '所有权人名称疑似填写有误（集体/公司、个人）,'

            # else:
            #     yd = ''

        nature = df.loc[i, '养殖主体类型']
        name = df.loc[i, '养殖经营人名称']
        if (nature != '其他') & ('家庭农场' in name):
            yd += ''
        else:
            # 主体性质为个人，主体名称不是人名
            if (nature == '个人') & (not is_person(name)):
                yd += '主体名称疑似填写有误（非人名）,'

            # 主体性质为集体/公司，但名称不是公司
            elif (nature == '集体/公司') & (not is_company(name)):
                yd += '主体名称疑似填写有误（非集体/公司）,'

            # 主体性质为其他，但主体名称是个人或集体/公司
            elif (nature == '其他') & (not is_chinese(name)):
                # if (not is_chinese(name)):
                yd += '主体名称疑似填写有误（非中文）,'

            elif name in ['村集体', '村委会', '个人', '无', '集体', '集体0']:
                yd += '主体名称疑似填写有误,'

                # if is_company(name) or is_person(name) or ('家庭农场' in name):
                #     yd += '主体性质疑似填写有误,'

            # 联系人不是人名
            name = df.loc[i, '联系人']
            if not is_person(name):
                yd += '联系人疑似填写有误（非人名）,'

            # 人名疑似笔误
            if is_person_similar(df.loc[i, '池塘所有权人名称'], df.loc[i, '养殖经营人名称']) and (
                    df.loc[i, '池塘所有权人名称'] != df.loc[i, '养殖经营人名称']):
                yd += '人名疑似笔误,'

        df.loc[i, '名称疑点'] = yd[0:-1]

    df.loc[df['名称疑点'] == '', '名称疑点'] = '无异常'

    return df


def is_person(str_char):
    str_char = str_char.strip()
    if not is_chinese(str_char):
        return False
    if len(str_char) > 4:
        return False

    pattern = ['村', '街', '社区', '集体', '殖', '养殖场', '农场', '钓场',
               '公司', '居委会', '委员会', '老百姓', '九组', '八组',
               '七组', '六组', '五组', '四组', '三组', '二组', '一组', '十一',
               '种牛场', '种蜂场', '林场']
    for p in pattern:
        if p in str_char:
            return False

    # with open(SURNAME_PATH, 'r', encoding='UTF-8') as f:
    #     data = f.read()
    #     f.close()
    # p_surname = data.split(',')
    # for p in p_surname:
    #     if p == str_char[:len(p)]:
    #         return True
    return True


def is_company(str_char):
    str_char = str_char.strip()

    pattern1 = [r'(', r')', r'（', r'）']
    for p in pattern1:
        str_char = str_char.replace(p, r'')

    if not is_chinese(str_char):
        return False

    pattern2 = ['镇', '村', '街', '社区', '集体', '居委会', '组', '农庄', '基地',
                '合作社', '养殖场', '农场', '钓场', '生产队', '处理中心', '发展中心', '养殖中心', '水务站',
                '厂', '公司', '集团', '研究院', '局', '种牛场', '部', '种蜂场', '闸管所', '高级中学', '服务中心',
                '禽业', '能源', '委员会', '生态园', '林场', '农科院', '电站', '育苗场', '管理所', '病院', '蚕种场',
                '湾景区', '农业园区', '医院', '牧业', '风景区', '管理所', '促进中心', '帕蒂亚庄园', '猪场', '张湾中学',
                '人民政府', '指导站', '经济开发区', '张湾乡', '闸坝所', '管理处', '气象台', '邓楼果园', '丙辰电子',
                '联亚纺织',
                '第二中学', '水产良种场', '养殖', '山茶场', '鱼种场', '金绿生态', '盱眙国联', '淮安市淮安区园艺场',
                '村委会',
                '果园', '槐树居', '管委会', '柳山居', '石集乡瓦房居', '示范园', '国营泗阳林苗圃', '荷香园',
                '科技示范园', '产业园',
                '联鑫钢构', '水利站', '管理中心', '农技中心', '铜山区三河尖矿']
    for p in pattern2:
        if p in str_char:
            return True

    return False


def is_chinese(str_char):
    str_char = str_char.strip()
    for char in str_char:
        if 'CJK' not in unicodedata.name(char):
            return False
    return True


# 判断人名是否为笔误（同读音）
def is_person_similar(name1, name2):
    threshold = 0.1
    pattern = [r' ', r' ']
    for p in pattern:
        name1 = name1.replace(p, r'')
        name2 = name2.replace(p, r'')
    if (len(name1) == len(name2)) and (is_person(name1)) and (is_person(name2)):
        if dimsim.get_distance(name1, name2) < threshold:
            return True
    else:
        return False


def pkAnalysis(sjoins, polygons, psxx):
    sjoins['疑点信息'] = sjoins['疑点信息'].str.replace('排口位置较远', '')
    sjoins['疑点信息'] = sjoins['疑点信息'].str.replace('，排口位置较远', '')
    sjoins['疑点信息'] = sjoins['疑点信息'].str.replace('排口位置较远，', '')

    sjoins['排口疑点'] = '无异常'
    sjoins = sjoins.to_crs('epsg:32650')
    polygons = polygons.to_crs('epsg:32650')
    psxx = psxx.to_crs('epsg:32650')

    sjoins_group = sjoins.groupby('合并id')
    sjoins_group_tbid = sjoins_group['图斑id'].unique()
    sjoins_group_ctid = sjoins_group['池塘id'].unique()
    sjoins_group_pknm = sjoins_group['排口位置'].unique().apply(lambda x: len(x))
    for i in sjoins_group_tbid.index:
        if sjoins_group_pknm[i] > 0:
            tbid = sjoins_group_tbid[i]
            ctid = sjoins_group_ctid[i]
            try:
                # tb = polygons.loc[tbid,['geometry']].dissolve().buffer(200).values[0]
                tb = \
                polygons.loc[polygons[polygons['图斑id'].isin(tbid)].index, ['geometry']].dissolve().buffer(200).values[
                    0]
            except:
                # tb = sjoins.loc[ctid,['geometry']].dissolve().buffer(500).values[0]
                tb = sjoins.loc[sjoins[sjoins['池塘id'].isin(ctid)].index, ['geometry']].dissolve().buffer(500).values[
                    0]

            for j in ctid:
                if j in psxx['池塘id']:
                    pk = psxx.loc[j, 'geometry']
                    if not pk.intersects(tb):
                        sjoins.loc[j, '排口疑点'] = '排口标记较远'

    return sjoins


def contractTimeAnalysis(sjoins):
    '''
    承包期限
    '''
    sjoins['承包期限疑点'] = ''
    #  所有权人名称和主体名称不一致，承包期限未填写
    idx = (sjoins['池塘所有权人名称'] != sjoins['养殖经营人名称']) & (
                sjoins['承包期限'].isnull() | sjoins['承包期限'] == '/')
    sjoins.loc[idx, '承包期限疑点'] = '主体与所有权人不同但承包期限未填写'

    # 承包结束时间疑似过短
    # idx = (~sjoins['承包期限'].isnull()) & (sjoins['承包期限']!='/')
    # idx = sjoins[idx].index
    # for i in idx:
    #     contract_endtime = sjoins.loc[i, '承包期限'].split(' : ')[1]
    #     if is_person_similar(sjoins.loc[i, '池塘所有权人名称'], sjoins.loc[i, '养殖经营人名称']):
    #         time_difference = datetime.strptime(contract_endtime, "%Y-%m-%d") - datetime.now()
    #         if time_difference.days < 10*365:
    #             sjoins.loc[i, '承包期限疑点'] = sjoins.loc[i, '承包期限疑点'] + ',承包结束时间疑似过短'

    # 养殖主体和所有权人一致，无承包期限
    idx = (sjoins['池塘所有权人名称'] == sjoins['养殖经营人名称']) & (
                (~sjoins['承包期限'].isnull()) & (sjoins['承包期限'] != '/'))
    sjoins.loc[idx, '承包期限疑点'] = '主体与所有权人相同应无承包期限'

    sjoins.loc[sjoins['承包期限疑点'] == '', '承包期限疑点'] = '无异常'

    return sjoins


def idnumberAndZTMCAnalysis(sjoins):
    '''
    分析同主体名、不同身份证号的疑点
    '''
    sjoins['身份证号疑点'] = ''
    grouped = sjoins[sjoins['填报状态'] == '已填报养殖'].groupby(['养殖经营人名称', '身份证号'])
    groups = grouped.size().index.values
    idnumber = [g[1] for g in groups]
    # 同证件号不同人名
    dulplicates = getDulplicates(idnumber)
    dulplicates = dulplicates[dulplicates != '/']
    for d in dulplicates:
        idx = (sjoins['身份证号'] == d)
        sjoins.loc[idx, '身份证号疑点'] += '同身份证号不同人名'
    # 同人名不同证件号 删除
    # grouped = sjoins.groupby(['地址','养殖经营人名称','身份证号'])
    # groups = grouped.size().index.values
    # name = ['-'.join(g[0:2]) for g in groups]
    # dulplicates = getDulplicates(name)
    # name_series = sjoins['地址'] + '-' + sjoins['养殖经营人名称']
    # for d in dulplicates:
    #     idx = (name_series == d)
    #     sjoins.loc[idx,'身份证号疑点'] += '同人名不同身份证号,'

    # sjoins.loc[sjoins['身份证号疑点']=='','身份证号疑点'] = '无异常'

    return sjoins

if __name__ == "__main__":
    datapath = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250825'
    prefixlktable = r'E:\全省养殖池溏上图入库普查\填报进度统计\江苏省城市缩写-调格式.xlsx'  # 图斑编号前缀查找表
    xlsfile = '无锡市.xlsx'
    polygon_file = r'E:\全省养殖池溏上图入库普查\项目验收\2024年12月图斑抽检结果\1311773池塘图斑及抽检图斑\0728池塘图斑.gpkg'
    yzpz_file = r'E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250402\池塘信息-1743556009602-20250402095641-无锡市-疑点统计表-全\养殖种类-江苏.xlsx'
    os.chdir(datapath)

    # 数据连接
    sjoins, polygons, pk = mergeData(xlsfile, polygon_file)

    sjoins['图斑疑点'] = ''

    # 无对应图斑
    idx1 = sjoins['图斑id'] == '/'
    idx2 = sjoins['养殖状态'] == '养殖'
    sjoins.loc[idx1 & idx2, '图斑疑点'] += '无对应图斑；'

    # 多点对应同一图斑
    dulplicates = getDulplicates(sjoins.loc[sjoins['图斑id'] != '/', '图斑id'].values)
    for d in dulplicates:
        idx = sjoins['图斑id'] == d
        if (sjoins.loc[idx, '养殖状态'] == '养殖').any():
            idx_str = '、'.join(sjoins.loc[idx, '池塘id'].values.tolist())
            sjoins.loc[idx, '图斑疑点'] += idx_str + '对应同一图斑;'

    sjoins['亩产量疑点'] = ''
    # 有养殖品种但亩产量为0
    idx = sjoins['养殖品种/预计亩产量'].str.contains(':0')
    sjoins.loc[idx, '亩产量疑点'] += '有养殖品种但亩产量为0;'

    # 排口距离池塘超过常规范围
    sjoins = pkAnalysis(sjoins, polygons, pk)

    sjoins['证件号码疑点'] = ''
    # 身份证号、社会统一信用代码长度不对
    idx1 = sjoins['身份证号'].str.len() < 18
    idx2 = sjoins['身份证号'].str.len() > 1
    idx3 = sjoins['身份证号'].str.len() > 19
    sjoins.loc[idx1 & idx2, '证件号码疑点'] += '身份证号码长度不对;'
    sjoins.loc[idx3, '证件号码疑点'] += '身份证号码长度不对;'

    idx4 = sjoins['统一社会信用代码'].str.len() < 18
    idx5 = sjoins['统一社会信用代码'].str.len() > 1
    idx6 = sjoins['统一社会信用代码'].str.len() > 19
    sjoins.loc[idx4 & idx5, '证件号码疑点'] += '统一社会信用代码长度不对;'
    sjoins.loc[idx6, '证件号码疑点'] += '统一社会信用代码长度不对;'

    # 名称疑点
    sjoins = MCAnalysis(sjoins)

    # 承包期限疑点
    sjoins = contractTimeAnalysis(sjoins)
    # 特殊日期手动筛选

    # 同证件号不同人名 IDNUMYD
    sjoins = idnumberAndZTMCAnalysis(sjoins)

    # 尾水净化区面积填10000，常水位超过100；尾水处置频率4500
    # 手动筛

    # 亩产量超过推广中心给的上限值
    df_mcl = pd.read_excel(yzpz_file)
    df_mcl1 = df_mcl.dropna(subset='产量上限（斤）')
    pz_list = df_mcl1['三级'].tolist()
    # sjoins['亩产量疑点']=''
    for col in sjoins.columns:
        pz = col.replace('亩产量(斤/亩)', '')
        if pz in pz_list:
            value = df_mcl1[df_mcl1['三级'] == pz]['产量上限（斤）'].values[0]
            # col=pz+'亩产量(斤/亩)'
            idx = sjoins[col] > value
            sjoins.loc[idx, '亩产量疑点'] += pz + f'亩产量超出产量上限({value}),'
    idx2 = (sjoins['总产量(斤/亩)'] > 4000) & (sjoins['养殖品种数量'] > 4)
    sjoins.loc[idx2, '亩产量疑点'] += '品种超过4个、同时产量超过4000斤/亩'

    # 校对状态
    sjoins['校对状态'] = ''
    idx = ~sjoins['状态'].str.contains('通过')
    sjoins.loc[idx, '校对状态'] = '未校对通过'

    # 承包期限
    sjoins['数据疑点'] = ''
    sjoins['承包开始时间'] = sjoins["承包期限"].astype(str).str.split(" : ").str[0]
    sjoins['承包结束时间'] = sjoins["承包期限"].astype(str).str.split(" : ").str[1]
    idx = sjoins['承包开始时间'] == sjoins['承包结束时间']
    sjoins.loc[idx, '数据疑点'] += '承包期限起始时间一致'

    outfile = xlsfile.replace('.xlsx', '-疑点.xlsx')
    sjoins.to_excel(outfile)

    
    # def requiredFieldCheck(df, name):
    #     '''
    #     必填项检查
    #     '''
    #     fclss = {
    #         '填报人': ['用户类别', '手机号码'],
    #         '养殖经营人': ['养殖主体类型', '养殖经营人名称', '证件号'],
    #         '池塘所在地址': ['市*', '县（市、区）*', '乡镇（街道）*', '村（社区）*'],
    #         '联系人': ['联系人*', '联系方式*'],
    #         '养殖状态': ['养殖状态*'],
    #         '所有权人': ['池塘所有权*', '池塘所有权人名称*'],
    #         '池塘信息': ['面积', '用途*', '水体类型*', '养殖方式*', '养殖类型*', '养殖水体*', '养殖品种/预计亩产量*',
    #                      '尾水集中排放期*', '清塘淤泥处理方式*', '有无尾水处理*'],
    #         '清塘淤泥处置': ['处置频率*'],
    #         '尾水处理': ['尾水处理工艺*'],
    #         '尾水净化区面积': ['尾水净化区面积*']
    #     }
    #     df['证件号'] = df['身份证号'] + df['统一社会信用代码']
    #     df['面积'] = df['合同面积'] + df['净水面面积']
    #
    #     # 证件号码必填
    #     idx = df[df['证件号'] == ''].index
    #     df.loc[idx, BZ] += f"身份证号码、统一社会信用代码均未填，"
    #
    #     # 养殖主体类型* 为个人时，身份证号*必填
    #     idx = df[(df['养殖主体类型'] == '个人') & (df['身份证号'] == '')].index
    #     df.loc[idx, BZ] += f"个人养殖未填写身份证号，"
    #
    #     # 养殖主体类型* 为集体/公司时，统一社会信用代码必填
    #     idx = df[(df['养殖主体类型'] == '集体/公司') & (df['统一社会信用代码'] == '')].index
    #     df.loc[idx, BZ] += f"集体/公司养殖未填写统一社会信用代码，"
    #
    #     if name == '养殖':
    #         # 养殖状态为“养殖”且用途不是休闲垂钓时的必填
    #         df1 = df[(df['养殖状态'] == '养殖') & (df['用途'] != '休闲垂钓') & (df['用途'] != '尾水净化')]
    #         for k in ['面积', '水体类型', '养殖方式', '养殖品种/预计亩产量', '尾水集中排放期', '清塘淤泥处理方式',
    #                   '有无尾水处理']:
    #             idx = df1[df1[k] == ''].index
    #             df.loc[idx, BZ] += f"{k}未填，"
    #
    #         # 养殖状态为“养殖”且用途是休闲垂钓或尾水净化时的必填
    #         df1 = df[(df['养殖状态'] == '养殖') & (df['用途'] == '休闲垂钓')]
    #         for k in ['面积', '尾水集中排放期', '清塘淤泥处理方式', '有无尾水处理']:
    #             idx = df1[df1[k] == ''].index
    #             df.loc[idx, BZ] += f"{k}未填，"
    #
    #         df1 = df[(df['养殖状态'] == '养殖') & (df['用途'] == '尾水净化')]
    #         for k in ['面积', '尾水集中排放期', '清塘淤泥处理方式', '有无尾水处理']:
    #             idx = df1[df1[k] == ''].index
    #             df.loc[idx, BZ] += f"{k}未填，"
    #
    #         # 清塘淤泥处理方式*不等于“不处置”时的必填
    #         df1 = df[df['清塘淤泥处理方式'] != "不处置"]
    #         idx = df1[df1['处置频率'] == ''].index
    #         df.loc[idx, BZ] += f"处置频率未填，"
    #
    #         # 有无尾水处理*填写“有”时的必填
    #         df1 = df[df['有无尾水处理'] == "有"]
    #         idx = df1[df1['尾水处理工艺'] == ''].index
    #         df.loc[idx, BZ] += f"尾水处理工艺未填，"
    #
    #         # 有尾水处理、且非原位修复时的必填
    #         df1 = df[df['尾水处理工艺'] != '']
    #         df2 = df1[df1['尾水处理工艺'] != '原位修复']
    #         idx = df2[df2['尾水净化区面积'] == ''].index
    #         df.loc[idx, BZ] += f"尾水净化区面积未填，"
    #
    #         # 面积大于50亩必填“是否完成池塘标准化改造*”
    #         df['图斑面积（亩）']=(df['图斑面积_y'].astype(float))*0.0015
    #         idx = df[(df['图斑面积（亩）']>=50) & (df['是否完成池塘标准化改造']=='')].index
    #         df.loc[idx,BZ] += f"50亩以上池塘未填 是否完成池塘标准化改造*\n"
    #
    #     return df
    # #
    # outfile = xlsfile.replace('.xlsx', '-疑点.xlsx')
    #
    # name = outfile.split('.xlsx')[0]
    #
    # df = pd.read_excel(outfile, dtype=str)  # , skiprows=1
    #
    # BZ = '必填项检查'
    # # 未填项设置为''
    # for c in df.columns:
    #     df.loc[df[c] == '/', c] = ''
    # df = df.fillna('')
    # df[BZ] = ''
    #
    # # 未使用必填项检查
    # df_wsy = df[df['填报状态'].str.contains('已填报非养殖')].copy()
    # df_wsy = requiredFieldCheck(df_wsy, name='未使用')
    # # df_wsy.to_excel("必填项检查_未使用.xlsx",index=False)
    #
    # # 养殖必填项检查
    # df_yz = df[df['填报状态'].str.contains('已填报养殖')].copy()
    # df_yz = requiredFieldCheck(df_yz, name='养殖')
    # # df_yz.to_excel("必填项检查_养殖.xlsx",index=False)
    #
    # # 50亩以上池塘未填 是否完成池塘标准化改造
    # df_yz['面积_亩'] = pd.to_numeric(df_yz['面积_亩'], errors='coerce')
    # idx1 = df_yz['面积_亩'].astype(float) >= 50
    # idx2 = ((df_yz['是否完成池塘标准化改造'] == '') | (df_yz['是否完成池塘标准化改造'] == '---'))
    #
    # df_yz.loc[idx1 & idx2, BZ] += "50亩以上池塘未填 是否完成池塘标准化改造;"
    #
    # # 养殖主体类型为集体/公司时未填排口位置
    # idx3 = df_yz['养殖主体类型'] == '集体/公司'
    # idx4 = ((df_yz['排口位置'] == '') | (df_yz['排口位置'] == '---'))
    # df_yz.loc[idx3 & idx4, BZ] += "养殖主体类型为集体/公司时未填排口位置;"
    #
    # df_yd = pd.concat([df_yz, df_wsy], ignore_index=True)
    # df2 = df_yd.rename(
    #     columns={'图斑疑点': '图斑质控', '亩产量疑点': '亩产量质控', '排口疑点': '排口质控', '证件号码疑点': '证件号码质控',
    #              '名称疑点': '名称质控', '承包期限疑点': '承包期限质控', '身份证号疑点': '身份证号质控',
    #              '数据疑点': '数据质控'})
    # df2.to_excel(name + "-必填项检查-总.xlsx", index=False)
    #
    # df2["所在乡镇"] = df2["地址"].astype(str).str.split("-").str[2] + '-' + df2["地址"].astype(str).str.split("-").str[3]
    #
    # idx1 = df2['图斑质控'] != ''
    # idx2 = df2['亩产量质控'] != ''
    # idx3 = df2['排口质控'] != '无异常'
    # idx4 = df2['证件号码质控'] != ''
    # idx5 = df2['名称质控'] != '无异常'
    # idx6 = df2['承包期限质控'] != '无异常'
    # idx7 = df2['身份证号质控'] != ''
    # idx8 = df2['校对状态'] != ''
    # idx9 = df2['数据质控'] != ''
    # idx10 = df2['必填项检查'] != ''
    #
    # df3 = df2[idx1 | idx2 | idx3 | idx4 | idx5 | idx6 | idx7 | idx8 | idx9 | idx10].copy()
    # len(df3)
    #
    # keywords = ["鲫鱼", "鳊鲂", "泥鳅", "淡水鲈鱼", "黄鳝", "蛙", "乌鳢"]
    # # idx1=df3['用途'].str.contains('成品养殖')|df3['用途'].str.contains('苗种培育')
    # idx1 = df3['用途'].str.contains('成品养殖')
    # df_a = df3[idx1].copy()
    # mask = df_a["养殖品种/预计亩产量"].astype(str).apply(lambda x: any(k in x for k in keywords))
    # filtered_a = df_a[mask].copy()
    # filtered_b = cachu(df3, filtered_a)
    #
    #
    #
    # address_unq = dizhi2(df3)
    # address_unq
    #
    # e = 0
    # for i in address_unq:
    #     with pd.ExcelWriter(i + '-数据质控.xlsx') as writer:
    #         idx1 = filtered_a['地址'].str.contains(i)
    #         df1 = filtered_a[idx1].copy()
    #         e = e + len(df1)
    #         df1 = df1[
    #             ['池塘id', '养殖经营人名称', '养殖主体类型', '身份证号', '统一社会信用代码', '地址', '所在乡镇', '联系人',
    #              '联系方式',
    #              '池塘所有权', '池塘所有权人名称', '池塘所有权人证件号码', '池塘土地属性', '承包期限', '合同面积',
    #              '净水面面积',
    #              '合并id', '常水位', '用途', '水体类型', '养殖方式', '养殖品种/预计亩产量', '状态', '养殖状态', '图斑编号',
    #              '面积_亩',
    #              '是否完成池塘标准化改造', '排口位置', '尾水集中排放期', '清塘淤泥处理方式', '处置频率', '有无尾水处理',
    #              '尾水处理工艺',
    #              '尾水净化区面积', '检测日期', '检测塘口位置', '检测方式', '检测指标', '第三方检测机构',
    #              '图斑质控', '亩产量质控', '排口质控', '证件号码质控', '名称质控', '承包期限质控', '身份证号质控',
    #              '数据质控', '必填项检查', '校对状态']]
    #         df1.to_excel(writer, sheet_name='成品养殖七鱼相关', index=False)
    #
    #         idx6 = filtered_b['地址'].str.contains(i)
    #         df4 = filtered_b[idx6].copy()
    #         e = e + len(df4)
    #         df4 = df4[
    #             ['池塘id', '养殖经营人名称', '养殖主体类型', '身份证号', '统一社会信用代码', '地址', '所在乡镇', '联系人',
    #              '联系方式',
    #              '池塘所有权', '池塘所有权人名称', '池塘所有权人证件号码', '池塘土地属性', '承包期限', '合同面积',
    #              '净水面面积',
    #              '合并id', '常水位', '用途', '水体类型', '养殖方式', '养殖品种/预计亩产量', '状态', '养殖状态', '图斑编号',
    #              '面积_亩',
    #              '是否完成池塘标准化改造', '排口位置', '尾水集中排放期', '清塘淤泥处理方式', '处置频率', '有无尾水处理',
    #              '尾水处理工艺',
    #              '尾水净化区面积', '检测日期', '检测塘口位置', '检测方式', '检测指标', '第三方检测机构',
    #              '图斑质控', '亩产量质控', '排口质控', '证件号码质控', '名称质控', '承包期限质控', '身份证号质控',
    #              '数据质控', '必填项检查', '校对状态']]
    #         df4.to_excel(writer, sheet_name='其他', index=False)
    #
    # e
    #
    # df3_2 = df3[['池塘id', '养殖经营人名称', '养殖主体类型', '身份证号', '统一社会信用代码', '地址', '所在乡镇', '联系人',
    #              '联系方式',
    #              '池塘所有权', '池塘所有权人名称', '池塘所有权人证件号码', '池塘土地属性', '承包期限', '合同面积',
    #              '净水面面积',
    #              '合并id', '常水位', '用途', '水体类型', '养殖方式', '养殖品种/预计亩产量', '状态', '养殖状态', '图斑编号',
    #              '面积_亩',
    #              '是否完成池塘标准化改造', '排口位置', '尾水集中排放期', '清塘淤泥处理方式', '处置频率', '有无尾水处理',
    #              '尾水处理工艺',
    #              '尾水净化区面积', '检测日期', '检测塘口位置', '检测方式', '检测指标', '第三方检测机构',
    #              '图斑质控', '亩产量质控', '排口质控', '证件号码质控', '名称质控', '承包期限质控', '身份证号质控',
    #              '数据质控', '必填项检查', '校对状态']]
    # df3_2.to_excel("数据质控总表.xlsx", index=False)