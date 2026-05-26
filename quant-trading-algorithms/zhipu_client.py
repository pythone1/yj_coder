import json
import os

import requests


API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def chat_completion(messages, model=None, tools=None, timeout=180):
    api_key = os.getenv("ZHIPUAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing ZHIPUAI_API_KEY")

    model = model or os.getenv("ZHIPU_MODEL", "glm-4.5-air")

    try:
        from zhipuai import ZhipuAI

        client = ZhipuAI(api_key=api_key)
        kwargs = {"model": model, "messages": messages, "stream": False}
        if tools:
            kwargs["tools"] = tools
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    except ImportError:
        pass

    session = requests.Session()
    session.trust_env = False
    payload = {"model": model, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools
    response = session.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=timeout,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Zhipu API error {response.status_code}: {response.text[:500]}")
    data = response.json()
    return data["choices"][0]["message"]["content"]
