import os,glob
import shutil

import geopandas as gpd

pth0 = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘'
os.chdir(pth0)

dstpath = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\所有地方行政区划'

pthes = glob.glob('*')
for pth in pthes:
    if os.path.isdir(pth):
        files = glob.glob(f"{pth}\\*.shp")
        for f in files:
            if '图斑' not in f:
                name = os.path.basename(f)[0:-4]
                outfiles = glob.glob(f"{pth}\\{name}*")
                for outfile in outfiles:
                    shutil.copy(outfile,f"{dstpath}\\{pth}-{os.path.basename(outfile)}")