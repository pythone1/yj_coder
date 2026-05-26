import os
import json
import configparser

import geopandas as gpd

from .pgsql import selectPgItems

os.environ['PROJ_LIB'] = r"C:\Users\Administrator\.conda\envs\geoprocess\Lib\site-packages\osgeo\data\proj"

CONFIGS = dict()
cp = configparser.ConfigParser()
# cp.read(r"P:\dataserver_python\createtask\qdApp\config.ini",encoding="utf-8")
cp.read("config.ini",encoding="utf-8")

d = dict(cp._sections)
for k in d:
    CONFIGS[k] = dict(d[k])

def getWtVctParams(request):
  '''
  获取程序运行所需参数
  :param request: HttpRequest对象
  :return: dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['obj'] = request.GET.get("obj")
  config['user']['fields'] = request.GET.get("fields")
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  try:
    config['user']['refimg'] = json.loads(request.GET.get("refimg"))
  except:
    pass
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)
  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['water_vectors'], exist_ok=True)
  return config

def getIdtWatersOnStlImageParams(request):
  '''
  获取程序运行所需参数
  :param request: HttpRequest对象
  :return: dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['srcimg_url'] = request.GET.get("srcimg_url")
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名

  config = extendROIinfo(config)

  # 查找源影像
  service_name = config['user']['srcimg_url'].split('/')[-2]
  platform = service_name.split('_')[0]
  product_level = service_name.split('_')[2]
  if platform in ['gf1', 'gf2', 'gf6'] and product_level == 'l51rgb':
    srctable = config['pgsql']['l51rgb_table']
  elif platform == 's2' and product_level == 'l51ref':
    srctable = config['pgsql']['l51ref_table']
  elif platform == 's1' and product_level == 'db':
    srctable = config['pgsql']['db_table']
  else:
    raise Exception('请选择gf-1/2/6 l51rgb 或 s2 l51ref 或 s1 db级别的影像')
  strsql = 'select * from {} where service_url=\'{}\''.format(srctable,config['user']['srcimg_url'])
  results,colnames = selectPgItems(config['pgsql'],strsql)
  # 提取源影像信息
  if len(results) == 0:
    raise Exception('未检索到源影像')
  else:
    config['srcimg_info'] = dict()
    for i in range(len(colnames)):
      c = colnames[i]
      config['srcimg_info'][c] = results[0][i]

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l54syfb'], exist_ok=True)

  return config

def getIdtWatersOnAerImageParams(request):
  '''
  获取程序运行所需参数
  :param request: HttpRequest对象
  :return: dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['srcimg_url'] = request.GET.get("srcimg_url")
  config['user']['task_id'] = (request.GET.get("task_id")).strip()

  # 查找源影像
  srctable = config['pgsql']['l51rgb_table']
  strsql = 'select * from {} where service_url=\'{}\''.format(srctable, config['user']['srcimg_url'])
  results, colnames = selectPgItems(config['pgsql'], strsql)
  # 提取源影像信息
  if len(results) == 0:
    raise Exception('未检索到源影像')
  else:
    config['srcimg_info'] = dict()
    for i in range(len(colnames)):
      c = colnames[i]
      config['srcimg_info'][c] = results[0][i]

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l54syfb'], exist_ok=True)

  return config

def getWaterqaSpecOnlyParams(request):
  '''
  获取程序运行所需参数
  :param request: HttpRequest对象
  :return: dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['srcimg_url'] = request.GET.get("srcimg_url")
  config['user']['product_type'] = request.GET.get("product_type")
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)

  # 检查指标类型的参数
  if config['user']['product_type'] not in ['水色', '黑臭指数']:
    raise Exception('product_type 需从 水色、黑臭指数 中选择1项')

  # 查找源影像
  service_name = config['user']['srcimg_url'].split('/')[-2]
  product_level = service_name.split('_')[2]
  if product_level == 'l51rgb':
    srctable = config['pgsql']['l51rgb_table']
  elif product_level == 'l51ref':
    srctable = config['pgsql']['l51ref_table']
  else:
    raise Exception('请选择l51rgb 或 l51ref 级别的影像')
  strsql = 'select * from {} where service_url=\'{}\''.format(srctable, config['user']['srcimg_url'])
  results, colnames = selectPgItems(config['pgsql'], strsql)
  # 提取源影像信息
  if len(results) == 0:
    raise Exception('未检索到源影像')
  else:
    config['srcimg_info'] = dict()
    for i in range(len(colnames)):
      c = colnames[i]
      config['srcimg_info'][c] = results[0][i]

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l54fui'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l54sd'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l54dbwi'], exist_ok=True)

  return config

def getWaterqaRetrivalParams(request):
  '''
  获取程序运行所需参数
  :param request: HttpRequest对象
  :return: dict 程序执行所需参数
  '''
  pass

def getFmVctParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['farmland_vectors'], exist_ok=True)

  return config

def getLcVctParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['landcover_vectors'], exist_ok=True)

  return config

def getS1UpdataParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['st_date'] = request.GET.get("st_date")
  config['user']['ed_date'] = request.GET.get("ed_date")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)
  # 创建必须的文件路径
  os.makedirs(config['savepath']['grd'], exist_ok=True)
  os.makedirs(config['savepath']['db'], exist_ok=True)

  return config

def getS2UpdataParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['st_date'] = request.GET.get("st_date")
  config['user']['ed_date'] = request.GET.get("ed_date")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['min_cldpct'] = request.GET.get("min_cldpct")
  config['user']['max_cldpct'] = request.GET.get("max_cldpct")
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l23'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l51rgb'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l51ref'], exist_ok=True)

  # parameters related to geoscene. 涉及地图服务、切片服务、要素服务的，需指定样式模板
  config['geoscene']['tpl_lyrname'] = CONFIGS['geoscene']['tpl_rgb_lyr']

  return config

def getS3UpdataParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  # print(config['user']['st_date'],config['user']['ed_date'],config['user']['roi'],config['user']['prj_name'],config['user']['task_id'])
  config['user']['st_date'] = request.GET.get("st_date")
  config['user']['ed_date'] = request.GET.get("ed_date")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  print(config['user'])
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)
  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l1'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l51rgb'], exist_ok=True)

  # parameters related to geoscene. 涉及地图服务、切片服务、要素服务的，需指定样式模板
  config['geoscene']['tpl_lyrname'] = CONFIGS['geoscene']['tpl_rgb_lyr']

  return config

def getCCRSImgUpdataParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['st_date'] = request.GET.get("st_date")
  config['user']['ed_date'] = request.GET.get("ed_date")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  # 提取roi中的名称、wkt描述、中心经纬度，生成roi矢量文件，记录文件名
  config = extendROIinfo(config)

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l1'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l23'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l51rgb'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l51ref'], exist_ok=True)

  # parameters related to geoscene. 涉及地图服务、切片服务、要素服务的，需指定样式模板
  config['geoscene']['tpl_lyrname'] = CONFIGS['geoscene']['tpl_rgb_lyr']

  return config

def getAerialImgUpdataParams(request):
  '''
  获取程序运行所需参数
  :param request:
  :return:
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['area_name'] = request.GET.get("area_name")
  config['user']['platform'] = request.GET.get("platform")
  config['user']['sensor'] = request.GET.get("sensor")
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l0'], exist_ok=True)

  # parameters related to geoscene. 涉及地图服务、切片服务、要素服务的，需指定样式模板
  config['geoscene']['tpl_lyrname'] = CONFIGS['geoscene']['tpl_rgb_lyr']

  return config

def getGaodePOIParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['poi_type'] = request.GET.get("poi_type")
  config['user']['distance'] = request.GET.get("distance")
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  gdf = gpd.GeoDataFrame.from_features(config['user']['roi'])
  config['user']['roi_name'] = gdf.loc[0, 'name']
  config['user']['roi_wkt'] = gdf.loc[0, 'geometry'].wkt
  config['user']['roi_cx'] = round(gdf.loc[0, 'geometry'].x, 4)
  config['user']['roi_cy'] = round(gdf.loc[0, 'geometry'].y, 4)

  # 检查参数
  if config['user']['poi_type'] not in list(config['gaode_poi'].keys()):
    raise Exception('无效的高德POI类型')

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['poi'], exist_ok=True)

  # parameters related to geoscene. 涉及地图服务、切片服务、要素服务的，需指定样式模板
  config['geoscene']['tpl_lyrname'] = CONFIGS['geoscene']['tpl_poi_lyr']

  return config

def getPrecipitationParams(request):
  '''
  获取程序运行所需参数
  :param request:HttpRequest对象
  :return:dict 程序执行所需参数
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['st_date'] = request.GET.get("st_date")
  config['user']['ed_date'] = request.GET.get("ed_date")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  gdf = gpd.GeoDataFrame.from_features(config['user']['roi'])
  config['user']['roi_name'] = gdf.loc[0, 'name']
  config['user']['roi_wkt'] = gdf.loc[0, 'geometry'].wkt
  config['user']['roi_cx'] = round(gdf.loc[0, 'geometry'].x, 4)
  config['user']['roi_cy'] = round(gdf.loc[0, 'geometry'].y, 4)
  config['user']['prj_name'] = (request.GET.get("prj_name")).strip()
  config['user']['task_id'] = (request.GET.get("task_id")).strip()

  return config

def extendROIinfo(config):
  '''
  对用户提供的json格式的roi进行处理，生成可直接使用的信息
  :param config: dict(dict())
  :return:
  '''
  # json格式矢量转gdf对象
  gdf = gpd.GeoDataFrame.from_features(config['user']['roi'])
  # roi 名称
  config['user']['roi_name'] = gdf.loc[0, 'name']
  # roi wkt描述
  config['user']['roi_wkt'] = gdf.loc[0, 'geometry'].wkt
  # 中心经度
  config['user']['roi_cx'] = round(gdf.loc[0, 'geometry'].centroid.x, 4)
  # 中心纬度
  config['user']['roi_cy'] = round(gdf.loc[0, 'geometry'].centroid.y, 4)
  # 生成兴趣区矢量文件
  config['user']['roi_file'] = os.path.join(config['savepath']['roi'], config['user']['task_id']+'.shp')
  gdf.to_file(config['user']['roi_file'], encoding='utf-8')

  return config

