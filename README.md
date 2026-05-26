# Geospatial-AI-Ecosystem (天空地一体化与水务智能算法生态系统)

这是一个面向工业级应用的地理信息系统 (GIS)、卫星/无人机遥感 (RS) 图像解译、城市排水管网水力学建模与活性污泥生化工艺 (ASM1) 智能控制的综合算法生态仓。

由 **杨佳** (29岁, 毕业于南京工程学院车辆工程专业, 现就职于南大五维电子科技有限公司研发中心数据部, 资深 AI 算法与遥感工程师) 独立设计与开发。

---

## 🌟 仓库项目矩阵 (Project Matrix)

本仓库包含以下 6 大核心工业级项目：

### 1. [urban-drainage-source-apportionment](./urban-drainage-source-apportionment)
*   **城市排水管网入流异常溯源与定位分析系统**
*   **技术栈**：Python + SWMM (Storm Water Management Model) API (`swmmh5.dll/exe`) + 遗传算法 (GA) + 自适应大都会算法 (AM-MCMC 采样) + 贝叶斯推导。
*   **核心功能**：通过在 9 个排水管网监测传感器节点上收集时序数据，设计 GA 粗筛选与 AM-MCMC 细解算的贝叶斯优化框架，在 20 个候选入流节点中精准定位出 5 个隐蔽异常注入点，成功克服了同流路汇聚造成的“代偿模糊路径”（compensation），后验模拟 NSE (纳什系数) 达 **0.936**。

### 2. [wastewater-process-control-lstm](./wastewater-process-control-lstm)
*   **东阳污水处理厂 AI 预测预警与运行自适应控制优化系统**
*   **技术栈**：PyTorch + LSTM + 互相关分析 (CCF) + 双重级联滤波 (SCADA 清洗) + 反硝化工艺机理 (ASM1) + 模型预测控制 (MPC)。
*   **核心功能**：针对污水厂工艺处理超长水力与生化代谢时滞（HRT达15-20.5小时），自研 12小时（144步长）Lookback Window LSTM 时序预测网络。超前 2 小时预测出水 TN、TP、NH3-N 变化；设计中值加滑动平均级联滤波清洗 SCADA 异常死值；动态调控风机曝气风量及外加碳源和 PAC 投药流量，在稳定出水品质的同时，化学药耗降低 **15% 以上**。

### 3. [aquaculture-pond-drainage-analysis](./aquaculture-pond-drainage-analysis)
*   **水产养殖坑塘排水与滩涂水域变化 NDWI/NDVI 统计模型**
*   **技术栈**：Python + GeoPandas + Shapely + Rasterio + Matplotlib + PyQtGraph。
*   **核心功能**：基于长时序多源遥感影像波段提取，自研 NDWI、NDVI 指数处理流水线。统计分析宜兴及盐城等重点水产普查地物的排水时间与面积动态，支持大范围图斑面积自动计算及空间投影转换（CGCS2000）。

### 4. [industrial-forklift-ratio-monitoring](./industrial-forklift-ratio-monitoring)
*   **滇中有色废渣二次提炼铜铲运比例 AI 智能监控系统**
*   **技术栈**：Python + OpenCV + 目标检测 (YOLO/PyTorch) + 行为计数。
*   **核心功能**：针对有色金属精炼配比铲车司机不按规定铲斗比例进料的生产痛点，部署 AI 动作与料堆位置监控系统，自动识别铲斗负荷状态并统计铲斗次数，与车载称重计协同通信，防止后续配比工序出错。

### 5. [glm5-rag-quant-trading](./glm5-rag-quant-trading)
*   **基于智谱 GLM-5 RAG 的量化交易知识库引擎**
*   **技术栈**：Python + 智谱 API + Qdrant 向量数据库 + HNSW 索引 + LangChain。
*   **核心功能**：面向垂直领域的金融量化和编码规范搭建的 RAG 召回链路，利用密集和稀疏混合检索实现高精度知识检索与代码生成。

### 6. [satellite-imagery-water-quality-retrieval](./satellite-imagery-water-quality-retrieval)
*   **多源卫星遥感影像自动处理与水质反演推送系统**
*   **技术栈**：Python + Sentinel-2/3 API + GF-4 影像处理 + Cloud Masking + Sen2Cor 大气校正 + Webhook。
*   **核心功能**：自动化检索下载每日最新影像，对云雾遮挡区域进行滑窗去云和插值拼接，运行反射率定标及大气纠正，自动输出黑臭指数、悬浮物及叶绿素反演热力图，并与企业微信 Webhook 绑定实现每日定时推送。

---

## 🛠️ 安装与配置说明 (Installation)

由于本项目依赖底层的地理信息库与水力学模拟引擎，请使用 Anaconda 环境进行依赖安装：

```bash
# 创建 Conda 环境
conda create -n geo-ai-env python=3.9 -y
conda activate geo-ai-env

# 安装 GIS 空间数据处理基础包
conda install -c condensol-forge gdal geopandas rasterio shapely -y

# 安装深度学习与算法包
pip install torch torchvision pandas numpy matplotlib openpyxl pyqt5 pyqtgraph qdrant-client
```

对于 `urban-drainage-source-apportionment` 文件夹下的水动力解算，请确保系统 PATH 变量中包含 `swmmh5.dll` 引擎依赖。

---

## 🏆 荣誉与执照 (Certifications)
*   中华人民共和国高级程序员资格认证
*   中国民用航空局高级无人机驾驶员执照 (AOPA 合格证)
