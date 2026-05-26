import os,glob

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString

def extract_coordinates(location):
    lon, lat = map(float, location.split('，'))
    return Point(lon, lat)

def round_coordinates(coords, precision):
    try:
        return [(round(x, precision), round(y, precision)) for x, y in coords]
    except:
        return [(round(x, precision), round(y, precision)) for x, y,z in coords]

def round_geometry(geom, precision):
    if isinstance(geom, Point):
        return Point(round(geom.x, precision), round(geom.y, precision))
    elif isinstance(geom, LineString):
        return LineString(round_coordinates(geom.coords, precision))
    elif isinstance(geom, Polygon):
        exterior = round_coordinates(geom.exterior.coords, precision)
        interiors = [round_coordinates(interior.coords, precision) for interior in geom.interiors]
        return Polygon(exterior, interiors)
    else:
        return geom.__class__([round_geometry(part, precision) for part in geom.geoms])

def isChanged(ogdf,ngdf,precision=10):
    '''
    判断新图斑是否发生变化
    ogdf: gpd.GeoDataFrame 原图斑
    ngdf: gpd.GeoDataFrame 新图斑
    precision: int 对坐标小数点后几位进行一致性判断
    '''
    # 保留小数位
    ogdf['geometry'] = ogdf['geometry'].apply(lambda geom: round_geometry(geom, precision))
    ngdf['geometry'] = ngdf['geometry'].apply(lambda geom: round_geometry(geom, precision))

    # 新旧两图斑合并，重复为未改变，不重复的为变化
    ogdf['idx0'] = 'o' + ogdf.index.astype('str')
    ngdf['idx0'] = 'n' + ngdf.index.astype('str')
    gdf0 = pd.concat([ogdf,ngdf])
    idx0 = gdf0.duplicated(subset='geometry',keep=False) # 重复项标记
    idx1 = gdf0.loc[idx0,'idx0'].values
    flg = [True if 'n' in i else False for i in idx1]
    idx1 = idx1[flg]
    idx1 = [i[1:] for i in idx1]
    idx1 = np.array(idx1,'int')

    changed = np.array([True] * len(ngdf))
    changed[idx1] = False

    ngdf.drop('idx0',axis=1,inplace=True)

    return changed

def intersectsOnly(gdf1,gdf2,how='inner'):
    '''
    相交不相接
    '''
    intersects = gpd.sjoin(gdf1,gdf2,how=how,predicate='intersects')
    intersects['index_left'] = intersects.index
    intersects.reset_index(inplace=True)
    touches = gpd.sjoin(gdf1,gdf2,predicate='touches',how='inner')
    for i,row in touches.iterrows():
        idx = (intersects['index_left']==i) & (intersects['index_right']==row['index_right'])
        intersects.drop(intersects[idx].index,axis=0,inplace=True)

    return intersects

def M1T1(gdf1,gdf2):
    '''
    返回gdf1中与gdf2 1-1相交（不含相接）的图斑
    '''
    intersects = intersectsOnly(gdf1,gdf2,how='inner')
    a1,b1 = np.unique(intersects['index_left'].values,return_counts=True)
    a2,b2 = np.unique(intersects['index_right'].values,return_counts=True)
    idx = a1[b1==1]
    for idxr in a2[b2>1]:
        idxl = intersects.loc[intersects['index_right']==idxr,'index_left'].values
        for i in idxl:
            idx = idx[idx!=i]
    
    intersects.set_index('index_left',inplace=True)

    return intersects.loc[idx,:]


def checkIDsMode(ogdf,ngdf,field='mode'):
    '''
    确定图斑修改模式。图斑分3类：未发生变化的图斑ID不变，发生变化但与原图斑可1-1对应的继承原ID，否则新编ID
    ogdf: gpd.GeoDataFrame 原图斑
    ngdf: gpd.GeoDataFrame 新图斑
    field: ngdf中记录修改模式的字段名
    '''
    changed = isChanged(ogdf,ngdf,precision=10)
    set1 = ngdf[changed==False] # 未发生变化的图斑
    set2 = ngdf[changed] # 发生变化的图斑

    # 未发生变化的图斑-field字段标记应为0
    idx = set1[set1[field]==0].index
    ngdf.loc[idx,'newid'] = ngdf.loc[idx,'ID']
    ngdf.loc[idx,'newtbid'] = ngdf.loc[idx,'TBID']
    idx = set1[set1[field]!=0].index
    ngdf.loc[idx,'备注'] = '无变化，疑似标记错误'

    # 发生变化的图斑按是否与原图斑1-1匹配分两类
    m11 = M1T1(set2,ogdf)
    set2['m11'] = False
    set2.loc[m11.index,'m11'] = True 
    set21 = set2[set2['m11']]
    set22 = set2[set2['m11']==False]

    # 发生变化但与原图斑可1-1对应的：field字段标记应为1
    idx = set21[set21[field]==1].index
    ngdf.loc[idx,'newid'] = m11.loc[idx,'ID_right']
    ngdf.loc[idx,'newtbid'] = m11.loc[idx,'TBID_right']
    idx = set21[set21[field]!=1].index
    ngdf.loc[idx,'备注'] = '应继承编号，疑似标记错误'

    # 发生变化且与原图斑不1-1对应的：field字段标记应为2
    idx = set22[set22[field]!=2].index
    ngdf.loc[idx,'备注'] = '应新增编号，疑似标记错误'

    return ngdf

if __name__ == '__main__':
    datapth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\外发池塘'
    os.chdir(datapth)

    orifile = '大丰区池塘图斑_ori.shp'
    newfile = '大丰区池塘图斑_20241227更新.shp'

    ogdf = gpd.read_file(orifile)
    ngdf = gpd.read_file(newfile)

    ngdf_check = checkIDsMode(ogdf,ngdf,field='mode')

    ngdf_check.to_file(newfile.replace('.shp','_check.shp'),encoding='utf-8')

