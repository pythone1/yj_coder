import shutil

from CTXXTBYD import *

if __name__ == "__main__":
    datapth = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250611\武进区\池塘按照镇拆分\去除未使用虾蟹'
    os.chdir(datapth)
    xzqfile = r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250611\武进区\武进区.gpkg' # 行政区划文件

    xlsfile = r'F:\xiangmu\20241225全省池塘问题核查\无锡市_梁溪区\池塘导入模版.xlsx' # 信息填报表
    xzq = gpd.read_file(xzqfile).to_crs('epsg:4490')


    ctfiles = glob.glob(r'E:\全省养殖池溏上图入库普查\养殖信息统计\20250611\武进区\池塘按照镇拆分\去除未使用虾蟹\*.gpkg')
    for ctfile in ctfiles:
        name = os.path.splitext(os.path.basename(ctfile))[0]
        ct = gpd.read_file(ctfile).to_crs('epsg:4490')
        generateMapByDistrict(ct,xzq,xlsfile,datapth,name)

    # shutil.copy(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\养殖品种-20250113.xlsx','养殖品种-20250113.xlsx')