"""
项目名称: aquaculture-census-platform
技术领域: 01-geospatial-remote-sensing
模块说明: new.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import geopandas as gpd

# 输入文件（支持 shp / gpkg）
input_path = r"E:\全省养殖池溏上图入库普查\项目验收\20260310\无锡市池塘信息.gpkg"   # 或 .shp
output_path = r"E:\全省养殖池溏上图入库普查\项目验收\20260310\锡山惠山.gpkg"      # 或 .shp

# 读取数据
gdf = gpd.read_file(input_path)

# ====== 核心筛选 ======
gdf_filtered = gdf[
    (
        gdf["地址"].str.contains("锡山", na=False) |
        gdf["地址"].str.contains("惠山", na=False)
    )
    & (gdf["图斑面积"] > 20)
    & (gdf["填报状态"] == "已填报养殖")
]

# ====== 导出 ======
gdf_filtered.to_file(output_path, driver="GPKG", encoding="utf-8")

print(f"筛选完成，共 {len(gdf_filtered)} 条")