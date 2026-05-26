# Geospatial-AI-Ecosystem (天空地一体化与水务智能算法生态系统)

这是一个面向工业级应用的地理信息系统 (GIS)、卫星/无人机遥感 (RS) 图像解译、城市排水管网水力学建模与活性污泥生化工艺 (ASM1) 智能控制的综合算法生态仓。

由 **杨佳** (资深 AI 算法与遥感工程师) 独立设计与开发。

---

## 🌟 仓库项目矩阵 (Project Matrix)

本仓库将 30 多个优秀的项目和研究代码整合成 5 大专业级领域技术板块：

### 1. 🌌 天空地一体化遥感与 GIS (Geospatial & RS-GIS)
面向卫星和无人机多源数据，涵盖 Sentinel-1/2/3 自动下载、大气校正、去云拼接、水体反演与省级水产普查系统。
*   **[satellite-imagery-water-quality-retrieval](./satellite-imagery-water-quality-retrieval)** / **[water-quality-satellite-classification](./water-quality-satellite-classification)**
    *   *多源卫星遥感影像自动处理与水质反演推送系统*：支持 Sentinel-2/3、GF-4 自动下载、大气纠正、黑臭指数、悬浮物反演及企业微信 Webhook 自动推送。
*   **[provincial-aquaculture-census](./provincial-aquaculture-census)**
    *   *全省养殖池塘上图入库普查系统*：涵盖数据合规性检查、填报进度自动统计、疑点影像交叉核查，支持大规模遥感结果与地理数据库（GeoDatabase）对接。
*   **[aquaculture-pond-extraction](./aquaculture-pond-extraction)**
    *   *高分辨率遥感养殖池塘图斑智能提取*：利用遥感图像边缘及纹理特征提取规则，实现坑塘图斑精确提取。
*   **[satellite-remote-sensing-products](./satellite-remote-sensing-products)**
    *   *卫星遥感专题产品开发套件*：支持各种遥感指数运算，输出多波段拼接产品。
*   **[sentinel1-auto-download](./sentinel1-auto-download)** / **[sentinel2-downloader](./sentinel2-downloader)**
    *   *Sentinel-1 (雷达/SAR) & Sentinel-2 自动检索与批处理工具*。
*   **[tianditu-map-generation](./tianditu-map-generation)**
    *   *天地图网页大屏自动构建与可视化系统*。
*   **[remote-sensing-water-indices](./remote-sensing-water-indices)**
    *   *水色指数与黑臭指数遥感波段计算库*。

---

### 2. 💧 水务工程与智能控制 (Environmental & Water Control AI)
城市水系统仿真、污水厂智能控制及水质预测算法。
*   **[urban-drainage-source-apportionment](./urban-drainage-source-apportionment)**
    *   *城市排水管网入流异常溯源与定位分析系统*：基于 Python + SWMM API + 遗传算法 (GA) + AM-MCMC 时序异常溯源，解决管网污水渗漏/非法注入路径模糊问题。
*   **[wastewater-process-control-lstm](./wastewater-process-control-lstm)** / **[lstm-wastewater-model](./lstm-wastewater-model)**
    *   *污水处理厂 AI 预测预警与运行自适应控制优化系统*：12 小时长窗口 LSTM 网络预测出水指标；结合 SCADA 双重级联滤波与生化 ASM1 机理实现 Model Predictive Control (MPC) 智能控制，降耗 **15% 以上**。
*   **[activated-sludge-model](./activated-sludge-model)**
    *   *ASM1 (活性污泥 1 号模型) 生化解算器与动态仿真引擎*。
*   **[pond-drainage-algorithm](./pond-drainage-algorithm)**
    *   *养殖坑塘非稳态排水演进与水动力计算模型*。
*   **[sheyang-wastewater-project](./sheyang-wastewater-project)**
    *   *射阳城北污水处理厂工艺分析与建模优化工程*。
*   **[pypoo-process-simulation](./pypoo-process-simulation)**
    *   *PyPOO 污水处理工艺单元模拟与反应动力学仿真框架*。

---

### 3. 👁️ 计算机视觉与物联监控 (Computer Vision & Edge AI)
基于前沿检测与分割模型的实时监控、图像解译与边缘端应用。
*   **[industrial-forklift-ratio-monitoring](./industrial-forklift-ratio-monitoring)** / **[forklift-cv-tracking](./forklift-cv-tracking)**
    *   *有色金属二次精炼铲车配比智能监控系统*：YOLOv11 负荷动作识别 + UWB 室内定位协议对接，智能跟踪车辆行驶轨迹与上料频次。
*   **[segment-anything-2-pipelines](./segment-anything-2-pipelines)**
    *   *SAM 2 (Segment Anything 2) 在遥感与 GIS 图斑交互解译中的流水线应用*。
*   **[unet-water-segmentation](./unet-water-segmentation)**
    *   *UNet 经典语义分割网络在遥感水体/图斑识别中的落地实现*。
*   **[yolov12-training-pipelines](./yolov12-training-pipelines)**
    *   *前沿 YOLOv12 目标检测与行为识别模型微调及评估工具*。
*   **[yolo-flask-web-app](./yolo-flask-web-app)**
    *   *基于 Flask 的实时 YOLO 图像推理接口与可视化 Web 平台*。
*   **[image-segmentation-tools](./image-segmentation-tools)**
    *   *通用的遥感及工业零部件边缘识别分割算法库*。

---

### 4. 🤖 智能体、量化与通用 AI (LLM Agents & Quant Trading)
前沿的大语言模型智能应用与量化交易决策平台。
*   **[glm5-rag-quant-trading](./glm5-rag-quant-trading)** / **[quant-trading-algorithms](./quant-trading-algorithms)**
    *   *基于智谱 GLM-5 RAG 的金融量化与代码规范召回库*：利用 Qdrant (HNSW) 混合检索与时序因子计算的决策库。
*   **[auto-glm-agent](./auto-glm-agent)**
    *   *基于 Open-AutoGLM 的安卓/多端操控 Agent 原型*：结合 ADB 动作定义与大模型视觉多模态动作决策。
*   **[ppt-generation-agent](./ppt-generation-agent)**
    *   *智能 PPT 排版与报告大纲自动化生成体*：基于 Python-PPTX 的文档级智能渲染排版。
*   **[llm-chatbot-service](./llm-chatbot-service)**
    *   *极简前端/后端全栈 Chatbot 智能会话交互系统*。
*   **[yuxiaozhu-wechat-api](./yuxiaozhu-wechat-api)**
    *   *“鱼小助”微信小程序/公众号后端高性能接口代码*。

---

### 5. 🛠️ 研发底座与学习实验室 (Developer Learning & Tech Labs)
底座架构与技术预研沉淀。
*   **[developer-learning-labs](./developer-learning-labs)**
    *   *个人学习与原型验证实验室*：保存前沿框架的 Demo 实现与调试记录。
*   **[research-and-development](./research-and-development)**
    *   *研发中心数据部技术白皮书与文档归档*。
*   **[engineering-tech-scripts](./engineering-tech-scripts)**
    *   *通用工程化工具箱*：含表格合并、文档转换、PDF/Word 操作接口等。
*   **[qt-pyqt5-examples](./qt-pyqt5-examples)**
    *   *基于 PyQt5 的桌面可视化 GUI 组件集*。
*   **[jupyter-notebooks](./jupyter-notebooks)**
    *   *用于快速验证算法可行性的 Jupyter 时空分析沙箱*。

---

## 🛠️ 安装与配置说明 (Installation)

由于本项目依赖底层的地理信息库与水力学模拟引擎，请使用 Anaconda 环境进行依赖安装：

```bash
# 创建 Conda 环境
conda create -n geo-ai-env python=3.9 -y
conda activate geo-ai-env

# 安装 GIS 空间数据处理基础包
conda install -c conda-forge gdal geopandas rasterio shapely -y

# 安装深度学习与算法包
pip install torch torchvision pandas numpy matplotlib openpyxl pyqt5 pyqtgraph qdrant-client opencv-python pyyaml ultralytics
```

对于 `urban-drainage-source-apportionment` 文件夹下的水动力解算，请确保系统 PATH 变量中包含 `swmmh5.dll` 引擎依赖。

---

## 🏆 个人执照与技术实力 (Certifications)
*   中华人民共和国高级程序员资格认证
*   中国民用航空局高级无人机驾驶员执照 (AOPA 合格证)
