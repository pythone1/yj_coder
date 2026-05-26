import os
import glob
import shutil
import sys
from osgeo import gdal, gdalconst
import numpy as np
import segmentation_models as sm
import rasterio
import imgprocess as imgpro

def GFidentifyWaterarea(inputfile,resultfile,modelpath,tmp_imgslice,tmp_mask):

    def getimgslice(inputfile,outpath):
        '''
        功能：影像切片，将影像切片为1024x1024像素
        '''
        geottif=imgpro.geotiffread(inputfile)
        imgpro.imgslice_by_pixels(geottif,1024, outpath)

    def find_padding(v, divisor=64):
        '''
            功能：影像边缘填充，以满足入影像和输出影像大小一致
        '''
        v_divisible = max(divisor, int(divisor * np.ceil(v / divisor)))
        total_pad = v_divisible - v
        pad_1 = total_pad // 2
        pad_2 = total_pad - pad_1
        return pad_1, pad_2

    def rasterMosaic(maskpath, outfile):
        '''
        功能：镶嵌
        输入：
        maskpath str 生成的mask掩膜文件路径
        输出：
        outfile str 返回镶嵌后的文件
        '''
        maskfiles = glob.glob(maskpath + "\\*.tif")
        ref_raster = gdal.Open(maskfiles[0], gdal.GA_ReadOnly)
        ref_proj = ref_raster.GetProjection()
        options = gdal.WarpOptions(srcSRS=ref_proj, dstSRS=ref_proj, format='GTiff', resampleAlg=gdalconst.GRA_Bilinear)
        gdal.Warp(outfile, maskfiles, options=options)

    # 加载模型
    model = sm.Unet(backbone_name='resnet18', input_shape=(None, None, 4),
                   encoder_weights=None, classes=1, activation='sigmoid')
    model.load_weights(modelpath)

    #图像切片
    imgslicepath = tmp_imgslice
    if not os.path.exists(imgslicepath):
        os.mkdir(imgslicepath)
    getimgslice(inputfile, imgslicepath)

    #读取影像
    os.chdir(imgslicepath)
    tiffiles = glob.glob("*.tif")
    for tiffile in enumerate(tiffiles):
        tifpath = os.path.join(imgslicepath, tiffile[1])
        with rasterio.open(tifpath) as dataset:
            image = dataset.read()
        image = np.moveaxis(image, 0, -1)
        pad_r = find_padding(image.shape[0])
        pad_c = find_padding(image.shape[1])
        image = np.pad(image, ((pad_r[0], pad_r[1]), (pad_c[0], pad_c[1]), (0, 0)), 'reflect')

        # 解决推理后无填充索引的问题
        if pad_r[1] == 0:
            pad_r = (pad_r[0], 1)
        if pad_c[1] == 0:
            pad_c = (pad_c[0], 1)

        image = image.astype(np.float32)
        image = np.nan_to_num(image, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
        image = image - np.min(image)
        image = image / np.maximum(np.max(image), 1)

        # 模型预测
        image = np.expand_dims(image, axis=0)
        inference = model.predict(image)
        inference = np.squeeze(inference)
        inference = inference[pad_r[0]:-pad_r[1], pad_c[0]:-pad_c[1]]

        # 计算软阈值
        inference = 1. / (1 + np.exp(-(16 * (inference - 0.5))))
        inference = np.clip(inference, 0, 1)

        #预测得分拉伸到[0 255]，并以二值化显示
        mask = np.array(np.round((inference) * 255, 0), dtype=np.uint8)
        mask[mask > 0] = 1

        #保存掩膜文件
        kwargs = dataset.meta
        kwargs.update(
            dtype=rasterio.uint8,
            count=1,
            compress='lzw')

        maskpath = tmp_mask
        if not os.path.exists(maskpath):
            os.mkdir(maskpath)
        outmask=os.path.join(maskpath,tiffile[1].replace('.tif', '_mask.tif'))
        with rasterio.open(outmask, 'w', **kwargs) as dst:
            dst.write_band(1, mask.astype(rasterio.uint8))

    ##将所有mask水域掩膜文件镶嵌成一张影像
    rasterMosaic(maskpath, resultfile)

    ##清空切片、mask掩膜临时文件夹下的内容
    os.chdir(os.path.dirname(maskpath))
    shutil.rmtree(imgslicepath)
    shutil.rmtree(maskpath)


inputfile = sys.argv[1]
resultfile = sys.argv[2]
modelpath = sys.argv[3]
tmp_imgslice=sys.argv[4]
tmp_mask = sys.argv[5]

# inputfile=r'P:\imgdata\L51RGB\gf6_pms_l51rgb_20201023_20201023_20230505T134325.tif'
# resultfile=r'P:\imgdata\L54SYFB\gf6_pms_l54syfb_20201023_20201023_20230505T164859.tif'
# modelpath=r'P:\models\waterExtractModel_GF\checkpoints\cp.080.ckpt'
# tmp_imgslice=r'P:\temp\tmp_imgslice'
# tmp_mask=r'P:\temp\tmp_mask'
GFidentifyWaterarea(inputfile,resultfile,modelpath,tmp_imgslice,tmp_mask)
