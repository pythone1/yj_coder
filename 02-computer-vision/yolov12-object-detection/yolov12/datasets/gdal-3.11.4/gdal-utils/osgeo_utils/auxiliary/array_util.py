"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: array_util.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ******************************************************************************
#
#  Project:  GDAL utils.auxiliary
#  Purpose:  array and scalar related types functions
#  Author:   Idan Miara <idan@miara.com>
#
# ******************************************************************************
#  Copyright (c) 2021, Idan Miara <idan@miara.com>
#
# SPDX-License-Identifier: MIT
# ******************************************************************************
import array
from typing import TYPE_CHECKING, Sequence, Union

ScalarLike = Union[
    int,
    float,
]

if TYPE_CHECKING:
    # avoid "TypeError: Subscripted generics cannot be used with class and instance checks" while using isinstance()
    ArrayLike = Union[
        ScalarLike,
        Sequence[ScalarLike],
        array.array,
    ]
else:
    ArrayLike = Union[
        ScalarLike,
        Sequence,
        array.array,
    ]

try:
    from numpy import ndarray

    ArrayLike = Union[ArrayLike, ndarray]
except ImportError:
    pass

ArrayOrScalarLike = Union[ArrayLike, ScalarLike]


def array_dist(
    x: ArrayOrScalarLike, y: ArrayOrScalarLike, is_max: bool = True
) -> ScalarLike:
    if isinstance(x, ScalarLike.__args__):
        return abs(x - y)
    try:
        from osgeo_utils.auxiliary.numpy_util import array_dist as np_array_dist

        return np_array_dist(x=x, y=y, is_max=is_max)
    except ImportError:
        return (
            max(abs(a - b) for a, b in zip(x, y))
            if is_max
            else max(abs(a - b) for a, b in zip(x, y))
        )
