'''
@Time    :   2021/04/27
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 矢量数据处理
'''
import numpy as np
import ogr
import geotable
from osgeo import gdal, osr
import kml2geojson as k2g
import geopandas as gpd
import shutil
import os

import imgProcess as imgpro

# 读取矢量文件
def shpfileread(shpfile):
    # open shpfile driver
    ds = ogr.Open(shpfile)
    driver = ds.GetDriver()
    # get layer
    layer_nums = ds.GetLayerCount()
    for i in range(layer_nums):
        layer = ds.GetLayerByIndex(i)
        layerDefn = layer.GetLayerDefn()
        layer_name = layerDefn.GetName()
    # get epsg
    crs = layer.GetSpaticalRef()
    epsg = crs.GetAttrValue('AUTHORITY',1)
    # get field
    field_num = layerDefn.GetFieldCount()
    fields = []
    for i in range(field_num):
        field_defn = layerDefn.GetFieldDefn(i)
        field_name = field_defn.GetName()
        field_type = field_defn.GetTypeName()
        fields.append({'filed_name':field_name,'filed_type':filed_type})
    return epsg,fields


# 读取Kml文件，返回wkt
def kmlread(kmlfile):
    k2g.convert(kmlfile, './temp')
    try:
        gdf = gpd.read_file(os.path.splitext('./temp/'+os.path.split(kmlfile)[-1])[0]+'.geojson',encoding='gbk')
    except:
        gdf = gpd.read_file(os.path.splitext('./temp/'+os.path.split(kmlfile)[-1])[0]+'.geojson',encoding='utf-8')
    shutil.rmtree( './temp')    # 递归删除目录及目录下所有文件
    # wkt = gdf['geometry'][0].wkt
    # return wkt
    return gdf

# 根据wkt创建shp
def createShpfile_from_WKT(shpfile,wkt):
    # shppath = os.path.dirname(shpfile)  #shpfile 目录
    # shpfilename = os.path.basename(shpfile).split(".")[0]   #shpfile 文件名
    polygon = ogr.CreateGeometryFromWkt(wkt)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(shpfile)  # 指定目录
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    layer = data_source.CreateLayer(shpfile,srs,ogr.wkbPolygon)   # 指定名称
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(polygon)
    layer.CreateFeature(feature)
    feature = None
    data_source = None

# 根据kml创建shp
def createShpfile_from_KML(shpfile,kmlfile):
    geo_table = geotable.load(kmlfile)
    wkt = geo_table.geometries[0].wkt
    polygon = ogr.CreateGeometryFromWkt(wkt)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(shpfile)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    layer = data_source.CreateLayer("polygon",srs,ogr.wkbPolygon)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetGeometry(polygon)
    layer.CreateFeature(feature)
    feature = None
    data_source = None

# 根据坐标[x1 y1 x2 y2 ...]创建shp
def createShpfile_from_coordinates(shpfile,coordinates,epsg=4326):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(shpfile)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    layer = data_source.CreateLayer("polygon",srs,ogr.wkbPolygon)
    feature = ogr.Feature(layer.GetLayerDefn())
    coordinates_num = int(coordinates.shape[0] / 2)
    print(coordinates_num)
    wkt = "POLYGON(("
    for i in range(coordinates_num):
        wkt = wkt + str(coordinates[i*2]) + " " + str(coordinates[i*2+1]) + ","
    wkt = wkt[0:-1] + "))"
    polygon = ogr.CreateGeometryFromWkt(wkt)
    feature.SetGeometry(polygon)
    layer.CreateFeature(feature)
    feature = None
    data_source = None

# 面转凸多边形
def createGeomConvex(ori_shpfile,convex_shpfile):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    inds = ogr.Open(ori_shpfile,0)
    inlayer = inds.GetLayer()
    # 获取空间参考
    insrs = inlayer.GetSpatialRef()
    # 创建几何体集合，写入多边形
    geomcoll = ogr.Geometry(ogr.wkbGeometryCollection)
    for feature in inlayer:
        geomcoll.AddGeometry(feature.GetGeometryRef())
    # 获取凸多边形
    geomconvex = geomcoll.ConvexHull()
    # 创建输出文件
    # if os.path.exists(convex_shpfile):
    #     driver.DeleteDataSource(convex_shpfile)
    outds = driver.CreateDataSource(convex_shpfile)
    outlayer = outds.CreateLayer('converxHull',srs = insrs,geom_type = ogr.wkbPolygon)
    # 创建要素并写入
    outfeature = ogr.Feature(outlayer.GetLayerDefn())
    outfeature.SetGeometry(geomconvex)
    outlayer.CreateFeature(outfeature)
    feature = None
    inds = None
    outds = None

# 经纬度转投影坐标
def lonlat2geo(proj, lon, lat):
    '''
    将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
    :param dataset: GDAL地理数据
    :param lon: 地理坐标lon经度
    :param lat: 地理坐标lat纬度
    :return: 经纬度坐标(lon, lat)对应的投影坐标
    '''
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(proj)
    geosrs = prosrs.CloneGeogCS()
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    coords = ct.TransformPoint(lat, lon)
    return coords[:2]

# 投影坐标转经纬度
def geo2lonlat(proj,x,y):
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(proj)
    geosrs = prosrs.CloneGeogCS()
    ct = osr.CoordinateTransformation(prosrs,geosrs)
    coords = ct.TransformPoint(y,x)
    return coords[:2]

# shp文件重投影
def reproject(infile,outfile,insrs,outsrs):
    t = osr.SpatialReference()
    t.ImportFromEPSG(4326)
    outsrs = t
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8","NO")
    gdal.SetConfigOption("SHAPE_ENCODING","")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    # create the CoordinateTransForm
    coordTrans = osr.CoordinateTransformation(insrs,outsrs)
    # get the input layer
    inDataSet = driver.Open(infile)
    inlayer = inDataSet.GetLayer()
    # create the output layer
    outDataSet = driver.CreateDataSource(outfile)
    outlayer = outDataSet.CreateLayer("repoject",outsrs,geom_type = inlayer.GetGeomType())
    # add fields
    inLayerDefn = inlayer.GetLayerDefn()
    for i in range(0,inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outlayer.CreateField(fieldDefn)
    # get the output layer's feature definition
    outLayerDefn = outlayer.GetLayerDefn()
    # loop through the input features
    inFeature = inlayer.GetNextFeature()
    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()        
        # reproject the geometry
        geom.Transform(coordTrans)
        # resort coordinates
        newwkt = 'POLYGON (('
        wkt = geom.ExportToWkt()
        coordinates = wkt.split("((")[1].split("))")[0]
        coordinates = coordinates.split(",")
        for i in range(len(coordinates)):
            x = coordinates[i].split(" ")[0]
            y = coordinates[i].split(" ")[1]
            newwkt = newwkt + y + " " + x + ","
        newwkt = newwkt[:-1] + "))"
        newgeom = ogr.CreateGeometryFromWkt(newwkt)
        print(newgeom.ExportToWkt())
        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry and attribute
        outFeature.SetGeometry(newgeom)
        for i in range(0,outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),inFeature.GetField(i))
            # add the feature to the shapefile
            outlayer.CreateFeature(outFeature)
            # destroy the feature and get the next input feature
            outFeature.Destroy()
            inFeature.Destroy()
            inFeature = inlayer.GetNextFeature()
    # close the shapefile
    inDataSet.Destroy()
    outDataSet.Destroy()

# 判断是否相交
def isIntersect(shpfile1,shpfile2):
    driver=ogr.GetDriverByName('ESRI Shapefile')
    dataSource1=driver.Open(shpfile1,0) #0-只读,1-可写
    dataSource2=driver.Open(shpfile2,0) #0-只读,1-可写    

    if dataSource1 is None or dataSource2 is None:
        print('Could not intersection')
    else:
        layer1=dataSource1.GetLayer()
        layer2=dataSource2.GetLayer()
        srs1 = layer1.GetSpatialRef()
        srs2 = layer2.GetSpatialRef()
        transform = osr.CoordinateTransformation(srs1,srs2) # 1转2
        flag = False
        for feature1 in layer1:
            geom1=feature1.GetGeometryRef()
            geom1.Transform(transform)
            for feature2 in layer2:
                geom2=feature2.GetGeometryRef()
                intersection=geom1.Intersection(geom2)
                print(intersection)
                if (intersection.ExportToWkt()!="POLYGON EMPTY") and (intersection.ExportToWkt()!="GEOMETRYCOLLECTION EMPTY"):
                    flag = True
                    break                                
            layer2.ResetReading()   # ResetReading()用来复位,不然下次使用GetNextFeature程序接着上次读的位置继续读
        return flag

if __name__ == '__main__':
    t=kmlread(r'D:\Users\Desktop\测试\1.kml')

    # shp1 = r'D:\ProcessingData\TEMP\test\test1.shp'
    # shp2 = r'D:\ProcessingData\TEMP\test\test2.shp'
    # shp3 = r'D:\ProcessingData\TEMP\test\test3.shp'
    # print(isIntersect(shp1,shp3))

    # shpfile = r'D:\Users\Administrator\Desktop\best_model\test.shp'
    # coordinates = np.array([119.192678867346,34.9497490850763,119.192678867346,34.9492904187473,119.192965298415,34.9492904187473,119.192965298415,34.9497490850763])
    # createShpfile_from_coordinates(shpfile, coordinates, epsg=4326)

    
    