"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: ingest.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

import time

from app.core.config import get_settings
from app.services.chunker import chunk_text
from app.services.corpus_store import CorpusStore
from app.services.pdf_parser import list_pdf_files, parse_pdf
from app.services.vector_store import VectorStore
from app.services.zhipu_client import ZhipuClient


class IngestService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.vector_store = VectorStore()
        self.zhipu_client = ZhipuClient()
        self.corpus_store = CorpusStore()

    def rebuild(self) -> tuple[int, int, float]:
        start_time = time.perf_counter()
        pdf_files = list_pdf_files(self.settings.docs_dir)
        self.vector_store.reset()
        all_records: list[dict] = []

        indexed_file_count = 0
        total_chunks = 0

        for pdf_file in pdf_files:
            pages = parse_pdf(pdf_file)
            ids: list[str] = []
            documents: list[str] = []
            metadatas: list[dict] = []

            for parsed_page in pages:
                chunks = chunk_text(parsed_page.text, self.settings.chunk_size, self.settings.chunk_overlap)
                for chunk_index, chunk in enumerate(chunks):
                    ids.append(f"{parsed_page.file_name}-{parsed_page.page}-{chunk_index}")
                    documents.append(chunk)
                    metadata = {
                        "file_name": parsed_page.file_name,
                        "file_path": parsed_page.file_path,
                        "page": parsed_page.page,
                        "chunk_index": chunk_index,
                    }
                    metadatas.append(metadata)
                    all_records.append({**metadata, "content": chunk})

            if not documents:
                continue

            if self.zhipu_client.ready:
                try:
                    embeddings = self.zhipu_client.create_embeddings(documents)
                    self.vector_store.upsert(ids, documents, embeddings, metadatas)
                except Exception:
                    pass
            indexed_file_count += 1
            total_chunks += len(documents)

        self.corpus_store.save(all_records)
        duration = time.perf_counter() - start_time
        return indexed_file_count, total_chunks, duration
