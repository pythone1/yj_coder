import os,glob

import pandas as pd
import numpy as np
import geopandas as gpd
from id_validator import validator

FIXEDVALUES = {
    '用户类别*':['养殖户','渔技员','企业工作人员','政府工作人员','其他'],
    '养殖主体类型*':['个人','集体/公司','其他'],
    '养殖状态*':['养殖','未使用'],
    '池塘所有权*':['个人','集体/公司','其他'],
    '用途*':['成品养殖','苗种培育','尾水净化','饵料培育','休闲垂钓','其他'],
    '水体类型*':['淡水','咸水','海水'],
    '养殖方式*':['池塘养殖','渔光一体','跑道鱼','其他'],
    '养殖类型*':['单养','混养'],
    '养殖水体*':['淡水养殖','海水养殖'],
    '清塘淤泥处理方式*':['不处置','边坡堆放','池塘内部堆填','外运堆肥','外运填埋','其他'],
    '尾水处理工艺*':['三池两坝','多级净化','原位修复','人工湿地','集中处理','其他'],
    '检测方式':['快检','第三方'],
    '水质指标':['悬浮物','PH','总氮','总磷','高锰酸盐'],
    '排水月份':np.array(list(range(1,14))).astype('str').tolist(),
    '池塘土地属性':['坑塘水面','耕地','基本农田','其他'],
    '有无尾水处理*':['有','无']
}

YZPZFILE = r'E:\全省养殖池溏上图入库普查\批量导入\养殖品种-20250113.xlsx'
FIXEDVALUES['养殖品种'] = pd.read_excel(YZPZFILE)['三级'].to_list()

XZQFILE = r'E:\全省养殖池溏上图入库普查\批量导入\全省行政区名20250122.xlsx'
xzq = pd.read_excel(XZQFILE)
FIXEDVALUES['地址*'] = ('江苏省' + '-' + xzq['市'] + '-' + xzq['区县'] + '-' + xzq['街道'] + '-' + xzq['村委']).to_list()

TMPFILE = r'E:\全省养殖池溏上图入库普查\批量导入\池塘导入模版-软件导入.xlsx'

BZ = '合规性检查'

def polygonsNormalize(gdf):
    '''
    池塘图斑表格按软件重命名
    '''
    # gdf.drop_duplicates(subset=['geometry'],inplace=True)
    gdf['area'] = gdf['area'] / 666.666
    gdf.rename(columns={
        'tbid':'图斑编号*',
        'id':'图斑id*',
        'area':'图斑面积'
    },inplace=True)
    gdf['图斑id*'] = gdf['图斑id*'].astype('int')
    gdf['图斑编号*'] = gdf['图斑编号*'].str.replace(',','')

    gdf['center_point'] = gdf.geometry.representative_point()
    gdf['centerx'] = gdf.center_point.x.round(6).astype('str')
    gdf['centery'] = gdf.center_point.y.round(6).astype('str')
    gdf['池塘经纬度*'] = gdf['centerx'] + '，' + gdf['centery']

    return gdf

def xttableNormalize(df,gdf):
    '''
    池塘信息填报表转软件需要格式
    '''
    # 删备注信息
    df = df[df['图斑编号*']!='对应地图上池塘编号']
    # 删样例数据
    df = df[(df['养殖经营人名称*']!='张三') & (df['身份证号*']!='320625196606135164')]
    df = df[(df['联系人*']!='李四') & (df['联系方式*']!='15062283574')]

    # 删除表格中空格、换行符
    for k in df.columns:
        if '时间' not in k:
            df[k] = df[k].str.replace('\n','').str.replace(' ','')
        else:
            df[k] = df[k].str.replace('\n','')

    # 地址
    df['地址*'] = '江苏省-' + df['市*'] + '-' + df['县（市、区）*'] + '-' + df['乡镇（街道）*'] + '-' + df['村（社区）*']
    # df.drop(columns=['市*','县（市、区）*','乡镇（街道）*','村（社区）*'],inplace=True)

    # TBID转ID、添加填报点坐标
    df = pd.merge(df,gdf.loc[:,['图斑id*','图斑编号*','池塘经纬度*','图斑面积']],on='图斑编号*',how='left')
    # df.drop(columns=['图斑编号*'],inplace=True)

    #承包期限
    df[BZ] = ''
    if df['承包开始时间'].isnull().all():
        df['承包期限'] = '/'
    else:
        st = pd.to_datetime(df['承包开始时间'],errors='coerce').dt.strftime('%Y-%m-%d')
        ed = pd.to_datetime(df['承包结束时间'],errors='coerce').dt.strftime('%Y-%m-%d')
        idx1 = ((st.isnull()) & (~df['承包开始时间'].isnull())) | ((ed.isnull()) & (~df['承包结束时间'].isnull()))
        idx1 = df[idx1].index
        df.loc[idx1,BZ] = 'ERROR-承包日期格式校验不通过\n'
        idx2 =((~st.isnull()) & (~df['承包开始时间'].isnull())) & ((~ed.isnull()) & (~df['承包结束时间'].isnull()))
        idx2 = df[idx2].index
        df.loc[idx2,'承包期限'] = st + '，' + ed

    #统一社会信用代码
    df.rename(columns={
        '统一社会信用代码':'统一社会信用代码*'
    },inplace=True)

    # 养殖品种/预计亩产量*
    df['养殖品种/预计亩产量*'] = df['养殖品种/预计亩产量*'].str.replace('：',':')
    df['养殖品种/预计亩产量*'] = df['养殖品种/预计亩产量*'].str.replace('斤','')
    df['养殖品种/预计亩产量*'] = df['养殖品种/预计亩产量*'].str.replace('\n','')

    # 尾水排放期
    df['尾水集中排放期*'] = df['尾水集中排放期*'].str.replace(',','，')
    df['尾水集中排放期*'] = df['尾水集中排放期*'].str.replace('3-5年排水','13')

    # 用户类别*
    df['用户类别*'] = df['用户类别*'].str.replace('鱼技员','渔技员')

    # 用途*
    df['用途*'] = df['用途*'].str.replace('苗种育苗','苗种培育')

    # 养殖主体类型*
    df['养殖主体类型*'] = df['养殖主体类型*'].str.replace('集团','集体')
    df['养殖主体类型*'] = df['养殖主体类型*'].str.replace('企业','公司')

    # 池塘所有权
    df['池塘所有权*'] = df['池塘所有权*'].str.replace('集团','集体')
    df['池塘所有权*'] = df['池塘所有权*'].str.replace('企业','公司')

    return df
def rowNull(df):
    '''
    整行未填
    '''
    t = (df.loc[:,'用户类别*':'第三方检测机构']!='').sum(axis=1)
    idx = df[t==1].index

    if len(idx) > 0:
        df.loc[idx,BZ] = "WARNING-未填报\n"

    return df

def requiredFieldCheck(df):
    '''
    必填项检查
    '''
    fclss = {
        '填报人': ['用户类别*','手机号码*'],
        '养殖经营人': ['养殖主体类型*','养殖经营人名称*','证件号'],
        '池塘所在地址': ['市*','县（市、区）*','乡镇（街道）*','村（社区）*'],
        '联系人': ['联系人*','联系方式*'],
        '养殖状态': ['养殖状态*'],
        '所有权人': ['池塘所有权*','池塘所有权人名称*'],
        '池塘信息': ['面积','用途*','水体类型*','养殖方式*','养殖类型*','养殖水体*','养殖品种/预计亩产量*','尾水集中排放期*','清塘淤泥处理方式*','有无尾水处理*'],
        '清塘淤泥处置': ['处置频率*'],
        '尾水处理':['尾水处理工艺*'],
        '尾水净化区面积':['尾水净化区面积*']
    }
    df['证件号'] = df['身份证号*'] + df['统一社会信用代码*']
    df['面积'] = df['合同面积*'] + df['净水面面积*']

    # 无差别必填
    for k in ['填报人','养殖经营人','池塘所在地址','联系人','养殖状态']:
        cols = fclss[k]
        t = (df.loc[:,cols]!='').sum(axis=1)
        idx = t[t<len(cols)].index
        df.loc[idx,BZ] += f"ERROR-{k}信息不全\n"

    # 养殖状态为“养殖”且用途不是休闲垂钓时的必填
    df1 = df[(df['养殖状态*']=='养殖') & (df['用途*']!='休闲垂钓')]
    for k in ['所有权人','池塘信息']:
        cols = fclss[k]
        t = (df1.loc[:,cols]!='').sum(axis=1)
        idx = t[t<len(cols)].index
        df.loc[idx,BZ] += f"ERROR-{k}信息不全\n"
    
    # 养殖状态为“养殖”且用途是休闲垂钓时的必填
    df1 = df[(df['养殖状态*']=='养殖') & (df['用途*']=='休闲垂钓')]
    fclss['池塘信息'] = ['面积','尾水集中排放期*','清塘淤泥处理方式*','有无尾水处理*']
    for k in ['所有权人','池塘信息']:
        cols = fclss[k]
        t = (df1.loc[:,cols]!='').sum(axis=1)
        idx = t[t<len(cols)].index
        df.loc[idx,BZ] += f"ERROR-{k}信息不全\n"
    
    # 养殖状态为“养殖”且用途是休闲垂钓时的应不填
    t = (df1.loc[:,'水体类型*':'是否完成池塘标准化改造*']!='').sum(axis=1)
    idx = t[t>0].index
    df.loc[idx,BZ] += f"WARNING-用途*填写休闲垂钓时【水体类型~是否完成池塘标准化改造】信息不录入\n"
    df.loc[idx,'水体类型*':'是否完成池塘标准化改造*'] = ''
    
    # 清塘淤泥处理方式*不等于“不处置”时的必填
    df2 = df1[df1['清塘淤泥处理方式*']!="不处置"]
    for k in ['清塘淤泥处置']:
        cols = fclss[k]
        t = (df2.loc[:,cols]!='').sum(axis=1)
        idx = t[t<len(cols)].index
        df.loc[idx,BZ] += f"ERROR-{k}信息不全\n"

    # 有无尾水处理*填写“有”时的必填
    df3 = df1[df1['有无尾水处理*']=="有"]
    for k in ['尾水处理']:
        cols = fclss[k]
        t = (df3.loc[:,cols]!='').sum(axis=1)
        idx = t[t<len(cols)].index
        df.loc[idx,BZ] += f"ERROR-{k}信息不全\n"
    
    # 有尾水处理、且非原位修复时的必填
    df4 = df3[df3['尾水处理工艺*']!='原位修复']
    for k in ['尾水净化区面积']:
        cols = fclss[k]
        t = (df4.loc[:,cols]!='').sum(axis=1)
        idx = t[t<len(cols)].index
        df.loc[idx,BZ] += f"ERROR-{k}信息不全\n"

    # 养殖主体类型* 为个人时，身份证号*必填
    idx = df[(df['养殖主体类型*']=='个人') & (df['身份证号*']=='')].index
    df.loc[idx,BZ] += f"ERROR-个人养殖未填写身份证号*\n"

    # 养殖主体类型* 为集体/公司时，统一社会信用代码必填
    idx = df[(df['养殖主体类型*']=='集体/公司') & (df['统一社会信用代码*']=='')].index
    df.loc[idx,BZ] += f"ERROR-集体/公司养殖未填写统一社会信用代码\n"

    # 面积大于50亩必填“是否完成池塘标准化改造*”
    idx = df[(df['图斑面积']>=50) & (df['是否完成池塘标准化改造*']=='') & (df['养殖状态*']!='未使用')].index
    df.loc[idx,BZ] += f"ERROR-50亩以上池塘未填 是否完成池塘标准化改造*\n"

    # 养殖状态*填“未使用”，后续信息应不填
    df5 = df[df['养殖状态*']=='未使用']
    t = (df5.loc[:,'池塘所有权*':'第三方检测机构']!='').sum(axis=1)
    idx = t[t>0].index
    df.loc[idx,BZ] += f"WARNING-养殖状态*填写未使用则后续信息不录入\n"

    return df


def fiexedValuesCheck(df,values):
    '''
    有固定选项的字段检查
    df: pd.DataFrame
    values: dict{
        '字段':['值1','值2'],
    }
    '''
    # 养殖品种
    t = df['养殖品种/预计亩产量*'].str.split('，',expand=True)
    yzpz_df = pd.DataFrame()
    for i in range(len(t.columns)):
        yzpz_df[f'养殖品种{i}'] = t[i].str.split(':',expand=True)[0]
    yzpz_df = yzpz_df.fillna('')
    yzpz = np.unique(yzpz_df.values)
    yzpz = yzpz[yzpz!='']
    for v in yzpz:
        if v not in values['养殖品种']:
            idx = df[(yzpz_df==v).any(axis=1)].index
            df.loc[idx,BZ] += f"ERROR-超出养殖品种规定值: {v}\n"

    # 检测指标
    t = df['检测指标'].str.split('，',expand=True)
    jczb = pd.DataFrame()
    for i in range(len(t.columns)):
        jczb[f'检测指标{i}'] = t[i].str.split('：',expand=True)[0]
    jczb = jczb.fillna('')
    jczb = np.unique(jczb.values)
    jczb = jczb[jczb!='']
    for v in jczb:
        if v not in values['水质指标']:
            idx = df['检测指标'].str.contains(v)
            df.loc[idx,BZ] += f"ERROR-超出检测指标规定值: {v}\n"

    # 排水月份
    psyf = df['尾水集中排放期*'].str.split('，',expand=True)
    psyf = psyf.fillna('')
    psyf = np.unique(psyf.values)
    psyf = psyf[psyf!='']
    for v in psyf:
        if v not in values['排水月份']:
            idx = df['尾水集中排放期*'].str.contains(v,regex=False)
            df.loc[idx,BZ] += f"ERROR-尾水集中排放期*错误: {v} \n"

    for k in list(values.keys()):
        if k in df.columns:
            vals = df[k].unique()
            vals = vals[vals!='']
            for v in vals:
                if v not in values[k]:
                    idx = df[k]==v
                    df.loc[idx,BZ] += f"ERROR-超出{k}规定值: {v}\n"
    
    return df

def TBIDCheck(df):
    '''
    TBID检查是否存在
    '''
    idx = df[df['图斑id*']==''].index
    df.loc[idx,BZ] += 'ERROR-图斑编号不存在\n'

    return df

def isIDCard(idcard):
    try:
        return validator.is_valid(idcard)
    except:
        return False

def idCardCheck(df):
    '''
    身份证校验
    '''
    # 主体身份证
    idx1 = (df['养殖主体类型*']=='个人') & (df['身份证号*'].map(isIDCard)==False)
    idx = df[idx1].index
    df.loc[idx,BZ] += 'ERROR-身份证号*校验不通过\n'
    
    # 主体统一社会信用代码
    idx2 = (df['养殖主体类型*']=='集体/公司') & (df['统一社会信用代码*'].map(len)!=18)
    idx = df[idx2].index
    df.loc[idx,BZ] += 'ERROR-统一社会信用代码*校验不通过\n'

    # 所有权人证件号码
    idx3 = (df['池塘所有权*']=='个人' ) & (df['池塘所有权人证件号码'].map(len)>0) & (df['池塘所有权人证件号码'].map(isIDCard)==False)
    idx4 = (df['池塘所有权*']=='集体/公司') & (df['池塘所有权人证件号码'].map(len)>0) & (df['池塘所有权人证件号码'].map(len)!=18)
    idx = df[idx3|idx4].index
    df.loc[idx,BZ] += 'ERROR-池塘所有权人证件号码校验不通过\n'

    return df
    
def tbidDuplicatedCheck(df):
    '''
    检查有无重复图斑id
    '''
    v = df['图斑编号*'].values
    a,b = np.unique(v,return_counts=True)
    mvs = a[b>1]

    for v in mvs:
        df.loc[df['图斑编号*']==v,BZ] += 'WARNING-图斑编号*重复\n'
    
    return df

def phnnumCheck(df):
    '''
    检查手机号
    '''
    ks = ['手机号码*','联系方式*']
    for k in ks:
        ln = df[k].str.len()
        idx = ln!=11
        df.loc[idx,BZ] += f'ERROR-{k}校验不通过\n'

    return df

def nameCheck(df):
    '''
    人名检查
    '''
    # 养殖经营人名称* 养殖主体类型*
    ln = df['养殖经营人名称*'].str.len()
    idx = (df['养殖主体类型*']=='个人') & (ln>4)
    df.loc[idx,BZ] += f'ERROR-养殖经营人名称*校验不通过\n'

    # 池塘所有权人名称* 池塘所有权*
    ln = df['池塘所有权人名称*'].str.len()
    idx = (df['池塘所有权*']=='个人') & (ln>4)
    df.loc[idx,BZ] += f'ERROR-池塘所有权人名称*校验不通过\n'

    # 联系人*
    ln = df['联系人*'].str.len()
    idx = ln>4
    df.loc[idx,BZ] += f'ERROR-联系人*校验不通过\n'

    return df

def numCheck(df,fields=['处置频率*','常水位','合同面积*','净水面面积*']):
    '''
    数值类型字段检查
    '''
    for f in fields:
        fv = pd.to_numeric(df[f],errors='coerce')
        idx1 = (df[f]!='') & (fv.isnull())
        df.loc[idx1,BZ] += f'ERROR-{f}非数值型\n'
    
    return df

if __name__ == "__main__":
    pth = r'E:\全省养殖池溏上图入库普查\宜兴\20250331宜兴未填报统计\软件导入'
    ctfile = r'E:\全省养殖池溏上图入库普查\疑点核查\常州市\20250324江苏省池塘图斑.gpkg'
    # ctfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\批量导入\淮安市_洪泽区\洪泽区池塘图斑.shp'
    os.chdir(pth)

    ct = gpd.read_file(ctfile)
    ct = polygonsNormalize(ct)
    
    files = glob.glob('*.xlsx')
    # files = glob.glob('20250214_检查.xlsx')
    print(files)
    print(len(files))

    # 多个文件合并后导入
    df_list = []
    for f in files:
        df = pd.read_excel(f,dtype='str',sheet_name=None)
        df_list.append(pd.concat(df.values(),ignore_index=True))
    df = pd.concat(df_list,ignore_index=True)
    df = xttableNormalize(df,ct)
    
    # 未填项设置为''
    for c in df.columns:
        df.loc[df[c]=='/',c] = ''
    df = df.fillna('')

    # 合规性检查
    # 图斑编号存在
    df = TBIDCheck(df)
    set0 = df[df[BZ].str.contains('图斑编号不存在')]       # TBID不存在
    df = df.drop(set0.index)    # TBID存在
    
    # 整行未填
    df = rowNull(df)
    set1 = df[df[BZ].str.contains('未填报')]   # 未填报
    set2 = df[~df[BZ].str.contains('未填报')]   # 填报
    
    # 固定选项检查
    set2 = fiexedValuesCheck(set2,FIXEDVALUES)

    # 必填项检查
    set2 = requiredFieldCheck(set2)

    # 证件号检查
    set2 = idCardCheck(set2)

    # 人名检查
    set2 = nameCheck(set2)

    # 手机号检查
    set2 = phnnumCheck(set2)

    # 图斑id重复检查
    set2 = tbidDuplicatedCheck(set2)

    # 数值类型检查
    set2 = numCheck(set2)

    # 导出检查结果
    df = pd.concat([set0,set1,set2]).sort_index()
    outfile = f"{os.path.basename(pth)}_检查.xlsx"
    df.drop(columns=['地址*','图斑id*','池塘经纬度*','图斑面积','承包期限','证件号','面积']).to_excel(outfile,index=False)

    # 导出软件需要格式
    cols = pd.read_excel(TMPFILE).columns
    outfile = f"{os.path.basename(pth)}_软件导入.xlsx"
    set2.loc[:,cols].to_excel(outfile,index=False)