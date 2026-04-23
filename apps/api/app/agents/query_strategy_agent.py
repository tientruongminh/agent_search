from __future__ import annotations

from app.schemas.intent import Intent
from app.schemas.query_plan import QueryGroup, QueryPlan
from app.services.openai_client import OpenAIJsonClient


class QueryStrategyAgent:
    def __init__(self, client: OpenAIJsonClient):
        self.client = client

    def run(self, intent: Intent) -> QueryPlan:
        schema = QueryPlan.model_json_schema()
        payload = self.client.generate_json(
            system_prompt="Generate a query plan for document retrieval across search engines, GitHub, and course pages. Keep purpose/source labels precise.",
            user_prompt=intent.model_dump_json(),
            schema_name="query_plan",
            schema=schema,
        )
        if payload:
            try:
                return QueryPlan.model_validate(payload)
            except Exception:
                pass
        return self._fallback(intent)

    def _fallback(self, intent: Intent) -> QueryPlan:
        institution = f" {intent.institution}" if intent.institution else ""
        base_topic = intent.topic.strip()
        query_groups = [
            QueryGroup(
                purpose="official_pdf",
                source_type="search",
                priority=1,
                queries=[f"{base_topic}{institution} pdf", f"{base_topic}{institution} lecture slides"],
            ),
            QueryGroup(
                purpose="github_coursework",
                source_type="github_repo",
                priority=2,
                queries=[f"{base_topic}{institution} github", f"{base_topic}{institution} site:github.com"],
            ),
            QueryGroup(
                purpose="exam_focus",
                source_type="search",
                priority=3,
                queries=[f"{base_topic}{institution} đề thi", f"{base_topic}{institution} midterm"],
            ),
        ]
        return QueryPlan(query_groups=query_groups, bilingual=True, strategy="precision_first")

