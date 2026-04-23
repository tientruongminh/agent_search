from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from app.schemas.candidate import Candidate
from app.utils.text_similarity import jaccard_similarity


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", "", ""))


class DedupeEngine:
    def run(self, candidates: list[Candidate]) -> list[Candidate]:
        deduped: list[Candidate] = []
        seen_canonical: set[str] = set()
        seen_resolved: set[str] = set()
        seen_filenames: set[str] = set()
        seen_sha_like: set[str] = set()

        for candidate in candidates:
            canonical = canonicalize_url(candidate.canonical_url or candidate.source_url)
            resolved = canonicalize_url(candidate.resolved_url) if candidate.resolved_url else None
            filename = (candidate.filename or "").lower().strip()
            title = (candidate.title_hint or "").strip().lower()

            if canonical and canonical in seen_canonical:
                continue
            if resolved and resolved in seen_resolved:
                continue
            if filename and filename in seen_filenames:
                continue
            if any(jaccard_similarity(title, existing.title_hint or "") > 0.95 for existing in deduped if title):
                continue

            seen_canonical.add(canonical)
            if resolved:
                seen_resolved.add(resolved)
            if filename:
                seen_filenames.add(filename)
            if candidate.metadata.get("sha256"):
                seen_sha_like.add(str(candidate.metadata["sha256"]))
            deduped.append(candidate)
        return deduped

