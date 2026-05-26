# 导入所需的库
from ultralytics import YOLO
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import torch
# 为了解决 OpenMP 运行时被多次链接到程序中的问题，设置环境变量
# os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'


if torch.cuda.is_available():
    print("GPU is available.")
    print("Number of GPUs available: ", torch.cuda.device_count())
    print("GPU(s) detail: ")
    for i in range(torch.cuda.device_count()):
        print(f"Device {i}: {torch.cuda.get_device_name(i)}")
else:
    print("GPU is not available.")


# 定义设备，如果GPU可用，使用GPU，否则使用CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
# 创建一个 tensor
x = torch.rand(5, 3)

# 将 tensor 移动到定义的设备上
x = x.to(device)

# 打印 tensor 以验证其是否在正确的设备上
print(x)



# 加载模型
model = YOLO(r'I:\pyMethod\ultralytics-main\fish_pose\fish\weights\best.pt')  # 加载一个自定义训练的模型
# 使用模型进行预测
results = model(r'I:\downloads\DeepFish\datasets\test\Picture33.jpg')  # 在一个图像上进行预测

# 创建绘图区域
fig, ax = plt.subplots(1)

# 创建绘图区域
fig, ax = plt.subplots(1)

# 遍历预测结果
for result in results:
    # 获取原始图像并显示
    orig_img = result.orig_img
    ax.imshow(orig_img)
    # 获取关键点数据
    keypoints = result.keypoints.data
    # 遍历每一个对象的关键点
    for i, obj_keypoints in enumerate(keypoints):
        # 遍历每一个关键点
        for j, keypoint in enumerate(obj_keypoints):
            # 解析关键点数据
            x, y, confidence = keypoint.tolist()
            # 创建一个圆形标记（实心）
            circle = patches.Circle((x, y), radius=5, edgecolor='r', facecolor='red')
            # 添加标记到绘图区域
            ax.add_patch(circle)
            # 在图像上标记关键点坐标，调整标注位置
            plt.text(x + 5, y - 5, f"x={x:.2f}, y={y:.2f}", fontsize=8, color='white', bbox=dict(facecolor='blue', boxstyle='round,pad=0.2'))
        # 设置标题
        plt.title(f"Object {i+1}")

# 显示图像
plt.show()

