from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_REPO_PATTERN = re.compile(r"github\.com/(?P<owner>[^/]+)/(?P<repo>[^/#?]+)")


class GitHubService:
    base_url = "https://api.github.com"

    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "agentic-material-search-v2",
        }
        if settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token}"

    def search_repositories(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        try:
            with httpx.Client(timeout=settings.request_timeout_seconds, headers=self.headers) as client:
                response = client.get(f"{self.base_url}/search/repositories", params={"q": query, "per_page": limit})
                response.raise_for_status()
            return response.json().get("items", [])
        except Exception:
            logger.exception("GitHub repository search failed for query=%s", query)
            return []

    def list_repository_assets(self, repo_url: str, max_depth: int = 4, limit: int = 12) -> list[dict[str, Any]]:
        parsed = self.parse_repo_url(repo_url)
        if not parsed:
            return []
        owner, repo = parsed
        try:
            with httpx.Client(timeout=settings.request_timeout_seconds, headers=self.headers) as client:
                repo_response = client.get(f"{self.base_url}/repos/{owner}/{repo}")
                repo_response.raise_for_status()
                default_branch = repo_response.json().get("default_branch", "main")
                tree_response = client.get(f"{self.base_url}/repos/{owner}/{repo}/git/trees/{default_branch}", params={"recursive": 1})
                tree_response.raise_for_status()
            items = tree_response.json().get("tree", [])
        except Exception:
            logger.exception("GitHub repo expansion failed for repo=%s", repo_url)
            return []

        assets: list[dict[str, Any]] = []
        for item in items:
            path = item.get("path", "")
            if item.get("type") != "blob":
                continue
            if path.count("/") > max_depth:
                continue
            if not re.search(r"\.(pdf|ppt|pptx|doc|docx|ipynb|md|txt)$", path, re.IGNORECASE):
                continue
            assets.append(
                {
                    "path": path,
                    "html_url": f"https://github.com/{owner}/{repo}/blob/{default_branch}/{path}",
                    "download_url": f"https://raw.githubusercontent.com/{owner}/{repo}/{default_branch}/{path}",
                }
            )
        assets.sort(key=lambda asset: self._asset_priority(asset["path"]), reverse=True)
        return assets[:limit]

    @staticmethod
    def _asset_priority(path: str) -> tuple[int, int, int]:
        lowered = path.lower()
        extension_weights = {
            ".pdf": 5,
            ".md": 4,
            ".txt": 3,
            ".ipynb": 3,
            ".ppt": 2,
            ".pptx": 2,
            ".doc": 1,
            ".docx": 1,
        }
        extension_score = 0
        for suffix, score in extension_weights.items():
            if lowered.endswith(suffix):
                extension_score = score
                break
        keyword_score = sum(
            1
            for keyword in ["lecture", "note", "notes", "slide", "syllabus", "course", "machine-learning", "deep-learning"]
            if keyword in lowered
        )
        shallow_bonus = max(0, 6 - lowered.count("/"))
        return extension_score, keyword_score, shallow_bonus

    @staticmethod
    def parse_repo_url(repo_url: str) -> tuple[str, str] | None:
        match = _REPO_PATTERN.search(repo_url)
        if not match:
            return None
        return match.group("owner"), match.group("repo")

    @staticmethod
    def blob_to_raw(url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc != "github.com" or "/blob/" not in parsed.path:
            return url
        return url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
