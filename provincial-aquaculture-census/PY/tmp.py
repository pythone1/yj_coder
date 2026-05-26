import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df = pd.read_excel(r"D:\Users\Documents\WXWork\1688858186325806\Cache\File\2025-12\连云港市.xlsx")

gdf = gpd.GeoDataFrame(
    df,
    geometry=[Point(xy) for xy in zip(df["jd"], df["wd"])],
    crs="EPSG:4326"
)

gdf.to_file("结果_WGS84.gpkg", driver="GPKG", index=False)
