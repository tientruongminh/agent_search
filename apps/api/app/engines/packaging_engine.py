from __future__ import annotations

import csv
import json
from pathlib import Path
from uuid import uuid4

from app.schemas.file_result import ArtifactItem, ArtifactManifest, RankedFile
from app.schemas.search_state import SearchState
from app.services.storage import LocalArtifactStorage
from app.services.zip_service import build_zip
from app.utils.filenames import safe_filename


class PackagingEngine:
    def __init__(self, storage: LocalArtifactStorage):
        self.storage = storage

    def run(self, state: SearchState) -> ArtifactManifest:
        job_id = state.job_id
        output_dir = f"jobs/{job_id}"
        artifacts: list[ArtifactItem] = []
        package_files: list[tuple[str, str]] = []

        for ranked in state.ranked_files:
            local_path = Path(ranked.local_path)
            relative_path = str(Path(output_dir) / "downloads" / local_path.name)
            if Path(ranked.local_path).exists() and str(local_path).startswith(str(self.storage.root)):
                relative_path = str(local_path.relative_to(self.storage.root))
            artifact_id = f"art_{uuid4().hex}"
            artifact = ArtifactItem(
                id=artifact_id,
                name=local_path.name,
                kind="download",
                relative_path=relative_path,
                download_url=f"/jobs/{job_id}/artifacts/{artifact_id}",
            )
            artifacts.append(artifact)
            package_files.append((local_path, f"downloads/{local_path.name}"))

        csv_relative = self._write_results_csv(job_id, state.ranked_files)
        summary_relative = self._write_summary(job_id, state)
        top_results_relative = self._write_top_results(job_id, state.ranked_files)
        why_relative = self._write_json(
            job_id,
            "package/why_selected.json",
            {result.id: result.why_selected for result in state.ranked_files},
        )
        report_relative = self._write_json(
            job_id,
            "package/job_report.json",
            {
                "job_id": state.job_id,
                "fallback_mode": state.fallback_mode,
                "reflection_count": state.reflection_count,
                "verified_files": len(state.verified_files),
                "ranked_files": len(state.ranked_files),
            },
        )

        metadata_paths = [
            ("results.csv", csv_relative),
            ("summary.md", summary_relative),
            ("top_results.md", top_results_relative),
            ("why_selected.json", why_relative),
            ("job_report.json", report_relative),
        ]
        for name, relative_path in metadata_paths:
            artifact_id = f"art_{uuid4().hex}"
            artifacts.append(
                ArtifactItem(
                    id=artifact_id,
                    name=name,
                    kind="metadata",
                    relative_path=relative_path,
                    download_url=f"/jobs/{job_id}/artifacts/{artifact_id}",
                )
            )
            package_files.append((self.storage.resolve(relative_path), f"package/{name}"))

        manifest_relative = self._write_json(
            job_id,
            "package/manifest.json",
            {
                "job_id": job_id,
                "artifacts": [artifact.model_dump() for artifact in artifacts],
            },
        )
        manifest_id = f"art_{uuid4().hex}"
        manifest_artifact = ArtifactItem(
            id=manifest_id,
            name="manifest.json",
            kind="metadata",
            relative_path=manifest_relative,
            download_url=f"/jobs/{job_id}/artifacts/{manifest_id}",
        )
        artifacts.append(manifest_artifact)
        package_files.append((self.storage.resolve(manifest_relative), "package/manifest.json"))

        bundle_relative = f"jobs/{job_id}/bundle.zip"
        build_zip(self.storage.resolve(bundle_relative), package_files)
        bundle_id = f"art_{uuid4().hex}"
        bundle_artifact = ArtifactItem(
            id=bundle_id,
            name="bundle.zip",
            kind="bundle",
            relative_path=bundle_relative,
            download_url=f"/jobs/{job_id}/artifacts/{bundle_id}",
        )
        artifacts.append(bundle_artifact)

        manifest = ArtifactManifest(job_id=job_id, artifacts=artifacts, bundle_url=bundle_artifact.download_url, output_dir=output_dir)
        self._write_json(
            job_id,
            "package/manifest.json",
            {
                "job_id": job_id,
                "bundle_url": bundle_artifact.download_url,
                "artifacts": [artifact.model_dump() for artifact in artifacts],
            },
        )
        return manifest

    def _write_results_csv(self, job_id: str, ranked_files: list[RankedFile]) -> str:
        relative_path = f"jobs/{job_id}/package/results.csv"
        path = self.storage.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["id", "title", "final_score", "topic_score", "institution_score", "file_type", "download_url"],
            )
            writer.writeheader()
            for row in ranked_files:
                writer.writerow(
                    {
                        "id": row.id,
                        "title": row.title,
                        "final_score": row.final_score,
                        "topic_score": row.topic_score,
                        "institution_score": row.institution_score,
                        "file_type": row.file_type,
                        "download_url": row.download_url,
                    }
                )
        return relative_path

    def _write_summary(self, job_id: str, state: SearchState) -> str:
        top_line = state.ranked_files[0].title if state.ranked_files else "No verified files"
        content = "\n".join(
            [
                f"# Search Summary for {state.job_id}",
                "",
                f"- Request: {state.raw_request}",
                f"- Fallback mode: {state.fallback_mode or 'none'}",
                f"- Reflection count: {state.reflection_count}",
                f"- Verified files: {len(state.verified_files)}",
                f"- Top result: {top_line}",
            ]
        )
        return self._write_text(job_id, "package/summary.md", content)

    def _write_top_results(self, job_id: str, ranked_files: list[RankedFile]) -> str:
        lines = ["# Top Results", ""]
        for result in ranked_files[:10]:
            lines.append(f"## {result.title}")
            lines.append(f"- Score: {result.final_score}")
            lines.append(f"- Source: {result.source_domain or 'unknown'}")
            lines.append(f"- Download: {result.download_url}")
            lines.append("")
        return self._write_text(job_id, "package/top_results.md", "\n".join(lines))

    def _write_json(self, job_id: str, relative_suffix: str, payload: dict) -> str:
        return self._write_text(job_id, relative_suffix, json.dumps(payload, ensure_ascii=False, indent=2))

    def _write_text(self, job_id: str, relative_suffix: str, payload: str) -> str:
        relative_path = f"jobs/{job_id}/{relative_suffix}"
        stored = self.storage.save_text(relative_path, payload)
        return stored.relative_path
