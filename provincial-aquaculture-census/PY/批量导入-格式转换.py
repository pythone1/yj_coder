import os,glob

from CTXXTBYD import *

def xttableNormalize(df,gdf):
    '''
    池塘信息填报表转软件需要格式
    '''
    # 删备注信息
    df.drop(0,axis=0,inplace=True)
    # 删样例数据
    df = df[(df['养殖经营人名称*']!='张三') & (df['身份证号*']!='320625196606135164')]

    # 地址
    df['地址*'] = '江苏省-' + df['市*'] + '-' + df['县（市、区）*'] + '-' + df['乡镇（街道）*'] + '-' + df['村（社区）*']
    df.drop(columns=['市*','县（市、区）*','乡镇（街道）*','村（社区）*'],inplace=True)

    # TBID转ID、添加填报点坐标
    df = pd.merge(df,gdf.loc[:,['图斑id*','图斑编号*','池塘经纬度*']],on='图斑编号*')
    df.drop(columns=['图斑编号*'],inplace=True)

    #承包期限
    if df['承包开始时间'].isnull().all():
        df['承包期限'] = '/'
        df.drop(columns=['承包开始时间','承包结束时间'],inplace=True)
    else:
        df['承包开始时间'] = df['承包开始时间'].dt.strftime('%Y-%m-%d')
        df['承包结束时间'] = df['承包结束时间'].dt.strftime('%Y-%m-%d')
        df['承包期限'] = df['承包开始时间'] + '，' + df['承包结束时间']
        df.drop(columns=['承包开始时间','承包结束时间'],inplace=True)

    #统一社会信用代码
    df.rename(columns={
        '统一社会信用代码':'统一社会信用代码*'
    },inplace=True)  

    # 养殖品种/预计亩产量*
    df['养殖品种/预计亩产量*'] = df['养殖品种/预计亩产量*'].str.replace('：',':')

    # 尾水排放期
    df['尾水集中排放期*'] = df['尾水集中排放期*'].str.replace(',','，')

    return df

def polygonsNormalize(gdf):
    '''
    池塘图斑表格按软件重命名
    '''
    gdf.drop_duplicates(subset=['geometry'],inplace=True)
    gdf.rename(columns={
        'TBID':'图斑编号*',
        'ID':'图斑id*'
    },inplace=True)
    gdf['图斑id*'] = gdf['图斑id*'].astype('int')
    gdf['图斑编号*'] = gdf['图斑编号*'].str.replace(',','')
    gdf['centerx'] = gdf.geometry.centroid.x.round(6).astype('str')
    gdf['centery'] = gdf.geometry.centroid.y.round(6).astype('str')
    gdf['池塘经纬度*'] = gdf['centerx'] + '，' + gdf['centery']

    return gdf
    

    
if __name__ == "__main__":
    datapth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\泰州市_兴化市\0地方填报'
    ct_file = f'{os.path.dirname(datapth)}\\泰州兴化池塘.shp'
    outpath = f'{os.path.dirname(datapth)}\\0地方填报_转软件格式'
    os.chdir(datapth)
    os.makedirs(outpath,exist_ok=True)

    gdf = gpd.read_file(ct_file)
    gdf = polygonsNormalize(gdf)
    
    df_list = []
    files = glob.glob("*.xlsx")
    for f in files:
        df = pd.read_excel(f,dtype='str')
        # 规范检查
        # 转格式
        df = xttableNormalize(df,gdf)
        df_list.append(df)
    df = pd.concat(df_list,ignore_index=True)
    df.to_excel(f"{outpath}\\{f}",index=False)

