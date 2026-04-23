from __future__ import annotations

from pydantic import BaseModel, Field


class RankedFile(BaseModel):
    id: str
    title: str
    local_path: str
    download_url: str
    sha256: str
    file_type: str | None = None
    size_bytes: int
    page_count: int | None = None
    source_domain: str | None = None
    summary: str | None = None
    why_selected: list[str] = Field(default_factory=list)
    verified_signals: list[str] = Field(default_factory=list)
    institution_score: float = 0.0
    topic_score: float = 0.0
    final_score: float = 0.0
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class ArtifactItem(BaseModel):
    id: str
    name: str
    kind: str
    relative_path: str
    download_url: str


class ArtifactManifest(BaseModel):
    job_id: str
    artifacts: list[ArtifactItem] = Field(default_factory=list)
    bundle_url: str | None = None
    output_dir: str

