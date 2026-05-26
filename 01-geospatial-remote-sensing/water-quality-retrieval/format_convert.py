'''
@Time    :   2022/02/23
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 断面溯源数据kml、shp、json格式转换
'''

import os
import glob
import shutil

import geopandas as gpd
import fiona
from shapely import wkt

fiona.supported_drivers['KML'] = 'rw'

def shp2json(shppath,inplace=True,keywords=''):
    '''
    功能：shp数据转出为json，在shp的同目录下生成json文件夹，存放对应格式数据
    shppath：待转换shp文件的存放路径
    inplace：bool 若工作路径已存在json文件夹，文件夹是否整个删除替换。若True，删除原文件夹，创建新的；若False，保留原文件夹，只替换同名文件
    keywords：str 可按关键字转换shp文件夹中特定的文件
    '''
    # 工作路径
    workpath = os.path.dirname(shppath)

    # 创建json文件存储路径
    jsonpath = os.path.join(workpath,'json')
    if not os.path.exists(jsonpath):
        os.mkdir(jsonpath)
    else:
        if inplace:
            shutil.rmtree(jsonpath)
            os.mkdir(jsonpath)

    # 转换
    shpfiles = glob.glob(shppath+'\\*'+keywords+'*.shp')
    for shpfile in shpfiles:
        gdf = gpd.read_file(shpfile)
        gdf = gdf.to_crs('epsg:4326')
        if gdf.geom_type[0] == 'Point':

            gdf = setCordinatesPrecision(gdf)
        basename = os.path.basename(shpfile)[0:-4]
        basename = basename.replace('静态数据','')
        gdf.to_file(os.path.join(jsonpath, basename + ".json"), driver="GeoJSON", encoding="utf-8")

def shp2kml(shppath,inplace=True,keywords=''):
    '''
    功能：shp数据转出为kml，在shp的同目录下生成kml文件夹，存放对应格式数据
    shppath：待转换shp文件的存放路径
    inplace：bool 若工作路径已存在json文件夹，文件夹是否整个删除替换。若True，删除原文件夹，创建新的；若False，保留原文件夹，只替换同名文件
    keywords：str 可按关键字转换shp文件夹中特定的文件
    '''
    # 工作路径
    workpath = os.path.dirname(shppath)

    # 创建kml文件存储路径
    kmlpath = os.path.join(workpath,'kml')
    print(kmlpath)
    if not os.path.exists(kmlpath):
        os.mkdir(kmlpath)
    else:
        if inplace:
            shutil.rmtree(kmlpath)
            os.mkdir(kmlpath)

    # 转换
    shpfiles = glob.glob(shppath+'\\*'+keywords+'*.shp')
    for shpfile in shpfiles:
        gdf = gpd.read_file(shpfile)
        basename = os.path.basename(shpfile)[0:-4]
        basename = basename.replace('静态数据','')
        outfile = os.path.join(kmlpath, basename + ".kml")
        if os.path.exists(outfile):
            os.remove(outfile)
        gdf.to_file(outfile, driver='KML')


def setCordinatesPrecision(gdf,precision=6):
    '''
    功能：设置坐标小数点后位数
    shpfile: gaopandas对象
    precision: 小数点精度
    返回：修改后的gdf
    '''
    x = gdf['geometry'].x.round(int(precision)).astype('str')
    y = gdf['geometry'].y.round(int(precision)).astype('str')
    for i in range(len(x)):
        gdf.loc[i,'wkt_str'] = 'POINT (' + x[i] + ' ' + y[i] + ')'
    gdf['geometry'] = gdf['wkt_str'].apply(wkt.loads)
    gdf = gdf.drop(['wkt_str'], axis=1)

    return gdf
import math

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 偏心率平方

def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>谷歌、高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return [gg_lng, gg_lat]

def gcj02_to_wgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return [lng, lat]
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def bd09_to_wgs84(bd_lon, bd_lat):
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)

def _transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """


if __name__ == '__main__':
    # shp转json示例
    shppath0 = r'D:\Users\Administrator\Desktop\kml转geson\新建文件夹'
    shp2json(shppath0)
    
    # # file_list = ['断面基础信息','断面区域问题','断面区域源清单','断面整治工程项目']
    file_list = ['淮沭新河蔷薇河']
    #
    for f in file_list:
        shppath = os.path.join(shppath0,f,'shp')
        shp2json(shppath)


    # # shp转kml示例
    # shppath0 = r'D:\Users\Administrator\Desktop\kml转geson\新建文件夹'
    # # file_list = ['断面基础信息','断面区域问题','断面区域源清单','断面整治工程项目']
    # file_list = ['淮沭新河蔷薇河']
    # for f in file_list:
    #     shppath = os.path.join(shppath0, f, 'shp')
    #
    #     shp2kml(shppath)

