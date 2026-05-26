import os
import glob
import numpy as np
from osgeo import gdal, osr

# ========= 你的函数 =========
class geotiffinfo:
    def __init__(self, rows, cols, bands, geo_transform, projection, dataarray, epsg):
        self.rows = rows
        self.cols = cols
        self.bands = bands
        self.geo_transform = geo_transform
        self.projection = projection
        self.dataarray = dataarray
        self.epsg = epsg


def geotiffread(tiffile):
    raster_dataset = gdal.Open(tiffile, gdal.GA_ReadOnly)
    geo_transform = raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()
    srs = osr.SpatialReference(wkt=proj)
    epsg = srs.GetAttrValue("AUTHORITY", 1)

    dataarray = []
    for i in range(1, raster_dataset.RasterCount + 1):
        band = raster_dataset.GetRasterBand(i)
        dataarray.append(band.ReadAsArray())
    dataarray = np.dstack(dataarray)
    rows, cols, bands = dataarray.shape
    del raster_dataset, band
    return geotiffinfo(rows, cols, bands, geo_transform, proj, dataarray, epsg)


def getNDWI(refdata):
    refdata = refdata.astype(np.float32)
    g, nir = refdata[:, :, 1], refdata[:, :, 3]  # G = band2, NIR = band4
    ndwi = (g - nir) / (g + nir + 1e-6)  # 防止除0
    ndwi[np.isnan(ndwi)] = 0
    return ndwi


def geotiffwrite(tiffile, data, geo_transform, projection, datatype="FLOAT32"):
    driver = gdal.GetDriverByName("GTiff")
    if len(data.shape) == 3:
        rows, cols, bands = data.shape
    else:
        rows, cols = data.shape
        bands = 1
    if datatype == "FLOAT32":
        dataset = driver.Create(
            tiffile, cols, rows, bands, gdal.GDT_Float32,
            options=["TILED=YES", "COMPRESS=LZW"]
        )
    elif datatype == "UINT8":
        dataset = driver.Create(
            tiffile, cols, rows, bands, gdal.GDT_Byte,
            options=["TILED=YES", "COMPRESS=LZW"]
        )
    else:
        raise ValueError("Unsupported data type")

    dataset.SetGeoTransform(geo_transform)
    dataset.SetProjection(projection)
    if bands == 1:
        dataset.GetRasterBand(1).WriteArray(data)
    else:
        for i in range(bands):
            dataset.GetRasterBand(i + 1).WriteArray(data[:, :, i])
    dataset = None
    print(f"✅ 写出成功: {os.path.basename(tiffile)}")


# ========= 主程序 =========
def batch_calculate_ndwi(input_dir):
    tif_files = glob.glob(os.path.join(input_dir, "*.tif"))
    if not tif_files:
        print("⚠️ 没有找到任何 tif 文件")
        return
    print(f"共找到 {len(tif_files)} 个 TIF 文件")

    for tif in tif_files:
        try:
            print(f"➡️ 正在处理: {os.path.basename(tif)}")
            ref = geotiffread(tif)
            ndwi = getNDWI(ref.dataarray)
            out_tif = os.path.splitext(tif)[0] + "_ndwi.tif"
            geotiffwrite(out_tif, ndwi, ref.geo_transform, ref.projection, "FLOAT32")
        except Exception as e:
            print(f"❌ {os.path.basename(tif)} 处理失败: {e}")


if __name__ == "__main__":
    # ======= 修改为你的栅格所在文件夹路径 =======
    input_dir = r"E:\哨兵影像\20251229\drive-download-20251230T011616Z-1-001\SQD"
    batch_calculate_ndwi(input_dir)
