import geopandas as gpd
import pandas as pd
import os

from CTXXTBYD import *

def calculate_filled_ponds_progress(pond_shapefile_path, admin_shapefile_path, xzq_name, basename):
    """
    计算池塘填报进度，并保存结果到 Excel 文件。

    参数：
    pond_shapefile_path (str): 池塘 Shapefile 文件路径
    admin_shapefile_path (str): 行政区 Shapefile 文件路径
    xzq_name (str): 行政区的字段名称，用于分组统计池塘数量
    basename (str): 输出 Excel 文件前缀
    """
    # 读取池塘的 Shapefile
    pond_gdf = gpd.read_file(pond_shapefile_path)

    # 读取行政区 Shapefile
    admin_gdf = gpd.read_file(admin_shapefile_path)
    admin_gdf[xzq_name] = admin_gdf['NAME']

    # 确保池塘数据和行政区数据的 CRS 相同
    pond_gdf = pond_gdf.to_crs(admin_gdf.crs)

    # 删除不必要的字段
    pond_gdf = pond_gdf.drop(['index_right'], axis=1)

    # 执行池塘与行政区的空间相交，找到与行政区相交的池塘
    ponds_with_town = gpd.sjoin(pond_gdf, admin_gdf[[xzq_name, 'geometry']], how='inner')

    # 去重 
    ponds_with_town = ponds_with_town.drop_duplicates(subset=['geometry'])

    # 按行政区分组并统计池塘数量
    town_pond_count = ponds_with_town.groupby(xzq_name).size().reset_index(name='池塘数量')

    # 筛选出“状态”不为“未填报”的池塘数据
    filled_ponds = ponds_with_town[ponds_with_town['填报状态'] != '未填报']

    # 按行政区分组并统计已填报池塘的数量
    town_filled_count = filled_ponds.groupby(xzq_name).size().reset_index(name='已填报数量')

    # 合并池塘数量和已填报数量数据
    merged_df = pd.merge(town_pond_count, town_filled_count, on=xzq_name, how='left')

    # 填充空值为 0
    merged_df['已填报数量'].fillna(0, inplace=True)

    # 计算填报进度（已填报数量 / 池塘数量）
    merged_df['填报进度'] = merged_df['已填报数量'] / merged_df['池塘数量']

    # 将已填报数量转换为百分比格式，保留两位小数
    merged_df['填报进度'] = merged_df['填报进度'].apply(lambda x: f"{x*100:.2f}%")

    # xzq_name"所在辖区"
    merged_df = merged_df.rename(columns={xzq_name: '所在辖区'})

    # 保存合并后的结果到 Excel 文件
    merged_df.to_excel(f"{basename}-填报进度统计.xlsx", index=False)

    print(f"填报进度统计结果已保存到：{basename}-填报进度统计.xlsx")

    # 筛选出“状态”为“未填报”的池塘数据
    unfilled_ponds_data = ponds_with_town[ponds_with_town['填报状态'] == '未填报']

    # xzq_name“图斑编号”和“所在辖区”
    # unfilled_ponds_data = unfilled_ponds[['TBID', xzq_name]]
    unfilled_ponds_data = unfilled_ponds_data.rename(columns={'TBID': '图斑编号', xzq_name: '所在辖区'})

    # 清理“图斑编号”列中的逗号
    unfilled_ponds_data['图斑编号'] = unfilled_ponds_data['图斑编号'].str.replace(',', '', regex=False)

    # 创建未填报池塘统计文件路径
    unfilled_output_path = f"{basename}-未填报图斑统计.xlsx"

    # 保存未填报池塘的统计数据到 Excel 文件
    unfilled_ponds_data[['图斑编号', '所在辖区']].to_excel(unfilled_output_path, index=False)

    print(f"未填报图斑统计结果已保存到：{unfilled_output_path}")

    # # 按行政区导出未填报图斑导出html页面
    # savepath = f"{basename}-未填报图斑分布"
    # os.makedirs(savepath,exist_ok=True)
    # unfilled_ponds_data = unfilled_ponds_data.to_crs('epsg:4490')
    # admin_gdf = admin_gdf.to_crs('epsg:4490')
    # unfilled_ponds_data['longitude'] = unfilled_ponds_data.geometry.centroid.x
    # unfilled_ponds_data['latitude'] = unfilled_ponds_data.geometry.centroid.y
    # for name in admin_gdf[xzq_name].unique():
    #     ct = unfilled_ponds_data[unfilled_ponds_data['所在辖区']==name]
    #     xzq = admin_gdf[admin_gdf[xzq_name]==name]
    #     unfilled_ponds_map = createCTMap(ct,xzq,labelfield='图斑编号')
    #     unfilled_ponds_map.save(f'{savepath}\\{name}-未填报池塘分布.html')

if __name__ == '__main__':
    pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\淮安市\20250228淮安市盱眙县进度统计'
    os.chdir(pth)

    pond_shapefile_path = '池塘信息-淮安市盱眙县20250228-池塘图斑.gpkg'
    admin_shapefile_path = '盱眙县_同名合并.shp'
    xzq_name = 'XZQMC'
    # xzq_name = '镇名称'
    # xzq_name = 'NAME'
    basename = f"{'-'.join(pond_shapefile_path.split('-')[0:-1])}-{os.path.basename(admin_shapefile_path)[0:3]}"

    calculate_filled_ponds_progress(pond_shapefile_path, admin_shapefile_path, xzq_name, basename)
