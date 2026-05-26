import os,glob
from datetime import datetime

import geopandas as gpd
import numpy as np

orifile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250123江苏省池塘图斑_按编号附行政区属性.shp'
newfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\扬州市\20250123扬州市池塘图斑_按编号附行政区属性.shp'
shi = '扬州市'

st = datetime.now()
gdf = gpd.read_file(orifile)
ed = datetime.now()
spd = (ed - st).total_seconds()
print(f"读数据：{np.round(spd/60,2)} min")

st = datetime.now()
gdf = gdf[gdf['市']==shi]
ed = datetime.now()
spd = (ed - st).total_seconds()
print(f"筛选：{np.round(spd/60,2)} min")

st = datetime.now()
gdf.to_file(newfile,encoding='utf-8')
ed = datetime.now()
spd = (ed - st).total_seconds()
print(f"写出：{np.round(spd/60,2)} min")