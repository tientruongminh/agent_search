from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.page_fetcher import GuardrailViolation, validate_outbound_url
from app.services.storage import LocalArtifactStorage
from app.utils.filenames import filename_from_url, safe_filename


@dataclass
class DownloadResult:
    local_path: str
    relative_path: str
    final_url: str
    content_type: str | None
    size_bytes: int


class Downloader:
    def __init__(self, storage: LocalArtifactStorage):
        self.storage = storage

    def download(self, url: str, *, job_id: str, preferred_name: str | None = None) -> DownloadResult:
        validate_outbound_url(url)
        with httpx.Client(timeout=settings.request_timeout_seconds, follow_redirects=True, max_redirects=settings.redirect_limit) as client:
            with client.stream("GET", url, headers={"User-Agent": "agentic-material-search-v2"}) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type")
                total = 0
                chunks: list[bytes] = []
                for chunk in response.iter_bytes():
                    total += len(chunk)
                    if total > settings.max_file_size_bytes:
                        raise GuardrailViolation("File exceeds max size")
                    chunks.append(chunk)
                payload = b"".join(chunks)
                extension = Path(urlparse(str(response.url)).path).suffix
                base_name = preferred_name or filename_from_url(str(response.url))
                if extension and not base_name.endswith(extension):
                    base_name = f"{base_name}{extension}"
                relative_path = f"jobs/{job_id}/downloads/{safe_filename(base_name)}"
                stored = self.storage.save_bytes(relative_path, payload)
                return DownloadResult(
                    local_path=stored.local_path,
                    relative_path=stored.relative_path,
                    final_url=str(response.url),
                    content_type=content_type,
                    size_bytes=len(payload),
                )
