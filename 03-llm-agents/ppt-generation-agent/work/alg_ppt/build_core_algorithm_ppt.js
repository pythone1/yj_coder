const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const { imageSizingCrop } = require("./pptxgenjs_helpers/image");
const { warnIfSlideElementsOutOfBounds } = require("./pptxgenjs_helpers/layout");
const { safeOuterShadow } = require("./pptxgenjs_helpers/util");

const ROOT = __dirname;
const PROJECT_ROOT = path.resolve(ROOT, "..", "..");
const OUT_DIR = path.join(ROOT, "output");
fs.mkdirSync(OUT_DIR, { recursive: true });

const ASSETS = {
  panorama: path.join(ROOT, "assets", "wwtp_panorama.jpeg"),
};

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "江苏南大五维电子科技有限公司";
pptx.subject = "水处理智能精准控制一体化项目核心算法架构";
pptx.title = "水处理智能精准控制一体化项目核心算法架构详解";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const C = {
  navy: "0E355C",
  deepBlue: "165D9C",
  blue: "2E86DE",
  cyan: "2EB8D3",
  green: "23A36C",
  orange: "F59F0A",
  red: "EC5B4F",
  gold: "C58B18",
  ink: "1F2937",
  gray: "5D6B80",
  light: "EDF5FE",
  pale: "F8FBFF",
  line: "D4E1EF",
  white: "FFFFFF",
  dark: "0A2239",
};

function addTopBand(slide, title, section) {
  slide.background = { color: C.white };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: 0.75,
    line: { color: C.navy, transparency: 100 },
    fill: { color: C.navy },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 5.55,
    h: 0.75,
    line: { color: C.blue, transparency: 100 },
    fill: { color: C.blue },
  });
  slide.addText(title, {
    x: 0.32,
    y: 0.14,
    w: 8.8,
    h: 0.34,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 22,
    bold: true,
    color: C.white,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 11.1,
    y: 0.16,
    w: 1.18,
    h: 0.32,
    rectRadius: 0.05,
    line: { color: "6FB6FF", width: 1 },
    fill: { color: C.deepBlue },
  });
  slide.addText(section, {
    x: 11.1,
    y: 0.215,
    w: 1.18,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 9.6,
    bold: true,
    color: C.white,
  });
  slide.addText("核心算法架构", {
    x: 12.08,
    y: 0.19,
    w: 0.92,
    h: 0.16,
    margin: 0,
    align: "right",
    fontFace: "Microsoft YaHei",
    fontSize: 9.6,
    bold: true,
    color: C.white,
  });
}

function addFooter(slide, text) {
  slide.addShape(pptx.ShapeType.line, {
    x: 0.45,
    y: 6.98,
    w: 12.35,
    h: 0,
    line: { color: C.line, width: 1 },
  });
  slide.addText(text, {
    x: 0.5,
    y: 7.03,
    w: 12.25,
    h: 0.15,
    margin: 0,
    align: "right",
    fontFace: "Microsoft YaHei",
    fontSize: 7.2,
    color: "72849C",
  });
}

function addIntroStrip(slide, text) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.55,
    y: 0.95,
    w: 12.2,
    h: 0.48,
    rectRadius: 0.04,
    line: { color: C.line, width: 1 },
    fill: { color: C.light },
  });
  slide.addText(text, {
    x: 0.74,
    y: 1.08,
    w: 11.8,
    h: 0.18,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 11,
    bold: true,
    color: C.navy,
  });
}

function addPanel(slide, x, y, w, h, title) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.07,
    line: { color: C.line, width: 1.1 },
    fill: { color: C.pale },
  });
  slide.addText(title, {
    x: x + 0.16,
    y: y + 0.14,
    w: w - 0.3,
    h: 0.18,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 14,
    bold: true,
    color: C.navy,
  });
}

function addCard(slide, { x, y, w, h, title, body, color, bodySize = 9.8, fill = C.white }) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.06,
    line: { color, width: 1.2 },
    fill: { color: fill },
    shadow: safeOuterShadow("A6C1DA", 0.12, 45, 2, 1),
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 0.12,
    y: y + 0.12,
    w: Math.min(1.68, w - 0.24),
    h: 0.34,
    rectRadius: 0.04,
    line: { color, transparency: 100 },
    fill: { color },
  });
  slide.addText(title, {
    x: x + 0.18,
    y: y + 0.205,
    w: w - 0.28,
    h: 0.14,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 11.2,
    bold: true,
    color: C.white,
  });
  slide.addText(body, {
    x: x + 0.16,
    y: y + 0.58,
    w: w - 0.3,
    h: h - 0.72,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: bodySize,
    color: C.ink,
    valign: "top",
  });
}

function addPill(slide, x, y, w, h, text, color, fontSize = 10.2) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.04,
    line: { color, width: 1.1 },
    fill: { color: C.white },
  });
  slide.addText(text, {
    x,
    y: y + 0.09,
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

function addArrow(slide, x, y, w, h = 0, color = C.line) {
  slide.addShape(pptx.ShapeType.line, {
    x,
    y,
    w,
    h,
    line: { color, width: 1.25, beginArrowType: "none", endArrowType: "triangle" },
  });
}

function addInfoRow(slide, x, y, label, text, color, w = 3.25, h = 0.42) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w: 1.06,
    h,
    rectRadius: 0.04,
    line: { color, transparency: 100 },
    fill: { color },
  });
  slide.addText(label, {
    x,
    y: y + 0.1,
    w: 1.06,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10.1,
    bold: true,
    color: C.white,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 1.18,
    y,
    w,
    h,
    rectRadius: 0.04,
    line: { color, width: 1 },
    fill: { color: C.white },
  });
  slide.addText(text, {
    x: x + 1.33,
    y: y + 0.1,
    w: w - 0.2,
    h: 0.14,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 9.5,
    color: C.ink,
  });
}

function addMetricRow(slide, y, items, color) {
  const boxW = 2.93;
  items.forEach((item, i) => {
    const x = 0.6 + i * 3.15;
    slide.addShape(pptx.ShapeType.roundRect, {
      x,
      y,
      w: boxW,
      h: 0.48,
      rectRadius: 0.04,
      line: { color, width: 1 },
      fill: { color: C.white },
    });
    slide.addText(item, {
      x: x + 0.08,
      y: y + 0.12,
      w: boxW - 0.16,
      h: 0.16,
      margin: 0,
      align: "center",
      fontFace: "Microsoft YaHei",
      fontSize: 9.2,
      bold: true,
      color: C.ink,
    });
  });
}

function addBulletList(slide, x, y, w, lines, color = C.ink, fontSize = 10.2, gap = 0.32) {
  lines.forEach((line, idx) => {
    const cy = y + idx * gap;
    slide.addShape(pptx.ShapeType.ellipse, {
      x,
      y: cy + 0.04,
      w: 0.08,
      h: 0.08,
      line: { color, transparency: 100 },
      fill: { color },
    });
    slide.addText(line, {
      x: x + 0.16,
      y: cy,
      w: w - 0.16,
      h: 0.18,
      margin: 0,
      fontFace: "Microsoft YaHei",
      fontSize,
      color,
    });
  });
}

function finalize(slide) {
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function buildCover() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };
  slide.addImage({
    path: ASSETS.panorama,
    ...imageSizingCrop(ASSETS.panorama, 6.9, 0, 6.43, H),
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 8.1,
    h: H,
    line: { color: C.navy, transparency: 100 },
    fill: { color: C.navy },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 7.35,
    y: 0,
    w: 5.98,
    h: H,
    line: { color: "08233B", transparency: 60 },
    fill: { color: "08233B", transparency: 35 },
  });
  slide.addText("水处理智能精准控制一体化项目", {
    x: 0.56,
    y: 1.0,
    w: 6.65,
    h: 0.5,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 24,
    bold: true,
    color: C.white,
  });
  slide.addText("三大核心 AI 模型算法架构详解", {
    x: 0.56,
    y: 1.63,
    w: 6.65,
    h: 0.4,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 28,
    bold: true,
    color: "7FD3FF",
  });
  slide.addText("聚焦膜污染预判与清洗、锅炉给水水质与药剂协同、深度水处理硬度调节三大模型", {
    x: 0.58,
    y: 2.28,
    w: 6.5,
    h: 0.36,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 11.8,
    color: "D7E8FA",
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.58,
    y: 3.0,
    w: 6.18,
    h: 1.74,
    rectRadius: 0.07,
    line: { color: "64B5F6", transparency: 35, width: 1 },
    fill: { color: "133A61" },
  });
  addBulletList(slide, 0.88, 3.34, 5.5, [
    "核心底座：EWMA、Isolation Forest、RF、SVM、XGBoost、CatBoost、LSTM、TCN、Transformer、MPC、NSGA-II",
    "前沿发散：B-PINN、DIOKO EMPC、Fuzzy GNN",
    "汇报主线：架构导向、算法分工、控制闭环、输出结果",
  ], C.white, 10.2, 0.42);
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.58,
    y: 5.2,
    w: 2.2,
    h: 0.42,
    rectRadius: 0.04,
    line: { color: "4FC3F7", transparency: 100 },
    fill: { color: "1E88E5" },
  });
  slide.addText("项目算法专题汇报", {
    x: 0.58,
    y: 5.32,
    w: 2.2,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10.5,
    bold: true,
    color: C.white,
  });
  slide.addText("江苏南大五维电子科技有限公司", {
    x: 0.6,
    y: 6.45,
    w: 4.2,
    h: 0.18,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 11,
    color: "E7F2FF",
  });
  slide.addText("核心算法架构", {
    x: 10.55,
    y: 6.55,
    w: 2.2,
    h: 0.18,
    margin: 0,
    align: "right",
    fontFace: "Microsoft YaHei",
    fontSize: 10.2,
    bold: true,
    color: C.white,
  });
  finalize(slide);
}

function buildOverview() {
  const slide = pptx.addSlide();
  addTopBand(slide, "总体算法体系", "总览 01");
  addIntroStrip(slide, "整体方案由“统一数据底座 + 三大模型引擎 + 执行闭环”组成，三套模型共用感知、治理、优化与反馈能力，分别服务于膜清洗、给水加药与硬度调节。");

  addPanel(slide, 0.55, 1.68, 12.22, 4.96, "统一算法底座与三模型关系图");
  addPill(slide, 0.9, 2.08, 1.58, 0.56, "在线感知\n水质 / 设备 / 药耗", C.cyan, 10);
  addPill(slide, 2.72, 2.08, 1.58, 0.56, "数据治理\n清洗 / 对齐 / 特征", C.blue, 10);
  addPill(slide, 4.54, 2.08, 1.58, 0.56, "状态识别\n分类 / 告警 / 分型", C.green, 10);
  addPill(slide, 6.36, 2.08, 1.58, 0.56, "趋势预测\n短时 / 中时 / 窗口", C.orange, 10);
  addPill(slide, 8.18, 2.08, 1.58, 0.56, "优化控制\n投药 / 能耗 / 约束", C.blue, 10);
  addPill(slide, 10.0, 2.08, 1.58, 0.56, "执行反馈\n泵阀 / 清洗 / 回写", C.green, 10);
  addArrow(slide, 2.48, 2.36, 0.22);
  addArrow(slide, 4.3, 2.36, 0.22);
  addArrow(slide, 6.12, 2.36, 0.22);
  addArrow(slide, 7.94, 2.36, 0.22);
  addArrow(slide, 9.76, 2.36, 0.22);

  addCard(slide, {
    x: 0.74,
    y: 3.1,
    w: 3.76,
    h: 2.52,
    title: "模型一：膜污染预判与清洗",
    body:
      "导向：从被动清洗转向按需清洗\n底座：EWMA / Isolation Forest + RF / SVM + LSTM / TCN\n前沿：B-PINN 做机理与数据双驱建模",
    color: C.blue,
    bodySize: 10,
  });
  addCard(slide, {
    x: 4.78,
    y: 3.1,
    w: 3.76,
    h: 2.52,
    title: "模型二：锅炉给水水质与药剂协同",
    body:
      "导向：pH 稳定与综合成本最优\n底座：CatBoost / XGBoost + LSTM + NSGA-II\n前沿：DIOKO EMPC 做实时经济预测控制",
    color: C.green,
    bodySize: 10,
  });
  addCard(slide, {
    x: 8.82,
    y: 3.1,
    w: 3.76,
    h: 2.52,
    title: "模型三：深度水处理硬度调节",
    body:
      "导向：前馈与反馈闭环稳定命中硬度区间\n底座：XGBoost + TCN / Transformer + MPC\n前沿：Fuzzy GNN 做机理融合与解释增强",
    color: C.orange,
    bodySize: 10,
  });

  addFooter(slide, "汇报结构：总体架构、模型架构图、算法底座、前沿补充、控制输出。");
  finalize(slide);
}

function buildMembraneArchitecture() {
  const slide = pptx.addSlide();
  addTopBand(slide, "模型一：膜污染预判与清洗架构", "模型一");
  addIntroStrip(slide, "模型目标是将膜污染识别、污染趋势预判与清洗动作生成贯通起来，形成从早期征兆到定制化清洗指令的闭环。");

  addPanel(slide, 0.55, 1.68, 7.28, 4.98, "算法架构图");
  addPill(slide, 0.95, 2.12, 1.3, 0.46, "TMP / 压差", C.blue, 10.1);
  addPill(slide, 2.42, 2.12, 1.18, 0.46, "通量", C.cyan, 10.1);
  addPill(slide, 3.77, 2.12, 1.28, 0.46, "浊度 / SDI", C.green, 10.1);
  addPill(slide, 5.22, 2.12, 1.55, 0.46, "清洗历史", C.orange, 10.1);
  addArrow(slide, 1.58, 2.58, 0.5, 0.28);
  addArrow(slide, 3.0, 2.58, 0.15, 0.28);
  addArrow(slide, 4.42, 2.58, -0.18, 0.28);
  addArrow(slide, 5.98, 2.58, -0.52, 0.28);

  addCard(slide, {
    x: 2.0,
    y: 2.94,
    w: 4.45,
    h: 0.86,
    title: "数据治理层",
    body: "缺失补全、异常剔除、时滞对齐、特征构造",
    color: C.blue,
    bodySize: 10,
  });
  addArrow(slide, 4.2, 3.8, 0, 0.25);
  addCard(slide, {
    x: 0.9,
    y: 4.14,
    w: 2.18,
    h: 1.02,
    title: "征兆识别",
    body: "EWMA\nIsolation Forest",
    color: C.cyan,
    bodySize: 10.1,
  });
  addCard(slide, {
    x: 3.14,
    y: 4.14,
    w: 2.38,
    h: 1.02,
    title: "污染分型",
    body: "RF / SVM\n区分结垢、胶体、有机、生物污染",
    color: C.green,
    bodySize: 9.4,
  });
  addCard(slide, {
    x: 5.62,
    y: 4.14,
    w: 1.54,
    h: 1.02,
    title: "趋势预判",
    body: "LSTM\nTCN",
    color: C.orange,
    bodySize: 10.1,
  });
  addArrow(slide, 2.0, 5.16, 1.08, 0.34);
  addArrow(slide, 4.32, 5.16, 1.32, 0.34);
  addCard(slide, {
    x: 2.22,
    y: 5.24,
    w: 3.9,
    h: 0.72,
    title: "清洗决策生成",
    body: "规则库 + 贝叶斯优化输出时机、剂型、浓度和时长",
    color: C.red,
    bodySize: 9.3,
  });
  addArrow(slide, 6.12, 5.6, 0.66, 0);
  addPill(slide, 6.86, 5.39, 0.68, 0.4, "输出", C.red, 10);

  addPanel(slide, 8.08, 1.68, 4.69, 4.98, "架构说明");
  addInfoRow(slide, 8.3, 2.12, "输入", "TMP、压差、通量、浊度、清洗记录、膜龄", C.blue, 3.12);
  addInfoRow(slide, 8.3, 2.68, "识别", "EWMA 与 Isolation Forest 捕捉早期异常", C.cyan, 3.12);
  addInfoRow(slide, 8.3, 3.24, "分型", "RF / SVM 输出污染类型标签", C.green, 3.12);
  addInfoRow(slide, 8.3, 3.8, "预测", "LSTM / TCN 计算未来清洗阈值窗口", C.orange, 3.12);
  addInfoRow(slide, 8.3, 4.36, "动作", "规则库 + 贝叶斯优化生成清洗方案", C.red, 3.12);
  addInfoRow(slide, 8.3, 4.92, "目标", "把被动清洗改造成按需清洗与精准护膜", C.blue, 3.12);

  addMetricRow(slide, 6.16, [
    "预警窗口：提前覆盖人工处置时间",
    "识别结果：污染类型与清洗动作一一对应",
    "执行目标：避免无效清洗与过度清洗",
    "最终结果：延长膜寿命并降低维护成本",
  ], C.blue);

  addFooter(slide, "模型一关键词：征兆识别、污染分型、趋势预判、清洗决策。");
  finalize(slide);
}

function buildMembraneDetail() {
  const slide = pptx.addSlide();
  addTopBand(slide, "模型一：机理-数据双驱的智能维保底座", "模型一");
  addIntroStrip(slide, "膜污染模型以“机理-数据双驱”为核心，在经典识别与时序预测底座之上，引入 B-PINN 提升少样本条件下的机理一致性与不确定性刻画能力。");

  addCard(slide, {
    x: 0.64,
    y: 1.74,
    w: 4.0,
    h: 1.58,
    title: "架构导向",
    body:
      "打破“定期清洗 / 故障后清洗”的被动模式，建立从污染征兆捕捉到清洗方案输出的全链路闭环，实现按需清洗与精准护膜。",
    color: C.blue,
    bodySize: 10.2,
  });
  addCard(slide, {
    x: 4.8,
    y: 1.74,
    w: 4.0,
    h: 1.58,
    title: "核心底座",
    body:
      "EWMA、Isolation Forest 负责异常前兆；RF、SVM 负责污染定性分类；LSTM、TCN 负责时间窗口预测；规则库与贝叶斯优化负责方案输出。",
    color: C.green,
    bodySize: 10.1,
  });
  addCard(slide, {
    x: 8.96,
    y: 1.74,
    w: 3.72,
    h: 1.58,
    title: "输出结果",
    body:
      "直接给出“时机 + 剂型 + 浓度 + 时长”的完整清洗指令，并把历史执行结果回灌模型，形成自校正闭环。",
    color: C.orange,
    bodySize: 10.1,
  });

  addPanel(slide, 0.64, 3.56, 7.1, 2.62, "前沿补充：B-PINN 融合逻辑");
  addPill(slide, 0.96, 4.02, 1.48, 0.46, "物理机理方程", C.blue, 10);
  addPill(slide, 2.66, 4.02, 1.52, 0.46, "历史运行样本", C.cyan, 10);
  addPill(slide, 4.42, 4.02, 1.34, 0.46, "贝叶斯推断", C.green, 10);
  addPill(slide, 6.02, 4.02, 1.34, 0.46, "B-PINN", C.orange, 10);
  addArrow(slide, 2.44, 4.25, 0.18);
  addArrow(slide, 4.18, 4.25, 0.2);
  addArrow(slide, 5.76, 4.25, 0.18);
  addBulletList(slide, 0.94, 4.9, 6.2, [
    "把污染物传输与截留的物理偏微分方程嵌入损失函数，避免模型脱离工艺机理。",
    "在样本稀缺时仍保持稳定精度，同时量化污染转移与噪声的不确定性。",
    "适合膜污染多机理叠加、现场样本不足、清洗结果反馈滞后的场景。",
  ], C.ink, 9.7, 0.34);

  addPanel(slide, 7.96, 3.56, 4.72, 2.62, "汇报可直接讲的价值点");
  addBulletList(slide, 8.26, 4.0, 4.0, [
    "把经验清洗改造成数据驱动的按需清洗。",
    "把污染类别与清洗动作建立一对一映射。",
    "把少样本和高不确定性的场景纳入可解释建模。",
    "把清洗效果、膜寿命与清洗成本放到同一框架里评估。",
  ], C.ink, 10, 0.4);

  addFooter(slide, "前沿补充：B-PINN 强调物理方程嵌入、少样本稳定性与不确定性量化。");
  finalize(slide);
}

function buildBoilerArchitecture() {
  const slide = pptx.addSlide();
  addTopBand(slide, "模型二：锅炉给水水质与药剂协同架构", "模型二");
  addIntroStrip(slide, "锅炉给水模型围绕 pH 稳定、药剂协同和综合成本控制展开，把状态估计、时序预判与多目标优化统一到同一控制链路。");

  addPanel(slide, 0.55, 1.68, 7.28, 4.98, "算法架构图");
  addPill(slide, 0.94, 2.12, 1.12, 0.46, "pH", C.blue, 10.2);
  addPill(slide, 2.22, 2.12, 1.18, 0.46, "流量", C.cyan, 10.2);
  addPill(slide, 3.56, 2.12, 1.18, 0.46, "温度", C.green, 10.2);
  addPill(slide, 4.9, 2.12, 1.62, 0.46, "泵阀 / 回流", C.orange, 10.2);
  addArrow(slide, 1.5, 2.58, 0.45, 0.28);
  addArrow(slide, 2.8, 2.58, 0.12, 0.28);
  addArrow(slide, 4.14, 2.58, -0.2, 0.28);
  addArrow(slide, 5.88, 2.58, -0.58, 0.28);

  addCard(slide, {
    x: 1.78,
    y: 2.94,
    w: 4.8,
    h: 0.86,
    title: "数据治理层",
    body: "采样统一、异常剔除、状态编码、回流与流量耦合关系整理",
    color: C.blue,
    bodySize: 9.8,
  });
  addArrow(slide, 4.18, 3.8, 0, 0.24);
  addCard(slide, {
    x: 0.96,
    y: 4.14,
    w: 2.18,
    h: 1.02,
    title: "状态估计",
    body: "CatBoost\nXGBoost",
    color: C.cyan,
    bodySize: 10.1,
  });
  addCard(slide, {
    x: 3.2,
    y: 4.14,
    w: 2.02,
    h: 1.02,
    title: "时序预判",
    body: "LSTM\n流量突变 - pH 趋势",
    color: C.green,
    bodySize: 9.5,
  });
  addCard(slide, {
    x: 5.38,
    y: 4.14,
    w: 1.48,
    h: 1.02,
    title: "保护层",
    body: "阈值\n滞回",
    color: C.red,
    bodySize: 10.1,
  });
  addArrow(slide, 2.0, 5.16, 1.18, 0.34);
  addArrow(slide, 4.16, 5.16, 1.22, 0.34);
  addCard(slide, {
    x: 2.28,
    y: 5.22,
    w: 3.76,
    h: 0.72,
    title: "多目标优化控制",
    body: "NSGA-II 联动药剂、能耗、约束边界并输出执行量",
    color: C.orange,
    bodySize: 9.3,
  });
  addArrow(slide, 6.04, 5.58, 0.7, 0);
  addPill(slide, 6.82, 5.37, 0.66, 0.4, "执行", C.orange, 10);

  addPanel(slide, 8.08, 1.68, 4.69, 4.98, "架构说明");
  addInfoRow(slide, 8.3, 2.12, "输入", "pH、流量、温度、回流、泵阀状态", C.blue, 3.12);
  addInfoRow(slide, 8.3, 2.68, "估计", "CatBoost / XGBoost 识别当前水质工况", C.cyan, 3.12);
  addInfoRow(slide, 8.3, 3.24, "预判", "LSTM 计算流量突变后的 pH 走向", C.green, 3.12);
  addInfoRow(slide, 8.3, 3.8, "保护", "阈值和滞回负责实时止损与回退", C.red, 3.12);
  addInfoRow(slide, 8.3, 4.36, "优化", "NSGA-II 处理药剂和能耗的多目标平衡", C.orange, 3.12);
  addInfoRow(slide, 8.3, 4.92, "目标", "把 pH 稳定与吨水综合成本最低统一起来", C.blue, 3.12);

  addMetricRow(slide, 6.16, [
    "工艺目标：pH 保持在 8.8-9.3 区间",
    "经济目标：药剂消耗与能耗综合成本最低",
    "控制指标：过冲、振荡、恢复时间可量化",
    "执行要求：异常工况下可快速回切人工",
  ], C.green);

  addFooter(slide, "模型二关键词：状态估计、时序预判、多目标优化、实时执行。");
  finalize(slide);
}

function buildBoilerDetail() {
  const slide = pptx.addSlide();
  addTopBand(slide, "模型二：全局寻优的经济预测控制底座", "模型二");
  addIntroStrip(slide, "锅炉给水模型在 CatBoost / XGBoost、LSTM 与 NSGA-II 底座之上，引入 DIOKO EMPC，把复杂非线性动态映射到可实时求解的经济预测控制框架中。");

  addCard(slide, {
    x: 0.64,
    y: 1.74,
    w: 4.0,
    h: 1.58,
    title: "架构导向",
    body:
      "核心目标是让锅炉给水 pH 稳定在 8.8-9.3 区间，同时将阻垢剂、杀菌剂与能耗等吨水综合成本压到最低。",
    color: C.blue,
    bodySize: 10.2,
  });
  addCard(slide, {
    x: 4.8,
    y: 1.74,
    w: 4.0,
    h: 1.58,
    title: "核心底座",
    body:
      "CatBoost / XGBoost 负责当前状态估计，LSTM 负责短时 pH 趋势前瞻，NSGA-II 负责在约束条件下做系统级多目标联动求解。",
    color: C.green,
    bodySize: 10.1,
  });
  addCard(slide, {
    x: 8.96,
    y: 1.74,
    w: 3.72,
    h: 1.58,
    title: "输出结果",
    body:
      "输出给水加药量、保护动作、执行边界与经济运行结果，形成面向实时控制的闭环决策指令。",
    color: C.orange,
    bodySize: 10.1,
  });

  addPanel(slide, 0.64, 3.56, 7.1, 2.62, "前沿补充：DIOKO EMPC 融合逻辑");
  addPill(slide, 0.96, 4.02, 1.38, 0.46, "非线性动态", C.blue, 10);
  addPill(slide, 2.58, 4.02, 1.72, 0.46, "神经网络映射", C.cyan, 10);
  addPill(slide, 4.56, 4.02, 1.72, 0.46, "高维线性隐空间", C.green, 10);
  addPill(slide, 6.52, 4.02, 0.86, 0.46, "EMPC", C.orange, 10);
  addArrow(slide, 2.34, 4.25, 0.18);
  addArrow(slide, 4.3, 4.25, 0.22);
  addArrow(slide, 6.28, 4.25, 0.18);
  addBulletList(slide, 0.94, 4.92, 6.25, [
    "把高维非线性过程映射成高维线性可控隐空间，显著降低实时优化求解难度。",
    "将原本复杂的非凸问题转化为更易实时求解的二次规划问题，适配在线控制。",
    "在不依赖全状态物理测量的情况下，仍能预测未来经济运行成本并稳定输出控制量。",
  ], C.ink, 9.7, 0.34);

  addPanel(slide, 7.96, 3.56, 4.72, 2.62, "汇报可直接讲的价值点");
  addBulletList(slide, 8.26, 4.0, 4.0, [
    "把“pH 安全稳定”和“吨水综合成本最低”放到同一控制目标里。",
    "把多药剂、多约束、多执行量联动起来，不再只盯单一加药点。",
    "把复杂非线性控制问题压缩成可实时运行的经济预测控制问题。",
    "把主动防御、实时求解和鲁棒控制统一起来。",
  ], C.ink, 10, 0.4);

  addFooter(slide, "前沿补充：DIOKO EMPC 强调高维隐空间线性化、实时求解和经济优化。");
  finalize(slide);
}

function buildHardnessArchitecture() {
  const slide = pptx.addSlide();
  addTopBand(slide, "模型三：深度水处理硬度调节架构", "模型三");
  addIntroStrip(slide, "硬度调节模型围绕原水波动、药剂前馈和出水反馈构建闭环修偏体系，把出水硬度锁定在目标区间，并同步压缩药耗。");

  addPanel(slide, 0.55, 1.68, 7.28, 4.98, "算法架构图");
  addPill(slide, 0.94, 2.12, 1.4, 0.46, "原水硬度", C.blue, 10.1);
  addPill(slide, 2.54, 2.12, 1.12, 0.46, "流量", C.cyan, 10.1);
  addPill(slide, 3.86, 2.12, 1.12, 0.46, "浊度", C.green, 10.1);
  addPill(slide, 5.18, 2.12, 1.42, 0.46, "出水硬度", C.orange, 10.1);
  addArrow(slide, 1.62, 2.58, 0.42, 0.28);
  addArrow(slide, 2.98, 2.58, 0.16, 0.28);
  addArrow(slide, 4.3, 2.58, -0.12, 0.28);
  addArrow(slide, 5.9, 2.58, -0.54, 0.28);

  addCard(slide, {
    x: 1.84,
    y: 2.94,
    w: 4.74,
    h: 0.86,
    title: "数据治理层",
    body: "缺失补全、异常剔除、时滞对齐、波动特征提取",
    color: C.blue,
    bodySize: 9.8,
  });
  addArrow(slide, 4.18, 3.8, 0, 0.24);
  addCard(slide, {
    x: 1.0,
    y: 4.14,
    w: 2.18,
    h: 1.02,
    title: "状态估计",
    body: "XGBoost\nCatBoost",
    color: C.cyan,
    bodySize: 10.1,
  });
  addCard(slide, {
    x: 3.24,
    y: 4.14,
    w: 2.08,
    h: 1.02,
    title: "波动预判",
    body: "TCN\nTransformer",
    color: C.green,
    bodySize: 10.1,
  });
  addCard(slide, {
    x: 5.46,
    y: 4.14,
    w: 1.42,
    h: 1.02,
    title: "反馈修偏",
    body: "偏差\n校正",
    color: C.red,
    bodySize: 10.1,
  });
  addArrow(slide, 2.02, 5.16, 1.26, 0.34);
  addArrow(slide, 4.28, 5.16, 1.22, 0.34);
  addCard(slide, {
    x: 2.34,
    y: 5.22,
    w: 3.74,
    h: 0.72,
    title: "前馈 + 反馈控制",
    body: "MPC / BayesOpt 计算碳酸钠投加量与控制边界",
    color: C.orange,
    bodySize: 9.3,
  });
  addArrow(slide, 6.08, 5.58, 0.68, 0);
  addPill(slide, 6.84, 5.37, 0.66, 0.4, "执行", C.orange, 10);

  addPanel(slide, 8.08, 1.68, 4.69, 4.98, "架构说明");
  addInfoRow(slide, 8.3, 2.12, "输入", "原水硬度、流量、浊度、出水硬度、碱度", C.blue, 3.12);
  addInfoRow(slide, 8.3, 2.68, "估计", "XGBoost / CatBoost 计算当前药剂需求", C.cyan, 3.12);
  addInfoRow(slide, 8.3, 3.24, "预判", "TCN / Transformer 预测 30-60 分钟波动", C.green, 3.12);
  addInfoRow(slide, 8.3, 3.8, "控制", "前馈 + 反馈 + MPC / BayesOpt 计算投加量", C.orange, 3.12);
  addInfoRow(slide, 8.3, 4.36, "修偏", "出水反馈负责持续抑制超调与振荡", C.red, 3.12);
  addInfoRow(slide, 8.3, 4.92, "目标", "把出水硬度稳定锁定在 270-280 mg/L 区间", C.blue, 3.12);

  addMetricRow(slide, 6.16, [
    "目标区间：出水硬度稳定命中 270-280 mg/L",
    "成本目标：碳酸钠吨水消耗与波动损失下降",
    "控制指标：命中率、方差、收敛时间、超调量",
    "运维指标：模型漂移发现速度与回标速度",
  ], C.orange);

  addFooter(slide, "模型三关键词：波动预判、机理约束、前馈反馈、闭环修偏。");
  finalize(slide);
}

function buildHardnessDetail() {
  const slide = pptx.addSlide();
  addTopBand(slide, "模型三：认知驱动的机理融合抗扰底座", "模型三");
  addIntroStrip(slide, "硬度调节模型以 XGBoost、TCN / Transformer 与前馈反馈控制为主体，在此之上引入 Fuzzy GNN，强化解释能力、空间关联理解和专家可核验性。");

  addCard(slide, {
    x: 0.64,
    y: 1.74,
    w: 4.0,
    h: 1.58,
    title: "架构导向",
    body:
      "面对原水剧烈波动，通过前馈与反馈交织的闭环修偏体系，把出水硬度稳定锁定在 270-280 mg/L 区间，实现精准控药。",
    color: C.blue,
    bodySize: 10.2,
  });
  addCard(slide, {
    x: 4.8,
    y: 1.74,
    w: 4.0,
    h: 1.58,
    title: "核心底座",
    body:
      "Transformer / TCN 负责多变量长依赖波动预测；XGBoost 负责非线性投药规律挖掘；前馈 + 反馈控制负责最大化抑制超调与振荡。",
    color: C.green,
    bodySize: 10.1,
  });
  addCard(slide, {
    x: 8.96,
    y: 1.74,
    w: 3.72,
    h: 1.58,
    title: "输出结果",
    body:
      "输出碳酸钠投加量、目标区间命中率与收敛速度，并持续把反馈偏差回灌到控制器中。",
    color: C.orange,
    bodySize: 10.1,
  });

  addPanel(slide, 0.64, 3.56, 7.1, 2.62, "前沿补充：Fuzzy GNN 融合逻辑");
  addPill(slide, 0.98, 4.02, 1.38, 0.46, "拓扑图结构", C.blue, 10);
  addPill(slide, 2.58, 4.02, 1.48, 0.46, "模糊逻辑", C.cyan, 10);
  addPill(slide, 4.3, 4.02, 1.64, 0.46, "互信息筛选", C.green, 10);
  addPill(slide, 6.16, 4.02, 1.18, 0.46, "Fuzzy GNN", C.orange, 10);
  addArrow(slide, 2.36, 4.25, 0.18);
  addArrow(slide, 4.06, 4.25, 0.22);
  addArrow(slide, 5.94, 4.25, 0.18);
  addBulletList(slide, 0.94, 4.92, 6.25, [
    "把管网节点与水质参数组织成图结构，显式表达空间耦合与传递关系。",
    "把模糊逻辑和互信息筛选融入深度图模型，提取真正起决定作用的子图特征。",
    "把黑盒预测转化成可读语义规则，支持专家直接核实调参逻辑。",
  ], C.ink, 9.7, 0.34);

  addPanel(slide, 7.96, 3.56, 4.72, 2.62, "汇报可直接讲的价值点");
  addBulletList(slide, 8.26, 4.0, 4.0, [
    "把复杂深度学习结果转成专家能理解的语义规则。",
    "把空间拓扑、水质波动和控制逻辑放到同一张图里理解。",
    "把机理、数据和解释能力一起纳入建模框架。",
    "把专家信任度和模型精度同时抬起来。",
  ], C.ink, 10, 0.4);

  addFooter(slide, "前沿补充：Fuzzy GNN 强调图结构表达、模糊语义规则与可解释控制逻辑。");
  finalize(slide);
}

function buildSummary() {
  const slide = pptx.addSlide();
  addTopBand(slide, "三模型算法方案总结", "总结");
  addIntroStrip(slide, "整套方案的讲法可以统一成“目标导向 - 核心底座 - 前沿发散 - 控制输出”四段式，每个模型都能围绕这个结构稳定展开。");

  addCard(slide, {
    x: 0.62,
    y: 1.72,
    w: 3.9,
    h: 1.92,
    title: "膜污染预判与清洗",
    body:
      "目标：按需清洗、精准护膜\n底座：EWMA / Isolation Forest + RF / SVM + LSTM / TCN\n发散：B-PINN\n输出：清洗窗口、剂型、浓度、时长",
    color: C.blue,
    bodySize: 10.2,
  });
  addCard(slide, {
    x: 4.72,
    y: 1.72,
    w: 3.9,
    h: 1.92,
    title: "锅炉给水水质与药剂协同",
    body:
      "目标：pH 稳定、药耗与能耗最优\n底座：CatBoost / XGBoost + LSTM + NSGA-II\n发散：DIOKO EMPC\n输出：投药量、执行边界、经济成本",
    color: C.green,
    bodySize: 10.2,
  });
  addCard(slide, {
    x: 8.82,
    y: 1.72,
    w: 3.9,
    h: 1.92,
    title: "深度水处理硬度调节",
    body:
      "目标：硬度区间稳定命中\n底座：XGBoost + Transformer / TCN + 前馈反馈控制\n发散：Fuzzy GNN\n输出：投药量、命中率、收敛速度",
    color: C.orange,
    bodySize: 10.2,
  });

  addPanel(slide, 0.62, 4.0, 12.1, 2.36, "汇报落点");
  addBulletList(slide, 0.92, 4.42, 11.2, [
    "先讲清三模型分别解决什么控制问题，再讲各自的算法分层和控制闭环。",
    "核心底座部分强调工程可落地性，前沿发散部分强调技术先进性和未来扩展性。",
    "每个模型都对应明确输入、核心算法、控制动作和结果指标，形成完整叙述链路。",
    "整套 PPT 已经把模型架构图和详细文字拆开，方便直接汇报或继续微调。",
  ], C.ink, 10.2, 0.42);

  addFooter(slide, "项目主线：统一底座、三大模型、算法发散、闭环执行。");
  finalize(slide);
}

async function main() {
  buildCover();
  buildOverview();
  buildMembraneArchitecture();
  buildMembraneDetail();
  buildBoilerArchitecture();
  buildBoilerDetail();
  buildHardnessArchitecture();
  buildHardnessDetail();
  buildSummary();

  const outPath = path.join(PROJECT_ROOT, "水处理智能精准控制一体化项目_核心算法架构详解.pptx");
  await pptx.writeFile({ fileName: outPath });
  console.log(`WROTE ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
