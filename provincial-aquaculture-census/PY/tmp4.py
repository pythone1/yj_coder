import os,glob

import pandas as pd
import geopandas as gpd
import numpy as np

# file = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\总体进度\池塘信息-202502141300.xlsx'
# df = pd.read_excel(file,skiprows=1,dtype='str')

# df1 = df[df['地址'].str.contains('盐都区')]
# df2 = df[df['地址'].str.contains('亭湖区')]

# print('1')

# 盐都区重复填报点数
file = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\总体进度\池塘信息-202502141300-填报点.gpkg'
gdf = gpd.read_file(file)
vls = gdf['图斑id']
a,b = np.unique(vls,return_counts=True)
print(len(a[b>1]))