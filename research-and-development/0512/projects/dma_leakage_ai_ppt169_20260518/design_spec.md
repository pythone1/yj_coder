# dma_leakage_ai - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | dma_leakage_ai |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 23 pages |
| **Design Style** | General Consulting with high-visual engineering illustration |
| **Target Audience** | 智慧水务项目汇报对象、管理层、工程技术团队 |
| **Use Case** | “机理、算法与实践：人工智能行业应用实证分析”专题汇报 |
| **Created Date** | 2026-05-18 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280x720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 48px, top 86px after header, bottom 46px |
| **Content Area** | 1184x568 |

---

## III. Visual Theme

### Theme Style

- **Style**: 模板蓝灰规范底座 + Fluid 粗版的白底科技插图感。
- **Theme**: Light theme.
- **Tone**: 专业、工程化、智慧水务、可落地。
- **Mandatory brand behavior**: Every generated page keeps the template logo at top-right. Pages 1-4 are preserved as full-slide template backgrounds.

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#EEF6FC` | New page background |
| **Header blue-gray** | `#7589A0` | Template-style top bar |
| **Primary blue** | `#4997D9` | Key titles, chart lines, model nodes |
| **Deep blue** | `#1E4E78` | Main assertions and diagram labels |
| **Light panel** | `#EAF5FC` | Soft callout panels |
| **Accent orange** | `#DB8B2A` | Leak anomaly, high risk, physical-model highlight |
| **Success green** | `#2A9774` | Governance, closed-loop, feedback |
| **Warning red** | `#CC4242` | Top-N risk / critical warning |
| **Body text** | `#111827` | Main text |
| **Secondary text** | `#53657D` | Subtitle and notes |
| **Border/divider** | `#B8D5EA` | Thin dividers and soft containers |
| **White** | `#FFFFFF` | Cards and image scrims |

### Gradient Scheme

Use restrained gradients only for scrims over Fluid images:

```xml
<linearGradient id="softBlueScrim" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stop-color="#EEF6FC" stop-opacity="0.95"/>
  <stop offset="70%" stop-color="#EEF6FC" stop-opacity="0.20"/>
  <stop offset="100%" stop-color="#EEF6FC" stop-opacity="0"/>
</linearGradient>
```

---

## IV. Typography System

### Font Plan

**Typography direction**: CJK-primary modern sans, strong title weights, clean engineering labels.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Body** | `"Microsoft YaHei"` | `Arial` | `sans-serif` |
| **Emphasis** | `SimHei` | `Arial Black` | `sans-serif` |
| **Code** | - | `Consolas`, `"Courier New"` | `monospace` |

**Per-role font stacks**

- Title: `"Microsoft YaHei", Arial, sans-serif`
- Body: `"Microsoft YaHei", Arial, sans-serif`
- Emphasis: `SimHei, "Arial Black", "Microsoft YaHei", sans-serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

**Baseline**: Body font size = 18px.

| Purpose | Size |
| ------- | ---- |
| Cover title | 44-62px |
| Section / chapter title | 34-42px |
| Page title | 30-36px |
| Subtitle | 21-24px |
| Body content | 18px |
| Diagram labels | 14-18px |
| Footer/page number | 10-12px |

---

## V. Layout Principles

### Page Structure

- **Header area**: 70px high blue-gray band, page title left, small section chip and logo right.
- **Content area**: 86px to 660px, flexible. Favor large images and cleaned labels from Fluid.
- **Footer area**: 20-40px for page number or key takeaway. Avoid heavy footers except section openers.

### Layout Pattern Library

- Preserve pages 1-4: full-slide image backgrounds.
- Cover / transition: full-bleed or dominant Fluid illustration with scrim and large title.
- Mechanism pages: asymmetric image-led layouts, not card grids.
- Algorithm pages: matrix/table only when needed.
- Process pages: pipeline, flywheel, stair-step, and hub-spoke diagrams.
- Dense pages: use clean tables, restrained cards, and visible hierarchy.

### Spacing Specification

| Element | Current Project |
| ------- | --------------- |
| Safe margin from canvas edge | 48px |
| Content block gap | 28-42px |
| Icon-text gap | 10-14px |
| Card gap | 24px |
| Card padding | 22px |
| Card border radius | 14-24px |

---

## VI. Icon Usage Specification

### Source

- **Built-in icon library**: `phosphor-duotone`
- **Usage method**: SVG placeholder `<use data-icon="phosphor-duotone/icon-name"/>`
- Icons are supporting marks only. Fluid images and custom diagrams are the main visuals.

### Recommended Icon List

| Purpose | Icon Path | Page |
| ------- | --------- | ---- |
| Dynamic baseline | `phosphor-duotone/wave-sine` | 10 |
| Data / feature store | `phosphor-duotone/database` | 9, 17 |
| Risk warning | `phosphor-duotone/warning-circle` | 10, 12 |
| Model engine | `phosphor-duotone/brain` | 8, 18 |
| Governance / closed loop | `phosphor-duotone/check-circle` | 20 |
| Topology / graph | `phosphor-duotone/share-network` | 14 |
| Target / Top-N | `phosphor-duotone/target` | 13 |
| Operation flywheel | `phosphor-duotone/arrows-clockwise` | 21 |
| List / matrix | `phosphor-duotone/list-checks` | 15 |
| Time / drift | `phosphor-duotone/clock-clockwise` | 21 |

---

## VII. Visualization Reference List

Catalog read: 70 templates / 10 categories

Per-page selection:

- P06 timeline | summary-quote: "Pick for 3-8 milestone events on a horizontal time axis (no duration)."
- P07 layered_architecture | summary-quote: "Pick for 3-4 horizontal architecture layers (e.g. presentation/service/data), 2-4 module cards per layer."
- P08 process_flow | summary-quote: "Pick for 3-8 sequential steps connected by simple arrows."
- P09 hub_spoke | summary-quote: "Pick for 1 core capability + 4-8 surrounding capabilities (platform/ecosystem)."
- P10 line_chart | summary-quote: "Pick for 1-3 time-series on a continuous axis showing direction."
- P13 pipeline_with_stages | summary-quote: "Pick for 3-5 stage horizontal pipeline where each stage = title + 1-line description + output artifact, connected by directional arrows."
- P15 comparison_table | summary-quote: "Pick for 2-4 plans/products compared across many feature rows (dense matrix)."
- P16 numbered_steps | summary-quote: "Pick for 3-6 horizontal sequential steps with numeric emphasis."
- P18 isometric_stairs | summary-quote: "Pick for 4-7 ascending stages emphasizing growth/maturity progression visually."
- P20 chevron_process | summary-quote: "Pick for 3-6 phase methodology with chunky arrow-chain progression and deliverables per phase."
- P21 flywheel_diagram | summary-quote: "Pick for circular self-reinforcing growth loop where each stage compounds the next (e.g. Attract -> Engage -> Delight)."

Runners-up considered:

- cycle_diagram | rejected for P21: the operation loop is self-reinforcing through accumulated labels and retraining, not just a closed cycle.
- icon_grid | rejected for P17: five core data tables require governance requirements and usage descriptions, not just parallel feature labels.
- process_flow | rejected for P18: model training path is an ascending maturity progression, so isometric_stairs better captures increasing capability.
- basic_table | rejected for P15: algorithm matrix is strategic comparison with selected tasks and outputs, so comparison_table is stronger.

| Visualization Type | Reference Template | Used In |
| ------------------ | ------------------ | ------- |
| timeline | `templates/charts/timeline.svg` | P06 |
| layered_architecture | `templates/charts/layered_architecture.svg` | P07 |
| process_flow | `templates/charts/process_flow.svg` | P08 |
| hub_spoke | `templates/charts/hub_spoke.svg` | P09 |
| line_chart | `templates/charts/line_chart.svg` | P10 |
| pipeline_with_stages | `templates/charts/pipeline_with_stages.svg` | P13 |
| comparison_table | `templates/charts/comparison_table.svg` | P15 |
| numbered_steps | `templates/charts/numbered_steps.svg` | P16 |
| isometric_stairs | `templates/charts/isometric_stairs.svg` | P18 |
| chevron_process | `templates/charts/chevron_process.svg` | P20 |
| flywheel_diagram | `templates/charts/flywheel_diagram.svg` | P21 |

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Acquire Via | Status | Reference |
| -------- | ---------- | ----- | ------- | ---- | ----------- | ------ | --------- |
| template_full_slide_01.png | 1280x720 | 1.78 | Preserve original slide 1 | Background | user | Existing | Template first slide |
| template_full_slide_02.png | 1280x720 | 1.78 | Preserve original slide 2 | Background | user | Existing | Template second slide |
| template_full_slide_03.png | 1280x720 | 1.78 | Preserve original slide 3 | Background | user | Existing | Template third slide |
| template_full_slide_04.png | 1280x720 | 1.78 | Preserve original slide 4 | Background | user | Existing | Template fourth slide |
| template_slide_01_image_01.png | 192x192 | 1.00 | Logo on every new page | Decorative | user | Existing | Template logo |
| fluid_slide_01_image_01.jpg | 2752x1536 | 1.79 | Topic cover / opening image | Illustration | user | Existing | Isometric blue water pipe network |
| fluid_slide_03_image_07.png | 2752x1536 | 1.79 | DMA layered model visual | Diagram | user | Existing | Physical/sensing/intelligence layer |
| fluid_slide_04_image_08.png | 2752x1536 | 1.79 | Feature fusion / agent visual | Diagram | user | Existing | Multisource feature fusion |
| fluid_slide_08_image_13.png | 2752x1536 | 1.79 | Dynamic baseline curve visual | Diagram | user | Existing | Prediction interval and actual flow |
| fluid_slide_09_image_17.png | 2752x1536 | 1.79 | Unsupervised anomaly visual | Diagram | user | Existing | Clustering and outlier idea |
| fluid_slide_10_image_20.png | 2752x1536 | 1.79 | Pipe risk ranking visual | Diagram | user | Existing | Risk factors and tree model |
| fluid_slide_11_image_21.jpg | 2752x1536 | 1.79 | Physics + data fusion visual | Diagram | user | Existing | Hydraulic model and AI fusion |
| fluid_slide_12_image_22.jpg | 2752x1536 | 1.79 | GNN / knowledge graph visual | Diagram | user | Existing | Network topology and graph |
| fluid_slide_15_image_25.jpg | 2752x1536 | 1.79 | Data governance visual | Diagram | user | Existing | Five tables and governance engine |
| fluid_slide_16_image_26.jpg | 2752x1536 | 1.79 | Four-step model building visual | Diagram | user | Existing | Progressive model training |
| fluid_slide_17_image_27.jpg | 2752x1536 | 1.79 | Model validation visual | Diagram | user | Existing | Algorithm vs business metrics |
| fluid_slide_18_image_32.jpg | 2752x1536 | 1.79 | Engineering landing visual | Diagram | user | Existing | Warning / convergence / action |
| fluid_slide_19_image_33.png | 2752x1536 | 1.79 | Work order feedback visual | Diagram | user | Existing | Structured work order feedback |
| fluid_slide_20_image_34.jpg | 2752x1536 | 1.79 | Operation flywheel visual | Diagram | user | Existing | Drift monitoring and iteration |
| fluid_slide_21_image_35.jpg | 2752x1536 | 1.79 | Closing summary visual | Illustration | user | Existing | Digital pipe organism |

---

## IX. Content Outline

### Part 1: Existing Template Pages

#### Slide 01 - 人工智能的诞生
- **Layout**: preserved full-slide template image.
- **Content**: no change.

#### Slide 02 - 人工智能的发展
- **Layout**: preserved full-slide template image.
- **Content**: no change.

#### Slide 03 - 人工智能的构成
- **Layout**: preserved full-slide template image.
- **Content**: no change.

#### Slide 04 - 2025-2026，应用时代来临
- **Layout**: preserved full-slide template image.
- **Content**: no change.

### Part 2: Topic Opening

#### Slide 05 - 从“AI应用时代”切入智慧水务
- **Layout**: figure-text overlap using Fluid pipe illustration.
- **Visualization**: no-template-match; image-led transition.
- **Content**:
  - AI的价值落点不是算法展示，而是可执行的水务工程指令。
  - DMA漏损检测是“数据、机理、业务闭环”同时成立的典型场景。

#### Slide 06 - 漏损识别从固定规则走向融合智能
- **Layout**: horizontal timeline.
- **Visualization**: timeline.
- **Content**:
  - 人工经验 -> 固定阈值 -> 统计/机器学习 -> 深度时序 -> 融合智能。
  - 升级动因：从“发现异常”走向“定位、处置、复盘”。

#### Slide 07 - DMA是AI建模的基本业务单元
- **Layout**: layered architecture with Fluid image as soft background.
- **Visualization**: layered_architecture.
- **Content**:
  - 感知层、数据层、模型层、业务层。
  - DMA锁定片区，AI完成动态基线、异常识别、候选定位和风险排序。

#### Slide 08 - AI模型有四个关键接入点
- **Layout**: process flow.
- **Visualization**: process_flow.
- **Content**:
  - 动态基线、异常识别、候选定位、工单闭环。
  - 输出异常时段、疑似原因、候选管段、定位置信度、复核方式。

#### Slide 09 - 多源特征融合让漏损异常可解释
- **Layout**: hub-spoke around DMA risk evidence chain.
- **Visualization**: hub_spoke.
- **Content**:
  - 运行时序、时间上下文、空间资产、历史事件、业务状态。
  - 从单点超限转向证据链判断。

### Part 3: Algorithms And Mechanism

#### Slide 10 - 动态基线用残差识别真实漏损
- **Layout**: Fluid curve visual + cleaned decision logic.
- **Visualization**: line_chart.
- **Content**:
  - LSTM/GRU输出预测区间和残差序列。
  - 夜间实际流量持续高于预测上界且伴随压力响应时，触发高置信度预警。

#### Slide 11 - 少标签阶段先筛查，再沉淀黄金标签
- **Layout**: three algorithm capsules + feedback rail.
- **Visualization**: no-template-match; custom anomaly detection layout.
- **Content**:
  - 孤立森林、DBSCAN、自编码器。
  - 统计异常必须经人工复核并回填为标签。

#### Slide 12 - 资产与历史工单驱动管段风险排序
- **Layout**: Fluid risk-ranking illustration + factor stack.
- **Visualization**: no-template-match; image-led risk ranking.
- **Content**:
  - 管龄、材质、口径、压力、道路、维修次数、投诉频次。
  - 输出管段风险分、风险等级、巡检和改造优先级。

#### Slide 13 - 机理融合把DMA异常收敛到候选管段
- **Layout**: data side + physics side + central Top-N pipeline.
- **Visualization**: pipeline_with_stages.
- **Content**:
  - 水力模型提供拓扑、压力传播、漏点敏感性。
  - 机器学习快速匹配异常响应，形成候选管段Top-N。

#### Slide 14 - GNN与知识图谱从点线检测走向全局洞察
- **Layout**: topology / knowledge graph split.
- **Visualization**: no-template-match; graph relationship diagram.
- **Content**:
  - GNN纳入管网拓扑邻接关系和压力传播机制。
  - 知识图谱组织DMA、管段、设备、工单、投诉和维修证据。

#### Slide 15 - 算法选型矩阵：任务决定模型
- **Layout**: comparison table.
- **Visualization**: comparison_table.
- **Content**:
  - 动态基线、异常识别、候选定位、分区优化、智能决策。
  - 每类任务对应推荐算法和上线输出。

### Part 4: Implementation And Operation

#### Slide 16 - 实施路径采用试点先行、分步推广
- **Layout**: numbered steps.
- **Visualization**: numbered_steps.
- **Content**:
  - 短期基础预警，中期闭环定位，长期全生命周期管理。
  - 试点选择边界清晰、计量可靠、压力点完整、工单较多的DMA。

#### Slide 17 - 数据治理底座决定模型上限
- **Layout**: five data table modules around governance engine.
- **Visualization**: no-template-match; data governance diagram.
- **Content**:
  - 设备表、管网表、时序表、工单表、标签表。
  - 统一编码、时间对齐、拓扑校验、工单结构化。

#### Slide 18 - 模型建设遵循四步阶梯训练法
- **Layout**: ascending staircase.
- **Visualization**: isometric_stairs.
- **Content**:
  - 基础预警、动态残差、交叉验证、定位收敛。
  - 先可用，再提升定位精度和闭环能力。

#### Slide 19 - 模型验证要跨越算法与业务
- **Layout**: two-column validation split.
- **Visualization**: no-template-match; metric split layout.
- **Content**:
  - 算法指标：MAE、RMSE、F1、AUC、残差稳定性。
  - 业务指标：复核命中率、Top-N命中率、平均排查范围、闭环时间。

#### Slide 20 - 工程落地必须进入现场作业流
- **Layout**: chevron process.
- **Visualization**: chevron_process.
- **Content**:
  - 预警、收敛、派单、核查、维修、复盘。
  - SCADA供实时流压，GIS供拓扑定位，工单系统承接闭环。

#### Slide 21 - 长效运营依赖漂移监控与持续进化飞轮
- **Layout**: flywheel.
- **Visualization**: flywheel_diagram.
- **Content**:
  - Daily异常监控、Weekly现场回填、Quarterly漂移评估、Bi-Annually再训练。
  - 模型不是一次性成果，而是日常管网管理能力。

### Part 5: Closing

#### Slide 22 - 结论：AI价值是可解释的工程指令
- **Layout**: four conclusion anchors with Fluid closing image.
- **Visualization**: no-template-match; summary layout.
- **Content**:
  - 业务牵引、数据底座、算法引擎、闭环运营。
  - DMA锁定异常片区，AI形成动态证据链，工程闭环兑现降漏价值。

#### Slide 23 - 参考资料
- **Layout**: clean reference list.
- **Visualization**: basic_table.
- **Content**:
  - EPANET 2.2, NIST AI RMF, LSTM, GRU, Isolation Forest, DBSCAN, Random Forest, GBDT, GA.

---

## X. Speaker Notes Requirements

- Total presentation duration: 18-25 minutes.
- Notes style: formal, concise, conclusion-first.
- Purpose: report and persuade; support a formal engineering application presentation.
- File naming: match SVG names, e.g. `01_template_intro.md`.
- `notes/total.md` will use headings; split note files must not include heading lines.

---

## XI. Technical Constraints Reminder

1. viewBox: `0 0 1280 720`.
2. Background uses `<rect>` elements.
3. Text wrapping uses `<tspan>`; `<foreignObject>` forbidden.
4. Use `fill-opacity` / `stroke-opacity`, not `rgba()`.
5. Forbidden: `<style>`, `class`, `textPath`, `animate*`, `script`, `iframe`.
6. No `<g opacity>`.
7. Every new page uses `template_slide_01_image_01.png` logo at top-right.
8. Pages 1-4 use full-slide images and should not be redesigned.
