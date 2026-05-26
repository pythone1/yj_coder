from geoserver.catalog import Catalog
import os

fileheader = "file://"# C:/SWork/geoserverdata/"	#数据存储路径
geourl = "http://o3198111t6.qicp.vip:8082/geoserver/rest/workspaces"
geocat = Catalog(geourl,'admin','geoserver@123')	#create a Catalog object,默认用户名和密码

def uploadGeotiff(store_name,destFile,workspace="Sentinel2AutoServe",style="SD_normal"):
    workspace = geocat.get_workspace(workspace)	#workspace name
    data_url = fileheader + destFile		#存储路径
    try:
        geocat.create_coveragestore_external_geotiff(store_name,data_url,workspace,True)
        print('success!---1')
        geocat.modify_layer(store_name,workspace,style)
        print('success!---2')
    except Exception:
        pass

# 发SHP不能定义style，目前有点问题        
def uploadShp(store_name,destFile,workspace="ad",style="ad_shp"):
    workspace = geocat.get_workspace(workspace)        #workspace name
    data_url = fileheader + destFile                #存储路径
    try:
        geocat.create_coveragestore_external_shp(store_name,data_url,workspace,True)
        print('success!---1')
        # geocat.modify_layer(store_name,workspace,style)
        # print('success!---2')
    except Exception as e:
        print(str(e))
        pass
	
#uploadGeotiff('C:/SWork/geoserverdata/H08_20201114_0300_1HARP031_FLDK.02401_02401_AOT_L2_Mean_interpolate.tif')