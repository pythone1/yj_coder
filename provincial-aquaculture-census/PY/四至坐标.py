import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import os

# 极简版：读取面（Polygon/MultiPolygon）shp -> 转 4326 -> 提取外环顶点 -> 自动编号 -> 导出 GPKG 与 Excel

def shp_polygons_to_vertices(shp_path: str, output_gpkg: str, output_excel: str):
    gdf = gpd.read_file(shp_path)

    if gdf.crs is None:
        raise ValueError("输入 shp 缺少 CRS，请先在 GIS 中定义或在代码中设置原始 EPSG 后再运行。")

    gdf = gdf.to_crs(epsg=4326)

    records = []
    geoms = []
    pid = 1

    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        # 只处理 Polygon / MultiPolygon 的外环顶点
        parts = []
        if geom.geom_type == 'Polygon':
            parts = [geom]
        elif geom.geom_type == 'MultiPolygon':
            parts = list(geom.geoms)
        else:
            # 非面要素也尽量处理（LineString/Point）
            try:
                coords = list(geom.coords)
            except Exception:
                continue
            for c in coords:
                x = c[0]; y = c[1]
                records.append({'point_id': pid, 'lon': x, 'lat': y})
                geoms.append(Point(x, y))
                pid += 1
            continue

        for part in parts:
            for c in list(part.exterior.coords):
                # 有时坐标是 (x, y, z) 或更多，取前两个
                x = c[0]; y = c[1]
                records.append({'point_id': pid, 'lon': x, 'lat': y})
                geoms.append(Point(x, y))
                pid += 1

    pts_gdf = gpd.GeoDataFrame(records, geometry=geoms, crs='EPSG:4326')

    # 确保输出目录存在
    def _ensure_dir(p):
        d = os.path.dirname(p)
        if d:
            os.makedirs(d, exist_ok=True)

    _ensure_dir(output_gpkg)
    _ensure_dir(output_excel)

    # 写入 GPKG（点图层，图层名 vertices）
    pts_gdf.to_file(output_gpkg, layer='vertices', driver='GPKG')

    # 写入 Excel（只包含 point_id, lon, lat）
    pd.DataFrame(records)[['point_id', 'lon', 'lat']].to_excel(output_excel, index=False)

    print(f"完成：共导出 {len(records)} 个点 -> {output_gpkg} 和 {output_excel}")




if __name__ == "__main__":
    shp_path = r"E:\哨兵影像\20251009张国正\11.gpkg"  # 输入shp路径
    output_gpkg = r"E:\哨兵影像\20251009张国正\1118.gpkg"  # 输出gpkg
    output_excel = r"E:\哨兵影像\20251009张国正\1118.xlsx"  # 输出excel

    shp_polygons_to_vertices(shp_path, output_gpkg, output_excel)
