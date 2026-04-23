from __future__ import annotations

from urllib.parse import urlparse

from app.schemas.candidate import Candidate
from app.schemas.query_plan import Budget, QueryPlan
from app.services.github_api import GitHubService


class GitHubDiscoveryAgent:
    def __init__(self, github: GitHubService):
        self.github = github

    def run(self, plan: QueryPlan, budget: Budget) -> list[Candidate]:
        candidates: list[Candidate] = []
        github_queries = [group for group in plan.query_groups if group.source_type == "github_repo"]
        for group in github_queries[: budget.max_queries_per_job]:
            for query in group.queries:
                repos = self.github.search_repositories(query, limit=min(5, budget.max_candidates_per_source))
                for repo in repos:
                    url = repo.get("html_url")
                    if not url:
                        continue
                    candidates.append(
                        Candidate(
                            source_url=url,
                            canonical_url=url,
                            source_type="github_repo",
                            discovery_agent="github_discovery_agent",
                            domain=urlparse(url).hostname,
                            title_hint=repo.get("full_name"),
                            score_raw=0.7,
                            metadata={"stars": repo.get("stargazers_count", 0)},
                        )
                    )
        return candidates

