from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.state_machine import JobStage
from app.schemas.candidate import Candidate
from app.schemas.events import StateEvent
from app.schemas.file_result import ArtifactManifest, RankedFile
from app.schemas.intent import Intent
from app.schemas.query_plan import Budget, QueryPlan
from app.schemas.verified_candidate import VerifiedCandidate


class SearchState(BaseModel):
    job_id: str
    raw_request: str
    stage: JobStage = JobStage.QUEUED
    intent: Intent | None = None
    plan: QueryPlan | None = None
    budget: Budget | None = None
    discovered_candidates: list[Candidate] = Field(default_factory=list)
    expanded_candidates: list[Candidate] = Field(default_factory=list)
    deduped_candidates: list[Candidate] = Field(default_factory=list)
    verified_files: list[VerifiedCandidate] = Field(default_factory=list)
    ranked_files: list[RankedFile] = Field(default_factory=list)
    packaged_artifacts: ArtifactManifest | None = None
    reflection_count: int = 0
    fallback_mode: str | None = None
    logs: list[StateEvent] = Field(default_factory=list)

