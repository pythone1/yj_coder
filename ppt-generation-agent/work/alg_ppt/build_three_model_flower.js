const path = require("path");
const PptxGenJS = require("pptxgenjs");
const { warnIfSlideElementsOutOfBounds } = require("./pptxgenjs_helpers/layout");
const { safeOuterShadow } = require("./pptxgenjs_helpers/util");

const ROOT = __dirname;
const PROJECT_ROOT = path.resolve(ROOT, "..", "..");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "项目方案组";
pptx.company = "水处理智能精准控制一体化项目";
pptx.subject = "水处理智能精准控制三模型算法架构";
pptx.title = "水处理智能精准控制一体化项目 三模型算法架构三页版";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const FONT_TITLE = 25;
const FONT_BODY = 14;

const BASE = {
  bg: "071828",
  bg2: "0A2034",
  white: "F4FAFF",
  sub: "8EC6F2",
  text: "EAF5FF",
  panel: "0B1F31",
  panel2: "0D243A",
  line: "244C6C",
  gold: "F0C86B",
  blue: "63C4FF",
  green: "53EFA5",
};

const SLIDES = [
  {
    title: "膜污染预判与清洗AI决策模型",
    subtitle: "“机理-数据”双驱智能维保架构",
    leftHeader: "感知层",
    centerHeader: "算法层",
    rightHeader: "控制层",
    core: "核心中枢：智能预判与决策中枢",
    leftText:
      "【感知层】\n实时输入跨膜压差（TMP）、产水通量衰减率、\n进水浊度及清洗历史记录与膜龄。",
    basicText:
      "【基础算法层】\n1. 征兆识别：采用 EWMA（指数加权移动平均）与\nIsolation Forest（孤立森林）捕捉早期微小异常。\n2. 污染分类：随机森林（RF）、XGBoost 与 SVM\n精准区分结垢、有机、胶体或生物污染。\n3. 趋势预测：依托 LSTM 与 TCN（时间卷积网络）\n动态计算未来的清洗时间窗口。",
    frontierText:
      "【前沿点睛】\n引入贝叶斯物理信息神经网络（B-PINN）。通过将流体力学\n偏微分方程等物理机理嵌入神经网络的损失函数中，并结合\n贝叶斯推断，在少样本情况下即可高精度量化纳米级污染物\n转移与截留的不确定性，有效应对多孔介质的异质性挑战。",
    rightText:
      "【控制层】\n联动规则库与 Bayes Optimization（贝叶斯优化），\n输出“时机+配方+浓度+时长”的最优清洗指令，\n确保预警至少覆盖 6 小时的人工处置窗口。",
    leftTags: ["TMP", "通量衰减率", "进水浊度", "清洗历史"],
    rightTags: ["时机", "配方", "浓度", "时长"],
    leftColor: BASE.blue,
    centerColor: BASE.gold,
    rightColor: BASE.green,
  },
  {
    title: "锅炉给水水质与药剂协同AI模型",
    subtitle: "全局寻优的经济预测控制",
    leftHeader: "感知层",
    centerHeader: "算法层",
    rightHeader: "控制层",
    core: "核心中枢：多目标经济寻优中枢",
    leftText:
      "【感知层】\n实时采集进水流量、凝结水 pH、温度及加药泵和\n阀门的启停状态。",
    basicText:
      "【基础算法层】\n1. 短时状态估计：CatBoost / XGBoost 快速计算当\n前水质工况下的药剂需求。\n2. 时序预测：LSTM / GRU / TCN 深度挖掘多变量\n关系，预测未来 10-30 分钟内的水质与流量走势。",
    frontierText:
      "【前沿点睛】\n引入深层输入输出 Koopman 算子（DIOKO）的经济模型预测控制。\n该算法将高维非线性的水质动态变化映射到高维线性隐空间中，\n将复杂的非凸优化问题直接转化为极易求解的二次规划问题。\n不仅使计算效率呈指数级提升（超 5600 倍），还在无需全状态\n物理测量的情况下提供极致的鲁棒性与成本控制。",
    rightText:
      "【控制层】\n结合阈值保护与滞回逻辑快速止损，采用 MPC\n（模型预测控制）与 NSGA-II（多目标遗传算法）\n联动求解，计算氨水等药剂的最佳投加量与执行边界，\n长效锁定 pH 在 8.8-9.3 的安全区间。",
    leftTags: ["进水流量", "凝结水 pH", "温度", "泵阀启停"],
    rightTags: ["阈值保护", "MPC", "NSGA-II", "pH 8.8-9.3"],
    leftColor: BASE.blue,
    centerColor: BASE.gold,
    rightColor: BASE.green,
  },
  {
    title: "深度水处理硬度调节AI模型",
    subtitle: "机理融合的精准抗扰闭环系统",
    leftHeader: "感知层",
    centerHeader: "算法层",
    rightHeader: "控制层",
    core: "核心中枢：闭环抗扰决策中枢",
    leftText:
      "【感知层】\n实时输入原水硬度、进水流量、浊度、碱度及出水\n硬度的反馈值。",
    basicText:
      "【基础算法层】\n1. 状态估计：运用 XGBoost / CatBoost 完成数据缺失\n补全、异常剔除与时滞对齐，深度解析非线性映射规律。\n2. 长时波动预测：引入 Transformer / TCN 提取多变量\n的长依赖关系，预判未来 30-60 分钟的原水硬度冲击波动轨迹。",
    frontierText:
      "【前沿点睛】\n引入可解释性模糊图神经网络（Fuzzy GNN）。通过构建空间拓扑图并\n结合互信息与模糊逻辑（Fuzzy Logic），模型能够自动生成人类可读的\n语义规则。在不牺牲预测精度的前提下提供空间局部化的规则解释，\n支持运维专家直接核实预判逻辑，大幅降低水处理误判率。",
    rightText:
      "【控制层】\n采用“前馈预测 + 反馈校正 + MPC / BayesOpt”闭环控制\n体系。最大化抑制超调与振荡，将出水硬度精准锁定在\n270-280 mg/L 命中区间，控制碳酸钠的吨水消耗。",
    leftTags: ["原水硬度", "进水流量", "浊度", "碱度+反馈"],
    rightTags: ["前馈预测", "反馈校正", "MPC / BayesOpt", "270-280 mg/L"],
    leftColor: BASE.blue,
    centerColor: BASE.gold,
    rightColor: BASE.green,
  },
];

function addBackground(slide) {
  slide.background = { color: BASE.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: H,
    line: { color: BASE.bg, transparency: 100 },
    fill: { color: BASE.bg },
  });

  slide.addShape(pptx.ShapeType.ellipse, {
    x: 10.02,
    y: 0.08,
    w: 2.7,
    h: 2.7,
    line: { color: BASE.blue, transparency: 100 },
    fill: { color: BASE.blue, transparency: 92 },
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 0.06,
    y: 4.88,
    w: 2.2,
    h: 2.2,
    line: { color: BASE.green, transparency: 100 },
    fill: { color: BASE.green, transparency: 95 },
  });

  for (let i = 0; i < 7; i++) {
    slide.addShape(pptx.ShapeType.line, {
      x: 0.2,
      y: 1.02 + i * 0.88,
      w: 12.9,
      h: 0,
      line: { color: BASE.line, transparency: 84, width: 0.7 },
    });
  }
  for (let i = 0; i < 11; i++) {
    slide.addShape(pptx.ShapeType.line, {
      x: 0.55 + i * 1.18,
      y: 0.04,
      w: 0,
      h: 7.1,
      line: { color: BASE.line, transparency: 92, width: 0.5 },
    });
  }
}

function addTitle(slide, data) {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.22,
    y: 0.18,
    w: 0.06,
    h: 0.56,
    line: { color: data.leftColor, transparency: 100 },
    fill: { color: data.leftColor },
  });
  slide.addText(data.title, {
    x: 0.42,
    y: 0.14,
    w: 8.8,
    h: 0.34,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: FONT_TITLE,
    bold: true,
    color: BASE.white,
  });
  slide.addText(data.subtitle, {
    x: 0.42,
    y: 0.56,
    w: 8.8,
    h: 0.2,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: FONT_BODY,
    color: BASE.sub,
  });
}

function addPanel(slide, x, y, w, h, color, title) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.05,
    line: { color, width: 1.3, transparency: 18 },
    fill: { color: BASE.panel, transparency: 8 },
    shadow: safeOuterShadow("08111B", 0.26, 45, 2.5, 1),
  });
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w,
    h: 0.46,
    line: { color, transparency: 50, width: 1 },
    fill: { color, transparency: 78 },
  });
  slide.addText(title, {
    x: x + 0.14,
    y: y + 0.09,
    w: w - 0.28,
    h: 0.14,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: FONT_BODY,
    bold: true,
    color,
  });
}

function addArrow(slide, x, y, w, color) {
  slide.addShape(pptx.ShapeType.line, {
    x,
    y,
    w,
    h: 0,
    line: { color, width: 1.8, endArrowType: "triangle" },
  });
}

function addBoxTitle(slide, text, x, y, w, color) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.38,
    rectRadius: 0.05,
    line: { color, transparency: 100 },
    fill: { color, transparency: 78 },
  });
  slide.addText(text, {
    x: x + 0.08,
    y: y + 0.09,
    w: w - 0.16,
    h: 0.12,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: FONT_BODY,
    bold: true,
    color,
  });
}

function addTextBlock(slide, text, x, y, w, h, color, align = "left") {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    margin: 0.08,
    fontFace: "Microsoft YaHei",
    fontSize: FONT_BODY,
    color,
    valign: "mid",
    breakLine: false,
    align,
  });
}

function addChipGrid(slide, chips, x, y, w, color) {
  const gapX = 0.12;
  const gapY = 0.12;
  const chipW = (w - gapX) / 2;
  const chipH = 0.46;
  chips.forEach((chip, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const cx = x + col * (chipW + gapX);
    const cy = y + row * (chipH + gapY);
    slide.addShape(pptx.ShapeType.roundRect, {
      x: cx,
      y: cy,
      w: chipW,
      h: chipH,
      rectRadius: 0.05,
      line: { color, width: 1, transparency: 30 },
      fill: { color, transparency: 84 },
    });
    slide.addText(chip, {
      x: cx + 0.03,
      y: cy + 0.12,
      w: chipW - 0.06,
      h: 0.12,
      margin: 0,
      align: "center",
      fontFace: "Microsoft YaHei",
      fontSize: FONT_BODY,
      color,
    });
  });
}

function addLeftPanelBody(slide, data, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 0.16,
    y: y + 0.66,
    w: w - 0.32,
    h: 3.08,
    rectRadius: 0.05,
    line: { color: data.leftColor, transparency: 55, width: 1 },
    fill: { color: BASE.panel2, transparency: 12 },
  });
  addTextBlock(slide, data.leftText, x + 0.28, y + 0.82, w - 0.56, 2.74, BASE.text);
  slide.addShape(pptx.ShapeType.line, {
    x: x + 0.22,
    y: y + 3.98,
    w: w - 0.44,
    h: 0,
    line: { color: data.leftColor, transparency: 65, width: 0.9 },
  });
  addChipGrid(slide, data.leftTags, x + 0.18, y + 4.18, w - 0.36, data.leftColor);
}

function addRightPanelBody(slide, data, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 0.16,
    y: y + 0.66,
    w: w - 0.32,
    h: 3.48,
    rectRadius: 0.05,
    line: { color: data.rightColor, transparency: 55, width: 1 },
    fill: { color: BASE.panel2, transparency: 12 },
  });
  addTextBlock(slide, data.rightText, x + 0.28, y + 0.82, w - 0.56, 3.14, BASE.text);
  slide.addShape(pptx.ShapeType.line, {
    x: x + 0.22,
    y: y + 4.34,
    w: w - 0.44,
    h: 0,
    line: { color: data.rightColor, transparency: 65, width: 0.9 },
  });
  addChipGrid(slide, data.rightTags, x + 0.18, y + 4.52, w - 0.36, data.rightColor);
}

function addCenterPanelBody(slide, data, x, y, w, h) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 1.02,
    y: y + 0.68,
    w: w - 2.04,
    h: 0.52,
    rectRadius: 0.06,
    line: { color: data.centerColor, transparency: 28, width: 1.1 },
    fill: { color: data.centerColor, transparency: 86 },
  });
  slide.addText(data.core, {
    x: x + 1.14,
    y: y + 0.86,
    w: w - 2.28,
    h: 0.12,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: FONT_BODY,
    bold: true,
    color: data.centerColor,
  });

  slide.addShape(pptx.ShapeType.line, {
    x: x + w / 2,
    y: y + 1.2,
    w: 0,
    h: 0.34,
    line: { color: data.centerColor, width: 1.6, endArrowType: "triangle" },
  });

  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 0.32,
    y: y + 1.58,
    w: w - 0.64,
    h: 2.0,
    rectRadius: 0.05,
    line: { color: data.centerColor, transparency: 18, width: 1.1 },
    fill: { color: BASE.panel2, transparency: 6 },
  });
  addBoxTitle(slide, "基础算法层", x + 2.16, y + 1.4, 1.88, data.centerColor);
  addTextBlock(slide, data.basicText, x + 0.52, y + 1.84, w - 1.04, 1.56, BASE.text);

  slide.addShape(pptx.ShapeType.line, {
    x: x + w / 2,
    y: y + 3.58,
    w: 0,
    h: 0.3,
    line: { color: data.centerColor, width: 1.6, endArrowType: "triangle" },
  });

  slide.addShape(pptx.ShapeType.roundRect, {
    x: x + 0.32,
    y: y + 3.92,
    w: w - 0.64,
    h: 1.82,
    rectRadius: 0.05,
    line: { color: data.centerColor, transparency: 18, width: 1.1 },
    fill: { color: BASE.panel2, transparency: 6 },
  });
  addBoxTitle(slide, "前沿点睛", x + 2.3, y + 3.74, 1.6, data.centerColor);
  addTextBlock(slide, data.frontierText, x + 0.52, y + 4.12, w - 1.04, 1.46, BASE.text);
}

function finalize(slide) {
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function buildSlide(data) {
  const slide = pptx.addSlide();
  addBackground(slide);
  addTitle(slide, data);

  const y = 1.08;
  const h = 6.06;
  const leftX = 0.3;
  const leftW = 2.75;
  const centerX = 3.28;
  const centerW = 6.78;
  const rightX = 10.28;
  const rightW = 2.75;

  addPanel(slide, leftX, y, leftW, h, data.leftColor, data.leftHeader);
  addPanel(slide, centerX, y, centerW, h, data.centerColor, data.centerHeader);
  addPanel(slide, rightX, y, rightW, h, data.rightColor, data.rightHeader);

  addArrow(slide, 3.07, 3.88, 0.17, data.leftColor);
  addArrow(slide, 10.08, 3.88, 0.17, data.rightColor);

  addLeftPanelBody(slide, data, leftX, y, leftW, h);
  addCenterPanelBody(slide, data, centerX, y, centerW, h);
  addRightPanelBody(slide, data, rightX, y, rightW, h);

  finalize(slide);
}

async function main() {
  SLIDES.forEach(buildSlide);
  const out = path.join(PROJECT_ROOT, "水处理智能精准控制一体化项目_三模型算法架构三页版.pptx");
  await pptx.writeFile({ fileName: out });
  console.log(`WROTE ${out}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
