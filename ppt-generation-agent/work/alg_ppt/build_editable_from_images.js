const path = require("path");
const PptxGenJS = require("pptxgenjs");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers/layout");
const { safeOuterShadow } = require("./pptxgenjs_helpers/util");
const { imageSizingContain } = require("./pptxgenjs_helpers/image");

const ROOT = __dirname;
const PROJECT_ROOT = path.resolve(ROOT, "..", "..");
const ASSET = (...parts) => path.join(ROOT, "editable_assets_clean", ...parts);

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "水处理智能精准控制一体化项目";
pptx.subject = "架构图拆分可编辑版";
pptx.title = "架构图拆分可编辑版";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const C = {
  bg: "F7FBFF",
  blue: "6DBBEF",
  blue2: "DFF2FB",
  teal: "84D7D0",
  teal2: "E8F8F6",
  green: "8AD8B4",
  purple: "CBBCE8",
  purple2: "F3EDFA",
  text: "1D2E3A",
  sub: "4F7288",
  line: "A9C8D8",
  orange: "F8B44B",
  orange2: "FFF1CF",
};

function addBg(slide) {
  slide.background = { color: C.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: H,
    line: { color: C.bg, transparency: 100 },
    fill: { color: C.bg },
  });
}

function addTitle(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.28,
    y: 0.18,
    w: 10.9,
    h: 0.46,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 21,
    bold: true,
    color: "17252F",
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 3.35,
      y: 0.68,
      w: 6.8,
      h: 0.2,
      margin: 0,
      align: "center",
      fontFace: "Microsoft YaHei",
      fontSize: 11.5,
      bold: true,
      color: "253744",
    });
  }
}

function addPanel(slide, opts) {
  const { x, y, w, h, color, title, fill = "FFFFFF" } = opts;
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.05,
    line: { color, width: 1.2, transparency: 10 },
    fill: { color: fill },
    shadow: safeOuterShadow("BACFDC", 0.14, 45, 1.5, 0.5),
  });
  if (title) {
    slide.addShape(pptx.ShapeType.rect, {
      x,
      y,
      w,
      h: 0.42,
      line: { color, transparency: 100 },
      fill: { color, transparency: 40 },
    });
    slide.addText(title, {
      x: x + 0.08,
      y: y + 0.1,
      w: w - 0.16,
      h: 0.14,
      margin: 0,
      align: "center",
      fontFace: "Microsoft YaHei",
      fontSize: 12,
      bold: true,
      color: "203541",
    });
  }
}

function addSectionLabel(slide, text, x, y, w) {
  slide.addText(text, {
    x,
    y,
    w,
    h: 0.18,
    margin: 0,
    align: "center",
    fontFace: "Microsoft YaHei",
    fontSize: 10.2,
    bold: true,
    color: "213541",
  });
}

function addBody(slide, text, x, y, w, h, size = 9.2, opts = {}) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    margin: opts.margin ?? 0.02,
    fontFace: "Microsoft YaHei",
    fontSize: size,
    color: opts.color || C.text,
    bold: !!opts.bold,
    breakLine: false,
    valign: opts.valign || "top",
    align: opts.align || "left",
  });
}

function addImg(slide, imgPath, x, y, w, h) {
  slide.addImage({ path: imgPath, ...imageSizingContain(imgPath, x, y, w, h) });
}

function addDivider(slide, x, y, w, color = C.line) {
  slide.addShape(pptx.ShapeType.line, {
    x,
    y,
    w,
    h: 0,
    line: { color, width: 0.8, transparency: 20 },
  });
}

function addMiniCard(slide, text, x, y, w, h, color = C.teal) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.04,
    line: { color, width: 1, transparency: 12 },
    fill: { color: "FFFFFF" },
  });
  addBody(slide, text, x + 0.04, y + 0.08, w - 0.08, h - 0.12, 9.2, {
    bold: true,
    align: "center",
    valign: "mid",
  });
}

function addDot(slide, x, y, r = 0.08, color = C.blue) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x: x - r,
    y: y - r,
    w: r * 2,
    h: r * 2,
    line: { color, transparency: 100 },
    fill: { color },
  });
}

function connect(slide, x1, y1, x2, y2, color = "86AFC6", width = 1) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1,
    y: y1,
    w: x2 - x1,
    h: y2 - y1,
    line: { color, width, transparency: 18 },
  });
}

function membraneSlide() {
  const slide = pptx.addSlide();
  addBg(slide);
  addTitle(slide, "水处理 AI 决策模型架构：\n膜污染预判与智能清洗一体化方案");

  addImg(slide, ASSET("m_membrane.png"), 0.18, 0.82, 4.45, 1.26);

  addPanel(slide, {
    x: 0.18,
    y: 2.08,
    w: 4.25,
    h: 5.1,
    color: C.blue,
    title: "感知与数据治理层",
    fill: "FDFEFF",
  });
  addSectionLabel(slide, "多源数据实时感知", 0.36, 2.56, 3.9);
  addImg(slide, ASSET("m_sense_icons.png"), 0.42, 2.84, 3.78, 0.82);
  addBody(
    slide,
    "膜压差（TMP）    产水通量    浊度/SDI    清洗历史记录及膜龄",
    0.35,
    3.74,
    3.95,
    0.26,
    8.8,
    { align: "center" }
  );
  addDivider(slide, 0.34, 4.04, 3.92);
  addSectionLabel(slide, "工业数据精细化治理", 0.36, 4.12, 3.9);
  addImg(slide, ASSET("m_flow_arrow.png"), 0.48, 4.38, 3.64, 0.56);
  addBody(
    slide,
    "运用 3σ 原则剔除异常值，通过线性插值补全缺失，\n并利用互相关算法解决水力滞后引起的时间错位。",
    0.36,
    5.0,
    3.92,
    0.52
  );
  addDivider(slide, 0.34, 5.56, 3.92);
  addSectionLabel(slide, "特征构造与归一化", 0.36, 5.64, 3.9);
  addImg(slide, ASSET("m_feature_icons.png"), 0.48, 5.96, 3.64, 0.6);
  addBody(
    slide,
    "计算压差日增速、通量衰减率等衍生指标，并将不同量级的\n指标标准化，确保模型训练的权重平衡。",
    0.36,
    6.72,
    3.92,
    0.34
  );

  addPanel(slide, {
    x: 4.68,
    y: 0.92,
    w: 8.44,
    h: 2.02,
    color: C.teal,
    title: "基础算法层",
    fill: "FCFFFF",
  });
  const algCards = [
    {
      x: 4.84,
      title: "EWMA 与孤立森林：征兆识别",
      img: "m_alg_ewma.png",
      body: "指数加权移动平均（EWMA）与\nIsolation Forest 联动，捕捉膜污染早期\n信号与运行异常。",
    },
    {
      x: 7.63,
      title: "随机森林与 XGBoost：污染分类",
      img: "m_alg_rf.png",
      body: "采用随机森林（RF）等分类算法，精准\n识别结垢、有机污染、胶体污染或生物\n污染类型。",
    },
    {
      x: 10.42,
      title: "LSTM 与 TCN：趋势预测",
      img: "m_alg_tcn.png",
      body: "利用长短期记忆网络（LSTM）或时间卷积\n网络（TCN）计算未来 6-24 小时内的\n清洗窗口。",
    },
  ];
  algCards.forEach((card) => {
    addPanel(slide, {
      x: card.x,
      y: 1.34,
      w: 2.55,
      h: 1.34,
      color: C.teal,
      fill: "F9FEFD",
    });
    addBody(slide, card.title, card.x + 0.08, 1.42, 2.4, 0.24, 9.1, {
      bold: true,
    });
    addImg(slide, ASSET(card.img), card.x + 0.18, 1.74, 2.18, 0.38);
    addBody(slide, card.body, card.x + 0.08, 2.16, 2.4, 0.38, 8.25);
  });

  addPanel(slide, {
    x: 4.68,
    y: 3.04,
    w: 8.44,
    h: 2.3,
    color: C.teal,
    title: "控制与决策层",
    fill: "FCFFFF",
  });
  addPanel(slide, {
    x: 4.86,
    y: 3.46,
    w: 3.72,
    h: 0.84,
    color: C.teal,
    fill: "F9FEFD",
  });
  addBody(slide, "贝叶斯优化策略生成", 5.05, 3.54, 3.3, 0.16, 9.8, {
    bold: true,
    align: "center",
  });
  addImg(slide, ASSET("m_ctrl_bayes.png"), 5.08, 3.76, 3.22, 0.28);
  addBody(slide, "预置规则库 + 贝叶斯优化算法", 5.02, 4.1, 3.36, 0.14, 8.6, {
    align: "center",
  });

  addPanel(slide, {
    x: 8.72,
    y: 3.46,
    w: 4.18,
    h: 0.84,
    color: C.teal,
    fill: "F9FEFD",
  });
  addBody(slide, "最优清洗方案配置", 8.92, 3.54, 3.78, 0.16, 9.8, {
    bold: true,
    align: "center",
  });
  addImg(slide, ASSET("m_ctrl_config.png"), 8.92, 3.76, 2.06, 0.32);
  addBody(
    slide,
    "清洗程序\n药剂浓度\n清洗时长",
    11.16,
    3.72,
    1.35,
    0.42,
    8.8,
    { bold: true }
  );

  addDivider(slide, 4.96, 4.34, 7.82, C.teal);

  addBody(slide, "指令下发与执行反馈", 5.02, 4.46, 2.3, 0.16, 9.8, {
    bold: true,
    align: "center",
  });
  addImg(slide, ASSET("m_ctrl_action.png"), 5.02, 4.72, 1.58, 0.32);
  addBody(
    slide,
    "加药泵频率\n阀门开度\n实时监测执行效果，\n持续修正模型偏差。",
    6.88,
    4.64,
    1.72,
    0.46,
    8.8,
    { align: "center" }
  );

  addBody(slide, "核心目标：按需清洗", 9.02, 4.46, 2.85, 0.16, 9.8, {
    bold: true,
    align: "center",
  });
  addImg(slide, ASSET("m_ctrl_goal.png"), 9.24, 4.68, 2.08, 0.4);
  addBody(
    slide,
    "沿清洗效果与膜寿命共同寻优，\n实现出水稳定达标与膜水处理成本最小化。",
    8.86,
    5.08,
    3.25,
    0.24,
    8.5,
    { align: "center" }
  );

  addPanel(slide, {
    x: 4.68,
    y: 5.48,
    w: 8.44,
    h: 1.68,
    color: C.purple,
    title: "前沿发散补充：B-PINN 框架",
    fill: "FEFBFF",
  });
  addBody(slide, "物理信息神经网络（B-PINN）", 4.98, 5.72, 2.58, 0.16, 9.4, {
    bold: true,
    align: "center",
  });
  addImg(slide, ASSET("m_bpin_nnet.png"), 5.02, 5.96, 2.1, 0.38);
  addBody(
    slide,
    "通过贝叶斯推断表达传质介质中的噪声，\n提供预测的量化区间，增强复杂环境下的鲁棒性。",
    4.96,
    6.44,
    2.42,
    0.28,
    8.0,
    { align: "center" }
  );
  addImg(slide, ASSET("m_bpin_dist.png"), 7.58, 5.98, 1.44, 0.4);
  addBody(
    slide,
    "贝叶斯推断与不确定性量化",
    7.52,
    6.5,
    1.62,
    0.16,
    8.3,
    { bold: true, align: "center" }
  );
  addImg(slide, ASSET("m_bpin_bridge.png"), 10.18, 5.96, 2.12, 0.38);
  addBody(
    slide,
    "利用 PINN 的反演模型设计初始参数，\n为真实工况下的预测推演提供更精准的仿真底座。",
    9.94,
    6.44,
    2.92,
    0.28,
    8.0,
    { align: "center" }
  );

  warnIfSlideHasOverlaps(slide, pptx, {
    muteContainment: true,
    ignoreLines: true,
    ignoreDecorativeShapes: true,
  });
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function boilerSlide() {
  const slide = pptx.addSlide();
  addBg(slide);
  addTitle(
    slide,
    "锅炉给水水质与药剂协同 AI 模型：从感知到前沿优化的智慧控制架构",
    "实现 pH 值（8.8-9.3）精准稳定控制与药剂极致降本增效"
  );

  const cols = [
    { x: 0.22, title: "感知与数据治理层\n— 全维度状态捕捉" },
    { x: 3.47, title: "基础算法层\n— 状态估计与趋势预判" },
    { x: 6.72, title: "控制与优化层\n— 多目标精准控制" },
    { x: 9.97, title: "前沿探索层\n— 极致优化与性能跃迁" },
  ];
  cols.forEach((col) =>
    addPanel(slide, {
      x: col.x,
      y: 1.28,
      w: 2.96,
      h: 5.92,
      color: C.line,
      title: col.title,
      fill: "FDFEFF",
    })
  );

  addImg(slide, ASSET("b_col1_top.png"), 0.42, 1.95, 2.55, 0.95);
  addBody(
    slide,
    "多维实时数据输入：实时采集 pH 值、进水流量、温度、凝结水回流状态以及加药泵/阀门的运行参数。",
    0.38,
    3.02,
    2.64,
    0.62,
    8.85,
    { bold: true }
  );
  addImg(slide, ASSET("b_col1_mid.png"), 0.42, 3.88, 2.55, 0.98);
  addBody(
    slide,
    "数据治理与特征提取：采用线性插值补全缺失值，并通过互相关算法解决“水力滞后”导致的时间错位，确保输入数据的连续性与关联性。",
    0.38,
    4.98,
    2.64,
    0.74,
    8.75,
    { bold: true }
  );
  addImg(slide, ASSET("b_col1_bot.png"), 0.42, 6.05, 2.55, 0.72);
  addBody(
    slide,
    "泵阀状态感知：捕捉加药泵频率与启停状态，为后续的执行反馈提供基础支撑。",
    0.38,
    6.78,
    2.64,
    0.32,
    8.8,
    { bold: true }
  );

  addImg(slide, ASSET("b_col2_top.png"), 3.64, 1.95, 2.62, 2.1);
  addBody(
    slide,
    "CatBoost 短时状态估计：利用 CatBoost 算法处理多维非线性关联，对当前系统的运行状态进行高精度估计。",
    3.64,
    4.1,
    2.62,
    0.62,
    8.7,
    { bold: true }
  );
  addImg(slide, ASSET("b_col2_bot.png"), 3.72, 5.16, 2.48, 0.88);
  addBody(
    slide,
    "LSTM/GRU/TCN 时序趋势预测：挖掘“历史流量-pH 变化”规律，提前 10-30 分钟预测 pH 值走势，实现对系统波动的超前感知。",
    3.64,
    6.14,
    2.62,
    0.8,
    8.6,
    { bold: true }
  );

  addImg(slide, ASSET("b_col3_top.png"), 6.92, 1.98, 2.56, 0.6);
  addBody(
    slide,
    "MPC 与 NSGA-II 协同优化：基于模型预测控制（MPC）与多目标遗传算法（NSGA-II），在满足工艺约束的前提下计算最优控制组合。",
    6.9,
    2.84,
    2.58,
    0.72,
    8.7,
    { bold: true }
  );
  addImg(slide, ASSET("b_col3_scale.png"), 7.06, 3.74, 1.48, 1.18);
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 8.74,
    y: 4.0,
    w: 0.92,
    h: 0.98,
    rectRadius: 0.05,
    line: { color: "00A8D7", transparency: 100 },
    fill: { color: "00BDEB", transparency: 8 },
  });
  addBody(slide, "↓20%", 8.8, 4.08, 0.8, 0.18, 18, {
    bold: true,
    color: C.orange,
    align: "center",
  });
  addBody(
    slide,
    "以上的降本潜力：\n通过智能调控，实现氨水吨水消耗低 20% 以上，\n显著优化资源配置。",
    8.8,
    4.34,
    0.78,
    0.56,
    8.5,
    { bold: true, color: "1E3B4D" }
  );
  addImg(slide, ASSET("b_col3_bot.png"), 6.94, 5.6, 2.45, 0.86);
  addBody(
    slide,
    "精准药剂投加建议：实时计算氨水投加量，确保 pH 值稳定在 8.8-9.3 的安全区间，有效防止过冲。",
    6.9,
    6.46,
    2.58,
    0.52,
    8.7,
    { bold: true }
  );

  addImg(slide, ASSET("b_col4_top.png"), 10.16, 1.98, 2.46, 0.86);
  addBody(
    slide,
    "DIOKO 深层输入输出 Koopman 算子：采用 DIOKO 框架将复杂的非线性动力学转化为线性 latent 空间，极大降低模型复杂度。",
    10.12,
    2.92,
    2.58,
    0.72,
    8.7,
    { bold: true }
  );
  addImg(slide, ASSET("b_col4_mid.png"), 10.2, 4.0, 2.38, 0.86);
  addBody(
    slide,
    "极速非凸优化（EMPC）：绕过复杂的非凸优化难题，利用凸优化算法实现计算效率的数千倍提升。",
    10.12,
    4.96,
    2.58,
    0.62,
    8.7,
    { bold: true }
  );
  addImg(slide, ASSET("b_col4_bot.png"), 10.34, 5.94, 2.08, 0.66);
  addBody(
    slide,
    "极致降本与自适应能力：赋能系统在极端工况下的鲁棒性，追求能效比与药耗平衡的理论极限。",
    10.12,
    6.74,
    2.58,
    0.32,
    8.65,
    { bold: true }
  );

  warnIfSlideHasOverlaps(slide, pptx, {
    muteContainment: true,
    ignoreLines: true,
    ignoreDecorativeShapes: true,
  });
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function hardnessSlide() {
  const slide = pptx.addSlide();
  addBg(slide);
  addTitle(slide, "深度水处理硬度调节 AI 模型：全链路精准控制架构");

  const topY = 1.2;
  const topH = 3.95;
  const cols = [
    { x: 0.28, w: 3.0, title: "感知与数据治理层", en: "(Perception & Governance)" },
    { x: 3.46, w: 3.0, title: "基础算法层", en: "(Base Algorithms)" },
    { x: 6.64, w: 3.0, title: "控制与修偏层", en: "(Control & Correction)" },
    { x: 9.82, w: 3.0, title: "前沿探索层", en: "(Frontier Intelligence)" },
  ];
  cols.forEach((col, idx) => {
    addPanel(slide, {
      x: col.x,
      y: topY,
      w: col.w,
      h: topH,
      color: idx === 3 ? C.green : C.line,
      title: col.title,
      fill: idx === 3 ? "F8FDFC" : "FDFEFF",
    });
    addBody(slide, col.en, col.x + 0.12, topY + 0.48, col.w - 0.24, 0.16, 8.8, {
      align: "center",
      color: C.sub,
      bold: true,
    });
  });

  const leftLabels = [
    { text: "原水硬度\n(Hardness)", y: 1.95 },
    { text: "流量\n(Flow)", y: 2.55 },
    { text: "浊度\n(Turbidity)", y: 3.15 },
    { text: "碱度\n(Alkalinity)", y: 3.75 },
    { text: "出水硬度反馈\n(Feedback)", y: 4.35 },
  ];
  leftLabels.forEach((item, i) => {
    addMiniCard(slide, item.text, 0.46, item.y, 1.1, 0.42, C.blue);
    connect(slide, 1.56, item.y + 0.21, 1.98, 3.18, "9CC2D7", 1);
  });
  addImg(slide, ASSET("h_icon_align.png"), 1.92, 2.22, 1.1, 1.46);
  addBody(
    slide,
    "时滞对齐与\n异常剔除",
    1.88,
    3.76,
    1.18,
    0.42,
    11,
    { bold: true, align: "center" }
  );

  const netNodes = [
    [3.82, 2.32], [4.46, 1.72], [5.2, 1.72], [5.84, 2.32],
    [3.82, 3.08], [4.46, 2.72], [5.2, 2.72], [5.84, 3.08],
    [4.46, 3.82], [5.2, 3.82],
  ];
  for (let i = 0; i < netNodes.length; i++) {
    for (let j = i + 1; j < netNodes.length; j++) {
      if (Math.abs(netNodes[i][1] - netNodes[j][1]) < 0.9 || Math.abs(netNodes[i][0] - netNodes[j][0]) < 1.6) {
        connect(slide, netNodes[i][0], netNodes[i][1], netNodes[j][0], netNodes[j][1], "C9DDE8", 0.7);
      }
    }
  }
  netNodes.forEach(([x, y], idx) => addDot(slide, x, y, idx % 3 === 0 ? 0.095 : 0.075, idx % 2 ? "75C4E6" : "7FA8CE"));
  addMiniCard(slide, "XGBoost", 4.18, 1.92, 0.92, 0.42, C.teal);
  addMiniCard(slide, "CatBoost", 5.12, 1.92, 0.92, 0.42, C.teal);
  addMiniCard(slide, "Transformer", 4.02, 3.38, 1.08, 0.42, C.teal);
  addMiniCard(slide, "TCN", 5.14, 3.38, 0.78, 0.42, C.teal);
  addBody(slide, "状态估计\n(State Estimation)", 4.38, 2.48, 1.18, 0.5, 10.6, {
    align: "center",
    bold: true,
  });
  addBody(slide, "长期波动趋势\n(Long-Term Trend)", 4.26, 4.04, 1.42, 0.44, 10, {
    align: "center",
    bold: true,
  });

  addMiniCard(slide, "动态输出", 6.94, 2.02, 1.16, 0.42, C.teal);
  addMiniCard(slide, "前馈 + 反馈", 6.94, 2.76, 1.16, 0.42, C.teal);
  addMiniCard(slide, "MPC / BayesOpt", 6.94, 3.5, 1.16, 0.42, C.teal);
  addImg(slide, ASSET("h_icon_valve.png"), 8.18, 2.36, 0.68, 0.72);
  addBody(slide, "碳酸钠最优\n投加指令", 8.02, 3.0, 0.98, 0.42, 10.2, {
    bold: true,
    align: "center",
  });
  connect(slide, 8.14, 2.96, 7.86, 3.74, "A9C8D8", 1.2);
  addImg(slide, ASSET("h_icon_reactor.png"), 8.26, 3.56, 0.86, 1.22);

  slide.addShape(pptx.ShapeType.roundRect, {
    x: 10.12,
    y: 2.02,
    w: 2.4,
    h: 2.4,
    rectRadius: 0.06,
    line: { color: "2D6287", width: 1, transparency: 15 },
    fill: { color: "173B58" },
  });
  addImg(slide, ASSET("h_icon_brain.png"), 10.38, 2.22, 1.88, 1.18);
  addBody(
    slide,
    "可解释性模糊图神经网络\n(Explainable Fuzzy GNN)",
    10.26,
    3.54,
    2.12,
    0.4,
    9.8,
    { bold: true, align: "center", color: "F1F8FF" }
  );
  addBody(
    slide,
    "人类可读的语义规则\n(Human-Readable Rules)",
    10.26,
    4.02,
    2.12,
    0.36,
    9.6,
    { bold: true, align: "center", color: "F1F8FF" }
  );

  addBody(slide, "关键绩效目标", 5.6, 5.28, 2.1, 0.2, 13.5, {
    bold: true,
    align: "center",
  });
  connect(slide, 0.42, 5.46, 5.3, 5.46, "B9D4E2", 1);
  connect(slide, 7.98, 5.46, 12.9, 5.46, "B9D4E2", 1);

  addImg(slide, ASSET("h_gauge_icon.png"), 0.3, 5.6, 1.42, 1.42);
  addBody(slide, "硬度控制区间：270-280 mg/L", 1.86, 5.9, 5.0, 0.22, 18, {
    bold: true,
    color: "2A5D86",
  });
  addBody(slide, "出水硬度高度收敛，防止结垢", 1.9, 6.32, 3.7, 0.18, 10.6, {
    bold: true,
  });

  const tableX = 4.78;
  const tableY = 6.18;
  const colW = [1.1, 1.2, 1.4];
  const rowH = [0.2, 0.2, 0.2, 0.2];
  const headers = ["核心指标", "目标/范围", "关联算法"];
  const rows = [
    ["出水硬度目标", "270 - 280 mg/L", "MPC / BayesOpt"],
    ["药剂节能效率", "> 20% 降幅", "XGBoost / CatBoost"],
    ["波动预测窗口", "30 - 60 分钟", "TCN / Transformer"],
  ];
  let cx = tableX;
  headers.forEach((head, i) => {
    slide.addShape(pptx.ShapeType.rect, {
      x: cx,
      y: tableY,
      w: colW[i],
      h: rowH[0],
      line: { color: "BFD7E4", width: 1 },
      fill: { color: "EAF6FB" },
    });
    addBody(slide, head, cx + 0.02, tableY + 0.05, colW[i] - 0.04, 0.1, 8.8, {
      bold: true,
      align: "center",
      valign: "mid",
    });
    cx += colW[i];
  });
  rows.forEach((row, r) => {
    let x = tableX;
    row.forEach((cell, i) => {
      slide.addShape(pptx.ShapeType.rect, {
        x,
        y: tableY + rowH[0] + r * rowH[1],
        w: colW[i],
        h: rowH[1],
        line: { color: "BFD7E4", width: 1 },
        fill: { color: "FDFEFF" },
      });
      addBody(slide, cell, x + 0.02, tableY + rowH[0] + r * rowH[1] + 0.05, colW[i] - 0.04, 0.1, 8.55, {
        align: "center",
        valign: "mid",
      });
      x += colW[i];
    });
  });

  addImg(slide, ASSET("h_arrow_icon.png"), 8.74, 5.84, 0.58, 0.64);
  addBody(slide, "药剂消耗降低 > 20%", 9.42, 5.88, 2.66, 0.2, 16, {
    bold: true,
    color: "2A5D86",
  });
  addBody(slide, "通过精准加药模型显著减少消耗量", 9.44, 6.28, 2.88, 0.16, 10, {
    bold: true,
  });
  addImg(slide, ASSET("h_loop_icon.png"), 8.88, 6.54, 0.62, 0.5);
  addBody(slide, "全闭环自动化决策", 9.42, 6.58, 2.34, 0.18, 15, {
    bold: true,
  });
  addBody(slide, "毫秒级响应，消除滞后性", 9.44, 6.92, 2.32, 0.16, 10, {
    bold: true,
  });

  warnIfSlideElementsOutOfBounds(slide, pptx);
}

async function main() {
  membraneSlide();
  boilerSlide();
  hardnessSlide();
  const out = path.join(PROJECT_ROOT, "架构图拆分可编辑版_3页.pptx");
  await pptx.writeFile({ fileName: out });
  console.log(`WROTE ${out}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
