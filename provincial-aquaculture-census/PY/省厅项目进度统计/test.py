import os,glob

import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.ops import unary_union


import numpy as np

pth = r'E:\江苏省养殖池塘上图入库项目\进度统计\全省进度\20250327'
os.chdir(pth)
files = glob.glob(f"池塘信息表\\*.xlsx")
df_list = []
for f in files:
    print(f"read {f}")
    df_list.append(pd.read_excel(f, dtype=str, skiprows=1))
ctxx = pd.concat(df_list,ignore_index=True)