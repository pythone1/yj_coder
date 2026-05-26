import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
import os, re, glob
import pandas as pd
from datetime import datetime
import time
from shapely.geometry import mapping


os.environ['SHAPE_ENCODING'] = "UTF-8"

# 移除Z轴（3D坐标转2D）
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, MultiLineString, MultiPoint
from shapely.ops import transform


def remove_z(geom):
    if geom is None:
        return None
    if geom.geom_type == 'Point':
        return Point(geom.x, geom.y)
    elif geom.geom_type == 'LineString':
        return LineString([(x, y) for x, y, *_ in geom.coords])
    elif geom.geom_type == 'Polygon':
        exterior = [(x, y) for x, y, *_ in geom.exterior.coords]
        interiors = [
            [(x, y) for x, y, *_ in interior.coords]
            for interior in geom.interiors
        ]
        return Polygon(exterior, interiors)
    elif geom.geom_type.startswith('Multi'):
        parts = [remove_z(part) for part in geom.geoms]
        return {
            'MultiPoint': MultiPoint,
            'MultiLineString': MultiLineString,
            'MultiPolygon': MultiPolygon
        }[geom.geom_type](parts)
    return geom

def prepare_gdf(shp_path):
    # 读取 shp
    gdf = gpd.read_file(shp_path, encoding='utf-8')
    gdf['geometry'] = gdf['geometry'].apply(remove_z)
    # 统一到 WGS84
    gdf = gdf.to_crs(4326)
    # 投影坐标下计算面积（UTM 50N，可根据实际修改）
    gdf['yzmj'] = gdf.to_crs(epsg=32650)['geometry'].area.values
    gdf['tkbh'] = gdf.index
    gdf['paishui'] = [set() for _ in range(len(gdf))]
    gdf['wushui'] = [set() for _ in range(len(gdf))]
    return gdf


def extract_date(filename):
    match = re.search(r'\d{8}T\d{6}', filename)
    if match:
        return match.group(0)[:8]  # YYYYMMDD
    else:
        raise ValueError(f"No valid date found in {filename}.")


def get_month_from_filename(filename):
    date_str = extract_date(filename)
    return datetime.strptime(date_str, "%Y%m%d").strftime("M%m")


def calculate_ndwi_and_drainage_time(tiffiles, gdf, outfile):
    tiffiles = sorted(tiffiles, key=lambda x: extract_date(x))
    columns = ['tkbh', 'yzmj'] + [extract_date(tif) for tif in tiffiles]
    results_df = pd.DataFrame(columns=columns)
    results_df['tkbh'] = gdf.index
    results_df['yzmj'] = gdf['yzmj']
    
    last_water_status = {tkbh: '' for tkbh in gdf.index}
    last_water_date = {tkbh: '' for tkbh in gdf.index}
    
    for tif_path in tiffiles:
        filename = os.path.basename(tif_path)
        date = extract_date(filename)
        print(f"正在处理 {filename}, 日期={date}")
        
        with rasterio.open(tif_path) as ndwi_src:
            # 确保矢量坐标系与栅格一致
            gdf_proj = gdf.to_crs(ndwi_src.crs)
            condition_list = []
            
            # 预处理：将所有几何图形转换为栅格掩膜，每个几何图形赋予唯一ID（index+1）
            shapes = []
            for idx, geom in enumerate(gdf_proj['geometry']):
                if geom is not None and not geom.is_empty:
                    shapes.append((mapping(geom), idx + 1))  # 值为idx+1，避免0（因为背景是0）
            
            # 使用rasterize创建精确掩膜
            from rasterio.features import rasterize
            mask_array = rasterize(
                shapes,
                out_shape=ndwi_src.shape,
                transform=ndwi_src.transform,
                fill=0,  # 背景值
                dtype=np.uint8
            )
            
            for index, row in gdf_proj.iterrows():
                try:
                    # 跳过空几何
                    if row['geometry'] is None or row['geometry'].is_empty:
                        raise ValueError("空几何")
                    
                    # 获取当前几何图形的掩膜：值为index+1的位置
                    geom_mask = (mask_array == (index + 1))
                    
                    # 读取原始NDWI数据
                    ndwi_image = ndwi_src.read(1)
                    ndwi_nodata = ndwi_src.nodata if ndwi_src.nodata is not None else -9999
                    
                    # 应用几何掩膜：只保留几何内部的NDWI值，外部设为nodata
                    masked_ndwi = np.where(geom_mask, ndwi_image, ndwi_nodata)
                    
                    # 计算有效像素：在几何内部且不是nodata
                    valid_mask = (masked_ndwi != ndwi_nodata) & geom_mask
                    total_pixels = np.sum(valid_mask)
                    
                    if total_pixels == 0:
                        condition = '不相交'
                    else:
                        ndwi_positive = np.sum(masked_ndwi[valid_mask] > 0)
                        ndwi_percentage = (ndwi_positive / total_pixels) * 100
                        print(f"池塘 {index} NDWI占比: {ndwi_percentage:.2f}%")
                        condition = '有水' if ndwi_percentage > 20 else '无水'
                
                except Exception as e:
                    print(f"警告: index={index}, tif={filename}, 错误={e}")
                    condition = '不相交'
                
                condition_list.append(condition)
                
                # 更新排水/无水逻辑（保持不变）
                if last_water_status[index] == '有水' and condition == '无水':
                    gdf.at[index, 'paishui'].add(date)
                
                if last_water_date[index]:
                    date1 = datetime.strptime(last_water_date[index], '%Y%m%d')
                    date2 = datetime.strptime(date, '%Y%m%d')
                    if last_water_status[index] == '无水' and condition == '无水':
                        if (date2 - date1).days > 15:
                            gdf.at[index, 'wushui'].add(date)
                
                last_water_date[index] = date
                last_water_status[index] = condition
            
            results_df[date] = condition_list
    
    # 写 paishui / wushui（保持不变）
    results_df['paishui'] = [
        ','.join(sorted(list(gdf.at[tkbh, 'paishui']))) for tkbh in results_df.index
    ]
    results_df['wushui'] = [
        ','.join(sorted(list(gdf.at[tkbh, 'wushui']))) for tkbh in results_df.index
    ]
    
    results_df.to_excel(outfile, index=False)
    return gdf

def main(shp_path, ndwi_path, outpath, outfile):
    st_time = time.time()
    tiffiles = glob.glob(os.path.join(ndwi_path, '*.tif'))
    gdf = prepare_gdf(shp_path)
    gdf = calculate_ndwi_and_drainage_time(tiffiles, gdf, outfile)

    # ⚠️ 保存前转换 set → str
    gdf['paishui'] = gdf['paishui'].apply(
        lambda x: ','.join(sorted(list(x))) if isinstance(x, set) else str(x)
    )
    gdf['wushui'] = gdf['wushui'].apply(
        lambda x: ','.join(sorted(list(x))) if isinstance(x, set) else str(x)
    )

    total_time = time.time() - st_time
    print(f"处理完成，总耗时：{total_time:.2f} 秒")

    gdf.to_file(outpath, driver="GeoJSON", encoding="utf-8")


if __name__ == "__main__":
    shp_path = r'E:\哨兵影像\20251229\片区1.gpkg'
    ndwi_path = r'E:\哨兵影像\20251229\drive-download-20251230T011616Z-1-001\SQD\NDWI'
    outpath = r'E:\哨兵影像\20251229\片区1.geojson'
    outfile = r'E:\哨兵影像\20251229\片区1.xlsx'
    main(shp_path, ndwi_path, outpath, outfile)
