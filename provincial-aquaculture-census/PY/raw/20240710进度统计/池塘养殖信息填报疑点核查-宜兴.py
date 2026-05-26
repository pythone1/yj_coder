from CTXXTBYD_1 import *

if __name__ == '__main__':
    datapath = r'F:\20240603\20240910'
    os.chdir(datapath)

    kwords = '宜兴'
    polygon_file = glob.glob('*.shp')[0]
    
    xlsfile = '池塘信息-1725949614506.xlsx'
    
    sjoins,polygons,pk = mergeData(xlsfile,polygon_file)

    # 名称疑点
    # sjoins = MCAnalysis(sjoins)

    # 承包期限疑点
    # sjoins = contractTimeAnalysis(sjoins)

    # # 同证件号不同人名 IDNUMYD
    # sjoins = idnumberAndZTMCAnalysis(sjoins)
    
    # 多点对应同一图斑、无对应图斑；填报状态
    sjoins,polygons = locationAnalysis(sjoins,polygons)

    # 点不在行政区划范围内
    # sjoins = inXZQH(sjoins,XZQH,shi='无锡市',xian='宜兴市')

    # 面积疑点 MJYD
    # sjoins = areaAnalysis1(sjoins) # 比对水面面积
    # sjoins = areaAnalysis2(sjoins) # 比对合同面积
    # sjoins = areaAnalysis3(sjoins) # 分析合同面积是否有未合并

    # 亩产量疑点
    # sjoins = yieldAnayesis(sjoins)

    # 排水时间疑点 WSYD
    # sjoins = PSHSJAnalysis(sjoins)

    # 排水口位置疑点 PKYD
    # sjoins = pkAnalysis(sjoins,pk)

    # 养殖类型疑点 YZLXYD
    # lctable_file = r'D:\项目数据\江苏省\疑点核查\养殖种类-江苏.xlsx'
    # lctable = pd.read_excel(lctable_file,sheet_name='Sheet2',index_col='四级')
    # sjoins = YZLXAnalysis(sjoins,lctable)

    # 养殖方式疑点 AQUATPYD
    # sjoins = AQUATPYDAnalysis(sjoins)

    # 输出数据
    # 字段整理
    # zdsm_file = r'G:\xiangmu\江苏省天地图分割\填报信息分析\20240704\进度统计用\总.txt'
    # zdsm = readZDSM(zdsm_file)
    # sjoins = YDReorganize(sjoins,zdsm)
    # 用户填报点附疑点信息-geojson
    # sjoins['池塘id'] = sjoins.index.values
    sjoins.to_file('疑点分析结果1.json',encoding='utf-8', driver='GeoJSON')
    # 用户填报点附疑点信息-xlsx
    # os.makedirs('疑点分析表',exist_ok=True)
    # toExcelByQZX('疑点分析表',sjoins.drop(columns=['池塘id','geometry']),'地址')
    # # zdsm_file = r'G:\xiangmu\江苏省天地图分割\填报信息分析\20240704\进度统计用\总-宜兴.txt'
    # # zdsm = readZDSM(zdsm_file)
    # # sjoins_out = sjoins.loc[:,zdsm.values()]
    # # sjoins_out.loc[sjoins_out['水面面积疑点']=='水面面积偏差大于1亩','水面面积疑点'] = '无异常'
    # # sjoins_out.loc[sjoins_out['合同面积疑点']=='合同面积偏差大于1亩','合同面积疑点'] = '无异常'
    # # idx = (sjoins_out['名称疑点']=='无异常') & (sjoins_out['位置疑点']=='无异常') & (sjoins_out['水面面积疑点']=='无异常') & (sjoins_out['合同面积疑点']=='无异常') & (sjoins_out['池塘合并疑点']=='无异常') & (sjoins_out['亩产量疑点']=='无异常')
    # # sjoins_out = sjoins_out[~idx]
    # # os.makedirs('疑点分析表-out1',exist_ok=True)
    # # toExcelByQZX2('疑点分析表-out1',sjoins_out,'详细地址')
    # # sjoins_out.loc[sjoins_out['水面面积疑点']=='水面面积偏差大于50%','水面面积疑点'] = '无异常'
    # # sjoins_out.loc[sjoins_out['合同面积疑点']=='合同面积偏差大于50%','合同面积疑点'] = '无异常'
    # # os.makedirs('疑点分析表-out2',exist_ok=True)
    # # toExcelByQZX2('疑点分析表-out2',sjoins_out,'详细地址')
    # # # 用户填报点附疑点信息-html
    # # sjoins_map = createYDMap(sjoins.loc[:,['中心点经度','中心点纬度','geometry']],polygons[polygons['IDYD']=='未填报'],polygons[polygons['IDYD']=='多次填报'])
    # # sjoins_map.save(f'{kwords}-填报点位分布.html')
    # # # 分割图斑附疑点信息
    # polygons=polygons.drop_duplicates(subset=['geometry'])  # 删除重复的面要素
    # polygons.drop('ID',axis=1).to_file('疑点分析结果2.json',encoding='utf-8', driver='GeoJSON')
    # # pk.to_file('排口点位.shp') 
