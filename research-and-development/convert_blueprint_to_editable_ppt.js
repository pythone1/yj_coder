const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const root = "E:/PY/research";
const outDir = path.join(root, "output/ppt");
const logoWhite = path.join(root, "tmp/template_media/image2.png");
fs.mkdirSync(outDir, { recursive: true });

const pptx = new pptxgen();
pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";
pptx.author = "Codex";
pptx.company = "南大五维";
pptx.subject = "今世缘酒业生产模块AI工艺分析与实施路径";
pptx.title = "今世缘酒业生产模块AI工艺分析与实施路径";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};
pptx.margin = 0;

const C = {
  bg: "08213A",
  bg2: "0A3158",
  bg3: "071723",
  panel: "0E2A3F",
  panel2: "123A55",
  cyan: "31E8FF",
  cyan2: "6AF5FF",
  blue: "1E84FF",
  deepBlue: "0B4276",
  gold: "D8A850",
  orange: "EE9E4A",
  white: "F4FBFF",
  mute: "B6D7EA",
  dim: "7EA9BE",
  line: "2D86B6",
  green: "42F0A8",
  red: "FF7B6E",
};

function addText(slide, text, x, y, w, h, opt = {}) {
  slide.addText(text, {
    x, y, w, h,
    margin: opt.margin ?? 0.04,
    fontFace: opt.fontFace || "Microsoft YaHei",
    fontSize: opt.size ?? 13,
    color: opt.color || C.white,
    bold: opt.bold || false,
    breakLine: opt.breakLine || false,
    align: opt.align || "left",
    valign: opt.valign || "top",
    fit: "shrink",
    paraSpaceAfterPt: opt.after ?? 0,
    breakLine: false,
  });
}

function shape(slide, type, x, y, w, h, opt = {}) {
  slide.addShape(type, {
    x, y, w, h,
    rectRadius: opt.radius,
    fill: { color: opt.fill || C.panel, transparency: opt.transparency ?? 0 },
    line: { color: opt.line || opt.fill || C.line, transparency: opt.lineTrans ?? 0, width: opt.width ?? 1 },
    rotate: opt.rotate || 0,
  });
}

function line(slide, x1, y1, x2, y2, color = C.cyan, width = 1.2, arrow = false, dash = false) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: {
      color,
      width,
      transparency: 0,
      beginArrowType: "none",
      endArrowType: arrow ? "triangle" : "none",
      dash: dash ? "dash" : "solid",
    },
  });
}

function bg(slide, variant = "dark") {
  slide.background = { color: variant === "light" ? "0B74B9" : C.bg };
  shape(slide, pptx.ShapeType.rect, 0, 0, 13.333, 7.5, { fill: variant === "light" ? "0E7CC3" : C.bg, line: variant === "light" ? "0E7CC3" : C.bg });
  shape(slide, pptx.ShapeType.rect, 0, 0, 13.333, 7.5, { fill: "000000", line: "000000", transparency: variant === "light" ? 72 : 35 });
  for (let i = 0; i < 7; i++) line(slide, -0.6 + i * 2.25, 0.15, 0.5 + i * 2.25, 7.4, "144767", 0.35, false, true);
  for (let i = 0; i < 9; i++) line(slide, 0.1, 0.7 + i * 0.72, 13.2, 0.48 + i * 0.72, "113A56", 0.25, false, true);
  shape(slide, pptx.ShapeType.arc, 7.1, -1.0, 7.5, 7.5, { fill: C.cyan, line: C.cyan, transparency: 100, width: 1.4 });
}

function addLogo(slide, x = 11.65, y = 0.22, w = 0.82, h = 0.82) {
  if (fs.existsSync(logoWhite)) slide.addImage({ path: logoWhite, x, y, w, h });
  else addText(slide, "5D\n南大五维", x, y, w, h, { size: 10, bold: true, align: "center" });
}

function title(slide, text, sub = "") {
  addText(slide, text, 0.62, 0.34, 9.8, 0.42, { size: 21, bold: true, color: C.white });
  line(slide, 0.62, 0.88, 9.7, 0.88, C.cyan, 1.1);
  if (sub) addText(slide, sub, 0.66, 0.98, 9.7, 0.32, { size: 9.8, color: C.mute });
  addLogo(slide);
}

function panel(slide, x, y, w, h, opt = {}) {
  shape(slide, pptx.ShapeType.roundRect, x, y, w, h, {
    fill: opt.fill || C.panel,
    line: opt.line || C.line,
    width: opt.width ?? 1.2,
    transparency: opt.transparency ?? 8,
  });
  line(slide, x + 0.12, y + 0.12, x + w - 0.12, y + 0.12, opt.glow || C.cyan, 0.7);
}

function pill(slide, text, x, y, w, color = C.cyan, opt = {}) {
  shape(slide, pptx.ShapeType.roundRect, x, y, w, 0.33, { fill: color, line: color, transparency: opt.transparency ?? 8 });
  addText(slide, text, x + 0.06, y + 0.07, w - 0.12, 0.18, { size: opt.size ?? 9.3, bold: true, color: opt.textColor || "061A28", align: "center" });
}

function bulletList(slide, items, x, y, w, h, opt = {}) {
  const lineH = opt.lineH || 0.33;
  items.forEach((t, i) => {
    shape(slide, pptx.ShapeType.ellipse, x, y + 0.08 + i * lineH, 0.07, 0.07, { fill: opt.dot || C.cyan, line: opt.dot || C.cyan });
    addText(slide, t, x + 0.16, y + i * lineH, w - 0.18, lineH, { size: opt.size ?? 9.3, color: opt.color || C.white });
  });
}

function iconCard(slide, titleText, body, x, y, w, h, color = C.cyan) {
  panel(slide, x, y, w, h, { line: color, fill: "08273B", transparency: 3 });
  shape(slide, pptx.ShapeType.ellipse, x + w / 2 - 0.22, y + 0.2, 0.44, 0.44, { fill: color, line: color, transparency: 15 });
  line(slide, x + w / 2 - 0.16, y + 0.42, x + w / 2 + 0.16, y + 0.42, C.white, 1.1);
  line(slide, x + w / 2, y + 0.26, x + w / 2, y + 0.58, C.white, 1.1);
  addText(slide, titleText, x + 0.18, y + 0.78, w - 0.36, 0.26, { size: 11.3, bold: true, color: C.white, align: "center" });
  addText(slide, body, x + 0.18, y + 1.18, w - 0.36, h - 1.35, { size: 8.7, color: C.mute, align: "center" });
}

function network(slide, points, color = C.cyan) {
  for (let i = 0; i < points.length - 1; i++) line(slide, points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], color, 0.8);
  points.forEach(([x, y], i) => {
    shape(slide, pptx.ShapeType.ellipse, x - 0.045, y - 0.045, 0.09, 0.09, { fill: i % 2 ? C.cyan2 : color, line: C.white, width: 0.3 });
  });
}

function processArrow(slide, labels, x, y, w, color = C.cyan) {
  const gap = 0.06;
  const itemW = (w - gap * (labels.length - 1)) / labels.length;
  labels.forEach((t, i) => {
    shape(slide, pptx.ShapeType.chevron, x + i * (itemW + gap), y, itemW, 0.48, { fill: i % 2 ? "104C6C" : "0B3956", line: color, transparency: 2 });
    addText(slide, t, x + i * (itemW + gap) + 0.04, y + 0.13, itemW - 0.08, 0.17, { size: 8.6, bold: true, color: C.white, align: "center" });
  });
}

function drawMountains(slide) {
  shape(slide, pptx.ShapeType.triangle, -0.4, 5.0, 4.8, 2.7, { fill: "0C4E77", line: "0C4E77", transparency: 22, rotate: 0 });
  shape(slide, pptx.ShapeType.triangle, 2.1, 4.75, 5.9, 2.95, { fill: "0D5F8E", line: "0D5F8E", transparency: 24 });
  shape(slide, pptx.ShapeType.triangle, 6.1, 5.05, 5.4, 2.55, { fill: "0A4366", line: "0A4366", transparency: 20 });
  shape(slide, pptx.ShapeType.rect, 0, 6.45, 13.333, 1.05, { fill: "071B2A", line: "071B2A", transparency: 15 });
}

function drawVessel(slide, cx, cy, scale = 1) {
  shape(slide, pptx.ShapeType.ellipse, cx - 0.9 * scale, cy - 0.9 * scale, 1.8 * scale, 1.8 * scale, { fill: "0D2A3C", line: C.gold, width: 1.7, transparency: 8 });
  shape(slide, pptx.ShapeType.ellipse, cx - 0.55 * scale, cy - 0.55 * scale, 1.1 * scale, 1.1 * scale, { fill: "071723", line: C.cyan, width: 1.1, transparency: 16 });
  shape(slide, pptx.ShapeType.arc, cx - 1.05 * scale, cy - 1.05 * scale, 2.1 * scale, 2.1 * scale, { fill: C.cyan, line: C.cyan, width: 1.2, transparency: 100 });
  network(slide, [[cx - 1.4*scale, cy + 1.0*scale],[cx - 0.7*scale, cy + 0.4*scale],[cx, cy + 0.82*scale],[cx + 0.7*scale, cy + 0.2*scale],[cx + 1.35*scale, cy + 0.8*scale]], C.cyan);
}

// 1 Cover
{
  const s = pptx.addSlide();
  bg(s, "light");
  drawMountains(s);
  drawVessel(s, 8.15, 2.95, 1.25);
  panel(s, 0.75, 2.7, 5.65, 1.85, { fill: "071723", line: "1F6E96", transparency: 10 });
  addText(s, "今世缘酒业生产模块AI工艺\n分析与实施路径", 1.05, 3.02, 4.95, 0.82, { size: 22.5, bold: true, color: C.white });
  addText(s, "开题版 | 数据、工艺、算法、效益一体化说明", 1.08, 4.02, 4.9, 0.26, { size: 10.6, color: C.mute });
  addText(s, "2026-04-24\n江苏南大五维电子科技有限公司", 1.06, 4.95, 4.2, 0.42, { size: 9.2, color: C.mute });
  addLogo(s, 11.7, 0.28, 0.72, 0.72);
}

// 2 Overview
{
  const s = pptx.addSlide();
  bg(s, "light");
  title(s, "生产模块总体进程", "从经验驱动走向数据驱动、模型驱动和闭环优化");
  panel(s, 1.35, 0.9, 10.7, 0.58, { fill: "061B2B", line: C.cyan, transparency: 2 });
  addText(s, "生产AI不是单点模型，而是把现场数据、工艺经验、算法判断和执行反馈串成一条持续进化的生产神经网络。", 1.65, 1.07, 10.1, 0.18, { size: 10.8, bold: true, color: C.white, align: "center" });
  const cards = [
    ["酿酒指挥中心", "酿造数据、专家经验、质量结果融合\n工艺预警、工艺选优、参数推荐\n目标：稳定产量与质量"],
    ["包装智能质检", "外观检测与酒体异物双链路\nYOLO、异常检测、多光源成像\n目标：降低漏检误检"],
    ["设备预测性维护", "电流、振动、温度、工单融合\n异常检测、RUL预测、维修建议\n目标：减少突发停机"],
    ["AGV路径优化", "地图拓扑、车辆状态、任务队列融合\n路径规划、冲突消解、调度优化\n目标：减少等待绕路"],
    ["仓储物流优化", "订单、库位、库存、车辆统一建模\n波次、装车、配送路径优化\n目标：缩短发货时间"],
  ];
  cards.forEach((c, i) => iconCard(s, c[0], c[1], 0.6 + i * 2.52, 2.05, 2.08, 3.6, [C.cyan, C.blue, C.green, "8F7BFF", C.gold][i]));
  processArrow(s, ["经验沉淀", "数据感知", "算法建模", "工艺执行", "效果反馈"], 1.25, 6.25, 10.85, C.cyan);
}

// 3 Craft to digital
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "匠心传承与数字未来的交汇点");
  panel(s, 0.62, 1.28, 5.8, 3.2, { fill: "151A1D", line: C.gold, transparency: 0 });
  addText(s, "千年的技艺沉淀", 0.95, 1.72, 3.6, 0.32, { size: 20, bold: true, color: C.gold });
  bulletList(s, [
    "制曲、润粮、上甑、摘酒依赖老师傅经验",
    "现场判断包含看、闻、尝、听、摸等隐性知识",
    "经验价值高，但难量化、难复制、难传承",
  ], 1.0, 2.25, 4.8, 1.2, { size: 10.2, dot: C.gold });
  drawVessel(s, 4.9, 3.25, 0.75);
  panel(s, 6.9, 1.28, 5.8, 3.2, { fill: "081E32", line: C.cyan, transparency: 0 });
  addText(s, "规模化的认知瓶颈", 7.25, 1.72, 3.8, 0.32, { size: 20, bold: true, color: C.cyan });
  bulletList(s, [
    "传感器、质检、工单、设备系统产生大量数据",
    "数据分散在不同系统，难以形成工艺因果链",
    "AI要把经验、数据和执行闭环连接起来",
  ], 7.3, 2.25, 4.9, 1.2, { size: 10.2 });
  network(s, [[8.2,3.85],[8.9,3.25],[9.65,3.75],[10.4,3.05],[11.2,3.6],[11.75,2.95]], C.cyan);
  const items = [["数据感知", "采集温湿度、酒醅、设备、质检和人工记录"], ["知识沉淀", "将专家经验转化为规则、标签和可检索案例"], ["决策进化", "从预警到推荐，再到低风险环节半自动优化"]];
  items.forEach((it, i) => {
    panel(s, 0.78 + i * 4.18, 5.2, 3.65, 0.86, { fill: "0B2C42", line: i === 0 ? C.gold : C.cyan, transparency: 4 });
    addText(s, it[0], 1.0 + i * 4.18, 5.33, 1.2, 0.22, { size: 11.8, bold: true, color: i === 0 ? C.gold : C.cyan });
    addText(s, it[1], 1.0 + i * 4.18, 5.65, 3.15, 0.26, { size: 8.8, color: C.mute });
  });
}

// 4 Brewing command center
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "酿酒指挥中心", "让发酵黑盒变成可解释、可预警、可推荐的工艺地图");
  panel(s, 0.6, 1.35, 2.45, 4.85, { fill: "2B1D14", line: C.gold, transparency: 6 });
  addText(s, "行业痛点", 0.92, 1.7, 1.3, 0.28, { size: 14, bold: true, color: C.gold });
  bulletList(s, [
    "酿造周期长、变量多",
    "质量波动常到出酒后才暴露",
    "专家经验难结构化沉淀",
    "温湿度、粮曲配比、入窖条件强耦合",
  ], 0.92, 2.18, 1.9, 1.55, { size: 8.9, dot: C.gold });
  drawVessel(s, 1.8, 4.65, 0.55);
  panel(s, 3.35, 1.35, 6.1, 3.95, { fill: "08273A", line: C.cyan, transparency: 2 });
  pill(s, "工艺链路", 3.68, 1.65, 1.2, C.cyan);
  processArrow(s, ["制曲", "润粮", "上甑", "蒸馏", "摊晾", "入窖", "发酵", "评价"], 3.65, 2.2, 5.45, C.cyan);
  pill(s, "算法逻辑", 3.68, 3.0, 1.2, C.gold, { textColor: "101010" });
  const algs = [
    ["工艺预警", "LightGBM / XGBoost\nLSTM / TCN / TFT"],
    ["工艺选优", "相似批次检索\n贝叶斯优化"],
    ["建议调参", "推荐参数\n理由与风险提示"],
  ];
  algs.forEach((a, i) => {
    panel(s, 3.75 + i * 1.84, 3.45, 1.55, 1.15, { fill: "0C3550", line: i === 1 ? C.gold : C.cyan });
    addText(s, a[0], 3.87 + i * 1.84, 3.58, 1.3, 0.2, { size: 10.2, bold: true, color: i === 1 ? C.gold : C.cyan, align: "center" });
    addText(s, a[1], 3.86 + i * 1.84, 3.9, 1.34, 0.48, { size: 8.2, color: C.white, align: "center" });
  });
  panel(s, 9.82, 1.35, 2.75, 4.85, { fill: "092234", line: C.cyan, transparency: 2 });
  addText(s, "功能效益", 10.12, 1.72, 1.5, 0.28, { size: 14, bold: true, color: C.cyan });
  bulletList(s, [
    "提前发现批次偏离",
    "复用优秀批次经验",
    "提高质量稳定性与优级酒率",
    "沉淀企业专属工艺知识库",
  ], 10.12, 2.18, 2.0, 1.55, { size: 8.9 });
  addText(s, "核心转变：从“凭感觉调工艺”到“有依据地选工艺、调参数”。", 3.55, 6.12, 5.75, 0.34, { size: 13.6, bold: true, color: C.gold, align: "center" });
}

// 5 Packaging quality
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "包装智能质检", "外观检测与酒体异物检测双链路，服务高速产线在线判定");
  panel(s, 0.55, 1.35, 2.2, 4.85, { fill: "09283B", line: C.cyan });
  addText(s, "数据采集", 0.85, 1.68, 1.1, 0.25, { size: 13, bold: true, color: C.cyan });
  bulletList(s, [
    "工业相机多角度图像",
    "背光、侧光、偏振光",
    "产线节拍与触发信号",
    "人工复核与缺陷标签",
  ], 0.85, 2.1, 1.62, 1.45, { size: 8.8 });
  panel(s, 3.05, 1.35, 7.05, 4.85, { fill: "071E31", line: C.cyan });
  pill(s, "外观检测", 3.38, 1.72, 1.18, C.cyan);
  for (let i = 0; i < 5; i++) {
    shape(s, pptx.ShapeType.rect, 3.42 + i * 1.18, 2.3, 0.42, 1.08, { fill: "0A617B", line: C.cyan, transparency: 16 });
    shape(s, pptx.ShapeType.ellipse, 3.36 + i * 1.18, 2.15, 0.54, 0.22, { fill: "103A50", line: C.cyan, transparency: 5 });
    shape(s, pptx.ShapeType.rect, 3.5 + i * 1.18, 2.0, 0.25, 0.22, { fill: "BDEFFF", line: C.cyan, transparency: 15 });
  }
  addText(s, "瓶盖 / 标签 / 喷码 / 液位 / 盒箱\nYOLO、Mask R-CNN、ViT、PatchCore", 4.7, 2.0, 3.6, 0.58, { size: 10.2, color: C.white, align: "center" });
  pill(s, "酒体异物", 3.38, 3.85, 1.18, C.gold, { textColor: "101010" });
  processArrow(s, ["旋瓶", "多光源", "视频帧", "轨迹分析", "NG剔除"], 3.45, 4.45, 5.85, C.gold);
  addText(s, "重点区分：真实异物、气泡、酒液晃动、瓶壁污点与玻璃反光", 3.55, 5.25, 5.65, 0.25, { size: 10.2, color: C.gold, align: "center" });
  panel(s, 10.45, 1.35, 2.35, 4.85, { fill: "09283B", line: C.cyan });
  addText(s, "功能效益", 10.75, 1.68, 1.1, 0.25, { size: 13, bold: true, color: C.cyan });
  bulletList(s, [
    "降低人工目检压力",
    "减少漏检与误杀",
    "缺陷按批次、材料、设备追溯",
    "形成持续更新的缺陷图库",
  ], 10.75, 2.1, 1.72, 1.45, { size: 8.8 });
  addText(s, "质检AI的关键不是“拍图”，而是光学工艺、缺陷样本库和在线模型共同稳定。", 2.2, 6.38, 9.0, 0.28, { size: 13, bold: true, color: C.gold, align: "center" });
}

// 6 Predictive maintenance
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "设备预测性维护", "从被动抢修转向主动预防，提前识别设备状态劣化");
  drawVessel(s, 4.25, 3.42, 0.95);
  panel(s, 0.6, 1.75, 2.55, 3.95, { fill: "09283B", line: C.cyan });
  addText(s, "设备数据", 0.9, 2.05, 1.2, 0.25, { size: 13, bold: true, color: C.cyan });
  bulletList(s, [
    "电流、电压、振动",
    "温度、压力、速度",
    "负载、启停、报警码",
    "维修工单与备件记录",
  ], 0.9, 2.48, 1.8, 1.42, { size: 9 });
  const mids = [["工况识别", "开机 / 稳态 / 换型 / 清洗"], ["异常检测", "Isolation Forest\nOne-Class SVM\nLSTM Autoencoder"], ["故障预测", "XGBoost / Transformer\nRUL剩余寿命"]];
  mids.forEach((m, i) => {
    panel(s, 6.2, 1.65 + i * 1.37, 2.2, 0.9, { fill: "0C3550", line: [C.cyan, C.gold, C.green][i] });
    addText(s, m[0], 6.42, 1.82 + i * 1.37, 0.9, 0.2, { size: 11.3, bold: true, color: [C.cyan, C.gold, C.green][i] });
    addText(s, m[1], 7.25, 1.73 + i * 1.37, 0.9, 0.42, { size: 8.3, color: C.white, align: "center" });
    line(s, 5.2, 3.4, 6.1, 2.1 + i * 1.37, [C.cyan, C.gold, C.green][i], 1.1, true);
  });
  panel(s, 9.2, 1.55, 3.0, 4.45, { fill: "09283B", line: C.cyan });
  addText(s, "输出动作", 9.55, 1.88, 1.2, 0.25, { size: 13, bold: true, color: C.cyan });
  bulletList(s, [
    "设备健康评分",
    "故障概率与剩余寿命",
    "建议维修窗口",
    "备件需求与停机影响",
    "维修结果回流模型",
  ], 9.55, 2.32, 2.1, 1.75, { size: 9 });
  addText(s, "价值：减少突发停机，把维修经验沉淀为可复用的设备知识库。", 2.8, 6.38, 7.9, 0.3, { size: 13.2, bold: true, color: C.gold, align: "center" });
}

// 7 AGV
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "AGV路径优化", "任务分配、路径规划、冲突消解和仿真评估联合优化");
  panel(s, 0.55, 1.38, 2.25, 4.7, { fill: "09283B", line: C.cyan });
  addText(s, "数据采集", 0.86, 1.72, 1.1, 0.25, { size: 13, bold: true, color: C.cyan });
  bulletList(s, [
    "厂区地图、节点、禁行区",
    "任务起点、终点、优先级",
    "车辆位置、电量、状态",
    "等待、拥堵、冲突记录",
  ], 0.86, 2.16, 1.68, 1.45, { size: 8.8 });
  panel(s, 3.05, 1.35, 6.6, 4.85, { fill: "061D31", line: C.cyan });
  const pts = [[3.85,4.85],[4.55,3.9],[5.45,4.55],[6.25,3.25],[7.2,4.1],[8.05,3.1],[8.75,4.75]];
  network(s, pts, C.cyan);
  pts.forEach(([x,y],i)=> addText(s, String(i+1), x-0.08, y-0.11, 0.16, 0.12, { size: 6.5, bold: true, color: "051822", align: "center" }));
  pill(s, "地图拓扑", 3.55, 2.02, 1.1, C.cyan);
  pill(s, "任务队列", 5.22, 2.02, 1.1, C.gold, { textColor: "101010" });
  pill(s, "车辆状态", 6.9, 2.02, 1.1, C.green, { textColor: "062018" });
  pill(s, "冲突消解", 7.42, 5.34, 1.2, "8F7BFF", { textColor: "FFFFFF" });
  addText(s, "A* / Dijkstra\nOR-Tools\n遗传算法 / 蚁群算法", 4.55, 5.22, 2.25, 0.52, { size: 9.8, bold: true, color: C.gold, align: "center" });
  panel(s, 10.0, 1.38, 2.65, 4.7, { fill: "09283B", line: C.cyan });
  addText(s, "功能效益", 10.32, 1.72, 1.1, 0.25, { size: 13, bold: true, color: C.cyan });
  bulletList(s, [
    "减少等待、空驶和绕路",
    "降低节点拥堵与死锁",
    "提高任务准时率",
    "用仿真先验证上线风险",
  ], 10.32, 2.16, 1.9, 1.45, { size: 8.9 });
  addText(s, "AGV效率问题不是单车路径，而是任务释放、车辆分配和节点占用的全局协同。", 2.0, 6.38, 9.3, 0.28, { size: 13.1, bold: true, color: C.gold, align: "center" });
}

// 8 Warehouse
{
  const s = pptx.addSlide();
  bg(s);
  title(s, "仓储物流优化", "订单、库位、装车与配送路径统一建模");
  panel(s, 0.65, 1.45, 2.65, 4.75, { fill: "09283B", line: C.cyan });
  addText(s, "工艺介绍", 0.95, 1.78, 1.1, 0.25, { size: 13, bold: true, color: C.cyan });
  bulletList(s, [
    "订单进入、库存定位、库位分配",
    "波次拣选、装车排程、配送路径",
    "多仓装货、多客户混装、时间窗约束",
  ], 0.95, 2.22, 1.95, 1.2, { size: 8.8 });
  for (let i = 0; i < 16; i++) {
    shape(s, pptx.ShapeType.rect, 5.2 + (i % 4) * 0.38, 3.55 - Math.floor(i / 4) * 0.28, 0.34, 0.22, { fill: i % 2 ? "C28E50" : "A86D3F", line: "53361D", width: 0.4 });
  }
  network(s, [[6.9,3.55],[7.45,2.7],[8.1,3.15],[8.55,2.35],[9.2,3.0],[9.75,2.45],[10.45,3.25],[10.85,2.55]], C.cyan);
  const steps = [["1. 库位优化", "ABC分类、SKU关联度、出库频次"], ["2. 波次排程", "客户、路线、时间窗、产品组合"], ["3. 装车排序", "车辆容量、月台、装载约束"], ["4. 路径优化", "VRP / MDVRP / VRPTW"]];
  steps.forEach((st, i) => {
    shape(s, pptx.ShapeType.chevron, 9.75, 1.35 + i * 1.15, 2.7, 0.7, { fill: i % 2 ? "0C4B73" : "0A3757", line: C.cyan });
    addText(s, st[0], 10.02, 1.49 + i * 1.15, 1.15, 0.2, { size: 10.4, bold: true, color: C.white });
    addText(s, st[1], 11.05, 1.45 + i * 1.15, 1.15, 0.28, { size: 7.9, color: C.mute });
  });
  panel(s, 3.75, 5.55, 4.9, 0.68, { fill: "071E31", line: C.gold });
  addText(s, "核心算法：OR-Tools / ALNS / VNS / 遗传算法", 4.0, 5.78, 4.35, 0.18, { size: 11.5, bold: true, color: C.gold, align: "center" });
  addText(s, "价值：缩短装车发货时间，提高库位利用率、车辆满载率和配送效率。", 2.2, 6.38, 9.0, 0.28, { size: 13.1, bold: true, color: C.gold, align: "center" });
}

// 9 Roadmap
{
  const s = pptx.addSlide();
  bg(s, "light");
  title(s, "分阶段推进建议与实施路径");
  const steps = [
    ["0-2个月", "基础数据与样板设计", "梳理数据源、采集口径、业务指标与样板场景边界"],
    ["3-6个月", "POC验证与模型上线", "完成酿酒预警、外观质检、设备异常检测等样板验证"],
    ["6-12个月", "业务闭环与系统联动", "打通MES/WMS/SCADA/质检/工单，形成反馈闭环"],
    ["12个月以上", "全链路闭环优化", "沉淀企业专属模型，扩展到跨场景联动优化"],
  ];
  steps.forEach((st, i) => {
    const x = 0.9 + i * 3.05;
    const y = 4.9 - i * 0.62;
    shape(s, pptx.ShapeType.chevron, x, y, 2.65, 0.72, { fill: ["0B709D","0E8AB6","1AB8D4","62DDEB"][i], line: C.cyan, transparency: 8 });
    panel(s, x - 0.05, y + 0.86, 2.55, 1.15, { fill: "08273B", line: C.cyan, transparency: 4 });
    addText(s, st[0], x + 0.12, y + 1.02, 1.0, 0.2, { size: 10.8, bold: true, color: C.gold });
    addText(s, st[1], x + 0.12, y + 1.35, 1.95, 0.22, { size: 10.6, bold: true, color: C.white });
    addText(s, st[2], x + 0.12, y + 1.68, 2.05, 0.34, { size: 7.9, color: C.mute });
  });
  addText(s, "实施原则：先做可验证样板，再做业务闭环；先辅助决策，再逐步探索低风险半自动优化。", 1.1, 6.52, 11.1, 0.28, { size: 13, bold: true, color: C.white, align: "center" });
}

// 10 Reference
{
  const s = pptx.addSlide();
  bg(s, "light");
  title(s, "标杆案例与前沿技术背书（参考资料）");
  const refs = [
    ["酒企案例", "五粮液数字化车间\n泸州老窖智能酿造\n洋河智能工厂实践"],
    ["质检案例", "康耐视机器视觉\n海康机器人视觉检测\n医药瓶检与异物检测设备"],
    ["算法技术", "YOLO / Mask R-CNN / ViT\nLSTM / TFT / Transformer\nPatchCore / Autoencoder"],
    ["优化技术", "OR-Tools路径优化\nALNS / VNS启发式算法\n数字孪生仿真评估"],
    ["工艺平台", "MES / WMS / SCADA\n质检系统 / 设备工单\n知识库与RAG问答"],
    ["沉淀方向", "工艺知识图谱\n专家经验结构化\n企业专属生产大模型"],
  ];
  refs.forEach((r, i) => {
    const x = i % 2 ? 7.05 : 1.05;
    const y = 1.45 + Math.floor(i / 2) * 1.35;
    panel(s, x, y, 5.0, 0.9, { fill: "08273B", line: C.cyan, transparency: 4 });
    addText(s, r[0], x + 0.22, y + 0.18, 1.3, 0.22, { size: 11, bold: true, color: C.gold });
    addText(s, r[1], x + 1.55, y + 0.14, 3.1, 0.5, { size: 8.6, color: C.white });
  });
  addLogo(s, 5.95, 5.88, 0.76, 0.76);
  addText(s, "感谢聆听", 5.0, 6.45, 2.7, 0.28, { size: 18, bold: true, color: C.white, align: "center" });
  addText(s, "以生产工艺为主线，把AI嵌入数据、模型、执行和反馈闭环。", 3.65, 6.82, 5.4, 0.18, { size: 9.5, color: C.mute, align: "center" });
}

const out = path.join(outDir, "Jinshiyuan_AI_Production_Blueprint_可编辑版.pptx");
pptx.writeFile({ fileName: out });
