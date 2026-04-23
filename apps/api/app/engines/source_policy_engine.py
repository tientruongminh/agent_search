from __future__ import annotations

import json
from functools import lru_cache
from urllib.parse import urlparse

from app.core.config import settings
from app.schemas.candidate import Candidate

OFFICIAL_DOMAINS = {"hcmus.edu.vn", "fit.hcmus.edu.vn", "math.hcmus.edu.vn"}


@lru_cache
def load_policy_config() -> dict:
    return json.loads(settings.source_policy_path.read_text(encoding="utf-8"))


class SourcePolicyEngine:
    def __init__(self) -> None:
        self.config = load_policy_config()

    def classify(self, candidate: Candidate) -> str:
        domain = (candidate.domain or urlparse(candidate.stable_url()).hostname or "").lower()
        if any(domain == item or domain.endswith(f".{item}") for item in OFFICIAL_DOMAINS):
            return "official_domain"
        if "github.com" in domain and candidate.source_type == "github_repo":
            return "github_repo"
        if "githubusercontent.com" in domain or ("github.com" in domain and candidate.source_type == "github_file"):
            return "github_file"
        if candidate.source_type.endswith("_page") or candidate.source_type.endswith("_blog"):
            return "community_blog"
        return "unknown_mirror"

    def policy_for(self, candidate: Candidate) -> dict[str, float]:
        return self.config.get(self.classify(candidate), self.config["unknown_mirror"])

    def source_quality(self, candidate: Candidate) -> float:
        return float(self.policy_for(candidate).get("trust_score", 0.2))

