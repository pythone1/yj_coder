from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, require_admin
from app.core.config import get_settings
from app.models.schemas import IndexedFileItem, KnowledgeStatusResponse, RebuildResponse
from app.services.corpus_store import CorpusStore
from app.services.ingest import IngestService
from app.services.pdf_parser import list_pdf_files
from app.services.vector_store import VectorStore
from app.services.zhipu_client import ZhipuClient

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/status", response_model=KnowledgeStatusResponse)
def get_knowledge_status(current_user: dict = Depends(get_current_user)) -> KnowledgeStatusResponse:
    settings = get_settings()
    vector_store = VectorStore()
    corpus_store = CorpusStore()
    pdf_files = list_pdf_files(settings.docs_dir)
    return KnowledgeStatusResponse(
        indexed_files=len(pdf_files),
        indexed_chunks=max(vector_store.count(), corpus_store.count()),
        docs_dir=str(settings.docs_dir),
        vector_db_dir=str(settings.vector_db_dir),
        zhipu_ready=ZhipuClient().ready,
    )


@router.get("/files", response_model=list[IndexedFileItem])
def get_files(current_user: dict = Depends(get_current_user)) -> list[IndexedFileItem]:
    settings = get_settings()
    items: list[IndexedFileItem] = []
    for path in list_pdf_files(settings.docs_dir):
        stat = path.stat()
        items.append(
            IndexedFileItem(
                name=path.name,
                path=str(path.resolve()),
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            )
        )
    return items


@router.post("/rebuild", response_model=RebuildResponse)
def rebuild_knowledge_base(current_user: dict = Depends(require_admin)) -> RebuildResponse:
    try:
        indexed_files, indexed_chunks, duration = IngestService().rebuild()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RebuildResponse(
        indexed_files=indexed_files,
        indexed_chunks=indexed_chunks,
        duration_seconds=round(duration, 2),
    )
