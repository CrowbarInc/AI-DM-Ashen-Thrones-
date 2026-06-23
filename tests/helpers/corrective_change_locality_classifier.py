"""CA2 corrective-change locality path classifier (read-side only).

Mutually exclusive, ordered path buckets per CA discovery section 5.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

PATH_BUCKETS: tuple[str, ...] = (
    "production_runtime_source",
    "tests",
    "docs_reports",
    "scripts_tools",
    "fixtures_data",
    "generated_artifacts",
    "unclassified",
)

GENERATED_ARTIFACT_PREFIXES: tuple[str, ...] = (
    "artifacts/",
    "codex_pytest_tmp",
    ".pytest_cache/",
    "htmlcov/",
    ".coverage",
    "coverage/",
)

DOCS_REPORT_PREFIXES: tuple[str, ...] = (
    "docs/",
    "audits/",
)

SCRIPTS_TOOLS_PREFIXES: tuple[str, ...] = (
    "tools/",
    "scripts/",
    ".github/",
)

FIXTURE_DATA_PREFIXES: tuple[str, ...] = (
    "data/",
    "fixtures/",
)

PRODUCTION_RUNTIME_PREFIXES: tuple[str, ...] = (
    "game/",
    "static/",
)

SCRIPTS_TOOLS_ROOT_FILES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "pytest.ini",
        "setup.cfg",
        "setup.py",
        "requirements.txt",
        "requirements-dev.txt",
        "Makefile",
        "tox.ini",
        "mypy.ini",
        "ruff.toml",
        ".pre-commit-config.yaml",
    }
)

DOCS_REPORT_ROOT_SUFFIXES: tuple[str, ...] = (".md", ".txt")


def normalize_path(path: str) -> str:
    """Normalize a repository-relative path for classification."""
    normalized = path.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _is_generated_artifact(normalized: str) -> bool:
    if not normalized:
        return False
    for prefix in GENERATED_ARTIFACT_PREFIXES:
        if normalized.startswith(prefix) or f"/{prefix}" in normalized:
            return True
        if prefix.endswith("/") is False and normalized.split("/", 1)[0].startswith(prefix):
            return True
    name = Path(normalized).name
    if name == ".coverage" or name.startswith(".coverage."):
        return True
    return False


def _is_test_path(normalized: str) -> bool:
    if normalized.startswith("tests/"):
        return True
    name = Path(normalized).name
    return name.startswith("test_") or name.endswith("_test.py")


def _is_docs_report_path(normalized: str) -> bool:
    if any(normalized.startswith(prefix) for prefix in DOCS_REPORT_PREFIXES):
        return True
    name = Path(normalized).name
    if "/" not in normalized:
        return any(name.endswith(suffix) for suffix in DOCS_REPORT_ROOT_SUFFIXES)
    return normalized.endswith(".md") or normalized.endswith(".txt")


def _is_scripts_tools_path(normalized: str) -> bool:
    if any(normalized.startswith(prefix) for prefix in SCRIPTS_TOOLS_PREFIXES):
        return True
    name = Path(normalized).name
    return name in SCRIPTS_TOOLS_ROOT_FILES


def _is_fixture_data_path(normalized: str) -> bool:
    return any(normalized.startswith(prefix) for prefix in FIXTURE_DATA_PREFIXES)


def _is_production_runtime_path(normalized: str) -> bool:
    return any(normalized.startswith(prefix) for prefix in PRODUCTION_RUNTIME_PREFIXES)


def classify_path(path: str) -> str:
    """Classify one changed path into exactly one CA path bucket."""
    normalized = normalize_path(path)
    if not normalized:
        return "unclassified"

    # Ordered precedence: generated before tests so codex_pytest_tmp never lands in tests.
    if _is_generated_artifact(normalized):
        return "generated_artifacts"
    if _is_test_path(normalized):
        return "tests"
    if _is_docs_report_path(normalized):
        return "docs_reports"
    if _is_scripts_tools_path(normalized):
        return "scripts_tools"
    if _is_fixture_data_path(normalized):
        return "fixtures_data"
    if _is_production_runtime_path(normalized):
        return "production_runtime_source"
    return "unclassified"


@dataclass(frozen=True)
class PathClassificationSummary:
    path_buckets: tuple[tuple[str, str], ...]
    bucket_counts: Mapping[str, int]

    @property
    def total_paths(self) -> int:
        return len(self.path_buckets)

    def count_for(self, bucket: str) -> int:
        return int(self.bucket_counts.get(bucket, 0))


def classify_paths(paths: Sequence[str]) -> PathClassificationSummary:
    """Classify changed paths and return per-path buckets plus aggregate counts."""
    assignments: list[tuple[str, str]] = []
    counts: Counter[str] = Counter()
    for path in paths:
        bucket = classify_path(path)
        if bucket not in PATH_BUCKETS:
            raise ValueError(f"unknown bucket {bucket!r} for path {path!r}")
        assignments.append((normalize_path(path), bucket))
        counts[bucket] += 1
    ordered_counts = {bucket: int(counts.get(bucket, 0)) for bucket in PATH_BUCKETS}
    return PathClassificationSummary(
        path_buckets=tuple(assignments),
        bucket_counts=ordered_counts,
    )


def validate_classification(summary: PathClassificationSummary) -> list[str]:
    """Return validation errors for a classification summary."""
    errors: list[str] = []
    if summary.total_paths == 0:
        return errors

    seen_paths: set[str] = set()
    for path, bucket in summary.path_buckets:
        if path in seen_paths:
            errors.append(f"duplicate bucket assignment for path: {path}")
        seen_paths.add(path)
        if bucket not in PATH_BUCKETS:
            errors.append(f"unknown bucket {bucket!r} for path {path!r}")

    bucket_sum = sum(summary.bucket_counts.values())
    if bucket_sum != summary.total_paths:
        errors.append(
            f"bucket count mismatch: sum({bucket_sum}) != total changed paths ({summary.total_paths})"
        )
    return errors


BUCKET_DEFINITIONS: dict[str, str] = {
    "production_runtime_source": (
        "Executable product code under `game/` and `static/`, plus registered runtime packages."
    ),
    "tests": "Authored tests and helpers under `tests/`; excludes `codex_pytest_tmp*`.",
    "docs_reports": "Human-authored docs under `docs/`, `audits/`, and report markdown.",
    "scripts_tools": "Tooling under `tools/`, `scripts/`, `.github/`, and build/CI/config files.",
    "fixtures_data": "Committed fixtures, snapshots, and scenario inputs under `data/` and `fixtures/`.",
    "generated_artifacts": (
        "Generated output under `artifacts/`, `codex_pytest_tmp*`, caches, and coverage files."
    ),
    "unclassified": "Any changed path that does not match a higher-precedence bucket.",
}

BUCKET_EXAMPLE_PATHS: dict[str, tuple[str, ...]] = {
    "production_runtime_source": ("game/api.py", "static/app.js"),
    "tests": ("tests/test_start_campaign_api.py", "tests/helpers/golden_replay.py"),
    "docs_reports": ("docs/reports/openai_api_key_lazy_config_fix_20260520.md", "audits/cycle_f.md"),
    "scripts_tools": ("tools/bug_fix_locality_report.py", ".github/workflows/convergence-checks.yml"),
    "fixtures_data": ("data/session.json", "data/scenes/frontier_gate.json"),
    "generated_artifacts": (
        "artifacts/bug_fix_locality_report.md",
        "codex_pytest_tmp19/test_start_campaign_emits_open0/data/session.json",
    ),
    "unclassified": ("unknown.xyz",),
}
