from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from app.core.metrics import metrics_text
from app.storage.db import session_scope

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready() -> dict[str, str]:
    with session_scope() as session:
        session.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    return metrics_text()
