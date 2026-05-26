from snappy import ProductIO, HashMap, GPF,jpy
import sys,snappy,cv2,os,glob
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal, osr,ogr,gdalconst
import imgprocess as imgpro
import zipfile

def unzip_and_get_folder_path(zip_file_path):
    # 获取压缩文件所在目录
    zip_dir = os.path.dirname(zip_file_path)

    # 解压文件到压缩文件所在目录
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(zip_dir)

    # 生成解压后的文件夹名
    folder_name = os.path.splitext(os.path.basename(zip_file_path))[0]
    folder_path = os.path.join(zip_dir, folder_name +'.SEN3')
    print(folder_path)
    return folder_path


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


def rasterMosaic(tifpath, outfile, keywords):
    tiffiles = glob.glob(tifpath + '\\' + keywords + '*.tif')
    print(tiffiles)
    ref_raster = gdal.Open(tiffiles[0], gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()

    # 将选项更改为字符串列表形式
    options = [
        'SRC_SRS=' + ref_proj,
        'DST_SRS=' + ref_proj,
        'FORMAT=GTiff',
        'RESAMPLE_ALG=BILINEAR'
    ]

    gdal.Warp(outfile, tiffiles, options=options)

# 反射率（16位4波段）转RGB（8位3波段）,2% | 5%线性拉伸(stretch_mode = "2%" |stretch_mode =  "5%")
def ref2RGB(data,stretch_mode):
    '''
    rgb拉伸
    :param:data: np.array ref矩阵
    :param:stretch_mode:str 1% | 2% | 5%线性拉伸
    '''
    for i in range(3):
        t = data[:,:,i]
        t_st,t_ed = imgpro.getBreakpointsByLinear(t,mode=stretch_mode)
        t[t < t_st] = t_st
        t[t > t_ed] = t_ed
        t = (t - t_st) / (t_ed - t_st) * 254 + 1  # 有效值的映射范围 [1,255]
        t[data[:, :, i] == 0] = 0  # 背景值设0
        data[:, :, i] = t.copy()
    return data


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
def readS3OLCIProduct(s3_path):
    """
    读取S3 OLCI产品
    :param s3_path: str, S3 OLCI产品路径
    :return: org.esa.snap.core.datamodel.Product
    """
    try:
        print('\tReading Sentinel-3 zip file...')
        prod = ProductIO.readProduct(s3_path)
    except IOError:
        print("错误：SNAP无法读取指定的文件！")
        return None

    return prod

def subsetToGeoRegion(product,wkt,source_bands):
    '''
    按地理坐标范围裁剪
    :param product: org.esa.snap.core.datamodel.Product
    :param wkt: The subset region in geographical coordinates using WKT-format,
    e.g. POLYGON((<lon1> <lat1>, <lon2> <lat2>, ..., <lon1> <lat1>))
    :return: org.esa.snap.core.datamodel.Product
    '''
    print('\tSubset...')
    params = HashMap()
    params.put("sourceBands", source_bands)
    params.put('copyMetadata', True)
    params.put('geoRegion', wkt)
    print(product)
    results = GPF.createProduct('Subset', params, product)

    return results

def subsetToRectangle(product, x, y, width, height, source_bands):
    """
    矩形框裁剪
    :param product: org.esa.snap.core.datamodel.Product
    :param x: int, 起始列坐标
    :param y: int, 起始行坐标
    :param width: int, 宽度
    :param height: int, 高度
    :param source_bands: str, 要裁剪的波段名称列表，以逗号分隔，如"Oa08_radiance,Oa06_radiance,Oa04_radiance"
    :return: org.esa.snap.core.datamodel.Product
    """
    parameters = HashMap()
    parameters.put("sourceBands", source_bands)
    parameters.put("region", "%s,%s,%s,%s" % (x, y, width, height))
    parameters.put("subSamplingX", "1")
    parameters.put("subSamplingY", "1")
    parameters.put("copyMetadata", "true")

    # 执行裁剪操作
    results = GPF.createProduct("Subset", parameters, product)

    return results

def reprojectProduct(product, crs):
    """
    投影
    :param product: org.esa.snap.core.datamodel.Product
    :param crs: str, 投影坐标系，如'EPSG:4326'
    :return: org.esa.snap.core.datamodel.Product
    """
    parameters = HashMap()
    parameters.put("crs", crs)
    parameters.put("resampling", "Nearest")
    parameters.put("noDataValue", "NaN")
    parameters.put("orthorectify", "true")
    parameters.put("includeTiePointGrids", "true")
    parameters.put("addDeltaBands", "false")
    parameters.put("copyMetadata", "true")

    # 执行投影操作
    results = GPF.createProduct("Reproject", parameters, product)

    return results

def selectBands(product, source_bands):
    """
    选择导出波段
    :param product: org.esa.snap.core.datamodel.Product
    :param source_bands: str, 要选择的波段名称列表，以逗号分隔，如"Oa08_radiance,Oa06_radiance,Oa04_radiance"
    :return: org.esa.snap.core.datamodel.Product
    """
    parameters = HashMap()
    parameters.put("sourceBands", source_bands)

    # 执行选择操作
    results = GPF.createProduct("BandSelect", parameters, product)

    return results

def writeProductToFile(product, output_file):
    """
    将Product写入到文件
    :param product: org.esa.snap.core.datamodel.Product
    :param output_file_path: str, 输出文件路径
    :return: None
    """
    ProductIO.writeProduct(product, output_file, "GeoTIFF")



def write2File(savefile,product_list,format='GeoTIFF'):
    '''
    写出
    :param filename: str
    :param product: org.esa.snap.core.datamodel.Product
    :param format: str
    :return: None
    '''
    print("Writing...")
    file_dir = os.path.dirname(savefile)

    incremental = False
    if len(product_list) ==1:
        snappy.GPF.writeProduct(product_list[0], snappy.File(savefile), format, incremental, snappy.ProgressMonitor.NULL)
    else:
        for i,product in enumerate(product_list):
            savefile_Subset = file_dir + '\\' + str(i) + '_Subset.tif'
            GPF.writeProduct(product_list[i], snappy.File(savefile_Subset), format, incremental, snappy.ProgressMonitor.NULL)
        #进行镶嵌
        print(savefile)
        rasterMosaic(file_dir, savefile, keywords='*_Subset*')
        #删除镶嵌的_Subset文件
        removefiles_list = glob.glob(file_dir+'\\'+'*_Subset.tif')
        for removefile in removefiles_list:
            os.remove(removefile)


def preprocessing(file_list,savefile,dest_rigon=None):
    '''
    哨兵三影像预处理
    :param:file_list: str 解压文件存放路径
    :param:Sentinel3_path: str 哨兵三影像存放路径
    :param:dest_rigon:list或wkt 需要显示的范围 可以是[500,500,1000,1000],或wkt
    :param:savepath: str 预处理影像保存路径
    '''
    print('开始预处理')
    product_list = []
    for i in range(len(file_list)):
        # 读取S3 OLCI产品
        print(file_list[i])
        outfile = unzip_and_get_folder_path(file_list[i])
        prod = readS3OLCIProduct(outfile)
        print('读取完成')
        # 创建子集，选择RGB三个波段,矩形框裁剪小范围，这里写死
        source_bands = "Oa08_radiance,Oa06_radiance,Oa04_radiance"
        if dest_rigon:
            if isinstance(dest_rigon, list):
                # 裁剪
                x, y, width, height = dest_rigon[0],dest_rigon[1],dest_rigon[2],dest_rigon[3]
                prod_clipBands = subsetToRectangle(prod, x, y, width, height, source_bands)
                print('裁剪完成')
            #wtk裁剪
            elif isinstance(dest_rigon,str):
                wkt = dest_rigon
                prod_clipBands = subsetToGeoRegion(prod, wkt, source_bands)
                print('裁剪完成')
        #创建子集,进行重投影
        crs = '4326'
        reproj_prod = reprojectProduct(prod_clipBands, crs)
        print('重投影完成')
        #创建子集，筛选导出的波段
        prod_RGBBands = selectBands(reproj_prod, source_bands)
        product_list.append(prod_RGBBands)
        print('选择波段完成')
    print(savefile)
    print(product_list)
    # savefile = r'F:\API_148\imgdata\L51RGB\1.tif'
    write2File(savefile, product_list, format='GeoTIFF')
    print('导出完成')

file_group = sys.argv[1]
savefile = sys.argv[2]
dest_rigon = sys.argv[3]

file_list = file_group.split(',')
print(file_list)
print(savefile)
# dest_rigon = [1000, 2000, 3000, 3000]
preprocessing(file_list,savefile,dest_rigon)

# if __name__ == '__main__':
#     #预处理,导出RGB图像及快试图
#     file_list = [r'F:\API_148\imgdata\L1\S3A_OL_1_EFR____20230410T020615_20230410T020915_20230410T040440_0179_097_274_2340_PS1_O_NR_003.zip']
#     savefile = r'F:\API_148\imgdata\L1\1.tif'
#     dest_rigon = [1000, 2000, 3000, 3000]
#     preprocessing(file_list, savefile, dest_rigon)
    # 矩形框裁剪
    # dest_rigon = [1000,2000,3000,3000]
    # preprocessing(file_list, dest_rigon, savepath)
    # 下载example
    # api = download.createAPI(user='yj980202', password='s821472144')
    # geojsonPath = r'E:\PY\Sentinel-3\xuwei_map.geojson'
    # footprint = geojson_to_wkt(read_geojson(geojsonPath))
    # daterange = ('20221227', '20221228')
    # products = download.requestS3ProductsInfo(api, footprint, daterange, product_type='OL_1_EFR___', platform='Sentinel-3')
    # savepath = r'E:\PY\Sentinel-3'
    # file_list = download.downloadSentinelProducts(api, products, savepath)
    # #





