from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import boto3

from app.core.config import settings


@dataclass
class StoredObject:
    relative_path: str
    local_path: str
    public_path: str
    mirror_url: str | None = None


class LocalArtifactStorage:
    def __init__(self, root: Path | None = None):
        self.root = (root or settings.artifact_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, relative_path: str, payload: bytes) -> StoredObject:
        absolute_path = self.root / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(payload)
        return StoredObject(relative_path=relative_path, local_path=str(absolute_path), public_path=str(absolute_path))

    def save_text(self, relative_path: str, payload: str) -> StoredObject:
        return self.save_bytes(relative_path, payload.encode("utf-8"))

    def resolve(self, relative_path: str) -> Path:
        return (self.root / relative_path).resolve()


class S3MirrorStorage(LocalArtifactStorage):
    def __init__(self, root: Path | None = None):
        super().__init__(root=root)
        self.enabled = bool(settings.s3_bucket and settings.aws_access_key_id and settings.aws_secret_access_key)
        self.client = None
        if self.enabled:
            self.client = boto3.client(
                "s3",
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )

    def save_bytes(self, relative_path: str, payload: bytes) -> StoredObject:
        stored = super().save_bytes(relative_path, payload)
        mirror_url = None
        if self.enabled and self.client:
            self.client.put_object(Bucket=settings.s3_bucket, Key=relative_path, Body=payload)
            mirror_url = f"s3://{settings.s3_bucket}/{relative_path}"
        stored.mirror_url = mirror_url
        return stored


def get_storage() -> LocalArtifactStorage:
    if settings.storage_backend.lower() == "s3":
        return S3MirrorStorage()
    return LocalArtifactStorage()

