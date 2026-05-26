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
def rasterMosaic_byTIF(tifpath1,tifpath2,outpath):
    os.chdir(tifpath1)
    tiffiles = glob.glob("*.tif")
    for tiffile in tiffiles:
        tiffile1 = tiffile
        tiffile2 = os.path.join(tifpath2,tiffile)
        outfile = os.path.join(outpath,tiffile)

        ref_raster = gdal.Open(tiffile1,gdal.GA_ReadOnly)
        ref_proj = ref_raster.GetProjection() 
        options = gdal.WarpOptions(srcSRS=ref_proj,dstSRS=ref_proj,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
        gdal.Warp(outfile,[tiffile1,tiffile2],options=options)

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
    points = points.to_crs(crs='EPSG:'+str(geotiff.epsg))

    data = geotiff.dataarray
    for i in points.index:
        lon = points.loc[i,'geometry'].x
        lat = points.loc[i,'geometry'].y
        x,y = geom2pixel(geotiff.geo_transform,lon,lat)
        for j in range(geotiff.bands):
            points.loc[i,'B'+str(j+1)] = data[y,x,j]
    
    return points


def clip_tiff_with_shapefile(tiff_path, shapefile_path, output_path):
    # 打开矢量图层
    shp_ds = ogr.Open(shapefile_path)
    if shp_ds is None:
        raise RuntimeError('Unable to open the shapefile.')

    shp_layer = shp_ds.GetLayer()

    # 使用shapefile的边界对tif图像进行裁剪
    options = gdal.WarpOptions(cutlineDSName=shapefile_path, cropToCutline=True)
    warp_result = gdal.Warp(srcDSOrSrcDSTab=tiff_path, destNameOrDestDS=output_path, options=options)

    if warp_result is None:
        raise RuntimeError('Error during the warp operation.')

    # 关闭数据集
    shp_ds = None
    warp_result = None

    print(f'Output saved to: {output_path}')


import geopandas as gpd
import numpy as np
from shapely.geometry import box
import os


def process_geospatial_data(range_file_path, ponds_file_path, n, output_dir, grid_size=300):
    def split_geometry(geometry, n, axis=0):
        minx, miny, maxx, maxy = geometry.bounds
        if axis == 0:  # Split along x-axis
            splits = np.linspace(minx, maxx, n + 1)
            return [box(splits[i], miny, splits[i + 1], maxy) for i in range(n)]
        else:
            splits = np.linspace(miny, maxy, n + 1)
            return [box(minx, splits[i], maxx, splits[i + 1]) for i in range(n)]

    def generate_grid(geometry, crs, grid_size=300):
        minx, miny, maxx, maxy = geometry.bounds
        x_coords = np.arange(minx, maxx, grid_size)
        y_coords = np.arange(miny, maxy, grid_size)
        grid = [box(x, y, x + grid_size, y + grid_size) for x in x_coords for y in y_coords]
        return gpd.GeoDataFrame({'geometry': grid}, crs=crs)

    # 读取文件
    range_gdf = gpd.read_file(range_file_path)
    ponds_gdf = gpd.read_file(ponds_file_path)

    # 投影到 EPSG:32650
    range_gdf = range_gdf.to_crs(epsg=32650)
    ponds_gdf = ponds_gdf.to_crs(epsg=32650)

    # 获取城市范围的总几何
    city_geometry = range_gdf.unary_union

    # 切割范围
    split_geometries = split_geometry(city_geometry, n)

    # 获取池塘文件的名字
    ponds_file_name = os.path.splitext(os.path.basename(ponds_file_path))[0]

    # 为每个分块生成输出
    for i, geom in enumerate(split_geometries):
        # 创建 GeoDataFrame 并裁剪
        block_gdf = gpd.GeoDataFrame(geometry=[geom], crs=range_gdf.crs)
        block_gdf = gpd.overlay(block_gdf, range_gdf, how='intersection')

        # 提取与池塘相交的部分（简单相交，不裁剪）
        intersected_ponds = ponds_gdf[ponds_gdf.intersects(geom)]
        ponds_output_path = f'{output_dir}/{ponds_file_name}_ponds_{i + 1}.gpkg'
        intersected_ponds.to_file(ponds_output_path, driver='GPKG')

        # 生成网格
        grid_gdf = generate_grid(geom, range_gdf.crs, grid_size)

        # 提取网格与原始范围相交的部分（简单相交，不裁剪）
        intersected_grid = grid_gdf[grid_gdf.intersects(city_geometry)]
        grid_output_path = f'{output_dir}/{ponds_file_name}_grid_{i + 1}.gpkg'
        intersected_grid.to_file(grid_output_path, driver='GPKG')

        # 保存分块范围文件（裁剪）
        block_output_path = f'{output_dir}/{ponds_file_name}_range_{i + 1}.gpkg'
        block_gdf.to_file(block_output_path, driver='GPKG')

    print("处理完成")




if __name__ == '__main__':
    # import geopandas as gpd
    #
    # # 读取shapefile文件
    # gdf = gpd.read_file(r'G:\xiangmu\江苏省天地图分割\实习生每日进度收集\二次校核结果\东海县_人工修正2.gpkg')
    #
    # # 转换投影为EPSG:32650 (UTM Zone 50N)
    # gdf = gdf.to_crs(epsg=32650)
    #
    # # 计算总面积，单位为平方米
    # total_area_sqm = gdf['geometry'].area.sum()
    #
    # # 将面积转换为亩（1亩 = 666.6667平方米）
    # total_area_sqkm = total_area_sqm / 666.6667
    # print(len(gdf))
    # print(f"Total area: {total_area_sqkm:.2f} 亩")

    # # 使用示例
    # range_file_path = r'G:\xiangmu\江苏省天地图分割\实习生每日进度收集\鼓楼建邺秦淮玄武\建邺秦淮鼓楼玄武范围.gpkg'
    # ponds_file_path = r'G:\xiangmu\江苏省天地图分割\实习生每日进度收集\鼓楼建邺秦淮玄武\建邺秦淮鼓楼玄武_人工校核2.gpkg'
    # n = 5  # 设置列数
    # output_dir = r'G:\xiangmu\江苏省天地图分割\实习生每日进度收集\鼓楼建邺秦淮玄武\test'  # 设置输出文件夹路径
    #
    # process_geospatial_data(range_file_path, ponds_file_path, n, output_dir)

    # import geopandas as gpd
    # from shapely import wkt
    #
    # # 定义WKT字符串
    # polygon_wkt = "POLYGON ((116.72590661875483 34.762595072747914, 116.72590661875483 34.62637431415109, 117.10085732976387 34.389252548591244, 117.57171861946449 34.1442477396418, 118.33036249581909 33.731882438726345, 118.32164244268267 33.21545017742362, 118.55708450079277 31.929515407762537, 118.88844266637966 31.350432477055378, 119.9435318662077 30.827837178509185, 120.60631713614151 30.790249200746857, 121.32137163190527 30.872615334861692, 121.64401817267674 31.029663281966492, 121.94050410027455 31.380213676034586, 121.91539888824326 31.70900300393474, 121.81075676691194 31.997872558905897, 120.19752406305264 34.31903960486821, 119.32550638529187 34.87891792372616, 119.12494203524233 35.18591435315831, 118.34886326000884 34.6926726458795, 117.08446873188058 34.993248961368025, 116.63974485087869 34.95752770494303, 116.72590661875483 34.762595072747914))"
    #
    # # 使用shapely将WKT字符串转换为geometry对象
    # polygon = wkt.loads(polygon_wkt)
    #
    # # 创建GeoDataFrame
    # gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
    #
    # # 将GeoDataFrame转换为GeoJSON格式并保存为文件
    # gdf.to_file("polygon.geojson", driver="GeoJSON").

    tiffile = r'F:\xiangmu\lyg\20250604\S2B_MSIL2A_20250604T024529_N0511_R132_T50SQD_20250604T044832.SAFE_SD.tif'
    shpfile = r'F:\Unlimited\Enterprisewechat_AutoBroadcast\RGB\海域掩膜.shp'
    outfile = r'F:\xiangmu\lyg\20250604\S2B_MSIL2A_20250604T024529_N0511_R132_T50SQD_20250604T044832.SAFE_SD_C.tif'
    imgclip_with_shp(tiffile, shpfile, outfile)

    tiffile = r'F:\xiangmu\lyg\20250604\S2B_MSIL2A_20250604T024529_N0511_R132_T50SQD_20250604T044832.SAFE_DBWI.tif'
    shpfile = r'F:\Unlimited\Enterprisewechat_AutoBroadcast\RGB\海域掩膜.shp'
    outfile = r'F:\xiangmu\lyg\20250604\S2B_MSIL2A_20250604T024529_N0511_R132_T50SQD_20250604T044832.SAFE_DBWI_C.tif'
    imgclip_with_shp(tiffile, shpfile, outfile)

    # tiffile = r'G:\Unlimited\Enterprisewechat_AutoBroadcast\DBWI\S2A_MSIL2A_20241111T024941_N0511_R132_T50SQD_20241111T061751.SAFE_DBWI.tif'
    # shpfile = r'G:\Unlimited\Enterprisewechat_AutoBroadcast\RGB\海域掩膜.shp'
    # outfile = r'G:\Unlimited\Enterprisewechat_AutoBroadcast\DBWI\S2A_MSIL2A_20241111T024941_N0511_R132_T50SQD_20241111T061751.SAFE_DBWI_clip2.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)

    # # import geopandas as gpd
    # from shapely.geometry import Point
    #
    # # 加载.shp文件
    # file_path = r'G:\BaiduNetdiskDownload\nj\定位.shp'
    # gdf = gpd.read_file(file_path)
    #
    # # 确保数据在WGS84坐标系下（EPSG:4326），这样经纬度计算才准确
    # gdf = gdf.to_crs(epsg=4326)
    #
    # # 计算经纬度，并作为新列添加到GeoDataFrame中
    # gdf['经度'] = gdf.geometry.x
    # gdf['纬度'] = gdf.geometry.y
    #
    # # 打印结果
    # print(gdf[['id', '经度', '纬度']])
    #
    # for index, row in gdf.iterrows():
    #     print(f"{row['id']}的坐标分别是，东经{row['经度']}, 北纬{row['纬度']}")

    # from osgeo import gdal, osr
    # import numpy as np
    #
    #
    # # def convert_to_rgb(input_path, output_path):
    # #     # 读取原始的单波段GeoTIFF文件
    # #     dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
    # #     band = dataset.GetRasterBand(1)  # 假设图像是单波段
    # #
    # #     # 读取数据并规范化到[0, 255]
    # #     gray_image_float32 = band.ReadAsArray().astype(np.float32)
    # #     min_val = np.nanmin(gray_image_float32)
    # #     max_val = np.nanmax(gray_image_float32)
    # #
    # #     # 处理全为相同值的特殊情况
    # #     if max_val - min_val == 0:
    # #         gray_image_normalized = np.zeros_like(gray_image_float32) * 255
    # #     else:
    # #         gray_image_normalized = (gray_image_float32 - min_val) / (max_val - min_val) * 255
    # #
    # #     # 类型转换到np.uint8
    # #     gray_image_uint8 = gray_image_normalized.astype(np.uint8)
    # #
    # #     # 扩展到3波段RGB
    # #     rgb_image = np.stack((gray_image_uint8,) * 3, axis=-1)
    # #
    # #     # 保存RGB图像为GeoTIFF
    # #     driver = gdal.GetDriverByName('GTiff')
    # #     out_dataset = driver.Create(output_path, dataset.RasterXSize, dataset.RasterYSize, 3, gdal.GDT_Byte)
    # #
    # #     # 设置仿射变换和投影
    # #     out_dataset.SetGeoTransform(dataset.GetGeoTransform())
    # #     out_dataset.SetProjection(dataset.GetProjection())
    # #
    # #     # 写入RGB数据
    # #     for i in range(3):
    # #         out_band = out_dataset.GetRasterBand(i + 1)
    # #         out_band.WriteArray(rgb_image[:, :, i])
    # #
    # #     # 清理
    # #     out_dataset.FlushCache()
    #
    #
    # def convert_to_rgb_inverted(input_path, output_path):
    #     # 读取原始的单波段GeoTIFF文件
    #     dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
    #     band = dataset.GetRasterBand(1)  # 假设图像是单波段
    #
    #     # 读取数据
    #     gray_image_float32 = band.ReadAsArray().astype(np.float32)
    #     min_val = np.nanmin(gray_image_float32)
    #     max_val = np.nanmax(gray_image_float32)
    #
    #     # 规范化到[0, 255]然后反转
    #     if max_val - min_val == 0:
    #         gray_image_normalized_inverted = np.full_like(gray_image_float32, 255)
    #     else:
    #         gray_image_normalized = (gray_image_float32 - min_val) / (max_val - min_val) * 255
    #         gray_image_normalized_inverted = 255 - gray_image_normalized  # 反转数值
    #
    #     # 类型转换到np.uint8
    #     gray_image_uint8 = gray_image_normalized_inverted.astype(np.uint8)
    #
    #     # 扩展到3波段RGB
    #     rgb_image = np.stack((gray_image_uint8,) * 3, axis=-1)
    #
    #     # 保存RGB图像为GeoTIFF
    #     driver = gdal.GetDriverByName('GTiff')
    #     out_dataset = driver.Create(output_path, dataset.RasterXSize, dataset.RasterYSize, 3, gdal.GDT_Byte)
    #
    #     # 设置仿射变换和投影
    #     out_dataset.SetGeoTransform(dataset.GetGeoTransform())
    #     out_dataset.SetProjection(dataset.GetProjection())
    #
    #     # 写入RGB数据
    #     for i in range(3):
    #         out_band = out_dataset.GetRasterBand(i + 1)
    #         out_band.WriteArray(rgb_image[:, :, i])
    #
    #     # 清理
    #     out_dataset.FlushCache()
    #
    #
    # def convert_to_rgb(input_path, output_path):
    #     # 读取原始的单波段GeoTIFF文件
    #     dataset = gdal.Open(input_path, gdal.GA_ReadOnly)
    #     band = dataset.GetRasterBand(1)  # 假设图像是单波段
    #
    #     # 读取数据
    #     gray_image_float32 = band.ReadAsArray().astype(np.float32)
    #     min_val = np.nanmin(gray_image_float32)
    #     max_val = np.nanmax(gray_image_float32)
    #
    #     target_min = 50
    #     target_max = 200
    #
    #     # 处理全为相同值的特殊情况
    #     if max_val - min_val == 0:
    #         gray_image_normalized = np.full_like(gray_image_float32, target_min)
    #     else:
    #         # 规范化到50-200
    #         gray_image_normalized = ((gray_image_float32 - min_val) / (max_val - min_val)) * (
    #                     target_max - target_min) + target_min
    #
    #     # 类型转换到np.uint8
    #     gray_image_uint8 = np.clip(gray_image_normalized, 0, 255).astype(np.uint8)  # 确保值在0到255之间
    #
    #     # 扩展到3波段RGB
    #     rgb_image = np.stack((gray_image_uint8,) * 3, axis=-1)
    #
    #     # 保存RGB图像为GeoTIFF
    #     driver = gdal.GetDriverByName('GTiff')
    #     out_dataset = driver.Create(output_path, dataset.RasterXSize, dataset.RasterYSize, 3, gdal.GDT_Byte)
    #
    #     # 设置仿射变换和投影
    #     out_dataset.SetGeoTransform(dataset.GetGeoTransform())
    #     out_dataset.SetProjection(dataset.GetProjection())
    #
    #     # 写入RGB数据
    #     for i in range(3):
    #         out_band = out_dataset.GetRasterBand(i + 1)
    #         out_band.WriteArray(rgb_image[:, :, i])
    #
    #     # 清理
    #     out_dataset.FlushCache()
    #
    #
    # from PIL import Image
    # import os
    #
    #
    # # Function to convert TIFF to PNG
    # def convert_tiff_to_png(tiff_file_path, png_file_path=None):
    #     """
    #     Convert a TIFF file to a PNG file.
    #
    #     Parameters:
    #     - tiff_file_path: str, path to the input TIFF file.
    #     - png_file_path: str, optional, path to the output PNG file. If not provided, the output will be saved in the same directory as the input file with a .png extension.
    #
    #     Returns:
    #     - str, path to the output PNG file.
    #     """
    #     # Open the TIFF file
    #     with Image.open(tiff_file_path) as img:
    #         # Define the PNG file path if not provided
    #         if png_file_path is None:
    #             png_file_path = os.path.splitext(tiff_file_path)[0] + '.png'
    #         # Save the image as PNG
    #         img.save(png_file_path, "PNG")
    #     return png_file_path
    #
    # # Example usage:
    # convert_tiff_to_png(r'G:\xiangmu\超分分割测试\median_rgb_out.tif')

    # 调用函数
    # input_path = r'G:\qiwei\WXWork\1688858186325806\Cache\File\2024-02\median.tif'
    # output_path = r'G:\qiwei\WXWork\1688858186325806\Cache\File\2024-02\median_50_200.tif'
    # convert_to_rgb(input_path, output_path)

    # 现在rgb_image是一个3波段的8位RGB图像
    # 例如，使用cv2.imwrite保存图像
    # cv2.imwrite('path_to_save_rgb_image.tif', rgb_image)

    # shpfile=r'G:\xiangmu\20240118开福区点污染源汇总\污染热力图\道路.shp'
    # shp2geotiff(shpfile, rows, cols, geo_transform, projection, field=None, fieldType="UINT8")
    # info = geotiffread(r'G:\xiangmu\20231020高邮水产养殖水面数据\river2.tif')
    # data = geotiffread(r'G:\xiangmu\20231020高邮水产养殖水面数据\f1.tif').dataarray
    # geotiffwrite(r'G:\xiangmu\20231020高邮水产养殖水面数据\3.tif',data,info.geo_transform,info.projection)
    # # from PIL import Image
    # import numpy as np
    # import random
    # #
    # # # 路径设置
    # # # 读取图像
    # animal_path = r'G:\xiangmu\20231020高邮水产养殖水面数据\fish.tif'
    # background_path = r'G:\xiangmu\20231020高邮水产养殖水面数据\river2.tif'
    # animal_img = Image.open(animal_path).convert('RGBA')
    # background_img = Image.open(background_path).convert('RGBA')
    #
    # # 转换背景图为numpy数组
    # background_array = np.array(background_img)
    #
    # # 找到所有非零像素的位置
    # non_zero_indices = np.argwhere(np.any(background_array[:, :, :3] != 0, axis=-1))
    #
    # # 选择随机位置
    # num_animals = 20
    # positions = []
    #
    # while len(positions) < num_animals:
    #     idx = random.choice(non_zero_indices)
    #     x, y = idx[1], idx[0]
    #
    #     # 检查动物是否可以放置在这个位置（不超过背景边界）
    #     if x + animal_img.width < background_img.width and y + animal_img.height < background_img.height:
    #         # 确保不与已选择的位置重叠
    #         overlap = False
    #         for pos in positions:
    #             if (x >= pos[0] and x < pos[0] + animal_img.width) or \
    #                     (y >= pos[1] and y < pos[1] + animal_img.height):
    #                 overlap = True
    #                 break
    #         if not overlap:
    #             positions.append((x, y))
    #
    # # 创建一个新的图片用于输出，复制背景到输出图像
    # output_img = background_img.copy()
    #
    # # 将动物贴到随机位置
    # for position in positions:
    #     output_img.paste(animal_img, position, animal_img)
    #
    # output_img_path = r'G:\xiangmu\20231020高邮水产养殖水面数据\f1.tif'
    # output_img.save(output_img_path, format='TIFF')

    # input_tif = r'G:\xiangmu\20231020高邮水产养殖水面数据\result.tif'
    # input_shp = r'G:\BaiduNetdiskDownload\溧阳市\死鱼提取.shp'
    # output_tif = r'G:\xiangmu\20231020高邮水产养殖水面数据\river2.tif'
    # #  执行裁剪
    # clip_tiff_with_shapefile(input_tif, input_shp, output_tif)
     # 保存结果

    # from shapely.geometry import box
    #
    # # 读取Shapefile
    # shp_file_path = r'G:\xiangmu\水产养殖\南京水体采样测试\溧阳浊度SD对照测试\溧阳\溧阳市.shp'  # 这里替换为你的shp文件路径
    # gdf = gpd.read_file(shp_file_path)
    #
    # # 设置目标坐标系为UTM 50N (EPSG:32650)
    # utm_crs = 'EPSG:32650'
    # gdf_utm = gdf.to_crs(utm_crs)
    #
    # # 计算外接矩形（bounding box）
    # bounds = gdf_utm.total_bounds  # 获取一个(minx, miny, maxx, maxy)的元组
    # bbox = box(*bounds)  # 创建外接矩形
    #
    # # 计算外接矩形的面积
    # area = bbox.area
    #
    # print(f'外接矩形的面积（在UTM 50N坐标系下）: {area} 平方米')
    # from nowatermark import WatermarkRemover

    # datainfo = geotiffread(r'G:\BaiduNetdiskDownload\changsha4\logo.tif')
    # array = datainfo.dataarray
    # mask = (array[:, :, 0] < 80) & (array[:, :, 1] < 90) & (array[:, :, 2] < 70)
    # # 将遮罩中为True的所有位置在原数组中设置为0
    # array[mask] = 0
    #
    # # gray_image = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
    # geotiffwrite(r'G:\BaiduNetdiskDownload\changsha4\logo_black.tif',array,datainfo.geo_transform,datainfo.projection)

    # path = 'G:/BaiduNetdiskDownload/nowatermark-data/'
    # watermark_template_filename = path + 'anjuke-watermark-template.jpg'
    # print(watermark_template_filename)
    # remover = WatermarkRemover()
    # remover.load_watermark_template(watermark_template_filename)
    # remover.remove_watermark(path + 'anjuke2.jpg', path + 'anjuke2-result.jpg')
    # remover.remove_watermark(path + 'anjuke4.jpg', path + 'anjuke4-result.jpg')

    # import geopandas as gpd
    # from shapely.geometry import LineString
    #
    # # 指定搜索的目录和通配符模式
    # # pattern = '/*.shp'  # 如果是在当前目录下搜索，可以用 './*.shp'
    # pattern = r'G:\qiwei\WXWork\1688858186325806\Cache\File\2023-12\08管理线\*.shp'  # 请替换为您的.shp文件所在的目录路径
    #
    # # 使用glob.glob()获取所有匹配的文件路径
    # shp_files = glob.glob(pattern)
    #
    # # 用于存储所有文件的长度总和
    # total_length_km = 0
    #
    # # 用于存储每个文件的长度
    # file_lengths_km = []
    #
    # # 对于每个shp文件，进行坐标转换并计算长度
    # for shp_file in shp_files:
    #     # 使用geopandas读取矢量文件
    #     gdf = gpd.read_file(shp_file)
    #
    #     # 投影到UTM 50N坐标系（EPSG:32650）
    #     gdf_utm = gdf.to_crs(epsg=32650)
    #
    #     # 初始化长度总和
    #     total_length = 0
    #
    #     # 遍历geodataframe中的每个geometry
    #     for geom in gdf_utm.geometry:
    #         if isinstance(geom, LineString):
    #             # 计算当前线段的长度并累加到总和中
    #             total_length += geom.length
    #         else:
    #             print(f"{shp_file} 中的几何对象不是线段。")
    #
    #     # 将长度从米换算成千米
    #     total_length_km_file = total_length / 1000
    #     file_lengths_km.append(total_length_km_file)
    #
    #     # 累加到全局的长度总和
    #     total_length_km += total_length_km_file
    #
    # # 打印每个文件的长度和占总长度的比例
    # for shp_file, length_km in zip(shp_files, file_lengths_km):
    #     length_percentage = (length_km / total_length_km) * 100 if total_length_km else 0
    #     print(f"{shp_file} 中线段的总长度为：{length_km} 千米，占总长度的百分比为：{length_percentage:.2f}%。")
    #
    # # 打印总长度
    # print(f"所有文件的线段总长度为：{total_length_km} 千米.")
    # import pandas as pd
    # import geopandas as gpd
    # from shapely.geometry import Point
    #
    # # 读取Excel文件
    # # 请替换 'path_to_excel_file.xlsx' 为你的Excel文件的路径
    # # 如果你的点坐标在不同的列，或者工作表(sheet)不是第一个，请相应地调整
    # df = pd.read_excel(r'G:\qiwei\WXWork\1688858186325806\Cache\File\2024-01\卫星反演数据.xlsx', sheet_name='Sheet2')
    #
    # # 确保经度和纬度的列名与你的Excel文件中的列名匹配
    # # 这里假设第二列是经度，第三列是纬度
    # gdf = gpd.GeoDataFrame(
    #     df,
    #     geometry=[Point(xy) for xy in zip(df.iloc[:, 2], df.iloc[:, 3])]
    # )
    #
    # # 设置坐标参考系统(CRS)为WGS84，这是常用的地理坐标系统，EPSG代码是4326
    # gdf.crs = "EPSG:4326"
    # # 将GeoDataFrame保存为Shapefile
    # # 请替换 'output_path' 为你希望保存shapefile的路径
    # gdf.to_file(r'G:\xiangmu\lyg\20240106水质反演\反演点位.shp',ecoding='utf-8')

    # import glob
    # import geopandas as gpd
    #
    # # 使用glob模块找到所有的GeoJSON文件
    # geojson_files = glob.glob(r'G:\Unlimited\点位核查专用\数据清洗\按坑塘核实排口\统计\*.geojson')
    #
    # # 使用geopandas读取第一个文件以初始化合并
    # if geojson_files:
    #     combined_gdf = gpd.read_file(geojson_files[0])
    #
    #     # 遍历剩余的文件并逐一合并
    #     for file in geojson_files[1:]:
    #         gdf = gpd.read_file(file)
    #         combined_gdf = combined_gdf.append(gdf, ignore_index=True)
    #
    #     # 将合并后的GeoDataFrame写入一个新的GeoJSON文件
    #     combined_gdf.to_file(r"G:\Unlimited\点位核查专用\数据清洗\按坑塘核实排口\统计\combined_geojson.geojson", driver='GeoJSON')
    # else:
    #     print("No GeoJSON files found.")

    # data = geotiffread(r'G:\BaiduNetdiskDownload\East_Jiangsu\East_Jiangsu_Wuxi.tif')
    # array = data.dataarray== 6
    # geotiffwrite(r'G:\BaiduNetdiskDownload\East_Jiangsu\wuxi.tif',array,data.geo_transform,data.projection)


    # desfile = r'G:\xiangmu\20240126地图下载专用\宜兴矢量地图分块下载\八倍\配准\天地图0.5配准.tif'
    # dst_epsg = 32650
    # outfile = r'G:\xiangmu\20240126地图下载专用\宜兴矢量地图分块下载\八倍\配准\天地图0.5配准测试50N.tif'
    # tiffileReproject(desfile, outfile, dst_epsg)

    # 图像镶嵌1:对一个文件夹下所有tif进行镶嵌
    # tifpath = r'E:\file\NJ_DATA\GF_20210219_20210319_L03_CGCS2000'
    # outfile = r'E:\file\NJ_DATA\GF_20210219_20210319_L03_CGCS2000\202102_RGB.tif'
    # rasterMosaic(tifpath,outfile)

    # 矢量裁剪栅格
    # tiffile=r'I:\pyMethod\Enterprisewechat_AutoBroadcast\lianyungang\DBWI\S2A_MSIL2A_20231018T024711_N0509_R132_T50SQD_20231018T060156_DBWI.tif'
    # shpfile=r'I:\pyMethod\Enterprisewechat_AutoBroadcast\lianyungang\海掩膜.shp'
    # outfile=r'I:\pyMethod\Enterprisewechat_AutoBroadcast\lianyungang\DBWI\S2A_MSIL2A_20231018T024711_N0509_R132_T50SQD_20231018T060156_DBWI_clip.tif'
    # imgclip_with_shp(tiffile, shpfile, outfile)



    # # 栅格提取至点
    # tiffile = r'D:\研究数据\20220620卫星遥感水质分析\sentinel2\reflectance\S2B_MSIL2A_20220607T023549_N0400_R089_T51STT_20220607T052001_REF.tif'
    # shpfile = r'D:\研究数据\20220620卫星遥感水质分析\采样点.shp'

    # geotiff = geotiffread(tiffile)    
    # points = gpd.read_file(shpfile)
    # points = raster2Points(geotiff,points)
    # points = pd.DataFrame(points)
    # points.drop('geometry',axis=1,inplace=True)
    # points.to_excel(r'D:\研究数据\20220620卫星遥感水质分析\采样数据.xlsx')

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
    

    # 去NODATA
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

    # tifpath=r'H:\下载\reflectance\镶嵌专用'
    # outfile = r'H:\下载\reflectance\镶嵌\20230129.tif'
    # rasterMosaic(tifpath,outfile)

    # 图像镶嵌2:对2个不同文件夹下同名tif进行镶嵌
    # tifpath1 = r'H:\下载\reflectance\snd\allTimeWater.tif'
    # tifpath2 = r'H:\下载\reflectance\smd\allTimeWater.tif'
    # outpath = r'H:\下载\reflectance\allTimeWater.tif'
    # rasterMosaic_byTIF(tifpath1,tifpath2,outpath)

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
    #
    #     mask = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    #     mask[mask>0] = 1
    #
    #     cnts = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
    #     if len(cnts) > 0:
    #         cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
    #         cnt = cnts[0]
    #         cv2.fillConvexPoly(mask,cnt,1)
    #
    #         img[np.logical_and(mask==1,img[:,:,0]==0)] = 1
    #
    #         geotiffwrite(os.path.join(outpath1,tiffile),img,geotiff.geo_transform,proj)
    #
    #         options = gdal.WarpOptions(srcSRS=geotiff.projection,dstSRS=proj,width=geotiff.rows,height=geotiff.cols,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    #         gdal.Warp(os.path.join(outpath2,tiffile),os.path.join(outpath1,tiffile),options=options)
