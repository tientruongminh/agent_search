from __future__ import annotations

from urllib.parse import urlparse

from app.schemas.candidate import Candidate
from app.schemas.query_plan import Budget
from app.services.page_fetcher import PageFetcher
from app.utils.filenames import filename_from_url


class CourseCrawlerAgent:
    def __init__(self, fetcher: PageFetcher):
        self.fetcher = fetcher

    def run(self, discovered: list[Candidate], budget: Budget) -> list[Candidate]:
        expanded: list[Candidate] = []
        official_pages = [item for item in discovered if item.source_type == "official_page"][: budget.max_candidates_per_source]
        for candidate in official_pages:
            try:
                document = self.fetcher.fetch_html(candidate.source_url)
                for link in self.fetcher.extract_document_links(document):
                    url = link["url"]
                    expanded.append(
                        Candidate(
                            source_url=url,
                            canonical_url=url,
                            parent_url=candidate.source_url,
                            source_type="official_file" if url.endswith((".pdf", ".ppt", ".pptx", ".doc", ".docx")) else "official_page",
                            discovery_agent="course_crawler_agent",
                            domain=urlparse(url).hostname,
                            title_hint=link["label"],
                            filename=filename_from_url(url),
                            depth=candidate.depth + 1,
                            score_raw=0.75,
                        )
                    )
            except Exception:
                continue
        return expanded

