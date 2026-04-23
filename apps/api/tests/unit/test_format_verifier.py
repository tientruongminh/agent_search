from pathlib import Path

from app.services.pdf_reader import PdfReaderService
from app.verifiers.format_verifier import FormatVerifier


def test_format_verifier_extracts_excerpt_from_markdown(tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    path.write_text("# Machine Learning Notes\nGradient descent and regression.", encoding="utf-8")

    result = FormatVerifier(PdfReaderService()).verify(str(path))

    assert result.ok is True
    assert "Machine Learning Notes" in (result.excerpt or "")
    assert result.title == "notes.md"

