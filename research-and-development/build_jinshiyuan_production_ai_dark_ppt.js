const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const root = "E:/PY/research";
const outDir = path.join(root, "output/ppt");
const assetDir = path.join(root, "tmp/dark_ppt_assets");
const logoWhite = path.join(root, "tmp/template_media/image2.png");
fs.mkdirSync(outDir, { recursive: true });
fs.mkdirSync(assetDir, { recursive: true });

const pptx = new pptxgen();
pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";
pptx.author = "Codex";
pptx.subject = "今世缘酒业生产模块AI智能升级";
pptx.title = "酿造数字神经网络";
pptx.company = "南大五维";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const C = {
  bg: "111923",
  bg2: "18222E",
  panel: "202C38",
  panel2: "273646",
  line: "6E8396",
  gold: "C99A55",
  gold2: "F1C77A",
  blue: "5FA8D3",
  cyan: "5DE3F0",
  white: "EAF2F8",
  muted: "A9B7C5",
  ink: "101820",
  green: "78C091",
  orange: "F2A65A",
  red: "E56B6F",
};

function addText(slide, text, x, y, w, h, opt = {}) {
  slide.addText(text, {
    x, y, w, h,
    margin: opt.margin ?? 0.02,
    fit: "shrink",
    fontFace: "Microsoft YaHei",
    fontSize: opt.size ?? 16,
    bold: opt.bold ?? false,
    color: opt.color ?? C.white,
    align: opt.align ?? "left",
    valign: opt.valign ?? "top",
    breakLine: false,
    paraSpaceAfterPt: opt.after ?? 0,
    ...opt.extra,
  });
}

function shape(slide, type, x, y, w, h, fill, line = fill, transparency = 0) {
  const s = slide.addShape(type, {
    x, y, w, h,
    fill: { color: fill, transparency },
    line: { color: line, width: 1 },
  });
  return s;
}

function panel(slide, x, y, w, h, opt = {}) {
  const s = slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.04,
    fill: { color: opt.fill ?? C.panel, transparency: opt.transparency ?? 8 },
    line: { color: opt.line ?? C.line, transparency: 10, width: opt.width ?? 1.2 },
  });
  return s;
}

function label(slide, text, x, y, w, h, color = C.gold, size = 12) {
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w, h,
    fill: { color, transparency: 0 },
    line: { color, transparency: 100 },
  });
  addText(slide, text, x + 0.08, y + 0.04, w - 0.16, h - 0.08, {
    size,
    bold: true,
    color: C.ink,
    align: "center",
    valign: "mid",
  });
}

function line(slide, x1, y1, x2, y2, color = C.line, width = 1.2, arrow = false) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width, endArrowType: arrow ? "triangle" : "none" },
  });
}

function title(slide, text, sub = "") {
  addText(slide, text, 0.62, 0.32, 10.6, 0.55, { size: 24, bold: true, color: C.white });
  line(slide, 0.62, 0.95, 12.6, 0.95, C.gold, 1.3);
  if (sub) addText(slide, sub, 0.66, 1.04, 10.8, 0.32, { size: 10.5, color: C.muted });
  if (fs.existsSync(logoWhite)) {
    slide.addImage({ path: logoWhite, x: 11.78, y: 0.20, w: 0.72, h: 0.72 });
  } else {
    addText(slide, "5D", 11.9, 0.45, 0.7, 0.38, { size: 24, bold: true, color: C.white, align: "right" });
  }
}

function bg(slide) {
  slide.background = { color: C.bg };
  shape(slide, pptx.ShapeType.rect, 0, 0, 13.333, 7.5, C.bg, C.bg);
  shape(slide, pptx.ShapeType.rect, 0, 0, 13.333, 7.5, "000000", "000000", 35);
  for (let i = 0; i < 6; i++) {
    line(slide, 0.3 + i * 2.4, 0.15, 0.9 + i * 2.4, 7.2, "263849", 0.45);
  }
  for (let i = 0; i < 8; i++) {
    line(slide, 0.15, 0.8 + i * 0.75, 13.1, 0.65 + i * 0.75, "203142", 0.35);
  }
}

function metalFrame(slide, x, y, w, h) {
  panel(slide, x, y, w, h, { fill: "121C26", line: "7A8B9A", transparency: 0, width: 1.2 });
  line(slide, x + 0.15, y + 0.2, x + w - 0.15, y + 0.2, "405466", 0.8);
  line(slide, x + 0.15, y + h - 0.2, x + w - 0.15, y + h - 0.2, "405466", 0.8);
}

function flowPill(slide, text, x, y, w, color = C.panel2, textColor = C.white) {
  panel(slide, x, y, w, 0.55, { fill: color, line: C.line, transparency: 0 });
  addText(slide, text, x + 0.08, y + 0.12, w - 0.16, 0.25, { size: 12.2, bold: true, color: textColor, align: "center" });
}

function card(slide, head, body, x, y, w, h, color = C.gold) {
  panel(slide, x, y, w, h, { fill: "121C26", line: color, transparency: 0, width: 1.1 });
  label(slide, head, x + 0.14, y + 0.12, Math.min(1.75, w - 0.28), 0.32, color, 10.5);
  addText(slide, body, x + 0.2, y + 0.55, w - 0.4, h - 0.65, { size: 11.6, color: C.white });
}

function dataModelOutput(slide, data, model, output, y = 2.05) {
  const xs = [0.9, 4.75, 8.6];
  const heads = ["数据感知", "算法计算", "工艺执行"];
  const colors = [C.gold, C.blue, C.green];
  const bodies = [data, model, output];
  for (let i = 0; i < 3; i++) {
    panel(slide, xs[i], y, 3.15, 2.25, { fill: C.panel, line: colors[i], transparency: 0, width: 1.3 });
    label(slide, heads[i], xs[i] + 0.18, y + 0.16, 1.55, 0.34, colors[i], 10);
    addText(slide, bodies[i].join("\n"), xs[i] + 0.28, y + 0.72, 2.65, 1.25, { size: 11.2, color: C.white });
    if (i < 2) line(slide, xs[i] + 3.18, y + 1.15, xs[i + 1] - 0.2, y + 1.15, C.gold, 1.7, true);
  }
}

function stageChain(slide, steps, x = 0.85, y = 5.25, w = 11.65) {
  const gap = 0.08;
  const nodeW = (w - gap * (steps.length - 1)) / steps.length;
  for (let i = 0; i < steps.length; i++) {
    flowPill(slide, steps[i], x + i * (nodeW + gap), y, nodeW, i % 2 ? "243646" : "2A4053");
    if (i < steps.length - 1) line(slide, x + (i + 1) * nodeW + i * gap + 0.01, y + 0.28, x + (i + 1) * (nodeW + gap) - 0.03, y + 0.28, C.gold, 1.2, true);
  }
}

function axisRow(slide, y, leftTitle, leftText, mid, rightText) {
  panel(slide, 0.9, y, 11.55, 0.72, { fill: "1B2835", line: "526B80", transparency: 0 });
  label(slide, leftTitle, 1.05, y + 0.15, 1.45, 0.34, C.gold, 10.5);
  addText(slide, leftText, 2.75, y + 0.16, 3.3, 0.3, { size: 11.3, color: C.white, align: "center" });
  addText(slide, mid, 6.15, y + 0.16, 1.25, 0.3, { size: 13.5, bold: true, color: C.gold2, align: "center" });
  addText(slide, rightText, 7.55, y + 0.16, 4.35, 0.3, { size: 11.3, color: C.white, align: "center" });
}

// 1 cover
{
  const s = pptx.addSlide();
  bg(s);
  if (fs.existsSync(logoWhite)) {
    s.addImage({ path: logoWhite, x: 10.8, y: 5.25, w: 1.0, h: 1.0 });
  } else {
    addText(s, "5D", 10.55, 5.0, 1.5, 0.7, { size: 42, bold: true, color: C.white, align: "right" });
  }
  // vessel outline
  s.addShape(pptx.ShapeType.arc, { x: 4.3, y: 1.05, w: 4.6, h: 4.9, line: { color: "C9D4DF", width: 2, transparency: 15 }, adjustPoint: 0.22 });
  s.addShape(pptx.ShapeType.arc, { x: 4.25, y: 1.08, w: 4.7, h: 4.85, line: { color: C.gold, width: 1.5, transparency: 10 }, adjustPoint: 0.76 });
  const pts = [
    [5.15, 2.25], [5.95, 2.6], [6.75, 2.25],
    [5.5, 3.3], [6.35, 3.45], [7.25, 3.2],
    [5.25, 4.25], [6.25, 4.65], [7.35, 4.25],
  ];
  pts.forEach((p) => {
    shape(s, pptx.ShapeType.ellipse, p[0], p[1], 0.11, 0.11, C.gold2, C.gold2);
  });
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      if (Math.abs(i - j) <= 4) line(s, pts[i][0] + 0.055, pts[i][1] + 0.055, pts[j][0] + 0.055, pts[j][1] + 0.055, "D6C0A0", 0.45);
    }
  }
  addText(s, "酿造数字神经网络", 7.25, 5.45, 4.8, 0.6, { size: 31, bold: true, color: C.white, align: "right" });
  addText(s, "今世缘酒业生产模块AI智能升级与实施蓝图", 6.2, 6.12, 5.85, 0.32, { size: 15, color: C.muted, align: "right" });
  addText(s, "2026年4月", 0.65, 6.55, 2.4, 0.25, { size: 12, color: C.muted });
}

// 2 pain point
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "匠心传承与数字未来的交汇点");
  panel(s, 0.65, 1.35, 12.0, 4.2, { fill: "121C26", line: "7C8B99", transparency: 0 });
  shape(s, pptx.ShapeType.rect, 0.9, 1.65, 5.6, 2.35, "3A2B1C", "846A45", 8);
  addText(s, "传统工艺经验", 1.25, 1.95, 2.8, 0.35, { size: 21, bold: true, color: C.gold2 });
  addText(s, "制曲、润粮、上甑、发酵、摘酒依赖老师傅眼观、鼻嗅、口尝。\n经验价值高，但难以规模化复制。", 1.25, 2.55, 4.7, 0.95, { size: 14, color: C.white });
  shape(s, pptx.ShapeType.rect, 6.65, 1.65, 5.6, 2.35, "17283A", "637A91", 8);
  addText(s, "数字化瓶颈", 7.0, 1.95, 2.8, 0.35, { size: 21, bold: true, color: C.white });
  addText(s, "批次波动、质检压力、设备停机、物流等待都在消耗质量与效率。\nAI要把经验、数据和执行闭环打通。", 7.0, 2.55, 4.7, 0.95, { size: 14, color: C.white });
  ["人工经验", "数据感知", "知识传承", "决策响应", "产出成效"].forEach((t, i) => {
    flowPill(s, t, 1.0 + i * 2.25, 4.55, 1.7, i === 0 ? C.gold : C.panel2);
    if (i < 4) line(s, 2.7 + i * 2.25, 4.83, 3.15 + i * 2.25, 4.83, C.gold, 1.1, true);
  });
  addText(s, "核心判断：不是替代“匠人”，而是将经验解码、量化、进化为持续迭代的生产数字大脑。", 0.95, 6.25, 11.5, 0.36, { size: 16, bold: true, color: C.gold2, align: "center" });
}

// 3 evolution
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "进化：从“人工经验”到“数字大脑”");
  axisRow(s, 1.55, "数据感知", "依赖五感，局部且易受疲劳影响", "→", "多模态传感网，全天候高频采样");
  axisRow(s, 2.55, "知识传承", "师徒口传心授，周期长且易流失", "→", "历史优秀批次特征提取，可复制沉淀");
  axisRow(s, 3.55, "决策响应", "事后复盘追责，问题已造成偏差", "→", "实时异常预警，多维参数动态推荐");
  axisRow(s, 4.55, "产出成效", "批次间存在波动，依赖专家发挥", "→", "参数闭环优化，趋近黄金批次标准");
  addText(s, "AI升级的价值不在“炫技”，而在把传统经验变成稳定、可复用、可评测的生产能力。", 1.1, 6.1, 11.0, 0.35, { size: 16, bold: true, color: C.gold2, align: "center" });
}

// 4 common engine
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "驱动全场景的AI通用引擎");
  // Circular loop approximation
  shape(s, pptx.ShapeType.arc, 4.55, 1.45, 4.0, 4.0, "FFFFFF", "BFC8D2", 100);
  shape(s, pptx.ShapeType.arc, 4.82, 1.72, 3.45, 3.45, "FFFFFF", C.gold, 100);
  addText(s, "AI\n工艺引擎", 5.55, 2.82, 1.9, 0.75, { size: 24, bold: true, color: C.white, align: "center" });
  const nodes = [
    ["数据采集", "融合环境传感、工艺过程流、质量标签与人工经验。", 0.9, 1.65, C.gold],
    ["算法计算", "异常检测、时序建模、多目标优化，解析深层规律。", 9.3, 1.65, C.blue],
    ["工艺执行", "输出参数选优、风险预警与调度策略，由人工确认或系统执行。", 9.3, 4.55, C.gold],
    ["成效反馈", "采集执行结果与产量/质量反馈，自动重训模型。", 0.9, 4.55, C.blue],
  ];
  nodes.forEach(([h, b, x, y, color]) => card(s, h, b, x, y, 3.25, 1.25, color));
  line(s, 4.15, 2.25, 4.85, 2.55, C.gold, 1.2, true);
  line(s, 8.55, 2.55, 9.15, 2.25, C.gold, 1.2, true);
  line(s, 9.15, 5.1, 8.55, 4.2, C.gold, 1.2, true);
  line(s, 4.15, 5.1, 4.85, 4.2, C.gold, 1.2, true);
  addText(s, "这不是黑盒，而是一条透明的、从“辅助决策”迈向“全局优化”的神经传导链路。", 1.25, 6.45, 10.7, 0.3, { size: 15.5, bold: true, color: C.gold2, align: "center" });
}

// 5 scenario map
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "生产模块五大AI场景全景图");
  const scene = [
    ["酿酒指挥中心", "LSTM/TFT + SHAP\n质量预测 · 工艺选优", 1.0, 1.55, C.gold],
    ["包装智能质检", "YOLO/ViT/OCR\n外观检测 · 酒体异物", 5.0, 1.55, C.blue],
    ["设备预测维护", "IForest/LSTM-AE/RUL\n健康评分 · 维修建议", 9.0, 1.55, C.green],
    ["AGV路径优化", "A*/CBS/OR-Tools\n路径规划 · 冲突消解", 3.0, 4.1, C.orange],
    ["仓储物流优化", "ABC/VRP/ALNS\n库位 · 波次 · 装车", 7.0, 4.1, C.red],
  ];
  scene.forEach(([h, b, x, y, color]) => card(s, h, b, x, y, 3.25, 1.35, color));
  line(s, 4.25, 2.2, 5.0, 2.2, C.line, 1.2, true);
  line(s, 8.25, 2.2, 9.0, 2.2, C.line, 1.2, true);
  line(s, 6.6, 2.9, 4.45, 4.1, C.line, 1.2, true);
  line(s, 6.8, 2.9, 8.15, 4.1, C.line, 1.2, true);
  addText(s, "五个场景共用一套数据底座和算法能力，但业务输出必须落到具体工艺动作。", 1.2, 6.35, 10.8, 0.35, { size: 15.5, bold: true, color: C.gold2, align: "center" });
}

// 6 brewing center
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "酿酒指挥中心：把批次经验转化为工艺推荐");
  dataModelOutput(
    s,
    ["温湿度 / 酒醅温度", "水分 / 酸度 / 蒸汽压力", "摘酒酒度 / 质检结果", "人工操作记录"],
    ["LSTM / TFT时序预测", "LightGBM / XGBoost", "SHAP原因解释", "相似批次 / 贝叶斯优化"],
    ["异常预警", "质量/产量预测", "参数推荐", "优秀批次复用"],
    1.55
  );
  stageChain(s, ["制曲", "润粮", "上甑", "蒸馏", "摊晾", "入窖", "发酵", "摘酒"], 0.65, 4.65, 12.05);
  addText(s, "实施节奏：先做预警和工艺选优，再做建议调参，最终在低风险环节验证半自动控制。", 0.95, 6.25, 11.5, 0.34, { size: 15.5, bold: true, color: C.gold2, align: "center" });
}

// 7 quality
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "包装智能质检：外观检测与酒体异物双链路");
  panel(s, 0.8, 1.55, 11.7, 4.45, { fill: "121C26", line: "7C8B99", transparency: 0 });
  const upperY = 2.0;
  [["相机光源", 0.95], ["图像采集", 3.1], ["YOLO/ViT/OCR", 5.25], ["缺陷定位", 7.55], ["NG剔除", 9.7]].forEach(([t, x], i) => {
    flowPill(s, t, x, upperY, 1.6, i === 2 ? C.blue : C.panel2);
    if (i < 4) line(s, x + 1.6, upperY + 0.28, x + 2.02, upperY + 0.28, C.gold, 1.1, true);
  });
  addText(s, "外观检测：瓶盖、标签、喷码、液位、瓶身破损", 1.0, 1.65, 6.5, 0.25, { size: 12.5, bold: true, color: C.gold2 });
  const lowerY = 4.0;
  [["背光偏振", 0.95], ["多相机/旋瓶", 3.1], ["视频帧差", 5.25], ["轨迹识别", 7.55], ["疑似复核", 9.7]].forEach(([t, x], i) => {
    flowPill(s, t, x, lowerY, 1.6, i === 3 ? C.blue : C.panel2);
    if (i < 4) line(s, x + 1.6, lowerY + 0.28, x + 2.02, lowerY + 0.28, C.gold, 1.1, true);
  });
  addText(s, "酒体异物：悬浮物、气泡、瓶身污点、玻璃反光", 1.0, 3.65, 6.5, 0.25, { size: 12.5, bold: true, color: C.gold2 });
  addText(s, "价值：减少人工目检压力，沉淀缺陷图库，实现批次、材料、设备问题追溯。", 1.0, 6.35, 11.2, 0.3, { size: 15, bold: true, color: C.gold2, align: "center" });
}

// 8 maintenance
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "设备预测性维护：从故障维修到主动预防");
  dataModelOutput(
    s,
    ["设备台账 / 型号 / 部件", "电流 / 振动 / 温度 / 压力", "报警码 / 停机记录", "维修工单 / 备件记录"],
    ["工况识别", "Isolation Forest", "LSTM AutoEncoder", "XGBoost / RUL预测"],
    ["健康评分", "故障概率", "维修窗口", "备件与工单闭环"],
    1.65
  );
  stageChain(s, ["设备台账", "时序采集", "工况识别", "健康评分", "异常预警", "维修闭环"], 0.8, 5.25, 11.75);
  addText(s, "优先选择停机损失大的包装线、灌装机、输送系统、泵、空压机、AGV和立体库设备。", 1.05, 6.35, 11.0, 0.3, { size: 15, bold: true, color: C.gold2, align: "center" });
}

// 9 logistics
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "AGV与仓储物流：让生产物流节拍可计算、可调度");
  panel(s, 0.75, 1.55, 5.75, 4.4, { fill: "121C26", line: C.blue, transparency: 0 });
  label(s, "AGV路径优化", 1.0, 1.85, 1.85, 0.36, C.blue);
  addText(s, "地图拓扑、任务队列、车辆位置、电量、节点占用", 1.05, 2.45, 4.6, 0.55, { size: 13, color: C.white });
  addText(s, "A* / Dijkstra\nCBS冲突消解\nOR-Tools任务分配\n离线仿真评估", 1.05, 3.35, 4.65, 1.25, { size: 17, bold: true, color: C.gold2, align: "center" });
  addText(s, "输出：动态路径、拥堵预警、等待下降、准时率提升", 1.05, 5.05, 4.8, 0.38, { size: 13, color: C.white, align: "center" });
  panel(s, 6.85, 1.55, 5.75, 4.4, { fill: "121C26", line: C.green, transparency: 0 });
  label(s, "仓储物流优化", 7.1, 1.85, 1.95, 0.36, C.green);
  addText(s, "订单、库存、库位、车辆、客户时间窗、多仓节点", 7.15, 2.45, 4.6, 0.55, { size: 13, color: C.white });
  addText(s, "ABC库位评分\n订单聚类与波次\nVRP / ALNS / VNS\n装车排程优化", 7.15, 3.35, 4.65, 1.25, { size: 17, bold: true, color: C.gold2, align: "center" });
  addText(s, "输出：推荐库位、装车顺序、配送路径、里程下降", 7.15, 5.05, 4.8, 0.38, { size: 13, color: C.white, align: "center" });
  addText(s, "物流场景的关键不是单个最短路径，而是订单、车辆、仓库和生产节拍的联合优化。", 1.1, 6.35, 11.0, 0.32, { size: 15, bold: true, color: C.gold2, align: "center" });
}

// 10 roadmap
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "实施路线：先样板、后复制、再闭环");
  const phases = [
    ["0-2个月", "数据口径", "点位、批次、设备、质量标签、接口清单"],
    ["3-6个月", "P0样板", "酿酒选优、包装外观质检、设备健康评分"],
    ["6-12个月", "调度优化", "酒体异物样机、AGV仿真、仓储装车优化"],
    ["12个月+", "闭环迭代", "工艺建议、维修工单、物流全链路持续优化"],
  ];
  phases.forEach((p, i) => {
    panel(s, 0.85 + i * 3.05, 2.0, 2.65, 2.55, { fill: "121C26", line: [C.blue, C.green, C.orange, C.red][i], transparency: 0 });
    label(s, p[0], 1.05 + i * 3.05, 2.25, 1.25, 0.34, [C.blue, C.green, C.orange, C.red][i], 10);
    addText(s, p[1], 1.05 + i * 3.05, 2.95, 2.2, 0.35, { size: 18, bold: true, color: C.gold2 });
    addText(s, p[2], 1.05 + i * 3.05, 3.55, 2.15, 0.65, { size: 11.5, color: C.white });
    if (i < 3) line(s, 3.5 + i * 3.05, 3.25, 3.85 + i * 3.05, 3.25, C.gold, 1.2, true);
  });
  card(s, "近期抓手", "酿酒工艺选优、包装外观质检、设备预测维护", 1.0, 5.45, 3.45, 0.9, C.green);
  card(s, "攻关验证", "酒体悬浮异物检测、工艺半自动调参", 4.95, 5.45, 3.45, 0.9, C.orange);
  card(s, "长期闭环", "生产指挥中心、持续学习、跨系统联动优化", 8.9, 5.45, 3.45, 0.9, C.blue);
}

// 11 benefits
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "预期价值：质量、效率、成本与数据资产");
  const items = [
    ["质量稳定", "批次波动下降\n包装漏检下降\n优级率提升", C.green],
    ["效率提升", "人工质检压力下降\nAGV等待下降\n装车时长下降", C.blue],
    ["成本优化", "突发停机减少\n车辆里程下降\n备件库存更合理", C.orange],
    ["资产沉淀", "工艺知识库\n缺陷图库\n设备健康库\n物流策略库", C.gold],
  ];
  items.forEach((it, i) => {
    const row = Math.floor(i / 2);
    const col = i % 2;
    card(s, it[0], it[1], 1.05 + col * 6.15, 1.75 + row * 2.0, 5.4, 1.45, it[2]);
  });
  addText(s, "最终目标：以生产工艺为主线，把AI嵌入数据、模型、执行和反馈闭环。", 1.1, 6.2, 11.0, 0.38, { size: 18, bold: true, color: C.gold2, align: "center" });
}

// 12 close
{
  const s = pptx.addSlide();
  bg(s);
  addText(s, "生产模块AI智能升级", 2.0, 2.35, 9.3, 0.65, { size: 31, bold: true, color: C.white, align: "center" });
  addText(s, "不是堆模型，而是构建贯穿工艺、质量、设备与物流的数字神经网络", 2.0, 3.2, 9.3, 0.36, { size: 16, color: C.gold2, align: "center" });
  stageChain(s, ["数据感知", "算法计算", "工艺执行", "成效反馈", "持续进化"], 1.6, 4.35, 10.2);
  addText(s, "江苏南大五维电子科技有限公司", 4.2, 6.45, 5.0, 0.25, { size: 12.5, color: C.muted, align: "center" });
}

const out = path.join(outDir, "今世缘酒业生产模块AI智能升级与实施蓝图_深色科技版.pptx");
pptx.writeFile({ fileName: out });
