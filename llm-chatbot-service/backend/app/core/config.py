from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    zhipu_api_key: str = Field(default="")
    zhipu_chat_model: str = Field(default="glm-4.5")
    zhipu_embedding_model: str = Field(default="embedding-3")
    docs_dir: Path = Field(default=Path("E:/PY/chatbot"))
    vector_db_dir: Path = Field(default=Path("E:/PY/chatbot/backend/data/chroma_db"))
    app_data_dir: Path = Field(default=Path("E:/PY/chatbot/backend/data"))
    frontend_dist_dir: Path = Field(default=Path("E:/PY/chatbot/frontend/dist"))
    collection_name: str = Field(default="knowledge_base")
    chunk_size: int = Field(default=800)
    chunk_overlap: int = Field(default=120)
    retrieval_top_k: int = Field(default=5)
    similarity_threshold: float = Field(default=0.15)
    max_context_chunks: int = Field(default=4)
    frontend_origins: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")
    embedding_batch_size: int = Field(default=12)
    request_retry_count: int = Field(default=5)
    request_retry_backoff: float = Field(default=2.0)
    min_chunk_chars: int = Field(default=80)
    kb_confidence_threshold: float = Field(default=0.12)
    max_history_messages: int = Field(default=8)
    admin_emails: str = Field(default="")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.docs_dir.mkdir(parents=True, exist_ok=True)
    settings.app_data_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_db_dir.mkdir(parents=True, exist_ok=True)
    return settings
