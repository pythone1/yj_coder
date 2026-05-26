# 04-smart-water-systems (智慧水务与工艺机理控制)

本目录收录了城市排水分区拓扑时序仿真、污水处理工艺数学建模以及活性污泥生化控制（ASM1）核心算法。

## 📁 项目列表

### 1. [drainage-network-source-tracking](./drainage-network-source-tracking)
*   **城市排水管网异常节点入流贝叶斯溯源系统**
*   **技术栈**：Python + SWMM API + 遗传算法 (GA) + AM-MCMC 采样
*   **功能**：在大型排水管网拓扑结构中，利用遗传算法进行全局粗筛，并采用自适应马尔可夫链蒙特卡洛（AM-MCMC）算法进行高精度逆流溯源解算，精确定位非法排污及雨污渗漏节点。

### 2. [wastewater-lstm-control](./wastewater-lstm-control)
*   **污水厂出水指标预测与 MPC 工艺优化控制系统**
*   **技术栈**：PyTorch + LSTM + CCF 时延分析 + 反硝化 ASM1 机理 + 模型预测控制 (MPC)
*   **功能**：利用 12小时 Lookback 预测窗口的 LSTM 预测工艺末端指标变化，动态求解最优曝气风机赫兹频率及加药泵速，降耗 **15% 以上**。

### 3. [pypoo-reactor-simulation](./pypoo-reactor-simulation)
*   **PyPOO 污水处理生化反应器动态解算框架**
*   **技术栈**：Python + SciPy (ODE 求解) + YAML Configs
*   **功能**：采用面向对象开发，对二沉池、曝气池和消化反应器等物理单元进行组装，输入 YAML 流程图自动求解动态生化反应平衡。
