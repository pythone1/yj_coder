# Geospatial-AI-Ecosystem (天空地一体化与智慧水务算法生态仓)

这是一个面向工业级应用的地理信息系统 (GIS)、卫星/无人机遥感 (RS) 图像解译、城市排水管网水力学建模与活性污泥生化工艺 (ASM1) 智能控制的综合算法生态仓。

由 **杨佳** (资深 AI 算法与遥感工程师) 独立设计、开发与重构。

---

## 🌟 仓库分类矩阵 (Categorized Project Matrix)

为了提高仓库工程性与代码可读性，本项目已全面清理零散的辅助脚本和低代码小工程，将剩余的 **13 个高含金量主体系统** 重构整合为以下 **4 大核心技术领域** 目录：

### 📁 [01-geospatial-remote-sensing](./01-geospatial-remote-sensing) (遥感与空间地理信息分析)
*   **[water-quality-retrieval](./01-geospatial-remote-sensing/water-quality-retrieval)**：*多源卫星遥感影像自动处理与水质反演系统*。支持 Sentinel-2/3、GF-4 自动下载、去云拼接、反射率定标及叶绿素、悬浮物和黑臭指数时序反演，支持企业微信 Webhook 每日定时推送。
*   **[aquaculture-census-platform](./01-geospatial-remote-sensing/aquaculture-census-platform)**：*全省养殖池塘普查分析系统*。支持海量池塘空间属性字段比对、去重与重叠消除，自动核对遥感图斑结果并导出疑点排查报告。
*   **[water-quality-classification](./01-geospatial-remote-sensing/water-quality-classification)**：*基于 SVM/随机森林的卫星影像地表水域自动分类器*。

### 📁 [02-computer-vision](./02-computer-vision) (计算机视觉与边缘物联)
*   **[forklift-monitoring-yolo-uwb](./02-computer-vision/forklift-monitoring-yolo-uwb)**：*特种车辆动作与轨迹智能监控系统*。利用 YOLO 边缘端实时检测铲斗负荷状态与上料倾倒动作，并与车间内 UWB 物联定位坐标包实时融合计算，防错比对并统计作业频次。
*   **[sam2-interactive-segmentation](./02-computer-vision/sam2-interactive-segmentation)**：*基于 Segment Anything 2 的遥感多源地物交互式解译工具*。支持点击/交互边界框 Prompt，一键分割复杂图斑并导出为矢量多边形（Shapely）。
*   **[unet-water-segmentation](./02-computer-vision/unet-water-segmentation)**：*基于 UNet 的高精度遥感水体像素级语义分割网络*。
*   **[yolov12-object-detection](./02-computer-vision/yolov12-object-detection)**：*YOLOv12 目标检测网络训练与工程指标评估套件*。

### 📁 [03-llm-agents](./03-llm-agents) (大模型智能体与量化应用)
*   **[glm5-quant-rag](./03-llm-agents/glm5-quant-rag)**：*基于智谱 GLM-5 与 Qdrant 的量化交易知识库 RAG 引擎*。利用混合检索召回算法规范与技术指标代码。
*   **[auto-glm-device-agent](./03-llm-agents/auto-glm-device-agent)**：*基于大模型视觉决策的多端 ADB 自动操控 Agent*。
*   **[ppt-generation-agent](./03-llm-agents/ppt-generation-agent)**：*智能商业幻灯片排版与自动化生成 Agent*。
*   **[llm-chatbot](./03-llm-agents/llm-chatbot)**：*前/后端一体化全栈 Chatbot 智能交互平台*。

### 📁 [04-smart-water-systems](./04-smart-water-systems) (智慧水务与工艺机理控制)
*   **[drainage-network-source-tracking](./04-smart-water-systems/drainage-network-source-tracking)**：*城市排水管网异常节点入流贝叶斯溯源系统*。利用 Python 驱动 SWMM 引擎，设计遗传算法（GA）进行大范围拓扑粗筛，并采用 AM-MCMC 时序采样高精度定位排污/渗漏源。
*   **[wastewater-lstm-control](./04-smart-water-systems/wastewater-lstm-control)**：*污水厂出水预测与 MPC 自适应加药/曝气优化系统*。看回 12 小时的 LSTM 预测结合 ASM1 模型预测控制，实现出水稳定且药耗风耗降低 **15% 以上**。
*   **[pypoo-reactor-simulation](./04-smart-water-systems/pypoo-reactor-simulation)**：*基于面向对象（OOP）设计的二沉池及反应器生化动态解算仿真框架*。

---

## 🛠️ 安装与配置说明 (Installation)

由于本项目依赖底层的地理信息库与水力学模拟引擎，请使用 Anaconda 环境进行依赖安装：

```bash
# 创建 Conda 环境
conda create -n geo-ai-env python=3.9 -y
conda activate geo-ai-env

# 安装 GIS 空间数据处理基础包
conda install -c conda-forge gdal geopandas rasterio shapely -y

# 安装深度学习、计算机视觉与大模型 API 相关依赖包
pip install torch torchvision pandas numpy matplotlib openpyxl pyqt5 pyqtgraph qdrant-client opencv-python pyyaml ultralytics
```

对于 `04-smart-water-systems/drainage-network-source-tracking` 目录下的管网计算，请确保系统 PATH 变量中已包含 `swmmh5.dll` 引擎运行环境。

---

## 🏆 个人执照与技术实力 (Certifications)
*   中华人民共和国高级程序员资格认证
*   中国民用航空局高级无人机驾驶员执照 (AOPA 合格证)
