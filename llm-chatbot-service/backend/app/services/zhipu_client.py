from __future__ import annotations

import time
from typing import Any

import requests

from app.core.config import get_settings


class ZhipuClient:
    base_url = "https://open.bigmodel.cn/api/paas/v4"

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def ready(self) -> bool:
        key = self.settings.zhipu_api_key.strip()
        return bool(key) and not key.startswith("your_")

    def _headers(self) -> dict[str, str]:
        if not self.ready:
            raise RuntimeError("ZHIPU_API_KEY is missing. Please configure backend/.env.")
        return {
            "Authorization": f"Bearer {self.settings.zhipu_api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.request_retry_count + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/{endpoint}",
                    headers=self._headers(),
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                last_error = exc
                status_code = exc.response.status_code if exc.response is not None else None
                if status_code not in {429, 500, 502, 503, 504}:
                    raise
            except requests.RequestException as exc:
                last_error = exc

            if attempt < self.settings.request_retry_count:
                time.sleep(self.settings.request_retry_backoff * attempt)

        raise RuntimeError(f"调用智普接口失败，已重试 {self.settings.request_retry_count} 次: {last_error}")

    def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings: list[list[float]] = []
        batch_size = max(1, self.settings.embedding_batch_size)
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            payload = {"model": self.settings.zhipu_embedding_model, "input": batch}
            body = self._post("embeddings", payload, timeout=60)
            embeddings.extend(item["embedding"] for item in body.get("data", []))
            if start + batch_size < len(texts):
                time.sleep(0.8)
        return embeddings

    def chat(
        self,
        question: str,
        context_blocks: list[dict[str, Any]],
        mode: str = "knowledge_first",
        history_messages: list[dict[str, str]] | None = None,
    ) -> str:
        context_text = "\n\n".join(
            f"[来源 {idx}] 文件：{item['file_name']} | 页码：{item['page']}\n{item['content']}"
            for idx, item in enumerate(context_blocks, start=1)
        )
        history_text = "\n".join(
            f"{'用户' if item['role'] == 'user' else '助手'}：{item['content']}"
            for item in (history_messages or [])
        )

        if mode == "general_fallback":
            system_prompt = (
                "你是一个企业问答助手。"
                "当知识库证据不足时，你可以基于通用专业知识回答，但必须明确标注这是通用判断，不是知识库结论。"
                "回答要专业、直接、可执行，避免编造具体数据或项目细节。"
            )
            user_prompt = (
                f"最近会话历史：\n{history_text or '无'}\n\n"
                f"用户问题：\n{question}\n\n"
                f"可用知识库片段（可能不足）：\n{context_text or '当前没有可用上下文。'}\n\n"
                "请按下面规则回答：\n"
                "1. 先直接回答问题。\n"
                "2. 如果知识库证据不足，可以增加一段“通用补充判断：”。\n"
                "3. 如果引用了知识库，在末尾写“参考来源：文件名-页码”；如果没有可靠知识库依据，就写“参考来源：本回答主要基于模型通用知识”。"
            )
        else:
            system_prompt = (
                "你是一个企业知识库问答助手。"
                "你必须优先依据提供的知识库内容回答。"
                "如果知识库证据不完整，可以结合通用专业知识做补充，但要明确区分哪些是知识库依据，哪些是通用补充。"
                "回答要专业、简洁，并尽量总结为可执行结论。"
            )
            user_prompt = (
                f"最近会话历史：\n{history_text or '无'}\n\n"
                f"用户问题：\n{question}\n\n"
                f"知识库上下文：\n{context_text or '当前没有可用上下文。'}\n\n"
                "请优先基于知识库回答。若证据不足，可增加一段“通用补充判断：”。"
                "如果使用了知识库，请在末尾补一句“参考来源：文件名-页码”；如果没有可靠知识库依据，就写“参考来源：本回答主要基于模型通用知识”。"
            )

        payload = {
            "model": self.settings.zhipu_chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        body = self._post("chat/completions", payload, timeout=120)
        return body["choices"][0]["message"]["content"].strip()
