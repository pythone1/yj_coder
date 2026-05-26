const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const root = "E:/PY/research";
const outDir = path.join(root, "output/ppt");
const imgDir = path.join(root, "tmp/jinshiyuan_input_media2");
fs.mkdirSync(outDir, { recursive: true });

const pptx = new pptxgen();
pptx.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
pptx.layout = "WIDE";
pptx.author = "Codex";
pptx.company = "南大五维";
pptx.subject = "今世缘酒业生产模块AI工艺分析与实施路径";
pptx.title = "Jinshiyuan AI Production Blueprint Editable Fidelity";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const C = {
  white: "F2FBFF",
  mute: "B8D8E9",
  cyan: "2FEAFF",
  gold: "F0B75B",
  dark: "061A2A",
  panel: "09283A",
  line: "2E9DCA",
};

function img(n) {
  return path.join(imgDir, `image${n}.png`);
}

function bg(slide, n) {
  slide.addImage({ path: img(n), x: 0, y: 0, w: 13.333, h: 7.5 });
}

function text(slide, value, x, y, w, h, opt = {}) {
  slide.addText(value, {
    x, y, w, h,
    margin: opt.margin ?? 0.04,
    fontFace: "Microsoft YaHei",
    fontSize: opt.size ?? 10,
    color: opt.color || C.white,
    bold: !!opt.bold,
    align: opt.align || "left",
    valign: opt.valign || "top",
    fit: "shrink",
    paraSpaceAfterPt: 0,
  });
}

function panel(slide, x, y, w, h, opt = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: opt.fill || C.dark, transparency: opt.transparency ?? 4 },
    line: { color: opt.line || C.line, transparency: opt.lineTrans ?? 0, width: opt.width ?? 1 },
  });
  if (opt.topLine !== false) {
    slide.addShape(pptx.ShapeType.line, {
      x: x + 0.15, y: y + 0.16, w: w - 0.3, h: 0,
      line: { color: opt.glow || C.cyan, transparency: 10, width: 0.7 },
    });
  }
}

function pill(slide, value, x, y, w, opt = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.28,
    fill: { color: opt.fill || C.cyan, transparency: opt.transparency ?? 0 },
    line: { color: opt.fill || C.cyan, width: 0.6 },
  });
  text(slide, value, x + 0.04, y + 0.055, w - 0.08, 0.13, {
    size: opt.size ?? 8.2,
    bold: true,
    color: opt.color || "061A2A",
    align: "center",
  });
}

function bullets(slide, items, x, y, w, opt = {}) {
  const gap = opt.gap || 0.28;
  items.forEach((item, i) => {
    slide.addShape(pptx.ShapeType.ellipse, {
      x, y: y + 0.08 + i * gap, w: 0.06, h: 0.06,
      fill: { color: opt.dot || C.cyan },
      line: { color: opt.dot || C.cyan, width: 0.3 },
    });
    text(slide, item, x + 0.13, y + i * gap, w - 0.13, gap, {
      size: opt.size || 8.6,
      color: opt.color || C.white,
    });
  });
}

function titleBar(slide, title, sub = "") {
  panel(slide, 0.52, 0.26, 8.5, 0.78, { fill: "061827", transparency: 14, line: C.cyan });
  text(slide, title, 0.75, 0.42, 5.9, 0.26, { size: 18, bold: true });
  if (sub) text(slide, sub, 0.78, 0.76, 7.6, 0.14, { size: 7.8, color: C.mute });
}

function coverText(slide) {
  panel(slide, 0.72, 2.78, 5.58, 1.74, { fill: "071927", transparency: 5, line: "347FA8" });
  text(slide, "今世缘酒业生产模块AI工艺\n分析与实施路径", 1.02, 3.05, 4.85, 0.72, { size: 20, bold: true });
  text(slide, "开题版 | 数据、工艺、算法、效益一体化说明", 1.03, 3.97, 4.55, 0.18, { size: 9.5, color: C.mute });
  text(slide, "2026-04-24\n江苏南大五维电子科技有限公司", 1.02, 4.92, 3.2, 0.34, { size: 7.8, color: C.mute });
}

function overview(slide) {
  panel(slide, 1.45, 0.76, 10.55, 0.66, { fill: "061827", transparency: 5, line: C.cyan });
  text(slide, "生产模块总体进程", 5.3, 0.87, 2.8, 0.24, { size: 15.5, bold: true, align: "center" });
  text(slide, "从人工经验到数字大脑：数据感知、算法判断、工艺执行、效果反馈闭环", 2.15, 1.18, 9.05, 0.14, { size: 7.8, color: C.mute, align: "center" });
  const cards = [
    ["酿酒指挥中心", "酿造数据、专家经验、质量结果融合\n工艺预警 / 工艺选优 / 参数推荐"],
    ["包装智能质检", "外观缺陷与酒体异物双链路\nYOLO / 异常检测 / 多光源成像"],
    ["设备预测性维护", "运行时序、报警码、维修工单融合\n异常检测 / RUL预测 / 维修建议"],
    ["AGV路径优化", "地图拓扑、任务队列、车辆状态融合\n路径规划 / 冲突消解 / 调度优化"],
    ["仓储物流优化", "订单、库存、库位、车辆统一建模\n波次 / 装车 / 配送路径优化"],
  ];
  cards.forEach((c, i) => {
    const x = 0.64 + i * 2.52;
    panel(slide, x, 2.1, 2.02, 3.36, { fill: "061D2E", transparency: 7, line: C.line });
    text(slide, c[0], x + 0.18, 2.95, 1.66, 0.18, { size: 10, bold: true, align: "center" });
    text(slide, c[1], x + 0.2, 3.35, 1.62, 0.7, { size: 7.4, color: C.mute, align: "center" });
  });
}

function craft(slide) {
  titleBar(slide, "匠心传承与数字未来的交汇点");
  panel(slide, 0.55, 5.13, 3.72, 0.92, { fill: "131A20", transparency: 3, line: "6E7A83" });
  text(slide, "千年的技艺沉淀", 0.92, 5.33, 1.6, 0.18, { size: 10.6, bold: true, color: C.gold });
  text(slide, "制曲、润粮、上甑、摘酒等环节依赖看、闻、尝、听、摸等隐性经验。", 0.9, 5.65, 2.95, 0.22, { size: 7.2, color: C.mute });
  panel(slide, 4.8, 5.13, 3.72, 0.92, { fill: "131A20", transparency: 3, line: "6E7A83" });
  text(slide, "规模化的认知瓶颈", 5.18, 5.33, 1.7, 0.18, { size: 10.6, bold: true, color: C.cyan });
  text(slide, "数据分散在传感器、质检、工单、设备系统中，尚未形成完整工艺因果链。", 5.15, 5.65, 2.95, 0.22, { size: 7.2, color: C.mute });
  panel(slide, 9.05, 5.13, 3.72, 0.92, { fill: "131A20", transparency: 3, line: "6E7A83" });
  text(slide, "转型的必然", 9.45, 5.33, 1.35, 0.18, { size: 10.6, bold: true, color: C.gold });
  text(slide, "AI不是替代匠人，而是将经验解码、量化并持续迭代为生产数字大脑。", 9.42, 5.65, 2.92, 0.22, { size: 7.2, color: C.mute });
}

function brewing(slide) {
  panel(slide, 3.35, 0.56, 8.55, 0.9, { fill: "061827", transparency: 3, line: C.cyan });
  text(slide, "酿酒指挥中心", 3.62, 0.72, 1.75, 0.24, { size: 15, bold: true, color: C.cyan });
  text(slide, "让发酵黑盒变成可解释、可预警、可推荐的工艺地图。", 3.62, 1.08, 6.9, 0.14, { size: 7.8, color: C.mute });
  pill(slide, "工艺链路", 4.02, 1.78, 0.9);
  ["制曲", "润粮", "上甑", "蒸馏摘酒", "摊晾", "入窖", "发酵", "评价"].forEach((v, i) => pill(slide, v, 4.0 + i * 0.72, 2.18, 0.58, { fill: i % 2 ? "0D6E91" : "16CBE4", size: 6.2 }));
  const alg = [
    ["工艺预警", "LightGBM / XGBoost\nLSTM / TCN / TFT"],
    ["工艺选优", "相似批次检索\n贝叶斯优化"],
    ["建议调参", "推荐参数\n理由与风险提示"],
  ];
  alg.forEach((a, i) => {
    panel(slide, 4.1 + i * 1.7, 3.28, 1.35, 0.78, { fill: "0A314A", transparency: 3, line: i === 1 ? C.gold : C.cyan });
    text(slide, a[0], 4.2 + i * 1.7, 3.42, 1.15, 0.14, { size: 8.6, bold: true, color: i === 1 ? C.gold : C.cyan, align: "center" });
    text(slide, a[1], 4.2 + i * 1.7, 3.7, 1.15, 0.25, { size: 6.6, color: C.white, align: "center" });
  });
  panel(slide, 9.6, 3.65, 2.4, 1.55, { fill: "062032", transparency: 5, line: C.line });
  text(slide, "功能效益", 9.88, 3.9, 0.9, 0.16, { size: 10.5, bold: true, color: C.cyan });
  bullets(slide, ["提前发现批次偏离", "复用优秀批次经验", "提高质量稳定性", "沉淀工艺知识库"], 9.88, 4.25, 1.6, { size: 7.2, gap: 0.23 });
}

function packaging(slide) {
  titleBar(slide, "包装智能质检", "外观检测与酒体异物检测双链路，服务高速产线在线判定");
  panel(slide, 0.48, 1.56, 1.98, 4.45, { fill: "061D2E", transparency: 5, line: C.line });
  text(slide, "数据采集", 0.75, 1.83, 0.9, 0.18, { size: 11, bold: true, color: C.cyan });
  bullets(slide, ["工业相机多角度图像", "背光、侧光、偏振光", "产线节拍与触发信号", "人工复核与缺陷标签"], 0.75, 2.25, 1.45, { size: 7.2, gap: 0.28 });
  panel(slide, 2.75, 1.72, 7.15, 3.9, { fill: "061D2E", transparency: 26, line: C.cyan });
  pill(slide, "外观检测", 3.05, 2.0, 0.9);
  text(slide, "瓶盖 / 标签 / 喷码 / 液位 / 盒箱\nYOLO、Mask R-CNN、ViT、PatchCore", 4.15, 2.05, 3.8, 0.42, { size: 8.4, color: C.white, align: "center" });
  pill(slide, "酒体异物", 3.05, 4.02, 0.9, { fill: C.gold, color: "101010" });
  text(slide, "旋瓶、多光源、视频帧、运动轨迹分析\n区分真实异物、气泡、酒液晃动、瓶壁污点和反光", 4.0, 4.05, 4.35, 0.42, { size: 8.2, color: C.gold, align: "center" });
  panel(slide, 10.45, 2.05, 1.95, 3.05, { fill: "061D2E", transparency: 5, line: C.line });
  text(slide, "功能效益", 10.72, 2.33, 0.9, 0.18, { size: 11, bold: true, color: C.cyan });
  bullets(slide, ["降低人工目检压力", "减少漏检误杀", "按批次材料设备追溯", "缺陷图库持续更新"], 10.72, 2.76, 1.35, { size: 7.1, gap: 0.27 });
}

function maintenance(slide) {
  panel(slide, 1.0, 4.95, 2.1, 0.76, { fill: "061D2E", transparency: 5, line: C.line });
  text(slide, "设备预测性维护", 1.24, 5.13, 1.3, 0.18, { size: 10.5, bold: true, color: C.cyan });
  text(slide, "从被动抢修转向主动预防。", 1.23, 5.42, 1.45, 0.12, { size: 6.8, color: C.mute });
  const left = [["设备数据", "电流、振动、温度、压力、报警码"], ["运行状态", "开机、稳态、换型、清洗、停机"], ["维修工单", "故障类型、备件更换、停机时长"]];
  left.forEach((a, i) => {
    panel(slide, 7.1, 1.25 + i * 1.0, 1.75, 0.66, { fill: "061D2E", transparency: 5, line: C.line });
    text(slide, a[0], 7.32, 1.38 + i * 1.0, 0.7, 0.13, { size: 8.5, bold: true, color: C.cyan });
    text(slide, a[1], 8.0, 1.34 + i * 1.0, 0.62, 0.22, { size: 5.9, color: C.mute });
  });
  const right = [["异常检测", "Isolation Forest\nLSTM Autoencoder"], ["故障预测", "XGBoost / Transformer\nRUL剩余寿命"], ["维修建议", "维修窗口\n备件需求"]];
  right.forEach((a, i) => {
    panel(slide, 10.1, 1.25 + i * 1.0, 1.82, 0.66, { fill: "061D2E", transparency: 5, line: i === 1 ? C.gold : C.line });
    text(slide, a[0], 10.3, 1.38 + i * 1.0, 0.72, 0.13, { size: 8.5, bold: true, color: i === 1 ? C.gold : C.cyan });
    text(slide, a[1], 11.02, 1.32 + i * 1.0, 0.72, 0.25, { size: 5.9, color: C.mute });
  });
}

function agv(slide) {
  titleBar(slide, "AGV路径优化", "任务分配、路径规划、冲突消解和仿真评估联合优化");
  panel(slide, 0.55, 1.46, 2.05, 4.36, { fill: "061D2E", transparency: 5, line: C.line });
  text(slide, "数据采集", 0.82, 1.75, 0.85, 0.18, { size: 11, bold: true, color: C.cyan });
  bullets(slide, ["厂区地图、节点、禁行区", "任务起点、终点、优先级", "车辆位置、电量、状态", "等待、拥堵、冲突记录"], 0.82, 2.18, 1.45, { size: 7.1, gap: 0.28 });
  panel(slide, 3.12, 1.65, 6.35, 4.05, { fill: "061D2E", transparency: 45, line: C.cyan });
  pill(slide, "地图拓扑", 3.55, 2.05, 0.9);
  pill(slide, "任务队列", 5.25, 2.05, 0.9, { fill: C.gold, color: "101010" });
  pill(slide, "车辆状态", 6.95, 2.05, 0.9, { fill: "3EE5A5", color: "061A2A" });
  text(slide, "A* / Dijkstra\nOR-Tools\n遗传算法 / 蚁群算法", 4.7, 5.1, 2.25, 0.5, { size: 9.2, bold: true, color: C.gold, align: "center" });
  panel(slide, 10.05, 1.72, 2.25, 3.45, { fill: "061D2E", transparency: 5, line: C.line });
  text(slide, "功能效益", 10.35, 2.0, 0.9, 0.18, { size: 11, bold: true, color: C.cyan });
  bullets(slide, ["减少等待、空驶和绕路", "降低节点拥堵和死锁", "提高任务准时率", "仿真验证上线风险"], 10.35, 2.42, 1.55, { size: 7.2, gap: 0.28 });
}

function warehouse(slide) {
  titleBar(slide, "仓储物流优化", "订单、库位、装车与配送路径统一建模");
  panel(slide, 0.62, 1.48, 2.35, 4.55, { fill: "061D2E", transparency: 5, line: C.line });
  text(slide, "工艺介绍", 0.9, 1.78, 0.85, 0.18, { size: 11, bold: true, color: C.cyan });
  bullets(slide, ["订单进入、库存定位、库位分配", "波次拣选、装车排程、配送路径", "多仓装货、多客户混装、时间窗约束"], 0.9, 2.22, 1.75, { size: 7.1, gap: 0.32 });
  const steps = [["1. 库位优化", "ABC分类、SKU关联度"], ["2. 波次排程", "客户、路线、时间窗"], ["3. 装车排序", "车辆容量、月台约束"], ["4. 路径优化", "VRP / MDVRP / VRPTW"]];
  steps.forEach((a, i) => {
    panel(slide, 9.85, 1.45 + i * 1.07, 2.35, 0.62, { fill: "063554", transparency: 7, line: C.cyan });
    text(slide, a[0], 10.05, 1.58 + i * 1.07, 0.9, 0.14, { size: 8.5, bold: true });
    text(slide, a[1], 10.9, 1.55 + i * 1.07, 0.92, 0.18, { size: 6.2, color: C.mute });
  });
  panel(slide, 3.75, 5.62, 4.65, 0.54, { fill: "061D2E", transparency: 4, line: C.gold });
  text(slide, "核心算法：OR-Tools / ALNS / VNS / 遗传算法", 4.03, 5.8, 4.1, 0.12, { size: 9.4, bold: true, color: C.gold, align: "center" });
}

function roadmap(slide) {
  titleBar(slide, "分阶段推进建议与实施路径");
  const steps = [
    ["0-2个月", "基础数据与样板设计", "梳理数据源、采集口径、业务指标与样板边界"],
    ["3-6个月", "POC验证与模型上线", "完成酿酒预警、外观质检、设备异常检测"],
    ["6-12个月", "业务闭环与系统联动", "打通MES/WMS/SCADA/质检/工单"],
    ["12个月以上", "全链路闭环优化", "沉淀企业专属模型，扩展跨场景联动"],
  ];
  steps.forEach((s, i) => {
    panel(slide, 1.05 + i * 3.0, 4.85 - i * 0.57, 2.35, 1.15, { fill: "061D2E", transparency: 5, line: C.cyan });
    text(slide, s[0], 1.25 + i * 3.0, 5.05 - i * 0.57, 0.9, 0.16, { size: 9.4, bold: true, color: C.gold });
    text(slide, s[1], 1.25 + i * 3.0, 5.38 - i * 0.57, 1.65, 0.16, { size: 8.8, bold: true });
    text(slide, s[2], 1.25 + i * 3.0, 5.68 - i * 0.57, 1.72, 0.24, { size: 6.2, color: C.mute });
  });
}

function refs(slide) {
  titleBar(slide, "标杆案例与前沿技术背书（参考资料）");
  const refs = [
    ["酒企案例", "五粮液数字化车间 / 泸州老窖智能酿造 / 洋河智能工厂"],
    ["质检案例", "康耐视机器视觉 / 海康机器人 / 医药瓶检与异物检测"],
    ["算法技术", "YOLO / Mask R-CNN / ViT / LSTM / TFT / Transformer"],
    ["优化技术", "OR-Tools / ALNS / VNS / 数字孪生仿真评估"],
    ["工艺平台", "MES / WMS / SCADA / 质检系统 / 设备工单"],
    ["沉淀方向", "工艺知识图谱 / 专家经验结构化 / 企业专属生产大模型"],
  ];
  refs.forEach((r, i) => {
    const x = i % 2 ? 7.0 : 1.05;
    const y = 1.45 + Math.floor(i / 2) * 1.18;
    panel(slide, x, y, 5.0, 0.72, { fill: "061D2E", transparency: 5, line: C.line });
    text(slide, r[0], x + 0.22, y + 0.22, 0.9, 0.14, { size: 9.2, bold: true, color: C.gold });
    text(slide, r[1], x + 1.15, y + 0.21, 3.5, 0.16, { size: 7.2, color: C.white });
  });
  panel(slide, 4.55, 6.08, 4.25, 0.58, { fill: "061D2E", transparency: 5, line: C.cyan });
  text(slide, "感谢聆听", 5.45, 6.22, 2.4, 0.18, { size: 14, bold: true, align: "center" });
}

const builders = [coverText, overview, craft, brewing, packaging, maintenance, agv, warehouse, roadmap, refs];
for (let i = 1; i <= 10; i++) {
  const slide = pptx.addSlide();
  bg(slide, i);
  builders[i - 1](slide);
}

const out = path.join(outDir, "Jinshiyuan_AI_Production_Blueprint_可编辑保真版.pptx");
pptx.writeFile({ fileName: out });
