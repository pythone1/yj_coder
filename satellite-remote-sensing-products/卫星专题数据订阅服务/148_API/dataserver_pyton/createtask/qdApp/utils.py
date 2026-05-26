import os
import json

def getS1UpdataParams(request):
  '''
  从http request 获取请求信息
  :param request: HttpRequest对象
  :return:
  '''
  config = {}
  # parameters from request
  config['prj_name'] = request.GET.get("prjname")
  config['st_date'] = request.GET.get("stdate")
  config['ed_date'] = request.GET.get("eddate")
  config['roi'] = json.loads(request.GET.get("roi"))

  # parameters related to savepath
  config['s1_L1_path'] = r'Q:\卫星专题数据订阅服务\s1_GRD'
  config['s1_L2_path'] = r'Q:\卫星专题数据订阅服务\s1_DB'
  os.makedirs(config['s1_L1_path'], exist_ok=True)
  os.makedirs(config['s1_L2_path'], exist_ok=True)

  # parameters related to scihub
  config['scihub_site'] = "https://scihub.copernicus.eu/dhus"
  config['scihub_user'] = "wenyansha"
  config['scihub_password'] = "WenYansha12"

  # parameters related to geoscene
  config['portal_url'] = 'https://ndww149.ndww.gis/geoscene'
  config['portal_user'] = 'ndww'
  config['portal_password'] = 'ndwwtech5d'
  config['server_url'] = 'https://ndww149.ndww.gis/server'
  config['cachedir'] = "I:\\geosceneserver\\directories\\geoscenecache"
  config['outputdir'] = 'I:\\geosceneserver\\directories\\geosceneoutput'

  return config






