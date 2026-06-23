const fs = require('fs');
const vm = require('vm');

const path = 'js/radar.js';
const source = fs.readFileSync(path, 'utf8');
const ctx = { window: {} };
const current = vm.runInNewContext(`${source}\nknowledgeRadar;`, ctx);
const seen = new Set(current.map((item) => item.id));

const additions = [
  {
    id: 'deep_agents_harness',
    name: 'Deep Agents / Agent Harness',
    domain: 'Agent 工程',
    horizon: '立即补',
    maturity: '快速落地',
    relevance: 96,
    summary: '把工具调用循环升级为带规划、虚拟文件系统、子代理、长期记忆、权限和人工确认的 Agent 外骨架。',
    why: '你的求职软件已经有简历、证据库、知识雷达、导出和Git同步，下一步正适合做成多步 Agent 工作台，而不是单个聊天入口。',
    actions: ['设计任务清单与状态机', '增加文件证据工作区', '为高风险动作设置人工确认'],
    interview: '我会把 Agent 看成 harness：工具、文件系统、记忆、子代理、权限、trace 和人工确认组合起来，才能支撑真实多步任务。',
    sources: [
      { label: 'LangChain Deep Agents overview', url: 'https://docs.langchain.com/oss/python/deepagents/overview' }
    ]
  },
  {
    id: 'agent_handoffs',
    name: 'Agent Handoffs / Specialist Routing',
    domain: 'Agent 编排',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 94,
    summary: '由一个分诊 Agent 判断任务类型，再把上下文转交给简历、JD、作品集、知识库或Git同步等专门 Agent。',
    why: '商用求职助手不能把所有事塞给一个大提示词，必须按任务边界拆分专业角色并控制移交上下文。',
    actions: ['定义简历/JD/作品集/同步四类专员', '记录 handoff reason', '限制接收方可见上下文'],
    interview: '我会使用 handoff 模式做专家路由：分诊 Agent 只负责判断去向，专门 Agent 负责执行，并记录移交原因和上下文过滤规则。',
    sources: [
      { label: 'OpenAI Agents SDK handoffs', url: 'https://openai.github.io/openai-agents-python/handoffs/' }
    ]
  },
  {
    id: 'agent_tool_guardrails',
    name: 'Tool Guardrails / Tripwires',
    domain: 'AI 安全',
    horizon: '立即补',
    maturity: '生产化',
    relevance: 95,
    summary: '在工具调用前后设置输入、输出、权限和越界检测，触发 tripwire 时中止或转人工确认。',
    why: '后续如果做自动投递、改简历、推Git、读E盘文件，必须防止 prompt injection 和越权操作。',
    actions: ['为写文件/推送/外发动作加确认', '给工具输入定义 schema', '记录触发拦截的原因'],
    interview: '我不会让模型直接决定高风险动作，而是在工具边界加 schema、权限、guardrail 和 tripwire，必要时转人工确认。',
    sources: [
      { label: 'OpenAI Agents SDK guardrails', url: 'https://openai.github.io/openai-agents-python/guardrails/' }
    ]
  },
  {
    id: 'mcp_roots_elicitation_sampling',
    name: 'MCP Roots / Elicitation / Sampling',
    domain: '协议生态',
    horizon: '立即补',
    maturity: '快速标准化',
    relevance: 93,
    summary: 'MCP 不只是 tools，还包括 roots、elicitation、sampling、resources、prompts 等能力边界和交互机制。',
    why: '你本地项目大量依赖文件、文档、工具和外部数据，理解 MCP 的能力协商和安全边界会显著提升面试表达。',
    actions: ['补充 MCP 能力矩阵卡', '区分 tools/resources/prompts', '给本地文件访问标注 roots 边界'],
    interview: 'MCP 的关键不是“接工具”三个字，而是标准化上下文、工具、资源、提示词、能力协商和用户授权边界。',
    sources: [
      { label: 'MCP 2025-06-18 specification', url: 'https://modelcontextprotocol.io/specification/2025-06-18' }
    ]
  },
  {
    id: 'virtual_filesystem_agents',
    name: 'Virtual Filesystem for Agents',
    domain: 'Agent 工程',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 91,
    summary: '给 Agent 一个受控的虚拟文件系统，用于存放中间结果、长文档摘要、草稿、证据片段和任务状态。',
    why: '简历编辑器、证据说明、Markdown/JSON 导出都天然适合文件化；虚拟FS能降低上下文爆炸和误覆盖风险。',
    actions: ['建立 workspace/artifacts 约定', '把长证据转文件引用', '区分只读证据和可写草稿'],
    interview: '复杂 Agent 不能只靠上下文窗口硬扛，我会把中间结果和证据放入受控文件系统，再由模型按需读取。',
    sources: [
      { label: 'LangChain Deep Agents filesystem', url: 'https://docs.langchain.com/oss/python/deepagents/overview' }
    ]
  },
  {
    id: 'agent_permission_policy',
    name: 'Agent Permission Policy',
    domain: 'AI 安全',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 92,
    summary: '用声明式权限控制 Agent 可读、可写、可执行、可联网、可外发的范围，把能力变成可审计策略。',
    why: '本机有大量个人文档和项目代码，求职助手必须做到默认只读、明确授权、外发前确认。',
    actions: ['定义 read/write/send 三类权限', '高风险动作默认人工确认', '把权限策略展示到设置页'],
    interview: '我会把 Agent 权限当成工程配置：哪些路径只读、哪些工具可执行、哪些动作必须确认，而不是只靠提示词约束。',
    sources: [
      { label: 'Deep Agents permissions', url: 'https://docs.langchain.com/oss/python/deepagents/permissions' },
      { label: 'MCP security principles', url: 'https://modelcontextprotocol.io/specification/2025-06-18#security-and-trust-safety' }
    ]
  },
  {
    id: 'sandboxed_computer_use',
    name: 'Sandboxed Computer Use',
    domain: '自动化执行',
    horizon: '下一批',
    maturity: '快速落地',
    relevance: 89,
    summary: '让模型在受控沙箱里读写文件、执行命令或操作浏览器，减少对真实系统的误操作风险。',
    why: '你的软件后续可能做自动投递、网页抓取、简历导出和仓库同步，沙箱化能把效率和安全同时抬起来。',
    actions: ['把自动化动作放入沙箱', '保留执行日志和产物', '危险操作先预演再确认'],
    interview: '我会把 computer use 放进 sandbox：先限定文件系统、网络和命令权限，再让 Agent 执行，并把日志用于复盘。',
    sources: [
      { label: 'Deep Agents sandboxes', url: 'https://docs.langchain.com/oss/python/deepagents/overview' },
      { label: 'OpenAI Agents SDK sandbox agents', url: 'https://openai.github.io/openai-agents-python/' }
    ]
  },
  {
    id: 'agent_event_streaming',
    name: 'Agent Event Streaming',
    domain: '用户体验',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 88,
    summary: '把 Agent 的计划、工具调用、文件读写、子任务和最终结果以事件流方式展示，避免用户面对黑箱等待。',
    why: '商用软件要让用户知道系统在做什么，尤其是简历修改、证据检索、Git同步这类长任务。',
    actions: ['设计任务事件面板', '展示当前步骤和耗时', '失败时给出可恢复动作'],
    interview: '我会把 Agent 运行过程流式化：计划、工具调用、读写文件、失败重试和人工确认都可见，用户才敢用。',
    sources: [
      { label: 'Deep Agents event streaming', url: 'https://docs.langchain.com/oss/python/deepagents/overview' },
      { label: 'OpenAI Agents SDK streaming', url: 'https://openai.github.io/openai-agents-python/' }
    ]
  },
  {
    id: 'prompt_caching_strategy',
    name: 'Prompt Caching Strategy',
    domain: '成本优化',
    horizon: '下一批',
    maturity: '生产化',
    relevance: 87,
    summary: '把稳定系统提示、长简历、项目证据、JD模板等前缀缓存起来，降低重复调用延迟和成本。',
    why: '求职系统会反复使用同一批简历、项目证据和知识库，缓存策略比每次全量塞上下文更适合商用。',
    actions: ['标记稳定上下文块', '拆分高复用前缀和动态请求', '统计缓存命中率'],
    interview: '我会把上下文拆成稳定前缀和动态输入，对稳定的简历/证据/JD框架做 prompt caching，优化延迟和成本。',
    sources: [
      { label: 'Deep Agents context management', url: 'https://docs.langchain.com/oss/python/deepagents/overview' }
    ]
  },
  {
    id: 'agent_primitives',
    name: 'Agent Primitives: Plan / Act / Observe / Evaluate',
    domain: 'Agent 工程',
    horizon: '立即补',
    maturity: '基础范式',
    relevance: 97,
    summary: '把 Agent 能力拆成计划、行动、观察、评估、记忆、权限和人工确认等原语，支撑 Loop Engineering。',
    why: 'Loop Engineering 已经收录，但还需要把底层工程原语拆清楚，方便面试时从概念讲到实现。',
    actions: ['给 Loop Engineering 增加原语图', '把简历优化流程拆成循环', '为每步定义失败处理'],
    interview: '我会从 Agent primitives 解释工程化：Plan 定目标，Act 调工具，Observe 收集结果，Evaluate 打分，Memory 沉淀，Guardrail 管边界。',
    sources: [
      { label: 'LangGraph durable agents', url: 'https://langchain-ai.github.io/langgraph/' },
      { label: 'OpenAI Agents SDK', url: 'https://openai.github.io/openai-agents-python/' }
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
