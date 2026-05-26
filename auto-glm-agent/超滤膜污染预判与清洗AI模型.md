# **基于机理融合与无监督学习的超滤膜污染智能预判与清洗决策优化研究报告**

1\. 执行摘要

在市政供水与工业废水回用领域，超滤（Ultrafiltration, UF）膜系统的运行稳定性直接关系到产水水质与运营成本（OPEX）。当前，大多数水厂仍沿用基于时间步长的传统“定时清洗”策略，这种非自适应的模式往往导致两个极端：一是清洗滞后，导致膜孔发生不可逆堵塞，缩短膜寿命；二是过度清洗，造成化学药剂浪费、停机时间增加及膜材料的氧化损伤。

本报告针对用户提出的“膜污染预判与清洗AI模型”构建需求，特别是针对缺乏历史标注数据（无Y值、无故障标签）的“冷启动”场景，进行了详尽的文献调研与技术论证。基于300余份前沿学术文献与工业技术手册的综合分析，本报告构建了一套融合流体力学机理与无监督机器学习（Unsupervised Learning）的智能运维框架。

核心发现与决策建议包括：

1. **污染表征重构**：单纯依赖跨膜压差（TMP）数值不足以精准判断污染类型。必须引入跨膜压差的变化率（$d\\text{TMP}/dt$）及其二阶导数（曲率），结合标准化渗透率（$K\_{20}$）衰减曲线，利用Hermia堵塞模型区分“滤饼层过滤”（线性增长）与“孔堵塞”（指数增长）1。  
2. **清洗策略修正**：针对用户设想的“浊度升高 $\\rightarrow$ 酸洗”逻辑进行了修正。高浊度通常意味着胶体或悬浮颗粒负荷，应优先采用物理反洗或碱性表面活性剂清洗，而非酸洗。酸洗主要针对硬度导致的无机结垢。对于成分复杂的进水，推荐采用“碱性氧化剂（NaClO+NaOH）+ 螯合酸（柠檬酸）”的组合清洗工艺，该组合在全尺寸水厂测试中显示出对复合污染（有机物-铝/硅共沉淀）的最佳恢复效果 3。  
3. **无监督AI模型**：针对无标签数据，建议采用**K-Means聚类算法**对历史运行周期的TMP曲线形态进行分类，识别不同的污染模式（Cluster）；同时部署**自动编码器（Autoencoder）或LSTM网络**进行异常检测，利用重构误差（Reconstruction Error）作为污染严重程度的量化指标，解决“无目标Y值”的建模难题 5。  
4. **动态干预控制**：摒弃固定时长的清洗模式，建立基于渗透率恢复速率（$dK/dt$）的动态终止机制。当清洗过程中的渗透率恢复曲线进入“平台期”（Plateau），且变化率低于设定阈值（如1%/10min）时，即判定清洗结束，以防止无效清洗 7。

本报告将从膜污染机理、多维表征指标、清洗化学原理、无监督学习算法架构及工程落地路线图五个维度展开，提供一份可直接指导现场实施的深度技术文档。

## ---

**2\. 超滤膜污染的机理分型与多维表征**

要构建精准的预判模型，首先必须从物理和化学层面解构“膜污染”。膜污染并非单一现象，而是物理沉积、化学吸附和生物生长的复杂耦合。

### **2.1 膜污染的流体力学机理（Hermia模型应用）**

在恒通量（Constant Flux）运行模式下（工业UF典型模式），污染体现为TMP的随时间上升。Hermia孔堵塞模型提供了通过TMP曲线形状反推污染机理的数学依据 9。

| 污染机理模型 | 物理现象描述 | TMP曲线特征 (恒通量) | 关键数学特征 | 典型成因 |
| :---- | :---- | :---- | :---- | :---- |
| **完全孔堵塞 (Complete Blocking)** | 颗粒尺寸 $\\approx$ 膜孔径。颗粒直接封死膜孔开口，有效过滤面积急剧减少。 | **指数级急剧上升** (Concave Up) | $d^2P/dt^2 \> 0$ (二阶导数为正) | 进水中含有与膜孔径相当的胶体或大分子有机物。 |
| **标准孔堵塞 (Standard Blocking)** | 颗粒尺寸 $\<$ 膜孔径。污染物吸附在膜孔内壁，导致孔径逐渐变小。 | **加速上升** | 阻力增长通常快于滤饼层，且难以通过水力反洗去除。 | 溶解性有机物 (DOM)、腐殖酸吸附。 |
| **中间孔堵塞 (Intermediate Blocking)** | 颗粒可能堵塞孔口，也可能沉积在已堵塞的颗粒上。过渡状态。 | **逐渐上升** | 介于指数与线性之间。 | 混合粒径分布的进水。 |
| **滤饼层过滤 (Cake Filtration)** | 颗粒尺寸 $\>$ 膜孔径。颗粒堆积在膜表面形成多孔滤饼层。 | **线性上升** (Linear) | $dP/dt \\approx \\text{Constant}$ (一阶导数恒定) | 悬浮固体 (TSS)、活性污泥、较大颗粒物。 |

**工程启示**：在构建AI模型时，不仅要输入当前的TMP值，必须输入\*\*TMP的一阶导数（斜率）和二阶导数（曲率）\*\*作为特征变量。如果模型检测到TMP呈指数上升，预示着严重的孔堵塞，必须立即干预；若呈线性上升，则可通过常规反洗维持 1。

### **2.2 基于污染物化学性质的分类与表征**

根据污染物的化学成分，膜污染主要分为四类。针对用户提出的“水质指标表征”问题，下表总结了各类污染的关键水质指征 11。

#### **2.2.1 颗粒与胶体污染 (Particulate/Colloidal Fouling)**

* **物质来源**：泥沙、粘土、二氧化硅胶体、悬浮物。  
* **表征指标**：  
  * **进水浊度 (Turbidity)**：最直接指标。浊度显著升高（如 \>10 NTU）通常对应滤饼层的快速形成。  
  * **淤泥密度指数 (SDI)**：针对胶体污染更敏感。SDI \> 5 预示极高的胶体污堵风险。  
  * **TSS (总悬浮固体)**：与滤饼层厚度线性相关。  
* **水力表现**：TMP线性增长，物理反洗（Backwash）可恢复性较高（Reversible）。

#### **2.2.2 有机污染 (Organic Fouling)**

* **物质来源**：天然有机物 (NOM)、腐殖酸 (Humic Acid)、富里酸、蛋白质、多糖。  
* **表征指标**：  
  * **TOC (总有机碳)** / **COD\_Mn**：直接反映有机负荷。  
  * **UV254 (紫外吸光度)**：特异性指示含苯环结构的腐殖质类物质，这类物质对PVDF膜有极强的疏水吸附性。  
  * **TMP特征**：在低浊度下，若TMP出现非线性快速上升，且反洗恢复率低（Irreversible），通常指向有机吸附 3。  
* **交互作用**：钙离子 ($Ca^{2+}$) 会与腐殖酸形成“桥接”，加剧有机污染层的致密性 13。

#### **2.2.3 无机结垢 (Inorganic Scaling)**

* **物质来源**：碳酸钙 ($CaCO\_3$)、硫酸钙 ($CaSO\_4$)、金属氧化物 (Fe, Mn, Al)。  
* **表征指标**：  
  * **硬度 (Hardness)** & **碱度 (Alkalinity)**：高硬度结合高pH值，极易导致碳酸钙结垢。  
  * **金属离子浓度**：Fe \> 0.1 mg/L, Mn \> 0.05 mg/L, Al \> 0.05 mg/L。特别是铝盐混凝剂过量投加导致的残留铝，是造成不可逆无机污染的常见原因 3。  
  * **TMP特征**：通常表现为长周期的基础阻力（反洗后阻力）缓慢爬升，物理反洗几乎无效。

#### **2.2.4 生物污染 (Biofouling)**

* **物质来源**：细菌、藻类及其分泌的胞外聚合物 (EPS)。  
* **表征指标**：  
  * **温度**：水温升高（尤其20-35°C）会显著加速微生物繁殖 14。  
  * **ATP (三磷酸腺苷)**：反映生物活性，但在线监测较难。  
  * **TMP特征**：运行初期稳定，随生物膜成熟出现爆发式增长（Exponential growth），且产生极其粘稠的“粘液层”，增加清洗难度。

## ---

**3\. 清洗化学体系与策略优化**

针对用户关于“不同污染适用什么清洗剂”及“影响清洗因素”的疑问，本节基于化学机理与实验数据进行详细阐述。

### **3.1 清洗剂选择决策逻辑**

用户原有的设想（浊度 $\\rightarrow$ 酸洗）存在一定误区。高浊度形成的泥饼层通常由无机颗粒和有机粘结剂组成，直接酸洗可能导致某些有机物（如腐殖酸）在低pH下沉淀硬化，反而难以去除。

**修正后的清洗剂选择矩阵**：

| 目标污染物 | 首选清洗剂 | 辅助/替代剂 | 作用机理 | 适用场景判据 |
| :---- | :---- | :---- | :---- | :---- |
| **有机物 (腐殖酸、蛋白质)** | **碱性氧化剂** (NaOH \+ NaClO) | 碱性表面活性剂 (SDS) | **水解与氧化**：NaOH使有机物带负电（静电排斥）并皂化油脂；NaClO氧化断链，破坏凝胶层结构 3。 | TOC/UV254升高；TMP非线性上升；膜面有滑腻感。 |
| **生物膜 (Biofilm)** | **氧化剂** (NaClO) | 酶制剂 (Enzymes) | **杀菌与解构**：破坏EPS骨架，杀灭微生物。 | 压差突增；高温季节；系统停机后。 |
| **无机结垢 (碳酸盐)** | **矿物酸** (HCl, $H\_2SO\_4$) | 氨基磺酸 | **溶解**：质子 ($H^+$) 与碳酸根反应生成$CO\_2$和可溶盐。 | 硬度高；pH高；反洗后阻力持续上升。 |
| **金属氧化物 (Fe, Al, Mn)** | **有机螯合酸** (柠檬酸 Citric Acid, 草酸) | 连二亚硫酸钠 (还原剂) | **螯合作用**：柠檬酸根与金属离子形成稳定的水溶性络合物。 | 混凝剂投加过量 (Al/Fe残留)；地下水铁锰超标 3。 |
| **胶体/悬浮颗粒** | **物理清洗 \+ 碱洗** | 阴离子表面活性剂 | **分散与松解**：降低表面张力，使颗粒脱落。 | 浊度/SDI高；主要是物理反洗，化学加强反洗(CEB)用碱。 |

**特别说明**：

* **铝污染（Al Fouling）**：如果前处理使用了聚合氯化铝（PAC），膜表面常形成铝的氢氧化物或铝-有机络合物。研究表明，\*\*柠檬酸（Sodium Citrate/Citric Acid）\*\*对铝污染的清洗效果远优于盐酸或硫酸，因为其具有强螯合能力 3。  
* **组合污染（Complex Fouling）**：实际水体通常是有机-无机复合污染。\*\*“先碱后酸”\*\*是处理地表水的通用黄金法则。碱洗/氧化先把包裹在矿物颗粒外层的有机“胶水”溶掉，暴露出内部的无机晶体，随后的酸洗才能发挥作用。反之，若先酸洗，酸可能无法穿透有机层，且低pH值可能导致腐殖酸胶体更加致密 3。

### **3.2 影响清洗效果的关键因素 (Sinner's Circle)**

用户关心的“温度、时间、流量”是清洗工艺的核心控制变量，需遵循以下规律：

1. **温度 (Temperature)**：**最关键的增效因子**。  
   * **效应**：根据阿伦尼乌斯方程，温度每升高10°C，化学反应速率约增加一倍。同时，高温降低水的粘度，增加湍流程度，利于传质。  
   * **数据支持**：研究显示，将CIP温度从20°C提升至35-40°C，对有机物和生物膜的去除效率可提升50%以上 17。  
   * **限制**：必须低于膜材料的耐受极限（PVDF通常 \< 40-50°C，PVC \< 35°C），防止膜丝收缩或孔径永久变形 19。  
   * **策略**：建议加热清洗液至 **35°C $\\pm$ 2°C**。  
2. **清洗时长 (Duration)**：**非线性收益**。  
   * **效应**：污染物去除呈指数衰减。前30-60分钟去除率最高，随后进入平台期。  
   * **数据支持**：对于NaClO清洗，大部分通量恢复发生在最初的1-2小时内。延长至8小时以上虽然略有提升，但不仅占用产能，还增加膜老化的风险 3。  
   * **策略**：采用动态终止判定（见第6章），而非固定时长。  
3. **清洗流量 (Flow/Flux)**：**剪切力清洗**。  
   * **效应**：高流速（Cross-flow velocity）提供剪切力，带走剥离的污染物。  
   * **策略**：建议采用“浸泡（Soak）- 循环（Recycle）”交替模式。浸泡利用化学扩散作用进入膜孔深处，循环利用水力剪切带走表面滤饼。  
4. **浓度 (Concentration)**：  
   * **效应**：浓度越高反应越快，但存在阈值。对于NaClO，500ppm通常足以应对大多数有机污染；过高（如\>2000ppm）会加速PVDF膜的脱氟降解 19。  
   * **策略**：常规维护清洗（CEB）用低浓度（200-500ppm），恢复性清洗（CIP）用高浓度（500-1000ppm，视厂商手册而定）。

## ---

**4\. “冷启动”条件下的膜污染预判模型构建**

针对用户“没有目标Y值、没有参考标准”的实际困难，单纯的监督学习（Supervised Learning，如回归预测通量）无法实施。本报告提出一套基于\*\*特征工程（Feature Engineering）**与**无监督学习（Unsupervised Learning）\*\*的混合模型架构，解决无标签数据的分类与预判问题。

### **4.1 数据特征工程：构建“虚拟传感器”**

原始数据（压力、流量、时间）本身信息有限，需要转化为反映物理状态的高阶特征。

1. 标准化渗透率 ($K\_{25}$)：

   $$K\_{25} \= \\frac{Q}{TMP} \\cdot e^{0.023 \\times (25 \- T)}$$  
   * **意义**：剔除水温变化对粘度的影响，提取纯粹的膜阻力变化。这是所有判断的基准。  
2. 污堵速率 ($F\_R$)：

   $$F\_R \= \\frac{d(\\text{TMP})}{dt}$$  
   * **意义**：计算一个过滤周期内TMP的上升斜率。斜率陡峭意味着快速堵塞（可能为孔堵塞或高负荷），斜率平缓意味着滤饼层增厚。  
3. 恢复率 ($\\alpha\_{rec}$)：

   $$\\alpha\_{rec} \= \\frac{TMP\_{end, cycle\\\_n} \- TMP\_{start, cycle\\\_n+1}}{TMP\_{end, cycle\\\_n} \- TMP\_{clean}}$$  
   * **意义**：量化物理反洗的效率。如果 $\\alpha\_{rec}$ 持续下降，说明不可逆污染（Irreversible Fouling）正在积累，需要化学清洗介入。  
4. Hermia指数 ($n$)：  
   利用滑动窗口对 $d^2t/dV^2 \= k(dt/dV)^n$ 进行拟合，估算 $n$ 值。  
   * $n \\approx 0$: 滤饼过滤（可逆性高）。  
   * $n \\approx 2$: 完全孔堵塞（风险高，需化学清洗）。

### **4.2 无监督学习模型：污染模式识别**

在没有人工标注“这是有机污染”或“这是无机污染”的情况下，利用聚类算法自动发现数据中的模式。

**算法选择：K-Means 聚类**

* **输入特征**：。  
* **工作原理**：算法将历史运行周期自动分为 $k$ 类（建议 $k=3$ 或 $4$）。  
* **结果解释（人工介入赋予物理意义）**：  
  * *Cluster 1 (高频类)*：浊度高，TMP线性上升，反洗恢复率高 $\\rightarrow$ **定义为：颗粒/胶体污染**。  
  * *Cluster 2 (低频类)*：浊度低，TOC高，TMP指数上升，反洗恢复率低 $\\rightarrow$ **定义为：有机/吸附污染**。  
  * *Cluster 3 (长期趋势)*：基础阻力缓慢爬升，与硬度相关 $\\rightarrow$ **定义为：无机结垢**。  
* **落地价值**：一旦聚类模型训练完成，对于新的实时数据，模型会将其归类到Cluster X，系统即可查表执行对应的清洗策略。

### **4.3 物理信息神经网络 (PINN)：融合机理的预测**

为了弥补纯数据驱动的不足，引入物理约束的神经网络（PINN）。

* **架构**：构建一个预测TMP的神经网络。  
* 损失函数 (Loss Function)：

  $$L \= L\_{data} \+ \\lambda \\cdot L\_{physics}$$

  其中 $L\_{physics}$ 是Hermia方程的残差。  
* **作用**：强迫模型遵循流体力学定律，即使在数据稀缺的情况下，也能给出符合物理规律的预测，并能反向解算出当前的污染阻力分布（滤饼层阻力 vs 孔内阻力）9。

## ---

**5\. 智能清洗干预策略与流程设计**

基于上述分析，针对用户“构建模型分析什么时候冲洗、用什么洗、洗多久”的需求，设计如下可落地的决策逻辑。

### **5.1 干预时机判定 (When to Clean?)**

放弃单纯的时间触发，改为**多重条件触发机制**：

1. **渗透率衰减触发**：  
   * 规则：当标准化渗透率 $K\_{25}$ 下降至初始值（或上次CIP后值）的 **70%-85%** 时，触发清洗 7。  
   * *理由*：此时污染尚处于松散阶段，容易去除；若低于70%，污染物可能发生烧结或压缩，变为永久性污染。  
2. **TMP绝对值触发**：  
   * 规则：TMP \> 1.5 bar (或厂商建议上限的80%)。  
   * *理由*：保护膜丝机械强度。  
3. **异常斜率触发 (Anomaly Detection)**：  
   * 规则：利用LSTM或自动编码器监测实时TMP曲线。如果重构误差（Reconstruction Error）超过3$\\sigma$，说明发生了非预期的快速污染（如进水水质突变），立即触发清洗 5。

### **5.2 清洗剂与工艺决策 (What & How?)**

基于\*\*决策树（Decision Tree）\*\*的逻辑模型（用于PLC编程）：

* **步骤 1：判断污染类型 (基于实时传感器与聚类结果)**  
  * IF (浊度积分值 \> 阈值 AND 反洗恢复率 \> 90%) $\\rightarrow$ **物理污染** $\\rightarrow$ 执行：加强反洗 (Air Scour \+ Water)。  
  * IF (反洗恢复率 \< 85% AND 进水pH/硬度 高) $\\rightarrow$ **无机结垢倾向** $\\rightarrow$ 执行：酸洗 (Citric/HCl)。  
  * IF (反洗恢复率 \< 85% AND TMP呈指数增长 OR TOC高) $\\rightarrow$ **有机/生物污染** $\\rightarrow$ 执行：碱性氧化清洗 (NaOH \+ NaClO)。  
  * **默认兜底策略**：若无法明确区分，或长周期未清洗，执行 **“标准组合清洗”：碱+氧化剂 (35°C, 30min) $\\rightarrow$ 排空 $\\rightarrow$ 酸 (35°C, 30min)**。这已被证明能覆盖最广泛的污染谱系 3。

### **5.3 清洗终止条件 (When to Stop?)**

引入\*\*渗透率平台期（Permeability Plateau）\*\*判定算法，替代固定时长。

* **算法逻辑**：  
  1. 在化学清洗循环过程中，每隔 $t$ 分钟（如5分钟）低压开启产水泵测定一次瞬时渗透率 $K(t)$。  
  2. 计算渗透率恢复速率：$R \= \\frac{K(t) \- K(t-\\Delta t)}{\\Delta t}$。  
  3. **终止判据**：当 $R \< \\epsilon$ （例如，每10分钟恢复率增幅小于1%）时，认为清洗效果已达极限，停止清洗。  
* **优势**：避免“为了洗而洗”，大幅减少停机时间和化学品消耗 8。

## ---

**6\. 工程实施路线图**

### **6.1 硬件与数据基础建设 (Phase 1\)**

* **传感器配置**：必须具备进水/产水压力变送器、进水流量计、温度传感器。强烈建议增加**在线浊度仪**和**pH计**。  
* **数据采集**：建立时序数据库（如InfluxDB），采集频率建议 $\\le 1$分钟/次。  
* **数据清洗**：剔除停机、反洗瞬间的噪点数据，计算 $K\_{25}$。

### **6.2 规则控制试运行 (Phase 2\)**

* 不立即上AI模型。先在SCADA/PLC中写入**5.1**和**5.2**中的规则逻辑。  
  * 设定 $K\_{25}$ 下降15%报警。  
  * 设定简单的逻辑：高浊度 $\\rightarrow$ 加强反洗；高阻力 $\\rightarrow$ 组合化学清洗。  
* **人工标注**：在每次清洗后，记录“清洗前TMP”、“清洗后TMP”、“使用药剂”。这为后续训练AI提供了宝贵的“标签”。

### **6.3 智能化升级 (Phase 3\)**

* **部署K-Means模型**：积累3-6个月数据后，对历史周期进行聚类，识别本水厂特有的污染模式。  
* **部署平台期终止算法**：在清洗程序中加入反馈控制逻辑，实现自适应清洗时长。  
* **持续优化**：利用强化学习（Reinforcement Learning）思路，以“单位产水成本（元/吨）”为奖励函数，微调清洗触发阈值（例如，是降15%洗还是降20%洗最经济？）。

## ---

**7\. 结论**

对于缺乏经验且无历史标注数据的超滤系统，盲目构建复杂的监督学习模型是不可行的。最佳路径是\*\*“机理为本，AI为辅”\*\*：

1. **利用机理**（Hermia模型、Darcy定律）将原始数据转化为具有物理意义的特征（如标准化渗透率、阻力分布）。  
2. **利用无监督AI**（聚类、异常检测）在无标签数据中发现污染模式，建立从“模式”到“清洗配方”的映射关系。  
3. **利用反馈控制**（平台期判定）实现清洗过程的实时优化。

实际操作中，建议优先采纳\*\*“碱性氧化剂（NaClO+NaOH）+ 柠檬酸”\*\*的组合清洗工艺作为基准方案，并利用温度（35-40°C）这一关键杠杆提升效率。通过上述分步实施，项目可实现从粗放式管理向精细化、智能化运维的平稳过渡。

---

引用文献索引：

3 Membranes 2024, 14, 251 (DWTP Cleaning Strategy)

11 General Fouling Types & Mechanisms

9 Physics-Informed ML & Hermia Models

5 Autoencoders & Anomaly Detection

17 Temperature Effects on Cleaning

4 Chemical Cleaning Optimization

1 TMP Profile Analysis

7 Cleaning Triggers & Termination Criteria

6 Clustering & Unsupervised Learning

*(注：报告中提到的具体参数如“下降15%”、“35°C”均为基于文献的行业最佳实践值，在实际工程中应根据膜厂商技术手册进行微调。)*

#### **引用的著作**

1. A Simple Method to Identify the Dominant Fouling Mechanisms during Membrane Filtration Based on Piecewise Multiple Linear Regression \- NIH, 访问时间为 十二月 24, 2025， [https://pmc.ncbi.nlm.nih.gov/articles/PMC7465108/](https://pmc.ncbi.nlm.nih.gov/articles/PMC7465108/)  
2. Generalization and Expansion of the Hermia Model for a Better Understanding of Membrane Fouling \- PMC \- NIH, 访问时间为 十二月 24, 2025， [https://pmc.ncbi.nlm.nih.gov/articles/PMC10056723/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10056723/)  
3. membranes-14-00251.pdf  
4. Fouling and Chemical Cleaning Strategies for Submerged Ultrafiltration Membrane: Synchronized Bench-Scale, Full-Scale, and Engineering Tests \- MDPI, 访问时间为 十二月 24, 2025， [https://www.mdpi.com/2077-0375/14/12/251](https://www.mdpi.com/2077-0375/14/12/251)  
5. Univariate Anomaly Detection in Pressure Data of a Pilot Aerobic Membrane Bioreactor Unit using Long Short-Term Memory Autoencoders \- PubMed, 访问时间为 十二月 24, 2025， [https://pubmed.ncbi.nlm.nih.gov/41386448/?utm\_source=FeedFetcher\&utm\_medium=rss\&utm\_campaign=None\&utm\_content=1JIsr3YNQVWZuOa9b\_nU8v5u4C1lRfY88zxPNb0fH3zJmke5v6\&fc=None\&ff=20251213182332\&v=2.18.0.post22+67771e2](https://pubmed.ncbi.nlm.nih.gov/41386448/?utm_source=FeedFetcher&utm_medium=rss&utm_campaign=None&utm_content=1JIsr3YNQVWZuOa9b_nU8v5u4C1lRfY88zxPNb0fH3zJmke5v6&fc=None&ff=20251213182332&v=2.18.0.post22+67771e2)  
6. (Initial page layout) \- CORE, 访问时间为 十二月 24, 2025， [https://core.ac.uk/download/pdf/55825453.pdf](https://core.ac.uk/download/pdf/55825453.pdf)  
7. Foulants and Cleaning Procedures for composite polyamide RO/NF Membrane Elements \- Hydranautics, 访问时间为 十二月 24, 2025， [https://membranes.com/wp-content/uploads/Documents/TSB/TSB107.pdf](https://membranes.com/wp-content/uploads/Documents/TSB/TSB107.pdf)  
8. Chemical Cleaning of Membranes: Effective Techniques | BIONET, 访问时间为 十二月 24, 2025， [https://bionet.com/expert-references/chemical-cleaning-of-membranes/](https://bionet.com/expert-references/chemical-cleaning-of-membranes/)  
9. Development of physics-informed machine-learning models to enhance understanding and prediction of membrane fouling \- DOI, 访问时间为 十二月 24, 2025， [https://doi.org/10.1016/J.MEMSCI.2025.124133](https://doi.org/10.1016/J.MEMSCI.2025.124133)  
10. Two classical fouling-developing theories: (a) intermediate-blocking... \- ResearchGate, 访问时间为 十二月 24, 2025， [https://www.researchgate.net/figure/Two-classical-fouling-developing-theories-a-intermediate-blocking-theory-and-b-cake\_fig1\_352435456](https://www.researchgate.net/figure/Two-classical-fouling-developing-theories-a-intermediate-blocking-theory-and-b-cake_fig1_352435456)  
11. Membrane Fouling: Common Causes, Types, and Remediation \- Kurita America, 访问时间为 十二月 24, 2025， [https://www.kuritaamerica.com/the-splash/membrane-fouling-common-causes-types-and-remediation](https://www.kuritaamerica.com/the-splash/membrane-fouling-common-causes-types-and-remediation)  
12. How Membrane Fouling Affects Ultrafiltration Systems \- Clean Tech Water, 访问时间为 十二月 24, 2025， [https://www.cleantechwater.co.in/impact-membrane-fouling-ultrafiltration-efficiency-industrial-wastewater/](https://www.cleantechwater.co.in/impact-membrane-fouling-ultrafiltration-efficiency-industrial-wastewater/)  
13. Outlining the Roles of Membrane-Foulant and Foulant-Foulant Interactions in Organic Fouling During Microfiltration and Ultrafiltration: A Mini-Review \- Frontiers, 访问时间为 十二月 24, 2025， [https://www.frontiersin.org/journals/chemistry/articles/10.3389/fchem.2020.00417/full](https://www.frontiersin.org/journals/chemistry/articles/10.3389/fchem.2020.00417/full)  
14. Four types of Membrane Fouling, 访问时间为 十二月 24, 2025， [https://www.membrane-solutions.com/news\_1224.htm](https://www.membrane-solutions.com/news_1224.htm)  
15. Fouling and Chemical Cleaning Strategies for Submerged Ultrafiltration Membrane: Synchronized Bench-Scale, Full-Scale, and Engineering Tests \- ResearchGate, 访问时间为 十二月 24, 2025， [https://www.researchgate.net/publication/386160768\_Fouling\_and\_Chemical\_Cleaning\_Strategies\_for\_Submerged\_Ultrafiltration\_Membrane\_Synchronized\_Bench-Scale\_Full-Scale\_and\_Engineering\_Tests](https://www.researchgate.net/publication/386160768_Fouling_and_Chemical_Cleaning_Strategies_for_Submerged_Ultrafiltration_Membrane_Synchronized_Bench-Scale_Full-Scale_and_Engineering_Tests)  
16. Optimization of Membrane Cleaning Strategy for Advanced Treatment of Polymer Flooding Produced Water by Nanofiltration | Request PDF \- ResearchGate, 访问时间为 十二月 24, 2025， [https://www.researchgate.net/publication/297657481\_Optimization\_of\_Membrane\_Cleaning\_Strategy\_for\_Advanced\_Treatment\_of\_Polymer\_Flooding\_Produced\_Water\_by\_Nanofiltration](https://www.researchgate.net/publication/297657481_Optimization_of_Membrane_Cleaning_Strategy_for_Advanced_Treatment_of_Polymer_Flooding_Produced_Water_by_Nanofiltration)  
17. TSG-C-001 Membrane Cleaning Guide \- Water Application Elements, 访问时间为 十二月 24, 2025， [https://water-membrane-solutions.mann-hummel.com/content/dam/lse-wfs/product-related-assets/manuals-guides/TSG-C-001-Membrane-Cleaning-Guide-Water-Application-Elements.pdf](https://water-membrane-solutions.mann-hummel.com/content/dam/lse-wfs/product-related-assets/manuals-guides/TSG-C-001-Membrane-Cleaning-Guide-Water-Application-Elements.pdf)  
18. Influencing factors of ultrafiltration flux \- chiwatec, 访问时间为 十二月 24, 2025， [https://cnchiwatec.com/influencing-factors-of-ultrafiltration-flux.html](https://cnchiwatec.com/influencing-factors-of-ultrafiltration-flux.html)  
19. TSG-C-004 Membrane Cleaning Guide Food & Dairy UF & MF, 访问时间为 十二月 24, 2025， [https://s7g10.scene7.com/is/content/mannhummel/turboclean-food-dairy-uf-mf-elements-membrane-cleaning-guidepdf](https://s7g10.scene7.com/is/content/mannhummel/turboclean-food-dairy-uf-mf-elements-membrane-cleaning-guidepdf)  
20. Choose A Proper Cleaning Agent for UF Membrane Chemical Cleaning \- Snowate, 访问时间为 十二月 24, 2025， [https://www.snowate.com/parts/membrane/supports/uf-membrane-cleaning.html](https://www.snowate.com/parts/membrane/supports/uf-membrane-cleaning.html)  
21. Membrane chemical cleaning: why is it required and how is it performed? \- Sterlitech Corporation, 访问时间为 十二月 24, 2025， [https://www.sterlitech.com/blog/post/membrane-chemical-cleaning](https://www.sterlitech.com/blog/post/membrane-chemical-cleaning)  
22. Membrane fouling \- Wikipedia, 访问时间为 十二月 24, 2025， [https://en.wikipedia.org/wiki/Membrane\_fouling](https://en.wikipedia.org/wiki/Membrane_fouling)  
23. Development of physics-informed machine-learning models to enhance understanding and prediction of membrane fouling \- research.chalmers.se, 访问时间为 十二月 24, 2025， [https://research.chalmers.se/en/publication/546258](https://research.chalmers.se/en/publication/546258)  
24. Factors that Affect the Performance of Reverse Osmosis Membrane Filters \- Membracon, 访问时间为 十二月 24, 2025， [https://www.membracon.co.uk/blog/factors-that-affect-the-performance-of-reverse-osmosis-membrane-filters/](https://www.membracon.co.uk/blog/factors-that-affect-the-performance-of-reverse-osmosis-membrane-filters/)  
25. \[2305.01539\] Jacobian-Scaled K-means Clustering for Physics-Informed Segmentation of Reacting Flows \- arXiv, 访问时间为 十二月 24, 2025， [https://arxiv.org/abs/2305.01539](https://arxiv.org/abs/2305.01539)