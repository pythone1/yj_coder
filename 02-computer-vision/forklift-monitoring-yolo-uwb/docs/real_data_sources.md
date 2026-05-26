# 真实数据源与联调建议

这份清单用于给当前“UWB 主判 + 视觉辅助”原型提供更接近真实场景的测试数据。

## 1. 叉车目标检测数据

- Hugging Face `keremberke/forklift-object-detection`
  - 链接: https://huggingface.co/datasets/keremberke/forklift-object-detection
  - 特点: 421 张图片，类别为 `forklift` 和 `person`
  - 用途: 适合快速验证叉车检测模型、做人车同框误检分析

- Roboflow Universe `forklift` 数据集
  - 链接: https://universe.roboflow.com/forklift-4ulnu/forklift-uo0vm
  - 特点: 6.4k 图像，类别为 `forklift` 和 `person`
  - 用途: 更适合后续微调 forklift 专用检测器

- Roboflow Universe `3DForklift`
  - 链接: https://universe.roboflow.com/forklift-klnjt/3dforklift
  - 特点: 约 1k 图像，带 `Forklift / Head / Tail`
  - 用途: 更适合研究叉车朝向、车头车尾方向和路径方向判断

## 2. 可参考的叉车模型

- Hugging Face `keremberke/yolov8m-forklift-detection`
  - 链接: https://huggingface.co/keremberke/yolov8m-forklift-detection
  - 特点: 叉车专用检测模型，标签为 `forklift` 和 `person`
  - 用途: 比通用 COCO 模型更适合仓储叉车场景

## 3. 工业视频与行为类数据

- Voxel51 `Safe_and_Unsafe_Behaviours`
  - 链接: https://huggingface.co/datasets/Voxel51/Safe_and_Unsafe_Behaviours
  - 来源页: https://data.mendeley.com/datasets/xjmtb22pff/1
  - 特点: 691 个工业视频片段，包含 `Carrying Overload with Forklift`
  - 用途: 适合后续验证“异常作业行为检测”，不只看目标检测

## 4. 当前工程最建议的验证顺序

1. 先用现有 RTSP/USB 摄像头视频，跑 `YOLO + 跟踪 + 图像区域状态机`
2. 再补叉车专用检测模型，降低通用车辆模型对叉车的漏检和误检
3. 最后用公开工业视频或你们现场录像，联调 `UWB 主判 + 视频辅助`

## 5. 联调建议

- 如果现场视频视角固定，优先做区域判定，不要一开始做复杂重识别
- 如果现场叉车数量不多，`track_id + 区域状态机` 往往已经够用
- 如果 UWB 已经稳定给到坐标，视频链路优先承担“校验与留证”职责
