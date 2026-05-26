const path = require("path");
const PptxGenJS = require("pptxgenjs");
const { imageSizingCrop } = require("./pptxgenjs_helpers/image");
const { warnIfSlideElementsOutOfBounds } = require("./pptxgenjs_helpers/layout");
const { safeOuterShadow } = require("./pptxgenjs_helpers/util");

const ROOT = __dirname;
const PROJECT_ROOT = path.resolve(ROOT, "..", "..");
const ASSETS = {
  panorama: path.join(ROOT, "assets", "wwtp_panorama.jpeg"),
};

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "江苏南大五维电子科技有限公司";
pptx.subject = "水处理三模型算法架构三页版";
pptx.title = "水处理三模型算法架构三页版";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const BASE = {
  bg: "081C33",
  panel: "F9FBFF",
  white: "FFFFFF",
  text: "1E293B",
  muted: "96A7BC",
  line: "D7E4F2",
};

function slideBg(slide, accent, accent2) {
  slide.background = { color: BASE.bg };
  slide.addImage({
    path: ASSETS.panorama,
    ...imageSizingCrop(ASSETS.panorama, 8.55, 0, 4.78, 7.5),
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 8.55,
    y: 0,
    w: 4.78,
    h: 7.5,
    line: { color: BASE.bg, transparency: 100 },
    fill: { color: BASE.bg, transparency: 35 },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 9.1,
    y: 0.55,
    w: 3.1,
    h: 3.1,
    line: { color: accent, transparency: 100 },
    fill: { color: accent, transparency: 76 },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 10.2,
    y: 3.95,
    w: 2.5,
    h: 2.5,
    line: { color: accent2, transparency: 100 },
    fill: { color: accent2, transparency: 82 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: 0.88,
    line: { color: "0A213C", transparency: 100 },
    fill: { color: "0A213C", transparency: 10 },
  });
}

function header(slide, chip, title, subtitle, accent) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.62,
    y: 0.42,
    w: 1.38,
    h: 0.34,
    rectRadius: 0.05,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText(chip, {
    x: 0.62,
    y: 0.49,
    w: 1.38,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10.2,
    bold: true,
    color: BASE.white,
  });
  slide.addText(title, {
    x: 0.62,
    y: 0.96,
    w: 6.85,
    h: 0.38,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 24,
    bold: true,
    color: BASE.white,
  });
  slide.addText(subtitle, {
    x: 0.64,
    y: 1.4,
    w: 6.8,
    h: 0.22,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 11.5,
    color: "D8E6F5",
  });
}

function mainPanel(slide) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.56,
    y: 1.86,
    w: 8.2,
    h: 4.95,
    rectRadius: 0.08,
    line: { color: "D8E5F2", width: 1.2 },
    fill: { color: BASE.panel },
    shadow: safeOuterShadow("0C1C2B", 0.18, 45, 2, 1),
  });
}

function sidePanel(slide, accent) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 9.18,
    y: 1.86,
    w: 3.62,
    h: 4.95,
    rectRadius: 0.08,
    line: { color: BASE.white, transparency: 85, width: 1.2 },
    fill: { color: "0E2A48", transparency: 10 },
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 9.42,
    y: 2.1,
    w: 1.48,
    h: 0.36,
    rectRadius: 0.05,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText("模型要点", {
    x: 9.42,
    y: 2.18,
    w: 1.48,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10.2,
    bold: true,
    color: BASE.white,
  });
}

function panelTitle(slide, text) {
  slide.addText(text, {
    x: 0.82,
    y: 2.12,
    w: 3,
    h: 0.2,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 14.5,
    bold: true,
    color: BASE.text,
  });
}

function infoRow(slide, x, y, label, text, accent, isDark = true) {
  const textColor = isDark ? BASE.white : BASE.text;
  const borderColor = isDark ? "B9D4EC" : accent;
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w: 0.92,
    h: 0.4,
    rectRadius: 0.04,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText(label, {
    x,
    y: y + 0.1,
    w: 0.92,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 9.8,
    bold: true,
    color: BASE.white,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 1.06,
    y,
    w: 2.15,
    h: 0.4,
    rectRadius: 0.04,
    line: { color: borderColor, width: 1 },
    fill: { color: isDark ? "102C48" : BASE.white, transparency: isDark ? 10 : 0 },
  });
  slide.addText(text, {
    x: x + 1.18,
    y: y + 0.09,
    w: 1.9,
    h: 0.16,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 9.1,
    color: textColor,
  });
}

function pill(slide, x, y, w, h, text, color, textColor = BASE.text, fontSize = 10.1) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.04,
    line: { color, width: 1.1 },
    fill: { color: BASE.white },
  });
  slide.addText(text, {
    x,
    y: y + 0.1,
    w,
    h: h - 0.12,
    margin: 0,
    align: "center",
    valign: "mid",
    fontFace: "Microsoft YaHei",
    fontSize,
    bold: true,
    color: textColor,
  });
}

function block(slide, x, y, w, h, title, body, accent, bodySize = 9.4) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.06,
    line: { color: accent, width: 1.2 },
    fill: { color: BASE.white },
    shadow: safeOuterShadow("A6BFDA", 0.08, 45, 2, 1),
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 0.1,
    y: y + 0.1,
    w: Math.min(1.5, w - 0.2),
    h: 0.32,
    rectRadius: 0.04,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText(title, {
    x: x + 0.16,
    y: y + 0.18,
    w: w - 0.2,
    h: 0.14,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 10.6,
    bold: true,
    color: BASE.white,
  });
  slide.addText(body, {
    x: x + 0.14,
    y: y + 0.54,
    w: w - 0.22,
    h: h - 0.64,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: bodySize,
    color: BASE.text,
    valign: "top",
  });
}

function arrow(slide, x, y, w, h = 0, color = BASE.line) {
  slide.addShape(pptx.ShapeType.line, {
    x,
    y,
    w,
    h,
    line: { color, width: 1.25, beginArrowType: "none", endArrowType: "triangle" },
  });
}

function keywordChips(slide, words, accent) {
  let x = 9.42;
  let y = 6.12;
  words.forEach((word, idx) => {
    const w = 0.82 + Math.max(0, word.length - 4) * 0.12;
    slide.addShape(pptx.ShapeType.roundRect, {
      x,
      y,
      w,
      h: 0.3,
      rectRadius: 0.06,
      line: { color: accent, width: 1 },
      fill: { color: BASE.white, transparency: 5 },
    });
    slide.addText(word, {
      x,
      y: y + 0.08,
      w,
      h: 0.12,
      margin: 0,
      align: "center",
      fontFace: "Microsoft YaHei",
      fontSize: 8.8,
      bold: true,
      color: BASE.white,
    });
    x += w + 0.12;
    if (idx === 1) {
      x = 9.42;
      y = 6.48;
    }
  });
}

function footer(slide) {
  slide.addText("江苏南大五维电子科技有限公司", {
    x: 0.66,
    y: 7.02,
    w: 3.2,
    h: 0.14,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 8,
    color: "B6C8DA",
  });
}

function finalize(slide) {
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function buildMembraneSlide() {
  const accent = "2EA7FF";
  const accent2 = "26D3C6";
  const slide = pptx.addSlide();
  slideBg(slide, accent, accent2);
  header(slide, "模型一", "膜污染预判与清洗", "机理-数据双驱的智能维保架构", accent);
  mainPanel(slide);
  sidePanel(slide, accent);
  panelTitle(slide, "算法架构图");

  pill(slide, 1.02, 2.5, 1.28, 0.46, "TMP / 压差", accent);
  pill(slide, 2.5, 2.5, 1.08, 0.46, "通量", accent2);
  pill(slide, 3.78, 2.5, 1.24, 0.46, "浊度 / SDI", "31B56A");
  pill(slide, 5.22, 2.5, 1.46, 0.46, "清洗历史", "F4A014");

  arrow(slide, 1.66, 2.96, 0.38, 0.28);
  arrow(slide, 3.04, 2.96, 0.18, 0.28);
  arrow(slide, 4.4, 2.96, -0.1, 0.28);
  arrow(slide, 5.95, 2.96, -0.52, 0.28);

  block(slide, 2.02, 3.32, 4.36, 0.82, "数据治理层", "缺失补全、异常剔除、时滞对齐、特征构造", accent, 9.8);
  arrow(slide, 4.18, 4.14, 0, 0.2);
  block(slide, 1.04, 4.48, 2.02, 1.02, "征兆识别", "EWMA\nIsolation Forest", accent2, 10);
  block(slide, 3.16, 4.48, 2.18, 1.02, "污染分型", "RF / SVM\n区分结垢、胶体、有机、生物污染", "2AAE66", 9.2);
  block(slide, 5.48, 4.48, 1.62, 1.02, "趋势预判", "LSTM\nTCN", "F59E0B", 10);
  arrow(slide, 2.02, 5.5, 1.16, 0.34);
  arrow(slide, 4.34, 5.5, 1.16, 0.34);
  block(slide, 2.34, 5.76, 3.78, 0.74, "清洗决策生成", "规则库 + 贝叶斯优化输出时机、剂型、浓度和时长", "F05A4A", 9.1);
  arrow(slide, 6.12, 6.12, 0.68, 0);
  pill(slide, 6.9, 5.95, 0.62, 0.38, "输出", "F05A4A", BASE.text, 9.4);

  infoRow(slide, 9.42, 2.76, "目标", "按需清洗、精准护膜", accent);
  infoRow(slide, 9.42, 3.32, "底座", "EWMA / RF / SVM / LSTM / TCN", accent2);
  infoRow(slide, 9.42, 3.88, "前沿", "B-PINN 嵌入物理方程与不确定性", "31B56A");
  infoRow(slide, 9.42, 4.44, "输出", "清洗窗口、剂型、浓度、时长", "F59E0B");
  infoRow(slide, 9.42, 5.0, "价值", "把被动清洗改造成按需清洗", "F05A4A");
  keywordChips(slide, ["异常前兆", "污染分型", "时间窗口", "B-PINN"], accent);
  footer(slide);
  finalize(slide);
}

function buildBoilerSlide() {
  const accent = "21B573";
  const accent2 = "27C5D9";
  const slide = pptx.addSlide();
  slideBg(slide, accent, accent2);
  header(slide, "模型二", "锅炉给水水质与药剂协同", "全局寻优的经济预测控制架构", accent);
  mainPanel(slide);
  sidePanel(slide, accent);
  panelTitle(slide, "算法架构图");

  pill(slide, 1.02, 2.5, 1.06, 0.46, "pH", "2E86DE");
  pill(slide, 2.28, 2.5, 1.08, 0.46, "流量", accent2);
  pill(slide, 3.56, 2.5, 1.08, 0.46, "温度", accent);
  pill(slide, 4.84, 2.5, 1.62, 0.46, "泵阀 / 回流", "F4A014");

  arrow(slide, 1.54, 2.96, 0.38, 0.28);
  arrow(slide, 2.84, 2.96, 0.18, 0.28);
  arrow(slide, 4.12, 2.96, -0.08, 0.28);
  arrow(slide, 5.86, 2.96, -0.54, 0.28);

  block(slide, 1.94, 3.32, 4.44, 0.82, "数据治理层", "采样统一、异常剔除、状态编码、回流与流量耦合整理", "2E86DE", 9.5);
  arrow(slide, 4.16, 4.14, 0, 0.2);
  block(slide, 1.04, 4.48, 2.04, 1.02, "状态估计", "CatBoost\nXGBoost", accent2, 10);
  block(slide, 3.18, 4.48, 2.08, 1.02, "时序预判", "LSTM\n流量突变 - pH 趋势", accent, 9.5);
  block(slide, 5.42, 4.48, 1.48, 1.02, "保护层", "阈值\n滞回", "F05A4A", 10);
  arrow(slide, 2.04, 5.5, 1.14, 0.34);
  arrow(slide, 4.3, 5.5, 1.12, 0.34);
  block(slide, 2.36, 5.76, 3.74, 0.74, "多目标优化控制", "NSGA-II 联动药剂、能耗与约束边界并输出执行量", "F4A014", 9.1);
  arrow(slide, 6.1, 6.12, 0.68, 0);
  pill(slide, 6.9, 5.95, 0.62, 0.38, "执行", "F4A014", BASE.text, 9.4);

  infoRow(slide, 9.42, 2.76, "目标", "pH 稳定 + 综合成本最低", accent);
  infoRow(slide, 9.42, 3.32, "底座", "CatBoost / XGBoost + LSTM + NSGA-II", accent2);
  infoRow(slide, 9.42, 3.88, "前沿", "DIOKO EMPC 做实时经济预测控制", "31B56A");
  infoRow(slide, 9.42, 4.44, "输出", "投药量、执行边界、经济成本", "F59E0B");
  infoRow(slide, 9.42, 5.0, "价值", "把 pH 安全与经济最优放进同一控制框架", "F05A4A");
  keywordChips(slide, ["状态估计", "LSTM", "NSGA-II", "DIOKO"], accent);
  footer(slide);
  finalize(slide);
}

function buildHardnessSlide() {
  const accent = "F3A41A";
  const accent2 = "31C3C8";
  const slide = pptx.addSlide();
  slideBg(slide, accent, accent2);
  header(slide, "模型三", "深度水处理硬度调节", "认知驱动的机理融合抗扰架构", accent);
  mainPanel(slide);
  sidePanel(slide, accent);
  panelTitle(slide, "算法架构图");

  pill(slide, 1.0, 2.5, 1.34, 0.46, "原水硬度", "2E86DE");
  pill(slide, 2.54, 2.5, 1.04, 0.46, "流量", accent2);
  pill(slide, 3.78, 2.5, 1.04, 0.46, "浊度", "2BB468");
  pill(slide, 5.02, 2.5, 1.42, 0.46, "出水硬度", accent);

  arrow(slide, 1.66, 2.96, 0.34, 0.28);
  arrow(slide, 2.98, 2.96, 0.16, 0.28);
  arrow(slide, 4.2, 2.96, -0.08, 0.28);
  arrow(slide, 5.74, 2.96, -0.48, 0.28);

  block(slide, 1.98, 3.32, 4.4, 0.82, "数据治理层", "缺失补全、异常剔除、时滞对齐、波动特征提取", "2E86DE", 9.5);
  arrow(slide, 4.16, 4.14, 0, 0.2);
  block(slide, 1.08, 4.48, 2.04, 1.02, "状态估计", "XGBoost\nCatBoost", accent2, 10);
  block(slide, 3.22, 4.48, 2.06, 1.02, "波动预判", "TCN\nTransformer", "2BB468", 10);
  block(slide, 5.42, 4.48, 1.48, 1.02, "反馈修偏", "偏差\n校正", "F05A4A", 10);
  arrow(slide, 2.06, 5.5, 1.16, 0.34);
  arrow(slide, 4.3, 5.5, 1.12, 0.34);
  block(slide, 2.42, 5.76, 3.66, 0.74, "前馈 + 反馈控制", "MPC / BayesOpt 计算碳酸钠投加量与控制边界", accent, 9.1);
  arrow(slide, 6.08, 6.12, 0.7, 0);
  pill(slide, 6.9, 5.95, 0.62, 0.38, "执行", accent, BASE.text, 9.4);

  infoRow(slide, 9.42, 2.76, "目标", "硬度区间稳定命中 + 药耗收缩", accent);
  infoRow(slide, 9.42, 3.32, "底座", "XGBoost + TCN / Transformer + MPC", accent2);
  infoRow(slide, 9.42, 3.88, "前沿", "Fuzzy GNN 做图结构解释增强", "31B56A");
  infoRow(slide, 9.42, 4.44, "输出", "投药量、命中率、收敛速度", "F59E0B");
  infoRow(slide, 9.42, 5.0, "价值", "把机理、数据与解释能力统一建模", "F05A4A");
  keywordChips(slide, ["波动预测", "前馈反馈", "硬度区间", "Fuzzy GNN"], accent);
  footer(slide);
  finalize(slide);
}

async function main() {
  buildMembraneSlide();
  buildBoilerSlide();
  buildHardnessSlide();
  const out = path.join(PROJECT_ROOT, "水处理智能精准控制一体化项目_三模型算法架构三页版.pptx");
  await pptx.writeFile({ fileName: out });
  console.log(`WROTE ${out}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
