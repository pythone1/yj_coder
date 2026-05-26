import os,glob
import shutil
import zipfile
import xml.dom.minidom
import numpy as np

import imgprocess as imgpro

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
    imginfo['center_lon'] = (max(coords_x) + min(coords_x)) / 2
    imginfo['center_lat'] = (max(coords_y) + min(coords_y)) / 2

    return imginfo


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
    granulepath = os.path.join(safefile, 'GRANULE')
    l2apath = glob.glob(granulepath + '\\*')[0]
    r10path = os.path.join(l2apath, 'IMG_DATA', 'R10m')

    # extract certain img file
    tcifile = glob.glob(r10path + '\\*TCI*.jp2')[0]
    bfile = glob.glob(r10path + '\\*B02*.jp2')[0]
    gfile = glob.glob(r10path + '\\*B03*.jp2')[0]
    rfile = glob.glob(r10path + '\\*B04*.jp2')[0]
    nirfile = glob.glob(r10path + '\\*B08*.jp2')[0]

    # stack b,g,r,nir layers to generate REF10m products
    b = imgpro.geotiffread(bfile)
    g = imgpro.geotiffread(gfile)
    r = imgpro.geotiffread(rfile)
    nir = imgpro.geotiffread(nirfile)
    geotrans = b.geo_transform
    projection = b.projection
    ref10m = np.dstack((b.dataarray, g.dataarray, r.dataarray, nir.dataarray))
    imgpro.geotiffwrite(outfile_ref10m, ref10m, geotrans, projection, datatype="UINT16")

    # extract TCI as RGB products
    rgb = imgpro.geotiffread(tcifile).dataarray
    imgpro.geotiffwrite(outfile_rgb, rgb, geotrans, projection, datatype="UINT8")

    # read img info from xml file
    xmlfile = glob.glob(safefile+'\\MTD*.xml')[0]
    imginfo = getS2Imginfo(xmlfile)

    # remove unzipped files
    shutil.rmtree(safefile)

    return imginfo



# # test function
# xmlfile = r'D:\tmp1\S2B_MSIL2A_20221008T024609_N0400_R132_T50SQD_20221008T050713.SAFE\MTD_MSIL2A.xml'
# info = getS2Imginfo(xmlfile)
# print(info)