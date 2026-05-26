"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: __init__.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

from .bot_sort import BOTSORT
from .byte_tracker import BYTETracker
from .track import register_tracker

__all__ = "register_tracker", "BOTSORT", "BYTETracker"  # allow simpler import
