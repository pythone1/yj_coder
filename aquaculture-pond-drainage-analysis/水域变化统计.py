import os
import glob
import geopandas as gpd
import os
import glob
import geopandas as gpd

# 获取所有 shapefile 文件，并按文件名排序
shp_files = sorted(glob.glob(r'I:\pyMethod\segment-anything\111\溧阳统计\有无水\*.shp'))

# 迭代所有相邻的shapefile对
for i in range(len(shp_files) - 1):
    # 获取时间列名
    time1 = os.path.basename(shp_files[i]).split('_')[0]
    time2 = os.path.basename(shp_files[i+1]).split('_')[0]
    print(time1,time2)
    # 读取相邻的两个shapefile
    gdf1 = gpd.read_file(shp_files[i])
    gdf2 = gpd.read_file(shp_files[i+1])
    print(shp_files[i],shp_files[i+1])
    # 在每个 GeoDataFrame 中选出有水/无水的部分
    gdf2_subset = gdf2[['BH', time2]]
    merged_gdf = gdf1.merge(gdf2_subset, on='BH')
    merged_gdf.set_geometry('geometry', inplace=True)
    # merged_gdf['geometry'] = merged_gdf['geometry_x']
    # merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry='geometry')
    gdf1_water = merged_gdf[merged_gdf[time1] == 1]
    gdf1_water_gdf2_no_water = gdf1_water[gdf1_water[time2] == 0]
    # print(len(gdf1_water),len(gdf2_no_water))
    # # 找出两个 GeoDataFrames 在空间上完全重叠的部分
    # water_to_no_water = gpd.overlay(gdf1_water, gdf2_no_water, how='intersection')
    # print(len(water_to_no_water))
    # # 将结果保存为新的 shapefile
    gdf1_water_gdf2_no_water.to_file(f'{time1}-{time2}水域减少范围.shp')