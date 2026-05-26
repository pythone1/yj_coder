const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const root = "E:/PY/research";
const outDir = path.join(root, "output/ppt");
fs.mkdirSync(outDir, { recursive: true });

const templateDir = path.join(root, "tmp/template_pdf_pages");
const bgCover = path.join(templateDir, "template_page_1.png");
const bgContents = path.join(templateDir, "template_page_2.png");
const bgBody = path.join(templateDir, "template_page_4.png");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.subject = "今世缘酒业生产模块AI工艺实施方案";
pptx.title = "今世缘酒业生产模块AI工艺实施方案";
pptx.company = "南大五维";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";
pptx.margin = 0;

const C = {
  blue: "075699",
  deep: "083F73",
  mid: "2F80ED",
  cyan: "15AFC8",
  green: "22A06B",
  orange: "F59E0B",
  red: "D94B4B",
  purple: "6256C7",
  ink: "17324D",
  muted: "5B677A",
  line: "BFD3E5",
  pale: "F5FAFE",
  white: "FFFFFF",
};

function addBg(slide, type = "body") {
  const img = type === "cover" ? bgCover : type === "contents" ? bgContents : bgBody;
  slide.addImage({ path: img, x: 0, y: 0, w: 13.333, h: 7.5 });
}

function addText(slide, text, x, y, w, h, opt = {}) {
  slide.addText(text, {
    x, y, w, h,
    margin: opt.margin ?? 0.02,
    fit: "shrink",
    fontFace: "Microsoft YaHei",
    fontSize: opt.size ?? 16,
    bold: opt.bold ?? false,
    color: opt.color ?? C.ink,
    valign: opt.valign ?? "top",
    align: opt.align ?? "left",
    breakLine: false,
    paraSpaceAfterPt: opt.after ?? 0,
    ...opt.extra,
  });
}

function title(slide, text, sub = "") {
  slide.addShape(pptx.ShapeType.rect, { x: 0.25, y: 0.22, w: 9.7, h: 0.65, fill: { color: C.white }, line: { color: C.white } });
  addText(slide, text, 0.38, 0.28, 9.4, 0.45, { size: 24, bold: true, color: C.deep });
  slide.addShape(pptx.ShapeType.line, { x: 0.38, y: 0.9, w: 12.3, h: 0, line: { color: C.deep, width: 1.4 } });
  if (sub) {
    addText(slide, sub, 0.4, 0.98, 11.5, 0.32, { size: 9.5, color: C.muted });
  }
}

function pill(slide, text, x, y, w, h, color = C.mid, size = 11) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.06,
    fill: { color },
    line: { color },
  });
  addText(slide, text, x + 0.03, y + 0.04, w - 0.06, h - 0.08, { size, bold: true, color: C.white, align: "center", valign: "mid" });
}

function card(slide, head, body, x, y, w, h, color = C.mid) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.05,
    fill: { color: C.white, transparency: 0 },
    line: { color: C.line, width: 0.9 },
  });
  pill(slide, head, x + 0.14, y + 0.12, Math.min(2.2, w - 0.28), 0.33, color, 9.5);
  addText(slide, body, x + 0.18, y + 0.55, w - 0.36, h - 0.65, { size: 11.5, color: C.ink });
}

function flowNode(slide, text, x, y, w, h, color = "EAF4FB", fontSize = 13) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.04,
    fill: { color },
    line: { color: C.line, width: 1 },
  });
  addText(slide, text, x + 0.05, y + 0.06, w - 0.1, h - 0.12, { size: fontSize, bold: true, color: C.ink, align: "center", valign: "mid" });
}

function arrow(slide, x1, y1, x2, y2, color = "7C9AB6") {
  slide.addShape(pptx.ShapeType.line, {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width: 1.8, endArrowType: "triangle" },
  });
}

function dataModelOutput(slide, titleText, dataItems, modelItems, outputItems, y = 1.75) {
  const xs = [0.75, 4.75, 8.75];
  const heads = ["数据输入", "算法模型", "业务输出"];
  const colors = [C.mid, C.orange, C.green];
  const arrays = [dataItems, modelItems, outputItems];
  addText(slide, titleText, 0.72, 1.25, 11.2, 0.38, { size: 17, bold: true, color: C.deep });
  for (let i = 0; i < 3; i++) {
    card(slide, heads[i], arrays[i].join("\n"), xs[i], y, 3.35, 2.45, colors[i]);
  }
  arrow(slide, 4.1, y + 1.2, 4.55, y + 1.2);
  arrow(slide, 8.1, y + 1.2, 8.55, y + 1.2);
}

function stageRibbon(slide, steps, x = 0.75, y = 4.65, w = 11.9, h = 1.0) {
  const colors = ["D9EAF7", "E2F0D9", "FFF2CC", "FCE4D6", "E4DFEC"];
  const gap = 0.12;
  const nodeW = (w - gap * (steps.length - 1)) / steps.length;
  for (let i = 0; i < steps.length; i++) {
    flowNode(slide, steps[i], x + i * (nodeW + gap), y, nodeW, h, colors[i % colors.length], 12);
    if (i < steps.length - 1) arrow(slide, x + (i + 1) * nodeW + i * gap + 0.02, y + h / 2, x + (i + 1) * (nodeW + gap) - 0.04, y + h / 2);
  }
}

function addImagePlaceholder(slide, x, y, w, h, titleText) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.04,
    fill: { color: "F7FBFF" },
    line: { color: C.line, width: 1.1, dash: "dash" },
  });
  addText(slide, titleText, x + 0.2, y + 0.18, w - 0.4, 0.35, { size: 12.5, bold: true, color: C.deep });
}

// 1 Cover
{
  const s = pptx.addSlide();
  addBg(s, "cover");
  s.addShape(pptx.ShapeType.rect, { x: 4.0, y: 2.45, w: 7.2, h: 1.6, fill: { color: "075699", transparency: 12 }, line: { color: "075699", transparency: 100 } });
  addText(s, "今世缘酒业生产模块", 4.25, 2.65, 6.8, 0.48, { size: 20, bold: true, color: C.white, align: "center" });
  addText(s, "AI工艺实施方案", 4.25, 3.15, 6.8, 0.65, { size: 31, bold: true, color: C.white, align: "center" });
  pill(s, "算法融入生产工艺 · 领导汇报版", 4.9, 4.45, 4.8, 0.42, C.cyan, 11);
}

// 2 Contents
{
  const s = pptx.addSlide();
  addBg(s, "contents");
  s.addShape(pptx.ShapeType.rect, { x: 6.05, y: 1.4, w: 6.8, h: 4.65, fill: { color: "076EB8", transparency: 10 }, line: { color: "076EB8", transparency: 100 } });
  const items = [
    ["01", "生产AI总体架构"],
    ["02", "五个生产场景算法地图"],
    ["03", "核心场景实施链路"],
    ["04", "阶段路线与预期效益"],
  ];
  items.forEach((it, i) => {
    addText(s, `${it[0]}-`, 6.4, 1.72 + i * 0.95, 0.85, 0.35, { size: 23, bold: true, color: C.white });
    addText(s, it[1], 7.25, 1.77 + i * 0.95, 5.0, 0.32, { size: 18, color: C.white });
  });
}

// 3 Overall architecture
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "生产AI总体架构", "从工艺现场数据进入AI工艺引擎，再输出预警、质检、维护、调度和物流优化");
  flowNode(s, "生产现场\n传感器 / 视觉 / PLC", 0.8, 1.85, 2.4, 1.0, "D9EAF7");
  flowNode(s, "业务系统\nMES / WMS / 工单 / 质检", 0.8, 3.3, 2.4, 1.0, "E2F0D9");
  flowNode(s, "AI工艺引擎\n预测 · 检测 · 优化 · 解释", 4.25, 2.35, 3.2, 1.45, "17324D", 14);
  addText(s, "预测模型：LSTM / TFT / XGBoost\n视觉模型：YOLO / ViT / 异物轨迹\n异常模型：IForest / AutoEncoder\n优化模型：OR-Tools / VRP / ALNS", 4.55, 4.0, 2.7, 1.15, { size: 10.3, color: C.deep });
  flowNode(s, "业务应用\n预警 / 质检 / 调度 / 推荐", 8.55, 1.85, 2.7, 1.0, "FFF2CC");
  flowNode(s, "反馈闭环\n复核 / 维修 / 执行结果", 8.55, 3.3, 2.7, 1.0, "FCE4D6");
  arrow(s, 3.25, 2.35, 4.05, 2.75);
  arrow(s, 3.25, 3.85, 4.05, 3.0);
  arrow(s, 7.55, 2.75, 8.35, 2.35);
  arrow(s, 7.55, 3.0, 8.35, 3.85);
  addText(s, "关键：每个模型必须能说明采集什么数据、输出什么业务动作、如何验证收益。", 0.8, 6.1, 11.0, 0.35, { size: 15, bold: true, color: C.deep });
}

// 4 scenario matrix
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "五个生产场景算法地图", "把AI算法放进具体工艺任务，而不是停留在概念层");
  const rows = [
    ["酿酒指挥中心", "时序预测 / 工艺选优 / SHAP解释", "质量稳定、经验沉淀"],
    ["包装智能质检", "YOLO / ViT / OCR / 异物轨迹", "漏检下降、缺陷追溯"],
    ["设备预测维护", "异常检测 / 健康评分 / RUL", "提前维修、减少停机"],
    ["AGV路径优化", "A* / CBS / OR-Tools / 仿真", "减少等待、提升准时率"],
    ["仓储物流优化", "库位评分 / 波次 / VRP", "缩短装车、降低里程"],
  ];
  const x = [0.75, 3.4, 8.0];
  const w = [2.45, 4.3, 3.7];
  ["场景", "算法任务", "业务效益"].forEach((h, i) => pill(s, h, x[i], 1.65, w[i], 0.38, C.deep, 11));
  rows.forEach((r, idx) => {
    const y = 2.18 + idx * 0.72;
    r.forEach((txt, i) => {
      s.addShape(pptx.ShapeType.roundRect, { x: x[i], y, w: w[i], h: 0.52, fill: { color: idx % 2 === 0 ? C.white : "F2F7FB" }, line: { color: C.line, width: 0.7 } });
      addText(s, txt, x[i] + 0.06, y + 0.08, w[i] - 0.12, 0.32, { size: i === 0 ? 12 : 11.5, bold: i === 0, color: C.ink, align: i === 0 ? "center" : "left" });
    });
  });
  card(s, "优先启动", "酿酒工艺选优、包装外观质检、设备预测维护", 0.85, 6.0, 3.65, 0.85, C.green);
  card(s, "攻关验证", "酒体悬浮异物检测、工艺半自动调参", 4.95, 6.0, 3.65, 0.85, C.orange);
  card(s, "中期扩展", "AGV调度、仓储物流全链路优化", 9.05, 6.0, 3.65, 0.85, C.mid);
}

// 5 Brewing
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "酿酒指挥中心：预测、解释、选优", "围绕制曲、上甑、蒸馏、摊晾、入窖、发酵等工艺环节形成AI辅助决策");
  dataModelOutput(
    s,
    "核心逻辑：把批次数据和专家经验转化为可解释的工艺参数推荐",
    ["温湿度 / 酒醅温度", "水分 / 酸度 / 蒸汽压力", "摘酒酒度 / 质检结果", "人工操作记录"],
    ["LSTM / TFT 时序预测", "LightGBM / XGBoost", "SHAP原因解释", "相似批次检索 / 贝叶斯优化"],
    ["异常预警", "质量/产量预测", "工艺参数推荐", "优秀批次复用"]
  );
  stageRibbon(s, ["工艺段建模", "批次数据对齐", "质量预测", "参数选优", "效果回流"], 0.75, 5.6, 11.8, 0.75);
  addText(s, "效益：稳定质量和产量，减少批次波动，把经验型判断沉淀为可复用工艺知识。", 0.78, 6.55, 11.5, 0.32, { size: 14, bold: true, color: C.deep });
}

// 6 Brewing phases
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "酿酒指挥中心分阶段落地", "先做可解释预警和工艺选优，再考虑建议调参与半自动控制");
  const phases = [
    ["阶段一：工艺预警", "建立批次正常范围，识别温度、酸度、水分、蒸汽等异常偏离。\n算法：统计控制图、异常检测、LightGBM、LSTM。"],
    ["阶段二：工艺选优", "从优秀批次中检索相似条件，推荐润粮、上甑、摊晾、入窖等参数。\n算法：相似批次、SHAP、贝叶斯优化。"],
    ["阶段三：建议调参", "输出推荐参数、依据、风险提示，由工艺人员确认执行并回流结果。\n算法：规则约束、反馈学习、局部MPC验证。"],
  ];
  phases.forEach((p, i) => card(s, p[0], p[1], 0.85 + i * 4.15, 2.0, 3.75, 3.2, [C.mid, C.orange, C.green][i]));
  addText(s, "注意：涉及实际工艺参数调整时，先保持“AI建议 + 人工确认”，待多批次验证稳定后再做局部自动化。", 0.9, 6.2, 11.5, 0.5, { size: 14, bold: true, color: C.red });
}

// 7 Quality
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "包装智能质检：外观检测与酒体异物双链路", "外观检测可快速复制，酒体悬浮异物需先验证光学与节拍");
  flowNode(s, "外观检测\n瓶盖 / 标签 / 喷码 / 液位", 0.75, 1.75, 2.2, 0.85, "D9EAF7");
  flowNode(s, "高速相机\n环形光 / 背光 / 触发", 3.35, 1.75, 2.15, 0.85, "E2F0D9");
  flowNode(s, "YOLO / ViT / OCR\n缺陷识别与定位", 5.9, 1.75, 2.2, 0.85, "FFF2CC");
  flowNode(s, "NG剔除\n人工复核 / 样本回流", 8.5, 1.75, 2.25, 0.85, "FCE4D6");
  arrow(s, 2.95, 2.18, 3.25, 2.18); arrow(s, 5.5, 2.18, 5.8, 2.18); arrow(s, 8.1, 2.18, 8.4, 2.18);
  flowNode(s, "酒体异物\n悬浮物 / 气泡 / 反光", 0.75, 3.65, 2.2, 0.85, "D9EAF7");
  flowNode(s, "背光偏振\n多相机 / 旋瓶或停顿", 3.35, 3.65, 2.15, 0.85, "E2F0D9");
  flowNode(s, "视频帧差\n轨迹识别 / 异常分类", 5.9, 3.65, 2.2, 0.85, "FFF2CC");
  flowNode(s, "疑似复核\n参数优化 / 产线验证", 8.5, 3.65, 2.25, 0.85, "FCE4D6");
  arrow(s, 2.95, 4.08, 3.25, 4.08); arrow(s, 5.5, 4.08, 5.8, 4.08); arrow(s, 8.1, 4.08, 8.4, 4.08);
  card(s, "效益", "降低漏检和人工目检压力；形成缺陷图像库、批次追溯和质量改进闭环。", 0.9, 5.8, 11.4, 0.9, C.green);
}

// 8 Maintenance
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "设备预测性维护：从被动维修到主动预防", "以关键设备健康评分、异常预警和维修建议为第一阶段目标");
  dataModelOutput(
    s,
    "核心逻辑：运行时序 + 维修工单，形成设备健康评分和故障预警",
    ["设备台账 / 型号 / 部件", "电流 / 振动 / 温度 / 压力", "报警码 / 停机记录", "维修工单 / 备件记录"],
    ["工况识别", "Isolation Forest / One-Class SVM", "LSTM AutoEncoder", "XGBoost / RUL预测"],
    ["健康评分", "异常预警", "维修窗口建议", "备件与工单闭环"]
  );
  stageRibbon(s, ["设备台账", "时序采集", "健康评分", "异常预警", "维修闭环"], 0.75, 5.6, 11.8, 0.75);
}

// 9 AGV
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "AGV路径优化：多车协同与冲突消解", "从地图拓扑和任务队列出发，先仿真验证，再灰度上线调度策略");
  dataModelOutput(
    s,
    "核心逻辑：任务、车辆、节点占用三类数据共同决定调度效率",
    ["厂区地图 / 节点拓扑", "任务队列 / 优先级", "车辆位置 / 电量 / 载重", "历史轨迹 / 等待时间"],
    ["A* / Dijkstra路径规划", "时间窗冲突消解", "CBS多车路径", "OR-Tools / 仿真评估"],
    ["车辆分配", "动态路径", "拥堵预警", "等待和绕路下降"]
  );
  stageRibbon(s, ["地图拓扑", "任务队列", "路径规划", "冲突消解", "仿真上线"], 0.75, 5.6, 11.8, 0.75);
}

// 10 Warehouse
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "仓储物流优化：库位、波次、装车、路径联动", "面向多仓装货、多客户混装和配送时间窗做约束优化");
  dataModelOutput(
    s,
    "核心逻辑：把订单、库存、库位、车辆和客户时间窗转化为优化问题",
    ["订单 / 客户 / 时间窗", "库存 / SKU / 批次 / 库位", "车辆容量 / 月台 / 路线", "历史装车与配送记录"],
    ["ABC库位评分", "订单聚类 / 波次拣选", "装车排程", "VRP / ALNS / VNS"],
    ["推荐库位", "波次计划", "装车顺序", "配送路径与里程下降"]
  );
  stageRibbon(s, ["订单库存", "库位分析", "订单波次", "装车排程", "路径优化"], 0.75, 5.6, 11.8, 0.75);
}

// 11 Algorithm map
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "算法能力如何落到生产", "按任务类型组合算法，而不是一个大模型解决全部问题");
  const algos = [
    ["时序预测", "LSTM / TCN / TFT\n酿酒质量、设备状态、供应链需求", C.mid],
    ["机器视觉", "YOLO / ViT / OCR\n包装外观、异物检测、缺陷追溯", C.green],
    ["异常检测", "IForest / AE / SPC\n设备劣化、工艺偏离、质检异常", C.orange],
    ["运筹优化", "OR-Tools / VRP / ALNS\nAGV调度、装车排程、配送路径", C.red],
    ["可解释AI", "SHAP / 相似批次\n工艺选优、参数推荐、原因分析", C.purple],
    ["知识增强", "RAG / 规则引擎\n工艺文档、维修经验、SOP问答", C.cyan],
  ];
  algos.forEach((a, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    card(s, a[0], a[1], 0.85 + col * 4.15, 1.75 + row * 1.55, 3.75, 1.15, a[2]);
  });
  addText(s, "评价口径：每个模型都要对应明确的数据来源、业务动作和收益指标。", 0.9, 5.45, 11.5, 0.35, { size: 15, bold: true, color: C.deep });
  stageRibbon(s, ["数据输入", "模型计算", "解释校验", "业务执行", "反馈迭代"], 0.9, 6.1, 11.3, 0.55);
}

// 12 Roadmap
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "实施路线：先样板、后复制、再闭环", "用阶段性成果降低生产场景的不确定性");
  const phases = [
    ["0-2个月", "数据口径", "点位、批次、设备、质量标签、接口清单"],
    ["3-6个月", "P0样板", "酿酒选优、包装外观质检、设备健康评分"],
    ["6-12个月", "调度优化", "酒体异物样机、AGV仿真、仓储装车优化"],
    ["12个月+", "闭环迭代", "工艺建议、维修工单、物流全链路持续优化"],
  ];
  phases.forEach((p, i) => {
    card(s, p[0], `${p[1]}\n${p[2]}`, 0.75 + i * 3.05, 2.0, 2.65, 2.2, [C.mid, C.green, C.orange, C.red][i]);
    if (i < phases.length - 1) arrow(s, 3.4 + i * 3.05, 3.1, 3.68 + i * 3.05, 3.1);
  });
  card(s, "近期抓手", "酿酒工艺选优、包装外观质检、设备预测维护", 0.9, 5.25, 3.6, 0.9, C.green);
  card(s, "技术攻关", "酒体悬浮异物检测、工艺半自动调参", 4.95, 5.25, 3.6, 0.9, C.orange);
  card(s, "长期闭环", "生产指挥中心、持续学习、跨系统联动优化", 9.0, 5.25, 3.6, 0.9, C.mid);
}

// 13 Benefits
{
  const s = pptx.addSlide();
  addBg(s, "body");
  title(s, "预期效益与领导关注点", "从质量、效率、成本和数据资产四个维度衡量建设效果");
  const benefits = [
    ["质量稳定", "酿酒批次波动下降\n包装漏检和误检下降", C.green],
    ["效率提升", "质检人工压力下降\nAGV等待和装车时长下降", C.mid],
    ["成本优化", "突发停机减少\n库存、车辆和配送成本优化", C.orange],
    ["资产沉淀", "工艺知识库、缺陷图库、设备健康库、物流策略库", C.purple],
  ];
  benefits.forEach((b, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    card(s, b[0], b[1], 1.0 + col * 6.1, 2.0 + row * 2.0, 5.35, 1.45, b[2]);
  });
  addText(s, "最终目标：以生产工艺为主线，把AI嵌入数据、模型、执行和反馈闭环。", 1.0, 6.35, 11.0, 0.42, { size: 17, bold: true, color: C.deep, align: "center" });
}

const out = path.join(outDir, "今世缘酒业生产模块AI工艺实施方案_模板背景版.pptx");
pptx.writeFile({ fileName: out });
