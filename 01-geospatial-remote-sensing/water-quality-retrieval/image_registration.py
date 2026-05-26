"""
项目名称: water-quality-retrieval
技术领域: 01-geospatial-remote-sensing
模块说明: image_registration.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os,glob

from arosics import COREG

if __name__ == '__main__':
    # 方式一：一对一匹配
    # 参考图像
    reffile = r'J:\研究数据\20221105几何配准测试\SPD.tif'
    # 待配准图像
    targetfile = r'J:\研究数据\20221105几何配准测试\gf.tif'
    # 配准输出图像
    outfile = r'J:\研究数据\20221105几何配准测试\gf_georefed2.tif'

    CR = COREG(reffile,targetfile,path_out=outfile,ws=(512,512),max_shift=2000)
    CR.calculate_spatial_shifts()
    CR.correct_shifts()


    # # 方式二：一对多匹配
    # # 参考图像
    # reffile = r'J:\研究数据\20221105几何配准测试\SPD.tif'
    # # 待配准图像存放路径
    # inpath = r''
    # # 输出图像存放路径
    # outpath = r''

    # os.chdir(inpath)
    # tiffiles = glob.glob("*.tif")
    # for tiffile in tiffiles:
    #     outfile = os.path.join(outpath,tiffile)
    #     CR = COREG(reffile,tiffile,path_out=outfile,ws=(512,512),max_shift=2000)
    #     CR.calculate_spatial_shifts()
    #     CR.correct_shifts()


    


