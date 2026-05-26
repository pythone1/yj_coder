# segment-anything-2-pipelines (SAM2 遥感影像交互式解译)

## 📌 项目介绍
结合 Meta Segment Anything 2 (SAM 2) 视觉大模型，实现对遥感影像中坑塘、农田、道路的一键多点提示交互式精准提取与边界导出。

## 🛠️ 技术栈
- PyTorch
- SAM 2 (Meta Weights API)
- OpenCV / GeoPandas

## 🌟 核心功能
- 支持 Point、Box 及 Mask 多维 Prompt 交互输入。
- 自动将分割出的边界 Mask 转换为 Shapely 多边形并导出 GeoJSON。
