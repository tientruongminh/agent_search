from __future__ import annotations

import logging
import re

from app.schemas.intent import Intent, SearchGoal
from app.schemas.verified_candidate import SemanticVerification
from app.utils.text_similarity import cosine_text_similarity, jaccard_similarity

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer, util
except Exception:
    SentenceTransformer = None
    util = None


class SemanticVerifier:
    def __init__(self) -> None:
        self.model = None
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            except Exception:
                logger.exception("Embedding model failed to initialize")
                self.model = None

    def verify(self, *, title: str, excerpt: str | None, intent: Intent, filename: str) -> SemanticVerification:
        text = " ".join(part for part in [title, excerpt or "", filename] if part)
        topic_score = self._topic_score(intent.topic, text)
        file_type = self._classify_file_type(text, intent.goal)
        signals = self._signals(intent.topic, text, file_type)
        summary = (excerpt or title or filename).strip()[:300] or None
        return SemanticVerification(
            semantic_signals=signals,
            topic_score=topic_score,
            file_type=file_type,
            summary=summary,
            excerpt=(excerpt or "")[:1200] or None,
        )

    def _topic_score(self, topic: str, text: str) -> float:
        lexical = max(jaccard_similarity(topic, text), cosine_text_similarity(topic, text))
        if self.model is None or util is None:
            return round(min(1.0, lexical), 4)
        try:
            embeddings = self.model.encode([topic, text], convert_to_tensor=True)
            semantic = float(util.cos_sim(embeddings[0], embeddings[1]).item())
            semantic = (semantic + 1) / 2
            return round(max(lexical, semantic), 4)
        except Exception:
            logger.exception("Embedding similarity failed")
            return round(min(1.0, lexical), 4)

    def _classify_file_type(self, text: str, goal: SearchGoal) -> str:
        lowered = text.lower()
        if re.search(r"\b(midterm|final|quiz|exam|de thi|on thi)\b", lowered):
            return "exam"
        if re.search(r"\b(slide|lecture|bai giang|chapter|syllabus)\b", lowered):
            return "lecture"
        if re.search(r"\b(project|implementation|lab|assignment|notebook)\b", lowered):
            return "project"
        if goal == SearchGoal.RESEARCH_REFERENCE:
            return "reference"
        return "document"

    def _signals(self, topic: str, text: str, file_type: str) -> list[str]:
        topic_tokens = [token for token in re.findall(r"[a-zA-Z0-9]+", topic.lower()) if token]
        text_lower = text.lower()
        matched = [token for token in topic_tokens if token in text_lower]
        if file_type not in matched:
            matched.append(file_type)
        return matched[:6]

