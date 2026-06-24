# 知识雷达更新记录

## 2026-06-23：Agent 工程化补强

本轮新增 10 个前沿概念，重点围绕商用 Agent 系统从 demo 到生产可用所需的工程能力。

## 新增条目

- Deep Agents / Agent Harness
- Agent Handoffs / Specialist Routing
- Tool Guardrails / Tripwires
- MCP Roots / Elicitation / Sampling
- Virtual Filesystem for Agents
- Agent Permission Policy
- Sandboxed Computer Use
- Agent Event Streaming
- Prompt Caching Strategy
- Agent Primitives: Plan / Act / Observe / Evaluate

## 选词原则

- 必须能转化为求职面试表达，而不是只收录热词。
- 必须能落到当前软件建设路线，例如简历优化、证据库、JD 匹配、Git 同步、自动化导出。
- 优先收录官方文档或主流工程框架已经形成稳定概念的内容。

## 主要参考源

- OpenAI Agents SDK：`https://openai.github.io/openai-agents-python/`
- OpenAI Agents Handoffs：`https://openai.github.io/openai-agents-python/handoffs/`
- OpenAI Agents Guardrails：`https://openai.github.io/openai-agents-python/guardrails/`
- Model Context Protocol 2025-06-18 Specification：`https://modelcontextprotocol.io/specification/2025-06-18`
- LangGraph：`https://langchain-ai.github.io/langgraph/`
- LangChain Deep Agents：`https://docs.langchain.com/oss/python/deepagents/overview`

## 后续待收录方向

- Agent evaluation harness
- Tool-use replay and deterministic regression
- Browser-use agents for job application workflows
- Personal knowledge vault with evidence-level permissions
- Multi-modal remote-sensing VLM workflows
- Edge/on-device agent routing

## 2026-06-23：协议、安全、评测与 GeoAI 补强

本轮新增 12 个条目，补齐 Agent 互操作协议、Agent UI、标准化安全框架、生产评测，以及 AI算法/遥感算法工程师方向必须跟进的地球观测基础模型。

## 新增条目

- Agent2Agent Protocol (A2A)
- AG-UI / Agent User Interaction Protocol
- OWASP LLM Top 10 2025
- Agent Eval Regression
- OpenTelemetry GenAI Semantic Conventions
- AlphaEarth Foundations / Satellite Embeddings
- Prithvi EO 2.0 / HLS Foundation Model
- Clay Foundation Model
- SAMGeo / Segment Geospatial
- Remote Sensing VLM Grounding
- Geospatial Embedding Retrieval
- Few-shot GeoAI Adaptation

## 主要参考源

- Google A2A：`https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/`
- AG-UI：`https://docs.ag-ui.com/`
- OWASP LLM Top 10：`https://owasp.org/www-project-top-10-for-large-language-model-applications/`
- LangSmith Evaluation：`https://docs.langchain.com/langsmith/evaluation-concepts`
- OpenTelemetry GenAI：`https://opentelemetry.io/docs/specs/semconv/gen-ai/`
- AlphaEarth Foundations：`https://deepmind.google/blog/alphaearth-foundations-helps-map-our-planet-in-unprecedented-detail/`
- Prithvi EO 2.0：`https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M`
- Clay Foundation Model：`https://github.com/Clay-foundation/model`
- SAMGeo：`https://github.com/opengeos/segment-geospatial`

## 2026-06-23：云原生地理空间工程栈补强

本轮新增 10 个条目，补齐遥感算法工程师从离线脚本走向商用产品时必须掌握的数据底座：资产目录、云优化栅格、矢量数据湖、时空立方体、动态瓦片和低成本地图发布。

## 新增条目

- Cloud-native Geospatial Stack
- STAC Catalog / STAC API
- Cloud Optimized GeoTIFF (COG)
- Zarr / Xarray Data Cube
- GeoParquet Vector Lake
- DuckDB Spatial Analytics
- TiTiler Dynamic Raster Tiles
- Overture Maps / GERS
- PMTiles Static Tile Delivery
- Spatiotemporal Feature Store

## 主要参考源

- STAC：`https://stacspec.org/en`
- OGC Cloud Optimized GeoTIFF：`https://docs.ogc.org/is/21-026/21-026.html`
- Zarr：`https://zarr.dev/`
- GeoParquet：`https://geoparquet.org/`
- DuckDB Spatial：`https://duckdb.org/docs/stable/core_extensions/spatial/overview`
- TiTiler：`https://developmentseed.org/titiler/`
- Overture Maps：`https://overturemaps.org/`
- PMTiles：`https://pmtiles.io/`

## 2026-06-23：Computer Use、浏览器 Agent 与开放词汇视觉补强

本轮新增 10 个条目，覆盖能真实操作网页/桌面的 Agent、GUI Agent 评测，以及遥感视觉中更贴近项目落地的开放词汇检测、时序分割、自监督视觉骨干和实时 DETR 检测器。

## 新增条目

- Computer Use Agents (CUA)
- Browser-use / Web Task Agents
- OSWorld / GUI Agent Benchmark
- UI-TARS / Native GUI Agents
- PANGAEA / Geospatial FM Benchmark
- TerraMind / Multimodal EO Foundation Model
- DINOv3 / Self-supervised Vision Backbone
- Grounded SAM / Open-vocabulary Segmentation
- SAM 2 for Video & Temporal Geospatial
- RF-DETR / Real-time Transformer Detection

## 主要参考源

- OpenAI Computer Use：`https://platform.openai.com/docs/guides/tools-computer-use`
- Browser Use：`https://docs.browser-use.com/`
- OSWorld：`https://os-world.github.io/`
- UI-TARS：`https://github.com/bytedance/UI-TARS`
- PANGAEA：`https://github.com/VMarsocci/pangaea-bench`
- TerraMind：`https://arxiv.org/abs/2504.11171`
- DINOv3：`https://github.com/facebookresearch/dinov3`
- Grounded SAM：`https://github.com/IDEA-Research/Grounded-Segment-Anything`
- SAM 2：`https://github.com/facebookresearch/sam2`
- RF-DETR：`https://github.com/roboflow/rf-detr`

## 2026-06-23：LLM 推理系统与成本治理补强

本轮新增 10 个条目，覆盖商用 LLM/Agent 后端必须掌握的性能栈：KV cache、prefix caching、continuous batching、prefill/decode 分离、结构化生成、量化部署和 SLO/成本治理。

## 新增条目

- vLLM / PagedAttention
- Automatic Prefix Caching
- SGLang / RadixAttention
- Disaggregated Prefill/Decode Serving
- LMCache / Persistent KV Cache
- KV-aware Routing
- Continuous Batching
- Structured Generation Runtime
- LLM SLO / Cost Governance
- Quantized LLM Serving

## 主要参考源

- vLLM Prefix Caching：`https://docs.vllm.ai/en/stable/design/prefix_caching/`
- vLLM Metrics：`https://docs.vllm.ai/en/stable/serving/metrics.html`
- SGLang：`https://docs.sglang.ai/`
- SGLang GitHub：`https://github.com/sgl-project/sglang`
- NVIDIA Dynamo Disaggregated Serving：`https://docs.nvidia.com/dynamo/v-0-7-1/design-docs/disaggregated-serving`
- LMCache：`https://docs.lmcache.ai/`
- OpenTelemetry GenAI：`https://opentelemetry.io/docs/specs/semconv/gen-ai/`

## 2026-06-23：RAG 质量闭环与 AI 治理补强

本轮新增 10 个条目，覆盖从“能检索回答”到“可评测、可优化、可治理”的完整闭环：prompt 编译、RAG 组件指标、混合检索、视觉文档检索、LLM 评审校准、主动学习、合成评测、模型/数据卡和 AI 供应链。

## 新增条目

- DSPy / Prompt Compilation
- Ragas Component Metrics
- Hybrid Search + RRF + Rerank
- ColPali / Visual Document Retrieval
- Late Interaction Retrieval / ColBERT
- LLM-as-Judge Calibration
- Active Learning Data Engine
- Synthetic Eval Dataset Generation
- Model Cards / Data Cards / Lineage
- AI Supply Chain Provenance

## 主要参考源

- DSPy：`https://dspy.ai/`
- Ragas Metrics：`https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/`
- LangChain Retrieval：`https://docs.langchain.com/oss/python/langchain/retrieval`
- ColPali：`https://github.com/illuin-tech/colpali`
- LangSmith Evaluation：`https://docs.langchain.com/langsmith/evaluation-concepts`
- OpenAI Evals：`https://github.com/openai/evals`
- Label Studio Active Learning：`https://labelstud.io/guide/active_learning`
- Hugging Face Model Cards：`https://huggingface.co/docs/hub/model-cards`
- SLSA：`https://slsa.dev/`
- CycloneDX ML-BOM：`https://cyclonedx.org/capabilities/mlbom/`

## 2026-06-23：时序基础模型、水系统控制与安全优化补强

本轮新增 10 个条目，覆盖你水处理、养殖和遥感项目中高价值的时序预测、表格建模、因果干预、安全优化和机理-AI 混合建模能力。

## 新增条目

- Time-series Foundation Models
- Chronos / Probabilistic Forecasting
- TimeGPT / Forecasting API
- TabPFN / Tabular Foundation Model
- Causal ML for Intervention Effects
- Safe Bayesian Optimization
- Digital Twin + Model Predictive Control
- Physics-informed Neural Operators
- SWMM + AI Surrogate Modeling
- Sensor Drift & Data Quality Monitoring

## 主要参考源

- Google TimesFM：`https://github.com/google-research/timesfm`
- Amazon Chronos：`https://github.com/amazon-science/chronos-forecasting`
- Nixtla TimeGPT：`https://docs.nixtla.io/`
- TabPFN：`https://github.com/PriorLabs/TabPFN`
- DoWhy：`https://www.pywhy.org/dowhy/`
- EconML：`https://econml.azurewebsites.net/`
- BoTorch：`https://botorch.org/`
- SafeOpt：`https://github.com/befelix/SafeOpt`
- GEKKO：`https://gekko.readthedocs.io/en/latest/`
- do-mpc：`https://www.do-mpc.com/`
- NeuralOperator：`https://neuraloperator.github.io/dev/`
- NVIDIA PhysicsNeMo：`https://docs.nvidia.com/physicsnemo/latest/`
- EPA SWMM：`https://www.epa.gov/water-research/storm-water-management-model-swmm`
- Evidently：`https://docs.evidentlyai.com/`
- Great Expectations：`https://docs.greatexpectations.io/`

## 2026-06-24：状态空间模型、时空图学习、MLOps 与向量数据库生产化补强

本轮新增 12 个条目，重点从“会做模型 demo”推进到“能做商用 AI 系统”：覆盖长序列建模、时空图学习、数据/模型版本治理、特征管理、Lakehouse 数据底座、向量数据库混合检索，以及可持久化 Agent 工作流。

## 新增条目

- Mamba / Selective State Space Models
- Mamba-2 / State Space Duality
- PatchTST / Time-series Transformer
- Spatiotemporal Graph Neural Networks
- DVC / Dataset Versioning
- MLflow Model Registry
- Feast / Feature Store
- Lakehouse for AI / Geospatial Data
- Qdrant / Payload Filtering + HNSW
- Milvus / Hybrid Sparse-Dense Search
- Weaviate / Named Vectors
- LangGraph / Durable Agent Workflows

## 主要参考源

- Mamba：`https://github.com/state-spaces/mamba`
- PatchTST：`https://github.com/yuqinie98/PatchTST`
- PyTorch Geometric Temporal：`https://pytorch-geometric-temporal.readthedocs.io/`
- DVC：`https://dvc.org/doc`
- MLflow Model Registry：`https://mlflow.org/docs/latest/ml/model-registry/`
- Feast：`https://docs.feast.dev/`
- Apache Iceberg：`https://iceberg.apache.org/`
- Delta Lake：`https://docs.delta.io/latest/index.html`
- Qdrant：`https://qdrant.tech/documentation/`
- Milvus Hybrid Search：`https://milvus.io/docs/hybrid_search_with_milvus.md`
- Weaviate Named Vectors：`https://docs.weaviate.io/weaviate/config-refs/schema/multi-vector`
- LangGraph：`https://langchain-ai.github.io/langgraph/`

## 2026-06-24：深度知识卡沉淀：GeoAI、视觉文档 RAG 与推理服务

本轮不只新增雷达词条，而是把已核验的前沿方向沉淀进 `js/knowledge.js` 的“前沿 AI 工程”深度卡，方便直接用于面试表达、项目迁移和作品集报告。

## 新增深度卡

- Prithvi-EO-2.0：多时相地球观测基础模型
- Clay Foundation Model：开源 Earth Embedding 底座
- ColPali / ColQwen：视觉文档检索与多模态 RAG
- SGLang / RadixAttention：结构化生成与 KV Cache 复用

## 主要参考源

- Prithvi-EO-2.0 Hugging Face：`https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M-TL`
- Prithvi-EO-2.0 论文：`https://arxiv.org/abs/2412.02732`
- Clay Foundation Model：`https://github.com/Clay-foundation/model`
- ColPali 论文：`https://arxiv.org/abs/2407.01449`
- ColPali/ColQwen 模型卡：`https://huggingface.co/vidore/colqwen2-v0.1`
- SGLang GitHub：`https://github.com/sgl-project/sglang`
- SGLang 论文：`https://arxiv.org/abs/2312.07104`

## 求职迁移方向

- 遥感算法工程师：把 Prithvi-EO-2.0 和 Clay 作为 GeoAI backbone/embedding 方向，和 UNet、DeepLabv3、SAMGeo、传统指数法形成对比。
- AI 应用工程：把 ColPali/ColQwen 用于投标文件、报告、PPT 和图表证据库的多模态 RAG。
- 商用系统工程：用 SGLang/RadixAttention 解释长上下文、结构化生成、KV cache 复用和推理成本治理。
