import os,glob

import geopandas as gpd

# 镇村按镇代码合并
pth = r'F:\项目数据\江苏省一池一档水产养殖基本情况普查项目\业主资料\扬州市_高邮市\三调最新镇界、村界'
os.chdir(pth)
file1 = '三调最新村界矢量数据.shp' # 村文件
file2 = '三调最新镇界矢量数据.shp' # 镇文件

gdf1 = gpd.read_file(file1)
gdf2 = gpd.read_file(file2)

zhen_col1 = '镇代码' # 村文件中镇代码的列名
zhen_col2 = 'XZQDM' # 镇文件中镇代码的列名

for i,row in gdf2.iterrows():
    idx = gdf1['镇代码']==row['XZQDM']
    gdf1.loc[idx,'镇名称'] = row['XZQMC']
    # idx = gdf1['镇代码']==row['乡镇名称']
    # gdf1.loc[idx,'镇名称'] = row['乡镇名']

gdf1.to_file('高邮市_村级行政区划.shp',encoding='utf-8') # 注意输出文件包含“行政”两个字，方便后面自动索引