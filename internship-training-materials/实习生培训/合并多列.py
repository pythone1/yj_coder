import os,glob

import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon


def createFishnet(bounds,interval=300,epsg=32650):
    '''
    创建渔网
    bounds： [minx,miny,maxx,maxy]
    interval: 间隔，单位：米
    '''
 
    # 设置研究区域的边界，这里以一个矩形为例
    minx, miny, maxx, maxy = bounds
 
    # 创建一个网格，每个格子的边长等于间隔
    rows = np.arange(miny, maxy + interval, interval)
    cols = np.arange(minx, maxx + interval, interval)
 
    # 创建鱼网的多边形列表
    net = []
    for y in rows:
        for x in cols:
            net.append(Polygon([(x, y), (x + interval, y), (x + interval, y + interval), (x, y + interval)]))
 
    # 将多边形列表转换为GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=net)
 
    # 设置研究区域的CRS，例如WGS 84
    crs = f'EPSG:{epsg}'
    gdf.crs = crs

    return gdf

def filterNms(gdf, scfield='st_score', threshold=0.7):
    '''
    NMS去重
    '''
    if 'area' not in gdf.columns:
        gdf['area'] = gdf.geometry.area
    gdf = gdf.sort_values('area', ascending=False).reset_index(drop=True)
    geoms = gdf.geometry
    scores = gdf[scfield].values
    index = geoms.index.values
    n = len(geoms)
    devided = np.zeros(n)
    reserves = np.array([False] * n)
    while 0 in devided:
        i = index[devided == 0][0]
        geom1 = geoms[i]
        geoms2 = geoms[geoms.intersects(geom1)]
        similar_idx = isSamilar(geoms2, geom1, threshold)
        devided[similar_idx] = 1
        if len(similar_idx) > 1:
            nmax = similar_idx[scores[similar_idx] == scores[similar_idx].max()][0]
            reserves[nmax] = True
        else:
            reserves[similar_idx] = True

    return gdf[reserves]

def isSamilar(geom2, geom1, threshold=0.7):
    '''
    判断geom1，geom2是否相似
    threshold: 如果geom1,geom2交并比大于threshold,则认为包含
    '''
    intersections = geom2.intersection(geom1)
    intersect_area = intersections.area.values
    iou = intersect_area / (geom2.area + geom1.area - intersect_area)
    intersect_ids = intersections.index.values

    return intersect_ids[iou > threshold]



datapath = r'D:\图斑校核\current2'
outpath = r'D:\图斑校核\current2'
basename = '沭阳县d5m_x78180_x91210'
os.makedirs(outpath,exist_ok=True)
os.chdir(datapath)

# 合并筛选图斑
files = glob.glob('*去河湖.shp')
glist = []
for f in files:
    gdf = gpd.read_file(f)
    glist.append(gdf)
gdf = pd.concat(glist)
gdf = filterNms(gdf, scfield='st_score', threshold=0.7)
gdf.to_file(f'{outpath}\\{basename}_去河湖.shp') 

# 创建合并范围渔网
gdf = gdf.to_crs('epsg:32650')
bounds = gdf.total_bounds.tolist()
fishnet = createFishnet(bounds,interval=300)
fishnet.to_file(f'{outpath}\\{basename}_fishnet300m.gpkg') 

files = glob.glob('*_天地图矢量提取水域.shp')
glist = []
for f in files:
    print(f)
    gdf = gpd.read_file(f)
    glist.append(gdf)
gdf = pd.concat(glist)

gdf.to_file(f'{outpath}\\{basename}_天地图矢量提取水域.shp')


