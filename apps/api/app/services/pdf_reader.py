from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class PdfParseResult:
    page_count: int
    excerpt: str
    title: str | None = None


class PdfReaderService:
    def parse(self, path: str | Path, max_pages: int = 2) -> PdfParseResult:
        reader = PdfReader(str(path))
        excerpt_parts: list[str] = []
        for page in reader.pages[:max_pages]:
            text = page.extract_text() or ""
            if text:
                excerpt_parts.append(text.strip())
        metadata = reader.metadata or {}
        return PdfParseResult(
            page_count=len(reader.pages),
            excerpt="\n".join(excerpt_parts)[:4000],
            title=getattr(metadata, "title", None) if metadata else None,
        )

