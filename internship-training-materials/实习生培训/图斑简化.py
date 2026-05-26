import geopandas as gpd

orifile = r'D:\图斑校核\current\武进区d5m_x104240_x117270_去河湖_范围内_补图斑1.shp'
dstfile = r'D:\图斑校核\current\武进区d5m_x104240_x117270_去河湖_范围内_补图斑1_simp.shp'

gdf = gpd.read_file(orifile)
gdf.geometry = gdf.geometry.simplify(tolerance=0.5)

gdf.to_file(dstfile)