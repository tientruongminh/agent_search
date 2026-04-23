from __future__ import annotations

import logging

import dramatiq

from app.agents.course_crawler_agent import CourseCrawlerAgent
from app.agents.expansion_agent import ExpansionAgent
from app.agents.feedback_agent import FeedbackAgent
from app.agents.github_discovery_agent import GitHubDiscoveryAgent
from app.agents.intent_agent import IntentAgent
from app.agents.query_strategy_agent import QueryStrategyAgent
from app.agents.search_engine_agent import SearchEngineAgent
from app.core.budget import BudgetController
from app.core.logging import configure_logging
from app.core.metrics import increment_metric
from app.core.state_machine import JobStage
from app.engines.dedupe_engine import DedupeEngine
from app.engines.packaging_engine import PackagingEngine
from app.engines.ranking_engine import RankingEngine
from app.engines.source_policy_engine import SourcePolicyEngine
from app.orchestration.orchestrator import SearchOrchestratorV2
from app.schemas.api import SearchRequest
from app.services.brave_search import BraveSearchService
from app.services.downloader import Downloader
from app.services.github_api import GitHubService
from app.services.openai_client import OpenAIJsonClient
from app.services.page_fetcher import PageFetcher
from app.services.pdf_reader import PdfReaderService
from app.services.storage import get_storage
from app.storage.db import session_scope
from app.storage.repositories.jobs import JobRepository
from app.verifiers.format_verifier import FormatVerifier
from app.verifiers.institution_verifier import InstitutionVerifier
from app.verifiers.semantic_verifier import SemanticVerifier
from app.verifiers.transport_verifier import TransportVerifier
from app.workers.broker import broker  # noqa: F401

logger = logging.getLogger(__name__)


def build_orchestrator() -> SearchOrchestratorV2:
    storage = get_storage()
    openai_client = OpenAIJsonClient()
    source_policy = SourcePolicyEngine()
    return SearchOrchestratorV2(
        intent_agent=IntentAgent(openai_client),
        query_agent=QueryStrategyAgent(openai_client),
        budget=BudgetController(),
        search_agent=SearchEngineAgent(BraveSearchService()),
        github_agent=GitHubDiscoveryAgent(GitHubService()),
        course_agent=CourseCrawlerAgent(PageFetcher()),
        expansion=ExpansionAgent(GitHubService(), PageFetcher(), source_policy),
        dedupe=DedupeEngine(),
        transport=TransportVerifier(Downloader(storage)),
        format_verifier=FormatVerifier(PdfReaderService()),
        semantic=SemanticVerifier(),
        institution=InstitutionVerifier(),
        ranker=RankingEngine(source_policy),
        packager=PackagingEngine(storage),
        feedback=FeedbackAgent(),
    )


@dramatiq.actor(max_retries=0)
def run_search_job(job_id: str) -> None:
    configure_logging()
    with session_scope() as session:
        repo = JobRepository(session)
        job = repo.require_job(job_id)
        request = SearchRequest.model_validate(
            {
                "raw_request": job.raw_request,
                "goal": job.goal,
                "preferred_formats": job.preferred_formats,
                "strictness": job.strictness,
            }
        )
        try:
            orchestrator = build_orchestrator()
            orchestrator.run(job, request, repo)
            increment_metric("jobs_processed")
        except Exception as exc:
            logger.exception("Search job failed", extra={"job_id": job_id})
            repo.update_job_stage(job, JobStage.FAILED, status="failed", error_message=str(exc))
            increment_metric("jobs_failed")
