from __future__ import annotations

from enum import StrEnum


class JobStage(StrEnum):
    QUEUED = "QUEUED"
    PLANNING = "PLANNING"
    BUDGETING = "BUDGETING"
    DISCOVERING = "DISCOVERING"
    EXPANDING = "EXPANDING"
    DEDUPING = "DEDUPING"
    VERIFYING = "VERIFYING"
    RANKING = "RANKING"
    PACKAGING = "PACKAGING"
    FEEDBACK_UPDATE = "FEEDBACK_UPDATE"
    DONE = "DONE"
    FAILED = "FAILED"


TERMINAL_STAGES = {JobStage.DONE, JobStage.FAILED}

_ALLOWED_TRANSITIONS: dict[JobStage, set[JobStage]] = {
    JobStage.QUEUED: {JobStage.PLANNING, JobStage.FAILED},
    JobStage.PLANNING: {JobStage.BUDGETING, JobStage.FAILED},
    JobStage.BUDGETING: {JobStage.DISCOVERING, JobStage.FAILED},
    JobStage.DISCOVERING: {JobStage.EXPANDING, JobStage.FAILED},
    JobStage.EXPANDING: {JobStage.DEDUPING, JobStage.FAILED},
    JobStage.DEDUPING: {JobStage.VERIFYING, JobStage.FAILED},
    JobStage.VERIFYING: {JobStage.DISCOVERING, JobStage.RANKING, JobStage.FAILED},
    JobStage.RANKING: {JobStage.PACKAGING, JobStage.FAILED},
    JobStage.PACKAGING: {JobStage.FEEDBACK_UPDATE, JobStage.FAILED},
    JobStage.FEEDBACK_UPDATE: {JobStage.DONE, JobStage.FAILED},
    JobStage.DONE: set(),
    JobStage.FAILED: set(),
}


def validate_transition(current: JobStage, new: JobStage) -> None:
    if new not in _ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Invalid transition from {current} to {new}")


def progress_for_stage(stage: JobStage) -> int:
    ordered = [
        JobStage.QUEUED,
        JobStage.PLANNING,
        JobStage.BUDGETING,
        JobStage.DISCOVERING,
        JobStage.EXPANDING,
        JobStage.DEDUPING,
        JobStage.VERIFYING,
        JobStage.RANKING,
        JobStage.PACKAGING,
        JobStage.FEEDBACK_UPDATE,
        JobStage.DONE,
    ]
    if stage == JobStage.FAILED:
        return 100
    return int((ordered.index(stage) / (len(ordered) - 1)) * 100)

