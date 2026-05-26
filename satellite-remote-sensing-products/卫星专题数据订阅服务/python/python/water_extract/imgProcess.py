'''
@Time    :   2021/04/06 18:20:19
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 基础图像处理
'''

import os
import shutil
import scipy.signal as signal
# from cv2 import DRAW_MATCHES_FLAGS_NOT_DRAW_SINGLE_POINTS, imshow
import numpy as np
import glob
import copy
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import matplotlib as mpl
import datetime as dt
# import scipy.signal as signal
from shapely import geometry, wkt
import geopandas as gpd  # 必须先导入geopandas再导入gdal!
from osgeo import gdal, gdalconst, osr,ogr

# import geomProcess as geompro


def imgShow(imgname,img):
    '''
    功能：图像显示
    imgname: 图像显示窗口名称
    img:待显示图像
    '''
    cv2.imshow(imgname,img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

##############################
##########栅格读写#############
##############################
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
    proj = raster_dataset.GetProjection()
    srs = osr.SpatialReference(proj) # 获取投影坐标系
    epsg = srs.GetAttrValue('AUTHORITY',1)   # 获取投影坐标系epsg编号
    dataarray=[]
    for i in range(1,raster_dataset.RasterCount+1):
        band=raster_dataset.GetRasterBand(i)    # 波段从1计数
        dataarray.append(band.ReadAsArray())
    
    dataarray=np.dstack(dataarray)  
    rows,cols,bands=dataarray.shape
    if bands == 1:
        dataarray = dataarray[:,:,0]
    del raster_dataset,band
    geotiff=geotiffinfo(rows,cols,bands,geo_transform,proj,dataarray,epsg)
    return geotiff

# 按像元大小读栅格文件
def geotiffreadByPixels(tiffile, xoff=0, yoff=0, xsize=None, ysize=None):
    """按照像元数读取栅格文
    tiffile：栅格文件路径
    xoff：行起始像元
    yoff：列起始像元
    xsize：图像的行大小，从起始像元数开始计算
    ysize：图像的列大小，从起始像元数开始计算
    """
    raster_dataset = gdal.Open(tiffile, gdal.GA_ReadOnly)
    geo_transform = raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()
    srs = osr.SpatialReference(proj)  # 获取投影坐标系
    epsg = srs.GetAttrValue('AUTHORITY', 1)  # 获取投影坐标系epsg编号
    dataarray = []
    for i in range(1, raster_dataset.RasterCount + 1):
        band = raster_dataset.GetRasterBand(i)  # 波段从1计数
        dataarray.append(band.ReadAsArray(xoff, yoff, xsize, ysize))

    dataarray = np.dstack(dataarray)
    rows, cols, bands = dataarray.shape
    if bands == 1:
        dataarray = dataarray[:, :, 0]
    del raster_dataset, band
    geotiff = geotiffinfo(rows, cols, bands, geo_transform, proj, dataarray, epsg)
    return geotiff

# 获取栅格文件坐标系信息
def getSRSPair(tiffile):
    dataset = gdal.Open(tiffile)
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(dataset.GetProjection())
    geosrs = prosrs.CloneGeogCS()
    return prosrs,geosrs

# 获取栅格图像范围
def getGeotiffRange(geotiff):
    # geotiff = imgpro.geotiffread(tiffile)
    rows = geotiff.rows
    cols = geotiff.cols
    geotrans = geotiff.geo_transform
    l = geotrans[0]
    r = l + cols * geotrans[1]
    t= geotrans[3]
    b = t + rows * geotrans[5]
    range_list = [[l,t],[r,t],[r,b],[l,b],[l,t]]
    range_wkt = "POLYGON (("
    for i in range_list:
        range_wkt = range_wkt + str(i[0]) + " " + str(i[1]) + ","
    range_wkt = range_wkt[0:-1] + "))"
    range_df = pd.DataFrame([range_wkt],columns=['geom'])
    range_df['geom'] = range_df['geom'].apply(wkt.loads)
    range_gdf = gpd.GeoDataFrame(range_df,crs="EPSG:"+str(geotiff.epsg),geometry='geom')
    return range_gdf

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
        dataset.GetRasterBand(1).WriteArray(data)
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
获取新的仿射变换参数（用于裁剪过程）
'''
def get_newtrans(transform, min_x, max_x, min_y, max_y):
    # min_x, max_x, min_y, max_y --> 左经度，右经度，下纬度，上纬度
    # Getting georeference info
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]
    # Computing Point1(i1,j1), Point2(i2,j2)
    i1 = int((min_x - xOrigin) / pixelWidth)
    j1 = int((yOrigin - max_y) / pixelHeight)
    i2 = int((max_x - xOrigin) / pixelWidth)
    j2 = int((yOrigin - min_y) / pixelHeight)
    new_xsize = i2 - i1 + 1
    new_ysize = j2 - j1 + 1
    # New upper-left X,Y values
    new_x = xOrigin + i1 * pixelWidth
    new_y = yOrigin - j1 * pixelHeight
    new_transform = (
        new_x, transform[1], transform[2], new_y, transform[4], transform[5])
    return new_transform, new_xsize, new_ysize, i1, i2, j1, j2



##############################
##########投影转换#############
##############################
'''栅格投影'''
def tiffileReproject(reffile,srcfile,outfile):
    ref_raster = gdal.Open(reffile,gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    # geo_transform=ref_raster.GetGeoTransform()
    # xRes = geo_transform[1]
    # yRes = geo_transform[5]
    geotiff = geotiffread(reffile)
    rows = geotiff.rows
    cols = geotiff.cols
    src_raster = gdal.Open(srcfile)
    src_proj = src_raster.GetProjection()
    # options = gdal.WarpOptions(srcSRS=src_proj,dstSRS=ref_proj,xRes=xRes,yRes=yRes,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    options = gdal.WarpOptions(srcSRS=src_proj,dstSRS=ref_proj,width=cols,height=rows,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    gdal.Warp(outfile,srcfile,options=options)

def tiffileReproject(srcfile,desfile,dst_epsg):
    '''
    功能：栅格投影
    srcfile: str 输入文件
    desfile: str 输出文件
    dst_epsg: int 目标坐标系对应的EPSG编号
    '''
    geotiff = geotiffread(srcfile)
    new_projection = osr.SpatialReference()
    new_projection.ImportFromEPSG(dst_epsg)

    new_projection = new_projection.ExportToWkt()
    gdal.Warp(desfile,srcfile,srcSRS=geotiff.projection,dstSRS =new_projection)

##############################
##########栅格裁剪、拼接#############
##############################
'''
图像镶嵌1：对一个文件夹下所有tif进行镶嵌
'''
def rasterMosaic(tifpath,outfile):
    tiffiles = glob.glob(tifpath+"\\*.tif")
    ref_raster = gdal.Open(tiffiles[0],gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    options = gdal.WarpOptions(srcSRS=ref_proj,dstSRS=ref_proj,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    gdal.Warp(outfile,tiffiles,options=options)

'''
图像镶嵌2：对2个不同文件夹下同名tif进行镶嵌
'''
def rasterMosaic_byTIF(tifpathes,outpath):
    os.chdir(tifpathes[0])
    tiffiles = glob.glob("*.tif")
    for tiffile in tiffiles:
        file_list = []
        for tifpath in tifpathes:
            filename = os.path.join(tifpath,tiffile)
            file_list.append(filename)

        outfile = os.path.join(outpath,tiffile)
        ref_raster = gdal.Open(tiffile,gdal.GA_ReadOnly)
        ref_proj = ref_raster.GetProjection() 
        options = gdal.WarpOptions(srcSRS=ref_proj,dstSRS=ref_proj,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
        gdal.Warp(outfile,file_list,options=options)

'''
创建缓冲区，用于按矢量裁剪栅格模块
矢量文件复杂、直接裁剪结果为空时，可先以0为缓冲距离创建新的矢量
'''
def createBuffer(inputfn, outputBufferfn, bufferDist,fieldName,fieldType):
    # 支持中文路径
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8","NO")
    # 使属性表字段支持中文
    gdal.SetConfigOption("SHAPE_ENCODING","CP936")

    inputds = ogr.Open(inputfn)
    inputlyr = inputds.GetLayer()
    spatialRef=inputlyr.GetSpatialRef() # 获取输入空间参考

    # 定义输出矢量
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

'''按矢量裁剪栅格'''
def imgclip_with_shp(tiffile,shpfile,outfile,dstNodata=0):    
    if tiffile.endswith(".tif"):
        # tiffile为某个tif文件
        gdal.Warp(outfile,tiffile,cutlineDSName = shpfile,cropToCutline = False,dstNodata = dstNodata)
    else:
        # tiffile为存放多个待裁剪栅格的路径
        os.chdir(tiffile)
        tiffiles = glob.glob("*55.tif")
        for f in tiffiles:
            tif = tiffile + "\\" + f
            # 矢量文件复杂、直接裁剪结果为空时，可先以0为缓冲距离创建新的矢量
            shp_buf = shpfile.replace(".shp","_buffer.shp")
            print(shp_buf)
            createBuffer(shpfile, shp_buf, 0.0,'gridcode',ogr.OFTInteger)
            out = outfile + "\\" + f
            print(out)
            if dstNodata == None:
                gdal.Warp(out,tif,cutlineDSName = shp_buf,cropToCutline = True) 
            else:
                gdal.Warp(out,tif,cutlineDSName = shp_buf,cropToCutline = True,dstNodata = 0) 


'''
按像元数切片
tifdata：geotiffinfo对象
pixelnum：像元数
outpath：切片存放路径
prefix：切片文件名-前缀
suffix：切片文件名-后缀
datatype：数据存储类型
'''
def imgslice_by_pixels(tifdata,pixelnum,outpath,prefix = "subset_sentinel2_",suffix = ".tif",datatype = "FLOAT32",*buf_dist):
    # 统计切片数量
    xnum = int(tifdata.cols / pixelnum) # 横向满足pixelnum的分块数量，向下取整
    ynum = int(tifdata.rows / pixelnum) # 纵向满足pixelnum的分块数量，向下取整

    # 切片
    data = tifdata.dataarray
    geo_transform = tifdata.geo_transform
    subset_id = 0 
    print(xnum,ynum)
    # 待切片矩阵大小 < pixcelnum*pixcelnum
    if ynum == 0 and xnum == 0:
        subset_id = subset_id + 1      
        subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
        geotiffwrite(subsetfilename,data,geo_transform,tifdata.projection,datatype)
    # 待切片矩阵行数 < pixcelnum
    elif ynum == 0 and xnum > 0:
        startrow = 0
        endrow = tifdata.rows
        # 遍历列，切片
        for j in range(xnum):
            startcol = j * pixelnum
            endcol = startcol + pixelnum
            if len(buf_dist)>0:
                startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
            subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
            if not none_tag:
                subset_id = subset_id + 1
                subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)
        if endcol < tifdata.cols-1:
            startcol = xnum * pixelnum
            endcol = tifdata.cols
            if len(buf_dist)>0:
                startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
            subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
            if not none_tag:
                subset_id = subset_id + 1
                subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)
    # 待切片矩阵列数 < pixcelnum
    elif ynum > 0 and xnum == 0:
        startcol = 0
        endcol = tifdata.cols
        # 遍历行，切片
        for i in range(ynum):
            startrow = i * pixelnum
            endrow = startrow + pixelnum
            if len(buf_dist)>0:
                startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
            subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
            if not none_tag:
                subset_id = subset_id + 1
                subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)
        if endrow < tifdata.rows-1:
            startrow = ynum * pixelnum
            endrow = tifdata.rows
            if len(buf_dist)>0:
                startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
            subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
            if not none_tag:
                subset_id = subset_id + 1
                subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)
    # 待切片矩阵大小 > pixcelnum*pixcelnum
    elif ynum > 0 and xnum > 0:
        for i in range(ynum):       #纵轴
            startrow = i * pixelnum
            endrow = startrow + pixelnum
            for j in range(xnum):   #横轴         
                startcol = j * pixelnum
                endcol = startcol + pixelnum
                if len(buf_dist)>0:
                    startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
                subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
                print("getImgtile success")
                if not none_tag:
                    subset_id = subset_id + 1
                    subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                    geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)
            if endcol < tifdata.cols-1:
                startcol = xnum * pixelnum
                endcol = tifdata.cols
                if len(buf_dist)>0:
                    startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
                subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
                if not none_tag:
                    subset_id = subset_id + 1
                    subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                    geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)
        if endrow < tifdata.rows-1:
            startrow = ynum * pixelnum
            endrow = tifdata.rows
            for j in range(xnum):
                startcol = j * pixelnum
                endcol = startcol + pixelnum
                if len(buf_dist)>0:
                    startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
                subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
                if not none_tag:
                    subset_id = subset_id + 1
                    subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                    geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)
            if endcol < tifdata.cols-1:
                startcol = xnum * pixelnum
                endcol = tifdata.cols
                if len(buf_dist)>0:
                    startrow,endrow,startcol,endcol = getBufRange(tifdata.rows,tifdata.cols,startrow,endrow,startcol,endcol,buf_dist[0]) 
                subset_tif,none_tag = getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol)
                if not none_tag:
                    subset_id = subset_id + 1
                    subsetfilename = getTileName(outpath,prefix,subset_id,suffix)
                    geotiffwrite(subsetfilename,subset_tif.dataarray,subset_tif.geo_transform,tifdata.projection,datatype)            

# 按设定缓冲距更新矩阵切片索引
def getBufRange(rows,cols,startrow,endrow,startcol,endcol,buf_dist):
    if startrow >= buf_dist:
        startrow = startrow - buf_dist
    if endrow < rows-buf_dist:
        endrow = endrow + buf_dist
    if startcol >= buf_dist:
        startcol = startcol - buf_dist
    if endcol < cols-buf_dist:
        endcol = endcol + buf_dist
    return startrow,endrow,startcol,endcol

# 按设定索引进行矩阵切片,tifdata为geotiff对象，返回切片后的新geotiff对象
def getImgtileByIndex(tifdata,startrow,endrow,startcol,endcol):
    # 矩阵切片
    data = tifdata.dataarray
    tile_data = data[startrow:endrow,startcol:endcol,:]  
    print(tile_data.shape)
    print(startrow,endrow,startcol,endcol)

    # 判断切片是否均为无效值
    if np.nanmax(np.nanmax(np.nanmax(tile_data))) == 0 or np.nanmin(np.nanmin(np.nanmin(tile_data))) == 255:
        none_tag = True
    else:
        none_tag = False

    # 更新坐标参数
    geo_transform = tifdata.geo_transform
    leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
    leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
    tile_geotrans = (leftup_x,geo_transform[1],geo_transform[2],leftup_y,geo_transform[4],geo_transform[5])

    # 生成geotiff对象
    tile = geotiffinfo(endrow-startrow,endcol-startcol,tifdata.bands,tile_geotrans,tifdata.projection,tile_data,tifdata.epsg)
    
    return tile,none_tag

# 按设定前、后缀名及切片号返回切片文件名
def getTileName(outpath,prefix,subset_id,suffix):
    filename = prefix + str(subset_id) + suffix       #裁剪图像保存格式为png
    filename = os.path.join(outpath,filename)
    return filename
    
'''
按行列数切片
tifdata：geotiffinfo对象
rownum,colnum：行列数
outpath：切片存放路径
prefix：切片文件名-前缀
suffix：切片文件名-后缀
datatype：数据存储类型
'''
def imgslice_by_rowcol(tifdata,rownum,colnum,outpath,prefix="subset_GF2_",suffix=".tif",datatype="FLOAT32"):
    imgwidth = int(tifdata.cols / rownum)    #向下取整
    imgheight = int(tifdata.rows / rownum)
    # if tifdata.bands==1:
    #     data = tifdata.dataarray.reshape((tifdata.rows,tifdata.cols,1))
    # else:
    #     data = tifdata.dataarray
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
                # if tifdata.bands==1:
                #     subset=np.resize(subset,(subset.shape[0],subset.shape[1]))
                # else:
                #     pass
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

'''求两图像交集'''
def getIntersectTIFRange(tiffile1,tiffile2,outpath):
    geotif1 = geotiffread(tiffile1)
    geotif2 = geotiffread(tiffile2)
    range1 = getGeotiffRange(geotif1)
    range2 = getGeotiffRange(geotif2)
    range2 = range2.to_crs(range1.crs)
    srs = geotif1.srs
    intersect = gpd.overlay(range1,range2,how="intersection")
    intersect_file = os.path.join(outpath,"intersect_range.shp")
    intersect.to_file(intersect_file)
    new_file1 = os.path.join(outpath,os.path.basename(tiffile1).replace(".tif","_cliped.tif"))
    new_file2 = os.path.join(outpath,os.path.basename(tiffile2).replace(".tif","_cliped.tif"))
    gdal.Warp(new_file1,tiffile1,cutlineDSName=intersect_file,cropToCutline=True,dstSRS=srs,width=geotif1.rows,height=geotif1.cols)
    gdal.Warp(new_file2,tiffile2,cutlineDSName=intersect_file,cropToCutline=True,dstSRS=srs,width=geotif1.rows,height=geotif1.cols)
    return new_file1,new_file2



##############################
##########栅格矢量转换#############
##############################
'''矢量转栅格'''
def shp2geotiff(shpfile,rows,cols,geo_transform,projection,field=None,fieldType="UINT8"): 
    data_source = gdal.OpenEx(shpfile,gdal.OF_VECTOR)
    tiffile = shpfile.replace(".shp",".tif")  
    layer=data_source.GetLayer(0)
    driver=gdal.GetDriverByName("GTiff")    #"MEM"
    if fieldType == "UINT8":
        target_ds=driver.Create(tiffile,cols,rows,1,gdal.GDT_Byte)
    elif fieldType == "UINT16":
        target_ds = driver.Create(tiffile,cols,rows,1,gdal.GDT_UInt16)
    target_ds.SetGeoTransform(geo_transform)
    target_ds.SetProjection(projection)
    if field is None:
        gdal.RasterizeLayer(target_ds,[1],layer,None)
    else:
        OPTIONS=['ATTRIBUTE='+field]
        gdal.RasterizeLayer(target_ds,[1],layer,options=OPTIONS)

    band=target_ds.GetRasterBand(1)
    return band.ReadAsArray()

'''栅格转矢量'''
def createShpfile_from_tiffile(shpfile,tiffile,fieldName="MASK"):
    geotiff = geotiffread(tiffile)
    data = geotiff.dataarray
    data_dim = len(data.shape)
    if data_dim == 3:
        data = data[:,:,0]    
    # data[data>0] = 1
    # data[data<=0] = 0
    driver = gdal.GetDriverByName('MEM')
    raster = driver.Create('',geotiff.cols, geotiff.rows, 1, gdal.GDT_Byte)
    raster.SetGeoTransform(geotiff.geo_transform)
    raster.SetProjection(geotiff.projection)
    raster.GetRasterBand(1).WriteArray(data)
    band = raster.GetRasterBand(1)
    
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(shpfile)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(geotiff.projection)
    layer = data_source.CreateLayer(shpfile,srs)
    # 添加属性列
    newField = ogr.FieldDefn(fieldName, ogr.OFTInteger)
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

'''栅格转矢量'''
def createShpfile_from_geotiff(shpfile,dataarray,geotransform,projection,fieldName,fieldType):
    rows,cols = dataarray.shape
    driver = gdal.GetDriverByName('MEM')
    # raster = driver.Create('',cols, rows, 1, gdal.GDT_Byte)
    raster = driver.Create('',cols,rows,1,gdal.GDT_UInt32)
    raster.SetGeoTransform(geotransform)
    raster.SetProjection(projection)
    raster.GetRasterBand(1).WriteArray(dataarray)
    band = raster.GetRasterBand(1)
    
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(shpfile)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(projection)
    layer = data_source.CreateLayer(shpfile,srs)
    # 添加属性列
    if fieldType == "INT":
        newField = ogr.FieldDefn(fieldName, ogr.OFTInteger)
    elif fieldType == "UINT16":
        newField = ogr.FieldDefn(fieldName,ogr.OFSTInt16)
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
    band=None

'''提取图像边界线'''
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



##############################
##########图形态运算#############
##############################
''' 图像平滑'''
def smoothdata(dataarray,method):
    if method == "median":   
        newdata = signal.medfilt(dataarray,5)   #中值滤波
    return newdata

''' 图像平滑'''
def imgSmoothing(dataarray,method,kernel_size):
    half_width = int((kernel_size - 1) / 2)
    shape = dataarray.shape
    row = shape[0]
    col = shape[1]
    smth_data = np.zeros([row,col])
    # 中值滤波
    if method == "mode":
        for i in range(half_width,row-half_width+1):
            for j in range(half_width,col-half_width+1):
                tmp_window = dataarray[i-half_width:i+half_width+1,j-half_width:j+half_width+1]
                tmp_window = list(tmp_window.flatten())
                counts = np.bincount(tmp_window)
                smth_data[i,j] = np.argmax(counts)
                smth_data[0:half_width,j] = smth_data[half_width,j]
                smth_data[-half_width:,j] = smth_data[-half_width,j]
        for i in range(half_width):
            smth_data[i,:] = smth_data[half_width,:]
            smth_data[row-i-1,:] = smth_data[row-half_width-1,:]
    return smth_data

'''图像锐化'''
def sharpening(img):
    kernerl = np.array([[0,-1,0],
                        [-1,5,-1],
                        [0,-1,0]])
    img_sharpen = cv2.filter2D(src=img,ddepth=-1,kernel=kernerl)
    return img_sharpen 

'''图像闭运算：先膨胀再腐蚀'''
def closeOperation(img,kernelsize):
    kernel = np.ones((kernelsize, kernelsize), np.uint8)
    closed = cv2.morphologyEx(img,cv2.MORPH_CLOSE,kernel)
    return closed

''' 图像开运算：先腐蚀再膨胀'''
def openOperation(img,kernelsize):
    kernel = np.ones((kernelsize, kernelsize), np.uint8)
    opened = cv2.morphologyEx(img,cv2.MORPH_OPEN,kernel)
    return opened

''' 边缘检测'''
def extractEdges(data):
    # data = cv2.imread(imgfile,-1)
    im_gaussian=cv2.GaussianBlur(data,(3,3),0,0)
    im_gaussian=np.uint8(im_gaussian*255/np.max(im_gaussian))
    canny=cv2.Canny(im_gaussian,10,150)
    return canny

'''斑块联通'''
def baweraopen(image,size):
    '''
    @image:单通道二值图，数据类型uint8
    @size:欲去除区域大小(黑底上的白区域)
    '''
    nlabels, labels, stats, centroids = cv2.connectedComponentsWithStats(image)
    mask=np.zeros_like(image)
    areas=[s[4] for s in stats]
    sorted_idx=np.argsort(areas) # 面积从小到大的序号

    for lidx,area in zip(sorted_idx,[areas[s] for s in sorted_idx[:-1]]):
        if area>size:
            mask[labels==lidx]=1
    # print(np.max(mask),np.sum(mask==np.max(mask)))
    # mask[labels==0]=0
    return mask

def riverExpand(data,distance):
    '''
    功能：河流扩宽，增强显示效果.
    思路：data的掩膜膨胀，膨胀后原data区域不变，新扩张区域插值
    data: np.dataarray 河流的栅格矩阵
    distance: int 扩展距离
    返回：
    data_expand: np.dataarray 扩宽后的栅格矩阵
    '''
    data[np.isnan(data)] = 0

    kernel = np.ones((distance,distance),np.uint8)
    mask = np.zeros_like(data)
    mask[data>0] = 1
    mask = cv2.dilate(mask,kernel)
    data[np.logical_and(mask==1, data==0)] = np.nan
    array = np.ma.masked_invalid(data)

    x = np.arange(0,array.shape[1])
    y = np.arange(0,array.shape[0])

    xx,yy = np.meshgrid(x,y)

    x1 = xx[~array.mask]
    y1 = yy[~array.mask]
    newarr = array[~array.mask].data

    data_expand = interpolate.griddata((x1,y1),newarr.ravel(),(xx,yy),method='nearest')

    return data_expand

# def getHog(img):
#     des,hog_img = hog(img,orientations=8,pixels_per_cell=(4,4),cells_per_block=(4,4),block_norm='L2',visualize=True,feature_vector=False)

def countHogHist(img_gray,cell_size=3,block_size=4):
    cell = 3
    block = 4
    img_Norientation = np.zeros(img_gray.shape)

    i, j = 0, 0
    while i + cell*block < np.shape(img_gray)[0] :
        while j + cell*block < np.shape(img_gray)[1]:               
            img_block = img_gray[i:i+cell*block, j:j+cell*block]
            ft_block, hog_image = hog(img_block, orientations=8, pixels_per_cell=(3, 3), cells_per_block=(4, 4), block_norm= 'L2',visualize=True, feature_vector = False)
            orientation_block = np.sum(ft_block.reshape((-1,8)), axis = 0)
            orientation_list = list(np.where(orientation_block==np.max(orientation_block)))
            if len(orientation_list):
                Norientation = np.max(orientation_list)
            else:
                Norientation = -1
            img_Norientation[i:i+cell*block, j:j+cell*block] = Norientation
            
            j = j + cell*block
        i = i + cell*block
        j = 0
    return img_Norientation

def getLBP(refdata,n_points=160,radius=8,METHOD='uniform'):
    '''
    radius 半径
    n_points 对应输出矩阵的最大值
    '''
    rgb = ref2RGB(refdata,"2%")
    img_gray = cv2.cvtColor(rgb.astype(np.float32), cv2.COLOR_RGB2GRAY)
    img_gray = normalize(img_gray)
    lbp = local_binary_pattern(img_gray, n_points, radius, METHOD)
    return lbp

'''栅格图斑提取为矢量'''
def findContours(img_gray,geotrans,epsg): 
    cnt_df = pd.DataFrame([],columns=['ID','length','area','C','edgeNum','geometry'])

    label_max = np.nanmax(img_gray)
    for i in range(1,label_max+1):
        t = img_gray.copy()
        t[t!=i] = 0
        cnt, hierarchy = cv2.findContours(t, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = cnt[0]
        cnt_len = cv2.arcLength(cnt, True) #计算轮廓周长
        cnt = cv2.approxPolyDP(cnt, 0.01*cnt_len, True) #多边形逼近
        
        cnt_num = len(cnt)  # 多边形边数
        if cnt_num>2:        
            cnt_area = cv2.contourArea(cnt)  #多边形面积
            cnt_C = cnt_len / cnt_area  

            cnt_df.loc[i,'geometry'] = cnt2wkt(cnt,geotrans)                         
            cnt_df.loc[i,'edgeNum'] = cnt_num
            cnt_df.loc[i,'length'] = cnt_len            
            cnt_df.loc[i,'area'] = cnt_area
            cnt_df.loc[i,'C'] = cnt_C
        # a = cnt_df.copy()
        # a['geometry'] = a['geometry'].apply(wkt.loads)
    cnt_df['geometry'] = cnt_df['geometry'].apply(wkt.loads)
    cnt_df['ID'] = cnt_df.index.values + 1
    cnt_df = gpd.GeoDataFrame(cnt_df,crs="EPSG:"+str(epsg),geometry='geometry')
    
    return cnt_df      

'''图像坐标转wkt格式地理坐标'''
def cnt2wkt(cnt,geotrans):
    wkt_str = ''
    for xy in list(cnt):
        lon = geotrans[0] + xy[0][0] * geotrans[1]
        lat = geotrans[3] + xy[0][1] * geotrans[5]
        wkt_str = wkt_str + str(lon) + ' ' + str(lat) + ','
    wkt_str = 'POLYGON((' + wkt_str + wkt_str.split(',')[0] + '))'
    return wkt_str

'''图像缩放'''
def scaleImage(img,scale_factor):
    ratio = (scale_factor * img.shape[1]) / img.shape[1]
    dim = (int(scale_factor * img.shape[1]),int(img.shape[0] * ratio))

    resized = cv2.resize(img,dim,interpolation=cv2.INTER_AREA)

    return resized

'''图像翻转'''
def flipImage(img,flip_type):    
    flipped = cv2.flip(img,flip_type)    
    return flipped

'''图像旋转'''
def rotateImage(img,angle):
    (h,w) = img.shape[:2]
    center = (np.floor(w/2),np.floor(h/2))

    M = cv2.getRotationMatrix2D(center,angle,1.0)
    rotated = cv2.warpAffine(img,M,(w,h))

    return rotated

'''图像加高斯噪声'''
def saltPepperNoiseImage(img,s_vs_p,amount):
    row,col,ch = img.shape
    out = np.copy(img)
    # salt mode
    num_salt = np.ceil(amount * img.size * s_vs_p)
    coords = [np.random.randint(0,i-1,int(num_salt)) for i in img.shape]
    out[coords] = 1

    # pepper mode
    num_pepper = np.ceil(amount * img.size * (1. - s_vs_p))
    coords = [np.random.randint(0,i-1,int(num_pepper)) for i in img.shape]
    out[coords] = 0

    return out

'''图像分割'''
def imgSegByKmeans(data,geotrans,proj):
    # 图像增强
    img_seg = clahe(data)
    # img_seg = data

    # 图像分割
    # step1: cluster
    if len(data.shape) == 2:
        img_dim = 1
    else:
        img_dim = data.shape[2]
    pixel_vals = img_seg.reshape((-1,img_dim))
    pixel_vals = np.float32(pixel_vals)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.85)
    k = 6
    retval, labels, centers = cv2.kmeans(pixel_vals, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    segmented_image = labels.reshape((img_seg.shape[0], img_seg.shape[1]))
    # geotiffwrite(outfile,segmented_image,geo_transform,projection,datatype="UINT16") 

    # connect and label
    mask_filtered = np.zeros((img_seg.shape[0], img_seg.shape[1]))
    for i in range(k):        
        mask = segmented_image == i
        mask = mask.astype('int8')
        num_labels, label_img, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=4)
        t = label_img + (np.nanmax(mask_filtered)+1) * mask
        mask_filtered = mask_filtered + t
    print("总联通图斑数",np.max(mask_filtered))
    createShpfile_from_geotiff('temp.shp',mask_filtered,geotrans,proj,fieldName='ID',fieldType="UINT16")
    
    # select by area
    geompro.addAreaField('temp.shp')
    conneted_labels = gpd.read_file('temp.shp')
    idx = conneted_labels.loc[:,'SHP_AREA'] > 0.004
    conneted_labels = conneted_labels[idx]
    conneted_labels.to_file('temp_filtered.shp', encoding="utf-8")
    conneted_labels = shp2geotiff('temp_filtered.shp',data.shape[0],data.shape[1],geotrans,proj,field='ID',fieldType="UINT16")

    os.remove('temp.shp')
    os.remove('temp_filtered.shp')

    return segmented_image,conneted_labels

##############################
##########彩色增强#############
##############################
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
    return int(st_value),int(ed_value)

# 反射率（16位4波段）转RGB（8位3波段）,2% | 5%线性拉伸(stretch_mode = "2%" |stretch_mode =  "5%")
def ref2RGB(reffile,stretch_mode,RGBfile=False):
    geotiff = geotiffread(reffile)
    data = geotiff.dataarray
    data = data[:,:,0:3]    
    for i in range(3):
        t = data[:,:,i].copy()
        t_st,t_ed = getBreakpointsByLinear(t,mode=stretch_mode)
        t[t<t_st] = t_st
        t[t>t_ed] = t_ed
        t = (t-t_st) / (t_ed-t_st) * 254 + 1    # 有效值的映射范围 [1,255]
        t[data[:,:,i]==0] = 0   # 背景值设0
        data[:,:,i] = t.copy()
    r = copy.deepcopy(data[:,:,2])
    data[:,:,2] = copy.deepcopy(data[:,:,0])
    data[:,:,0] = copy.deepcopy(r)
    if RGBfile:
        geotiffwrite(RGBfile,data,geotiff.geo_transform,geotiff.projection,datatype="UINT8")
    
# 按累计概率百分数获取断点
def getBreakPointByPct(data,percentage):
    data = data[data>0]
    minvalue = np.nanmin(data)
    maxvalue = np.nanmax(data)
    bins = np.linspace(minvalue,maxvalue,101)   # 101个结点，分100个区间
    cml_frequence,_,_ = plt.hist(data,bins,histtype='bar',cumulative=True)
    total_num = len(data)
    y = cml_frequence / total_num
    t = np.abs(y-percentage)
    bk_index = np.where(t==np.nanmin(t))[0][0]
    bk_value = bins[bk_index]
    return bk_value

# 空洞填充（有效图像范围内0值转1值）
def fillImgHoles(data,kernelsize=5):
    mask = data[:,:,0].copy()
    
    mask[mask>0] = 1
    mask = closeOperation(mask,kernelsize)

    data[np.logical_and(mask==1,data[:,:,0]==0)] = 1

    return data

            
'''
限制对比度自适应直方图均衡
:param img: 待测图像
:param tileGridSize: 划分小区域的大小一般为8
:return: 返回的是直方图均衡化后的图像
'''
def clahe(img_in,tileGridSize=8):    
    img = img_in.copy().astype(np.float32)

    img = (img-np.nanmin(img))/(np.nanmax(img)-np.nanmin(img))*255
    img = np.array(img,dtype='uint8')
    clahe = cv2.createCLAHE(clipLimit=2.0,tileGridSize=(tileGridSize,tileGridSize)) #先设置区域块tile的大小以及裁剪的限制
    if len(img.shape) == 2:
        cll = clahe.apply(img)  #对图片进行自适应均衡化
    else:
        cll = np.zeros_like(img)
        for i in range(img.shape[2]):
            cll[:,:,i] = clahe.apply(img[:,:,i])
    return cll


##############################
##########遥感指数和归一化#############
##############################
def getNDWI(refdata):
    refdata = refdata.astype(np.float)
    nir = refdata[:,:,3]
    g = refdata[:,:,1]
    ndwi = (g-nir)/(g+nir)
    return ndwi

def getNDVI(refdata):
    refdata = refdata.astype(np.float32)
    r = refdata[:,:,2]
    nir = refdata[:,:,3]
    ndvi = (nir-r)/(nir+r)
    return ndvi

def normalize(array,level=1,method='extreme'):
    array_min, array_max = np.nanmin(array), np.nanmax(array)

    if method == 'extreme':
        nor_data = ((array - array_min)/(array_max - array_min))

    nor_data = nor_data * level

    return nor_data

def getStdMeanImage(data,windowsize=10):
    std_img = np.zeros_like(data)
    mean_img = np.zeros_like(data)

    for i in range(int(windowsize/2), np.shape(data)[0]):
        for j in range(int(windowsize/2), np.shape(data)[1]):
            wmax = i + windowsize
            hmax = j + windowsize
            if wmax > np.shape(data)[0]:
                wmax = np.shape(data)[0]
            if hmax > np.shape(data)[1]:
                hmax = np.shape(data)[1]
            img_block = data[i:wmax, j:hmax]
            std_img[i:wmax, j:hmax] = np.std(img_block)
            mean_img[i:wmax, j:hmax] = np.mean(img_block)
    stdmean = np.dstack((normalize(mean_img), normalize(std_img)))
    return stdmean

def geom2pixel(geotrans,lon,lat):
    '''
    功能: 投影坐标转像素坐标
    geotrans: geotiff.geo_transform 坐标转换6参数
    lon：float 经度
    lat: float 纬度
    返回：
    x: int 列坐标
    y: int 行坐标
    '''
    x = int((lon - geotrans[0]) / geotrans[1])
    y = int((lat - geotrans[3]) / geotrans[5])

    return x,y

def raster2Points(geotiff,points):
    '''
    功能：栅格提取至点
    geotiff: geotiff对象
    points: gpd.GeoDataFrame对象
    返回：
    points: 在原points基础上增加栅格提取值
    '''
    points=points.set_crs(epsg="4326", inplace=True)
    # points = points.to_crs(crs='EPSG:'+str(geotiff.epsg))

    data = geotiff.dataarray
    for i in points.index:
        lon = points.loc[i,'geometry'].x
        lat = points.loc[i,'geometry'].y
        x,y = geom2pixel(geotiff.geo_transform,lon,lat)
        if len(data.shape)==2:
            points.loc[i, 'data' ] = data[y, x]
        else:
            for j in range(geotiff.bands):
                points.loc[i,'B'+str(j+1)] = data[y,x,j]
    return points

##ref上增加标签band
def getFilename(file_dir):
    File_Id=[]
    File_Name = []
    for files in os.listdir(file_dir):
        file_num=files.split('_')[0].split('.')[0]
        File_Id.append(file_num)
        File_Name.append(files)
    return File_Id,File_Name

def geotiffUnify(outfile, srcfile, referencefile, datatype):
    geotiff_tpl = geotiffread(referencefile)
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
    srs_geotiff = geotiffread(outfile)
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
    if len(mask.shape) == 3:
        dst_array[mask[:, :, 0] == 0] = 0
    else:
        dst_array[mask == 0] = 0

    geotiffwrite(outfile, dst_array, dst_geotrans, dst_proj, datatype)

def Resample(tiffile,plus):
    '''
    功能：对栅格进行重采样，改变栅格的大小
    plus:表示原图放大的倍数
    '''
    img=geotiffread(tiffile)
    data=img.dataarray
    geo_transform=img.geo_transform
    epsg = img.epsg
    projection=img.projection
    dataarray=cv2.resize(data,dsize=None,fx=plus,fy=plus,interpolation=cv2.INTER_LINEAR)
    # dataarray=dataarray.reshape(dataarray.shape[0], dataarray.shape[1], 1)
    geo_transform_list = list(geo_transform)
    geo_transform_list[1]=geo_transform_list[1]/plus
    geo_transform_list[5]=geo_transform_list[5]/plus
    geo_transform=tuple(geo_transform_list)
    # imgpro.geotiffwrite(outfile,data,geo_transform_new,projection,datatype="UINT8")
    if len(dataarray.shape) <=2:
        bands=[]
        rows, cols = dataarray.shape
        bands==1
    else:
        rows, cols, bands = dataarray.shape
    geotiff = geotiffinfo(rows, cols, bands, geo_transform, projection, dataarray,epsg)
    return geotiff

if __name__ == '__main__':
    # tiffile = r'D:\tmp3\landtype.tif'
    # shpfile = tiffile.replace(".tif",".shp")
    # createShpfile_from_tiffile(shpfile,tiffile)

    # # 图像裁剪
    # workpath = r'D:\tmp1'
    # os.chdir(workpath)

    # shpfile = 'roi.shp' # 绘图范围，手绘
    # tiffile = 'LYG_SPD.tif' # 原图
    # outfile = 'waterarea1.tif'  # 中间结果：裁剪图像
    # imgclip_with_shp(tiffile,shpfile,outfile)
    # geotiff = geotiffread(outfile)
    # data = geotiff.dataarray
    # data[np.isnan(data)] = 0
    # data[data!=0] = 1
    # geotiffwrite('watermask1.tif',data,geotiff.geo_transform,geotiff.projection)    # 中间结果：水域掩膜的tif
    # createShpfile_from_tiffile('watermask1.shp','watermask1.tif',fieldName="MASK")  # 最后结果：水域掩膜的shp
    
    # tiffile = r''   # 黑臭指数saturation
    # geotiff = geotiffread(tiffile)
    # data = geotiff.dataarray
    # mask = np.zeros_like(data)
    # mask[data<0.025] = 1    
    # geotiffwrite(tiffile[0:-4]+"_lt0025.tif",mask,geotiff.geo_transform,geotiff.projection)

    # # 提取水域
    # workpath = r'D:\tmp1\烧香河农田水域变化比对'
    # os.chdir(workpath)
    # tiffile = 'S2A_MSIL2A_20210408T023541_N0300_R089_T50SQD_20210408T043855_REF10m.tif'
    # geotiff = geotiffread(tiffile)
    # data = geotiff.dataarray
    # ndwi = getNDWI(data)
    # ndwi[ndwi>0] = 1
    # ndwi[ndwi<0] = 0
    # geotiffwrite(tiffile.replace('.tif',"_NDWI.tif"),ndwi,geotiff.geo_transform,geotiff.projection,datatype="UINT8")
    
    # # 影像作差
    # workpath = r'D:\tmp1\烧香河农田水域变化比对'
    # os.chdir(workpath)
    # file1 = 'S2B_MSIL2A_20220521T024549_N0400_R132_T50SQD_20220521T052752_REF10m_NDWI.tif'
    # file2 = 'S2A_MSIL2A_20210710T024551_N0301_R132_T50SQD_20210710T044905_REF10m_NDWI.tif'
    # geotiff1 = geotiffread(file1)
    # geotiff2 = geotiffread(file2)
    # data1 = geotiff1.dataarray.astype(np.float32)
    # data2 = geotiff2.dataarray.astype(np.float32)
    # diff = data1 - data2
    # geotiffwrite('20220521_minus_20210710.tif',diff,geotiff1.geo_transform,geotiff1.projection,datatype="FLOAT32")

    # # 栅格提取至点
    # tifpath = r'G:\启动大气遥感产品\H'
    # shpfile = r'G:\启动大气遥感产品\outlier_point.shp'
    # pts_df = pd.DataFrame([], columns=['site_ID', '时间', 'AQI', 'CO', 'NO2', 'O3', 'PM2_5', 'PM10','SO2'])
    # pts_df_sum=pd.DataFrame()
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # for g, tiffile in enumerate(tiffiles):
    #     geotiff = geotiffread(tiffile)
    #     points = gpd.read_file(shpfile)
    #     points = raster2Points(geotiff,points)
    #     # points = pd.DataFrame(points)
    #     list=['AQI', 'CO', 'NO2', 'O3', 'PM2_5', 'PM10','SO2']
    #     index_name = tiffile.split('.')[0].split('_')[3]
    #     if index_name=="PM2":
    #         index_name = tiffile[-9:-4]
    #     row_id=list.index(index_name)
    #     pts_df.iloc[:,row_id+2]=points.iloc[:,-1]
    #     if index_name=="AQI":
    #         pts_df.iloc[:, 0] = points.iloc[:, 6]
    #         pts_df.iloc[:, 1] = tiffile.split('.')[0].split('_')[2]
    #     if index_name=="SO2":
    #         pts_df_sum = pts_df_sum.append(pts_df)
    #     # points.drop('geometry',axis=1,inplace=True)
    # pts_df_sum.to_excel(os.path.join(tifpath,'image_data_1.xlsx'))

    # # 波段合成
    # tifpath = r'D:\项目数据\安徽省淮北市\淮北市水管家服务项目\ndvi_timeseries_202201_202206'
    # outfile = r'D:\项目数据\安徽省淮北市\淮北市水管家服务项目\ndvi_timeseries_202201_202206\ndvi_timeseries_202201_202206.tif'
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # dataarrays = []
    # for tiffile in tiffiles:
    #    geotiff = geotiffread(tiffile)
    #    dataarray = geotiff.dataarray
    #    dataarray[dataarray<0.3] = 0
    #    dataarrays.append(geotiff.dataarray)
    # dataarrays = np.dstack(dataarrays)
    # geotiffwrite(outfile,dataarrays,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32") 

#     # 聚类分析
#     tiffile = r'D:\项目数据\安徽省淮北市\淮北市水管家服务项目\ndvi_timeseries_202201_202206\ndvi_timeseries_202201_202206.tif'
#     geotiff = geotiffread(tiffile)
#     img_seg = geotiff.dataarray
#     img_seg[img_seg<0.3] = 0
#     img_dim = geotiff.bands
#     pixel_vals = img_seg.reshape((-1,img_dim))
#     pixel_vals = np.float32(pixel_vals)
#     criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.85)
#     k = 6
#     retval, labels, centers = cv2.kmeans(pixel_vals, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
#     segmented_image = labels.reshape((img_seg.shape[0], img_seg.shape[1]))
#     outfile = r'D:\项目数据\安徽省淮北市\淮北市水管家服务项目\ndvi_timeseries_202201_202206\ndvi_kmean6_0float.tif'
#     geotiffwrite(outfile,segmented_image,geotiff.geo_transform,geotiff.projection)



#     # e指数变换
#     path0 = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\reflectance2'
#     parameters = ['tp']
#     for parameter in parameters:
#         inpath = os.path.join(path0,parameter)
#         outpath = os.path.join(path0,parameter+'_recover')
#         if not os.path.exists(outpath):
#             os.mkdir(outpath)
#         os.chdir(inpath)
#         tiffiles = glob.glob("*.tif")
#         for tiffile in tiffiles:
#             geotiff = geotiffread(tiffile)
#             dataarray = geotiff.dataarray
#             dataarray = np.exp(dataarray)
#             dataarray[dataarray==1] = 0
#             geotiffwrite(os.path.join(outpath,tiffile),dataarray,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")


#     # 栅格提取至点
#     shpfile = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\水质监测点.shp'
#     gdf0 = gpd.read_file(shpfile)
#     pts_df = pd.DataFrame([],columns=['采样点','经度','纬度','时间','x坐标','y坐标'])
#     pts_num = len(gdf0)

#     tifpath = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\reflectance2\tp_recover'
#     os.chdir(tifpath)
#     tiffiles = glob.glob("*.tif")
#     for i,tiffile in enumerate(tiffiles):
#         geotiff = geotiffread(tiffile)
#         geotrans = geotiff.geo_transform
#         epsg = geotiff.epsg
#         gdf = gdf0.to_crs("EPSG:"+epsg)
#         for n in range(pts_num):
#             pts_df.loc[i*pts_num+n,'采样点'] = gdf0.loc[n,'NAME']
#             pts_df.loc[i*pts_num+n,'经度'] = gdf0.loc[n,'geometry'].x
#             pts_df.loc[i*pts_num+n,'纬度'] = gdf0.loc[n,'geometry'].y
#             pts_df.loc[i*pts_num+n,'x坐标'] = int((gdf.loc[n,'geometry'].x - geotrans[0]) / geotrans[1])
#             pts_df.loc[i*pts_num+n,'y坐标'] = int((gdf.loc[n,'geometry'].y - geotrans[3]) / geotrans[5])
#             pts_df.loc[i*pts_num+n,'时间'] = tiffile.split('T')[0]
#             band_num = geotiff.bands
#             if band_num == 1:
#                 pts_df.loc[i*pts_num+n,'B1'] = geotiff.dataarray[pts_df.loc[i*pts_num+n,'y坐标'],pts_df.loc[i*pts_num+n,'x坐标']]
#             else:
#                 for j in range(band_num):
#                     pts_df.loc[i*pts_num+n,'B'+str(j+1)] = geotiff.dataarray[pts_df.loc[i*pts_num+n,'y坐标'],pts_df.loc[i*pts_num+n,'x坐标'],j]
    
#     pts_df.to_excel(r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\tp反演值.xlsx')

#     # 光谱匹配自动站数据
#     spec_table = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\光谱数据.xlsx'
#     spec_df = pd.read_excel(spec_table)

#     var_list = ['氨氮','高锰酸盐指数','溶解氧','总磷']
#     smpdata_path = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\水质监测数据\清洗数据'
#     os.chdir(smpdata_path)
#     for i in spec_df.index:
#         smp_name = spec_df.loc[i,'采样点']
#         smp_date = str(spec_df.loc[i,'时间'])
#         if smp_name == '恒隆污水厂排口' or smp_name == '恒隆污水厂下游':
#             smp_date = smp_date[0:4]+'-'+smp_date[4:6]+'-'+smp_date[6:]
#             continue
#         else:
#             smp_date = smp_date[0:4]+'-'+smp_date[4:6]+'-'+smp_date[6:]+' 12:00:00'
#         smpdata_file = smp_name+'-清洗.xlsx'
#         smpdata_df = pd.read_excel(smpdata_file)
#         smpdata_df.set_index('时间',inplace=True)
#         for var in var_list:
#             try:
#                 smpdata = smpdata_df.loc[smp_date,var]
#                 spec_df.loc[i,var] = smpdata
#             except:
#                 continue            
    
#     spec_df.to_excel(r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\样本数据.xlsx')


#     0 值转空
#     tifpath0 = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\reflectance2'
#     var_list = ['codmn','nh3n','tp']
#     for var in var_list:
#         tifpath = os.path.join(tifpath0,var+"_cliped_smoothed")
#         outpath = os.path.join(tifpath0,var+"_cliped_smoothed_02nan")
#         if not os.path.exists(outpath):
#             os.mkdir(outpath)
#         os.chdir(tifpath)
#         tiffiles = glob.glob("*.tif")
#         for tiffile in tiffiles:        
#             outfile = os.path.join(outpath,tiffile)
#             geotiff = geotiffread(tiffile)
#             dataarray = geotiff.dataarray
#             dataarray[dataarray==0] = np.nan
#             geotiffwrite(outfile,dataarray,geotiff.geo_transform,geotiff.projection,datatype='FLOAT32')
    

    # # 去NODATA
    # path = r'D:\研究数据\20220620卫星遥感水质分析\gf4\waterQA'
    # newpath = r'D:\研究数据\20220620卫星遥感水质分析\gf4\waterQA'
    # os.chdir(path)
    # tiffiles = glob.glob("*8784*chlaByLgI.tif")
    # for tiffile in tiffiles:
    #     geotiff = geotiffread(tiffile)
    #     dataarray = geotiff.dataarray
    #     dataarray[np.isnan(dataarray)] = 0
    #     geotiffwrite(os.path.join(newpath,tiffile[0:-4]+"_1.tif"),geotiff.dataarray,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")

#     # 转真彩色
#     reffile = r'D:\tmp3\南京秦淮河水色分析\20220411T024539_20220411T025331_T50SPA.tif'
#     geotiff = geotiffread(reffile)
#     dataarray = geotiff.dataarray
#     ref2RGB(reffile,'2%',RGBfile=r'D:\tmp3\南京秦淮河水色分析\20220411T024539_20220411T025331_T50SPA_RGB.tif')

#     path = r'D:\tmp1\聚南大桥水域提取\rawdata\reflectance' 
#     os.chdir(path)
#     tiffiles = glob.glob("*.tif")
#     for i,tiffile in enumerate(tiffiles):
#         geotiff = geotiffread(tiffile)
#         ndwi = getNDWI(geotiff.dataarray)        
#         if i == 0:
#             ndwi[ndwi>0] = 1
#             ndwi[ndwi<0] = 0
#             waterarea = ndwi.copy()
#         else:
#             waterarea[ndwi>0] = 1
    
#     geotiffwrite(r'D:\tmp1\聚南大桥水域提取\rawdata\waterarea.tif',waterarea,geotiff.geo_transform,geotiff.projection,datatype="UINT8")


#     # 栅格转矢量
#     tiffile = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\reflectance2\codmn\20220111T025059_20220111T025055_T50SPD_codmn.tif'
#     shpfile = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\watermask.shp'
#     geotiff = geotiffread(tiffile)
#     dataarray = geotiff.dataarray
#     dataarray[dataarray>0] = 1
#     createShpfile_from_geotiff(shpfile,dataarray,geotiff.geo_transform,geotiff.projection,'ID','INT')
    

#     # 图像裁剪
#     shpfile = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\watermask.shp'
#     tifpath0 = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\reflectance2'
#     var_list = ['codmn','nh3n','tp']
#     for var in var_list:
#         tifpath = os.path.join(tifpath0,var+"_recover")
#         outpath = os.path.join(tifpath0,var+"_cliped")
#         if not os.path.exists(outpath):
#             os.mkdir(outpath)
#         os.chdir(tifpath)
#         tiffiles = glob.glob("*.tif")
#         for tiffile in tiffiles:        
#             outfile = os.path.join(outpath,tiffile)
#             imgclip_with_shp(tiffile,shpfile,outfile)


#     # 图像平滑
#     tifpath0 = r'D:\项目数据\江苏省连云港市\20220606大浦闸附近污水排口影响分析\reflectance2'
#     var_list = ['codmn','nh3n','tp']
#     for var in var_list:
#         tifpath = os.path.join(tifpath0,var+"_cliped")
#         outpath = os.path.join(tifpath0,var+"_cliped_smoothed")
#         if not os.path.exists(outpath):
#             os.mkdir(outpath)
#         os.chdir(tifpath)
#         tiffiles = glob.glob("*.tif")
#         for tiffile in tiffiles:        
#             outfile = os.path.join(outpath,tiffile)
#             geotiff = geotiffread(tiffile)
#             dataarray = geotiff.dataarray
#             smoothed = smoothdata(dataarray,method='median')
#             geotiffwrite(outfile,smoothed,geotiff.geo_transform,geotiff.projection,datatype='FLOAT32')

#     # 背景值处理1：背景值设0
#     tifpath = r'D:\项目数据\安徽省宿州市\泗县石梁河石龙湖流域动态溯源分析服务项目\reflectance'
#     outpath = r'D:\项目数据\安徽省宿州市\泗县石梁河石龙湖流域动态溯源分析服务项目\reflectance_bk0'
#     os.chdir(tifpath)
#     tiffiles = glob.glob("*T50SNB.tif")
#     for tiffile in tiffiles:
#         geotiff = geotiffread(tiffile)
#         dataarray = geotiff.dataarray
#         nodata_value = dataarray[0,0,:]
#         dataarray[dataarray==nodata_value]=0
#         geotiffwrite(os.path.join(outpath,tiffile),dataarray,geotiff.geo_transform,geotiff.projection,datatype="UINT16")


#     # 图像镶嵌1:对一个文件夹下所有tif进行镶嵌
    tifpath = r'I:\sl\新配准一类图像合集\一类图像合集'
    outfile = r'I:\sl\新配准一类图像合集\一类图像合集\xiangqian.tif'
    rasterMosaic(tifpath,outfile)

    # # 图像镶嵌2:对2个不同文件夹下同名tif进行镶嵌
    # tifpathes = [r'D:\tmp1\20220701北凌河数据下载\20210101_20210701_reflectance0',r'D:\tmp1\20220701北凌河数据下载\20210101_20210701_reflectance1',\
    #     r'D:\tmp1\20220701北凌河数据下载\20210101_20210701_reflectance2',r'D:\tmp1\20220701北凌河数据下载\20210101_20210701_reflectance3',\
    #         r'D:\tmp1\20220701北凌河数据下载\20210101_20210701_reflectance4',r'D:\tmp1\20220701北凌河数据下载\20210101_20210701_reflectance5']
    # outpath = r'D:\tmp1\20220701北凌河数据下载\20210101_20210701_reflectance'
    # os.makedirs(outpath,exist_ok=True)
    # rasterMosaic_byTIF(tifpathes,outpath)    

#     # 图像镶嵌3:对同一文件夹下所有TIF按日期进行合并，且背景值不参与合并
#     tifpath = r'D:\项目数据\安徽省宿州市\泗县石梁河石龙湖流域动态溯源分析服务项目\reflectance_bk0'    
#     outpath = r'D:\项目数据\安徽省宿州市\泗县石梁河石龙湖流域动态溯源分析服务项目\reflectance_mosaic'
#     os.chdir(tifpath)
#     tiffiles = glob.glob("*.tif")
#     # 提取所有日期序列
#     date_list = []
#     for tiffile in tiffiles:
#         date_list.append(tiffile.split("_")[0])
#     date_list = set(date_list)
#     # 按日期检索待合并文件，并对检索到的文件进行合并
#     for sensedate in date_list:
#         tiffiles = glob.glob(sensedate+"*.tif")
#         # 先定义栅格模板（大小）     
#         lon_l,lon_r,lat_u,lat_b = [],[],[],[]
#         for tiffile in tiffiles:
#             geotiff = geotiffread(tiffile)
#             geotrans = geotiff.geo_transform
#             rows,cols = geotiff.rows,geotiff.cols
#             lon_l.append(geotrans[0])
#             lat_u.append(geotrans[3])
#             lon_r.append(geotrans[0]+cols*geotrans[1])
#             lat_b.append(geotrans[3]+rows*geotrans[5])
#         min_x,max_x = min(lon_l),max(lon_r)
#         min_y,max_y = min(lat_b),max(lat_u)
#         geotrans0 = (min_x,geotrans[1],geotrans[2],max_y,geotrans[4],geotrans[5])
#         res_x = abs(geotrans[1])
#         res_y = abs(geotrans[5])
#         rows = int((max_y - min_y) / res_y)
#         cols = int((max_x - min_x) / res_x)
#         dataarray = np.zeros((rows,cols,geotiff.bands))  

#         # 再取原栅格的非0值对模板进行填充
#         for tiffile in tiffiles:
#             geotiff = geotiffread(tiffile)
#             geotrans = geotiff.geo_transform
#             st_x = int((geotrans[0]-min_x) / res_x)
#             st_y = int((max_y-geotrans[3]) / res_y)
#             subset = dataarray[st_y:st_y+geotiff.rows,st_x:st_x+geotiff.cols,:]
#             filled_mask = np.zeros_like(subset)
#             filled_mask[subset>0] = 1
#             subset[filled_mask==0] = geotiff.dataarray[filled_mask==0]
#             dataarray[st_y:st_y+geotiff.rows,st_x:st_x+geotiff.cols] = subset
#         geotiffwrite(os.path.join(outpath,sensedate+".tif"),dataarray,geotrans0,geotiff.projection,datatype="UINT16")

    

#     # 高光谱波段合成
#     tifpath = r'D:\通用数据\XD1_20220307114157_001-007\XD1_20220307114157_003_L1A'
#     os.chdir(tifpath)
#     tiffiles = glob.glob("*L1A*.tif")
#     print(tiffiles)

#     dataarray = []
#     for tiffile in tiffiles:
#         geotiff = geotiffread(tiffile)
#         dataarray.append(geotiff.dataarray)
#     dataarray = np.dstack(dataarray)
#     geotiffwrite(r'D:\通用数据\XD1_20220307114157_001-007\XD1_20220307114157_003_L1A.tif',dataarray,geotiff.geo_transform,geotiff.projection,datatype="UINT16")
    
    
#     # 图像压缩
#     tifpath = r'D:\项目数据\江苏省连云港市\连云港全域水色分析\S2Products'
#     os.chdir(tifpath)
#     tiffile = glob.glob("*SD.tif")[0]

#     geotiff = geotiffread(tiffile)
#     geotiffwrite(r'D:\tmp1\tmp22.tif',geotiff.dataarray,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")
#     cmd_str = r'gdaladdo -ro ' +  r'D:\tmp1\tmp0.tif' + ' 1 2 4 6'
#     os.system(cmd_str)

#     # 植被变化
#     shpfile = r'.shp'   # 耕地范围矢量文件
#     tifpath = r''   # 反射率文件
#     os.chdir(tifpath)
#     tiffiles = glob.glob("*.tif")
#     ndvi_list = []
#     time_list = []
#     for tiffile in tiffiles:
#         geotiff = geotiffread(tiffile)
#         refdata = geotiff.dataarray
#         landmask = shp2geotiff(shpfile,geotiff.rows,geotiff.cols,geotiff.geo_transform,geotiff.projection,field="")
#         refdata[landmask!=1] = 0
#         ndvi = getNDVI(refdata)
#         ndvi_list.append(np.mean(ndvi))
#         time_list.append(tiffile.split(".")[0])
#     df = pd.DataFrame()
#     df['影像'] = time_list
#     df['NDVI'] = ndvi_list
#     df.to_excel(r'.xlsx')



        

        
        
    
#     shpfile = r'D:\项目数据\江苏省盐城市\盐城射阳利民河运棉河省考断面溯源整治项目\分析范围\射阳区域.shp'
#     tiffile = r'D:\研究数据\全国10米土地覆被数据\50S_20200101-20210101.tif'
#     outfile = r'D:\项目数据\江苏省盐城市\盐城射阳利民河运棉河省考断面溯源整治项目\土地分类\landuse_clss10.tif'
#     imgclip_with_shp(tiffile,shpfile,outfile)

#     shpfile = r'D:\项目数据\江苏省盐城市\盐城射阳利民河运棉河省考断面溯源整治项目\分析范围\射阳区域.shp'
#     refpath = r'D:\tmp2\reflectance'
#     cliped_refpath = r'D:\tmp2\reflectance_cliped'
#     NDVI_refpath = r'D:\tmp2\reflectance_cliped_NDVI'

#     ndvis = []
#     datetimes = []
#     os.chdir(refpath)
#     reffiles = glob.glob('*.tif')    
#     for reffile in reffiles:
#         print(reffile)
#         cliped_reffile = os.path.join(cliped_refpath,reffile)
#         # imgclip_with_shp(reffile,shpfile,cliped_reffile)
#         geotiff = geotiffread(cliped_reffile)
#         refdata = geotiff.dataarray.astype('float')
#         ndvi = getNDVI(refdata)
#         geotiffwrite(os.path.join(NDVI_refpath,reffile),ndvi,geotiff.geo_transform,geotiff.projection,datatype='FLOAT32')
#         ndvi = ndvi[ndvi>0]
#         ndvis.append(np.mean(ndvi))
#         datetimes.append(reffile[0:-4])
#     print(ndvis)
#     print(datetimes)

#     path0 = r'D:\tmp3'
#     outpath = r'D:\tmp3\RGB'
#     pathes1 = glob.glob(path0+"\\*.SAFE")
#     for path1 in pathes1:
#         path2 = os.path.join(path1+'\\GRANULE')
#         path3 = glob.glob(path2+"\\*")[0]
#         path4 = os.path.join(path3,'IMG_DATA','R10m')
#         src_file = glob.glob(path4+"\\*TCI_10m*")[0]
#         dst_file = os.path.join(outpath,os.path.basename(src_file))
#         shutil.copy(src_file,dst_file)

#     tiffile = r'D:\tmp4\GF2_PMS2_E120.4_N33.6_20210605_L1A0005683576_3band.tif'
#     basename = os.path.basename(tiffile)[0:-4]
#     outpath = r'D:\tmp4'

#     geotiff = geotiffread(tiffile)
#     data = geotiff.dataarray
#     for i in range(0,3):
#         print("processing band"+str(i+1))
#         t = data[:,:,i].copy()
#         st_val,ed_val = getBreakpointsByLinear(t,'2%')
#         t[t<st_val] = st_val
#         t[t>ed_val] = ed_val
#         t = (t - st_val) / (ed_val - st_val) * 254 + 1
#         t = np.ceil(t)
#         t[data[:,:,i]==0] = 0
#         data[:,:,i] = t.copy()
 
#     outfile = os.path.join(outpath,basename+"_RGB.tif")
#     geotiffwrite(outfile,data,geotiff.geo_transform,geotiff.projection)
    
    


#     tiffile = r'D:\项目数据\江苏省盐城市\大丰3断面\土地覆被\民主村土地覆被_clss10.tif'
#     geotiff = geotiffread(tiffile)
#     data = geotiff.dataarray
#     newdata = np.zeros_like(data)
#     newdata[data==1] = 3
#     newdata[data==2] = 2
#     newdata[data==3] = 2
#     newdata[data==4] = 3
#     newdata[data==5] = 1
#     newdata[data==6] = 2
#     newdata[data==7] = 4
#     newdata[data==8] = 5
#     geotiffwrite(r'D:\项目数据\江苏省盐城市\大丰3断面\土地覆被\民主村土地覆被_clss5.tif',newdata,geotiff.geo_transform,geotiff.projection)
    
#     tiffile1 = r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\卫星遥感水质调查\Q2_20220111\reflectance\S2B_MSIL2A_20220111T025059_N0301_R132_T50SQD_20220111T052451_REF10m.tif'
#     tiffile2 = r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\卫星遥感水质调查\Q4_20220225\waterQA\S2A_MSIL2A_20220225T024711_N0400_R132_T50SPD_20220225T051533_SD.tif'
#     tiffile3 = r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\卫星遥感水质调查\Q3_20220302\waterQA\S2B_MSIL2A_20220302T024629_N0400_R132_T50SPD_20220302T053317_SD.tif'
#     geotiff = geotiffread(tiffile2)
#     tif1 = geotiff.dataarray
#     # ndwi1 = getNDWI(tif1)
#     # ndwi1[ndwi1>0] = 1
#     # ndwi1[ndwi1<0] = 0
#     geotiff = geotiffread(tiffile3)
#     tif2 = geotiff.dataarray
#     # ndwi2 = getNDWI(tif2)
#     # ndwi2[ndwi2>0] = 1
#     # ndwi2[ndwi2<0] = 0
#     difference = tif2 - tif1
#     geotiffwrite(r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\卫星遥感水质调查\SD0302_minus_SD0225_SPD.tif',difference,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")
    
    
#     proj = osr.SpatialReference()
#     proj.ImportFromEPSG(4490)
#     proj = proj.ExportToWkt()
#     path = r'E:\new'
#     outpath1 = r'D:\tmp1'
#     outpath2 = r'D:\tmp2'
#     os.chdir(path)
#     tiffiles = glob.glob("*I50I532447*.tif")
#     for tiffile in tiffiles:
#         geotiff = geotiffread(tiffile)
#         img = geotiff.dataarray

#         mask = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
#         mask[mask>0] = 1

#         cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
#         if len(cnts) > 0:
#             cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
#             cnt = cnts[0]
#             cv2.fillConvexPoly(mask,cnt,1)

#             img[np.logical_and(mask==1,img[:,:,0]==0)] = 1
            
#             geotiffwrite(os.path.join(outpath1,tiffile),img,geotiff.geo_transform,proj)

#             options = gdal.WarpOptions(srcSRS=geotiff.projection,dstSRS=proj,width=geotiff.rows,height=geotiff.cols,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
#             gdal.Warp(os.path.join(outpath2,tiffile),os.path.join(outpath1,tiffile),options=options)


    # tiffile = r'D:\tmp1\QD08261_codmn.tif'
    # cmd_str = r'gdaladdo -ro ' +  tiffile + ' 2 4 8 16'
    # os.system(cmd_str)