#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from arosics import COREG
from arosics import DESHIFTER
from osgeo import  gdal
from osgeo import osr
from geoarray import GeoArray
import os
import numpy as np
from shapely import speedups
speedups.disable()

def read_tif_multiband(raster_data_path):
    raster_dataset=gdal.Open(raster_data_path,gdal.GA_ReadOnly)
    geo_transform=raster_dataset.GetGeoTransform()
    proj = raster_dataset.GetProjection()
    bands_data=[]
    for b in range(1,raster_dataset.RasterCount+1):
        band=raster_dataset.GetRasterBand(b)
        bands_data.append(band.ReadAsArray())
    
    bands_data=np.dstack(bands_data)
    rows,cols,n_bands=bands_data.shape
    del raster_dataset,band
    return rows,cols,n_bands,geo_transform,proj,bands_data


if __name__=="__main__":
    root=r'D:\ProcessingData\TEMP\test'
    os.chdir(root)
    im_reference='./GF2_7420.tif'
    im_target='./GF2_7617.tif'

    # rows,cols,n_bands,geo_transform1,proj1,bands_data1=read_tif_multiband(im_reference)
    # rows,cols,n_bands,geo_transform2,proj2,bands_data2=read_tif_multiband(im_target)
    # print(geo_transform1,proj1)
    # geoArr_reference=GeoArray(bands_data1,geo_transform1,proj1)
    # geoArr_target=GeoArray(bands_data2,geo_transform2,proj2)
    # print(geoArr_reference.geotransform,geoArr_reference.projection)
    # CR = COREG(geoArr_reference,geoArr_target,path_out='./GF_0619_register.tif',ws=(256,256))
    CR = COREG(im_reference,im_target,path_out='./GF2_7617_corr.tif',ws=(256,256),max_shift=20)
    CR.calculate_spatial_shifts()
    CR.correct_shifts()