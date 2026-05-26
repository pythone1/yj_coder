"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: vector_store.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from dataclasses import dataclass

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings


@dataclass
class StoredChunk:
    id: str
    text: str
    metadata: dict


class VectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = chromadb.PersistentClient(
            path=str(self.settings.vector_db_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self._get_collection()

    def _get_collection(self) -> Collection:
        return self.client.get_or_create_collection(name=self.settings.collection_name)

    def reset(self) -> None:
        try:
            self.client.delete_collection(self.settings.collection_name)
        except Exception:
            pass
        self.collection = self._get_collection()

    def upsert(self, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict]) -> None:
        if ids:
            self.collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def count(self) -> int:
        return self.collection.count()

    def query(self, query_embedding: list[float], top_k: int) -> list[StoredChunk]:
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]
        rows: list[StoredChunk] = []
        for row_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            item_metadata = dict(metadata or {})
            item_metadata["distance"] = float(distance)
            rows.append(StoredChunk(id=row_id, text=text, metadata=item_metadata))
        return rows
