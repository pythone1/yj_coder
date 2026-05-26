import os,glob

import pandas as pd
import geopandas as gpd
import numpy as np
from PIL import Image
from osgeo import gdal

import imgProcess as imgpro

if __name__ == '__main__':
    # ctfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250104江苏省池塘图斑.shp'
    # cttif = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\20250104江苏省池塘图斑.tif'
    # imgpth= r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\图像分割\准备数据\哨兵二号_各区县无云反射率'
    # outpth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\ndvimask'
    # os.chdir(imgpth)
    # os.makedirs(outpth,exist_ok=True)

    # # # 池塘矢量转栅格
    # # gdf = gpd.read_file(ctfile).to_crs('epsg:32650')
    # # minx,miny,maxx,maxy = gdf.total_bounds
    # # rows = int((maxy - miny) / 10)
    # # cols = int((maxx - minx) / 10)
    # # geotrans = (minx,10,0,maxy,0,-10)
    # # data = imgpro.shp2geotiff(ctfile,rows=rows,cols=cols,geo_transform=geotrans,projection='epsg:32650',field='ID')
    # # imgpro.geotiffwrite(cttif,data,geo_transform=geotrans,projection='epsg:32650',datatype='UINT16')
    # # imgpro.tiffileReproject(srcfile=cttif,
    # #                         desfile=cttif.replace('.tif','_4490.tif'),
    # #                         dst_epsg=4490)
    # ct_file = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\20250104江苏省池塘图斑_4490.tif'
    # geotif0 = imgpro.geotiffread(ct_file)
    # geotrans0 = geotif0.geo_transform
    # mask = geotif0.dataarray

    # cities = glob.glob('*')
    # for ct in cities:
    #     files = glob.glob(f'{ct}\\*.tif')
    #     df = pd.DataFrame(files,columns=['文件'])
    #     df['月份'] = df['文件'].str.split('\\',expand=True)[1].str.split('_',expand=True)[3].str[4:6].astype('int')
    #     df = df[(df['月份']==11) | (df['月份']==12) | (df['月份']==1)]
    #     files = df['文件'].values
        
    #     ndvi_stack = []
    #     for i,f in enumerate(files):
    #         geotif = imgpro.geotiffread(f)
    #         data = geotif.dataarray.astype('float')
    #         ndvi = (data[:,:,3] - data[:,:,2]) / (data[:,:,3] + data[:,:,2])
    #         if i == 0:
    #             ndvi_stack.append(ndvi)
    #             rows,cols = ndvi.shape
    #             xx = geotif.geo_transform[1]
    #             yy = geotif.geo_transform[5]
    #         else:
    #             ndvi1 = Image.fromarray(ndvi)
    #             ndvi_stack.append(np.array(Image.fromarray(ndvi).resize((cols,rows))))
    #     ndvi_stack = np.dstack(ndvi_stack)
    #     ndvi_max = np.nanmax(ndvi_stack,axis=2)

    #     # 图像范围
    #     geotrans = geotif.geo_transform
    #     bounds = (geotrans[0],geotrans[3]+geotrans[5]*rows,geotrans[0]+geotrans[1]*cols,geotrans[3])
        
    #     # 对应池塘掩码
    #     bounds_img = (int((bounds[0]-geotrans0[0])/geotrans0[1]),
    #                   int((bounds[1]-geotrans0[3])/geotrans0[5]),
    #                   int((bounds[2]-geotrans0[0])/geotrans0[1]),
    #                   int((bounds[3]-geotrans0[3])/geotrans0[5]),
    #                   )
    #     ct_mask = mask[bounds_img[3]:bounds_img[1],bounds_img[0]:bounds_img[2]]
    #     ct_mask = np.array(Image.fromarray(ct_mask).resize((cols,rows)))

    #     # ndvi掩码
    #     ndvi_max[ct_mask==0] = 0
    #     basename = os.path.basename(f)
    #     basename = '_'.join(basename.split('_')[0:3])
    #     imgpro.geotiffwrite(f'{outpth}\\{basename}.tif',ndvi_max,geo_transform=geotif.geo_transform,projection=geotif.projection,datatype='FLOAT32')


    # ## 全省合并
    # tifpth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\ndvimask'
    # os.chdir(tifpth)

    # outfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\江苏省_ndvimax.tif'
    # imgpro.rasterMosaic(tifpth,outfile)

    ## 统计稻田综合种养-全省
    tiffile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\江苏省_ndvimax.tif'
    ctfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250104江苏省池塘图斑.shp'
    geotif = imgpro.geotiffread(tiffile)
    data = geotif.dataarray

    thred = 0.3
    data[data>=thred] = 1
    data[data<thred] = 0
    outtif = tiffile.replace('.tif','_ged3.tif')
    imgpro.geotiffwrite(outtif,data,geotif.geo_transform,geotif.projection)
    imgpro.createShpfile_from_geotiff(outtif.replace('.tif','.shp'),outtif)

    ## 筛选
    file1 = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\江苏省_ndvimax_ged3.shp'
    file2 = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\图斑汇总\20241225江苏省池塘图斑\20250104江苏省池塘图斑.shp'
    file3 = r'S:\通用数据\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp'
    outpth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\江苏省_ndvimax_ged3'
    os.makedirs(outpth,exist_ok=True)

    gdf1 = gpd.read_file(file1)
    gdf1['area1'] = gdf1.to_crs('epsg:32650').geometry.area / 666.666
    gdf1 = gdf1[gdf1['area1']>=5]
    gdf2 = gpd.read_file(file2)
    gdf3 = gpd.read_file(file3)

    gdf4 = gpd.sjoin(gdf2,gdf1)
    gdf4.to_file(file1.replace('.shp','_稻田综合种养.shp'),encoding='utf-8')
    # gdf4 = gpd.read_file(file1.replace('.shp','_稻田综合种养.shp'))
    gdf4['area'] = gdf4.geometry.area / 666.6666
    gdf4.drop(columns=['index_right'],inplace=True)
    tj = pd.DataFrame([],columns=['总面积(亩)','稻田综合种养(亩)'])
    tj.loc[0,'稻田综合种养(亩)'] = gdf4['area'].sum() / 666.666
    tj.loc[0,'市'] = '江苏省'
    tj.loc[0,'县'] = '江苏省'
    for i,row in gdf3.iterrows():
        print(f'{i+1}/{len(gdf3)}:{row["市"]}{row["NAME"]}')
        gdf4_s = gdf4[gdf4.intersects(row.geometry)]
        gdf4_s.to_file(f'{outpth}\\{row["市"]}_{row["NAME"]}.shp',encoding='utf-8')
        tj.loc[i+1,'稻田综合种养(亩)'] = gdf4_s['area'].sum() / 666.666
        tj.loc[i+1,'市'] = row["市"]
        tj.loc[i+1,'县'] = row["NAME"]
    tj.to_excel(r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\其他\稻田综合种养\市池塘_ndvimaxged3_稻田综合种养统计.xlsx')
