from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SearchJob(Base):
    __tablename__ = "search_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"job_{uuid4().hex}")
    raw_request: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="queued")
    stage: Mapped[str] = mapped_column(String(32), default="QUEUED")
    goal: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preferred_formats: Mapped[list[str]] = mapped_column(JSON, default=list)
    strictness: Mapped[dict] = mapped_column(JSON, default=dict)
    fallback_mode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reflection_count: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    state_snapshots: Mapped[list["SearchStateSnapshot"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    events: Mapped[list["StateEventModel"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    queries: Mapped[list["SearchQuery"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    files: Mapped[list["FileRecord"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    artifacts: Mapped[list["JobArtifact"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class SearchStateSnapshot(Base):
    __tablename__ = "search_state_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"))
    stage: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[SearchJob] = relationship(back_populates="state_snapshots")


class StateEventModel(Base):
    __tablename__ = "state_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    stage: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(64))
    event: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    job: Mapped[SearchJob] = relationship(back_populates="events")


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"qry_{uuid4().hex}")
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"))
    query_text: Mapped[str] = mapped_column(Text)
    purpose: Mapped[str] = mapped_column(String(64))
    priority: Mapped[int] = mapped_column(Integer, default=1)
    source_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    results_count: Mapped[int] = mapped_column(Integer, default=0)

    job: Mapped[SearchJob] = relationship(back_populates="queries")


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"))
    candidate_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    local_path: Mapped[str] = mapped_column(Text)
    download_url: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(128))
    file_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_selected: Mapped[list[str]] = mapped_column(JSON, default=list)
    verified_signals: Mapped[list[str]] = mapped_column(JSON, default=list)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    source_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(64))
    institution_score: Mapped[float] = mapped_column(Float, default=0.0)
    topic_score: Mapped[float] = mapped_column(Float, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[SearchJob] = relationship(back_populates="files")


class JobArtifact(Base):
    __tablename__ = "job_artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"art_{uuid4().hex}")
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"))
    name: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(64))
    relative_path: Mapped[str] = mapped_column(Text)
    download_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[SearchJob] = relationship(back_populates="artifacts")


class SourceMemory(Base):
    __tablename__ = "source_memory"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"src_{uuid4().hex}")
    domain: Mapped[str] = mapped_column(String(255), unique=True)
    trust_score: Mapped[float] = mapped_column(Float, default=0.5)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"fb_{uuid4().hex}")
    job_id: Mapped[str] = mapped_column(ForeignKey("search_jobs.id"))
    file_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64))
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
