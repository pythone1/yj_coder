'''
@Time    :   2021/04/06 18:20:19
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 基础图像处理
'''

import os
import shutil
from cv2 import imshow
import numpy as np
import glob
import copy
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import matplotlib as mpl

# import scipy.signal as signal
from shapely import geometry, wkt
import geopandas as gpd  # 必须先导入geopandas再导入gdal!
from osgeo import gdal, gdalconst, osr,ogr

import geomProcess as geompro


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
        dataset=driver.Create(tiffile,cols,rows,bands,gdal.GDT_Float32)
    elif datatype == "UINT8":
        dataset = driver.Create(tiffile,cols,rows,bands,gdal.GDT_Byte) 
    elif datatype == "UINT16":
        dataset = driver.Create(tiffile,cols,rows,bands,gdal.GDT_UInt16)
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



##############################
##########栅格裁剪、拼接#############
##############################
'''
图像镶嵌
'''
def rasterMosaic(tifpath,outfile):
    tiffiles = glob.glob(tifpath+"\\*.tif")

    ref_raster = gdal.Open(tiffiles[0],gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    options = gdal.WarpOptions(srcSRS=ref_proj,dstSRS=ref_proj,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    gdal.Warp(outfile,tiffiles,options=options)

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
            # 矢量文件复杂、直接裁剪结果为空时，可先以0为缓冲距离创建新的矢量
            shp_buf = shpfile.replace(".shp","_buffer.shp")
            print(shp_buf)
            createBuffer(shpfile, shp_buf, 0.0,'gridcode',ogr.OFTInteger)
            out = outfile + "\\" + f
            print(out)
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
def imgslice_by_pixels(tifdata,pixelnum,outpath,prefix = "subset_",suffix = ".png",datatype = "UINT8",*buf_dist):
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
def imgslice_by_rowcol(tifdata,rownum,colnum,outpath,prefix="subset_",suffix=".png",datatype="UINT8"):
    imgwidth = int(tifdata.cols / rownum)    #向下取整
    imgheight = int(tifdata.rows / rownum)  
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
def shp2geotiff(shpfile,rows,cols,geo_transform,projection,field,fieldType="UINT8"): 
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
# # 图像平滑
# def smoothdata(dataarray,method):
#     if method == "median":   
#         newdata = signal.medfilt(dataarray,5)   #中值滤波
#     return newdata

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
    return st_value,ed_value

# 反射率（16位4波段）转RGB（8位3波段）,2% | 5%线性拉伸(stretch_mode = "2%" |stretch_mode =  "5%")
def ref2RGB(reffile,stretch_mode,RGBfile=False):
    geotiff = geotiffread(reffile)
    data = geotiff.dataarray
    data = data[:,:,0:3]    
    for i in range(3):
        t = data[:,:,i]
        t_st,t_ed = getBreakpointsByLinear(t,mode=stretch_mode)
        t = (t-t_st) / (t_ed-t_st) * 255
        t[t<0] = 0/
        t[t>255] = 255
        data[:,:,i] = t
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

if __name__ == '__main__':
    tifpath=r'U:\盐城无人机反射率\新建文件夹'
    outfile=r'U:\盐城无人机反射率\新建文件夹\ceshi.tif'
    rasterMosaic(tifpath, outfile)
    # shpfile = r'D:\Users\Administrator\Desktop\best_model\tif\slice\slice\1.shp'
    # tiffile = geotiffread(r'D:\Users\Administrator\Desktop\best_model\tif\1.tif')
    # createShpfile_from_geotiff(shpfile, tiffile)

    # tifpath = r'D:\Users\Desktop\一类图像合集\元素镶嵌'
    # # 确认输出路径
    # outfile = r'D:\Users\Desktop\一类图像合集\元素镶嵌\xq.tif'
    # rasterMosaic(tifpath, outfile)



    # tifpath=r'H:\lianyungang\t'
    # outfile=r'H:\lianyungang\t\1.tif'
    # rasterMosaic(tifpath, outfile)
    # tiffile=r'H:\lianyungang\S2A_MSIL2A_20220516T024551_N0400_R132_T50SQD_20220516T062219_RGB.tif'
    # shpfile=r'H:\xiangmu\lyg\nj.shp'
    # outfile=r'H:\xiangmu\lyg\SQD.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)
    # #
    # tifpath = r'E:\Work'
    # shppath = r'E:\Work'
    # outpath = r'E:\Work\xuzhou_yanhe\info'
    # os.chdir(tifpath)
    # tiffiles = glob.glob('*.tif')
    # print(tiffiles)
    # for tiffile in tiffiles:
    #     shpfile = os.path.join(shppath,tiffile.replace('_5band.tif','.shp'))
    #     shp_buf = os.path.join(shppath,shpfile.replace('.shp','_buf.shp'))
    #     createBuffer(shpfile, shp_buf, 0.0,'Parts',ogr.OFTInteger)
    #     outfile = os.path.join(outpath,tiffile.replace('_5band.tif','.tif'))
    #     imgclip_with_shp(tiffile,shp_buf,outfile)

    # tifpath = r'G:\项目文件\wurenji\txg'
    # shppath = r'G:\项目文件\wurenji\water'
    # outpath = r'G:\项目文件\wurenji\water\cut'
    # os.chdir(tifpath)
    # tiffiles = glob.glob('*.tif')
    # print(tiffiles)
    # for tiffile in tiffiles:
    #     shpfile = os.path.join(shppath,tiffile.replace('_5band.tif','.shp'))
    #     outfile = os.path.join(outpath,tiffile.replace('_5band.tif','.tif'))
    #     imgclip_with_shp(tiffile,shpfile,outfile)

# 裁剪
#     tifpath = r'H:\148\rf\st'
#     os.chdir(tifpath)
#     tiffiles = glob.glob('*.tif')
#     shpfile = r'H:\lyg\连云港掩膜\连云港.shp'
#     for tiffile in tiffiles:
#         outfile = r'H:\148\rf\st\caijian\1' + tiffile[0:-4] + ".tif"
#         imgclip_with_shp(tiffile,shpfile,outfile)

# # 地物分类
#     tiffile = r'H:\赣榆未裁剪无人机\AF_07.tif'
#     shpfile = r'H:\New_Shapefile.shp'
#     outfile = r'D:\Users\Administrator\Desktop\best_model\transform_added\test.tif'
#     imgclip_with_shp(tiffile,shpfile,outfile)
    #
    # tiffile = r'H:\lianyungang\xinzeng\SQD.tif'
    # geotiff = geotiffread(tiffile)
    # data = geotiff.dataarray
    # newdata = np.zeros_like(data)
    # newdata[data==1] = 3
    # newdata[data==2] = 2
    # newdata[data==3] = 2
    # newdata[data==4] = 3
    # newdata[data==5] = 1
    # newdata[data==6] = 2
    # newdata[data==7] = 4
    # newdata[data==8] = 5
    # geotiffwrite(r'H:\lianyungang\xinzeng\tudifenlei.tif',newdata,geotiff.geo_transform,geotiff.projection)



    
    # proj = osr.SpatialReference()
    # proj.ImportFromEPSG(4490)
    # proj = proj.ExportToWkt()
    # path = r'E:\new'
    # outpath1 = r'D:\tmp1'
    # outpath2 = r'D:\tmp2'
    # os.chdir(path)
    # tiffiles = glob.glob("*I50I532447*.tif")
    # for tiffile in tiffiles:
    #     geotiff = geotiffread(tiffile)
    #     img = geotiff.dataarray

    #     mask = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    #     mask[mask>0] = 1

    #     cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
    #     if len(cnts) > 0:
    #         cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
    #         cnt = cnts[0]
    #         cv2.fillConvexPoly(mask,cnt,1)

    #         img[np.logical_and(mask==1,img[:,:,0]==0)] = 1
            
    #         geotiffwrite(os.path.join(outpath1,tiffile),img,geotiff.geo_transform,proj)

    #         options = gdal.WarpOptions(srcSRS=geotiff.projection,dstSRS=proj,width=geotiff.rows,height=geotiff.cols,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    #         gdal.Warp(os.path.join(outpath2,tiffile),os.path.join(outpath1,tiffile),options=options)