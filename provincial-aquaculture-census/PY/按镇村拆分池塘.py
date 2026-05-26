import os,shutil

import geopandas as gpd


from CTXXTBYD import *

if __name__ == '__main__':
    datapth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\扬州市_广陵区'
    os.chdir(datapth)
    name = os.path.basename(datapth).split("_")[1]
    # xzqfile = glob.glob(f'*{name}*村行政*.shp')[0] # 行政区划文件
    xzqfile = glob.glob(f'扬州市_广陵区_村级行政区划.shp')[0] # 行政区划文件
    ctfile = f'{name}池塘图斑_20250123.shp' # 图斑文件
    xlsfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\池塘导入模版-20250121.xlsx' # 信息填报表

    # dm_col = 'ZLDWDM' # 记录村行政代码的列名
    # cun_col = 'ZLDWMC' # 记录村名称的列名
    # zhen_col = 'xz' # 记录镇名称的列名
    dm_col = 'XZQDM'# 记录村行政代码的列名
    cun_col = 'XZQMC' # 记录村名称的列名
    zhen_col = 'XZQMC1' # 记录镇名称的列名

    xzq = gpd.read_file(xzqfile).to_crs('epsg:4490')
    ct = gpd.read_file(ctfile).to_crs('epsg:4490')

    xzq1 = xzq.dissolve(by=[dm_col,cun_col])
    if len(xzq1)<len(xzq):
        # 村文件有同名、同代码图斑
        print('警告：村文件有同名、同代码图斑，替换为同名同代码合并文件，注意检查确认')
        xzq1.to_file(xzqfile.replace('.shp','_同名同代码合并.shp'),encoding='utf-8')
        generateMapByCounties(ct,xzq1,cun_col,zhen_col,dm_col,xlsfile,datapth)
        df = XQZTable(xzq1,dm_col,cun_col,zhen_col)
    elif len(xzq1)==len(xzq):
        # 村文件无同名、同代码图斑
        generateMapByCounties(ct,xzq,cun_col,zhen_col,dm_col,xlsfile,datapth)
        df = XQZTable(xzq,dm_col,cun_col,zhen_col)
    else:
        print('未知错误')

    shutil.copy(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\养殖品种-20250113.xlsx','养殖品种-20250113.xlsx')
    df.to_excel(f'{os.path.basename(datapth).split("_")[1]}行政村名.xlsx',index=False)



