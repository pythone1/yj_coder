"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: make_fuzzer_friendly_archive.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ******************************************************************************
#
#  Project:  GDAL
#  Purpose:  Make fuzzer friendly archive (only works in DEBUG mode)
#  Author:   Even Rouault, <even dot rouault at spatialys dot com>
#
# ******************************************************************************
#  Copyright (c) 2016 Even Rouault, <even dot rouault at spatialys dot com>
#
# SPDX-License-Identifier: MIT
# ******************************************************************************

import os
import sys


def Usage():
    print(
        f"Usage: {sys.argv[0]} -- This is a sample. Read source to know how to use. --"
    )
    return 2


def main(argv=sys.argv):
    if len(sys.argv) < 2:
        return Usage()
    fout = open(argv[1], "wb")
    fout.write("FUZZER_FRIENDLY_ARCHIVE\n".encode("ascii"))
    for filename in argv[2:]:
        fout.write(("***NEWFILE***:%s\n" % os.path.basename(filename)).encode("ascii"))
        fout.write(open(filename, "rb").read())
    fout.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
