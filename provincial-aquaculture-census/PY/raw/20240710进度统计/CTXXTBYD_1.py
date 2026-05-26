import os,glob

import geopandas as gpd
import pandas as pd
from shapely import wkt
import numpy as np
import folium
import folium.plugins
import unicodedata
import re
# from LAC import LAC
# import dimsim
from datetime import datetime, timedelta

# lac = LAC(mode='lac')
# SURNAME_PATH = r"G:\xiangmu\江苏省天地图分割\填报信息分析\20240704\进度统计用\常见姓氏.txt"
# XZQH = gpd.read_file(r'G:\qiwei\WXWork\1688858186325806\Cache\File\2024-06\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp')
# REGIONCODE = pd.read_excel(r'G:\xiangmu\江苏省天地图分割\填报信息分析\20240704\进度统计用\行政编码.xlsx')

def readZDSM(ZDSM_FILE):
    with open(ZDSM_FILE,encoding='utf-8') as f:
        data = f.read().split('\n')[1:-2]
        eng = [d.split("\'")[0].replace('`','').strip() for d in data]
        chn = [d.split("\'")[1].split(' ')[0] for d in data]
    zd_dict = {}
    for i in range(len(chn)):
        zd_dict[eng[i]] = chn[i]

    return zd_dict

def df2gdf(df,lon_col,lat_col,epsg=4326):
    '''
    功能：df对象转gdf
    df: pd.DataFrame 数据表，含经纬度数据列
    lon_col: str 经度对应的列名
    lat_col: str 纬度对应的列名
    epsg: int 坐标系对应的编号，默认4326 WGS-1984
    '''
    df['wkt_str'] = 'POINT (' + df[lon_col] + ' ' + df[lat_col] + ')'
    
    df['geometry'] = df['wkt_str'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df,crs='EPSG:'+str(epsg),geometry=df['geometry'])
    gdf = gdf.drop('wkt_str',axis=1)

    return gdf

def getDulplicates(data):
    '''
    获取有重复项的值
    '''
    a,b = np.unique(data,return_counts=True)
    
    return a[b>1]

def areaAnalysis1(gdf):
    '''
    分析面积疑点:矢量面积-水域面积
    '''
    areas1 = gdf['图斑面积'].values
    areas2 = gdf['净水面面积'].values
    diff = np.abs(areas2 - areas1)
    pct = diff / areas1
    results = np.array(['无异常']*len(diff),dtype='<U20')
    results[(areas1<=5) & (diff>1)] = '水面面积偏差大于1亩'
    results[(areas1>5) & (pct>0.5)] = '水面面积偏差大于50%'
    results[np.isnan(areas2)] = '无异常'
    gdf['水面面积疑点'] = results

    return gdf

def areaAnalysis2(gdf):
    '''
    分析面积疑点:矢量面积-合同面积
    gdf:用户填报点 拼接 分割面信息
    '''
    gdf['合同面积疑点'] = ''
    groupids = gdf['合并id'].values
    for g in groupids:
        idx = g.split(',')
        try:
            area1 = gdf.loc[idx,'合同面积'].values
            area1 = area1[~np.isnan(area1)]
            area2 = gdf.loc[idx,'图斑面积'].values
            area2 = np.sum(area2)
            if len(np.unique(area1)) > 1:
                gdf.loc[idx,'合同面积疑点'] = '同一合同不同面积'
            elif len(np.unique(area1)) == 0:
                gdf.loc[idx,'合同面积疑点'] = '无异常'
            else:
                diff = np.abs(area1[0] - area2)
                pct = diff / area2
                if (area2<=5) & (diff>1):
                    gdf.loc[idx,'合同面积疑点'] = '合同面积偏差大于1亩'
                elif (area2>5) & (pct>0.5):
                    gdf.loc[idx,'合同面积疑点'] = '合同面积偏差大于50%'
                else:
                    gdf.loc[idx,'合同面积疑点'] = '无异常'
        except:
            new_idx = []
            for i in idx:
                if i in gdf.index:
                    new_idx.append(i)
            gdf.loc[new_idx,'合同面积疑点'] = '合并池塘ID中有池塘被驳回'
            # idx = new_idx
            # area1 = gdf.loc[idx,'area_number'].values
            # area1 = area1[~np.isnan(area1)]
            # area2 = gdf.loc[idx,'area'].values
            # area2 = np.sum(area2)
            # if len(np.unique(area1)) > 1:
            #     gdf.loc[idx,'合同面积疑点'] = '同一合同不同面积'
            # elif len(np.unique(area1)) == 0:
            #     gdf.loc[idx,'合同面积疑点'] = '无异常'
            # else:
            #     diff = np.abs(area1[0] - area2)
            #     pct = diff / area2
            #     if (area2<=5) & (diff>1):
            #         gdf.loc[idx,'合同面积疑点'] = '合同面积偏差大于1亩'
            #         gdf.loc[idx,'合同面积偏差'] = diff
            #     elif (area2>5) & (pct>0.5):
            #         gdf.loc[idx,'合同面积疑点'] = '合同面积偏差大于50%'
            #         gdf.loc[idx,'合同面积偏差'] = pct
            #     else:
            #         gdf.loc[idx,'合同面积疑点'] = '无异常'

    
    return gdf

def areaAnalysis3(sjoins):
    '''
    分析合同面积是否有未合并
    '''
    sjoins['合并疑点'] = '无异常'
    grouped = sjoins.groupby(['合同面积','身份证号'])
    group_idx = grouped.size().index
    for gi in group_idx:
        merge_pond_ids = grouped.get_group(gi)['合并id'].values
        # 同合同面积、身份证号，不同合并池塘ID
        if len(np.unique(merge_pond_ids))>1:
            area2 = grouped.get_group(gi)['图斑面积'].sum()
            area1 = gi[0]
            diff = np.abs(area1 - area2)
            pct = diff / area2
            idx = grouped.get_group(gi).index
            prefix = ','.join([str(i) for i in idx])
            if (area2>5) & (pct>0.5):
                sjoins.loc[idx,'合并疑点'] = prefix + '疑似忘记合并且面积偏差大于50%'
            elif (area2<=5) & (diff>1):
                sjoins.loc[idx,'合并疑点'] = prefix + '疑似忘记合并且面积偏差大于1亩'
            else:
                sjoins.loc[idx,'合并疑点'] = prefix + '疑似忘记合并'

    return sjoins


def add_tian_di_tu_layers(map_object):
    tian_di_tu_normal_map = ("https://t6.tianditu.gov.cn/img_w/wmts"
                         "?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
                         "&LAYER=img&STYLE=default&TILEMATRIXSET=w"
                         "&FORMAT=tiles&TILECOL={x}&TILEROW={y}"
                         "&TILEMATRIX={z}&tk=5625113a2addc9a7594d0fffe3811311")

    # 天地图注记图层的URL模板
    tian_di_tu_zhuji = ("https://t6.tianditu.gov.cn/cia_w/wmts"
                        "?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
                        "&LAYER=cia&STYLE=default&TILEMATRIXSET=w"
                        "&FORMAT=tiles&TileCol={x}&TileRow={y}"
                        "&TileMatrix={z}&tk=5625113a2addc9a7594d0fffe3811311")
    
    for name, url in [("天地图影像", tian_di_tu_normal_map), ("天地图注记", tian_di_tu_zhuji)]:
        folium.TileLayer(
            tiles=url,
            attr=name,
            name=name,
            overlay=name,
            control=False
        ).add_to(map_object)

def createYDMap(yd1,yd2,yd3):
    '''
    生成疑点分布图
    yd1: points 用户填报点
    yd2: polygons 未填报图斑
    yd3: polygons 重复填报图斑
    xzq: polygons 行政区划
    '''
    minx,miny,maxx,maxy = yd1.total_bounds
    centroid_coords = [(miny+maxy)/2,(minx+maxx)/2]
    m = folium.Map(location=centroid_coords, zoom_start=15,tiles=None)
    add_tian_di_tu_layers(m)

    pt_cluster = folium.plugins.MarkerCluster().add_to(m)
    txt_cluster = folium.plugins.MarkerCluster().add_to(m)

    folium.GeoJson(
        yd1,
        name='填报疑点',
    ).add_to(pt_cluster)

    for i, row in yd1.iterrows():
        folium.Marker(
            location=[row['中心点纬度'],row['中心点经度']],
            show='True',
            icon=folium.DivIcon(
                icon_size=(30, 10),
                icon_anchor=(0, 0),
                html=f'''
                    <div style="font-size: 12pt; color: black; text-shadow:
                        -1px -1px 0 #fff,
                        1px -1px 0 #fff,
                        -1px 1px 0 #fff,
                        1px 1px 0 #fff;">
                        {i}
                    </div>'''
            )
        ).add_to(txt_cluster)

    style_function = lambda x: {
        'fillColor': '#transparent', 
        'color': '#00FF00',  # 绿色
        'weight': 1,
    }
    folium.GeoJson(
        yd2,
        style_function=style_function,
        name='未填报图斑',
    ).add_to(m)

    style_function = lambda x: {
        'fillColor': '#transparent',
        'color': '#FF0000',  # 红色
        'weight': 1,
    }
    folium.GeoJson(
        yd3,
        style_function=style_function,
        name='填报多点的图斑',
    ).add_to(m)

    # folium.LayerControl().add_to(m)

    return m


def mergeData(xls_file, polygon_file):
    # 池塘轮廓
    ctlk = gpd.read_file(polygon_file)
    ctlk = ctlk.set_index(['ID'], drop=False)
    ctlk['图斑面积'] = np.round(ctlk.to_crs('epsg:32650').geometry.area / 666.66, 2)

    # 池塘信息
    ctxx = pd.read_excel(xls_file, dtype=str, skiprows=1, index_col='池塘id')
    ctxx = ctxx[ctxx['池塘位置'] != '/']
    ctxx = ctxx[~ctxx['池塘位置'].isnull()]
    ctxx['longitude'] = ctxx['池塘位置'].str.split('，', expand=True)[0]
    ctxx['latitude'] = ctxx['池塘位置'].str.split('，', expand=True)[1]
    ctxx.loc[ctxx['合同面积'] == '/', '合同面积'] = np.nan
    ctxx.loc[ctxx['净水面面积'] == '/', '净水面面积'] = np.nan
    ctxx['合同面积'] = ctxx['合同面积'].astype('float')
    ctxx['净水面面积'] = ctxx['净水面面积'].astype('float')
    yzpz = ctxx['养殖品种/预计亩产量'].str.split('，', expand=True)
    for i in yzpz.columns:
        yzpz.loc[:, i] = yzpz.loc[:, i].str.split(':', expand=True)[0]
    ctxx['养殖品种'] = yzpz[0].fillna('')
    ctxx['养殖品种'] = ctxx['养殖品种'].str.replace(',,', '')
    for i in yzpz.columns[1:]:
        ctxx['养殖品种'] = ctxx['养殖品种'].str.cat(yzpz[i].fillna(''), sep=',')
    pattern = r'\d+.\d+'
    for i, row in ctxx.iterrows():
        str1 = row['养殖品种/预计亩产量']
        if (isinstance(str1, str)) & (str1 != '/'):
            matches = re.findall(pattern, str1)
            row['产量'] = ','.join(matches)
    ctxx = df2gdf(ctxx, 'longitude', 'latitude', epsg=4326).to_crs(ctlk.crs)

    # 池塘信息合并轮廓ID
    ctxx = gpd.sjoin(ctxx, ctlk, how='left')

    # 池塘信息填补合并编号
    ctxx.loc[ctxx['合并id'] == '/', '合并id'] = ctxx[ctxx['合并id'] == '/'].index

    # 排口位置
    pk = pd.read_excel(xls_file, dtype=str, skiprows=1, index_col='池塘id')
    pk = pk[~pk['排口位置'].isnull()]
    pk = pk[pk['排口位置'] != '/']
    pk['longitude'] = pk['排口位置'].str.split('，', expand=True)[0]
    pk['latitude'] = pk['排口位置'].str.split('，', expand=True)[1]
    pk = df2gdf(pk, 'longitude', 'latitude', epsg=4326).to_crs(ctlk.crs)
    pk = pk.drop(columns=['longitude', 'latitude'])

    # 删除已标记删除的数据、所有权人名称为空的数据、测试数据
    ctxx = ctxx[~ctxx['池塘所有权人名称'].isnull()]  # 未提交审核
    ctxx = deleteTestData1(ctxx, '养殖经营人名称', ['张三', '李四', '王五'])  # 完全匹配删除
    ctxx = deleteTestData2(ctxx, '养殖经营人名称', ['李想', '朱曦', '季鹏程', '测试'])  # 模糊匹配删除
    ctxx = deleteTestData1(ctxx, '池塘所有权人名称', ['张三', '李四', '王五'])
    ctxx = deleteTestData2(ctxx, '池塘所有权人名称', ['李想', '朱曦', '季鹏程', '测试'])
    print(ctxx)
    # 删除审核驳回数据
    ctxx = ctxx[~ctxx['状态'].str.contains('未上报|已驳回')]

    # 图斑增加填报主体名称信息
    ctlk = gpd.sjoin(ctlk, ctxx.loc[:, ['geometry', '养殖经营人名称']], how='left')
    # ctlk = gpd.sjoin(ctlk, ctxx.loc[:, ['geometry', '养殖经营人名称','养殖主体类型']], how='left')

    return ctxx, ctlk, pk

def pkAnalysis(sjoins,polygons,psxx):
    sjoins['排口疑点'] = '无异常'
    sjoins = sjoins.to_crs('epsg:32650')
    polygons = polygons.to_crs('epsg:32650')
    psxx = psxx.to_crs('epsg:32650')
    idx = np.unique(psxx['池塘id'].values)
    for i in idx:
        pk = psxx[psxx['池塘id']==i].geometry
        if i in sjoins.index.values:
            try:
                ct = polygons.loc[sjoins.loc[i,'ID'],'geometry'].buffer(200)
            except:
                ct = sjoins.loc[i,'geometry'].buffer(500)
            pkinct = [p.intersects(ct) for p in pk]
            if not all(pkinct):
                sjoins.loc[i,'排口疑点'] = '排口标记较远'

    return sjoins


def AQUATPYDAnalysis(sjoins):
    sjoins['养殖方式疑点'] = '无异常'
    idx1 = sjoins['养殖方式'] == '跑道养鱼'
    idx2 = np.array([True if '蟹' in sjoins['养殖品种/预计亩产量'].values else False])
    idx3 = np.array([True if '虾' in sjoins['养殖品种/预计亩产量'].values else False])
    idx = idx1 & idx2 & idx3
    sjoins.loc[idx,'养殖方式疑点'] = '养殖方式与养殖名称冲突'

    return sjoins

def deleteTestData1(df,field,keywords):
    '''
    按关键字keywords完全匹配删除测试数据
    '''
    # 删除测试数据
    values = df[field].values.tolist()

    test_idx = np.array([True if v in keywords else False for v in values])
    df = df[~test_idx]

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

def is_chinese(str_char):
    str_char = str_char.strip()
    for char in str_char:
        if 'CJK' not in unicodedata.name(char):
            return False
    return True

def is_person(str_char):
    str_char = str_char.strip()
    if not is_chinese(str_char):
        return False
    if len(str_char) > 4:
        return False
    
    pattern = ['村', '街', '社区', '集体', '殖', '场', '公司']      
    for p in pattern:
        if p in str_char:
            return False
    
    
    with open(SURNAME_PATH, 'r', encoding='UTF-8') as f:
        data = f.read()
        f.close()
    p_surname = data.split(',')
    for p in p_surname:
        if p == str_char[:len(p)]:
            return True
    return False

# 判断字符串是否为集体/公司
def is_company(str_char):
    str_char = str_char.strip()
    
    pattern1 = [r'(', r')', r'（', r'）']    
    for p in pattern1:
        str_char = str_char.replace(p, r'')
    
    if not is_chinese(str_char):
        return False
    
    pattern2 = ['镇', '村', '街', '社区', '集体', '居委会', '组',
                '合作社', '养殖场', '农场', '钓场', 
                '厂', '公司', '集团', '研究院','局','种牛场','部','种蜂场','闸管所']
    for p in pattern2:
        if p in str_char:
            return True
   
    return False

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

def isPhoneNumber(phonenumber):
    if (len(phonenumber) != 11) or (not phonenumber.isdigit()):
        return False
    return True

def contractPeriod(sjoins):
    '''
    承包期限疑点
    '''
    sjoins['CBQXYD'] = '无异常'
    time_difference = 0
    if time_difference.days < 10*365:
        return False
    
def idnumberAndZTMCAnalysis(sjoins):
    '''
    分析同主体名、不同身份证号的疑点
    '''
    sjoins['身份证号疑点'] = '无异常'
    grouped = sjoins.groupby(['养殖经营人名称','身份证号'])
    groups = grouped.size().index.values
    name = [g[0] for g in groups]
    idnumber = [g[1] for g in groups]
    # 同证件号不同人名
    dulplicates = getDulplicates(idnumber)
    for d in dulplicates:
        idx = (sjoins['身份证号'] == d)
        sjoins.loc[idx,'身份证号疑点'] += '同身份证号不同人名,'
    # 同人名不同证件号
    dulplicates = getDulplicates(name)
    for d in dulplicates:
        idx = (sjoins['养殖经营人名称'] == d)
        sjoins.loc[idx,'身份证号疑点'] += '同人名不同身份证号,'

    return sjoins

# def MCAnalysis(sjoins):
#     '''
#     所有权人、主体名称、联系人名称异常
#     '''
#     for i,row in sjoins.iterrows():
#         # 所有权人
#         nature = row['ownership']
#         name = row['ownership_user_name']
#         if '家庭农场' in name:
#             yd = ''
#         else:
#             # if (nature == '2') & (len(name)>4 or (not is_chinese(name))):
#             if (nature == '2') & (not is_person(name)):
#                 yd = '所有权人为个人但名称不符,'
#             elif (nature == '1') & (is_person(name)):
#                 yd = '所有权人为集体但名称不符,'
#             else:
#                 yd = ''

#         # 主体
#         nature = row['subject_nature']
#         name = row['subject_name']
#         if '家庭农场' in name:
#             yd += ''
#         else:
#             # if (nature == '1') & (len(name)>4 or (not is_chinese(name))):
#             if (nature == '2') & (len(name)>4 or (not is_chinese(name))):
#                 yd += '主体性质为个人但名称不符,'
#             elif (nature == '2') & (is_person(name)):
#                 yd += '主体性质为集体但名称不符,'

#         # 联系人长度大于4，或字符串中有非中文字符
#         name = row['contacts']
#         if (len(name)>4) or (not is_chinese(name)):
#             yd += '联系人非人名,'
#         sjoins.loc[i,'MCYD'] = yd[0:-1]

#     sjoins.loc[sjoins['MCYD']=='','MCYD'] = '无异常'

#     return sjoins

def MCAnalysis(df):
    for i in df.index:
        nature = df.loc[i, '池塘所有权']
        name = df.loc[i, '池塘所有权人名称']
        if (nature != '3') & ('家庭农场' in name):
            yd = ''
        else:
            # 所有权为个人，所有权人名称不是人名
            if (nature == '2') & (not is_person(name)):
                yd = '所有权人名称疑似填写有误（非人名）,'
            
            # 所有权为集体，所有权人名称不是集体/公司
            elif (nature == '1') & (not is_company(name)):
                yd = '所有权人名称疑似填写有误（非集体/公司）,'
                    
            # 所有权为国有（其他），所有权名称不是人名且不是集体/公司
            elif (nature == '3') & ((is_company(name) or is_person(name)) or ('家庭农场' in name)):
                yd = '所有权人名称疑似填写有误（集体/公司、个人）,' 

            else:
                yd = ''

        nature = df.loc[i, '养殖主体类型']
        name = df.loc[i, '养殖经营人名称']
        if (nature != '3') & ('家庭农场' in name):
            yd += ''
        else:
            # 主体性质为个人，主体名称不是人名
            if (nature == '1') & (not is_person(name)):
                yd += '主体名称疑似填写有误（非人名）,'
                    
            # 主体性质为集体/公司，但名称不是公司
            elif (nature == '2') & (not is_company(name)):
                yd += '主体名称疑似填写有误（非集体/公司）,'
                    
            # 主体性质为其他，但主体名称是个人或集体/公司
            elif (nature == '3'):
                if (not is_chinese(name)):
                    yd += '主体名称疑似填写有误（非中文）,'
                
                if is_company(name) or is_person(name) or ('家庭农场' in name):
                    yd += '主体性质疑似填写有误,'        
            
            # 联系人不是人名
            name = df.loc[i, 'contacts']
            if not is_person(name):
                yd += '联系人疑似填写有误（非人名）,'

            # 人名疑似笔误
            if is_person_similar(df.loc[i, 'ownership_user_name'], df.loc[i, 'subject_name']) and (df.loc[i, 'ownership_user_name'] != df.loc[i, 'subject_name']):
                yd += '人名疑似笔误,'

        df.loc[i,'名称疑点'] = yd[0:-1]

    df.loc[df['名称疑点']=='','名称疑点'] = '无异常'

    return df

def contractTimeAnalysis(sjoins):
    '''
    承包期限
    '''
    sjoins['承包期限疑点'] = '无异常'
    #  所有权人名称和主体名称不一致，承包期限未填写
    idx = (sjoins['池塘所有权人名称']!=sjoins['养殖经营人名称']) & (sjoins['承包期限'].isnull() | sjoins['承包期限']=='/')
    sjoins.loc[idx,'承包期限疑点'] = '主体与所有权人不同但承包期限未填写'

    idx = (~sjoins['承包期限'].isnull()) & (sjoins['承包期限']!='/')
    idx = sjoins[idx].index
    for i in idx:
        contract_endtime = sjoins.loc[i, '承包期限'].split(' : ')[1]
        if is_person_similar(sjoins.loc[i, '池塘所有权人名称'], sjoins.loc[i, '养殖经营人名称']):
            time_difference = datetime.strptime(contract_endtime, "%Y-%m-%d") - datetime.now()
            if time_difference.days < 10*365:
                sjoins.loc[i, '承包期限疑点'] = sjoins.loc[i, '承包期限疑点'] + ',承包结束时间疑似过短' 

    return sjoins

def toExcelByQZX(outpath,df,field):
    '''
    按字段唯一值分sheet输出表格
    '''
    df.to_excel(os.path.join(outpath,'总表.xlsx'),sheet_name='总表')
    xzq = np.unique(df[field].values)
    xzq = ['-'.join(x.split('-')[0:-1]) for x in xzq]
    xzq = list(set(xzq))
    address = df[field].str.split('-',expand=True)
    address = address[0] + '-' + address[1] + '-' + address[2] + '-' + address[3]
    for x in xzq:
        subsets = df[address==x]
        subsets.to_excel(os.path.join(outpath,f'{x}.xlsx'))

def toExcelByQZX2(outpath,df,field):
    '''
    按字段唯一值分sheet输出表格,某疑点列全为无异常则该列删除
    '''
    yd_columns = ['名称疑点','位置疑点','水面面积疑点','合同面积疑点','池塘合并疑点','亩产量疑点']
    df.to_excel(os.path.join(outpath,'总表.xlsx'),sheet_name='总表')
    xzq = np.unique(df[field].values)
    xzq = ['-'.join(x.split('-')[0:-1]) for x in xzq]
    xzq = list(set(xzq))
    address = df[field].str.split('-',expand=True)
    address = address[0] + '-' + address[1] + '-' + address[2] + '-' + address[3]
    for x in xzq:
        subsets = df[address==x]
        for c in yd_columns:
            v = np.unique(subsets[c].values)
            if (len(v) == 1) & (v[0] == '无异常'):
                subsets = subsets.drop(columns=[c])
        subsets.to_excel(os.path.join(outpath,f'{x}.xlsx'))

def yieldAnayesis(df):
    '''
    产量疑点：单养河蟹亩产量小于100或大于500作为疑点
    '''
    df['亩产量疑点'] = '无异常'
    idx0 = df['养殖品种'] == '河蟹'
    subsets = df.loc[idx0,:]
    subsets['产量'] = subsets['产量'].astype(int)
    idx = subsets['产量'] < 100
    subsets.loc[idx,'亩产量疑点'] = '河蟹亩产量小于100'
    idx = subsets['产量'] > 500
    subsets.loc[idx,'亩产量疑点'] = '河蟹亩产量大于500'
    df.loc[idx0,'亩产量疑点'] = subsets['亩产量疑点']

    return df

def inXZQH(gdf1,gdf2,shi,xian):
    '''
    填报点是否在行政区划范围内
    '''
    idx = (gdf2['市'] == shi) & (gdf2['NAME'] == xian)
    gdf2 = gdf2[idx].to_crs('epsg:32650')
    gdf2.geometry = gdf2.geometry.buffer(100)
    gdf2 = gdf2.to_crs(gdf1.crs)
    idx = gdf1.geometry.intersects(gdf2.geometry.values[0])
    gdf1.loc[idx,'区划外疑点'] = '无异常'
    gdf1.loc[~idx,'区划外疑点'] = '在区划范围外'

    return gdf1

# 删除异常填报养殖名称的条目，合并同类养殖名称的条目
def clean_data_by_variety(df):
    # 剔除异常填报品种的条目
    df3 = df.copy()
    for var in df3.loc[:,'variety_name'].unique():
        if len(var.split(',')) > len(set(var.split(','))):
            # print(var)
            # print(df3.loc[df3['名称'] == var].index)
            df3.drop(index=df3.loc[df['variety_name'] == var].index, inplace=True)
    
    # 生成主要养殖品种（去重）
    var_seq = df3.loc[:,'variety_name'].unique()
    var_freq = np.zeros(len(var_seq))

    for i in range(len(var_seq) - 1):
        for j in range(i + 1, len(var_seq)):
            if set(var_seq[i].split(',')) == set(var_seq[j].split(',')):
                var_freq[j] = var_freq[j] + 1
    var_unique = var_seq[var_freq == 0]
    
    # 增加一列，存放修改后的养殖品种和亩产量
    df3['养殖品种修正'] = ''
    df3['亩产量修正'] = ''
    for i in df3.index:
        var0 = df3.loc[i, 'variety_name']
        var_vol0 = df3.loc[i, 'yield']
        for var in var_unique:
            if (set(var0.split(',')) == set(var.split(','))):
                v0_seq = np.array(var0.split(','))
                vq_seq = np.array(var.split(','))
                vol0_seq = np.array(var_vol0.split(','))
                var_vol1 = ''
                for vq in vq_seq:
                    var_vol1 = var_vol1 + str(vol0_seq[v0_seq == vq][0]) + ','
                var_vol1 = var_vol1[:-1]

                df3.loc[i, '养殖品种修正'] = var
                df3.loc[i, '亩产量修正'] = var_vol1

    df3['variety_name'] = df3['养殖品种修正']
    df3['yield'] = df3['亩产量修正']

    return df3.drop(columns=['养殖品种修正','亩产量修正'])

# 增加镇名称栏，为各镇街中文名称
def add_regionname(df, df_regioncode):
    df1 = df.copy()
    df1['镇名称'] = ''
    for i in df1.index:
        for j in df_regioncode.index:
            if int(df1.loc[i, 'town_code']) == df_regioncode.loc[j,'code']/1000:
                regionname = df_regioncode.copy().loc[j,'街道']
                df1.loc[i, '镇名称'] = regionname
                break
    df1['town_code'] = df1['镇名称']

    return df1.drop(columns=['镇名称'])

# def locationAnalysis(sjoins,polygons):
#     # 点不在图斑内
#     sjoins['IDYD'] = '无异常'
#     sjoins.loc[sjoins['index_right'].isnull(),'IDYD'] = '无对应图斑'
    
#     # 1个图斑有多个点
#     dulplicates = getDulplicates(sjoins['ID'].values) # ID来自polygon ID
#     dulplicates = dulplicates[~np.isnan(dulplicates)]
#     for d in dulplicates:
#         idx = sjoins['ID']==d
#         idx_str = ','.join(sjoins[idx].index.values.tolist())
#         sjoins.loc[idx,'IDYD'] = idx_str+'对应同一图斑'
    
#     # 图斑内无点
#     polygons['IDYD'] = ''
#     registered = np.unique(sjoins['ID'].values)
#     registered = registered[~np.isnan(registered)]
#     polygons.loc[registered,'IDYD'] = '已填报'
#     polygons.loc[polygons['IDYD']=='','IDYD'] = '未填报'
#     polygons.loc[dulplicates,'IDYD'] = '多次填报'

#     # 新增填报状态：已填报养殖、已填报非养殖、未填报
#     polygons['status'] = '未填报'
#     idx = (polygons['subject_name']=='未养殖') | ((polygons['subject_name']=='退养') | (polygons['subject_name']=='水库'))
#     polygons.loc[idx,'IDYD'] = '已填报非养殖'
#     idx = (~polygons['subject_name'].isnull()) & (polygons['subject_name']!='未养殖') & ((polygons['subject_name']!='退养') & (polygons['subject_name']!='水库'))
#     polygons.loc[idx,'IDYD'] = '已填报养殖'

#     return polygons

def locationAnalysis(sjoins, polygons):
    # 点不在图斑内
    sjoins['位置疑点'] = '无异常'
    sjoins.loc[sjoins['index_right'].isnull(), '位置疑点'] = '无对应图斑'

    # 1个图斑有多个点
    dulplicates = getDulplicates(sjoins['ID'].values)  # ID来自polygon ID
    dulplicates = dulplicates[~np.isnan(dulplicates)]
    for d in dulplicates:
        idx = sjoins['ID'] == d
        idx_str = ','.join(sjoins[idx].index.values.astype('str').tolist())
        sjoins.loc[idx, '位置疑点'] = idx_str + '对应同一图斑'

    # 图斑内无点
    polygons['位置疑点'] = ''
    registered = np.unique(sjoins['ID'].values)
    registered = registered[~np.isnan(registered)]
    polygons.loc[registered, '位置疑点'] = '已填报'
    polygons.loc[polygons['位置疑点'] == '', '位置疑点'] = '未填报'
    polygons.loc[dulplicates, '位置疑点'] = '多次填报'

    # 新增填报状态：已填报养殖、已填报非养殖、未填报
    polygons['status'] = '未填报'
    idx = (polygons['养殖经营人名称'] == '未养殖') | (
                (polygons['养殖经营人名称'] == '退养') | (polygons['养殖经营人名称'] == '水库') | (
                    polygons['养殖经营人名称'] == '光伏'))
    polygons.loc[idx, 'status'] = '已填报非养殖'
    idx = (~polygons['养殖经营人名称'].isnull()) & (polygons['养殖经营人名称'] != '未养殖') & (
                (polygons['养殖经营人名称'] != '退养') & (polygons['养殖经营人名称'] != '水库') & (
                    polygons['养殖经营人名称'] != '光伏'))
    polygons.loc[idx, 'status'] = '已填报养殖'

    return sjoins, polygons


def statusAnalysis(gdf0,xlsfile,shppath):
    '''
    根据excel表补充已填报非养殖
    '''
    dfs = pd.read_excel(xlsfile,sheet_name=None)
    idx = []
    for k in list(dfs.keys()):
        gdf = gpd.read_file(f'{shppath}\\{k}养殖池塘.gpkg').set_index('CTBH')
        gdf['ID'] = gdf['ID'].astype('int')
        df = dfs[k]
        ctbh = df['CTBH'].values
        ids = gdf.loc[ctbh,'ID'].values
        idx.append(ids)
    idx = np.unique(np.hstack(idx))
    gdf0.loc[idx,'status'] = '已上报非养殖'

    return gdf0

def statusAnalysis2(gdf0,xlsfile,shppath):
    '''
    根据excel表补充光伏
    '''
    dfs = pd.read_excel(xlsfile,sheet_name=None)
    idx = []
    for k in list(dfs.keys()):
        gdf = gpd.read_file(f'{shppath}\\{k}养殖池塘.gpkg').set_index('CTBH')
        gdf['ID'] = gdf['ID'].astype('int')
        df = dfs[k]
        ctbh = df['CTBH'].values
        ids = gdf.loc[ctbh,'ID'].values
        idx.append(ids)
    idx = np.unique(np.hstack(idx))
    gdf0.loc[idx,'status'] = '已上报光伏'

    return gdf0

def YZLXAnalysis(sjoins,lctable):
    sjoins['YZLXYD'] = '无异常'
    for i in sjoins.index:
        # 用户填报类型
        yzlx1 = sjoins.loc[i,'variety_name']
        if isinstance(yzlx1,str):
            try:
                yzlx1 = np.array([lctable.loc[y,'YZLX'] for y in yzlx1.split(',')])
                yzlx1 = np.nanmin(yzlx1)
                # 卫星监测类型
                if (~np.isnan(yzlx1)) & (sjoins.loc[i,'area']>5):
                    yzlx2 = sjoins.loc[i,'YZLX']
                    if yzlx2!=yzlx1:
                        sjoins.loc[i,'YZLXYD'] = '养殖类型疑点'
            except:
                continue

    return sjoins
