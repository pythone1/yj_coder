import os
import json
import configparser

import geopandas as gpd

CONFIGS = dict()
cp = configparser.ConfigParser()
cp.read("config.ini",encoding="utf-8")
d = dict(cp._sections)
for k in d:
    CONFIGS[k] = dict(d[k])

def getS1UpdataParams(request):
  '''
  从http request 获取请求信息
  :param request: HttpRequest对象
  :return:
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['prj_name'] = request.GET.get("prj_name")
  config['user']['st_date'] = request.GET.get("st_date")
  config['user']['ed_date'] = request.GET.get("ed_date")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  gdf = gpd.GeoDataFrame.from_features(config['user']['roi'])
  config['user']['roi_name'] = gdf.loc[0, 'name']
  config['user']['roi_wkt'] = gdf.loc[0,'geometry'].wkt
  config['user']['roi_cx'] = round(gdf.loc[0, 'geometry'].x,4)
  config['user']['roi_cy'] = round(gdf.loc[0, 'geometry'].y,4)

  # 创建必须的文件路径
  os.makedirs(config['savepath']['grd'], exist_ok=True)
  os.makedirs(config['savepath']['db'], exist_ok=True)

  return config

def getS2UpdataParams(request):
  '''
  从http request 获取请求信息
  :param request: HttpRequest对象
  :return:
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['prj_name'] = request.GET.get("prj_name")
  config['user']['st_date'] = request.GET.get("st_date")
  config['user']['ed_date'] = request.GET.get("ed_date")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  gdf = gpd.GeoDataFrame.from_features(config['user']['roi'])
  config['user']['roi_name'] = gdf.loc[0, 'name']
  config['user']['roi_wkt'] = gdf.loc[0, 'geometry'].wkt
  config['user']['roi_cx'] = round(gdf.loc[0, 'geometry'].x, 4)
  config['user']['roi_cy'] = round(gdf.loc[0, 'geometry'].y, 4)
  config['user']['min_cldpct'] = request.GET.get("min_cldpct")
  config['user']['max_cldpct'] = request.GET.get("max_cldpct")

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l23'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l51rgb'], exist_ok=True)
  os.makedirs(CONFIGS['savepath']['l51ref'], exist_ok=True)

  # parameters related to geoscene. 涉及地图服务、切片服务、要素服务的，需指定样式模板
  config['geocene']['tpl_lyrname'] = CONFIGS['geoscene']['tpl_rgb_lyr']

  return config

def getIdtWaterParams(request):
  '''
  从http request 获取请求信息
  :param request: HttpRequest对象
  :return:
  '''
  # 获取系统初始化参数
  config = CONFIGS.copy()
  # 补充用户参数（parameters from request）
  config['user'] = dict()
  config['user']['prj_name'] = request.GET.get("prj_name")
  config['user']['roi'] = json.loads(request.GET.get("roi"))
  gdf = gpd.GeoDataFrame.from_features(config['roi'])
  config['user']['roi_name'] = gdf.loc[0, 'name']
  config['user']['roi_wkt'] = gdf.loc[0, 'geometry'].wkt
  config['user']['roi_cx'] = round(gdf.loc[0, 'geometry'].x, 4)
  config['user']['roi_cy'] = round(gdf.loc[0, 'geometry'].y, 4)
  config['user']['srcimg_url'] = request.GET.get("srcimg_url")

  # 根据数据源类型选择数据表查找影像
  service_name = config['user']['srcimg_url'].split('/')[-2]
  platform = service_name.split('_')[0]
  if platform in ['gf1', 'gf2', 'gf6']:
    config['user']['srctable'] = config['pgsql']['l51rgb_table']
  elif platform == 's2':
    config['user']['srctable'] = config['pgsql']['l51ref_table']
  elif platform == 's1':
    config['user']['srctable'] = config['pgsql']['db_table']
  else:
    raise Exception('请选择高分、哨兵二、哨兵一的图层')

  # 创建必须的文件路径
  os.makedirs(CONFIGS['savepath']['l54syfb'],exist_ok=True)

  return config


