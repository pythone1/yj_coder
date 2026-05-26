import os,glob

import geopandas as gpd
import pandas as pd
import numpy as np

roifile = r'D:\图斑校核\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
ori_path = r'D:\图斑校核\current2'
outpath = r'D:\图斑校核\current2'
qx = '沭阳县'

orifiles = glob.glob(f'{ori_path}\\*_x78180_x91210_去河湖.shp')
for orifile in orifiles:
    outfile = f"{outpath}\\{os.path.basename(orifile).replace('.shp','_范围内.shp')}"
    roi = gpd.read_file(roifile)
    roi = roi[roi['NAME']==qx]
    gdf = gpd.read_file(orifile)
    roi = roi.to_crs(gdf.crs)
    gdf = gdf[gdf.geometry.intersects(roi.geometry.values[0])]
    gdf.to_file(outfile)