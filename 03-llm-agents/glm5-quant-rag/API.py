"""
项目名称: glm5-quant-rag
技术领域: 03-llm-agents
模块说明: API.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

import os


api_key = os.getenv("ZHIPUAI_API_KEY", "").strip()
if not api_key:
    raise SystemExit("Missing ZHIPUAI_API_KEY")

from zhipu_client import chat_completion


content = chat_completion(
    model=os.getenv("ZHIPU_MODEL", "glm-4.5-air"),
    messages=[{"role": "user", "content": "请只回复 ASCII 文本：OK"}],
)
print(content)
