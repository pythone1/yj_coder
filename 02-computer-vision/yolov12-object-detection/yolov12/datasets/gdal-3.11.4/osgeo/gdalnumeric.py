"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: gdalnumeric.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from numpy import *
from osgeo.gdal_array import *

from warnings import warn

warn('instead of `import gdalnumeric`, please consider `import numpy` and/or `from osgeo import gdal_array`',
     DeprecationWarning)
