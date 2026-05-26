import math
import numpy as np
from imgprocess import geotiffwrite,geotiffread

def getNDWI(refdata):
    '''
    功能：计算NDWI(水体指数)，用于提取水域
    原理：水体近红外吸收更大
    refdata: np.dataarray 反射率
    '''
    refdata = refdata.astype(np.float)
    g,nir = refdata[:,:,1],refdata[:,:,3]
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

def identifyWaterarea(inputfile,resultfile,satellite):
    '''
    从影像识别水域
    :param inputfile:
    :param resultfile:
    :param satellite:
    :return:
    '''
    platform =
    if satellite == 's2':
        # geotiff = geotiffread(inputfile)
        # data = geotiff.dataarray
        # ndwi = getNDWI(data)
        # ndwi[ndwi>0] = 1
        # ndwi[ndwi<0] = 0
        # geotiffwrite(resultfile,ndwi,geotiff.geo_transform,geotiff.projection,datatype="UINT8")
        pass
    elif satellite == ''

def deriveFUI(data):
    '''
    功能：计算水色指数、水体透明度
    data: np.array
    返回：
    FUI: np.array
    SD: np.array
    '''
    rows,cols,bands = data.shape
    #波段选择
    r = 3-1
    g = 2-1
    b = 1-1
    R = data[:,:,r]
    G = data[:,:,g]
    B = data[:,:,b]
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

def waterQA():


