import requests
import math
import json
import pandas as pd
import geopandas as gpd
from shapely import wkt

def searchPOIsAround(center_xy,poi_name,distance,key):
    '''
    功能：按坐标、距离半径检索POI(检索所有结果),检索结果以表格形式输出到内容框
    center_xy: str 经度,纬度
    poi_name：str POI类型
    distance: int 检索半径 单位米
    key: str 高德key
    '''
    poi_code = getCode(poi_name)

    offset = 25
    totalnum,result_df = searchPOIsAroundByPage(center_xy,poi_code,distance,page=1,key=key,offset=offset)
    if offset < totalnum:
        page_num = math.ceil(totalnum / offset)
        for page in range(2, page_num + 1):
            totalnum,page_df = searchPOIsAroundByPage(center_xy, poi_code, distance, page, key, offset)
            result_df = pd.concat([result_df,page_df],axis=0,ignore_index=True)

    result_gdf = df2gdf(result_df, '经度', '纬度', epsg=4326)

    return result_gdf

def searchPOIsAroundByPage(center_xy,poi_code,distance,page,key,offset=25):
    '''
    功能：按坐标、距离半径检索POI(检索某一页)
    center_xy: str 经度,纬度
    poi_code：str POI类型对应的编码
    distance: int 检索半径 单位米
    page: int 检索页
    key: str 高德key
    offset: int 每页检索结果的数量
    '''
    url = 'https://restapi.amap.com/v3/place/around?parameters'
    parameters = {
        'key': key,
        'location': center_xy,
        'types': poi_code,
        'radius': str(distance),  # 搜索半径,单位米
        'sortrule': 'distance',  # 按距离排序
        'offset': offset,
        'page': page,
        'extensions': 'all'
    }

    s = requests.session()
    s.trust_env = False
    res = s.get(url=url, params=parameters)  # 检索
    json_data = json.loads(res.text)
    status = json_data['status']  # 检索成功标识

    df = pd.DataFrame([], columns=['名称', '省', '市', '经度', '纬度', '类型'])
    poi_num = 0
    if int(status) > 0:
        poi_num = int(json_data['count'])
        pois = json_data['pois']
        for i, poi in enumerate(pois):
            df.loc[i, '名称'] = poi['name']
            df.loc[i, '省'] = poi['pname']
            df.loc[i, '市'] = poi['adname']
            df.loc[i, '经度':'纬度'] = list(map(float, poi['location'].split(",")))
            df.loc[i, '类型'] = poi['type']  # 存在一个对象同属多种类型的情况，多种类型间用|分隔，同种类型不同等级用,分隔

    return poi_num, df

def getCode(poi_name):
    '''
    功能：查找POI类型对应的编码
    '''
    poi_dict = {
        '公司企业': '170000',
        '汽车服务': '010000',
        '汽车销售': '020000',
        '汽车维修': '030000',
        '摩托车服务': '040000',
        '餐饮服务': '050000',
        '购物服务': '060000',
        '生活服务': '070000',
        '体育休闲服务': '080000',
        '医疗保健服务': '090000',
        '住宿服务': '100000',
        '风景名胜': '110000',
        '商务住宅': '120000',
        '政府机构及社会团体': '130000',
        '科教文化服务': '140000',
        '交通设施服务': '150000',
        '金融保险服务': '160000',
        '道路附属设施': '180000',
        '地名地址信息': '190000',
        '公共设施': '200000',
        '事件活动': '220000',
        '室内设施': '970000',
        '通行设施': '990000'
    }

    return poi_dict.get(poi_name)


def df2gdf(df, lon_col, lat_col, epsg=4326):
    '''
    功能：df对象转gdf
    df: pd.DataFrame 数据表，含经纬度数据列
    lon_col: str 经度对应的列名
    lat_col: str 纬度对应的列名
    epsg: int 坐标系对应的编号，默认4326 WGS-1984
    '''
    for i in df.index:
        df.loc[i, 'wkt_str'] = 'POINT (' + str(df.loc[i, lon_col]) + ' ' + str(df.loc[i, lat_col]) + ')'

    df['geometry'] = df['wkt_str'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs='EPSG:' + str(epsg), geometry=df['geometry'])
    gdf = gdf.drop('wkt_str', axis=1)

    return gdf

if __name__ == '__main__':
    # 函数调用示例
    center_xy = '120.1546,33.8829'
    poi_name = '公司企业'
    distance = 50000 # 单位米
    result = searchPOIsAround(center_xy,poi_name,distance)

    print(result)