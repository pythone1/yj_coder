# 02-computer-vision (计算机视觉与边缘物联)

本目录收录了工业及遥感场景下的计算机视觉（目标检测、语义分割、交互式图斑分割）核心项目。

## 📁 项目列表

### 1. [forklift-monitoring-yolo-uwb](./forklift-monitoring-yolo-uwb)
*   **工业铲车配比动作与轨迹智能监控系统**
*   **技术栈**：Python + YOLOv11 + OpenCV + UWB 串口协议
*   **功能**：在冶炼与配料车间边缘端部署 YOLO 模型，智能识别铲斗负荷状态（满载、空载）及司机倾倒动作，并与车间内 UWB 定位信号深度融合，智能比对铲车配料比例，输出作业统计日志。

### 2. [sam2-interactive-segmentation](./sam2-interactive-segmentation)
*   **SAM 2 遥感影像交互式高精解译工具**
*   **技术栈**：PyTorch + Segment Anything 2 (Meta API) + GeoPandas
*   **功能**：接入前沿视觉大模型，实现对卫星/无人机高分影像中的不规则地物（池塘、大棚、道路）的多点点击/红线交互框提示（Prompt）式分割，一键提取出高精确的边界 Mask 并转存为地理矢量数据。

### 3. [unet-water-segmentation](./unet-water-segmentation)
*   **经典 UNet 遥感水体/图斑像素级分割工程**
*   **技术栈**：Python + PyTorch + UNet 语义分割架构
*   **功能**：对复杂光谱背景的水体进行像素级判定，支持全套训练、评测与可视化 Mask 导出流程。

### 4. [yolov12-object-detection](./yolov12-object-detection)
*   **YOLOv12 目标检测模型训练与工程评估套件**
*   **技术栈**：PyTorch + Ultralytics YOLOv12
*   **功能**：包含训练配置、数据集对齐和快速调优工具，用于工业安全和特种车辆的视觉场景应用。
