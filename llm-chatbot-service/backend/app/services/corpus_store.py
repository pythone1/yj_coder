from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings


class CorpusStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.path = Path(settings.vector_db_dir) / "corpus.json"

    def save(self, records: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def count(self) -> int:
        return len(self.load())
