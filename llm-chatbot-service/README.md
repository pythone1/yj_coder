# 共享知识库问答助手

基于 `FastAPI + React + ChromaDB + PyMuPDF + 智普模型` 的共享知识库问答系统。当前版本支持：

- 共享知识库检索问答
- 登录注册
- 用户会话隔离
- 管理员权限与用户管理
- FastAPI 单端口托管前端
- 适合通过 Cloudflare Tunnel 暴露到公网

## 本地开发

### 后端

```bash
cd E:\PY\chatbot\backend
copy .env.example .env
conda run -n yolov12 pip install -r requirements.txt
conda run -n yolov12 uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端开发模式

```bash
cd E:\PY\chatbot\frontend
copy .env.example .env
npm install
npm run dev
```

## 单端口运行

### 先构建前端

```bash
cd E:\PY\chatbot\frontend
npm install
npm run build
```

### 再启动后端

```bash
cd E:\PY\chatbot\backend
conda run -n yolov12 uvicorn app.main:app --host 0.0.0.0 --port 8000
```

启动后直接访问：

```text
http://127.0.0.1:8000
```

此时前端静态页面由 FastAPI 直接托管，API 与页面同源，不需要再单独暴露 `5173`。

## Cloudflare Tunnel 建议流程

### 1. 保证单端口服务已启动

```text
http://127.0.0.1:8000
```

### 2. 安装 cloudflared

可参考 Cloudflare 官方安装方式，Windows 安装后确认：

```bash
cloudflared --version
```

### 3. 临时映射公网

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

执行后会得到一个 `trycloudflare.com` 的公网地址，适合测试或演示。

### 4. 正式域名方式

如果你有 Cloudflare 域名：

```bash
cloudflared tunnel login
cloudflared tunnel create chatbot
cloudflared tunnel route dns chatbot chat.your-domain.com
```

然后创建配置文件，例如：

```yaml
tunnel: <tunnel-id>
credentials-file: C:\Users\Administrator\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: chat.your-domain.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

启动：

```bash
cloudflared tunnel run chatbot
```

## 说明

- 当前知识库是你统一维护的共享知识库，不要求普通用户上传 PDF
- 第一位注册用户默认成为管理员
- 管理员可重建知识库、管理用户管理员权限
- 普通用户只负责问答和自己的会话历史
