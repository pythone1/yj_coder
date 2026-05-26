from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.core.config import get_settings

settings = get_settings()
allowed_origins = [item.strip() for item in settings.frontend_origins.split(",") if item.strip()]
frontend_dist_dir = Path(settings.frontend_dist_dir)

app = FastAPI(title="Local Knowledge Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if frontend_dist_dir.exists():
    assets_dir = frontend_dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    def serve_index() -> FileResponse:
        return FileResponse(frontend_dist_dir / "index.html")


    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> FileResponse:
        candidate = frontend_dist_dir / full_path
        if full_path and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist_dir / "index.html")
