const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'a2a_agent_protocol',
    name: 'Agent2Agent Protocol (A2A)',
    domain: '协议生态',
    horizon: '立即补',
    maturity: '快速标准化',
    relevance: 94,
    summary: 'A2A 关注不同框架、不同厂商 Agent 之间的发现、任务协作、状态同步和产物交换。',
    why: 'MCP 解决 Agent 连接工具和上下文，A2A 解决 Agent 之间如何互相发现、委派和协作，适合讲多智能体求职工作流。',
    actions: ['补充 A2A 与 MCP 对比卡', '设计 JD/简历/投递 Agent 协作流', '记录 Agent Card 和任务状态概念'],
    interview: '我会把 MCP 和 A2A 分开讲：MCP 偏工具与上下文接入，A2A 偏 Agent 间任务协作、能力发现、状态同步和 artifact 交付。',
    sources: [
      { label: 'Google A2A announcement', url: 'https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/' }
    ]
  },
  {
    id: 'ag_ui_protocol',
    name: 'AG-UI / Agent User Interaction Protocol',
    domain: '用户体验',
    horizon: '下一批',
    maturity: '新兴',
    relevance: 88,
    summary: '把 Agent 的事件、状态、工具调用、用户确认和界面更新标准化，让前端不只是展示最终答案。',
    why: '你的应用要走向商用，用户需要看到简历修改、证据检索、Git同步等长任务的过程，而不是等待黑箱结果。',
    actions: ['设计 Agent 事件流 UI', '把人工确认做成协议事件', '区分 plan/tool/result/error 四类事件'],
    interview: '我会把 Agent UI 做成事件驱动：计划、工具调用、等待确认、产物和错误都流式展示，降低用户不信任感。',
    sources: [
      { label: 'AG-UI docs', url: 'https://docs.ag-ui.com/' }
    ]
  },
  {
    id: 'owasp_llm_top10_2025',
    name: 'OWASP LLM Top 10 2025',
    domain: 'AI 安全',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 93,
    summary: '面向 LLM 应用的风险框架，包括提示注入、敏感信息泄露、供应链、过度代理和不安全输出处理等。',
    why: '求职助手会读取本地文档、联网检索、写文件和推 Git，必须用标准风险框架约束自动化边界。',
    actions: ['把高风险动作映射到 OWASP 风险', '为外部 JD 做注入检测', '给写文件/推送/外发动作加确认'],
    interview: '我会按 OWASP LLM Top 10 做安全设计，重点防 prompt injection、sensitive information disclosure 和 excessive agency。',
    sources: [
      { label: 'OWASP Top 10 for LLM Applications', url: 'https://owasp.org/www-project-top-10-for-large-language-model-applications/' }
    ]
  },
  {
    id: 'agent_eval_regression',
    name: 'Agent Eval Regression',
    domain: '评测体系',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 92,
    summary: '把 Agent 多步任务做成可重复评测集，比较任务成功率、工具轨迹、证据一致性、成本和耗时。',
    why: '简历润色、JD匹配、证据引用、知识雷达更新都需要回归测试，否则每次升级模型都有可能悄悄退化。',
    actions: ['建立 20 条求职任务评测集', '记录工具调用轨迹', '比较升级前后成功率和成本'],
    interview: '我会把 Agent 评测从“答案好不好”扩展到任务是否完成、轨迹是否合规、证据是否正确、成本是否可控。',
    sources: [
      { label: 'LangSmith evaluation concepts', url: 'https://docs.langchain.com/langsmith/evaluation-concepts' }
    ]
  },
  {
    id: 'opentelemetry_genai_semconv',
    name: 'OpenTelemetry GenAI Semantic Conventions',
    domain: '工程运维',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 87,
    summary: '用统一语义字段记录 GenAI 请求、模型、token、工具调用、延迟、错误和 trace。',
    why: '当前雷达已有 AgentOps，但还需要落到可观测性标准字段，方便后续接日志、监控和成本统计。',
    actions: ['补充 trace 字段表', '记录 token/latency/model/tool spans', '为长任务生成 trace id'],
    interview: '我会按 OpenTelemetry GenAI 语义约定记录模型调用、工具调用、token、延迟和错误，方便排障和成本治理。',
    sources: [
      { label: 'OpenTelemetry GenAI semantic conventions', url: 'https://opentelemetry.io/docs/specs/semconv/gen-ai/' }
    ]
  },
  {
    id: 'alphaearth_foundations',
    name: 'AlphaEarth Foundations / Satellite Embeddings',
    domain: '遥感基础模型',
    horizon: '立即补',
    maturity: '前沿',
    relevance: 96,
    summary: 'Google DeepMind 的地球观测嵌入模型，把多源遥感数据压缩为可用于制图、分类和变化分析的统一表示。',
    why: '你做养殖池塘、断面溯源、水色水质和滩涂规划，卫星 embedding 是遥感算法岗位必须跟进的新范式。',
    actions: ['补充 Earth Engine embedding 工作流', '对比传统指数与 embedding 特征', '设计养殖池塘 few-shot 分类实验'],
    interview: '遥感基础模型正在从单景影像分割走向时空 embedding，未来可以用少量样本快速适配地物分类、变化检测和水环境分析。',
    sources: [
      { label: 'Google DeepMind AlphaEarth Foundations', url: 'https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/' }
    ]
  },
  {
    id: 'prithvi_eo_2',
    name: 'Prithvi EO 2.0 / HLS Foundation Model',
    domain: '遥感基础模型',
    horizon: '立即补',
    maturity: '可实践',
    relevance: 94,
    summary: 'IBM-NASA 地球观测基础模型，面向 Harmonized Landsat Sentinel-2 等多光谱遥感任务微调。',
    why: '这是遥感算法工程师可直接讲清楚的开源基础模型路线，和你已有 Sentinel/水体/养殖图斑任务高度相关。',
    actions: ['补 Prithvi 微调卡', '整理 HLS 输入波段与 patch 策略', '设计池塘/水体分类迁移实验'],
    interview: 'Prithvi 这类 EO foundation model 的价值是用大规模遥感预训练特征降低下游标注量，再通过微调适配水体、农田和城市地物任务。',
    sources: [
      { label: 'Prithvi EO 2.0 model card', url: 'https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M' },
      { label: 'NASA IMPACT HLS foundation examples', url: 'https://github.com/NASA-IMPACT/hls-foundation-os' }
    ]
  },
  {
    id: 'clay_geospatial_foundation',
    name: 'Clay Foundation Model',
    domain: '遥感基础模型',
    horizon: '下一批',
    maturity: '可实践',
    relevance: 90,
    summary: '开源 Earth foundation model，面向 Sentinel、DEM、地球观测 embedding 和下游制图任务。',
    why: 'Clay 适合作为简历作品集里的开源 GeoAI 实验方向，用来展示你能把基础模型迁移到本地遥感场景。',
    actions: ['补 Clay 安装与推理卡', '比较 Clay/Prithvi/传统CNN', '选一个池塘样本做 embedding 可视化'],
    interview: '我会把 Clay 看作开放 GeoAI 基座，用它做特征提取、微调和下游分类，再和传统 UNet/DeepLabv3 做效果对比。',
    sources: [
      { label: 'Clay Foundation Model GitHub', url: 'https://github.com/Clay-foundation/model' }
    ]
  },
  {
    id: 'samgeo_remote_sensing',
    name: 'SAMGeo / Segment Geospatial',
    domain: '遥感视觉',
    horizon: '立即补',
    maturity: '可实践',
    relevance: 95,
    summary: '把 Segment Anything 与 GeoTIFF、矢量数据、瓦片影像和 GIS 工作流结合起来做地理空间分割。',
    why: '这和你江苏省养殖池塘上图入库项目直接相关，可以把 SAM 分割经验表达得更工程化。',
    actions: ['补 SAMGeo 工具链卡', '整理 raster-to-vector 后处理', '把池塘图斑项目映射到 SAMGeo 流程'],
    interview: 'SAM 用在遥感不能只点一下出 mask，还要处理坐标、瓦片、重叠、矢量化、拓扑修复和 GIS 入库。',
    sources: [
      { label: 'segment-geospatial GitHub', url: 'https://github.com/opengeos/segment-geospatial' }
    ]
  },
  {
    id: 'remote_sensing_vlm_grounding',
    name: 'Remote Sensing VLM Grounding',
    domain: '多模态遥感',
    horizon: '下一批',
    maturity: '新兴',
    relevance: 91,
    summary: '用视觉语言模型理解遥感图像、文本描述、地名、地物类别和空间关系，支持开放词汇识别与解释。',
    why: '未来遥感算法岗位会从固定类别分割走向“文本查询 + 地物定位 + 证据解释”，适合你的 AI+遥感复合定位。',
    actions: ['补开放词汇遥感检测卡', '设计文本提示识别养殖池塘/排口', '对比 CLIP/SAM/YOLO 组合流程'],
    interview: '遥感 VLM 的关键是把地物语义和空间定位连接起来，让模型能按文本提示找对象，并输出可解释证据。',
    sources: [
      { label: 'AlphaEarth Foundations context', url: 'https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/' },
      { label: 'segment-geospatial GitHub', url: 'https://github.com/opengeos/segment-geospatial' }
    ]
  },
  {
    id: 'geospatial_embedding_retrieval',
    name: 'Geospatial Embedding Retrieval',
    domain: '空间检索',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 89,
    summary: '把影像块、矢量图斑、地物属性和文本标签编码成 embedding，支持相似区域检索、样本挖掘和少样本分类。',
    why: '你的项目有大量池塘、断面、水体和报告证据，空间 embedding 可以帮助找相似样本、扩充训练集和做项目检索。',
    actions: ['设计图斑 embedding 索引', '把错误样本做相似检索', '连接 RAG 证据库与 GIS 图斑'],
    interview: '我会把向量检索扩展到地理空间对象：影像 patch、图斑属性和文本标签一起入库，用于相似样本挖掘和快速制图。',
    sources: [
      { label: 'AlphaEarth Satellite Embedding dataset', url: 'https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/' }
    ]
  },
  {
    id: 'few_shot_geoai_adaptation',
    name: 'Few-shot GeoAI Adaptation',
    domain: '遥感算法',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 92,
    summary: '利用遥感基础模型、少量标注、主动学习和难例挖掘，把模型快速适配到本地地物类别。',
    why: '真实项目标注永远不够，养殖池塘、水体、排口、工业缺陷都需要少样本快速迭代能力。',
    actions: ['设计主动学习闭环', '标注高不确定样本', '比较 fine-tune、LoRA 和线性探针'],
    interview: '我会用基础模型特征降低标注量，再通过主动学习挑难例，形成少样本适配和持续迭代闭环。',
    sources: [
      { label: 'Prithvi EO 2.0 model card', url: 'https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M' },
      { label: 'Clay Foundation Model GitHub', url: 'https://github.com/Clay-foundation/model' }
    ]
  }
];

let added = 0;
for (const item of additions) {
  if (!seen.has(item.id)) {
    current.push(item);
    seen.add(item.id);
    added += 1;
  }
}

const prefix = 'const knowledgeRadar = ';
const start = source.indexOf(prefix);
const renderMarker = '\nconst radarFilterState =';
const renderStart = source.indexOf(renderMarker, start);
const end = renderStart === -1 ? -1 : source.lastIndexOf('\n]', renderStart);
if (start === -1 || end === -1 || renderStart === -1) {
  throw new Error('Unable to locate knowledgeRadar array boundary');
}

const beforeArray = source.slice(0, start);
const afterArray = source.slice(end + 2);
const nextSource = `${beforeArray}${prefix}${JSON.stringify(current, null, 4)};${afterArray}`;
fs.writeFileSync(path, nextSource, 'utf8');
console.log(JSON.stringify({ added, total: current.length }, null, 2));
