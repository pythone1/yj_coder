"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: errors.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license

from ultralytics.utils import emojis


class HUBModelError(Exception):
    """
    Custom exception class for handling errors related to model fetching in Ultralytics YOLO.

    This exception is raised when a requested model is not found or cannot be retrieved.
    The message is also processed to include emojis for better user experience.

    Attributes:
        message (str): The error message displayed when the exception is raised.

    Note:
        The message is automatically processed through the 'emojis' function from the 'ultralytics.utils' package.
    """

    def __init__(self, message="Model not found. Please check model URL and try again."):
        """Create an exception for when a model is not found."""
        super().__init__(emojis(message))
