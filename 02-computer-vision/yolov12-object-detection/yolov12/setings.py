"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: setings.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from ultralytics import settings

# View all settings
print(settings)

# Return a specific setting
value = settings["runs_dir"]

from ultralytics import settings

# Update a setting
settings.update({"runs_dir": r"E:\PY\YOLO\yolov12"})

# Update multiple settings
settings.update({"runs_dir": r"E:\PY\YOLO\yolov12", "tensorboard": False})

# Reset settings to default values
settings.reset()