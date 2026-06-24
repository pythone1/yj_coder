# AI & 遥感测绘面试备战中心

这是一个本地运行的求职准备工作台，当前保留内容集中在简历、项目作品集、AI/遥感/数据工程知识库、模拟面试、背诵卡片和汇报 PPT。

## 启动

双击 `start_server.bat`，或在当前目录运行：

```bat
py -3 -m http.server 8000
```

然后访问：

```text
http://localhost:8000
```

## 当前模块

- `index.html`：主页面和视图容器。
- `js/resume.js`：在线简历编辑与导出，简历页支持编辑状态栏、评分状态、区块快速跳转、会话内撤销/恢复和持久化版本历史。
- `js/portfolio.js`：求职项目作品集数据与渲染。
- `js/radar.js`：前沿 AI 工程知识雷达，跟踪新概念、求职相关度、建设动作和来源链接。
- `js/knowledge.js`：AI、遥感、数据工程、前沿 AI 工程知识库。
- `js/quiz.js`：模拟面试题库。
- `js/app.js`：应用状态、导航、搜索、卡片、PPT 等交互逻辑。
- `css/style.css`：全局样式和作品集页面样式。
- 全局搜索：统一检索知识库、知识雷达、作品集和面试题，支持结果面板、回车进入和 Esc 关闭。
- 数据中心：浏览器本地持久化状态、全量 JSON 备份/恢复、用户配置、安全重置、简历版本历史、岗位 JD 匹配分析和求职材料报告导出入口。
- `scripts/update_resume_content.js`：结构化更新在线简历、JSON 备份和 Markdown 简历。
- `scripts/update_radar_frontier.js`：增量补充前沿 AI/Agent 工程知识雷达条目。
- `scripts/update_radar_geoai_frontier.js`：增量补充 Agent 协议、安全评测和 GeoAI/遥感基础模型条目。
- `scripts/update_radar_geospatial_infra.js`：增量补充云原生地理空间数据工程与遥感产品化条目。
- `scripts/update_radar_cua_vision_frontier.js`：增量补充 Computer Use、浏览器 Agent、GUI 评测和开放词汇视觉条目。
- `scripts/update_radar_inference_frontier.js`：增量补充 LLM 推理系统、KV cache、结构化生成和成本治理条目。
- `scripts/update_radar_rag_governance.js`：增量补充 RAG 评测、视觉文档检索、主动学习和 AI 治理条目。
- `scripts/update_radar_timeseries_control.js`：增量补充时序基础模型、表格基础模型、水系统控制和安全优化条目。
- `scripts/update_radar_mlops_spatiotemporal.js`：增量补充状态空间模型、时空图学习、MLOps、Lakehouse 和向量数据库生产化条目。
- `docs/resume_evidence_notes.md`：简历项目内容的本地文档依据与待补指标清单。
- `docs/knowledge_radar_update_notes.md`：知识雷达新增概念、来源和后续待收录方向。
- `docs/ui_experience_audit.md`：UI 体验审查、移动端适配记录和后续验收建议。
- `docs/deployment_notes.md`：本地运行、静态托管和后续服务化部署说明。

## 内容边界

已清理物理错题、协议类和无关临时生成文件；当前项目只保留求职、面试、作品集和 AI 技术知识相关内容。

## 知识更新机制

新增技术概念先进入 `js/radar.js` 的知识雷达，评估求职相关度、建设阶段、领域和行动项；成熟后再沉淀进 `js/knowledge.js` 的深度知识库。雷达页支持关键词、技术域和建设阶段筛选，避免后续持续收录时信息失控。
