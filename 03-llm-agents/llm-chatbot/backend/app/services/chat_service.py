"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: chat_service.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

from app.core.config import get_settings
from app.models.schemas import ChatResponse
from app.services.retriever import RetrieverService
from app.services.session_store import SessionStore
from app.services.zhipu_client import ZhipuClient


class ChatService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.retriever = RetrieverService()
        self.zhipu_client = ZhipuClient()
        self.session_store = SessionStore()

    def ask(self, question: str, user_id: str, session_id: str | None = None) -> ChatResponse:
        session = self.session_store.ensure_session(user_id, session_id, fallback_title=question)
        history = self.session_store.recent_messages(user_id, session["id"], self.settings.max_history_messages)
        sources = self.retriever.retrieve(question)
        top_score = max((source.score for source in sources), default=0.0)
        has_confident_kb = bool(sources) and top_score >= self.settings.kb_confidence_threshold

        if not sources:
            answer = self.zhipu_client.chat(
                question,
                [],
                mode="general_fallback",
                history_messages=history,
            )
            self.session_store.add_message(session["id"], "user", question)
            self.session_store.add_message(session["id"], "assistant", answer)
            return ChatResponse(
                session_id=session["id"],
                answer=answer,
                sources=[],
                used_knowledge_base=False,
                answer_mode="general_fallback",
                debug={"reason": "no_relevant_context", "top_score": top_score},
            )

        mode = "knowledge_first" if has_confident_kb else "general_fallback"
        answer = self.zhipu_client.chat(
            question,
            [source.model_dump() for source in sources],
            mode=mode,
            history_messages=history,
        )
        self.session_store.add_message(session["id"], "user", question)
        self.session_store.add_message(session["id"], "assistant", answer)
        return ChatResponse(
            session_id=session["id"],
            answer=answer,
            sources=sources,
            used_knowledge_base=has_confident_kb,
            answer_mode=mode,
            debug={"retrieved_chunks": len(sources), "top_score": top_score},
        )
