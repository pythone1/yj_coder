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
