"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: pond_extraction.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from CTXXTBYD import *

if __name__ == '__main__':
    datapath = r'F:\20240603\0704\射阳'
    os.chdir(datapath)
    polygon_file = glob.glob('*射阳*.shp')[0]

    kwords = os.path.basename(datapath)
    
    sjoins,polygons,pk = mergeData(datapath,polygon_file)

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

    # 面积疑点 MJYD
    sjoins = areaAnalysis1(sjoins) # 比对水面面积
    sjoins = areaAnalysis2(sjoins) # 比对合同面积
    sjoins = areaAnalysis3(sjoins) # 分析合同面积是否有未合并

    # # 亩产量疑点
    # sjoins = yieldAnayesis(sjoins)

    # # 排水时间疑点 WSYD
    # sjoins = PSHSJAnalysis(sjoins)

    # # 排水口位置疑点 PKYD
    # sjoins = pkAnalysis(sjoins,pk)

    # # 养殖类型疑点 YZLXYD
    # lctable_file = r'D:\项目数据\江苏省\疑点核查\养殖种类-江苏.xlsx'
    # lctable = pd.read_excel(lctable_file,sheet_name='Sheet2',index_col='四级')
    # sjoins = YZLXAnalysis(sjoins,lctable)

    # # 养殖方式疑点 AQUATPYD
    # sjoins = AQUATPYDAnalysis(sjoins)

    # 根据excel表补充已填报非养殖
    xlsfile = r'F:\20240603\CTBH非养殖统计.xlsx'
    shppath = r'F:\20240603\0627\射阳\shp'
    polygons = statusAnalysis(polygons,xlsfile,shppath)
    xlsfile = r'F:\20240603\CTBH光伏统计.xlsx'
    polygons = statusAnalysis2(polygons,xlsfile,shppath)

    # 输出数据
    # 字段整理
    zdsm_file = r'C:\0924Sentinel处理\射阳进度统计用\总.txt'
    zdsm = readZDSM(zdsm_file)
    sjoins = YDReorganize(sjoins,zdsm)
    # sjoins = sjoins.drop(columns=['亩产量疑点'])
    # 用户填报点附疑点信息-geojson
    sjoins['池塘id'] = sjoins.index.values
    # sjoins.to_file('疑点分析结果1.json',encoding='utf-8', driver='GeoJSON')
    # # 用户填报点附疑点信息-xlsx
    # os.makedirs('疑点分析表',exist_ok=True)
    # toExcelByQZX('疑点分析表',sjoins.drop(columns=['池塘id','geometry']),'详细地址')
    # idx = (sjoins['名称疑点']=='无异常') & (sjoins['位置疑点']=='无异常') & (sjoins['水面面积疑点']=='无异常') & (sjoins['合同面积疑点']=='无异常') & (sjoins['池塘合并疑点']=='无异常')
    # sjoins_out = sjoins[~idx]
    # os.makedirs('疑点分析表-out',exist_ok=True)
    # toExcelByQZX('疑点分析表-out',sjoins_out,'详细地址')
    # # 用户填报点附疑点信息-html
    # sjoins_map = createYDMap(sjoins.loc[:,['中心点经度','中心点纬度','geometry']],polygons[polygons['IDYD']=='未填报'],polygons[polygons['IDYD']=='多次填报'])
    # sjoins_map.save(f'{kwords}-填报点位分布.html')
    # 分割图斑附疑点信息
    polygons=polygons.drop_duplicates(subset=['geometry'])  # 删除重复的面要素
    polygons.drop('ID',axis=1).to_file('疑点分析结果2-1.json',encoding='utf-8', driver='GeoJSON')
    # pk.to_file('排口点位.shp') 
