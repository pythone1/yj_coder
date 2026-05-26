"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: retriever.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from app.core.config import get_settings
from app.models.schemas import SourceItem
from app.services.local_retriever import LocalRetriever
from app.services.vector_store import VectorStore
from app.services.zhipu_client import ZhipuClient


class RetrieverService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.vector_store = VectorStore()
        self.zhipu_client = ZhipuClient()
        self.local_retriever = LocalRetriever()

    def retrieve(self, question: str) -> list[SourceItem]:
        if self.zhipu_client.ready:
            try:
                embeddings = self.zhipu_client.create_embeddings([question])
                if embeddings:
                    rows = self.vector_store.query(embeddings[0], top_k=self.settings.retrieval_top_k)
                    sources: list[SourceItem] = []
                    for row in rows:
                        score = max(0.0, 1.0 - float(row.metadata.get("distance", 1.0)))
                        if score < self.settings.similarity_threshold:
                            continue
                        sources.append(
                            SourceItem(
                                file_name=str(row.metadata.get("file_name", "")),
                                file_path=str(row.metadata.get("file_path", "")),
                                page=int(row.metadata.get("page", 0)),
                                chunk_index=int(row.metadata.get("chunk_index", 0)),
                                content=row.text,
                                score=round(score, 4),
                            )
                        )
                    if sources:
                        return sources[: self.settings.max_context_chunks]
            except Exception:
                pass

        return self.local_retriever.retrieve(question)
