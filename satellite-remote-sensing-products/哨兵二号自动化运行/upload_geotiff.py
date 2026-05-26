from numpy.core.fromnumeric import product
from geoserver import store
from geoserver.catalog import Catalog
import os
from mysql_pool import DB_CONN
import datetime

fileheader = "file://" # C:/SWork/geoserverdata/"	#数据存储路径
geourl = "http://o3198111t6.qicp.vip:8082/geoserver/rest/workspaces"
geocat = Catalog(geourl,'admin','geoserver@123')	#create a Catalog object,默认用户名和密码

# satellite_name 卫星名称 ex: GF-1/GF-6
# format 数据格式 ex: TIFF/SHP
# catalog 分类 1：卫星影像 2：图像范围 31：水质反演产品(COD) 32:NH4 33:TN 34:TP 35:水色 36透明度 
# sensor 传感器 ex: PMS / WFV / MSI
# resolution 分辨率
# map_name 图层名称
# cover_name 覆盖范围shp名称，
# center_long 中心点经度
# center_lat 中心点纬度
# pro_time 产品时间
@DB_CONN
def db_insert_map_record(db, satellite_name,format,catalog,sensor,resolution,map_name,cover_name,center_long,center_lat,pro_time):
    try:
        # %s的个数要和参数一样多
        sql = "INSERT INTO data_maps (satellite_name,format,catalog,sensor,resolution,map_name,cover_name,center_long,center_lat,pro_time) VALUES \
            ( '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"
        data = (satellite_name,format,catalog,sensor,resolution,map_name,cover_name,center_long,center_lat,pro_time)
        db.cursor.execute(sql % data)
        db.conn.commit()
        return 0
    except Exception as e:
        print(str(e))
        db.conn.rollback()
        return 1

def getS2MapInfo(store_name):
    # sensor tyoe
    sensor = "MSI"
    strs = store_name.split("_")
    product_type = strs[-1]
    cover_name = store_name.replace(product_type,"COV")
    if product_type == "RGB":
        catalog = "1"
        format = "TIFF"
        resolution = 10
    elif product_type == "COV":
        catalog = "2"
        format = "SHP"
        resolution = 10
    elif product_type == "SD":
        catalog = "36"
        format = "TIFF"
        resolution = 10
    else:
        print("a product type has not been recorded")
        return False
    sensetime = strs[2][0:4] + "-" + strs[2][4:6] + "-" + strs[2][6:8]
    return format,catalog,sensor,resolution,cover_name,sensetime

def uploadGeotiff(store_name,destFile,workspace="S2Serve",style="SD_normal"):
    workspace = geocat.get_workspace(workspace)	#workspace name
    data_url = fileheader + destFile		#存储路径
    print(data_url)
    try:
        # geocat.create_coveragestore_external_geotiff(store_name,data_url,workspace,True)
        # print('success!---1')
        # geocat.modify_layer(store_name,workspace,style)
        # geocat.modify_coverage_trancolor(store_name,workspace)
        # print('success!---2')
        # 图层信息录入数据库
        satellite_name = store_name.split("_")[0]
        if "S2" in satellite_name:
            format,catalog,sensor,resolution,cover_name,sensetime = getS2MapInfo(store_name)
        else:
            print("a wrong satellite product")
        db_insert_map_record(satellite_name,format,catalog,sensor,resolution,"S2Server:"+store_name,"S2Server:"+cover_name,'','',sensetime)
        print('success!---3')
    except Exception:
        pass

# 发SHP不能定义style，目前有点问题        
def uploadShp(store_name,destFile,workspace="S2Server",style="S2_COV"):
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
# uploadGeotiff("S2A_MSIL2A_20210203T025931_N0214_R032_T50RLU_20210203T055016_SD",r'I:\Sentinel2_DATA\20210228\waterQA\S2A_MSIL2A_20210203T025931_N0214_R032_T50RLU_20210203T055016_SD.tif',workspace="S2Server",style="S2_SD")

if __name__=="__main__":
    db = DB_CONN()
    satellite_name = "S2Server:S2A_MSIL2A_20210203T025931_N0214_R032_T50RLT_20210203T055016_SD"
    query_sql = "select satellite_name from data_maps where satellite_name ='%s'"
    try:
        result = db.cursor.execute(query_sql % satellite_name)
        print("result:",result)
    except Exception as e:
        print(str(e))
        print("000000")
    
    # try:
        # %s的个数要和参数一样多
    #     sql = "INSERT INTO data_maps (satellite_name,format,catalog,sensor,resolution,map_name,cover_name,center_long,center_lat,pro_time) VALUES \
    #         ( '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"
    #     data = (satellite_name,format,catalog,sensor,resolution,map_name,cover_name,center_long,center_lat,pro_time)
    #     db.cursor.execute(sql % data)
    #     db.conn.commit()
    #     print("1111")
    # except Exception as e:
    #     print(str(e))
    #     db.conn.rollback()
    #     print("000000")