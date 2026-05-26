"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: local_retriever.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import get_settings
from app.models.schemas import SourceItem
from app.services.corpus_store import CorpusStore


def _keyword_overlap(question: str, content: str) -> float:
    query_tokens = {token for token in question.lower().split() if token.strip()}
    if not query_tokens:
        query_tokens = {char for char in question if not char.isspace()}
    content_lower = content.lower()
    overlap = sum(1 for token in query_tokens if token in content_lower)
    return overlap / max(1, len(query_tokens))


class LocalRetriever:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.corpus_store = CorpusStore()

    def retrieve(self, question: str) -> list[SourceItem]:
        records = self.corpus_store.load()
        if not records:
            return []

        documents = [record["content"] for record in records]
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1)
        matrix = vectorizer.fit_transform(documents)
        query_vector = vectorizer.transform([question])
        scores = cosine_similarity(query_vector, matrix).flatten()

        combined_scores: list[tuple[int, float]] = []
        for index, base_score in enumerate(scores):
            content = records[index]["content"]
            if len(content.strip()) < self.settings.min_chunk_chars:
                continue
            overlap_bonus = _keyword_overlap(question, content) * 0.35
            length_bonus = min(len(content) / 1200, 1.0) * 0.08
            final_score = float(base_score) + overlap_bonus + length_bonus
            combined_scores.append((index, final_score))

        ranked_indices = [index for index, _ in sorted(combined_scores, key=lambda item: item[1], reverse=True)]

        sources: list[SourceItem] = []
        seen_signatures: set[str] = set()
        for index in ranked_indices:
            score = next(score for idx, score in combined_scores if idx == index)
            if score <= 0:
                continue
            record = records[index]
            signature = record["content"].strip()
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            sources.append(
                SourceItem(
                    file_name=record["file_name"],
                    file_path=record["file_path"],
                    page=int(record["page"]),
                    chunk_index=int(record["chunk_index"]),
                    content=record["content"],
                    score=round(score, 4),
                )
            )
            if len(sources) >= self.settings.max_context_chunks:
                break
        return sources
