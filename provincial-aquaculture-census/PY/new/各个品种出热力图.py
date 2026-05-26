import geopandas as gpd
import pandas as pd
import folium
from folium import Choropleth, LayerControl
from branca.colormap import linear

# === 第一步：加载数据 ===
# 1. 读取产量表格（列：市、区县、品种、产量（吨））
yield_df = pd.read_excel(r"E:\全省养殖池溏上图入库普查\合规性检查\20250523\所有品种产量统计结果所有品种产量统计结果.xlsx")

# 2. 读取shapefile（必须包含“市”字段）
gdf = gpd.read_file(r"F:\xiangmu\江苏省天地图分割\实习生每日进度收集\天地图_2021公众版江苏省行政区划\JiangSu_XZQH.shp")  # 请替换为你的shp路径
gdf = gdf[["市", "geometry"]]  # 保留市字段和geometry

# === 第二步：按“市”和“品种”聚合产量 ===
city_yield = yield_df.groupby(["市", "品种"], as_index=False)["产量（吨）"].sum()

# === 第三步：循环每个品种，生成一个choropleth图层 ===
# 准备底图
m = folium.Map(location=[32.0, 119.0], zoom_start=7)

# 获取所有品种
varieties = city_yield["品种"].unique()

# 给每个品种生成一个图层
for variety in varieties:
    variety_data = city_yield[city_yield["品种"] == variety]

    # 将产量合并到GeoDataFrame中
    merged = gdf.merge(variety_data, how="left", on="市")
    merged["产量（吨）"] = merged["产量（吨）"].fillna(0)

    # 定义颜色比例尺（自动适应最大值）
    max_val = merged["产量（吨）"].max()
    min_val = merged["产量（吨）"].min()
    print(min_val)
    colormap = linear.Reds_08.scale(min_val, max_val)
    colormap.caption = f"{variety} 产量热力图（吨）"

    # 转为GeoJson格式，构建layer
    geojson = folium.GeoJson(
        merged,
        name=variety,
        style_function=lambda feature, v=variety: {
            'fillColor': colormap(feature["properties"]["产量（吨）"]),
            'color': 'black',
            'weight': 2,
            'fillOpacity': 0.8,
        },
        tooltip=folium.GeoJsonTooltip(fields=["市", "产量（吨）"], aliases=["市", f"{variety}产量（吨）"]),
        show=False  # 初始不显示，避免重叠
    )

    geojson.add_to(m)
    colormap.add_to(m)

# 添加图层切换器
folium.LayerControl(collapsed=False).add_to(m)

# === 第四步：保存地图 ===
m.save(r"E:\全省养殖池溏上图入库普查\合规性检查\20250523\品种热力图.html")
