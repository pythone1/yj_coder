'''
@Time    :   2021/04/06 18:20:19
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 基础图像处理
'''
import math
import os
import geopandas as gpd  # 必须先导入geopandas再导入gdal!
from osgeo import gdal,ogr,osr
import numpy as np
import glob
import scipy.signal as signal
import cv2
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd
import copy

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
def geotiffread(tiffile,drange=None):
    '''
    读影像
    tiffile:str 文件名
    drange: str 读取范围，None读取所有行列，否则用[xoff,yoff,xsize,ysize]指定读取范围
    '''
    raster_dataset=gdal.Open(tiffile,gdal.GA_ReadOnly)
    geo_transform=raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()  #获得的是一个指向内部投影参考字符串的指针
    srs = osr.SpatialReference(proj) # 获取投影坐标系
    epsg = srs.GetAttrValue('AUTHORITY',1)   # 获取投影坐标系epsg编号

    if drange is None:
        # dataarray=[]
        # for i in range(1,raster_dataset.RasterCount+1):
        #     band=raster_dataset.GetRasterBand(i)    # 波段从1计数
        #     dataarray.append(band.ReadAsArray())  #
        # dataarray=np.dstack(dataarray)
        # del raster_dataset,band
        dataarray = raster_dataset.ReadAsArray()
        if len(dataarray.shape) == 3:
            dataarray = np.transpose(dataarray,(1,2,0))
    else:
        # drange = [xoff,yoff,xsize,ysize]
        # 防止溢出
        xoff = max(0,drange[0])
        yoff = max(0,drange[1])
        xsize = min(raster_dataset.RasterXSize-xoff,drange[2])
        ysize = min(raster_dataset.RasterYSize-yoff,drange[3])
        dataarray = raster_dataset.ReadAsArray(xoff,yoff,xsize,ysize)
        if len(dataarray.shape) == 3:
            dataarray = np.transpose(dataarray,(1,2,0))
        
        # 用0补全drange范围
        if len(dataarray.shape) == 3:
            if drange[0]<0:
                dataarray = np.pad(dataarray,((0,0),(0,0),(-drange[0],0)),'constant',constant_values=0)
            if drange[1]<0:
                dataarray = np.pad(dataarray,((0,0),(-drange[1],0),(0,0)),'constant',constant_values=0)
            if drange[2]>raster_dataset.RasterXSize-drange[0]:
                w = drange[2] - (raster_dataset.RasterXSize-drange[0])
                dataarray = np.pad(dataarray,((0,0),(0,0),(0,w)),'constant',constant_values=0)
            if drange[3]>raster_dataset.RasterYSize-drange[1]:
                w = drange[3] - (raster_dataset.RasterYSize-drange[1])
                dataarray = np.pad(dataarray,((0,0),(0,w),(0,0)),'constant',constant_values=0)
        elif len(dataarray.shape) == 2:
            if drange[0]<0:
                dataarray = np.pad(dataarray,((0,0),(-drange[0],0)),'constant',constant_values=0)
            if drange[1]<0:
                dataarray = np.pad(dataarray,((-drange[1],0),(0,0)),'constant',constant_values=0)
            if drange[2]>raster_dataset.RasterXSize-drange[0]:
                w = drange[2] - (raster_dataset.RasterXSize-drange[0])
                dataarray = np.pad(dataarray,((0,0),(0,w)),'constant',constant_values=0)
            if drange[3]>raster_dataset.RasterYSize-drange[1]:
                w = drange[3] - (raster_dataset.RasterYSize-drange[1])
                dataarray = np.pad(dataarray,((0,w),(0,0)),'constant',constant_values=0)

        geo_transform = (geo_transform[0]+drange[0]*geo_transform[1],geo_transform[1],0,
                         geo_transform[3]+drange[1]*geo_transform[5],0,geo_transform[5])

    rows,cols = dataarray.shape[0:2]
    bands = dataarray.shape[2] if len(dataarray.shape)>2 else 1
    geotiff=geotiffinfo(rows,cols,bands,geo_transform,proj,dataarray,epsg)

    return geotiff

def getGeoInfo(tiffile):
    raster_dataset=gdal.Open(tiffile,gdal.GA_ReadOnly)
    geotrans=raster_dataset.GetGeoTransform()
    cols = raster_dataset.RasterXSize
    rows = raster_dataset.RasterYSize
    proj = raster_dataset.GetProjection()  #获得的是一个指向内部投影参考字符串的指针
    srs = osr.SpatialReference(proj) # 获取投影坐标系
    epsg = srs.GetAttrValue('AUTHORITY',1)   # 获取投影坐标系epsg编号

    return geotrans,rows,cols,epsg


# 获取栅格文件坐标系信息
def getSRSPair(tiffile):
    dataset = gdal.Open(tiffile)
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    return prosrs,geosrs
def getNDWI(refdata):
    refdata = refdata.astype(np.float)
    nir = refdata[:,:,3]
    g = refdata[:,:,1]
    ndwi = (g-nir)/(g+nir)
    return ndwi


'''
写栅格文件
tiffile可为*.tif, *.png（datatype需为UINT8）
datatype choose from ["FLOAT32","UINT8"]
'''
def geotiffwrite(tiffile,data,geo_transform,projection,datatype="UINT8"):
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
            createBuffer(shp, shp_buf, 500,'gridcode',ogr.OFTInteger)
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

def imgslice_by_pixels(tifpath,pixelnum,outpath,prefix = "subset_",suffix = ".png",datatype = ""):
    
    # tif_name = os.listdir(tifpath)
    # for i in range(len(tif_name)):
    #     filename = os.path.splitext(tif_name[i])[0]
    #     form = os.path.splitext(tif_name[i])[1]
    #     tif = tifpath + "\\" + filename + form
    #     # tif_list = glob.glob(tifpath + '\\' + '*.tif')
    #     print(filename)
    # for tif in tif_list:
    tifdata = geotiffread(tifpath)
    #横轴完整分块数量
    xnum = int(tifdata.cols / pixelnum) #向下取整
    #纵轴完整分块数量
    ynum = int(tifdata.rows / pixelnum)
    print(xnum,ynum)
    data = tifdata.dataarray
    geo_transform = tifdata.geo_transform
    subset_id = 0
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
                #分块子集左上角横坐标
                leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                #分块子集左上角纵坐标
                leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                subset_id = subset_id + 1                               #分块从1计数
                subsetfilename = str(subset_id) + suffix       #裁剪图像保存格式为png
                subsetfilename = os.path.join(outpath,subsetfilename)
                geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)  #裁剪图像保存数据类型为uint8
        if endcol < tifdata.cols:
            startcol = xnum * pixelnum
            subset = data[startrow:endrow,startcol:,:]
            if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
                continue
            else:
                #分块子集左上角横坐标
                leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                #分块子集左上角纵坐标
                leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                subset_id = subset_id + 1
                subsetfilename = str(subset_id) + suffix
                subsetfilename = os.path.join(outpath,subsetfilename)
                geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)
    if endrow < tifdata.rows:
        startrow = ynum * pixelnum
        for j in range(xnum):   #纵轴
            startcol = (j-1) * pixelnum
            endcol = j * pixelnum - 1
            subset = data[startrow:,startcol:endcol,:]
            if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
                continue
            else:
                #分块子集左上角横坐标
                leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                #分块子集左上角纵坐标
                leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                subset_id = subset_id + 1
                subsetfilename =  str(subset_id) + suffix
                subsetfilename = os.path.join(outpath,subsetfilename)
                geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)
        if endcol < tifdata.cols:
            startcol = xnum * pixelnum
            subset = data[startrow:,startcol:,:]
            if ~(np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255):
                #分块子集左上角横坐标
                leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
                #分块子集左上角纵坐标
                leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
                subset_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])
                subset_id = subset_id + 1
                subsetfilename = str(subset_id) + suffix
                subsetfilename = os.path.join(outpath,subsetfilename)
                geotiffwrite(subsetfilename,subset,subset_geotrans,tifdata.projection,datatype)

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

    imgwidth = int(tifdata.cols / rownum)    #向下取整
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
            if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
                continue
            else:
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
        if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
            continue
        else:
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
        if np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255:
            continue
        else:
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
    if ~(np.nanmax(np.nanmax(subset)) == 0 or np.nanmin(np.nanmin(subset)) == 255):
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
    tiffile = shpfile.replace(".shp",".tif")  
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
def createShpfile_from_geotiff(shpfile,tiffile):
    geotiff = geotiffread(tiffile)
    data = geotiff.dataarray
    # data[data>0] = 1
    data[data<=0] = 0
    driver = gdal.GetDriverByName('MEM')
    raster = driver.Create('',geotiff.cols, geotiff.rows, 1, gdal.GDT_Byte)
    raster.SetGeoTransform(geotiff.geo_transform)
    raster.SetProjection(geotiff.projection)
    raster.GetRasterBand(1).WriteArray(data)
    band = raster.GetRasterBand(1)
    
    if shpfile.endswith('.shp'):
        driver = ogr.GetDriverByName("ESRI Shapefile")
    elif shpfile.endswith('.gpkg'):
        driver = ogr.GetDriverByName("GPKG")
    data_source = driver.CreateDataSource(shpfile)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(geotiff.projection)
    layer = data_source.CreateLayer(shpfile,srs)
    # 添加属性列
    newField = ogr.FieldDefn('MASK', ogr.OFTInteger)
    layer.CreateField(newField)   
    gdal.Polygonize(band, band, layer,0, [], callback=None )
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
    geotiff= None
    band=None

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
    elif mode == '1%':
        t = np.abs(y-0.01)
        st_index = np.where(t==np.nanmin(t))[0][0]
        st_value = bins[st_index]
        t = np.abs(y-0.99)
        ed_index = np.where(t==np.nanmin(t))[0][0]
        ed_value = bins[ed_index]
    return st_value,ed_value

# 反射率（16位4波段）转RGB（8位3波段）,2% | 5%线性拉伸(stretch_mode = "2%" |stretch_mode =  "5%")
def ref2RGB(data,bands=[3,2,1],stretch_mode='2%'):
    data = data[:,:,bands]
    for i in range(3):
        t = data[:,:,i].copy()
        t_st,t_ed = getBreakpointsByLinear(t,mode=stretch_mode)
        t[t < t_st] = t_st
        t[t > t_ed] = t_ed
        t = (t - t_st) / (t_ed - t_st) * 254 + 1  # 有效值的映射范围 [1,255]
        t[data[:, :, i] == 0] = 0  # 背景值设0
        data[:, :, i] = t.copy()
    # geotiffwrite(RGBfile,data,geotiff.geo_transform,geotiff.projection,datatype="UINT8")
    return data.astype('uint8')

##########投影转换#############
##############################
'''栅格投影'''
def tiffileReproject(srcfile,desfile,dst_epsg):
    geotiff = geotiffread(srcfile)
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
        jpgdata = geotiffread(jpg)
        data = jpgdata.dataarray
        subset_geotrans = jpgdata.geo_transform
        subsetfilename = tifpath+'\\'+filename+'.tif'
        datatype = "UINT8"
        geotiffwrite(subsetfilename,data,subset_geotrans,jpgdata.projection,datatype)


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
    # bands = 1
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


def geotiffread_pix(tiffile, xoff=0, yoff=0, window_size=None):

    raster_dataset = gdal.Open(tiffile, gdal.GA_ReadOnly)
    geo_transform = raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()
    srs = osr.SpatialReference(wkt=proj)
    epsg = srs.GetAttrValue('AUTHORITY', 1)

    if window_size:
        xsize = min(window_size[0], raster_dataset.RasterXSize - xoff)
        ysize = min(window_size[1], raster_dataset.RasterYSize - yoff)
    else:
        xsize, ysize = raster_dataset.RasterXSize, raster_dataset.RasterYSize

    dataarray = []
    for band_index in range(1, raster_dataset.RasterCount + 1):
        band = raster_dataset.GetRasterBand(band_index)
        data = band.ReadAsArray(xoff, yoff, xsize, ysize)
        if data is not None:
            dataarray.append(data)

    if not dataarray:
        return None
    if len(dataarray) == 1:
        dataarray = dataarray[0]
    else:
        dataarray = np.dstack(dataarray)
    top_left_x = geo_transform[0] + xoff * geo_transform[1]
    top_left_y = geo_transform[3] + yoff * geo_transform[5]
    current_geo_transform = (
        top_left_x, geo_transform[1], geo_transform[2], top_left_y, geo_transform[4], geo_transform[5])
    geotiff = geotiffinfo(xsize, ysize, raster_dataset.RasterCount, current_geo_transform, proj, dataarray, epsg)
    return geotiff
def style_transfer(source_image, target_image):
    # 快速fft变换
    h, w, c = source_image.shape
    out = []
    for i in range(c):
        source_image_f = np.fft.fft2(source_image[:, :, i])
        source_image_fshift = np.fft.fftshift(source_image_f)
        target_image_f = np.fft.fft2(target_image[:, :, i])
        target_image_fshift = np.fft.fftshift(target_image_f)

        change_length = 1
        source_image_fshift[int(h / 2) - change_length:int(h / 2) + change_length,
        int(h / 2) - change_length:int(h / 2) + change_length] = \
            target_image_fshift[int(h / 2) - change_length:int(h / 2) + change_length,
            int(h / 2) - change_length:int(h / 2) + change_length]

        source_image_ifshift = np.fft.ifftshift(source_image_fshift)
        source_image_if = np.fft.ifft2(source_image_ifshift)
        source_image_if = np.abs(source_image_if)

        source_image_if[source_image_if > 255] = np.max(source_image[:, :, i])
        out.append(source_image_if)
    out = np.array(out)
    out = out.swapaxes(1, 0).swapaxes(1, 2)

    out = out.astype(np.uint8)
    return out

def fft_save(data_path):
    img_path_A = os.path.join(data_path, 'A')
    img_path_B = os.path.join(data_path, 'B')
    img_B_save = os.path.join(data_path, 'A_fft')
    names = os.listdir(img_path_A)
    print(names)
    if not os.path.exists(img_B_save):
        os.mkdir(img_B_save)
    for name in names:
        img_A = cv2.imread(os.path.join(img_path_A, name))
        img_B = cv2.imread(os.path.join(img_path_B, name))
        img_B_fft = style_transfer(source_image=img_A, target_image=img_B)
        cv2.imwrite(os.path.join(img_B_save, name), img_B_fft)
def derive_FUI(data):
    '''
    功能：计算水色指数、水体透明度
    data: np.array
    返回：
    FUI: np.array
    SD: np.array
    '''
    rows, cols, bands = data.shape
    # 波段选择
    r = 3 - 1
    g = 2 - 1
    b = 1 - 1
    R = data[:, :, r]
    G = data[:, :, g]
    B = data[:, :, b]
    X = 2.7689 * R + 1.7517 * G + 1.1302 * B
    Y = 1.0000 * R + 4.5907 * G + 0.0601 * B
    Z = 0.0565 * G + 5.5943 * B
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    # z = Z / (X + Y + Z)
    del R, G, B, X, Y, Z
    x1 = y - 0.3333
    y1 = x - 0.3333
    alpha = np.zeros([rows, cols])
    for i in range(rows):
        for j in range(cols):
            alpha[i, j] = math.atan2(y1[i, j], x1[i, j]) * 180 / np.pi
    # plt.imshow(alpha)
    del x1, y1
    FUI = np.zeros([rows, cols])
    a = np.array([-140.054, -135.414, -123.059, -107.207, -91.443, -60.546, -27.923,
                  -11.913, 1.634, 11.445, 19.243, 21.424, 22.644, 25.429, 27.926, 31.411,
                  35.226, 40.552, 46.222, 50.339, 55.587])
    for i in range(20):
        FUI[alpha >= a[i]] = i + 1
    FUI[alpha > a[20]] = 21
    a1 = alpha.copy()
    a1 = a1 + 180
    a1[FUI >= 8] = 0
    a2 = FUI.copy()
    a2[FUI < 8] = 0
    sd1 = 8144.5 / np.power(a1, 1.534)
    sd2 = 44.122 / np.power(a2, 1.138)
    SD = sd1
    SD[FUI >= 8] = sd2[FUI >= 8]
    SD[np.isnan(SD)] = 0
    del sd1, sd2
    return FUI, SD

def waterMask(refdata, threshold=0):
    '''
    功能：利用NDWI进行水域掩膜
    返回: np.array,非水域设0，水域保留原值
    refdata: np.dataarray 反射率
    threshold: float 阈值，小于该阈值的为非水体，大于阈值为水体
    '''
    watermask = getNDWI(refdata)
    watermask[watermask < threshold] = 0
    watermask[watermask > threshold] = 1
    # refdata[watermask == 0] = 0
        # refdata[watermask==1] = 1
    # return refdata
    return watermask

def getNDWI(refdata):
    '''
    功能：计算NDWI(水体指数)，用于提取水域
    原理：水体近红外吸收更大
    refdata: np.dataarray 反射率

    '''
    refdata = refdata.astype(np.float64)
    g,nir = refdata[:,:,1],refdata[:,:,3]
    ndwi = (g-nir)/(g+nir)

    return ndwi
# 图像平滑
def smoothdata(dataarray,method="median"):
    if method == "median":
        newdata = signal.medfilt(dataarray,5)   #中值滤波
    return newdata


def resample_images(inputfilePath, outputfilePath, width, height):
    """
    :param inputfilePath: 输入路径
    :param outputfilePath: 输出路径
    :param width: 输出影像宽度
    :param height: 输出影像高度
    """

    # 打开输入影像
    inputrasfile = gdal.Open(inputfilePath, gdal.GA_ReadOnly)
    inputProj = inputrasfile.GetProjection()  # 获取输入影像的坐标系
    inputGeoTrans = inputrasfile.GetGeoTransform()  # 获取输入影像的仿射矩阵

    # 计算重采样输出文件的 GeoTransform
    x_res = inputGeoTrans[1] * inputrasfile.RasterXSize / width
    y_res = inputGeoTrans[5] * inputrasfile.RasterYSize / height
    outputGeoTrans = (inputGeoTrans[0], x_res, inputGeoTrans[2], inputGeoTrans[3], inputGeoTrans[4], y_res)

    # 创建重采样输出文件（设置投影及六参数）
    driver = gdal.GetDriverByName('GTiff')
    output = driver.Create(outputfilePath, width, height, inputrasfile.RasterCount, inputrasfile.GetRasterBand(1).DataType)
    output.SetGeoTransform(outputGeoTrans)
    output.SetProjection(inputProj)


    gdal.ReprojectImage(inputrasfile, output, inputProj, None, gdal.GRA_Bilinear, 0.0, 0.0, )
        # gdal.ReprojectImage(input_band, output_band, None, None, gdal.GRA_Bilinear)

    # gdal.ReprojectImage(inputrasfile, output, inputProj, None, gdal.GRA_Bilinear, 0.0, 0.0, )
    # 关闭文件
    output.FlushCache()
    output = None
    inputrasfile = None

def getNDVI(refdata):
    '''
    功能：计算NDWI(水体指数)，用于提取水域
    原理：水体近红外吸收更大
    refdata: np.dataarray 反射率

    '''
    # refdata = refdata.astype(np.float64)
    red,nir = refdata[:,:,0],refdata[:,:,3]
    ndvi = (nir - red) / (nir + red)

    return ndvi

def getNDBI(refdata):
    '''
    功能：计算NDWI(水体指数)，用于提取水域
    原理：水体近红外吸收更大
    refdata: np.dataarray 反射率

    '''
    # refdata = refdata.astype(np.float64)
    swir,nir = refdata[:,:,4],refdata[:,:,3]
    ndbi = (swir - nir) / (nir + swir)

    return ndbi
def create_pyramids(output_file):
    ds = gdal.Open(output_file, gdal.GA_ReadOnly)
    gdal.SetConfigOption('COMPRESS_OVERVIEW', 'LZW')
    ds.BuildOverviews('NEAREST', [2, 4, 8, 16, 32, 64])
    del ds  # 关闭数据集


# if __name__ == '__main__':
    files = glob.glob(r'S:\哨兵数据\哨兵反射率\RQV')
    for file in files:
        print(file)
        create_pyramids(file)

    files = glob.glob(r'S:\哨兵数据\哨兵反射率\SQA')
    for file in files:
        print(file)
        create_pyramids(file)

    # files = glob.glob(r'I:\江苏省哨兵数据下载\REF\pymaid\*.tif')
    # for file in files:
    #     print(file)
    #     create_pyramids(file)
    # data = geotiffread_pix(r'S:\项目数据\江苏省养殖池塘\1m土地覆被分类_重投影\金坛区.tif')
    # print(data.dataarray.shape)

    # filelist = glob.glob(r'F:\20231029\*.tif')
    # for tiffile in filelist:
    #     refdata = geotiffread(tiffile)
    #     directory, filename = os.path.split(tiffile)
    #     filename, extension = os.path.splitext(filename)
    #     # 添加后缀到文件名
    #     new_filename = filename + '_NDWI' + extension
    #     # 重新组合得到新的文件路径
    #     new_path = os.path.join(directory, new_filename)
    #     ndwi = waterMask(refdata.dataarray)
    #     geotiffwrite(new_path,ndwi,refdata.geo_transform,refdata.projection)
    # ref_list = glob.glob(r'I:\pyMethod\segment-anything\lyg\1\REF切片\*.tif')
    # for tif in ref_list:
    #     info = geotiffread(tif)
    #     ndvidata = getNDVI(info.dataarray)
    #     ndwidata = getNDWI(info.dataarray)
    # tifdata = geotiffread(r'I:\pyMethod\segment-anything\data\哨兵水域提取测试\big_tif\minnir.tif')
    # rownum = 3
    # colnum = 3
    # outpath = r'I:\pyMethod\segment-anything\data\哨兵水域提取测试\big_tif'
    # imgslice_by_rowcol(tifdata, rownum, colnum, outpath, prefix="subset_", suffix=".tif", datatype="FLOAT32")


    # geotiff = geotiffread(r'I:\pyMethod\segment-anything\data\哨兵水域提取测试\256_200\哨兵二测试.tif')
    # data = ref2RGB(geotiff, stretch_mode='2%')
    # RGBfile = r'I:\pyMethod\segment-anything\data\哨兵水域提取测试\256_200\RGB1111.tif'
    # geotiffwrite(RGBfile,data,geotiff.geo_transform,geotiff.projection,datatype="UINT8")


    #     ndvifile = r'I:\pyMethod\segment-anything\lyg\1\REF切片\NDVI' + '\\' + os.path.basename(tif)
    #     ndwifile = r'I:\pyMethod\segment-anything\lyg\1\REF切片\NDWI' + '\\' + os.path.basename(tif)
    #     geotiffwrite(ndvifile, ndvidata, info.geo_transform, info.projection, datatype='FLOAT32')
    #     geotiffwrite(ndwifile,ndwidata,info.geo_transform,info.projection,datatype='FLOAT32')
    #
    #     width, height = 4096, 4096
    #     rsfile = r'I:\pyMethod\segment-anything\lyg\1\REF切片\NDVI\RS'+'\\'+ os.path.basename(tif)
    #     resample_images(ndvifile,rsfile,width,height)
    #
    #     rsfile_2 = r'I:\pyMethod\segment-anything\lyg\1\REF切片\NDWI\RS'+'\\'+ os.path.basename(tif)
    #     resample_images(ndwifile,rsfile_2,width,height)

    # ndbidata = getNDBI(info.dataarray)
    # geotiffwrite(r'G:\pyMethod\指数\NDBI.tif',ndbidata,info.geo_transform,info.projection,datatype='FLOAT32')


    #
    # tiffile = r'S:\项目数据\江苏省养殖池塘\天地图影像地图_重投影\宜兴市.tif'
    # shpfile = r'S:\项目数据\江苏省养殖池塘\宜兴分块分割测试\宜兴市_4500_9000_范围.gpkg'
    # outfile = r'S:\项目数据\江苏省养殖池塘\宜兴分块分割测试\宜兴市_4500_9000.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)
    #
    # inputfilePath = r'I:\pyMethod\segment-anything\data\5120\yuce\water_tif\40水域.tif'
    # outputfilePath = r'I:\pyMethod\segment-anything\data\5120\yuce\water_tif\7.tif'
    # width =1024

    # height =1024
    # resample_images(inputfilePath, outputfilePath, width, height)

    # tiffile = r'I:\pyMethod\segment-anything\data\1024\geo_predict_1024.png'
    # shpfile = r'I:\pyMethod\segment-anything\data\1024\geo_predict_1024_1.shp'
    # createShpfile_from_geotiff(shpfile, tiffile)

    # # 赋予坐标信息
    # info = geotiffread(r'I:\pyMethod\segment-anything\data\1024_sample\test\202010GF4_test18.png')
    # data = geotiffread(r'I:\pyMethod\segment-anything\data\1024_sample\test\forset.png').dataarray
    # geotiffwrite(r'I:\pyMethod\segment-anything\data\1024_sample\test\geo_forset.png',data,info.geo_transform,info.projection)

    # width, height = 40482,73363
    # tif = r'G:\pyMethod\指数\NDBI.tif'
    # rsfile = r'G:\pyMethod\指数\NDBI_RS.tif'
    # resample_images(tif,rsfile,width,height)

    # # tifpath = r'G:\pyMethod\指数\NDVI.tif'
    # pixelnum = 20480
    # outpath = r'G:\pyMethod\指数\NDBI切片'
    # imgslice_by_pixels(rsfile, pixelnum, outpath, prefix="", suffix=".tif", datatype="FLOAT32")

    # tiffilelist = glob.glob(r'G:\pyMethod\指数\NDBI切片\*.tif')
    # for tif in tiffilelist:
    #     print(tif)
    #     rsfile = r'G:\pyMethod\指数\NDBI切片\重采样'+'\\'+ os.path.basename(tif)
    #     width, height = 4096,4096
    #     resample_images(tif,rsfile,width,height)

    # # sd平滑
    # # ref出sd
    # refpath = r'F:\20231029'
    # os.chdir(refpath)
    # import glob
    # reffiles = glob.glob("*.tif")
    # outpath = r'F:\20231029\宜兴_FUI'
    # for i,reffile in enumerate(reffiles):
    #     print(reffile)
    #
    #     # 反射率
    #     geotiff = geotiffread(reffile)
    #     refdata = geotiff.dataarray.astype(np.float)
    #     ndwi = getNDWI(refdata)
    #     refdata[ndwi < 0] = 0
    #     # 水色指数
    #     FUI, SD = derive_FUI(refdata)
    #     # SD = smoothdata(SD)
    #     # SD[np.isnan(SD)] = 0
    #     outfile = os.path.join(outpath, reffile[0:-4] + "_FUI.tif")
    #     geotiffwrite(outfile, FUI, geotiff.geo_transform, geotiff.projection)

    # # REF转RGB
    # refpath = r'G:\suxitongyuqnqu\ref'
    # rgbpath = r'G:\suxitongyuqnqu'
    # os.chdir(refpath)
    # reffiles = glob.glob("*.tif")
    # for reffile in reffiles:
    #     print(reffile)
    #     RGBfile = os.path.join(rgbpath,reffile)
    #     stretch_mode = "1%"
    #     ref2RGB(reffile, RGBfile, stretch_mode)

    # 矢量裁剪栅格
    # tiffile = r'I:\paddlex_data\rawData\landClassify_nanjing_20201020\img\caijian\GF4\RGB\GF_REF.tif'
    # shpfile = r'I:\pyMethod\segment-anything\data\big_tif\fanwei\范围.shp'
    # outfile = r'I:\pyMethod\segment-anything\data\big_tif\fanwei\REF.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)
    # #
    # tiffile = r'I:\paddlex_data\rawData\landClassify_nanjing_20201020\img\caijian\GF4\RGB\diwufenlei\tianditu\new\GF_RGB.tif'
    # shpfile = r'I:\pyMethod\segment-anything\data\big_tif\fanwei\范围.shp'
    # outfile = r'I:\pyMethod\segment-anything\data\big_tif\fanwei\RGB.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)

    # 矢量裁剪栅格
    # tiffile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\无锡市.tif'
    # shpfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪区域\宜兴市_buffered.shp'
    # outfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\按市县裁剪\宜兴市.tif'
    # # imgclip_with_shp(tiffile, shpfile, outfile)
    # dst_epsg = 32650
    # destfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪+投影\宜兴市.tif'
    # tiffileReproject(outfile, destfile, dst_epsg)


    # tiffile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\常州市.tif'
    # shpfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪区域\武进区_buffered.shp'
    # outfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\按市县裁剪\武进区.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)
    # dst_epsg = 32650
    # destfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪+投影\武进区.tif'
    # tiffileReproject(outfile, destfile, dst_epsg)
    #
    #
    # tiffile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\常州市.tif'
    # shpfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪区域\金坛市_buffered.shp'
    # outfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\按市县裁剪\金坛市.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)
    # dst_epsg = 32650
    # destfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪+投影\金坛市.tif'
    # tiffileReproject(outfile, destfile, dst_epsg)

    # tiffile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\常州市.tif'
    # shpfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪区域\溧阳市_buffered.shp'
    # outfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\按市县裁剪\溧阳市.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)
    # dst_epsg = 32650
    # destfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\原始数据\裁剪+投影\溧阳市.tif'
    # tiffileReproject(outfile, destfile, dst_epsg)






    # 投影
    # desfile = r'S:\BaiduNetdiskDownload\江苏省影像下载\武进区.tif'
    # dst_epsg = 32650
    # outfile = r'S:\项目数据\江苏省养殖池塘\天地图影像地图_重投影\武进区.tif'
    # tiffileReproject(desfile, outfile, dst_epsg)

    # # 重采样
    # referencefilePath= r'K:\wxyb\2014-2021\3\201484.tif'
    # inputfilePath = r'K:\wxyb\2014-2021\3\2021_COREG.tif'
    # outputfilePath = r'K:\wxyb\2014-2021\3\2021_COREG_RS.tif'
    # resample_images(referencefilePath, inputfilePath, outputfilePath)



    #傅里叶变化
    # data_path = r'K:\GF\2016_2020\yangben'
    # # test_path = r'D:\Desktop\test\1\B'
    # fft_save(data_path)
    # # fft_save(test_path)
    # geoinfo = geotiffread(r'H:\Tensorflow\image_RGB\lyg20221019GF6\GF6_PMS_E118.8_N35.0_20221019_L1A1120259483_moisc.tif')
    # data = geoinfo.dataarray
    # r = copy.deepcopy(data[:,:,2])
    # data[:,:,2] = copy.deepcopy(data[:,:,0])
    # data[:,:,0] = copy.deepcopy(r)
    # geotiffwrite(r'H:\Tensorflow\image_RGB\lyg20221019GF6\20221019_lygGF6_REF.tif',data,geoinfo.geo_transform,geoinfo.projection,datatype='FLOAT32')


    # reffile=r'H:\Tensorflow\image_RGB\lyg20221019GF6\20221019_lygGF6_REF.tif'
    # RGBfile=r'H:\Tensorflow\image_RGB\lyg20221019GF6\20221019_lygGF6_RGB.tif'
    # stretch_mode='2%'
    # ref2RGB(reffile, RGBfile, stretch_mode)




    # print(1)
    # tiffile = r'J:\项目文件\江苏省连云港市\12.12黑臭点位无人机正射\复堆河\复堆河拼接\3_dsm_ortho\2_mosaic\复堆河拼接_transparent_mosaic_group1.tif'
    # geotiffinfo = geotiffread(tiffile)
    # dataarray = geotiffinfo.dataarray
    # print(dataarray.shape)
    # rows,cols,dim = dataarray.shape
    # data_new = np.zeros((rows,cols,3))
    # data_new[:, :, 0] = dataarray[:, :, 0]
    # data_new[:, :, 1] = dataarray[:, :, 1]
    # data_new[:, :, 2] = dataarray[:, :, 2]
    # geotiffwrite(r'J:\项目文件\江苏省连云港市\12.12黑臭点位无人机正射\复堆河\复堆河拼接\3_dsm_ortho\2_mosaic\1.tif',data_new,geotiffinfo.geo_transform,geotiffinfo.projection)
