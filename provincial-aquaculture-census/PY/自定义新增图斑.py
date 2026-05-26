import geopandas as gpd
import pandas as pd
from shapely.ops import transform
from shapely.geometry import mapping
import pyproj


def load_shapefile(file_shp):
    """加载池塘矢量数据。"""
    return gpd.read_file(file_shp)

def remove_z_coords(geom):
    """去除 Z 坐标，仅保留 XY 坐标。"""
    return transform(lambda x, y, z=None: (x, y), geom)
def load_excel_template(file_excel):
    """加载 Excel 样本表格结构。"""
    xls = pd.ExcelFile(file_excel)
    return pd.read_excel(xls, sheet_name=xls.sheet_names[0])


def process_ponds(shp_file, file_excel, t_prefix="1", t_start=1, id_start=1000000, output_excel="output.xlsx",
                  output_geojson="output.geojson"):
    """处理 SHP 文件，生成表格和 GeoJSON 文件。"""
    gdf = load_shapefile(shp_file).to_crs(32650)
    df = load_excel_template(file_excel)

    gdf_list = []
    tbid_max = t_start
    id_max = id_start

    for idx, row in gdf.iterrows():
        if pd.notna(row.get("TBID")) and row["TBID"]:
            new_TBID = row["TBID"]  # 保留原有 TBID
            new_ID = row.get("ID", "")  # 保留原有 ID
        else:
            new_TBID = f"{t_prefix},{tbid_max}"
            new_ID = id_max
            tbid_max += 1
            id_max += 1

        area = row.geometry.area

        # 坐标转换为 EPSG:4490
        project = pyproj.Transformer.from_crs("EPSG:32650", "EPSG:4490", always_xy=True).transform
        geom_4490 = transform(project, row.geometry)

        geom_4490 = remove_z_coords(geom_4490)
        geom_str = ";".join([f"{x},{y}" for x, y in mapping(geom_4490)["coordinates"][0]])

        df.loc[len(df)] = [1, "", new_ID, new_TBID, area, 1, 0, 1, 1, 1, 1, geom_str]

        gdf_list.append({
            "池塘id": "",
            "ID": new_ID,
            "TBID": new_TBID,
            "area": area,
            "PSHSJ": 1,
            "YZLX": 0,
            "status": 1,
            "reserve1": 1,
            "reserve2": 1,
            "mode": 1,
            "geometry": geom_4490
        })

    df.to_excel(output_excel, index=False)
    # gpd.GeoDataFrame(gdf_list, geometry="geometry", crs="EPSG:4490").to_file(output_geojson)


if __name__ == "__main__":
    shp_file = r"E:\全省养殖池溏上图入库普查\图斑修改\20250806\20250521.shp"  # 这里替换为你的 SHP 文件路径
    file_excel = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\图斑更新(1).xlsx"  # 指定样本表格
    process_ponds(shp_file, file_excel, t_prefix="CZSJTQ", t_start=30604, id_start=1320700,
                  output_excel=r"E:\全省养殖池溏上图入库普查\图斑修改\20250806\20250521.xlsx",
                  output_geojson=r"E:\全省养殖池溏上图入库普查\图斑修改\20250311\result.geojson")
