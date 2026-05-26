'''
@Time    :   2022/03/07
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 水质/水色相关算法
'''

import os
import glob
import numpy as np
import pandas as pd

import imgProcess as imgpro

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

def getBOCI(refdata,wavelength):
    '''
    功能：计算BOCI(黑臭水体遥感分级指数)，用于黑臭河道识别
    原理：黑臭水体绿光波段的基线高度差与红光波段反射率之比较小
    refdata: np.dataarray 反射率
    wavelength: list 反射率的波长信息，纳米
    '''
    b,g,r = refdata[:,:,0],refdata[:,:,1],refdata[:,:,2]
    wb,wg,wr = wavelength[0:3]
    baseline_g = b + (r-b) * (wg-wb) / (wr - wb)
    boci = (g - baseline_g) / r
    boci[refdata[:,:,0]==0] = np.nan
    boci[boci<0] = np.nan
    boci[boci>1] = np.nan

    return boci

def getWCI(refdata,wavelength):
    '''
    功能：计算WCI(水体清洁指数)，用于黑臭河道识别
    原理：黑臭水体从蓝光到绿光的上升幅度低于一般水体，从绿光到红光的上升幅度大于一般水体（注意可能与光谱不符）
    refdata: np.dataarray 反射率
    wavelength: list 反射率的波长信息，纳米
    '''
    b,g,r = refdata[:,:,0],refdata[:,:,1],refdata[:,:,2]
    wb,wg,wr = wavelength[0:3]
    a1 = (g - b) / (wg - wb)
    a2 = (r - g) / (wr - wg)
    wci = a1 / a2
    wci[refdata[:,:,0]==0] = np.nan

    return wci

def getGreenSpectralDifference(refdata):
    '''
    功能：计算黑臭光谱指数H，用于黑臭河道识别
    refdata: np.dataarray 反射率
    '''
    b,g,r,nir = refdata[:,:,0],refdata[:,:,1],refdata[:,:,2],refdata[:,:,3]
    h = (2 * g - b - r) / ((b + g + r + nir) / 4)
    h[refdata[:,:,0]==0] = np.nan

    return h

def getCIEValues(refdata,reftable):
    '''
    功能：计算CIE坐标系下颜色主导波长、饱和度，用于黑臭河道识别
    refdata: np.dataarray 反射率
    reftablefile: CIE坐标下，alpha lamda sd参照表
    '''
    #波段选择        
    B,G,R = refdata[:,:,0],refdata[:,:,1],refdata[:,:,2]
    X = 2.7689 * R + 1.7517 * G + 1.1302 * B
    Y = 1.0000 * R + 4.5907 * G + 0.0601 * B
    Z = 0.0565 * G + 5.5943 * B
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    # z = Z / (X + Y + Z)
    del R,G,B,X,Y,Z

    x1 = y - 0.3333
    y1 = x - 0.3333

    alpha = np.arctan2(y1,x1) * 180 / np.pi  

    lamda,sd = CIEalpha2lamda(alpha,reftable)
    sc = np.sqrt(x1*x1+y1*y1)
    saturation = sc/sd
    
    alpha[refdata[:,:,0]==0] = np.nan  
    lamda[refdata[:,:,0]==0] = np.nan
    saturation[refdata[:,:,0]==0] = np.nan  
    saturation[saturation>1] = np.nan

    return alpha,lamda,saturation


def CIEalpha2lamda(alpha_array,reftable):
    '''
    功能：在CIE坐标下，根据查找表从alpha 获取lamda\SD值，sd为标准色距离中心店（0.33333,0.33333）的距离
    refdata: np.dataarray 反射率
    reftablefile: CIE坐标下，alpha lamda sd参照表
    '''
    # reftable = pd.read_excel(reftablefile,skiprows=2)

    lamda = reftable['nm'].values.tolist()
    alpha = reftable['alpha'].values.tolist()
    sd = reftable['距离S距离'].values.tolist()

    lamda_array = np.zeros_like(alpha_array)
    sd_array = np.zeros_like(alpha_array)

    for i in range(len(reftable)):
        sd_array[alpha_array>=alpha[i]] = sd[i]
        lamda_array[alpha_array>=alpha[i]] = lamda[i]
    
    return lamda_array,sd_array



if __name__ == '__main__':
    outpath = r'E:\vx\spcsqc\heichou'  #出黑臭指数的路径
    refpath = r'E:\vx\spcsqc\reflectance'  #放置反射率的路径
    os.chdir(refpath)

    reftablefile = r'E:\vx\spcsqc\heichou\cie1931年标准色度观测者的光谱色品坐标.xls'   #放入标准色度表格，附件中有
    reftable = pd.read_excel(reftablefile,skiprows=2)

    s2_wavelength = [490,560,665,842]
    reffiles = glob.glob("*.tif")

    for reffile in reffiles:
        geotiff = imgpro.geotiffread(reffile)
        refdata = geotiff.dataarray.astype(np.float)
        refdata = waterMask(refdata)




        # boci = getBOCI(refdata,s2_wavelength)
        # outfile = os.path.join(outpath,reffile[0:-4]+"_BOCI.tif")
        # imgpro.geotiffwrite(outfile,boci,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")

        # wci = getWCI(refdata,s2_wavelength)
        # outfile = os.path.join(outpath,reffile[0:-4]+"_WCI.tif")
        # imgpro.geotiffwrite(outfile,wci,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")

        # h = getGreenSpectralDifference(refdata)
        # outfile = os.path.join(outpath,reffile[0:-4]+"_H.tif")
        # imgpro.geotiffwrite(outfile,h,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")

        alpha,lamda,saturation = getCIEValues(refdata,reftable)
        # outfile = os.path.join(outpath,reffile[0:-4]+"_alpha.tif")
        # imgpro.geotiffwrite(outfile,alpha,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")
        # outfile = os.path.join(outpath,reffile[0:-4]+"_lamda.tif")
        # imgpro.geotiffwrite(outfile,lamda,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")
        outfile = os.path.join(outpath,reffile[0:-4]+"_saturation.tif")
        imgpro.geotiffwrite(outfile,saturation,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")



    