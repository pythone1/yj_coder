const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers/layout");
const { safeOuterShadow } = require("./pptxgenjs_helpers/util");
const { imageSizingCrop, imageSizingContain } = require("./pptxgenjs_helpers/image");

const ROOT = __dirname;
const PROJECT_ROOT = path.resolve(ROOT, "..", "..");
const IMG = (...parts) => path.join(PROJECT_ROOT, "0415", ...parts);
const OUTPUT_ASCII = path.join(PROJECT_ROOT, "0415", "Dehua_Project_Showcase.pptx");
const OUTPUT_CN = path.join(PROJECT_ROOT, "0415", "苏州德华机械设备有限公司_项目展示.pptx");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "苏州德华机械设备有限公司";
pptx.subject = "项目展示";
pptx.title = "苏州德华机械设备有限公司 项目展示";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const C = {
  bg: "F5F7FA",
  white: "FFFFFF",
  navy: "12304D",
  navy2: "244D72",
  text: "29465D",
  soft: "6E879C",
  line: "D8E1E8",
  gold: "D6932E",
  panel: "FFFFFF",
};

function addBase(slide, bg = C.bg) {
  slide.background = { color: bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: H,
    line: { color: bg, transparency: 100 },
    fill: { color: bg },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.24,
    y: 0.22,
    w: W - 0.48,
    h: H - 0.44,
    line: { color: C.line, width: 1.1 },
    fill: { color: bg, transparency: 100 },
  });
}

function addPanel(slide, x, y, w, h, fill = C.panel) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.04,
    line: { color: C.line, width: 1 },
    fill: { color: fill },
    shadow: safeOuterShadow("B8C7D3", 0.12, 45, 1.4, 0.4),
  });
}

function addText(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    margin: opts.margin ?? 0.02,
    fontFace: "Microsoft YaHei",
    fontSize: opts.fontSize ?? 16,
    bold: opts.bold ?? false,
    color: opts.color ?? C.text,
    align: opts.align ?? "left",
    valign: opts.valign ?? "top",
    breakLine: false,
    paraSpaceAfterPt: opts.paraSpaceAfterPt ?? 2,
    lineSpacingMultiple: opts.lineSpacingMultiple ?? 1.02,
  });
}

function addBulletList(slide, items, x, y, w, h, fontSize = 14.5) {
  slide.addText(
    items.map((item) => ({
      text: item,
      options: { bullet: { indent: fontSize * 0.9 } },
    })),
    {
      x,
      y,
      w,
      h,
      margin: 0,
      fontFace: "Microsoft YaHei",
      fontSize,
      color: C.text,
      breakLine: false,
      paraSpaceAfterPt: 8,
      valign: "top",
    }
  );
}

function addHeader(slide, title, subtitle = "") {
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.46,
    y: 0.42,
    w: 0.08,
    h: 0.56,
    line: { color: C.gold, transparency: 100 },
    fill: { color: C.gold },
  });
  addText(slide, title, 0.68, 0.35, 8.8, 0.36, {
    fontSize: 24,
    bold: true,
    color: C.navy,
    margin: 0,
  });
  if (subtitle) {
    addText(slide, subtitle, 0.68, 0.76, 9.8, 0.18, {
      fontSize: 11.5,
      color: C.soft,
      margin: 0,
    });
  }
  slide.addShape(pptx.ShapeType.line, {
    x: 0.68,
    y: 1.12,
    w: 11.98,
    h: 0,
    line: { color: C.line, width: 1 },
  });
}

function addLabel(slide, text, x, y, w) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.34,
    rectRadius: 0.03,
    line: { color: C.navy2, transparency: 100 },
    fill: { color: C.navy2 },
  });
  addText(slide, text, x, y + 0.08, w, 0.12, {
    fontSize: 10.5,
    color: C.white,
    bold: true,
    align: "center",
    margin: 0,
  });
}

function addContactBar(slide, x, y, w) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.42,
    rectRadius: 0.03,
    line: { color: "E7EEF3", width: 1 },
    fill: { color: "F9FBFC" },
  });
  addText(slide, "联系方式：徐建娣  18962120213", x + 0.18, y + 0.11, w - 0.36, 0.14, {
    fontSize: 13.2,
    bold: true,
    color: C.navy,
    margin: 0,
  });
}

function coverSlide() {
  const slide = pptx.addSlide();
  const hero = IMG("苏州天佑项目1.jpg");
  slide.background = { color: "0F2941" };
  slide.addImage({ path: hero, ...imageSizingCrop(hero, 0, 0, W, H) });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: W,
    h: H,
    line: { color: "0F2941", transparency: 100 },
    fill: { color: "0F2941", transparency: 38 },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 5.9,
    h: H,
    line: { color: "0C2236", transparency: 100 },
    fill: { color: "0C2236", transparency: 18 },
  });

  addText(slide, "苏州德华机械设备有限公司", 0.72, 1.16, 4.9, 0.42, {
    fontSize: 28,
    bold: true,
    color: C.white,
    margin: 0,
  });
  addText(slide, "项目展示", 0.72, 1.8, 2.8, 0.46, {
    fontSize: 31,
    bold: true,
    color: "F6C76F",
    margin: 0,
  });
  addText(slide, "工业吸尘与除尘系统解决方案", 0.74, 2.5, 4.2, 0.2, {
    fontSize: 14,
    color: "E8F0F5",
    margin: 0,
  });

  addPanel(slide, 0.72, 3.18, 4.52, 2.34);
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.72,
    y: 3.18,
    w: 0.12,
    h: 2.34,
    line: { color: C.gold, transparency: 100 },
    fill: { color: C.gold },
  });
  addText(
    slide,
    "本公司专业研究、开发、设计和制造工业吸尘器，持续为中外客户提供与进口设备配套的工业吸尘解决方案，拥有扎实的空气动力学理论基础和丰富工程经验。",
    1.02,
    3.48,
    3.88,
    1.16,
    { fontSize: 16, color: C.navy }
  );
  addText(slide, "您的满意是我们最大的追求", 1.02, 4.82, 3.1, 0.18, {
    fontSize: 14.8,
    bold: true,
    color: C.navy2,
  });
  addText(slide, "联系方式：徐建娣  18962120213", 1.02, 5.12, 3.32, 0.18, {
    fontSize: 13.2,
    bold: true,
    color: C.navy,
  });

  // Intentional overlays: background image plus dark masks.
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function introSlide() {
  const slide = pptx.addSlide();
  addBase(slide);
  addHeader(slide, "公司简介", "Company Profile");

  addPanel(slide, 0.62, 1.42, 6.1, 5.46);
  addText(slide, "企业定位", 0.94, 1.74, 1.6, 0.2, {
    fontSize: 18,
    bold: true,
    color: C.navy,
  });
  addText(
    slide,
    "苏州德华机械设备有限公司是以工业吸尘器研发、设计、制造为核心的综合型机械企业，长期服务于工业制造现场的吸尘、除尘与配套系统建设。",
    0.94,
    2.08,
    5.4,
    0.84,
    { fontSize: 16 }
  );
  addText(slide, "技术与产品优势", 0.94, 3.06, 2.4, 0.2, {
    fontSize: 18,
    bold: true,
    color: C.navy,
  });
  addBulletList(
    slide,
    [
      "具备较强科研开发能力，在空气动力学领域拥有扎实理论与实践基础",
      "DH 系列产品采用知名品牌电机、电器及德国技术低噪音高压风机",
      "推出分体式旋风分离工业吸尘器，并拥有多项技术专利",
      "产品兼具结构紧凑、动力可靠、稳定性高和寿命长等特点",
    ],
    0.98,
    3.42,
    5.26,
    2.82,
    14.2
  );

  addPanel(slide, 7.02, 1.42, 5.68, 2.34);
  addText(slide, "产品主要特点", 7.34, 1.74, 2.0, 0.2, {
    fontSize: 18,
    bold: true,
    color: C.navy,
  });
  addBulletList(
    slide,
    [
      "过滤系统由旋风分离器、液固完全分离装置、主尘隔等组成",
      "操作简单，安全可靠，稳定性高，适用于多类工业场景",
    ],
    7.36,
    2.12,
    4.92,
    1.06,
    14.2
  );

  addPanel(slide, 7.02, 4.04, 5.68, 2.84);
  addText(slide, "发展理念与联系", 7.34, 4.36, 2.4, 0.2, {
    fontSize: 18,
    bold: true,
    color: C.navy,
  });
  addText(
    slide,
    "公司持续开发新产品，力求让设备能力始终跟上市场需求，推动“中国造”机械设备走向更广阔的国际市场。",
    7.34,
    4.72,
    4.98,
    0.84,
    { fontSize: 16 }
  );
  slide.addShape(pptx.ShapeType.line, {
    x: 7.34,
    y: 5.84,
    w: 4.78,
    h: 0,
    line: { color: C.line, width: 1.1 },
  });
  addText(slide, "联系人：徐建娣", 7.34, 6.02, 1.9, 0.18, {
    fontSize: 15.2,
    bold: true,
    color: C.navy2,
  });
  addText(slide, "联系电话：18962120213", 7.34, 6.34, 2.6, 0.18, {
    fontSize: 15.2,
    bold: true,
    color: C.navy,
  });

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function suzhouSlide() {
  const slide = pptx.addSlide();
  addBase(slide);
  addHeader(slide, "项目一：苏州天佑项目", "室内主机系统与屋顶除尘单元");

  addPanel(slide, 0.6, 1.42, 7.42, 5.5);
  const indoor = IMG("苏州天佑项目1.jpg");
  slide.addImage({ path: indoor, ...imageSizingContain(indoor, 0.88, 1.74, 6.86, 4.2) });
  addLabel(slide, "室内主机设备", 0.88, 6.12, 1.52);

  addPanel(slide, 8.28, 1.42, 4.46, 2.92);
  const roof = IMG("苏州天佑项目2.jpg");
  slide.addImage({ path: roof, ...imageSizingCrop(roof, 8.54, 1.72, 3.94, 2.14) });
  addLabel(slide, "屋顶除尘单元", 8.54, 3.94, 1.52);

  addPanel(slide, 8.28, 4.6, 4.46, 2.32);
  addText(slide, "项目展示要点", 8.6, 4.92, 1.8, 0.2, {
    fontSize: 18,
    bold: true,
    color: C.navy,
  });
  addBulletList(
    slide,
    [
      "系统包含现场主机设备与室外除尘装置",
      "设备布置完整，控制柜与管路连接清晰",
      "适合用于工业现场集中吸尘与除尘展示",
    ],
    8.62,
    5.3,
    3.66,
    1.1,
    14
  );

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function shanghaiSlide() {
  const slide = pptx.addSlide();
  addBase(slide);
  addHeader(slide, "项目二：上海小西生物项目", "现场设备实景展示");

  addPanel(slide, 0.62, 1.5, 8.0, 5.28);
  const img = IMG("上海小西生物1.jpg");
  slide.addImage({ path: img, ...imageSizingContain(img, 0.92, 1.82, 7.4, 4.02) });
  addLabel(slide, "现场设备实景", 0.94, 6.08, 1.48);

  addPanel(slide, 8.92, 1.5, 3.82, 5.28);
  addText(slide, "项目简介", 9.22, 1.86, 1.6, 0.2, {
    fontSize: 18,
    bold: true,
    color: C.navy,
  });
  addText(
    slide,
    "该项目展示了德华工业吸尘设备在生物医药类场景中的现场落地形式，设备纵向布置整齐，利于集中管理和连续运行。",
    9.22,
    2.22,
    3.02,
    1.02,
    { fontSize: 15.5 }
  );
  slide.addShape(pptx.ShapeType.line, {
    x: 9.22,
    y: 3.48,
    w: 2.98,
    h: 0,
    line: { color: C.line, width: 1 },
  });
  addText(slide, "展示关键词", 9.22, 3.7, 1.6, 0.18, {
    fontSize: 16,
    bold: true,
    color: C.navy2,
  });
  addBulletList(
    slide,
    ["设备阵列布局", "现场安装整洁", "适合标准化项目展示"],
    9.24,
    4.02,
    2.84,
    1.18,
    14
  );
  addText(slide, "德华设备在不同工业场景下均可实现稳定可靠运行。", 9.22, 5.86, 3.02, 0.5, {
    fontSize: 15,
    bold: true,
    color: C.navy,
  });

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function infineonSlide() {
  const slide = pptx.addSlide();
  addBase(slide);
  addHeader(slide, "项目三：英飞凌科技（无锡）项目", "双场景设备展示");

  addPanel(slide, 0.6, 1.5, 5.98, 5.32);
  const img1 = IMG("英飞凌科技（无锡）项目1.jpg");
  slide.addImage({ path: img1, ...imageSizingContain(img1, 0.92, 1.82, 5.34, 3.9) });
  addLabel(slide, "系统设备展示", 0.92, 6.0, 1.56);

  addPanel(slide, 6.84, 1.5, 5.9, 5.32);
  const img2 = IMG("英飞凌科技（无锡）项目2.jpg");
  slide.addImage({ path: img2, ...imageSizingContain(img2, 7.14, 1.82, 5.3, 3.9) });
  addLabel(slide, "工艺设备展示", 7.14, 6.0, 1.56);

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

async function main() {
  coverSlide();
  introSlide();
  suzhouSlide();
  shanghaiSlide();
  infineonSlide();
  await pptx.writeFile({ fileName: OUTPUT_ASCII });
  fs.copyFileSync(OUTPUT_ASCII, OUTPUT_CN);
  console.log(`Wrote ${OUTPUT_ASCII}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
