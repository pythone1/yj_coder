import os,glob
import gc
import subprocess
import time,datetime
import json

import cv2
import numpy as np
import pandas as pd
import geopandas as gpd
from django.http import HttpResponse

from initParameters import *
from sentinelrequest import createAPI,requestS1ProductsInfo,downloadSentinelProducts,requestS2ProductsInfo
from preprocess_S2 import s2L2APreprocess
from waterQAProducts import identifyWaterarea, waterQA
from postgresql_opration import selectPgItems
import imgprocess as imgpro

# python.exe文件所在路径，如果有多个版本的python，请注意对应的路径
snappy_python_exe_path = r'C:\Users\Administrator\.conda\envs\snappyenv\python.exe'
geoscene_python_exe_path = r'D:\Program Files\GeoScene\Pro\bin\Python\Scripts\propy'
# 要执行的python脚本文件
snappy_py_file_path = r'Q:\卫星专题数据订阅服务\sentinel1_update\qdApp\preprocess_S1.py'
geoscene_py_file_path = r'Q:\卫星专题数据订阅服务\sentinel1_update\qdApp\geoscene_server.py'

def s1Update(request):
    '''
    哨兵一号影像更新
    :return : 包含http状态返回代码code，运行记录msg和geoscene服务地址service_url 的HttpResponse
    '''
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # get parameters
    try:
        config = getS1UpdataParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # generate scihub api
    sentinel_api = createAPI(config['scihub']['user'], config['scihub']['password'], config['scihub']['site'])
    # search img
    daterange = (config['user']['st_date'], config['user']['ed_date'])
    footprint = config['user']['roi_wkt']
    products = requestS1ProductsInfo(sentinel_api, footprint, daterange)
    products_num = len(products)
    if products_num == 0:
        return HttpResponse(json.dumps(httpResult(200, "查询到 0 景影像"), ensure_ascii=False))
    msg = "查询到 %d 景影像;" % products_num
    # download img
    try:
        file_list = downloadSentinelProducts(sentinel_api, products, config['savepath']['grd'])
    except:
        msg = msg + "网络异常，下载失败;"
        return HttpResponse(json.dumps(httpResult(400, msg), ensure_ascii=False))
    msg = msg + "所有影像下载成功;"

    # preprocess: divide imgs into groups by date and mosaic the imgs sensed in one day during preprocessing
    dates = [x.split('_')[4][0:8] for x in file_list]   # 从S1A_IW_GRDH_1SDV_20230302T101158_20230302T101223_047464_05B2C8_E5DF 提取日期
    date_uni = list(set(dates))
    msg = msg + "按拍摄日期划分为 %d 组影像:" % len(date_uni)
    center_xy = 'E%dN%d'%(config['user']['roi_cx'],config['user']['roi_cy'])
    imginfo = pd.DataFrame()    # 创建一个记录影像元数据的对象
    for i,dstr in enumerate(date_uni):
        # divide img groups
        file_group = glob.glob(config['savepath']['grd']+'\\*'+dstr+"*.zip")
        file_group = ','.join(file_group)

        # preprocess by group
        date_now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        # 命名规则：卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度
        basename = 's1_csar_grd_{0}_{0}_{1}_{2}'.format(dstr,date_now,center_xy)
        resultfile = os.path.join(config['savepath']['db'],basename+'.tif')
        try:
            print('processing %s ...' % dstr)
            # 控制台调用，目的为强制snap释放内存。(snap问题，批处理反复调用时，如果数据量大，可能很快就因为内存不能及时释放导致操作失败)
            gc.enable()
            gc.collect()
            command = [snappy_python_exe_path, snappy_py_file_path, file_group, resultfile, footprint]
            pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            # 睡眠30s，以等待释放内存
            print("Sleeping...")
            time.sleep(30)
            msg = msg + "%s 预处理完成... " % dstr
        except subprocess.CalledProcessError as e:
            out_bytes = e.output.decode()
            code = e.returncode
            print(code, out_bytes)
            msg = msg + "%s 预处理失败... " % dstr
            return HttpResponse(json.dumps(httpResult(400, msg), ensure_ascii=False))

        # release processed data through geoscene
        try:
            # 控制台调用，使用另外一个python程序
            service_url = createGeoSceneService(config['geoscene'],service_name=basename,share_file=resultfile,service_type='img_service')
            msg = msg + "%s 服务发布完成;" % dstr
        except:
            msg = msg + "%s 服务发布失败;" % dstr
            return HttpResponse(json.dumps(httpResult(400, msg), ensure_ascii=False))

        # create thumb file
        thumbfile = resultfile.replace('.tif','.jpg')
        createThumbfile(thumbfile,resultfile,band_idx = [0])

        # edit imginfo
        imginfo.loc[i, 'st_time'] = dstr
        imginfo.loc[i, 'ed_time'] = dstr
        imginfo['produce_time'] = date_now
        imginfo.loc[i,'filename'] = basename+'.tif'
        imginfo.loc[i,'thumbfile'] = thumbfile
        imginfo.loc[i, 'service_url'] = service_url
        imginfo.loc[i, 'ori_file'] = ','.join(file_group)

    imginfo['platform'] = 'sentinel1'
    imginfo['sensor'] = 'csar'
    imginfo['band_name'] = 'vh,vv'
    imginfo['product_level'] = 'DB'
    imginfo['geometry'] = config['roi']
    imginfo['center_lon'] = config['roi_cx']
    imginfo['center_lat'] = config['roi_cy']
    imginfo['file_path'] = config['db_path']
    imginfo['image_gsd'] = 10
    imginfo['prj_name'] = config['prj_name']
    imginfo['area_name'] = config['roi_name']

    # insert imginfo to table
    # updataGeoTables(table_name,imginfo,config)

    return HttpResponse(json.dumps(httpResult(200, msg,service_url), ensure_ascii=False))

def s2Update(request):
    '''
    哨兵二号影像更新
    :return : 包含http状态返回代码code，运行记录msg和geoscene服务地址service_url 的HttpResponse
    '''
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # get parameters
    try:
        config = getS2UpdataParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # generate scihub api
    sentinel_api = createAPI(config['user']['user'], config['user']['password'], config['user']['site'])
    # search img
    daterange = (config['user']['st_date'], config['user']['ed_date'])
    footprint = config['user']['roi_wkt']
    cloud = (config['user']['min_cldpct'], config['user']['max_cldpct'])
    products = requestS2ProductsInfo(sentinel_api, footprint, daterange,cloud=cloud)
    products_num = len(products)
    if products_num == 0:
        return HttpResponse(json.dumps(httpResult(200, "查询到 0 景影像"), ensure_ascii=False))
    msg = "查询到 %d 景影像;" % products_num
    # download img
    try:
        file_list = downloadSentinelProducts(sentinel_api, products, config['savepath']['l23'])
    except:
        msg = msg + "网络异常，下载失败;"
        return HttpResponse(json.dumps(httpResult(400, msg), ensure_ascii=False))
    msg = msg + "所有影像下载成功;"

    # preprocess: extract TCI img as RGB product, and stack g,b,r,nir layers to REF10m
    center_xy = 'E%dN%d' % (config['user']['roi_cx'], config['user']['roi_cy'])
    imginfo_rgb = pd.DataFrame()  # 创建一个记录影像元数据的对象
    imginfo_ref = pd.DataFrame()  # 创建一个记录影像元数据的对象
    for i, f in enumerate(file_list):
        try:
            print('processing %s ...' % f)
            sensedate = f.split('_')[2]
            date_now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
            # 命名规则：卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度
            basename_rgb = 's2_msi_l51rgb_{0}_{0}_{1}_{2}'.format(sensedate, date_now, center_xy)
            basename_ref = 's2_msi_l51ref_{0}_{0}_{1}_{2}'.format(sensedate, date_now, center_xy)
            inputfile = os.path.join(config['l23_path'], f)
            resultfile_rgb = os.path.join(config['savepath']['l51rgb'], basename_rgb+'.tif')
            resultfile_ref = os.path.join(config['savepath']['l51ref'], basename_ref+'.tif')
            xmlinfo = s2L2APreprocess(inputfile, resultfile_rgb, resultfile_ref)
            msg = msg + "%s 预处理完成... " % f
        except Exception as e:
            print(e)
            msg = msg + "%s 预处理失败... " % f
            return HttpResponse(json.dumps(httpResult(400, msg), ensure_ascii=False))

        # release processed data through geoscene
        try:
            # 控制台调用，使用另外一个python程序
            rgb_service_url = createGeoSceneService(config['geoscene'], service_name=basename_rgb, share_file=resultfile_rgb,
                                                service_type='map_service')
            ref_service_url = createGeoSceneService(config['geoscene'], service_name=basename_ref, share_file=resultfile_ref,
                                                    service_type='img_service')
            msg = msg + "%s 服务发布完成;\ " % f
        except:
            msg = msg + "%s 服务发布失败;\ " % f
            return HttpResponse(json.dumps(httpResult(400, msg), ensure_ascii=False))

        # create thumb file
        thumbfile = resultfile_rgb.replace('.tif', '.jpg')
        createThumbfile(thumbfile, resultfile_rgb, band_idx=[0,1,2])
        thumbfile = resultfile_ref.replace('.tif', '.jpg')
        createThumbfile(thumbfile, resultfile_rgb, band_idx=[3, 2, 1])

        # edit imginfo
        imginfo_ref.loc[i, 'st_time'] = imginfo_rgb.loc[i, 'st_time'] = sensedate
        imginfo_ref.loc[i, 'ed_time'] = imginfo_rgb.loc[i, 'ed_time'] = sensedate
        imginfo_ref.loc[i, 'produce_time'] = imginfo_rgb['produce_time'] = date_now
        imginfo_rgb.loc[i, 'filename'] = basename_rgb + '.tif'
        imginfo_ref.loc[i, 'filename'] = basename_ref + '.tif'
        imginfo_rgb.loc[i, 'thumbfile'] = basename_rgb + '.jpg'
        imginfo_ref.loc[i, 'thumbfile'] = basename_ref + '.jpg'
        imginfo_rgb.loc[i, 'service_url'] = rgb_service_url
        imginfo_ref.loc[i, 'service_url'] = ref_service_url
        imginfo_ref.loc[i, 'ori_file'] = imginfo_rgb.loc[i, 'ori_file'] = inputfile
        imginfo_ref.loc[i, 'cld_pct'] = imginfo_rgb.loc[i, 'cld_pct'] = xmlinfo['cld_pct']
        imginfo_ref.loc[i, 'geometry'] = imginfo_rgb.loc[i, 'geometry'] = xmlinfo['footprint']

    imginfo_ref['platform'] = imginfo_rgb['platform'] = 'sentinel2'
    imginfo_ref['sensor'] = imginfo_rgb['sensor'] = 'msi'
    imginfo_rgb['band_name'] = 'r,g,b'
    imginfo_ref['band_name'] = 'g,b,r,nir'
    imginfo_rgb['product_level'] = 'l51rgb'
    imginfo_ref['product_level'] = 'l51ref'
    imginfo_ref['center_lon'] = imginfo_rgb['center_lon'] = xmlinfo['center_lon']
    imginfo_ref['center_lat'] = imginfo_rgb['center_lat'] = xmlinfo['center_lat']
    imginfo_ref['tile_field'] = imginfo_rgb['center_lat'] = f.split('_')[5]
    imginfo_rgb['file_path'] = config['savepath']['l51rgb']
    imginfo_ref['file_path'] = config['savepath']['l51ref']
    imginfo_ref['image_gsd'] = imginfo_rgb['image_gsd'] = 10
    imginfo_ref['prj_name'] = imginfo_rgb['prj_name'] = config['user']['prj_name']
    imginfo_ref['area_name'] = imginfo_rgb['area_name'] = config['user']['roi_name']

    # insert imginfo to table
    # updataGeoTables(table_name,imginfo,config)

    service_url = ','.join(rgb_service_url,ref_service_url)
    return HttpResponse(json.dumps(httpResult(200, msg, service_url), ensure_ascii=False))

def createWaterareaProduct(request):
    '''
    水域提取
    :param request: 包含http状态返回代码code，运行记录msg和geoscene服务地址service_url 的HttpResponse
    :return:
    '''
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # get parameters
    try:
        config = getIdtWaterParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # find rgb or ref img file
    try:
        srctable = config['user']['srctable']
        srcimg_url = "\'" + config['user']['srcimg_url'] + "\'"
        strsql = 'SELECT filename,file_path FROM {} WHERE service_url={}'.format(srctable,srcimg_url)
        results = selectPgItems(config['pgsql'],strsql) # list[(filename,file_path),(filename,file_path)]形式的查询结果
    except:
        return HttpResponse(json.dumps(httpResult(400, "数据文件索引错误"), ensure_ascii=False))

    # identify water area
    try:
        srcfiles = [r[0] for r in results]
        srcpathes = [r[1] for r in results]
        # 按数据源类型、拍摄日期分组进行水域提取
        fids = ['_'.join(f.split('_')[0:3]+f.split('_')[3].split('T')) for f in srcfiles]
        fids = list(set(fids))
        for fid in fids:
            file_group = []
            for i,f in enumerate(srcfiles):
                if fid in f:
                    file_group.append(os.path.join(srcpathes[i],f))

            # 提取水域
            resultfile = file_group[0].split('_')
            # resultfile[2] = 'l54syfb'
            identifyWaterarea(file_group,resultfile)
    except:
        return HttpResponse(json.dumps(httpResult(400, "影像计算错误"), ensure_ascii=False))

    # release processed data through geoscene
    try:
        # 控制台调用，使用另外一个python程序
        # createGeoSceneService(config['geoscene'], service_name, share_file, service_type)
        pass
    except:
        return HttpResponse(json.dumps(httpResult(400, "服务发布错误"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(400, "产品制备完成",service_url), ensure_ascii=False))


def createWaterQAProduct(request):
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    # get parameters
    try:
        config = getIdtWaterQAParams(request)
    except:
        return HttpResponse(json.dumps(httpResult(400, "参数错误"), ensure_ascii=False))

    # find rgb or ref img file
    try:
        imgfile = searchImgfile(config['satellite'],config['productid'])
    except:
        return HttpResponse(json.dumps(httpResult(400, "数据文件索引错误"), ensure_ascii=False))

    # identify water area
    try:
        product_type = config['product_type']
        basename = os.path.basename(imgfile).replace('.tif','_{}.tif'.format(product_type))
        resultfile = os.path.join(config['savepath'],basename)
        waterQA(imgfile,resultfile,product_type)
    except:
        return HttpResponse(json.dumps(httpResult(400, "影像计算错误"), ensure_ascii=False))

    # release processed data through geoscene
    try:
        # 控制台调用，使用另外一个python程序
        gc.enable()
        gc.collect()
        config_str = json.dumps(config, ensure_ascii=False)
        servicename = basename
        command = [geoscene_python_exe_path, geoscene_py_file_path, config_str, servicename, resultfile,
                   "img_service"]
        pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        service_url = str(pipeline_out.decode('UTF-8', 'strict'))
        # 睡眠30s，以等待释放内存
        print("Sleeping...")
        time.sleep(30)
    except:
        return HttpResponse(json.dumps(httpResult(400, "服务发布错误"), ensure_ascii=False))

    return HttpResponse(json.dumps(httpResult(400, "产品制备完成",service_url), ensure_ascii=False))

def httpResult(code,msg,service_url=""):
    res = dict()
    res["code"] = code
    res["msg"] = msg
    res["service_url"] = service_url

    return res

def test(request):
    if request.method == "POST":
        return HttpResponse(json.dumps(httpResult(400, "不支持POST方法"), ensure_ascii=False))

    prjname = request.GET.get("prjname")
    print(prjname)
    stdate = request.GET.get("stdate")
    eddate = request.GET.get("roi")

    return HttpResponse(json.dumps(httpResult(prjname, stdate,eddate), ensure_ascii=False))

def createGeoSceneService(config,service_name,share_file,service_type):
    '''
    创建服务
    :param config: dict 运行参数
    :param service_name: str 服务名称
    :param share_file: str 共享文件名
    :param service_type: str 服务类型。可选img_service, map_service, feature_service, tile_service
    :return:
    '''
    gc.enable()
    gc.collect()
    config_str = json.dumps(config, ensure_ascii=False)
    command = [geoscene_python_exe_path, geoscene_py_file_path, config_str, service_name, share_file, service_type]
    pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    service_url = str(pipeline_out.decode('UTF-8', 'strict'))
    # 睡眠30s，以等待释放内存
    print("Sleeping...")
    time.sleep(30)

    return service_url

def createThumbfile(thumbfile,srcfile,band_idx):
    '''
    生成缩略图
    :param thumbfile: str 缩略图文件
    :param srcfile:  str 源文件
    :param band_idx: list[int] 可视化的波段索引
    :return:
    '''
    if len(band_idx) < 3:
        band_idx = band_idx[0:1]
    else:
        band_idx = band_idx[0:3]

    geotiff = imgpro.geotiffread(srcfile)
    dataarray = geotiff.dataarray
    subdataset = []
    for i in band_idx:
        subdataset.append(dataarray[:,:,i])
    subdataset = np.dstack(subdataset)
    del dataarray
    subdataset = imgpro.imgStretch(subdataset,'2%')
    rows,cols = subdataset.shape[0:2]
    fx = round(256 * 1.0 / rows,4)
    fy = round(256 * 1.0 / cols,4)
    subdataset = cv2.resize(subdataset,fx,fy)
    cv2.imwrite(thumbfile,subdataset)

# if __name__ == '__main__':
#     try:
#         service_name = 'imgsrvtest14'
#         imgfile = r'J:\研究数据\20230223geoscene自动发布地图服务测试\testdata\S2B_MSIL2A_20230225T024709_N0509_R132_T50SPD_20230225T051442_DBWI.tif'
#
#         command = [geoscene_python_exe_path, geoscene_py_file_path, config, service_name, imgfile, "img_service"]
#         pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
#     except subprocess.CalledProcessError as e:
#         out_bytes = e.output.decode()
#         code = e.returncode
#         print(code, out_bytes)
