from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("BROKER_MODE", "stub")
os.environ.setdefault("DATABASE_URL", "sqlite:///./agent_search_test.db")
os.environ.setdefault("ARTIFACT_ROOT", str(Path.cwd() / ".local" / "test-artifacts"))


@pytest.fixture(autouse=True)
def clean_artifacts() -> None:
    artifact_root = Path(os.environ["ARTIFACT_ROOT"])
    artifact_root.mkdir(parents=True, exist_ok=True)
    for path in artifact_root.rglob("*"):
        if path.is_file():
            path.unlink()

