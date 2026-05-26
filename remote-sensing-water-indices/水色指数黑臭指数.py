# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:08:57 2020

@author: Wen Yansha
funciotn: derive FUI and SD parameters from a reflectance image
输入1：tiffile 反射率文件,*tif格式
输入2：sensortype 传感器类型，包括pms,modis,oli
输入3：**_fname 自定义FUI/SD输出文件名
输出1：FUI 水色 & SD 透明度 数值矩阵
输出2：将 FUI 水色 & SD 透明度 写为tif文件

Calibrated on Thu Oct 29 15:52:23 2020
@author: Wen Yansha
修改内容: 增加浊度算法（引自 田礼乔Dogliotti A I, Ruddick K G 等，2015），测试效果一般
输入1：tiffile 反射率文件,*tif格式
输入2：sensortype 传感器类型，包括pms,modis,oli
输入3：**_fname 自定义Trubidity输出文件名
输出1：浊度 数值矩阵
输出2：将 浊度 写为tif文件
"""

import numpy as np
import math
from osgeo import gdal

def geotiffread(tiffile):
    dataset = gdal.Open(tiffile,gdal.GA_ReadOnly)
    geo_transform = dataset.GetGeoTransform()
    proj = dataset.GetProjection()
    row = dataset.RasterYSize
    col = dataset.RasterXSize
    layer = dataset.RasterCount
    data = np.zeros((row, col, layer))
    for b in range(dataset.RasterCount):
        band = dataset.GetRasterBand(b + 1)
        data[:, :, b] = band.ReadAsArray()
    return data,row,col,layer,geo_transform,proj

def geotiffwrite(fname,data,geo_transform,projection):
    driver=gdal.GetDriverByName("GTiff")
    if len(data.shape) == 3:
        row,col,layer=data.shape
        #driver.Create(filename, im_width, im_height, im_bands, datatype)
        dataset=driver.Create(fname,col,row,layer,gdal.GDT_Float32)
    elif len(data.shape) == 2:
        row,col=data.shape
        layer = 1
        dataset=driver.Create(fname,col,row,1,gdal.GDT_Float32)    
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    if layer == 1:
        dataset.GetRasterBand(1).WriteArray(data)
    else:        
        for i in range(layer):
            dataset.GetRasterBand(i+1).WriteArray(data[i])
    dataset=None # 关闭文件

def derive_FUI(bgrdata):
    '''
    功能：计算水色指数，输出FUI和SD
    bgrdata: np.dataarray 待计算水色指数的三维矩阵，BGR图像，波段顺序按蓝绿红排列
    输出：FUI np.dataarray 水色指数 21个离散值，指示21个水色等级
    SD np.dataarray 透明度指数 连续分布
    '''    
    bgrdata = np.float64(bgrdata)
    b,g,r = 0,1,2
    R = bgrdata[:,:,r]
    G = bgrdata[:,:,g]
    B = bgrdata[:,:,b]
    X = 2.7689 * R + 1.7517 * G + 1.1302 * B
    Y = 1.0000 * R + 4.5907 * G + 0.0601 * B
    Z = 0.0565 * G + 5.5943 * B
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    #z = Z / (X + Y + Z)
    x1 = y - 0.3333
    y1 = x - 0.3333
    alpha = np.zeros([row,col])
    for i in range(row):
        for j in range(col):
            alpha[i,j] = math.atan2(y1[i,j],x1[i,j]) * 180 / np.pi           
    FUI = np.zeros([row,col])    
    a = np.array([-140.054,-135.414,-123.059,-107.207,-91.443,-60.546,-27.923,
        -11.913,1.634,11.445,19.243,21.424,22.644,25.429,27.926,31.411,
        35.226,40.552,46.222,50.339,55.587])
    for i in range(20):
        FUI[alpha>=a[i]] = i+1
    FUI[alpha>a[20]] = 21

    a1 = alpha.copy()
    a1[FUI>=8] = 0
    a2 = FUI.copy()
    a2[FUI<8] = 0
    sd1 = 8144.5 * np.power(a1+180,-1.534)
    sd2 = 44.122 * np.power(a2,-1.138)
    SD = sd1
    SD[FUI>=8] = sd2[FUI>=8]    

    return FUI,SD,alpha   

def derive_turbidity(rnirdata):
    '''
    功能：计算浊度
    rnirdata: np.dataarray 红、近红外数据
    返回 turbidity np.dataarray 浊度
    '''
    r,nir = 0,1
    ksi = (rnirdata[:,:,nir] - 0.028) / 0.005
    turbidity = (1-ksi) * 21170 * np.power(rnirdata[:,:,r],2.4880) + ksi * 2.4354 * np.power(rnirdata[:,:,nir],2.5673)
    
    return turbidity

def getDBWI(bgdata):
    '''
    功能：黑臭指数
    bgdata: np.dataarray 蓝、绿波段数据
    返回 DBWI np.dataarray 黑臭指数
    '''
    b,g = 0,1
    return bgdata[:,:,g] - bgdata[:,:,b]

def func():
    a = 2
    print(a)

    
if __name__=="__main__":
    #输入1：反射率文件
    tiffile = r'D:\tmp2\1124_transparent_mosaic_group1.tif'
    #输入2：蓝、绿、红、近红外在tif文件中对应的波段序号（从0开始计数）
    b,g,r,nir = 0,1,2,3
    #输入3：自定义FUI输出文件名
    FUI_fname = tiffile.replace('.tif','_FUI.tif')
    #输入4：自定义SD输出文件名
    SD_fname = r'D:\tmp1\sentinel2_20210831_ref20m_SD.tif'
    #输入5：自定义NTU输出文件名
    NTU_fname = r'D:\ProcessingData\TEMP\test\Turbidity.tif'    
    #输入6：自定义黑臭指数输出文件名
    DBWI_fname = r'D:\ProcessingData\TEMP\test\DBWI.tif'    
    
    #读取反射率文件
    data,row,col,layer,geo_transform,proj = geotiffread(tiffile) 
    # 水域掩膜
    ndwi = (data[:,:,g] - data[:,:,nir]) / (data[:,:,g] + data[:,:,nir])
    data[ndwi<0] = 0

    # 取蓝绿红波段，计算水色
    bgrdata = np.dstack(data[:,:,b],data[:,:,g],data[:,:,r])  
    FUI,SD,alpha = derive_FUI(bgrdata)
    geotiffwrite(FUI_fname,FUI,geo_transform,proj)
    geotiffwrite(SD_fname,SD,geo_transform,proj)
    
    # 取红、近红外波段计算浊度
    rnirdata = np.dstack(data[:,:,r],data[:,:,nir])  
    ntu = derive_turbidity(rnirdata)
    geotiffwrite(NTU_fname,ntu,geo_transform,proj)

    # 取蓝、绿波段计算黑臭指数DBWI
    bgdata = np.dstack(data[:,:,b],data[:,:,g]) 
    dbwi = getDBWI(bgdata)
    geotiffwrite(DBWI_fname,dbwi,geo_transform,proj)
