from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.core.state_machine import JobStage


class StateEvent(BaseModel):
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    stage: JobStage
    actor: str
    event: str
    payload: dict = Field(default_factory=dict)

