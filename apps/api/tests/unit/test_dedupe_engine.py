from app.engines.dedupe_engine import DedupeEngine
from app.schemas.candidate import Candidate


def test_dedupe_engine_removes_duplicate_urls() -> None:
    engine = DedupeEngine()
    candidates = [
        Candidate(source_url="https://example.com/a.pdf", source_type="expanded_file", discovery_agent="x"),
        Candidate(source_url="https://example.com/a.pdf?download=1", canonical_url="https://example.com/a.pdf", source_type="expanded_file", discovery_agent="y"),
    ]
    deduped = engine.run(candidates)
    assert len(deduped) == 1

