from typing import Any

from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    file_name: str
    file_path: str
    page: int
    chunk_index: int
    content: str
    score: float


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class MessageItem(BaseModel):
    role: str
    content: str
    created_at: str


class ChatSessionItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class RenameSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceItem]
    used_knowledge_base: bool
    answer_mode: str = Field(default="knowledge_base")
    debug: dict[str, Any] = Field(default_factory=dict)


class KnowledgeStatusResponse(BaseModel):
    indexed_files: int
    indexed_chunks: int
    docs_dir: str
    vector_db_dir: str
    zhipu_ready: bool


class IndexedFileItem(BaseModel):
    name: str
    path: str
    size_bytes: int
    modified_at: str


class RebuildResponse(BaseModel):
    indexed_files: int
    indexed_chunks: int
    duration_seconds: float


class CreateSessionResponse(BaseModel):
    session: ChatSessionItem


class SessionMessagesResponse(BaseModel):
    session: ChatSessionItem
    messages: list[MessageItem]


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=6, max_length=120)


class UserProfile(BaseModel):
    id: str
    email: str
    is_admin: bool
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile


class UpdateUserRoleRequest(BaseModel):
    is_admin: bool
