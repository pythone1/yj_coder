import geopandas as gpd
from shapely.ops import unary_union
import shapely
import random
from collections import defaultdict

in_path = r"F:\20251027宜兴市养殖水域滩涂规划修编\数据\三区划定\禁养区.shp"
out_path = r"F:\20251027宜兴市养殖水域滩涂规划修编\过程数据\新建镇养殖区\去重叠\禁养区.gpkg"

# 优先级映射（数值越大表示优先级越高/更重要）
priority_map = {"1-2": 6, "1-3": 5, "1-4": 4, "1-5": 3, "1-1": 2, "1-6": 1}

# 面积阈值（m^2），小于此认为数值噪声
AREA_EPS = 1e-8

# 随机种子（可复现）
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# -----------------------
# 1. 读取并准备（保留原始属性，强制序号为字符串）
# -----------------------
gdf = gpd.read_file(in_path)
if gdf.crs is None:
    raise ValueError("输入图层没有 CRS，请先设定。")

if "序号" not in gdf.columns:
    raise ValueError("图层必须包含字段 '序号'（字符串），例如 '1-1'。")

# 保留原始列名（用于输出）
orig_columns = [c for c in gdf.columns if c != "geometry"]

# 生成唯一 id
gdf = gdf.reset_index().rename(columns={"index": "orig_index"})
gdf["序号"] = gdf["序号"].astype(str)

# 投影到米制（用于几何运算）
gdf_proj = gdf.to_crs(epsg=4326)
gdf_proj["geometry"] = gdf_proj.geometry.buffer(0)  # 修几何

# 初始化标记
gdf_proj["overlap"] = 0

# -----------------------
# 2. 两两判定重叠（用空间索引，仅当交集面积 > AREA_EPS 时视为重叠）并收集每对的交集几何
# -----------------------
sindex = gdf_proj.sindex
n = len(gdf_proj)
overlap_pairs = []  # list of (i, j, inter_geom)

for i in range(n):
    gi = gdf_proj.geometry.iloc[i]
    if gi is None or gi.is_empty:
        continue
    cand = list(sindex.intersection(gi.bounds))
    for j in cand:
        if j <= i:
            continue
        gj = gdf_proj.geometry.iloc[j]
        if gj is None or gj.is_empty:
            continue
        if not gi.intersects(gj):
            continue
        inter = gi.intersection(gj)
        if inter is None or inter.is_empty:
            continue
        if inter.area > AREA_EPS:
            overlap_pairs.append((i, j, inter))
            gdf_proj.at[i, "overlap"] = 1
            gdf_proj.at[j, "overlap"] = 1
            
AREA_EPS = 1e-10
# -----------------------
# 3. 切割并保留所有部分
#    对每个原要素 i：
#      - 找到所有与 i 重叠的 other 几何（原始其它要素的 geometry）
#      - 为 i 生成：每个交集块（from_overlap=1）和余下部分（可能多个，from_overlap=0）
# -----------------------
# 先构建每个 i 的交集几何列表（交集是 i 与 j 的交集）
inter_by_i = defaultdict(list)
for i, j, inter_geom in overlap_pairs:
    inter_by_i[i].append(inter_geom)
    inter_by_i[j].append(inter_geom)

# 新的记录列表
records = []

for idx, row in gdf_proj.iterrows():
    oid = int(row["orig_index"])
    orig_attrs = row[orig_columns].to_dict()  # 原始属性字典
    seq = str(row["序号"])
    geom = row.geometry

    # 1) 余下部分 = geom - union(intersections)
    inter_list = inter_by_i.get(idx, [])
    if inter_list:
        # union 可能为空
        union_inter = unary_union([g for g in inter_list if (g is not None and not g.is_empty)])
    else:
        union_inter = None

    if union_inter is None or union_inter.is_empty:
        # 无重叠交集，则原始几何全部作为一个 remainder（from_overlap=0）
        if geom is not None and (not geom.is_empty) and geom.area > AREA_EPS:
            rec = orig_attrs.copy()
            rec.update({
                "orig_index": oid,
                "orig_seq": seq,
                "from_overlap": 0,
                "geometry": geom
            })
            records.append(rec)
    else:
        # 差集可能为 Polygon 或 MultiPolygon 或 GeometryCollection
        remainder = geom.difference(union_inter)
        if remainder is not None and (not remainder.is_empty):
            # 若是多部件，拆开保存每一部分
            if remainder.geom_type == "Polygon":
                parts = [remainder]
            else:
                try:
                    parts = list(remainder.geoms)
                except Exception:
                    parts = [remainder]
            for p in parts:
                if p is None or p.is_empty or p.area <= AREA_EPS:
                    continue
                rec = orig_attrs.copy()
                rec.update({
                    "orig_index": oid,
                    "orig_seq": seq,
                    "from_overlap": 0,
                    "geometry": p
                })
                records.append(rec)

    # 2) 为该原要素把每个交集块都保存为单独记录（from_overlap=1）
    #    （即便交集块在不同原要素之间几何相同，我们也为每个原要素生成一条对应记录）
    for ig in inter_list:
        if ig is None or ig.is_empty or ig.area <= AREA_EPS:
            continue
        rec = orig_attrs.copy()
        rec.update({
            "orig_index": oid,
            "orig_seq": seq,
            "from_overlap": 1,
            "geometry": ig
        })
        records.append(rec)

# 形成 GeoDataFrame（使用投影 CRS）
gdf_cut = gpd.GeoDataFrame(records, crs=gdf_proj.crs)
gdf_cut = gdf_cut.reset_index(drop=True)

# -----------------------
# 4. 对所有来自交集（from_overlap==1）的块做“完全重叠”分组（几何一模一样）
#    用几何的 WKB 作为分组 key（通常稳定），组内比较所属 orig_seq 优先级，优先级最低的随机删一个
# -----------------------
# 初始化 删除 字段
gdf_cut["删除"] = 0

# 只处理 from_overlap==1
overlap_pieces = gdf_cut[gdf_cut["from_overlap"] == 1].copy()
overlap_pieces = overlap_pieces.reset_index()  # 保留原行index以便回写删除标记

def geom_wkb(g):
    if g is None or g.is_empty:
        return None
    return g.wkb

overlap_pieces["wkb"] = overlap_pieces.geometry.apply(geom_wkb)
overlap_pieces = overlap_pieces[overlap_pieces["wkb"].notnull()].copy()

# group identical geometries by wkb
groups = overlap_pieces.groupby("wkb")

for _, grp in groups:
    if len(grp) <= 1:
        continue  # 没有完全重叠
    # grp contains rows with identical geometry but possibly different orig_index (来自不同原要素)
    # Compute each row's priority value
    pr_list = []
    for i_r, r in grp.iterrows():
        seq = str(r["orig_seq"]) if r["orig_seq"] is not None else ""
        pr = priority_map.get(seq, 0)  # default 0 表示最低优先级
        pr_list.append(pr)
    # We treat larger number = higher priority (保留)，因此要删除优先级最小者
    min_pr = min(pr_list)
    # candidates indices within grp with this min_pr
    candidates = [int(idx) for idx, r in grp.iterrows() if priority_map.get(str(r["orig_seq"]), 0) == min_pr]
    # 如果有多个同样最低优先级，随机选一个删除
    if len(candidates) > 0:
        choice = random.Random(RANDOM_SEED + len(candidates)).choice(candidates)
        # grp.loc[choice, 'index'] gives the original index in gdf_cut (because we reset_index earlier)
        original_row_index = int(grp.loc[choice, "index"])
        gdf_cut.at[original_row_index, "删除"] = 1
        # 其余保留（删除=0）

# -----------------------
# 5. 删除删除标记为 1 的记录
# -----------------------
gdf_cut = gdf_cut[gdf_cut["删除"] == 0].reset_index(drop=True)

# -----------------------
# 6. 为切分后的记录生成 新序号（按 orig_seq 分组，依次编号 orig_seq-1, orig_seq-2...）
# -----------------------
group_counters = defaultdict(int)
new_seq_list = []
for _, r in gdf_cut.iterrows():
    key = r["orig_seq"] if r["orig_seq"] is not None else ""
    group_counters[key] += 1
    new_seq_list.append(f"{key}-{group_counters[key]}")
gdf_cut["新序号"] = new_seq_list

# -----------------------
# 7. 计算 规划面积（公顷） 与 经度/纬度（WGS84）
# -----------------------
# 规划面积（公顷）在投影 CRS（m）下直接计算
gdf_cut = gdf_cut.to_crs(32650)
gdf_cut["规划面积（公顷）"] = gdf_cut.geometry.area / 10000.0

# 计算经纬度（转回 WGS84）
gdf_out = gdf_cut.to_crs(epsg=4326)
centroids = gdf_out.geometry.centroid
gdf_out["经度"] = centroids.x
gdf_out["纬度"] = centroids.y

# -----------------------
# 8. 组织输出字段并写出（保留原始属性列 + 新字段）
# -----------------------
# 确保必要字段存在
for c in ["orig_index", "orig_seq", "from_overlap", "新序号", "删除", "规划面积（公顷）", "经度", "纬度"]:
    if c not in gdf_out.columns:
        gdf_out[c] = None

# 输出列顺序：原始列（除 geometry） + 控制字段 + geometry
out_cols = orig_columns.copy()
if "orig_index" not in out_cols:
    out_cols = ["orig_index"] + out_cols
# 保证不会重复
out_cols = list(dict.fromkeys(out_cols))
final_cols = out_cols + ["orig_seq", "from_overlap", "新序号", "删除", "规划面积（公顷）", "经度", "纬度", "geometry"]

# 写出 GeoPackage（单图层）
gdf_out.to_file(out_path, layer="ponds_final", driver="GPKG", encoding="utf-8")

print("✅ 处理完成，输出已保存：", out_path)
print(f"输入要素数: {len(gdf)}；切分后记录数: {len(gdf_out)}")
print(f"标记 overlap=1 的原始要素数: {int(gdf_proj['overlap'].sum())}")
print(f"标记 删除=1 的切分块数: {int((gdf_out['删除']==1).sum())}")
print("说明：")
print(" - 字段说明：orig_index(原要素id)、orig_seq(原序号)、from_overlap(1=交集块,0=余下部分)、新序号、删除(1=建议删除)、规划面积（公顷）、经度、纬度。")
