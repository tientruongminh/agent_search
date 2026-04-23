from __future__ import annotations

import threading

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.state_machine import JobStage
from app.schemas.api import FeedbackRequest, FeedbackResponse, JobResultsResponse, JobStatusResponse, SearchJobResponse, SearchRequest
from app.storage.db import get_session
from app.storage.repositories.jobs import JobRepository
from app.workers.tasks import run_search_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _run_job_in_background(job_id: str) -> None:
    thread = threading.Thread(target=run_search_job.fn, args=(job_id,), daemon=True)
    thread.start()


@router.post("/search", response_model=SearchJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_search_job(payload: SearchRequest, session: Session = Depends(get_session)) -> SearchJobResponse:
    repo = JobRepository(session)
    job = repo.create_job(payload)
    session.commit()
    if settings.broker_mode.lower() == "redis":
        run_search_job.send(job.id)
    else:
        _run_job_in_background(job.id)
    return SearchJobResponse(job_id=job.id, status=job.status, stage=JobStage(job.stage), created_at=job.created_at)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, session: Session = Depends(get_session)) -> JobStatusResponse:
    repo = JobRepository(session)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    results = repo.list_ranked_files(job_id)
    artifacts = repo.get_artifact_manifest(job_id)
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        stage=JobStage(job.stage),
        raw_request=job.raw_request,
        fallback_mode=job.fallback_mode,
        reflection_count=job.reflection_count,
        progress=job.progress,
        result_count=len(results),
        artifact_count=len(artifacts.artifacts),
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        events=repo.list_events(job_id),
    )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
def get_results(job_id: str, session: Session = Depends(get_session)) -> JobResultsResponse:
    repo = JobRepository(session)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    results = repo.list_ranked_files(job_id)
    manifest = repo.get_artifact_manifest(job_id)
    fallback_explanation = None
    if not results and job.stage == JobStage.DONE.value:
        fallback_explanation = "No verified files passed the thresholds; inspect source pages and retry with broader constraints."
    return JobResultsResponse(
        job_id=job.id,
        status=job.status,
        stage=JobStage(job.stage),
        results=results,
        artifacts=manifest.artifacts,
        fallback_explanation=fallback_explanation,
        bundle_url=manifest.bundle_url,
    )


@router.post("/{job_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_202_ACCEPTED)
def record_feedback(job_id: str, payload: FeedbackRequest, session: Session = Depends(get_session)) -> FeedbackResponse:
    repo = JobRepository(session)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    repo.record_feedback(job_id, payload)
    session.commit()
    return FeedbackResponse()
