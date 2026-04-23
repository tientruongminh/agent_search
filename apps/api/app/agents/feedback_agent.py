from __future__ import annotations

from app.schemas.search_state import SearchState
from app.storage.repositories.jobs import JobRepository


class FeedbackAgent:
    def update_from_job(self, state: SearchState, repo: JobRepository) -> None:
        for ranked in state.ranked_files[:10]:
            if ranked.source_domain:
                repo.upsert_source_memory(ranked.source_domain, ranked.final_score)
