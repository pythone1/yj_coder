import math
import os,glob
import shutil
import subprocess
import json
import numpy as np
from osgeo import gdal

from imgprocess import geotiffwrite,geotiffread
import SAR_Getwater_process as S1GP

def getNDWI(g,nir):
    '''
    功能：计算NDWI(水体指数)，用于提取水域
    原理：水体近红外吸收更大
    g: np.dataarray 绿光波段反射率
    nir: np.dataarray 近红外波段反射率
    '''
    ndwi = (g-nir)/(g+nir)

    return ndwi

def waterMask(refdata,threshold=0):
    '''
    功能：利用NDWI进行水域掩膜
    返回: np.array,非水域设0，水域保留原值
    refdata: np.dataarray 反射率
    threshold: float 阈值，小于该阈值的为非水体，大于阈值为水体
    '''
    watermask = getNDWI(refdata)
    watermask[watermask<threshold] = 0
    watermask[watermask>threshold] = 1
    refdata[watermask==0] = 0

    return refdata

def getDBWI(b, g):
    '''
    功能：计算DBWI(黑臭水体指数)，用于提取黑臭水体
    原理：黑臭水体在蓝绿波段上升缓慢，其他水体在该波段上升较较快
    b:  np.dataarray 反射率蓝光波段
    g:  np.dataarray 反射率绿光波段
    '''
    dbwi = (g-b)

    return dbwi

def deriveSD(r,g,b):
    '''
    功能：计算水色指数、水体透明度
    b,g,r:  np.dataarray 反射率蓝、绿、红波段
    返回：
    FUI: np.array 水色指数
    SD: np.array 水体透明度指数
    '''
    R = r
    G = g
    B = b
    rows, cols=R.shape[0],R.shape[1]
    X = 2.7689 * R + 1.7517 * G + 1.1302 * B
    Y = 1.0000 * R + 4.5907 * G + 0.0601 * B
    Z = 0.0565 * G + 5.5943 * B
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    #z = Z / (X + Y + Z)
    del R,G,B,X,Y,Z
    x1 = y - 0.3333
    y1 = x - 0.3333
    alpha = np.zeros([rows,cols])
    for i in range(rows):
        for j in range(cols):
            alpha[i,j] = math.atan2(y1[i,j],x1[i,j]) * 180 / np.pi
    del x1,y1
    FUI = np.zeros([rows,cols])
    a = np.array([-140.054,-135.414,-123.059,-107.207,-91.443,-60.546,-27.923,
        -11.913,1.634,11.445,19.243,21.424,22.644,25.429,27.926,31.411,
        35.226,40.552,46.222,50.339,55.587])
    for i in range(20):
        FUI[alpha>=a[i]] = i+1
    FUI[alpha>a[20]] = 21
    a1 = alpha.copy()
    a1 = a1 + 180
    a1[FUI>=8] = 0
    a2 = FUI.copy()
    a2[FUI<8] = 0
    sd1 = 8144.5 / np.power(a1,1.534)
    sd2 = 44.122 / np.power(a2,1.138)
    SD = sd1
    SD[FUI>=8] = sd2[FUI>=8]
    SD[np.isnan(SD)] = 0
    del sd1,sd2
    return FUI,SD

def pond_water(S1_IMG,inshp,value,outfile):
    '''
    从sentinel1识别坑塘水体
    S1_IMG-双极化影像,.tif
    inshp-坑塘矢量.shp
    value-占比取值
    outfile:二值化结果,.tif
    '''
    mask_data,new_meta=S1GP.extract_from_shp(inshp,S1_IMG)              #掩膜
    geotrans = new_meta.get("transform")
    swi_data=S1GP.getSWI(mask_data,vh_idx=0,vv_idx=1)                   #波段运算,波段顺序与哨兵官网一致
    swi_data[np.isnan(swi_data)]=0
    segment=S1GP.window_segment(swi_data,50,0.1)                        #阈值分割,注意窗口尺寸和重复率

    shp_path=os.path.dirname(outfile)+'\\shp'                           #outfile的上一层路径下新建shp文件夹用于存放占比矢量
    if not os.path.exists(shp_path):
        os.makedirs(shp_path)
    outshp=S1GP.count_from_shp(segment,inshp,geotrans,value)            #占比矢量
    shpfile = os.path.join(shp_path,S1_IMG[0:-4]+'.shp')
    outshp.to_file(shpfile)

    S1GP.shp2raster(S1_IMG,shpfile,outfile,field='judge',filed_type=gdal.GDT_Byte)

    shutil.rmtree(shp_path)                                                     #删除占比矢量文件夹,若不删除则保持注释

def identifyWaterarea(inputfile,resultfile,config):
    '''
    从影像识别水域
    :param inputfile: str 输入影像
    :param resultfile: str 输出文件
    :param platform: str 平台类型
    :return:
    '''
    # platform = config['user']['platform']
    platform = config['srcimg_info']['platform']

    # 水域识别
    if platform == 'sentinel2':
        geotiff = geotiffread(inputfile)
        data = geotiff.dataarray.astype(float)
        g, nir = data[:, :, 1], data[:, :, 3]
        ndwi = getNDWI(g,nir)
        ndwi[ndwi>0] = 1
        ndwi[ndwi<0] = 0
        geotiffwrite(resultfile,ndwi,geotiff.geo_transform,geotiff.projection,datatype="UINT8")
    elif platform in ['gf1','gf2','gf6']:
        command = [config['python_exe']['tensorflow_python_exe_path'],config['py_file']['GFidentifyWaterarea'],
                   inputfile, resultfile,
                   config['model_idt_waters_gf']['modelpath'],config['savepath']['tmp_imgslice'],config['savepath']['tmp_mask']]
        pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    elif platform == 'sentinel1':
        file_list = glob.glob(config['savepath']['pondshp'] + '\\*.shp')
        roi_basename = os.path.basename(config['user']['roi_file'])
        pondshp = os.path.join(config['savepath']['pondshp'],roi_basename)
        if pondshp in file_list:  # 已有坑塘矢量则执行S1的水域提取,0.26为占比取值,注意pond_water中的窗口尺寸及重复率
            pond_water(inputfile, pondshp, 0.26, resultfile)
        else:
            # 没有坑塘矢量则邮箱推送任务内容
            raise Exception('无对应坑塘的矢量掩膜。')
    else:
        raise Exception('没有对应卫星的水域识别算法')


def getWaterQA(inputfile,resultfile,config,band_name):
    '''
    水色计算
    :inputfiles: list[str] 输入影像 list中为同一时间拍摄的多张影像，需拼接裁剪后输出
    :param resultfile: str 输出文件
    :param band_name: list[str] 波段名称
    param product_type str 产品类型
    :return:
    '''
    product_type = config['user']['product_type']
    geotiff = geotiffread(inputfile)
    data = geotiff.dataarray.astype(float)
    r, g, b = data[:, :, band_name.index('r')], data[:, :, band_name.index('g')], data[:, :, band_name.index('b')]

    if product_type== '黑臭指数':
        dbwi = getDBWI(b,g)
        geotiffwrite(resultfile,dbwi,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")
    elif product_type== '水色':
        fui,sd = deriveSD(r,g,b)
        geotiffwrite(resultfile, sd, geotiff.geo_transform, geotiff.projection,datatype="FLOAT32")
    else:
        raise Exception('无对应数据产品类型')
