import os,glob

import geopandas as gpd
import pandas as pd

if __name__ == "__main__":
    pth = r'S:\通用数据\全省水域滩涂养殖规划数据\规划图\无锡市'
    os.chdir(pth)

    file1 = '无锡市1.shp'
    file2 = '无锡市2.shp'
    file3 = '无锡市3.shp'

    gdf1 = gpd.read_file(file1)
    gdf2 = gpd.read_file(file2)
    gdf3 = gpd.read_file(file3)

    gdf = pd.concat([gdf1,gdf2,gdf3])
    gdf.to_file('无锡市_123合并.shp',encoding='utf-8')

    idx = ~gdf['行政区'].isnull()
    gdf.loc[idx,'区县'] = gdf.loc[idx,'行政区'].str[0:3]
    gdf = gdf[gdf['区县']=='宜兴市']
    gdf.to_file('无锡市_123合并_宜兴市.shp',encoding='utf-8')

