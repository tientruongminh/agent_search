from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.budget import BudgetController
from app.core.state_machine import JobStage
from app.engines.dedupe_engine import DedupeEngine
from app.engines.packaging_engine import PackagingEngine
from app.engines.ranking_engine import RankingEngine
from app.engines.source_policy_engine import SourcePolicyEngine
from app.orchestration.orchestrator import SearchOrchestratorV2
from app.schemas.api import SearchRequest
from app.schemas.candidate import Candidate
from app.schemas.intent import Intent, IntentStrictness, SearchGoal
from app.schemas.query_plan import Budget, QueryPlan
from app.schemas.verified_candidate import InstitutionVerification, SemanticVerification
from app.services.storage import LocalArtifactStorage
from app.storage.models import Base
from app.storage.repositories.jobs import JobRepository


class FakeIntentAgent:
    def run(self, raw_request: str) -> Intent:
        return Intent(
            topic="machine learning",
            institution="HCMUS",
            goal=SearchGoal.EXAM_PREPARATION,
            preferred_formats=["pdf"],
            strictness=IntentStrictness(institution_strict=True, format_strict=True),
        )


class FakeQueryAgent:
    def run(self, intent: Intent) -> QueryPlan:
        return QueryPlan()


class FakeSearchAgent:
    def run(self, plan: QueryPlan, budget: Budget):
        candidate = Candidate(
            source_url="https://fit.hcmus.edu.vn/ml.pdf",
            source_type="official_file",
            discovery_agent="fake",
            domain="fit.hcmus.edu.vn",
            filename="ml.pdf",
            title_hint="Machine Learning Lecture",
        )
        return [candidate], {}


class FakeGitHubAgent:
    def run(self, plan: QueryPlan, budget: Budget):
        return []


class FakeCrawlerAgent:
    def run(self, discovered, budget: Budget):
        return []


class FakeExpansionAgent:
    def run(self, discovered, budget: Budget):
        return discovered


class FakeTransportVerifier:
    def __init__(self, path: str):
        self.path = path

    def verify(self, candidate: Candidate, *, job_id: str):
        class Result:
            ok = True
            reason = None
            download = type(
                "Download",
                (),
                {
                    "local_path": self.path,
                    "relative_path": "jobs/test/downloads/ml.pdf",
                    "final_url": candidate.source_url,
                    "content_type": "application/pdf",
                    "size_bytes": Path(self.path).stat().st_size,
                },
            )()

        return Result()


class FakeFormatVerifier:
    def verify(self, path: str, content_type: str | None = None):
        class Result:
            ok = True
            reason = None
            page_count = 24
            excerpt = "Machine learning regression classification"
            title = "Machine Learning"

        return Result()


class FakeSemanticVerifier:
    def verify(self, *, title: str, excerpt: str | None, intent: Intent, filename: str):
        return SemanticVerification(semantic_signals=["machine", "learning"], topic_score=0.92, file_type="lecture", summary=title)


class FakeInstitutionVerifier:
    def verify(self, candidate: Candidate, intent: Intent, excerpt: str | None = None):
        return InstitutionVerification(institution_signals=["HCMUS"], institution_score=0.88)


class FakeFeedbackAgent:
    def update_from_job(self, state, repo):
        return None


def test_orchestrator_pipeline_persists_results(tmp_path: Path) -> None:
    pdf_path = tmp_path / "ml.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nfake")

    engine = create_engine(f"sqlite:///{tmp_path / 'integration.db'}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    with Session() as session:
        repo = JobRepository(session)
        job = repo.create_job(SearchRequest(raw_request="machine learning hcmus", goal=SearchGoal.EXAM_PREPARATION))
        session.commit()

        orchestrator = SearchOrchestratorV2(
            intent_agent=FakeIntentAgent(),
            query_agent=FakeQueryAgent(),
            budget=BudgetController(),
            search_agent=FakeSearchAgent(),
            github_agent=FakeGitHubAgent(),
            course_agent=FakeCrawlerAgent(),
            expansion=FakeExpansionAgent(),
            dedupe=DedupeEngine(),
            transport=FakeTransportVerifier(str(pdf_path)),
            format_verifier=FakeFormatVerifier(),
            semantic=FakeSemanticVerifier(),
            institution=FakeInstitutionVerifier(),
            ranker=RankingEngine(SourcePolicyEngine()),
            packager=PackagingEngine(LocalArtifactStorage(tmp_path / "artifacts")),
            feedback=FakeFeedbackAgent(),
        )
        state = orchestrator.run(job, SearchRequest(raw_request="machine learning hcmus"), repo)
        session.commit()

    assert state.stage == JobStage.DONE
    assert len(state.ranked_files) == 1
    assert state.packaged_artifacts is not None
    assert any(item.kind == "bundle" for item in state.packaged_artifacts.artifacts)

