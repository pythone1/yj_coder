import geopandas as gpd
import os
import pandas as pd

os.chdir(r'E:\全省养殖池溏上图入库普查\项目验收\图斑变更')

# 读取图斑 A 和 B
gdf_a = gpd.read_file("20241225江苏省池塘图斑.shp")[['TBID', 'geometry']].copy()
gdf_b = gpd.read_file("20250522池塘图斑.gpkg")[['tbid', 'geometry']].copy().rename(columns={'tbid': 'TBID'})

# 获取 TBID 集合
set_a = set(gdf_a['TBID'])
set_b = set(gdf_b['TBID'])

# 分类统计
deleted_tbids = set_a - set_b
added_tbids = set_b - set_a
common_tbids = set_a & set_b

# 提取编号相同的图斑
gdf_a_common = gdf_a[gdf_a['TBID'].isin(common_tbids)].copy()
gdf_b_common = gdf_b[gdf_b['TBID'].isin(common_tbids)].copy()

# 添加来源标记
gdf_a_common['source'] = 'A'
gdf_b_common['source'] = 'B'

# 拼接图斑用于判断轮廓是否一致
gdf_ab = pd.concat([gdf_a_common, gdf_b_common], ignore_index=True)
gdf_ab['to_discard'] = 0

# 空间连接找出可能重叠的图斑对
gdf_sjoined = gpd.sjoin(gdf_ab, gdf_ab, how='inner', predicate='intersects')

# 对于 TBID 相同且来源不同的图斑对，计算 IOU 判断是否轮廓一致
for index, row in gdf_sjoined.iterrows():
    left_index = index
    right_index = row['index_right']
    if left_index == right_index:
        continue  # 自比较跳过
    if gdf_ab.at[left_index, 'source'] == gdf_ab.at[right_index, 'source']:
        continue  # 同来源跳过，只比较 A vs B

    geom1 = gdf_ab.at[left_index, 'geometry']
    geom2 = gdf_ab.at[right_index, 'geometry']
    inter_area = geom1.intersection(geom2).area
    union_area = geom1.union(geom2).area
    iou = inter_area / union_area

    if 1 - iou <= 0.001:  # 轮廓几乎一致，保留其中一个
        gdf_ab.at[left_index, 'to_discard'] = 1  # 不影响结果，只用于排除一致图斑

# 得到变化图斑 TBID 列表
changed_tbids = gdf_ab[(gdf_ab['to_discard'] == 0) & (gdf_ab['source'] == 'B')]['TBID'].tolist()

# 打印统计结果
print(f"原有图斑数（A）: {len(set_a)}")
print(f"当前图斑数（B）: {len(set_b)}")
print(f"删除图斑数: {len(deleted_tbids)}")
print(f"新增图斑数: {len(added_tbids)}")
print(f"编号不变但轮廓改变的图斑数: {len(changed_tbids)}")
print(f"总变更图斑数: {len(deleted_tbids) + len(added_tbids) + len(changed_tbids)}")

# 导出删除、新增和轮廓改变图斑
gdf_a[gdf_a['TBID'].isin(deleted_tbids)].to_file("删除图斑.gpkg", driver='GPKG')
gdf_b[gdf_b['TBID'].isin(added_tbids)].to_file("新增图斑.gpkg", driver='GPKG')
gdf_b[gdf_b['TBID'].isin(changed_tbids)].to_file("轮廓改变图斑.gpkg", driver='GPKG')
