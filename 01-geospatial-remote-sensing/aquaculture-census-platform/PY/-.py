"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: -.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os

import pandas as pd

pth = r'E:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\进度统计'
os.chdir(pth)

xlsfile = '池塘信息-202503062100--填报图斑统计（按校对状态）-未填报图斑对应地方行政区划.xlsx'
name = '浦口区'
df = pd.read_excel(xlsfile,index_col=[0,1])
df['区县'] = df.index.get_level_values(1)
idx1 = df['区县'].str.contains(name)
idx2 = df['地方区划'].str.contains(name)
idx = idx1 | idx2
df.loc[idx,:].drop(columns=['区县']).to_excel(xlsfile.replace('.xlsx',f'-{name}.xlsx'))