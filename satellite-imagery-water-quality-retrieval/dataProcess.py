from operator import index
import os
import glob
from matplotlib.pyplot import axes
import pandas as pd
import numpy as np

import geopandas as gpd
import fiona
import geotable
from shapely import wkt
from coord_convert.transform import gcj2wgs,bd2wgs
import pdfplumber

#手动启东KML驱动程序
fiona.supported_drivers['KML'] = 'rw'

def extractTablesFromPDF(pdffile,st_page,ed_page,header_num,header_repeat=True,rows_merge=True):
    '''
    功能：从PDF提取表格
    pdffile: pdf文件
    header_num: int 列名所占行数
    header_repeat: bool 表头是否有重复
    rows_merge: bool 是否根据首列是否为''判断是否与上一行内容合并
    '''
    dfs = []    
    
    with pdfplumber.open(pdffile) as pdf:     
        pages = pdf.pages[st_page-1:ed_page]
        if header_repeat: 
            for page in pages:
                rows = page.extract_table()
                dfs.append(pd.DataFrame(rows[header_num:],columns=rows[0:header_num]))                   
        else:
            for i,page in enumerate(pages):
                rows = page.extract_table()
                if i == 0:
                    dfs.append(pd.DataFrame(rows[header_num:],columns=rows[0:header_num]))
                else:
                    dfs.append(pd.DataFrame(rows,columns=dfs[0].columns))

    # 合并
    df = pd.concat(dfs,axis=0,ignore_index=True)
    if rows_merge:
        idx = df.index[df.iloc[:,0]==''].tolist()
        for i in idx:
            df.loc[i-1,:] = df.loc[i-1,:] + df.loc[i,:]
            df = df.drop([i],axis=0)    
        df = df.reset_index(drop=True)

    return df

def tablesMerge(dfs_dict,idnt_col='worksheet'):
    '''
    功能：表格合并
    dfs_dict: dict 待合并的多个表格。key为表名或文件名，value为pd.DataFrame对象
    idnt_col：str 合并后的表格会新增一属性列区分数据属于哪一张表，idnt_col为该属性列名
    返回：pd.DataFrame 合并后的表格
    '''
    sheetnames = list(dfs_dict.keys())
    dfs = []
    for sheetname in sheetnames:
        df = dfs_dict[sheetname]
        df[idnt_col] = sheetname
        print(df.columns)
        dfs.append(df)

    newdf = pd.concat(dfs, axis=0, ignore_index=True)

    return newdf

def extractAndConvertCoordinates(rawcol,coord_patt,coord_range=(0,180)):
    '''
    功能：从混合文本中提取经度/纬度数值，并统一转换为以°为单位的数值
    rawcol：pd.Series 原始混合文本
    coord_patt: 正则表达式。从原始文本筛选有效文本的规则，主要用于剔除与经纬度无关的数值
    coord_range: 坐标的合理范围。
    返回：new_coord_df pd.DataFrame 共6列，分别为 原始混合文本、度、分、秒、总和、提取异常标记
    '''
    # 原始文本预处理：剔除空格、换行符
    rawcol = rawcol.astype('string')
    rawcol = rawcol.str.replace('\n', '')
    rawcol = rawcol.str.replace(' ', '')
    print("rawcol: ", type(rawcol), '\n', rawcol)

    # 按照coor_patt的规则，提取与经纬度相关的文本
    raw_coord_df = rawcol.str.extract(coord_patt)
    print('raw_coor_df: ', type(raw_coord_df), '\n', raw_coord_df)

    # 从经纬度相关的混合文本中提取数字。
    # 注意extractall返回的是多重索引的df对象，第一重索引为rawcol的行索引，第二重为度、分、秒（或只有度)，列值为rawcol每行的度分秒数值
    raw_coord_series = raw_coord_df.loc[:, 0].str.extractall(r'(\d*\.*\d+)').loc[:, 0].astype('float')
    print('raw_coord_series: ', type(raw_coord_series), '\n', raw_coord_series)
    # 将多重索引重组为常规的一层索引，并记录在新的df对象中
    new_coord_df = pd.DataFrame(0, index=range(len(rawcol)), columns=['度', '分', '秒'])
    idx_level2_num = len(set(list(raw_coord_series.index.get_level_values(1))))  # 第二重索引的类型数量
    print(idx_level2_num)
    if idx_level2_num >= 3:
        new_coord_df['度'] = raw_coord_series[:, 0]
        new_coord_df['分'] = raw_coord_series[:, 1]
        new_coord_df['秒'] = raw_coord_series[:, 2]
    elif idx_level2_num == 2:
        new_coord_df['度'] = raw_coord_series[:, 0]
        new_coord_df['分'] = raw_coord_series[:, 1]
    elif idx_level2_num == 1:
        new_coord_df['度'] = raw_coord_series[:, 0]
    print('new_coord_df: ', type(new_coord_df), '\n', new_coord_df)

    # 将提取数值统一转换为以°为单位的数值
    new_coord_df = new_coord_df.fillna(0)
    new_coord_df['总和'] = new_coord_df['度'] + new_coord_df['分'] / 60 + new_coord_df['秒'] / 3600

    # 通过转换后数值的范围判断提取是否合理
    idx = np.logical_or(new_coord_df['总和'] > coord_range[1], new_coord_df['总和'] < coord_range[0])
    new_coord_df.loc[idx, '提取结果'] = '提取失败'

    # 在新表中插入原始列作为参考
    new_coord_df.insert(0, '原文本', rawcol)

    return new_coord_df

def extractDigitAndUnits(rawcol,contain_unit=True):
    '''
    功能：从混合文本中提取数值和单位
    rawcol：pd.Series 原始混合文本
    返回：new_df pd.DataFrame 共3列，分别为 原始混合文本、数值、单位、提取异常标记
    '''
    # 存放提取文本的df
    new_df = pd.DataFrame([],index=range(len(rawcol)))

    # 原始文本预处理：剔除空格、换行符
    rawcol = rawcol.astype('string')
    rawcol.str.replace('\n','')
    rawcol.str.replace(' ','')
    new_df['原文本'] = rawcol    

    # 提取数值
    digit_df = rawcol.str.extract(r'(\d*\.*\d+)')
    new_df['数值'] = digit_df.loc[:,0].astype('float')

    # 提取单位。将跟在数值后面的非数值作为单位
    if contain_unit:
        unit_df = rawcol.str.extract(r'(\d*\.*\d+\D*)')
        unit_df = unit_df.loc[:,0].str.extract(r'([^\.|\d]+)')
        new_df['单位'] = unit_df.loc[:,0].str.strip()

    # 标记提取异常的记录
    # 异常1：单元格内 有多个数字
    digit_df = rawcol.str.extractall(r'(\d*\.*\d+)')    
    digit_num = len(set(list(digit_df.index.get_level_values(1))))
    if digit_num > 1:
        idx = digit_df.index.get_loc_level(key=1,level=1)
        idx = idx[1]
        new_df.loc[idx,'提取结果'] = '提取异常'
    # 异常2：单元格内无数字提取出来
    idx = new_df['数值'].isnull()
    new_df.loc[idx,'提取结果'] = '提取异常'

    return new_df


def coordConvert_xls(orifile,sheetname,lon_col,lat_col,transformation='gcj2wgs'):
    '''
    功能：表格数据的坐标转换（百度、高德转WGS1984）
    '''
    df = pd.read_excel(orifile,sheet_name=sheetname)
    col_dict = {lon_col: '经度', lat_col: '纬度'}
    df.rename(columns=col_dict, inplace=True)

    if transformation == 'gcj2wgs':
        t = [gcj2wgs(coordinate[0], coordinate[1]) for coordinate in list(zip(df['经度'], df['纬度']))]
    elif transformation == 'bd2wgs':
        t = [bd2wgs(coordinate[0], coordinate[1]) for coordinate in list(zip(df['经度'], df['纬度']))]
    df['经度'], df['纬度'] = list(zip(*t))
    df = df.round({'经度':6,'纬度':6})

    return df

def coordConvert_vector(orifile,transformation='gcj2wgs'):
    '''
    功能：矢量数据的坐标转换（百度、高德转WGS1984）
    orifile: 原文件
    transformation： str 转换类型. 包括 gcj2wgs bd2wgs
    返回：坐标更新后的gdf对象
    '''
    # 判断文件格式
    user_format = os.path.basename(orifile).split('.')[1]

    # 读文件
    if user_format in ['shp','json']:
        gdf = gpd.read_file(orifile)
    elif user_format in ['kml','kmz']:
        gtb = geotable.load(orifile)
        gdf = gtb2gdf(gtb)

    # 判断矢量类型
    geom_type = gdf.geom_type[0]

    # 根据矢量类型选择转换方式
    if 'Point' not in geom_type:
        if transformation == 'gcj2wgs':
            gdf = gcj2wgs_poly(gdf)
        elif transformation == 'bd2wgs':
            gdf = bd2wgs_poly(gdf)
    else:
        if transformation == 'gcj2wgs':
            gdf = gcj2wgs_point(gdf)
        elif transformation == 'bd2wgs':
            gdf = bd2wgs_point(gdf)

    return gdf

def gcj2wgs_poly(gdf):
    '''
    功能：针对面要素、线要素的坐标转换
    gdf: geopandas.GeoDataframe
    geom_col：str geometry对象的列名
    返回：坐标值更新后的gdf
    '''
    # 原坐标的wkt
    gdf['wkt_str'] = [geom.wkt for geom in gdf['geometry']]   # geometry对象转WKT，方便取坐标值

    # 从原坐标WKT提取坐标数值并依次转换
    gdf['coord_str'] = [wkt_str.split('((')[1].split('))')[0] for wkt_str in gdf['wkt_str']]    # 从WKT截取坐标部分
    for idx in gdf.index:
        new_wkt_str = ''
        coord_str = gdf.loc[idx,'coord_str']
        coord_list = coord_str.split(', ')  # 多个坐标的数值序列
        for coord in coord_list:            # 单个坐标的数值序列
            coord = list(map(float,coord.split(' ')))
            new_coord = gcj2wgs(coord[0],coord[1])          # 坐标转换
            new_wkt_str = new_wkt_str + str(new_coord[0]) + ' ' + str(new_coord[1]) + ','   # 拼接新坐标的WKT
        new_wkt_str = 'POLYGON ((' + new_wkt_str[0:-1] + '))'
        gdf.loc[idx,'new_wkt_str'] = new_wkt_str

    # 坐标更新，删除多余列
    gdf['geometry'] = gdf['new_wkt_str'].apply(wkt.loads)
    gdf = gdf.drop(['wkt_str','coord_str','new_wkt_str'],axis=1)

    return gdf

def bd2wgs_poly(gdf):
    '''
    功能：针对面要素、线要素的坐标转换
    gdf: geopandas.GeoDataframe
    geom_col：str geometry对象的列名
    返回：坐标值更新后的gdf
    '''
    # 原坐标的wkt
    gdf['wkt_str'] = [geom.wkt for geom in gdf['geometry']]   # geometry对象转WKT，方便取坐标值

    # 从原坐标WKT提取坐标数值并依次转换
    gdf['coord_str'] = [wkt_str.split('((')[1].split('))')[0] for wkt_str in gdf['wkt_str']]    # 从WKT截取坐标部分
    for idx in gdf.index:
        new_wkt_str = ''
        coord_str = gdf.loc[idx,'coord_str']
        coord_list = coord_str.split(', ')  # 多个坐标的数值序列
        for coord in coord_list:            # 单个坐标的数值序列
            coord = list(map(float,coord.split(' ')))
            new_coord = bd2wgs(coord[0],coord[1])          # 坐标转换
            new_wkt_str = new_wkt_str + str(new_coord[0]) + ' ' + str(new_coord[1]) + ','   # 拼接新坐标的WKT
        new_wkt_str = 'POLYGON ((' + new_wkt_str[0:-1] + '))'
        gdf.loc[idx,'new_wkt_str'] = new_wkt_str

    # 坐标更新，删除多余列
    gdf['geometry'] = gdf['new_wkt_str'].apply(wkt.loads)
    gdf = gdf.drop(['wkt_str','coord_str','new_wkt_str'],axis=1)

    return gdf

def gcj2wgs_point(gdf):
    '''
    功能：针对点要素的坐标转换
    gdf: geopandas.GeoDataframe
    geom_col：str geometry对象的列名
    返回：坐标值更新后的gdf
    '''
    ori_lon = gdf['geometry'].x
    ori_lat = gdf['geometry'].y

    for idx in gdf.index:
        new_lon,new_lat = gcj2wgs(ori_lon[idx],ori_lat[idx])
        gdf.loc[idx,'new_wkt'] = 'POINT (' + str(new_lon) + ' ' + str(new_lat) + ')'

    gdf['geometry'] = gdf['new_wkt'].apply(wkt.loads)
    gdf = gdf.drop(['new_wkt'],axis=1)

    return gdf

def bd2wgs_point(gdf):
    '''
    功能：针对点要素的坐标转换
    gdf: geopandas.GeoDataframe
    geom_col：str geometry对象的列名
    返回：坐标值更新后的gdf
    '''
    ori_lon = gdf['geometry'].x
    ori_lat = gdf['geometry'].y

    for idx in gdf.index:
        new_lon, new_lat = bd2wgs(ori_lon[idx], ori_lat[idx])
        gdf.loc[idx, 'new_wkt'] = 'POINT (' + str(new_lon) + ' ' + str(new_lat) + ')'

    gdf['geometry'] = gdf['new_wkt'].apply(wkt.loads)
    gdf = gdf.drop(['geometry'], axis=1)

    return gdf

def gtb2gdf(gtb):
    '''
    功能：geotable对象转为geopandas对象
    gtb: geotable.load(kmlfile)
    返回：gdf
    '''
    gdf = gpd.GeoDataFrame([],crs='EPSG:4326')

    # 复制一般属性列
    columns = gtb.columns
    for col in columns:
        if col not in ['geometry_object','geometry_layer','geometry_proj4']:
            gdf[col] = gtb[col]

    # 复制几何属性列
    gdf['geometry'] = [geom.wkt for geom in gtb['geometry_object']]
    gdf['geometry'] = gdf['geometry'].apply(wkt.loads)

    return gdf

def isColumnsExist(columns_df,reflist,Eng_col='英文字段'):
    '''
    功能：判断列名是否为标准库中已存在的字段
    columns_df: pd.DataFrame 待判定的字段表
    Eng_col： 指定存放英文字段的列索引
    reflist: list 标准库中已存在的字段列表
    返回：pd.DataFrame 在columns_df上增加一列，标记库中不存在的字段
    '''
    for i in columns_df.index:
        if columns_df.loc[i,Eng_col] in reflist:
            columns_df.loc[i,'是否为标准库中字段名'] = '是'
        else:
            columns_df.loc[i,'是否为标准库中字段名'] = '否'
    
    return columns_df

def extractXlsColumns(xlsfile,sheetname=None):
    '''
    功能：从xlsfile提取列名
    xlsfile: 待提取的表格文件
    sheetname: 待提取sheet,None提取所有表，list提取[]内所有表格
    返回：pd.DataFrame ['要素类', '英文字段']
    '''
    colnames = []
    features = []

    dfs_dict = pd.read_excel(xlsfile,sheet_name=sheetname)
    sheetnames = list(dfs_dict.keys())

    for sheetname in sheetnames:
        df = dfs_dict[sheetname]
        colnames.extend(df.columns.tolist())
        features.extend([sheetname]*len(df.columns))
    
    columns_df = pd.DataFrame([],columns=['要素类', '英文字段'])
    columns_df['要素类'] = features
    columns_df['英文字段'] = colnames

    return columns_df
        
def extractSHPColumns(shppath):
    '''
    功能：从Shapefiles提取列名
    shppath: Shapefiles存放路径
    返回：pd.DataFrame ['要素类', '英文字段']
    ''' 
    os.chdir(shppath)
    shpfiles = glob.glob("*.shp")

    # 提取要素-英文列名
    colnames_eng = []
    featurenames = []
    for shpfile in shpfiles:
        gdf = gpd.read_file(shpfile)
        colnames_eng.extend(list(gdf.columns.values))

        featurename = shpfile[0:-4].replace('静态数据', '')
        featurenames.extend([featurename] * len(gdf.columns.values))

    columns_df = pd.DataFrame([], columns=['要素类', '英文字段'])
    columns_df['要素类'] = featurenames
    columns_df['英文字段'] = colnames_eng

    columns_df = columns_df[~columns_df['英文字段'].isin(['geometry'])]

    return columns_df

def setCordinatesPrecision(gdf,precision=6):
    '''
    功能：设置坐标小数点后位数
    shpfile: gaopandas对象
    precision: 小数点精度
    返回：修改后的gdf
    '''
    x = gdf['geometry'].x.round(int(precision)).astype('str')
    y = gdf['geometry'].y.round(int(precision)).astype('str')
    for i in range(len(x)):
        gdf.loc[i,'wkt_str'] = '(' + x[i] + ' ' + y[i] + ')'

    gdf['geometry'] = gdf['wkt_str'].apply(wkt.loads)
    gdf = gdf.drop(['wkt_str'], axis=1)

    return gdf

def addCityCode(data_gdf,city_gdf,citycode_df):
    '''
    功能：给几何对象添加城市编码
    data_gdf: geopandas.GeoDataFrame对象，待添加城市编码的地理数据
    city_gdf：geopandas.GeoDataFrame对象，城市的矢量范围，用于判定data位于哪个行政区范围内
    citycode_df: pd.DataFrame对象，用于按城市名称检索城市编码
    返回：添加城市编码的geopandas.GeoDataFrame对象
    '''
    # 判断几何类型
    geom_type = data_gdf['geometry'].geom_type[0]

    # 获取几何对象所在的行政区名称
    if 'Polygon' in geom_type:
        gdf = gpd.overlay(data_gdf,city_gdf)    
    elif 'Point' in geom_type:
        gdf = gpd.sjoin(data_gdf,city_gdf)

    # 根据行政区名称获取行政区代码
    city_list = set(list(gdf['SZDQMC']))
    for city in city_list:
        idx = gdf['SZDQMC'] == city
        citycode = str(list(citycode_df.loc[citycode_df['中文名']==city,'adcode'])[0])
        gdf.loc[idx,'SZDQDM'] = citycode
    
    # 删除多余属性列
    if 'Polygon' in geom_type:
        gdf = gdf.drop(['SZDQMC'],axis=1)   
    elif 'Point' in geom_type:
        gdf = gdf.drop(['index_right','SZDQMC'],axis=1)

    return gdf
        
def checkValRange(df,val_range_dict):
    '''
    功能：检查数值范围
    df: pd.DataFrame，待检测表格
    val_range_dict：dict key为待检测列名，value为该列正常的数值范围
    返回：pd.DataFrame，在待检测表格上新增’检测结果'列，超出阈值的标记“数值异常"
    '''
    key_list = list(val_range_dict.keys())
    column_list = df.columns.tolist()

    for key in key_list:
        try:
            if key in column_list:
                idx = np.logical_or(df[key]<val_range_dict[key][0],df[key]>val_range_dict[key][1])
                df.loc[idx,'检测结果'] = '超出阈值'
            else:
                print(key+' 列不存在')
        except:
            print(key+' 列存在非数值')
            pat = r'([^\d|\.]*)'
            idx = df[key].str.match(pat)
            idx[pd.isnull(idx)] = False
            df.loc[idx,key] = np.nan
            df.loc[idx, '检测结果'] = '原值含字母，替换为空'
            idx = np.logical_or(df[key]<val_range_dict[key][0],df[key]>val_range_dict[key][1])
            df.loc[idx, '检测结果'] = '超出阈值'

    return df

def xls2kml(df,loncol,latcol):
    '''
    功能：excel转kml
    df: pd.DataFrame excel表格
    loncol: str 经度列列名，要求该列数值为清洗后以°为单位的数值
    latcol: str 纬度列列名，要求该列数值为清洗后以°为单位的数值
    返回：gpd.GeoDataFrame
    '''
    # 删除经度或纬度列为空的行
    df = df[df[loncol].notna()]
    df = df[df[latcol].notna()]

    for i in df.index:
        df.loc[i,'wkt_str'] = 'POINT (' + str(df.loc[i,'经度']) + ' ' + str(df.loc[i,'纬度']) + ')'
    df['geometry'] = df['wkt_str'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df,crs='EPSG:4326',geometry = df['geometry'])   
    gdf = gdf.drop('wkt_str',axis=1)

    return gdf



if __name__ == '__main__':
    # # 示例1：合并1个excel内的多个表
    # xlsfile = r'D:\研究数据\20220314数据整理落图\测试数据\2022大丰入河排污口（环保+行政审批+水利）.xls'     # 待合并的excel文件
    # outfile = r'D:\研究数据\20220314数据整理落图\测试数据\2022大丰入河排污口（环保+行政审批+水利）_合并.xlsx'  # 合并后的新文件
    # sheet_name = ['水利局','行政审批局']    # 读excel内指定的2张表，参与合并
    # # sheet_name=None     # 读excel内所有表，参与合并
    # skiprows = 1

    # dfs_dict = pd.read_excel(xlsfile, sheet_name=sheet_name, skiprows=skiprows)    # 读excel表
    # newdf = tablesMerge(dfs_dict,idnt_col='要素类型')   # 执行合并操作
    # newdf.to_excel(outfile,index=False) # 将合并后的表格写出到新文件


    # # 示例2：经纬度提取和转换
    # # 定义原文件和转换后的结果文件
    # outfile = r'D:\研究数据\20220314数据整理落图\测试数据\2022大丰入河排污口（环保+行政审批+水利）_合并_corrdConvert.xls'
    # xlsfile = r'D:\研究数据\20220314数据整理落图\测试数据\2022大丰入河排污口（环保+行政审批+水利）_合并.xlsx'
    # sheetname = 0
    # loncol,latcol = '排口位置','排口位置'
    
    # # 提取规则
    # # lon_patt = r'(东经\S*120\S*北纬)'     # 2022大丰入河排污口（环保+行政审批+水利）_合并.xls    东经开头、含120字符，北纬结尾
    # # lat_patt = r'(北纬\S*33\S*)'
    # # lon_patt = r'(\S*)'     # 畜禽养殖能力分乡镇-4000家去除拆除和重复最新.xlsx   全文本
    # # lat_patt = r'(\S*)'
    # # lon_patt = r'(东经[^\u4e00-\u9fa5]+)'  # 大丰内河合法码头调查摸底一览表-1.xlsx   东经开头，非中文字符结尾
    # # lat_patt = r'(纬[^\u4e00-\u9fa5]+)'
    # lon_patt = r'(121\.\d+\D)'  # 断面附近工业企业.xlsx   121开头、后接小数点、小数点后至少有1个数字，以非数字结尾
    # lat_patt = r'(3\d+\.\d+)'
    # # lon_patt = r'(\S*)'  # 全区水产养殖塘水监测水质数据汇总.xlsx   全文本
    # # lat_patt = r'(\S*)'
    
    # # 合理范围（用于判断提取和转换数值是否合理）
    # lon_range = (110,130)
    # lat_range = (31, 35)
    
    # # 数值提取和转换
    # df = pd.read_excel(xlsfile,sheet_name=sheetname)
    # raw_lon_col = df[loncol]
    # lon_result = extractAndConvertCoordinates(raw_lon_col, lon_patt, lon_range)
    # raw_lat_col = df[latcol]
    # lat_result = extractAndConvertCoordinates(raw_lat_col, lat_patt,lat_range)
    
    # # 预览和写出结果
    # print(lon_result['总和'])
    # print(lat_result['总和'])
    # writer = pd.ExcelWriter(outfile)
    # lon_result.to_excel(writer,sheet_name='经度')
    # lat_result.to_excel(writer,sheet_name='纬度')
    # writer.save()
    # writer.close()


    # # 示例3：数值提取
    # outfile = r'D:\研究数据\20220314数据整理落图\测试数据\2022大丰入河排污口（环保+行政审批+水利）_数值单位拆分.xls'
    # xlsfile = r'D:\研究数据\20220314数据整理落图\测试数据\2022大丰入河排污口（环保+行政审批+水利）_合并.xls'
    # sheetname = 0
    # colname = '污水类型及排放量'  
    # contain_unit = True  # 是否要提取单位，是True，否False

    # rawcol = pd.read_excel(xlsfile)[colname]
    # newdf = extractDigitAndUnits(rawcol,contain_unit)
    # newdf.to_excel(outfile)

    
    # 示例4-1：单个坐标点 高德、百度、WGS-1984坐标转换
    # coordinates = gcj2wgs(113.2,32.1)  # 高德转WGS-1984
    # coordinates = [float(format(i, '.6f')) for i in coordinates]
    # print(coordinates)
    # coordinates = bd2wgs(113.2,32.1)  # 百度转WGS-1984
    # coordinates = [float(format(i, '.6f')) for i in coordinates]
    # print(coordinates)
    
    # 示例4-2：excel记录的坐标序列 高德、百度、WGS-1984坐标转换
    # xlsfile = r'C:\Users\Administrator\Documents\ArcGIS\scratch\现场勘测点位_TableToExcel.xls'
    # outfile = r'C:\Users\Administrator\Documents\ArcGIS\scratch\现场勘测点位转WGS84.xls'
    # sheetname = '现场勘测点位_TableToExcel'
    # lon_col,lat_col = 'jd','wd'
    # transformation = 'gcj2wgs'
    # # transformation = 'bd2wgs'
    # df = coordConvert_xls(xlsfile,sheetname,lon_col,lat_col,transformation)
    # df.to_excel(outfile)

    # # 示例4-3：kml/shp文件里的坐标 高德、百度、WGS-1984坐标转换
    # orifile = r'D:\研究数据\20220314数据整理落图\测试数据\kml\断面管控区域静态数据.kml'
    # outfile = r'D:\研究数据\20220314数据整理落图\测试数据\断面管控区域静态数据.kml'
    # gdf = coordConvert_vector(orifile,transformation='gcj2wgs')

    # if os.path.exists(outfile):
    #     os.remove(outfile)
    # gdf.to_file(outfile,encoding='utf-8',driver='KML')
    # gdf.to_file(outfile[0:-4]+'.json', encoding='utf-8', driver='GeoJSON')
    # gdf.to_file(outfile[0:-4]+'.shp',encoding='utf-8',driver='ESRI Shapefile')

    
    # # 示例5：从pdf提取表格
    # pdffile = r'C:\Users\Administrator\Desktop\数据处理1培训材料\测试数据\射阳县利民河、运棉河污染源溯源报告-211231.pdf'  
    # header_num = 2  # 表头占几行
    # header_repeat = True    # 表头在每页是否重复
    # rows_merge = True       # 是否判断第一列单元格是否为空，若空与上一行内容合并
    # st_page,ed_page = 132, 135  # 起止页
    
    # df = extractTablesFromPDF(pdffile,st_page,ed_page,header_num,header_repeat,rows_merge)
    # print(df)
    # df.to_csv(r'D:\研究数据\20220314数据整理落图\测试数据\利民河黄沙港镇污染源情况汇总表.csv',index=False)
    # # df.to_excel(r'D:\研究数据\20220314数据整理落图\测试数据\利民河黄沙港镇污染源情况汇总表.xlsx',index=False)


    # # 示例6-1：检查xls文件中的列名是否都在规定的属性表内
    # tablefile = r'D:\研究数据\20220314数据整理落图\列名参照表.xlsx'
    # xlsfile = r'D:\研究数据\20220314数据整理落图\测试数据\生态眼动态监测溯源信息数字化资料清单 .xlsx'     # 待合并的excel文件
    # sheetname=None     # 读excel内所有表，参与合并
    # skiprows = 0

    # columns_df = extractXlsColumns(xlsfile,sheetname=sheetname)    

    # reftable = pd.read_excel(tablefile,sheet_name='汇总')
    # reflist = reftable['字段名'].tolist()

    # columns_df = isColumnsExist(columns_df,reflist)
    # columns_df.to_excel(xlsfile.split('.')[0]+'_列名检查结果.xlsx')

    # # 示例6-2：检查shp文件中的列名是否都在规定的属性表内
    # tablefile = r'D:\研究数据\20220314数据整理落图\列名参照表.xlsx'
    # shppath = r'D:\研究数据\20220314数据整理落图\测试数据\shp'     # 待合并的excel文件

    # columns_df = extractSHPColumns(shppath)    

    # reftable = pd.read_excel(tablefile,sheet_name='汇总')
    # reflist = reftable['字段名'].tolist()

    # columns_df = isColumnsExist(columns_df,reflist)
    # columns_df.to_excel(shppath+'\\列名检查结果.xlsx')


    # 示例7：点坐标保留小数点后6位
    # file = open(r'E:\项目文件\江苏省南通市启东市\闸坝排口标记\排口闸坝标记\闸坝排口泵站\泵站.json', 'r', encoding='utf-8')
    # gdf=gpd.read_file(r'E:\项目文件\江苏省南通市启东市\闸坝排口标记\排口闸坝标记\闸坝排口泵站\ceshi.json')
    # gdf = setCordinatesPrecision(gdf)
    outpath = r'E:\项目文件\江苏省南通市启东市\闸坝排口标记\排口闸坝标记\闸坝排口泵站 - 副本'  # 定义输出路径
    outshp = os.path.join(outpath,'shp')
    if not os.path.exists(outshp):
        os.mkdir(outshp)
    outjson = os.path.join(outpath,'json')
    if not os.path.exists(outjson):
        os.mkdir(outjson)
    outkml = os.path.join(outpath,'kml')
    if not os.path.exists(outkml):
        os.mkdir(outkml)

    shppath = r'E:\项目文件\江苏省南通市启东市\闸坝排口标记\排口闸坝标记\闸坝排口泵站 - 副本'     # 输入待处理文件存放地址
    os.chdir(shppath)
    shpfiles = glob.glob('*.shp')
    print(shpfiles)
    for shpfile in shpfiles:
        gdf = gpd.read_file(shpfile)
        gdf = setCordinatesPrecision(gdf)
        gdf.to_file(os.path.join(outpath,'shp',shpfile),encoding='utf-8')     # 输出shp
        gdf.to_file(os.path.join(outpath,'json',shpfile[0:-4]+'.json'),driver='GeoJSON')    # 输出geojson
        #fiona包

        gdf.to_file(os.path.join(outpath,'kml',shpfile[0:-4]+'.kml'),driver='KML')    # 输出kml

    
    # # 示例8：赋行政区号属性
    # # 输出路径
    # outpath = r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\数据梳理20220321\new'  
    # outshp = os.path.join(outpath,'shp')
    # if not os.path.exists(outshp):
    #     os.mkdir(outshp)
    # outjson = os.path.join(outpath,'json')
    # if not os.path.exists(outjson):
    #     os.mkdir(outjson)
    # outkml = os.path.join(outpath,'kml')
    # if not os.path.exists(outkml):
    #     os.mkdir(outkml)

    # # 行政区文件，要求行政区文件只有“SZDQMC”属性列，存储行政区名称
    # xzq_file = r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\数据梳理20220321\徐圩新区附近行政区\行政区.shp'
    # xzq_gdf = gpd.read_file(xzq_file)
    #
    # # 城市编码文件
    # citycode_file = r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\数据梳理20220321\城市编码.xlsx'
    # citycode_df = pd.read_excel(citycode_file)
    #
    # # 待处理矢量数据的存储路径
    # shppath = r'D:\项目数据\江苏省连云港市\徐圩新区污染溯源2\数据梳理20220321\shp'
    # os.chdir(shppath)
    # shpfiles = glob.glob('*.shp')
    # for shpfile in shpfiles:
    #     gdf = gpd.read_file(shpfile)
    #     gdf = addCityCode(gdf,xzq_gdf,citycode_df)
    #
    #     print(gdf)

    #     # 输出shp
    #     gdf.to_file(os.path.join(outpath,'shp',shpfile),encoding='utf-8') 
    #     # 输出geojson
    #     gdf.to_file(os.path.join(outpath,'json',shpfile[0:-4]+'.json'),driver='GeoJSON')
    #     # 输出kml
    #     if os.path.exists(os.path.join(outpath,'kml',shpfile[0:-4]+'.kml')):
    #         os.remove(os.path.join(outpath,'kml',shpfile[0:-4]+'.kml'))
    #     gdf.to_file(os.path.join(outpath,'kml',shpfile[0:-4]+'.kml'),driver='KML')

    
    # # 示例9：删除指定列中含字母的数值，并检查其余数值范围是否正常
    # xlsfile = r'C:\Users\WenY\Desktop\研究数据\20220301数据整理落图\测试数据\数值范围检查测试.xlsx'
    # sheetname = 0
    # val_range_dict = {'cod':[0,20],'nh4':[0,10],'tp':[0,20]}
    
    # df = pd.read_excel(xlsfile,sheet_name=sheetname)
    # df = checkValRange(df,val_range_dict)
    # print(df)

            
    # # 示例10：excel转kml
    # xlsfile = r'D:\研究数据\20220314数据整理落图\测试数据\excel转kml测试数据.xlsx'
    # outfile = r'D:\研究数据\20220314数据整理落图\测试数据\excel转kml测试数据.kml'
    # sheetname = 0
    # loncol,latcol = '经度','纬度'

    # df = pd.read_excel(xlsfile,sheet_name=sheetname)
    # gdf = xls2kml(df,loncol,latcol)

    # if os.path.exists(outfile):
    #     os.remove(outfile)
    # gdf.to_file(outfile,encoding='utf-8',driver='KML')