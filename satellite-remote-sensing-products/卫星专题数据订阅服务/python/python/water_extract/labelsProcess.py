#/usr/bin/env python
# -*- coding: UTF-8 -*-
import  os
import  imgProcess as imgpro
import cv2
import numpy as np
import glob
from osgeo import gdal, gdalconst, osr, ogr
import random

class geotiffinfo():
    '''
    tif信息
    '''
    def __init__(self,rows,cols,bands,geo_transform,projection,dataarray,*sensor):
        self.rows=rows
        self.cols=cols
        self.bands=bands
        self.geo_transform=geo_transform
        self.projection=projection
        self.dataarray=dataarray
        self.sensor = sensor
        if sensor == "pms" or sensor == "rededge":
            self.b_index = 0
            self.g_index = 1
            self.r_index = 2
            self.nir_index = 3

def geotiffUnify(outfile, srcfile, referencefile, datatype):
    '''
    功能：重采样影像到与参考影像一致范围
    outfile：输出影像文件
    srcfile：要重采样的文件
    referencefile：参考影像文件
    datatype：数据类型
    '''
    geotiff_tpl = imgpro.geotiffread(referencefile)
    # 投影+重采样
    src_raster = gdal.Open(srcfile)
    src_proj = src_raster.GetProjection()
    dst_proj = geotiff_tpl.projection
    res = geotiff_tpl.geo_transform[1]
    options = gdal.WarpOptions(
        srcSRS=src_proj,
        dstSRS=dst_proj,
        xRes=res,
        yRes=res,
        format='GTiff',
        resampleAlg=gdalconst.GRA_NearestNeighbour)
    gdal.Warp(outfile, srcfile, options=options)

    # 源矩阵范围及大小
    srs_geotiff = imgpro.geotiffread(outfile)
    srs_geotrans = srs_geotiff.geo_transform
    srs_rows = srs_geotiff.rows
    srs_cols = srs_geotiff.cols
    srs_bands = srs_geotiff.bands
    srs_array = srs_geotiff.dataarray

    # 目标矩阵范围及大小
    dst_geotrans = geotiff_tpl.geo_transform
    dst_rows = geotiff_tpl.rows
    dst_cols = geotiff_tpl.cols

    srs_stx = max(int((dst_geotrans[0] - srs_geotrans[0]) / res), 0)
    dst_stx = max(int((srs_geotrans[0] - dst_geotrans[0]) / res), 0)
    srs_sty = max(int((dst_geotrans[3] - srs_geotrans[3]) / (-res)), 0)
    dst_sty = max(int((srs_geotrans[3] - dst_geotrans[3]) / (-res)), 0)

    if dst_cols < dst_stx + srs_cols:
        dst_edx = dst_cols
        srs_edx = srs_stx + (dst_edx - dst_stx)
    else:
        srs_edx = srs_cols
        dst_edx = dst_stx + (srs_edx - srs_stx)

    if dst_rows < dst_stx + srs_rows:
        dst_edy = dst_rows
        srs_edy = srs_sty + (dst_edy - dst_sty)
    else:
        srs_edy = srs_rows
        dst_edy = dst_sty + (srs_edy - srs_sty)

    if srs_bands == 1:
        dst_array = np.zeros((dst_rows, dst_cols))
        dst_array[dst_sty:dst_edy, dst_stx:dst_edx] = srs_array[srs_sty:srs_edy, srs_stx:srs_edx]
    else:
        dst_array = np.zeros((dst_rows, dst_cols, srs_bands))
        dst_array[dst_sty:dst_edy, dst_stx:dst_edx, :] = srs_array[srs_sty:srs_edy, srs_stx:srs_edx, :]

    mask = geotiff_tpl.dataarray
    if len(mask.shape) >= 3:
        dst_array[mask[:, :, 0] == 0] = 0
    else:
        dst_array[mask == 0] = 0

    imgpro.geotiffwrite(outfile, dst_array, dst_geotrans, dst_proj, datatype)
    return dst_array


# 功能：根据图像和矢量标签制备分块样本
# tiffile：图像文件名，含绝对路径。输入图像为已经处理好的反射率图像，或者NDVI\NDWI\G波段组合图像
# 矢量标签：矢量标签（*.shp）文件名，含绝对路径
# outpath：样本保存路径。算法自动在outpath文件夹下创建Annotations、JPEGImages文件夹，分别存放标签和图片
# imgsize：int 指定样本图像大小
def getTrainingSet(tiffile, outpath, labelsfile, imgsize=1024, labelfield='ID'):
    # 定义存储路径
    anno_path = os.path.join(outpath, "Annotations2")
    jpeg_path = os.path.join(outpath, "JPEGImages2")
    if not os.path.exists(anno_path):
        os.mkdir(anno_path)
    if not os.path.exists(jpeg_path):
        os.mkdir(jpeg_path)
    basename = os.path.basename(tiffile)[0:-4]

    # label矢量转栅格
    # geotiff = resize_tif(tiffile,plus)
    geotiff = imgpro.geotiffread(tiffile)
    print('样本已读取')
    rows = geotiff.rows
    cols = geotiff.cols
    print(rows, cols)

    # label_array = imgpro.shp2geotiff(shpfile, rows, cols, geotiff.geo_transform, geotiff.projection, field=labelfield)
    # label_array[label_array > 7] = 0  # 重叠样本设为空
    label_array_info = imgpro.geotiffread(labelsfile)
    label_array = label_array_info.dataarray

    # print(label_array_info.rows,label_array_info.cols)
    print('标签已读取')
    # raster设置为满足cv2-RGB图像输出的波段顺序
    data = geotiff.dataarray
    geo_transform = geotiff.geo_transform

    # if geotiff.bands == 3:
    #     t = data[:, :, 2].copy()
    #     data[:, :, 2] = data[:, :, 0]
    #     data[:, :, 0] = t

    # 按imgsize裁剪遍历栅格，若label为空pass，否则保存annoimg和jpeg_img
    img_idx = 0  # 样本序号
    step = 512
    for i in range(0, rows, step):
        for j in range(0, cols, step):

            # 取值
            c_label = label_array[i:i + imgsize, j:j + imgsize]
            c_data = data[i:i + imgsize, j:j + imgsize, :]

            # data_label = c_label.copy()

            c_label[c_label == 2] = 0
            c_label[c_label == 3] = 0
            c_label[c_label == 4] = 0
            # c_label[c_label == 5] = 0
            # c_label[c_label == 6] = 0
            # 非标记区域置为0
            # data_label[c_label == 0] = 255
            # data_label[c_label == 1] = 0
            # data_label[c_label == 2] = 1
            # data_label[c_label == 3] = 2
            # data_label[c_label == 4] = 3
            print(c_label.shape, c_data.shape)
            # 非空保存输出
            if c_label.size != 0 and c_data.size != 0:
                if c_label.shape == (1024, 1024, 1):
                    if c_data.shape == (1024, 1024, 5):
                        # 保留存在标签的图像
                        if np.max(c_label) > 0 and np.max(c_data) > 0:
                            # 样本从1开始计数
                            img_idx = img_idx + 1
                            filename = str(img_idx)

                            # if geotiff.bands == 3:
                            c_geotrans = (
                                geo_transform[0] + j * geo_transform[1], geo_transform[1], geo_transform[2],
                                geo_transform[3] + i * geo_transform[5], geo_transform[4], geo_transform[5])
                            # 标签制作
                            imgpro.geotiffwrite(os.path.join(anno_path, filename + ".tif"), c_label, c_geotrans,
                                                geotiff.projection, datatype="UINT8")
                            #     cv2.imwrite(os.path.join(anno_path, filename + ".png") , c_label)
                            #     样本制作
                            imgpro.geotiffwrite(os.path.join(jpeg_path, filename + ".tif"), c_data, c_geotrans,
                                                geotiff.projection, datatype="FLOAT32")
                            # else:
                            # cv2.imwrite(os.path.join(jpeg_path, filename + ".png") , c_data)
                            print("success!---", str(img_idx))


def splitTrainingTestSet(tifpath, labelpath, train_output, test_output):
    '''
    # 功能：随机切分训练集和测试集
    tifpath：str  tif反射率文件路径
    labelpath：str  标签文件路径
    train_output：str 训练集输出路径
    test_output  str 测试集输出路径
    '''
    os.chdir(tifpath)
    os.makedirs(train_output, exist_ok=True)
    os.makedirs(test_output, exist_ok=True)

    labelfile_id, labelfile_name = imgpro.getFilename(labelpath)
    sum_tiffiles = glob.glob("*.tif")
    random.shuffle(sum_tiffiles)
    print('sum_tiffiles-------------------', len(sum_tiffiles))

    test_tiffiles = random.sample(sum_tiffiles, round(len(sum_tiffiles) * 0.3))
    # #测试集
    for test_tiffile in enumerate(test_tiffiles):
        test_geotiff = imgpro.geotiffread(test_tiffile[1])
        refdata = test_geotiff.dataarray
        new_array = np.zeros((refdata.shape[0], refdata.shape[1], 4), np.uint16)
        for i in range(4):
            new_array[:, :, i] = refdata[:, :, i]
        print(os.path.join(test_output, test_tiffile[1]))
        imgpro.geotiffwrite(os.path.join(test_output, test_tiffile[1]), new_array, test_geotiff.geo_transform,
                            test_geotiff.projection, datatype="UINT16")
    # #训练集
    train_tiffiles = set(sum_tiffiles).difference(set(test_tiffiles))
    for g, train_tiffile in enumerate(train_tiffiles):
        ref_geotiff = imgpro.geotiffread(train_tiffile)
        refdata = ref_geotiff.dataarray
        new_array = np.zeros((refdata.shape[0], refdata.shape[1], 5), np.uint16)
        index_num = train_tiffile.split('_')[0].split('.')[0]
        match_id = labelfile_id.index(str(index_num))
        if not match_id is None:
            label_geotiff = imgpro.geotiffread(os.path.join(labelpath, labelfile_name[match_id]))
            labeldata = label_geotiff.dataarray
            # labeldata[labeldata >1]= 0
        # if np.sum(labeldata==1)>= labeldata.shape[0] * labeldata.shape[1] * 0.1:
        try:
            for i in range(4):
                new_array[:, :, i] = refdata[:, :, i]
            new_array[:, :, i+1] = labeldata
            print(os.path.join(train_output, str(index_num) + '_addlable.tif'))
            imgpro.geotiffwrite(os.path.join(train_output, str(index_num) + '_addlable.tif'), new_array, ref_geotiff.geo_transform, ref_geotiff.projection,datatype="UINT16")
        except:
            pass
    print(g)


##重采样
# srcfile = r'I:\sl\南京地区天地图优化\sentinel2-nanjing\nanjingclss_2022-04-18.tif'
# outfile = srcfile.replace('.tif','_resample.tif')
# referencefile = r'I:\sl\南京地区天地图优化\clsscorrect_new.tif'
# geotiffUnify(outfile, srcfile, referencefile, "UINT16")

##切片
# tiffile=r'H:\Tensorflow\image_RGB\lyg20221019GF6\GF6_PMS_E118.8_N35.0_20221019_L1A1120259483_moisc_ref.tif'
# outpath = r'H:\Tensorflow\image_RGB\lyg20221019GF6'
# getTestingSet(tiffile, outpath,imgsize=1024)

# 随机切分训练集和测试集
# image图片路径
# tifpath = r'H:\Tensorflow\sentinel2_image\JPEGImages'
# labelpath = r'H:\Tensorflow\sentinel2_image\Annotations'
# train_output = r'H:\Tensorflow\sentinel2_image\addlabel_image'
# test_output = r'H:\Tensorflow\sentinel2_image\test_image'
# splitTrainingTestSet(tifpath, labelpath, train_output, test_output)


