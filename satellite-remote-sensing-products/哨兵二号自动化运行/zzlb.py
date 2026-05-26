import shutil
import imgProcess as imgpro
import zipfile
import os
import glob
import xml.dom.minidom
import numpy as np
import math
import matplotlib.pyplot as plt
import pandas as pd
import ogr
import time
import sched
from osgeo import gdal,osr
from sentinelsat import SentinelAPI,read_geojson,geojson_to_wkt
import datetime
import func_waterretrieval as warelib
import openpyxl
import geomProcess as geopro
import upload_geotiff as geoserver
## 中值滤波
if __name__=="__main__":
    tifpath=r'I:\Sentinel2_DATA\20210730\0927'
    savepath=r'I:\Sentinel2_DATA\20210730\0927\中值滤波'
    os.chdir(tifpath)#将工作目录切换到该地址
    files = glob.glob("*.tif") 
    for f in files:
        savefile=os.path.join(savepath,f)
        geotiff = imgpro.geotiffread(f)
        dataarray = geotiff.dataarray
        newdata=imgpro.smoothdata(dataarray,'median')
        imgpro.geotiffwrite(savefile,newdata,geotiff.geo_transform,geotiff.projection,datatype='FLOAT32')