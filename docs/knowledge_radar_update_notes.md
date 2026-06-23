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
