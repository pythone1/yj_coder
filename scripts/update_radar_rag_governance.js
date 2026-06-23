const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'dspy_prompt_compilation',
    name: 'DSPy / Prompt Compilation',
    domain: '评测驱动优化',
    horizon: '立即补',
    maturity: '快速落地',
    relevance: 92,
    summary: '把 prompt 手工调参升级为“程序 + 示例集 + 指标”的自动优化，用优化器搜索更高分的指令和示例。',
    why: '你的简历润色、项目证据提取、JD 匹配和雷达收录都可以用小样本评测集驱动 prompt 迭代，而不是凭感觉改词。',
    actions: ['为简历润色建 20 条训练样例', '定义事实准确率和岗位匹配指标', '用 DSPy 优化 RAG/分类 prompt'],
    interview: '我会把 prompt 当成可编译资产：给出训练样例和 metric，让 DSPy 这类优化器自动搜索更稳的指令和示例组合。',
    sources: [
      { label: 'DSPy GEPA optimization', url: 'https://dspy.ai/getting-started/gepa-optimization/' },
      { label: 'DSPy docs', url: 'https://dspy.ai/' }
    ]
  },
  {
    id: 'ragas_component_metrics',
    name: 'Ragas Component Metrics',
    domain: 'RAG 评测',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 94,
    summary: '用 context precision、context recall、faithfulness、response relevancy 等指标分别评估检索器和生成器。',
    why: '项目证据库和简历生成最怕“看起来很顺但证据不支持”，Ragas 指标能把问题拆到检索、排序、回答三个环节。',
    actions: ['为项目证据库建立 RAGAS 评测集', '分别记录 context precision 和 faithfulness', '失败样例回流到切片/重排策略'],
    interview: 'RAG 评测不能只看最终答案，要拆成检索是否找对、排序是否靠前、回答是否忠实证据、语言是否相关。',
    sources: [
      { label: 'Ragas metrics list', url: 'https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/' },
      { label: 'Ragas faithfulness', url: 'https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/' }
    ]
  },
  {
    id: 'hybrid_search_rrf_rerank',
    name: 'Hybrid Search + RRF + Rerank',
    domain: '检索系统',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 91,
    summary: '结合 BM25 关键词检索、向量检索、RRF 融合和 cross-encoder 重排，提高术语、编号、路径和语义检索的综合召回。',
    why: '你的文档里有大量项目名、路径、指标、中文术语和英文技术词，纯向量或纯关键词都容易漏召回。',
    actions: ['为证据库加 BM25 + embedding 双路检索', '实现 RRF 融合', '对 top50 做 rerank'],
    interview: '我会用 hybrid search 解决术语和语义的双重召回问题，再用 reranker 提升 top-k 精度。',
    sources: [
      { label: 'LangChain retrieval docs', url: 'https://docs.langchain.com/oss/python/langchain/retrieval' },
      { label: 'Elasticsearch hybrid search in LangChain', url: 'https://www.elastic.co/search-labs/blog/langchain-elasticsearch-hybrid-search' }
    ]
  },
  {
    id: 'colpali_visual_document_retrieval',
    name: 'ColPali / Visual Document Retrieval',
    domain: '多模态检索',
    horizon: '立即补',
    maturity: '快速落地',
    relevance: 90,
    summary: '直接把 PDF 页面作为图像编码检索，利用 VLM 和 late interaction 处理表格、图件、版式和扫描文档。',
    why: '你有大量投标文件、汇报 PDF、图件和扫描式材料，传统 OCR + 文本切片会丢失版式与图表信息。',
    actions: ['选一份投标 PDF 做视觉检索 demo', '比较 OCR RAG 与 ColPali RAG', '保留页图和引用区域'],
    interview: '对于图表密集的 PDF，我会考虑 ColPali 这类视觉文档检索，直接检索页面图像特征，而不是只依赖 OCR 文本。',
    sources: [
      { label: 'ColPali GitHub', url: 'https://github.com/illuin-tech/colpali' },
      { label: 'ColPali Hugging Face blog', url: 'https://huggingface.co/blog/manu/colpali' }
    ]
  },
  {
    id: 'late_interaction_retrieval',
    name: 'Late Interaction Retrieval / ColBERT',
    domain: '检索系统',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 86,
    summary: '保留 query 与文档 token 级交互，而不是压成单个向量，兼顾语义细粒度和可扩展检索。',
    why: '技术文档和岗位 JD 里很多细节靠单向量会被平均掉，late interaction 更适合找精确术语和上下文。',
    actions: ['补 ColBERT/ColPali 对比卡', '标记适合 late interaction 的长文档场景', '评估索引成本和召回收益'],
    interview: 'Late interaction 的价值是避免把整段文本压成一个向量，保留 token 级匹配能力，适合细粒度技术检索。',
    sources: [
      { label: 'ColPali GitHub', url: 'https://github.com/illuin-tech/colpali' }
    ]
  },
  {
    id: 'llm_judge_calibration',
    name: 'LLM-as-Judge Calibration',
    domain: '评测体系',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 89,
    summary: '用标注样本、rubric、一致性检查和人工抽检校准 LLM 评审，避免模型评测自嗨。',
    why: '简历质量、项目表述真实性、JD 匹配度都可能用 LLM 评分，但评分器本身必须被校准。',
    actions: ['为简历评分建立人工 gold set', '固定 rubric 与反例', '监控评审一致性和偏差'],
    interview: 'LLM-as-judge 要有 gold set、rubric、pairwise 对比和人工抽检，否则评分只是另一个不稳定模型输出。',
    sources: [
      { label: 'LangSmith evaluation concepts', url: 'https://docs.langchain.com/langsmith/evaluation-concepts' },
      { label: 'OpenAI Evals', url: 'https://github.com/openai/evals' }
    ]
  },
  {
    id: 'active_learning_data_engine',
    name: 'Active Learning Data Engine',
    domain: '数据闭环',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 90,
    summary: '把低置信度、误检、冲突样本和用户反馈回流到标注、训练、评测和再部署流程。',
    why: '遥感分割、目标检测、RAG 证据检索和简历生成都会持续遇到难例，主动学习能让系统越用越准。',
    actions: ['建立错误样本池', '按不确定性挑样本', '记录样本版本和模型版本'],
    interview: '我会把模型上线后的错误样本和人工反馈变成数据引擎，用主动学习挑最有价值的样本去标注和再训练。',
    sources: [
      { label: 'Label Studio active learning guide', url: 'https://labelstud.io/guide/active_learning' }
    ]
  },
  {
    id: 'synthetic_eval_dataset',
    name: 'Synthetic Eval Dataset Generation',
    domain: '评测体系',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 87,
    summary: '用模型辅助生成边界问题、反例、困难样例和多样化查询，再由人工或规则筛选成评测集。',
    why: '求职系统场景多、真实失败样本少，合成评测能快速覆盖 JD 歧义、证据错配、幻觉和格式错误。',
    actions: ['生成 JD/简历/证据错配样例', '人工审核合成样本', '把失败样本沉淀为回归集'],
    interview: '我会用合成数据扩展评测覆盖面，但关键样本必须人工审核，避免把模型的偏差复制进评测集。',
    sources: [
      { label: 'Ragas testset generation docs', url: 'https://docs.ragas.io/en/stable/concepts/test_data_generation/' }
    ]
  },
  {
    id: 'model_data_cards_lineage',
    name: 'Model Cards / Data Cards / Lineage',
    domain: '模型治理',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 88,
    summary: '为模型、数据集、评测集、限制条件和适用场景建立文档与血缘，方便审计、交接和复现。',
    why: '你的项目横跨遥感、水处理、养殖和 RAG，只有把数据来源、模型版本和评测记录写清楚，作品集才更可信。',
    actions: ['为雷达/简历/作品集数据建 data card', '记录模型版本和训练数据', '把评测结果写入变更记录'],
    interview: '我会给模型和数据都建 card：来源、版本、适用范围、限制、评测指标和已知风险都要可追溯。',
    sources: [
      { label: 'Hugging Face model cards', url: 'https://huggingface.co/docs/hub/model-cards' },
      { label: 'Hugging Face dataset cards', url: 'https://huggingface.co/docs/hub/datasets-cards' }
    ]
  },
  {
    id: 'ai_supply_chain_provenance',
    name: 'AI Supply Chain Provenance',
    domain: 'AI 安全',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 86,
    summary: '追踪模型、数据、依赖、权重、许可证、构建过程和部署产物来源，降低供应链和合规风险。',
    why: '后续接入开源模型、遥感数据和自动化工具时，必须知道权重、数据和依赖是否可信、可用、可商用。',
    actions: ['记录模型许可证和来源', '为依赖生成清单', '给外部模型加入安全与合规检查'],
    interview: 'AI 供应链治理要追踪模型权重、数据来源、依赖版本、许可证和构建过程，避免把不可控资产带进生产系统。',
    sources: [
      { label: 'SLSA framework', url: 'https://slsa.dev/' },
      { label: 'CycloneDX ML-BOM', url: 'https://cyclonedx.org/capabilities/mlbom/' }
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
