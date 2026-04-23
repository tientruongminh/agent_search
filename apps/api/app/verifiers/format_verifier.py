from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.pdf_reader import PdfReaderService


@dataclass
class FormatVerificationResult:
    ok: bool
    reason: str | None = None
    page_count: int | None = None
    excerpt: str | None = None
    title: str | None = None


class FormatVerifier:
    def __init__(self, pdf_reader: PdfReaderService):
        self.pdf_reader = pdf_reader

    def verify(self, path: str, content_type: str | None = None) -> FormatVerificationResult:
        suffix = Path(path).suffix.lower()
        if suffix == ".pdf":
            try:
                parsed = self.pdf_reader.parse(path)
                return FormatVerificationResult(ok=True, page_count=parsed.page_count, excerpt=parsed.excerpt, title=parsed.title)
            except Exception as exc:
                return FormatVerificationResult(ok=False, reason=f"Invalid PDF: {exc}")
        if suffix in {".ppt", ".pptx", ".doc", ".docx", ".md", ".txt", ".ipynb"}:
            file_size = Path(path).stat().st_size
            if file_size <= 0:
                return FormatVerificationResult(ok=False, reason="Empty file")
            return FormatVerificationResult(ok=True, page_count=None, excerpt=None, title=None)
        return FormatVerificationResult(ok=False, reason=f"Unsupported file extension: {suffix}")

