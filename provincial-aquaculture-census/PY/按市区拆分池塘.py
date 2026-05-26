import os,glob

import geopandas as gpd

if __name__ == '__main__':
    # ''' 按天地图行政区划矢量拆分'''
    # ctfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20241225江苏省池塘图斑.shp'
    # xzqfile = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'

    # name = '赣榆区'

    # ct = gpd.read_file(ctfile)
    # # xzq = gpd.read_file(xzqfile).to_crs('epsg:32650')
    # # xzq = xzq[xzq['NAME']==name]
    # # xzq = xzq.buffer(3000).to_crs(ct.crs)
    # # ct = ct[ct.intersects(xzq.values[0])]
    # xzq = gpd.read_file(xzqfile)
    # xzq = xzq[xzq['NAME']==name].to_crs(ct.crs)
    # ct = ct[ct.intersects(xzq.geometry.values[0])]
    # print(f'{name}图斑：{len(ct)}个')

    # ct.drop_duplicates(subset=['geometry']).to_file(f'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\泰州市_靖江区\{name}池塘图斑_buf3000.shp',encoding='utf-8')
    # xzq.to_file(f'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\连云港市_赣榆区\{name}行政区划.shp',encoding='utf-8')

    ''' 按给定行政区划矢量拆分'''
    ctfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250123江苏省池塘图斑.shp'
    xzqfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\扬州市\行政区划\高邮市_村级行政区划_同名合并.shp'

    ct = gpd.read_file(ctfile)
    xzq = gpd.read_file(xzqfile).to_crs(ct.crs)
    ct = gpd.sjoin(ct,xzq)

    pth0 = os.path.dirname(xzqfile)
    name = os.path.basename(pth0).split('_')[1]
    # name = os.path.basename(pth0).split('_')[0]
    ct.to_file(f'{pth0}\\{name}池塘图斑_20250123.shp',encoding='gbk')

    


