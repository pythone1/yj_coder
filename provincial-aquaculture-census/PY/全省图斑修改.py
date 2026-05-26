import geopandas as gpd
import pandas as pd
from shapely.ops import transform
from shapely.geometry import mapping
import pyproj


def remove_z_coords(geom):
    """去除 Z 坐标，仅保留 XY 坐标。"""
    return transform(lambda x, y, z=None: (x, y), geom)


def load_data(file_A, file_B, file_points, file_excel):
    """加载池塘矢量数据和 Excel 表格。"""
    A = gpd.read_file(file_A)
    B = gpd.read_file(file_B)
    points = gpd.read_file(file_points)
    xls = pd.ExcelFile(file_excel)
    df = pd.read_excel(xls, sheet_name="Sheet1")
    return A, B, points, df


def find_deleted_ponds(A, B, df):
    """找出 A 有但 B 没有的 TBID，并添加到 Excel 结果表格。"""
    deleted = A[~A["TBID"].isin(B["TBID"])]
    for idx, row in deleted.iterrows():
        df.loc[len(df)] = [3, "", row["ID"], "", "", "", "", "", "", "", "", ""]
    return df


def process_new_ponds(B, points, df, max_existing_id=1319170):
    """处理 B 中 TBID 为空的新增池塘数据。"""
    new_rows = B[B["TBID"].isna()].copy().to_crs(32650)
    points = points.to_crs(32650)

    # 计算最大 TBID 编号
    tbid_parts = [x.split(",") for x in B["TBID"].dropna().astype(str) if "," in x]
    tbid_dict = {}
    for part in tbid_parts:
        prefix, number = part[0], int(part[1])
        tbid_dict[prefix] = max(tbid_dict.get(prefix, 0), number)

    most_common_prefix, max_num = (
    max(tbid_dict, key=tbid_dict.get), tbid_dict[max(tbid_dict, key=tbid_dict.get)]) if tbid_dict else ("1", 1)

    gdf_list = []
    num = 0
    for idx, row in new_rows.iterrows():
        num += 1
        new_TBID = f"{most_common_prefix},{max_num + num}"
        new_ID = max_existing_id + num
        area = row.geometry.area

        # 进行点匹配，判断是否填充池塘 ID
        intersecting_points = points[points.intersects(row.geometry)]
        pond_id = intersecting_points["池塘id"].values[0] if not intersecting_points.empty else ""
        pond_status = 2 if pond_id else 1

        # 坐标转换为 EPSG:4490
        project = pyproj.Transformer.from_crs("EPSG:32650", "EPSG:4490", always_xy=True).transform
        geom_2d = remove_z_coords(row.geometry)
        geom_4490 = transform(project, geom_2d)
        geom_str = ";".join([f"{x},{y}" for x, y in mapping(geom_4490)["coordinates"][0]])
        df.loc[len(df)] = [1, pond_id, new_ID, new_TBID, area, 1, 0, pond_status, 1, 1, 1, geom_str]

        gdf_list.append({
            "池塘id": pond_id,
            "ID": new_ID,
            "TBID": new_TBID,
            "area": area,
            "PSHSJ": 1,
            "YZLX": 0,
            "status": pond_status,
            "reserve1": 1,
            "reserve2": 1,
            "mode": 1,
            "geometry": geom_4490
        })


    return df, gpd.GeoDataFrame(gdf_list, geometry="geometry", crs="EPSG:4490")


def save_results(df, gdf, output_excel, output_geojson):
    """保存 Excel 和 GeoJSON 文件。"""
    df.to_excel(output_excel, index=False)
    gdf.to_file(output_geojson)


if __name__ == "__main__":
    file_A = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\常州市金坛区原始.shp"
    file_B = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\常州市金坛区.shp"
    file_points = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\常州市金坛区20250304-填报点.gpkg"
    file_excel = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\图斑更新(1).xlsx"
    output_excel = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\金坛区新增.xlsx"
    output_geojson = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\金坛区2.geojson"

    A, B, points, df = load_data(file_A, file_B, file_points, file_excel)
    df = find_deleted_ponds(A, B, df)
    df, gdf = process_new_ponds(B, points, df)
    save_results(df, gdf, output_excel, output_geojson)
