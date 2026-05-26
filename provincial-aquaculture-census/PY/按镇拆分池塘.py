import os,shutil

import geopandas as gpd

from CTXXTBYD import *

def generateMapByZhen(ct,xzq,zhen_col,xlsfile,datapth):
    '''
    按镇拆分池塘
    '''
    ct.drop_duplicates(subset=['geometry'],inplace=True)
    ct['longitude'] = ct.geometry.centroid.x
    ct['latitude'] = ct.geometry.centroid.y
    df = pd.DataFrame()
    for i,row in xzq.iterrows():
        geom = row.geometry
        intersects = ct[ct['地址'].str.contains(str(row[zhen_col]), na=False)]
        df.loc[i,'镇'] = row[zhen_col]
        df.loc[i,'池塘数量'] = len(intersects)
        intersects_map = createCTMap(intersects,geom)
        os.makedirs('镇池塘图斑及信息表',exist_ok=True)
        intersects_map.save(f'{datapth}\\镇池塘图斑及信息表\\{row[zhen_col]}-池塘分布.html')

        workbook = openpyxl.load_workbook(xlsfile)
        sheet = workbook.active
        for j,v in enumerate(intersects['TBID'].values):
            sheet.cell(6+j,3).value = v.replace(',','')
        workbook.save(f'{datapth}\\镇池塘图斑及信息表\\{row[zhen_col]}-池塘信息表.xlsx')
    df.to_excel(f'{datapth}\\池塘数量统计.xlsx')


if __name__ == '__main__':
    datapth = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250611\武进区'
    os.chdir(datapth)
    # name = os.path.basename(datapth).split("_")[1]
    name = '武进区'
    xzqfile = glob.glob(f'{name}.shp')[0] # 行政区划文件
    ctfile = f'{name}池塘.gpkg' # 图斑文件
    xlsfile = r'F:\xiangmu\20241225全省池塘问题核查\无锡市_梁溪区\池塘导入模版.xlsx' # 信息填报表

    zhen_col = '镇名称' # 记录镇名称的列名

    xzq = gpd.read_file(xzqfile).to_crs('epsg:4490')
    ct = gpd.read_file(ctfile).to_crs('epsg:4490')

    generateMapByZhen(ct,xzq,zhen_col,xlsfile,datapth)
    
    # shutil.copy(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\养殖品种-20250113.xlsx','养殖品种-20250113.xlsx')



