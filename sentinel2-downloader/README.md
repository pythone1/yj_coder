# sentinel2-downloader (Sentinel-2 遥感数据自动化检索与下载)

## 📌 项目介绍
自动从欧空局数据空间下载指定区域、无云或低云覆盖率的 Sentinel-2 多光谱遥感产品（L1C/L2A）。

## 🛠️ 技术栈
- Python
- SpatioTemporal Asset Catalog (STAC) API / Requests

## 🌟 核心功能
- 自动提取目标区域切片（Granule），合并网络下载线程，并在下载失败时触发自动重试机制。
