"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: __init__.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

from ultralytics.models.yolo.classify.predict import ClassificationPredictor
from ultralytics.models.yolo.classify.train import ClassificationTrainer
from ultralytics.models.yolo.classify.val import ClassificationValidator

__all__ = "ClassificationPredictor", "ClassificationTrainer", "ClassificationValidator"
