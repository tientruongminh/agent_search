from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class Candidate(BaseModel):
    source_url: str
    resolved_url: str | None = None
    canonical_url: str | None = None
    source_type: str
    discovery_agent: str
    domain: str | None = None
    title_hint: str | None = None
    mime_hint: str | None = None
    parent_url: str | None = None
    depth: int = 0
    score_raw: float = 0.0
    filename: str | None = None
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)

    def stable_url(self) -> str:
        return self.resolved_url or self.canonical_url or self.source_url

