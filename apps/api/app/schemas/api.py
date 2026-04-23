from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.state_machine import JobStage
from app.schemas.events import StateEvent
from app.schemas.file_result import ArtifactItem, ArtifactManifest, RankedFile
from app.schemas.intent import IntentStrictness, SearchGoal


class SearchRequest(BaseModel):
    raw_request: str
    goal: SearchGoal | None = None
    preferred_formats: list[str] = Field(default_factory=list)
    strictness: IntentStrictness | None = None
    max_downloads: int | None = None


class SearchJobResponse(BaseModel):
    job_id: str
    status: str
    stage: JobStage
    created_at: datetime


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: JobStage
    raw_request: str
    fallback_mode: str | None = None
    reflection_count: int = 0
    progress: int = 0
    result_count: int = 0
    artifact_count: int = 0
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    events: list[StateEvent] = Field(default_factory=list)


class JobResultsResponse(BaseModel):
    job_id: str
    status: str
    stage: JobStage
    results: list[RankedFile] = Field(default_factory=list)
    artifacts: list[ArtifactItem] = Field(default_factory=list)
    fallback_explanation: str | None = None
    bundle_url: str | None = None


class FeedbackRequest(BaseModel):
    action: str
    file_id: str | None = None
    score: int | None = None
    metadata: dict = Field(default_factory=dict)


class FeedbackResponse(BaseModel):
    accepted: bool = True

