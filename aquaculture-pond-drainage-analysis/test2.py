import geopandas as gpd
from shapely.geometry import Polygon

# === 1. 读取 shp 文件 ===
shp_path = r"F:\20251027宜兴市养殖水域滩涂规划修编\数据\三区划定\禁养区.shp"   # 替换为你的文件路径
gdf = gpd.read_file(shp_path)
gdf = gdf.to_crs(epsg=4326)
# 给每个要素一个临时 id（原始索引保留）
gdf = gdf.reset_index().rename(columns={"index": "orig_index"})
gdf["geometry"] = gdf.geometry.buffer(0)  # 修复几何

eps = 0.000000001
gdf["overlap"] = 0

# overlay 计算交集（会包含自身与其他）
inter = gpd.overlay(gdf, gdf, how='intersection')

# overlay 会生成两个索引列：orig_index_1, orig_index_2 （不同 geopandas 版本名可能不同）
# 下面用通用方式找出代表左右两边索引的列名
idx_cols = [c for c in inter.columns if "orig_index" in c]
if len(idx_cols) < 2:
    # 有些 geopandas 版本交集后索引列可能叫 index_1, index_2
    idx_cols = [c for c in inter.columns if c.startswith("index")]

left_idx_col, right_idx_col = idx_cols[0], idx_cols[1]

# 过滤掉自身交集（两边索引相等的）
inter = inter[inter[left_idx_col] != inter[right_idx_col]]

# 只保留实际面积大于 eps 的交集
inter["area"] = inter.geometry.area
valid_inter = inter[inter["area"] > eps]

# 把所有出现过的 orig_index 标记为 overlap=1
left_ids = valid_inter[left_idx_col].unique().tolist()
right_ids = valid_inter[right_idx_col].unique().tolist()
all_ids = set(left_ids) | set(right_ids)

gdf.loc[gdf["orig_index"].isin(all_ids), "overlap"] = 1

# 如果你想恢复原始索引和列，可以：
gdf = gdf.set_index("orig_index")
# === 5. 保存结果 ===
out_path = r"F:\20251027宜兴市养殖水域滩涂规划修编\过程数据\新建镇养殖区\4.gpkg"
gdf.to_file(out_path, encoding="utf-8")

print("✅ 检查完成，结果已保存到：", out_path)
