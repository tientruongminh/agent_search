from __future__ import annotations

from app.schemas.intent import Intent, IntentStrictness, SearchGoal
from app.services.openai_client import OpenAIJsonClient


class IntentAgent:
    def __init__(self, client: OpenAIJsonClient):
        self.client = client

    def run(self, raw_request: str) -> Intent:
        schema = Intent.model_json_schema()
        payload = self.client.generate_json(
            system_prompt="Extract a structured search intent for educational material retrieval. Return only fields defined by the schema.",
            user_prompt=raw_request,
            schema_name="search_intent",
            schema=schema,
        )
        if payload:
            try:
                return Intent.model_validate(payload)
            except Exception:
                pass
        return self._fallback(raw_request)

    def _fallback(self, raw_request: str) -> Intent:
        lowered = raw_request.lower()
        goal = SearchGoal.GENERAL_SEARCH
        if any(token in lowered for token in ["đề thi", "on thi", "midterm", "final", "quiz", "exam"]):
            goal = SearchGoal.EXAM_PREPARATION
        elif any(token in lowered for token in ["slide", "bài giảng", "lecture", "syllabus"]):
            goal = SearchGoal.LECTURE_MATERIAL
        elif any(token in lowered for token in ["paper", "research", "survey", "reference"]):
            goal = SearchGoal.RESEARCH_REFERENCE
        elif any(token in lowered for token in ["project", "lab", "implementation", "assignment"]):
            goal = SearchGoal.PROJECT_IMPLEMENTATION

        topic = raw_request
        institution = "HCMUS" if "hcmus" in lowered else None
        department = "FIT-HCMUS" if "fit" in lowered else None
        preferred_formats = [fmt for fmt in ["pdf", "ppt", "doc"] if fmt in lowered] or ["pdf"]
        return Intent(
            topic=topic.replace("hcmus", "").strip(),
            institution=institution,
            department=department,
            goal=goal,
            preferred_formats=preferred_formats,
            preferred_sources=["official_course_pages", "github_coursework", "public_notes"],
            language=["vi", "en"],
            strictness=IntentStrictness(
                institution_strict=bool(institution),
                format_strict="pdf" in preferred_formats,
                source_strict=False,
            ),
        )

