import pandas as pd

# 读取 Excel 数据
df = pd.read_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\出图\1\尾水模板.xlsx')  # 替换为实际路径

# 提取“市”字段
df['市'] = df['地址'].str.split('-').str[1]
df['面积'] = df['图斑面积_y']  # 记得单位为亩

# 计算各市总面积
total_area_by_city = df.groupby('市')['面积'].sum()
df_ws = df.copy()
尾水工艺 = ['原位修复', '三池两坝', '集中处理', '多级净化', '人工湿地', '其他']
# 只保留这六种尾水工艺的数据
df_ws = df[df['尾水处理工艺'].isin(尾水工艺)].copy()
# 计算尾水处理总面积（按市）
ws_area_by_city = df_ws.groupby('市')['面积'].sum()
ws_rate = (ws_area_by_city / total_area_by_city * 100).round(2)

# 各工艺面积与占比
ws_gongyi = df_ws.groupby(['市', '尾水处理工艺'])['面积'].sum().reset_index()
ws_gongyi = ws_gongyi.merge(ws_area_by_city.rename('总尾水面积'), on='市')
ws_gongyi['占比'] = (ws_gongyi['面积'] / ws_gongyi['总尾水面积'] * 100).round(2)

# 筛除“不处置”的淤泥处理方式
df_yn = df[df['清塘淤泥处理方式'] != '不处置']
yn_area_by_city = df_yn.groupby('市')['面积'].sum()
yn_rate = (yn_area_by_city / total_area_by_city * 100).round(2)

# 各工艺面积与占比
yn_gongyi = df_yn.groupby(['市', '清塘淤泥处理方式'])['面积'].sum().reset_index()
yn_gongyi = yn_gongyi.merge(yn_area_by_city.rename('总淤泥面积'), on='市')
yn_gongyi['占比'] = (yn_gongyi['面积'] / yn_gongyi['总淤泥面积'] * 100).round(2)

# 固定工艺顺序
尾水顺序 = ['原位修复', '三池两坝', '集中处理', '多级净化', '人工湿地', '其他']
淤泥顺序 = ['边坡堆放', '池塘内部堆填', '外运堆肥','外运填埋','其它']

# 汇总描述结果
results = []

for city in sorted(df['市'].dropna().unique()):
    ws_percent = ws_rate.get(city, 0.0)
    ws_gdf = ws_gongyi[ws_gongyi['市'] == city]
    ws_summary = []
    for g in 尾水顺序:
        area = ws_gdf[ws_gdf['尾水处理工艺'] == g]['面积']
        ws_summary.append(f"{area.values[0]:.2f}" if not area.empty else "0.0")

    yn_percent = yn_rate.get(city, 0.0)
    yn_gdf = yn_gongyi[yn_gongyi['市'] == city]
    yn_summary = []
    for g in 淤泥顺序:
        area = yn_gdf[yn_gdf['清塘淤泥处理方式'] == g]['面积']
        yn_summary.append(f"{area.values[0]:.2f}" if not area.empty else "0.0")

    desc = (
        f"{city}养殖池塘中，约{ws_percent:.2f}%的池塘会采用工艺进行尾水处理，"
        f"其中采用原位修复、三池两坝、集中处理、多级净化、人工湿地和其他方式的池塘面积分别为"
        f"{'、'.join(ws_summary)}亩。"
        f"{city}养殖池塘中，约{yn_percent:.2f}%的池塘会进行淤泥处置，"
        f"其中采用边坡堆放、池塘内部堆填、外运堆肥、其他方式的池塘面积分别为"
        f"{'、'.join(yn_summary)}亩。"
    )

    results.append({
        '市': city,
        '尾水处理占比%': ws_percent,
        '淤泥处置占比%': yn_percent,
        '尾水处理面积（原位修复）': ws_summary[0],
        '尾水处理面积（三池两坝）': ws_summary[1],
        '尾水处理面积（集中处理）': ws_summary[2],
        '尾水处理面积（多级净化）': ws_summary[3],
        '尾水处理面积（人工湿地）': ws_summary[4],
        '尾水处理面积（其他）': ws_summary[5],
        '淤泥处理面积（边坡堆放）': yn_summary[0],
        '淤泥处理面积（池塘内部堆填）': yn_summary[1],
        '淤泥处理面积（外运堆肥）': yn_summary[2],
        '淤泥处理面积（外运填埋）': yn_summary[3],
        '淤泥处理面积（其他）': yn_summary[4],
        '描述': desc
    })


# 保存为表格
result_df = pd.DataFrame(results)
result_df.to_excel(r'E:\全省养殖池溏上图入库普查\合规性检查\20250516\数据统计\各市尾水及淤泥处理描述统计(不筛选有无尾水处理占比更新).xlsx', index=False)

print("已生成并保存：各市尾水及淤泥处理描述统计.xlsx")
