import os,glob
import geopandas as gpd
import numpy as np
import pandas as pd

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

# ''' 按点提取多边形1: 同数据来源 '''
# datapath = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\图像分割\tmp\addpts'
# orifile = f'{datapath}\\赣榆区d5m_x0_x58635_去河湖.shp' # 人工删减编辑后的矢量文件
# pointfile = f'{datapath}\\补点.shp' # 人工标记需要补图斑的点文件
# polygonfiles = glob.glob(f'{datapath}\\*_天地图矢量提取水域.gpkg') # 补充图斑数据来源
# outfile = f'{datapath}\\\赣榆区d5m_x0_x58635_去河湖_人工修正1.gpkg' # 输出文件

# ori_gdf = gpd.read_file(orifile).to_crs('epsg:32650')
# gdf_list = [ori_gdf]

# points = gpd.read_file(pointfile).to_crs('epsg:32650')
# for polygonfile in polygonfiles:
#     print(f'reading {polygonfile}')
#     selected_idx = []
#     polygons = gpd.read_file(polygonfile).to_crs('epsg:32650')

#     selected0 = gpd.sjoin(polygons,points,predicate='contains')
#     for i in selected0['index_right'].values:
#         idx = selected0[selected0['index_right'] == i]['area'].idxmin()
#         selected_idx.append(idx)
#     selected = polygons.loc[np.unique(selected_idx),:]
#     gdf_list.append(selected)

# results = pd.concat(gdf_list)
# results = results.drop_duplicates()
# results['area'] = results.geometry.area
# results = filterNms(results,'area',0.7)
# results.geometry = results.geometry.simplify(tolerance=0.5)
# results.to_file(outfile,encoding='utf-8')


''' 按点提取多边形2: 不同数据来源 '''
orifile = r'D:\图斑校核\江苏省_常州市_溧阳市\溧阳市d5m_x84695_去河湖.shp' # 人工删减编辑后的矢量文件
pointfile = r'D:\图斑校核\point.shp' # 人工标记需要补图斑的点文件
polygonfiles = glob.glob(r'D:\图斑校核\江苏省_常州市_溧阳市\溧阳市d5m_x84695_去重.shp') # 补充图斑数据来源
outfile = r'D:\图斑校核\江苏省_常州市_溧阳市\溧阳市d5m_x84695_去河湖_补图斑.shp' # 输出文件

gdf_list = []
for polygonfile in polygonfiles:
    print(f'reading {polygonfile}')
    polygons = gpd.read_file(polygonfile)
    polygons = polygons.to_crs('epsg:32650')
    if 'index_right' in polygons.columns:
        polygons = polygons.drop('index_right',axis=1)
    gdf_list.append(polygons)
polygons = pd.concat(gdf_list,ignore_index=True)
polygons['area'] = polygons.geometry.area

print('筛选图斑...')
points = gpd.read_file(pointfile)
points = points.to_crs('epsg:32650')
selected0 = gpd.sjoin(polygons,points,predicate='contains')
selected_idx = []
for i in selected0['index_right'].values:
    idx = selected0[selected0['index_right'] == i]['area'].idxmin()
    selected_idx.append(idx)
selected = polygons.loc[np.unique(selected_idx),:]

print('拼接去重...')
ori_gdf = gpd.read_file(orifile)
results = pd.concat([ori_gdf,selected],ignore_index=True)
results = results.drop_duplicates()
results = results[results.geometry.is_valid]
results['area'] = results.geometry.area
results = filterNms(results,'area',0.7)
results.to_file(outfile,encoding='utf-8')

