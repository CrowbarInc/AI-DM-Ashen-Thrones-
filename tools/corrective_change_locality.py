"""CA2 corrective-change locality Git collector and path accounting engine.

Converts reviewed cohort entries into reproducible per-commit locality counts.
Read-side only: no trend analysis, medians, recurrence integration, or runtime changes.
"""
from __future__ import annotations

import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.corrective_change_locality_classifier import (  # noqa: E402
    BUCKET_DEFINITIONS,
    BUCKET_EXAMPLE_PATHS,
    PATH_BUCKETS,
    PathClassificationSummary,
    classify_paths,
    normalize_path,
    validate_classification,
)
from tests.helpers.corrective_change_locality_cohort import (  # noqa: E402
    DEFAULT_COHORT_CSV_PATH,
    CorrectiveChangeLocalityCohortRow,
    load_cohort,
    validate_cohort,
)

DEFAULT_REPORT_PATH = "artifacts/ca2_path_classification_report.md"

CA1_BUCKET_TO_AUTHORITY_FIELD: dict[str, str] = {
    "production_runtime_source": "production_files_touched",
    "tests": "test_files_touched",
    "docs_reports": "docs_files_touched",
    "scripts_tools": "tooling_files_touched",
    "fixtures_data": "fixture_files_touched",
    "generated_artifacts": "generated_files_touched",
}


@dataclass(frozen=True)
class CommitLocalityMeasurement:
    cohort_id: str
    commit_hash: str
    qualifies: bool
    changed_paths: tuple[str, ...]
    classification: PathClassificationSummary

    @property
    def bucket_counts(self) -> Mapping[str, int]:
        return self.classification.bucket_counts

    @property
    def total_changed_paths(self) -> int:
        return self.classification.total_paths

    @property
    def effective_files_touched(self) -> int:
        return self.total_changed_paths - self.bucket_counts.get("generated_artifacts", 0)


@dataclass
class CohortLocalityCollection:
    measurements: list[CommitLocalityMeasurement] = field(default_factory=list)

    @property
    def cohort_wide_bucket_totals(self) -> dict[str, int]:
        totals: Counter[str] = Counter()
        for measurement in self.measurements:
            for bucket, count in measurement.bucket_counts.items():
                totals[bucket] += count
        return {bucket: int(totals.get(bucket, 0)) for bucket in PATH_BUCKETS}


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else ROOT


def inspect_commit_hash(commit_hash: str, *, repo_root: Path | None = None) -> bool:
    """Return True when the commit object exists in the local Git repository."""
    text = str(commit_hash or "").strip()
    if not text:
        return False
    root = _repo_root(repo_root)
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{text}^{{commit}}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def collect_changed_paths(commit_hash: str, *, repo_root: Path | None = None) -> list[str]:
    """Collect changed paths for one commit via git diff-tree."""
    text = str(commit_hash or "").strip()
    if not text:
        raise ValueError("commit hash is missing")
    root = _repo_root(repo_root)
    if not inspect_commit_hash(text, repo_root=root):
        raise ValueError(f"commit hash not found: {text}")

    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", text],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise ValueError(f"git diff-tree failed for {text}: {stderr or result.returncode}")

    paths = [normalize_path(line) for line in result.stdout.splitlines() if line.strip()]
    return paths


def compute_locality_counts(
    paths: Sequence[str],
) -> PathClassificationSummary:
    """Classify changed paths and compute bucket counts."""
    summary = classify_paths(paths)
    errors = validate_classification(summary)
    if errors:
        raise ValueError("classification validation failed:\n" + "\n".join(f"- {err}" for err in errors))
    return summary


def measure_commit_locality(
    row: CorrectiveChangeLocalityCohortRow,
    *,
    repo_root: Path | None = None,
) -> CommitLocalityMeasurement:
    """Collect and classify changed paths for one cohort row."""
    paths = collect_changed_paths(row.commit_hash, repo_root=repo_root)
    classification = compute_locality_counts(paths)
    return CommitLocalityMeasurement(
        cohort_id=row.cohort_id,
        commit_hash=row.commit_hash,
        qualifies=row.qualifies,
        changed_paths=tuple(paths),
        classification=classification,
    )


def validate_measurement_against_authority(
    row: CorrectiveChangeLocalityCohortRow,
    measurement: CommitLocalityMeasurement,
) -> list[str]:
    """Compare Git-derived counts with CA1 authority fields."""
    errors: list[str] = []
    classification_errors = validate_classification(measurement.classification)
    errors.extend(f"{row.cohort_id}: {err}" for err in classification_errors)

    if measurement.total_changed_paths != row.total_files_touched:
        errors.append(
            f"{row.cohort_id}: total changed paths ({measurement.total_changed_paths}) "
            f"!= authority total_files_touched ({row.total_files_touched})"
        )

    for bucket, field_name in CA1_BUCKET_TO_AUTHORITY_FIELD.items():
        actual = measurement.bucket_counts.get(bucket, 0)
        expected = getattr(row, field_name)
        if actual != expected:
            errors.append(
                f"{row.cohort_id}: {bucket} count ({actual}) != authority {field_name} ({expected})"
            )

    unclassified = measurement.bucket_counts.get("unclassified", 0)
    if unclassified:
        errors.append(f"{row.cohort_id}: unclassified path count is {unclassified}")

    expected_effective = measurement.total_changed_paths - measurement.bucket_counts.get(
        "generated_artifacts", 0
    )
    if expected_effective != row.effective_files_touched:
        errors.append(
            f"{row.cohort_id}: effective_files_touched ({row.effective_files_touched}) "
            f"!= total - generated ({expected_effective})"
        )
    return errors


def collect_cohort_locality(
    rows: Sequence[CorrectiveChangeLocalityCohortRow],
    *,
    repo_root: Path | None = None,
) -> CohortLocalityCollection:
    """Collect locality measurements for all cohort rows."""
    collection = CohortLocalityCollection()
    for row in rows:
        if not row.commit_hash:
            raise ValueError(f"{row.cohort_id}: commit hash is missing")
        collection.measurements.append(measure_commit_locality(row, repo_root=repo_root))
    return collection


def validate_cohort_locality_collection(
    rows: Sequence[CorrectiveChangeLocalityCohortRow],
    collection: CohortLocalityCollection,
) -> list[str]:
    """Validate a cohort collection against authority rows and accounting rules."""
    errors: list[str] = []
    if len(rows) != len(collection.measurements):
        errors.append("measurement count does not match cohort row count")
        return errors

    row_by_id = {row.cohort_id: row for row in rows}
    for measurement in collection.measurements:
        row = row_by_id.get(measurement.cohort_id)
        if row is None:
            errors.append(f"unexpected measurement for unknown cohort_id {measurement.cohort_id!r}")
            continue
        errors.extend(validate_measurement_against_authority(row, measurement))
    return errors


def load_reviewed_cohort(csv_path: str | Path | None = None) -> list[CorrectiveChangeLocalityCohortRow]:
    """Load and validate the reviewed CA cohort authority CSV."""
    errors = validate_cohort(csv_path)
    if errors:
        raise ValueError("cohort validation failed:\n" + "\n".join(f"- {err}" for err in errors))
    return load_cohort(csv_path)


def render_ca2_path_classification_report_md(collection: CohortLocalityCollection) -> str:
    """Render CA2 path classification report markdown."""
    totals = collection.cohort_wide_bucket_totals
    lines = [
        "# CA2 Path Classification Report",
        "",
        "> CA2 Git collection and path-bucket accounting for the reviewed corrective cohort.",
        "",
        "## Bucket definitions",
        "",
    ]
    for bucket in PATH_BUCKETS:
        lines.append(f"### `{bucket}`")
        lines.append("")
        lines.append(BUCKET_DEFINITIONS[bucket])
        lines.append("")
        examples = BUCKET_EXAMPLE_PATHS.get(bucket, ())
        if examples:
            lines.append("Example paths:")
            for example in examples:
                lines.append(f"- `{example}`")
            lines.append("")

    lines.extend(["## Cohort-wide bucket totals", ""])
    for bucket in PATH_BUCKETS:
        lines.append(f"- **{bucket}**: {totals.get(bucket, 0)}")
    lines.append("")
    lines.append(f"- **Total changed paths:** {sum(totals.values())}")
    lines.append(f"- **Unclassified paths:** {totals.get('unclassified', 0)}")
    lines.append("")

    lines.extend(["## Per-commit accounting", ""])
    for measurement in collection.measurements:
        counts = measurement.bucket_counts
        lines.append(
            f"- **{measurement.cohort_id}** `{measurement.commit_hash[:7]}` — "
            f"total={measurement.total_changed_paths}, "
            f"production={counts.get('production_runtime_source', 0)}, "
            f"tests={counts.get('tests', 0)}, "
            f"fixtures={counts.get('fixtures_data', 0)}, "
            f"generated={counts.get('generated_artifacts', 0)}, "
            f"unclassified={counts.get('unclassified', 0)}"
        )
    lines.append("")
    return "\n".join(lines)


def write_ca2_path_classification_report(
    output_path: str | Path | None = None,
    csv_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> tuple[CohortLocalityCollection, str]:
    """Collect cohort locality measurements and write the CA2 report."""
    rows = load_reviewed_cohort(csv_path)
    collection = collect_cohort_locality(rows, repo_root=repo_root)
    errors = validate_cohort_locality_collection(rows, collection)
    if errors:
        raise ValueError("cohort locality validation failed:\n" + "\n".join(f"- {err}" for err in errors))

    markdown = render_ca2_path_classification_report_md(collection)
    target = Path(output_path or DEFAULT_REPORT_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return collection, markdown


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect CA corrective-change locality path classifications.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / DEFAULT_COHORT_CSV_PATH,
        help=f"Reviewed cohort CSV (default: {DEFAULT_COHORT_CSV_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / DEFAULT_REPORT_PATH,
        help=f"Markdown output path (default: {DEFAULT_REPORT_PATH})",
    )
    args = parser.parse_args()

    _collection, markdown = write_ca2_path_classification_report(
        args.output,
        csv_path=args.csv,
        repo_root=ROOT,
    )
    print(f"Wrote {args.output} ({len(markdown.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
