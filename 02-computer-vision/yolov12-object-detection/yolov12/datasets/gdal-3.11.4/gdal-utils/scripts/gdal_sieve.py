"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: gdal_sieve.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

#!/usr/bin/env python3

import sys

from osgeo.gdal import deprecation_warn

# import osgeo_utils.gdal_sieve as a convenience to use as a script
from osgeo_utils.gdal_sieve import *  # noqa
from osgeo_utils.gdal_sieve import main

deprecation_warn("gdal_sieve")
sys.exit(main(sys.argv))
