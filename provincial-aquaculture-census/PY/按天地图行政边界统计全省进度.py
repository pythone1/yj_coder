import os, glob

from CTXXTBYD import *

if __name__ == '__main__':
    pth = r'E:\全省养殖池溏上图入库普查\填报进度统计\常州市'
    os.chdir(pth)

    ctxxfile = '常州市金坛区20250304.xlsx'
    ct_file = r'E:\全省养殖池溏上图入库普查\填报进度统计\常州市\池塘图斑.shp'
    # xzq_fle = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
    # deletes = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250123基础上删除图斑' # 要指定删除的图斑文件所在文件夹，没有要删除的写None

    sjoins, polygons, pk = mergeData(ctxxfile, ct_file, dels_file=None)
    print(f'mergeData finished')

    # 写出点矢量
    st_time = datetime.now()
    sjoins['池塘id'] = sjoins.index.values
    sjoins.to_file(f'{ctxxfile.split(".")[0]}-填报点.gpkg', encoding='utf-8', driver='GPKG')
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"写出点矢量：{np.round(spd_time / 60, 0)} 分钟")

    # 写出面矢量
    st_time = datetime.now()
    polygons.drop('ID', axis=1).to_file(f'{ctxxfile.split(".")[0]}-池塘图斑.gpkg', encoding='utf-8', driver='GPKG')
    ed_time = datetime.now()
    spd_time = (ed_time - st_time).total_seconds()
    print(f"写出面矢量：{np.round(spd_time / 60, 0)} 分钟")

    # sjoins = gpd.read_file(f'{ctxxfile.split(".")[0]}-填报点.gpkg')
    # polygons = gpd.read_file(f'{ctxxfile.split(".")[0]}-池塘图斑.gpkg')

    # xzq = gpd.read_file(xzq_fle)
    #
    # st_time = datetime.now()
    # TBJDTJ01(sjoins,f"{ctxxfile.split('.')[0]}-填报点统计.xlsx")
    # ed_time = datetime.now()
    # spd_time = (ed_time - st_time).total_seconds()
    # print(f"TBJDTJ01：{np.round(spd_time/60,0)} 分钟")
    #
    # st_time = datetime.now()
    # TBJDTJ02(polygons,xzq,f"{ctxxfile.split('.')[0]}-填报图斑统计（按填报状态）.xlsx")
    # ed_time = datetime.now()
    # spd_time = (ed_time - st_time).total_seconds()
    # print(f"TBJDTJ02：{np.round(spd_time/60,0)} 分钟")
    #
    # st_time = datetime.now()
    # TBJDTJ03(polygons,xzq,f"{ctxxfile.split('.')[0]}-填报图斑统计（按校对状态）.xlsx")
    # ed_time = datetime.now()
    # spd_time = (ed_time - st_time).total_seconds()
    # print(f"TBJDTJ03：{np.round(spd_time/60,0)} 分钟")
    #
    # # 各区县汇总的表格
    # zongbiao(f"{ctxxfile.split('.')[0]}-填报图斑统计（按校对状态）.xlsx")
