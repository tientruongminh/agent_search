from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


def slugify(value: str, default: str = "file") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or default


def filename_from_url(url: str, fallback: str = "document.bin") -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or fallback


def safe_filename(name: str) -> str:
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-.")
    return stem or "artifact"

