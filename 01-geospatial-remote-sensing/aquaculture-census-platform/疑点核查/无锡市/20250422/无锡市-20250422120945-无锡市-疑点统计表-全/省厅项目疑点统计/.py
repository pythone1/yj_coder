"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: .py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import geopandas as gpd
from shapely.ops import unary_union
import glob, os
def assign_groups(gdf):
    group_id = 1  # 初始化全局 group_id
    subset = gdf.copy()
    # 初始化分组字段为 -1
    subset['group'] = -1
    # 对该 address 分组
    for i, row in subset.iterrows():
        if subset.at[i, 'group'] == -1:
            subset.at[i, 'group'] = group_id
            overlapping = subset[subset.index != i][subset['buffer'].intersects(row['buffer'])]
            while not overlapping.empty:
                subset.loc[overlapping.index, 'group'] = group_id
                overlapping = subset[(subset['group'] == -1) &
                                     (subset['buffer'].intersects(unary_union(overlapping['buffer'])))]
            # 如果该分组只有一个元素，将其标记为 0（不参与分组）
            if len(subset[subset['group'] == group_id]) == 1:
                subset.loc[subset['group'] == group_id, 'group'] = 0
                group_id -= 1  # 撤销该组的分组 ID
            group_id += 1  # 更新全局 group_id
        # 将分组结果回写到原数据
        gdf.loc[subset.index, 'group'] = subset['group']
    return gdf

# 计算面积并过滤
def filter_by_area(gdf, min_area_acre=0,max_area_acre=9999999999999):
    # 添加面积列（平方米）
    gdf['area_acre'] = gdf.geometry.area/ 666.6667
    # 计算每个分组的总面积
    grouped = gdf.groupby('group')['area_acre'].sum().reset_index()
    # 过滤出总面积大于指定亩的分组
    # 筛选出面积在指定范围内的分组
    large_groups = grouped[(grouped['area_acre'] > min_area_acre) & (grouped['area_acre'] < max_area_acre)]

    # 只保留原始gdf中符合面积要求的组
    filtered_gdf = gdf[gdf['group'].isin(large_groups['group'])]
    return filtered_gdf, large_groups[['group', 'area_acre']]

# 生成中心点GeoJSON
def create_centroid_geojson(gdf, area_df, geojson_path):
    centroids = []
    for _, row in area_df.iterrows():
        group_id = row['group']
        group_geometry = gdf[gdf['group'] == group_id].geometry
        centroid = unary_union(group_geometry).centroid  # 计算分组的中心点
        centroids.append({'group': group_id, 'area_acre': row['area_acre'], 'geometry': centroid})

    # 创建GeoDataFrame并存储中心点
    centroid_gdf = gpd.GeoDataFrame(centroids)
    centroid_gdf['area_acre'] = centroid_gdf['area_acre'].round(2)
    centroid_gdf.set_geometry('geometry', inplace=True)
    centroid_gdf.crs = gdf.crs  # 保持坐标系一致

    # 保存为GeoJSON
    centroid_gdf.to_file(geojson_path, driver='GeoJSON')


# 主函数
def identify_contiguous_ponds(shp_path, output_path, buffer_distance=25, min_area_acre=0,max_area_acre=99999999999999999):
    gdf = gpd.read_file(shp_path)
    gdf = gdf.to_crs(epsg=32650)
    gdf['buffer'] = gdf.geometry.buffer(buffer_distance)
    gdf['group'] = -1
    gdf = assign_groups(gdf)

    # gdf = gdf[gdf['group'] != 0]
    group_area = gdf.groupby('group')['geometry'].apply(lambda x: x.area.sum() / 666.7)
    # 将每个组的总面积赋给对应的行
    gdf['分组总面积'] = gdf['group'].map(group_area)
    # 计算面积并过滤总面积大于50亩的组
    filtered_gdf, area_info = filter_by_area(gdf, min_area_acre,max_area_acre)

    filtered_gdf = calculate_rectangularity_index(filtered_gdf)
    # 保存过滤后的GeoDataFrame
    filtered_gdf = filtered_gdf.drop(columns=['buffer'])
    filtered_gdf.to_file(output_path, driver='GPKG')



def calculate_rectangularity_index(gdf):
    gdf['规整度'] = gdf['geometry'].apply(lambda x: x.area / x.minimum_rotated_rectangle.area if x.minimum_rotated_rectangle.area != 0 else 0)
    return gdf

# 主程序调用
if __name__ == '__main__':
    file = r'E:\江苏省养殖池塘上图入库项目\质控检查\0319连云港\非养殖疑点\信息表-20250321150217-连云港市-池塘图斑赋疑点-非养殖.gpkg'
    output_path = os.path.join(os.path.dirname(file), os.path.splitext(os.path.basename(file))[0] + "分组筛选规整度.gpkg")
    identify_contiguous_ponds(
        file,
        output_path,
        buffer_distance=25,
        min_area_acre=50
    )
