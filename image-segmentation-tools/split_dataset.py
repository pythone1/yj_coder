import os
import random
import numpy as np


def split_dataset(data_dir, val_split=0.2, seed=42):
	"""
    切分数据集为训练集和验证集
    Args:
        data_dir (str): 数据集根目录, 例如 'F:/data/sample'
        val_split (float): 验证集比例
        seed (int): 随机种子
    """
	random.seed(seed)
	np.random.seed(seed)
	# 确保路径存在
	img_dir = os.path.join(data_dir, 'JPEGImages')
	mask_dir = os.path.join(data_dir, 'Annotations')
	if not os.path.exists(img_dir) or not os.path.exists(mask_dir):
		print(f"错误：图片目录 {img_dir} 或掩码目录 {mask_dir} 不存在。")
		return
	# 获取所有图片文件名（不含扩展名）
	img_filenames = [f.split('.')[0] for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
	print(img_filenames)
	# 随机打乱文件名列表
	random.shuffle(img_filenames)
	# 计算切分点
	split_idx = int(len(img_filenames) * (1 - val_split))
	train_filenames = img_filenames[:split_idx]
	val_filenames = img_filenames[split_idx:]
	# 写入训练集列表文件
	with open(os.path.join(data_dir, 'train_list.txt'), 'w') as f:
		for name in train_filenames:
			# 假设掩码图为png格式，如果不是，请修改后缀
			img_path = os.path.join(img_dir, name + '.png')  # 也可以检查 .jpeg, .png
			mask_path = os.path.join(mask_dir, name + '.png')
			if os.path.exists(img_path) and os.path.exists(mask_path):
				f.write(f"{img_path}\t{mask_path}\n")
	# 写入验证集列表文件
	with open(os.path.join(data_dir, 'val_list.txt'), 'w') as f:
		for name in val_filenames:
			img_path = os.path.join(img_dir, name + '.png')
			mask_path = os.path.join(mask_dir, name + '.png')
			if os.path.exists(img_path) and os.path.exists(mask_path):
				f.write(f"{img_path}\t{mask_path}\n")
	print(f"数据集切分完成！")
	print(f"训练集样本数: {len(train_filenames)}，列表已保存至 {os.path.join(data_dir, 'train_list.txt')}")
	print(f"验证集样本数: {len(val_filenames)}，列表已保存至 {os.path.join(data_dir, 'val_list.txt')}")


if __name__ == '__main__':
	# 请确保此路径是您的数据集根目录
	data_root = 'F:/data/sample'
	split_dataset(data_root)