import geopandas as gpd
import pandas as pd
import time
from shapely.geometry import Point, Polygon, LineString
def extract_coordinates(location):
    lon, lat = map(float, location.split('，'))
    return Point(lon, lat)
def round_coordinates(coords, precision):
    return [(round(x, precision), round(y, precision)) for x, y in coords]
def round_geometry(geom, precision):
    if isinstance(geom, Point):
        return Point(round(geom.x, precision), round(geom.y, precision))
    elif isinstance(geom, LineString):
        return LineString(round_coordinates(geom.coords, precision))
    elif isinstance(geom, Polygon):
        exterior = round_coordinates(geom.exterior.coords, precision)
        interiors = [round_coordinates(interior.coords, precision) for interior in geom.interiors]
        return Polygon(exterior, interiors)
    else:
        return geom.__class__([round_geometry(part, precision) for part in geom.geoms])
    
def deduplicate_geometries(input_path_A, input_path_B, output_path, duplicates_output_path,crs_epsg=4326,precision = 6):
    """
    合并两个矢量文件（shapefile），基于几何列去重并输出结果。

    :param input_path_A: str, 第一个输入文件的路径
    :param input_path_B: str, 第二个输入文件的路径
    :param output_path: str, 输出去修改过的图斑的文件路径
    :param duplicates_output_path: str, 输出未修改的图斑的文件路径
    :param crs_epsg: int, 坐标参考系统的 EPSG 代码，默认为 4326
    :return: gdf_out, 去重后剩余的gdf
    """
    # 记录开始时间
    start_time = time.time()

    # 读取两个矢量文件
    A = gpd.read_file(input_path_A)
    B = gpd.read_file(input_path_B)

    # 转换坐标参考系统为指定的 EPSG
    A = A.to_crs(epsg=crs_epsg)
    B = B.to_crs(epsg=crs_epsg)

    A['geometry'] = A['geometry'].apply(lambda geom: round_geometry(geom, precision))
    B['geometry'] = B['geometry'].apply(lambda geom: round_geometry(geom, precision))

    # 合并两个数据集
    combined = pd.concat([A, B])

    # 基于几何列去重（找出两个池塘文件不一样的地方）
    gdf_out = combined[combined.duplicated(subset='geometry', keep=False) == False]

    gdf_duplicates = combined[combined.duplicated(subset='geometry', keep=False)]

    # 输出去重后的结果
    gdf_out.to_file(output_path)
    gdf_duplicates.to_file(duplicates_output_path)
    # 计算并输出耗时
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"匹配修改过的图斑用时{elapsed_time:.2f}秒")
    print(f"有修改图斑共计{len(gdf_out)}个")

    return gdf_out

def process_user_points(gdf_out,user_point_path, user_id,user_point_outpath):
    """
    处理用户提供的池塘位置表格，筛选修改过的池塘id。
    :param gdf_out: 修过过的池塘图斑
    :param user_point_path: 池塘位置数据Excel文件路径
    :param user_id: Excel表格中对应的用户填报编号
    :param user_point_outpath: 输出用户Excel表格中的点位矢量文件
    """
    try:
        start_time = time.time()
        # 读取用户数据
        user_point_df = pd.read_excel(user_point_path)
        # 如果表头为“池塘位置”，应用extract_coordinates函数提取坐标
        # user_point_df['geometry'] = user_point_df['池塘位置'].apply(extract_coordinates)
        # 如果表头为“经度”、”纬度“时使用
        user_point_df['geometry'] = user_point_df.apply(lambda row: Point(row['中心点经度'], row['中心点纬度']), axis=1)
        # 将DataFrame转换为GeoDataFrame
        user_point_gdf = gpd.GeoDataFrame(user_point_df, geometry='geometry', crs='EPSG:4326')
        user_point_gdf.to_file(user_point_outpath)
        # 读取目标图斑数据
        gdf_out = gdf_out.to_crs(4326)
        # 空间连接，查找用户数据和图斑数据的匹配点
        matched_points = gpd.sjoin(user_point_gdf[[user_id, 'geometry']], gdf_out[['geometry']], how='inner', op='within')

        # 获取唯一的ID
        unique_ids = matched_points[user_id].drop_duplicates()
        unique_ids_list = unique_ids.tolist()

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"匹配用户填报点位用时{elapsed_time:.2f}秒")
        print(f"共匹配到填报点位{len(gdf_out)}个")

        return unique_ids_list
    except Exception as e:
        print(f"处理过程中发生错误: {e}，请检查表格字段")

if __name__ == "__main__":
    #查找改动过的所有图斑
    input_path_A = r"S:\项目数据\江苏省养殖池塘\精确度统计\B版\江苏省_盐城市_射阳县_out.shp"
    input_path_B = r"S:\项目数据\江苏省养殖池塘\精确度统计\C版\江苏省_盐城市_射阳县_out.shp"
    output_path = r"S:\项目数据\江苏省养殖池塘\精确度统计\射阳BC有修改的图斑.gpkg"
    duplicates_output_path = r"S:\项目数据\江苏省养殖池塘\精确度统计\射阳BC未改动的图斑.gpkg"
    gdf_out = deduplicate_geometries(input_path_A, input_path_B, output_path,duplicates_output_path)

    #修改过的图斑匹配用户打点的id，输出所有改动的池塘id，注意需要确定表格的表头字段
    user_point_path = r"S:\项目数据\江苏省养殖池塘\精确度统计\射阳疑点分析总表.xlsx"
    user_point_outpath = r"S:\项目数据\江苏省养殖池塘\精确度统计\用户打点位置.gpkg"
    user_id = 'id'
    unique_ids_list = process_user_points(gdf_out, user_point_path, user_id, user_point_outpath)
    print(unique_ids_list)


