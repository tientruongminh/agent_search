from __future__ import annotations

from pydantic import BaseModel, Field


class QueryGroup(BaseModel):
    purpose: str
    source_type: str
    priority: int = 1
    queries: list[str] = Field(default_factory=list)


class QueryPlan(BaseModel):
    query_groups: list[QueryGroup] = Field(default_factory=list)
    bilingual: bool = False
    strategy: str = "precision_first"


class Budget(BaseModel):
    max_queries_per_job: int = 12
    max_candidates_per_source: int = 40
    max_expansion_depth: int = 3
    max_verifications: int = 80
    max_downloads: int = 20
    max_reflection_loops: int = 1
    max_runtime_seconds: int = 180
    max_llm_tokens: int = 12000

