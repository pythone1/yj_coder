# yangjia_dma_ai_rebuild_v9 - Design Spec

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | yangjia_dma_ai_rebuild_v9 |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 20 slides |
| **Design Style** | Top consulting, technical presentation, clean water-industry visual language |
| **Target Audience** | 水务企业管理层、技术负责人、运维负责人、外部交流对象 |
| **Use Case** | AI 供水管网 DMA 漏损检测应用汇报 |
| **Created Date** | 2026-05-14 |

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280x720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | 50px left/right, 42px top, 36px bottom |
| **Content Area** | 1180x610 |

## III. Visual Theme

### Theme Style

- **Style**: 结论先行、技术可信、业务闭环清晰。
- **Theme**: 深蓝封面与章节页，浅色内容页。
- **Tone**: 水务基础设施、AI 模型、工程落地结合。

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#F7FAFC` | Main content background |
| **Dark background** | `#062E5F` | Cover and section opener |
| **Panel** | `#FFFFFF` | Text blocks and diagrams |
| **Soft panel** | `#EEF6FB` | Secondary bands |
| **Primary** | `#0059B3` | Titles, major lines |
| **Accent** | `#00A6D6` | AI/data highlights |
| **Secondary accent** | `#F28C28` | Leak/risk/emergency emphasis |
| **Body text** | `#102033` | Main text |
| **Secondary text** | `#5D7186` | Captions |
| **Border** | `#B9D9ED` | Light dividers |

## IV. Typography System

### Font Plan

**Typography direction**: CJK-primary technical sans, enlarged for projection.

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | SimHei, Microsoft YaHei | Arial | sans-serif |
| **Body** | Microsoft YaHei | Arial | sans-serif |
| **Emphasis** | SimSun | Georgia | serif |
| **Code** | - | Consolas, Courier New | monospace |

**Per-role font stacks**

- Title: `SimHei, Microsoft YaHei, sans-serif`
- Body: `Microsoft YaHei, Arial, sans-serif`
- Emphasis: `Georgia, SimSun, serif`
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy

Baseline body size is 22px. Page titles use 36-40px, section openers 48px, cover title 54px, annotations 16px. Body text is kept at 20-24px; no dense page uses micro text as primary content.

## V. Layout Principles

### Page Structure

- **Header area**: 42-96px, title plus short section label, no explanatory filler.
- **Content area**: 560px, large visual anchor plus editable PPT text/diagram layer.
- **Footer area**: 26px, compact deck label and page number.

### Layout Pattern Library

Use varied structures: cover split with hero visual, roadmap, timeline, architecture, comparison matrix, pipeline, lifecycle loop, implementation roadmap, and closing synthesis. Avoid repeated four-card pages.

### Spacing Specification

- Safe margin: 50px.
- Primary block gap: 28-42px.
- Card padding: 18-24px.
- Rounded rectangles: 8-14px.
- Image crops: only where the image is decorative; architecture images are no-crop.

## VI. Icon Usage Specification

### Source

Built-in `chunk-filled` library. Icons are secondary; the deck relies on clean editable shapes, lines, image panels, and large text.

### Recommended Icon List

`arrow-right`, `arrow-trend-up`, `brain`, `chart-line`, `database`, `faucet-drip`, `gear`, `location-dot`, `magnifying-glass`, `network-wired`, `route`, `server`, `shield`, `signal`, `sitemap`, `water`, `wrench`.

## VII. Visualization Reference List

Catalog read: 70 templates / 10 categories.

Per-page selection:
- P03 `timeline` | summary-quote: "Pick for 3-8 milestone events on a horizontal time axis (no duration). Skip for tasks with start/end ranges (use gantt_chart) or vertical layout (use roadmap_vertical)."
- P05 `comparison_table` | summary-quote: "Pick for 2-4 plans/products compared across many feature rows (dense matrix). Skip for pricing-tier marketing layout (use comparison_columns)."
- P06 `layered_architecture` | summary-quote: "Pick for 3-4 horizontal architecture layers (e.g. presentation/service/data), 2-4 module cards per layer. Each module card MUST carry title + 1-line capability description — do not omit description even when source is brief. Skip if no per-module descriptions are available (use icon_grid) or no horizontal layering (use module_composition)."
- P10 `process_flow` | summary-quote: "Pick for 3-8 sequential steps connected by simple arrows. Skip if cyclical (use cycle_diagram) or stages produce named outputs (use pipeline_with_stages)."
- P13 `cycle_diagram` | summary-quote: "Pick for 4-6 stage closed loop with no clear start/end (e.g. PDCA). Skip for self-reinforcing growth loop (use flywheel_diagram) or linear flow (use process_flow)."
- P15 `numbered_steps` | summary-quote: "Pick for 3-6 horizontal sequential steps with numeric emphasis. Skip if steps need connector arrows (use process_flow) or named output artifacts (use pipeline_with_stages)."

Runners-up considered:
- `icon_grid` rejected: insufficient for algorithm mechanism and business value mapping.
- `agenda_list` rejected: would produce overly empty section pages.
- `comparison_columns` rejected: better for service tiers, not algorithm selection.

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Status | Generation Description |
| -------- | ---------- | ----- | ------- | ---- | ------ | ---------------------- |
| cover_clean.png | 1448x1086 | 1.33 | Cover hero image | Illustration | Existing | Existing generated water-AI scene |
| dma_ai_positioning_full.png | 1672x941 | 1.78 | DMA+AI positioning architecture | Diagram | Existing | Existing generated architecture |
| dynamic_baseline_full.png | 1672x941 | 1.78 | LSTM/GRU baseline explanation | Diagram | Existing | Existing generated architecture |
| data_training_full.png | 1672x941 | 1.78 | Data/model training pipeline | Diagram | Existing | Existing generated architecture |
| overall_architecture.png | 1672x941 | 1.78 | Overall platform architecture | Diagram | Existing | Existing generated architecture |
| algorithm_combo.png | 1672x941 | 1.78 | Algorithm family overview | Diagram | Existing | Existing generated architecture |
| implementation_path.png | 1672x941 | 1.78 | Implementation path | Diagram | Existing | Existing generated architecture |
| workorder_no_person.png | 1672x941 | 1.78 | Work order closed loop | Diagram | Existing | Existing generated architecture |

## IX. Content Outline

### Part 1: AI model development

#### Slide 01 - AI模型在供水管网DMA系统漏损检测中的应用
- **Layout**: Dark cover, large title, hero visual on right, three compact tags.
- **Content**: Topic, scope, three-part narrative.

#### Slide 02 - 本部分解决三个问题
- **Layout**: Three-column agenda with bottom logic line.
- **Content**: 发展逻辑、核心技术、实施路径.

#### Slide 03 - AI应用从规则判别走向闭环智能
- **Visualization**: timeline.
- **Content**: 阈值规则、统计模型、机器学习、深度学习、智能体协同.

#### Slide 04 - 智能体承担模型编排与业务协同
- **Layout**: Architecture image plus editable four-layer agent stack.
- **Content**: 数据感知、模型推理、工具调用、工单反馈.

#### Slide 05 - 算法选型取决于数据形态与业务动作
- **Visualization**: comparison_table.
- **Content**: 时序预测、异常识别、水力融合、决策排序.

#### Slide 06 - DMA宏观锁定与AI微观溯源形成定位闭环
- **Visualization**: layered_architecture.
- **Content**: DMA分区计量、多源融合、AI溯源、现场闭环.

### Part 2: Core AI technologies and value

#### Slide 07 - 2.2 核心AI技术及业务价值
- **Layout**: Dark section opener with three pillars.

#### Slide 08 - LSTM/GRU建立动态基线，识别夜间流量异常
- **Layout**: Generated architecture image plus editable callouts.
- **Content**: 周期特征、突变响应、残差评分、预警输出.

#### Slide 09 - 无监督异常检测适合低标签漏损场景
- **Layout**: Three mechanism panels.
- **Content**: 孤立森林、DBSCAN、自编码器.

#### Slide 10 - 水力模型融合把异常信号转化为候选管段
- **Visualization**: process_flow.
- **Content**: 参数校核、仿真样本库、特征匹配、候选排序.

#### Slide 11 - GA、RF、GBT分别解决校核、分类与高噪声排序
- **Layout**: Algorithm comparison matrix.
- **Content**: 适用输入、输出、优势、工程注意点.

#### Slide 12 - 多源数据融合支撑从预警到决策的业务闭环
- **Layout**: Data pipeline image plus editable data layers.
- **Content**: SCADA/GIS/工单/巡检/资产.

#### Slide 13 - 业务价值落在四类可执行动作
- **Visualization**: cycle_diagram.
- **Content**: 预警分级、定位优先级、巡检路径、改造排序.

### Part 3: Implementation path

#### Slide 14 - 第四部分 实施路径
- **Layout**: Dark section opener, implementation path visual.

#### Slide 15 - 4.1 前期规划先明确目标与边界
- **Visualization**: numbered_steps.
- **Content**: 现状诊断、目标设定、试点边界、阶段推进.

#### Slide 16 - 4.2 数据治理决定模型上限
- **Layout**: Data governance pipeline.
- **Content**: 多源归集、清洗标准、标签体系、中台服务.

#### Slide 17 - 4.3 模型建设采用“选型-训练-验证-上线-迭代”
- **Layout**: Training workflow with evaluation gates.
- **Content**: 场景拆解、样本构建、鲁棒验证、漂移监测.

#### Slide 18 - 4.4 工程落地以端边云协同承接实时性与算力
- **Layout**: Edge-cloud architecture.
- **Content**: 设备接入、边缘识别、云端训练、系统集成.

#### Slide 19 - 4.5 长效运营把模型纳入常态运维
- **Layout**: Work order loop and role responsibility table.
- **Content**: 分层能力、模型监控、硬件维护、安全治理.

#### Slide 20 - 收束：AI漏损检测的落地判断标准
- **Layout**: Three conclusion blocks plus visual strip.
- **Content**: 数据可信、模型可解释、闭环可执行.

## X. Speaker Notes Requirements

Speaker notes saved in `notes/total.md`, one `# Slide NN` heading per page. Notes are direct presentation content only and avoid meta-instruction wording.

## XI. Technical Constraints Reminder

SVG viewBox must be `0 0 1280 720`; no `<style>`, no `class`, no `<foreignObject>`, no `rgba()`, no group opacity. Text uses SVG `<text>` and `<tspan>`. All images referenced from `images/` and architecture diagrams use no-crop placement.
