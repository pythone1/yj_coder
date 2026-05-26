import geopandas as gpd

# 读取 GPKG 文件
gdf = gpd.read_file(r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-06\池塘信息表--池塘图斑(1).gpkg")

# 地址字段筛选含有指定关键词
keywords_address = ['宜兴']
address_mask = gdf['地址'].fillna('').apply(lambda x: any(k in x for k in keywords_address))

# 品种字段筛选含有“鲫鱼”或“鳊”
keywords_fish = ['鲫鱼', '鳊']
fish_mask = gdf['养殖品种/预计亩产量'].fillna('').apply(lambda x: any(k in x for k in keywords_fish))

# 过滤图斑
filtered_gdf = gdf[address_mask & fish_mask]

# 计算中心点
centroids = filtered_gdf.geometry.centroid

# 创建新的 GeoDataFrame 只包含中心点（无字段）
centroid_gdf = gpd.GeoDataFrame(geometry=centroids, crs=filtered_gdf.crs)

# 导出为 shapefile
centroid_gdf.to_file(r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-06\宜兴市鳊鱼鲫鱼中心点坐标\宜兴市鳊鱼鲫鱼中心点坐标.shp", encoding='utf-8')
