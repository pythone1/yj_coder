'''
@Time    :   2021/04/06 18:20:19
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 基础图像处理
'''

import os
import geopandas as gpd  # 必须先导入geopandas再导入gdal!
from osgeo import gdal, osr
import numpy as np
import glob
import ogr
import scipy.signal as signal
import cv2
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import copy
import imgProcess as imgpro
import math

class geotiffinfo():
    '''
    tif信息
    '''
    def __init__(self,rows,cols,bands,geo_transform,projection,dataarray,epsg,*sensor):
        self.rows=rows
        self.cols=cols
        self.bands=bands
        self.geo_transform=geo_transform
        self.projection=projection
        self.dataarray=dataarray
        self.epsg = epsg
        self.sensor = sensor        
        if sensor == "pms" or sensor == "rededge":
            self.b_index = 0
            self.g_index = 1
            self.r_index = 2
            self.nir_index = 3

# 读栅格文件
def geotiffread(tiffile):
    raster_dataset=gdal.Open(tiffile,gdal.GA_ReadOnly)
    geo_transform=raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()  #获得的是一个指向内部投影参考字符串的指针
    srs = osr.SpatialReference(proj) # 获取投影坐标系
    epsg = srs.GetAttrValue('AUTHORITY',1)   # 获取投影坐标系epsg编号
    dataarray=[]
    for i in range(1,raster_dataset.RasterCount+1):
        band=raster_dataset.GetRasterBand(i)    # 波段从1计数
        dataarray.append(band.ReadAsArray())  #
    
    dataarray=np.dstack(dataarray)
    rows,cols,bands=dataarray.shape
    del raster_dataset,band
    geotiff=geotiffinfo(rows,cols,bands,geo_transform,proj,dataarray,epsg)
    return geotiff

# 获取栅格文件坐标系信息
def getSRSPair(tiffile):
    dataset = gdal.Open(tiffile)
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    return prosrs,geosrs

'''
写栅格文件
tiffile可为*.tif, *.png（datatype需为UINT8）
datatype choose from ["FLOAT32","UINT8"]
'''
def geotiffwrite(tiffile,data,geo_transform,projection,datatype="FLOAT32"):
    driver = gdal.GetDriverByName("GTiff")
    if len(data.shape) == 3:
        rows,cols,bands=data.shape
    elif len(data.shape) == 2:
        rows,cols=data.shape
        bands = 1
    if datatype == "FLOAT32":
        dataset=driver.Create(tiffile,cols,rows,bands,gdal.GDT_Float32,options=["TILED=YES", "COMPRESS=LZW"])
    elif datatype == "UINT8":
        dataset = driver.Create(tiffile,cols,rows,bands,gdal.GDT_Byte,options=["TILED=YES", "COMPRESS=LZW"]) 
    elif datatype == "UINT16":
        dataset = driver.Create(tiffile,cols,rows,bands,gdal.GDT_UInt16,options=["TILED=YES", "COMPRESS=LZW"])
    else:
        print("A datatype dose not support yet!")
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    if bands == 1:
        if len(data.shape) == 2:
            dataset.GetRasterBand(1).WriteArray(data)
        elif len(data.shape) == 3:
            dataset.GetRasterBand(1).WriteArray(data[:,:,0])
    else:
        for i in range(bands):
            dataset.GetRasterBand(i+1).WriteArray(data[:,:,i])
    dataset = None #关闭文件

'''
将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
:param dataset: GDAL地理数据
:param lon: 地理坐标lon经度
:param lat: 地理坐标lat纬度
:return: 经纬度坐标(lon, lat)对应的投影坐标
'''
def lonlat2geo(proj, lon, lat):
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(proj)
    geosrs = prosrs.CloneGeogCS()
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    coords = ct.TransformPoint(lat, lon)
    return coords[:2]

'''
根据GDAL的六参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
''' 
def geo2imagexy(geo_transform, x, y):    
    trans = geo_transform
    a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = np.array([x - trans[0], y - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解

'''
根据GDAL的六参数模型将影像图上坐标（行列号）转为投影或地理坐标
''' 
def imagexy2geo(geo_transform,row,col):
    lng = geo_transform[0] + geo_transform[1] * col
    lat = geo_transform[3] + geo_transform[5] * row
    return lng,lat

'''
创建缓冲区，用于按矢量裁剪栅格模块
矢量文件复杂、直接裁剪结果为空时，可先以0为缓冲距离创建新的矢量
'''
def createBuffer(inputfn, outputBufferfn, bufferDist,fieldName,fieldType):
    # # 支持中文路径
    # gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8","NO")
    # # 使属性表字段支持中文
    # gdal.SetConfigOption("SHAPE_ENCODING","CP936")

    inputds = ogr.Open(inputfn)
    inputlyr = inputds.GetLayer()
    # inputlyrfield=inputlyr.GetLayerDefn()
    spatialRef=inputlyr.GetSpatialRef() # 获取输入空间参考
    # transform = osr.CoordinateTransformation(spatialRef, spatialRef) # 转换
    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(outputBufferfn):
        shpdriver.DeleteDataSource(outputBufferfn)
    outputBufferds = shpdriver.CreateDataSource(outputBufferfn)
    bufferlyr = outputBufferds.CreateLayer(outputBufferfn, srs=spatialRef,geom_type=ogr.wkbPolygon)
    featureDefn = bufferlyr.GetLayerDefn()
    # 新建属性
    infield=ogr.FieldDefn(fieldName,fieldType)
    bufferlyr.CreateField(infield)
    # 添加feature
    for feature in inputlyr:
        ingeom = feature.GetGeometryRef()
        geomBuffer = ingeom.Buffer(bufferDist)
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(geomBuffer)
        # 添加feature属性
        fieldValue=feature.GetField(fieldName)
        outFeature.SetField(fieldName,fieldValue)
        # 添加feature到layer
        bufferlyr.CreateFeature(outFeature)
        outFeature = None

# 按矢量裁剪栅格
def imgclip_with_shp(tiffile,shpfile,outfile):
    if tiffile.endswith(".tif"):
        # tiffile为某个tif文件
        gdal.Warp(outfile,tiffile,cutlineDSName = shpfile,cropToCutline = True,dstNodata = 0)
    else:
        # tiffile为存放多个待裁剪栅格的路径
        os.chdir(tiffile)
        tiffiles = glob.glob("*.tif")
        for f in tiffiles:
            tif = tiffile + "\\" + f
            shp = shpfile + "\\%s.shp"%(f[:-4])
            # 矢量文件复杂、直接裁剪结果为空时，可先以0为缓冲距离创建新的矢量
            shp_buf = shpfile + "\\%s_buffer.shp"%(f[:-4])
            createBuffer(shp, shp_buf, 0.0,'gridcode',ogr.OFTInteger)
            out = outfile + "\\" + f
            gdal.Warp(out,tif,cutlineDSName = shp_buf,cropToCutline = True,dstNodata = 0)
##


'''
按像元数切片
tifdata：geotiffinfo对象
pixelnum：像元数
outpath：切片存放路径
prefix：切片文件名-前缀
suffix：切片文件名-后缀
datatype：数据存储类型
'''
def imgslice_by_pixels(tifpath,pixelnum,outpath,prefix = "subset_",suffix = ".png",datatype = "UINT8"):
    subset_id = 0
    tif_name = os.listdir(tifpath)
    for i in range(len(tif_name)):
        filename = os.path.splitext(tif_name[i])[0]
        form = os.path.splitext(tif_name[i])[1]
        tif = tifpath + "\\" + filename + form
        # tif_list = glob.glob(tifpath + '\\' + '*.tif')
        print(filename)
    # for tif in tif_list:
        tifdata = geotiffread(tif)

        #横轴完整分块数量
        xnum = int(tifdata.cols / pixelnum) #向下取整
        #纵轴完整分块数量
        ynum = int(tifdata.rows / pixelnum)
        print(xnum,ynum)
        data = tifdata.dataarray
        t = data[:,:,0].copy()
        data[:, :, 0]=data[:,:,2]
        data[:, :, 2]=t

        # geo_transform = tifdata.geo_transform

        for i in range(ynum):       #横轴
            startrow = i * pixelnum
            endrow = startrow + pixelnum - 1
            for j in range(xnum):   #纵轴
                startcol = j * pixelnum
                endcol = startcol + pixelnum - 1
                # print(startrow,startcol)
                subset = data[startrow:endrow+1,startcol:endcol+1,:]
                if np.nanmax(np.nanmax(np.nanmax(subset))) == 0 or np.nanmin(np.nanmin(np.nanmin(subset))) == 255:
                    continue
                else:
                    # print(np.nanmax(np.nanmax(subset)),np.nanmin(np.nanmin(subset)))
                    # 分块子集左上角横坐标
                    # leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                    # #分块子集左上角纵坐标
                    # leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                    # subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                    subset_id = subset_id + 1                               #分块从1计数
                    subsetfilename = filename + str(subset_id) + suffix       #裁剪图像保存格式为png
                    subsetfilename = os.path.join(outpath,subsetfilename)
                    cv2.imwrite(subsetfilename,subset)
                    # geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)  #裁剪图像保存数据类型为uint8
            if endcol < tifdata.cols:
                startcol = xnum * pixelnum
                subset = data[startrow:endrow,startcol:,:]
                # if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
                #     continue
                # else:
                    #分块子集左上角横坐标
                # leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                # #分块子集左上角纵坐标
                # leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                # subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                subset_id = subset_id + 1
                subsetfilename = filename + str(subset_id) + suffix
                subsetfilename = os.path.join(outpath,subsetfilename)
                cv2.imwrite(subsetfilename,subset)
                # geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)
        if endrow < tifdata.rows:
            startrow = ynum * pixelnum
            for j in range(xnum):   #纵轴
                startcol = (j-1) * pixelnum
                endcol = j * pixelnum - 1
                subset = data[startrow:,startcol:endcol,:]
                # if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
                #     continue
                # else:
                    #分块子集左上角横坐标
                # leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                # #分块子集左上角纵坐标
                # leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                # subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                subset_id = subset_id + 1
                subsetfilename = filename + str(subset_id) + suffix
                subsetfilename = os.path.join(outpath,subsetfilename)
                cv2.imwrite(subsetfilename,subset)
                # geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)
            if endcol < tifdata.cols:
                startcol = xnum * pixelnum
                subset = data[startrow:,startcol:,:]
                # if ~(np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255):
                    #分块子集左上角横坐标
                # leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                # #分块子集左上角纵坐标
                # leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                # subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                subset_id = subset_id + 1
                subsetfilename = filename + str(subset_id) + suffix
                subsetfilename = os.path.join(outpath,subsetfilename)
                cv2.imwrite(subsetfilename,subset)
                # geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)

'''
按行列数切片
tifdata：geotiffinfo对象
rownum,colnum：行列数
outpath：切片存放路径
prefix：切片文件名-前缀
suffix：切片文件名-后缀
datatype：数据存储类型
'''
def imgslice_by_rowcol(tifdata,rownum,colnum,outpath,prefix="subset_",suffix=".png",datatype="UINT8"):

    imgwidth = int(tifdata.cols / rownum)
    imgheight = int(tifdata.rows / rownum)
    print(imgwidth)
    print(imgheight)
    data = tifdata.dataarray
    geo_transform = tifdata.geo_transform
    subset_id = 0
    for i in range(rownum-1):
        startrow = i * imgheight
        endrow = startrow + imgheight
        for j in range(colnum-1):
            startcol = j  * imgwidth
            endcol = startcol + imgwidth
            subset = data[startrow:endrow,startcol:endcol,:]
            # if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
            #     continue
            # else:
                #分块子集左上角横坐标
            leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
            #分块子集左上角纵坐标
            leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
            subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
            subset_id = subset_id + 1
            subsetfilename = prefix + str(subset_id) + suffix
            subsetfilename = os.path.join(outpath,subsetfilename)
            geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)
        startcol = (colnum-1) * imgwidth
        subset = data[startrow:endrow,startcol:,:]
        # if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
        #     continue
        # else:
            #分块子集左上角横坐标
        leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
        #分块子集左上角纵坐标
        leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
        subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
        subset_id = subset_id + 1
        subsetfilename = prefix + str(subset_id) + suffix
        subsetfilename = os.path.join(outpath,subsetfilename)
        geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)
    startrow = (rownum-1) * imgheight
    for j in range(colnum-1):
        startcol = j * imgwidth
        endcol = startcol + imgwidth
        subset = data[startrow:,startcol:endcol,:]
    # if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
    #     continue
    #     else:
            #分块子集左上角横坐标
        leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
        #分块子集左上角纵坐标
        leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
        subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
        subset_id = subset_id + 1
        subsetfilename = prefix + str(subset_id) + suffix
        subsetfilename = os.path.join(outpath,subsetfilename)
        geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)
    startcol = (colnum-1) * imgwidth
    subset = data[startrow:,startcol:,:]
    # if ~(np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255):
        #分块子集左上角横坐标
    leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
    #分块子集左上角纵坐标
    leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
    subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
    subset_id = subset_id + 1
    subsetfilename = prefix + str(subset_id) + suffix
    subsetfilename = os.path.join(outpath,subsetfilename)
    geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)

# 矢量转栅格
def shp2geotiff(shpfile,rows,cols,geo_transform,projection,field): 
    data_source = gdal.OpenEx(shpfile,gdal.OF_VECTOR)
    tiffile = shpfile.replace(".shp","convert.tif")
    layer=data_source.GetLayer(0)
    driver=gdal.GetDriverByName("GTiff")    #"MEM"
    target_ds=driver.Create(tiffile,cols,rows,1,gdal.GDT_Byte)
    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(projection)
    if field is None:
        gdal.RasterizeLayer(target_ds,[1],layer,None)
    else:
        OPTIONS=['ATTRIBUTE='+field]
        gdal.RasterizeLayer(target_ds,[1],layer,options=OPTIONS)

    band=target_ds.GetRasterBand(1)
    return band.ReadAsArray()

# 图像平滑
def smoothdata(dataarray,method):
    if method == "median":   
        newdata = signal.medfilt(dataarray,5)   #中值滤波
    return newdata


# 栅格转矢量
def createShpfile_from_geotiff(shpfile, tiffile):
    geotiff = geotiffread(tiffile)
    data = geotiff.dataarray[:, :, 0]
    # data[data > 0] = 1
    data[data <= 0] = 0
    driver = gdal.GetDriverByName('MEM')
    raster = driver.Create('', geotiff.cols, geotiff.rows, 1, gdal.GDT_Byte)
    raster.SetGeoTransform(geotiff.geo_transform)
    raster.SetProjection(geotiff.projection)
    raster.GetRasterBand(1).WriteArray(data)
    band = raster.GetRasterBand(1)

    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(shpfile)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(geotiff.projection)
    layer = data_source.CreateLayer(shpfile, srs)
    # 添加属性列
    newField = ogr.FieldDefn('waterTpye', ogr.OFTInteger)
    layer.CreateField(newField)
    gdal.Polygonize(band, band, layer, 0, [], callback=None)
    '''
    gdal.Polygonize(GDALRasterBandH hSrcBand,   //输入栅格图像波段
                    GDALRasterBandH hMaskBand,  //掩膜图像波段，零为空，可以为NULL
                    OGRLayerH hOutLayer,        //矢量化后的矢量图层
                    int iPixValField,           //需要将像元DN值写入矢量属性字段的字段索引
                    char **papszOptions         //算法选项，设为NULL
                    GDALProgressFunc pfnProgress,   //进度条回调函数
                    void *pProgressArg          //进度条参数
    )
    '''
    data_source.Destroy()
    geotiff = None
    band = None

# 返回节点所在行列号
def getImageNodes(data,x1,y1,x2,y2):
    rows,cols = data.shape
    # x3为下一个存在节点的行，默认为0
    x3 = 0
    f_col1 = y1
    f_col2 = y2    
    for i in range(x1+1,rows-1):
        # 前置条件，x1后1行非空
        c_line = data[i,:]
        index = np.where(c_line > 0)
        c_col1 = np.nanmin(index)
        c_col2 = np.nanmax(index)
        b_line = data[i,:]
        if np.nanmax(b_line) > 0:
            # 若x1后2行非空，判断当前行是否存在节点
            index = np.where(b_line > 0)
            b_col1 = np.nanmin(index)
            b_col2 = np.nanmax(index)
            dcf1 = c_col1 - f_col1
            dbc1 = b_col1 - c_col1
            dcf2 = c_col2 - f_col2
            dbc2 = b_col2 - c_col2
            if ((dcf1==0 & dbc1==0) or (dcf1*dbc1>0)) and ((dcf2==0 & dbc2==0) or (dcf2*dbc2>0)):
                # 若左右两侧均无节点，继续扫描下一行
                f_col1 = c_col1
                f_col2 = c_col2
            else:
                # 若左右两侧存在节点（可能是任一侧，可能是两侧），记录左右节点坐标
                x3 = i
                x4 = i
                y3 = c_col1
                y4 = c_col2
                # 标记x3后是否还存在非0行
                flag = True
                break
        else:
            # 若x1后2行为空，则x后1行即为最后1个存在节点的行
            x3 = i
            x4 = i
            y3 = c_col1
            y4 = c_col2
            # 标记x3后是否还存在非0行
            flag = False
            break
    if i == rows-2 and x3 == 0:
        # 若遍历至倒数第一行仍无节点，则data最后一行即为最终行
        x3 = rows-1
        x4 = rows-1
        c_line = data[rows-1,:]
        index = np.where(c_line>0)
        y3 = np.nanmin(index)
        y4 = np.nanmax(index)
        # 标记x3后是否还存在非0行
        flag = False
    return x3,y3,x4,y4,flag

# 栅格转矢量：提取图像边界线
def getImageEdge(tiffile):
    geotiff = geotiffread(tiffile)
    rows = geotiff.rows
    data = geotiff.dataarray[:,:,0]
    # 存放左侧节点行坐标、列坐标
    x1 = []
    y1 = []
    # 存放右侧节点行坐标、列坐标 
    x2 = []
    y2 = []   
    # 确认首行
    for i in range(rows):
        line = data[i,:]        
        if np.nanmax(line) > 0:
            x1.append(i)
            x2.append(i)
            index = np.where(line>0)
            y1.append(np.nanmin(index))
            y2.append(np.nanmax(index))
            flag = True
            break
    # 遍历后续行
    k = 0
    while flag:        
        x3,y3,x4,y4,flag = getImageNodes(data,x1[k],y1[k],x2[k],y2[k])
        x1.append(x3)
        x2.append(x4)
        y1.append(y3)
        y2.append(y4)
        k = k + 1
    pixel_num = len(x1)
    # 行列号转投影或地理坐标
    x1 = np.array(x1).astype(np.int16)
    y1 = np.array(y1).astype(np.int16)
    x2 = np.array(x2).astype(np.int16)
    y2 = np.array(y2).astype(np.int16)
    lng2,lat2 = imagexy2geo(geotiff.geo_transform,y2,x2)    # x为行坐标，对应纬度
    lng1,lat1 = imagexy2geo(geotiff.geo_transform,y1,x1)    # y为列坐标，对应经度
    # 整理坐标为[lng1,lat1,lng2,lat2,...]格式
    pixel_crd = np.zeros((1,pixel_num*4))
    for i in range(pixel_num):
        pixel_crd[0,i*2] = lng2[i]
        pixel_crd[0,i*2+1] = lat2[i]
        pixel_crd[0,pixel_num*4-(i*2+2)] = lng1[i]
        pixel_crd[0,pixel_num*4-(i*2+1)] = lat1[i]
    return pixel_crd    

# 灰度图转伪彩色之按自然间断法获取间断点
def getBreakpointsByJecks(data,num = 5):
    data = data[data>0]
    minvalue = np.nanmin(data)
    maxvalue = np.nanmax(data)        
    bins = np.linspace(minvalue,maxvalue,101)  # 101个结点，分100个区间
    frequence,_,_ = plt.hist(data,bins,histtype='bar',cumulative=True)
    total_num = len(data)
    y = frequence / total_num
    intervals = np.linspace(0,1,num+1)    # 分5个色阶，有6个结点
    breakpoints = [0]
    brk_index = [0]
    for i in range(1,num+1):
        t = intervals[i]
        t = np.abs(y - t)
        brk_index.append(np.where(t==np.nanmin(t))[0][0])
        breakpoints.append(bins[brk_index[i]])
    return breakpoints

# 灰度图转伪彩色之按自然间断法设色
def gray2colors(tiffile,uplimit=10):
    geotiff = geotiffread(tiffile)
    data = geotiff.dataarray[:,:,0]
    data[data>uplimit] = 0      # 超过上限值的不着色
    breakpoints = getBreakpointsByJecks(data)
    # 设置归一化原则：数组归一化到[0,1]
    norm_rule = mpl.colors.BoundaryNorm(breakpoints,100)
    # 设置颜色映射规则：[0,1]映射到颜色表
    list_colors = [(0.9412,0.5843,0.2078),(1,1,0.3294),(0.3176,0.9804,0.1176),(0.2314,0.7412,0.9608),(0.6706,0.9961,1)]
    cm = mpl.colors.LinearSegmentedColormap.from_list("style1",list_colors,N=100)
    fig = plt.figure()
    ax = plt.axes()
    im = ax.imshow(data,norm = norm_rule,interpolation='nearest',origin='lower',cmap=cm)
    plt.colorbar(im,cmap=cm,norm=norm_rule)   
    # 保存图像
    path = os.path.dirname(tiffile)
    filename = os.path.basename(tiffile).replace(".tif","_FC.jpg")
    plt.savefig(filename,dpi = 300) 
    plt.show()
    

# 图像线性拉伸-获取间断点
def getBreakpointsByLinear(data,mode = '2%'):
    data = data[data>0]
    minvalue = np.nanmin(data)
    maxvalue = np.nanmax(data)
    bins = np.linspace(minvalue,maxvalue,101)   # 101个结点，分100个区间
    cml_frequence,_,_ = plt.hist(data,bins,histtype='bar',cumulative=True)
    total_num = len(data)
    y = cml_frequence / total_num
    if mode == '2%':
        t = np.abs(y-0.02)
        st_index = np.where(t==np.nanmin(t))[0][0]
        st_value = bins[st_index]
        t = np.abs(y-0.98)
        ed_index = np.where(t==np.nanmin(t))[0][0]
        ed_value = bins[ed_index]
    elif mode == '5%':
        t = np.abs(y-0.05)
        st_index = np.where(t==np.nanmin(t))[0][0]
        st_value = bins[st_index]
        t = np.abs(y-0.95)
        ed_index = np.where(t==np.nanmin(t))[0][0]
        ed_value = bins[ed_index]
    return int(st_value),int(ed_value)

# 反射率（16位4波段）转RGB（8位3波段）,2% | 5%线性拉伸(stretch_mode = "2%" |stretch_mode =  "5%")
def ref2RGB(data,RGBfile,stretch_mode):
    # geotiff = geotiffread(reffile)
    # data = geotiff.dataarray
    # data = data[:,:,0:3]
    for i in range(3):
        t = data[:,:,i]
        t_st,t_ed = getBreakpointsByLinear(t,mode=stretch_mode)
        t[t < t_st] = t_st
        t[t > t_ed] = t_ed
        t = (t - t_st) / (t_ed - t_st) * 254 + 1  # 有效值的映射范围 [1,255]
        t[data[:, :, i] == 0] = 0  # 背景值设0
        data[:, :, i] = t.copy()
    # r = copy.deepcopy(data[:,:,2])
    # data[:,:,2] = copy.deepcopy(data[:,:,0])
    # data[:,:,0] = copy.deepcopy(r)
    # geotiffwrite(RGBfile,data,geotiff.geo_transform,geotiff.projection,datatype="UINT8")
    return  data

##########投影转换#############
##############################
'''栅格投影'''
def tiffileReproject(srcfile,desfile,dst_epsg):
    geotiff = imgpro.geotiffread(srcfile)
    new_projection = osr.SpatialReference()
    new_projection.ImportFromEPSG(dst_epsg)
    new_projection=new_projection.ExportToWkt()
    gdal.Warp(desfile,srcfile,srcSRS=geotiff.projection,dstSRS=new_projection)

# 计算FUI,SD
def derive_FUI(data):
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
    # plt.imshow(alpha)
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
    del sd1,sd2
    return FUI,SD

def dbwi_extract(data):
    b = data[:, :, 0].astype(float)
    g = data[:, :, 1].astype(float)
    # r = data[:, :, 2].astype(float)
    # NIR = data[:, :, 3].astype(float)
    dbwi = (g - b)
    # ndwi = (g - NIR) / (g + NIR)
    # dbwi[ndwi < 0] = 0
    return dbwi

if __name__ == '__main__':
    import gdal
    import numpy as np

    data_path = r'D:\Desktop\test\1\2015-2020\sample\label'
    label_list = glob.glob(data_path+'//'+'*.tif')
    n_class0 = 0
    n_class1 = 0
    n_class2 = 0
    for label in label_list:
        print(label)
        src = gdal.Open(label).ReadAsArray()
        n_class0 += np.sum(np.where(src == 0))
        n_class1 += np.sum(np.where(src == 1))
        n_class2 += np.sum(np.where(src == 255))
    sum = n_class0+n_class1+n_class2
    print("背景：{}，第一类：{}，第二类：{}".format(n_class0/sum , n_class1/sum,n_class2/sum))
    print(sum)

    # shpfile=r'C:\Users\Administrator\Documents\WXWork\1688858186325806\Cache\File\2023-03\clsscorrect_pro_delectpatches.shp'
    # shp2geotiff(shpfile, rows, cols, geo_transform, projection, field)
    # data = cv2.imread(r'E:\paddleseg\dataset\remote\train\1.png')
    # imgsize = 1024
    # for i in range(0, 4096, 1024):
    #     for j in range(0, 4096, 1024):
    #         name =str(i)+str(j)
    #         c_data = data[i:i + imgsize, j:j + imgsize, :]
    #         cv2.imwrite(r'E:\paddleseg\dataset\remote\train'+'\\'+name+'.png', c_data)
    # reffile = r'D:\Users\Desktop\water_shp\S3B_OL_1_EFR____20230109T022651_20230109T022951_20230109T114758_0179_074_374_2340_PS2_O_NT_003_1024RGG.jpg'
    # geotiff = geotiffread(reffile)
    # dataarray = geotiff.dataarray
    # RGBfile = r'D:\Users\Desktop\water_shp\5.jpg'
    # stretch_mode = "2%"
    # dataarray=ref2RGB(dataarray, RGBfile, stretch_mode)
    # geotiffwrite(RGBfile,dataarray,geotiff.geo_transform,geotiff.projection,datatype="UINT8")
    # 矢量裁剪栅格
    # tiffile = r'D:\Users\Desktop\启动无人机\1125中央河\1125中央河多光谱镶嵌.tif'
    # shpfile = r'D:\Users\Desktop\启动无人机\1125中央河\1125中央河水域.shp'
    # outfile = r'D:\Users\Desktop\启动无人机\1125中央河\shuiyu.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)
    #
    # #计算FUI,SD,DBWI
    # geotifinfo = geotiffread(outfile)
    # data = geotifinfo.dataarray
    # FUI, SD =derive_FUI(data)
    # DBWI = dbwi_extract(data)
    #
    # geotiffwrite(r'D:\Users\Desktop\启动无人机\1125中央河\结果\fui.tif',FUI,geotifinfo.geo_transform,geotifinfo.projection)
    # geotiffwrite(r'D:\Users\Desktop\启动无人机\1125中央河\结果\sd.tif', SD, geotifinfo.geo_transform, geotifinfo.projection)
    # geotiffwrite(r'D:\Users\Desktop\启动无人机\1125中央河\结果\dbwi.tif', DBWI, geotifinfo.geo_transform, geotifinfo.projection)




    # reffile = r'H:\=学习\无人机三期\原始影像\dgg.tif'
    # RGBfile = r'H:\=学习\无人机三期\波段转换\dgg.tif'
    # stretch_mode = "2%"
    # ref2RGB(reffile, RGBfile, stretch_mode)

    # shpfile = r'D:\Users\Administrator\Desktop\best_model\tif\slice\slice\1.shp'
    # tiffile = r'D:\Users\Administrator\Desktop\best_model\tif\1.tif'
    # createShpfile_from_geotiff(shpfile, tiffile)

    # tifpath = r'L:\长江南京段无人机影像\信大无人机\11月北岸'
    # # tif_list = glob.glob(tifpath + '\\' + '*.tif')
    # # for tif in tif_list:
    # # tifdata=geotiffread(tif)
    # pixelnum=512
    # outpath=r'I:\paikou\tif'
    # imgslice_by_pixels(tifpath, pixelnum, outpath, prefix="", suffix=".tif", datatype="UINT8")
    #
    # tifdata = geotiffread(r'E:\paddleseg\dataset\remote\train').dataarray
    # outpath= r'E:\paddleseg\dataset\remote\train'
    # rownum= 4
    # colnum= 4
    # imgslice_by_rowcol(tifdata, rownum,colnum, outpath, prefix="", suffix=".jpg", datatype="UINT8")
    # A_list = glob.glob(r'E:\PY\STANet\dataset\val\label'+ '\\' + '*.png')

    # print(A_list)
    # outpath = r'E:\PY\STANet\dataset\255\val\label'
    # i=1
    # for tif in A_list:
    #     print(tif)
    #     tifdata = geotiffread(tif)
    #     rownum = int(4)
    #     colnum = int(4)
    #     imgslice_by_rowcol(tifdata, rownum, colnum, outpath, prefix=str(i), suffix=".png", datatype="UINT8")
    #     i+=1






    # srcfile=(r'H:\148\S2A_MSIL2A_20210710T024551_N0301_R132_T50SQD_20210710T044905_RGB.tif')
    # desfile=(r'H:\148\SQD.tif')
    # dst_epsg=4326
    # tiffileReproject(srcfile, desfile, dst_epsg)


    # tifpath = r'H:\头兴港0617'
    # outpath = r'H:\头兴港0617\裁剪'
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     print(tiffile)
    #     geotiff = geotiffread(tiffile)
    #     data = geotiff.dataarray
    #     data[data==-10000] = 0
    #     geotiffwrite(os.path.join(outpath,tiffile),data,geotiff.geo_transform,geotiff.projection)

    # tiffiles = r'H:\148\rf\st\1'  # 黑臭指数saturation
    # for tiffile in tiffiles:
    #     geotiff = geotiffread(tiffile)
    #     data = geotiff.dataarray
    #     mask = np.zeros_like(data)
    #     mask[data < 0.025] = 1
    #     geotiffwrite(tiffile[0:-4] + "_lt0025.tif", mask, geotiff.geo_transform, geotiff.projection)

    # tiffile = r'H:\148\rf\st\1\S2A_MSIL2A_20210710T024551_N0301_R132_T50SQD_20210710T044905_REF10m_saturation.tif'  # 黑臭指数saturation
    # geotiff = geotiffread(tiffile)
    # data = geotiff.dataarray
    # mask = np.zeros_like(data)
    # mask[data < 0.025] = 1
    # geotiffwrite(tiffile[0:-4] + "_lt0025.tif", mask, geotiff.geo_transform, geotiff.projection)

    # # 根据reflectance仅仅出SD文件
    # path = r'E:\Work\xuzhou_yanhe\reflectance\reflectance'  #输入给定的reflectance的文件夹
    # outpath = r'E:\Work\xuzhou_yanhe\sd'                    #输出的文件夹
    # os.chdir(path)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles
    #     geotiff = imgpro.geotiffread(tiffile)
    #     data = geotiff.dataarray.astype(np.float)
    #     ndwi = (data[:, :, 1] - data[:, :, 3]) / (data[:, :, 1] + data[:, :, 3])
    #     data[ndwi < 0] = 0
    #     FUI, SD = derive_FUI(data)
    #     outfile = os.path.join(outpath, tiffile[0:-4] + '_SD.tif')
    #     imgpro.geotiffwrite(outfile, SD, geotiff.geo_transform, geotiff.projection, datatype="FLOAT32")

    # imgslice_by_pixels(tifpath, pixelnum, outpath, prefix="subset_", suffix=".png", datatype="UINT8")