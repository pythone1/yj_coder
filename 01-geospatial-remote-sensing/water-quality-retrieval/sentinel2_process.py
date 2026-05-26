'''
@Time    :   2021/04/13
@Author  :   WEN YANSHA
@Contact :   shuju1@tech-5d.com
@功能: 哨兵二号（L2A）产品自动下载和处理，输出反射率图像，输出水质参数分布图
'''

import os,glob,shutil
import zipfile
import xml.dom.minidom
import numpy as np
import pandas as pd
import math
import ogr
import time
import sched
from osgeo import gdal,osr
import scipy.signal as signal
from sentinelsat import SentinelAPI,read_geojson,geojson_to_wkt
import datetime
import openpyxl

import imgProcess as imgpro
import geomProcess as geopro
import upload_geotiff as geoserver

# 影像下载
def sentinel2Dow(api,geojson,dates,platformname,processinglevel,cloud):
    footprint=geojson_to_wkt(read_geojson(geojson))
    print(footprint)
    products=api.query(footprint,date=dates, \
            platformname=platformname, \
                processinglevel = processinglevel, \
                    cloudcoverpercentage = cloud)

    products_df=api.to_dataframe(products)
    if len(products_df)>0:
        print('符合条件影像有%d幅'%len(products_df))
        # ## IDM method
        # urllist=products_df['link'].values
        # ids=products_df['identifier'].values+'.zip'
        # savepath=root+'\\'+geojson.split('.')[0]
        # CallIDM(urllist, ids,savepath)

        # api method
        # print(products_df.head(5))
        # products_df.to_csv('./res.csv',index=False)
        api.download_all(products)
        return True
    else:
        print('未找到符合条件影像')
        return False

# 解压文件到当前文件夹
def unzipfiles(path):
    for f in os.listdir(path):
        if f.endswith(".zip"):
            zip_file = zipfile.ZipFile(path+'\\'+f)
            for f1 in zip_file.namelist():
                zip_file.extract(f1,path)


# 判别云量
def get_cloud_percentage(MTD_file):
    dom = xml.dom.minidom.parse(MTD_file)       # xml对象
    root = dom.documentElement                  # xml节点集合
    cloud_note = root.getElementsByTagName('CLOUDY_PIXEL_PERCENTAGE')[0]    # 指定节点
    cloud_value = cloud_note.firstChild.data    # 获取节点值
    return float(cloud_value)

# 10m波段合成
def layer_stack1(R10m_path,ref_file):
    files = os.listdir(R10m_path)
    for f in files:
        if "B02" in f:
            b_filename = os.path.join(R10m_path,f)
            continue
        elif "B03" in f:
            g_filename = os.path.join(R10m_path,f)
            continue
        elif "B04" in f:
            r_filename = os.path.join(R10m_path,f)
            continue
        elif "B08" in f:
            nir_filename = os.path.join(R10m_path,f)
            continue    
    b = imgpro.geotiffread(b_filename)
    g = imgpro.geotiffread(g_filename)
    r = imgpro.geotiffread(r_filename)
    nir = imgpro.geotiffread(nir_filename)
    data = np.dstack((b.dataarray,g.dataarray,r.dataarray,nir.dataarray))
    del g,r,nir
    print("layer stacked result: ",data.shape)
    imgpro.geotiffwrite(ref_file,data,b.geo_transform,b.projection,datatype="UINT16")

# 20m波段合成
def layer_stack2(R20m_path,ref_file):
    bands = ['B02','B03','B04','B05','B06','B07','B8A','B11','B12']
    band_num = len(bands)
    os.chdir(R20m_path)
    b1_file = glob.glob("*"+bands[0]+"*")[0]
    b1 = imgpro.geotiffread(b1_file)
    data = b1.dataarray
    for i in range(1,band_num-1):
        f = glob.glob("*"+bands[i]+"*")[0]
        geotiff = imgpro.geotiffread(f)
        data = np.dstack((data,geotiff.dataarray))
    del geotiff
    print("layer stacked result: ",data.shape)
    imgpro.geotiffwrite(ref_file,data,b1.geo_transform,b1.projection,datatype="UINT16")

   
# 水域提取
def extract_waterarea(ref_file,waterref_file,*ori_waterarea):   
    if len(ori_waterarea)>0: 
        # 按初始水域范围裁剪待计算栅格
        water_buf = ori_waterarea.replace(".shp","_tmp.shp")
        imgpro.createBuffer(ori_waterarea, water_buf, 0.0,'gridcode',ogr.OFTInteger)
        imgpro.imgclip_with_shp(ref_file,water_buf,waterref_file)
        # 对裁剪后栅格重新进行水域掩膜
        waterref = imgpro.geotiffread(waterref_file)
        data = waterref.dataarray.astype(np.float)
        ndwi = (data[:,:,1] - data[:,:,3]) / (data[:,:,1] + data[:,:,3])
        ndwi[ndwi>0] = 1
        ndwi[ndwi<=0] = 0
        for i in range(4):
            t = data[:,:,i]
            t[ndwi==0] = 0
            data[:,:,i] = t
        # 写水域掩膜后的reflectance file
        imgpro.geotiffwrite(waterref_file,data,waterref.geo_transform,waterref.projection,datatype="UINT16")     
    else:
        waterref = imgpro.geotiffread(ref_file)
        band_num = waterref.dataarray.shape[2]
        data = waterref.dataarray.astype(np.float)
        ndwi = (data[:,:,1] - data[:,:,3]) / (data[:,:,1] + data[:,:,3])
        ndwi[ndwi>0] = 1
        ndwi[ndwi<=0] = 0
        for i in range(band_num):
            t = data[:,:,i]
            t[ndwi==0] = 0
            data[:,:,i] = t
        # 写水域掩膜后的reflectance file
        imgpro.geotiffwrite(waterref_file,data,waterref.geo_transform,waterref.projection,datatype="UINT16")

def lonlat2geo(proj, lon, lat):
    '''
    将经纬度坐标转为投影坐标（具体的投影坐标系由给定数据确定）
    :param dataset: GDAL地理数据
    :param lon: 地理坐标lon经度
    :param lat: 地理坐标lat纬度
    :return: 经纬度坐标(lon, lat)对应的投影坐标
    '''
    prosrs = osr.SpatialReference()
    prosrs.ImportFromWkt(proj)
    geosrs = prosrs.CloneGeogCS()
    ct = osr.CoordinateTransformation(geosrs, prosrs)
    coords = ct.TransformPoint(lat, lon)
    return coords[:2]
    
def geo2imagexy(geo_transform, x, y):
    '''
    根据GDAL的六参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）
    '''
    trans = geo_transform
    a = np.array([[trans[1], trans[2]], [trans[4], trans[5]]])
    b = np.array([x - trans[0], y - trans[3]])
    return np.linalg.solve(a, b)  # 使用numpy的linalg.solve进行二元一次方程的求解

# 提取有效“地面值-反射率光谱”样本对
def get_effect_samples(ref_path,ground_sample_file,parameters):    
    # 读采样点经纬度
    df = pd.read_excel(ground_sample_file,sheet_name=0)
    lng = df.loc[:,'lng'].values
    lat = df.loc[:,'lat'].values
    grdsamp_num = len(lng)
    print("original groud samples num:",grdsamp_num)
    # 待写：“地面值-反射率光谱”
    newdf = pd.DataFrame(data=None,columns=['name','lng','lat','province','city','basin','river','b','g','r','nir'])
    files = os.listdir(ref_path)
    k = 0
    for ref_file in files:
        if ref_file.endswith("_WTREF.tif"):
            ref_file = os.path.join(ref_path,ref_file)
            ref = imgpro.geotiffread(ref_file)
            lng_min = ref.geo_transform[0]
            lat_max = ref.geo_transform[3]
            lng_max = ref.geo_transform[0] + ref.cols * ref.geo_transform[1]
            lat_min = ref.geo_transform[3] + ref.rows * ref.geo_transform[5]
            print("image ",ref_file,": ",lng_min,lng_max,lat_min,lat_max)            
            for i in range(grdsamp_num):
                [x,y]=lonlat2geo(ref.projection, lng[i], lat[i])
                if (x>=lng_min) & (x<=lng_max) & (y>=lat_min) & (y<=lat_max):
                    print("sample ",i,":",x,y)
                    xy=geo2imagexy(ref.geo_transform,x,y) 
                    row=int(xy[1])
                    col=int(xy[0]) 
                    ref_value = ref.dataarray[row,col,:]
                    if np.nanmin(ref_value) > 0:
                        print(ref_value)
                        newdf.loc[k,'b':'nir'] = ref_value  
                        newdf.loc[k,'name'] = df.loc[i,'mn_name'] 
                        newdf.loc[k,'province'] = df.loc[i,'up_area_name'] 
                        newdf.loc[k,'city'] = df.loc[i,'area_name'] 
                        newdf.loc[k,'basin'] = df.loc[i,'up_river_name'] 
                        newdf.loc[k,'river'] = df.loc[i,'river_name']                         
                        newdf.loc[k,'lng':'lat'] = df.loc[i,'lng':'lat'] 
                        for p in parameters:
                            newdf.loc[k,p] = df.loc[i,p]
                        k = k + 1
    print("有效样本数：",k)
    if k > 0:
        wb = openpyxl.load_workbook(ground_sample_file)
        writer = pd.ExcelWriter(ground_sample_file,engine='openpyxl')
        writer.book = wb
        newdf.to_excel(writer,sheet_name='grdsmp_spec')
        writer.save()
        writer.close()
    return newdf

# 水质参数反演
def derive_parameters(ref_path,ground_sample_file,parameters):
    band_idx = [0,1,2,3]
    sampledata = pd.read_excel(ground_sample_file)
    outmodel = warelib.derive_model(sampledata,parameters)
    os.chdir(ref_path)
    tiffiles = glob.glob("*.tif")
    for c_file in tiffiles:
        warelib.waterretrieve(c_file,band_idx,outmodel,parameters)

# 计算FUI,SD
def derive_FUI(data):
    rows,cols,bands = data.shape
    #波段选择        
    r = 3-1
    g = 2-1
    b = 1-1    
    R = data[:,:,r]
    G = data[:,:,g]
    B = data[:,:,b]
    X = 2.7689 * R + 1.7517 * G + 1.1302 * B
    Y = 1.0000 * R + 4.5907 * G + 0.0601 * B
    Z = 0.0565 * G + 5.5943 * B
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    #z = Z / (X + Y + Z)
    del R,G,B,X,Y,Z
    x1 = y - 0.3333
    y1 = x - 0.3333
    alpha = np.zeros([rows,cols])    
    for i in range(rows):
        for j in range(cols):
            alpha[i,j] = math.atan2(y1[i,j],x1[i,j]) * 180 / np.pi           
    # plt.imshow(alpha)
    del x1,y1
    FUI = np.zeros([rows,cols])    
    a = np.array([-140.054,-135.414,-123.059,-107.207,-91.443,-60.546,-27.923,
        -11.913,1.634,11.445,19.243,21.424,22.644,25.429,27.926,31.411,
        35.226,40.552,46.222,50.339,55.587])
    for i in range(20):
        FUI[alpha>=a[i]] = i+1
    FUI[alpha>a[20]] = 21    
    a1 = alpha.copy()
    a1 = a1 + 180
    a1[FUI>=8] = 0    
    a2 = FUI.copy()
    a2[FUI<8] = 0
    sd1 = 8144.5 / np.power(a1,1.534)
    sd2 = 44.122 / np.power(a2,1.138)
    SD = sd1
    SD[FUI>=8] = sd2[FUI>=8]   
    del sd1,sd2   
    return FUI,SD

# 基线高度差base line height difference
def BLHD(data,wavelength,index):
    b1 = data[:,:,index[0]]
    b2 = data[:,:,index[1]]
    b3 = data[:,:,index[2]]
    blh = b1 + (b3-b1) * (wavelength[index[1]]-wavelength[index[0]]) / (wavelength[index[2]]-wavelength[index[0]])
    difference = b2-blh
    difference[b2==0] = 0
    return difference

# 计算叶绿素
def derive_chla(data,wavelength):
    # wavelength = [490,560,665,705,740,783,842,1610,2190]
    FAI = BLHD(data,wavelength,[2,6,7])
    MCIwide = BLHD(data,wavelength,[2,3,4])
    return FAI,MCIwide

# 数据下载
def downloadProc(path,dates,geojson):
    # ############   下载   ###########
    print("start downding...")
    user='yj980202'
    password='s821472144'
    site='https://scihub.copernicus.eu/dhus'
    api=SentinelAPI(user,password,site)
    path0 = os.path.dirname(path)

    # today = datetime.datetime.now()
    # tomorrow = today + datetime.timedelta(days=1)
    # tomorrow = today + datetime.timedelta(days=1)
    # today = today + datetime.timedelta(days=-48)   # -48 0801~0918;
    # dates=(today.strftime("%Y%m%d"),tomorrow.strftime("%Y%m%d"))              # 时间段，算首剔尾

    print(dates)
    platformname = 'Sentinel-2'     # 平台
    processinglevel = 'Level-2A'    # 产品级别
    cloud = (0,10)                  # 云量
    if sentinel2Dow(api,geojson,dates,platformname,processinglevel,cloud) == True:
    if True:
        print("decompressing...")
        unzipfiles(path)
        print("preprocessing...")
        s2_files = glob.glob("*.SAFE")
        ref_path = os.path.join(path,"reflectance")
        coverage_path = os.path.join(path,"coverage")
        RGB_path = os.path.join(path,"RGB")
        if not os.path.exists(ref_path):
            os.mkdir(ref_path)
        if not os.path.exists(coverage_path):
            os.mkdir(coverage_path)
        if not os.path.exists(RGB_path):
            os.mkdir(RGB_path)
        for s2 in s2_files:
            ref10_file = os.path.join(ref_path,s2.replace(".SAFE","_REF10m.tif"))
            ref20_file = os.path.join(ref_path,s2.replace(".SAFE","_REF20m.tif"))
            GRANULE_file = os.path.join(path,s2,'GRANULE')
            L2A_file = os.listdir(GRANULE_file)[0]
            R10m_file = os.path.join(GRANULE_file,L2A_file,'IMG_DATA','R10m')
            R20m_file = os.path.join(GRANULE_file,L2A_file,'IMG_DATA','R20m')
            # 10m 反射率波段合成
            layer_stack1(R10m_file,ref10_file)
            # 20m 反射率波段合成
            layer_stack2(R20m_file,ref20_file)
            # 创建RGB图像
            TCI_path = os.path.join(GRANULE_file,L2A_file,'IMG_DATA','R10m')
            TCI_file = glob.glob(TCI_path+"\\"+"*TCI*.jp2")[0]
            RGB_file = os.path.join(RGB_path,s2.replace(".SAFE","_RGB.tif"))
            geotiff = imgpro.geotiffread(TCI_file)
            imgpro.geotiffwrite(
                RGB_file,geotiff.dataarray,
                geotiff.geo_transform,geotiff.projection,datatype="UINT8"
                )
            # 创建RGB图像金字塔
            cmd_str = r'gdaladdo -ro ' +  RGB_file + ' 2 4 8 16'
            os.system(cmd_str)
            # 创建有效范围的掩膜
            # extract tiffile's boundary
            ori_shp = os.path.join(coverage_path,"temp_ori.shp")
            imgpro.createShpfile_from_geotiff(ori_shp,ref10_file)
            # simplify the boundary line
            convex_shp = os.path.join(coverage_path,"temp_convex.shp")
            geopro.createGeomConvex(ori_shp,convex_shp)
            # coordinate system transformation
            coverage_file = os.path.join(coverage_path,s2.replace(".SAFE","_COV.shp"))
            prosrs,geosrs = imgpro.getSRSPair(ref10_file)
            geopro.reproject(convex_shp,coverage_file,prosrs,geosrs)
        os.chdir(coverage_path)
        tempfiles = glob.glob("*temp*")
        for temp in tempfiles:
            tempfile = os.path.join(coverage_path,temp)
            os.remove(tempfile)
        return True
    else:
        return False

# 获取波段组合
def getImgGroups(path):
    unzipfiles(path)
    s2_files = glob.glob("*.SAFE")
    ref_path = os.path.join(path,"reflectance")
    coverage_path = os.path.join(path,"coverage")
    RGB_path = os.path.join(path,"RGB")
    if not os.path.exists(ref_path):
        os.mkdir(ref_path)
    if not os.path.exists(coverage_path):
        os.mkdir(coverage_path)
    if not os.path.exists(RGB_path):
        os.mkdir(RGB_path)
    for s2 in s2_files: 
        ref10_file = os.path.join(ref_path,s2.replace(".SAFE","_REF10m.tif")) 
        ref20_file = os.path.join(ref_path,s2.replace(".SAFE","_REF20m.tif")) 
        GRANULE_file = os.path.join(path,s2,'GRANULE')
        L2A_file = os.listdir(GRANULE_file)[0]
        R10m_file = os.path.join(GRANULE_file,L2A_file,'IMG_DATA','R10m') 
        R20m_file = os.path.join(GRANULE_file,L2A_file,'IMG_DATA','R20m') 
        # 10m 反射率波段合成
        layer_stack1(R10m_file,ref10_file) 
        # 20m 反射率波段合成  
        layer_stack2(R20m_file,ref20_file)      
        # 创建RGB图像
        RGB_file = os.path.join(RGB_path,s2.replace(".SAFE","_RGB.tif"))
        imgpro.ref2RGB(ref10_file,RGB_file,stretch_mode="5%")
        # 创建有效范围的掩膜              
        # extract tiffile's boundary
        ori_shp = os.path.join(coverage_path,"temp_ori.shp")
        imgpro.createShpfile_from_geotiff(ori_shp,ref10_file)
        # simplify the boundary line
        convex_shp = os.path.join(coverage_path,"temp_convex.shp")
        geopro.createGeomConvex(ori_shp,convex_shp)
        # coordinate system transformation
        coverage_file = os.path.join(coverage_path,s2.replace(".SAFE","_COV.shp")) 
        prosrs,geosrs = imgpro.getSRSPair(ref10_file)
        geopro.reproject(convex_shp,coverage_file,prosrs,geosrs)
    os.chdir(coverage_path)
    tempfiles = glob.glob("*temp*")
    for temp in tempfiles:
        tempfile = os.path.join(coverage_path,temp)
        os.remove(tempfile)              
    return True

# 水体反射率提取
def getWaterREF(path,*ori_waterarea):    
    ref_path = os.path.join(path,"reflectance")
    waterarea_path = os.path.join(path,"waterarea")
    if not os.path.exists(waterarea_path):
        os.mkdir(waterarea_path)
    os.chdir(path)
    s2_files = glob.glob("*.zip")
    if len(ori_waterarea)>0:
        for f in s2_files:
            ref10_file = os.path.join(ref_path,f.replace(".zip","_REF10m.tif"))
            ref20_file = os.path.join(ref_path,f.replace(".zip",'_REF20m.tif'))
            waterREF10_file = os.path.join(waterarea_path,f.replace(".zip",'_WTREF10m.tif'))
            waterREF20_file = os.path.join(waterarea_path,f.replace(".zip",'_WTREF20m.tif'))
            extract_waterarea(ref10_file,waterREF10_file,ori_waterarea)
            extract_waterarea(ref20_file,waterREF20_file,ori_waterarea)
    else:
        for f in s2_files:
            ref10_file = os.path.join(ref_path,f.replace(".zip","_REF10m.tif"))
            ref20_file = os.path.join(ref_path,f.replace(".zip",'_REF20m.tif'))
            waterREF10_file = os.path.join(waterarea_path,f.replace(".zip",'_WTREF10m.tif'))
            waterREF20_file = os.path.join(waterarea_path,f.replace(".zip",'_WTREF20m.tif'))
            # 提取10m 分辨率的水体反射率
            extract_waterarea(ref10_file,waterREF10_file)
            # 提取20m 分辨率的水体反射率
            extract_waterarea(ref20_file,waterREF20_file)

# normalized products of 10m resolusion           
def algoProc1(path):
    print("producing products with resolution of 10 meters:")    
    waterarea_path = os.path.join(path,"waterarea")
    waterQA_path = os.path.join(path,"waterQA")
    if not os.path.exists(waterQA_path):
        os.mkdir(waterQA_path)
    os.chdir(waterarea_path)
    ref_files = glob.glob("*WTREF10m.tif") 
    for ref_file in ref_files:             
        waterref = imgpro.geotiffread(ref_file)
        # 计算水色
        SD_file = os.path.join(waterQA_path,ref_file.replace("_WTREF10m","_SD"))
        FUI_file = os.path.join(waterQA_path,ref_file.replace("_WTREF10m","_FUI"))
        FUI,SD = derive_FUI(waterref.dataarray.astype(np.float))
        SD[SD == 0] = np.nan
        SD = signal.medfilt(SD,5)
        SD[SD>10] = 10
        SD = (SD / 10 * 250).astype(np.uint8)
        imgpro.geotiffwrite(FUI_file,FUI,waterref.geo_transform,waterref.projection,datatype="UINT8")
        imgpro.geotiffwrite(SD_file,SD,waterref.geo_transform,waterref.projection,datatype="UINT8") 
        # 创建SD图像金字塔
        cmd_str = r'gdaladdo -ro ' +  SD_file + ' 2 4 8 16'
        os.system(cmd_str) 
        # # 计算叶绿素(10 m resolusion)
        # NDCI_file = os.path.join(waterQA_path,ref_file.replace("_WTREF10m","_chla_NDCI"))
        # data = waterref.dataarray
        # chla_NDCI = (data[:,:,1] - data[:,:,2]) / (data[:,:,1] + data[:,:,2])   # (G-R) / (G+R)
        # chla_NDCI[chla_NDCI>1] = 0
        # chla_NDCI = signal.medfilt(chla_NDCI,5)
        # imgpro.geotiffwrite(NDCI_file,chla_NDCI,waterref.geo_transform,waterref.projection,datatype="FLOAT32")

# normalized products of 20m resolusion
def algoProc2(path):
    print("producing products with resolution of 20 meters:") 
    waterarea_path = os.path.join(path,"waterarea")
    waterQA_path = os.path.join(path,"waterQA")
    if not os.path.exists(waterQA_path):
        os.mkdir(waterQA_path)
    os.chdir(waterarea_path)
    ref_files = glob.glob("*WTREF20m.tif") 
    wavelength = [490,560,665,705,740,783,842,1610,2190]
    for ref_file in ref_files:    
        # 计算叶绿素（20m resolution）
        nFAI_file = os.path.join(waterQA_path,ref_file.replace("_WTREF20m","_chla_nFAI"))
        nMCIwide_file = os.path.join(waterQA_path,ref_file.replace("_WTREF20m","_chla_nMCIwide"))
        waterref = imgpro.geotiffread(ref_file)
        data = waterref.dataarray.astype(np.float)
        t = data[:,:,0]
        FAI,MCIwide = derive_chla(data,wavelength)
        FAImin = np.nanmin(np.nanmin(FAI))
        FAImax = np.nanmax(np.nanmax(FAI))
        print(FAImin)
        nFAI = (FAI - FAImin) / (FAImax - FAImin)
        nFAI[t == 0] = 0
        nFAI = imgpro.smoothdata(nFAI,"median")
        MCIwidemin = np.nanmin(np.nanmin(MCIwide))
        MCIwidemax = np.nanmax(np.nanmax(MCIwide))
        nMCIwide = (MCIwide - MCIwidemin) / (MCIwidemax - MCIwidemin)  
        nMCIwide[t == 0] = 0  
        nMCIwide = imgpro.smoothdata(nMCIwide,"median")
        imgpro.geotiffwrite(nFAI_file,nFAI,waterref.geo_transform,waterref.projection,datatype="FLOAT32")
        imgpro.geotiffwrite(nMCIwide_file,nMCIwide,waterref.geo_transform,waterref.projection,datatype="FLOAT32")

# 绝对指标计算
def algoProc3(path,ground_sample_file,parameters):
    print("deriving ",parameters," ...")
    band_idx = [0,1,2,3]
    ref_path = os.path.join(path,"waterarea")
    sampledata = get_effect_samples(ref_path,ground_sample_file,parameters)
    # sampledata = pd.read_excel(ground_sample_file,sheet_name='grdsmp_spec1')
    if len(sampledata.index) >= 10:
        outmodel = warelib.derive_model(sampledata,parameters)
        ref_files = os.listdir(ref_path)
        for f in ref_files:
            if f.endswith("_WTREF10m.tif"):
                ref_file = os.path.join(ref_path,f)
                warelib.waterretrieve(ref_file,band_idx,outmodel,parameters)   
    else:
        print("not enough usable ground samples.")

# 图层发布
def geoserverLayerRelease(path):
    RGBPath = os.path.join(path,"RGB")
    waterQAPath = os.path.join(path,"waterQA")
    covPath = os.path.join(path,"coverage")
    # 发布RGB产品
    RGBfiles = glob.glob(RGBPath+"\\*.tif")
    for RGBfile in RGBfiles:
        store_name = os.path.basename(RGBfile)[0:-4]
        geoserver.uploadGeotiff(store_name,RGBfile,workspace="S2Server",style="S2_RGB")
    # 发布waterQA-SD产品
    QAfiles = glob.glob(waterQAPath+"\\*SD.tif")
    for QAfile in QAfiles:
        store_name = os.path.basename(QAfile)[0:-4]
        geoserver.uploadGeotiff(store_name,QAfile,workspace="S2Server",style="S2_SD")
    # 发布产品范围
    COVfiles = glob.glob(covPath+"\\*.shp")
    print(COVfiles)
    for COVfile in COVfiles:
        store_name = os.path.basename(COVfile)[0:-4]
        print(store_name)
        geoserver.uploadShp(store_name,COVfile,workspace="S2Server")

def unzipfile(filename):
    path = os.path.dirname(filename)
    zip_file = zipfile.ZipFile(filename)
    for f in zip_file.namelist():
        zip_file.extract(f,path)

def getCloudMSK(safe_file):
    granule = os.path.join(safe_file,"GRANULE")
    L2A = glob.glob(granule+"\\*")[0]
    cld_mask = os.path.join(L2A,"QI_DATA","MSK_CLDPRB_20m.jp2")
    return cld_mask
    
def cloudmask(path):
    safefiles = glob.glob(path+"\\*.SAFE")
    for safefile in safefiles:  
        # 获取云掩膜文件
        cloud20m_file = getCloudMSK(safefile)
        cloud20m_dataset = gdal.Open(cloud20m_file,gdal.GA_ReadOnly)
        cloud10m_file = os.path.join(path,"cld_10m.tif")
        gdal.Warp(cloud10m_file,cloud20m_dataset,xRes=10,yRes=10)
        geotiff = imgpro.geotiffread(cloud20m_file)
        cld20m = geotiff.dataarray[:,:,0]
        geotiff = imgpro.geotiffread(cloud10m_file)
        cld10m = geotiff.dataarray[:,:,0]
        geotiff = None
        cloud20m_dataset = None
        os.remove(cloud10m_file)

        # 水色产品掩膜
        basename = os.path.basename(safefile).replace(".SAFE","") 
        waterQA = os.path.join(path,"waterQA")
        waterQAfiles = glob.glob(waterQA+"\\"+basename+"*.tif")
        for waterqafile in waterQAfiles:
            dataset = gdal.Open(waterqafile,gdal.GA_Update)
            dataarray = dataset.GetRasterBand(1).ReadAsArray()
            dataarray[np.isnan(dataarray)] = 0  # 取消空值设置
            resolution = dataset.GetGeoTransform()[1]
            if resolution == 10:
                dataarray[cld10m>0] = 0
            elif resolution == 20:
                dataarray[cld20m>0] = 0
            else:
                print("no cloud mask product matched resolution of ",resolution," meters")
            dataset.GetRasterBand(1).WriteArray(dataarray)

if __name__=="__main__":
    # # 根据reflectance仅仅出SD文件
    path = r'D:\Users\Administrator\Desktop\best_model\2'  #输入给定的reflectance的文件夹
    outpath = r'D:\Users\Administrator\Desktop\best_model\2'     #输出的文件夹
    os.chdir(path)
    tiffiles = glob.glob("*.tif")
    for tiffile in tiffiles:
        geotiff = imgpro.geotiffread(tiffile)
        data = geotiff.dataarray.astype(np.float)
        ndwi = (data[:, :, 1] - data[:, :, 3]) / (data[:, :, 1] + data[:, :, 3])
        data[ndwi < 0] = 0
        FUI, SD = derive_FUI(data)
        outfile = os.path.join(outpath, tiffile[0:-4] + '_SD.tif')
        imgpro.geotiffwrite(outfile, SD, geotiff.geo_transform, geotiff.projection, datatype="FLOAT32")


    # 解压原始数据，出RGB、水色、rf
    path = r'H:\xiangmu\shuise'      #这里放置原始影像的路径
    # os.chdir(path)
    # unzipfiles(path)
    # downloadProc(path)
    getImgGroups(path)
    getWaterREF(path)
    algoProc1(path)








    # #
    # path0 = r'I:\Sentinel2_DATA'
    # ground_sample_file = os.path.join(path0,"ground_sample.xlsx")   # 地面样点
    # parameters = ['codmn','nh3n','tp','tn']
    # ori_waterarea = r'D:\ProcessingData\TEMP\dataprocess\赵公河\ori_waterarea.shp'      # 初始水域


#根据范围下载
    # existed_filepathes = [r'G:\Sentinel_DATA\20220301',r'G:\Sentinel_DATA\20220308']
    # existed_files = []
    # for existed_filepath in existed_filepathes:
    #     os.chdir(existed_filepath)
    #     zipfiles = glob.glob("*.zip")
    #     for zfile in zipfiles:
    #         existed_files.append(zfile.replace(".zip",""))
    # print(existed_files)



# 文件的下载
#     path = r'xxxxx' #下载路径
#     geojson=os.path.join(path0,'SouthYZRiver.geojson')    # geojson格式的范围
#     dates = ("20220301", "20220308")  #检索影像的日期
#     os.chdir(path)
#     existed_filepathes = [r'G:\Sentinel_DATA\20220301']  #防止重复
#     downloadProc(path,except_list=existed_files)  #防止重复
#     getWaterREF(path)
#     algoProc1(path)


    # geoserverLayerRelease(path)
#



    # while True:       
    #     # 每天晚上11点下载
    #     if int(time.strftime("%H")) == 11:
    #         today = time.strftime("%Y%m%d")
    #         path = os.path.join(path0,today)
    #         if not os.path.exists(path):
    #             os.mkdir(path) 
    #         os.chdir(path)
    #         # 数据下载
    #         if downloadProc(path) == True:
    #             # 专题产品计算
    #             if "ori_waterarea" in dir():
    #                 getWaterREF(path,ori_waterarea)
    #             else:
    #                 getWaterREF(path)
    #             algoProc1(path)
    #             algoProc2(path)
    #             # 水色产品掩膜

    #             if "ground_sample_file" in dir():
    #                 algoProc3(path,ground_sample_file,parameters)
    #             # 专题图层发布
    #             geoserverLayerRelease(path)
    #             # 解压文件移除
    #             os.chdir(path)  
    #             tempfiles = glob.glob("*.SAFE")
    #             for temp in tempfiles:
    #                 tempfile = os.path.join(path,temp)
    #                 shutil.rmtree(tempfile)
    #         else:
    #             # 若数据未下载，删除当日文件夹
    #             os.chdir(path0)
    #             os.rmdir(path)
    #         print(today,"finished ！")
    #     #休眠一小时
    #     time.sleep(3600)        
    #     # time.sleep(60)        
