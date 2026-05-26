import sys
import os
import time
import math
import onnxruntime as rt
import numpy as np
import glob
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QLabel,QTableWidget,QTableWidgetItem,QButtonGroup
import fiona
fiona.supported_drivers['KML'] = 'rw'

from osgeo import gdal, gdalconst
import imgProcess as imgpro
import shuiyu
from infer_onnx import *

class MainDialog(QDialog):
    def __init__(self,parent=None):
        super(QDialog,self).__init__(parent)
        # 用户界面
        self.ui = shuiyu.Ui_Dialog()
        # 用户界面初始化
        self.ui.setupUi(self)

        #变量声明
        # 用于存储文件名字和存储路径{}
        self.ui.file_dic = {}
        # 添加groupbox,用于控制两个模式选择的radiobutton
        self.ui.getimgtype_group = QButtonGroup()
        self.ui.getimgtype_group.addButton(self.ui.geomode_radiobutton)
        self.ui.getimgtype_group.addButton(self.ui.normmode_radiobutton)
        # #存储geowrite需要的栅格信息,list
        self.ui.geoinfo_list = []
        #存储模型的路径，用户写入的路径,str
        self.ui.modelfile = ''
        #存储用户输入的图像大小，int
        self.ui.pixelnum= int(2048)
        #存储预测结果栅格的路径,str
        self.ui.outpath_tif = ''
        #存储用户导出合并栅格的路径,str
        self.ui.filename_mergeTif = ''

    def getImgType(self):
        """选择模式，对应识别完整坐标的图像，
        更新变量self.ui.img_tpye,str
        1对应识别完整坐标影像模式
        2对应识别中心影像坐标模式"""
        #group控制radiobutton
        for button in self.ui.getimgtype_group.buttons():
            if button.isChecked():
                text_button = button.text()
                if text_button=='完整坐标影像识别':
                    self.ui.img_tpye = 1
                elif text_button=='无坐标影像识别':
                    self.ui.img_tpye = 2

    def openImgPath(self):
        """打开文件,用户选择文件夹路径，打开所有的tif\jpg\png格式的图像
        存储用户打开的文件路径，
        添加标签到文件显示清单"""
        tiffile_path = QFileDialog.getExistingDirectory(self, '选择文件夹', r'D:\Desktop\test\waterClassify_ganyuyanchen_2048\outputs\1')
        # 取出三种后缀的图像
        imgExtensions = [".tif", ".jpg", ".png"]
        tiffile_list = []
        for imgFile in imgExtensions:
            tiffile_list = tiffile_list + glob.glob(tiffile_path + '\\' + '*' + imgFile)
        # 设置行数
        QTableWidget.setRowCount(self.ui.openImgFile_dftablewidget, 1)
        # 设置列数
        QTableWidget.setColumnCount(self.ui.openImgFile_dftablewidget, len(tiffile_list))
        hearder1 = self.ui.openImgFile_dftablewidget.verticalHeader()
        hearder1.hide()
        hearder2 = self.ui.openImgFile_dftablewidget.horizontalHeader()
        hearder2.hide()
        for j, tiffile in enumerate(tiffile_list):
            filename = os.path.basename(tiffile).split(".")[0]
            self.ui.file_dic[filename] = tiffile
            TextItem = QTableWidgetItem(str(filename))
            self.ui.openImgFile_dftablewidget.setItem(0, j, TextItem)

    def ProcessEvents(self):
        """页面实时刷新解决进度不显示问题"""
        # 实时刷新界面
        QApplication.processEvents()
        # 睡眠一秒
        time.sleep(1)

    def selectModelFile(self):
        """"用于存储用户选择模型文件路径"""
        model_path = QFileDialog.getOpenFileName(self, '选择ONNX模型', r'D:\Desktop\test\waterClassify_ganyuyanchen_2048')
        self.ui.modelfile = model_path

    def setImgSize_slcet(self):
        """"用于用户设置图像切割的大小"""
        self.ui.pixelnum = int(self.ui.setimgsize_ledit.text())

    def water_classify_pro(self):
        """水域分割主函数"
        依次进行数据读取，数据预处理，水域分割，用户展示"""
        # 设置行数
        QTableWidget.setRowCount(self.ui.process_dftablewidget, 1)
        # # 设置列数
        QTableWidget.setColumnCount(self.ui.process_dftablewidget, len(self.ui.file_dic))
        hearder1 = self.ui.process_dftablewidget.verticalHeader()
        hearder1.hide()
        hearder2 = self.ui.process_dftablewidget.horizontalHeader()
        hearder2.hide()
        modelfile,_ = self.ui.modelfile
        pixelnum = self.ui.pixelnum

        print(modelfile)
        sess = load_model(modelfile)
        print("模型加载完成")
        for i,key in enumerate(self.ui.file_dic.keys()):
            tiffile = self.ui.file_dic[key]
            dirpath = os.path.dirname(tiffile)
            outpath_visual = os.path.join(dirpath, "visual")
            if not os.path.exists(outpath_visual):
                os.mkdir(outpath_visual)
            basename = os.path.basename(tiffile)[0:-4]
            outpath_tif = os.path.join(dirpath, "predict_tif")
            if not os.path.exists(outpath_tif):
                os.mkdir(outpath_tif)
            self.ui.outpath_tif=outpath_tif
            outpath_shp = os.path.join(dirpath, "predict_shp")
            if not os.path.exists(outpath_shp):
                os.mkdir(outpath_shp)
            out_tif = os.path.join(outpath_tif, basename + ".tif")
            out_shp = os.path.join(outpath_shp, basename + ".shp")

            if self.ui.img_tpye == 1:
                print('开始预测')
                geotifinfo = geoClassify(tiffile,pixelnum, sess,out_tif,out_shp,outpath_visual,img_tpye=1)
                self.ui.geoinfo_list.append(geotifinfo)
            else:
                geoClassify(tiffile, pixelnum, sess, out_tif,out_shp,outpath_visual,img_tpye=2)
            TextItem = QTableWidgetItem(str(key + '已完成'))
            self.ui.process_dftablewidget.setItem(0, i, TextItem)
            self.ProcessEvents()

    def export_vector(self):
        """用于用户导出矢量"""
        if self.ui.img_tpye==2:
            msg_box = QMessageBox(QMessageBox.Information, '提示', '请选择“完整坐标影像识别“模式，再尝试该功能')
            msg_box.exec_()
        else:
            """保存矢量文件"""
             #写入可存储文件的格式
            filename, type = QFileDialog.getSaveFileName(self, 'save file', '/', 'TIF files (*.tif);;SHP files (*.shp);;All Files (*)')
            dri = os.path.basename(filename).split(".")[1]

            if dri=='shp':
                if self.ui.filename_mergeTif == 1:
                    msg_box = QMessageBox(QMessageBox.Information, '提示', '请先导出tif文件')
                    msg_box.exec_()
                else:
                    imgpro.createShpfile_from_geotiff(filename, self.ui.filename_mergeTif)
            elif dri=='tif':
                tifpath=self.ui.outpath_tif
                rasterMosaic(tifpath, filename)
                self.ui.filename_mergeTif = filename
            else:
                pass


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

def geoClassify(tiffile, pixelnum,sess,out_tif,out_shp,outpath_visual,img_tpye):
    """
    读取图像进行分块预测，并对结果可视化，保存预测结果
    :param tiffile: 用户选择的栅格文件,str
    :param pixelnum: 用户设置的图像分块的大小int
    :param model: 加载的模型
    :param out_tif: 预测生成的栅格文件str
    :param outpath_visual: 可视化生成的预测记过路径str
    :param img_tpye: 用于图像的种类的判定，带坐标的对应1，无坐标的对应2,int
    :return: 带坐标的图像返回geotiinfo对象 []
    """
    geotiff = imgpro.geotiffread(tiffile)
    im = geotiff.dataarray  # np.int
    print(im.dtype)
    # im =im.astype('int8')
    geo_transform = geotiff.geo_transform
    projection = geotiff.projection
    rows, cols, bands = im.shape
    # 数据预处理（统一数据为三个波段，转为float32）
    dataarray = preProcess(im)  # np.float
    print(3)
    # 分块进行模型预测
    print(4)
    result = Main_Classify(dataarray,pixelnum,sess)  # np.int
    print(6)
    geotiinfo = geotiffinfo(rows,cols,bands,geo_transform, projection, result)
    imgpro.geotiffwrite(out_tif, result, geotiinfo.geo_transform, geotiinfo.projection, datatype="UINT8")
    if img_tpye == 1:

        # imgpro.createShpfile_from_geotiff(out_shp, out_tif)
    #     print(7)
        return geotiinfo

def Main_Classify(im,pixelnum,sess):
    """
    对图像进行分块预测
    :param im: 图像的矩阵np.float
    :param pixelnum: 分块的大小int
    :param model: 用户选择的模型str
    :param outpath_visual: 可视化路径str
    :return: 存储预测结果只含0，1值的矩阵 np.int
    """
    rows, cols, _ = im.shape
    # 分块预测设置
    bufdist = 256
    # 分块预测，生成一个零矩阵河原始图像同大小的图像
    result1 = np.zeros((rows, cols))
    #向上取整
    xnum = math.ceil(cols / pixelnum)
    ynum = math.ceil(rows / pixelnum)
    print(5)
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
                print(1)
                #调用模型进行预测，'label_map'存储预测结果灰度图
                result = onnx_predict(sess,subdata)

                result1[kernel_y[0]:kernel_y[1], kernel_x[0]:kernel_x[1]] = result[kernel_y[0] - ylim[0]:(kernel_y[0] - ylim[
                    0]) + (kernel_y[1] - kernel_y[0]), kernel_x[0] - xlim[0]:(kernel_x[0] - xlim[0]) + (
                            kernel_x[1] - kernel_x[0])]

    return result1


# 栅格镶嵌
def rasterMosaic(tifpath, outfile):
    """
    对预测结果的tif图像进行合并
    :param tifpath: 分块栅格的路径str
    :param outfile: 输出的合并的栅格str
    """

    tiffiles = glob.glob(tifpath + "\\*.tif")
    ref_raster = gdal.Open(tiffiles[0], gdal.GA_ReadOnly)
    ref_proj = ref_raster.GetProjection()
    options = gdal.WarpOptions(srcSRS=ref_proj, dstSRS=ref_proj, format='GTiff', resampleAlg=gdalconst.GRA_Bilinear)
    gdal.Warp(outfile, tiffiles, options=options)

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

if __name__ == '__main__':

    #创建一个应用程序对象
    myapp = QApplication(sys.argv)
    myDlg = MainDialog()
    #处于显示的状态
    myDlg.show()
    #让整个app开始运行，进入无限循环
    sys.exit(myapp.exec_())

