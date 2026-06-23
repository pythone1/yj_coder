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
- `js/resume.js`：在线简历编辑与导出。
- `js/portfolio.js`：求职项目作品集数据与渲染。
- `js/radar.js`：前沿 AI 工程知识雷达，跟踪新概念、求职相关度、建设动作和来源链接。
- `js/knowledge.js`：AI、遥感、数据工程、前沿 AI 工程知识库。
- `js/quiz.js`：模拟面试题库。
- `js/app.js`：应用状态、导航、搜索、卡片、PPT 等交互逻辑。
- `css/style.css`：全局样式和作品集页面样式。
- `scripts/update_resume_content.js`：结构化更新在线简历、JSON 备份和 Markdown 简历。
- `docs/resume_evidence_notes.md`：简历项目内容的本地文档依据与待补指标清单。

## 内容边界

已清理物理错题、协议类和无关临时生成文件；当前项目只保留求职、面试、作品集和 AI 技术知识相关内容。

## 知识更新机制

新增技术概念先进入 `js/radar.js` 的知识雷达，评估求职相关度、建设阶段、领域和行动项；成熟后再沉淀进 `js/knowledge.js` 的深度知识库。雷达页支持关键词、技术域和建设阶段筛选，避免后续持续收录时信息失控。
