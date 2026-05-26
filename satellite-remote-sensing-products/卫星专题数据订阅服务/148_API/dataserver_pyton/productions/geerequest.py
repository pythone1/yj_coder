import os
import ee
import geemap
import geopandas as gpd
import json

# #配置代理地址
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10809'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10809'

# # GEE初始化
ee.Initialize()

def requestPrecipitationProductsInfo(daterange):
    '''
    查询降雨量数据
    :param daterange: cell(str,str) 检索时间范围
    :return:
    '''
    products = ee.ImageCollection('NASA/GPM_L3/IMERG_V06') \
                .filterDate(daterange[0],daterange[1]) \
                .select(['precipitationCal'])
    return products

def extract_precipitation(lat,lon, products):
    '''
    功能：提取降水数据
    lat,lon: wkt格式的文本，经纬度坐标
    products: collections.OrderedDict 待下载影像产品
    savepath: str 保存路径
    返回:
    precipitation_point:dict  降雨数据
    '''
    #按点提取栅格值
    point_geom=ee.Geometry.Point(lat, lon)
    precipitation_point=geemap.extract_pixel_values(products, region=point_geom).getInfo()

    return precipitation_point


