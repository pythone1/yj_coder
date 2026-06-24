const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'mamba_selective_state_space',
    name: 'Mamba / Selective State Space Models',
    domain: '长序列建模',
    horizon: '立即补',
    maturity: '快速升温',
    relevance: 93,
    summary: '用选择性状态空间机制处理长序列依赖，面向长文本、时序信号、遥感序列和边缘推理场景提供 Transformer 之外的路线。',
    why: '你的水质、污水厂、遥感时间序列和传感器数据都存在长序列问题，Mamba/SSM 是面试中能体现前沿敏感度的关键词。',
    actions: ['补一页 SSM vs Transformer 对比卡', '把它纳入时序模型路线图', '标注适合长序列和低延迟推理的场景'],
    interview: 'Mamba 这类 selective SSM 的重点是在线性复杂度下建模长序列，并通过输入相关的选择机制增强表达能力；我会把它作为 Transformer 和 LSTM 之外的长序列候选方案。',
    sources: [
      { label: 'Mamba GitHub', url: 'https://github.com/state-spaces/mamba' }
    ]
  },
  {
    id: 'mamba2_state_space_duality',
    name: 'Mamba-2 / State Space Duality',
    domain: '长序列建模',
    horizon: '下一批',
    maturity: '前沿',
    relevance: 88,
    summary: 'Mamba-2 进一步讨论状态空间模型与注意力机制的结构关联，适合跟踪长上下文、长序列和高吞吐推理方向。',
    why: '如果面试官问前沿模型架构，能从 Mamba 延伸到 Mamba-2，说明你不是只记名词，而是在看架构演进。',
    actions: ['补 Mamba-2 概念卡', '整理 SSD 与 Attention 的差异', '保留为长序列建模进阶知识点'],
    interview: 'Mamba-2 我会作为长序列架构演进来理解：它关注状态空间模型与注意力的结构联系，核心价值是探索更高效的序列建模和推理路径。',
    sources: [
      { label: 'Mamba GitHub', url: 'https://github.com/state-spaces/mamba' }
    ]
  },
  {
    id: 'patchtst_time_series_transformer',
    name: 'PatchTST / Time-series Transformer',
    domain: '时序预测',
    horizon: '立即补',
    maturity: '可实践',
    relevance: 91,
    summary: '把时间序列切成 patch，用 Transformer 做长期预测和表征学习，是工业时序预测中很常见的强 baseline。',
    why: '你的 LSTM 水质预测可以升级为 LSTM、PatchTST、TimesFM/Chronos 的分层对比，简历和作品集表达会更专业。',
    actions: ['加入时序模型 baseline 对比', '用水质数据测试长预测窗口', '记录和 LSTM/LightGBM 的误差差异'],
    interview: 'PatchTST 的思想是借鉴视觉 patch，把连续时序分块后输入 Transformer，减少 token 长度并增强局部模式建模，适合长期预测 baseline。',
    sources: [
      { label: 'PatchTST GitHub', url: 'https://github.com/yuqinie98/PatchTST' }
    ]
  },
  {
    id: 'spatiotemporal_graph_neural_networks',
    name: 'Spatiotemporal Graph Neural Networks',
    domain: '时空智能',
    horizon: '下一批',
    maturity: '可实践',
    relevance: 92,
    summary: '把站点、管网、河网、养殖塘或遥感网格表示为图，并同时建模空间连接和时间演化。',
    why: '断面溯源、管网入流入渗、养殖塘水质联动都天然是时空图问题，比单点时间序列更接近真实业务结构。',
    actions: ['梳理管网/断面/塘口图结构', '补 STGNN 概念卡', '设计一个站点图预测 demo'],
    interview: '时空图模型会把节点的时间变化和边上的空间关系一起建模，适合水网、交通网、站点监测和区域遥感这类有拓扑依赖的数据。',
    sources: [
      { label: 'PyTorch Geometric Temporal', url: 'https://pytorch-geometric-temporal.readthedocs.io/' }
    ]
  },
  {
    id: 'dvc_data_versioning',
    name: 'DVC / Dataset Versioning',
    domain: 'MLOps',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 94,
    summary: '像管理代码一样管理训练数据、遥感样本、标注集、模型文件和实验依赖，保证每次训练可追溯、可复现。',
    why: '你的遥感样本集、Roboflow 数据、养殖池塘图斑和水质时序数据都需要版本化，否则作品集很难体现工程规范。',
    actions: ['给样本集增加版本号规则', '补训练数据来源和变更记录', '规划 DVC/对象存储目录结构'],
    interview: '模型效果不是只由代码决定，数据版本同样关键；我会用 DVC 这类工具记录数据、参数和模型产物，让训练结果可复现。',
    sources: [
      { label: 'DVC documentation', url: 'https://dvc.org/doc' }
    ]
  },
  {
    id: 'mlflow_model_registry',
    name: 'MLflow Model Registry',
    domain: 'MLOps',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 92,
    summary: '集中管理模型版本、指标、参数、制品和阶段流转，支撑从实验到上线的模型治理。',
    why: '商用 AI 软件不只看训练脚本，还看实验记录、模型注册、回滚和上线流程，这正是你项目需要补强的工程层。',
    actions: ['设计模型注册字段', '记录每次训练的指标和数据版本', '补 dev/staging/prod 模型流转说明'],
    interview: '我会把训练产物放进 model registry，记录数据版本、参数、指标和部署阶段，避免模型上线后无法追溯来源或回滚。',
    sources: [
      { label: 'MLflow Model Registry', url: 'https://mlflow.org/docs/latest/ml/model-registry/' }
    ]
  },
  {
    id: 'feast_feature_store',
    name: 'Feast / Feature Store',
    domain: 'MLOps',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 88,
    summary: '统一管理离线训练特征和在线推理特征，避免训练-服务特征不一致，并沉淀可复用特征资产。',
    why: '水质预测、碳源曝气优化、养殖预警都需要时间窗口特征和实时特征，feature store 能把这些能力产品化。',
    actions: ['梳理水质/工艺/遥感特征字典', '区分离线训练与在线推理特征', '补特征复用和特征漂移说明'],
    interview: 'Feature store 解决的是特征复用和训练-服务一致性问题，尤其适合多模型共用水质、工艺、气象和遥感特征的场景。',
    sources: [
      { label: 'Feast documentation', url: 'https://docs.feast.dev/' }
    ]
  },
  {
    id: 'lakehouse_for_ai_geospatial',
    name: 'Lakehouse for AI / Geospatial Data',
    domain: '数据工程',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 89,
    summary: '用 Iceberg/Delta 等表格式管理大规模数据湖，让遥感影像索引、样本表、时序数据和模型结果可查询、可演进。',
    why: '全省养殖池塘、遥感产品、断面溯源和自动报告都需要统一数据底座，lakehouse 是比散落文件更商业化的表达。',
    actions: ['规划影像索引表和样本元数据表', '补数据湖表格式概念卡', '设计结果产品的分区和版本字段'],
    interview: '我会把大规模遥感和时序数据从散文件管理升级为 lakehouse 表格式，重点解决 schema 演进、分区查询、数据血缘和多任务复用。',
    sources: [
      { label: 'Apache Iceberg docs', url: 'https://iceberg.apache.org/' },
      { label: 'Delta Lake docs', url: 'https://docs.delta.io/latest/index.html' }
    ]
  },
  {
    id: 'qdrant_payload_filtering_hnsw',
    name: 'Qdrant / Payload Filtering + HNSW',
    domain: '向量数据库',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 90,
    summary: '在向量相似度检索基础上结合 payload 条件过滤，用于企业知识库、项目材料检索和多条件 RAG 查询。',
    why: '你的求职材料、投标文档、项目证据和养殖知识库需要按项目、时间、来源、可信度过滤，而不是只做纯向量相似。',
    actions: ['给 RAG 文档设计 metadata 字段', '补向量检索过滤概念卡', '规划 Qdrant/Milvus 对比表'],
    interview: '生产 RAG 通常不能只依赖向量近邻，还要结合项目、时间、权限、来源等 payload 过滤，保证检索结果既相关又可控。',
    sources: [
      { label: 'Qdrant documentation', url: 'https://qdrant.tech/documentation/' }
    ]
  },
  {
    id: 'milvus_hybrid_search',
    name: 'Milvus / Hybrid Sparse-Dense Search',
    domain: '向量数据库',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 90,
    summary: '融合稠密向量语义检索和稀疏关键词检索，适合技术文档、招投标材料、项目证据和问答知识库。',
    why: '你的资料中有大量专业名词、地名、指标和项目编号，混合检索比单一 embedding 更适合精准召回。',
    actions: ['补 BM25+dense 混合检索卡', '设计投标文档和简历证据库检索方案', '加入 rerank 评估指标'],
    interview: '技术资料 RAG 我会优先考虑 hybrid search：稀疏检索抓关键词和编号，稠密检索抓语义，再用 rerank 做最终排序。',
    sources: [
      { label: 'Milvus hybrid search docs', url: 'https://milvus.io/docs/hybrid_search_with_milvus.md' }
    ]
  },
  {
    id: 'weaviate_named_vectors',
    name: 'Weaviate / Named Vectors',
    domain: '向量数据库',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 86,
    summary: '同一对象保存多组向量表示，例如标题、正文、图像、项目标签分别向量化，支持更细粒度的多模态检索。',
    why: '你的项目材料同时包含标题、正文、图片、遥感图、表格和证据链接，多向量建模更适合构建专业作品集知识库。',
    actions: ['设计标题/正文/图片多向量 schema', '补 named vectors 概念卡', '评估多向量检索对证据召回的提升'],
    interview: 'Named vectors 让一个文档对象有多个向量视角，比如标题、正文和图片分别检索，适合多模态项目材料和复杂知识库。',
    sources: [
      { label: 'Weaviate named vectors', url: 'https://docs.weaviate.io/weaviate/config-refs/schema/multi-vector' }
    ]
  },
  {
    id: 'langgraph_durable_agent_workflows',
    name: 'LangGraph / Durable Agent Workflows',
    domain: 'Agent 工程',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 95,
    summary: '把 Agent 做成可持久化、可恢复、可插入人工确认的状态机/图工作流，而不是一次性聊天脚本。',
    why: '你的在线简历、知识库、自动报告和求职材料整理都需要可靠流程：读取、判断、生成、校验、人工确认、归档。',
    actions: ['把求职材料处理设计成 graph workflow', '补 human-in-the-loop 节点', '记录每步状态和失败恢复策略'],
    interview: '我会用图工作流把 Agent 拆成可观测节点，关键动作加入人工确认和状态持久化，让它能处理长任务而不是只完成一次回答。',
    sources: [
      { label: 'LangGraph documentation', url: 'https://langchain-ai.github.io/langgraph/' }
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
