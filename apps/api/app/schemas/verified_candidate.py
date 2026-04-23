from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.candidate import Candidate


class SemanticVerification(BaseModel):
    semantic_signals: list[str] = Field(default_factory=list)
    topic_score: float = 0.0
    file_type: str = "unknown"
    summary: str | None = None
    excerpt: str | None = None


class InstitutionVerification(BaseModel):
    institution_signals: list[str] = Field(default_factory=list)
    institution_score: float = 0.0


class VerifiedCandidate(BaseModel):
    candidate: Candidate
    transport_ok: bool
    format_ok: bool
    semantic: SemanticVerification
    institution: InstitutionVerification
    confidence: float
    verified_signals: list[str] = Field(default_factory=list)
    reject_reasons: list[str] = Field(default_factory=list)
    local_path: str
    sha256: str
    size_bytes: int
    page_count: int | None = None
    content_type: str | None = None

