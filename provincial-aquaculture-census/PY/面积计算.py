import geopandas as gpd
import geopandas as gpd
import pandas as pd

# 读取gpkg
gpkg_path = r"E:\全省养殖池溏上图入库普查\项目验收\20260310\无锡市池塘信息.gpkg"
gdf = gpd.read_file(gpkg_path)

# 地址字段按 "-" 拆分，取第三个
gdf["地址拆分"] = gdf["地址"].astype(str).str.split("-").str[2]

# 投影到32650计算面积
gdf_proj = gdf.to_crs(epsg=32650)

# 计算面积（平方米）
gdf_proj["面积"] = gdf_proj.geometry.area

# 分组统计
result = (
    gdf_proj
    .groupby(["填报状态", "地址拆分"])
    .agg(
        图斑数量=("geometry", "count"),
        总面积=("面积", "sum")
    )
    .reset_index()
)

# 面积转亩（可选）
result["总面积_亩"] = result["总面积"] / 666.6667

# 输出
print(result)

# 保存Excel
result.to_excel("统计结果.xlsx", index=False)
# # shp路径
# shp_path = r"E:\全省养殖池溏上图入库普查\项目验收\20260310\二级保护区.gpkg"
#
# # 读取shp
# gdf = gpd.read_file(shp_path, encoding='gbk')
#
# # 如果原始是经纬度
# if gdf.crs is None:
#     gdf = gdf.set_crs(4326)
#
# # 转投影到32650
# gdf = gdf.to_crs(32650)
#
# # 计算面积
# gdf["area_m2"] = gdf.geometry.area
# gdf["area_mu"] = gdf["area_m2"] * 0.0015
#
# # 按填报状态统计：数量 + 面积
# result = gdf.groupby("填报状态").agg(
#     数量=("geometry", "count"),
#     总面积_平方米=("area_m2", "sum"),
#     总面积_亩=("area_mu", "sum")
# )
#
# print(result)

