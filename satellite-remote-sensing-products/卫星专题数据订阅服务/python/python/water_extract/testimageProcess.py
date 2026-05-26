#/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import random
import cv2
import numpy as np
import glob
import copy
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib as mpl
import shapefile
from geopandas import GeoDataFrame
from shapely import geometry, wkt
from osgeo import gdal, gdalconst, osr, ogr
import geopandas as gpd  # 必须先导入geopandas再导入gdal!
import imgProcess as imgpro

mpl.rcParams['axes.unicode_minus']=False#显示负号

# 功能：对测试图像切片
# tiffile：图像文件名，含绝对路径。输入图像为已经处理好的反射率图像
# outpath：样本保存路径。算法自动在outpath文件夹下创建对tiffile切片后的RefImages文件
# imgsize：int 指定样本图像大小
def getTestingSet(tiffile, outpath,  imgsize=1024, labelfield='ID'):
    # 定义存储路径
    ref_path = os.path.join(outpath, "RefImages切片")
    if not os.path.exists(ref_path):
        os.mkdir(ref_path)
    geotiff = imgpro.geotiffread(tiffile)
    print('样本已读取')
    data = geotiff.dataarray
    geo_transform = geotiff.geo_transform
    rows = geotiff.rows
    cols = geotiff.cols
    print(rows, cols)

    img_idx = 0  # 样本序号
    step = 512
    for i in range(0, rows, step):
        for j in range(0, cols, step):
            # 取值
            c_data = data[i:i + imgsize, j:j + imgsize, :]
            print( c_data.shape)
            # 非空保存输出
            if  c_data.size != 0:
                    if c_data.shape == (1024, 1024, 4):
                        # 保留存在标签的图像
                        if  np.max(c_data) > 0:
                            # 样本从1开始计数
                            img_idx = img_idx + 1
                            filename = str(img_idx)
                            c_geotrans = (
                                geo_transform[0] + j * geo_transform[1], geo_transform[1], geo_transform[2],
                                geo_transform[3] + i * geo_transform[5], geo_transform[4], geo_transform[5])
                            #     样本制作
                            imgpro.geotiffwrite(os.path.join(ref_path, filename + ".tif"), c_data, c_geotrans,
                                                geotiff.projection, datatype="FLOAT32")
                            print("success!---", str(img_idx))

# ####随机切分训练集和测试集
# # image图片路径
# tifpath = r'H:\Tensorflow\1.16\JPEGImages'
# os.chdir(tifpath)
# #标签路径
# labelpath=r'H:\Tensorflow\1.16\Annotations'
# #输出路径
# input = r'H:\Tensorflow\tianditu_image3\addlabel_image'
# os.makedirs(input,exist_ok=True)
# #测试集输出路径
# testinput = r'H:\Tensorflow\tianditu_image3\test_image'
# os.makedirs(testinput,exist_ok=True)
# labelfile_id,labelfile_name=imgpro.getFilename(labelpath)
# sum_tiffiles = glob.glob("*.tif")
# random.shuffle(sum_tiffiles)
# print('sum_tiffiles-------------------',len(sum_tiffiles))
# test_tiffiles = random.sample(sum_tiffiles,round(len(sum_tiffiles)*0.3))
# for test_tiffile in enumerate(test_tiffiles):
#     test_geotiff = imgpro.geotiffread(test_tiffile[1])
#     refdata = test_geotiff.dataarray
#     print(os.path.join(testinput, test_tiffile[1]))
#     imgpro.geotiffwrite(os.path.join(testinput, test_tiffile[1]), refdata, test_geotiff.geo_transform,test_geotiff.projection,datatype="UINT16")
# tiffiles =set(sum_tiffiles).difference(set(test_tiffiles))
# for g,tiffile in enumerate(tiffiles):
#     ref_geotiff = imgpro.geotiffread(tiffile)
#     refdata = ref_geotiff.dataarray
#     new_array = np.zeros((refdata.shape[0],refdata.shape[1],5),np.uint16)
#     index_num=tiffile.split('_')[0].split('.')[0]
#     match_id=labelfile_id.index(str(index_num))
#     if not match_id is None:
#         label_geotiff = imgpro.geotiffread(os.path.join(labelpath, labelfile_name[match_id]))
#         labeldata = label_geotiff.dataarray
#         # labeldata[labeldata == 2]= 0
#         # labeldata[labeldata ==3] = 0
#     # if np.sum(labeldata==1)>= labeldata.shape[0] * labeldata.shape[1] * 0.1:
#     try:
#         for i in range(4):
#             new_array[:, :, i]=refdata[:,:,i]
#         new_array[:, :, 4]=labeldata
#         print(os.path.join(input,str(index_num)+ '_addlable.tif'))
#         imgpro.geotiffwrite(os.path.join(input,str(index_num)+ '_addlable.tif'),new_array,ref_geotiff.geo_transform,ref_geotiff.projection)
#     except:
#         pass
# print(g)
#
# # #图像裁剪
# tifpath = r'H:\Tensorflow\tianditu_image2\无人机黑臭影像'
# os.chdir(tifpath)
# tiffiles = glob.glob("*0107.tif")
# shpfile = r'H:\Tensorflow\tianditu_image2\无人机黑臭影像\water_100_0034_0107.shp'
# # shpdata=GeoDataFrame.from_file(shpfile)#读取shp面状文件
# for g,tiffile in enumerate(tiffiles):
#     print(tiffile)
#     outfile = tifpath+'\\'+tiffile[0:-4]+'_cliped.tif'
#     tiffile=tifpath+'\\'+tiffile
#     # imgpro.imgclip_with_shp(tifpath,shpfile,outfile)
#     # gdal.Warp(outfile, tiffile, format='GTiff', cutlineDSName=shpfile, cropToCutline=True, dstNodata=0)#cropToCutline=True剪后影像大小跟矢量文件的图框大小一致
#     gdal.Warp(outfile, tiffile, format='GTiff', cutlineDSName=shpfile, cropToCutline=False, dstNodata=0)#cropToCutline=False结果图像大小会跟待裁剪影像大小一致
# print(g)

# # ##影像切片
# #情况一：无移动步长切片
# # tifpath=r'H:\Tensorflow\image_RGB\lyg20221019GF6'
# # os.chdir(tifpath)
# # outpath = r'H:\Tensorflow\image_RGB\lyg20221019GF6\切片'
# # os.makedirs(outpath,exist_ok=True)
# # tiffiles = glob.glob("GF6*.tif")
# # for g,tiffile in enumerate(tiffiles):
# #     geotiff = imgpro.geotiffread(tiffile)
# #     tifdata=geotiff.dataarray
# #     rgb2refdata=imgpro.bgr2Rgb(tifdata)
# #     rgb2refile=tiffile.replace('.tif','_ref.tif')
# #     rgb2refgeo=imgpro.geotiffread(rgb2refile)
# #     # geotiffwrite(rgb2reffile, rgb2refdata, geotiff.geo_transform, geotiff.projection)
# #     # imgpro.imgslice_by_rowcol(tifdata,3,3, outpath)
# #     imgpro.imgslice_by_pixels(rgb2refgeo,4000, outpath)
# # print(g)
# #情况二：有移动步长的切片（默认为步长512）
# tiffile=r'H:\Tensorflow\image_RGB\lyg20221019GF6\GF6_PMS_E118.8_N35.0_20221019_L1A1120259483_moisc_ref.tif'
# outpath = r'H:\Tensorflow\image_RGB\lyg20221019GF6'
# getTestingSet(tiffile, outpath,imgsize=1024)

####输出结果拼接
tiffpath=r'H:\Tensorflow\image_RGB\lyg20221019GF6\tensorflow_test'
os.chdir(tiffpath)
outpath = r'H:\Tensorflow\image_RGB\lyg20221019GF6\tensorflow_test'
os.makedirs(outpath,exist_ok=True)
filename=['model1','model2','model3','model4','model5']
for i in range(4,len(filename)):
    tiffiles = glob.glob("*"+filename[i]+"*.tif")
    outfile=tiffiles[0][-15:-4]+'1.tif'
    ref_raster = gdal.Open(tiffiles[0], gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    options = gdal.WarpOptions(srcSRS=ref_proj, dstSRS=ref_proj, format='GTiff', resampleAlg=gdalconst.GRA_Bilinear)
    gdal.Warp(outfile, tiffiles, options=options)