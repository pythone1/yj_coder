import os,glob
from datetime import datetime

import pandas as pd
import geopandas as gpd
import numpy as np

from CTXXTBYD import *




if __name__ == '__main__':
    '''
    按池塘图斑统计总体及各分区填报进度，例如：
    	                    已填报养殖	            已填报非养殖	        未填报
    总区域	                11662个/122175.33亩	    12923个/101961.63亩	137个/6319.2亩
    禁养区	                717个/10507.26亩	    897个/16238.51亩	4个/1062.08亩
    退养区（含太湖3公里）	1296个/26152.63亩	    1724个/29769.6亩	2个/27.31亩
    禁养区和退养区外	    9649个/85515.44亩	    10302个/55953.52亩	131个/5229.81亩
    '''
    ctfile = r'' # 池塘图斑文件, 已合并填报信息,含填报状态字段status,status分'已填报养殖','已填报非养殖','未填报'3种值
    roifile = r'' # 分区统计范围，NONE或矢量文件名，矢量文件中须有NAME字段区分不同分区
    outfile = r''
    
    gdf = gpd.read_file(ctfile)
    roi = gpd.read_file(ctfile).to_crs(gdf.crs)
    df = TBJDTJ3(gdf,roi=roifile)
    df.to_excel(outfile)
