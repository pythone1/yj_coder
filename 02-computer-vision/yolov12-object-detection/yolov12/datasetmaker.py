"""
项目名称: yolov12-object-detection
技术领域: 02-computer-vision
模块说明: datasetmaker.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os
import random
import shutil
from pathlib import Path

# 原始数据路径
IMG_DIR = "data/images"
LBL_DIR = "data/labels"

# 输出路径
OUT_DIR = "dataset"
splits = ['train', 'val', 'test']

# 划分比例 7:2:1
ratios = [0.7, 0.2, 0.1]

def make_dirs():
    for split in splits:
        for sub in ["images", "labels"]:
            Path(f"{OUT_DIR}/{split}/{sub}").mkdir(parents=True, exist_ok=True)

def split_dataset():
    imgs = [f for f in os.listdir(IMG_DIR) if f.endswith((".jpg", ".png", ".jpeg"))]
    random.shuffle(imgs)

    n_total = len(imgs)
    n_train = int(n_total * ratios[0])
    n_val = int(n_total * ratios[1])

    train_files = imgs[:n_train]
    val_files = imgs[n_train:n_train+n_val]
    test_files = imgs[n_train+n_val:]

    split_map = {"train": train_files, "val": val_files, "test": test_files}

    for split, files in split_map.items():
        for f in files:
            img_src = os.path.join(IMG_DIR, f)
            lbl_src = os.path.join(LBL_DIR, f.rsplit(".", 1)[0] + ".txt")

            img_dst = f"{OUT_DIR}/{split}/images/{f}"
            lbl_dst = f"{OUT_DIR}/{split}/labels/{f.rsplit('.',1)[0]}.txt"

            shutil.copy(img_src, img_dst)
            if os.path.exists(lbl_src):
                shutil.copy(lbl_src, lbl_dst)

    print(f"数据集划分完成，总数: {n_total}, 训练: {len(train_files)}, 验证: {len(val_files)}, 测试: {len(test_files)}")

def make_yaml():
    yaml_text = f"""
path: {OUT_DIR}
train: train/images
val: val/images
test: test/images

names:
  0: class0
  1: class1
  # TODO: 根据实际类别修改
"""
    with open("dataset.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_text)

if __name__ == "__main__":
    make_dirs()
    split_dataset()
    make_yaml()
