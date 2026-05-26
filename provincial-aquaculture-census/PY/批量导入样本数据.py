import shutil

from CTXXTBYD import *

if __name__ == "__main__":
    datapth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\徐州市_丰县'
    os.chdir(datapth)
    xzqfile = '丰县行政区划.shp' # 行政区划文件
    ctfile = '丰县池塘图斑.shp' # 图斑文件
    xlsfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\池塘导入模版.xlsx' # 信息填报表

    xzq = gpd.read_file(xzqfile).to_crs('epsg:4490')
    ct = gpd.read_file(ctfile).to_crs('epsg:4490')

    generateMapByDistrict(ct,xzq,xlsfile,datapth)

    gdf = gpd.read_file('丰县池塘图斑.shp')
    df = pd.read_excel('池塘信息表.xlsx')

    df.drop([0,1,2,3],inplace=True)

    df['地址*'] = '江苏省-' + df['市*'] + '-' + df['县（市、区）*'] + '-' + df['乡镇（街道）*'] + '-' + df['村（社区）*']
    df.drop(columns=['市*','县（市、区）*','乡镇（街道）*','村（社区）*'],inplace=True)

    gdf.rename(columns={
        'TBID':'图斑编号*',
        'ID':'图斑id*'
    },inplace=True)
    gdf['图斑编号*'] = gdf['图斑编号*'].str.replace(',','')
    gdf['centerx'] = gdf.geometry.centroid.x.round(6).astype('str')
    gdf['centery'] = gdf.geometry.centroid.y.round(6).astype('str')
    gdf['池塘经纬度*'] = gdf['centerx'] + '，' + gdf['centery']
    df = pd.merge(df,gdf.loc[:,['图斑id*','图斑编号*','池塘经纬度*']],on='图斑编号*')

    # df['承包开始时间'] = df['承包开始时间'].dt.strptime('%Y-%m-%d')
    # df['承包结束时间'] = df['承包结束时间'].dt.strptime('%Y-%m-%d')
    # df['承包期限'] = df['承包开始时间'] + '，' + df['承包结束时间']
    df['承包期限'] = '2025-01-01，2028-01-01'
    df.drop(columns=['承包开始时间','承包结束时间'],inplace=True)

    df.rename(columns={
        '统一社会信用代码':'统一社会信用代码*'
    },inplace=True)  

    df.to_excel('池塘信息表_软件.xlsx',index=False)

