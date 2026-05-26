"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: gdal_mkdir.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

#!/usr/bin/env python3
###############################################################################
#
#  Project:  GDAL samples
#  Purpose:  Create a virtual directory
#  Author:   Even Rouault <even.rouault at spatialys.com>
#
###############################################################################
#  Copyright (c) 2017, Even Rouault <even.rouault at spatialys.com>
#
# SPDX-License-Identifier: MIT
###############################################################################

import sys

from osgeo import gdal


def Usage():
    print("Usage: gdal_mkdir filename")
    return 2


def gdal_mkdir(argv, progress=None):
    # pylint: disable=unused-argument
    filename = None

    argv = gdal.GeneralCmdLineProcessor(argv)
    if argv is None:
        return -1

    for i in range(1, len(argv)):
        if filename is None:
            filename = argv[i]
        elif argv[i][0] == "-":
            print("Unexpected option : %s" % argv[i])
            return Usage()
        else:
            print("Unexpected option : %s" % argv[i])
            return Usage()

    if filename is None:
        return Usage()

    ret = gdal.Mkdir(filename, int("0755", 8))
    if ret != 0:
        print("Creation failed")
    return ret


def main(argv=sys.argv):
    return gdal_mkdir(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
