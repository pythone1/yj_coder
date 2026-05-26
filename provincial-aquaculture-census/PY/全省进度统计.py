import os,glob

from CTXXTBYD import * 



def zongbiao(xlsxfile):
    dfs = pd.read_excel(xlsxfile,sheet_name=None)
    del dfs['所有市']
    df = pd.concat(dfs.values(),ignore_index=True)
    df = df.set_index(['市','区县'])
    df.to_excel(xlsxfile.replace('.xlsx','2.xlsx'))

if __name__ == '__main__':
    pth = r'E:\全省养殖池溏上图入库普查\填报进度统计\苏州市\20250427'
    os.chdir(pth)
    ctxxfile = r"E:\全省养殖池溏上图入库普查\填报进度统计\苏州市\20250427\苏州市.xlsx"
    ct_file = r'E:\全省养殖池溏上图入库普查\填报进度统计\苏州市\20250427\20250425江苏省池塘图斑.gpkg'
    # xzq_fle = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
    xzq_fle = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250122江苏省池塘顺延编号\JiangSu_XZQH.shp'
    # deletes = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250123基础上删除图斑'
    deletes = None
    sjoins,polygons,pk = mergeData(ctxxfile,ct_file)

    # 写出矢量
    sjoins['池塘id'] = sjoins.index.values

    polygons=polygons.drop_duplicates(subset=['geometry'])  # 删除重复的面要素

    sjoins = sjoins.reset_index(drop=True)
    sjoins.to_file(f'{ctxxfile.split(".")[0]}-填报点.gpkg',encoding='utf-8', driver='GPKG')
    polygons.drop('ID',axis=1).to_file(f'{ctxxfile.split(".")[0]}-池塘图斑.gpkg',encoding='utf-8', driver='GPKG')
    print(f'write gpkg finished')
    sjoins = gpd.read_file(f'{ctxxfile.split(".")[0]}-填报点.gpkg')
    polygons = gpd.read_file(f'{ctxxfile.split(".")[0]}-池塘图斑.gpkg')

    xzq = gpd.read_file(xzq_fle)
    xzq = xzq[xzq['市']=='苏州市']

    st_time = datetime.now()
    TBJDTJ01(sjoins,f"{ctxxfile.split('.')[0]}-填报点统计.xlsx")
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"TBJDTJ01：{np.round(spd_time/60,0)} 分钟")

    st_time = datetime.now()
    TBJDTJ02(polygons,xzq,f"{ctxxfile.split('.')[0]}-填报图斑统计（按填报状态）.xlsx",deletes)
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"TBJDTJ02：{np.round(spd_time/60,0)} 分钟")

    st_time = datetime.now()
    TBJDTJ03(polygons,xzq,f"{ctxxfile.split('.')[0]}-填报图斑统计（按校对状态）.xlsx",deletes)
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"TBJDTJ03：{np.round(spd_time/60,0)} 分钟")

    zongbiao(f"{ctxxfile.split('.')[0]}-填报图斑统计（按填报状态）.xlsx")
    zongbiao(f"{ctxxfile.split('.')[0]}-填报图斑统计（按校对状态）.xlsx")