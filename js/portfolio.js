const portfolioCases = [
    {
        title: "Geospatial-AI-Ecosystem",
        role: "地理空间 AI 项目群 / 产品化原型",
        priority: "主推",
        summary: "覆盖智能地图、遥感解译、空间数据处理与可视化的综合项目群，适合证明跨场景工程整合能力。",
        stack: ["Geospatial AI", "遥感", "GIS", "可视化", "工程集成"],
        metrics: ["13 个系统", "4 类业务域", "多项目组合"],
        evidence: "E:\\PY\\Geospatial-AI-Ecosystem",
        interview: "重点讲“从算法到产品界面”的闭环：数据接入、空间分析、模型推理、地图表达和交互验证。"
    },
    {
        title: "射阳水厂 MFS-BPNN-SSA 复现",
        role: "污水处理建模 / 论文复现与模型审查",
        priority: "主推",
        summary: "围绕出水总氮预测和碳源投加分析，完成多模型复现、数据审查和风险边界梳理。",
        stack: ["KNN", "LightGBM", "BiRNN", "LSTM", "BPNN", "MFS"],
        metrics: ["7165 行数据", "2025-01-01 至 2026-05-01", "RTX 4060 训练环境"],
        evidence: "E:\\PY\\射阳城北污水处理厂\\射阳水厂\\mfs_bpnn_ssa_reproduction\\0610\\v3_results",
        interview: "强调这是离线分析与论文复现，不包装成已上线节能成果；重点讲数据口径、目标值、验证集和模型风险。"
    },
    {
        title: "SWMM + AM-MCMC 雨洪参数率定",
        role: "水文模型率定 / 不确定性分析",
        priority: "主推",
        summary: "用 SWMM 模型结合 AM-MCMC 做参数搜索和结果评估，能体现传统机理模型与统计推断结合能力。",
        stack: ["SWMM", "AM-MCMC", "NSE", "Python", "水文建模"],
        metrics: ["mean_nse = 0.9362", "参数率定", "模型评估"],
        evidence: "E:\\PY\\LSTM\\0520",
        interview: "从模型结构、参数空间、采样策略、NSE 指标和不确定性边界讲清楚，避免只说调参。"
    },
    {
        title: "CNN-AE 管网异常检测审查",
        role: "异常检测 / 结果复核",
        priority: "精选",
        summary: "对管网事件检测流程做复现和审查，能展示时序异常检测、误报分析和上线风险意识。",
        stack: ["CNN-AE", "时序异常检测", "事件匹配", "误报分析"],
        metrics: ["19/19 事件命中", "4 个误报", "344.9h 中位提前量"],
        evidence: "E:\\PY\\research\\0604",
        interview: "按“复现结果可用、生产结论需谨慎”表达：命中率、提前量、误报和标签定义都要一起讲。"
    },
    {
        title: "企业知识库 RAG Chatbot",
        role: "全栈 AI 应用 / 知识库问答",
        priority: "主推",
        summary: "具备文档解析、向量检索、模型问答、会话管理、后台管理和部署链路的完整 AI 应用。",
        stack: ["FastAPI", "React", "ChromaDB", "PyMuPDF", "RAG", "Cloudflare"],
        metrics: ["单端口部署", "权限与会话", "后台管理"],
        evidence: "E:\\PY\\chatbot",
        interview: "讲清楚解析、切分、召回、重排、提示词、权限隔离和部署方式，是最贴近 AI 工程岗位的项目。"
    },
    {
        title: "叉车定位与视觉识别系统",
        role: "工业现场识别 / 多源融合",
        priority: "精选",
        summary: "以 UWB 定位为主、YOLO 视觉辅助，结合串口/日志数据验证 A-C、B-C 等区域判断。",
        stack: ["UWB", "YOLO", "SQLite", "串口解析", "工业视觉"],
        metrics: ["UWB 主判定", "视觉辅助", "A-C/B-C 样例验证"],
        evidence: "E:\\PY\\叉车识别",
        interview: "重点讲工程取舍：现场鲁棒性优先，视觉不是唯一依据，而是对定位和事件判断做辅助增强。"
    },
    {
        title: "工业视觉方案调研与选型",
        role: "计算机视觉方案设计 / 成本评估",
        priority: "补充",
        summary: "围绕 2D 视觉、OCR、SAM、YOLO、Mask R-CNN 做方案对比，沉淀预算、精度和验收指标。",
        stack: ["YOLO", "SAM", "Mask R-CNN", "OCR", "方案评估"],
        metrics: ["精度指标", "预算对比", "验收口径"],
        evidence: "E:\\PY\\test\\0612",
        interview: "适合回答“你如何做技术选型”：从场景约束、样本量、标注成本、部署环境和验收标准反推方案。"
    }
];

function portfolioEscape(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function renderPortfolio() {
    const statsEl = document.getElementById("portfolio-stats");
    const gridEl = document.getElementById("portfolio-grid");
    if (!statsEl || !gridEl) return;

    const mainCases = portfolioCases.filter(item => item.priority === "主推").length;
    const stacks = new Set(portfolioCases.flatMap(item => item.stack));

    statsEl.innerHTML = [
        { label: "可投递项目", value: portfolioCases.length },
        { label: "主推案例", value: mainCases },
        { label: "技术关键词", value: stacks.size },
        { label: "证据路径", value: "全量保留" }
    ].map(item => `
        <div class="portfolio-stat">
            <span>${portfolioEscape(item.label)}</span>
            <strong>${portfolioEscape(item.value)}</strong>
        </div>
    `).join("");

    gridEl.innerHTML = portfolioCases.map(item => `
        <article class="portfolio-case">
            <div class="portfolio-case-header">
                <div>
                    <span class="priority-badge">${portfolioEscape(item.priority)}</span>
                    <h3>${portfolioEscape(item.title)}</h3>
                    <p>${portfolioEscape(item.role)}</p>
                </div>
                <i data-lucide="briefcase-business"></i>
            </div>
            <p class="portfolio-summary">${portfolioEscape(item.summary)}</p>
            <div class="portfolio-metrics">
                ${item.metrics.map(metric => `<span>${portfolioEscape(metric)}</span>`).join("")}
            </div>
            <div class="portfolio-stack">
                ${item.stack.map(tag => `<span>${portfolioEscape(tag)}</span>`).join("")}
            </div>
            <div class="portfolio-evidence">
                <i data-lucide="folder-search"></i>
                <span>${portfolioEscape(item.evidence)}</span>
            </div>
            <div class="portfolio-interview">
                <strong>面试讲法</strong>
                <p>${portfolioEscape(item.interview)}</p>
            </div>
        </article>
    `).join("");

    if (window.lucide) {
        lucide.createIcons();
    }
}

window.portfolioCases = portfolioCases;
window.renderPortfolio = renderPortfolio;
