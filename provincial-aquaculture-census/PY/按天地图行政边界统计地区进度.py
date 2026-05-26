import os,glob

from CTXXTBYD import * 


if __name__ == '__main__':
    pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\20250227灌云县'
    os.chdir(pth)

    # ctxxfile = '池塘信息-淮安市淮安区202502270930.xlsx'
    # ct_file = '20250123徐州市池塘图斑_按编号附行政区属性.shp'
    # xzq_fle = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
    # # deletes = None # 要指定删除的图斑文件所在文件夹，没有要删除的写None
    # deletes = '上报删除图斑'
    # QX = '徐州市'

    # ctxxfile = '池塘信息-连云港市灌云县202502270930.xlsx'
    # ct_file = '20250123连云港市池塘图斑_按编号附行政区属性.shp'
    # xzq_fle = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
    # deletes = None
    # QX = '连云港市'

    ctxxfile = '池塘信息-扬州市-202502270930.xlsx'
    ct_file = '20250123连云港市池塘图斑_按编号附行政区属性.shp'
    xzq_fle = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
    deletes = None
    QX = '扬州市'
    
    sjoins,polygons,pk = mergeData(ctxxfile,ct_file,dels_file=deletes)
    print(f'mergeData finished')

    # 写出点矢量
    st_time = datetime.now()
    sjoins['池塘id'] = sjoins.index.values
    sjoins.to_file(f'{ctxxfile.split(".")[0]}-填报点.gpkg',encoding='utf-8', driver='GPKG')
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"写出点矢量：{np.round(spd_time/60,0)} 分钟")
    sjoins.drop('geometry',axis=1).to_excel(f'{ctxxfile.split(".")[0]}-填报点.xlsx')

    # 写出面矢量
    st_time = datetime.now()
    polygons.drop('ID',axis=1).to_file(f'{ctxxfile.split(".")[0]}-池塘图斑.gpkg',encoding='utf-8', driver='GPKG')
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"写出面矢量：{np.round(spd_time/60,0)} 分钟")

    sjoins = gpd.read_file(f'{ctxxfile.split(".")[0]}-填报点.gpkg')
    polygons = gpd.read_file(f'{ctxxfile.split(".")[0]}-池塘图斑.gpkg')

    xzq = gpd.read_file(xzq_fle)
    xzq = xzq[xzq['市']==QX]
    
    st_time = datetime.now()
    TBJDTJ01(sjoins,f"{ctxxfile.split('.')[0]}-填报点统计.xlsx")
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"TBJDTJ01：{np.round(spd_time/60,0)} 分钟")
    
    st_time = datetime.now()
    TBJDTJ02(polygons,xzq,f"{ctxxfile.split('.')[0]}-填报图斑统计（按填报状态）.xlsx")
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"TBJDTJ02：{np.round(spd_time/60,0)} 分钟")
    
    st_time = datetime.now()
    TBJDTJ03(polygons,xzq,f"{ctxxfile.split('.')[0]}-填报图斑统计（按校对状态）.xlsx")
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"TBJDTJ03：{np.round(spd_time/60,0)} 分钟")
