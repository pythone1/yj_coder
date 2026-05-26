from dataclasses import dataclass
from pathlib import Path

import fitz

from app.services.chunker import normalize_text


@dataclass
class ParsedPage:
    file_name: str
    file_path: str
    page: int
    text: str


def list_pdf_files(docs_dir: Path) -> list[Path]:
    return sorted(path for path in docs_dir.glob("*.pdf") if path.is_file())


def parse_pdf(path: Path) -> list[ParsedPage]:
    pages: list[ParsedPage] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            text = normalize_text(page.get_text("text"))
            if not text:
                continue
            pages.append(
                ParsedPage(
                    file_name=path.name,
                    file_path=str(path.resolve()),
                    page=index,
                    text=text,
                )
            )
    return pages
