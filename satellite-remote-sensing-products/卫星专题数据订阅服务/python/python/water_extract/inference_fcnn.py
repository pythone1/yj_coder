from __future__ import division #精确除法
import argparse
import numpy as np
import cv2, time, os, pickle, sys
import glob
from osgeo import gdal
import rasterio
from rasterio.enums import Resampling
from copy import deepcopy
import segmentation_models as sm
import arcticrivermap4
 
import xarray as xr
import tifffile as tiff
import rioxarray
import pandas as pd
import geopandas as gpd
import tensorflow as tf

def find_padding(v, divisor=64): ##填充像素，使得输出图像与原图像保持相同大小
    v_divisible = max(divisor, int(divisor * np.ceil(v / divisor)))
    total_pad = v_divisible - v
    pad_1 = total_pad // 2
    pad_2 = total_pad - pad_1
    return pad_1, pad_2


def inference(model, image, data_dim):

    # load and preprocess the input image 
    if data_dim != 1:
        [ny, nx, bands] = np.shape(image)
        if(bands==8):
            image = np.delete(image,[0,3,5,7], 2)
        elif(bands==7) :
            image = np.delete(image, 6, 2) # LandSat
   
    print("size of image:", np.shape(image), "min/max/mean", np.min(image), np.max(image), np.mean(image))

    pad_r = find_padding(image.shape[0])
    pad_c = find_padding(image.shape[1])



    image = np.pad(image, ((pad_r[0], pad_r[1]), (pad_c[0], pad_c[1]), (0,0)), 'reflect')

    #判断测试影像是否与训练影像大小相等
    if pad_r[1] == 0:
        pad_r = (pad_r[0], 1)
    if pad_c[1] == 0:
        pad_c = (pad_c[0], 1)

    image = image.astype(np.float32)
    image = image - np.min(image)
    image = image / np.maximum(np.max(image), 1)

    print("Image properties", type(image), np.shape(image), np.min(image), np.max(image))

    # run inference
    image = np.expand_dims(image, axis=0)
    print(image)
    inference = model.predict(image)

    inference = np.squeeze(inference)

    inference = inference[pad_r[0]:-pad_r[1], pad_c[0]:-pad_c[1]]

    # soft threshold
    inference = 1./(1+np.exp(-(16*(inference-0.5))))
    inference = np.clip(inference, 0, 1)
    return inference

def main(args):
    os.chdir(args.input_path)
    tiffiles = glob.glob("*.tif")
    print(tiffiles)
    for tiffile in enumerate(tiffiles):
        path = os.path.join(args.input_path, str(tiffile[1])).replace("\\", "/")
        print('path',path)

        with rasterio.open(path) as dataset:
            image = dataset.read()

            if (np.ndim(image) == 3):
                image = np.moveaxis(image, 0, -1) #np.moveaxis(a, src, dst)moveaxis方法将数组的轴进行移动。src表示所要移动的轴的索引，dst表示所要移动到的位置
                                                  #a.shape=(2, 3, 4),b = np.moveaxis(a, 0, -1)，b.shape=(3, 4, 2)。
            # image crop:
            if args.central_fraction != None:
                image = tf.image.central_crop(image, args.central_fraction)#裁剪图像的中心区域

        # Load inference model
        model = None
        try:
            if args.model_index == 1 and args.data_dim == 4:
                model = arcticrivermap4.model()
            elif args.model_index == 2:
                model = sm.Unet(backbone_name='resnet18', input_shape=(None, None, args.data_dim),
                                    encoder_weights=None, classes=1, activation='sigmoid')
            elif args.model_index == 3:
                model = sm.Unet(backbone_name='resnet34', input_shape=(None, None, args.data_dim),
                                    encoder_weights=None, classes=1, activation='sigmoid')
            elif args.model_index == 4:
                model = sm.Linknet(backbone_name='resnet18', input_shape=(None, None, args.data_dim),
                                    encoder_weights=None, classes=1, activation='sigmoid')
            elif args.model_index == 5:
                model = sm.Linknet(backbone_name='resnet34', input_shape=(None, None, args.data_dim),
                                    encoder_weights=None, classes=1, activation='sigmoid')
        except:
            print('please recheck the supporting neural networks and backbones')

        model.load_weights(args.checkpoint_path)

        mask = inference(model, image, args.data_dim)
        #预测得分拉伸映射到[0,255]
        mask = np.array(np.round((mask) * 255, 0), dtype=np.uint8)
        # 预测结果二值化
        mask[mask>0]=1

        kwargs = dataset.meta
        kwargs.update(
            dtype=rasterio.uint8,
            count=1,
            compress='lzw'
        )
        #输出预测tif
        output_tif = os.path.join(args.output_folder, tiffile[1].replace('.tif','_model'+str(args.model_index)+'_test.tif')).replace("\\","/")
        print('output_tif--------------------',output_tif)
        with rasterio.open(output_tif, 'w', **kwargs) as dst:
            dst.write_band(1, mask.astype(rasterio.uint8))

def main_argparse():
    for i in range(5, 6):
        file_name=r'H:\Tensorflow\tianditu_image2'
        print('file_name-----------------',file_name)
        input_path=r'H:\Tensorflow\image_RGB\lyg20221019GF6\RefImages切片'
        print('input_path-----------------', input_path)
        checkpoint_path = file_name+'\\model' + str(i)+'\\checkpoints\\cp.030.ckpt'
        print('checkpoint_path-----------------', checkpoint_path)
        output_folder =  r'H:\Tensorflow\image_RGB\lyg20221019GF6\tensorflow_test'
        print('output_folder-----------------', output_folder)

        parser = argparse.ArgumentParser()  # argparse,参数解析包，可以用来方便地读取命令行参数。
        parser.add_argument('--input_path', type=str, default=input_path,
                            help="测试图像的路径")
        parser.add_argument('--checkpoint_path', type=str, default=checkpoint_path,
                            help="检查点的保存路径")
        parser.add_argument('--output_folder', type=str, default=output_folder,
                            help="tif影像的测试结果路径")
        parser.add_argument('--model_index', type=int, default=i,
                            help="FCNN模型的索引，1是DWM，2是U18，3是U34，4是L18，5是L34")
        parser.add_argument('--data_dim', type=int, default=4,
                            help="训练数据的维度")
        parser.add_argument('--central_fraction', default=None, type=float,
                            help="图像中心区域裁剪的比例")

        args = parser.parse_args()

        if not os.path.exists(args.output_folder):
            os.mkdir(args.output_folder)
        main(args)

if __name__ == '__main__':
    main_argparse()
 

