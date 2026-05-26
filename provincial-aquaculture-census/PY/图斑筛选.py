import geopandas as gpd
import pandas as pd

# 读取 Excel，提取 "图斑ID （新增 修改 删除必填）" 列
excel_path = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\删除.xlsx"  # 修改为你的 Excel 文件路径
sheet_name = "Sheet1"  # 修改为正确的工作表名称
df_excel = pd.read_excel(excel_path, sheet_name=sheet_name)

# 提取 "图斑ID （新增 修改 删除必填）" 列，并去除空值
id_list = df_excel["ID"].dropna().astype(str).tolist()

# 读取 SHP 文件
shp_path = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\常州市金坛区原始.shp"  # 修改为你的 Shapefile 路径
gdf = gpd.read_file(shp_path)

# 筛选 ID 在 id_list 里的项目
filtered_gdf = gdf[gdf["ID"].astype(str).isin(id_list)]

# 指定要保存的 Excel 文件路径
output_excel_path = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\删除结果.gpkg"
filtered_gdf.to_file(output_excel_path)
# 保存结果到 Excel
output_excel_path = r"E:\全省养殖池溏上图入库普查\图斑修改\常州市\金坛区\新增专用.excel"
filtered_gdf.drop(columns="geometry").to_excel(output_excel_path, index=False)
