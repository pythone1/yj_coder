const fs = require("fs");
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
const ASSET = (...parts) =>
  path.join(PROJECT_ROOT, "work", "physics_ai_assets", ...parts);
const OUTPUT = path.join(PROJECT_ROOT, "Physics-Constrained_Industrial_AI_editable.pptx");
const OUTPUT_CN = path.join(PROJECT_ROOT, "Physics-Constrained_Industrial_AI_可编辑版.pptx");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "OpenAI";
pptx.subject = "Physics-Constrained Industrial AI 可编辑版";
pptx.title = "Physics-Constrained Industrial AI 可编辑版";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const COLORS = {
  bg: "F8F6F1",
  grid: "D9DFE8",
  navy: "0E2C4B",
  navySoft: "274D72",
  navyDeep: "0A2340",
  blue: "5EA7DA",
  blueFill: "EAF4FB",
  blueFill2: "D9EEF9",
  orange: "E7A11D",
  orangeFill: "FCE8B7",
  text: "18314E",
  muted: "465F77",
  border: "163655",
  white: "FFFFFF",
};

function addGridBackground(slide) {
  slide.background = { color: COLORS.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: H,
    line: { color: COLORS.bg, transparency: 100 },
    fill: { color: COLORS.bg },
  });

  const vStep = 0.28;
  for (let x = 0.02; x <= W - 0.02; x += vStep) {
    slide.addShape(pptx.ShapeType.line, {
      x,
      y: 0,
      w: 0,
      h: H,
      line: { color: COLORS.grid, transparency: 82, width: 0.5 },
    });
  }
  const hStep = 0.28;
  for (let y = 0.02; y <= H - 0.02; y += hStep) {
    slide.addShape(pptx.ShapeType.line, {
      x: 0,
      y,
      w: W,
      h: 0,
      line: { color: COLORS.grid, transparency: 86, width: 0.5 },
    });
  }

  slide.addShape(pptx.ShapeType.rect, {
    x: 0.22,
    y: 0.2,
    w: W - 0.44,
    h: H - 0.4,
    line: { color: COLORS.border, width: 1.1, transparency: 10 },
    fill: { color: COLORS.bg, transparency: 100 },
  });
}

function addTitle(slide, title) {
  slide.addText(title, {
    x: 0.56,
    y: 0.28,
    w: 12.1,
    h: 0.54,
    margin: 0,
    fontFace: "Microsoft YaHei",
    fontSize: 27,
    bold: true,
    color: COLORS.navy,
  });
}

function addCornerMarks(slide, x, y, w, h, color = COLORS.border) {
  const L = 0.14;
  const S = 0.14;
  const line = { color, width: 1, transparency: 18 };
  slide.addShape(pptx.ShapeType.line, { x, y, w: L, h: 0, line });
  slide.addShape(pptx.ShapeType.line, { x, y, w: 0, h: S, line });
  slide.addShape(pptx.ShapeType.line, { x: x + w - L, y, w: L, h: 0, line });
  slide.addShape(pptx.ShapeType.line, {
    x: x + w,
    y,
    w: 0,
    h: S,
    line,
  });
  slide.addShape(pptx.ShapeType.line, {
    x,
    y: y + h,
    w: L,
    h: 0,
    line,
  });
  slide.addShape(pptx.ShapeType.line, {
    x,
    y: y + h - S,
    w: 0,
    h: S,
    line,
  });
  slide.addShape(pptx.ShapeType.line, {
    x: x + w - L,
    y: y + h,
    w: L,
    h: 0,
    line,
  });
  slide.addShape(pptx.ShapeType.line, {
    x: x + w,
    y: y + h - S,
    w: 0,
    h: S,
    line,
  });
}

function addPanel(slide, opts) {
  const {
    x,
    y,
    w,
    h,
    fill = "FFFFFF",
    transparency = 6,
    lineColor = COLORS.border,
    lineWidth = 1.1,
    radius = 0.04,
    shadow = true,
  } = opts;
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: radius,
    line: { color: lineColor, width: lineWidth, transparency: 10 },
    fill: { color: fill, transparency },
    shadow: shadow
      ? safeOuterShadow("B4C4D4", 0.14, 45, 1.4, 0.5)
      : undefined,
  });
  addCornerMarks(slide, x + 0.08, y + 0.08, w - 0.16, h - 0.16, lineColor);
}

function addTopAccent(slide, x, y, w, color) {
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w,
    h: 0.12,
    line: { color, transparency: 100 },
    fill: { color },
  });
}

function addLeftAccent(slide, x, y, h, color) {
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w: 0.16,
    h,
    line: { color, transparency: 100 },
    fill: { color },
  });
}

function addText(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    margin: opts.margin ?? 0.04,
    fontFace: "Microsoft YaHei",
    fontSize: opts.fontSize ?? 15,
    bold: opts.bold ?? false,
    color: opts.color ?? COLORS.text,
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    breakLine: false,
    paraSpaceAfterPt: opts.paraSpaceAfterPt ?? 2,
    lineSpacingMultiple: opts.lineSpacingMultiple ?? 1.05,
  });
}

function addRichText(slide, runs, x, y, w, h, opts = {}) {
  slide.addText(runs, {
    x,
    y,
    w,
    h,
    margin: opts.margin ?? 0.04,
    fontFace: "Microsoft YaHei",
    fontSize: opts.fontSize ?? 15,
    color: opts.color ?? COLORS.text,
    valign: opts.valign ?? "mid",
    paraSpaceAfterPt: opts.paraSpaceAfterPt ?? 2,
    lineSpacingMultiple: opts.lineSpacingMultiple ?? 1.05,
    breakLine: false,
  });
}

function addImage(slide, imagePath, x, y, w, h) {
  slide.addImage({ path: imagePath, ...imageSizingContain(imagePath, x, y, w, h) });
}

function addConnectorDot(slide, x, y, color = COLORS.navy) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x: x - 0.035,
    y: y - 0.035,
    w: 0.07,
    h: 0.07,
    line: { color, transparency: 100 },
    fill: { color },
  });
}

function addRightArrow(slide, x, y, w, h) {
  slide.addShape(pptx.ShapeType.rightArrow, {
    x,
    y,
    w,
    h,
    line: { color: COLORS.navyDeep, transparency: 100 },
    fill: { color: COLORS.navyDeep },
  });
}

function slideOne() {
  const slide = pptx.addSlide();
  addGridBackground(slide);
  addTitle(slide, "行业痛点与核心蜕变： 从被动向主动的智能化跨越");

  addPanel(slide, {
    x: 0.56,
    y: 1.24,
    w: 3.48,
    h: 4.9,
    fill: "FFFDF7",
    transparency: 4,
    lineColor: "C79A37",
  });
  addTopAccent(slide, 0.67, 1.36, 3.26, COLORS.orange);
  addImage(slide, ASSET("s1_left.png"), 1.18, 2.64, 1.44, 1.44);
  addText(slide, "传统管理模式：\n人工巡检 + 被动运维", 0.95, 5.07, 2.7, 0.74, {
    fontSize: 17.2,
    bold: true,
    align: "center",
    valign: "mid",
    color: COLORS.navyDeep,
  });

  addText(slide, "全面引入人工智能垂类模型", 4.65, 1.85, 4.1, 0.34, {
    fontSize: 20,
    bold: true,
    align: "center",
    color: COLORS.navySoft,
  });
  addImage(slide, ASSET("s1_center.png"), 4.72, 2.34, 3.94, 2.62);
  addRightArrow(slide, 3.92, 3.6, 0.78, 0.36);
  addRightArrow(slide, 8.66, 3.6, 0.78, 0.36);
  addText(
    slide,
    "选择潭中有色生产工艺环节进行试点，\n与现有工艺深度结合。",
    4.54,
    5.14,
    4.32,
    0.58,
    {
      fontSize: 13.4,
      align: "center",
      color: COLORS.navyDeep,
    }
  );

  addPanel(slide, {
    x: 9.3,
    y: 1.24,
    w: 3.48,
    h: 4.9,
    fill: COLORS.blueFill,
    transparency: 4,
    lineColor: COLORS.blue,
  });
  addTopAccent(slide, 9.41, 1.36, 3.26, "2E92D6");
  addImage(slide, ASSET("s1_right.png"), 9.94, 2.55, 2.05, 2.05);
  addText(slide, "蜕变管理模式：\n数据驱动 + 主动预测", 9.68, 5.03, 2.72, 0.8, {
    fontSize: 17.2,
    bold: true,
    align: "center",
    valign: "mid",
    color: COLORS.navyDeep,
  });

  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 6.42,
    w: W,
    h: 1.08,
    line: { color: COLORS.navyDeep, transparency: 100 },
    fill: { color: COLORS.navyDeep },
  });
  addRichText(
    slide,
    [
      { text: "减少耗材、能源 ", options: { bold: true, color: COLORS.white } },
      { text: "20-35%", options: { bold: true, color: "2F9BE9", fontSize: 36 } },
      { text: " 成本", options: { bold: true, color: COLORS.white } },
    ],
    1.65,
    6.64,
    10.2,
    0.42,
    {
      fontSize: 31,
      valign: "mid",
      margin: 0,
    }
  );

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function slideTwo() {
  const slide = pptx.addSlide();
  addGridBackground(slide);
  addTitle(slide, "破局之道：项目核心优势与传统工业数据平台对比");

  addPanel(slide, {
    x: 0.7,
    y: 1.55,
    w: 5.28,
    h: 5.24,
    fill: "FFFEFB",
    transparency: 0,
    lineColor: COLORS.orange,
    shadow: false,
  });
  addPanel(slide, {
    x: 6.07,
    y: 1.55,
    w: 6.52,
    h: 5.24,
    fill: "FCFEFF",
    transparency: 0,
    lineColor: COLORS.navy,
    shadow: false,
  });

  slide.addShape(pptx.ShapeType.rect, {
    x: 0.7,
    y: 1.55,
    w: 5.28,
    h: 0.96,
    line: { color: COLORS.orange, transparency: 100 },
    fill: { color: COLORS.orange },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 6.07,
    y: 1.55,
    w: 6.52,
    h: 0.96,
    line: { color: COLORS.blue, transparency: 100 },
    fill: { color: "5D9ED2" },
  });

  addText(slide, "市场上工业数据平台痛点", 1.2, 1.86, 4.3, 0.28, {
    fontSize: 22,
    bold: true,
    align: "center",
    color: COLORS.white,
  });
  addText(slide, "我们的轻量模型核心优势", 6.75, 1.86, 5.1, 0.28, {
    fontSize: 22,
    bold: true,
    align: "center",
    color: COLORS.white,
  });

  const leftRows = [
    "建设成本极高，难以产生实际经济效益。",
    "部署周期漫长，实施阻力大。",
    "长期维护投入大，技术门槛高。",
  ];
  const leftYs = [2.63, 4.0, 5.37];
  for (let i = 0; i < leftRows.length; i++) {
    addPanel(slide, {
      x: 0.7,
      y: leftYs[i],
      w: 5.28,
      h: 1.13,
      fill: "FFFEFB",
      transparency: 0,
      lineColor: "C98F22",
      shadow: false,
    });
    addText(slide, leftRows[i], 1.12, leftYs[i] + 0.34, 4.5, 0.46, {
      fontSize: 17.2,
      bold: true,
      color: "B4720E",
      valign: "mid",
    });
  }

  addPanel(slide, {
    x: 6.07,
    y: 2.63,
    w: 6.52,
    h: 1.13,
    fill: "FFFFFF",
    transparency: 0,
    lineColor: COLORS.navy,
    shadow: false,
  });
  addRichText(
    slide,
    [
      { text: "聚焦实际工艺：", options: { bold: true, color: COLORS.navyDeep } },
      {
        text: "简易部署，维护极简，直接挂钩经济效益。",
        options: { color: COLORS.text },
      },
    ],
    6.42,
    2.95,
    5.88,
    0.48,
    {
      fontSize: 16.2,
      margin: 0,
    }
  );

  addPanel(slide, {
    x: 6.07,
    y: 4.0,
    w: 6.52,
    h: 1.28,
    fill: "F7FBFF",
    transparency: 0,
    lineColor: COLORS.navy,
    lineWidth: 1.8,
    shadow: false,
  });
  addRichText(
    slide,
    [
      { text: "强制物理方程约束：", options: { bold: true, color: COLORS.navyDeep } },
      {
        text:
          "模型不仅学习历史数据中的统计规律，更强制嵌入工艺流程的\n化学、物理方程作为硬性约束条件。",
        options: { color: COLORS.text },
      },
    ],
    6.42,
    4.22,
    4.85,
    0.72,
    {
      fontSize: 15.2,
      margin: 0,
    }
  );
  addImage(slide, ASSET("s2_formula.png"), 11.5, 4.2, 0.64, 0.52);

  addPanel(slide, {
    x: 6.07,
    y: 5.37,
    w: 6.52,
    h: 1.13,
    fill: "FFFFFF",
    transparency: 0,
    lineColor: COLORS.navy,
    shadow: false,
  });
  addRichText(
    slide,
    [
      { text: "极端工况保障：", options: { bold: true, color: COLORS.navyDeep } },
      {
        text: "即使在极端工况下，输出也必然符合物理客观规律，确保底层控制指令的绝对安全性和可行性。",
        options: { color: COLORS.text },
      },
    ],
    6.42,
    5.66,
    5.88,
    0.5,
    {
      fontSize: 15.2,
      margin: 0,
    }
  );

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function addPanelHeader(slide, x, y, w, text) {
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w,
    h: 0.48,
    line: { color: COLORS.border, width: 1, transparency: 10 },
    fill: { color: COLORS.bg, transparency: 0 },
  });
  addCornerMarks(slide, x + 0.08, y + 0.08, w - 0.16, 0.32, COLORS.navySoft);
  addText(slide, text, x + 0.08, y + 0.1, w - 0.16, 0.22, {
    fontSize: 18.5,
    bold: true,
    align: "center",
    color: COLORS.navyDeep,
  });
}

function addParallelLines(slide, x1, y1, x2, y2, count = 5) {
  for (let i = 0; i < count; i++) {
    const dx = i * 0.1;
    const line = { color: "6B9BC0", width: 1.2, transparency: 18 };
    slide.addShape(pptx.ShapeType.line, {
      x: x1 + dx,
      y: y1,
      w: 0,
      h: y2 - y1,
      line,
    });
    slide.addShape(pptx.ShapeType.line, {
      x: x1 + dx,
      y: y2,
      w: x2 - (x1 + dx),
      h: 0,
      line,
    });
  }
}

function slideThree() {
  const slide = pptx.addSlide();
  addGridBackground(slide);
  addTitle(slide, "垂类应用与模型机理：构建基于物理约束的轻量大脑");

  const panels = [
    {
      x: 0.68,
      title: "轻量级模型",
      image: ASSET("s3_left_icon_clean.png"),
      text:
        "采用时序预测（Transformer、LSTM）、\n随机森林（XGBoost）、强化学习等\n轻量级模型，架构瘦简，部署极简。",
    },
    {
      x: 4.98,
      title: "嵌入物理机制",
      image: ASSET("s3_mid_icon_clean.png"),
      text:
        "将工艺流程原理与专家知识\n作为硬约束或正则化项加入模型中，\n确立模型运行的绝对底层逻辑与边界。",
    },
    {
      x: 9.28,
      title: "细分与下沉",
      image: ASSET("s3_right_icon_clean.png"),
      text:
        "不依赖公开泛化数据，仅使用\n工业现场的高频时序与工艺配方数据。\n精准切入能耗占比高、优化空间大的\n单体关键工序。",
    },
  ];

  for (const panel of panels) {
    addPanel(slide, {
      x: panel.x,
      y: 1.55,
      w: 3.46,
      h: 3.58,
      fill: "FFFEFC",
      transparency: 0,
      lineColor: COLORS.border,
      shadow: false,
    });
    addPanelHeader(slide, panel.x, 1.55, 3.46, panel.title);
    addImage(slide, panel.image, panel.x + 1.2, 2.05, 1.08, 0.86);
    addText(slide, panel.text, panel.x + 0.28, 3.28, 2.9, 1.15, {
      fontSize: 13.8,
      color: COLORS.navyDeep,
      bold: false,
    });
  }

  addParallelLines(slide, 2.16, 5.08, 5.2, 6.02, 5);
  for (let i = 0; i < 5; i++) {
    slide.addShape(pptx.ShapeType.line, {
      x: 6.48 + i * 0.1,
      y: 5.08,
      w: 0,
      h: 0.94,
      line: { color: "6B9BC0", width: 1.2, transparency: 18 },
    });
  }
  for (let i = 0; i < 5; i++) {
    const x = 10.68 - i * 0.1;
    slide.addShape(pptx.ShapeType.line, {
      x,
      y: 5.08,
      w: 0,
      h: 0.62,
      line: { color: "6B9BC0", width: 1.2, transparency: 18 },
    });
    slide.addShape(pptx.ShapeType.line, {
      x,
      y: 5.7,
      w: -(x - 8.14),
      h: 0,
      line: { color: "6B9BC0", width: 1.2, transparency: 18 },
    });
  }

  slide.addShape(pptx.ShapeType.roundRect, {
    x: 3.22,
    y: 6.04,
    w: 6.86,
    h: 0.58,
    rectRadius: 0.03,
    line: { color: COLORS.navyDeep, width: 1, transparency: 10 },
    fill: { color: COLORS.navyDeep },
  });
  addCornerMarks(slide, 3.32, 6.12, 6.66, 0.42, "A8C4E0");
  addText(slide, "聚焦应用于单个工艺本身，保障高优化率与本质安全。", 3.56, 6.19, 6.2, 0.22, {
    fontSize: 18,
    bold: true,
    align: "center",
    color: COLORS.white,
  });

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function addLConnector(slide, x1, y1, x2, y2) {
  const line = { color: COLORS.navySoft, width: 1.3, transparency: 14 };
  slide.addShape(pptx.ShapeType.line, {
    x: x1,
    y: y1,
    w: x2 - x1,
    h: 0,
    line,
  });
  slide.addShape(pptx.ShapeType.line, {
    x: x2,
    y: y1,
    w: 0,
    h: y2 - y1,
    line,
  });
  slide.addShape(pptx.ShapeType.ellipse, {
    x: x2 - 0.05,
    y: y2 - 0.05,
    w: 0.1,
    h: 0.1,
    line: { color: COLORS.blue, transparency: 100 },
    fill: { color: COLORS.blue },
  });
}

function addInfoCard(slide, x, y, w, h, title, body) {
  addPanel(slide, {
    x,
    y,
    w,
    h,
    fill: "F7FBFE",
    transparency: 0,
    lineColor: COLORS.border,
    shadow: false,
  });
  addLeftAccent(slide, x + 0.1, y + 0.1, h - 0.2, COLORS.blue);
  addText(slide, title, x + 0.34, y + 0.36, w - 0.56, 0.28, {
    fontSize: 19,
    bold: true,
    color: COLORS.navyDeep,
  });
  addText(slide, body, x + 0.34, y + 0.84, w - 0.56, h - 1.02, {
    fontSize: 13.6,
    color: COLORS.text,
  });
}

function slideFour() {
  const slide = pptx.addSlide();
  addGridBackground(slide);
  addTitle(slide, "极致下沉：低成本与边缘化极简部署方案");

  addInfoCard(
    slide,
    0.46,
    3.02,
    3.82,
    2.1,
    "极简硬件需求",
    "仅需采用低功耗芯片即可满足轻量级\n模型推理。可在低算力边缘设备上流畅\n运行，彻底告别昂贵的 GPU 依赖。"
  );

  addImage(slide, ASSET("s4_center_chip.png"), 4.55, 2.35, 4.08, 3.18);

  addInfoCard(
    slide,
    8.94,
    1.45,
    3.9,
    2.02,
    "高 Token 效率",
    "利用先进的迁移学习技术，模型摆脱对\n海量长周期历史数据的依赖。实现一至两周\n浅层周期试运行，大幅度压缩试错与\n时间成本。"
  );

  addInfoCard(
    slide,
    8.94,
    4.42,
    3.9,
    2.26,
    "快速适配与自学习",
    "仅需小样本数据即可掌握通用物理规律\n与特定设备特性。部署后通过实时采集\n数据开启持续自学习优化闭环，实现\n低成本的快速全厂复制。"
  );

  addLConnector(slide, 4.28, 4.0, 4.52, 4.0);
  addLConnector(slide, 8.25, 2.76, 8.92, 2.76);
  addLConnector(slide, 8.25, 5.25, 8.92, 5.25);

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function addCalloutBox(slide, x, y, w, h, text) {
  addPanel(slide, {
    x,
    y,
    w,
    h,
    fill: "FFFFFF",
    transparency: 0,
    lineColor: COLORS.border,
    shadow: false,
  });
  addText(slide, text, x + 0.12, y + 0.16, w - 0.24, h - 0.26, {
    fontSize: 13.4,
    color: COLORS.text,
    bold: false,
    valign: "mid",
  });
}

function slideFive() {
  const slide = pptx.addSlide();
  addGridBackground(slide);
  addTitle(slide, "全链路智能化： 数据·AI·应用 三层系统架构闭环");

  slide.addShape(pptx.ShapeType.circularArrow, {
    x: 3.12,
    y: 1.52,
    w: 6.98,
    h: 5.26,
    line: { color: COLORS.blue, transparency: 100 },
    fill: { color: "4F9FD5", transparency: 0 },
  });
  addText(
    slide,
    "围绕核心逻辑演进：数据驱动决策 ↔ 模型优化控制 ↔ 成果落地闭环",
    3.64,
    1.18,
    5.96,
    0.28,
    {
      fontSize: 14.2,
      bold: true,
      align: "center",
      color: COLORS.navySoft,
    }
  );

  addImage(slide, ASSET("s5_stack_no_arc.png"), 3.86, 1.92, 5.48, 4.72);

  addCalloutBox(
    slide,
    0.22,
    2.08,
    3.0,
    1.18,
    "基于AI输出结果，执行自动控制与精准操作决策，\n最终实现降本增效与节能减耗的落地闭环。"
  );
  addCalloutBox(
    slide,
    0.22,
    5.04,
    3.0,
    1.18,
    "全面采集与工艺流程关联的多源异构数据，\n并进行深度清洗与预处理，夯实决策基石。"
  );
  addCalloutBox(
    slide,
    10.14,
    3.44,
    2.96,
    1.42,
    "人工智能垂类模型对海量输入数据进行实时吞吐与分析，\n精准给出最优工艺参数与控制指令。"
  );

  slide.addShape(pptx.ShapeType.line, {
    x: 3.22,
    y: 2.76,
    w: 0.66,
    h: 0,
    line: { color: COLORS.navySoft, width: 1.25, transparency: 10 },
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 3.22,
    y: 5.72,
    w: 1.12,
    h: 0,
    line: { color: COLORS.navySoft, width: 1.25, transparency: 10 },
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 9.34,
    y: 4.08,
    w: 0.8,
    h: 0,
    line: { color: COLORS.navySoft, width: 1.25, transparency: 10 },
  });
  addConnectorDot(slide, 3.22, 2.76);
  addConnectorDot(slide, 3.22, 5.72);
  addConnectorDot(slide, 9.34, 4.08);

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

async function main() {
  slideOne();
  slideTwo();
  slideThree();
  slideFour();
  slideFive();
  await pptx.writeFile({ fileName: OUTPUT });
  fs.copyFileSync(OUTPUT, OUTPUT_CN);
  console.log(`Wrote ${OUTPUT}`);
  console.log(`Copied ${OUTPUT_CN}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
