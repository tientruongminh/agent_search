from __future__ import annotations

from app.schemas.intent import SearchGoal
from app.schemas.query_plan import Budget


class BudgetController:
    def init_budget(self, goal: SearchGoal, institution_strict: bool, max_downloads: int | None = None) -> Budget:
        base_queries = {
            SearchGoal.EXAM_PREPARATION: 12,
            SearchGoal.LECTURE_MATERIAL: 10,
            SearchGoal.RESEARCH_REFERENCE: 14,
            SearchGoal.PROJECT_IMPLEMENTATION: 10,
            SearchGoal.GENERAL_SEARCH: 8,
        }[goal]
        strict_bonus = -2 if institution_strict else 0
        max_download_count = max_downloads or 20
        return Budget(
            max_queries_per_job=max(6, base_queries + strict_bonus),
            max_candidates_per_source=25 if institution_strict else 40,
            max_expansion_depth=3 if institution_strict else 4,
            max_verifications=60 if institution_strict else 80,
            max_downloads=max_download_count,
            max_reflection_loops=1,
            max_runtime_seconds=180,
            max_llm_tokens=12000,
        )

