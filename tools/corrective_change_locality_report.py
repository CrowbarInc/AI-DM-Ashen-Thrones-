"""CA3 corrective-change locality report (read-side measurement only).

Produces the first repository-authoritative Corrective Change Locality report
from CA1 cohort authority and CA2 Git path accounting. No recurrence joins,
trend windows, or predictive analytics.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.corrective_change_locality_cohort import (  # noqa: E402
    DEFAULT_COHORT_CSV_PATH,
    CorrectiveChangeLocalityCohortRow,
    qualifying_rows,
)
from tools.corrective_change_locality import (  # noqa: E402
    collect_cohort_locality,
    load_reviewed_cohort,
    validate_cohort_locality_collection,
)

DEFAULT_MD_OUTPUT_PATH = "artifacts/ca3_corrective_locality_report.md"
DEFAULT_JSON_OUTPUT_PATH = "artifacts/ca3_corrective_locality_report.json"
REPORT_SCHEMA_VERSION = 1
PRIMARY_METRIC = "files_touched_per_fix"


@dataclass(frozen=True)
class QualifyingFixMeasurement:
    cohort_id: str
    commit_hash: str
    title: str
    confidence: str
    repair_family: str
    total_files_touched: int
    production_files_touched: int
    test_files_touched: int
    generated_files_touched: int
    effective_files_touched: int

    @classmethod
    def from_authority_row(cls, row: CorrectiveChangeLocalityCohortRow) -> QualifyingFixMeasurement:
        return cls(
            cohort_id=row.cohort_id,
            commit_hash=row.commit_hash,
            title=row.title,
            confidence=row.confidence,
            repair_family=row.repair_family,
            total_files_touched=row.total_files_touched,
            production_files_touched=row.production_files_touched,
            test_files_touched=row.test_files_touched,
            generated_files_touched=row.generated_files_touched,
            effective_files_touched=row.effective_files_touched,
        )


def _percentile(values: Sequence[int | float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (pct / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * weight, 2)


def _round_mean(values: Sequence[int | float]) -> float:
    if not values:
        return 0.0
    return round(float(mean(values)), 2)


def qualifying_fix_measurements(
    rows: Sequence[CorrectiveChangeLocalityCohortRow],
) -> list[QualifyingFixMeasurement]:
    """Return qualifying fix rows; exclusion controls such as EX-01 are omitted."""
    return [QualifyingFixMeasurement.from_authority_row(row) for row in qualifying_rows(rows)]


def compute_files_touched_per_fix_stats(
    fixes: Sequence[QualifyingFixMeasurement],
) -> dict[str, Any]:
    """Compute primary Files Touched Per Fix distribution."""
    totals = [fix.total_files_touched for fix in fixes]
    if not totals:
        return {
            "cohort_size": 0,
            "median": 0.0,
            "mean": 0.0,
            "minimum": 0,
            "maximum": 0,
            "p75": 0.0,
            "p90": 0.0,
        }
    return {
        "cohort_size": len(totals),
        "median": float(median(totals)),
        "mean": _round_mean(totals),
        "minimum": min(totals),
        "maximum": max(totals),
        "p75": _percentile(totals, 75),
        "p90": _percentile(totals, 90),
    }


def compute_production_locality_stats(
    fixes: Sequence[QualifyingFixMeasurement],
) -> dict[str, Any]:
    values = [fix.production_files_touched for fix in fixes]
    if not values:
        return {
            "median": 0.0,
            "mean": 0.0,
            "minimum": 0,
            "maximum": 0,
        }
    return {
        "median": float(median(values)),
        "mean": _round_mean(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def compute_test_locality_stats(
    fixes: Sequence[QualifyingFixMeasurement],
) -> dict[str, Any]:
    values = [fix.test_files_touched for fix in fixes]
    if not values:
        return {"median": 0.0, "mean": 0.0}
    return {
        "median": float(median(values)),
        "mean": _round_mean(values),
    }


def compute_generated_artifact_distortion(
    fixes: Sequence[QualifyingFixMeasurement],
) -> dict[str, Any]:
    """Report raw vs effective medians and per-commit generated-artifact distortion."""
    raw_totals = [fix.total_files_touched for fix in fixes]
    effective_totals = [fix.effective_files_touched for fix in fixes]
    raw_median = float(median(raw_totals)) if raw_totals else 0.0
    effective_median = float(median(effective_totals)) if effective_totals else 0.0
    if raw_median > 0:
        median_distortion_pct = round((raw_median - effective_median) / raw_median * 100.0, 2)
    else:
        median_distortion_pct = 0.0

    polluted_fixes = [fix for fix in fixes if fix.generated_files_touched > 0]
    cohort_size = len(fixes)
    polluted_fix_pct = round(len(polluted_fixes) / cohort_size * 100.0, 2) if cohort_size else 0.0

    by_commit: list[dict[str, Any]] = []
    for fix in fixes:
        if fix.total_files_touched > 0:
            distortion_pct = round(
                fix.generated_files_touched / fix.total_files_touched * 100.0,
                2,
            )
        else:
            distortion_pct = 0.0
        by_commit.append(
            {
                "cohort_id": fix.cohort_id,
                "commit_hash": fix.commit_hash,
                "total_files_touched": fix.total_files_touched,
                "generated_files_touched": fix.generated_files_touched,
                "effective_files_touched": fix.effective_files_touched,
                "distortion_pct": distortion_pct,
            }
        )

    return {
        "raw_median": raw_median,
        "effective_median": effective_median,
        "median_distortion_pct": median_distortion_pct,
        "polluted_fix_count": len(polluted_fixes),
        "polluted_fix_pct": polluted_fix_pct,
        "by_commit": by_commit,
    }


def compute_repair_family_concentration(
    fixes: Sequence[QualifyingFixMeasurement],
) -> dict[str, Any]:
    counts = Counter(fix.repair_family for fix in fixes if fix.repair_family)
    cohort_size = len(fixes)
    if not counts or cohort_size == 0:
        return {
            "counts": {},
            "percentages": {},
            "largest_repair_family": "",
            "largest_repair_family_count": 0,
            "concentration_ratio": 0.0,
        }

    largest_family, largest_count = counts.most_common(1)[0]
    percentages = {
        family: round(count / cohort_size * 100.0, 2)
        for family, count in sorted(counts.items())
    }
    return {
        "counts": dict(sorted(counts.items())),
        "percentages": percentages,
        "largest_repair_family": largest_family,
        "largest_repair_family_count": largest_count,
        "concentration_ratio": round(largest_count / cohort_size, 4),
    }


def build_cohort_composition(
    rows: Sequence[CorrectiveChangeLocalityCohortRow],
    fixes: Sequence[QualifyingFixMeasurement],
) -> dict[str, Any]:
    qualifying = qualifying_rows(rows)
    exclusions = [row for row in rows if not row.qualifies]
    confidence = Counter(fix.confidence for fix in fixes if fix.confidence)
    dates = sorted(row.date for row in qualifying if row.date)
    return {
        "qualifying_count": len(fixes),
        "exclusion_count": len(exclusions),
        "exclusion_ids": [row.cohort_id for row in exclusions],
        "date_range": {
            "start": dates[0] if dates else "",
            "end": dates[-1] if dates else "",
        },
        "confidence_counts": dict(sorted(confidence.items())),
    }


def build_corrective_locality_report(
    rows: Sequence[CorrectiveChangeLocalityCohortRow],
) -> dict[str, Any]:
    """Build machine-readable CA3 corrective locality report from authority rows."""
    fixes = qualifying_fix_measurements(rows)
    files_touched = compute_files_touched_per_fix_stats(fixes)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "primary_metric": PRIMARY_METRIC,
        "source": DEFAULT_COHORT_CSV_PATH,
        "cohort_composition": build_cohort_composition(rows, fixes),
        "files_touched_per_fix": files_touched,
        "production_locality": compute_production_locality_stats(fixes),
        "test_locality": compute_test_locality_stats(fixes),
        "generated_artifact_distortion": compute_generated_artifact_distortion(fixes),
        "repair_family_concentration": compute_repair_family_concentration(fixes),
        "qualifying_fixes": [asdict(fix) for fix in fixes],
    }


def _metric_line(label: str, value: Any) -> str:
    return f"- **{label}:** {value}"


def render_corrective_locality_report_md(report: Mapping[str, Any]) -> str:
    """Render human-readable CA3 corrective locality report markdown."""
    composition = report["cohort_composition"]
    files_touched = report["files_touched_per_fix"]
    production = report["production_locality"]
    tests = report["test_locality"]
    distortion = report["generated_artifact_distortion"]
    families = report["repair_family_concentration"]
    fixes = report["qualifying_fixes"]

    lines = [
        "# CA3 Corrective Change Locality Report",
        "",
        "> First repository-authoritative measurement of corrective change locality.",
        "",
        f"_Primary metric: **{report['primary_metric']}** — source `{report['source']}`._",
        "",
        "## 1. Executive Summary",
        "",
        "This cohort measures what a genuine corrective fix costs to modify in this repository.",
        "",
        _metric_line("Qualifying fixes", files_touched["cohort_size"]),
        _metric_line("Median files touched per fix (raw)", files_touched["median"]),
        _metric_line("Median files touched per fix (effective)", distortion["effective_median"]),
        _metric_line("Median production files touched", production["median"]),
        _metric_line("Median test files touched", tests["median"]),
        _metric_line(
            "Largest repair family",
            f"{families['largest_repair_family']} ({families['largest_repair_family_count']} fixes)",
        ),
        "",
        "## 2. Cohort Composition",
        "",
        _metric_line("Qualifying fixes", composition["qualifying_count"]),
        _metric_line("Exclusion controls", composition["exclusion_count"]),
        _metric_line(
            "Excluded cohort IDs",
            ", ".join(composition["exclusion_ids"]) if composition["exclusion_ids"] else "none",
        ),
        _metric_line(
            "Date range",
            f"{composition['date_range']['start']} through {composition['date_range']['end']}",
        ),
        "",
        "### Confidence distribution",
        "",
    ]
    for confidence, count in composition["confidence_counts"].items():
        lines.append(f"- **{confidence}:** {count}")
    lines.extend(
        [
            "",
            "## 3. Files Touched Per Fix",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Cohort size | {files_touched['cohort_size']} |",
            f"| Median | {files_touched['median']} |",
            f"| Mean | {files_touched['mean']} |",
            f"| Minimum | {files_touched['minimum']} |",
            f"| Maximum | {files_touched['maximum']} |",
            f"| P75 | {files_touched['p75']} |",
            f"| P90 | {files_touched['p90']} |",
            "",
            "## 4. Production Locality",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Median production files touched | {production['median']} |",
            f"| Mean production files touched | {production['mean']} |",
            f"| Minimum | {production['minimum']} |",
            f"| Maximum | {production['maximum']} |",
            "",
            "## 5. Test Locality",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Median test files touched | {tests['median']} |",
            f"| Mean test files touched | {tests['mean']} |",
            "",
            "## 6. Generated Artifact Distortion",
            "",
            _metric_line("Raw median files touched", distortion["raw_median"]),
            _metric_line("Effective median files touched", distortion["effective_median"]),
            _metric_line("Median distortion percentage", f"{distortion['median_distortion_pct']}%"),
            _metric_line(
                "Fixes with generated-artifact pollution",
                f"{distortion['polluted_fix_count']} ({distortion['polluted_fix_pct']}%)",
            ),
            "",
            "### Distortion by commit",
            "",
            "| Cohort ID | Total | Generated | Effective | Distortion % |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in distortion["by_commit"]:
        lines.append(
            f"| {row['cohort_id']} | {row['total_files_touched']} | "
            f"{row['generated_files_touched']} | {row['effective_files_touched']} | "
            f"{row['distortion_pct']} |"
        )

    lines.extend(
        [
            "",
            "## 7. Repair Family Concentration",
            "",
            _metric_line("Largest repair family", families["largest_repair_family"]),
            _metric_line("Largest family count", families["largest_repair_family_count"]),
            _metric_line("Concentration ratio", families["concentration_ratio"]),
            "",
            "| Repair family | Count | Percentage |",
            "|---|---:|---:|",
        ]
    )
    for family, count in families["counts"].items():
        lines.append(f"| {family} | {count} | {families['percentages'][family]}% |")

    lines.extend(
        [
            "",
            "## 8. Full Cohort Table",
            "",
            "| Cohort ID | Commit | Title | Confidence | Repair family | Total | Production | Tests | Generated | Effective |",
            "|---|---|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for fix in fixes:
        title = str(fix["title"]).replace("|", "\\|")
        lines.append(
            f"| {fix['cohort_id']} | `{fix['commit_hash'][:7]}` | {title} | "
            f"{fix['confidence']} | {fix['repair_family']} | {fix['total_files_touched']} | "
            f"{fix['production_files_touched']} | {fix['test_files_touched']} | "
            f"{fix['generated_files_touched']} | {fix['effective_files_touched']} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_corrective_locality_report(
    md_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
    csv_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
    validate_git: bool = True,
) -> tuple[dict[str, Any], str]:
    """Validate CA2 accounting, build CA3 report, and write markdown/json artifacts."""
    root = repo_root if repo_root is not None else ROOT
    rows = load_reviewed_cohort(csv_path)
    if validate_git:
        collection = collect_cohort_locality(rows, repo_root=root)
        errors = validate_cohort_locality_collection(rows, collection)
        if errors:
            raise ValueError(
                "CA2 cohort locality validation failed:\n" + "\n".join(f"- {err}" for err in errors)
            )

    report = build_corrective_locality_report(rows)
    markdown = render_corrective_locality_report_md(report)

    md_target = Path(md_output_path or DEFAULT_MD_OUTPUT_PATH)
    json_target = Path(json_output_path or DEFAULT_JSON_OUTPUT_PATH)
    if not md_target.is_absolute():
        md_target = root / md_target
    if not json_target.is_absolute():
        json_target = root / json_target
    md_target.parent.mkdir(parents=True, exist_ok=True)
    json_target.parent.mkdir(parents=True, exist_ok=True)
    md_target.write_text(markdown, encoding="utf-8")
    json_target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, markdown


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate CA3 corrective change locality report.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / DEFAULT_COHORT_CSV_PATH,
        help=f"Reviewed cohort CSV (default: {DEFAULT_COHORT_CSV_PATH})",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / DEFAULT_MD_OUTPUT_PATH,
        help=f"Markdown output path (default: {DEFAULT_MD_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / DEFAULT_JSON_OUTPUT_PATH,
        help=f"JSON output path (default: {DEFAULT_JSON_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--skip-git-validation",
        action="store_true",
        help="Build report from authority CSV without CA2 Git validation.",
    )
    args = parser.parse_args()

    _report, markdown = write_corrective_locality_report(
        md_output_path=args.output_md,
        json_output_path=args.output_json,
        csv_path=args.csv,
        repo_root=ROOT,
        validate_git=not args.skip_git_validation,
    )
    print(f"Wrote {args.output_md} ({len(markdown.splitlines())} lines)")
    print(f"Wrote {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
