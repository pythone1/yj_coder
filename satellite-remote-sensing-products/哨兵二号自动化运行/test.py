# from scipy.sparse import data

import os
import glob
import numpy as np
# import shutil
import geopandas as gpd  # 必须先导入geopandas再导入gdal!
from osgeo import gdal, osr
from pandas.core.frame import DataFrame
# import  numpy as np
# import matplotlib.pyplot as plt
# import matplotlib as mpl
# import pandas as pd
# # import Sentinel2Process as s2pro

# import upload_geotiff as geoserver
import imgProcess as imgpro
# import ogr
# import geomProcess as geopro
# import pandas as pd# 
# import cv2
from subprocess import call
# from numpy.core.fromnumeric import prod
from sentinelsat import SentinelAPI,read_geojson,geojson_to_wkt
# from datetime import date
# import time
# import xlrd
# from tqdm import tqdm
import zipfile

def unzipfile(filename):
    path = os.path.dirname(filename)
    zip_file = zipfile.ZipFile(filename)
    for f in zip_file.namelist():
        zip_file.extract(f,path)

def getCloudMSK(safe_file):
    granule = os.path.join(safe_file,"GRANULE")
    L2A = glob.glob(granule+"\\*")[0]
    cld_mask = os.path.join(L2A,"QI_DATA","MSK_CLDPRB_20m.jp2")
    return cld_mask

def getDownloadedList(path):
    os.chdir(path)
    df = DataFrame([],columns=['title'])
    files = glob.glob("*.zip")
    for i,f in enumerate(files):
        df.loc[i,'title'] = f[0:-4]
    print(df)
    return df
if __name__ == '__main__':
    # 重新发布
    # path0 = r'I:\Sentinel2_DATA'
    # tifpathes = glob.glob(path0+"\\20*")
    # for tifpath in tifpathes:
    #     QApath = os.path.join(tifpath,"coverage")
    #     if os.path.exists(QApath):            
    #         SDfiles = glob.glob(QApath+"\\*_COV.shp")
    #         for SDfile in SDfiles:
    #             store_name = os.path.basename(SDfile)[0:-4]
    #             # geoserver.uploadGeotiff(store_name,tiffile,workspace="S2Server",style="S2_RGB")
    #             # geoserver.uploadGeotiff(store_name,SDfile,workspace="S2Server",style="S2_COV")
    #             geoserver.uploadShp(store_name,SDfile,workspace="S2Server")
    #             print(SDfile)

    # path0 = r'I:\Sentinel2_DATA'
    # pathes = glob.glob(path0+"\\20*")
    # for path in pathes:
    #     imgfiles = glob.glob(path+"\\*.zip")
    #     for imgfile in imgfiles:  
    #         # 获取云掩膜文件
    #         unzipfile(imgfile)  # 解压
    #         safefile = imgfile.replace(".zip",".SAFE")
    #         f_cloud20m = getCloudMSK(safefile)
    #         d_cloud20m = gdal.Open(f_cloud20m,gdal.GA_ReadOnly)
    #         f_cloud10m = os.path.join(path,"cld_10m.tif")
    #         gdal.Warp(f_cloud10m,d_cloud20m,xRes=10,yRes=10)
    #         geotiff = imgpro.geotiffread(f_cloud20m)
    #         cld20m = geotiff.dataarray[:,:,0]
    #         geotiff = imgpro.geotiffread(f_cloud10m)
    #         cld10m = geotiff.dataarray[:,:,0]
    #         geotiff = None
    #         d_cloud20m = None
    #         os.remove(f_cloud10m)

    #         # 水色产品掩膜
    #         basename = os.path.basename(imgfile).replace(".zip","") 
    #         waterQA = os.path.join(path,"waterQA")
    #         waterQAfiles = glob.glob(waterQA+"\\"+basename+"*.tif")
    #         for waterqafile in waterQAfiles:
    #             dataset = gdal.Open(waterqafile,gdal.GA_Update)
    #             dataarray = dataset.GetRasterBand(1).ReadAsArray()
    #             dataarray[np.isnan(dataarray)] = 0  # 取消空值设置
    #             resolution = dataset.GetGeoTransform()[1]
    #             if resolution == 10:
    #                 dataarray[cld10m>0] = 0
    #             elif resolution == 20:
    #                 dataarray[cld20m>0] = 0
    #             else:
    #                 print("no cloud mask product matched resolution of ",resolution," meters")
    #             dataset.GetRasterBand(1).WriteArray(dataarray)   
                
    
    # 哨兵二号offline自动下载
    # get downloaded list    
    # define IDM
    IDM = r'G:\python方法\PollutionArea\idm\IDM 6.38.1\IDMan.exe'
    DownPath = r'I:\Sentinel2_DATA\20210919' #数据要下载的地址  
    downloaded_list = getDownloadedList(DownPath)
    os.chdir(DownPath)  
    # get products list
    user='wenyansha'
    password='WenYansha12'
    site='https://scihub.copernicus.eu/dhus'
    api=SentinelAPI(user,password,site)
    path0 = r'I:\Sentinel2_DATA'
    geojson=os.path.join(path0,'BEIJING.geojson')    # 范围
    dates=("20210501","20210601")
    platformname = 'Sentinel-2'     # 平台
    processinglevel = 'Level-2A'    # 产品级别
    cloud = (0,10)                  # 云量
    footprint=geojson_to_wkt(read_geojson(geojson))
    products=api.query(footprint,date=dates, \
            platformname=platformname, \
                processinglevel = processinglevel, \
                    cloudcoverpercentage = cloud)
    products_df=api.to_dataframe(products)

    # download or activate products
    if len(products_df)>0:
        # products num
        print('符合条件影像有%d幅'%len(products_df))
        download_list = products_df
        # loop until downdload_list is none        
        while len(products_df)>0:
            n = 0
            product_id = products_df.index[n]
            product_info = api.get_product_odata(product_id)
            if product_info['title'] in downloaded_list['title'].values:
                products_df.drop(product_id,inplace=True)
            else:
                if product_info['Online']:
                    # download
                    link = products_df.loc[product_id,'link']
                    print("download ",product_id)
                    # call([IDM, '/d',link, '/p',DownPath,'/n','/a'])
                    # call([IDM,'/s'])  
                    # CallIDM(urllist, ids,savepath)
                    api.download(product_id)
                    products_df.drop(product_id,inplace=True)                              
                else:
                    # activate
                    api.download(product_id)
                    print("activate ",product_id)
                    product_line = products_df.loc[product_id]
                    products_df.drop(product_id,inplace=True)
                    products_df = products_df.append(product_line)
                    # download online products while waiting an offline product switching to online
                    if len(products_df) > 1:
                        for i in range(1,len(products_df)):
                            product_id2 = products_df.index[i]
                            product_info2 = api.get_product_odata(product_id)
                            if product_info2['title'] in downloaded_list['titile'].values:
                                products_df.drop(product_id2,inplace=True)
                            else:
                                if product_info2['Online']:
                                    link = products_df.loc[product_id2,'link']
                                    print("download ",product_id2)
                                    # call([IDM, '/d',link, '/p',DownPath,'/n','/a'])
                                    # call([IDM,'/s']) 
                                    api.download(product_id2)
                                    products_df.drop(product_id2,inplace=True)                            
                                    break     
                                else:
                                    continue
    else:
        print('未找到符合条件影像')

    # IDM = r"G:\python方法\PollutionArea\idm\IDM 6.38.1\IDMan.exe" #你电脑中IDM的位置
    # DownPath=r'I:\Sentinel2_DATA\test' #数据要下载的地址

    # api = SentinelAPI('wenyansha', 'WenYansha12', 'https://scihub.copernicus.eu/dhus')

    #用于读取数据的HTTP链接到列表中
    # filepath='HTTPandID.xlsx' 
    # workbook = xlrd.open_workbook(filepath)
    # sheet1 = workbook.sheet_by_name('HTTP')
    # linklist=sheet1.col_values(0)
    # #开始下载
    # print('开始任务：..................')
    # n=0
    # while linklist:
    #     print('---------------------------------------------------')
    #     n=n+1
    #     print('\n')
    #     print('第'+str(n)+'次循环'+'\n\n')
        
    #     id=linklist[0].split('\'')[1]
    #     link=linklist[0]
    #     product_info=api.get_product_odata(id)
    #     print('检查当列表里的第一个数据：')
    #     print('数据ID为：'+id)
    #     print('数据文件名为：'+product_info['title']+'\n')
        
    #     if product_info['Online']:
    #         print(product_info['title']+'为：online产品')
    #         print('加入IDM下载: '+link)
    #         call([IDM, '/d',link, '/p',DownPath,'/n','/a'])
    #         linklist.remove(link)
    #         call([IDM,'/s'])
    #     else:
    #         print(product_info['title']+'为：offline产品')
    #         print('去激活它')
    #         api.download(id)     #去激活它

    #         print('检查任务列表里是否存在online产品: .........')

    #         #等待激活成功的时候，检查现在的列表里还有没有online产品
    #         #如果有online的产品那就下载
    #         #首先检查列表中是否需要下载的数据
    #         if len(linklist)>1:
    #             #记录列表里可以下载的链接，并在最后把它们删除
    #             ilist=[]
    #             #开始寻找列表剩下的元素是否有online产品
    #             for i in range(1,len(linklist)):
    #                 id2=linklist[i].split('\'')[1]
    #                 link2=linklist[i]
    #                 product_info2=api.get_product_odata(id2)
    #                 if product_info2['Online']:
    #                     print(product_info2['title']+'为在线产品')
    #                     print('ID号为：'+id2)
    #                     print('加入IDM下载: '+link2)
    #                     print('--------------------------------------------')
                    
    #                     call([IDM, '/d',link2, '/p',DownPath,'/n','/a'])
    #                     #在列表中加入需要删除产品的HTTP链接信息
    #                     #直接在linklist中删除会linklist的长度会发生改变，最终造成i的值超过linklist的长度
    #                     ilist.append(link2)
    #                 else:
    #                     continue
    #             #把已经下载的数据的链接给删除掉
    #             if len(ilist)>0:
                    
    #                 call([IDM,'/s'])
    #                 for il in ilist:
    #                     linklist.remove(il)
                    
    #         print('本轮次检查结束，开始等到40分钟')
    #         #将该激活的产品删除，再加入到最后
    #         linklist.remove(link)
    #         linklist.append(link)
    #         #两次激活offline数据的间隔要大于30分钟
    #         for i in tqdm(range(int(1200)),ncols=100):
    #             time.sleep(2)

    # 样本标签修改
    # jpgpath = r'I:\PaddleX\user_dataset\DataSet_block33\JPEGImages'
    # annopath = r'I:\PaddleX\user_dataset\DataSet_block33\Annotations'
    # outpath = r'I:\PaddleX\user_dataset\DataSet_block33\newAnno'
    # os.chdir(annopath)
    # files = glob.glob("*.png")
    # for f in files:
    #     im = cv2.imread(f)[:,:,0]
    #     # mask = cv2.imread(os.path.join(jpgpath,f))[:,:,2]
    #     # im[mask==0] = 0
    #     cv2.imwrite(os.path.join(outpath,f),im)
    ##波段运算
    # fileName=r'D:\data\tif1.tif'
    # saveFile=r'D:\data\tn11.tif'
    # geotiff=imgProcess.geotiffread(fileName)
    # dataarray=geotiff.dataarray
    # dataarray[dataarray==32767] = 0
    # dataarray.astype("float32")
    
    # b1=dataarray[:,:,0]
    # b2=dataarray[:,:,1]
    # b3=dataarray[:,:,2]
    # b4=dataarray[:,:,3]
    # #v=-271.86*((b3)**2)-9.59*(b3)+6.95
    # #v=-0.08* (np.log(b2)/b4)-1.14
    # #v=-1245.25*((b1-b2)**2)-23.88*(b1-b2)+0.03
    # v=230.69*((b1-b3)**2)+31.31*(b1-b3)+1.36

    
    # imgProcess.geotiffwrite(saveFile,v,geotiff.geo_transform,geotiff.projection,datatype='FLOAT32')

    # 飞桨样本转换
    # path = r'H:\江苏省南京市\遥感影像采集标段-信息中心\提交成果\03真彩色正射影像\GF_20210219_20210319_L03_CGCS2000'
    # outpath = r'I:\PaddleX\user_dataset\NJ202103'
    # os.chdir(path)
    # files = glob.glob("*block31.tif")
    # for f in files:
    #     geotiff = imgpro.geotiffread(f)
    #     data = geotiff.dataarray
    #     t = data[:,:,2].copy()
    #     data[:,:,2] = data[:,:,0]
    #     data[:,:,0] = t
    #     outfile = os.path.join(outpath,f)
    #     cv2.imwrite(outfile,data)

    # # 提取时间
    # datapath = r'E:\cnsa_data\20210426需求'
    # os.chdir(datapath)
    # files = glob.glob("*.tar.gz")
    # df = pd.DataFrame([],columns=['序列号','更新时间'])
    # for i,f in enumerate(files):
    #     df.loc[i,'序列号'] = int(f.split("_")[-1][0:-7][3:])
    #     mtime = os.stat(f).st_mtime
    #     df.loc[i,'更新时间'] = int(time.strftime('%Y%m%d',time.localtime(mtime)))
    # df.to_excel(r'E:\cnsa_data\data20210426.xls')

    # # 对应时间
    # gf = r'E:\cnsa_data\高分清单.xlsx'
    # rd = pd.read_excel(gf)
    # serial0 = rd['产品序列号']
    # tmp = r'E:\cnsa_data\data20210426.xls'
    # t = pd.read_excel(tmp)
    # t_num =len(t)
    # for i in range(t_num):
    #     serial_num = t.loc[i,'序列号']
    #     index = np.where(serial0==serial_num)[0][0]
    #     rd.loc[index,'接收时间'] = t.loc[i,'更新时间'] 
    # rd.to_excel(r'E:\cnsa_data\高分清单.xlsx',index=False)

    # path = r'I:\Sentinel2_DATA'
    # os.chdir(path)
    # datefiles = glob.glob("test*")
    # for datefile in datefiles:
    #     os.chdir(os.path.join(path,datefile))
    #     sfiles = glob.glob("*.SAFE")
    #     for f in sfiles:
    #         os.removedirs(os.path.join(path,datefile,f))