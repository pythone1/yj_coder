# 01-geospatial-remote-sensing (遥感与空间地理信息分析)

本目录收录了核心的遥感数据处理、水质卫星反演以及省级水产养殖池塘普查分析系统。

## 📁 项目列表

### 1. [water-quality-retrieval](./water-quality-retrieval)
*   **多源卫星遥感影像自动处理与水质反演系统**
*   **技术栈**：Python + Sentinel-2/3 API + GF-4 影像处理 + Cloud Masking + Sen2Cor 大气校正
*   **功能**：实现每日遥感影像的自动检索与多线程下载，对云雾遮挡区域进行智能去云与插值拼接，运行反射率定标及大气纠正，自动输出黑臭指数、悬浮物及叶绿素反演热力图，并与企业微信 Webhook 联动定时推送。

### 2. [aquaculture-census-platform](./aquaculture-census-platform)
*   **全省养殖池塘上图入库大范围普查系统**
*   **技术栈**：Python + GeoPandas + Leaflet + Openpyxl
*   **功能**：对全省各地级市上报的数万条养殖池塘空间分布数据进行合规性核查、多边形重叠消除，并根据高分遥感图斑提取结果比对，自动输出异常排查报告，大幅提升地理数据库的数据完整率。

### 3. [water-quality-classification](./water-quality-classification)
*   **多光谱水色遥感分类模型**
*   **技术栈**：Python + Scikit-Learn (SVM/随机森林) + GDAL
*   **功能**：基于卫星波段光谱特征值，对地表水域进行自动化分类识别。
