# 港股 AI/芯片主题研究终端

## 运行

```powershell
conda activate LSTM
python data_engine.py
```

浏览器打开：

```text
http://127.0.0.1:8888
```

## 环境变量

```powershell
$env:ZHIPUAI_API_KEY="你的智谱Key"
$env:ZHIPU_MODEL="glm-4.5-air"
$env:APP_PORT="8888"
$env:REFRESH_SECONDS="15"
$env:DAILY_COLLECT_HOUR="7"
$env:COLLECT_DAYS="7"
```

`ZHIPUAI_API_KEY` 可选。未配置时，系统仍可运行行情、事件、主题热度和本地知识库检索，只是不调用 GLM。

每日采集：

- `data_engine.py` 启动后会自动运行 `knowledge_collector.py`。
- 默认每天 07:00 后执行一次。
- 有 `ZHIPUAI_API_KEY` 时会联网搜索财报、公告、基本面新闻和重大事件。
- 没有 Key 时只更新实体画像，不伪装成联网采集。

## 主要文件

- `data_engine.py`：主服务，负责行情刷新、事件库、RAG 检索、AI 问答、HTTP API。
- `index.html`：研究终端前端。
- `entities.yaml`：关注实体、股票代码、关键词配置。
- `RAG.py`：构建本地知识库 chunks；有可选依赖时生成 FAISS index。
- `knowledge_collector.py`：每日采集财报、公告、基本面新闻并挂入知识库。
- `prompts.py`：提示词工程模板，统一研究问答、采集、异动解释和日报格式。
- `events.db`：运行后自动生成的事件数据库。
- `zhipu_data.json`：运行态快照，供前端读取。
- `knowledge_base/`：本地知识库文件。

## API

- `GET /api/state`：完整运行态。
- `GET /api/events?entity=zhipu`：事件列表。
- `GET /api/report`：生成 Markdown 简报。
- `POST /chat`：AI/本地研究问答。

## 扩展新标的

编辑 `entities.yaml`：

```json
{
  "entities": {
    "example": {
      "display_name": "示例公司",
      "category": "AI应用",
      "stock_codes": ["00000.HK"],
      "keywords": ["示例公司"],
      "aliases": [],
      "notes": "人工确认后的备注"
    }
  }
}
```

当前文件是 JSON-compatible YAML，未安装 `PyYAML` 也能解析。
