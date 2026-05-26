import paddle
import paddle.nn as nn
import numpy as np

print("开始进行最小化环境测试...")
# ----------------------------------------------------------------------
# 1. 定义与训练脚本完全相同的参数和模型
# ----------------------------------------------------------------------
BATCH_SIZE = 2
IMAGE_SIZE_H = 512
IMAGE_SIZE_W = 512
NUM_CLASSES = 3
IGNORE_INDEX = 255


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
		out = nn.functional.interpolate(out, size=(IMAGE_SIZE_H, IMAGE_SIZE_W), mode='bilinear', align_corners=False)
		return out


# ----------------------------------------------------------------------
# 2. 直接在GPU上创建100%格式正确的假数据
# ----------------------------------------------------------------------
# 这完全绕过了您的数据集、文件读取和ToTensor变换
device = paddle.set_device('gpu')
print(f"测试设备: {device}")
# 假图片: [N, C, H, W], 值为随机浮点数
fake_image = paddle.randn([BATCH_SIZE, 3, IMAGE_SIZE_H, IMAGE_SIZE_W])
# 假标签: [N, H, W], 值为 {0, 1, 2} 和 255
mask_np = np.random.randint(0, NUM_CLASSES, size=(BATCH_SIZE, IMAGE_SIZE_H, IMAGE_SIZE_W), dtype=np.int64)
# 随机将一些像素设置为忽略索引
ignore_indices = np.random.choice(IMAGE_SIZE_H * IMAGE_SIZE_W, size=100, replace=False)
mask_np.reshape(-1)[ignore_indices] = IGNORE_INDEX
fake_mask = paddle.to_tensor(mask_np)
# 将数据移动到GPU
fake_image = fake_image.to(device)
fake_mask = fake_mask.to(device)
print(f"生成的假图片 shape: {fake_image.shape}, device: {fake_image.place}")
print(f"生成的假标签 shape: {fake_mask.shape}, device: {fake_mask.place}")
print(f"假标签中的唯一值: {paddle.unique(fake_mask)}")
# ----------------------------------------------------------------------
# 3. 实例化模型和损失，进行一次前向和损失计算
# ----------------------------------------------------------------------
model = SimpleSegNet(num_classes=NUM_CLASSES)
criterion = nn.CrossEntropyLoss(ignore_index=IGNORE_INDEX)
model.to(device)
print("\n--- 开始执行模型前向传播和损失计算 ---")
prediction = model(fake_image)
print(f"模型输出 shape: {prediction.shape}")
try:
	loss = criterion(prediction, fake_mask)
	print("\n============================================")
	print("【测试成功】损失函数计算正常！")
	print(f"计算出的损失值: {loss.numpy().item()}")
	print("============================================")
	print("\n结论：您的模型、损失函数和PaddlePaddle环境是正常的。")
	print("问题几乎可以100%确定出在您的数据加载和预处理流程中。")
except Exception as e:
	print("\n============================================")
	print("【测试失败】！")
	print(f"错误信息: {e}")
	print("============================================")
	print("\n结论：问题可能出在您的PaddlePaddle环境或模型本身。")
	print("这非常罕见，可能与CUDNN版本或PaddlePaddle的内部Bug有关。")