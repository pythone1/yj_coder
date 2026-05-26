import geopandas as gpd
import numpy as np
import pandas as pd
import os
import pinyin

def generate_tbid_for_city(total_admin,path_ponds, output_path, step=0.001):
    # 读取池塘矢量文件
    gdf_ponds = gpd.read_file(path_ponds)
    gdf_ponds = gdf_ponds.to_crs(4326)

    gdf_ponds['ID'] = range(1, len(gdf_ponds) + 1)


    # 遍历每个区县并进行相交、编号、保存操作
    for idx, admin_row in total_admin.iterrows():
        #市名称
        shi = admin_row['市']
        #区县名称
        district = admin_row['NAME']
        # 获取当前区县的边界
        gdf_admin_filtered = gpd.GeoDataFrame([admin_row], geometry='geometry', crs=total_admin.crs)
        # 初步筛选：仅保留与当前区县有交集的完整池塘图斑
        intersecting_ponds = gdf_ponds[gdf_ponds.intersects(gdf_admin_filtered.unary_union)]
        print(f"与 {district} 相交的图斑数量: {len(intersecting_ponds)}")
        if intersecting_ponds.empty:
            print(f"未找到匹配的图斑：{district}")
            continue

        # 计算池塘与行政区的相交部分面积
        intersected = gpd.overlay(intersecting_ponds, gdf_admin_filtered, how='intersection')
        intersected['area_within'] = intersected.geometry.area
        intersecting_ponds = intersecting_ponds.merge(intersected[['ID', 'area_within']], on='ID', how='left')
        intersecting_ponds['area_within'] = intersecting_ponds['area_within'].fillna(0) 

        boundary_ponds = intersecting_ponds[~intersecting_ponds.within(gdf_admin_filtered.unary_union)]
        print(len(boundary_ponds))
        # boundary_ponds.to_excel(r'G:\xiangmu\江苏省天地图分割\实习生每日进度收集\编号测试\图斑简化结果\1.xlsx')
        # 创建有效池塘的副本
        valid_ponds = intersecting_ponds.copy()

        # 检查边界池塘是否在其他区县中有更大的面积
        for pond_idx, pond_row in boundary_ponds.iterrows():
            pond_id = pond_row['ID']
            area_within = pond_row['area_within']
            area_dict = {}
            intersecting_admin = total_admin[total_admin.intersects(pond_row['geometry']) & (total_admin['NAME'] != district)]
            for admin_idx, admin in intersecting_admin.iterrows():
                # 获取当前区县的边界
                gdf_admin_filtered = gpd.GeoDataFrame([admin], geometry='geometry', crs=total_admin.crs)
                # 计算池塘与当前区县的相交部分
                intersected = gpd.overlay(intersecting_ponds[intersecting_ponds['ID'] == pond_id],
                                          gdf_admin_filtered, how='intersection')
                # 计算相交部分的面积
                intersected_area = intersected.geometry.area.sum()
                area_dict[admin['NAME']] = intersected_area
            if area_dict:
                # 找到交集面积最大的区县
                max_area_district = max(area_dict, key=area_dict.get)
                max_area = area_dict[max_area_district]
                print(area_dict, admin, max_area,area_within)
                # 如果在其他区县中找到了更大的相交面积，则从 valid_ponds 中去除该池塘
                if max_area > area_within:
                    print(f"池塘ID {pond_id} 在其他区县中的相交面积更大，去除该图斑。")
                    valid_ponds = valid_ponds[valid_ponds['ID'] != pond_id]

        # 如果没有符合条件的图斑，跳过
        if valid_ponds.empty:
            print(f"未找到符合条件的图斑：{district}")
            continue

        # 生成TBID字段
        short_name = ''.join(
            [word[0].upper() for word in pinyin.get(admin_row['市'] + district, format='strip', delimiter=' ').split()])
        print(short_name)
        valid_ponds['centroid'] = valid_ponds.centroid
        valid_ponds['x'] = valid_ponds.centroid.x
        valid_ponds['y'] = valid_ponds.centroid.y
        y_min = valid_ponds['y'].min()
        y_max = valid_ponds['y'].max()
        current_ctbh = 1
        results = []

        for y in np.arange(y_max + step, y_min - step, -step):
            subset = valid_ponds[(valid_ponds['y'] <= y) & (valid_ponds['y'] > y - step)]
            if not subset.empty:
                subset = subset.sort_values(by='x')
                subset['TBID'] = [short_name + ',' + str(i).zfill(5) for i in
                                  range(current_ctbh, current_ctbh + len(subset))]
                current_ctbh += len(subset)
                results.append(subset)

        # 合并所有结果并更新原始 intersecting_ponds 的 TBID 字段
        valid_ponds = gpd.GeoDataFrame(pd.concat(results, ignore_index=True), geometry='geometry')
        intersecting_ponds = intersecting_ponds.merge(valid_ponds[['ID', 'TBID']], on='ID', how='left')

        # 移除不必要的字段并保存文件
        intersecting_ponds = intersecting_ponds.to_crs(32650)
        intersecting_ponds['area'] = intersecting_ponds.geometry.area
        intersecting_ponds['ID'] = intersecting_ponds['ID'].astype(float)
        # 将 'area' 字段中为空的值设置为 0
        intersecting_ponds['area'] = intersecting_ponds['area'].fillna(0)

        # 添加新字段并设置默认值
        intersecting_ponds['PSHSJ'] = '/'
        intersecting_ponds['YZLX'] = 0
        intersecting_ponds['status'] = 1
        intersecting_ponds['reserve1'] = 1
        intersecting_ponds['reserve2'] = 1

        intersecting_ponds['ID'] = intersecting_ponds['ID'].astype(float)
        intersecting_ponds['YZLX'] = intersecting_ponds['YZLX'].astype(str)
        intersecting_ponds['PSHSJ'] = intersecting_ponds['PSHSJ'].astype(str)
        intersecting_ponds = intersecting_ponds.dropna(subset=['TBID'])
        print(intersecting_ponds['ID'].dtype)  # 这将输出列的类型，例如：float64
        intersecting_ponds = intersecting_ponds[
            ['area', 'ID', 'TBID', 'PSHSJ', 'YZLX', 'status', 'reserve1', 'reserve2', 'geometry']]
        intersecting_ponds = intersecting_ponds.to_crs(4490)
        output_file = os.path.join(output_path,
                                   os.path.splitext(os.path.basename(path_ponds))[0] + f'_{shi+district}_ID_TBID.gpkg')
        intersecting_ponds.to_file(output_file,ecoding='utf-8')

def batch_process_ponds(admin_shp, ponds_file, output_path):
    # 读取全省的行政区矢量文件
    gdf_admin = gpd.read_file(admin_shp)
    gdf_admin = gdf_admin.to_crs(4326)

    # 处理指定文件
    generate_tbid_for_city(gdf_admin,ponds_file, output_path)

if __name__ == '__main__':
    #合并全省图斑（去重）

    # 全省图斑编号
    admin_shp = r'S:\天地图矢量图\全省池塘编号测试\JiangSu_XZQH.shp' # 特定文件，改过沭阳县-->沭和一县
    ponds_file = r'S:\天地图矢量图\全省池塘编号测试\全省图斑.shp'
    output_path = r'S:\天地图矢量图\全省池塘编号测试\按区县编号'
    batch_process_ponds(admin_shp, ponds_file, output_path)
