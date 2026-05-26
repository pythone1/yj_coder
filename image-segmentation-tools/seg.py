import os
import paddle
import paddle.nn as nn
import paddle.vision.transforms as T
from paddle.io import Dataset, DataLoader
from PIL import Image
import numpy as np

# ----------------------------------------------------------------------
# 1. 设置参数和超参
# ----------------------------------------------------------------------
# 数据集路径配置
DATA_DIR = 'E:\水产种质资源保护区\演示\sample'  # 请确保此路径正确
TRAIN_LIST_PATH = os.path.join(DATA_DIR, 'train_list.txt')
VAL_LIST_PATH = os.path.join(DATA_DIR, 'val_list.txt')
# 训练超参数
BATCH_SIZE = 4  # CPU训练时，可以适当减小batch_size，比如2，以避免内存不足
EPOCHS = 20
LEARNING_RATE = 0.001
IMAGE_SIZE = (512, 512)  # 统一图片和掩码的尺寸
# 模型参数
NUM_CLASSES = 3


# ----------------------------------------------------------------------
# 2. 自定义数据集类 (保持不变)
# ----------------------------------------------------------------------
class SegmentationDataset(Dataset):
	def __init__(self, data_list_file, transform=None):
		self.transform = transform
		self.data_list = []
		with open(data_list_file, 'r') as f:
			for line in f:
				img_path, mask_path = line.strip().split('\t')
				self.data_list.append((img_path, mask_path))
	
	def __getitem__(self, idx):
		img_path, mask_path = self.data_list[idx]
		# 读取图片和掩码
		image = Image.open(img_path).convert('RGB')
		mask = Image.open(mask_path).convert('L')  # L模式表示灰度图，适合单通道掩码
		# 应用变换
		if self.transform:
			image, mask = self.transform(image, mask)
		return image, mask
	
	def __len__(self):
		return len(self.data_list)


# ----------------------------------------------------------------------
# 3. 定义数据预处理和DataLoader (保持不变)
# ----------------------------------------------------------------------
class ComposeTwo:
	def __init__(self, transforms):
		self.transforms = transforms
	
	def __call__(self, img, mask):
		for t in self.transforms:
			img, mask = t(img, mask)
		return img, mask


class Resize:
	def __init__(self, size):
		self.size = size
	
	def __call__(self, img, mask):
		return img.resize(self.size, Image.BILINEAR), mask.resize(self.size, Image.NEAREST)


class ToTensor:
	def __call__(self, img, mask):
		img = T.to_tensor(img)
		mask_np = np.array(mask)
		processed_mask = np.full_like(mask_np, 255, dtype=np.int64)
		processed_mask[mask_np == 1] = 0
		processed_mask[mask_np == 2] = 1
		processed_mask[mask_np == 3] = 2
		mask = paddle.to_tensor(processed_mask, dtype='int64')
		return img, mask


train_transform = ComposeTwo([
	Resize(IMAGE_SIZE),
	ToTensor()
])
val_transform = ComposeTwo([
	Resize(IMAGE_SIZE),
	ToTensor()
])
train_dataset = SegmentationDataset(TRAIN_LIST_PATH, transform=train_transform)
val_dataset = SegmentationDataset(VAL_LIST_PATH, transform=val_transform)
train_loader = DataLoader(dataset=train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
val_loader = DataLoader(dataset=val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)


# ----------------------------------------------------------------------
# 4. 定义模型 (保持不变)
# ----------------------------------------------------------------------
class SimpleSegNet(nn.Layer):
	def __init__(self, num_classes):
		super(SimpleSegNet, self).__init__()
		self.conv1 = nn.Sequential(nn.Conv2D(3, 64, 3, padding=1), nn.BatchNorm2D(64), nn.ReLU())
		self.conv2 = nn.Sequential(nn.Conv2D(64, 128, 3, padding=1), nn.BatchNorm2D(128), nn.ReLU())
		self.pool = nn.MaxPool2D(2, stride=2)
		self.up1 = nn.Sequential(nn.Conv2DTranspose(128, 64, 2, stride=2), nn.BatchNorm2D(64), nn.ReLU())
		self.up2 = nn.Sequential(nn.Conv2DTranspose(64, num_classes, 2, stride=2))
	
	def forward(self, x):
		x1 = self.conv1(x)
		x2 = self.pool(x1)
		x3 = self.conv2(x2)
		x4 = self.pool(x3)
		x5 = self.up1(x4)
		if x5.shape[2:] != x1.shape[2:]:
			x5 = nn.functional.interpolate(x5, size=x1.shape[2:], mode='bilinear', align_corners=False)
		x6 = x1 + x5
		out = self.up2(x6)
		out = nn.functional.interpolate(out, size=IMAGE_SIZE, mode='bilinear', align_corners=False)
		return out


# ----------------------------------------------------------------------
# 5. 训练过程
# ----------------------------------------------------------------------
device = paddle.set_device('cpu')
print("警告：检测到GPU环境存在兼容性问题，已强制切换到CPU进行训练。")
# 实例化模型、损失函数和优化器，并将模型移动到指定设备
model = SimpleSegNet(num_classes=NUM_CLASSES)
criterion = nn.CrossEntropyLoss(ignore_index=255)
optimizer = paddle.optimizer.Adam(learning_rate=LEARNING_RATE, parameters=model.parameters())
print("开始训练...")
print(
	f"训练参数: Batch Size={BATCH_SIZE}, Epochs={EPOCHS}, LR={LEARNING_RATE}, Num Classes={NUM_CLASSES}, Ignore Index=255")
for epoch in range(EPOCHS):
	model.train()  # 设置为训练模式
	for batch_id, (image, mask) in enumerate(train_loader):
		image = image.to(device)
		mask = mask.to(device)
		# 前向计算
		prediction = model(image)
		loss = criterion(prediction, mask)
		# 反向传播
		loss.backward()
		optimizer.step()
		optimizer.clear_grad()
		if batch_id % 10 == 0:
			print(
				f"Epoch [{epoch + 1}/{EPOCHS}], Batch [{batch_id}/{len(train_loader)}], Loss: {loss.numpy().item():.4f}")
	# 每个epoch结束后进行验证
	model.eval()  # 设置为评估模式
	total_val_loss = 0
	with paddle.no_grad():
		for image, mask in val_loader:
			image = image.to(device)
			mask = mask.to(device)
			prediction = model(image)
			loss = criterion(prediction, mask)
			total_val_loss += loss.numpy().item()
	avg_val_loss = total_val_loss / len(val_loader)
	print(f"--- Epoch [{epoch + 1}/{EPOCHS}] 完成, 平均验证损失: {avg_val_loss:.4f} ---")
print("训练完成！")
# 保存模型参数
paddle.save(model.state_dict(), 'semantic_seg_model_3class_cpu.pdparams')
print("模型已保存为 semantic_seg_model_3class_cpu.pdparams")