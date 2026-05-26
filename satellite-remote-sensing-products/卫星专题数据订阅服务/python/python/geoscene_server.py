import requests
import json
import sys
import os
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

    r = requests.post(gentokenurl, data=params, verify=False)
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
        r = requests.post(server_regdatastore, data=params, verify=False)
        print(r.text)
    except Exception as e:
        print(e)

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
        r = requests.post(server_createservice, data=params, verify=False)
        print(r.text)
    except Exception as e:
        print(e)

def mainImageServie(portal_url,portal_user,portal_password,server_url,service_name,imgfile,cachedir,outputdir):
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
        print("门户登录错误:", e)

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
        print("服务发布错误：", e)

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


def main(config,share_file,service_name,service_type):
    '''
    发布服务的主函数
    :param config: dict 含服务发布所需信息，如portarl_url, portal_user等
    :param share_file: str 待发布文件
    :param service_name: str 服务名称
    :param service_type: str 服务类型. 可选 img_service，map_service
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
                                         share_file, cachedir,outputdir)

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

    return service_url


config_geoscene = json.loads(sys.argv[1])
service_name = sys.argv[2]
share_file = sys.argv[3]
service_type = sys.argv[4]

main(config_geoscene,share_file,service_name,service_type)
