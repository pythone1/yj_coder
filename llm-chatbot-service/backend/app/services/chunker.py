import re


def normalize_text(text: str) -> str:
    cleaned = text.replace("\x00", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if not text.strip():
        return []

    paragraphs = [segment.strip() for segment in re.split(r"\n{2,}", text) if segment.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_size:
            current = paragraph
            continue

        start = 0
        step = max(1, chunk_size - overlap)
        while start < len(paragraph):
            end = start + chunk_size
            chunks.append(paragraph[start:end])
            start += step
        current = ""

    if current:
        chunks.append(current)

    merged: list[str] = []
    for item in chunks:
        normalized = item.strip()
        if not normalized:
            continue
        if merged and len(normalized) < 80:
            merged[-1] = f"{merged[-1]}\n{normalized}".strip()
        else:
            merged.append(normalized)

    return merged
