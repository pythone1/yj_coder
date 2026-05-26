import math
import sys

import numpy as np
import fiona
import paddlex as pdx
fiona.supported_drivers['KML'] = 'rw'
import imgprocess as imgpro

def preProcess(im):
    """
     传入geotifread读取的RGB顺序矩阵，对图像进行波段处理,准备BGR顺序，并转float32型
    :param im: 图像的矩阵
    :return: 处理完成后的新矩阵np.float
    """
    t = im[:, :, 2].copy()
    im[:, :, 2] = im[:, :, 0]
    im[:, :, 0] = t
    # 语义分割2.0版本需要数据类型转换float32
    im = im.astype('float32')
    return im

class geotiffinfo():
    '''
    tif信息
    '''
    def __init__(self,rows,cols,bands,geo_transform,projection,dataarray,*sensor):
        self.rows = rows
        self.cols = cols
        self.bands = bands
        self.geo_transform=geo_transform
        self.projection=projection
        self.dataarray=dataarray
        self.sensor = sensor
        if sensor == "pms" or sensor == "rededge":
            self.b_index = 0
            self.g_index = 1
            self.r_index = 2
            self.nir_index = 3

def geoClassify(abs_path, pixelnum,bufdist,modelpath,savepath):
    """
    读取图像进行分块预测，并对结果可视化，保存预测结果
    :param tiffile: 用户选择的栅格文件,str
    :param pixelnum: 用户设置的图像分块的大小int
    :param bufdist: int 重叠距离
    :param model: 加载的模型
    :param out_tif: 预测生成的栅格文件str
    :return: 带坐标的图像返回geotiinfo对象 []
    """
    # for result in results:
    model = pdx.load_model(modelpath)
    geotiff = imgpro.geotiffread(abs_path)
    im = geotiff.dataarray  # np.int
    geo_transform = geotiff.geo_transform
    projection = geotiff.projection
    rows, cols, bands = im.shape
    # 数据预处理（统一数据为三个波段，转为float32）
    dataarray = preProcess(im)  # np.float

    # 分块进行模型预测
    result = Main_Classify(dataarray,pixelnum,bufdist,model)  # np.int
    geotiinfo = geotiffinfo(rows,cols,bands,geo_transform, projection, result)
    imgpro.geotiffwrite(savepath, result, geotiinfo.geo_transform, geotiinfo.projection, datatype="UINT8")


def Main_Classify(im,pixelnum,bufdist,model):
    """
    对图像进行分块预测
    :param im: 图像的矩阵np.float
    :param pixelnum: 分块的大小int
    :param bufdist: int 重叠距离
    :param model: 用户选择的模型str
    :return: 存储预测结果只含0，1值的矩阵 np.int
    """
    rows, cols, _ = im.shape
    # 分块预测设置
    # 分块预测，生成一个零矩阵河原始图像同大小的图像
    result1 = np.zeros((rows, cols), dtype=np.int)
    #向上取整
    xnum = math.ceil(cols / pixelnum)
    ynum = math.ceil(rows / pixelnum)
    for i in range(ynum):
        # 防止输入的图像过小裁剪行数只有1行（rows<=pixelnum）
        if ynum == 1:
            ylim = [0, rows]
            kernel_y = [0, rows]
        # 裁剪行数大于1行
        else:
            if i == 0:
                ylim = [0, pixelnum + bufdist]  # 向一定方向扩展按照缓冲距延伸 再进行分类
                kernel_y = [0, pixelnum]  # 在分类结果上只取核心范围kernel_x/y
            elif i == ynum - 1:
                ylim = [i * pixelnum - bufdist, rows]
                kernel_y = [i * pixelnum, rows]
            else:
                ylim = [i * pixelnum - bufdist, (i + 1) * pixelnum + bufdist]
                kernel_y = [i * pixelnum, (i + 1) * pixelnum]
        for j in range(xnum):
            # 防止输入的图像过小裁剪行数只有1行（rows<=pixelnum）
            if xnum == 1:
                xlim = [0, cols]
                kernel_x = [0, cols]
            else:  # 裁剪行数大于1列
                if j == 0:
                    xlim = [0, pixelnum + bufdist]  # 向一定方向扩展按照缓冲距延伸 再进行分类
                    kernel_x = [0, pixelnum]  # 在分类结果上只取核心范围kernel_x/y
                elif j == xnum - 1:
                    xlim = [j * pixelnum - bufdist, cols]
                    kernel_x = [j * pixelnum, cols]
                else:
                    xlim = [j * pixelnum - bufdist, (j + 1) * pixelnum + bufdist]
                    kernel_x = [j * pixelnum, (j + 1) * pixelnum]
            subdata = im[ylim[0]:ylim[1], xlim[0]:xlim[1], :]

            if np.max(subdata) > 0:

                #调用模型进行预测，'label_map'存储预测结果灰度图
                visual_result=model.predict(subdata)
                #多类识别
                result = visual_result['label_map']

                # #单类识别
                # bands = visual_result['score_map'].shape[2]
                # treshould = 0.6
                # #设置阈值
                # for i in range(bands):
                #     if i != 0:
                #         result = visual_result['score_map'][:, :, i]
                #         result[score > treshould] = 1
                #         result[score < treshould] = 0

                #可视化
                # pdx.seg.visualize(subdata, visual_result, weight=0.5, save_dir=outpath_visual)

                result1[kernel_y[0]:kernel_y[1], kernel_x[0]:kernel_x[1]] = result[kernel_y[0] - ylim[0]:(kernel_y[0] - ylim[
                    0]) + (kernel_y[1] - kernel_y[0]), kernel_x[0] - xlim[0]:(kernel_x[0] - xlim[0]) + (
                            kernel_x[1] - kernel_x[0])]
    return result1

abs_path = sys.argv[1]
pixelnum = sys.argv[2]
bufdist = sys.argv[3]
modelpath = sys.argv[4]
savepath = sys.argv[5]

geoClassify(abs_path, pixelnum,bufdist,modelpath,savepath)