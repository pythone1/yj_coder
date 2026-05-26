"""
round_corners.py

功能：把 gpkg/shp 中的多边形要素的尖角“圆角化”（适用于 EPSG:4326）
输入：任意多边形 gpkg/shp（或其它支持的格式）
输出：GeoPackage（gpkg）文件（图层名可自定义）

原理：
1. densify（细分边）—— 为每段边按指定最大距离插入更多点
2. buffer(radius).buffer(-radius) —— 用缓冲去掉尖角，得到圆角效果
3. 对异常几何进行回退处理，避免崩掉整个批处理

依赖：
  geopandas, shapely, numpy
"""

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LinearRing
from shapely.ops import unary_union
import numpy as np
import os
import sys

# ========== 参数区（请按需要修改） ==========
input_path = r"E:\水产种质资源保护区\网箱浮法.shp"   # 输入文件（支持 shp/gpkg 等）
output_gpkg = r"E:\水产种质资源保护区\网箱浮法_round.gpkg"  # 输出 gpkg 路径
out_layer = "pond_round"

# 对于 EPSG:4326 推荐值（度为单位）
densify_max_seg = 0.00003   # 每段最长的经纬度差，越小插点越密（建议 0.00002 ~ 0.00008）
round_radius = 0.00012      # 圆角半径（度），越大角越圆（建议 0.00005 ~ 0.0003）
min_area_threshold = 1e-10  # 面积过小则跳过（避免 tiny polygons）
# ============================================

def densify_coords(coords, max_seg):
    """给一圈 coords (list of (x,y), closed or not) 做细分插点，保证每段 <= max_seg（基于欧氏距离）"""
    # ensure numpy array
    pts = np.array(coords)
    if len(pts) == 0:
        return pts
    # if closed, remove last duplicate for processing, will close later
    closed = np.allclose(pts[0], pts[-1])
    if closed:
        pts = pts[:-1]
    new_pts = []
    for i in range(len(pts)):
        p0 = pts[i]
        p1 = pts[(i + 1) % len(pts)]
        seg_vec = p1 - p0
        seg_len = np.hypot(seg_vec[0], seg_vec[1])
        # Determine number of segments to split into (at least 1)
        if seg_len == 0:
            n = 1
        else:
            n = max(1, int(np.ceil(seg_len / max_seg)))
        # create points from p0 to p1, excluding endpoint except for final closure
        for k in range(n):
            t = k / n
            new_pts.append((p0[0] + seg_vec[0] * t, p0[1] + seg_vec[1] * t))
    # append final point (same as original first if closed)
    # ensure closure
    if not np.allclose(new_pts[0], new_pts[-1]):
        new_pts.append(new_pts[0])
    return np.array(new_pts)

def round_polygon(poly, densify_max_seg, radius):
    """对单个 Polygon 做 densify + buffer-rounding，若失败则返回原始 poly"""
    if poly is None or poly.is_empty:
        return poly
    try:
        # exterior
        ext_coords = list(poly.exterior.coords)
        ext_dense = densify_coords(ext_coords, densify_max_seg)
        if len(ext_dense) < 4:
            # 无法构成面，返回原始
            return poly

        # interiors (holes)
        interiors = []
        for ring in poly.interiors:
            rcoords = list(ring.coords)
            r_dense = densify_coords(rcoords, densify_max_seg)
            if len(r_dense) >= 4:
                interiors.append(r_dense.tolist())

        # rebuild polygon from densified coords
        try:
            poly_dense = Polygon(ext_dense, interiors)
            if not poly_dense.is_valid:
                # try to fix by buffering 0
                poly_dense = poly_dense.buffer(0)
        except Exception:
            poly_dense = poly  # fallback

        # small-area protection
        if poly_dense.area < min_area_threshold:
            return poly

        # buffer rounding: positive buffer then negative buffer to keep roughly same shape
        rounded = poly_dense.buffer(radius, join_style=1, resolution=16)  # join_style=1 round
        rounded = rounded.buffer(-radius, join_style=1, resolution=16)
        # if buffer produced MultiPolygon (split), try unary_union or keep as-is
        if rounded.is_empty:
            return poly
        # ensure result is polygonal
        if isinstance(rounded, (Polygon, MultiPolygon)):
            return rounded
        else:
            return poly
    except Exception as e:
        # 出错回退原始几何，打印简单日志
        print("⚠️ round_polygon failed for one feature:", e)
        return poly

def process_gdf(gdf, densify_max_seg, radius):
    """处理 GeoDataFrame，返回新 GDF（保留原属性）"""
    geoms = []
    for i, geom in enumerate(gdf.geometry):
        if geom is None or geom.is_empty:
            geoms.append(geom)
            continue
        # 支持 Polygon / MultiPolygon
        if geom.geom_type == "Polygon":
            geoms.append(round_polygon(geom, densify_max_seg, radius))
        elif geom.geom_type == "MultiPolygon":
            parts = []
            for p in geom.geoms:
                parts.append(round_polygon(p, densify_max_seg, radius))
            # 合并非空部分
            parts = [p for p in parts if p is not None and not p.is_empty]
            if len(parts) == 0:
                geoms.append(geom)
            elif len(parts) == 1:
                geoms.append(parts[0])
            else:
                geoms.append(MultiPolygon(parts))
        else:
            # 非面要素直接保留
            geoms.append(geom)
    new_gdf = gdf.copy()
    new_gdf.geometry = geoms
    return new_gdf

def main():
    # 读取
    print("读取：", input_path)
    gdf = gpd.read_file(input_path)
    if gdf.crs is None:
        print("警告：输入图层无 CRS，请确认为 EPSG:4326！")
    else:
        print("输入 CRS:", gdf.crs)

    # 若不是 4326，提醒并继续（因为半径是度单位）
    if str(gdf.crs).find("4326") == -1:
        print("提示：当前输入 CRS 不是 EPSG:4326。脚本假定圆角半径和密度参数以经纬度度数为单位。")

    print(f"共 {len(gdf)} 要素，开始处理（densify_max_seg={densify_max_seg}, round_radius={round_radius}）...")
    result = process_gdf(gdf, densify_max_seg, round_radius)

    # 写出
    if os.path.exists(output_gpkg):
        os.remove(output_gpkg)
    result.to_file(output_gpkg, driver="GPKG", layer=out_layer)
    print("完成，输出：", output_gpkg)

if __name__ == "__main__":
    main()
