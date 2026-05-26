from pathlib import Path
import shutil
import geopandas as gpd

shp_path = Path(r"E:\全省养殖池溏上图入库普查\填报进度统计\0409\盐城市_池塘图斑_地址含盐城市_shp\盐城市_池塘图斑_地址含盐城市.shp")
out_dir = shp_path.parent
stem = shp_path.stem

tmp_dir = out_dir / "_tbmj_update_tmp"
if tmp_dir.exists():
    shutil.rmtree(tmp_dir)
tmp_dir.mkdir()
tmp_shp = tmp_dir / (stem + ".shp")

gdf = gpd.read_file(shp_path)
proj = gdf.to_crs(epsg=32650)
gdf["tbmj"] = (proj.geometry.area * 0.0015).round(6)
gdf.to_file(tmp_shp, driver="ESRI Shapefile", encoding="UTF-8")

for suffix in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
    src = tmp_shp.with_suffix(suffix)
    dst = shp_path.with_suffix(suffix)
    if dst.exists():
        dst.unlink()
    shutil.move(str(src), str(dst))

shutil.rmtree(tmp_dir)

print("updated_rows=", len(gdf))
print("tbmj_min=", float(gdf["tbmj"].min()))
print("tbmj_max=", float(gdf["tbmj"].max()))
print("tbmj_head=", gdf["tbmj"].head(5).tolist())
