import os
import glob

import cv2 as cv
import numpy as np
import rasterio as rio
from rasterio.mask import mask
from osgeo import gdal, osr,ogr,gdalconst
import geopandas as gpd
from rasterstats import zonal_stats
import fiona

import imgprocess as imgpro



os.environ['PROJ_LIB'] = r'F:\pycharm\Lib\site-packages\pyproj\proj_dir\share\proj'

'''
光学影像计算归一化水体指数
输入darray类型
返回darray类型-二值化矩阵
'''


def getNDWI(refdata):
    refdata = refdata.astype(np.float)
    nir = refdata[:, :, 3]
    g = refdata[:, :, 1]
    ndwi = (g - nir) / (g + nir)
    ndwi[ndwi > 0] = 1
    ndwi[ndwi <= 0] = 0
    return ndwi


'''
制作多时序归一化NDWI掩膜
输入文件路径
返回darray类型-二值化矩阵
'''


def more_NDWI(path):
    data_list = []
    os.chdir(path)
    tiffiles = glob.glob("*.tif")
    for tiffile in tiffiles:
        tif = imgpro.geotiffread(tiffile)
        data = tif.dataarray
        data_list.append(data)  # array写入list

    all = map(sum, zip(*data_list))  # 所有二值化矩阵相加,结果转出为array
    all_data = np.array(list(all))

    NDWIS = np.zeros_like(np.squeeze(all_data))
    rows, cols = NDWIS.shape
    for i in range(rows):
        for j in range(cols):
            if all_data[i, j] > 0:
                NDWIS[i, j] = 1

    return NDWIS


'''
矢量掩膜栅格
输入矢量.shp文件、栅格.tif文件
返回darray类型、元数据信息dict,key有driver、dtype、nodata、width、height、count、crs、transform
'''


def extract_from_shp(inshp, raster):
    with fiona.open(inshp, "r", encoding='utf-8') as shapefile:
        # 获取所有要素feature的形状geometry
        geoms = [feature["geometry"] for feature in shapefile]

    # 裁剪
    with rio.open(raster) as src:
        out_image, out_transform = mask(src, geoms, crop=True)
        out_meta = src.meta.copy()
    # 更新元数据
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})

    return out_image, out_meta


'''
波段运算作用是扩大水体与其他的差异
输入darray类型、指定极化波段索引
返回darray类型
注:rasterio库与imgprocess读取的shape有所不同
'''


def getSWI(SARdata, vh_idx, vv_idx):
    SARdata = SARdata.astype(np.float32)
    vv = SARdata[vv_idx, :, :]  # 使用rasterio.open方式读取时,波段索引在前
    vh = SARdata[vh_idx, :, :]
    # vv = SARdata[:,:,vv_idx]                 #使用imgprocess.geotiffread方式读取时,波段索引在后
    # vh = SARdata[:,:,vh_idx]
    vv[np.where(vv == 0)] = None
    vh[np.where(vh == 0)] = None  # 不计算背景值
    swi = 0.1747 * vv + 0.0082 * vv * vh + 0.0023 * (vv ** 2) - 0.0015 * (vh ** 2) + 0.1904
    return swi


'''
迭代阈值算法:T的差值变化趋于稳定
输入darray类型
返回阈值
'''


def IHT(data):
    vmin = np.min(data)  # 求出图像的最大灰度值和最小灰度值
    vmax = np.max(data)
    T0 = (vmax + vmin) / 2  # 将最大灰度值和最小灰度值的中间值设为初始阈值T0
    while True:
        avg1 = data[data > T0].mean().mean()  # 根据阈值T0将图像分割为两部分，分别求出两者的平均灰度值
        avg2 = data[data <= T0].mean().mean()
        T1 = (avg1 + avg2) / 2
        if abs(T1 - T0) <= 0:
            break
        else:
            T0 = T1

    return T0


'''
最大类方差算法
输入darray类型
返回阈值
'''


def otsu(data):
    value_min = np.min(data)  # 确定图像的灰度范围
    value_max = np.max(data)
    all_mean = data.mean()
    row = data.shape[0]
    col = data.shape[1]
    best_th = 0  # 初始阈值
    max_variance = 0.0  # 初始方差
    for th in np.arange(value_min, value_max):
        N1 = np.sum(data <= th)  # 小于阈值、大于阈值的像元数量
        N2 = np.sum(data > th)
        S1 = data[data <= th].sum()
        S2 = data[data > th].sum()
        M1 = S1 / N1  # 所有小于阈值这一类像元的灰度均值、所有大于阈值这一类像元的灰度均值
        M2 = S2 / N2
        P1 = N1 / (row * col)  # 两类的像元数量占比
        P2 = N2 / (row * col)
        V = P1 * ((M1 - all_mean) ** 2) + P2 * ((M2 - all_mean) ** 2)  # 类间方差
        if V > max_variance:
            best_th = th
            max_variance = V
    return best_th


'''
分块阈值分割
输入:darray类型、CropSize-窗口尺寸、RepetitionRate-重复率
返回darray类型--二值化矩阵
'''


def window_segment(swi_data, CropSize, RepetitionRate):
    height = swi_data.shape[0]
    width = swi_data.shape[1]
    segment = np.zeros_like(swi_data)

    # 窗口从左上角开始
    for i in range(int((height - CropSize * RepetitionRate) / (CropSize * (1 - RepetitionRate)))):  # 窗口在行的移动次数
        for j in range(int((width - CropSize * RepetitionRate) / (CropSize * (1 - RepetitionRate)))):  # 窗口在列的移动次数
            row = int(i * CropSize * (1 - RepetitionRate))
            col = int(j * CropSize * (1 - RepetitionRate))
            cropped = swi_data[row: row + CropSize, col: col + CropSize]
            subset = cropped.copy()
            if cropped.mean() <= 0:  # 若窗口取到无水区域则赋值为0
                window = np.zeros_like(subset)
                segment[row: row + CropSize, col: col + CropSize] = window
            else:
                threshold = IHT(cropped)  # 求当前窗口阈值
                # threshold=otsu(cropped)
                subset[subset < threshold] = 0
                subset[subset >= threshold] = 1
                segment[row: row + CropSize, col: col + CropSize] = subset

                # 窗口移动至向前最后一列
    for i in range(int((height - CropSize * RepetitionRate) / (CropSize * (1 - RepetitionRate)))):
        row = int(i * CropSize * (1 - RepetitionRate))
        cropped = swi_data[row: row + CropSize, (width - CropSize): width]
        subset = cropped.copy()
        if cropped.mean() <= 0:  # 若窗口取到无水区域则赋值为0
            window = np.zeros_like(subset)
            segment[row: row + CropSize, (width - CropSize): width] = window
        else:
            threshold = IHT(cropped)  # 求当前窗口阈值
            # threshold=otsu(cropped)
            subset[subset < threshold] = 0
            subset[subset >= threshold] = 1
            segment[row: row + CropSize, (width - CropSize): width] = subset

    # 窗口移动至向前最后一行
    for j in range(int((width - CropSize * RepetitionRate) / (CropSize * (1 - RepetitionRate)))):
        col = int(j * CropSize * (1 - RepetitionRate))
        cropped = swi_data[(height - CropSize): height, col: col + CropSize]
        subset = cropped.copy()
        if cropped.mean() <= 0:  # 若窗口取到无水区域则赋值为0
            window = np.zeros_like(subset)
            segment[(height - CropSize): height, col: col + CropSize] = window
        else:
            threshold = IHT(cropped)  # 求当前窗口阈值
            # threshold=otsu(cropped)
            subset[subset < threshold] = 0
            subset[subset >= threshold] = 1
            segment[(height - CropSize): height, col: col + CropSize] = subset

    return segment


'''
根据矢量单元统计水体像元占比,并将占比判断的结果转为栅格
输入darray类型、矢量.shp文件、affine坐标变换信息(rasterio库格式的六参数)、value占比取值
返回含占比字段的GeoDataFrame类型
注:矢量必须与影像投影一致
'''


def count_from_shp(segment, shp_file, affine, value):
    shpdata = gpd.read_file(shp_file)
    outshp = shpdata.copy()
    per = zonal_stats(shpdata, segment, affine=affine, stats=['mean'])  # 计算水体像元占比
    field1 = []  # 空字段用于存放水体像元占比、占比判断结果
    field2 = []
    for i in range(len(per)):
        if per[i]['mean'] is None:
            field1.append(0)
            field2.append(0)
        else:
            field1.append(per[i]['mean'])
            if per[i]['mean'] > value:
                field2.append(1)
            else:
                field2.append(0)
    outshp.insert(outshp.shape[1], 'per', field1)
    outshp.insert(outshp.shape[1], 'judge', field2)
    return outshp


'''
矢量转栅格
输入:refer_tif-参考栅格(用于读取投影，应用至新栅格)、shpfile-含占比字段的矢量、field-给栅格赋值的字段
raster:新栅格,.tif文件
'''


def shp2raster(refer_tif, shpfile, raster, field, filed_type=gdal.GDT_Byte):
    tifdata = gdal.Open(refer_tif, gdalconst.GA_ReadOnly)
    geo_transform = tifdata.GetGeoTransform()
    proj = tifdata.GetProjection()

    shp = ogr.Open(shpfile)
    shp_layer = shp.GetLayer()
    x_min, x_max, y_min, y_max = shp_layer.GetExtent()
    pixel_size = geo_transform[1]
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)
    target_ds = gdal.GetDriverByName('GTiff').Create(raster, x_res, y_res, 1, filed_type)
    target_ds.SetGeoTransform((x_min, pixel_size, 0.0, y_max, 0.0, -pixel_size))
    target_ds.SetProjection(proj)
    band = target_ds.GetRasterBand(1)
    band.SetNoDataValue(-9999)
    band.FlushCache()

    if field is None:
        gdal.RasterizeLayer(target_ds, [1], shp_layer, None)
    else:
        OPTIONS = ['ATTRIBUTE=' + field]
        gdal.RasterizeLayer(target_ds, [1], shp_layer, options=OPTIONS)

    target_ds = None


'''
tif格式生成图片
img_path:需要转为图片的影像路径
jpg_path:图片存放路径
(注:路径不支持中文)
'''


def create_picture(img_path, jpg_path):
    file_list = os.listdir(img_path)
    for i in range(len(file_list)):
        file = file_list[i]
        if file.endswith('.tif'):
            tiffile = os.path.join(img_path, file)
            tif = cv.imread(tiffile, 1)
            tif_convert = (tif * 255).astype(np.uint8)
            filename = file[3:11]  # 指定字符位置，截取文件名中的时间以命名新文件
            picture = os.path.join(jpg_path, filename + '.jpg')
            cv.imwrite(picture, tif_convert)


if __name__ == "__main__":
    # # 计算归一化ndwi
    # path=r'G:\1125\IMG\S2_resample_clip'
    # outpath=r'G:\1125\NDWI_WATER'
    # os.chdir(path)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     geotiff = imgpro.geotiffread(tiffile)
    #     data = geotiff.dataarray
    #     ndwi = getNDWI(data)
    #     outfile = os.path.join(outpath,tiffile[0:-4]+'_NDWI_WATER.tif')
    #     imgpro.geotiffwrite(outfile,ndwi,geotiff.geo_transform,geotiff.projection,datatype="UINT16")

    # 多时序归一化NDWI掩膜
    path = r'G:\1125\SAR坑塘水体识别测试数据\11期数据\NDWI_WATER'
    geotiff = imgpro.geotiffread(r'G:\1125\SAR坑塘水体识别测试数据\11期数据\NDWI_WATER\S2_20200426SPD_NDWI_WATER.tif')
    NDWIS = more_NDWI(path)
    imgpro.geotiffwrite(r'G:\1125\TEST.tif', NDWIS, geotiff.geo_transform, geotiff.projection, datatype="FLOAT32")

    # 矢量掩膜栅格
    # inshp=r'G:\1125\SAR坑塘水体识别测试数据\04按天地图坑塘单元判定\SHP\kengtang_TDT_water.shp'
    # tifpath=r'G:\1125\SAR坑塘水体识别测试数据\11期数据\S1_IMG'
    # savepath=r'G:\1125\0322'
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     outfile = os.path.join(savepath,tiffile[0:-4]+'_MASK.tif')
    #     out_raster,out_meta=extract_from_shp(inshp, tiffile)
    #     with rio.open(outfile, "w", **out_meta) as dest:
    #          dest.write(out_raster)

    # 先掩膜后计算SWI
    # tifpath = r'G:\1125\SAR坑塘水体识别测试数据\11期数据\S1_IMG'
    # inshp=r'G:\1125\SAR坑塘水体识别测试数据\04按天地图坑塘单元判定\SHP\kengtang_TDT_water.shp'
    # swi_path = r'G:\1125\0322'
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     geotiff = imgpro.geotiffread(tiffile)
    #     mask_data,new_meta=extract_from_shp(inshp,tiffile)
    #     geotrans = new_meta.get("transform")                   #掩膜后的六参数
    #     new_geotrans = (geotrans[2],geotrans[0],geotrans[1],geotrans[5], geotrans[3], geotrans[4]) #rasterio库六参数顺序与imgpro.geotiffread顺序不一致
    #     swi_data=getSWI(mask_data)
    #     swi_data[np.isnan(swi_data)]=0                        #nodata改写为0
    #     outfile = os.path.join(swi_path,tiffile[0:-4]+'_MASK_SWI.tif')
    #     imgpro.geotiffwrite(outfile,swi_data,new_geotrans,geotiff.projection,datatype="FLOAT32")

    # 直接计算SWI
    # tifpath = r'G:\1125\IMG\S1_resample_clip'
    # swi_path = r'G:\1125\SWI'
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     geotiff = imgpro.geotiffread(tiffile)
    #     sardata = geotiff.dataarray
    #     swi = getSWI(sardata)
    #     imgpro.geotiffwrite(os.path.join(swi_path,tiffile),swi,geotiff.geo_transform,geotiff.projection,datatype="FLOAT32")

    # # 滑动窗口阈值分割
    # tifpath = r'G:\1125\SAR坑塘水体识别测试数据\11期数据\S1_IMG'
    # outpath = r'G:\1125\0322'
    # inshp=r'G:\1125\SAR坑塘水体识别测试数据\04按天地图坑塘单元判定\SHP\kengtang_TDT_water.shp'
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     geotiff = imgpro.geotiffread(tiffile)
    #     mask_data,new_meta=extract_from_shp(inshp,tiffile)
    #     geotrans = new_meta.get("transform")
    #     new_geotrans = (geotrans[2],geotrans[0],geotrans[1],geotrans[5], geotrans[3], geotrans[4])
    #     swi_data=getSWI(mask_data)
    #     swi_data[np.isnan(swi_data)]=0
    #     outfile = os.path.join(outpath,tiffile[0:-4]+'_IHT50.tif')
    #     segment=window_segment(swi_data,50,0.1)
    #     imgpro.geotiffwrite(outfile,segment,new_geotrans,geotiff.projection,datatype="UINT8")

    # 占比矢量
    # tifpath = r'G:\1125\SAR坑塘水体识别测试数据\11期数据\S1_IMG'
    # outpath = r'G:\1125\0322'
    # inshp=r'G:\1125\SAR坑塘水体识别测试数据\04按天地图坑塘单元判定\SHP\kengtang_TDT_water.shp'
    # os.chdir(tifpath)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     filename=os.path.splitext(tiffile)[0]
    #     mask_data,new_meta=extract_from_shp(inshp,tiffile)
    #     geotrans = new_meta.get("transform")
    #     swi_data=getSWI(mask_data)
    #     swi_data[np.isnan(swi_data)]=0
    #     segment=window_segment(swi_data,50,0.1)
    #     outshp=count_from_shp(segment,inshp,geotrans,0.26)
    #     outfile = os.path.join(outpath,filename+'.shp')
    #     outshp.to_file(outfile)

    # # 栅格转图片
    # img_path=r'G:\1125\change'
    # jpg_path=r'G:\1125\change\JPG'
    # create_picture(img_path,jpg_path)