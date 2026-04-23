from __future__ import annotations

import re
from urllib.parse import urlparse

from app.schemas.candidate import Candidate
from app.schemas.query_plan import Budget, QueryPlan
from app.services.github_api import GitHubService


class GitHubDiscoveryAgent:
    def __init__(self, github: GitHubService):
        self.github = github

    def run(self, plan: QueryPlan, budget: Budget) -> list[Candidate]:
        candidates: list[Candidate] = []
        seen_urls: set[str] = set()
        github_queries = [group for group in plan.query_groups if group.source_type == "github_repo"]
        for group in github_queries[: budget.max_queries_per_job]:
            for query in group.queries:
                for variant in self._query_variants(query):
                    repos = self.github.search_repositories(variant, limit=min(5, budget.max_candidates_per_source))
                    for repo in repos:
                        url = repo.get("html_url")
                        if not url or url in seen_urls:
                            continue
                        seen_urls.add(url)
                        candidates.append(
                            Candidate(
                                source_url=url,
                                canonical_url=url,
                                source_type="github_repo",
                                discovery_agent="github_discovery_agent",
                                domain=urlparse(url).hostname,
                                title_hint=repo.get("full_name"),
                                score_raw=0.7,
                                metadata={"stars": repo.get("stargazers_count", 0), "query_variant": variant},
                            )
                        )
                    if repos:
                        break
        return candidates

    def _query_variants(self, query: str) -> list[str]:
        variants: list[str] = []

        def add(value: str) -> None:
            normalized = re.sub(r"\s+", " ", value).strip()
            if normalized and normalized not in variants:
                variants.append(normalized)

        add(query)

        simplified = query.lower()
        simplified = re.sub(r"site:\S+", " ", simplified)
        simplified = re.sub(r"\b(github|gitlab|pdf|pptx?|docx?|slides?|lecture|notes?)\b", " ", simplified)
        add(simplified)

        institution_relaxed = re.sub(r"\b(hcmus|fit[- ]?hcmus|fit|vnu)\b", " ", simplified)
        add(institution_relaxed)

        compact_topic = re.sub(r"\b(machine learning|deep learning|data mining|computer vision|nlp)\b", lambda m: m.group(0), institution_relaxed)
        add(f"{compact_topic} course")
        add(f"{compact_topic} education")

        return variants[:5]
