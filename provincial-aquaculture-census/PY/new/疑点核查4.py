import os, glob
from datetime import datetime

from CTXXTBYD import *

if __name__ == '__main__':
    ''' 输入 '''
    # 城市名
    city = '苏州市'
    county = '吴江区'
    # city = '南京市'
    # county = ''

    # 工作路径
    # datapath = f'E:\江苏省养殖池塘上图入库项目\质控检查\宿迁0311\{city}{county}'
    datapath = r'E:\全省养殖池溏上图入库普查\PY\四条鱼专项\统计\五点\0731\信息表'
    prefixlktable = r'E:\全省养殖池溏上图入库普查\填报进度统计\江苏省城市缩写-调格式.xlsx'  # 图斑编号前缀查找表
    os.chdir(datapath)

    # 根据城市名查找池塘图斑文件
    # polygon_file = glob.glob('*.gpkg')[0]
    polygon_file = r'E:\全省养殖池溏上图入库普查\项目验收\2024年12月图斑抽检结果\1311773池塘图斑及抽检图斑\0728池塘图斑.gpkg'
    yzpz_file = r'E:\全省养殖池溏上图入库普查\疑点核查\无锡市\20250402\池塘信息-1743556009602-20250402095641-无锡市-疑点统计表-全\养殖种类-江苏.xlsx'
    xlsfile = '0731吴江区.xlsx'
    roifile = None  # 按指定区域统计填报进度。None：按全部统计；str：包含分区的矢量文件名，按分区统计

    ''' 处理 '''
    # 数据连接
    sjoins, polygons, pk = mergeData(xlsfile, polygon_file)
    # # 名称疑点-所有权人非公司
    # sjoins = MCAnalysis2(sjoins)
    # 名称疑点
    sjoins = MCAnalysis(sjoins)
    # 承包期限疑点
    sjoins = contractTimeAnalysis(sjoins)
    # 同证件号不同人名 IDNUMYD
    sjoins = idnumberAndZTMCAnalysis(sjoins)
    # 多点对应同一图斑、无对应图斑；填报状态
    sjoins, polygons = locationAnalysis(sjoins, polygons)

    # # # 点不在行政区划范围内
    # # sjoins = inXZQH(sjoins,XZQH,shi=city,xian=county)
    # # # 面积疑点 MJYD
    # # sjoins = areaAnalysis1(sjoins) # 比对水面面积
    # # sjoins = areaAnalysis2(sjoins) # 比对合同面积
    # # sjoins = areaAnalysis3(sjoins) # 分析合同面积是否有未合并

    # # 排水口位置疑点 PKYD
    sjoins = pkAnalysis(sjoins, polygons, pk)
    # # 亩产量疑点 MCLYD
    sjoins = mclAnalysis(sjoins, yzpz_file)
    # # 尾水检测位置疑点 PKYD
    # # sjoins = wsAnalysis(sjoins,polygons,ws)
    # # # 养殖方式疑点 AQUATPYD
    # # sjoins = AQUATPYDAnalysis(sjoins)
    # # sjoins = Shrimp_yieldAnayesis(sjoins)

    ''' 输出 '''
    dt = datetime.now().strftime('%Y%m%d%H%M%S')
    # # 矢量排口
    # pk.drop('池塘id',axis=1).to_file(f'{xlsfile.replace(".xlsx","")}-{dt}-{city}{county}-排口点位.gpkg',encoding='utf-8', driver='GPKG')
    # # 分割图斑附疑点信息
    # polygons.drop('ID',axis=1).to_file(f'{xlsfile.replace(".xlsx","")}-{dt}-{city}{county}-池塘图斑赋疑点.gpkg',encoding='utf-8', driver='GPKG')
    # 用户填报点附疑点信息
    sjoins['池塘id'] = sjoins.index.values
    sjoins.drop('池塘id', axis=1).to_file(f'{xlsfile.replace(".xlsx", "")}-{dt}-{city}{county}-填报点赋疑点.gpkg',
                                          encoding='utf-8', driver='GPKG')
    sjoins = weishiyong_lAnalysis(sjoins)
    # 用户填报点附疑点信息-xlsx 【所有有效填报点：输出一张总表，以及乡镇分表】
    outpath = f'{xlsfile.replace(".xlsx", "")}-{dt}-{city}{county}-疑点统计表-全'
    os.makedirs(outpath, exist_ok=True)
    toExcelByQZX(outpath, sjoins.drop(columns=['geometry']), '地址')

    # # 根据填报地址、按镇统计已填报数量
    # cun,zhen = TBJDTJ2(sjoins.drop(columns=['池塘id','geometry']))
    # writer = pd.ExcelWriter(f'{outpath}\\总表_按镇统计已填报数量.xlsx')
    # cun.to_excel(writer,sheet_name='村',index=False)
    # zhen.to_excel(writer,sheet_name='镇',index=False)
    # writer.save()
    # writer.close()

    # # 用户填报点附疑点信息-xlsx 【有疑点的填报点：输出一张总表，以及乡镇分表】
    # outpath = f'{dt}-{city}{county}-疑点统计表-仅疑点'
    # idx = pd.DataFrame([True] * len(sjoins))
    # idx.index = sjoins.index
    # for c in sjoins.columns:
    #     if ('疑点' in c) & (c!='疑点信息'):
    #         idx[0] = (sjoins[c]=='无异常') & (idx[0])
    # sjoins_out = sjoins[~idx[0]]
    # os.makedirs(outpath,exist_ok=True)
    # toExcelByQZX(outpath,sjoins_out,'地址')

    # # 用户填报点附疑点信息-html
    # sjoins_map = createYDMap(sjoins.loc[:,['longitude','latitude','geometry']],polygons[polygons['位置疑点']=='未填报'],polygons[polygons['位置疑点']=='多次填报'])
    # sjoins_map.save(f'{dt}-{city}{county}-填报点位分布.html')

