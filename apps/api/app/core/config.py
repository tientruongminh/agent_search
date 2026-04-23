from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Agentic Material Search API"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "development"

    database_url: str = "sqlite:///./agent_search.db"
    redis_url: str = "redis://localhost:6379/0"
    broker_mode: str = "stub"

    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    openai_base_url: str | None = None
    brave_api_key: str | None = None
    github_token: str | None = None

    storage_backend: str = "local"
    artifact_root: Path = Field(default_factory=lambda: Path.cwd() / ".local" / "artifacts")
    s3_bucket: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "ap-southeast-1"

    request_timeout_seconds: int = 20
    max_file_size_bytes: int = 25 * 1024 * 1024
    redirect_limit: int = 5
    max_runtime_seconds: int = 180
    max_results_per_query: int = 10
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    allowed_mime_types: str = ",".join(
        [
            "application/pdf",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/markdown",
            "text/plain",
            "application/octet-stream",
        ]
    )
    suspicious_domains: str = "bit.ly,tinyurl.com,localhost,127.0.0.1,0.0.0.0"

    @property
    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[4]

    @property
    def docs_root(self) -> Path:
        return self.repo_root / "docs"

    @property
    def ranking_profiles_path(self) -> Path:
        return self.docs_root / "ranking_profiles.json"

    @property
    def source_policy_path(self) -> Path:
        return self.docs_root / "source_policy.json"

    @property
    def allowed_mime_types_set(self) -> set[str]:
        return {mime.strip() for mime in self.allowed_mime_types.split(",") if mime.strip()}

    @property
    def suspicious_domain_set(self) -> set[str]:
        return {domain.strip().lower() for domain in self.suspicious_domains.split(",") if domain.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
