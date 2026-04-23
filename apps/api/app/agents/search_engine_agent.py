from __future__ import annotations

from urllib.parse import urlparse

from app.schemas.candidate import Candidate
from app.schemas.query_plan import Budget, QueryPlan
from app.services.brave_search import BraveSearchService
from app.utils.filenames import filename_from_url


class SearchEngineAgent:
    def __init__(self, brave: BraveSearchService):
        self.brave = brave

    def run(self, plan: QueryPlan, budget: Budget) -> tuple[list[Candidate], dict[str, int]]:
        candidates: list[Candidate] = []
        counts: dict[str, int] = {}
        for group in plan.query_groups[: budget.max_queries_per_job]:
            if group.source_type not in {"search", "official_page", "community_page"}:
                continue
            for query in group.queries:
                results = self.brave.search(query, count=min(budget.max_candidates_per_source, 10))
                counts[query] = len(results)
                for item in results:
                    url = item.get("url") or item.get("profile", {}).get("url")
                    if not url:
                        continue
                    domain = urlparse(url).hostname
                    candidates.append(
                        Candidate(
                            source_url=url,
                            canonical_url=url,
                            source_type="official_page" if domain and domain.endswith("hcmus.edu.vn") else "community_page",
                            discovery_agent="search_engine_agent",
                            domain=domain,
                            title_hint=item.get("title"),
                            mime_hint=item.get("page_age"),
                            score_raw=0.5,
                            filename=filename_from_url(url),
                        )
                    )
        return candidates, counts

