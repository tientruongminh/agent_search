from pathlib import Path

from app.engines.ranking_engine import RankingEngine
from app.engines.source_policy_engine import SourcePolicyEngine
from app.schemas.candidate import Candidate
from app.schemas.intent import Intent, IntentStrictness, SearchGoal
from app.schemas.verified_candidate import InstitutionVerification, SemanticVerification, VerifiedCandidate


def test_ranking_engine_orders_highest_score_first(tmp_path: Path) -> None:
    path = tmp_path / "doc.pdf"
    path.write_bytes(b"%PDF-1.4\n")
    candidate = Candidate(source_url="https://fit.hcmus.edu.vn/doc.pdf", source_type="official_file", discovery_agent="test", domain="fit.hcmus.edu.vn")
    verified = VerifiedCandidate(
        candidate=candidate,
        transport_ok=True,
        format_ok=True,
        semantic=SemanticVerification(semantic_signals=["machine", "learning"], topic_score=0.9, file_type="lecture"),
        institution=InstitutionVerification(institution_signals=["HCMUS"], institution_score=0.8),
        confidence=0.85,
        verified_signals=["machine", "HCMUS"],
        local_path=str(path),
        sha256="abc",
        size_bytes=200000,
        page_count=32,
        content_type="application/pdf",
    )
    ranking = RankingEngine(SourcePolicyEngine()).run(
        [verified],
        Intent(
            topic="machine learning",
            institution="HCMUS",
            goal=SearchGoal.LECTURE_MATERIAL,
            strictness=IntentStrictness(institution_strict=True),
        ),
    )
    assert ranking[0].final_score > 0.5

