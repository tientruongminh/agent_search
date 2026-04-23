from __future__ import annotations

import json
from functools import lru_cache
from uuid import uuid4

from app.core.config import settings
from app.engines.source_policy_engine import SourcePolicyEngine
from app.schemas.file_result import RankedFile
from app.schemas.intent import Intent
from app.schemas.verified_candidate import VerifiedCandidate
from app.utils.scoring import weighted_score


@lru_cache
def load_profiles() -> dict:
    return json.loads(settings.ranking_profiles_path.read_text(encoding="utf-8"))


class RankingEngine:
    def __init__(self, source_policy: SourcePolicyEngine):
        self.source_policy = source_policy
        self.profiles = load_profiles()

    def run(self, verified_candidates: list[VerifiedCandidate], intent: Intent) -> list[RankedFile]:
        weights = self.profiles[intent.goal.value]
        ranked: list[RankedFile] = []
        for item in verified_candidates:
            source_quality = self.source_policy.source_quality(item.candidate)
            exam_usefulness = self._exam_usefulness(item.semantic.file_type)
            file_usability = self._file_usability(item.size_bytes, item.page_count, item.candidate.mime_hint)
            total, breakdown = weighted_score(
                weights,
                {
                    "source_quality": source_quality,
                    "topic_relevance": item.semantic.topic_score,
                    "institution_match": item.institution.institution_score,
                    "exam_usefulness": exam_usefulness,
                    "file_usability": file_usability,
                },
            )
            why_selected = [
                f"topic score {item.semantic.topic_score:.2f}",
                f"institution score {item.institution.institution_score:.2f}",
                f"source quality {source_quality:.2f}",
                f"file type {item.semantic.file_type}",
            ]
            title = item.semantic.summary or item.candidate.title_hint or item.candidate.filename or item.candidate.source_url
            ranked.append(
                RankedFile(
                    id=f"file_{uuid4().hex}",
                    title=title[:180],
                    local_path=item.local_path,
                    download_url=item.candidate.stable_url(),
                    sha256=item.sha256,
                    file_type=item.semantic.file_type,
                    size_bytes=item.size_bytes,
                    page_count=item.page_count,
                    source_domain=item.candidate.domain,
                    summary=item.semantic.summary,
                    why_selected=why_selected,
                    verified_signals=item.verified_signals,
                    institution_score=item.institution.institution_score,
                    topic_score=item.semantic.topic_score,
                    final_score=total,
                    score_breakdown=breakdown,
                )
            )
        return sorted(ranked, key=lambda entry: entry.final_score, reverse=True)

    def _exam_usefulness(self, file_type: str) -> float:
        return {
            "exam": 1.0,
            "lecture": 0.7,
            "project": 0.5,
            "reference": 0.6,
            "document": 0.5,
        }.get(file_type, 0.4)

    def _file_usability(self, size_bytes: int, page_count: int | None, mime_hint: str | None) -> float:
        size_score = 1.0 if 50_000 <= size_bytes <= 20_000_000 else 0.5
        page_score = 0.6 if page_count is None else min(1.0, max(0.3, page_count / 20))
        format_score = 1.0 if (mime_hint or "").lower().endswith("pdf") else 0.8
        return round((size_score + page_score + format_score) / 3, 4)

