"""
项目名称: water-quality-classification
技术领域: 01-geospatial-remote-sensing
模块说明: seg_api.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import paddlex as pdx
from paddlex import transforms as T
import  imgProcess as A
# 下载和解压视盘分割数据集
# optic_dataset = 'https://bj.bcebos.com/paddlex/datasets/optic_disc_seg.tar.gz'
# pdx.utils.download_and_decompress(optic_dataset, path='./')

# train_transforms = T.Compose([
#     T.Resize(target_size=512),
#     T.RandomHorizontalFlip(),
#     T.Normalize(
#         mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
# ])
#
eval_transforms = T.Compose([
    T.Resize(target_size=512),
    T.Normalize(
        mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])
#
# # train_dataset = pdx.datasets.SegDataset(
# #     data_dir='optic_disc_seg',
# #     file_list='optic_disc_seg/train_list.txt',
# #     label_list='optic_disc_seg/labels.txt',
# #     transforms=train_transforms,
# #     shuffle=True)
#
eval_dataset = pdx.datasets.SegDataset(
    data_dir=r'E:\paddleseg\dataset\test',
    file_list=r'E:\paddleseg\dataset\test\train_list.txt',
    label_list=r'E:\paddleseg\dataset\test\labels.txt',
    transforms=eval_transforms,
    shuffle=False)

#评估接口
model = pdx.load_model(r'D:\Users\Desktop\inference_model')
# geotifinfo = A.geotiffread(r'D:\Users\Desktop\visual\BA_09_51.png')
# data = geotifinfo.dataarray
# t=data[:,:,0].copy()
# data[:, : ,0]=data[:, : ,2]
# data[:, : ,2]=t
# print(data.shape)
# result = model.predict(data)
# # print(result['label_map'].shape)
# # A.geotiffwrite(r'D:\Users\Desktop\visual\1.tif',result['label_map'],geotifinfo.geo_transform,geotifinfo.projection)
# print(result['score_map'].shape[2])
# bands = result['score_map'].shape[2]
# treshould=0.5
# for i in range(bands):
#     if i!=0:
#         score = result['score_map'][:,:,i]
#         score[score>treshould]=int(i)
#         score[score<treshould]=0
#
# A.geotiffwrite(r'D:\Users\Desktop\visual\0.5.tif',score,geotifinfo.geo_transform,geotifinfo.projection)
result=model.evaluate(eval_dataset, batch_size=1, return_details=True)
print(result)
