from imgProcess import *
import os
import numpy as np
import pandas as pd
import glob


def count_pixels_in_images(folder_path, output_filename):
    # 创建一个 DataFrame 来存储结果
    df = pd.DataFrame()

    # 遍历文件夹中的所有图像
    for filename in os.listdir(folder_path):
        # 只处理 .tif 文件
        if filename.endswith('.tif'):
            # 获取图像的完整路径
            image_path = os.path.join(folder_path, filename)

            directory, filename = os.path.split(image_path)
            basename = os.path.splitext(filename)[0]

            # 使用 glob 模块找到目录中与 raster 文件同名（不包括扩展名）的矢量文件，例如，所有的 .shp 文件
            vector_files = glob.glob(os.path.join(directory, f"{basename}.shp"))
            gdf_all = gpd.read_file(vector_files[0])

            gdf_all['MJ'] = gdf_all['MJ'].astype(float)
            total = gdf_all['MJ'].sum()

            # date_part = filename.split('_')[0]
            # print(image_path, vector_files[0],date_part)
            # gdf = gdf_all[gdf_all[date_part] == 1]
            # total = gdf['MJ'].astype(float).sum()
            # print(len(gdf_all),len(gdf))

            img = geotiffread(image_path).dataarray

            # 创建一个字典来存储每一个像素值的计数
            pixel_counts = {}

            # 计算1-21内像素的总数
            total_pixels = np.sum((img >= 1) & (img <= 21))

            # 循环 1 到 21，计算每个值的像素数量和百分比
            for i in range(1, 22):
                count = np.sum(img == i)
                percentage = (count / total_pixels) if total_pixels > 0 else 0  # 计算百分比
                pixel_counts[f'FUI={i}'] = count
                pixel_counts[f'像元数{i}'] = percentage
                pixel_counts[f'实际面积{i}'] = percentage * total  # 计算实际面积

            # 将结果添加到 DataFrame 中
            df = df.append({**{'图像名称': filename, 'Total': total}, **pixel_counts}, ignore_index=True)

    # 将 DataFrame 保存为 Excel 文件
    df.to_excel(output_filename, index=False)

if __name__=='__main__':
    # 使用函数
    count_pixels_in_images(r'I:\pyMethod\segment-anything\111\溧阳统计\坑塘减少\新的统计', r'I:\pyMethod\segment-anything\111\溧阳统计\坑塘减少\新的统计.xlsx')

    # shppath = r'I:\pyMethod\segment-anything\111\宜兴坑塘shp'
    # shpfile = glob.glob(shppath + '/*.shp')
    # for shp in shpfile:
    #     # 获取文件名（不含目录）
    #     filename = os.path.basename(shp)
    #     # 分割件名，获取日期部分
    #     date_part = filename.split('_')[0]
    #     gdf_all = gpd.read_file(shp)
    #     # gdf_all = gdf_all['MJ'].astype(float)
    #
    #     gdf_water = gdf_all[gdf_all[date_part] == '1']
    #     gdf_no_water = gdf_all[gdf_all[date_part] == '0']
    #     total_water,total_no_water = gdf_water['MJ'].astype(float).sum(),gdf_no_water['MJ'].astype(float).sum()
    #     print(date_part,total_water,total_no_water)