"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: seg_train.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os
os.environ["FLASH_ATTENTION"] = "0"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import warnings
warnings.filterwarnings("ignore", message="FlashAttention is not available")
warnings.filterwarnings("ignore", message="Using scaled_dot_product_attention instead")
from ultralytics import YOLO
import  os
import cv2
import numpy as np
from osgeo import gdal, osr
import imgProcess as imgpro
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

'''栅格投影'''
def tiffileReproject(srcfile,desfile,dst_epsg):
    geotiff = imgpro.geotiffread(srcfile)
    new_projection = osr.SpatialReference()
    new_projection.ImportFromEPSG(dst_epsg)
    new_projection=new_projection.ExportToWkt()
    gdal.Warp(desfile,srcfile,srcSRS=geotiff.projection,dstSRS=new_projection)

def jpg_t_tif(jpgpath,tifpath):
    '''jpg转tif'''
    jpg_name = os.listdir(jpgpath)
    # print(jpg_name)
    for i in range(len(jpg_name)):
        filename = os.path.splitext(jpg_name[i])[0]
        form = os.path.splitext(jpg_name[i])[1]
        jpg = jpgpath + "\\" + filename + form
        print(jpg)
        jpgdata = imgpro.geotiffread(jpg)
        data = jpgdata.dataarray
        subset_geotrans = jpgdata.geo_transform
        subsetfilename = tifpath+'\\'+filename+'.tif'
        datatype = "UINT8"
        imgpro.geotiffwrite(subsetfilename,data,subset_geotrans,jpgdata.projection,datatype)


def resample_images(referencefilePath, inputfilePath, outputfilePath):  # 影像重采样
    """
    :param referencefilePath: 重采样参考文件路径
    :param inputfilePath: 输入路径
    :param outputfilePath: 输出路径
    """
    # 获取参考影像信息, 其实可以自定义这些信息，有参考的话就不用查这些参数了
    referencefile = gdal.Open(referencefilePath, gdal.GA_ReadOnly)
    referencefileProj = referencefile.GetProjection()
    referencefiletrans = referencefile.GetGeoTransform()
    bandreferencefile = referencefile.GetRasterBand(1)
    width = referencefile.RasterXSize
    height = referencefile.RasterYSize
    bands = referencefile.RasterCount
    # 获取输入影像信息
    inputrasfile = gdal.Open(inputfilePath, gdal.GA_ReadOnly)  # 打开输入影像
    inputProj = inputrasfile.GetProjection()  # 获取输入影像的坐标系
    # 创建重采样输出文件（设置投影及六参数）
    driver = gdal.GetDriverByName('GTiff')  # 这里需要定义，如果不定义自己运算会大大增加运算时间
    output = driver.Create(outputfilePath, width, height, bands, bandreferencefile.DataType)  # 创建重采样影像
    output.SetGeoTransform(referencefiletrans)  # 设置重采样影像的仿射矩阵为参考面的仿射矩阵
    output.SetProjection(referencefileProj)  # 设置重采样影像的坐标系为参考面的坐标系
    # 参数说明 输入数据集、输出文件、输入投影、参考投影、重采样方法(最邻近内插\双线性内插\三次卷积等)、回调函数
    gdal.ReprojectImage(inputrasfile, output, inputProj, referencefileProj, gdal.GRA_Bilinear, 0.0, 0.0, )

"""对栅格进行重采样，改变栅格的大小plus代表原图除以的大小,输入4即变成原图的四分之一"""
def resize_tif(tiffile,plus):
    img=imgpro.geotiffread(tiffile)
    data=img.dataarray
    geo_transform=img.geo_transform
    projection=img.projection
    height,width=data.shape[:2]
    dataarray=cv2.resize(data, dsize=(width//plus,height//plus))
    geo_transform_list=list(geo_transform)
    geo_transform_list[1]=geo_transform_list[1]*(width/(width//plus))
    geo_transform_list[5]=geo_transform_list[5]*(width/(width//plus))

    geo_transform=tuple(geo_transform_list)
    # imgpro.geotiffwrite(outfile,data,geo_transform_new,projection,datatype="UINT8")
    rows, cols, bands = dataarray.shape
    geotiff = geotiffinfo(rows, cols, bands, geo_transform, projection, dataarray)
    return geotiff

def getTrainingSet1(tiffile,shpfile,outpath,imgsize=1024,labelfield='type'):
    # 定义存储路径
    anno_path = os.path.join(outpath, "Annotations")
    jpeg_path = os.path.join(outpath, "JPEGImages")
    if not os.path.exists(anno_path):
        os.mkdir(anno_path)
    if not os.path.exists(jpeg_path):
        os.mkdir(jpeg_path)
    basename = os.path.basename(tiffile)[0:-4]

    # label矢量转栅格
    # geotiff = resize_tif(tiffile,plus)
    geotiff=imgpro.geotiffread(tiffile)
    print('样本已读取')
    rows = geotiff.rows
    cols = geotiff.cols
    print(rows,cols)

    label_array = imgpro.shp2geotiff(shpfile, rows, cols, geotiff.geo_transform, geotiff.projection, field=labelfield)
    # label_array[label_array > 7] = 0  # 重叠样本设为空
    # label_array_info = imgpro.geotiffread(r'I:\paddlex_data\test\fenlei.tif')
    # label_array = label_array_info.dataarray

    # print(label_array_info.rows,label_array_info.cols)
    print('标签已读取')
    # raster设置为满足cv2-RGB图像输出的波段顺序
    data = geotiff.dataarray
    geo_transform = geotiff.geo_transform

    if geotiff.bands == 3:
        t = data[:, :, 2].copy()
        data[:, :, 2] = data[:, :, 0]
        data[:, :, 0] = t

    # 按imgsize裁剪遍历栅格，若label为空pass，否则保存annoimg和jpeg_img

    img_idx = 0  # 样本序号
    step = 256
    for i in range(0, rows, step):
        for j in range(0, cols, step):

            # 取值
            c_label = label_array[i:i + imgsize, j:j + imgsize]
            c_data = data[i:i + imgsize, j:j + imgsize, :]

            data_label = c_label.copy()
            # 非标记区域置为0
            # data_label[c_label == 255] = 0
            data_label[c_label==0]=255
            all_bands_zero = np.all(c_data == 0, axis=-1)
            data_label[all_bands_zero] = 0
            data_label[c_label == 1] = 1
            data_label[c_label == 2] = 2
            data_label[c_label == 3] = 3
            # 非空保存输出
            if c_label.size !=0 and c_data.size !=0:
                if np.max(c_label) > 0 and np.max(c_data) > 0:
                    img_idx = img_idx + 1
                    filename = str(img_idx)
                    cv2.imwrite(os.path.join(anno_path, ""+filename + ".png") , data_label)
                    cv2.imwrite(os.path.join(jpeg_path, ""+filename + ".png") , c_data)
                    print("success!---", str(img_idx))


if __name__ == '__main__':
    model = YOLO(r"F:\data\sample\seg.pt")
    results = model.train(data="coco128-seg.yaml", workers=0,epochs=100, imgsz=640,batch=2,device=0,project="runs", name="seg")