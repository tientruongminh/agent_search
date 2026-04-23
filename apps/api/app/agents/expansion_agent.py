from __future__ import annotations

from urllib.parse import urlparse

from app.engines.source_policy_engine import SourcePolicyEngine
from app.schemas.candidate import Candidate
from app.schemas.query_plan import Budget
from app.services.github_api import GitHubService
from app.services.page_fetcher import PageFetcher
from app.utils.filenames import filename_from_url


class ExpansionAgent:
    def __init__(self, github: GitHubService, fetcher: PageFetcher, source_policy: SourcePolicyEngine):
        self.github = github
        self.fetcher = fetcher
        self.source_policy = source_policy

    def run(self, discovered: list[Candidate], budget: Budget) -> list[Candidate]:
        expanded: list[Candidate] = list(discovered)
        github_repo_expansions = 0
        for candidate in discovered:
            policy = self.source_policy.policy_for(candidate)
            if candidate.depth >= min(policy.get("expand_depth", 0), budget.max_expansion_depth):
                continue
            if candidate.source_type == "github_repo":
                if github_repo_expansions >= max(2, budget.max_downloads):
                    continue
                assets = self.github.list_repository_assets(
                    candidate.source_url,
                    max_depth=int(policy.get("expand_depth", 3)),
                    limit=min(8, max(4, budget.max_downloads * 2)),
                )
                github_repo_expansions += 1
                for asset in assets:
                    expanded.append(
                        Candidate(
                            source_url=asset["download_url"],
                            canonical_url=asset["download_url"],
                            parent_url=candidate.source_url,
                            source_type="github_file",
                            discovery_agent="expansion_agent",
                            domain=urlparse(asset["download_url"]).hostname,
                            title_hint=asset["path"],
                            filename=filename_from_url(asset["download_url"]),
                            depth=candidate.depth + 1,
                            score_raw=0.85,
                        )
                    )
            elif candidate.source_type.endswith("_page"):
                try:
                    document = self.fetcher.fetch_html(candidate.source_url)
                    for link in self.fetcher.extract_document_links(document):
                        url = link["url"]
                        if not url.endswith((".pdf", ".ppt", ".pptx", ".doc", ".docx", ".md", ".txt")):
                            continue
                        expanded.append(
                            Candidate(
                                source_url=url,
                                canonical_url=url,
                                parent_url=candidate.source_url,
                                source_type="expanded_file",
                                discovery_agent="expansion_agent",
                                domain=urlparse(url).hostname,
                                title_hint=link["label"],
                                filename=filename_from_url(url),
                                depth=candidate.depth + 1,
                                score_raw=0.68,
                            )
                        )
                except Exception:
                    continue
        return expanded
