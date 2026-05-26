import json
import os,glob
import requests
import datetime
# from datetime import datetime, timedelta
import gc
import subprocess
import time
os.environ['PROJ_LIB'] = r"C:\Users\Administrator\.conda\envs\geoprocess\Lib\site-packages\osgeo\data\proj"

import pandas as pd
import numpy as np
import cv2

from sentinelrequest import *
from postgresql_opration import *
from mysql_operation import *
import imgprocess as imgpro
from preprocess_S2 import *
from waterQAProducts import identifyWaterarea,getWaterQA
from gaode_poi_server import searchPOIsAround
# from geerequest import *
os.environ['PROJ_LIB'] = r"C:\Users\Administrator\.conda\envs\geoprocess\Lib\site-packages\osgeo\data\proj"

def idtWatersOnStlImage(config):
    '''
    水域提取
    :param config: dict
    :return:
    '''
    # write results
    results = {
        'task_id': config['user']['task_id'],
        'url': '',
    }
    post_url = config['results']['post_url']
    # source file
    srcimg_info = config['srcimg_info']
    srcimg_filename = srcimg_info['filename']
    srcimg_filepath = srcimg_info['file_path']
    srcimg_file = os.path.join(srcimg_filepath,srcimg_filename)

    # identify water area
    try:
        t = srcimg_filename.split('.')[0].split('_')
        t[2] = 'l54syfb'
        t[5] = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        # t[6] = 'E%dN%d' % (config['user']['roi_cx'], config['user']['roi_cy'])
        basename = '_'.join(t)
        resultfile = os.path.join(config['savepath']['l54syfb'],basename+'.tif')
        identifyWaterarea(srcimg_file,resultfile,config)
    except:
        raise Exception('影像计算错误')

    # release processed data through geoscene
    try:
        # 控制台调用，使用另外一个python程序
        service_url = createGeoSceneService(config, service_name=basename,
                                            share_file=resultfile,
                                            service_type='img_service',
                                            tags=config['user']['prj_name'])
    except:
        raise Exception('服务发布错误')

    # create thumb file
    thumbfile = resultfile.replace('.tif', '.jpg')
    createThumbfile(thumbfile, resultfile, band_idx=[0])

    # edit imginfo
    imginfo = pd.DataFrame()
    # 沿用源影像元数据
    for k,v in srcimg_info.items():
        imginfo.loc[0,k] = v
    # 修改部分元数据
    imginfo.loc[0, 'produce_time'] = t[5]
    imginfo.loc[0, 'filename'] = basename + '.tif'
    imginfo.loc[0, 'thumbfile'] = basename + '.jpg'
    imginfo.loc[0, 'service_url'] = service_url
    imginfo.loc[0, 'ori_file'] = srcimg_file
    imginfo.loc[0, 'geometry'] = config['user']['roi_wkt']
    imginfo.loc[0, 'band_name'] = 'watermask'
    imginfo.loc[0, 'product_level'] = 'l54syfb'
    imginfo.loc[0, 'center_lon'] = config['user']['roi_cx']
    imginfo.loc[0, 'center_lat'] = config['user']['roi_cy']
    imginfo.loc[0, 'file_path'] = config['savepath']['l54syfb']
    imginfo.loc[0, 'prj_name'] = config['user']['prj_name']
    imginfo.loc[0, 'area_name'] = config['user']['roi_name']

    # insert imginfo to table
    try:
        dst_table = config['pgsql']['l54syfb_table']
        insertItems2Geotable(imginfo, dst_table, config['pgsql'])
    except:
        raise Exception('元数据入库失败')

    # put results
    results['url'] = service_url

    return postResults(post_url, results)

def idtWatersOnAerImage(config):
    results = {
        'task_id': config['user']['task_id'],
        'url': '',
    }
    post_url = config['results']['post_url']

    # source file
    srcimg_info = config['srcimg_info']
    srcimg_filename = srcimg_info['filename']
    srcimg_filepath = srcimg_info['file_path']
    srcimg_file = os.path.join(srcimg_filepath, srcimg_filename)

    # define result file
    t = srcimg_filename.split('_')
    t[2] = 'l54syfb'
    t[5] = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    t[6] = 'E%dN%d' % (config['user']['roi_cx'], config['user']['roi_cy'])
    basename = '_'.join(t)
    resultfile = os.path.join(config['savepath']['l54sd'], basename + '.tif')

    # 计算水域分布
    modelpath = config['model_idt_waters_aerial']['modelpath']
    pixelnum = config['model_idt_waters_aerial']['block_size']
    bufdist = config['model_idt_waters_aerial']['overlap']
    # 控制台调用,进行模型预测
    gc.enable()
    gc.collect()
    command = [config['python_exe']['paddlex_python_exe_path'],config['py_file']['paddlex_py_file_path'],
               srcimg_file, pixelnum, bufdist, modelpath, resultfile]
    pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)

    # release processed data through geoscene
    try:
        # 控制台调用，使用另外一个python程序
        service_url = createGeoSceneService(config, service_name=basename,
                                            share_file=resultfile,
                                            service_type='img_service',
                                            tags=config['user']['prj_name'])
    except:
        raise Exception('服务发布错误')

    # create thumb file
    thumbfile = resultfile.replace('.tif', '.jpg')
    createThumbfile(thumbfile, resultfile, band_idx=[0])

    # edit imginfo
    imginfo = pd.DataFrame()
    # 沿用源影像元数据
    for k, v in srcimg_info.items():
        imginfo.loc[0, k] = v
    # 修改部分元数据
    imginfo.loc[0, 'produce_time'] = t[5]
    imginfo.loc[0, 'filename'] = basename + '.tif'
    imginfo.loc[0, 'thumbfile'] = basename + '.jpg'
    imginfo.loc[0, 'service_url'] = service_url
    imginfo.loc[0, 'ori_file'] = srcimg_file
    imginfo.loc[0, 'band_name'] = 'watermask'
    imginfo.loc[0, 'product_level'] = 'l54syfb'
    imginfo.loc[0, 'file_path'] = config['savepath']['l54syfb']

    # insert imginfo to table
    try:
        dst_table = config['pgsql']['l54syfb_table']
        insertItems2Geotable(imginfo, dst_table, config['pgsql'])
    except:
        raise Exception('元数据入库失败')

    # put results
    results['url'] = service_url
    return postResults(post_url, results)

def waterqaSpecOnly(config):
    '''
    纯依靠光谱的水色指标计算
    :param config:
    :return:
    '''
    results = {
        'task_id': config['user']['task_id'],
        'url': '',
    }
    post_url = config['results']['post_url']
    print(config['srcimg_info'])
    # source file
    srcimg_info = config['srcimg_info']
    srcimg_filename = srcimg_info['filename']
    srcimg_filepath = srcimg_info['file_path']
    srcimg_file = os.path.join(srcimg_filepath, srcimg_filename)

    # define result file
    t = srcimg_filename.split('.')[0].split('_')
    t[5] = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    # t[6] = 'E%dN%d' % (config['user']['roi_cx'], config['user']['roi_cy'])
    if config['user']['product_type'] == '水色':
        t[2] = 'l54sd'
        band = 'sd'
        dst_table = config['pgsql']['l54sd_table']
        basename = '_'.join(t)
        savepath = config['savepath']['l54sd']
        resultfile = os.path.join(savepath, basename + '.tif')
    elif config['user']['product_type'] == '黑臭指数':
        t[2] = 'l54dbwi'
        band = 'dbwi'
        dst_table = config['pgsql']['l54dbwi_table']
        basename = '_'.join(t)
        savepath = config['savepath']['l54dbwi']
        resultfile = os.path.join(savepath, basename + '.tif')
    else:
        raise Exception('无对应参数模型')

    # 计算水色指数
    band_name = config['srcimg_info']['band_name'].replace(",", "")
    getWaterQA(srcimg_file, resultfile, config, band_name)

    # release processed data through geoscene
    try:
        # 控制台调用，使用另外一个python程序
        service_url = createGeoSceneService(config, service_name=basename,
                                            share_file=resultfile,
                                            service_type='img_service',
                                            tags=config['user']['prj_name'])
    except:
        raise Exception('服务发布错误')
    # create thumb file
    thumbfile = resultfile.replace('.tif', '.jpg')
    createThumbfile(thumbfile, resultfile, band_idx=[0])

    # edit imginfo
    imginfo = pd.DataFrame()
    # 沿用源影像元数据
    for k, v in srcimg_info.items():
        imginfo.loc[0, k] = v
    # 修改部分元数据
    imginfo.loc[0, 'produce_time'] = t[5]
    imginfo.loc[0, 'filename'] = basename + '.tif'
    imginfo.loc[0, 'thumbfile'] = basename + '.jpg'
    imginfo.loc[0, 'service_url'] = service_url
    imginfo.loc[0, 'ori_file'] = srcimg_file
    imginfo.loc[0, 'geometry'] = config['user']['roi_wkt']
    imginfo.loc[0, 'band_name'] = band
    imginfo.loc[0, 'product_level'] = t[2]
    imginfo.loc[0, 'center_lon'] = config['user']['roi_cx']
    imginfo.loc[0, 'center_lat'] = config['user']['roi_cy']
    imginfo.loc[0, 'file_path'] = savepath
    imginfo.loc[0, 'prj_name'] = config['user']['prj_name']
    imginfo.loc[0, 'area_name'] = config['user']['roi_name']

    # insert imginfo to table
    try:
        insertItems2Geotable(imginfo, dst_table, config['pgsql'])
    except:
        raise Exception('元数据入库失败')

    # put results
    results['url'] = service_url
    return postResults(post_url, results)

def waterqaRetrival(config):
    '''
    水质指标反演
    :param config:
    :return:
    '''
    pass

def s1Update(config):
    '''
    哨兵一号影像更新
    :return : 包含http状态返回代码code，运行记录msg和geoscene服务地址service_url 的HttpResponse
    '''
    # write results
    results = {
        'task_id': config['user']['task_id'],
        'message': '',
        'url': ''
    }
    post_url = config['results']['post_url']

    # generate scihub api
    sentinel_api = createAPI(config['scihub']['user'], config['scihub']['password'], config['scihub']['site'])
    # search img
    daterange = (config['user']['st_date'], config['user']['ed_date'])
    footprint = config['user']['roi_wkt']
    products = requestS1ProductsInfo(sentinel_api, footprint, daterange)
    products_num = len(products)
    if products_num == 0:
        results['message'] = '无影像更新'
        return postResults(post_url,results)
    msg = "查询到 %d 景影像;\n" % products_num
    print("查询到 %d 景影像;\n" % products_num)

    # download img
    try:
        file_list = downloadSentinelProducts(sentinel_api, products, config['savepath']['grd']) # 文件名，无路径
    except:
        msg = msg + "网络异常，下载失败;"
        raise Exception(msg)
    msg = msg + "所有影像下载成功;\n"
    print('影像下载完层')


    # preprocess: divide imgs into groups by date and mosaic the imgs sensed in one day during preprocessing
    dates = [x.split('_')[4][0:8] for x in file_list]   # 从S1A_IW_GRDH_1SDV_20230302T101158_20230302T101223_047464_05B2C8_E5DF 提取日期
    date_uni = list(set(dates))
    msg = msg + "按拍摄日期划分为 %d 组影像:\n" % len(date_uni)
    center_xy = 'E%sN%s'%(str(config['user']['roi_cx']).replace('.',''),
                          str(config['user']['roi_cy']).replace('.',''))
    imginfo = pd.DataFrame()    # 创建一个记录影像元数据的对象
    service_url_list = []
    for i,dstr in enumerate(date_uni):
        # divide img groups
        file_group = [f for f in file_list if dstr in f]
        file_group = [os.path.join(config['savepath']['grd'],f+'.zip') for f in file_group]
        file_group = ','.join(file_group)

        # 检查数据库中数据情况
        criteria_dict ={
            'st_date': dstr,
            'ed_date': dstr,
            'center_lon': config['user']['roi_cx'],
            'center_lat': config['user']['roi_cy'],
        }
        service_urls = checkProductsInDB(config['pgsql'],'grddb',criteria_dict)
        if len(service_urls) == 0:
            # preprocess by group
            date_now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
            # 命名规则：卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度
            basename = 's1_csar_grd_{0}_{0}_{1}_{2}'.format(dstr,date_now,center_xy)
            resultfile = os.path.join(config['savepath']['grddb'],basename+'.tif')
            try:
                print('processing %s ...' % dstr)
                # 控制台调用，目的为强制snap释放内存。(snap问题，批处理反复调用时，如果数据量大，可能很快就因为内存不能及时释放导致操作失败)
                gc.enable()
                gc.collect()
                command = [config['python_exe']['snappy_python_exe_path'],
                           config['py_file']['snappy_py_file_path1'], file_group, resultfile, footprint]
                pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
                # 睡眠30s，以等待释放内存
                print("Sleeping...")
                time.sleep(30)
                msg = msg + "%s 预处理完成... \n" % dstr
            except subprocess.CalledProcessError as e:
                out_bytes = e.output.decode()
                code = e.returncode
                print(code, out_bytes)
                msg = msg + "%s 预处理失败... \n" % dstr
                raise Exception(msg)

            # release processed data through geoscene
            try:
                # 控制台调用，使用另外一个python程序
                service_url = createGeoSceneService(config,service_name=basename,
                                                    share_file=resultfile,
                                                    service_type='img_service',
                                                    tags=config['user']['prj_name'])
                service_url_list.append(service_url)
                msg = msg + "%s 服务发布完成;\n" % dstr
            except:
                msg = msg + "%s 服务发布失败;\n" % dstr
                raise Exception(msg)

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
            imginfo.loc[i, 'ori_file'] = file_group
        else:
            service_url_list.extend(config['user']['roi_cx'])

    if len(imginfo)>0:
        imginfo['platform'] = 'sentinel1'
        imginfo['sensor'] = 'csar'
        imginfo['band_name'] = 'vh,vv'
        imginfo['product_level'] = 'grddb'
        imginfo['geometry'] = config['user']['roi_wkt']
        imginfo['center_lon'] = config['user']['roi_cx']
        imginfo['center_lat'] = config['user']['roi_cy']
        imginfo['file_path'] = config['savepath']['grddb']
        imginfo['image_gsd'] = 10
        imginfo['prj_name'] = config['user']['prj_name']
        imginfo['area_name'] = config['user']['roi_name']

        # insert imginfo to table
        try:
            tablename = config['pgsql']['grddb_table']
            insertItems2Geotable(imginfo,tablename,config['pgsql'])
        except:
            msg = msg + "元数据入库失败;\n"
            raise Exception(msg)

    results['message'] = '更新%d景影像'%products_num
    results['url'] = ','.join(service_url_list)
    response = postResults(post_url,results)

    return response

def s2Update(config):
    '''
    哨兵二号影像更新
    :return : 包含http状态返回代码code，运行记录msg和geoscene服务地址service_url 的HttpResponse
    '''
    # write results
    results = {
        'task_id': config['user']['task_id'],
        'message': '',
        'ref_url': '',
        'rgb_url': ''
    }
    post_url = config['results']['post_url']

    # generate scihub api
    sentinel_api = createAPI(config['scihub']['user'], config['scihub']['password'], config['scihub']['site'])
    # search img
    daterange = (config['user']['st_date'], config['user']['ed_date'])
    footprint = config['user']['roi_wkt']
    cloud = (config['user']['min_cldpct'], config['user']['max_cldpct'])
    products = requestS2ProductsInfo(sentinel_api, footprint, daterange,cloud=cloud)
    products_num = len(products)
    if products_num == 0:
        results['message'] = '无影像更新'
        return postResults(post_url, results)
    msg = "查询到 %d 景影像;\n" % products_num
    print("查询到 %d 景影像;\n" % products_num)

    # download img （已下载的不会重复下载）
    try:
        file_list = downloadSentinelProducts(sentinel_api, products, config['savepath']['l23'])
    except:
        msg = msg + "网络异常，下载失败;\n"
        raise Exception(msg)
    msg = msg + "所有影像下载成功;\n"
    print("影像下载完成")

    # preprocess: extract TCI img as RGB product, and stack g,b,r,nir layers to REF10m
    imginfo_rgb = pd.DataFrame()  # 创建一个记录影像元数据的对象
    imginfo_ref10 = pd.DataFrame()  # 创建一个记录影像元数据的对象
    rgb_service_url_list = []
    ref_service_url_list = []
    for i, f in enumerate(file_list):
        print('processing %s ...' % f)
        inputfile = os.path.join(config['savepath']['l23'], f + '.zip')

        # # 提取影像元数据
        # unzipfile(inputfile)
        # safefile = inputfile.replace('.zip', '.SAFE')
        # xmlfile = glob.glob(safefile + '\\MTD*.xml')[0]
        # imginfo = getS2Imginfo(xmlfile)

        # # 准备生成影像产品
        # sensedate = f.split('_')[2].split('T')[0] # 只取日期，不要时间
        # date_now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

        # # 检查数据库是否已有rgb数据,没有则生成
        # criteria_dict = {
        #     'ori_file': inputfile
        # }
        # rgb_service_urls = checkProductsInDB(config['pgsql'], 'l51rgb', criteria_dict)
        # if len(rgb_service_urls) == 0:
        if True:
            print('create products..')
            # 命名规则：卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度
            # basename_rgb = 's2_msi_l51rgb_{0}_{0}_{1}'.format(sensedate, date_now)
            basename_rgb = 's2_msi_l51rgb_20230408_20230408_20230502T144929'
            resultfile_rgb = os.path.join(config['savepath']['l51rgb'], basename_rgb + '.tif')
            # getRGBProducts(safefile,resultfile_rgb)
            # 发布服务
            print('sharing..')
            try:
                service_name='test2'
                rgb_service_url = createGeoSceneService(config, service_name=service_name,
                                                        share_file=resultfile_rgb,
                                                        service_type='tile_service',
                                                        tags=config['user']['prj_name'])
                print(rgb_service_url)
                rgb_service_url_list.append(rgb_service_url)
            except:
                raise Exception('%sRGB图层发布错误'%f)
            # 缩略图
            print('thumbfile..')
            thumbfile = resultfile_rgb.replace('.tif', '.jpg')
            createThumbfile(thumbfile, resultfile_rgb, band_idx=[0, 1, 2])
            # 影像信息
            imginfo_rgb.loc[i, 'thumbfile'] = thumbfile
            imginfo_rgb.loc[i, 'st_time'] = sensedate
            imginfo_rgb.loc[i, 'ed_time'] = sensedate
            imginfo_rgb.loc[i, 'produce_time'] = date_now
            imginfo_rgb.loc[i, 'filename'] = basename_rgb + '.tif'
            imginfo_rgb.loc[i, 'service_url'] = rgb_service_url
            imginfo_rgb.loc[i, 'ori_file'] = inputfile  # 含绝对路径
            imginfo_rgb.loc[i, 'cld_pct'] = imginfo['cld_pct']
            imginfo_rgb.loc[i, 'geometry'] = config['user']['roi_wkt']
        else:
            rgb_service_url_list.extend(rgb_service_urls)

        # 检查数据库是否已有ref数据,没有则生成
        ref_service_url = checkProductsInDB(config['pgsql'], 'l51ref', criteria_dict)
        if len(ref_service_url) == 0:
            print('creae products..')
            # 命名规则：卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度
            basename_ref10 = 's2_msi_l51ref_{0}_{0}_{1}'.format(sensedate, date_now)
            resultfile_ref10 = os.path.join(config['savepath']['l51ref'], basename_ref10 + '.tif')
            getRef10Products(safefile,resultfile_ref10)
            # 发布服务
            print('sharing..')
            try:
                ref_service_url = createGeoSceneService(config, service_name=basename_ref10,
                                                        share_file=resultfile_ref10,
                                                        service_type='img_service',
                                                        tags=config['user']['prj_name'])
                ref_service_url_list.append(ref_service_url)
            except:
                raise Exception('%s反射率影像服务发布错误'%f)
            # 缩略图
            print('thumbfile..')
            thumbfile = resultfile_ref10.replace('.tif', '.jpg')
            createThumbfile(thumbfile, resultfile_ref10, band_idx=[3, 2, 1])
            # 影像信息
            imginfo_ref10.loc[i, 'thumbfile'] = thumbfile
            imginfo_ref10.loc[i, 'st_time'] = sensedate
            imginfo_ref10.loc[i, 'ed_time'] = sensedate
            imginfo_ref10.loc[i, 'produce_time'] = date_now
            imginfo_ref10.loc[i, 'filename'] = basename_ref10 + '.tif'
            imginfo_ref10.loc[i, 'service_url'] = ref_service_url
            imginfo_ref10.loc[i, 'ori_file'] = inputfile  # 含绝对路径
            imginfo_ref10.loc[i, 'cld_pct'] = imginfo['cld_pct']
            imginfo_ref10.loc[i, 'geometry'] = config['user']['roi_wkt']
        else:
            ref_service_url_list.extend(rgb_service_urls)

    print('save imginfo to db..')
    # 如果有新增RGB影像，补充公共的影像信息后入库
    if len(imginfo_rgb) > 0:
        imginfo_rgb['platform'] = 'sentinel2'
        imginfo_rgb['sensor'] = 'msi'
        imginfo_rgb['band_name'] = 'r,g,b'
        imginfo_rgb['product_level'] = 'l51rgb'
        imginfo_rgb['center_lon'] = imginfo['center_lon']
        imginfo_rgb['center_lat'] = imginfo['center_lat']
        imginfo_rgb['tile_field'] = f.split('_')[5]
        imginfo_rgb['file_path'] = config['savepath']['l51rgb']
        imginfo_rgb['image_gsd'] = 10
        imginfo_rgb['prj_name'] = config['user']['prj_name']
        imginfo_rgb['area_name'] = config['user']['roi_name']
        try:
            rgb_table = config['pgsql']['l51rgb_table']
            insertItems2Geotable(imginfo_rgb, rgb_table, config['pgsql'])
        except:
            msg = msg + "元数据入库失败;\n"
            raise Exception(msg)

    # 如果有新增REF10影像，补充公共的影像信息后入库
    if len(imginfo_rgb) > 0:
        imginfo_ref10['platform'] = 'sentinel2'
        imginfo_ref10['sensor'] = 'msi'
        imginfo_ref10['band_name'] = 'g,b,r,nir'
        imginfo_ref10['product_level'] = 'l51ref'
        imginfo_ref10['center_lon'] = imginfo['center_lon']
        imginfo_ref10['center_lat'] = imginfo['center_lat']
        imginfo_ref10['tile_field'] = f.split('_')[5]
        imginfo_ref10['file_path'] = config['savepath']['l51ref']
        imginfo_ref10['image_gsd'] = 10
        imginfo_ref10['prj_name'] = config['user']['prj_name']
        imginfo_ref10['area_name'] = config['user']['roi_name']
        try:
            ref10_table = config['pgsql']['l51ref_table']
            insertItems2Geotable(imginfo_ref10, ref10_table, config['pgsql'])
        except:
            msg = msg + "元数据入库失败;\n"
            raise Exception(msg)

    # 处理结果推送
    results['message'] = '更新%d景影像' % products_num
    results['rgb_url'] = ','.join(rgb_service_url_list)
    results['ref_url'] = ','.join(ref_service_url_list)
    response = postResults(post_url, results)

    return response

def s3Update(config):
    '''
    哨兵三号影像更新
    :return : 包含http状态返回代码code，运行记录msg和geoscene服务地址service_url 的HttpResponse
    '''
    # write results
    results = {
        'task_id': config['user']['task_id'],
        'message': '',
        'url': ''
    }
    post_url = config['results']['post_url']

    # generate scihub api
    sentinel_api = createAPI(config['scihub']['user'], config['scihub']['password'], config['scihub']['site'])
    # search img
    daterange = (config['user']['st_date'], config['user']['ed_date'])

    daterange = ('20230512', '20230513')
    footprint = config['user']['roi_wkt']

    print('参数已获取：')
    print(daterange)
    products = requestS3ProductsInfo(sentinel_api, footprint, daterange)
    products_num = len(products)

    if products_num == 0:
        results['message'] = '无影像更新'
        return postResults(post_url, results)

    msg = "查询到 %d 景影像;\n" % products_num
    # download img
    try:
        print('下载到：',config['savepath']['l1'])
        file_list = downloadSentinel3Products(sentinel_api, products, config['savepath']['l1'])  # 文件名，无路径
    except:
        msg = msg + "网络异常，下载失败;"
        raise Exception(msg)
    msg = msg + "所有影像下载成功;\n"
    # print(msg)
    # preprocess: divide imgs into groups by date and mosaic the imgs sensed in one day during preprocessing
    dates = [x[16:31] for x in file_list]
    print(dates)
    date_uni = list(set(dates))
    msg = msg + "按拍摄日期划分为 %d 组影像:\n" % len(date_uni)
    # print(msg)
    center_xy = 'E%sN%s' % (str(config['user']['roi_cx']).replace('.', ''),
                            str(config['user']['roi_cy']).replace('.', ''))
    imginfo = pd.DataFrame()  # 创建一个记录影像元数据的对象
    service_url_list = []
    for i, dstr in enumerate(date_uni):
        file_group = [f for f in file_list if dstr in f]
        file_group = [os.path.join(config['savepath']['l1'], f + '.zip') for f in file_group]
        file_group = ','.join(file_group)
        # preprocess by group
        date_now = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
        # 命名规则：卫星_传感器_产品级别_拍摄开始时间_拍摄结束时间_产品制备时间_中心经纬度
        basename = 's3_olci_l1_{0}_{0}_{1}_{2}'.format(dstr, date_now, center_xy)
        resultfile = os.path.join(config['savepath']['l51rgb'], basename + '.tif')
        try:
            print('processing %s ...' % dstr)
            # 控制台调用，目的为强制snap释放内存。(snap问题，批处理反复调用时，如果数据量大，可能很快就因为内存不能及时释放导致操作失败)
            gc.enable()
            gc.collect()
            command = [config['python_exe']['snappy_python_exe_path'],
                       r'P:\dataserver_pyton\productions\preprocess_S3.py', file_group, resultfile, footprint]
            pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            # 睡眠30s，以等待释放内存
            print("Sleeping...")
            # time.sleep(30)
            msg = msg + "%s 预处理完成... \n" % dstr
            print(msg)
        except subprocess.CalledProcessError as e:
            out_bytes = e.output.decode()
            code = e.returncode
            print(code, out_bytes)
            msg = msg + "%s 预处理失败... \n" % dstr
            raise Exception(msg)

        # release processed data through geoscene
        try:
            # 控制台调用，使用另外一个python程序
            service_url = createGeoSceneService(config, service_name=basename,
                                                share_file=resultfile,
                                                service_type='tile_service',
                                                tags=config['user']['prj_name'])
            service_url_list.append(service_url)
            msg = msg + "%s 服务发布完成;\n" % dstr
        except:
            msg = msg + "%s 服务发布失败;\n" % dstr
            # raise Exception(msg)
            print(msg)

        # create icon file
        rgb_icon_file = resultfile.replace('.tif', '.jpg')
        print(resultfile)
        print(rgb_icon_file)
        rgbdata = imgpro.geotiffread(resultfile).dataarray
        t = rgbdata[:,:,0].copy()
        rgbdata[:, :, 0] = rgbdata[:, :, 2]
        rgbdata[:, :, 2] = t
        print(rgbdata)
        stretch_mode = "5%"
        rgbdata = imgpro.S3_ref2RGB(rgbdata, stretch_mode)
        rgb_icon = imgpro.addText2Img(rgbdata, 'SENTINEL-3 RGB ' + dstr)
        cv2.imwrite(rgb_icon_file, rgb_icon)

        # edit imginfo
        imginfo.loc[i, 'st_time'] = dstr
        imginfo.loc[i, 'ed_time'] = dstr
        imginfo['produce_time'] = date_now
        imginfo.loc[i, 'filename'] = basename + '.tif'
        imginfo.loc[i, 'thumbfile'] = rgb_icon_file
        # imginfo.loc[i, 'service_url'] = service_url
        imginfo.loc[i, 'ori_file'] = ','.join(file_group)

    imginfo['platform'] = 'sentinel3'
    imginfo['sensor'] = 'olci'
    imginfo['band_name'] = 'r,g,b'
    imginfo['product_level'] = 'l51rgb'
    imginfo['geometry'] = config['user']['roi_wkt']
    print(config['user']['roi_wkt'])
    imginfo['center_lon'] = config['user']['roi_cx']
    print(config['user']['roi_cx'])
    imginfo['center_lat'] = config['user']['roi_cy']
    print(config['user']['roi_cy'])
    imginfo['file_path'] = config['savepath']['l51rgb']
    imginfo['image_gsd'] = 300
    imginfo['prj_name'] = config['user']['prj_name']
    imginfo['area_name'] = config['user']['roi_name']

    # insert imginfo to table
    try:
        print(config['pgsql']['l51rgb_table'])
        tablename = config['pgsql']['l51rgb_table']
        insertItems2Geotable(imginfo, tablename, config['pgsql'])
        print('入库成功')
    except:
        msg = msg + "元数据入库失败;\n"
        raise Exception(msg)

    results['message'] = '更新%d景影像' % products_num
    results['url'] = ','.join(service_url_list)
    response = postResults(post_url, results)

    return response

def gaodePOI(config):
    '''
    高德POI数据获取
    :param config:
    :return:
    '''
    results = {
        'task_id': config['user']['task_id'],
        'message': '',
        'url': '',
    }
    post_url = config['results']['post_url']

    center_xy = str(config['user']['roi_cx']) + ',' + str(config['user']['roi_cy'])
    poi_type = config['user']['poi_type']
    distance = config['user']['distance']

    # # get poi
    # try:
    #     poi_gdf = searchPOIsAround(center_xy, poi_type, distance,config['gaode_poi']['key'])
    # except:
    #     raise Exception('查询失败')
    #
    # poi_num = len(poi_gdf)
    # results['message'] = '查询到%d笔数据'%poi_num
    # if poi_num==0:
    #     return postResults(post_url, results)

    # save to shpfile
    centerx_str = str(config['user']['roi_cx']).replace(".","")
    centery_str = str(config['user']['roi_cy']).replace(".", "")
    basename = '{}_{}_{}'.format(config['user']['prj_name'],
                                 config['user']['roi_name'],
                                 config['user']['poi_type'])
    resultfile = os.path.join(config['savepath']['poi'],basename+'.shp')
    # poi_gdf.to_file(resultfile,encoding='utf-8')

    # release geoscene service
    try:
        # 控制台调用，使用另外一个python程序
        service_url = createGeoSceneService(config, service_name=basename,
                                            share_file=resultfile,
                                            service_type='feature_service',
                                            tags=config['user']['prj_name'])
    except:
        raise Exception('服务发布错误')

    # # put results
    # results['url'] = service_url
    # response = postResults(post_url, results)
    #
    # return response

def getPrecipitation(config):
    '''
    降雨量数据查询
    :param config:
    :return:
    '''
    results = {
        'task_id': config['user']['task_id'],
        'message': '',
    }
    post_url = config['results']['post_url']

    # search data
    st_date=config['user']['st_date'][:4]+'-'+config['user']['st_date'][4:6]+'-'+config['user']['st_date'][6:8]
    ed_date=config['user']['ed_date'][:4]+'-'+config['user']['ed_date'][4:6]+'-'+config['user']['ed_date'][6:8]
    daterange = (st_date, ed_date)
    lat = config['user']['roi_cx']
    lon = config['user']['roi_cy']
    try:
        products = requestPrecipitationProductsInfo(daterange)
    except:
        raise Exception('查询失败')

    products_num = products.size().getInfo()
    results['message'] = '查询到%d笔数据' % products_num
    if products_num == 0:
        return postResults(post_url, results)

    # extract_precipitation
    precipitation_point = extract_precipitation(lat, lon, products)
    precipitation_point = {k[:14]: v for k, v in precipitation_point.items()}

    # save precipitation_point to database
    try:
        preinfo = pd.DataFrame()
        start_date = datetime.strptime(st_date, "%Y-%m-%d")
        end_date = datetime.strptime(ed_date, "%Y-%m-%d")
        for i in range((end_date - start_date).days):
            date = start_date +datetime.timedelta(days=i)
            preinfo.loc[i, 'prj_name'] = config['user']['prj_name']
            preinfo.loc[i, 'geometry'] = config['user']['roi_wkt']
            preinfo.loc[i, 'record_time'] = str(date)[:10]
            # 查找每日降雨数据
            result_key = [index for index in precipitation_point.keys() if
                          str(date.strftime("%Y%m%d")) in str(index)]
            precipitation_day = {key: precipitation_point[key] for key in result_key}
            preinfo.loc[i, 'precipitation_point'] = str(precipitation_day)

        # insert imginfo to table
        tablename = config['mysql']['precipitation_table']
        insertItems2mysql(preinfo, tablename, config['mysql'])
    except:
        raise Exception('数据提取或入库失败')

    # return task info
    return postResults(post_url, results)

def createGeoSceneService(config,service_name,share_file,service_type,tags):
    '''
    创建服务
    :param config: dict 运行参数
    :param service_name: str 服务名称
    :param share_file: str 共享文件名
    :param service_type: str 服务类型。可选img_service, map_service, feature_service, tile_service
    :return:
    '''
    exe_path = config['python_exe']['geoscene_python_exe_path']
    exe_dir,exe_file = os.path.split(exe_path)
    os.chdir(exe_dir)

    gc.enable()
    gc.collect()
    config_geoscene = config['geoscene']
    config_geoscene = json.dumps(config_geoscene, ensure_ascii=False)
    c = [exe_file,config['py_file']['geoscene_py_file_path'],
         config_geoscene, service_name, share_file, service_type,tags]
    pipeline_out = subprocess.check_output(c, stderr=subprocess.DEVNULL, shell=True)
    print(pipeline_out)
    service_url = str(pipeline_out.decode('UTF-8', 'strict'))
    return service_url

def createThumbfile(thumbfile,srcfile,band_idx):
    '''
    生成缩略图
    :param thumbfile: str 缩略图文件
    :param srcfile:  str 源文件
    :param band_idx: list[int] 可视化的波段索引
    :param falsecolor: bool 是否使用伪彩色
    :return:
    '''
    if len(band_idx) < 3:
        band_idx = band_idx[0:1]
    else:
        band_idx = band_idx[0:3]

    # 读图
    geotiff = imgpro.geotiffread(srcfile)
    dataarray = geotiff.dataarray
    subdataset = []
    for i in band_idx:
        subdataset.append(dataarray[:,:,i])
    subdataset = np.dstack(subdataset)
    del dataarray

    # 颜色增强
    if len(band_idx) == 3:
        result = imgpro.imgStretch(subdataset,'2%')
    else:
        result = gray2cmap(subdataset)

    # 背景处理为0
    result[subdataset[:,:,0]==0] = 0

    # 重采样
    result = cv2.resize(result,(256,256))

    # 写图
    cv2.imwrite(thumbfile,result)

def gray2cmap(img, minvalue=None, maxvalue=None, bkvalue=0, inverse=False):
    '''
    功能：灰度图转伪彩色
    img: np.array 灰度图
    minvalue: float 灰度图拉伸的最小值
    maxvalue: float 灰度图拉伸的最大值
    bkvalue：float 图像背景值
    inverse: bool 转伪彩色时色带是否反转 True 翻转 低值红色 高值蓝色；False 相反
    '''
    if maxvalue is None:
        maxvalue = np.nanmax(img)
    if minvalue is None:
        minvalue = np.nanmin(img)

    img_norm = ((img - minvalue) / (maxvalue - minvalue) * 254).astype(np.uint8)
    img_norm[img < minvalue] = 0
    img_norm[img > maxvalue] = 254

    if inverse:
        img_norm[img != bkvalue] = 254 - img_norm[img != bkvalue]

    img_norm[img != bkvalue] = img_norm[img != bkvalue] + 1

    img_cmap = cv2.applyColorMap(img_norm, cv2.COLORMAP_JET)

    return img_cmap

def checkProductsInDB(pg_config,product_level,criteria_dict):
    '''
    在数据库中检查产品情况
    :param pg_config: dict 连接数据库的参数
    :param product_level: str 产品类型/级别/数据表名称
    :param criteria_dict: dict 查询条件（等于）
    :return:
    '''
    criteria = ''
    for k,v in criteria_dict.items():
        criteria = criteria + '{}=\'{}\''.format(k,v) + ' and '
    criteria = criteria[0:-5]
    strsql = 'select service_url from {} where {}'.format(product_level,criteria)
    results, colnames = selectPgItems(pg_config, strsql)

    return results



def postResults(url,result_dict):
    '''
    将处理结果推送到指定位置
    :param result_dict: dict key为参数名称，value为返回值
    :return:
    '''
    data = json.dumps(result_dict,ensure_ascii=False).encode("utf-8")
    s = requests.session()
    s.trust_env = False
    response = s.post(url,headers={'content-type':'application/json'},data=data)

    return response


if __name__ == '__main__':
    # config_file = r'P:\task_configs\D20230423T094722.json' # 农田
    config_file = r'P:\task_configs\D20230414T094722.json'  # 水系
    # config_file = r'P:\task_configs\D20230414T094722.json' # gaode_poi task
    # config_file = r'P:\task_configs\D20230505T163122.json' # sentinel2 update task
    # config_file = r'P:\task_configs\D20230505T172800_pre.json' ##降雨
    # config_file = r'P:\task_configs\D20230517T144000.json'  ##水色
    # config_file = r'P:\task_configs\D20230502T180200.json'  ##GF
    # load parameters
    with open(config_file) as f:
        config = json.load(f)

    # 直接调用执行函数
    # s3Update(config)
    # s2Update(config)
    # s1Update(config)
    # gaodePOI(config)
    # idtWatersOnStlImage(config)
    # waterqaSpecOnly(config)
    # getPrecipitation(config)

    # 人工发布服务后，将服务地址推送到指定位置
    # url = config['results']['post_url']
    # result_dict = {
    #     'task_id': config['user']['task_id'],
    #     'url':'**'
    # }
    # postResults(url, result_dict)
    url = 'http://10.10.10.22:8698/external/imageInfoUrl'
    result_dict = {
        'task_id': config['user']['task_id'],
        'url': 'https://geoscene.ndww.gis/server/rest/services/Hosted/淮北市水管家_淮北_E116_841831N33_882703_waters/FeatureServer'
    }
    postResults(url, result_dict)

    # # 记录影像元数据，录入数据库
    # filename=r'P:\imgdata\L51RGB\gf6_pms_l51rgb_20201023_20201023_20230505T134325.tif'
    # imginfo = pd.DataFrame()
    # imginfo.loc[0, 'platform'] = filename.split('\\')[-1][:3]
    # imginfo.loc[0, 'sensor'] ='pms'
    # imginfo.loc[0, 'band_name'] ='r,g,b'
    # imginfo.loc[0, 'st_time'] = filename.split('\\')[-1][15:23]
    # imginfo.loc[0, 'ed_time'] = filename.split('\\')[-1][24:32]
    # imginfo.loc[0, 'scene_id'] = ''
    # imginfo.loc[0, 'product_id'] = ''
    # imginfo.loc[0, 'cld_pct'] = '0'
    # imginfo.loc[0, 'product_level'] ='l51rgb'
    # imginfo.loc[0, 'center_lon'] = '119.2'
    # imginfo.loc[0, 'center_lat'] = '32.8'
    # imginfo.loc[0, 'tile_field'] = ''
    # imginfo.loc[0, 'filename'] = filename.split('\\')[-1]
    # imginfo.loc[0, 'file_path'] = 'P:\imgdata\L51RGB'
    # imginfo.loc[0, 'thumbfile'] = filename.replace('tif','jpg')
    # imginfo.loc[0, 'produce_time'] = filename.split('\\')[-1][33:48]
    # imginfo.loc[0, 'geometry'] ='POLYGON ((119.46556 32.45361, 119.505 32.45278, 119.50444 32.42778, 119.46472 32.42861, 119.46556 32.45361))'
    # imginfo.loc[0, 'service_url'] ="D:\\Program Files\\GeoScene\\Pro\\bin\\Python\\envs\\arcgispro-py3\\lib\\site-packages\\urllib3\\connectionpool.py:1020: InsecureRequestWarning: Unverified HTTPS request is being made to host "geoscene.ndww.gis'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings\r\n  InsecureRequestWarning,\r\nD:\\Program Files\\GeoScene\\Pro\\bin\\Python\\envs\\arcgispro-py3\\lib\\site-packages\\urllib3\\connectionpool.py:1020: InsecureRequestWarning: Unverified HTTPS request is being made to host 'geoscene.ndww.gis". Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/1.26.x/advanced-usage.html#ssl-warnings\r\n  InsecureRequestWarning,\r\nhttps://geoscene.ndww.gis/server/rest/services/gf6_pms_l54dbwi_20201023_20201023_20230509T095328/ImageServer\r\n"
    #     # 'https://geoscene.ndww.gis/server/rest/services/Hosted/gf6_pms_l51rgb_20201023_20201023_20230505T134325_tif/MapServer'
    # imginfo.loc[0, 'image_gsd'] = '2'
    # imginfo.loc[0, 'ori_file'] = ''
    # imginfo.loc[0, 'prj_name'] = '遥感影像采集'
    # # imginfo.loc[0, 'area_name'] = config['user']['area_name']
    # imginfo.loc[0, 'area_name'] ='扬州市湾头镇'
    #
    # tablename = config['pgsql']['l51rgb_table']
    # insertItems2Geotable(imginfo, tablename, config['pgsql'])

    # 生成缩略图
    # imgfile = r'P:\imgdata\L51RGB\gf6_pms_l51rgb_20201023_20201023_20230505T134325.tif'
    # thumbfile = imgfile.replace('.tif','.jpg')
    # band_idx = [0,1,2] # 多波段影像中用来做可视化的三波段索引
    # # band_idx = [0] # 单波段影像
    # createThumbfile(thumbfile,imgfile,band_idx)

    # imginfo.loc[0, 'platform'] = config['user']['platform']
    # imginfo.loc[0, 'platform'] = 'gf'
    # imginfo.loc[0, 'sensor'] = config['user']['sensor']
    # imginfo.loc[0, 'sensor'] = 'pms'
    # imginfo.loc[0, 'band_name'] = 'r,g,b'
    # imginfo.loc[0, 'st_time'] = '20210401'
    # imginfo.loc[0, 'ed_time'] = '20210630'
    # imginfo.loc[0, 'scene_id'] = ''
    # imginfo.loc[0, 'product_id'] = ''
    # imginfo.loc[0, 'cld_pct'] = '0'
    # imginfo.loc[0, 'product_level'] = 'l51rgb'
    # imginfo.loc[0, 'center_lon'] = '118.842533'
    # imginfo.loc[0, 'center_lat'] = '31.927636'
    # imginfo.loc[0, 'tile_field'] = ''
    # imginfo.loc[0, 'filename'] = 'gf_pms_l51rgb_20210401_20210630_20211222_E118.842533N31.927636.tif'
    # imginfo.loc[0, 'file_path'] = 'P:\imgdata\L51RGB'
    # imginfo.loc[0, 'thumbfile'] = 'P:\imgdata\L51RGB\gf_pms_l51rgb_20210401_20210630_20211222_E118842533N31927636.jpg'
    # imginfo.loc[0, 'produce_time'] = '20211222T150213'
    # imginfo.loc[0, 'geometry'] = config['user']['roi_wkt']
    # imginfo.loc[
    #     0, 'service_url'] = 'https://geoscene.ndww.gis/server/rest/services/Hosted/gf_pms_l51rgb_20210401_20210630_20211222_E118_842533N31_927636_tif/MapServer'
    # imginfo.loc[0, 'image_gsd'] = '2'
    # imginfo.loc[0, 'ori_file'] = ''
    # imginfo.loc[0, 'prj_name'] = config['user']['prj_name']
    # # imginfo.loc[0, 'area_name'] = config['user']['area_name']
    # imginfo.loc[0, 'area_name'] = config['user']['roi_name']
    #
    # tablename = config['pgsql']['l51rgb_table']
    # insertItems2Geotable(imginfo, tablename, config['pgsql'])
    #
    # # 生成缩略图
    # imgfile = r'P:\imgdata\L51RGB\gf_pms_l51rgb_20210401_20210630_20211222_E118.842533N31.927636.tif'
    # thumbfile = imgfile.replace('.tif', '.jpg')
    # band_idx = [0, 1, 2]  # 多波段影像中用来做可视化的三波段索引
    # # band_idx = [0] # 单波段影像
    # createThumbfile(thumbfile, imgfile, band_idx)






