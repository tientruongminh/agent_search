from __future__ import annotations

import re
from urllib.parse import urlparse

from app.schemas.candidate import Candidate
from app.schemas.intent import Intent
from app.schemas.verified_candidate import InstitutionVerification


class InstitutionVerifier:
    def verify(self, candidate: Candidate, intent: Intent, excerpt: str | None = None) -> InstitutionVerification:
        text = " ".join([candidate.title_hint or "", candidate.source_url, excerpt or ""]).lower()
        signals: list[str] = []
        score = 0.0

        for marker in ["hcmus", "fit-hcmus", "fit hcmus", "khoa toan", "toan-tin", "truong dai hoc khoa hoc tu nhien"]:
            if marker in text:
                signals.append(marker.upper())
                score += 0.18

        host = (candidate.domain or urlparse(candidate.stable_url()).hostname or "").lower()
        if host.endswith("hcmus.edu.vn"):
            signals.append(host)
            score += 0.35
        if intent.institution and intent.institution.lower() in text:
            signals.append(intent.institution)
            score += 0.2
        if intent.department and intent.department.lower() in text:
            signals.append(intent.department)
            score += 0.1
        if re.search(r"\b(cs|math|ml|ai)\d{3}\b", text):
            signals.append("course_code_pattern")
            score += 0.05

        return InstitutionVerification(institution_signals=signals[:8], institution_score=round(min(score, 1.0), 4))

