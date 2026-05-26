"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: predict.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os
from ultralytics import YOLO
import numpy as np
# 选择训练好的模型
MODEL_PATH = r"E:\PY\YOLO\yolov12\runs\chinken2\weights\best.pt"   # 修改为你的best.pt路径
IMAGE_DIR = r"E:\PY\YOLO\yolov12\datasets\chicken.v4i.yolov12\train\images"               # 需要预测的图片文件夹
OUTPUT_DIR = r"E:\PY\YOLO\yolov12\datasets\chicken.v4i.yolov12\test"                # 输出文件夹

def run_predict():
    model = YOLO(MODEL_PATH)
    # 预测文件夹下所有图片
    results = model.predict(
        source=IMAGE_DIR,     # 文件夹路径
        save=True,            # 保存预测结果图像
        save_txt=True,        # 保存预测框 txt
        project=OUTPUT_DIR,   # 输出目录
        name="exp"            # 实验名
    )

    print(f"预测完成，结果保存在 {OUTPUT_DIR}/exp")

if __name__ == "__main__":
    run_predict()
