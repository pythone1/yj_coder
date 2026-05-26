import os
import geopandas as gpd

from sentinelsat import SentinelAPI

def createAPI(user,password,site='https://scihub.copernicus.eu/dhus'):
    '''
    创建数据查询下载的API
    :param user: str 用户名
    :param password: str 密码
    :param site: str sichub官网
    :return: api sentinelsat.sentinel.SentinelAPI
    '''
    sentinel_api = SentinelAPI(user,password,site)

    return sentinel_api

def requestS1ProductsInfo(sentinel_api,footprint,daterange,product_type='GRD',sense_mode='IW',platform='Sentinel-1'):
    '''
    查询哨兵一号产品列表
    :param sentinel_api: sentinelsat.sentinel.SentinelAPI
    :param footprint: str wkt格式存储的区域范围
    :param daterange: cell(str,str)  检索时间范围
    :param product_type: str 产品类型，可选 SLC GRD OCN RAW
    :param sense_mode: str 扫描模式，Sentinel-1可选 SLC, GRD, OCN
    :param platform: str 平台，默认Sentinel-1
    sentinel_api.query其他参数说明见
    https://link.csdn.net/?target=https%3A%2F%2Fscihub.copernicus.eu%2Ftwiki%2Fdo%2Fview%2FSciHub
    UserGuide%2FFullTextSearch%3Fredirectedfrom%3DSciHubUserGuide.3FullTextSearch
    :return products: collections.OrderedDict
    :return file_list: list[str] 查询的文件名列表
    '''
    products = sentinel_api.query(footprint,
                                  date=daterange,
                                  platformname=platform,
                                  producttype=product_type,
                                  sensoroperationalmode=sense_mode)

    return products

def requestS2ProductsInfo(sentinel_api,footprint,daterange,product_type='L2A',cloud=(0,20),platform='Sentinel-2'):
    '''
    查询哨兵二号
    :param sentinel_api: sentinelsat.sentinel.SentinelAPI
    :param footprint: str wkt格式存储的区域范围
    :param daterange: cell(str,str) 检索时间范围
    :param product_type: str 产品类型，可选 L1C L2A
    :param cloud: cell(int,int) 云量条件 如(0,20)
    :param platform: str 平台，默认Sentinel-2
    :return:
    '''
    products = sentinel_api.query(footprint, date=daterange, \
                         platformname=platform, \
                         processinglevel=product_type, \
                         cloudcoverpercentage=cloud)

    return products

def getGeometryInfo(json_dict):
    '''
    json格式矢量 转 wkt格式文本，作为哨兵影像查询的输入范围。
    :param json_dict: dict json格式的矢量数据
    :return: wkt_str wkt格式的文本，记录坐标,如 POLYGON((112 32， 113 34, ...))
    '''
    gdf = gpd.GeoDataFrame.from_features(json_dict)
    wkt_str = gdf.loc[0,'geometry'].wkt
    center_x = gdf.loc[0,'geometry'].x
    center_y = gdf.loc[0, 'geometry'].y

    return wkt_str,center_x,center_y

def downloadSentinelProducts(sentinel_api,products,savepath):
    '''
    下载产品
    :param sentinel_api: sentinelsat.sentinel.SentinelAPI
    :param products: collections.OrderedDict 待下载影像产品
    :param savepath: str 保存路径
    :return: list[str] 返回文件名
    '''
    os.chdir(savepath)
    sentinel_api.download_all(products)
    file_list = sentinel_api.to_dataframe(products)['title'].to_list()

    return file_list
