"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: __init__.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

from .predict import SegmentationPredictor
from .train import SegmentationTrainer
from .val import SegmentationValidator

__all__ = "SegmentationPredictor", "SegmentationTrainer", "SegmentationValidator"
