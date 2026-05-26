# 导库
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import sys
import os
import random
from PIL import Image
from tqdm.notebook import tqdm
from paddleseg.datasets import Dataset
import paddleseg.transforms as T
from paddleseg.core import train
# 构建模型
import paddle
from paddleseg.models import DeepLabV3
from paddleseg.models.backbones import ResNet18_vd, ResNet34_vd, ResNet50_vd, ResNet101_vd, ResNet152_vd
from paddleseg.models.losses import CrossEntropyLoss
os.chdir(r'E:\PY\Unet\paddle')
# 类别标签的颜色配置
color_map = {
    0: [0, 0, 0],        # '未知': 类别 0
    1: [215, 200, 185],  # '裸地': 类别 1
    2: [131, 194, 56],   # '草地': 类别 2
    3: [241, 165, 180],  # '构筑': 类别 3
    4: [210, 216, 201],  # '道路': 类别 4
    5: [49, 173, 105],   # '林地': 类别 5
    6: [163, 214, 245],  # '水域': 类别 6
    7: [248, 208, 114],  # '耕地': 类别 7
    8: [229, 103, 102]   # '房屋': 类别 8
}


def label2color(lable):
    '''
    将单通道灰度label, 根据颜色配置转为三通道彩色
    '''
    # 将图像转换为 numpy 数组
    label_array = np.array(lable)
    # 创建彩色图像
    color_label_array = np.zeros((label_array.shape[0], label_array.shape[1], 3), dtype=np.uint8)

    # 将单通道标签映射为彩色图像
    for label_value, color in color_map.items():
        color_label_array[label_array == label_value] = color
    return color_label_array
        
        
# # 读取图像
# image_path = 'AJDataset/images/AJ1_100.jpg'
# label_path = 'AJDataset/labels/AJ1_100.png'
#
# image = Image.open(image_path)
# lable = Image.open(label_path)
# print(f"image path: {image_path}, image size: {image.size}")
# print(f"label path: {label_path}, label size: {lable.size}")
#
# # 可视化
# fig, axes = plt.subplots(1, 2, figsize=(1 * 5, 1 * 5))
# fig.subplots_adjust(top=1, bottom=0, left=0, right=1, hspace=0.01, wspace=0.01)
# axes[0].imshow(image)
# axes[0].axis("off")
# axes[0].set_title("image")
# axes[1].imshow(label2color(lable))
# axes[1].axis("off")
# axes[1].set_title("to color label")
# plt.show()

        
# 定义全局变量

# 数据集存放目录
DATA_ROOT = r'AJDataset'
# 训练集file_list文件路径
TRAIN_PATH=r'AJDataset/train.txt'
# 验证集file_list文件路径
VAL_PATH=r'AJDataset/val.txt'
# 测试集file_list文件路径
TEST_PATH=r'AJDataset/test.txt'
# 模型训练和visualdl日志文件的保存根路径
EXP_DIR = r'AJDataset/output'
# 测试集预测结果保存根路径
TEST_SAVE_DIR = r'AJDataset/results'
# 训练迭代次数（1 iter = 1 batch , 即进行一次前向传播和反向梯度下降）
# total iters = (total sample / batch size) * EPOCHS。若想使用EPOCHS，则需要知道total sample数量
ITERS = 20000 # 这里只训练了不到2 epoch。样本数量6000左右，训练集5315，5315 // 4 = 1328（iter）。即1epoch可迭代1328次。
# EPOCHS = 100 # 暂时没使用到
# 单卡batch 2
BACH_SIZE = 4
# 类别数(背景也算，即classes + background)
NUM_CLASSES = 9
# 图像大小
SIZE = (512, 512)
# 模型保存的间隔iter步数
SAVE_ITERS = 10
# 打印日志的间隔iter步数
LOG_ITERS = 1
# 用于异步读取数据的进程数量，大于等于1时开启子进程读取数据
NUM_WORKERS = 0

CUDA_VISIBLE_DEVICES=0

# The transforms must be a list!
train_transforms = [
    T.Resize(target_size=SIZE),
    T.RandomHorizontalFlip(),
    T.Normalize()
]

val_transforms = [
    T.Resize(target_size=SIZE),
    T.Normalize()
]

train_dataset = Dataset(
    mode='train',
    dataset_root=DATA_ROOT,
    transforms=train_transforms,
    num_classes=NUM_CLASSES,
    train_path=TRAIN_PATH,
)

val_dataset = Dataset(
    mode='val',
    dataset_root=DATA_ROOT,
    transforms=val_transforms,
    num_classes=NUM_CLASSES,
    val_path=VAL_PATH,
)

# pretrained参数，使用paddle预训练的deeplabv3_resnet50模型
model = DeepLabV3(
    num_classes=NUM_CLASSES,
    backbone=ResNet50_vd(), # currently support Resnet50_vd/Resnet101_vd/Xception65.
    pretrained="https://bj.bcebos.com/paddleseg/dygraph/cityscapes/deeplabv3_resnet50_os8_cityscapes_1024x512_80k/model.pdparams"
)

# 设置学习率、优化器
base_lr = 0.01
lr = paddle.optimizer.lr.PolynomialDecay(base_lr, power=0.9, decay_steps=3000, end_lr=0)
optimizer = paddle.optimizer.SGD(lr, parameters=model.parameters(), weight_decay=4.0e-5)

# 设置损失函数
losses = {}
losses['types'] = [CrossEntropyLoss()] * 1
losses['coef'] = [1]* 1

train(
    model=model,
    train_dataset=train_dataset,
    val_dataset=val_dataset,
    optimizer=optimizer,
    losses=losses,
    save_dir=EXP_DIR, # 模型和visualdl日志文件的保存根路径
    iters=ITERS, # 训练迭代次数
    batch_size=BACH_SIZE, # 单卡batch size
    save_interval=SAVE_ITERS, # 模型保存的间隔步数
    log_iters=LOG_ITERS, # 打印日志的间隔步数
    num_workers=NUM_WORKERS, # 用于异步读取数据的进程数量， 大于等于1时开启子进程读取数据
    use_vdl=True, # 是否开启visualdl记录训练数据
)