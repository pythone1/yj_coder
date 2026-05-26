import rasterio
import geopandas as gpd
import pandas as pd
from rasterio.mask import mask
import numpy as np

def ndwi_analysis(ndwi_path, shapefile_path, output_shapefile_path, output_excel_path):
    """
    对当期NDWI进行分析，输入历史坑塘shp文件，遍历shp中多边形，每个多边形对应NDWI中水的像素量多判定为有水，否则无水

    参数：
    ndwi_path: 当期NDWI数据的路径。
    shapefile_path: 输入的 SAM分出的坑塘shapefile 的路径。
    output_shapefile_path: 输出的 shapefile 的路径。
    output_excel_path: 输出的 Excel 文件的路径。
    """
    # 读取 shapefile 数据
    gdf = gpd.read_file(shapefile_path)

    # 初始化一个新的列 'water'
    gdf['water'] = 0

    # 打开 NDWI 数据
    with rasterio.open(ndwi_path) as src:

        # 遍历 GeoDataFrame 中的每个多边形
        for index, row in gdf.iterrows():
            geom = row.geometry

            # 使用 rasterio.mask 将 NDWI 数据裁剪到多边形的范围内
            out_image, out_transform = mask(src, [geom], crop=True)
            out_image = out_image[0]

            # 计算 100 和 200 的像素值的数量
            count_100 = np.sum(out_image > 0) #NDWI>水的像素两
            count_200 = np.sum(out_image <= 0) #NDWI<=0非水的像素量

            # 根据像素值的数量，决定 'water' 的值
            if count_100 > count_200:
                gdf.loc[index, 'water'] = 1
            else:
                gdf.loc[index, 'water'] = 2

        # 计算值为1的多边形的数量和总面积
        polygons_1 = gdf[gdf['water'] == 1]
        count_1 = len(polygons_1)
        total_area_1 = polygons_1.geometry.area.sum()

        # 计算值为2的多边形的数量和总面积
        polygons_2 = gdf[gdf['water'] == 2]
        count_2 = len(polygons_2)
        total_area_2 = polygons_2.geometry.area.sum()

    # 保存结果到新的 shapefile
    gdf.to_file(output_shapefile_path)

    # 创建一个 DataFrame 来保存结果
    data = {
        'Type': ['No water', 'Water'],
        'Count': [count_1, count_2],
        'Total Area (m2)': [total_area_1, total_area_2]
    }
    df = pd.DataFrame(data)

    # 保存结果到 Excel 文件
    df.to_excel(output_excel_path, index=False)

if __name__=='__main__':

    # 使用示例
    ndwi_path = r"I:\pyMethod\segment-anything\data\哨兵水域提取测试\栅格转矢量\20221214YX_ndwi.tif"
    shapefile_path = r"I:\pyMethod\segment-anything\data\哨兵水域提取测试\栅格转矢量\YI_NDWI.shp"
    output_shapefile_path = r"I:\pyMethod\segment-anything\data\哨兵水域提取测试\栅格转矢量\1.shp"
    output_excel_path = r"I:\pyMethod\segment-anything\data\哨兵水域提取测试\栅格转矢量\1.xlsx"
    ndwi_analysis(ndwi_path, shapefile_path, output_shapefile_path, output_excel_path)