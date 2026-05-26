const pptxgen = require("pptxgenjs");
const {
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
} = require("./pptxgenjs_helpers/layout");

async function main() {
const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "OpenAI";
pptx.subject = "0401 algorithm flow and metrics";
pptx.title = "0401 算法流程图与指标对应关系";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Microsoft YaHei",
  bodyFontFace: "Microsoft YaHei",
  lang: "zh-CN",
};

const slide = pptx.addSlide();
slide.background = { color: "F7F7F5" };

const colors = {
  ink: "1F2937",
  muted: "5B6573",
  blue: "DCEBFF",
  blueBorder: "4A7BD0",
  sand: "F5E7C8",
  sandBorder: "C98A1D",
  green: "DDEFD9",
  greenBorder: "4D8A43",
  rose: "F9E0E0",
  roseBorder: "C05656",
  violet: "E9E1F8",
  violetBorder: "7A58B0",
  gray: "E9ECEF",
  grayBorder: "9098A1",
  accent: "C75C1D",
};

function addBox(slideObj, x, y, w, h, title, body, fill, line) {
  slideObj.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: fill },
    line: { color: line, pt: 1.4 },
  });
  slideObj.addText(title, {
    x: x + 0.12, y: y + 0.08, w: w - 0.24, h: 0.22,
    fontFace: "Microsoft YaHei",
    fontSize: 13,
    bold: true,
    color: colors.ink,
    margin: 0,
    valign: "mid",
  });
  slideObj.addText(body, {
    x: x + 0.12, y: y + 0.34, w: w - 0.24, h: h - 0.42,
    fontFace: "Microsoft YaHei",
    fontSize: 8.7,
    color: colors.muted,
    margin: 0,
    breakLine: false,
    valign: "mid",
  });
}

function addDownMark(slideObj, x, y) {
  slideObj.addText("↓", {
    x, y, w: 0.3, h: 0.08,
    fontFace: "Microsoft YaHei",
    fontSize: 12,
    bold: true,
    color: colors.grayBorder,
    align: "center",
    margin: 0,
  });
}

slide.addText("0401 算法流程图与指标对应关系", {
  x: 0.45, y: 0.18, w: 7.8, h: 0.4,
  fontFace: "Microsoft YaHei",
  fontSize: 22,
  bold: true,
  color: colors.ink,
  margin: 0,
});

slide.addText("目的：把数据构造、GA、轮盘赌、AM、posterior summary、posterior predictive 分开看，不再把所有阶段混成一个 posterior median 分数。", {
  x: 0.48, y: 0.62, w: 12.2, h: 0.34,
  fontFace: "Microsoft YaHei",
  fontSize: 9.2,
  color: colors.muted,
  margin: 0,
});

// Left flowchart
slide.addText("算法流程图", {
  x: 0.45, y: 1.02, w: 2.0, h: 0.22,
  fontFace: "Microsoft YaHei",
  fontSize: 12,
  bold: true,
  color: colors.ink,
  margin: 0,
});

addBox(
  slide, 0.45, 1.28, 3.55, 0.78,
  "1. 正式真值事件模型",
  "0327_由旱天基线重建_三点注水模型_0.3倍.inp；三点注入 J76/J124/J140；truth replay 必须 = 1.0。",
  colors.blue, colors.blueBorder
);
addBox(
  slide, 0.45, 2.26, 3.55, 0.78,
  "2. 去注水得到正式基线",
  "从真值事件模型删去三处注水与对应时序，得到旱天基线；保证模板链闭合。",
  colors.sand, colors.sandBorder
);
addBox(
  slide, 0.45, 3.24, 3.55, 0.88,
  "3. build_0401_data",
  "从真值模型抽出总过程线与真值份额；用与 GA/AM 相同的 evaluate_shares 再构造 canonical event / observed_delta。",
  colors.green, colors.greenBorder
);
addBox(
  slide, 0.45, 4.34, 3.55, 0.92,
  "4. GA 多种群搜索",
  "20 维 simplex 份额向量；初始化为 sparse + Dirichlet；每代按 mean NSE 排序，做 elite 保留、交叉、变异、competition、migration。",
  colors.violet, colors.violetBorder
);
addBox(
  slide, 0.45, 5.5, 3.55, 0.78,
  "5. 轮盘赌 initial_PPD",
  "用 GA 末代合并池的 mean NSE 去负平移，转成概率后不放回抽样；得到 AM 的起点集合与 prior information。",
  colors.rose, colors.roseBorder
);
addBox(
  slide, 0.45, 6.48, 3.55, 0.9,
  "6. AM 多链采样",
  "每条链从 initial_PPD 起跑；proposal = 高斯游走 + simplex 投影；接受率按英文论文为 likelihood ratio；协方差自适应更新。",
  colors.gray, colors.grayBorder
);

addDownMark(slide, 2.08, 2.13);
addDownMark(slide, 2.08, 3.11);
addDownMark(slide, 2.08, 4.20);
addDownMark(slide, 2.08, 5.31);
addDownMark(slide, 2.08, 6.32);

// Right metrics table
slide.addText("每一步对应指标表", {
  x: 4.28, y: 1.02, w: 3.0, h: 0.22,
  fontFace: "Microsoft YaHei",
  fontSize: 12,
  bold: true,
  color: colors.ink,
  margin: 0,
});

const rows = [
  [
    { text: "阶段", options: { bold: true, color: "FFFFFF" } },
    { text: "该看什么", options: { bold: true, color: "FFFFFF" } },
    { text: "当前说明", options: { bold: true, color: "FFFFFF" } },
  ],
  ["Truth replay", "mean NSE / SSE", "验证模板、注水、评分链是否闭合；当前 = 1.0 / 4.09e-30"],
  ["GA", "ga_best_mean_nse + 每代最佳", "GA 是点优化器，主排序指标就是 mean NSE"],
  ["initial_PPD", "样本数、top 样本质量、分布宽度", "决定 AM 起点有多尖还是多散"],
  ["AM 采样", "接受率、AM样本最大 mean NSE、best by log_like", "AM 接受率按 likelihood；不能只看 posterior median"],
  ["posterior summary", "posterior_mean / median / P05 / P95 / top3", "解释结构与不确定性，不是最佳拟合分数"],
  ["posterior predictive", "coverage_mean + 各点 coverage", "看后验整体能否覆盖观测响应"],
];

slide.addTable(rows, {
  x: 4.28, y: 1.28, w: 8.55, h: 4.92,
  border: { type: "solid", pt: 1, color: "C7CDD4" },
  fill: "FFFFFF",
  color: colors.ink,
  fontFace: "Microsoft YaHei",
  fontSize: 8.3,
  margin: 0.05,
  rowH: 0.56,
  colW: [1.55, 2.6, 4.4],
  autoFit: false,
  valign: "mid",
  bold: false,
  fillHeader: colors.blueBorder,
  line: { color: "C7CDD4", pt: 1 },
});

slide.addText("Medium vs Large 的正确解读", {
  x: 4.28, y: 6.30, w: 3.1, h: 0.24,
  fontFace: "Microsoft YaHei",
  fontSize: 12,
  bold: true,
  color: colors.ink,
  margin: 0,
});

slide.addText(
  [
    { text: "Medium：", options: { bold: true, color: colors.ink } },
    { text: "GA best = 0.7425；posterior median = 0.7553；top3 = J145/J125/J124。更像“高分代偿解”。", options: { color: colors.muted } },
    { text: "\nLarge：", options: { bold: true, color: colors.ink } },
    { text: "GA best = 0.6873；AM样本最大 mean NSE = 0.8102；posterior median = 0.5606；top3 = J124/J140/J145。更像“真实结构解 + 多峰后验”。", options: { color: colors.muted } },
    { text: "\n提醒：", options: { bold: true, color: colors.accent } },
    { text: "不能只拿 posterior median 去代表整个流程优劣；GA、AM、posterior summary、posterior predictive 必须按各自指标解读。", options: { color: colors.accent } },
  ],
  {
    x: 4.28, y: 6.56, w: 8.55, h: 0.62,
    fontFace: "Microsoft YaHei",
    fontSize: 8.4,
    margin: 0.04,
    breakLine: false,
    fill: { color: "FFF7ED" },
    line: { color: "E8B27A", pt: 1.2 },
    valign: "mid",
  }
);

warnIfSlideHasOverlaps(slide, pptx);
warnIfSlideElementsOutOfBounds(slide, pptx);

await pptx.writeFile({ fileName: "E:/PY/LSTM/0401/output/slides/algo_flow_page/0401_算法流程与指标汇报页.pptx" });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
