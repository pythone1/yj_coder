import os,glob

import numpy as np
import geopandas as gpd
import pandas as pd

if __name__ == '__main__':
    pth = 'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\盐城市_东台市'
    os.chdir(pth)
    name = os.path.basename(pth).split("_")[1]
    files = glob.glob(f'*{name}*行政*.shp')
    for f in files:
        gdf = gpd.read_file(f)
        zhen_col = '镇名称'
        cun_col = 'ZLDWMC'

        mc = gdf[cun_col].values
        a,b = np.unique(mc,return_counts=True)
        print(f"全域:{a[b>1]}")
        
        zhen = gdf[zhen_col].unique()
        for z in zhen:
            gdf1 = gdf[gdf[zhen_col]==z]
            mc = gdf1[cun_col].values
            a,b = np.unique(mc,return_counts=True)
            print(f"{z}:{a[b>1]}")