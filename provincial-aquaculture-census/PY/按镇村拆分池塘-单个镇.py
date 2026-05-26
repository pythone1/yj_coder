import os,shutil

import geopandas as gpd


from CTXXTBYD import *

def generateMapByCounties(ct,xzq,cun_col,xlsfile,outpath):
    '''
    ct: gpd.GeoDataFrame 池塘图斑
    xzq: gpd.GeoDataFrame 行政区图斑
    cun_col: str 行政区中记录村名称的列名
    zhen_col: str 行政区中记录镇名称的列名
    '''
    ct['longitude'] = ct.geometry.centroid.x
    ct['latitude'] = ct.geometry.centroid.y
    for i,row in xzq.iterrows():
        geom = row.geometry
        intersects = ct[ct.intersects(geom)]
        intersects_map = createCTMap(intersects,geom)
        intersects_map.save(f'{outpath}\\{row[cun_col]}-池塘分布.html')

        workbook = openpyxl.load_workbook(xlsfile)
        sheet = workbook.active
        for j,v in enumerate(intersects['TBID'].values):
            sheet.cell(6+j,3).value = v.replace(',','')
        workbook.save(f'{outpath}\\{row[cun_col]}-池塘信息表.xlsx')

if __name__ == '__main__':
    datapth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\宿迁市_湖滨新区'
    os.chdir(datapth)
    xzqfile = '湖滨CJDCQ_同名合并.shp' # 行政区划文件
    ctfile = '湖滨新区池塘图斑.shp' # 图斑文件
    xlsfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\池塘导入模版.xlsx' # 信息填报表

    # dm_col = 'ZLDWDM' # 记录村行政代码的列名
    # cun_col = 'ZLDWMC' # 记录村名称的列名
    # zhen_col = '镇名称' # 记录镇名称的列名
    cun_col = 'ZLDWMC' # 记录村名称的列名

    xzq = gpd.read_file(xzqfile).to_crs('epsg:4490')
    ct = gpd.read_file(ctfile).to_crs('epsg:4490')

    xzq1 = xzq.dissolve(by=cun_col)
    if len(xzq1)<len(xzq):
        # 村文件有同名、同代码图斑
        print('警告：村文件有同名、同代码图斑，替换为同名同代码合并文件，注意检查确认')
        xzq1.to_file(xzqfile.replace('.shp','_同名同代码合并.shp'),encoding='utf-8')
        generateMapByCounties(ct,xzq1,cun_col,xlsfile,datapth)
    elif len(xzq1)==len(xzq):
        # 村文件无同名、同代码图斑
        generateMapByCounties(ct,xzq,cun_col,xlsfile,datapth)
    else:
        print('未知错误')

    shutil.copy(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\养殖品种-20250113.xlsx','养殖品种-20250113.xlsx')



