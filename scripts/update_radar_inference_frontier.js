const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'vllm_paged_attention',
    name: 'vLLM / PagedAttention',
    domain: '推理系统',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 94,
    summary: '通过把 KV cache 切成非连续 block 管理，降低显存碎片，提高并发吞吐，是开源 LLM Serving 的核心路线之一。',
    why: '你要做商用求职助手和 RAG 平台，后端不能只会调 API，还要知道模型服务如何支撑并发、长上下文和成本控制。',
    actions: ['补 PagedAttention 原理卡', '记录 TTFT/TPOT/吞吐指标', '设计本地 vLLM Serving 实验'],
    interview: '我会把 vLLM 的价值讲成显存管理问题：PagedAttention 让 KV cache 像分页内存一样按需分配，提升多请求并发效率。',
    sources: [
      { label: 'vLLM prefix caching design', url: 'https://docs.vllm.ai/en/stable/design/prefix_caching/' }
    ]
  },
  {
    id: 'automatic_prefix_caching',
    name: 'Automatic Prefix Caching',
    domain: '推理优化',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 93,
    summary: '复用相同系统提示、工具说明、长证据和固定上下文的 KV cache，减少重复 prefill 计算。',
    why: '你的简历、项目证据、知识库和 JD 模板会被反复使用，prefix caching 能直接降低延迟和成本。',
    actions: ['拆分稳定前缀和动态输入', '记录缓存命中率', '给简历证据库设计可缓存 prompt 模板'],
    interview: '我会把上下文分成稳定前缀和动态部分，对稳定的系统提示、证据库说明和简历材料做 prefix caching。',
    sources: [
      { label: 'vLLM automatic prefix caching', url: 'https://docs.vllm.ai/en/stable/design/prefix_caching/' }
    ]
  },
  {
    id: 'sglang_radix_attention',
    name: 'SGLang / RadixAttention',
    domain: '推理系统',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 91,
    summary: 'SGLang 面向结构化多轮 LLM 程序，RadixAttention 复用多次生成调用之间的 KV cache。',
    why: 'Agent、RAG、简历润色和多步骤 JD 分析往往是多轮生成程序，SGLang 这类 runtime 能减少重复计算。',
    actions: ['补 SGLang 程序化生成卡', '比较 vLLM 与 SGLang', '把多步骤简历优化拆成可缓存生成调用'],
    interview: 'SGLang 的价值在于把复杂 LLM 调用变成可编排程序，并用 RadixAttention 复用公共前缀和中间 KV cache。',
    sources: [
      { label: 'SGLang documentation', url: 'https://docs.sglang.ai/' },
      { label: 'SGLang GitHub', url: 'https://github.com/sgl-project/sglang' }
    ]
  },
  {
    id: 'disaggregated_prefill_decode',
    name: 'Disaggregated Prefill/Decode Serving',
    domain: '推理架构',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 90,
    summary: '把长上下文 prefill 和逐 token decode 分离到不同 worker 池，独立扩缩容并转移 KV cache。',
    why: '长简历、长文档 RAG 和多轮 Agent 对 prefill 与 decode 的算力需求不同，分离架构能降低成本并提升吞吐。',
    actions: ['补 prefill/decode 性能差异卡', '画 KV cache 转移链路', '记录适用场景和成本权衡'],
    interview: 'Prefill 是一次性处理长上下文，decode 是逐 token 生成；把二者分离可以按瓶颈独立扩容。',
    sources: [
      { label: 'NVIDIA Dynamo disaggregated serving', url: 'https://docs.nvidia.com/dynamo/v-0-7-1/design-docs/disaggregated-serving' }
    ]
  },
  {
    id: 'lmcache_kv_reuse',
    name: 'LMCache / Persistent KV Cache',
    domain: '推理优化',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 89,
    summary: '把 KV cache 从一次性临时状态变成可跨请求、跨会话、跨引擎复用的缓存层。',
    why: '求职系统会反复读取同一批材料，持久化 KV cache 能服务长上下文 Agent、RAG 和多轮对话。',
    actions: ['补 KV cache 生命周期卡', '区分 GPU/CPU/磁盘分层缓存', '设计证据库长前缀复用实验'],
    interview: 'LMCache 的思路是 prefill once, reuse everywhere，把长上下文的计算结果作为缓存资产复用。',
    sources: [
      { label: 'LMCache documentation', url: 'https://docs.lmcache.ai/' }
    ]
  },
  {
    id: 'kv_aware_routing',
    name: 'KV-aware Routing',
    domain: '推理架构',
    horizon: '下一批',
    maturity: '新兴',
    relevance: 87,
    summary: '路由请求时考虑哪台 worker 已有相关 KV cache，尽量减少重复 prefill 和跨节点传输。',
    why: '多用户、多岗位、多文档场景中，很多请求共享同一简历和项目证据，KV-aware routing 能提高缓存收益。',
    actions: ['设计 session/document affinity', '记录 cache hit/miss', '比较普通负载均衡与 KV-aware 路由'],
    interview: '当 KV cache 成为资源后，路由就不能只看负载，还要看哪台机器已有可复用上下文。',
    sources: [
      { label: 'NVIDIA Dynamo GitHub', url: 'https://github.com/ai-dynamo/dynamo' },
      { label: 'LMCache documentation', url: 'https://docs.lmcache.ai/' }
    ]
  },
  {
    id: 'continuous_batching',
    name: 'Continuous Batching',
    domain: '推理系统',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 88,
    summary: '在生成过程中动态加入和移除请求，避免固定 batch 等待，让不同长度请求共享 GPU 计算。',
    why: '商用 AI 系统请求长度差异很大，连续批处理是提高 GPU 利用率和降低排队延迟的基础手段。',
    actions: ['补动态 batch 调度卡', '记录吞吐和延迟指标', '解释短请求被长请求拖慢的问题'],
    interview: 'Continuous batching 解决的是请求长度不一致导致 GPU 空转的问题，让服务端在生成中动态调度 batch。',
    sources: [
      { label: 'SGLang GitHub runtime features', url: 'https://github.com/sgl-project/sglang' }
    ]
  },
  {
    id: 'structured_generation_runtime',
    name: 'Structured Generation Runtime',
    domain: '结构化输出',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 92,
    summary: '在推理阶段用 grammar、schema、constrained decoding 或 runtime 校验保证输出 JSON、表格、工具参数等结构正确。',
    why: '简历 JSON、JD 解析、知识雷达条目和项目证据必须结构稳定，不能只靠提示词祈祷模型听话。',
    actions: ['为雷达条目定义 JSON schema', '给导入导出加结构校验', '记录模型输出修复策略'],
    interview: '结构化输出要在 runtime 层约束或校验，schema、grammar 和错误重试比单纯 prompt 更可靠。',
    sources: [
      { label: 'SGLang structured outputs', url: 'https://sgl-project.github.io/advanced_features/structured_outputs.html' }
    ]
  },
  {
    id: 'llm_slo_cost_governance',
    name: 'LLM SLO / Cost Governance',
    domain: '工程运维',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 91,
    summary: '用 TTFT、TPOT、吞吐、错误率、缓存命中率、每任务成本和成功率定义 LLM 应用服务目标。',
    why: '商用求职系统需要可控成本和稳定体验，不能只说模型效果好，还要能讲延迟、成本、缓存和失败率。',
    actions: ['定义雷达/简历/JD 分析 SLO', '记录 token 与调用成本', '按任务路由快慢模型'],
    interview: '我会把 LLM 应用按任务定义 SLO：首 token 延迟、总耗时、成功率、每次任务成本和缓存命中率都要监控。',
    sources: [
      { label: 'OpenTelemetry GenAI semantic conventions', url: 'https://opentelemetry.io/docs/specs/semconv/gen-ai/' },
      { label: 'vLLM metrics docs', url: 'https://docs.vllm.ai/en/stable/serving/metrics.html' }
    ]
  },
  {
    id: 'quantized_llm_serving',
    name: 'Quantized LLM Serving',
    domain: '模型压缩',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 86,
    summary: '用 FP8、INT4、AWQ、GPTQ 等量化方式降低显存和成本，在精度、速度和部署门槛之间做权衡。',
    why: '本地或私有化部署求职助手、RAG 和小模型分类时，量化是降低硬件成本的重要手段。',
    actions: ['补量化格式对比卡', '区分权重量化和 KV cache 量化', '记录精度损失与吞吐收益'],
    interview: '量化不是越低比特越好，要看任务精度、显存、吞吐、延迟和模型兼容性，必要时保留关键模块精度。',
    sources: [
      { label: 'SGLang quantization support', url: 'https://github.com/sgl-project/sglang' }
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
