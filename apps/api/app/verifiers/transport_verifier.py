from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.schemas.candidate import Candidate
from app.services.downloader import DownloadResult, Downloader
from app.services.page_fetcher import GuardrailViolation


@dataclass
class TransportVerificationResult:
    ok: bool
    reason: str | None = None
    download: DownloadResult | None = None


class TransportVerifier:
    def __init__(self, downloader: Downloader):
        self.downloader = downloader

    def verify(self, candidate: Candidate, *, job_id: str) -> TransportVerificationResult:
        try:
            result = self.downloader.download(candidate.stable_url(), job_id=job_id, preferred_name=candidate.filename)
        except Exception as exc:
            return TransportVerificationResult(ok=False, reason=str(exc))

        content_type = (result.content_type or "").split(";")[0]
        if content_type and content_type not in settings.allowed_mime_types_set:
            return TransportVerificationResult(ok=False, reason=f"Unsupported MIME type: {content_type}")
        return TransportVerificationResult(ok=True, download=result)

