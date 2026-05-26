'''
@Time    :   2021/04/28
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 哨兵产品自动推送。
'''
from geoserver import store
import geomProcess
import os
import glob
import pandas as pd
import time
import kml2geojson as k2g
import shutil
import geopandas as gpd
import upload_geotiff as geoserver
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import imgProcess as imgpro
import datetime
from sentinelsat import SentinelAPI,read_geojson,geojson_to_wkt
import Sentinel2Process as s2pro

# 创建所有服务区域的kml列表，columns = ['filename','suffix']
def creatDF_from_files(path):
    df = pd.DataFrame([],columns = ['filename','suffix'])
    files = os.listdir(path)
    i = 0
    for f in files:
        if f.endswith(".kml") or f.endswith(".kmz"):
            df.loc[i,'filename'] = f.split(".")[0]
            df.loc[i,'suffix'] = "." + f.split(".")[1]
            i = i + 1
    return df

# 根据待筛选kml列表和已登记申请列表，划分待更新数据集、新增数据集
def devide_dataset(new_set,re_set):
    '''
    new_set:  columns = ['filename','suffix']
    re_set:   columns = ['申请人','申请范围','申请日期','数据存储地址','数据更新时间','temp']
    '''
    print(re_set)
    df = pd.DataFrame([],columns = ['filename','suffix'])
    k = 0
    for i in range(len(new_set['filename'])):
        filename = new_set.loc[i,'filename'].replace('_','')
        print(filename)
        if filename not in re_set['temp'].values.tolist():            
            df.loc[k,'filename'] = new_set.loc[i,'filename']
            df.loc[k,'suffix'] = new_set.loc[i,'suffix']
            k = k + 1
    return df

# 从数据集imgPath0中筛选满足空间（roi_shp）、时间（startpoint）要求的子集  
# 并拷贝至roi_shp所在的文件目录下
def selectSatisfiedImages(imgPath0,roi_shp,startpoint = 0):
    # 目标路径
    des_path = os.path.dirname(roi_shp)
    # 提取满足时间条件的路径
    files = os.listdir(imgPath0)
    subpath = []
    for f in files:
        if f.startswith('20'):
            t = int(f)
            if t > startpoint:
                subpath.append(f)
    # 在满足时间条件的路径中筛选满足空间条件的文件
    for p in subpath:
        coverage_path = os.path.join(imgPath0,p,'coverage')
        if os.path.exists(coverage_path):
            os.chdir(coverage_path)
            shpfiles = glob.glob("*.shp")
            for shpfile in shpfiles:                
                if geomProcess.isIntersect(roi_shp,shpfile):
                    print("sucess ",shpfile)
                    filename = shpfile.split('.')[0]
                    filename = filename.replace("_COV","")
                    # 拷贝反射率图像
                    ori_file = os.path.join(imgPath0,p,'RGB',filename+"_RGB.tif")
                    des_file = os.path.join(des_path,filename+"_RGB.tif")
                    shutil.copyfile(ori_file,des_file)
                    # 拷贝水质分布图
                    ori_path = os.path.join(imgPath0,p,'waterQA')
                    files = os.listdir(ori_path)
                    for f in files:
                        if filename in f:
                            ori_file = os.path.join(ori_path,f)
                            des_file = os.path.join(des_path,f)
                            shutil.copyfile(ori_file,des_file)

'''
功能1：提取文件
path：路径下存放多个目标区域的kml文件（kml命名 user_area_time）
regis_table：记录了已提取的文件信息（申请人 申请日期 申请范围 数据存储地址 数据更新日期）
imgPath0：待筛选数据集的存放路径
'''
def extractProducts(path,imgPath0,regis_table):
    re_set = pd.read_excel(regis_table,dtype={'申请日期':str}) # re_set:   columns = ['申请人','申请范围','申请日期','数据存储地址','数据更新时间']
    re_set['temp'] = re_set['申请人'] + re_set['申请范围'] + re_set['申请日期']
    re_set_num = len(re_set['申请人'])
    new_set = creatDF_from_files(path)  # new_set:  columns = ['filename','suffix']
    new_set = devide_dataset(new_set,re_set)
    # 已登记的申请，按时间更新数据
    # for i in range(re_set_num):
    #     subpath = re_set.loc[i,'数据存储地址']
    #     roi_shp = re_set.loc[i,'申请范围'] + re_set.loc[i,'申请日期'] + '.shp'
    #     roi_shp = os.path.join(subpath,roi_shp)
    #     selectSatisfiedImages(imgPath0,roi_shp,startpoint = int(re_set.loc[i,'数据更新日期']))
    #     re_set.loc[i,'数据更新日期'] = time.strftime("%Y%m%d")        
    # 未登记的申请，登记、创建矢量范围并选择满足条件的数据
    for i in range(len(new_set['filename'])):
        user,area,date = new_set.loc[i,'filename'].split('_')
        subpath = os.path.join(path,area+date)
        if not os.path.exists(subpath):
            os.mkdir(subpath)
        roi_kml = os.path.join(path,new_set.loc[i,'filename']+new_set.loc[i,'suffix'])  # user_area_date.kml
        roi_shp = os.path.join(subpath,area+date+".shp")           # area_date.shp
        roi_gdf = geomProcess.kmlread(roi_kml)
        roi_gdf.to_file(roi_shp)
        selectSatisfiedImages(imgPath0,roi_shp)
        re_set.loc[re_set_num+i,'申请人'] = user
        re_set.loc[re_set_num+i,'申请范围'] = area
        re_set.loc[re_set_num+i,'申请日期'] = date
        re_set.loc[re_set_num+i,'数据存储地址'] = subpath
        re_set.loc[re_set_num+i,'数据更新日期'] = time.strftime("%Y%m%d")  
    new_reset = re_set.drop('temp',axis=1)
    new_reset.to_excel(regis_table,index=False)
    return new_reset

'''
功能2：根据服务表单依次发布产品的地图服务
dataset: cloumns = ['申请人','申请范围','申请日期','数据存储地址','数据更新日期']
'''
def releaseProducts(dataset):
    datapath = dataset['数据存储地址']
    num = len(datapath)
    for i in range(num):
        datapath = dataset.loc[i,'数据存储地址']
        area = dataset.loc[i,'申请范围']
        os.chdir(datapath)
        tiffiles = glob.glob("*.tif")
        for tiffile in tiffiles:
            product_name = tiffile.replace(".tif","")
            product_type = product_name.split('_')[-1]   # 产品类型，如SD
            tifstyle = product_type + "_normal"     # 产品发布样式，如SD_normal
            timestr = product_name.split("_")[2]
            store_name = area + '_' + product_type + '_' + timestr     # 产品发布图层名，如沱湖_SD_20210502T050444
            destFile = os.path.join(datapath,tiffile)                  
            geoserver.uploadGeotiff(store_name,destFile,workspace="Sentinel2AutoServe",style=tifstyle)

'''
功能3：根据服务列表依次输出缩略图
'''
def visualizeProducts(dataset):
    datapath = dataset['数据存储地址']
    num = len(datapath)
    for i in range(num):
        path = datapath[i]
        os.chdir(path)
        tiffiles = glob.glob("*.tif")
        for tiffile in tiffiles:
            if tiffile.endswith("_SD.tif"):
                imgpro.gray2colors(tiffile,uplimit=10)

# 统计某地区某时间段内云量大于10%的有效数据量
def s2VirtualProductsNum(area,dates):
    # 连接服务器
    user=''
    password=''
    site='https://scihub.copernicus.eu/dhus'
    api=SentinelAPI(user,password,site)
    # 检索条件
    footprint=geojson_to_wkt(read_geojson(area))
    platformname = 'Sentinel-2'     # 平台
    processinglevel = 'Level-2A'    # 产品级别
    cloud = (0,10)                  # 云量
    # 检索
    products=api.query(footprint,date=dates, \
            platformname=platformname, \
                processinglevel = processinglevel, \
                    cloudcoverpercentage = cloud)
    products_df=api.to_dataframe(products)
    # 统计数量
    num = len(products_df)
    return num

'''
功能4：统计某地区一年内的有效观测频次
统计条件：范围area[*.geojson]自定义，开始时间starttime默认“202001”，统计周期为365天
'''
def s2ServeFrequence(area,starttime="20210101"):
    # area = r'I:\Sentinel2_DATA\服务频次统计\JS.geojson'    
    # starttime = '20200101'    # 00:00:00
    # 输出文件
    path = os.path.dirname(area)
    filename = os.path.basename(area)
    filename = os.path.join(path,filename.replace(".geojson",".xls"))
    starttime = datetime.datetime.strptime(starttime,'%Y%m%d').date() # %H:%M:%S
    df = pd.DataFrame([],columns=['time','num']) 
    for i in range(365):        
        st_time = starttime + datetime.timedelta(days=i)
        print(st_time)
        ed_time = starttime + datetime.timedelta(days=i+1)
        dates = (st_time.strftime("%Y%m%d"),ed_time.strftime("%Y%m%d"))
        df.loc[i,'num'] = s2VirtualProductsNum(area,dates)
        df.loc[i,'time'] = st_time.strftime("%Y%m%d")
    df.to_excel(filename)


if __name__=="__main__":
    # # 模块1：数据检索
    # path = r'I:\Sentinel2_DATA\申请服务项目'
    # imgPath0 = r'I:\Sentinel2_DATA'
    # regis_table = r'I:\Sentinel2_DATA\申请服务项目\申请列表.xlsx'
    # dataset_df = extractProducts(path,imgPath0,regis_table)


    # 模块2：服务频次统计
    # area=r'I:\Sentinel2_DATA\服务频次统计\盐河流域.geojson'
    # area=r'I:\Sentinel2_DATA\服务频次统计\LYG.geojson'
    # s2ServeFrequence(area)

    # 模块3：DELETE SAFE FILES
    # path = r'I:\Sentinel2_DATA'
    # os.chdir(path)
    # files0 = glob.glob("2021*")
    # for f0 in files0:
    #     os.chdir(os.path.join(path,f0))
    #     files1 = glob.glob("*.SAFE")
    #     for f1 in files1:
    #         shutil.rmtree(f1)

    # 模块4：图层发布
    # path0  = r'I:\Sentinel2_DATA'
    # pathes = glob.glob(path0+"\\20*")
    # for path in pathes:
    #     # path = r'I:\Sentinel2_DATA\20210531'
    #     print(path)
    #     RGBPath = os.path.join(path,"RGB")
    #     waterQAPath = os.path.join(path,"waterQA")
    #     covPath = os.path.join(path,"coverage")
    #     # 发布RGB产品
    #     RGBfiles = glob.glob(RGBPath+"\\*.tif")
    #     for RGBfile in RGBfiles:
    #         store_name = os.path.basename(RGBfile)[0:-4]
    #         geoserver.uploadGeotiff(store_name,RGBfile,workspace="ad",style="S2_RGB")
    #     # 发布waterQA-SD产品
    #     QAfiles = glob.glob(waterQAPath+"\\*SD.tif")
    #     for QAfile in QAfiles:
    #         store_name = os.path.basename(QAfile)[0:-4]
    #         geoserver.uploadGeotiff(store_name,QAfile,workspace="ad",style="S2_SD")
    #     # 发布产品范围
    #     COVfiles = glob.glob(covPath+"\\*.shp")
    #     print(COVfiles)
    #     for COVfile in COVfiles:
    #         store_name = os.path.basename(COVfile)[0:-4]
    #         print(store_name)
    #         geoserver.uploadShp(store_name,COVfile,workspace="ad")

    # 模块5：设置背景为空
    # path = r'I:\Sentinel2_DATA'
    # subpathes = glob.glob(path+"\\20*")
    # for subpath in subpathes:
    #     RGBPath = os.path.join(subpath,"RGB")
    #     RGBFiles = glob.glob(RGBPath+"\\*_RGB.tif")
    #     for RGBFile in RGBFiles:
    #         geotiff = imgpro.geotiffread(RGBFile)
    #         data = geotiff.dataarray
    #         imgpro.geotiffwrite(os.path.join(RGBPath,"temp.tif"),data,geotiff.geo_transform,geotiff.projection,datatype="UINT8",nodata_value=0)
    #         os.remove(RGBFile)
    #         os.rename(os.path.join(RGBPath,"temp.tif"),RGBFile)

    # # # 模块6：水色分布产品制作
    pathes = [r'F:\S2Data\anhuisuzhou\new']
    for path in pathes:
        os.chdir(path)
        s2pro.getImgGroups(path)
        s2pro.getWaterREF(path)
        s2pro.algoProc1(path)



