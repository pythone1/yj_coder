"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: gdal2tiles.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

#!/usr/bin/env python3

import sys

# Running main() must be protected that way due to use of multiprocessing on Windows:
# https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
if __name__ == "__main__":
    from osgeo.gdal import deprecation_warn

    # import osgeo_utils.gdal2tiles as a convenience to use as a script
    from osgeo_utils.gdal2tiles import *  # noqa
    from osgeo_utils.gdal2tiles import main

    deprecation_warn("gdal2tiles")
    sys.exit(main(sys.argv, called_from_main=True))
