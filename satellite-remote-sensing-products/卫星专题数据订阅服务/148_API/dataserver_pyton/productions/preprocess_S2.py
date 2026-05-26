import os,glob
import shutil
import zipfile
import xml.dom.minidom
import numpy as np
import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject
from rasterio import crs
from rasterio.enums import Resampling

def unzipfile(filename):
    '''
    解压zip文件到源文件所在路径
    :param filename:
    :return:
    '''
    dstpath = os.path.dirname(filename)
    zip_file = zipfile.ZipFile(filename) # The class for reading and writing ZIP files
    zip_file.extractall(dstpath) # 将文件解压到zip文件所在路径

def getS2Imginfo(xmlfile):
    '''
    读xml文件
    :param xmlfile: str xml文件
    :return:
    '''
    imginfo = dict()
    dom = xml.dom.minidom.parse(xmlfile)
    root = dom.documentElement

    # 云覆盖量
    node = root.getElementsByTagName('Cloud_Coverage_Assessment')[0]
    imginfo['cld_pct'] = node.childNodes[0].data

    # 影像覆盖范围
    # 先取轨迹坐标
    node = root.getElementsByTagName('EXT_POS_LIST')[0]
    coords = node.childNodes[0].data.split(' ')
    # 再构建 geojson
    coords_x = coords[1::2]
    coords_x = [float(x) for x in coords_x]
    coords_y = coords[0:-1:2]
    coords_y = [float(x) for x in coords_y]
    coords = [[[float(coords_x[i]),float(coords_y[i])] for i in range(len(coords_y))]]
    imginfo['footprint'] = {"type": "FeatureCollection",
                            "features": [{
                                "id": "0",
                                "type": "Feature",
                                "properties": {"Id": 0},
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": coords
                                }}]}

    # 中心经纬度
    imginfo['center_lon'] = round((max(coords_x) + min(coords_x)) / 2,4)
    imginfo['center_lat'] = round((max(coords_y) + min(coords_y)) / 2,4)

    return imginfo

def getRGBProducts(safefile,outfile):
    '''
    生成RGB文件
    :param safefile: str 哨兵二号的解压文件
    :param outfile: str 输出文件
    :return:
    '''
    granulepath = os.path.join(safefile, 'GRANULE')
    l2apath = glob.glob(granulepath + '\\*')[0]
    r10path = os.path.join(l2apath, 'IMG_DATA', 'R10m')

    # extract certain img file
    tcifile = glob.glob(r10path + '\\*TCI*.jp2')[0]

    # extract TCI as RGB products
    rgb = rio.open(tcifile)
    RIOReproject(src_ds=rgb, dst_img=outfile, dst_crs=crs.CRS.from_epsg(4326))
    rgb.close()

def getRef10Products(safefile,outfile):
    '''
    生成10米反射率文件
    :param safefile: str 哨兵二号的解压文件
    :param outfile: str 输出文件
    :return:
    '''
    granulepath = os.path.join(safefile, 'GRANULE')
    l2apath = glob.glob(granulepath + '\\*')[0]
    r10path = os.path.join(l2apath, 'IMG_DATA', 'R10m')

    # extract certain img file
    bfile = glob.glob(r10path + '\\*B02*.jp2')[0]
    gfile = glob.glob(r10path + '\\*B03*.jp2')[0]
    rfile = glob.glob(r10path + '\\*B04*.jp2')[0]
    nirfile = glob.glob(r10path + '\\*B08*.jp2')[0]

    # stack b,g,r,nir layers to generate REF10m products
    b = rio.open(bfile)
    g = rio.open(gfile)
    r = rio.open(rfile)
    nir = rio.open(nirfile)
    ref10m_array = np.dstack((b.read(1), g.read(1), r.read(1), nir.read(1)))
    RIOReproject(src_ds=b,dst_img=outfile,
                 dst_crs=crs.CRS.from_epsg(4326),inplacedata=ref10m_array)
    b.close()
    g.close()
    r.close()
    nir.close()

def s2L2APreprocess(filename,outfile_rgb,outfile_ref10m):
    '''
    哨兵二号预处理：将从官网下载的s2_l2a产品进行解压，提取TCI文件作为RGB产品；对bgrnir进行波段合成作为10米反射率产品，然后删除解压文件
    :param filename:
    :param outfile_rgb:
    :param outfile_ref10m:
    :return:
    '''
    # unzipfile
    unzipfile(filename)

    # head to R10m path under unzipped file
    safefile = filename.replace('.zip', '.SAFE')

    # ref10m
    getRef10Products(safefile,outfile_ref10m)

    # rgb
    getRGBProducts(safefile,outfile_rgb)

    # read img info from xml file
    xmlfile = glob.glob(safefile+'\\MTD*.xml')[0]
    imginfo = getS2Imginfo(xmlfile)

    # remove unzipped files
    shutil.rmtree(safefile)

    return imginfo

def RIOReproject(src_ds,dst_img,dst_crs=crs.CRS.from_epsg(4326),inplacedata=None):
    '''
    利用rasterio做重投影
    :param src_ds: rasterio 读取的对象 输入影像
    :param dst_img: str 输出影像文件
    :param dst_crs: crs.CRS 输出坐标
    :param inplacedata: None时输出源影像中的栅格；否则输出该参数指定的栅格np.dataarray, 指定栅格长宽同源影像
    :return:
    '''
    # 计算在新空间参考系下的仿射变换参数，图像尺寸
    dst_transform, dst_width, dst_height = calculate_default_transform(
        src_ds.crs,  # 输入坐标系
        dst_crs,  # 输出坐标系
        src_ds.width,  # 输入图像宽
        src_ds.height,  # 输入图像高
        *src_ds.bounds)  # 输入数据源的图像范围

    # 确认待投影矩阵
    if inplacedata is not None:
        src_array0 = inplacedata
        if len(inplacedata.shape) == 2:
            bandsnum = 1
        else:
            bandsnum = inplacedata.shape[2]
    else:
        src_array0 = np.empty((src_ds.height,src_ds.width,src_ds.count))
        bandsnum = src_ds.count
        for i in range(1,1+bandsnum):
            src_array0[:,:,i-1] = src_ds.read(i)

    # 更新数据集的元数据信息
    profile = src_ds.meta.copy()
    profile.update({
        'crs': dst_crs,
        'driver': 'GTiff',
        'transform': dst_transform,
        'width': dst_width,
        'height': dst_height,
        'count': bandsnum
    })

    # 重投影并写入数据
    with rio.open(dst_img, 'w', **profile) as dst_ds:
        for i in range(1, bandsnum + 1):
            src_array = src_array0[:,:,i-1]
            dst_array = np.empty((dst_height, dst_width), dtype=profile['dtype'])  # 初始化输出图像数据

            # 重投影
            reproject(
                # 源文件参数
                source=src_array,
                src_crs=src_ds.crs,
                src_transform=src_ds.transform,
                # 目标文件参数
                destination=dst_array,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                # 其它配置
                resampling=Resampling.average,
                num_threads=2)
            # 写入图像
            dst_ds.write(dst_array, i)

    # 创建金字塔
    cmd_str = r'gdaladdo -ro ' + dst_img + ' 2 4 8 16'
    os.system(cmd_str)

# # test function
# xmlfile = r'D:\tmp1\S2B_MSIL2A_20221008T024609_N0400_R132_T50SQD_20221008T050713.SAFE\MTD_MSIL2A.xml'
# info = getS2Imginfo(xmlfile)
# print(info)