import os,glob

import pandas as pd
import geopandas as gpd

pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑'
os.chdir(pth)

xlsfile = '江苏省城市缩写.xlsx'
shpfile = '20250123江苏省池塘图斑.shp'

df = pd.read_excel(xlsfile)
gdf = gpd.read_file(shpfile)

df['市区缩写'] = df['市区缩写'].upper()

for i,row in df.iterrows():
    idx = gdf[gdf['TBID'].startswith(row['市区缩写'])].index
    gdf.loc[idx,'市'] = row['市']
    gdf.loc[idx,'NAME'] = row['区县']

gdf.to_file(shpfile.replace('.shp','按编号附行政区属性.shp'),encoding='utf-8')
