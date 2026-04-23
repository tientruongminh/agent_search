from app.engines.source_policy_engine import SourcePolicyEngine
from app.schemas.candidate import Candidate


def test_source_policy_classifies_official_domain() -> None:
    engine = SourcePolicyEngine()
    candidate = Candidate(
        source_url="https://fit.hcmus.edu.vn/course/ml",
        source_type="official_page",
        discovery_agent="test",
        domain="fit.hcmus.edu.vn",
    )
    assert engine.classify(candidate) == "official_domain"
    assert engine.source_quality(candidate) > 0.8

