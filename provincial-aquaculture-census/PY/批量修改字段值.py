import os,glob

import geopandas as gpd
import pandas as pd
import numpy as np

def editFieldByLocation(gdf,roi,field,value):
    '''根据指定区域roi修改gdf字段field为特定值value'''
    idx = gpd.sjoin(gdf,roi,how='inner',predicate='intersects').index
    gdf.loc[idx,field] = value

    return gdf

def editFieldByIndex(gdf,idx,field,value):
    '''根据指定索引idx修改gdf字段field为特定值value'''
    gdf.loc[idx,field] = value

    return gdf

def readIndex(xlsfile,col='CTBH'):
    '''从excel表格xlsfile的数据列col读取图斑索引'''
    dfs = pd.read_excel(xlsfile,sheet_name=None)
    idx = []
    for k in list(dfs.keys()):
        df = dfs[k]
        idx.append(df[col].values)
    idx = np.unique(np.hstack(idx))
    
    
    return idx

if __name__ == '__main__':
    ''' 按矢量范围修改图斑 'status' 字段为  '已上报非养殖' 或 '已上报光伏' '''
    ctfile = r'' # 池塘图斑文件
    roifile = r'' # 矢量范围文件
    outfile = r'.json' # 输出文件,geojson格式
    field = 'status' # 待修改字段
    value = '已上报非养殖' # '已上报非养殖' 或 '已上报光伏'

    gdf = gpd.read_file(ctfile)
    roi = gpd.read_file(roifile).to_crs(gdf.crs)
    gdf = editFieldByLocation(gdf,roi,field,value)
    gdf.to_file(outfile,encoding='utf-8', driver='GeoJSON')
    

    ''' 按指定图斑编号修改图斑 'status' 字段为  '已上报非养殖' 或 '已上报光伏' '''
    ctfile = r'' # 池塘图斑文件
    idxfile = r'' # 记录图斑索引的表格文件，图斑索引值记录在"CTBH"列名下
    outfile = r'.json' # 输出文件,geojson格式
    field = 'status' # 待修改字段
    value = '已上报非养殖' # '已上报非养殖' 或 '已上报光伏'

    gdf = gpd.read_file(ctfile)
    idx = readIndex(idxfile,col='CTBH')
    gdf = editFieldByIndex(gdf,idx,field,value)
    gdf.to_file(outfile,encoding='utf-8', driver='GeoJSON')
