const knowledgeRadar = [
    {
        "id": "loop_engineering",
        "name": "Loop Engineering",
        "domain": "Agent 工程",
        "horizon": "立即补",
        "maturity": "新兴",
        "relevance": 98,
        "summary": "围绕“生成-执行-观察-评估-修正”的闭环设计 Agent，而不是只写一次 prompt。",
        "why": "商用 Agent 的关键不再是单轮回答，而是能持续读取状态、调用工具、评估结果、回滚错误并进入下一轮。",
        "actions": [
            "补一页知识卡",
            "设计一个求职材料优化 loop",
            "在面试中用它解释 Agent 工程化能力"
        ],
        "interview": "我会把 Agent 设计成闭环系统：Planner 生成计划，Executor 调工具，Observer 收集结果，Evaluator 打分，Controller 决定继续、回滚或交给人工。",
        "sources": [
            {
                "label": "LangGraph durable agents",
                "url": "https://langchain-ai.github.io/langgraph/"
            },
            {
                "label": "DSPy optimization",
                "url": "https://dspy.ai/"
            }
        ]
    },
    {
        "id": "context_engineering",
        "name": "Context Engineering",
        "domain": "LLM 应用",
        "horizon": "立即补",
        "maturity": "快速升温",
        "relevance": 97,
        "summary": "系统化管理模型上下文：指令、工具、记忆、检索证据、用户状态和任务轨迹。",
        "why": "长上下文不是把所有材料塞进去，真正难点是选择、压缩、排序、隔离和刷新上下文。",
        "actions": [
            "把简历/JD/作品集做成上下文包",
            "新增上下文预算字段",
            "给 RAG 面试答案加入上下文治理话术"
        ],
        "interview": "我会把 prompt 工程升级为 context engineering：先定义上下文来源，再做优先级、token 预算、证据隔离和过期策略。",
        "sources": [
            {
                "label": "LangGraph memory",
                "url": "https://langchain-ai.github.io/langgraph/concepts/memory/"
            },
            {
                "label": "LlamaIndex docs",
                "url": "https://docs.llamaindex.ai/"
            }
        ]
    },
    {
        "id": "agentops",
        "name": "AgentOps / Agent Observability",
        "domain": "工程运维",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 95,
        "summary": "为 Agent 增加 trace、工具调用日志、成本、延迟、失败率和人工接管记录。",
        "why": "面试中讲 Agent 项目时，能讲可观测性会明显区别于只会 demo 的候选人。",
        "actions": [
            "设计 trace 字段",
            "在 JD 匹配模块预留执行日志",
            "补充失败案例复盘模板"
        ],
        "interview": "Agent 上线必须记录每一步：模型输入输出、工具参数、返回值、耗时、成本、错误、重试和人工确认。",
        "sources": [
            {
                "label": "LangSmith observability",
                "url": "https://docs.smith.langchain.com/"
            },
            {
                "label": "OpenAI Agents tracing",
                "url": "https://openai.github.io/openai-agents-python/tracing/"
            }
        ]
    },
    {
        "id": "evalops",
        "name": "EvalOps / LLM Evaluation",
        "domain": "评测体系",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 96,
        "summary": "为 LLM/RAG/Agent 建立离线评测集、在线回归测试和人工评分闭环。",
        "why": "AI 应用真正可交付，靠的是评测集、红线样例、回归测试和指标趋势，不是几条好看的回答。",
        "actions": [
            "为简历润色建 20 条评测样例",
            "为 RAG 建证据一致性评分",
            "为面试训练建评分 rubric"
        ],
        "interview": "我会把 AI 功能按任务拆评测：准确性、证据一致性、格式合规、拒答边界、延迟和成本都要进回归测试。",
        "sources": [
            {
                "label": "OpenAI Evals",
                "url": "https://github.com/openai/evals"
            },
            {
                "label": "RAGAS",
                "url": "https://docs.ragas.io/"
            }
        ]
    },
    {
        "id": "guardrails",
        "name": "Guardrails / Structured Validation",
        "domain": "AI 安全",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 92,
        "summary": "对模型输出做结构、类型、事实、权限和安全约束，避免自由文本直接进入业务系统。",
        "why": "求职系统后续会生成简历、邮件、PPT 和岗位分析，必须校验格式、事实和敏感信息。",
        "actions": [
            "为 JD 解析定义 JSON schema",
            "为简历 bullet 做事实一致性检查",
            "高风险改写加人工确认"
        ],
        "interview": "我不会让模型自由输出直接落库，而会用 schema、校验器、敏感词规则和人工确认保护关键流程。",
        "sources": [
            {
                "label": "Guardrails AI",
                "url": "https://www.guardrailsai.com/docs"
            },
            {
                "label": "OpenAI structured outputs",
                "url": "https://platform.openai.com/docs/guides/structured-outputs"
            }
        ]
    },
    {
        "id": "human_in_the_loop",
        "name": "Human-in-the-Loop Agent",
        "domain": "Agent 工程",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 94,
        "summary": "在高风险步骤暂停，等待人工确认、编辑或审批，再继续执行。",
        "why": "求职材料、投递邮件、文件操作都属于需要人确认的动作，不能全自动黑箱执行。",
        "actions": [
            "为投递动作增加确认点",
            "为简历改写增加 diff 预览",
            "记录人工审批原因"
        ],
        "interview": "我会按风险分层：低风险自动执行，高风险暂停给人确认，所有确认都写入审计日志。",
        "sources": [
            {
                "label": "LangGraph human-in-the-loop",
                "url": "https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/"
            }
        ]
    },
    {
        "id": "mcp_a2a",
        "name": "MCP + A2A 协议栈",
        "domain": "Agent 生态",
        "horizon": "已收录",
        "maturity": "标准化",
        "relevance": 94,
        "summary": "MCP 连接工具和上下文，A2A 连接不同 Agent，是多 Agent 工作流的协议基础。",
        "why": "后续岗位库、简历库、知识库、浏览器和文件系统都可以按工具能力接入。",
        "actions": [
            "保留到知识库",
            "设计本地工具清单",
            "把作品集/JD/简历作为资源源"
        ],
        "interview": "MCP 是模型到工具，A2A 是 Agent 到 Agent；我会把权限、schema 和审计作为协议落地的重点。",
        "sources": [
            {
                "label": "Model Context Protocol",
                "url": "https://modelcontextprotocol.io/docs/getting-started/intro"
            },
            {
                "label": "Google A2A",
                "url": "https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/"
            }
        ]
    },
    {
        "id": "graph_rag",
        "name": "GraphRAG / Agentic RAG",
        "domain": "知识增强",
        "horizon": "已收录",
        "maturity": "快速落地",
        "relevance": 93,
        "summary": "把向量召回升级为实体、关系、社区摘要和多步检索规划。",
        "why": "你的项目证据分散在 E 盘多个目录，天然适合从文件证据图谱做项目问答和简历生成。",
        "actions": [
            "把项目-技术-指标建关系图",
            "生成岗位到项目映射",
            "为作品集增加关联知识点"
        ],
        "interview": "普通 RAG 更像片段检索，GraphRAG 能处理跨项目、跨实体和全局摘要问题。",
        "sources": [
            {
                "label": "Microsoft GraphRAG",
                "url": "https://microsoft.github.io/graphrag/"
            }
        ]
    },
    {
        "id": "memory_systems",
        "name": "Long-term Memory for Agents",
        "domain": "Agent 工程",
        "horizon": "下一批",
        "maturity": "快速升温",
        "relevance": 91,
        "summary": "把用户偏好、历史任务、项目证据和失败案例沉淀为可检索、可更新、可遗忘的长期记忆。",
        "why": "你的求职系统需要记住岗位偏好、项目讲法、投递记录和反复出错的表达。",
        "actions": [
            "定义记忆类型",
            "增加更新时间和可信度",
            "区分事实/推断/偏好"
        ],
        "interview": "Agent 记忆不是简单聊天记录，而是分层存储：事实、偏好、任务状态、技能画像和审计记录。"
    },
    {
        "id": "prompt_optimization",
        "name": "Prompt Optimization / DSPy",
        "domain": "LLM 应用",
        "horizon": "下一批",
        "maturity": "快速升温",
        "relevance": 89,
        "summary": "用数据和评测自动优化 prompt、示例和模块组合，而不是手工玄学调参。",
        "why": "简历润色、JD 解析、面试评分都可以变成可优化的语言程序。",
        "actions": [
            "为简历改写建输入输出样例",
            "用评测分数驱动提示词迭代",
            "记录 prompt 版本"
        ],
        "interview": "我会把 prompt 当成可评测、可版本化、可优化的程序组件，而不是一次性的文本。"
    },
    {
        "id": "reasoning_control",
        "name": "Reasoning Control / Test-Time Compute",
        "domain": "推理优化",
        "horizon": "已收录",
        "maturity": "快速落地",
        "relevance": 90,
        "summary": "按任务风险增加多候选、验证器、反思和选择步骤，换取更高正确率。",
        "why": "投递材料和技术答辩属于高价值任务，适合启用更强的推理控制。",
        "actions": [
            "为关键输出增加二次审查",
            "设置速度/质量模式",
            "记录验证理由"
        ],
        "interview": "我会按风险使用 test-time compute：普通问答快速生成，关键结论多候选加验证器。"
    },
    {
        "id": "vibe_to_spec",
        "name": "Vibe Coding 到 Spec-Driven Development",
        "domain": "软件工程",
        "horizon": "下一批",
        "maturity": "新兴",
        "relevance": 88,
        "summary": "AI 辅助开发从随口生成代码，走向需求、验收、测试和变更记录驱动。",
        "why": "这个软件会越来越大，必须避免脚本堆叠，进入模块化、测试化和规格化建设。",
        "actions": [
            "为每个模块写验收标准",
            "建立 smoke test",
            "拆分 app.js/resume.js"
        ],
        "interview": "AI 编程不能只看生成速度，必须有 spec、测试、代码审查和回归验证来保证长期可维护。"
    },
    {
        "id": "llm_security",
        "name": "Prompt Injection / Tool Sandbox",
        "domain": "AI 安全",
        "horizon": "已收录",
        "maturity": "生产化",
        "relevance": 92,
        "summary": "防止网页、JD、文档或检索内容诱导模型越权、泄露信息或执行危险工具。",
        "why": "岗位 JD 和网页内容都是不可信输入，后续如果接浏览器和文件工具必须有沙箱。",
        "actions": [
            "标记外部内容不可信",
            "工具最小权限",
            "敏感动作二次确认"
        ],
        "interview": "我会把外部文本视为数据而不是指令，工具调用必须经过权限和参数校验。"
    },
    {
        "id": "multimodal_rag",
        "name": "Multimodal RAG",
        "domain": "多模态",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 87,
        "summary": "同时检索文本、图片、表格、PPT、PDF 截图和视觉特征，生成带证据的回答。",
        "why": "你的项目资料里有 PPT、图表、遥感/视觉结果，不能只做纯文本 RAG。",
        "actions": [
            "抽取 PPT/PDF 图片证据",
            "给作品集增加截图证据",
            "设计多模态引用格式"
        ],
        "interview": "多模态 RAG 要解决图片、表格和文本的统一索引，以及回答时的证据定位。"
    },
    {
        "id": "geo_foundation",
        "name": "Geospatial Foundation Models",
        "domain": "遥感 AI",
        "horizon": "已收录",
        "maturity": "快速落地",
        "relevance": 90,
        "summary": "Prithvi、TerraTorch 等把遥感任务推向预训练-微调的基础模型范式。",
        "why": "与你的遥感/GIS 求职方向高度相关，是区别普通 CV 候选人的关键词。",
        "actions": [
            "补充遥感基础模型对比表",
            "关联 Geospatial-AI-Ecosystem",
            "增加面试问答"
        ],
        "interview": "遥感基础模型不同于通用 CV，核心差异是多光谱、时序、CRS、分辨率和跨区域泛化。",
        "sources": [
            {
                "label": "Prithvi-EO-2.0",
                "url": "https://github.com/NASA-IMPACT/Prithvi-EO-2.0"
            },
            {
                "label": "TerraTorch",
                "url": "https://github.com/IBM/terratorch"
            }
        ]
    },
    {
        "id": "vlm_vla",
        "name": "VLM / VLA / Computer Use",
        "domain": "多模态",
        "horizon": "下一批",
        "maturity": "快速升温",
        "relevance": 88,
        "summary": "从看图问答扩展到视觉理解、界面操作、动作规划和机器人控制。",
        "why": "工业视觉、UWB+YOLO、遥感解译都可以用 VLM/VLA 话术升级表达。",
        "actions": [
            "为工业视觉项目补 VLM 版本表达",
            "增加界面操作 Agent 知识点",
            "关联 OpenVLA"
        ],
        "interview": "VLM 负责视觉语义理解，VLA 进一步输出动作；生产系统仍要传感器冗余和安全边界。"
    },
    {
        "id": "inference_systems",
        "name": "LLM Inference Systems",
        "domain": "推理优化",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 86,
        "summary": "围绕 KV cache、continuous batching、speculative decoding、量化和并行策略优化推理服务。",
        "why": "AI 工程岗位越来越看重部署成本、延迟和吞吐，不只看模型调用。",
        "actions": [
            "把 MLA/GQA/KV cache 做成专题",
            "补充吞吐/延迟面试题",
            "整理 vLLM/SGLang 概念"
        ],
        "interview": "推理服务优化要同时看模型结构、KV cache、batch 调度、量化、并行和业务延迟预算。"
    },
    {
        "id": "synthetic_data",
        "name": "Synthetic Data / Data Flywheel",
        "domain": "数据闭环",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 84,
        "summary": "用模型生成、筛选、评测和人工确认的数据持续增强任务能力。",
        "why": "面试题、简历样例、JD 样例都可以形成数据飞轮，越用越准。",
        "actions": [
            "沉淀 JD 样例库",
            "沉淀面试问答样例",
            "建立人工审核标签"
        ],
        "interview": "AI 产品要有数据飞轮：真实使用数据、人工反馈、合成扩充和回归评测共同推动迭代。"
    },
    {
        "id": "llm_gateway_routing",
        "name": "LLM Gateway / Model Routing",
        "domain": "工程架构",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 93,
        "summary": "在多个模型、供应商和成本档位之间做路由、降级、重试、预算和审计。",
        "why": "商用 AI 应用不会只绑一个模型。岗位 JD 匹配、简历润色、面试训练可按任务难度选择快模型、强模型或本地模型。",
        "actions": [
            "设计模型路由策略",
            "区分速度/质量/成本模式",
            "给关键任务增加 fallback"
        ],
        "interview": "我会在业务层前面加 LLM Gateway：统一鉴权、限流、模型路由、预算、重试、fallback 和日志，避免应用代码直接耦合某个模型。",
        "sources": [
            {
                "label": "LiteLLM routing",
                "url": "https://docs.litellm.ai/docs/routing"
            }
        ]
    },
    {
        "id": "opentelemetry_genai",
        "name": "OpenTelemetry GenAI Observability",
        "domain": "工程运维",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 91,
        "summary": "用标准化 telemetry 记录模型请求、token、延迟、工具调用和错误，打通 AI 应用监控。",
        "why": "AgentOps 需要落到标准日志和指标，OpenTelemetry GenAI 语义约定正在成为跨平台可观测性的共同语言。",
        "actions": [
            "为后端预留 trace id",
            "记录 token/latency/cost",
            "把工具调用纳入 span"
        ],
        "interview": "我会用 OpenTelemetry 思路记录 GenAI 调用：模型名、输入输出规模、token、延迟、错误、工具调用链和用户会话，便于线上排障。",
        "sources": [
            {
                "label": "OpenTelemetry GenAI",
                "url": "https://opentelemetry.io/docs/specs/semconv/gen-ai/"
            }
        ]
    },
    {
        "id": "swe_agents",
        "name": "SWE Agents / Coding Agents",
        "domain": "软件工程",
        "horizon": "立即补",
        "maturity": "快速落地",
        "relevance": 92,
        "summary": "面向真实代码库的自动定位、修改、测试和提交工作流，评估基准从 toy task 转向真实 issue。",
        "why": "你这个软件后续会模块化，AI coding agent 的能力可以用于重构、测试生成和回归修复。",
        "actions": [
            "建立 smoke test",
            "拆分大文件前写验收",
            "用 issue/patch 思路管理改动"
        ],
        "interview": "我会把 coding agent 当成协作开发者：先读仓库、制定 patch、跑测试、解释风险，而不是直接生成孤立代码。",
        "sources": [
            {
                "label": "SWE-bench",
                "url": "https://www.swebench.com/"
            }
        ]
    },
    {
        "id": "swe_bench_verified",
        "name": "SWE-bench Verified / Real-world Eval",
        "domain": "评测体系",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 86,
        "summary": "用真实 GitHub issue 和人工验证子集评估软件工程 Agent 的修复能力。",
        "why": "这能帮助你在面试中区分“AI 会写代码”和“AI 能在真实仓库里解决问题”。",
        "actions": [
            "把本项目任务写成 issue",
            "为每个功能写验收测试",
            "记录 agent 修复成功率"
        ],
        "interview": "SWE-bench 类评测的价值在于真实代码上下文、真实失败测试和可验证 patch，比单文件算法题更接近工程岗位。"
    },
    {
        "id": "rlvr_grpo",
        "name": "RLVR / GRPO / Verifiable Rewards",
        "domain": "训练范式",
        "horizon": "下一批",
        "maturity": "快速升温",
        "relevance": 88,
        "summary": "用可验证答案、规则奖励或群组相对优化提升数学、代码、工具调用等任务的推理能力。",
        "why": "大模型训练从人类偏好扩展到可验证任务奖励，对代码、检索、规划和工具使用都有影响。",
        "actions": [
            "补一页训练范式对比",
            "把面试题区分偏好类/可验证类",
            "理解 GRPO 与 PPO 的差异"
        ],
        "interview": "RLVR 的关键是奖励可验证：代码能跑测试、数学有答案、工具调用有结果。GRPO 类方法减少 value model 依赖，用组内相对优势做优化。"
    },
    {
        "id": "model_distillation",
        "name": "Model Distillation / Specialist Models",
        "domain": "模型压缩",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 87,
        "summary": "把大模型能力迁移到更小、更便宜、更快的专用模型或分类器上。",
        "why": "简历分类、JD 标签、关键词抽取不一定都要强模型，蒸馏和专用小模型能降低成本。",
        "actions": [
            "区分强模型/小模型任务",
            "为高频任务设计蒸馏样例",
            "记录质量和成本对比"
        ],
        "interview": "我会把复杂生成任务交给强模型，把高频结构化任务蒸馏成小模型或规则分类器，降低成本和延迟。",
        "sources": [
            {
                "label": "OpenAI distillation",
                "url": "https://platform.openai.com/docs/guides/distillation"
            }
        ]
    },
    {
        "id": "edge_slm",
        "name": "Edge SLM / On-device AI",
        "domain": "部署形态",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 83,
        "summary": "小语言模型在本地、端侧或私有环境运行，承担低延迟、隐私敏感和离线任务。",
        "why": "求职材料和本地项目路径有隐私属性，端侧小模型适合做初筛、分类和本地摘要。",
        "actions": [
            "标记可本地执行任务",
            "预留本地模型接口",
            "区分隐私敏感数据"
        ],
        "interview": "我会按任务敏感度选择部署形态：隐私和低延迟任务优先端侧或本地小模型，高复杂任务再调用云端强模型。"
    },
    {
        "id": "vector_compression",
        "name": "Vector Compression / Binary Quantization",
        "domain": "检索系统",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 85,
        "summary": "通过 PQ、SQ、Binary Quantization、Matryoshka Embeddings 等降低向量存储和检索成本。",
        "why": "项目证据库、JD 库、知识库一旦增大，向量成本和召回质量需要工程权衡。",
        "actions": [
            "补充向量压缩专题",
            "给 RAG 知识库加存储成本估算",
            "比较召回率损失"
        ],
        "interview": "向量库优化不是只选 HNSW，还要考虑向量维度、量化、压缩、重排和召回率成本曲线。"
    },
    {
        "id": "data_contracts_ai",
        "name": "Data Contracts for AI",
        "domain": "数据治理",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 86,
        "summary": "为 AI 管道输入输出定义 schema、质量约束、血缘、版本和破坏性变更规则。",
        "why": "JD 解析、简历 JSON、作品集证据和知识点都需要稳定结构，否则后续功能容易被字段漂移打坏。",
        "actions": [
            "为 jobs/resume/portfolio/radar 定义 schema",
            "增加版本号",
            "记录字段变更"
        ],
        "interview": "AI 系统也需要数据契约：输入字段、类型、质量规则、血缘和版本，否则模型输出结构一变，下游就会失效。"
    },
    {
        "id": "ai_red_teaming",
        "name": "AI Red Teaming / Safety Evals",
        "domain": "AI 安全",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 84,
        "summary": "系统化测试 prompt injection、越权工具调用、隐私泄露、幻觉和危险建议。",
        "why": "后续如果接岗位网页、文件系统和自动投递，必须提前做安全评测。",
        "actions": [
            "建立攻击样例库",
            "测试外部 JD 注入",
            "为文件/投递动作设红线"
        ],
        "interview": "我会把 AI 安全测试纳入发布流程：用红队样例覆盖注入、越权、泄露、幻觉和危险动作。"
    },
    {
        "id": "rag_citation_verification",
        "name": "Citation Verification / Groundedness",
        "domain": "知识增强",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 90,
        "summary": "检查回答是否被检索证据支持，引用是否真实、相关且没有错配。",
        "why": "你的简历和项目材料必须事实准确，RAG 生成内容如果引用错证据会直接伤害可信度。",
        "actions": [
            "为项目证据加引用校验",
            "生成材料时标注事实来源",
            "不确定内容进入人工确认"
        ],
        "interview": "RAG 不能只看答案流畅度，还要做 groundedness 检查：每个关键结论都应能回到对应证据片段。"
    },
    {
        "id": "deep_agents_harness",
        "name": "Deep Agents / Agent Harness",
        "domain": "Agent 工程",
        "horizon": "立即补",
        "maturity": "快速落地",
        "relevance": 96,
        "summary": "把工具调用循环升级为带规划、虚拟文件系统、子代理、长期记忆、权限和人工确认的 Agent 外骨架。",
        "why": "你的求职软件已经有简历、证据库、知识雷达、导出和Git同步，下一步正适合做成多步 Agent 工作台，而不是单个聊天入口。",
        "actions": [
            "设计任务清单与状态机",
            "增加文件证据工作区",
            "为高风险动作设置人工确认"
        ],
        "interview": "我会把 Agent 看成 harness：工具、文件系统、记忆、子代理、权限、trace 和人工确认组合起来，才能支撑真实多步任务。",
        "sources": [
            {
                "label": "LangChain Deep Agents overview",
                "url": "https://docs.langchain.com/oss/python/deepagents/overview"
            }
        ]
    },
    {
        "id": "agent_handoffs",
        "name": "Agent Handoffs / Specialist Routing",
        "domain": "Agent 编排",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 94,
        "summary": "由一个分诊 Agent 判断任务类型，再把上下文转交给简历、JD、作品集、知识库或Git同步等专门 Agent。",
        "why": "商用求职助手不能把所有事塞给一个大提示词，必须按任务边界拆分专业角色并控制移交上下文。",
        "actions": [
            "定义简历/JD/作品集/同步四类专员",
            "记录 handoff reason",
            "限制接收方可见上下文"
        ],
        "interview": "我会使用 handoff 模式做专家路由：分诊 Agent 只负责判断去向，专门 Agent 负责执行，并记录移交原因和上下文过滤规则。",
        "sources": [
            {
                "label": "OpenAI Agents SDK handoffs",
                "url": "https://openai.github.io/openai-agents-python/handoffs/"
            }
        ]
    },
    {
        "id": "agent_tool_guardrails",
        "name": "Tool Guardrails / Tripwires",
        "domain": "AI 安全",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 95,
        "summary": "在工具调用前后设置输入、输出、权限和越界检测，触发 tripwire 时中止或转人工确认。",
        "why": "后续如果做自动投递、改简历、推Git、读E盘文件，必须防止 prompt injection 和越权操作。",
        "actions": [
            "为写文件/推送/外发动作加确认",
            "给工具输入定义 schema",
            "记录触发拦截的原因"
        ],
        "interview": "我不会让模型直接决定高风险动作，而是在工具边界加 schema、权限、guardrail 和 tripwire，必要时转人工确认。",
        "sources": [
            {
                "label": "OpenAI Agents SDK guardrails",
                "url": "https://openai.github.io/openai-agents-python/guardrails/"
            }
        ]
    },
    {
        "id": "mcp_roots_elicitation_sampling",
        "name": "MCP Roots / Elicitation / Sampling",
        "domain": "协议生态",
        "horizon": "立即补",
        "maturity": "快速标准化",
        "relevance": 93,
        "summary": "MCP 不只是 tools，还包括 roots、elicitation、sampling、resources、prompts 等能力边界和交互机制。",
        "why": "你本地项目大量依赖文件、文档、工具和外部数据，理解 MCP 的能力协商和安全边界会显著提升面试表达。",
        "actions": [
            "补充 MCP 能力矩阵卡",
            "区分 tools/resources/prompts",
            "给本地文件访问标注 roots 边界"
        ],
        "interview": "MCP 的关键不是“接工具”三个字，而是标准化上下文、工具、资源、提示词、能力协商和用户授权边界。",
        "sources": [
            {
                "label": "MCP 2025-06-18 specification",
                "url": "https://modelcontextprotocol.io/specification/2025-06-18"
            }
        ]
    },
    {
        "id": "virtual_filesystem_agents",
        "name": "Virtual Filesystem for Agents",
        "domain": "Agent 工程",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 91,
        "summary": "给 Agent 一个受控的虚拟文件系统，用于存放中间结果、长文档摘要、草稿、证据片段和任务状态。",
        "why": "简历编辑器、证据说明、Markdown/JSON 导出都天然适合文件化；虚拟FS能降低上下文爆炸和误覆盖风险。",
        "actions": [
            "建立 workspace/artifacts 约定",
            "把长证据转文件引用",
            "区分只读证据和可写草稿"
        ],
        "interview": "复杂 Agent 不能只靠上下文窗口硬扛，我会把中间结果和证据放入受控文件系统，再由模型按需读取。",
        "sources": [
            {
                "label": "LangChain Deep Agents filesystem",
                "url": "https://docs.langchain.com/oss/python/deepagents/overview"
            }
        ]
    },
    {
        "id": "agent_permission_policy",
        "name": "Agent Permission Policy",
        "domain": "AI 安全",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 92,
        "summary": "用声明式权限控制 Agent 可读、可写、可执行、可联网、可外发的范围，把能力变成可审计策略。",
        "why": "本机有大量个人文档和项目代码，求职助手必须做到默认只读、明确授权、外发前确认。",
        "actions": [
            "定义 read/write/send 三类权限",
            "高风险动作默认人工确认",
            "把权限策略展示到设置页"
        ],
        "interview": "我会把 Agent 权限当成工程配置：哪些路径只读、哪些工具可执行、哪些动作必须确认，而不是只靠提示词约束。",
        "sources": [
            {
                "label": "Deep Agents permissions",
                "url": "https://docs.langchain.com/oss/python/deepagents/permissions"
            },
            {
                "label": "MCP security principles",
                "url": "https://modelcontextprotocol.io/specification/2025-06-18#security-and-trust-safety"
            }
        ]
    },
    {
        "id": "sandboxed_computer_use",
        "name": "Sandboxed Computer Use",
        "domain": "自动化执行",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 89,
        "summary": "让模型在受控沙箱里读写文件、执行命令或操作浏览器，减少对真实系统的误操作风险。",
        "why": "你的软件后续可能做自动投递、网页抓取、简历导出和仓库同步，沙箱化能把效率和安全同时抬起来。",
        "actions": [
            "把自动化动作放入沙箱",
            "保留执行日志和产物",
            "危险操作先预演再确认"
        ],
        "interview": "我会把 computer use 放进 sandbox：先限定文件系统、网络和命令权限，再让 Agent 执行，并把日志用于复盘。",
        "sources": [
            {
                "label": "Deep Agents sandboxes",
                "url": "https://docs.langchain.com/oss/python/deepagents/overview"
            },
            {
                "label": "OpenAI Agents SDK sandbox agents",
                "url": "https://openai.github.io/openai-agents-python/"
            }
        ]
    },
    {
        "id": "agent_event_streaming",
        "name": "Agent Event Streaming",
        "domain": "用户体验",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 88,
        "summary": "把 Agent 的计划、工具调用、文件读写、子任务和最终结果以事件流方式展示，避免用户面对黑箱等待。",
        "why": "商用软件要让用户知道系统在做什么，尤其是简历修改、证据检索、Git同步这类长任务。",
        "actions": [
            "设计任务事件面板",
            "展示当前步骤和耗时",
            "失败时给出可恢复动作"
        ],
        "interview": "我会把 Agent 运行过程流式化：计划、工具调用、读写文件、失败重试和人工确认都可见，用户才敢用。",
        "sources": [
            {
                "label": "Deep Agents event streaming",
                "url": "https://docs.langchain.com/oss/python/deepagents/overview"
            },
            {
                "label": "OpenAI Agents SDK streaming",
                "url": "https://openai.github.io/openai-agents-python/"
            }
        ]
    },
    {
        "id": "prompt_caching_strategy",
        "name": "Prompt Caching Strategy",
        "domain": "成本优化",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 87,
        "summary": "把稳定系统提示、长简历、项目证据、JD模板等前缀缓存起来，降低重复调用延迟和成本。",
        "why": "求职系统会反复使用同一批简历、项目证据和知识库，缓存策略比每次全量塞上下文更适合商用。",
        "actions": [
            "标记稳定上下文块",
            "拆分高复用前缀和动态请求",
            "统计缓存命中率"
        ],
        "interview": "我会把上下文拆成稳定前缀和动态输入，对稳定的简历/证据/JD框架做 prompt caching，优化延迟和成本。",
        "sources": [
            {
                "label": "Deep Agents context management",
                "url": "https://docs.langchain.com/oss/python/deepagents/overview"
            }
        ]
    },
    {
        "id": "agent_primitives",
        "name": "Agent Primitives: Plan / Act / Observe / Evaluate",
        "domain": "Agent 工程",
        "horizon": "立即补",
        "maturity": "基础范式",
        "relevance": 97,
        "summary": "把 Agent 能力拆成计划、行动、观察、评估、记忆、权限和人工确认等原语，支撑 Loop Engineering。",
        "why": "Loop Engineering 已经收录，但还需要把底层工程原语拆清楚，方便面试时从概念讲到实现。",
        "actions": [
            "给 Loop Engineering 增加原语图",
            "把简历优化流程拆成循环",
            "为每步定义失败处理"
        ],
        "interview": "我会从 Agent primitives 解释工程化：Plan 定目标，Act 调工具，Observe 收集结果，Evaluate 打分，Memory 沉淀，Guardrail 管边界。",
        "sources": [
            {
                "label": "LangGraph durable agents",
                "url": "https://langchain-ai.github.io/langgraph/"
            },
            {
                "label": "OpenAI Agents SDK",
                "url": "https://openai.github.io/openai-agents-python/"
            }
        ]
    },
    {
        "id": "a2a_agent_protocol",
        "name": "Agent2Agent Protocol (A2A)",
        "domain": "协议生态",
        "horizon": "立即补",
        "maturity": "快速标准化",
        "relevance": 94,
        "summary": "A2A 关注不同框架、不同厂商 Agent 之间的发现、任务协作、状态同步和产物交换。",
        "why": "MCP 解决 Agent 连接工具和上下文，A2A 解决 Agent 之间如何互相发现、委派和协作，适合讲多智能体求职工作流。",
        "actions": [
            "补充 A2A 与 MCP 对比卡",
            "设计 JD/简历/投递 Agent 协作流",
            "记录 Agent Card 和任务状态概念"
        ],
        "interview": "我会把 MCP 和 A2A 分开讲：MCP 偏工具与上下文接入，A2A 偏 Agent 间任务协作、能力发现、状态同步和 artifact 交付。",
        "sources": [
            {
                "label": "Google A2A announcement",
                "url": "https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/"
            }
        ]
    },
    {
        "id": "ag_ui_protocol",
        "name": "AG-UI / Agent User Interaction Protocol",
        "domain": "用户体验",
        "horizon": "下一批",
        "maturity": "新兴",
        "relevance": 88,
        "summary": "把 Agent 的事件、状态、工具调用、用户确认和界面更新标准化，让前端不只是展示最终答案。",
        "why": "你的应用要走向商用，用户需要看到简历修改、证据检索、Git同步等长任务的过程，而不是等待黑箱结果。",
        "actions": [
            "设计 Agent 事件流 UI",
            "把人工确认做成协议事件",
            "区分 plan/tool/result/error 四类事件"
        ],
        "interview": "我会把 Agent UI 做成事件驱动：计划、工具调用、等待确认、产物和错误都流式展示，降低用户不信任感。",
        "sources": [
            {
                "label": "AG-UI docs",
                "url": "https://docs.ag-ui.com/"
            }
        ]
    },
    {
        "id": "owasp_llm_top10_2025",
        "name": "OWASP LLM Top 10 2025",
        "domain": "AI 安全",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 93,
        "summary": "面向 LLM 应用的风险框架，包括提示注入、敏感信息泄露、供应链、过度代理和不安全输出处理等。",
        "why": "求职助手会读取本地文档、联网检索、写文件和推 Git，必须用标准风险框架约束自动化边界。",
        "actions": [
            "把高风险动作映射到 OWASP 风险",
            "为外部 JD 做注入检测",
            "给写文件/推送/外发动作加确认"
        ],
        "interview": "我会按 OWASP LLM Top 10 做安全设计，重点防 prompt injection、sensitive information disclosure 和 excessive agency。",
        "sources": [
            {
                "label": "OWASP Top 10 for LLM Applications",
                "url": "https://owasp.org/www-project-top-10-for-large-language-model-applications/"
            }
        ]
    },
    {
        "id": "agent_eval_regression",
        "name": "Agent Eval Regression",
        "domain": "评测体系",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 92,
        "summary": "把 Agent 多步任务做成可重复评测集，比较任务成功率、工具轨迹、证据一致性、成本和耗时。",
        "why": "简历润色、JD匹配、证据引用、知识雷达更新都需要回归测试，否则每次升级模型都有可能悄悄退化。",
        "actions": [
            "建立 20 条求职任务评测集",
            "记录工具调用轨迹",
            "比较升级前后成功率和成本"
        ],
        "interview": "我会把 Agent 评测从“答案好不好”扩展到任务是否完成、轨迹是否合规、证据是否正确、成本是否可控。",
        "sources": [
            {
                "label": "LangSmith evaluation concepts",
                "url": "https://docs.langchain.com/langsmith/evaluation-concepts"
            }
        ]
    },
    {
        "id": "opentelemetry_genai_semconv",
        "name": "OpenTelemetry GenAI Semantic Conventions",
        "domain": "工程运维",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 87,
        "summary": "用统一语义字段记录 GenAI 请求、模型、token、工具调用、延迟、错误和 trace。",
        "why": "当前雷达已有 AgentOps，但还需要落到可观测性标准字段，方便后续接日志、监控和成本统计。",
        "actions": [
            "补充 trace 字段表",
            "记录 token/latency/model/tool spans",
            "为长任务生成 trace id"
        ],
        "interview": "我会按 OpenTelemetry GenAI 语义约定记录模型调用、工具调用、token、延迟和错误，方便排障和成本治理。",
        "sources": [
            {
                "label": "OpenTelemetry GenAI semantic conventions",
                "url": "https://opentelemetry.io/docs/specs/semconv/gen-ai/"
            }
        ]
    },
    {
        "id": "alphaearth_foundations",
        "name": "AlphaEarth Foundations / Satellite Embeddings",
        "domain": "遥感基础模型",
        "horizon": "立即补",
        "maturity": "前沿",
        "relevance": 96,
        "summary": "Google DeepMind 的地球观测嵌入模型，把多源遥感数据压缩为可用于制图、分类和变化分析的统一表示。",
        "why": "你做养殖池塘、断面溯源、水色水质和滩涂规划，卫星 embedding 是遥感算法岗位必须跟进的新范式。",
        "actions": [
            "补充 Earth Engine embedding 工作流",
            "对比传统指数与 embedding 特征",
            "设计养殖池塘 few-shot 分类实验"
        ],
        "interview": "遥感基础模型正在从单景影像分割走向时空 embedding，未来可以用少量样本快速适配地物分类、变化检测和水环境分析。",
        "sources": [
            {
                "label": "Google DeepMind AlphaEarth Foundations",
                "url": "https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/"
            }
        ]
    },
    {
        "id": "prithvi_eo_2",
        "name": "Prithvi EO 2.0 / HLS Foundation Model",
        "domain": "遥感基础模型",
        "horizon": "立即补",
        "maturity": "可实践",
        "relevance": 94,
        "summary": "IBM-NASA 地球观测基础模型，面向 Harmonized Landsat Sentinel-2 等多光谱遥感任务微调。",
        "why": "这是遥感算法工程师可直接讲清楚的开源基础模型路线，和你已有 Sentinel/水体/养殖图斑任务高度相关。",
        "actions": [
            "补 Prithvi 微调卡",
            "整理 HLS 输入波段与 patch 策略",
            "设计池塘/水体分类迁移实验"
        ],
        "interview": "Prithvi 这类 EO foundation model 的价值是用大规模遥感预训练特征降低下游标注量，再通过微调适配水体、农田和城市地物任务。",
        "sources": [
            {
                "label": "Prithvi EO 2.0 model card",
                "url": "https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M"
            },
            {
                "label": "NASA IMPACT HLS foundation examples",
                "url": "https://github.com/NASA-IMPACT/hls-foundation-os"
            }
        ]
    },
    {
        "id": "clay_geospatial_foundation",
        "name": "Clay Foundation Model",
        "domain": "遥感基础模型",
        "horizon": "下一批",
        "maturity": "可实践",
        "relevance": 90,
        "summary": "开源 Earth foundation model，面向 Sentinel、DEM、地球观测 embedding 和下游制图任务。",
        "why": "Clay 适合作为简历作品集里的开源 GeoAI 实验方向，用来展示你能把基础模型迁移到本地遥感场景。",
        "actions": [
            "补 Clay 安装与推理卡",
            "比较 Clay/Prithvi/传统CNN",
            "选一个池塘样本做 embedding 可视化"
        ],
        "interview": "我会把 Clay 看作开放 GeoAI 基座，用它做特征提取、微调和下游分类，再和传统 UNet/DeepLabv3 做效果对比。",
        "sources": [
            {
                "label": "Clay Foundation Model GitHub",
                "url": "https://github.com/Clay-foundation/model"
            }
        ]
    },
    {
        "id": "samgeo_remote_sensing",
        "name": "SAMGeo / Segment Geospatial",
        "domain": "遥感视觉",
        "horizon": "立即补",
        "maturity": "可实践",
        "relevance": 95,
        "summary": "把 Segment Anything 与 GeoTIFF、矢量数据、瓦片影像和 GIS 工作流结合起来做地理空间分割。",
        "why": "这和你江苏省养殖池塘上图入库项目直接相关，可以把 SAM 分割经验表达得更工程化。",
        "actions": [
            "补 SAMGeo 工具链卡",
            "整理 raster-to-vector 后处理",
            "把池塘图斑项目映射到 SAMGeo 流程"
        ],
        "interview": "SAM 用在遥感不能只点一下出 mask，还要处理坐标、瓦片、重叠、矢量化、拓扑修复和 GIS 入库。",
        "sources": [
            {
                "label": "segment-geospatial GitHub",
                "url": "https://github.com/opengeos/segment-geospatial"
            }
        ]
    },
    {
        "id": "remote_sensing_vlm_grounding",
        "name": "Remote Sensing VLM Grounding",
        "domain": "多模态遥感",
        "horizon": "下一批",
        "maturity": "新兴",
        "relevance": 91,
        "summary": "用视觉语言模型理解遥感图像、文本描述、地名、地物类别和空间关系，支持开放词汇识别与解释。",
        "why": "未来遥感算法岗位会从固定类别分割走向“文本查询 + 地物定位 + 证据解释”，适合你的 AI+遥感复合定位。",
        "actions": [
            "补开放词汇遥感检测卡",
            "设计文本提示识别养殖池塘/排口",
            "对比 CLIP/SAM/YOLO 组合流程"
        ],
        "interview": "遥感 VLM 的关键是把地物语义和空间定位连接起来，让模型能按文本提示找对象，并输出可解释证据。",
        "sources": [
            {
                "label": "AlphaEarth Foundations context",
                "url": "https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/"
            },
            {
                "label": "segment-geospatial GitHub",
                "url": "https://github.com/opengeos/segment-geospatial"
            }
        ]
    },
    {
        "id": "geospatial_embedding_retrieval",
        "name": "Geospatial Embedding Retrieval",
        "domain": "空间检索",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 89,
        "summary": "把影像块、矢量图斑、地物属性和文本标签编码成 embedding，支持相似区域检索、样本挖掘和少样本分类。",
        "why": "你的项目有大量池塘、断面、水体和报告证据，空间 embedding 可以帮助找相似样本、扩充训练集和做项目检索。",
        "actions": [
            "设计图斑 embedding 索引",
            "把错误样本做相似检索",
            "连接 RAG 证据库与 GIS 图斑"
        ],
        "interview": "我会把向量检索扩展到地理空间对象：影像 patch、图斑属性和文本标签一起入库，用于相似样本挖掘和快速制图。",
        "sources": [
            {
                "label": "AlphaEarth Satellite Embedding dataset",
                "url": "https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/"
            }
        ]
    },
    {
        "id": "few_shot_geoai_adaptation",
        "name": "Few-shot GeoAI Adaptation",
        "domain": "遥感算法",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 92,
        "summary": "利用遥感基础模型、少量标注、主动学习和难例挖掘，把模型快速适配到本地地物类别。",
        "why": "真实项目标注永远不够，养殖池塘、水体、排口、工业缺陷都需要少样本快速迭代能力。",
        "actions": [
            "设计主动学习闭环",
            "标注高不确定样本",
            "比较 fine-tune、LoRA 和线性探针"
        ],
        "interview": "我会用基础模型特征降低标注量，再通过主动学习挑难例，形成少样本适配和持续迭代闭环。",
        "sources": [
            {
                "label": "Prithvi EO 2.0 model card",
                "url": "https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M"
            },
            {
                "label": "Clay Foundation Model GitHub",
                "url": "https://github.com/Clay-foundation/model"
            }
        ]
    },
    {
        "id": "cloud_native_geospatial_stack",
        "name": "Cloud-native Geospatial Stack",
        "domain": "遥感数据工程",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 95,
        "summary": "以 STAC、COG、Zarr、GeoParquet、DuckDB Spatial 和动态瓦片服务构成云原生遥感数据处理底座。",
        "why": "遥感算法工程师不只训练模型，还要能把影像、矢量、索引、瓦片和接口组织成可复用的数据产品。",
        "actions": [
            "补一张云原生遥感架构图",
            "把池塘项目映射到 STAC/COG/GeoParquet",
            "设计本地轻量数据湖目录"
        ],
        "interview": "我会把遥感数据底座设计成云原生栈：STAC 做资产目录，COG/Zarr 做栅格访问，GeoParquet 做矢量分析，TiTiler 做在线瓦片。",
        "sources": [
            {
                "label": "STAC specification",
                "url": "https://stacspec.org/en"
            },
            {
                "label": "OGC Cloud Optimized GeoTIFF",
                "url": "https://docs.ogc.org/is/21-026/21-026.html"
            },
            {
                "label": "GeoParquet",
                "url": "https://geoparquet.org/"
            }
        ]
    },
    {
        "id": "stac_catalog_api",
        "name": "STAC Catalog / STAC API",
        "domain": "遥感数据工程",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 94,
        "summary": "用统一 JSON 结构描述时空资产、集合、链接、时间和空间范围，让多源遥感数据可发现、可索引、可检索。",
        "why": "你会处理 Sentinel、无人机、天地图和项目成果，STAC 能把这些影像和图斑产物纳入统一资产目录。",
        "actions": [
            "给项目成果定义 STAC Item",
            "记录 datetime/bbox/assets/properties",
            "预留 STAC API 查询入口"
        ],
        "interview": "STAC 的价值是把遥感资产描述标准化，避免每个数据源都写一套下载和解析逻辑。",
        "sources": [
            {
                "label": "STAC overview",
                "url": "https://stacspec.org/en"
            }
        ]
    },
    {
        "id": "cloud_optimized_geotiff",
        "name": "Cloud Optimized GeoTIFF (COG)",
        "domain": "遥感数据工程",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 93,
        "summary": "把 GeoTIFF 组织成支持 HTTP Range Request、内部瓦片和概览金字塔的云端可流式读取格式。",
        "why": "养殖池塘、断面溯源和水色专题图都需要快速预览、局部读取和在线制图，COG 是工程交付关键格式。",
        "actions": [
            "把输出影像转 COG",
            "生成 overview 和 tiling",
            "用局部读取替代整图下载"
        ],
        "interview": "COG 的关键是让大影像像网页资源一样按需读取，配合瓦片服务能显著提升遥感产品浏览和部署效率。",
        "sources": [
            {
                "label": "OGC COG Standard",
                "url": "https://docs.ogc.org/is/21-026/21-026.html"
            }
        ]
    },
    {
        "id": "zarr_xarray_datacube",
        "name": "Zarr / Xarray Data Cube",
        "domain": "时空数据",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 89,
        "summary": "用分块、压缩、N维数组格式承载多时相、多波段遥感和气象水文数据，适合 xarray/dask 并行分析。",
        "why": "水质、气象、遥感时序和模型预测天然是多维数据，Zarr 比一堆散文件更适合时空立方体分析。",
        "actions": [
            "把水质/影像时间序列抽象为 cube",
            "记录 chunk 策略",
            "比较 GeoTIFF 栈与 Zarr 读取性能"
        ],
        "interview": "当数据从单景影像变成多时相、多波段、多变量时，我会考虑 Zarr + xarray，把处理逻辑变成数据立方体计算。",
        "sources": [
            {
                "label": "Zarr overview",
                "url": "https://zarr.dev/"
            }
        ]
    },
    {
        "id": "geoparquet_vector_lake",
        "name": "GeoParquet Vector Lake",
        "domain": "空间数据工程",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 92,
        "summary": "用 Parquet 列式存储和地理空间元数据组织图斑、排口、断面、道路、水系等矢量数据。",
        "why": "你的项目有大量 shapefile/geojson/gpkg/excel 成果，GeoParquet 适合做高性能、可版本化、可分析的矢量数据湖。",
        "actions": [
            "把池塘图斑导出 GeoParquet",
            "记录 CRS 和 geometry 类型",
            "用 DuckDB 做面积/叠加统计"
        ],
        "interview": "传统 shapefile 适合交换，但生产分析我会优先考虑 GeoParquet，列式压缩、批量查询和数据湖生态更好。",
        "sources": [
            {
                "label": "GeoParquet",
                "url": "https://geoparquet.org/"
            }
        ]
    },
    {
        "id": "duckdb_spatial_analytics",
        "name": "DuckDB Spatial Analytics",
        "domain": "空间数据工程",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 90,
        "summary": "在本地用 DuckDB Spatial 直接查询 Parquet/GeoParquet/CSV，完成轻量级空间统计和数据质检。",
        "why": "求职软件和项目证据库都偏本地工作流，DuckDB Spatial 能在不搭 PostGIS 的情况下快速做空间数据分析。",
        "actions": [
            "写一个 GeoParquet 面积统计 demo",
            "替换部分 Excel 空间统计脚本",
            "建立矢量质检 SQL 模板"
        ],
        "interview": "我会按规模选工具：轻量本地分析用 DuckDB Spatial，团队级服务再上 PostGIS 或云数仓。",
        "sources": [
            {
                "label": "DuckDB Spatial extension",
                "url": "https://duckdb.org/docs/stable/core_extensions/spatial/overview"
            }
        ]
    },
    {
        "id": "titiler_dynamic_tiles",
        "name": "TiTiler Dynamic Raster Tiles",
        "domain": "遥感服务化",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 88,
        "summary": "把 COG、STAC 和栅格算法封装成动态瓦片服务，实现在线预览、渲染、指数计算和产品发布。",
        "why": "遥感成果不能只停留在离线图件，在线瓦片服务能让养殖池塘、水色指数和断面溯源产品更像商用系统。",
        "actions": [
            "设计 COG + TiTiler 预览链路",
            "增加指数渲染参数",
            "把专题图推送变成 URL 产品"
        ],
        "interview": "我会用 TiTiler 把遥感影像服务化：前端只请求瓦片，后端按需读取 COG 并动态渲染指数或分类结果。",
        "sources": [
            {
                "label": "TiTiler docs",
                "url": "https://developmentseed.org/titiler/"
            }
        ]
    },
    {
        "id": "overture_maps_gers",
        "name": "Overture Maps / GERS",
        "domain": "地图数据",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 83,
        "summary": "开放地图数据和 Global Entity Reference System，为道路、建筑、POI 等实体提供稳定 ID 和统一 schema。",
        "why": "遥感结果要和建筑、道路、行政区、兴趣点等底图实体联动，稳定实体 ID 有助于做数据融合和变化追踪。",
        "actions": [
            "补建筑/道路底图融合卡",
            "研究 GERS 稳定 ID",
            "对接遥感提取图斑与开放地图实体"
        ],
        "interview": "遥感识别结果要进入业务系统，关键不只是检测到对象，还要和稳定地图实体、行政区和业务属性关联。",
        "sources": [
            {
                "label": "Overture Maps",
                "url": "https://overturemaps.org/"
            }
        ]
    },
    {
        "id": "pmtiles_static_tile_delivery",
        "name": "PMTiles Static Tile Delivery",
        "domain": "地图服务化",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 82,
        "summary": "把矢量或栅格瓦片打包成单文件，通过静态对象存储分发，降低地图服务部署复杂度。",
        "why": "求职作品集和遥感产品展示需要低成本部署，PMTiles 适合静态托管专题图和项目演示。",
        "actions": [
            "把一个矢量图层转成 PMTiles",
            "测试静态托管地图展示",
            "比较 MBTiles/PMTiles/在线服务"
        ],
        "interview": "如果只是展示专题成果，我会考虑 PMTiles 这类静态瓦片方案，避免为一个演示系统维护完整地图服务器。",
        "sources": [
            {
                "label": "PMTiles",
                "url": "https://pmtiles.io/"
            }
        ]
    },
    {
        "id": "spatiotemporal_feature_store",
        "name": "Spatiotemporal Feature Store",
        "domain": "特征工程",
        "horizon": "下一批",
        "maturity": "新兴",
        "relevance": 91,
        "summary": "把水质、气象、影像指数、空间邻域、时间滞后和业务标签统一管理，服务预测、分类和溯源模型。",
        "why": "你的水质 LSTM、污水厂优化、池塘识别和断面溯源都依赖时空特征；特征管理能把项目经验复用起来。",
        "actions": [
            "定义时空特征 schema",
            "记录特征血缘和窗口",
            "把 LSTM 与遥感指数特征统一入库"
        ],
        "interview": "我会把模型前的数据准备沉淀成时空特征库，管理时间窗口、空间邻域、数据血缘和训练/推理一致性。",
        "sources": [
            {
                "label": "STAC assets context",
                "url": "https://stacspec.org/en"
            },
            {
                "label": "GeoParquet",
                "url": "https://geoparquet.org/"
            }
        ]
    },
    {
        "id": "computer_use_agents",
        "name": "Computer Use Agents (CUA)",
        "domain": "自动化执行",
        "horizon": "立即补",
        "maturity": "快速落地",
        "relevance": 93,
        "summary": "让模型通过截图、坐标、键鼠、浏览器和应用状态来完成真实 GUI 操作任务。",
        "why": "求职助手后续要做网页投递、表单填写、简历导出和资料上传，CUA 是从“生成文本”走向“执行任务”的关键能力。",
        "actions": [
            "定义浏览器/本地应用操作边界",
            "为投递任务加入人工确认",
            "记录每步截图和动作日志"
        ],
        "interview": "Computer Use Agent 的核心不是能点鼠标，而是把观察、计划、动作、失败恢复和权限确认组织成可审计执行链。",
        "sources": [
            {
                "label": "OpenAI computer use guide",
                "url": "https://platform.openai.com/docs/guides/tools-computer-use"
            }
        ]
    },
    {
        "id": "browser_use_workflows",
        "name": "Browser-use / Web Task Agents",
        "domain": "浏览器 Agent",
        "horizon": "立即补",
        "maturity": "快速落地",
        "relevance": 91,
        "summary": "用浏览器自动化 Agent 完成网页检索、表单填写、页面理解、下载上传和多步骤 Web 工作流。",
        "why": "岗位投递、JD 抓取、公司研究和作品集发布都发生在浏览器里，浏览器 Agent 是求职软件商业化关键模块。",
        "actions": [
            "设计 JD 抓取和职位归档流程",
            "加入域名白名单和外发确认",
            "保存页面快照和证据链接"
        ],
        "interview": "我会把浏览器 Agent 用在可审计的 Web 工作流中：页面解析、表单动作、下载上传和失败恢复都要有日志。",
        "sources": [
            {
                "label": "Browser Use docs",
                "url": "https://docs.browser-use.com/"
            }
        ]
    },
    {
        "id": "osworld_gui_benchmark",
        "name": "OSWorld / GUI Agent Benchmark",
        "domain": "评测体系",
        "horizon": "下一批",
        "maturity": "新兴",
        "relevance": 86,
        "summary": "面向真实操作系统和桌面应用的多模态 Agent 基准，用任务完成率评估 GUI 操作能力。",
        "why": "如果后续要做自动化办公和投递，不能只看模型回答，还要评估真实 GUI 任务是否完成。",
        "actions": [
            "建立本地简历导出 GUI 评测任务",
            "记录成功率和失败原因",
            "区分网页任务与桌面任务"
        ],
        "interview": "GUI Agent 评测要看任务完成率、动作轨迹、恢复能力和安全边界，而不是只看模型是否描述正确。",
        "sources": [
            {
                "label": "OSWorld benchmark",
                "url": "https://os-world.github.io/"
            }
        ]
    },
    {
        "id": "ui_tars_gui_agents",
        "name": "UI-TARS / Native GUI Agents",
        "domain": "多模态 Agent",
        "horizon": "下一批",
        "maturity": "前沿",
        "relevance": 84,
        "summary": "面向图形界面的视觉-动作模型，把屏幕理解、控件定位、动作生成和任务规划结合起来。",
        "why": "你熟悉自动化办公和软件搭建，GUI Agent 能把本地桌面软件、浏览器和 GIS 工具串成更完整的自动化链路。",
        "actions": [
            "补 GUI Agent 架构卡",
            "设计 QGIS/浏览器低风险演示任务",
            "把动作日志纳入安全审计"
        ],
        "interview": "GUI Agent 的难点在于屏幕语义理解、控件定位、动作规划和错误恢复，必须和权限策略、沙箱和日志结合。",
        "sources": [
            {
                "label": "UI-TARS GitHub",
                "url": "https://github.com/bytedance/UI-TARS"
            }
        ]
    },
    {
        "id": "pangaea_geo_benchmark",
        "name": "PANGAEA / Geospatial FM Benchmark",
        "domain": "遥感评测",
        "horizon": "立即补",
        "maturity": "前沿",
        "relevance": 92,
        "summary": "面向地球观测基础模型的多任务评测，用统一基准比较分类、分割、变化检测和多源遥感能力。",
        "why": "遥感基础模型越来越多，面试中要能讲清楚不只看模型名，还要看任务、数据集、迁移方式和评测指标。",
        "actions": [
            "补遥感基础模型评测卡",
            "列出分类/分割/变化检测指标",
            "比较 Prithvi/Clay/AlphaEarth 使用场景"
        ],
        "interview": "评价 GeoAI 基础模型要看跨传感器、跨区域、少样本和下游任务表现，而不是只看预训练规模。",
        "sources": [
            {
                "label": "PANGAEA benchmark",
                "url": "https://github.com/VMarsocci/pangaea-bench"
            }
        ]
    },
    {
        "id": "terramind_multimodal_eo",
        "name": "TerraMind / Multimodal EO Foundation Model",
        "domain": "遥感基础模型",
        "horizon": "下一批",
        "maturity": "前沿",
        "relevance": 90,
        "summary": "多模态地球观测基础模型方向，强调跨光学、SAR、时序、文本和多任务遥感表征。",
        "why": "你的遥感项目未来不应局限单一光学影像，SAR、DEM、水文、气象和文本报告都可成为模型输入。",
        "actions": [
            "补多模态 EO 输入矩阵",
            "整理光学/SAR/DEM/气象融合场景",
            "设计水体和滩涂多源特征实验"
        ],
        "interview": "遥感基础模型的下一步是多模态：不同传感器和时序数据要在统一表征空间里服务分类、分割和变化分析。",
        "sources": [
            {
                "label": "TerraMind paper",
                "url": "https://arxiv.org/abs/2504.11171"
            }
        ]
    },
    {
        "id": "dinov3_self_supervised_vision",
        "name": "DINOv3 / Self-supervised Vision Backbone",
        "domain": "视觉基础模型",
        "horizon": "立即补",
        "maturity": "前沿",
        "relevance": 91,
        "summary": "自监督视觉骨干网络方向，通过大规模无标注图像学习通用特征，适合少样本迁移到分割、检测和遥感任务。",
        "why": "你做的水体、建筑、池塘、工业缺陷都面临标注少的问题，自监督 backbone 是提升泛化能力的重要路线。",
        "actions": [
            "补自监督视觉骨干卡",
            "对比 DINO/MAE/CLIP 特征",
            "设计少样本池塘分类实验"
        ],
        "interview": "自监督视觉模型的价值是用无标注数据学通用表征，再用较少标注迁移到遥感分割和目标检测任务。",
        "sources": [
            {
                "label": "Meta DINOv3",
                "url": "https://github.com/facebookresearch/dinov3"
            }
        ]
    },
    {
        "id": "grounded_sam_pipeline",
        "name": "Grounded SAM / Open-vocabulary Segmentation",
        "domain": "遥感视觉",
        "horizon": "立即补",
        "maturity": "可实践",
        "relevance": 95,
        "summary": "把开放词汇检测、文本提示定位和 SAM 分割组合起来，实现“按文字找对象并输出 mask”。",
        "why": "这和你的养殖池塘、建筑、水体、排口、鸟类和江豚识别都高度相关，可把固定类别模型升级为文本驱动流程。",
        "actions": [
            "整理 GroundingDINO + SAM 流程",
            "做水体/建筑/池塘文本提示样例",
            "记录误检和提示词优化策略"
        ],
        "interview": "开放词汇分割通常是先用文本提示定位候选框，再用 SAM 精细分割，最后做 GIS 后处理和人工校核。",
        "sources": [
            {
                "label": "Grounded-SAM GitHub",
                "url": "https://github.com/IDEA-Research/Grounded-Segment-Anything"
            },
            {
                "label": "Grounding DINO GitHub",
                "url": "https://github.com/IDEA-Research/GroundingDINO"
            }
        ]
    },
    {
        "id": "sam2_video_geospatial",
        "name": "SAM 2 for Video & Temporal Geospatial",
        "domain": "遥感视觉",
        "horizon": "下一批",
        "maturity": "可实践",
        "relevance": 88,
        "summary": "SAM 2 的视频/时序分割能力可迁移到无人机视频、连续巡检和多时相遥感变化分析。",
        "why": "你会无人机航测和水域巡查，时序分割能支持持续追踪水体、船只、鸟类、污染带和养殖设施变化。",
        "actions": [
            "补 SAM 2 时序记忆机制卡",
            "设计无人机视频水体/鸟类分割 demo",
            "比较单帧 SAM 与时序 SAM"
        ],
        "interview": "SAM 2 的关键是把分割从单张图扩展到有记忆的视频对象追踪，适合无人机巡检和连续变化监测。",
        "sources": [
            {
                "label": "Meta SAM 2 GitHub",
                "url": "https://github.com/facebookresearch/sam2"
            }
        ]
    },
    {
        "id": "rf_detr_realtime_detection",
        "name": "RF-DETR / Real-time Transformer Detection",
        "domain": "目标检测",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 87,
        "summary": "实时 DETR 系列把 Transformer 检测器推向工业可用速度，适合与 YOLO 路线做对比。",
        "why": "你的 Roboflow、鸟类、江豚、工业缺陷检测经历需要持续跟进检测器新路线，不只停留在 YOLO。",
        "actions": [
            "补 YOLO vs DETR 对比卡",
            "记录实时检测指标 FPS/mAP/延迟",
            "选一个 Roboflow 数据集做路线对比"
        ],
        "interview": "目标检测我会按任务约束选模型：YOLO 强在成熟部署，DETR 系列强在端到端匹配和全局关系，最终看 mAP、延迟和误检类型。",
        "sources": [
            {
                "label": "RF-DETR Roboflow",
                "url": "https://github.com/roboflow/rf-detr"
            }
        ]
    },
    {
        "id": "vllm_paged_attention",
        "name": "vLLM / PagedAttention",
        "domain": "推理系统",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 94,
        "summary": "通过把 KV cache 切成非连续 block 管理，降低显存碎片，提高并发吞吐，是开源 LLM Serving 的核心路线之一。",
        "why": "你要做商用求职助手和 RAG 平台，后端不能只会调 API，还要知道模型服务如何支撑并发、长上下文和成本控制。",
        "actions": [
            "补 PagedAttention 原理卡",
            "记录 TTFT/TPOT/吞吐指标",
            "设计本地 vLLM Serving 实验"
        ],
        "interview": "我会把 vLLM 的价值讲成显存管理问题：PagedAttention 让 KV cache 像分页内存一样按需分配，提升多请求并发效率。",
        "sources": [
            {
                "label": "vLLM prefix caching design",
                "url": "https://docs.vllm.ai/en/stable/design/prefix_caching/"
            }
        ]
    },
    {
        "id": "automatic_prefix_caching",
        "name": "Automatic Prefix Caching",
        "domain": "推理优化",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 93,
        "summary": "复用相同系统提示、工具说明、长证据和固定上下文的 KV cache，减少重复 prefill 计算。",
        "why": "你的简历、项目证据、知识库和 JD 模板会被反复使用，prefix caching 能直接降低延迟和成本。",
        "actions": [
            "拆分稳定前缀和动态输入",
            "记录缓存命中率",
            "给简历证据库设计可缓存 prompt 模板"
        ],
        "interview": "我会把上下文分成稳定前缀和动态部分，对稳定的系统提示、证据库说明和简历材料做 prefix caching。",
        "sources": [
            {
                "label": "vLLM automatic prefix caching",
                "url": "https://docs.vllm.ai/en/stable/design/prefix_caching/"
            }
        ]
    },
    {
        "id": "sglang_radix_attention",
        "name": "SGLang / RadixAttention",
        "domain": "推理系统",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 91,
        "summary": "SGLang 面向结构化多轮 LLM 程序，RadixAttention 复用多次生成调用之间的 KV cache。",
        "why": "Agent、RAG、简历润色和多步骤 JD 分析往往是多轮生成程序，SGLang 这类 runtime 能减少重复计算。",
        "actions": [
            "补 SGLang 程序化生成卡",
            "比较 vLLM 与 SGLang",
            "把多步骤简历优化拆成可缓存生成调用"
        ],
        "interview": "SGLang 的价值在于把复杂 LLM 调用变成可编排程序，并用 RadixAttention 复用公共前缀和中间 KV cache。",
        "sources": [
            {
                "label": "SGLang documentation",
                "url": "https://docs.sglang.ai/"
            },
            {
                "label": "SGLang GitHub",
                "url": "https://github.com/sgl-project/sglang"
            }
        ]
    },
    {
        "id": "disaggregated_prefill_decode",
        "name": "Disaggregated Prefill/Decode Serving",
        "domain": "推理架构",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 90,
        "summary": "把长上下文 prefill 和逐 token decode 分离到不同 worker 池，独立扩缩容并转移 KV cache。",
        "why": "长简历、长文档 RAG 和多轮 Agent 对 prefill 与 decode 的算力需求不同，分离架构能降低成本并提升吞吐。",
        "actions": [
            "补 prefill/decode 性能差异卡",
            "画 KV cache 转移链路",
            "记录适用场景和成本权衡"
        ],
        "interview": "Prefill 是一次性处理长上下文，decode 是逐 token 生成；把二者分离可以按瓶颈独立扩容。",
        "sources": [
            {
                "label": "NVIDIA Dynamo disaggregated serving",
                "url": "https://docs.nvidia.com/dynamo/v-0-7-1/design-docs/disaggregated-serving"
            }
        ]
    },
    {
        "id": "lmcache_kv_reuse",
        "name": "LMCache / Persistent KV Cache",
        "domain": "推理优化",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 89,
        "summary": "把 KV cache 从一次性临时状态变成可跨请求、跨会话、跨引擎复用的缓存层。",
        "why": "求职系统会反复读取同一批材料，持久化 KV cache 能服务长上下文 Agent、RAG 和多轮对话。",
        "actions": [
            "补 KV cache 生命周期卡",
            "区分 GPU/CPU/磁盘分层缓存",
            "设计证据库长前缀复用实验"
        ],
        "interview": "LMCache 的思路是 prefill once, reuse everywhere，把长上下文的计算结果作为缓存资产复用。",
        "sources": [
            {
                "label": "LMCache documentation",
                "url": "https://docs.lmcache.ai/"
            }
        ]
    },
    {
        "id": "kv_aware_routing",
        "name": "KV-aware Routing",
        "domain": "推理架构",
        "horizon": "下一批",
        "maturity": "新兴",
        "relevance": 87,
        "summary": "路由请求时考虑哪台 worker 已有相关 KV cache，尽量减少重复 prefill 和跨节点传输。",
        "why": "多用户、多岗位、多文档场景中，很多请求共享同一简历和项目证据，KV-aware routing 能提高缓存收益。",
        "actions": [
            "设计 session/document affinity",
            "记录 cache hit/miss",
            "比较普通负载均衡与 KV-aware 路由"
        ],
        "interview": "当 KV cache 成为资源后，路由就不能只看负载，还要看哪台机器已有可复用上下文。",
        "sources": [
            {
                "label": "NVIDIA Dynamo GitHub",
                "url": "https://github.com/ai-dynamo/dynamo"
            },
            {
                "label": "LMCache documentation",
                "url": "https://docs.lmcache.ai/"
            }
        ]
    },
    {
        "id": "continuous_batching",
        "name": "Continuous Batching",
        "domain": "推理系统",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 88,
        "summary": "在生成过程中动态加入和移除请求，避免固定 batch 等待，让不同长度请求共享 GPU 计算。",
        "why": "商用 AI 系统请求长度差异很大，连续批处理是提高 GPU 利用率和降低排队延迟的基础手段。",
        "actions": [
            "补动态 batch 调度卡",
            "记录吞吐和延迟指标",
            "解释短请求被长请求拖慢的问题"
        ],
        "interview": "Continuous batching 解决的是请求长度不一致导致 GPU 空转的问题，让服务端在生成中动态调度 batch。",
        "sources": [
            {
                "label": "SGLang GitHub runtime features",
                "url": "https://github.com/sgl-project/sglang"
            }
        ]
    },
    {
        "id": "structured_generation_runtime",
        "name": "Structured Generation Runtime",
        "domain": "结构化输出",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 92,
        "summary": "在推理阶段用 grammar、schema、constrained decoding 或 runtime 校验保证输出 JSON、表格、工具参数等结构正确。",
        "why": "简历 JSON、JD 解析、知识雷达条目和项目证据必须结构稳定，不能只靠提示词祈祷模型听话。",
        "actions": [
            "为雷达条目定义 JSON schema",
            "给导入导出加结构校验",
            "记录模型输出修复策略"
        ],
        "interview": "结构化输出要在 runtime 层约束或校验，schema、grammar 和错误重试比单纯 prompt 更可靠。",
        "sources": [
            {
                "label": "SGLang structured outputs",
                "url": "https://sgl-project.github.io/advanced_features/structured_outputs.html"
            }
        ]
    },
    {
        "id": "llm_slo_cost_governance",
        "name": "LLM SLO / Cost Governance",
        "domain": "工程运维",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 91,
        "summary": "用 TTFT、TPOT、吞吐、错误率、缓存命中率、每任务成本和成功率定义 LLM 应用服务目标。",
        "why": "商用求职系统需要可控成本和稳定体验，不能只说模型效果好，还要能讲延迟、成本、缓存和失败率。",
        "actions": [
            "定义雷达/简历/JD 分析 SLO",
            "记录 token 与调用成本",
            "按任务路由快慢模型"
        ],
        "interview": "我会把 LLM 应用按任务定义 SLO：首 token 延迟、总耗时、成功率、每次任务成本和缓存命中率都要监控。",
        "sources": [
            {
                "label": "OpenTelemetry GenAI semantic conventions",
                "url": "https://opentelemetry.io/docs/specs/semconv/gen-ai/"
            },
            {
                "label": "vLLM metrics docs",
                "url": "https://docs.vllm.ai/en/stable/serving/metrics.html"
            }
        ]
    },
    {
        "id": "quantized_llm_serving",
        "name": "Quantized LLM Serving",
        "domain": "模型压缩",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 86,
        "summary": "用 FP8、INT4、AWQ、GPTQ 等量化方式降低显存和成本，在精度、速度和部署门槛之间做权衡。",
        "why": "本地或私有化部署求职助手、RAG 和小模型分类时，量化是降低硬件成本的重要手段。",
        "actions": [
            "补量化格式对比卡",
            "区分权重量化和 KV cache 量化",
            "记录精度损失与吞吐收益"
        ],
        "interview": "量化不是越低比特越好，要看任务精度、显存、吞吐、延迟和模型兼容性，必要时保留关键模块精度。",
        "sources": [
            {
                "label": "SGLang quantization support",
                "url": "https://github.com/sgl-project/sglang"
            }
        ]
    },
    {
        "id": "dspy_prompt_compilation",
        "name": "DSPy / Prompt Compilation",
        "domain": "评测驱动优化",
        "horizon": "立即补",
        "maturity": "快速落地",
        "relevance": 92,
        "summary": "把 prompt 手工调参升级为“程序 + 示例集 + 指标”的自动优化，用优化器搜索更高分的指令和示例。",
        "why": "你的简历润色、项目证据提取、JD 匹配和雷达收录都可以用小样本评测集驱动 prompt 迭代，而不是凭感觉改词。",
        "actions": [
            "为简历润色建 20 条训练样例",
            "定义事实准确率和岗位匹配指标",
            "用 DSPy 优化 RAG/分类 prompt"
        ],
        "interview": "我会把 prompt 当成可编译资产：给出训练样例和 metric，让 DSPy 这类优化器自动搜索更稳的指令和示例组合。",
        "sources": [
            {
                "label": "DSPy GEPA optimization",
                "url": "https://dspy.ai/getting-started/gepa-optimization/"
            },
            {
                "label": "DSPy docs",
                "url": "https://dspy.ai/"
            }
        ]
    },
    {
        "id": "ragas_component_metrics",
        "name": "Ragas Component Metrics",
        "domain": "RAG 评测",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 94,
        "summary": "用 context precision、context recall、faithfulness、response relevancy 等指标分别评估检索器和生成器。",
        "why": "项目证据库和简历生成最怕“看起来很顺但证据不支持”，Ragas 指标能把问题拆到检索、排序、回答三个环节。",
        "actions": [
            "为项目证据库建立 RAGAS 评测集",
            "分别记录 context precision 和 faithfulness",
            "失败样例回流到切片/重排策略"
        ],
        "interview": "RAG 评测不能只看最终答案，要拆成检索是否找对、排序是否靠前、回答是否忠实证据、语言是否相关。",
        "sources": [
            {
                "label": "Ragas metrics list",
                "url": "https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/"
            },
            {
                "label": "Ragas faithfulness",
                "url": "https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/"
            }
        ]
    },
    {
        "id": "hybrid_search_rrf_rerank",
        "name": "Hybrid Search + RRF + Rerank",
        "domain": "检索系统",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 91,
        "summary": "结合 BM25 关键词检索、向量检索、RRF 融合和 cross-encoder 重排，提高术语、编号、路径和语义检索的综合召回。",
        "why": "你的文档里有大量项目名、路径、指标、中文术语和英文技术词，纯向量或纯关键词都容易漏召回。",
        "actions": [
            "为证据库加 BM25 + embedding 双路检索",
            "实现 RRF 融合",
            "对 top50 做 rerank"
        ],
        "interview": "我会用 hybrid search 解决术语和语义的双重召回问题，再用 reranker 提升 top-k 精度。",
        "sources": [
            {
                "label": "LangChain retrieval docs",
                "url": "https://docs.langchain.com/oss/python/langchain/retrieval"
            },
            {
                "label": "Elasticsearch hybrid search in LangChain",
                "url": "https://www.elastic.co/search-labs/blog/langchain-elasticsearch-hybrid-search"
            }
        ]
    },
    {
        "id": "colpali_visual_document_retrieval",
        "name": "ColPali / Visual Document Retrieval",
        "domain": "多模态检索",
        "horizon": "立即补",
        "maturity": "快速落地",
        "relevance": 90,
        "summary": "直接把 PDF 页面作为图像编码检索，利用 VLM 和 late interaction 处理表格、图件、版式和扫描文档。",
        "why": "你有大量投标文件、汇报 PDF、图件和扫描式材料，传统 OCR + 文本切片会丢失版式与图表信息。",
        "actions": [
            "选一份投标 PDF 做视觉检索 demo",
            "比较 OCR RAG 与 ColPali RAG",
            "保留页图和引用区域"
        ],
        "interview": "对于图表密集的 PDF，我会考虑 ColPali 这类视觉文档检索，直接检索页面图像特征，而不是只依赖 OCR 文本。",
        "sources": [
            {
                "label": "ColPali GitHub",
                "url": "https://github.com/illuin-tech/colpali"
            },
            {
                "label": "ColPali Hugging Face blog",
                "url": "https://huggingface.co/blog/manu/colpali"
            }
        ]
    },
    {
        "id": "late_interaction_retrieval",
        "name": "Late Interaction Retrieval / ColBERT",
        "domain": "检索系统",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 86,
        "summary": "保留 query 与文档 token 级交互，而不是压成单个向量，兼顾语义细粒度和可扩展检索。",
        "why": "技术文档和岗位 JD 里很多细节靠单向量会被平均掉，late interaction 更适合找精确术语和上下文。",
        "actions": [
            "补 ColBERT/ColPali 对比卡",
            "标记适合 late interaction 的长文档场景",
            "评估索引成本和召回收益"
        ],
        "interview": "Late interaction 的价值是避免把整段文本压成一个向量，保留 token 级匹配能力，适合细粒度技术检索。",
        "sources": [
            {
                "label": "ColPali GitHub",
                "url": "https://github.com/illuin-tech/colpali"
            }
        ]
    },
    {
        "id": "llm_judge_calibration",
        "name": "LLM-as-Judge Calibration",
        "domain": "评测体系",
        "horizon": "立即补",
        "maturity": "生产化",
        "relevance": 89,
        "summary": "用标注样本、rubric、一致性检查和人工抽检校准 LLM 评审，避免模型评测自嗨。",
        "why": "简历质量、项目表述真实性、JD 匹配度都可能用 LLM 评分，但评分器本身必须被校准。",
        "actions": [
            "为简历评分建立人工 gold set",
            "固定 rubric 与反例",
            "监控评审一致性和偏差"
        ],
        "interview": "LLM-as-judge 要有 gold set、rubric、pairwise 对比和人工抽检，否则评分只是另一个不稳定模型输出。",
        "sources": [
            {
                "label": "LangSmith evaluation concepts",
                "url": "https://docs.langchain.com/langsmith/evaluation-concepts"
            },
            {
                "label": "OpenAI Evals",
                "url": "https://github.com/openai/evals"
            }
        ]
    },
    {
        "id": "active_learning_data_engine",
        "name": "Active Learning Data Engine",
        "domain": "数据闭环",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 90,
        "summary": "把低置信度、误检、冲突样本和用户反馈回流到标注、训练、评测和再部署流程。",
        "why": "遥感分割、目标检测、RAG 证据检索和简历生成都会持续遇到难例，主动学习能让系统越用越准。",
        "actions": [
            "建立错误样本池",
            "按不确定性挑样本",
            "记录样本版本和模型版本"
        ],
        "interview": "我会把模型上线后的错误样本和人工反馈变成数据引擎，用主动学习挑最有价值的样本去标注和再训练。",
        "sources": [
            {
                "label": "Label Studio active learning guide",
                "url": "https://labelstud.io/guide/active_learning"
            }
        ]
    },
    {
        "id": "synthetic_eval_dataset",
        "name": "Synthetic Eval Dataset Generation",
        "domain": "评测体系",
        "horizon": "下一批",
        "maturity": "快速落地",
        "relevance": 87,
        "summary": "用模型辅助生成边界问题、反例、困难样例和多样化查询，再由人工或规则筛选成评测集。",
        "why": "求职系统场景多、真实失败样本少，合成评测能快速覆盖 JD 歧义、证据错配、幻觉和格式错误。",
        "actions": [
            "生成 JD/简历/证据错配样例",
            "人工审核合成样本",
            "把失败样本沉淀为回归集"
        ],
        "interview": "我会用合成数据扩展评测覆盖面，但关键样本必须人工审核，避免把模型的偏差复制进评测集。",
        "sources": [
            {
                "label": "Ragas testset generation docs",
                "url": "https://docs.ragas.io/en/stable/concepts/test_data_generation/"
            }
        ]
    },
    {
        "id": "model_data_cards_lineage",
        "name": "Model Cards / Data Cards / Lineage",
        "domain": "模型治理",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 88,
        "summary": "为模型、数据集、评测集、限制条件和适用场景建立文档与血缘，方便审计、交接和复现。",
        "why": "你的项目横跨遥感、水处理、养殖和 RAG，只有把数据来源、模型版本和评测记录写清楚，作品集才更可信。",
        "actions": [
            "为雷达/简历/作品集数据建 data card",
            "记录模型版本和训练数据",
            "把评测结果写入变更记录"
        ],
        "interview": "我会给模型和数据都建 card：来源、版本、适用范围、限制、评测指标和已知风险都要可追溯。",
        "sources": [
            {
                "label": "Hugging Face model cards",
                "url": "https://huggingface.co/docs/hub/model-cards"
            },
            {
                "label": "Hugging Face dataset cards",
                "url": "https://huggingface.co/docs/hub/datasets-cards"
            }
        ]
    },
    {
        "id": "ai_supply_chain_provenance",
        "name": "AI Supply Chain Provenance",
        "domain": "AI 安全",
        "horizon": "下一批",
        "maturity": "生产化",
        "relevance": 86,
        "summary": "追踪模型、数据、依赖、权重、许可证、构建过程和部署产物来源，降低供应链和合规风险。",
        "why": "后续接入开源模型、遥感数据和自动化工具时，必须知道权重、数据和依赖是否可信、可用、可商用。",
        "actions": [
            "记录模型许可证和来源",
            "为依赖生成清单",
            "给外部模型加入安全与合规检查"
        ],
        "interview": "AI 供应链治理要追踪模型权重、数据来源、依赖版本、许可证和构建过程，避免把不可控资产带进生产系统。",
        "sources": [
            {
                "label": "SLSA framework",
                "url": "https://slsa.dev/"
            },
            {
                "label": "CycloneDX ML-BOM",
                "url": "https://cyclonedx.org/capabilities/mlbom/"
            }
        ]
    }
];;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

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
