from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.state_machine import JobStage, progress_for_stage
from app.schemas.api import FeedbackRequest, SearchRequest
from app.schemas.events import StateEvent
from app.schemas.file_result import ArtifactManifest, ArtifactItem, RankedFile
from app.schemas.query_plan import QueryPlan
from app.schemas.search_state import SearchState
from app.storage.models import FileRecord, JobArtifact, SearchJob, SearchQuery, SearchStateSnapshot, SourceMemory, StateEventModel, UserFeedback


class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_job(self, request: SearchRequest) -> SearchJob:
        job = SearchJob(
            raw_request=request.raw_request,
            goal=request.goal.value if request.goal else None,
            preferred_formats=request.preferred_formats,
            strictness=request.strictness.model_dump() if request.strictness else {},
            status="queued",
            stage=JobStage.QUEUED.value,
            progress=progress_for_stage(JobStage.QUEUED),
        )
        self.session.add(job)
        self.session.flush()
        return job

    def get_job(self, job_id: str) -> SearchJob | None:
        return self.session.get(SearchJob, job_id)

    def require_job(self, job_id: str) -> SearchJob:
        job = self.get_job(job_id)
        if not job:
            raise LookupError(f"Job {job_id} not found")
        return job

    def update_job_stage(
        self,
        job: SearchJob,
        stage: JobStage,
        *,
        status: str | None = None,
        fallback_mode: str | None = None,
        reflection_count: int | None = None,
        error_message: str | None = None,
    ) -> None:
        job.stage = stage.value
        job.status = status or ("completed" if stage == JobStage.DONE else "running")
        job.progress = progress_for_stage(stage)
        if fallback_mode is not None:
            job.fallback_mode = fallback_mode
        if reflection_count is not None:
            job.reflection_count = reflection_count
        if error_message is not None:
            job.error_message = error_message
        self.session.add(job)

    def add_event(self, job_id: str, event: StateEvent) -> None:
        self.session.add(
            StateEventModel(
                job_id=job_id,
                ts=event.ts,
                stage=event.stage.value,
                actor=event.actor,
                event=event.event,
                payload=event.payload,
            )
        )

    def save_snapshot(self, state: SearchState) -> None:
        self.session.add(
            SearchStateSnapshot(
                job_id=state.job_id,
                stage=state.stage.value,
                payload=state.model_dump(mode="json"),
            )
        )

    def replace_queries(self, job_id: str, plan: QueryPlan) -> None:
        self.session.execute(delete(SearchQuery).where(SearchQuery.job_id == job_id))
        for group in plan.query_groups:
            for query in group.queries:
                self.session.add(
                    SearchQuery(
                        job_id=job_id,
                        query_text=query,
                        purpose=group.purpose,
                        priority=group.priority,
                        source_type=group.source_type,
                        status="planned",
                    )
                )

    def mark_queries_complete(self, job_id: str, query_counts: dict[str, int]) -> None:
        query_rows = self.session.scalars(select(SearchQuery).where(SearchQuery.job_id == job_id)).all()
        for row in query_rows:
            row.status = "completed"
            row.results_count = query_counts.get(row.query_text, 0)
            self.session.add(row)

    def replace_ranked_files(self, job_id: str, ranked_files: Iterable[RankedFile]) -> None:
        self.session.execute(delete(FileRecord).where(FileRecord.job_id == job_id))
        for file in ranked_files:
            self.session.add(
                FileRecord(
                    id=file.id,
                    job_id=job_id,
                    candidate_url=file.download_url,
                    title=file.title,
                    local_path=file.local_path,
                    download_url=file.download_url,
                    sha256=file.sha256,
                    file_type=file.file_type,
                    size_bytes=file.size_bytes,
                    page_count=file.page_count,
                    summary=file.summary,
                    why_selected=file.why_selected,
                    verified_signals=file.verified_signals,
                    score_breakdown=file.score_breakdown,
                    source_domain=file.source_domain,
                    source_type="file",
                    institution_score=file.institution_score,
                    topic_score=file.topic_score,
                    final_score=file.final_score,
                )
            )

    def replace_artifacts(self, job_id: str, manifest: ArtifactManifest) -> None:
        self.session.execute(delete(JobArtifact).where(JobArtifact.job_id == job_id))
        for artifact in manifest.artifacts:
            self.session.add(
                JobArtifact(
                    id=artifact.id,
                    job_id=job_id,
                    name=artifact.name,
                    kind=artifact.kind,
                    relative_path=artifact.relative_path,
                    download_url=artifact.download_url,
                )
            )

    def list_events(self, job_id: str, limit: int = 50) -> list[StateEvent]:
        rows = (
            self.session.scalars(
                select(StateEventModel).where(StateEventModel.job_id == job_id).order_by(StateEventModel.id.desc()).limit(limit)
            )
            .all()
        )
        return [
            StateEvent(stage=JobStage(row.stage), actor=row.actor, event=row.event, payload=row.payload, ts=row.ts)
            for row in reversed(rows)
        ]

    def list_ranked_files(self, job_id: str) -> list[RankedFile]:
        rows = (
            self.session.scalars(select(FileRecord).where(FileRecord.job_id == job_id).order_by(FileRecord.final_score.desc()))
            .all()
        )
        return [
            RankedFile(
                id=row.id,
                title=row.title,
                local_path=row.local_path,
                download_url=row.download_url,
                sha256=row.sha256,
                file_type=row.file_type,
                size_bytes=row.size_bytes,
                page_count=row.page_count,
                source_domain=row.source_domain,
                summary=row.summary,
                why_selected=row.why_selected,
                verified_signals=row.verified_signals,
                institution_score=row.institution_score,
                topic_score=row.topic_score,
                final_score=row.final_score,
                score_breakdown=row.score_breakdown,
            )
            for row in rows
        ]

    def get_artifact_manifest(self, job_id: str) -> ArtifactManifest:
        rows = self.session.scalars(select(JobArtifact).where(JobArtifact.job_id == job_id).order_by(JobArtifact.created_at)).all()
        items = [
            ArtifactItem(
                id=row.id,
                name=row.name,
                kind=row.kind,
                relative_path=row.relative_path,
                download_url=row.download_url,
            )
            for row in rows
        ]
        bundle_url = next((item.download_url for item in items if item.kind == "bundle"), None)
        output_dir = f"jobs/{job_id}"
        return ArtifactManifest(job_id=job_id, artifacts=items, bundle_url=bundle_url, output_dir=output_dir)

    def get_artifact(self, job_id: str, artifact_id: str) -> JobArtifact | None:
        return self.session.scalar(
            select(JobArtifact).where(JobArtifact.job_id == job_id, JobArtifact.id == artifact_id)
        )

    def record_feedback(self, job_id: str, payload: FeedbackRequest) -> UserFeedback:
        feedback = UserFeedback(
            job_id=job_id,
            file_id=payload.file_id,
            action=payload.action,
            score=payload.score,
            payload=payload.metadata,
        )
        self.session.add(feedback)
        self.session.flush()
        return feedback

    def upsert_source_memory(self, domain: str, quality: float) -> None:
        row = self.session.scalar(select(SourceMemory).where(SourceMemory.domain == domain))
        if row is None:
            row = SourceMemory(domain=domain, trust_score=quality, success_rate=1.0, avg_quality_score=quality)
        else:
            row.avg_quality_score = round((row.avg_quality_score + quality) / 2, 4)
            row.success_rate = min(1.0, row.success_rate + 0.05)
            row.trust_score = round((row.trust_score + quality) / 2, 4)
        self.session.add(row)
