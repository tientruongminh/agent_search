from __future__ import annotations

import logging

from app.agents.course_crawler_agent import CourseCrawlerAgent
from app.agents.expansion_agent import ExpansionAgent
from app.agents.feedback_agent import FeedbackAgent
from app.agents.github_discovery_agent import GitHubDiscoveryAgent
from app.agents.intent_agent import IntentAgent
from app.agents.query_strategy_agent import QueryStrategyAgent
from app.agents.search_engine_agent import SearchEngineAgent
from app.core.budget import BudgetController
from app.core.metrics import increment_metric
from app.core.state_machine import JobStage, validate_transition
from app.engines.dedupe_engine import DedupeEngine
from app.engines.packaging_engine import PackagingEngine
from app.engines.ranking_engine import RankingEngine
from app.schemas.api import SearchRequest
from app.schemas.events import StateEvent
from app.schemas.query_plan import QueryGroup
from app.schemas.search_state import SearchState
from app.schemas.verified_candidate import VerifiedCandidate
from app.services.hashing import sha256_file
from app.storage.models import SearchJob
from app.storage.repositories.jobs import JobRepository
from app.verifiers.format_verifier import FormatVerifier
from app.verifiers.institution_verifier import InstitutionVerifier
from app.verifiers.semantic_verifier import SemanticVerifier
from app.verifiers.transport_verifier import TransportVerifier

logger = logging.getLogger(__name__)


class SearchOrchestratorV2:
    def __init__(
        self,
        *,
        intent_agent: IntentAgent,
        query_agent: QueryStrategyAgent,
        budget: BudgetController,
        search_agent: SearchEngineAgent,
        github_agent: GitHubDiscoveryAgent,
        course_agent: CourseCrawlerAgent,
        expansion: ExpansionAgent,
        dedupe: DedupeEngine,
        transport: TransportVerifier,
        format_verifier: FormatVerifier,
        semantic: SemanticVerifier,
        institution: InstitutionVerifier,
        ranker: RankingEngine,
        packager: PackagingEngine,
        feedback: FeedbackAgent,
    ) -> None:
        self.intent_agent = intent_agent
        self.query_agent = query_agent
        self.budget = budget
        self.search_agent = search_agent
        self.github_agent = github_agent
        self.course_agent = course_agent
        self.expansion = expansion
        self.dedupe = dedupe
        self.transport = transport
        self.format = format_verifier
        self.semantic = semantic
        self.institution = institution
        self.ranker = ranker
        self.packager = packager
        self.feedback = feedback

    def run(self, job: SearchJob, request: SearchRequest, repo: JobRepository) -> SearchState:
        state = SearchState(job_id=job.id, raw_request=request.raw_request)
        self._transition(state, repo, job, JobStage.PLANNING, "orchestrator", "planning.started")
        state.intent = self.intent_agent.run(request.raw_request)
        if request.goal:
            state.intent.goal = request.goal
        if request.preferred_formats:
            state.intent.preferred_formats = request.preferred_formats
        if request.strictness:
            state.intent.strictness = request.strictness
        self._event(state, repo, "intent_agent", "planning.intent_parsed", {"goal": state.intent.goal.value})

        self._transition(state, repo, job, JobStage.BUDGETING, "orchestrator", "budgeting.started")
        state.plan = self.query_agent.run(state.intent)
        repo.replace_queries(state.job_id, state.plan)
        state.budget = self.budget.init_budget(
            state.intent.goal,
            state.intent.strictness.institution_strict,
            request.max_downloads,
        )
        self._event(state, repo, "query_strategy_agent", "planning.query_plan_created", {"groups": len(state.plan.query_groups)})

        verified_files = self._discover_expand_verify(state, repo, retry=False)
        if len(verified_files) < 3 and state.reflection_count < state.budget.max_reflection_loops:
            state.reflection_count += 1
            state.fallback_mode = "broadened_queries"
            state.intent.strictness.source_strict = False
            state.intent.strictness.format_strict = False
            if state.plan.query_groups:
                fallback_group = state.plan.query_groups[0].model_copy(
                    update={
                        "purpose": "fallback_broadened",
                        "queries": [f"{state.intent.topic} {state.intent.institution or ''} resources", f"{state.intent.topic} notes pdf"],
                    }
                )
            else:
                fallback_group = QueryGroup(
                    purpose="fallback_broadened",
                    source_type="search",
                    priority=99,
                    queries=[f"{state.intent.topic} {state.intent.institution or ''} resources", f"{state.intent.topic} notes pdf"],
                )
            state.plan.query_groups.append(fallback_group)
            verified_files = self._discover_expand_verify(state, repo, retry=True)
        state.verified_files = verified_files

        self._transition(state, repo, job, JobStage.RANKING, "orchestrator", "ranking.started")
        state.ranked_files = self.ranker.run(state.verified_files, state.intent)
        repo.replace_ranked_files(state.job_id, state.ranked_files)
        increment_metric("jobs_ranked")
        self._event(state, repo, "ranking_engine", "ranking.completed", {"files": len(state.ranked_files)})

        self._transition(state, repo, job, JobStage.PACKAGING, "orchestrator", "packaging.started")
        state.packaged_artifacts = self.packager.run(state)
        repo.replace_artifacts(state.job_id, state.packaged_artifacts)
        increment_metric("bundles_created")
        self._event(state, repo, "packaging_engine", "packaging.bundle_created", {"artifacts": len(state.packaged_artifacts.artifacts)})

        self._transition(state, repo, job, JobStage.FEEDBACK_UPDATE, "orchestrator", "feedback.started")
        self.feedback.update_from_job(state, repo)
        self._event(state, repo, "feedback_agent", "feedback.memory_updated", {})

        self._transition(state, repo, job, JobStage.DONE, "orchestrator", "job.completed")
        increment_metric("jobs_completed")
        return state

    def _discover_expand_verify(self, state: SearchState, repo: JobRepository, *, retry: bool) -> list[VerifiedCandidate]:
        self._transition(state, repo, repo.require_job(state.job_id), JobStage.DISCOVERING, "orchestrator", "discovering.started")
        discovered, counts = self.search_agent.run(state.plan, state.budget)
        discovered.extend(self.github_agent.run(state.plan, state.budget))
        discovered.extend(self.course_agent.run(discovered, state.budget))
        repo.mark_queries_complete(state.job_id, counts)
        state.discovered_candidates = discovered
        increment_metric("candidates_discovered")
        self._event(state, repo, "discovery", "discovering.completed", {"count": len(discovered), "retry": retry})

        self._transition(state, repo, repo.require_job(state.job_id), JobStage.EXPANDING, "orchestrator", "expanding.started")
        state.expanded_candidates = self.expansion.run(discovered, state.budget)
        self._event(state, repo, "expansion_agent", "expanding.completed", {"count": len(state.expanded_candidates)})

        self._transition(state, repo, repo.require_job(state.job_id), JobStage.DEDUPING, "orchestrator", "deduping.started")
        state.deduped_candidates = self.dedupe.run(state.expanded_candidates)
        self._event(state, repo, "dedupe_engine", "deduping.completed", {"count": len(state.deduped_candidates)})

        self._transition(state, repo, repo.require_job(state.job_id), JobStage.VERIFYING, "orchestrator", "verifying.started")
        verified: list[VerifiedCandidate] = []
        for candidate in state.deduped_candidates[: state.budget.max_verifications]:
            transport = self.transport.verify(candidate, job_id=state.job_id)
            if not transport.ok or transport.download is None:
                self._event(state, repo, "transport_verifier", "verifying.transport_failed", {"url": candidate.source_url, "reason": transport.reason})
                continue
            format_result = self.format.verify(transport.download.local_path, transport.download.content_type)
            if not format_result.ok:
                self._event(state, repo, "format_verifier", "verifying.format_failed", {"url": candidate.source_url, "reason": format_result.reason})
                continue

            semantic_result = self.semantic.verify(
                title=candidate.title_hint or candidate.filename or candidate.source_url,
                excerpt=format_result.excerpt,
                intent=state.intent,
                filename=candidate.filename or "",
            )
            institution_result = self.institution.verify(candidate, state.intent, excerpt=format_result.excerpt)
            reject_reasons: list[str] = []
            if semantic_result.topic_score < 0.25:
                reject_reasons.append("low_topic_score")
            if state.intent.strictness.institution_strict and institution_result.institution_score < 0.3:
                reject_reasons.append("institution_mismatch")
            if reject_reasons:
                self._event(state, repo, "verification", "verifying.rejected", {"url": candidate.source_url, "reasons": reject_reasons})
                continue

            verified.append(
                VerifiedCandidate(
                    candidate=candidate,
                    transport_ok=True,
                    format_ok=True,
                    semantic=semantic_result,
                    institution=institution_result,
                    confidence=round((semantic_result.topic_score + institution_result.institution_score) / 2, 4),
                    verified_signals=semantic_result.semantic_signals + institution_result.institution_signals,
                    reject_reasons=[],
                    local_path=transport.download.local_path,
                    sha256=sha256_file(transport.download.local_path),
                    size_bytes=transport.download.size_bytes,
                    page_count=format_result.page_count,
                    content_type=transport.download.content_type,
                )
            )
        self._event(state, repo, "verification", "verifying.completed", {"count": len(verified), "retry": retry})
        return verified

    def _transition(self, state: SearchState, repo: JobRepository, job: SearchJob, stage: JobStage, actor: str, event_name: str) -> None:
        validate_transition(state.stage, stage)
        state.stage = stage
        repo.update_job_stage(job, stage, fallback_mode=state.fallback_mode, reflection_count=state.reflection_count)
        event = StateEvent(stage=stage, actor=actor, event=event_name, payload={})
        state.logs.append(event)
        repo.add_event(state.job_id, event)
        repo.save_snapshot(state)

    def _event(self, state: SearchState, repo: JobRepository, actor: str, event_name: str, payload: dict) -> None:
        event = StateEvent(stage=state.stage, actor=actor, event=event_name, payload=payload)
        state.logs.append(event)
        repo.add_event(state.job_id, event)
