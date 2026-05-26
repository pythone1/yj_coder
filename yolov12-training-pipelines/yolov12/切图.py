import os
import shutil
from PIL import Image
import numpy as np
import yaml

# --- 配置区 (请根据你的情况修改) ---
# 你的数据集根目录
DATA_ROOT = r"F:\data\sample\data"
# 你的原始文件夹名
ORIGINAL_IMAGE_DIR = "JPEGImages"
ORIGINAL_LABEL_DIR = "Annotations"
# YOLO期望的标准文件夹名
YOLO_IMAGE_DIR = "images"
YOLO_LABEL_DIR = "labels"
# 你的类别名称 (请务必修改成你自己的)
CLASS_NAMES = ['pond', 'farmland', 'buildings']  # <--- 修改这里


# --- 配置区结束 ---
def main():
	"""主函数：调整目录结构并预处理标签"""
	# --- 步骤 1: 重命名文件夹以匹配YOLO标准格式 ---
	print("--- 步骤 1: 重命名文件夹以匹配YOLO格式 ---")
	original_image_path = os.path.join(DATA_ROOT, ORIGINAL_IMAGE_DIR)
	yolo_image_path = os.path.join(DATA_ROOT, YOLO_IMAGE_DIR)
	original_label_path = os.path.join(DATA_ROOT, ORIGINAL_LABEL_DIR)
	yolo_label_path = os.path.join(DATA_ROOT, YOLO_LABEL_DIR)
	# 检查YOLO标准目录是否已存在，避免误操作
	if os.path.exists(yolo_image_path) or os.path.exists(yolo_label_path):
		print(f"错误：YOLO期望的文件夹 '{YOLO_IMAGE_DIR}' 或 '{YOLO_LABEL_DIR}' 已存在于 '{DATA_ROOT}' 中。")
		print("请先将它们手动删除或重命名，然后再运行此脚本。")
		return
	# 检查原始目录是否存在
	if not os.path.exists(original_image_path) or not os.path.exists(original_label_path):
		print(f"错误：找不到原始文件夹 '{ORIGINAL_IMAGE_DIR}' 或 '{ORIGINAL_LABEL_DIR}'。")
		print("请检查路径和文件夹名称是否正确。")
		return
	# 执行重命名
	print(f"准备将 '{ORIGINAL_IMAGE_DIR}' 重命名为 '{YOLO_IMAGE_DIR}'...")
	os.rename(original_image_path, yolo_image_path)
	print("完成。")
	print(f"准备将 '{ORIGINAL_LABEL_DIR}' 重命名为 '{YOLO_LABEL_DIR}'...")
	os.rename(original_label_path, yolo_label_path)
	print("完成。")
	print("--- 文件夹重命名完成 ---\n")
	# --- 步骤 2: 原地预处理标签 (将255替换为0) ---
	print("--- 步骤 2: 预处理标签文件 (将255替换为0) ---")
	print("警告：此操作将直接修改标签文件夹中的原始文件！建议先备份！")
	input("如果您已确认，请按 Enter 键继续，或按 Ctrl+C 取消...")
	label_files = [f for f in os.listdir(yolo_label_path) if os.path.isfile(os.path.join(yolo_label_path, f))]
	for label_filename in label_files:
		label_path = os.path.join(yolo_label_path, label_filename)
		try:
			with Image.open(label_path) as label_img:
				label_array = np.array(label_img)
				# 核心操作：将值为255的像素替换为0 (作为背景或忽略区域)
				label_array[label_array == 255] = 0
				# 保存，覆盖原文件
				new_img = Image.fromarray(label_array)
				new_img.save(label_path)
		except Exception as e:
			print(f"处理文件 {label_filename} 时出错: {e}")
	print("--- 标签预处理完成 ---\n")
	# --- 步骤 3: 创建 data.yaml ---
	print("--- 步骤 3: 创建 data.yaml ---")
	yaml_data = {
		'path': os.path.abspath(DATA_ROOT),
		'train': YOLO_IMAGE_DIR,
		'val': YOLO_IMAGE_DIR,  # 让YOLO从训练集中自动划分验证集
		'nc': len(CLASS_NAMES),
		'names': CLASS_NAMES
	}
	yaml_path = os.path.join(DATA_ROOT, 'data.yaml')
	with open(yaml_path, 'w', encoding='utf-8') as f:
		yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)
	print(f"data.yaml 文件已创建在: {yaml_path}")
	print("--- 全部准备就绪！---")


if __name__ == "__main__":
	# 确保已安装所需库
	# pip install numpy Pillow PyYAML
	main()