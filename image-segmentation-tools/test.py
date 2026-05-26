import os
import random
import zipfile
import yaml
import cv2
import matplotlib.pyplot as plt

# ======================
# 1. 数据集准备与划分
# ======================
dataset_root = r"E:\PY\seg\data\mine"
img_dir = os.path.join(dataset_root, "leftImg8bit")
mask_dir = os.path.join(dataset_root, "gtFine")
# 确保目录存在
os.makedirs(img_dir, exist_ok=True)
os.makedirs(mask_dir, exist_ok=True)
# 划分数据集
train_percent = 0.9
val_percent = 0.1
all_images = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png'))]
random.shuffle(all_images)
split_idx = int(len(all_images) * train_percent)
train_images = all_images[:split_idx]
val_images = all_images[split_idx:]


# 生成train.txt和val.txt
def create_file_list(images, filename):
	with open(os.path.join(dataset_root, filename), 'w') as f:
		for img in images:
			mask_name = os.path.splitext(img)[0] + '.png'
			f.write(f"leftImg8bit/{img} gtFine/{mask_name}\n")


create_file_list(train_images, "train.txt")
create_file_list(val_images, "val.txt")
print(f"数据集划分完成: 训练集{len(train_images)}张, 验证集{len(val_images)}张")
# ======================
# 2. 修改配置文件
# ======================
config_path = r"E:\PY\seg\PaddleSeg\configs\deeplabv3p\deeplabv3p_resnet50_os8_cityscapes_1024x512_80k.yml"
new_config = {
	'_base_': '../_base_/cityscapes.yml',
	'batch_size': 2,
	'iters': 200000,
	'model': {
		'type': 'DeepLabV3P',
		'backbone': {
			'type': 'ResNet50_vd',
			'output_stride': 8,
			'multi_grid': [1, 2, 4],
			'pretrained': 'https://bj.bcebos.com/paddleseg/dygraph/resnet50_vd_ssld_v2.tar.gz'
		},
		'num_classes': 3,
		'backbone_indices': [0, 3],
		'aspp_ratios': [1, 12, 24, 36],
		'aspp_out_channels': 256,
		'align_corners': False,
		'pretrained': None
	},
	'train_dataset': {
		'type': 'Dataset',
		'dataset_root': dataset_root,
		'train_path': os.path.join(dataset_root, "train.txt"),
		'num_classes': 3,
		'transforms': [
			{'type': 'ResizeStepScaling', 'min_scale_factor': 0.5, 'max_scale_factor': 2.0, 'scale_step_size': 0.25},
			{'type': 'RandomPaddingCrop', 'crop_size': [1024, 512]},
			{'type': 'RandomHorizontalFlip'},
			{'type': 'RandomDistort', 'brightness_range': 0.4, 'contrast_range': 0.4, 'saturation_range': 0.4},
			{'type': 'Normalize'}
		]
	},
	'val_dataset': {
		'type': 'Dataset',
		'dataset_root': dataset_root,
		'val_path': os.path.join(dataset_root, "val.txt"),
		'num_classes': 3,
		'mode': 'val',
		'transforms': [{'type': 'Normalize'}]
	},
	'optimizer': {'type': 'sgd', 'momentum': 0.9, 'weight_decay': 4.0e-05},
	'lr_scheduler': {
		'type': 'PolynomialDecay',
		'learning_rate': 0.01,
		'end_lr': 0,
		'power': 0.9
	},
	'loss': {
		'types': [{'type': 'CrossEntropyLoss', 'ignore_index': 255}],
		'coef': [1]
	}
}
# 保存新配置
new_config_path = os.path.join(dataset_root, "deeplabv3p_mine.yml")
with open(new_config_path, 'w') as f:
	yaml.dump(new_config, f)
print(f"配置文件已保存至: {new_config_path}")
print(new_config_path)
# ======================
# 3. 模型训练
# ======================
print("\n开始训练模型...")
train_cmd = f"""
python r'D:/APP/anaconda/envs/seg/Lib/site-packages/paddleseg/core/train.py' \
--config {new_config_path} \
--save_interval 5000 \
--save_dir {dataset_root}/output \
--num_workers 4 \
--log_iters 100
"""
print(train_cmd)
os.system(train_cmd)
print("训练完成！模型保存在:", os.path.join(dataset_root, "output"))
# ======================
# 4. 模型评估
# ======================
print("\n评估模型性能...")
eval_cmd = f"""
python D:/APP/anaconda/envs/seg/Lib/site-packages/paddleseg/core/val.py \
--config {new_config_path} \
--model_path {dataset_root}/output/iter_20000/model.pdparams
"""
os.system(eval_cmd)


# ======================
# 5. 单图预测与可视化
# ======================
def predict_and_visualize(image_path):
	# 执行预测
	predict_cmd = f"""
    python D:/APP/anaconda/envs/seg/Lib/site-packages/paddleseg/core/predict.py \
    --config {new_config_path} \
    --model_path {dataset_root}/output/iter_20000/model.pdparams \
    --image_path {image_path} \
    --save_dir {dataset_root}/predict_result
    """
	os.system(predict_cmd)
	# 可视化结果
	added_path = os.path.join(dataset_root, "predict_result/added_prediction", os.path.basename(image_path))
	pseudo_path = os.path.join(dataset_root, "predict_result/pseudo_color_prediction",
	                           os.path.splitext(os.path.basename(image_path))[0] + ".png")
	if os.path.exists(added_path) and os.path.exists(pseudo_path):
		added_img = cv2.cvtColor(cv2.imread(added_path), cv2.COLOR_BGR2RGB)
		pseudo_img = cv2.cvtColor(cv2.imread(pseudo_path), cv2.COLOR_BGR2RGB)
		plt.figure(figsize=(12, 6))
		plt.subplot(121)
		plt.imshow(added_img)
		plt.title("Prediction Overlay")
		plt.axis('off')
		plt.subplot(122)
		plt.imshow(pseudo_img)
		plt.title("Pseudo Color")
		plt.axis('off')
		plt.show()
	else:
		print("预测结果未找到，请检查路径")


# 示例预测（替换为您的图片路径）
test_image = r"E:\PY\seg\data\mine\leftImg8bit\001_2022_08_20_19_41_fish_eye_camera_Num_230.jpg"  # 修改为您的测试图片
if os.path.exists(test_image):
	predict_and_visualize(test_image)
else:
	print("测试图片不存在:", test_image)