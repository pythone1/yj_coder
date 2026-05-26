import os
import copy
from osgeo import gdal, osr
import numpy as np
import matplotlib.pyplot as plt

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