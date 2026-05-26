from CTXXTBYD_1 import *

if __name__ == '__main__':
    datapath = r'F:\20240603\0724\射阳'
    os.chdir(datapath)

    kwords = '射阳'
    polygon_file = glob.glob('*.shp')[0]
    print(polygon_file)
    xlsfile = '池塘信息-1721787350227.xlsx'
    
    sjoins,polygons,pk = mergeData(xlsfile,polygon_file)

    # # 名称疑点
    # sjoins = MCAnalysis(sjoins)

    # # 承包期限疑点
    # sjoins = contractTimeAnalysis(sjoins)

    # # 同证件号不同人名 IDNUMYD
    # sjoins = idnumberAndZTMCAnalysis(sjoins)
    
    # 多点对应同一图斑、无对应图斑；填报状态
    sjoins,polygons = locationAnalysis(sjoins,polygons)

    # # 点不在行政区划范围内
    # sjoins = inXZQH(sjoins,XZQH,shi='盐城市',xian='射阳县')

    # # 面积疑点 MJYD
    # sjoins = areaAnalysis1(sjoins) # 比对水面面积
    # sjoins = areaAnalysis2(sjoins) # 比对合同面积
    # sjoins = areaAnalysis3(sjoins) # 分析合同面积是否有未合并

    # # 亩产量疑点
    # sjoins = yieldAnayesis(sjoins)

    # # 排水口位置疑点 PKYD
    # sjoins = pkAnalysis(sjoins,pk)

    # # 养殖方式疑点 AQUATPYD
    # sjoins = AQUATPYDAnalysis(sjoins)

    # 根据excel表补充已填报非养殖
    xlsfile = r'F:\20240603\CTBH非养殖统计.xlsx'
    shppath = r'F:\20240603\0627\射阳\shp'
    polygons = statusAnalysis(polygons,xlsfile,shppath)
    xlsfile = r'F:\20240603\CTBH光伏统计.xlsx'
    polygons = statusAnalysis2(polygons,xlsfile,shppath)

    # 输出数据
    polygons=polygons.drop_duplicates(subset=['geometry'])  # 删除重复的面要素
    polygons.drop('ID',axis=1).to_file('疑点分析结果2-1.json',encoding='utf-8', driver='GeoJSON')
    # pk.to_file('排口点位.shp') 
