from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SearchGoal(StrEnum):
    EXAM_PREPARATION = "exam_preparation"
    LECTURE_MATERIAL = "lecture_material"
    RESEARCH_REFERENCE = "research_reference"
    PROJECT_IMPLEMENTATION = "project_implementation"
    GENERAL_SEARCH = "general_search"


class IntentStrictness(BaseModel):
    institution_strict: bool = True
    format_strict: bool = False
    source_strict: bool = False


class Intent(BaseModel):
    topic: str
    institution: str | None = None
    department: str | None = None
    goal: SearchGoal = SearchGoal.GENERAL_SEARCH
    preferred_formats: list[str] = Field(default_factory=lambda: ["pdf"])
    preferred_sources: list[str] = Field(default_factory=list)
    language: list[str] = Field(default_factory=lambda: ["vi", "en"])
    strictness: IntentStrictness = Field(default_factory=IntentStrictness)

