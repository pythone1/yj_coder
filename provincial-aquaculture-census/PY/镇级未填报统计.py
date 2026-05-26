import os, glob

from CTXXTBYD import *


def TBJDTJ01(df, outfile):
    '''
    全省填报进度统计-填报点
    '''
    cols = ['省', '市', '区县', '街道', '村委']
    dz = df['地址'].str.split('-', expand=True)
    for i in range(len(cols)):
        df[cols[i]] = dz.loc[:, i]
    # df['村委'] = df['市'] + '-' + df['区县'] + '-' + df['街道'] + '-' + df['村委']
    # df['街道'] = df['市'] + '-' + df['区县'] + '-' + df['街道']
    # df['区县'] = df['市'] + '-' + df['区县']

    with pd.ExcelWriter(outfile, engine='openpyxl') as writer:
        for i, c in enumerate(cols):
            tj = df.groupby(cols[0:i + 1])[['养殖经营人名称']].count()
            tj.rename(columns={'养殖经营人名称': '总数'}, inplace=True)
            t = df[df['填报状态'] == '已填报养殖'].groupby(cols[0:i + 1])[['养殖经营人名称']].count()
            tj.loc[t.index, '已填报养殖'] = t.values
            t = df[df['填报状态'] == '已填报非养殖'].groupby(cols[0:i + 1])[['养殖经营人名称']].count()
            tj.loc[t.index, '已填报非养殖'] = t.values
            tj.to_excel(writer, sheet_name=c)


def TBJDTJ02(polygons, xzq, outfile):
    '''
    全省填报进度统计-填报图斑
    '''
    with pd.ExcelWriter(outfile, engine='openpyxl') as writer:
        # 省为单位
        tj3 = {
            '省': ['江苏省'],
            '总图斑个数': [],
            '已填报养殖个数': [],
            '已填报非养殖个数': [],
            '未填报个数': [],
            '总图斑面积(亩)': [],
            '已填报养殖面积(亩)': [],
            '已填报非养殖面积(亩)': [],
            '未填报面积(亩)': [],
        }
        p = polygons
        tj3['总图斑个数'].append(len(p))
        tj3['总图斑面积(亩)'].append(np.round(p["area"].sum() / 666.666, 2))
        p1 = p[p["填报状态"] == "已填报养殖"]
        tj3['已填报养殖个数'].append(len(p1))
        tj3['已填报养殖面积(亩)'].append(np.round(p1["area"].sum() / 666.666, 2))
        p2 = p[p["填报状态"] == "已填报非养殖"]
        tj3['已填报非养殖个数'].append(len(p2))
        tj3['已填报非养殖面积(亩)'].append(np.round(p2["area"].sum() / 666.666, 2))
        p3 = p[p["填报状态"] == "未填报"]
        tj3['未填报个数'].append(len(p3))
        tj3['未填报面积(亩)'].append(np.round(p3["area"].sum() / 666.666, 2))
        tj3 = pd.DataFrame(tj3)
        tj3.to_excel(writer, sheet_name='省', index=False)
        writer.save()

        # 市为单位
        tj2 = {
            '市': [],
            '总图斑个数': [],
            '已填报养殖个数': [],
            '已填报非养殖个数': [],
            '未填报个数': [],
            '总图斑面积(亩)': [],
            '已填报养殖面积(亩)': [],
            '已填报非养殖面积(亩)': [],
            '未填报面积(亩)': [],
        }
        shi = xzq['市'].unique()
        if 'index_right' in polygons:
            polygons.drop(columns='index_right', inplace=True)
        for s in shi:
            xzq_s = xzq[xzq['市'] == s]
            p = gpd.sjoin(polygons, xzq_s.loc[:, ['geometry']]).drop_duplicates(subset=['geometry'])
            tj2['市'].append(s)
            tj2['总图斑个数'].append(len(p))
            tj2['总图斑面积(亩)'].append(np.round(p["area"].sum() / 666.666, 2))
            p1 = p[p["填报状态"] == "已填报养殖"]
            tj2['已填报养殖个数'].append(len(p1))
            tj2['已填报养殖面积(亩)'].append(np.round(p1["area"].sum() / 666.666, 2))
            p2 = p[p["填报状态"] == "已填报非养殖"]
            tj2['已填报非养殖个数'].append(len(p2))
            tj2['已填报非养殖面积(亩)'].append(np.round(p2["area"].sum() / 666.666, 2))
            p3 = p[p["填报状态"] == "未填报"]
            tj2['未填报个数'].append(len(p3))
            tj2['未填报面积(亩)'].append(np.round(p3["area"].sum() / 666.666, 2))
        tj2 = pd.DataFrame(tj2)
        tj2.to_excel(writer, sheet_name='市', index=False)
        writer.save()

        # 区为单位
        tj1 = {
            '市': [],
            '区县': [],
            '总图斑个数': [],
            '已填报养殖个数': [],
            '已填报非养殖个数': [],
            '未填报个数': [],
            '总图斑面积(亩)': [],
            '已填报养殖面积(亩)': [],
            '已填报非养殖面积(亩)': [],
            '未填报面积(亩)': [],
        }
        if 'index_right' in polygons:
            polygons.drop(columns='index_right', inplace=True)
        for i, row in xzq.iterrows():
            p = polygons[polygons.intersects(row.geometry)]
            tj1['市'].append(row['市'])
            tj1['区县'].append(row['NAME'])
            tj1['总图斑个数'].append(len(p))
            tj1['总图斑面积(亩)'].append(np.round(p["area"].sum() / 666.666, 2))
            p1 = p[p["填报状态"] == "已填报养殖"]
            tj1['已填报养殖个数'].append(len(p1))
            tj1['已填报养殖面积(亩)'].append(np.round(p1["area"].sum() / 666.666, 2))
            p2 = p[p["填报状态"] == "已填报非养殖"]
            tj1['已填报非养殖个数'].append(len(p2))
            tj1['已填报非养殖面积(亩)'].append(np.round(p2["area"].sum() / 666.666, 2))
            p3 = p[p["填报状态"] == "未填报"]
            tj1['未填报个数'].append(len(p3))
            tj1['未填报面积(亩)'].append(np.round(p3["area"].sum() / 666.666, 2))
        tj1 = pd.DataFrame(tj1)

        tj1.to_excel(writer, sheet_name='区县', index=False)
        writer.save()


def extract_intersecting_ponds(admin_shp, pond_shp, output_shp):
    # 读取行政区范围文件
    admin_area = gpd.read_file(admin_shp)

    # 读取池塘文件
    ponds = gpd.read_file(pond_shp)

    # 确保两者有相同的坐标参考系（CRS）
    if ponds.crs != admin_area.crs:
        ponds = ponds.to_crs(admin_area.crs)

    # 使用空间连接（sjoin）找出池塘与行政区的交集
    intersecting_ponds = gpd.sjoin(ponds, admin_area, how="inner", op="intersects")

    # 导出相交的池塘到新的Shapefile
    intersecting_ponds.to_file(output_shp, driver="ESRI Shapefile")
    print(f"导出相交的池塘文件成功，文件路径：{output_shp}")


def process_data(input_file, output_folder):
    # 读取Excel文件
    df = pd.read_excel(input_file, dtype=str)

    # 筛选出未填报、待校对（村）、已返回（村）的数据

    filtered_df = df[df['状态'].isin([None, '待校对（村）', '已返回（村）']) | df['状态'].isnull()]
    filtered_df['状态'].fillna('未填报', inplace=True)  # 空数据填充为“未填报”

    print(filtered_df)
    # 按照“地址”列拆分，假设地址格式是 "镇-村"，拆分出镇和村
    filtered_df[['镇', '村']] = filtered_df['地址'].str.split('-', expand=True).iloc[:, [2, 3]]

    # 获取所有镇的唯一值
    towns = filtered_df['镇'].unique()

    # 对每个镇进行处理
    for town in towns:
        # 筛选出该镇的数据
        town_data = filtered_df[filtered_df['镇'] == town]

        # 获取该镇的每个村的数据并导出
        for village in town_data['村'].unique():
            village_data = town_data[town_data['村'] == village]

            # 创建一个Excel文件，每个村一个表单，表单名字为村名
            village_data = village_data[['TBID', '地址', '状态']]  # 只保留TBID, 地址, 状态字段

            # 导出到Excel文件，sheet名称为村名称
            output_file = f'{output_folder}/{town}_{village}.xlsx'
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                village_data.to_excel(writer, index=False, sheet_name=village)

            print(f"导出成功: {output_file}")


def process_data(pond_shp, district_shp, output_folder):
    # 读取池塘文件和行政区文件
    ponds = gpd.read_file(pond_shp)
    districts = gpd.read_file(district_shp)

    # 确保两个数据框的 CRS 一致
    if ponds.crs != districts.crs:
        ponds = ponds.to_crs(districts.crs)

    # 筛选池塘数据：只保留状态为 '待校对（村）', '已返回（村）' 或 空值的记录
    ponds_filtered = ponds[ponds['状态'].isin(['待校对（村）', '已返回（村）']) | ponds['状态'].isnull()]
    ponds_filtered['状态'].fillna('未填报', inplace=True)  # 空数据填充为“未填报”
    print(len(ponds_filtered))
    ponds_filtered['TBID'] = ponds_filtered['TBID'].str.replace(',', '')
    # 计算池塘与行政区（村）的空间连接，使用 'ZLDWMC' 字段作为村的名称
    ponds_filtered = gpd.sjoin(ponds_filtered[['geometry', 'TBID', '状态']], districts[['geometry', '镇名称', 'ZLDWMC']])

    # 处理每个镇，导出对应的 Excel 文件
    for town in ponds_filtered['镇名称'].unique():
        # 获取当前镇的数据
        town_data = ponds_filtered[ponds_filtered['镇名称'] == town]
        # 创建Excel写入器
        output_file = f"{output_folder}/{town}池塘统计.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 按村（ZLDWMC）拆分，并将每个村的池塘状态和TBID输出到单独的表单
            for village in town_data['ZLDWMC'].unique():
                village_data = town_data[town_data['ZLDWMC'] == village]
                # 将村数据写入对应的表单
                village_data[['TBID', '状态']].to_excel(writer, index=False, sheet_name=village)

        print(f"导出成功: {output_file}")

def process_data_ZHEN(pond_shp, district_shp, output_folder):
    # 读取池塘文件和行政区文件
    ponds = gpd.read_file(pond_shp)
    districts = gpd.read_file(district_shp)

    # 确保两个数据框的 CRS 一致
    if ponds.crs != districts.crs:
        ponds = ponds.to_crs(districts.crs)

    # 筛选池塘数据：只保留状态为 '待校对（村）', '已返回（村）' 或 空值的记录
    ponds_filtered = ponds[ponds['状态'].isin(['待校对（村）', '已返回（村）']) | ponds['状态'].isnull()]
    ponds_filtered['状态'].fillna('未填报', inplace=True)  # 空数据填充为“未填报”
    print(len(ponds_filtered))

    # 计算池塘与行政区（村）的空间连接，使用 'ZLDWMC' 字段作为村的名称
    ponds_filtered = gpd.sjoin(ponds_filtered[['geometry', 'TBID', '状态']], districts[['geometry', '镇名称']])

    # 去掉 TBID 中的逗号
    ponds_filtered['TBID'] = ponds_filtered['TBID'].str.replace(',', '')

    # 处理每个镇，导出对应的 Excel 文件
    for town in ponds_filtered['镇名称'].unique():
        # 获取当前镇的数据
        town_data = ponds_filtered[ponds_filtered['镇名称'] == town]

        # 创建Excel写入器
        output_file = f"{output_folder}/{town}填报统计.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 将镇的数据写入单独的表单
            town_data[['TBID', '状态']].to_excel(writer, index=False, sheet_name=town)

        print(f"导出成功: {output_file}")

if __name__ == '__main__':
    # 统计未填报的待审核的数据
    # pth = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\20250210姜堰进度统计'
    # os.chdir(pth)
    # ctxxfile = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\20250210姜堰进度统计\池塘信息-202502101330.xlsx'
    # ct_file = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\20250210姜堰进度统计\姜堰.shp'
    # xzq_fle = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\泰州市_姜堰区\姜堰区村级行政区划_同名合并.shp'
    # sjoins, polygons, pk = mergeData(ctxxfile, ct_file)
    # print(f'mergeData finished')
    # # 写出矢量
    # sjoins['池塘id'] = sjoins.index.values
    # sjoins.to_file(f'{ctxxfile.split(".")[0]}-填报点.gpkg', encoding='utf-8', driver='GPKG')
    # polygons = polygons.drop_duplicates(subset=['geometry'])  # 删除重复的面要素
    # polygons.drop('ID', axis=1).to_file(f'{ctxxfile.split(".")[0]}-池塘图斑.gpkg', encoding='utf-8', driver='GPKG')
    # print(f'write gpkg finished')

    # 使用示例
    pond_shp = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\20250210姜堰进度统计\池塘信息-202502101330-池塘图斑.gpkg'  # 替换为输入Excel文件的路径
    output_folder = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\疑点和进度统计\20250210姜堰进度统计\按照区县拆分'  # 替换为输出文件夹的路径
    district_shp = r'S:\项目数据\江苏省一池一档水产养殖基本情况普查项目\信息填报\按区县拆分池塘\泰州市_姜堰区\姜堰区村级行政区划_同名合并.shp'
    process_data_ZHEN(pond_shp, district_shp, output_folder)

