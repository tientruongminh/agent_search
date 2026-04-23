from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.services.storage import get_storage
from app.storage.db import get_session
from app.storage.repositories.jobs import JobRepository

router = APIRouter(tags=["downloads"])


@router.get("/jobs/{job_id}/artifacts/{artifact_id}")
def download_artifact(job_id: str, artifact_id: str, session: Session = Depends(get_session)) -> FileResponse:
    repo = JobRepository(session)
    artifact = repo.get_artifact(job_id, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    storage = get_storage()
    path = storage.resolve(artifact.relative_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing")
    return FileResponse(path, filename=artifact.name)

