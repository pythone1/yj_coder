"""
项目名称: unet-water-segmentation
技术领域: 02-computer-vision
模块说明: utils.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import matplotlib.pyplot as plt


def plot_img_and_mask(img, mask):
    classes = mask.max() + 1
    fig, ax = plt.subplots(1, classes + 1)
    ax[0].set_title('Input image')
    ax[0].imshow(img)
    for i in range(classes):
        ax[i + 1].set_title(f'Mask (class {i + 1})')
        ax[i + 1].imshow(mask == i)
    plt.xticks([]), plt.yticks([])
    plt.show()
