import os,glob
import copy,cv2
from osgeo import gdal, osr,ogr,gdalconst
import numpy as np
import matplotlib.pyplot as plt
# import rasterio as rio
# from rasterio.warp import calculate_default_transform, reproject
# from rasterio import crs
# from rasterio.enums import Resampling

os.environ['PROJ_LIB'] = r"C:\Users\Administrator\.conda\envs\geoprocess\Lib\site-packages\osgeo\data\proj"

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
    raster_dataset = gdal.Open(tiffile, gdal.GA_ReadOnly)
    geo_transform = raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()
    srs = osr.SpatialReference(proj)  # 获取投影坐标系
    epsg = srs.GetAttrValue('AUTHORITY', 1)  # 获取投影坐标系epsg编号
    dataarray = []
    for i in range(1, raster_dataset.RasterCount + 1):
        band = raster_dataset.GetRasterBand(i)  # 波段从1计数
        dataarray.append(band.ReadAsArray())

    dataarray = np.dstack(dataarray)
    rows, cols, bands = dataarray.shape
    del raster_dataset, band
    geotiff = geotiffinfo(rows, cols, bands, geo_transform, proj, dataarray, epsg)

    return geotiff


'''
写栅格文件
tiffile可为*.tif, *.png（datatype需为UINT8）
datatype choose from ["FLOAT32","UINT8"]
'''
def geotiffwrite(tiffile, data, geo_transform, projection, datatype="UINT8"):
    driver = gdal.GetDriverByName("GTiff")
    if len(data.shape) == 3:
        rows, cols, bands = data.shape
    elif len(data.shape) == 2:
        rows, cols = data.shape
        bands = 1
    if datatype == "FLOAT32":
        dataset = driver.Create(tiffile, cols, rows, bands, gdal.GDT_Float32, options=["TILED=YES", "COMPRESS=LZW"])
    elif datatype == "UINT8":
        dataset = driver.Create(tiffile, cols, rows, bands, gdal.GDT_Byte, options=["TILED=YES", "COMPRESS=LZW"])
    elif datatype == "UINT16":
        dataset = driver.Create(tiffile, cols, rows, bands, gdal.GDT_UInt16, options=["TILED=YES", "COMPRESS=LZW"])
    else:
        print("A datatype dose not support yet!")
    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    if bands == 1:
        dataset.GetRasterBand(1).WriteArray(data)
    else:
        for i in range(bands):
            dataset.GetRasterBand(i + 1).WriteArray(data[:, :, i])
    dataset = None  # 关闭文件

    # 创建金字塔
    cmd_str = r'gdaladdo -ro ' + tiffile + ' 2 4 8 16'
    os.system(cmd_str)


def getBreakpointsByLinear(data, mode='2%'):
    data = data[data > 0]
    minvalue = np.nanmin(data)
    maxvalue = np.nanmax(data)
    bins = np.linspace(minvalue, maxvalue, 101)  # 101个结点，分100个区间
    cml_frequence, _, _ = plt.hist(data, bins, histtype='bar', cumulative=True)
    total_num = len(data)
    y = cml_frequence / total_num
    if mode == '2%':
        t = np.abs(y - 0.02)
        st_index = np.where(t == np.nanmin(t))[0][0]
        st_value = bins[st_index]
        t = np.abs(y - 0.98)
        ed_index = np.where(t == np.nanmin(t))[0][0]
        ed_value = bins[ed_index]
    elif mode == '5%':
        t = np.abs(y - 0.05)
        st_index = np.where(t == np.nanmin(t))[0][0]
        st_value = bins[st_index]
        t = np.abs(y - 0.95)
        ed_index = np.where(t == np.nanmin(t))[0][0]
        ed_value = bins[ed_index]
    elif mode == '1%':
        t = np.abs(y - 0.01)
        st_index = np.where(t == np.nanmin(t))[0][0]
        st_value = bins[st_index]
        t = np.abs(y - 0.99)
        ed_index = np.where(t == np.nanmin(t))[0][0]
        ed_value = bins[ed_index]
    return st_value, ed_value
def addText2Img(img,textstr):
    '''
    功能：给图片添加日期说明
    img: np.dataarray
    textstr: str 待添加文本内容
    返回：
    img: 添加文字后的图片
    '''
    imgsize = img.shape[0]
    fontsize = int(imgsize*0.001)
    locxy = int(imgsize*0.05)
    linewidth = int(imgsize*0.002)
    cv2.putText(img, textstr, (locxy, locxy), cv2.FONT_HERSHEY_SIMPLEX, fontsize, (255, 255, 255), linewidth)

    return img

def S3_ref2RGB(data,stretch_mode):
    '''
    rgb拉伸
    :param:data: np.array ref矩阵
    :param:stretch_mode:str 1% | 2% | 5%线性拉伸
    '''
    for i in range(3):
        t = data[:,:,i]
        t_st,t_ed = S3_getBreakpointsByLinear(t,mode=stretch_mode)
        t[t < t_st] = t_st
        t[t > t_ed] = t_ed
        t = (t - t_st) / (t_ed - t_st) * 254 + 1  # 有效值的映射范围 [1,255]
        t[data[:, :, i] == 0] = 0  # 背景值设0
        data[:, :, i] = t.copy()
    return data
# 图像线性拉伸-获取间断点
def S3_getBreakpointsByLinear(data,mode = '1%'):
    data = data[data>0]
    minvalue = 20
    maxvalue = 100
    print(minvalue,maxvalue)
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
def ref2RGB(reffile, stretch_mode, RGBfile=False):
    geotiff = geotiffread(reffile)
    data = geotiff.dataarray.astype('float')
    data = data[:, :, 0:3]
    data[data == 32767] = 0
    for i in range(3):
        t = data[:, :, i].copy()
        t_st, t_ed = getBreakpointsByLinear(t, mode=stretch_mode)
        t[t < t_st] = t_st
        t[t > t_ed] = t_ed
        t = (t - t_st) / (t_ed - t_st) * 254 + 1  # 有效值的映射范围 [1,255]
        t[data[:, :, i] == 0] = 0  # 背景值设0
        data[:, :, i] = t.copy()
    r = copy.deepcopy(data[:, :, 2])
    data[:, :, 2] = copy.deepcopy(data[:, :, 0])
    data[:, :, 0] = copy.deepcopy(r)
    if RGBfile:
        geotiffwrite(RGBfile, data, geotiff.geo_transform, geotiff.projection, datatype="UINT8")

    return data

def imgStretch(imgdata,stretch_mode):
    '''
    图像拉伸
    :param imgdata: np.dataarray
    :param stretch_mode: str 拉伸方法
    :return:
    '''
    imgdata = imgdata.astype('float')
    t_st, t_ed = getBreakpointsByLinear(imgdata, mode=stretch_mode)
    data = (imgdata - t_st) / (t_ed - t_st) * 254 + 1  # 有效值的映射范围 [1,255]
    data[imgdata==0] = 0
    data = data.astype('uint8')

    return data

'''按矢量裁剪栅格'''
def imgclip_with_shp(tiffile,shpfile,outfile,dstNodata=0):
    if tiffile.endswith(".tif"):
        shp_buf = shpfile.replace(".shp","_buffer.shp")
        createBuffer(shpfile, shp_buf, 0.0,'LX',ogr.OFTInteger)
        # tiffile为某个tif文件
        gdal.Warp(outfile,tiffile,cutlineDSName = shpfile,cropToCutline = True,dstNodata = dstNodata)
    else:
        # tiffile为存放多个待裁剪栅格的路径
        os.chdir(tiffile)
        tiffiles = glob.glob("*.tif")
        for f in tiffiles:
            tif = tiffile + "\\" + f
            # 矢量文件复杂、直接裁剪结果为空时，可先以0为缓冲距离创建新的矢量
            shp_buf = shpfile.replace(".shp","_buffer.shp")
            print(shp_buf)
            createBuffer(shpfile, shp_buf, 0.0,'NAME',ogr.OFTInteger)
            out = outfile + "\\" + f
            print(out)
            if dstNodata == None:
                gdal.Warp(out,tif,cutlineDSName = shp_buf,cropToCutline = True)
            else:
                gdal.Warp(out,tif,cutlineDSName = shp_buf,cropToCutline = True,dstNodata = 0)

'''
创建缓冲区，用于按矢量裁剪栅格模块
矢量文件复杂、直接裁剪结果为空时，可先以0为缓冲距离创建新的矢量
'''
def createBuffer(inputfn, outputBufferfn, bufferDist,fieldName,fieldType):
    # 支持中文路径
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8","YES")
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

'''
图像镶嵌1：对一个文件夹下所有tif进行镶嵌
'''
def rasterMosaic(inputfiles,outfile):
    ref_raster = gdal.Open(inputfiles[0],gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    options = gdal.WarpOptions(srcSRS=ref_proj,dstSRS=ref_proj,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    gdal.Warp(outfile,inputfiles,options=options)

'''
按像元数切片
tifdata：geotiffinfo对象
pixelnum：像元数
outpath：切片存放路径
prefix：切片文件名-前缀
suffix：切片文件名-后缀
datatype：数据存储类型
'''
def imgslice_by_pixels(tifdata,pixelnum,outpath,prefix = "subset_",suffix = ".tif",datatype = "FLOAT32",*buf_dist):
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

# 按设定前、后缀名及切片号返回切片文件名
def getTileName(outpath,prefix,subset_id,suffix):
    filename = prefix + str(subset_id) + suffix       #裁剪图像保存格式为png
    filename = os.path.join(outpath,filename)
    return filename


# 按设定索引进行矩阵切片,tifdata为geotiff对象，返回切片后的新geotiff对象
def getImgtileByIndex(tifdata, startrow, endrow, startcol, endcol):
    # 矩阵切片
    data = tifdata.dataarray
    tile_data = data[startrow:endrow, startcol:endcol, :]
    print(tile_data.shape)
    print(startrow, endrow, startcol, endcol)

    # 判断切片是否均为无效值
    if np.nanmax(np.nanmax(np.nanmax(tile_data))) == 0 or np.nanmin(np.nanmin(np.nanmin(tile_data))) == 255:
        none_tag = True
    else:
        none_tag = False

    # 更新坐标参数
    geo_transform = tifdata.geo_transform
    leftup_x = geo_transform[0] + startcol * geo_transform[1] + startrow * geo_transform[2]
    leftup_y = geo_transform[3] + startcol * geo_transform[4] + startrow * geo_transform[5]
    tile_geotrans = (leftup_x, geo_transform[1], geo_transform[2], leftup_y, geo_transform[4], geo_transform[5])

    # 生成geotiff对象
    tile = geotiffinfo(endrow - startrow, endcol - startcol, tifdata.bands, tile_geotrans, tifdata.projection,
                       tile_data, tifdata.epsg)

    return tile, none_tag

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

def rasterMosaic(tifpath,outfile,keywords):
    tiffiles = glob.glob(tifpath+'\\'+keywords+'*.tif')
    print(tiffiles)
    ref_raster = gdal.Open(tiffiles[0],gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    options = gdal.WarpOptions(srcSRS=ref_proj,dstSRS=ref_proj,format='GTiff',resampleAlg=gdalconst.GRA_Bilinear)
    gdal.Warp(outfile,tiffiles,options=options)

#
# tifpath = r'P:\imgdata\L51RGB'
# outfile = r'P:\imgdata\1111.tif'
# rasterMosaic(tifpath,outfile,keywords='*_Subset*')

