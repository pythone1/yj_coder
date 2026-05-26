# 03-llm-agents (大模型智能体与量化应用)

本目录收录了基于主流大语言模型、向量数据库以及多模态视觉操控的先进 Agent 原型系统。

## 📁 项目列表

### 1. [glm5-quant-rag](./glm5-quant-rag)
*   **基于智谱 GLM-5 与 Qdrant 的金融量化交易 RAG 检索引擎**
*   **技术栈**：Python + Zhipu API + Qdrant 向量数据库 + HNSW 索引
*   **功能**：对量化因子公式、交易规范和代码标准建立混合向量检索体系，实现秒级高精度知识召回与量化分析代码自动补全。

### 2. [auto-glm-device-agent](./auto-glm-device-agent)
*   **AutoGLM 视觉多模态设备操控智能体**
*   **技术栈**：Python + VLM API + Android ADB
*   **功能**：大模型视觉读取安卓屏幕截图，智能定位操作控件，生成并执行 ADB 点击、滑动指令，实现移动端的全自动流程流转。

### 3. [ppt-generation-agent](./ppt-generation-agent)
*   **智能 PPT 自动化排版大纲生成体**
*   **技术栈**：Python + LLM API + python-pptx
*   **功能**：根据大纲智能设计 PPT 幻灯片版式、主题配色与绝对坐标，生成格式优美的幻灯片成品。

### 4. [llm-chatbot](./llm-chatbot)
*   **全栈 Chatbot 智能会话交互系统**
*   **技术栈**：JavaScript + Node.js + Ollama API
*   **功能**：实现精美毛玻璃的前端对话窗口，支持大模型多轮会话日志落库。
