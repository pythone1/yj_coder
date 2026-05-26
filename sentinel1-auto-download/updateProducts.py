import os
import gc
import datetime,time
import subprocess
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
# import preprocess_S1 as s1pro

# python.exe文件所在路径，如果有多个版本的python，请注意对应的路径
python_exe_path = r'C:\ProgramData\Anaconda3\envs\snappyenv\python.exe'
# 要执行的python脚本文件
py_file_path = r'D:\pyMethod\snap\preprocess_S1.py'

def createAPI(user,password,site='https://scihub.copernicus.eu/dhus'):
    '''
    创建数据查询下载的API
    :param user: str 用户名
    :param password: str 密码
    :param site: str sichub官网
    :return: api sentinelsat.sentinel.SentinelAPI
    '''
    sentinel_api = SentinelAPI(user,password,site)

    return sentinel_api

def requestS1ProductsInfo(sentinel_api,footprint,daterange,product_type='GRD',sense_mode='IW',platform='Sentinel-1'):
    '''
    查询哨兵一号产品列表
    :param sentinel_api: sentinelsat.sentinel.SentinelAPI
    :param footprint: str wkt格式存储的区域范围
    :param daterange: list[str] 检索时间范围
    :param product_type: str 产品类型，可选 SLC GRD OCN RAW
    :param sense_mode: str 扫描模式，Sentinel-1可选 SLC, GRD, OCN
    :param platform: str 平台，默认Sentinel-1
    sentinel_api.query其他参数说明见
    https://link.csdn.net/?target=https%3A%2F%2Fscihub.copernicus.eu%2Ftwiki%2Fdo%2Fview%2FSciHub
    UserGuide%2FFullTextSearch%3Fredirectedfrom%3DSciHubUserGuide.3FullTextSearch
    :return products: collections.OrderedDict
    :return file_list: list[str] 查询的文件名列表
    '''

    products = sentinel_api.query(footprint,
                                  date=daterange,
                                  platformname=platform,
                                  producttype=product_type,
                                  sensoroperationalmode=sense_mode)

    return products

def downloadSentinelProducts(sentinel_api,products,savepath):
    '''
    下载产品
    :param sentinel_api: sentinelsat.sentinel.SentinelAPI
    :param products: collections.OrderedDict 待下载影像产品
    :param savepath: str 保存路径
    :return: list[str] 返回文件名
    '''
    os.chdir(savepath)
    try:
        sentinel_api.download_all(products)
        file_list = sentinel_api.to_dataframe(products)['title'].to_list()
        return file_list
    except Exception as e:
        print(e)
        return []


# 文件路径
grdfilepath = r'D:\tmp1\snappytest\s1_grd'
dbfilepath = r'D:\tmp1\snappytest\s1_grd_db1'
os.makedirs(dbfilepath,exist_ok=True)

# 创建sentinel api
user=''
password=''
sentinel_api = createAPI(user,password)

# 查询产品
# 区域
roi_file = r'D:\tmp1\snappytest\roi.geojson'
footprint = geojson_to_wkt(read_geojson(roi_file))
# 时间
ed_date = datetime.datetime.now()
st_date = ed_date + datetime.timedelta(days=-12)
daterange = (st_date.strftime('%Y%m%d'),ed_date.strftime('%Y%m%d'))
products = requestS1ProductsInfo(sentinel_api,footprint,daterange)

if len(products) > 0:
    # 下载产品
    # file_list = downloadSentinelProducts(sentinel_api,products,grdfilepath)
    file_list = ['S1A_IW_GRDH_1SDV_20230302T101158_20230302T101223_047464_05B2C8_E5DF',
                 'S1A_IW_GRDH_1SDV_20230309T100332_20230309T100357_047566_05B642_0C3A']

    if len(file_list) > 0:
        # 预处理
        zipfile_list = [os.path.join(grdfilepath,f+'.zip') for f in file_list]

        for zipfile in zipfile_list:
            print('processing %s ...' % zipfile)

            try:
                gc.enable()
                gc.collect()

                command = [python_exe_path, py_file_path, zipfile, dbfilepath, footprint]
                pipeline_out = subprocess.check_output(command, stderr=subprocess.STDOUT,shell=True)
                # 睡眠30s，以等待释放内存
                print("Sleeping...")
                time.sleep(30)
            except subprocess.CalledProcessError as e:
                out_bytes = e.output.decode()
                code = e.returncode
                print(code, out_bytes)
    # subprocess.check_output(['ls', '-l'])

