import requests
import json
import sys
import os
import datetime,time
import arcpy

def getPServerToken(portal_url, portal_user, portal_password, server_url):
    '''
    获取与portal联合的Server token
    :param portal_url: portal 地址
    :param portal_user: portal 用户名
    :param portal_password: portal 密码
    :param server_url: server 地址
    :return: 返回token
    '''
    gentokenurl = portal_url + '/sharing/rest/generateToken'
    params = {"f": "json", "username": portal_user, "password": portal_password, "expiration": "20",
              "client": "referer", "referer": server_url}

    s = requests.session()
    s.trust_env = False
    r = s.post(gentokenurl, data=params, verify=False)
    token = json.loads(r.text)["token"]

    return token

def getImageServiceDefinition(service_name, imgfile,cachedir,outputdir,portal_url,portal_user):
    '''
    获取通用的影像服务定义
    :param service_name: str 服务名称
    :param imgfile: str 影像文件存储地址（server所在服务器的路径）
    :param cachedir: str server所在服务器上的缓存路径
    :param outputdir: str server所在服务器上的输出路径
    :param portal_url: str portal 地址
    :param portal_user: str portal 用户名
    :return isdef: dict 服务定义信息
    '''
    isdef = {
        "serviceName": service_name,
        "type": "ImageServer",
        "description": "",
        "capabilities": "Image, Metadata, Mensuration",
        "provider": "ArcObjects11",
        "clusterName": "default",
        "minInstancesPerNode": 0,
        "maxInstancesPerNode": 2,
        "instancesPerContainer": 1,
        "maxWaitTime": 60,
        "maxStartupTime": 300,
        "maxIdleTime": 1800,
        "maxUsageTime": 600,
        "loadBalancing": "ROUND_ROBIN",
        "isolationLevel": "HIGH",
        "configuredState": "STARTED",
        "recycleInterval": 24,
        "recycleStartTime": "00:00",
        "keepAliveInterval": -1,
        "private": False,
        "isDefault": False,
        "maxUploadFileSize": 0,
        "allowedUploadFileTypes": "",
        "properties": {
            "copyright": "",
            "cacheDir": cachedir,
            "maxImageWidth": "15000",
            "rasterFunctions": "",
            "defaultTemplate": "None",
            "hasColormap": "false",
            "defaultCompressionQuality": "75",
            "antialiasingMode": "Fast",
            "hasValidSR": "true",
            "hasStaticData": "false",
            "availableMensurationCapabilities": "Basic",
            "maxImageHeight": "4100",
            "path": imgfile,
            "maximumSourceCellSize": "640",
            "useLocalCacheDir": "true",
            "allowFunction": "true",
            "supportedImageReturnTypes": "URL",
            "clientCachingAllowed": "true",
            "allowedMensurationCapabilities": "Basic",
            "maxExportTilesCount": "100000",
            "cacheControlMaxAge": "43200",
            "colormapToRGB": "false",
            "allowedTemplates": "",
            "hasLiveData": "false",
            "allowAnalysis": "true",
            "defaultCompressionTolerance": "0.01",
            "description": "",
            "esriImageServiceSourceType": "esriImageServiceSourceTypeDataset",
            "isCached": "false",
            "virtualOutputDir": "/rest/directories/geosceneoutput",
            "exportTilesAllowed": "false",
            "cacheOnDemand": "false",
            "maxSampleCount": "1000",
            "defaultResamplingMethod": "1",
            "minScale": "0",
            "rasterTypes": "",
            "outputDir": outputdir,
            "maxScale": "0",
            "availableTemplates": "",
            "availableCompressions": "None,JPEG,LZ77,LERC",
            "userName": portal_user,
            "textAntialiasingMode": "Force",
            "returnJPGPNGAsJPG": "false",
            "ignoreCache": "false",
            "portalURL": portal_url,
            "virtualCacheDir": "/rest/directories/arcgiscache",
            "allowedCompressions": "None,JPEG,LZ77,LERC",
            "allowCopy": "true"
        },
        "extensions": [],
        "frameworkProperties": {},
        "datasets": []
    }

    return isdef

def regdatastore(token,share_folder,server_url,shared_path="/fileShares/imagedata3"):
    '''
    将栅格数据所在文件夹注册到服务器
    :param token: str 与portal联合的Server token
    :param share_folder: str 栅格数据所在文件夹
    :param server_url: str server 地址
    :param shared_path: str 文件夹共享后在server浏览到的路径/名称
    :return None
    '''
    server_regdatastore = server_url + "/admin/data/registerItem"

    fileshare = {
      "path": shared_path,
      "type": "folder",
      "info": {
        "isManaged": False,
        "dataStoreConnectionType": "shared",
        "path": share_folder
      }
    }

    params = {"f": "json", "token": token, "item": json.dumps(fileshare), "referer": server_url}
    try:
        s = requests.session()
        s.trust_env = False
        r = s.post(server_regdatastore, data=params, verify=False)
    except Exception as e:
        raise Exception(e)

def createImageServie(token,server_url,service_def):
    '''
    创建影像服务
    :param token: str 与portal联合的Server token
    :param service_def: dict 服务定义信息
    :param server_url: str server 地址
    :return None
    '''
    server_createservice = server_url + "/admin/services/createService"

    params = {"f": "json", "token": token, "service": json.dumps(service_def), "referer": server_url}
    try:
        s = requests.session()
        s.trust_env = False
        r = s.post(server_createservice, data=params, verify=False)
    except Exception as e:
        raise Exception(e)

def mainImageServie(portal_url,portal_user,portal_password,server_url,service_name,imgfile,cachedir,outputdir,tags=""):
    '''
    发布影像图层的主函数
    :param portal_url: portal 地址
    :param portal_user: portal 用户名
    :param portal_password: portal 密码
    :param server_url: server 地址
    :param service_name: str 服务名称
    :param imgfile: str 影像文件存储地址（server所在服务器的路径）
    :param cachedir: str server所在服务器上的缓存路径
    :param outputdir: str server所在服务器上的输出路径
    :return: imgservice_url str 服务地址
    '''
    token = getPServerToken(portal_url,portal_user,portal_password,server_url)
    service_def = getImageServiceDefinition(service_name, imgfile,
                                            cachedir=cachedir,
                                            outputdir=outputdir,
                                            portal_url=portal_url,
                                            portal_user=portal_user)
    createImageServie(token, server_url, service_def)

    imgservice_url = server_url + '/rest/services/' + service_name + '/ImageServer'

    return imgservice_url


def applySymFromLayer(dstlayer, reflayer):
    '''
    功能：将图层reflayer样式复制给dstlayer
    dstlayer: arcpy._mp.Layer 目标图层
    reflayer: arcpy._mp.Layer 参考图层
    '''
    # 复制图层样式
    lyr = arcpy.management.ApplySymbologyFromLayer(
        in_layer=dstlayer,
        in_symbology_layer=reflayer,
        update_symbology="UPDATE")[0]

    return lyr

def releaseMapImageService(amap, shr_lyrs, service_name, portal_url, portal_user, portal_password, server_url, workpath):
    '''
    功能：发布地图类型服务
    amap: arcpy._mp.Map 地图
    shr_lyrs: arcpy._mp.Layer或其列表 待发布图层。列表可通过listLayers('*')获取
    service_name：str 所发布的服务的名称
    portal_url：str geoscene portal 地址
    portal_user: str geoscene portal 用户名
    portal_password: str geoscene portal 密码
    server_url: str geoscene server 地址
    workpath: str 过程文件存储地址
    '''
    # Sign in to portal
    try:
        arcpy.SignInToPortal(portal_url, portal_user, portal_password)
    except Exception as e:
        raise Exception("门户登录错误")

        return False

    # 设置输出文件
    outdir = workpath
    sddraft_filename = service_name + '.sddraft'
    sddraft_output_filename = outdir + '\\' + sddraft_filename
    sd_filename = service_name + '.sd'
    sd_output_filename = outdir + '\\' + sd_filename

    try:
        # 创建地图服务草稿
        sddraft = amap.getWebLayerSharingDraft("FEDERATED_SERVER", "MAP_IMAGE", service_name, shr_lyrs)
        sddraft.federatedServerUrl = server_url
        sddraft.exportToSDDraft(sddraft_output_filename)

        # 过渡服务
        arcpy.StageService_server(sddraft_output_filename, sd_output_filename)
        # 发布服务
        arcpy.UploadServiceDefinition_server(sd_output_filename, server_url)
    except Exception as e:
        raise Exception("服务发布错误")

        return False

    return True

def mainMapServie(filename,service_name,tpl_file,tpl_lyrname,blank_file,portal_url,portal_user,portal_password,server_url):
    # 获取模板图层
    tpl_aprx = arcpy.mp.ArcGISProject(tpl_file)
    tpl_map = tpl_aprx.listMaps()[0]
    tpl_lyr = tpl_map.listLayers('*{}*'.format(tpl_lyrname))[0]

    # 在空地图中加载新的图层并引用模板图层样式
    aprx = arcpy.mp.ArcGISProject(blank_file)
    amap = aprx.listMaps()[0]
    lyr = amap.addDataFromPath(filename)
    lyr = applySymFromLayer(lyr, tpl_lyr)

    # 发布地图服务
    outpath = os.path.dirname(blank_file)
    releaseMapImageService(amap, lyr, service_name, portal_url, portal_user, portal_password, server_url, outpath)

    service_url = server_url + '/rest/services/' + service_name + '/MapServer'

    return service_url

def getTileServiceScales(server_url, service_name, server_user, server_password):
    '''
    获取切片服务所有层级的比例尺信息
    :param server_url: server 地址
    :service_name: 切片服务名称
    :param server_user: server 用户名
    :param server_password: server 密码
    :return: scales 各层级比例尺的列表
    '''
    # get token
    token = getServerToken(server_user, server_password, server_url)

    # 从服务地址爬取服务信息
    params = {'token': token, 'f': 'json'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    service_rest = server_url + '/rest/services/Hosted/' + service_name + '/MapServer'

    s = requests.session()
    s.trust_env = False
    r = s.post(service_rest, data=params, verify=False)

    # 提取比例尺信息
    scales = []
    lodsinfo = json.loads(r.text)['tileInfo']['lods']
    for lod in lodsinfo:
        scales.append(float(lod['scale']))

    return scales

def getServerToken(server_user, server_password, server_url):
    '''
    获取ArcGIS Server token
    :param server_user: server 用户名
    :param server_password: server 密码
    :param server_url: server 地址
    :return: 返回token
    '''
    # Token URL is typically http://ndww149.ndww.gis/server/admin/generateToken
    token_url = server_url + '/admin/generateToken'
    params = {'username': server_user, 'password': server_password, 'client': 'requestip', 'f': 'json'}
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    s = requests.session()
    s.trust_env = False
    r = s.post(url=token_url, data=params, verify=False)
    token = json.loads(r.text)["token"]

    return token

def createTilesCache(server_url, service_name, scales, outdir, update_mode="RECREATE_ALL_TILES",
                     wait_for_job_completion="WAIT"):
    '''
    创建切片缓存
    :param server_url: server 地址
    :param service_name: str 图层名/服务名称
    :param scales: str list[float] 比例尺
    :param outdir: str 过程文件存储地址
    :param update_mode： str 参考ManageMapServerCacheTiles函数
    :param wait_for_job_completion: str 参考ManageMapServerCacheTiles函数
    '''
    # 服务rest
    service_rest = server_url + '/rest/services/Hosted/' + service_name + '/MapServer'

    # 过程记录文件
    currentTime = datetime.datetime.now()
    arg1 = currentTime.strftime("%Y%m%d%H%M%S")
    cachereport_file = os.path.join(outdir, 'cachereport_' + arg1 + '.txt')
    report = open(cachereport_file, 'w')

    # 缓存
    try:
        result = arcpy.server.ManageMapServerCacheTiles(service_rest, scales, update_mode,
                                                        wait_for_job_completion=wait_for_job_completion)

        while result.status < 4:
            time.sleep(0.2)
        result_value = result.getMessages()
        report.write("Completed " + str(result_value))
    except Exception as e:
        tb = sys.exc_info()[2]
        report.write("Failed at step 1 \n" "Line %i" % tb.tb_lineno)
        raise Exception(e)

    report.close()

def releaseTileService(amap,shr_lyrs,service_name,server_url,outdir,tags=""):
    '''
    功能：发布切片类型服务
    amap: arcpy._mp.Map 地图
    shr_lyrs: arcpy._mp.Layer或其列表 待发布图层。列表可通过listLayers('*')获取
    service_name：str 所发布的服务的名称
    server_url: str geoscene server 地址
    outdir: str 过程文件存储地址
    '''
    # 设置输出文件
    sddraft_filename = service_name + '.sddraft'
    sddraft_output_filename = outdir + '\\' +  sddraft_filename
    if os.path.exists(sddraft_output_filename):
        os.remove(sddraft_output_filename)
    sd_filename = service_name + '.sd'
    sd_output_filename = outdir + '\\' +  sd_filename
    if os.path.exists(sddraft_output_filename):
        os.remove(sd_output_filename)

    # 创建地图服务草稿
    sddraft = amap.getWebLayerSharingDraft("HOSTING_SERVER","TILE",service_name,shr_lyrs)
    sddraft.federatedServerUrl = server_url
    sddraft.overwriteExistingService = True
    sddraft.tags = tags
    sddraft.exportToSDDraft(sddraft_output_filename)

    # 过渡服务
    arcpy.StageService_server(sddraft_output_filename,sd_output_filename)
    # 发布服务
    arcpy.UploadServiceDefinition_server(sd_output_filename,"HOSTING_SERVER")

def mainTileService(filename,service_name,tpl_file,tpl_lyrname,blank_file,
                    portal_url,portal_user,portal_password,
                    server_url,server_user, server_password,
                    tags=""):
    # 获取模板图层
    tpl_aprx = arcpy.mp.ArcGISProject(tpl_file)
    tpl_map = tpl_aprx.listMaps()[0]
    tpl_lyr = tpl_map.listLayers('*{}*'.format(tpl_lyrname))[0]

    # 在空地图中加载新的图层并引用模板图层样式
    aprx = arcpy.mp.ArcGISProject(blank_file)
    amap = aprx.listMaps()[0]
    lyr = amap.addDataFromPath(filename)
    lyr = applySymFromLayer(lyr, tpl_lyr)

    # 地图保存为副本
    acopy = os.path.dirname(blank_file)
    acopy = os.path.join(acopy,'acopy.aprx')
    aprx.saveACopy(acopy)
    aprx = arcpy.mp.ArcGISProject(acopy)
    amap = aprx.listMaps()[0]
    lyrname = os.path.basename(filename).split('.')[0]
    lyr = amap.listLayers('*{}*'.format(lyrname))

    # 发布服务
    outpath = os.path.dirname(blank_file)
    try:
        # Sign in to portal
        arcpy.SignInToPortal(portal_url, portal_user, portal_password)
        # 发布切片服务
        releaseTileService(amap, lyr, service_name, server_url, outpath, tags)
        # 缓存切片
        scales = getTileServiceScales(server_url, service_name, server_user, server_password)
        createTilesCache(server_url, service_name, scales, outpath, update_mode="RECREATE_ALL_TILES",
                         wait_for_job_completion="DO_NOT_WAIT")
    except Exception as e:
        print(e)
        raise Exception(e)

    service_url = server_url + '/rest/services/' + service_name + '/MapServer'

    return service_url


def releaseFeatureService(amap, shr_lyrs, service_name,
                          portal_url, portal_user, portal_password,
                          server_url, workpath,tags=""):
    '''
    功能：发布要素类型服务
    amap: arcpy._mp.Map 地图
    shr_lyrs: arcpy._mp.Layer或其列表 待发布图层。列表可通过listLayers('*')获取
    service_name：str 所发布的服务的名称
    portal_url：str geoscene portal 地址
    portal_user: str geoscene portal 用户名
    portal_password: str geoscene portal 密码
    server_url: str geoscene server 地址
    workpath: str 过程文件存储地址
    '''
    # Sign in to portal
    try:
        arcpy.SignInToPortal(portal_url, portal_user, portal_password)
    except Exception as e:
        raise Exception("门户登录错误")

        return False

    # 设置输出文件
    outdir = workpath
    sddraft_filename = service_name + '.sddraft'
    sddraft_output_filename = outdir + '\\' + sddraft_filename
    sd_filename = service_name + '.sd'
    sd_output_filename = outdir + '\\' + sd_filename

    try:
        # 创建地图服务草稿
        sddraft = amap.getWebLayerSharingDraft("HOSTING_SERVER", "FEATURE", service_name, shr_lyrs)
        sddraft.federatedServerUrl = server_url
        sddraft.tags = tags
        sddraft.exportToSDDraft(sddraft_output_filename)

        # 过渡服务
        arcpy.StageService_server(sddraft_output_filename, sd_output_filename)
        # 发布服务
        arcpy.UploadServiceDefinition_server(sd_output_filename, "HOSTING_SERVER")
    except Exception as e:
        raise Exception(e)

        return False

    return True

def mainFeatureServie(filename,service_name,tpl_file,tpl_lyrname,blank_file,
                      portal_url,portal_user,portal_password,server_url,tags=""):
    # 获取模板图层
    tpl_aprx = arcpy.mp.ArcGISProject(tpl_file)
    tpl_map = tpl_aprx.listMaps()[0]
    tpl_lyr = tpl_map.listLayers('*{}*'.format(tpl_lyrname))[0]

    # 在空地图中加载新的图层并引用模板图层样式
    aprx = arcpy.mp.ArcGISProject(blank_file)
    amap = aprx.listMaps()[0]
    lyr = amap.addDataFromPath(filename)
    lyr = applySymFromLayer(lyr, tpl_lyr)

    # 地图保存为副本
    acopy = os.path.dirname(blank_file)
    acopy = os.path.join(acopy, 'acopy.aprx')
    aprx.saveACopy(acopy)
    aprx = arcpy.mp.ArcGISProject(acopy)
    amap = aprx.listMaps()[0]
    lyrname = os.path.basename(filename).split('.')[0]
    lyr = amap.listLayers('*{}*'.format(lyrname))

    # 发布地图服务
    outpath = os.path.dirname(blank_file)
    releaseFeatureService(amap, lyr, service_name,
                          portal_url, portal_user, portal_password,
                          server_url, outpath,tags)

    service_url = server_url + '/rest/services/' + service_name + '/MapServer'

    return service_url

def main(config,share_file,service_name,service_type,tags=""):
    '''
    发布服务的主函数
    :param config: dict 含服务发布所需信息，如portarl_url, portal_user等
    :param share_file: str 待发布文件
    :param service_name: str 服务名称
    :param service_type: str 服务类型. 可选 img_service，map_service
    :param prj_name: str 项目名称 （写入标签）
    :return:
    '''
    if service_type == "img_service":
        portal_url = config['portal_url']
        portal_user = config['portal_user']
        portal_password = config['portal_password']
        server_url = config['server_url']
        cachedir = config['cachedir']
        outputdir = config['outputdir']
        service_url = mainImageServie(portal_url, portal_user, portal_password, server_url, service_name,
                                         share_file, cachedir,outputdir,tags)

    elif service_type == "map_service":
        portal_url = config['portal_url']
        portal_user = config['portal_user']
        portal_password = config['portal_password']
        server_url = config['server_url']
        blank_file = config['blank_file']
        tpl_file = config['tpl_file']
        tpl_lyrname = config['tpl_rgb_lyr']
        service_url = mainMapServie(share_file,service_name,
                                    tpl_file,tpl_lyrname,blank_file,
                                    portal_url,portal_user,portal_password,server_url)

    elif service_type == "tile_service":
        portal_url = config['portal_url']
        portal_user = config['portal_user']
        portal_password = config['portal_password']
        server_url = config['server_url']
        blank_file = config['blank_file']
        tpl_file = config['tpl_file']
        tpl_lyrname = config['tpl_rgb_lyr']
        server_user = config['server_user']
        server_password = config['server_password']
        service_url = mainTileService(share_file, service_name, tpl_file, tpl_lyrname, blank_file,
                        portal_url, portal_user, portal_password, server_url, server_user, server_password,tags)

    elif service_type == "feature_service":
        portal_url = config['portal_url']
        portal_user = config['portal_user']
        portal_password = config['portal_password']
        server_url = config['server_url']
        blank_file = config['blank_file']
        tpl_file = config['tpl_file']
        tpl_lyrname = config['tpl_lyrname']
        service_url = mainFeatureServie(share_file,service_name,
                                        tpl_file,tpl_lyrname,blank_file,
                                        portal_url,portal_user,portal_password,
                                        server_url,tags=tags)


    return service_url

config_geoscene = json.loads(sys.argv[1])
service_name = sys.argv[2]
share_file = sys.argv[3]
service_type = sys.argv[4]
tags = sys.argv[5]
service_url=main(config_geoscene,share_file,service_name,service_type,tags)
print(service_url)
# print(service_name,share_file,service_type,tags)

# 测试发布切片服务
# acopy = r'O:\geoscene_project\blank\acopy.aprx'
# aprx = arcpy.mp.ArcGISProject(acopy)
# amap = aprx.listMaps()[0]
# lyr = amap.listLayers('*s2_msi_l51rgb_20230408T023531_20230408T023531_20230426T134713_E1215314N320065*')
# # 发布服务过程中记录文件存储位置
# outpath = r'O:\geoscene_project\blank'
# # 图层名
# service_name = 's2_msi_l51rgb_20230408_20230408_20230426T134713_E1215314N320065'
# # 服务器连接参数
# portal_url = 'https://geoscene.ndww.gis/geoscene'
# portal_user = 'ndww'
# portal_password = 'ndwwtech5d'
# server_url = 'https://geoscene.ndww.gis/server'
# server_user = 'siteadmin'
# server_password = 'ndwwtech5d'
#
# try:
#     # Sign in to portal
#     arcpy.SignInToPortal(portal_url, portal_user, portal_password)
#     # 发布切片服务
#     releaseTileService(amap, lyr, service_name, server_url, outpath)
#     print('Tile service upload successed.')
#     # 缓存切片
#     scales = getTileServiceScales(server_url, service_name, server_user, server_password)
#     createTilesCache(server_url, service_name, scales, outpath, update_mode="RECREATE_ALL_TILES",
#                      wait_for_job_completion="DO_NOT_WAIT")
#     print('Tile cache successed.')
#
# except Exception as e:
#     print(e)