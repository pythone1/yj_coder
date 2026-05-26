from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ChatSessionItem,
    CreateSessionResponse,
    MessageItem,
    RenameSessionRequest,
    SessionMessagesResponse,
)
from app.services.chat_service import ChatService
from app.services.session_store import SessionStore

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
def ask_question(payload: ChatRequest, current_user: dict = Depends(get_current_user)) -> ChatResponse:
    try:
        return ChatService().ask(payload.question, current_user["id"], payload.session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/sessions", response_model=CreateSessionResponse)
def create_session(current_user: dict = Depends(get_current_user)) -> CreateSessionResponse:
    session = SessionStore().create_session(current_user["id"])
    return CreateSessionResponse(session=ChatSessionItem(**session))


@router.get("/sessions", response_model=list[ChatSessionItem])
def list_sessions(current_user: dict = Depends(get_current_user)) -> list[ChatSessionItem]:
    return [ChatSessionItem(**item) for item in SessionStore().list_sessions(current_user["id"])]


@router.get("/sessions/{session_id}", response_model=SessionMessagesResponse)
def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)) -> SessionMessagesResponse:
    store = SessionStore()
    session = store.get_session(current_user["id"], session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = [MessageItem(**item) for item in store.list_messages(current_user["id"], session_id)]
    return SessionMessagesResponse(session=ChatSessionItem(**session), messages=messages)


@router.patch("/sessions/{session_id}", response_model=ChatSessionItem)
def rename_session(
    session_id: str,
    payload: RenameSessionRequest,
    current_user: dict = Depends(get_current_user),
) -> ChatSessionItem:
    store = SessionStore()
    session = store.rename_session(current_user["id"], session_id, payload.title.strip())
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ChatSessionItem(**session)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: dict = Depends(get_current_user)) -> dict[str, bool]:
    deleted = SessionStore().delete_session(current_user["id"], session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}
