const knowledgeRadar = [
    {
        id: "loop_engineering",
        name: "Loop Engineering",
        domain: "Agent 工程",
        horizon: "立即补",
        maturity: "新兴",
        relevance: 98,
        summary: "围绕“生成-执行-观察-评估-修正”的闭环设计 Agent，而不是只写一次 prompt。",
        why: "商用 Agent 的关键不再是单轮回答，而是能持续读取状态、调用工具、评估结果、回滚错误并进入下一轮。",
        actions: ["补一页知识卡", "设计一个求职材料优化 loop", "在面试中用它解释 Agent 工程化能力"],
        interview: "我会把 Agent 设计成闭环系统：Planner 生成计划，Executor 调工具，Observer 收集结果，Evaluator 打分，Controller 决定继续、回滚或交给人工。",
        sources: [
            { label: "LangGraph durable agents", url: "https://langchain-ai.github.io/langgraph/" },
            { label: "DSPy optimization", url: "https://dspy.ai/" }
        ]
    },
    {
        id: "context_engineering",
        name: "Context Engineering",
        domain: "LLM 应用",
        horizon: "立即补",
        maturity: "快速升温",
        relevance: 97,
        summary: "系统化管理模型上下文：指令、工具、记忆、检索证据、用户状态和任务轨迹。",
        why: "长上下文不是把所有材料塞进去，真正难点是选择、压缩、排序、隔离和刷新上下文。",
        actions: ["把简历/JD/作品集做成上下文包", "新增上下文预算字段", "给 RAG 面试答案加入上下文治理话术"],
        interview: "我会把 prompt 工程升级为 context engineering：先定义上下文来源，再做优先级、token 预算、证据隔离和过期策略。",
        sources: [
            { label: "LangGraph memory", url: "https://langchain-ai.github.io/langgraph/concepts/memory/" },
            { label: "LlamaIndex docs", url: "https://docs.llamaindex.ai/" }
        ]
    },
    {
        id: "agentops",
        name: "AgentOps / Agent Observability",
        domain: "工程运维",
        horizon: "立即补",
        maturity: "生产化",
        relevance: 95,
        summary: "为 Agent 增加 trace、工具调用日志、成本、延迟、失败率和人工接管记录。",
        why: "面试中讲 Agent 项目时，能讲可观测性会明显区别于只会 demo 的候选人。",
        actions: ["设计 trace 字段", "在 JD 匹配模块预留执行日志", "补充失败案例复盘模板"],
        interview: "Agent 上线必须记录每一步：模型输入输出、工具参数、返回值、耗时、成本、错误、重试和人工确认。",
        sources: [
            { label: "LangSmith observability", url: "https://docs.smith.langchain.com/" },
            { label: "OpenAI Agents tracing", url: "https://openai.github.io/openai-agents-python/tracing/" }
        ]
    },
    {
        id: "evalops",
        name: "EvalOps / LLM Evaluation",
        domain: "评测体系",
        horizon: "立即补",
        maturity: "生产化",
        relevance: 96,
        summary: "为 LLM/RAG/Agent 建立离线评测集、在线回归测试和人工评分闭环。",
        why: "AI 应用真正可交付，靠的是评测集、红线样例、回归测试和指标趋势，不是几条好看的回答。",
        actions: ["为简历润色建 20 条评测样例", "为 RAG 建证据一致性评分", "为面试训练建评分 rubric"],
        interview: "我会把 AI 功能按任务拆评测：准确性、证据一致性、格式合规、拒答边界、延迟和成本都要进回归测试。",
        sources: [
            { label: "OpenAI Evals", url: "https://github.com/openai/evals" },
            { label: "RAGAS", url: "https://docs.ragas.io/" }
        ]
    },
    {
        id: "guardrails",
        name: "Guardrails / Structured Validation",
        domain: "AI 安全",
        horizon: "立即补",
        maturity: "生产化",
        relevance: 92,
        summary: "对模型输出做结构、类型、事实、权限和安全约束，避免自由文本直接进入业务系统。",
        why: "求职系统后续会生成简历、邮件、PPT 和岗位分析，必须校验格式、事实和敏感信息。",
        actions: ["为 JD 解析定义 JSON schema", "为简历 bullet 做事实一致性检查", "高风险改写加人工确认"],
        interview: "我不会让模型自由输出直接落库，而会用 schema、校验器、敏感词规则和人工确认保护关键流程。",
        sources: [
            { label: "Guardrails AI", url: "https://www.guardrailsai.com/docs" },
            { label: "OpenAI structured outputs", url: "https://platform.openai.com/docs/guides/structured-outputs" }
        ]
    },
    {
        id: "human_in_the_loop",
        name: "Human-in-the-Loop Agent",
        domain: "Agent 工程",
        horizon: "立即补",
        maturity: "生产化",
        relevance: 94,
        summary: "在高风险步骤暂停，等待人工确认、编辑或审批，再继续执行。",
        why: "求职材料、投递邮件、文件操作都属于需要人确认的动作，不能全自动黑箱执行。",
        actions: ["为投递动作增加确认点", "为简历改写增加 diff 预览", "记录人工审批原因"],
        interview: "我会按风险分层：低风险自动执行，高风险暂停给人确认，所有确认都写入审计日志。",
        sources: [
            { label: "LangGraph human-in-the-loop", url: "https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/" }
        ]
    },
    {
        id: "mcp_a2a",
        name: "MCP + A2A 协议栈",
        domain: "Agent 生态",
        horizon: "已收录",
        maturity: "标准化",
        relevance: 94,
        summary: "MCP 连接工具和上下文，A2A 连接不同 Agent，是多 Agent 工作流的协议基础。",
        why: "后续岗位库、简历库、知识库、浏览器和文件系统都可以按工具能力接入。",
        actions: ["保留到知识库", "设计本地工具清单", "把作品集/JD/简历作为资源源"],
        interview: "MCP 是模型到工具，A2A 是 Agent 到 Agent；我会把权限、schema 和审计作为协议落地的重点。",
        sources: [
            { label: "Model Context Protocol", url: "https://modelcontextprotocol.io/docs/getting-started/intro" },
            { label: "Google A2A", url: "https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/" }
        ]
    },
    {
        id: "graph_rag",
        name: "GraphRAG / Agentic RAG",
        domain: "知识增强",
        horizon: "已收录",
        maturity: "快速落地",
        relevance: 93,
        summary: "把向量召回升级为实体、关系、社区摘要和多步检索规划。",
        why: "你的项目证据分散在 E 盘多个目录，天然适合从文件证据图谱做项目问答和简历生成。",
        actions: ["把项目-技术-指标建关系图", "生成岗位到项目映射", "为作品集增加关联知识点"],
        interview: "普通 RAG 更像片段检索，GraphRAG 能处理跨项目、跨实体和全局摘要问题。",
        sources: [
            { label: "Microsoft GraphRAG", url: "https://microsoft.github.io/graphrag/" }
        ]
    },
    {
        id: "memory_systems",
        name: "Long-term Memory for Agents",
        domain: "Agent 工程",
        horizon: "下一批",
        maturity: "快速升温",
        relevance: 91,
        summary: "把用户偏好、历史任务、项目证据和失败案例沉淀为可检索、可更新、可遗忘的长期记忆。",
        why: "你的求职系统需要记住岗位偏好、项目讲法、投递记录和反复出错的表达。",
        actions: ["定义记忆类型", "增加更新时间和可信度", "区分事实/推断/偏好"],
        interview: "Agent 记忆不是简单聊天记录，而是分层存储：事实、偏好、任务状态、技能画像和审计记录。"
    },
    {
        id: "prompt_optimization",
        name: "Prompt Optimization / DSPy",
        domain: "LLM 应用",
        horizon: "下一批",
        maturity: "快速升温",
        relevance: 89,
        summary: "用数据和评测自动优化 prompt、示例和模块组合，而不是手工玄学调参。",
        why: "简历润色、JD 解析、面试评分都可以变成可优化的语言程序。",
        actions: ["为简历改写建输入输出样例", "用评测分数驱动提示词迭代", "记录 prompt 版本"],
        interview: "我会把 prompt 当成可评测、可版本化、可优化的程序组件，而不是一次性的文本。"
    },
    {
        id: "reasoning_control",
        name: "Reasoning Control / Test-Time Compute",
        domain: "推理优化",
        horizon: "已收录",
        maturity: "快速落地",
        relevance: 90,
        summary: "按任务风险增加多候选、验证器、反思和选择步骤，换取更高正确率。",
        why: "投递材料和技术答辩属于高价值任务，适合启用更强的推理控制。",
        actions: ["为关键输出增加二次审查", "设置速度/质量模式", "记录验证理由"],
        interview: "我会按风险使用 test-time compute：普通问答快速生成，关键结论多候选加验证器。"
    },
    {
        id: "vibe_to_spec",
        name: "Vibe Coding 到 Spec-Driven Development",
        domain: "软件工程",
        horizon: "下一批",
        maturity: "新兴",
        relevance: 88,
        summary: "AI 辅助开发从随口生成代码，走向需求、验收、测试和变更记录驱动。",
        why: "这个软件会越来越大，必须避免脚本堆叠，进入模块化、测试化和规格化建设。",
        actions: ["为每个模块写验收标准", "建立 smoke test", "拆分 app.js/resume.js"],
        interview: "AI 编程不能只看生成速度，必须有 spec、测试、代码审查和回归验证来保证长期可维护。"
    },
    {
        id: "llm_security",
        name: "Prompt Injection / Tool Sandbox",
        domain: "AI 安全",
        horizon: "已收录",
        maturity: "生产化",
        relevance: 92,
        summary: "防止网页、JD、文档或检索内容诱导模型越权、泄露信息或执行危险工具。",
        why: "岗位 JD 和网页内容都是不可信输入，后续如果接浏览器和文件工具必须有沙箱。",
        actions: ["标记外部内容不可信", "工具最小权限", "敏感动作二次确认"],
        interview: "我会把外部文本视为数据而不是指令，工具调用必须经过权限和参数校验。"
    },
    {
        id: "multimodal_rag",
        name: "Multimodal RAG",
        domain: "多模态",
        horizon: "下一批",
        maturity: "快速落地",
        relevance: 87,
        summary: "同时检索文本、图片、表格、PPT、PDF 截图和视觉特征，生成带证据的回答。",
        why: "你的项目资料里有 PPT、图表、遥感/视觉结果，不能只做纯文本 RAG。",
        actions: ["抽取 PPT/PDF 图片证据", "给作品集增加截图证据", "设计多模态引用格式"],
        interview: "多模态 RAG 要解决图片、表格和文本的统一索引，以及回答时的证据定位。"
    },
    {
        id: "geo_foundation",
        name: "Geospatial Foundation Models",
        domain: "遥感 AI",
        horizon: "已收录",
        maturity: "快速落地",
        relevance: 90,
        summary: "Prithvi、TerraTorch 等把遥感任务推向预训练-微调的基础模型范式。",
        why: "与你的遥感/GIS 求职方向高度相关，是区别普通 CV 候选人的关键词。",
        actions: ["补充遥感基础模型对比表", "关联 Geospatial-AI-Ecosystem", "增加面试问答"],
        interview: "遥感基础模型不同于通用 CV，核心差异是多光谱、时序、CRS、分辨率和跨区域泛化。",
        sources: [
            { label: "Prithvi-EO-2.0", url: "https://github.com/NASA-IMPACT/Prithvi-EO-2.0" },
            { label: "TerraTorch", url: "https://github.com/IBM/terratorch" }
        ]
    },
    {
        id: "vlm_vla",
        name: "VLM / VLA / Computer Use",
        domain: "多模态",
        horizon: "下一批",
        maturity: "快速升温",
        relevance: 88,
        summary: "从看图问答扩展到视觉理解、界面操作、动作规划和机器人控制。",
        why: "工业视觉、UWB+YOLO、遥感解译都可以用 VLM/VLA 话术升级表达。",
        actions: ["为工业视觉项目补 VLM 版本表达", "增加界面操作 Agent 知识点", "关联 OpenVLA"],
        interview: "VLM 负责视觉语义理解，VLA 进一步输出动作；生产系统仍要传感器冗余和安全边界。"
    },
    {
        id: "inference_systems",
        name: "LLM Inference Systems",
        domain: "推理优化",
        horizon: "下一批",
        maturity: "生产化",
        relevance: 86,
        summary: "围绕 KV cache、continuous batching、speculative decoding、量化和并行策略优化推理服务。",
        why: "AI 工程岗位越来越看重部署成本、延迟和吞吐，不只看模型调用。",
        actions: ["把 MLA/GQA/KV cache 做成专题", "补充吞吐/延迟面试题", "整理 vLLM/SGLang 概念"],
        interview: "推理服务优化要同时看模型结构、KV cache、batch 调度、量化、并行和业务延迟预算。"
    },
    {
        id: "synthetic_data",
        name: "Synthetic Data / Data Flywheel",
        domain: "数据闭环",
        horizon: "下一批",
        maturity: "快速落地",
        relevance: 84,
        summary: "用模型生成、筛选、评测和人工确认的数据持续增强任务能力。",
        why: "面试题、简历样例、JD 样例都可以形成数据飞轮，越用越准。",
        actions: ["沉淀 JD 样例库", "沉淀面试问答样例", "建立人工审核标签"],
        interview: "AI 产品要有数据飞轮：真实使用数据、人工反馈、合成扩充和回归评测共同推动迭代。"
    },
    {
        id: "llm_gateway_routing",
        name: "LLM Gateway / Model Routing",
        domain: "工程架构",
        horizon: "立即补",
        maturity: "生产化",
        relevance: 93,
        summary: "在多个模型、供应商和成本档位之间做路由、降级、重试、预算和审计。",
        why: "商用 AI 应用不会只绑一个模型。岗位 JD 匹配、简历润色、面试训练可按任务难度选择快模型、强模型或本地模型。",
        actions: ["设计模型路由策略", "区分速度/质量/成本模式", "给关键任务增加 fallback"],
        interview: "我会在业务层前面加 LLM Gateway：统一鉴权、限流、模型路由、预算、重试、fallback 和日志，避免应用代码直接耦合某个模型。",
        sources: [
            { label: "LiteLLM routing", url: "https://docs.litellm.ai/docs/routing" }
        ]
    },
    {
        id: "opentelemetry_genai",
        name: "OpenTelemetry GenAI Observability",
        domain: "工程运维",
        horizon: "立即补",
        maturity: "生产化",
        relevance: 91,
        summary: "用标准化 telemetry 记录模型请求、token、延迟、工具调用和错误，打通 AI 应用监控。",
        why: "AgentOps 需要落到标准日志和指标，OpenTelemetry GenAI 语义约定正在成为跨平台可观测性的共同语言。",
        actions: ["为后端预留 trace id", "记录 token/latency/cost", "把工具调用纳入 span"],
        interview: "我会用 OpenTelemetry 思路记录 GenAI 调用：模型名、输入输出规模、token、延迟、错误、工具调用链和用户会话，便于线上排障。",
        sources: [
            { label: "OpenTelemetry GenAI", url: "https://opentelemetry.io/docs/specs/semconv/gen-ai/" }
        ]
    },
    {
        id: "swe_agents",
        name: "SWE Agents / Coding Agents",
        domain: "软件工程",
        horizon: "立即补",
        maturity: "快速落地",
        relevance: 92,
        summary: "面向真实代码库的自动定位、修改、测试和提交工作流，评估基准从 toy task 转向真实 issue。",
        why: "你这个软件后续会模块化，AI coding agent 的能力可以用于重构、测试生成和回归修复。",
        actions: ["建立 smoke test", "拆分大文件前写验收", "用 issue/patch 思路管理改动"],
        interview: "我会把 coding agent 当成协作开发者：先读仓库、制定 patch、跑测试、解释风险，而不是直接生成孤立代码。",
        sources: [
            { label: "SWE-bench", url: "https://www.swebench.com/" }
        ]
    },
    {
        id: "swe_bench_verified",
        name: "SWE-bench Verified / Real-world Eval",
        domain: "评测体系",
        horizon: "下一批",
        maturity: "生产化",
        relevance: 86,
        summary: "用真实 GitHub issue 和人工验证子集评估软件工程 Agent 的修复能力。",
        why: "这能帮助你在面试中区分“AI 会写代码”和“AI 能在真实仓库里解决问题”。",
        actions: ["把本项目任务写成 issue", "为每个功能写验收测试", "记录 agent 修复成功率"],
        interview: "SWE-bench 类评测的价值在于真实代码上下文、真实失败测试和可验证 patch，比单文件算法题更接近工程岗位。"
    },
    {
        id: "rlvr_grpo",
        name: "RLVR / GRPO / Verifiable Rewards",
        domain: "训练范式",
        horizon: "下一批",
        maturity: "快速升温",
        relevance: 88,
        summary: "用可验证答案、规则奖励或群组相对优化提升数学、代码、工具调用等任务的推理能力。",
        why: "大模型训练从人类偏好扩展到可验证任务奖励，对代码、检索、规划和工具使用都有影响。",
        actions: ["补一页训练范式对比", "把面试题区分偏好类/可验证类", "理解 GRPO 与 PPO 的差异"],
        interview: "RLVR 的关键是奖励可验证：代码能跑测试、数学有答案、工具调用有结果。GRPO 类方法减少 value model 依赖，用组内相对优势做优化。"
    },
    {
        id: "model_distillation",
        name: "Model Distillation / Specialist Models",
        domain: "模型压缩",
        horizon: "下一批",
        maturity: "生产化",
        relevance: 87,
        summary: "把大模型能力迁移到更小、更便宜、更快的专用模型或分类器上。",
        why: "简历分类、JD 标签、关键词抽取不一定都要强模型，蒸馏和专用小模型能降低成本。",
        actions: ["区分强模型/小模型任务", "为高频任务设计蒸馏样例", "记录质量和成本对比"],
        interview: "我会把复杂生成任务交给强模型，把高频结构化任务蒸馏成小模型或规则分类器，降低成本和延迟。",
        sources: [
            { label: "OpenAI distillation", url: "https://platform.openai.com/docs/guides/distillation" }
        ]
    },
    {
        id: "edge_slm",
        name: "Edge SLM / On-device AI",
        domain: "部署形态",
        horizon: "下一批",
        maturity: "快速落地",
        relevance: 83,
        summary: "小语言模型在本地、端侧或私有环境运行，承担低延迟、隐私敏感和离线任务。",
        why: "求职材料和本地项目路径有隐私属性，端侧小模型适合做初筛、分类和本地摘要。",
        actions: ["标记可本地执行任务", "预留本地模型接口", "区分隐私敏感数据"],
        interview: "我会按任务敏感度选择部署形态：隐私和低延迟任务优先端侧或本地小模型，高复杂任务再调用云端强模型。"
    },
    {
        id: "vector_compression",
        name: "Vector Compression / Binary Quantization",
        domain: "检索系统",
        horizon: "下一批",
        maturity: "生产化",
        relevance: 85,
        summary: "通过 PQ、SQ、Binary Quantization、Matryoshka Embeddings 等降低向量存储和检索成本。",
        why: "项目证据库、JD 库、知识库一旦增大，向量成本和召回质量需要工程权衡。",
        actions: ["补充向量压缩专题", "给 RAG 知识库加存储成本估算", "比较召回率损失"],
        interview: "向量库优化不是只选 HNSW，还要考虑向量维度、量化、压缩、重排和召回率成本曲线。"
    },
    {
        id: "data_contracts_ai",
        name: "Data Contracts for AI",
        domain: "数据治理",
        horizon: "下一批",
        maturity: "生产化",
        relevance: 86,
        summary: "为 AI 管道输入输出定义 schema、质量约束、血缘、版本和破坏性变更规则。",
        why: "JD 解析、简历 JSON、作品集证据和知识点都需要稳定结构，否则后续功能容易被字段漂移打坏。",
        actions: ["为 jobs/resume/portfolio/radar 定义 schema", "增加版本号", "记录字段变更"],
        interview: "AI 系统也需要数据契约：输入字段、类型、质量规则、血缘和版本，否则模型输出结构一变，下游就会失效。"
    },
    {
        id: "ai_red_teaming",
        name: "AI Red Teaming / Safety Evals",
        domain: "AI 安全",
        horizon: "下一批",
        maturity: "生产化",
        relevance: 84,
        summary: "系统化测试 prompt injection、越权工具调用、隐私泄露、幻觉和危险建议。",
        why: "后续如果接岗位网页、文件系统和自动投递，必须提前做安全评测。",
        actions: ["建立攻击样例库", "测试外部 JD 注入", "为文件/投递动作设红线"],
        interview: "我会把 AI 安全测试纳入发布流程：用红队样例覆盖注入、越权、泄露、幻觉和危险动作。"
    },
    {
        id: "rag_citation_verification",
        name: "Citation Verification / Groundedness",
        domain: "知识增强",
        horizon: "立即补",
        maturity: "生产化",
        relevance: 90,
        summary: "检查回答是否被检索证据支持，引用是否真实、相关且没有错配。",
        why: "你的简历和项目材料必须事实准确，RAG 生成内容如果引用错证据会直接伤害可信度。",
        actions: ["为项目证据加引用校验", "生成材料时标注事实来源", "不确定内容进入人工确认"],
        interview: "RAG 不能只看答案流畅度，还要做 groundedness 检查：每个关键结论都应能回到对应证据片段。"
    }
];

const radarFilterState = {
    query: "",
    domain: "all",
    horizon: "all"
};

function radarEscape(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function getRadarStats() {
    const domains = new Set(knowledgeRadar.map(item => item.domain));
    const urgent = knowledgeRadar.filter(item => item.horizon === "立即补").length;
    const covered = knowledgeRadar.filter(item => item.horizon === "已收录").length;
    const avgRelevance = Math.round(
        knowledgeRadar.reduce((sum, item) => sum + item.relevance, 0) / knowledgeRadar.length
    );
    return { domains: domains.size, urgent, covered, avgRelevance };
}

function syncRadarFilters() {
    const searchInput = document.getElementById("radar-search-input");
    const domainFilter = document.getElementById("radar-domain-filter");
    const horizonFilter = document.getElementById("radar-horizon-filter");

    if (searchInput) radarFilterState.query = searchInput.value.trim().toLowerCase();
    if (domainFilter) radarFilterState.domain = domainFilter.value || "all";
    if (horizonFilter) radarFilterState.horizon = horizonFilter.value || "all";
}

function renderRadarDomainOptions() {
    const domainFilter = document.getElementById("radar-domain-filter");
    if (!domainFilter) return;

    const selected = domainFilter.value || radarFilterState.domain;
    const domains = Array.from(new Set(knowledgeRadar.map(item => item.domain))).sort((a, b) => a.localeCompare(b, "zh-CN"));
    domainFilter.innerHTML = [
        `<option value="all">全部领域</option>`,
        ...domains.map(domain => `<option value="${radarEscape(domain)}">${radarEscape(domain)}</option>`)
    ].join("");
    domainFilter.value = domains.includes(selected) ? selected : "all";
}

function getFilteredRadarTopics() {
    syncRadarFilters();
    const query = radarFilterState.query;

    return knowledgeRadar.filter(item => {
        const matchesDomain = radarFilterState.domain === "all" || item.domain === radarFilterState.domain;
        const matchesHorizon = radarFilterState.horizon === "all" || item.horizon === radarFilterState.horizon;
        const haystack = [
            item.name,
            item.domain,
            item.horizon,
            item.maturity,
            item.summary,
            item.why,
            item.interview,
            ...(item.actions || [])
        ].join(" ").toLowerCase();
        const matchesQuery = !query || haystack.includes(query);
        return matchesDomain && matchesHorizon && matchesQuery;
    });
}

function renderKnowledgeRadar() {
    const statsEl = document.getElementById("radar-stats");
    const lanesEl = document.getElementById("radar-lanes");
    const gridEl = document.getElementById("radar-grid");
    const spotlightEl = document.getElementById("radar-spotlight");
    if (!statsEl || !lanesEl || !gridEl || !spotlightEl) return;

    renderRadarDomainOptions();
    const filteredTopics = getFilteredRadarTopics();
    const stats = getRadarStats();
    statsEl.innerHTML = [
        { label: "雷达概念", value: knowledgeRadar.length },
        { label: "技术域", value: stats.domains },
        { label: "立即补强", value: stats.urgent },
        { label: "当前结果", value: filteredTopics.length },
        { label: "平均求职相关度", value: `${stats.avgRelevance}%` }
    ].map(item => `
        <div class="radar-stat">
            <span>${radarEscape(item.label)}</span>
            <strong>${radarEscape(item.value)}</strong>
        </div>
    `).join("");

    const horizons = ["立即补", "下一批", "已收录"];
    lanesEl.innerHTML = horizons.map(horizon => {
        const items = filteredTopics.filter(item => item.horizon === horizon);
        return `
            <section class="radar-lane">
                <div class="radar-lane-title">
                    <h3>${radarEscape(horizon)}</h3>
                    <span>${items.length}</span>
                </div>
                <div class="radar-lane-items">
                    ${items.map(item => `
                        <button class="radar-chip" type="button" onclick="focusRadarTopic('${radarEscape(item.id)}')">
                            ${radarEscape(item.name)}
                        </button>
                    `).join("")}
                </div>
            </section>
        `;
    }).join("");

    gridEl.innerHTML = filteredTopics.length ? filteredTopics
        .slice()
        .sort((a, b) => b.relevance - a.relevance)
        .map(item => `
            <article class="radar-topic" data-radar-id="${radarEscape(item.id)}">
                <div class="radar-topic-head">
                    <div>
                        <span class="radar-domain">${radarEscape(item.domain)}</span>
                        <h3>${radarEscape(item.name)}</h3>
                    </div>
                    <strong>${item.relevance}</strong>
                </div>
                <p>${radarEscape(item.summary)}</p>
                <div class="radar-meta">
                    <span>${radarEscape(item.horizon)}</span>
                    <span>${radarEscape(item.maturity)}</span>
                </div>
                <button class="radar-detail-btn" type="button" onclick="focusRadarTopic('${radarEscape(item.id)}')">
                    查看建设动作
                    <i data-lucide="arrow-right"></i>
                </button>
            </article>
        `).join("") : `
            <div class="radar-empty">
                <i data-lucide="search-x"></i>
                <strong>没有匹配的技术概念</strong>
                <span>调整关键词、领域或建设阶段后再试。</span>
            </div>
        `;

    if (!filteredTopics.length) {
        spotlightEl.innerHTML = `
            <div class="radar-empty radar-empty-spotlight">
                <i data-lucide="search-x"></i>
                <strong>当前筛选没有可聚焦概念</strong>
                <span>清空筛选或换一个关键词继续浏览。</span>
            </div>
        `;
    } else {
        focusRadarTopic(filteredTopics[0].id);
    }

    if (window.lucide) {
        lucide.createIcons();
    }
}

function resetRadarFilters() {
    const searchInput = document.getElementById("radar-search-input");
    const domainFilter = document.getElementById("radar-domain-filter");
    const horizonFilter = document.getElementById("radar-horizon-filter");

    if (searchInput) searchInput.value = "";
    if (domainFilter) domainFilter.value = "all";
    if (horizonFilter) horizonFilter.value = "all";

    radarFilterState.query = "";
    radarFilterState.domain = "all";
    radarFilterState.horizon = "all";
    renderKnowledgeRadar();
}

function focusRadarTopic(topicId) {
    const topic = knowledgeRadar.find(item => item.id === topicId) || knowledgeRadar[0];
    const spotlightEl = document.getElementById("radar-spotlight");
    if (!topic || !spotlightEl) return;

    document.querySelectorAll(".radar-topic").forEach(item => {
        item.classList.toggle("active", item.dataset.radarId === topic.id);
    });

    spotlightEl.innerHTML = `
        <div class="radar-spotlight-header">
            <div>
                <span class="radar-domain">${radarEscape(topic.domain)}</span>
                <h3>${radarEscape(topic.name)}</h3>
            </div>
            <strong>${radarEscape(topic.horizon)}</strong>
        </div>
        <p class="radar-why">${radarEscape(topic.why)}</p>
        <div class="radar-action-list">
            ${topic.actions.map(action => `
                <div class="radar-action">
                    <i data-lucide="check-circle-2"></i>
                    <span>${radarEscape(action)}</span>
                </div>
            `).join("")}
        </div>
        <div class="radar-interview">
            <strong>面试表达</strong>
            <p>${radarEscape(topic.interview)}</p>
        </div>
        ${(topic.sources || []).length ? `
            <div class="radar-sources">
                ${(topic.sources || []).map(source => `
                    <a href="${radarEscape(source.url)}" target="_blank" rel="noopener">
                        ${radarEscape(source.label)}
                    </a>
                `).join("")}
            </div>
        ` : ""}
    `;

    if (window.lucide) {
        lucide.createIcons();
    }
}

window.knowledgeRadar = knowledgeRadar;
window.renderKnowledgeRadar = renderKnowledgeRadar;
window.focusRadarTopic = focusRadarTopic;
window.resetRadarFilters = resetRadarFilters;
