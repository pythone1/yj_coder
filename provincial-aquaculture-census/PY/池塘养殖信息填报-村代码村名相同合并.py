import os,glob
import geopandas as gpd

## 同名合并
pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\扬州市_广陵区'
os.chdir(pth)

files = glob.glob("*扬州市_广陵区_村级行政区划.shp")
for f in files:
    gdf = gpd.read_file(f)
    # gdf1 = gdf.dissolve(by=['ZLDWDM','ZLDWMC']) # 分别为村代码、村名称的列名
    gdf1 = gdf.dissolve(by=['XZQDM','XZQMC'])
    # gdf1 = gdf.dissolve(by=['ASCRIPTION'])
    gdf1.to_file(f.replace('.shp','_同名合并.shp'),encoding='utf-8')