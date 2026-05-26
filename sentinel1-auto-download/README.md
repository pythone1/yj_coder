# sentinel1-auto-download (Sentinel-1 雷达卫星数据自动下载)

## 📌 项目介绍
面向 Sentinel-1 合成孔径雷达（SAR）卫星影像的自动化检索、多线程下载与预处理系统。

## 🛠️ 技术栈
- Python
- SentinelAPI (Copernicus Data Space)
- Requests

## 🌟 核心功能
- 支持基于 ROI 经纬度多边形、时间窗口及偏振模式（VV/VH）自动检索。
- 支持断点续传、高并发下载任务调度与元数据信息解析。
