const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const { imageSizingCrop } = require("./pptxgenjs_helpers/image");
const { warnIfSlideElementsOutOfBounds } = require("./pptxgenjs_helpers/layout");
const { safeOuterShadow } = require("./pptxgenjs_helpers/util");

const ROOT = __dirname;
const OUT_DIR = path.join(ROOT, "output");
fs.mkdirSync(OUT_DIR, { recursive: true });

const ASSETS = {
  panorama: path.join(ROOT, "assets", "wwtp_panorama.jpeg"),
};

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "江苏南大五维电子科技有限公司";
pptx.subject = "污水处理三模型算法补充页";
pptx.title = "污水处理三模型算法补充页";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const C = {
  navy: "113E6B",
  blue: "2E86DE",
  cyan: "2BB3D3",
  green: "20A46A",
  orange: "F59E0B",
  red: "EA5A47",
  ink: "1F2937",
  gray: "5A6C82",
  line: "CFE0F0",
  pale: "F5FAFF",
  light: "EAF4FF",
  white: "FFFFFF",
  darkBlue: "0D5CAB",
};

function addHeader(slide, title, label) {
  slide.background = { color: C.white };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: 0.78,
    line: { color: C.navy, transparency: 100 },
    fill: { color: C.navy },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 5.3,
    h: 0.78,
    line: { color: C.blue, transparency: 100 },
    fill: { color: C.blue },
  });
  slide.addText(title, {
    x: 0.32,
    y: 0.15,
    w: 8.5,
    h: 0.34,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 22,
    bold: true,
    color: C.white,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 11.12,
    y: 0.16,
    w: 1.05,
    h: 0.34,
    rectRadius: 0.05,
    line: { color: "62AEFF", width: 1 },
    fill: { color: C.darkBlue },
  });
  slide.addText(label, {
    x: 11.12,
    y: 0.22,
    w: 1.05,
    h: 0.16,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10,
    bold: true,
    color: C.white,
  });
  slide.addText("南大五维", {
    x: 12.18,
    y: 0.19,
    w: 0.82,
    h: 0.16,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 10,
    bold: true,
    color: C.white,
    align: "right",
  });
}

function addFooter(slide, text) {
  slide.addShape(pptx.ShapeType.line, {
    x: 0.45,
    y: 6.98,
    w: 12.35,
    h: 0,
    line: { color: C.line, width: 1.1 },
  });
  slide.addText(text, {
    x: 0.48,
    y: 7.03,
    w: 12.25,
    h: 0.16,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 7.2,
    color: "72859D",
    align: "right",
  });
}

function addIntro(slide, text) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.55,
    y: 0.98,
    w: 12.2,
    h: 0.52,
    rectRadius: 0.04,
    line: { color: C.line, width: 1 },
    fill: { color: C.light },
  });
  slide.addText(text, {
    x: 0.75,
    y: 1.13,
    w: 11.8,
    h: 0.18,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 11.1,
    bold: true,
    color: C.navy,
  });
}

function addPill(slide, x, y, w, h, text, color, fontSize = 10.5) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.04,
    line: { color, width: 1 },
    fill: { color: C.white },
  });
  slide.addText(text, {
    x,
    y: y + 0.11,
    w,
    h: h - 0.12,
    margin: 0,
    align: "center",
    valign: "mid",
    fontFace: "Microsoft YaHei",
    fontSize,
    bold: true,
    color: C.ink,
  });
}

function addNode(slide, { x, y, w, h, title, body, color, bodySize = 9.6 }) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.06,
    line: { color, width: 1.2 },
    fill: { color: C.white },
    shadow: safeOuterShadow("ABC5DE", 0.14, 45, 2, 1),
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 0.12,
    y: y + 0.12,
    w: Math.min(w - 0.24, 1.5),
    h: 0.34,
    rectRadius: 0.04,
    line: { color, transparency: 100 },
    fill: { color },
  });
  slide.addText(title, {
    x: x + 0.18,
    y: y + 0.205,
    w: w - 0.3,
    h: 0.14,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 11.5,
    bold: true,
    color: C.white,
  });
  slide.addText(body, {
    x: x + 0.16,
    y: y + 0.58,
    w: w - 0.32,
    h: h - 0.74,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: bodySize,
    color: C.ink,
    valign: "top",
  });
}

function addPanel(slide, x, y, w, h, title) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    line: { color: C.line, width: 1.1 },
    fill: { color: "FBFDFF" },
  });
  slide.addText(title, {
    x: x + 0.18,
    y: y + 0.16,
    w: w - 0.36,
    h: 0.18,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 14,
    bold: true,
    color: C.navy,
  });
}

function addArrow(slide, x, y, w, h = 0, color = C.line, dash) {
  const line = { color, width: 1.2, beginArrowType: "none", endArrowType: "triangle" };
  if (dash) line.dash = dash;
  slide.addShape(pptx.ShapeType.line, { x, y, w, h, line });
}

function addInfoRow(slide, x, y, label, text, color, w = 4.4) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w: 1.1,
    h: 0.4,
    rectRadius: 0.04,
    line: { color, transparency: 100 },
    fill: { color },
  });
  slide.addText(label, {
    x,
    y: y + 0.1,
    w: 1.1,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10.3,
    bold: true,
    color: C.white,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 1.22,
    y,
    w: w,
    h: 0.4,
    rectRadius: 0.04,
    line: { color, width: 1 },
    fill: { color: "FFFFFF" },
  });
  slide.addText(text, {
    x: x + 1.37,
    y: y + 0.1,
    w: w - 0.25,
    h: 0.16,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 9.6,
    color: C.ink,
  });
}

function addMetricStrip(slide, y, items, color) {
  const boxW = 2.93;
  items.forEach((item, idx) => {
    const x = 0.6 + idx * 3.15;
    slide.addShape(pptx.ShapeType.roundRect, {
      x,
      y,
      w: boxW,
      h: 0.52,
      rectRadius: 0.04,
      line: { color, width: 1 },
      fill: { color: "FFFFFF" },
    });
    slide.addText(item, {
      x: x + 0.08,
      y: y + 0.14,
      w: boxW - 0.16,
      h: 0.18,
      margin: 0,
      align: "center",
      fontFace: "Microsoft YaHei",
      fontSize: 9.6,
      bold: true,
      color: C.ink,
    });
  });
}

function finalize(slide) {
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function buildSlide1() {
  const slide = pptx.addSlide();
  addHeader(slide, "三模型算法总体架构", "补充 01");
  addIntro(slide, "方案围绕“在线感知-数据治理-状态识别-趋势预测-优化控制-执行反馈”形成统一算法闭环，三套模型共用同一套数据与控制底座。");

  const nodes = [
    { x: 0.62, y: 1.78, t: "在线感知", b: "水质\n设备\n药耗", c: C.cyan },
    { x: 2.68, y: 1.78, t: "数据治理", b: "清洗\n对齐\n特征", c: C.blue },
    { x: 4.74, y: 1.78, t: "状态识别", b: "分类\n告警\n分型", c: C.green },
    { x: 6.8, y: 1.78, t: "趋势预测", b: "短时\n中时\n窗口", c: C.orange },
    { x: 8.86, y: 1.78, t: "优化控制", b: "投药\n能耗\n约束", c: C.blue },
    { x: 10.92, y: 1.78, t: "执行反馈", b: "泵阀\n清洗\n回写", c: C.green },
  ];
  nodes.forEach((n) => addPill(slide, n.x, n.y, 1.62, 0.64, `${n.t}\n${n.b}`, n.c, 10.2));
  for (let i = 0; i < nodes.length - 1; i++) addArrow(slide, nodes[i].x + 1.62, 2.1, 0.36, 0);
  addArrow(slide, 11.72, 2.42, 0, 0.44, C.red);
  addArrow(slide, 11.72, 2.86, -8.18, 0, C.red, "dash");
  addArrow(slide, 3.54, 2.86, 0, -0.36, C.red);

  addNode(slide, {
    x: 0.6,
    y: 3.1,
    w: 3.95,
    h: 2.92,
    title: "膜污染预判与清洗",
    body:
      "输入：TMP、压差、通量、浊度、清洗记录\n算法：EWMA / Isolation Forest + RF / XGBoost + LSTM / TCN\n输出：污染分型、清洗窗口、清洗配方和时长",
    color: C.blue,
    bodySize: 10.2,
  });
  addNode(slide, {
    x: 4.69,
    y: 3.1,
    w: 3.95,
    h: 2.92,
    title: "锅炉给水水质与药剂协同",
    body:
      "输入：pH、流量、温度、凝结水回流、加药泵状态\n算法：CatBoost / XGBoost + LSTM / GRU + MPC / NSGA-II\n输出：氨水等药剂投加量、阈值保护和联动控制量",
    color: C.green,
    bodySize: 10.2,
  });
  addNode(slide, {
    x: 8.78,
    y: 3.1,
    w: 3.95,
    h: 2.92,
    title: "深度水处理硬度调节",
    body:
      "输入：原水硬度、流量、浊度、碱度、出水硬度\n算法：XGBoost / CatBoost + TCN / Transformer + MPC / BayesOpt\n输出：碳酸钠投加量、目标区间命中率与波动收敛速度",
    color: C.orange,
    bodySize: 10.2,
  });

  slide.addImage({
    path: ASSETS.panorama,
    ...imageSizingCrop(ASSETS.panorama, 9.72, 4.86, 2.5, 0.86),
  });

  addFooter(slide, "参考：Environments 2023；Sensors 2023；Water Research 2023/2024；Nature Sustainability 2026。");
  finalize(slide);
}

function buildSlide2() {
  const slide = pptx.addSlide();
  addHeader(slide, "模型一：膜污染预判与清洗算法架构", "补充 02");
  addIntro(slide, "膜污染模型从污染征兆、污染类型、污染趋势和清洗动作四个层次展开，输出“何时洗、怎么洗、洗多久”的完整清洗指令。");

  addPanel(slide, 0.55, 1.7, 7.15, 4.95, "算法架构图");
  addPill(slide, 0.9, 2.12, 1.26, 0.5, "TMP / 压差", C.blue, 10);
  addPill(slide, 2.3, 2.12, 1.18, 0.5, "通量", C.cyan, 10);
  addPill(slide, 3.62, 2.12, 1.22, 0.5, "浊度 / SDI", C.green, 10);
  addPill(slide, 4.98, 2.12, 1.46, 0.5, "清洗历史", C.orange, 10);
  addArrow(slide, 1.53, 2.62, 0.72, 0.34);
  addArrow(slide, 2.88, 2.62, 0.72, 0.34);
  addArrow(slide, 4.23, 2.62, 0.72, 0.34);
  addArrow(slide, 5.75, 2.62, -0.75, 0.34);

  addNode(slide, {
    x: 2.08,
    y: 3.02,
    w: 4.1,
    h: 0.9,
    title: "数据治理",
    body: "缺失补全、异常剔除、时滞对齐、特征构造",
    color: C.blue,
    bodySize: 10.3,
  });
  addArrow(slide, 4.1, 3.92, 0, 0.28);
  addNode(slide, {
    x: 0.92,
    y: 4.22,
    w: 2.36,
    h: 1.02,
    title: "征兆识别",
    body: "EWMA\nIsolation Forest",
    color: C.cyan,
    bodySize: 10,
  });
  addNode(slide, {
    x: 3.0,
    y: 4.22,
    w: 2.62,
    h: 1.02,
    title: "污染分类",
    body: "RF / XGBoost / SVM\n区分结垢、有机、胶体、生物污染",
    color: C.green,
    bodySize: 9.2,
  });
  addNode(slide, {
    x: 5.38,
    y: 4.22,
    w: 1.72,
    h: 1.02,
    title: "趋势预测",
    body: "LSTM\nTCN",
    color: C.orange,
    bodySize: 10,
  });
  addArrow(slide, 2.1, 5.24, 0.86, 0.34);
  addArrow(slide, 4.31, 5.24, 1.08, 0.34);

  addNode(slide, {
    x: 2.36,
    y: 5.3,
    w: 3.55,
    h: 0.72,
    title: "清洗策略生成",
    body: "规则库 + Bayes 优化联动配方、浓度、时长和触发时点",
    color: C.red,
    bodySize: 9.2,
  });
  addArrow(slide, 5.91, 5.66, 0.64, 0);
  addPill(slide, 6.62, 5.45, 0.82, 0.42, "输出", C.red, 10.1);

  addPanel(slide, 7.95, 1.7, 4.83, 4.95, "架构说明");
  addInfoRow(slide, 8.18, 2.18, "输入", "TMP、压差、通量、浊度、清洗记录、膜龄", C.blue, 3.18);
  addInfoRow(slide, 8.18, 2.76, "识别", "EWMA 和 Isolation Forest 捕捉早期异常", C.cyan, 3.18);
  addInfoRow(slide, 8.18, 3.34, "分类", "RF / XGBoost / SVM 输出污染类型", C.green, 3.18);
  addInfoRow(slide, 8.18, 3.92, "预测", "LSTM / TCN 计算未来清洗窗口", C.orange, 3.18);
  addInfoRow(slide, 8.18, 4.5, "动作", "规则库 + Bayes 优化生成清洗方案", C.red, 3.18);
  addInfoRow(slide, 8.18, 5.08, "结果", "输出预警、清洗配方、浓度、时长", C.blue, 3.18);

  addMetricStrip(slide, 6.18, [
    "预警提前量：至少覆盖 6 小时人工处置窗口",
    "识别准确率：污染分型与清洗效果一一对应",
    "误报控制：避免无效清洗和过度清洗",
    "寿命目标：把清洗效果与膜寿命一起考核",
  ], C.blue);

  addFooter(slide, "参考：Membranes 2023；Advanced Membranes 2023；Nature Sustainability 2026。");
  finalize(slide);
}

function buildSlide3() {
  const slide = pptx.addSlide();
  addHeader(slide, "模型二：锅炉给水水质与药剂协同算法架构", "补充 03");
  addIntro(slide, "锅炉给水模型围绕 pH 稳定、药剂协同和约束控制展开，控制器既处理实时阈值动作，也处理短时趋势与多变量联动。");

  addPanel(slide, 0.55, 1.7, 7.15, 4.95, "算法架构图");
  addPill(slide, 0.9, 2.12, 1.2, 0.5, "pH", C.blue, 10.5);
  addPill(slide, 2.22, 2.12, 1.2, 0.5, "流量", C.cyan, 10.5);
  addPill(slide, 3.54, 2.12, 1.2, 0.5, "温度", C.green, 10.5);
  addPill(slide, 4.86, 2.12, 1.62, 0.5, "泵阀状态", C.orange, 10.2);

  addNode(slide, {
    x: 1.66,
    y: 3.0,
    w: 5.0,
    h: 0.86,
    title: "数据治理",
    body: "采样统一、异常剔除、特征组合、回流与流量耦合关系整理",
    color: C.blue,
    bodySize: 9.8,
  });
  addArrow(slide, 4.1, 3.86, 0, 0.24);
  addNode(slide, {
    x: 0.96,
    y: 4.16,
    w: 2.16,
    h: 0.98,
    title: "短时估计",
    body: "CatBoost\nXGBoost",
    color: C.cyan,
    bodySize: 10,
  });
  addNode(slide, {
    x: 3.24,
    y: 4.16,
    w: 1.98,
    h: 0.98,
    title: "趋势预测",
    body: "LSTM\nGRU / TCN",
    color: C.green,
    bodySize: 9.6,
  });
  addNode(slide, {
    x: 5.34,
    y: 4.16,
    w: 1.54,
    h: 0.98,
    title: "保护层",
    body: "阈值\n滞回",
    color: C.red,
    bodySize: 10,
  });
  addArrow(slide, 2.0, 5.14, 1.26, 0.34);
  addArrow(slide, 4.23, 5.14, 1.14, 0.34);
  addNode(slide, {
    x: 2.24,
    y: 5.26,
    w: 3.72,
    h: 0.78,
    title: "投药优化与联动控制",
    body: "MPC / NSGA-II 计算药剂投加量、联动泵频和执行边界",
    color: C.orange,
    bodySize: 9.2,
  });
  addArrow(slide, 5.96, 5.62, 0.8, 0);
  addPill(slide, 6.78, 5.41, 0.72, 0.42, "执行", C.orange, 10.2);

  addPanel(slide, 7.95, 1.7, 4.83, 4.95, "架构说明");
  addInfoRow(slide, 8.18, 2.18, "输入", "pH、流量、温度、回流、泵阀状态", C.blue, 3.18);
  addInfoRow(slide, 8.18, 2.76, "估计", "CatBoost / XGBoost 计算当前状态", C.cyan, 3.18);
  addInfoRow(slide, 8.18, 3.34, "预测", "LSTM / GRU / TCN 预测 10-30 分钟走势", C.green, 3.18);
  addInfoRow(slide, 8.18, 3.92, "保护", "阈值与滞回负责快速止损和回退", C.red, 3.18);
  addInfoRow(slide, 8.18, 4.5, "控制", "MPC / NSGA-II 处理投药量和联动边界", C.orange, 3.18);
  addInfoRow(slide, 8.18, 5.08, "输出", "给出投药量、执行量和回切条件", C.blue, 3.18);

  addMetricStrip(slide, 6.18, [
    "控制目标：pH 长时间稳定在 8.8-9.3 区间",
    "经济指标：氨水等药剂的吨水消耗量",
    "稳定指标：过冲幅度、振荡次数、恢复时间",
    "安全指标：异常触发后的回切和人工接管速度",
  ], C.green);

  addFooter(slide, "参考：Water Research 2023；Computers & Chemical Engineering 2025；Water Research 2024。");
  finalize(slide);
}

function buildSlide4() {
  const slide = pptx.addSlide();
  addHeader(slide, "模型三：深度水处理硬度调节算法架构", "补充 04");
  addIntro(slide, "硬度调节模型同时处理原水波动、药剂前馈和出水反馈，把碳酸钠投加动作收敛到稳定命中区间的闭环控制。");

  addPanel(slide, 0.55, 1.7, 7.15, 4.95, "算法架构图");
  addPill(slide, 0.9, 2.12, 1.48, 0.5, "原水硬度", C.blue, 10.2);
  addPill(slide, 2.54, 2.12, 1.14, 0.5, "流量", C.cyan, 10.5);
  addPill(slide, 3.84, 2.12, 1.14, 0.5, "浊度", C.green, 10.5);
  addPill(slide, 5.14, 2.12, 1.3, 0.5, "出水硬度", C.orange, 10.2);

  addNode(slide, {
    x: 1.72,
    y: 3.0,
    w: 4.9,
    h: 0.86,
    title: "数据治理",
    body: "缺失补全、异常值剔除、时滞对齐、波动特征提取",
    color: C.blue,
    bodySize: 9.8,
  });
  addArrow(slide, 4.1, 3.86, 0, 0.24);
  addNode(slide, {
    x: 1.02,
    y: 4.16,
    w: 2.24,
    h: 0.98,
    title: "状态估计",
    body: "XGBoost\nCatBoost",
    color: C.cyan,
    bodySize: 10,
  });
  addNode(slide, {
    x: 3.4,
    y: 4.16,
    w: 2.02,
    h: 0.98,
    title: "趋势预测",
    body: "TCN\nTransformer",
    color: C.green,
    bodySize: 10,
  });
  addNode(slide, {
    x: 5.56,
    y: 4.16,
    w: 1.24,
    h: 0.98,
    title: "反馈量",
    body: "偏差\n校正",
    color: C.red,
    bodySize: 10,
  });
  addArrow(slide, 2.14, 5.14, 1.3, 0.34);
  addArrow(slide, 4.42, 5.14, 1.18, 0.34);
  addNode(slide, {
    x: 2.34,
    y: 5.26,
    w: 3.66,
    h: 0.78,
    title: "投药控制",
    body: "前馈 + 反馈 + MPC / BayesOpt 计算碳酸钠投加量",
    color: C.orange,
    bodySize: 9.2,
  });
  addArrow(slide, 6.0, 5.62, 0.76, 0);
  addPill(slide, 6.78, 5.41, 0.72, 0.42, "执行", C.orange, 10.2);

  addPanel(slide, 7.95, 1.7, 4.83, 4.95, "架构说明");
  addInfoRow(slide, 8.18, 2.18, "输入", "原水硬度、流量、浊度、出水硬度、碱度", C.blue, 3.18);
  addInfoRow(slide, 8.18, 2.76, "估计", "XGBoost / CatBoost 计算当前药剂需求", C.cyan, 3.18);
  addInfoRow(slide, 8.18, 3.34, "预测", "TCN / Transformer 预测 30-60 分钟波动", C.green, 3.18);
  addInfoRow(slide, 8.18, 3.92, "控制", "前馈 + 反馈 + MPC / BayesOpt 计算投加量", C.orange, 3.18);
  addInfoRow(slide, 8.18, 4.5, "反馈", "目标区间命中后持续修偏，抑制超调", C.red, 3.18);
  addInfoRow(slide, 8.18, 5.08, "输出", "输出投药量、目标区间命中率和收敛速度", C.blue, 3.18);

  addMetricStrip(slide, 6.18, [
    "目标区间：出水硬度稳定命中 270-280 mg/L",
    "成本指标：碳酸钠吨水消耗和波动损失",
    "控制指标：命中率、方差、收敛时间、超调量",
    "运维指标：模型漂移发现速度和回标速度",
  ], C.orange);

  addFooter(slide, "参考：Sensors 2023；Engineering Proceedings 2026；Industrial Water Treatment 2024。");
  finalize(slide);
}

function buildSlide5() {
  const slide = pptx.addSlide();
  addHeader(slide, "算法分层与实施节奏", "补充 05");
  addIntro(slide, "整套方案分为基线层、增强层和前沿层三段推进：先把识别、预测、控制闭环做稳，再把长依赖、多变量和自适应能力逐步叠加。");

  addNode(slide, {
    x: 0.58,
    y: 1.72,
    w: 7.98,
    h: 1.18,
    title: "基线层",
    body:
      "RF / XGBoost / CatBoost 负责分类与状态估计；LSTM / GRU / TCN 负责短时预测；MPC / NSGA-II 负责约束控制和药耗优化。",
    color: C.green,
    bodySize: 10.2,
  });
  addNode(slide, {
    x: 0.58,
    y: 3.18,
    w: 7.98,
    h: 1.18,
    title: "增强层",
    body:
      "Transformer / GAT 处理多变量长依赖；SHAP 与漂移检测解释模型行为并盯住季节性变化；数字孪生把离线验证和在线控制接起来。",
    color: C.blue,
    bodySize: 10.2,
  });
  addNode(slide, {
    x: 0.58,
    y: 4.64,
    w: 7.98,
    h: 1.18,
    title: "前沿层",
    body:
      "Koopman EMPC、Physics-informed ML、Safe RL 处理更强的非线性和自适应控制，但前提是历史数据、边界规则和仿真底座已经完整。",
    color: C.orange,
    bodySize: 10.2,
  });

  addPanel(slide, 8.92, 1.72, 3.86, 4.62, "实施节奏");
  const steps = [
    "阶段 1：统一采样频率、缺失补全、异常剔除和时滞对齐，形成标准训练样本。",
    "阶段 2：完成分类模型、短时预测模型和规则保护层，建立可解释基线。",
    "阶段 3：把 MPC / NSGA-II 接入执行闭环，量化药耗、能耗和稳定性收益。",
    "阶段 4：在灰度环境中引入 Transformer / GAT / Koopman EMPC 等增强能力。",
  ];
  steps.forEach((step, idx) => {
    const y = 2.18 + idx * 0.93;
    slide.addShape(pptx.ShapeType.ellipse, {
      x: 9.16,
      y,
      w: 0.34,
      h: 0.34,
      line: { color: C.blue, width: 1 },
      fill: { color: C.blue },
    });
    slide.addText(String(idx + 1), {
      x: 9.16,
      y: y + 0.085,
      w: 0.34,
      h: 0.12,
      margin: 0,
      fontFace: "Microsoft YaHei",
      fontSize: 9,
      bold: true,
      color: C.white,
      align: "center",
    });
    if (idx < steps.length - 1) {
      slide.addShape(pptx.ShapeType.line, {
        x: 9.33,
        y: y + 0.34,
        w: 0,
        h: 0.58,
        line: { color: C.line, width: 1.1 },
      });
    }
    slide.addText(step, {
      x: 9.72,
      y: y + 0.02,
      w: 2.7,
      h: 0.34,
      margin: 0,
      fontFace: "Microsoft YaHei",
      fontSize: 9.8,
      color: C.ink,
    });
  });

  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.58,
    y: 6.02,
    w: 12.2,
    h: 0.56,
    rectRadius: 0.04,
    line: { color: C.line, width: 1 },
    fill: { color: C.light },
  });
  slide.addText("页面口径统一按“输入-算法-输出-控制逻辑”展开：先讲清结构，再讲清算法分工，最后落到控制动作和考核指标。", {
    x: 0.78,
    y: 6.18,
    w: 11.8,
    h: 0.16,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10.8,
    bold: true,
    color: C.navy,
  });

  addFooter(slide, "参考：Nature Sustainability 2026；Sensors 2023；Water Research 2023/2024；Computers & Chemical Engineering 2025。");
  finalize(slide);
}

async function main() {
  buildSlide1();
  buildSlide2();
  buildSlide3();
  buildSlide4();
  buildSlide5();
  const outPath = path.join(OUT_DIR, "污水处理三模型算法补充页.pptx");
  await pptx.writeFile({ fileName: outPath });
  console.log(`WROTE ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
