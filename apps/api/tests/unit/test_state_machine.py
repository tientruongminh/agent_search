import pytest

from app.core.state_machine import JobStage, progress_for_stage, validate_transition


def test_stage_progress_reaches_done() -> None:
    assert progress_for_stage(JobStage.QUEUED) == 0
    assert progress_for_stage(JobStage.DONE) == 100


def test_invalid_transition_raises() -> None:
    with pytest.raises(ValueError):
        validate_transition(JobStage.QUEUED, JobStage.RANKING)

