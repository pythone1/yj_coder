const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");

const ROOT = "E:/PY/research";
const IMG_DIR = path.join(ROOT, "tmp", "jinshiyuan_input_media2");
const OUT_DIR = path.join(ROOT, "output", "ppt");
const OUTPUT_ASCII = path.join(
  OUT_DIR,
  "Jinshiyuan_AI_Production_Blueprint_editable_clean.pptx"
);
const OUTPUT_CN = path.join(
  OUT_DIR,
  "今世缘酒业生产模块AI工艺分析与实施路径_可编辑版.pptx"
);

fs.mkdirSync(OUT_DIR, { recursive: true });

const pptx = new PptxGenJS();
pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "江苏南大五维电子科技有限公司";
pptx.subject = "今世缘酒业生产模块AI工艺分析与实施路径";
pptx.title = "今世缘酒业生产模块AI工艺分析与实施路径";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const W = 13.333;
const H = 7.5;
const C = {
  white: "F5FBFF",
  text: "F2FBFF",
  muted: "B9DCEC",
  cyan: "2FEAFF",
  cyanSoft: "75F3FF",
  cyanDark: "0B6789",
  gold: "F0B75B",
  green: "48F0B0",
  dark: "071B2B",
  dark2: "061827",
  panel: "09283A",
  line: "2E9DCA",
  blue: "0E7FD0",
};

function img(n) {
  return path.join(IMG_DIR, `image${n}.png`);
}

function addBg(slide, n) {
  slide.addImage({ path: img(n), x: 0, y: 0, w: W, h: H });
}

function addText(slide, text, x, y, w, h, opt = {}) {
  slide.addText(text, {
    x,
    y,
    w,
    h,
    margin: opt.margin ?? 0.03,
    fontFace: "Microsoft YaHei",
    fontSize: opt.size ?? 10,
    color: opt.color ?? C.text,
    bold: opt.bold ?? false,
    align: opt.align ?? "left",
    valign: opt.valign ?? "top",
    fit: "shrink",
    breakLine: false,
    paraSpaceAfterPt: opt.after ?? 0,
    lineSpacingMultiple: opt.lineSpacingMultiple ?? 1.0,
    transparency: opt.transparency ?? 0,
  });
}

function addPanel(slide, x, y, w, h, opt = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: opt.radius ?? 0.06,
    fill: {
      color: opt.fill ?? C.dark,
      transparency: opt.transparency ?? 8,
    },
    line: {
      color: opt.line ?? C.line,
      transparency: opt.lineTransparency ?? 0,
      width: opt.lineWidth ?? 1,
    },
  });
  if (opt.glow !== false) {
    slide.addShape(pptx.ShapeType.line, {
      x: x + 0.14,
      y: y + 0.14,
      w: w - 0.28,
      h: 0,
      line: {
        color: opt.glowColor ?? C.cyan,
        transparency: 12,
        width: 0.7,
      },
    });
  }
}

function addRect(slide, x, y, w, h, fill, transparency = 0) {
  slide.addShape(pptx.ShapeType.rect, {
    x,
    y,
    w,
    h,
    fill: { color: fill, transparency },
    line: { color: fill, transparency: 100 },
  });
}

function addPill(slide, text, x, y, w, opt = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: opt.h ?? 0.28,
    rectRadius: 0.08,
    fill: { color: opt.fill ?? C.cyan, transparency: opt.transparency ?? 0 },
    line: { color: opt.line ?? (opt.fill ?? C.cyan), width: 0.6 },
  });
  addText(slide, text, x + 0.04, y + 0.045, w - 0.08, (opt.h ?? 0.28) - 0.08, {
    size: opt.size ?? 8.2,
    bold: true,
    color: opt.color ?? "061A2A",
    align: "center",
    valign: "mid",
    margin: 0,
  });
}

function addBulletLines(slide, items, x, y, w, lineH, opt = {}) {
  items.forEach((item, idx) => {
    slide.addShape(pptx.ShapeType.ellipse, {
      x,
      y: y + 0.08 + idx * lineH,
      w: 0.05,
      h: 0.05,
      fill: { color: opt.dot ?? C.cyan },
      line: { color: opt.dot ?? C.cyan, width: 0.2 },
    });
    addText(slide, item, x + 0.11, y + idx * lineH, w - 0.11, lineH, {
      size: opt.size ?? 8.2,
      color: opt.color ?? C.text,
      bold: opt.bold ?? false,
      margin: 0,
    });
  });
}

function addTitleChip(slide, text, x, y, w, color = C.gold) {
  addPanel(slide, x, y, w, 0.34, {
    fill: "082335",
    transparency: 0,
    line: color,
    glowColor: color,
    lineWidth: 0.8,
  });
  addText(slide, text, x + 0.05, y + 0.06, w - 0.1, 0.18, {
    size: 8.9,
    bold: true,
    color,
    align: "center",
    margin: 0,
  });
}

function addSlide1() {
  const s = pptx.addSlide();
  addBg(s, 1);
  addPanel(s, 0.72, 2.76, 5.6, 1.95, {
    fill: "071927",
    transparency: 6,
    line: "347FA8",
  });
  addText(
    s,
    "今世缘酒业生产模块AI工艺\n分析与实施路径",
    1.02,
    3.04,
    4.95,
    0.92,
    { size: 20.5, bold: true }
  );
  addText(
    s,
    "详细版 | 聚焦“怎么完成场景、用什么数据、用什么算法、实现什么功能效益”",
    1.04,
    4.0,
    4.95,
    0.2,
    { size: 9.4, color: C.muted }
  );
  addText(
    s,
    "2026-04-24\n江苏南大五维电子科技有限公司",
    1.02,
    4.9,
    3.6,
    0.4,
    { size: 7.8, color: C.muted }
  );
}

function addOverviewCard(slide, x, title, lines) {
  addPanel(slide, x, 2.62, 2.02, 2.84, {
    fill: "061D2E",
    transparency: 2,
    line: C.line,
  });
  addRect(slide, x + 0.16, 2.84, 1.7, 0.34, "061D2E", 5);
  addText(slide, title, x + 0.16, 2.89, 1.7, 0.18, {
    size: 9.8,
    bold: true,
    align: "center",
    margin: 0,
  });
  addText(slide, "核心工艺对象：", x + 0.16, 3.32, 1.68, 0.14, {
    size: 7.1,
    bold: true,
    color: C.cyanSoft,
    margin: 0,
  });
  addText(slide, lines[0], x + 0.16, 3.5, 1.68, 0.52, {
    size: 6.9,
    color: C.gold,
    margin: 0,
  });
  addText(slide, "主要算法任务：", x + 0.16, 4.12, 1.68, 0.14, {
    size: 7.1,
    bold: true,
    color: C.cyanSoft,
    margin: 0,
  });
  addText(slide, lines[1], x + 0.16, 4.3, 1.68, 0.42, {
    size: 6.9,
    color: C.gold,
    margin: 0,
  });
  addText(slide, "最终功能效益：", x + 0.16, 4.82, 1.68, 0.14, {
    size: 7.1,
    bold: true,
    color: C.cyanSoft,
    margin: 0,
  });
  addText(slide, lines[2], x + 0.16, 5.0, 1.68, 0.36, {
    size: 6.9,
    color: C.gold,
    margin: 0,
  });
}

function addSlide2() {
  const s = pptx.addSlide();
  addBg(s, 2);
  addPanel(s, 1.96, 0.58, 8.28, 0.82, {
    fill: "061827",
    transparency: 0,
    line: C.cyan,
  });
  addText(s, "生产模块总体逻辑", 4.7, 0.72, 2.8, 0.18, {
    size: 15.5,
    bold: true,
    align: "center",
  });
  addText(
    s,
    "生产AI不能只做单点模型。它需要从生产工艺链路出发，把“数据采集、工艺建模、算法预测、业务执行、效果反馈”串起来。对今世缘而言，最稳妥的推进方式是先做可解释、可复核的辅助决策，再逐步走向半自动优化。",
    2.35,
    0.98,
    7.46,
    0.28,
    { size: 7.9, align: "center", color: C.text }
  );

  addOverviewCard(s, 0.6, "酿酒指挥中心", [
    "制曲、上甑、蒸馏、摊晾、入窖、发酵、出窖等制酒大工艺。",
    "时序预测、质量/产量预测、工艺参数选优、相似批次检索、可解释分析。",
    "稳定质量和产量，减少批次波动，把专家经验转化为可复用的工艺规则。",
  ]);
  addOverviewCard(s, 3.12, "包装智能质检", [
    "灌装、压盖、贴标、喷码、液位、瓶身外观、酒体悬浮异物。",
    "目标检测、图像分割、异常检测、颗粒轨迹识别、缺陷复核学习。",
    "降低漏检和人工复检压力，形成缺陷追溯和质量改进闭环。",
  ]);
  addOverviewCard(s, 5.64, "设备预测性维护", [
    "灌装机、输送线、泵、空压机、锅炉、AGV、立体库等关键设备。",
    "异常检测、健康评分、故障模式识别、剩余寿命预测。",
    "提前识别停机风险，优化维修计划，减少突发停机损失。",
  ]);
  addOverviewCard(s, 8.16, "AGV路径优化", [
    "厂区物流节点、AGV任务、车辆位置、充电桩、避障、任务优先级。",
    "路径规划、任务分配、多车冲突消解、仿真评估。",
    "减少等待和绕路，提高厂内物流准时率和设备利用率。",
  ]);
  addOverviewCard(s, 10.68, "仓储物流优化", [
    "库位、订单、库存、装车、车辆、配送、多仓发货。",
    "库位优化、订单波次、装车排程、车辆路径优化。",
    "缩短装车发货时间，提高库位利用率、车辆满载率和配送效率。",
  ]);
}

function addSlide3() {
  const s = pptx.addSlide();
  addBg(s, 3);
  addRect(s, 3.12, 0.16, 7.2, 0.52, "1B2127", 0);
  addText(s, "匠心传承与数字未来的交汇点", 3.55, 0.28, 6.4, 0.16, {
    size: 18.2,
    bold: true,
    align: "center",
  });

  const cols = [
    {
      x: 0.58,
      title: "千年的技艺积淀",
      color: C.gold,
      body:
        "制曲、润粮、上甑、发酵……传统的今世缘酿造工艺，依赖于“老师傅”的眼观、鼻嗅、口尝。这是艺术，也是高度的主观经验。",
    },
    {
      x: 4.36,
      title: "规模化的认知瓶颈",
      color: C.text,
      body:
        "当产能呈指数级跨越，仅凭人工感官已无法确保每个批次的极致稳定。环境的微小波动、人员的状态差异，都在无形中消耗着优级酒的产出率。",
    },
    {
      x: 8.14,
      title: "转型的必然",
      color: C.gold,
      body:
        "我们不需要替代“匠人”，我们需要将“匠人经验”解码、量化、进化为一个永不疲倦、持续进化的超级数字大脑。",
    },
  ];

  cols.forEach((col) => {
    addPanel(s, col.x, 5.0, 3.55, 1.38, {
      fill: "131A20",
      transparency: 0,
      line: "6E7A83",
    });
    addText(s, col.title, col.x + 0.22, 5.22, 3.1, 0.18, {
      size: 10.5,
      bold: true,
      color: col.color,
      align: "center",
    });
    addText(s, col.body, col.x + 0.22, 5.68, 3.1, 0.42, {
      size: 7.4,
      color: C.muted,
      align: "center",
    });
  });
}

function addSlide4() {
  const s = pptx.addSlide();
  addBg(s, 4);
  addPanel(s, 3.02, 0.38, 2.36, 0.7, {
    fill: "061827",
    transparency: 0,
    line: C.cyan,
  });
  addText(s, "酿酒指挥中心", 3.38, 0.56, 1.62, 0.18, {
    size: 15.2,
    bold: true,
    color: C.text,
    align: "center",
  });
  addRect(s, 3.1, 1.18, 9.15, 0.88, "061827", 8);
  addText(
    s,
    "工艺介绍：酿酒过程具有典型的多阶段、长周期、强经验特征。制曲、润粮、上甑、蒸馏摘酒、摊晾、入窖、发酵、出窖等环节都会影响最终酒体质量和产量。AI在这个场景中的作用不是直接替代工艺人员，而是把历史批次数据、现场传感数据和专家经验融合起来，形成“预警、解释、选优、推荐”的工艺辅助系统。",
    3.12,
    1.24,
    8.98,
    0.68,
    { size: 7.6, color: C.text }
  );

  const dataPills = [
    "1. 现场环境数据：车间温湿度、窖池/酒醅温度、通风状态、季节、天气、能耗等。",
    "2. 工艺过程数据：投料批次、粮曲配比、润粮时间、上甑节奏、蒸汽压力、摘酒酒度、摊晾时间、入窖条件、发酵周期。",
    "3. 质量结果数据：出酒率、优级酒率、理化指标、感官评分、微生物检测、异常批次记录。",
    "4. 人工经验数据：工艺员操作记录、异常处理记录、专家点评、班组差异、人工调整原因。",
  ];
  dataPills.forEach((t, idx) => {
    addPill(s, t, 3.28 + idx * 0.08, 2.62 + idx * 0.48, 8.08 - idx * 0.14, {
      fill: idx % 2 === 0 ? "18D9F1" : "0E7AA6",
      color: "082030",
      size: 7.8,
      h: 0.34,
    });
  });

  const stages = [
    {
      x: 3.0,
      title: "预警阶段",
      body:
        "输入：温湿度、酒醅温度、水分、酸度、蒸汽压力、历史质量标签。\n方法：异常检测、LightGBM/XGBoost、LSTM/TCN、统计控制图。\n输出：异常预警、偏离原因、风险等级。",
    },
    {
      x: 5.44,
      title: "选优阶段",
      body:
        "输入：当前批次状态、历史优秀批次、专家规则、质量目标。\n方法：相似批次检索、贝叶斯优化、SHAP解释、规则库推荐。\n输出：工艺参数建议、推荐依据、预期收益。",
    },
    {
      x: 7.88,
      title: "闭环阶段",
      body:
        "输入：推荐执行结果、人工确认、实际质量和产量反馈。\n方法：反馈学习、模型重训、MPC局部控制验证。\n输出：建议优化、半自动控制候选、工艺知识沉淀。",
    },
  ];
  stages.forEach((stage) => {
    addTitleChip(s, stage.title, stage.x + 0.28, 4.84, 1.72, C.cyan);
    addPanel(s, stage.x, 5.1, 2.22, 1.34, {
      fill: "082234",
      transparency: 0,
      line: C.line,
    });
    addText(s, stage.body, stage.x + 0.16, 5.38, 1.9, 0.88, {
      size: 7.05,
      color: C.text,
    });
  });

  addPanel(s, 10.28, 4.66, 2.9, 1.95, {
    fill: "0B2540",
    transparency: 0,
    line: C.blue,
  });
  addText(s, "功能效益", 11.1, 4.92, 1.2, 0.2, {
    size: 11.5,
    bold: true,
    align: "center",
  });
  addBulletLines(
    s,
    [
      "把“老师傅经验”转成可查询、可解释、可复盘的工艺知识。",
      "提前发现批次偏离，减少事后追责式分析。",
      "通过优秀批次复用和参数推荐，提高质量稳定性和优级酒率。",
      "为后续企业工艺大模型、数字孪生和生产指挥中心打底。",
    ],
    10.58,
    5.32,
    2.15,
    0.32,
    { size: 7.2 }
  );
}

function addSlide5() {
  const s = pptx.addSlide();
  addBg(s, 5);
  addPanel(s, 5.04, 0.16, 3.5, 0.66, {
    fill: "061827",
    transparency: 0,
    line: C.cyan,
  });
  addText(s, "包装智能质检", 5.56, 0.34, 2.5, 0.18, {
    size: 16.2,
    bold: true,
    align: "center",
  });
  addRect(s, 3.0, 0.88, 7.0, 0.72, "061827", 8);
  addText(
    s,
    "工艺介绍：包装质检分成两条链路。第一条是外观检测，覆盖瓶盖、标签、喷码、液位、瓶身破损、盒箱外观等。第二条是酒体悬浮异物检测，难点在透明或半透明异物、气泡、瓶身曲面反光、高速产线节拍和多瓶型适配。",
    3.06,
    0.98,
    6.88,
    0.48,
    { size: 7.8, color: C.text }
  );

  addPanel(s, 0.42, 2.38, 2.08, 4.02, {
    fill: "061D2E",
    transparency: 0,
    line: C.line,
  });
  addText(s, "数据采集", 1.02, 2.58, 0.92, 0.2, {
    size: 11.2,
    bold: true,
    align: "center",
    color: C.cyanSoft,
  });
  addBulletLines(
    s,
    [
      "图像数据：多角度图片/视频（瓶盖、标签、喷码、液位、瓶身、酒液区域、盒箱）。",
      "光学数据：背光、侧光、偏振光、暗场光。",
      "产线数据：线速、相机触发、工位、剔除结果、复核结果、批次信息。",
      "标签数据：缺陷类型、位置、严重等级、误检/漏检结论。",
    ],
    0.62,
    3.0,
    1.58,
    0.78,
    { size: 7.25 }
  );

  addPanel(s, 3.0, 1.56, 7.92, 5.12, {
    fill: "061D2E",
    transparency: 12,
    line: C.cyan,
  });

  const midRows = [
    {
      label: "外观检测",
      y: 2.52,
      fill: C.cyan,
      color: "061A2A",
      items: [
        "采集：多相机、环形/条形/背光图像。",
        "算法：传统视觉规则、YOLO、Mask R-CNN、ViT 或 PatchCore 异常检测。",
        "输出：缺陷识别、缺陷定位、NG剔除、复核队列。",
      ],
    },
    {
      label: "酒体异物",
      y: 4.74,
      fill: C.gold,
      color: "101010",
      items: [
        "采集：依赖光学工艺。旋瓶、背光、偏振光、酒液区域连续视频帧。",
        "算法：运动颗粒轨迹提取、时序帧差、目标检测、异常分类模型（区分真实异物/气泡/反光/污点）。",
        "输出：异物检出、气泡过滤、疑似样本复核。",
      ],
    },
    {
      label: "质量追溯",
      y: 6.14,
      fill: C.cyan,
      color: "061A2A",
      items: [
        "采集：NG图片、复核结论入库。",
        "算法：缺陷聚类、趋势/根因分析。",
        "输出：按类型/产线/批次/供应商输出质检看板。",
      ],
    },
  ];

  midRows.forEach((row) => {
    addPill(s, row.label, 3.2, row.y, 1.0, {
      fill: row.fill,
      color: row.color,
      size: 8.4,
      h: 0.3,
    });
    const widths = row.y < 6 ? [1.8, 2.25, 1.85] : [1.8, 2.05, 2.0];
    const xs = row.y < 6 ? [4.38, 6.35, 8.7] : [4.38, 6.35, 8.52];
    row.items.forEach((item, idx) => {
      addPanel(s, xs[idx], row.y + 0.16, widths[idx], row.y < 6 ? 0.86 : 0.6, {
        fill: "082335",
        transparency: 0,
        line: idx === 1 ? C.line : "1E91B7",
      });
      addText(s, item, xs[idx] + 0.12, row.y + 0.34, widths[idx] - 0.24, row.y < 6 ? 0.46 : 0.28, {
        size: row.y < 6 ? 7.2 : 7.1,
        color: idx === 1 && row.y >= 4.7 ? C.gold : C.text,
      });
    });
  });

  addPanel(s, 11.3, 2.2, 1.72, 4.0, {
    fill: "0B2540",
    transparency: 0,
    line: "86CFF4",
  });
  addText(s, "功能效益", 11.72, 2.56, 0.88, 0.2, {
    size: 11.5,
    bold: true,
    align: "center",
  });
  addBulletLines(
    s,
    [
      "减少人工目检压力，提高高速产线质量一致性。",
      "把缺陷从“发现一个处理一个”升级为“趋势分析”。",
      "酒体异物检测先以样机验证为目标，形成可量化的预检率、误杀率和节拍数据。",
    ],
    11.52,
    3.1,
    1.16,
    0.84,
    { size: 7.1 }
  );
}

function addSlide6() {
  const s = pptx.addSlide();
  addBg(s, 6);
  addPanel(s, 0.34, 5.46, 1.86, 0.54, {
    fill: "061D2E",
    transparency: 0,
    line: C.line,
  });
  addText(s, "设备预测性维护", 0.58, 5.62, 1.38, 0.14, {
    size: 10.8,
    bold: true,
    align: "center",
    color: C.text,
  });
  addRect(s, 0.36, 6.08, 3.46, 0.98, "061827", 10);
  addText(
    s,
    "工艺介绍：预测性维护面向包装线、灌装机、输送系统、泵、空压机、锅炉、AGV、立体库等关键设备。目标不是替代维修人员，而是在故障发生前识别设备状态劣化，提前安排保养和备件，减少突发停机。",
    0.42,
    6.18,
    3.24,
    0.72,
    { size: 8.0 }
  );

  const sources = [
    "设备基础：\n编码、型号、投产、保养周期、历史故障。",
    "运行时序：\n电流、电压、振动、温度、压力、速度、负载、启停。",
    "维修工单：\n故障类型、原因、备件更换、停机时长。",
    "生产关联：\n产线节拍、产品规格、环境温湿度。",
  ];
  sources.forEach((src, idx) => {
    addPanel(s, 5.35, 1.04 + idx * 0.92, 2.14, 0.64, {
      fill: "082335",
      transparency: 0,
      line: C.line,
    });
    addText(s, src, 5.52, 1.18 + idx * 0.92, 1.78, 0.32, {
      size: 7.9,
      color: C.text,
      bold: idx === 0,
    });
  });

  addPanel(s, 7.85, 2.88, 0.86, 0.74, {
    fill: "082335",
    transparency: 0,
    line: C.cyan,
  });
  addText(s, "数据\n汇聚", 8.05, 3.04, 0.46, 0.28, {
    size: 12,
    bold: true,
    align: "center",
    color: C.cyanSoft,
  });

  const steps = [
    {
      y: 1.08,
      title: "步骤1：健康评分",
      body:
        "建立设备健康画像，区分开机/稳定/停机工况。\n数据：运行曲线、报警记录。\n算法：统计基线、特征工程、健康指数模型。\n输出：设备健康分、风险分级、趋势看板。",
      color: C.green,
    },
    {
      y: 2.84,
      title: "步骤2：异常预警",
      body:
        "识别与正常模式不同的物理变化。\n数据：振动、电流、温度等实时时序。\n算法：Isolation Forest、One-Class SVM、LSTM Autoencoder。\n输出：异常点识别、预警原因、影响设备。",
      color: C.cyan,
    },
    {
      y: 4.6,
      title: "步骤3：维修决策",
      body:
        "故障预测与备件建议。\n数据：异常历史、故障标签、工单。\n算法：XGBoost、随机森林、Transformer时序、RUL。\n输出：维修建议、备件建议、保养计划。",
      color: C.gold,
    },
  ];
  steps.forEach((step) => {
    addPanel(s, 9.64, step.y, 3.72, 1.25, {
      fill: "082335",
      transparency: 0,
      line: C.line,
    });
    addText(s, step.title, 9.86, step.y + 0.14, 1.26, 0.16, {
      size: 9.5,
      bold: true,
      color: step.color,
    });
    addText(s, step.body, 9.84, step.y + 0.38, 3.2, 0.78, {
      size: 7.2,
      color: C.text,
    });
  });

  addPanel(s, 9.92, 6.0, 3.12, 0.96, {
    fill: "0B65AE",
    transparency: 0,
    line: C.blue,
  });
  addText(s, "功能效益", 11.02, 6.18, 1.0, 0.18, {
    size: 11.8,
    bold: true,
    align: "center",
  });
  addBulletLines(
    s,
    [
      "从被动抢修转向主动保养，减少突发停机。",
      "将维修经验沉淀为故障知识库。",
      "为设备采购、备件库存提供风险依据。",
    ],
    10.18,
    6.42,
    2.48,
    0.18,
    { size: 7.5 }
  );
}

function addSlide7() {
  const s = pptx.addSlide();
  addBg(s, 7);
  addPanel(s, 4.2, 0.06, 4.1, 0.58, {
    fill: "134F8A",
    transparency: 0,
    line: "2F7DCC",
  });
  addText(s, "AGV路径优化", 5.0, 0.18, 2.46, 0.18, {
    size: 19,
    bold: true,
    align: "center",
  });
  addRect(s, 2.18, 0.8, 8.84, 0.72, "061827", 8);
  addText(
    s,
    "工艺介绍：解决厂内物流任务在空间和时间上的冲突。影响效率的原因通常不是单车路径，而是任务优先级、节点拥堵、车辆等待、充电策略、WMS/MES任务释放节奏不匹配。AI应先做仿真和调度优化，再逐步参与实时调度。",
    2.28,
    0.96,
    8.6,
    0.44,
    { size: 8.3, align: "center" }
  );

  addPanel(s, 0.22, 1.52, 2.65, 4.28, {
    fill: "061D2E",
    transparency: 2,
    line: C.line,
  });
  addText(s, "数据采集", 0.34, 1.72, 1.08, 0.2, {
    size: 13,
    bold: true,
    color: C.text,
  });
  addBulletLines(
    s,
    [
      "地图数据：道路、节点、工位、禁行区、转弯半径、充电桩。",
      "任务数据：起终点、货物类型、优先级、释放/要求完成时间。",
      "车辆数据：位置、速度、电量、载重、空闲/执行、充电状态。",
      "执行数据：实际路线、等待时间、冲突次数、完成时长。",
    ],
    0.36,
    2.14,
    2.15,
    0.88,
    { size: 7.7 }
  );

  const boxes = [
    {
      x: 4.25,
      y: 1.82,
      title: "路径规划 | 基础路线生成",
      body: "输入：地图拓扑、禁行区、作业区。\n方法：A*、Dijkstra、动态成本函数。\n输出：候选路线、预计时间、路径成本。",
    },
    {
      x: 9.9,
      y: 1.82,
      title: "任务调度 | 解决任务分配",
      body: "输入：任务队列、车辆电量、优先级。\n方法：规则启发式、遗传算法、蚁群、OR-Tools。\n输出：车辆分配、任务排序、充电安排。",
    },
    {
      x: 4.1,
      y: 4.68,
      title: "冲突消解 | 时间维度碰撞避免",
      body: "输入：多车路径、节点占用时间。\n方法：时间窗、CBS、多智能体路径规划。\n输出：避让策略、重规划、拥堵预警。",
    },
    {
      x: 10.0,
      y: 4.62,
      title: "仿真评估 | 上线前验证",
      body: "输入：历史任务回放、实际轨迹。\n方法：离线仿真、策略对比、敏感性分析。\n输出：上线策略、预期收益、风险节点。",
    },
  ];
  boxes.forEach((box) => {
    addPanel(s, box.x, box.y, 2.82, 1.0, {
      fill: "082335",
      transparency: 0,
      line: C.line,
    });
    addText(s, box.title, box.x + 0.16, box.y + 0.12, 2.5, 0.16, {
      size: 8.5,
      bold: true,
      color: C.cyanSoft,
    });
    addText(s, box.body, box.x + 0.16, box.y + 0.34, 2.46, 0.52, {
      size: 7.2,
      color: C.text,
    });
  });

  addPanel(s, 0.22, 6.26, 12.28, 0.58, {
    fill: "0B2540",
    transparency: 0,
    line: C.blue,
  });
  addText(s, "功能效益", 0.38, 6.42, 1.08, 0.14, {
    size: 12.2,
    bold: true,
    color: C.text,
  });
  addText(
    s,
    "减少AGV等待、绕路和节点拥堵，提高任务准时率。通过仿真先验证策略，降低直接上线调度算法的风险。联动WMS/MES后，可让物流节拍更贴近生产节拍。",
    1.86,
    6.36,
    10.2,
    0.2,
    { size: 8.7, color: C.text }
  );
}

function addSlide8() {
  const s = pptx.addSlide();
  addBg(s, 8);
  addRect(s, 0.18, 0.06, 4.2, 0.52, "061827", 0);
  addText(s, "仓储物流优化", 0.42, 0.16, 2.36, 0.18, {
    size: 20.5,
    bold: true,
  });
  addText(
    s,
    "工艺介绍：覆盖从订单进入、库存定位、库位分配、波次拣选、装车排程到配送路径的全过程。白酒企业常见难点是多仓装货、多客户订单混装、车辆时间窗、库位分散和临时订单扰动。",
    0.42,
    0.96,
    7.56,
    0.48,
    { size: 8.7 }
  );

  const leftBoxes = [
    "1. 订单数据：\n客户、产品、数量、优先级、交付时间、混装/多仓需求。",
    "2. 库存数据：\nSKU、批次、库位、库存量、保质/周转要求。",
    "3. 仓库数据：\n库区、货架、月台、叉车、拣选路径、装车口。",
    "4. 车辆数据：\n车型、容量、路线、时间窗、装载约束。",
  ];
  leftBoxes.forEach((box, idx) => {
    addPanel(s, 0.42, 2.0 + idx * 1.06, 2.65, 0.86, {
      fill: "123552",
      transparency: 4,
      line: "3F78A3",
    });
    addText(s, box, 0.6, 2.18 + idx * 1.06, 2.15, 0.48, {
      size: 8.3,
      color: C.text,
      bold: idx === 0,
    });
  });

  const rightSteps = [
    "1. 库位优化（仓内）\n输入：SKU周转、关联度、出库频次。\n方法：ABC分类、关联规则、库位评分。\n输出：推荐库位、移库建议、热区分析。",
    "2. 订单波次（调度）\n输入：客户、时间窗、产品组合。\n方法：聚类、规则引擎、启发式排序。\n输出：波次计划、拣选顺序、月台安排。",
    "3. 装车排程（装载）\n输入：车辆、体积重量、多客户约束。\n方法：装载规划、约束优化。\n输出：装车顺序、车辆利用率、发车计划。",
    "4. 配送路径（仓外）\n输入：客户地址、多仓节点、道路距离。\n方法：VRP/MDVRP/VRPTW、OR-Tools、ALNS。\n输出：配送路线、预计到达时间。",
  ];
  rightSteps.forEach((step, idx) => {
    s.addShape(pptx.ShapeType.rightArrow, {
      x: 9.9,
      y: 1.28 + idx * 1.4,
      w: 3.0,
      h: 0.9,
      fill: { color: idx % 2 === 0 ? "0F78DE" : "0A5BB0", transparency: 6 },
      line: { color: "79B9FF", width: 0.8 },
    });
    addText(s, step, 10.06, 1.52 + idx * 1.4, 2.32, 0.52, {
      size: 7.4,
      color: C.text,
    });
  });

  addPanel(s, 4.42, 6.18, 7.62, 0.56, {
    fill: "0B2540",
    transparency: 0,
    line: C.line,
  });
  addText(
    s,
    "功能效益：缩短装车发货时间，减少车辆等待和仓内无效移动。提升库位利用率和车辆满载率，降低配送里程和调度成本。让仓储物流从人工经验排程逐步升级为优化系统。",
    4.62,
    6.34,
    7.22,
    0.2,
    { size: 8.9, align: "center" }
  );
}

function addSlide9() {
  const s = pptx.addSlide();
  addBg(s, 9);
  addRect(s, 2.8, 0.08, 5.6, 0.54, "061827", 0);
  addText(s, "分阶段推进建议与实施路径", 3.1, 0.18, 5.0, 0.18, {
    size: 21.5,
    bold: true,
    align: "center",
  });
  const cards = [
    {
      x: 0.6,
      y: 4.85,
      head: "0-2个月：基础设施与顶层设计",
      body:
        "重点任务：梳理生产工艺、设备点位、批次主线、质量标签和系统接口。\n交付物：生产数据字典、场景MVP清单、关键设备清单。\n判断标准：能否按批次追踪数据，能否定义每个场景的验收指标。",
    },
    {
      x: 3.85,
      y: 4.35,
      head: "3-6个月：POC核心场景落地验证",
      body:
        "重点任务：优先做酿酒预警/选优、包装外观质检、设备健康评分。\n交付物：三个POC样板系统、模型评测报告、业务看板。\n判断标准：业务人员愿意使用，指标可量化，数据能持续回流。",
    },
    {
      x: 7.06,
      y: 3.86,
      head: "6-12个月：复杂场景与仿真优化",
      body:
        "重点任务：推进酒体异物样机、AGV仿真调度、仓储装车/库位优化。\n交付物：样机测试报告、仿真平台、优化策略上线方案。\n判断标准：节拍、误检、等待时间、装车时间等指标有改善。",
    },
    {
      x: 10.1,
      y: 3.36,
      head: "12个月以上：全链路闭环与智能指挥",
      body:
        "重点任务：做工艺建议闭环、预测维护工单闭环、物流全链路优化。\n交付物：持续学习机制、跨系统联动、生产指挥中心。\n判断标准：形成稳定迭代机制，而不是一次性项目。",
    },
  ];
  cards.forEach((card) => {
    addPanel(s, card.x, card.y, 2.74, 1.78, {
      fill: "082335",
      transparency: 0,
      line: "88C9EA",
    });
    addText(s, card.head, card.x + 0.16, card.y + 0.2, 2.34, 0.32, {
      size: 8.9,
      bold: true,
      color: C.text,
    });
    addText(s, card.body, card.x + 0.16, card.y + 0.62, 2.34, 0.96, {
      size: 7.25,
      color: C.text,
    });
  });
}

function addRefBox(slide, x, y, title, support) {
  addPanel(slide, x, y, 4.86, 0.74, {
    fill: "061D2E",
    transparency: 2,
    line: C.line,
  });
  addText(slide, title, x + 0.22, y + 0.16, 4.3, 0.18, {
    size: 9.7,
    bold: true,
    color: C.text,
  });
  addText(slide, `支撑：${support}`, x + 0.22, y + 0.42, 4.3, 0.14, {
    size: 7.6,
    color: C.muted,
  });
}

function addSlide10() {
  const s = pptx.addSlide();
  addBg(s, 10);
  addRect(s, 2.7, 0.12, 6.1, 0.52, "061827", 0);
  addText(s, "标杆案例与前沿技术背书（参考资料）", 3.0, 0.2, 5.5, 0.18, {
    size: 19.5,
    bold: true,
    align: "center",
  });
  addRefBox(s, 1.02, 1.34, "酒企标杆 | 茅台制酒酿造技艺机器学习系统", "酿酒工艺数化/数字化、机器学习、SHAP解释、经验沉淀。");
  addRefBox(s, 6.72, 1.34, "酒企标杆 | 泸州老窖智能包装中心", "高速包装、AI质检、数字孪生、工业物联网。");
  addRefBox(s, 1.02, 2.48, "酒企标杆 | 洋河/双沟先进级智能工厂", "江苏酒企智能工厂对标、数字孪生和AI场景化。");
  addRefBox(s, 6.72, 2.48, "视觉设备 | Krones AI视觉检测", "包装外观、空瓶和灌装后检测。");
  addRefBox(s, 1.02, 3.62, "视觉设备 | Cognex异物检测方案", "酒体悬浮异物检测可参考医药灯检。");
  addRefBox(s, 6.72, 3.62, "运筹优化 | Google OR-Tools Routing", "AGV调度、车辆路径、仓储配送优化。");
  addRefBox(s, 1.02, 4.76, "发酵建模 | Hybrid Modeling for On-Line Fermentation", "发酵机理模型与数据模型融合。");
  addRefBox(s, 6.72, 4.76, "时序预测 | Temporal Fusion Transformers (TFT)", "多步预测和可解释时序建模。");
  addRect(s, 4.4, 6.04, 4.5, 0.78, "061827", 4);
  addText(s, "感谢您的聆听", 5.12, 6.16, 3.0, 0.18, {
    size: 17,
    bold: true,
    align: "center",
  });
  addText(
    s,
    "江苏南大五维电子科技有限公司\n技术上追求精益求精，服务上追求全心全意",
    5.0,
    6.42,
    3.26,
    0.28,
    { size: 8.5, align: "center", color: C.text }
  );
}

function buildDeck() {
  addSlide1();
  addSlide2();
  addSlide3();
  addSlide4();
  addSlide5();
  addSlide6();
  addSlide7();
  addSlide8();
  addSlide9();
  addSlide10();
}

async function main() {
  buildDeck();
  await pptx.writeFile({ fileName: OUTPUT_ASCII });
  fs.copyFileSync(OUTPUT_ASCII, OUTPUT_CN);
  console.log(OUTPUT_ASCII);
  console.log(OUTPUT_CN);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
