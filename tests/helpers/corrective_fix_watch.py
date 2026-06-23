"""CA11 corrective fix watch (read-side only).

Detects newly reviewed CA1-qualifying fixes not present in the frozen CA1 cohort
and assesses readiness for post-baseline locality comparison. Does not modify
baselines, cohorts, or integrate trends, recurrence, or forecasting.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from tests.helpers.corrective_change_locality_cohort import (
    DEFAULT_COHORT_CSV_PATH as CA1_COHORT_CSV_PATH,
    load_cohort,
)
from tests.helpers.corrective_fix_absence_report import (
    DEFAULT_BASELINE_JSON_PATH,
    load_baseline_summary,
)
from tests.helpers.post_baseline_corrective_cohort import (
    DEFAULT_REVIEW_QUEUE_PATH,
    ReviewQueueRow,
    load_review_queue,
)

DEFAULT_CA10_JSON_PATH = "artifacts/ca10_corrective_prevention_effectiveness_report.json"
DEFAULT_MD_OUTPUT_PATH = "artifacts/ca11_corrective_fix_watch_report.md"
DEFAULT_JSON_OUTPUT_PATH = "artifacts/ca11_corrective_fix_watch_report.json"
REPORT_SCHEMA_VERSION = 1
PRIMARY_METRIC = "corrective_fix_emergence_rate"

ReadinessState = Literal["no_new_fixes", "insufficient_sample", "comparison_ready"]


@dataclass(frozen=True)
class QualifyingFixDetection:
    commit_hash: str
    confidence: str
    defect_statement: str
    repair_family: str
    notes: str


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else Path(__file__).resolve().parents[2]


def load_ca1_cohort_commit_hashes(
    csv_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> set[str]:
    """Return all commit hashes present in the frozen CA1 cohort authority CSV."""
    target = Path(csv_path or CA1_COHORT_CSV_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    rows = load_cohort(target)
    return {row.commit_hash for row in rows if row.commit_hash}


def detect_new_qualifying_fixes(
    review_queue: Sequence[ReviewQueueRow],
    ca1_commit_hashes: set[str],
) -> list[QualifyingFixDetection]:
    """Return reviewed qualifying fixes whose commits are not already in CA1."""
    detected: list[QualifyingFixDetection] = []
    for row in review_queue:
        if not row.reviewed or row.qualifies is not True:
            continue
        if row.commit_hash in ca1_commit_hashes:
            continue
        detected.append(
            QualifyingFixDetection(
                commit_hash=row.commit_hash,
                confidence=row.confidence,
                defect_statement=row.defect_statement,
                repair_family=row.repair_family,
                notes=row.notes,
            )
        )
    return detected


def count_qualifying_fixes_pending(review_queue: Sequence[ReviewQueueRow]) -> int:
    """Count queue rows awaiting review completion or qualification decision."""
    pending = 0
    for row in review_queue:
        if not row.reviewed or row.qualifies is None:
            pending += 1
    return pending


def compute_corrective_fix_emergence_rate(
    new_qualifying_fixes: int,
    reviewed_candidates: int,
) -> dict[str, Any]:
    rate = round(new_qualifying_fixes / reviewed_candidates, 4) if reviewed_candidates else 0.0
    return {
        "primary_metric": PRIMARY_METRIC,
        "new_qualifying_fixes": new_qualifying_fixes,
        "reviewed_candidates": reviewed_candidates,
        "corrective_fix_emergence_rate": rate,
    }


def assess_cohort_readiness(new_qualifying_fixes: int) -> dict[str, Any]:
    if new_qualifying_fixes == 0:
        state: ReadinessState = "no_new_fixes"
        assessment = (
            "No new CA1-qualifying fixes detected outside the frozen CA1 cohort; "
            "CA12 post-baseline comparison is not yet justified."
        )
    elif new_qualifying_fixes <= 4:
        state = "insufficient_sample"
        assessment = (
            f"{new_qualifying_fixes} new qualifying fix(es) detected; "
            "sample size is below the five-fix threshold required for CA12 comparison readiness."
        )
    else:
        state = "comparison_ready"
        assessment = (
            f"{new_qualifying_fixes} new qualifying fixes detected; "
            "enough post-baseline evidence exists to justify CA12 locality comparison against CA4."
        )
    return {
        "state": state,
        "new_qualifying_fixes": new_qualifying_fixes,
        "comparison_ready_threshold": 5,
        "assessment": assessment,
        "ready_for_ca12": state == "comparison_ready",
    }


def load_ca10_report(
    json_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    target = Path(json_path or DEFAULT_CA10_JSON_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    return json.loads(target.read_text(encoding="utf-8"))


def build_corrective_fix_watch_report(
    *,
    review_queue: Sequence[ReviewQueueRow],
    ca1_commit_hashes: set[str],
    baseline: Mapping[str, Any],
    ca10_report: Mapping[str, Any],
) -> dict[str, Any]:
    detected = detect_new_qualifying_fixes(review_queue, ca1_commit_hashes)
    pending = count_qualifying_fixes_pending(review_queue)
    reviewed_candidates = sum(1 for row in review_queue if row.reviewed)
    emergence = compute_corrective_fix_emergence_rate(len(detected), reviewed_candidates)
    readiness = assess_cohort_readiness(len(detected))

    suppressed_duplicates = [
        row.commit_hash
        for row in review_queue
        if row.reviewed and row.qualifies is True and row.commit_hash in ca1_commit_hashes
    ]

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "primary_metric": PRIMARY_METRIC,
        "sources": {
            "baseline_json": DEFAULT_BASELINE_JSON_PATH,
            "review_queue_csv": DEFAULT_REVIEW_QUEUE_PATH,
            "ca1_cohort_csv": CA1_COHORT_CSV_PATH,
            "ca10_report_json": DEFAULT_CA10_JSON_PATH,
        },
        "watch_summary": {
            "qualifying_fixes_detected": len(detected),
            "qualifying_fixes_pending": pending,
            "total_reviewed_candidates": reviewed_candidates,
            "current_emergence_rate": emergence["corrective_fix_emergence_rate"],
        },
        "emergence_analysis": emergence,
        "cohort_readiness": readiness,
        "qualifying_fixes_detected": [asdict(item) for item in detected],
        "duplicate_suppression": {
            "ca1_cohort_hash_count": len(ca1_commit_hashes),
            "suppressed_qualifying_hashes": suppressed_duplicates,
        },
        "baseline_context": {
            "baseline_end_date": (baseline.get("cohort_boundaries") or {}).get("end_date"),
            "baseline_cohort_size": baseline.get("cohort_size"),
            "baseline_primary_metric": baseline.get("primary_metric"),
        },
        "prevention_context": {
            "preventive_absorption_ratio": ca10_report.get("preventive_absorption_ratio_analysis", {}).get(
                "preventive_absorption_ratio"
            ),
            "ca10_conclusion": ca10_report.get("conclusion"),
        },
    }


def _metric_line(label: str, value: Any) -> str:
    return f"- **{label}:** {value}"


def render_corrective_fix_watch_report_md(report: Mapping[str, Any]) -> str:
    summary = report["watch_summary"]
    emergence = report["emergence_analysis"]
    readiness = report["cohort_readiness"]
    detected = report["qualifying_fixes_detected"]
    baseline = report["baseline_context"]

    lines = [
        "# CA11 Corrective Fix Watch Report",
        "",
        "> Repository-native watch for new CA1-qualifying corrective fixes and CA12 comparison readiness.",
        "",
        f"_Primary metric: **{report['primary_metric']}** (`new_qualifying_fixes / reviewed_candidates`)._",
        "",
        "## Watch Summary",
        "",
        _metric_line("Qualifying fixes detected", summary["qualifying_fixes_detected"]),
        _metric_line("Qualifying fixes pending", summary["qualifying_fixes_pending"]),
        _metric_line("Total reviewed candidates", summary["total_reviewed_candidates"]),
        _metric_line("Current emergence rate", summary["current_emergence_rate"]),
        "",
        "## Emergence Analysis",
        "",
        _metric_line("New qualifying fixes", emergence["new_qualifying_fixes"]),
        _metric_line("Reviewed candidates", emergence["reviewed_candidates"]),
        _metric_line("Corrective fix emergence rate", emergence["corrective_fix_emergence_rate"]),
        "",
        "## Cohort Readiness Assessment",
        "",
        _metric_line("Readiness state", readiness["state"]),
        _metric_line("Ready for CA12", readiness["ready_for_ca12"]),
        _metric_line("Comparison-ready threshold", readiness["comparison_ready_threshold"]),
        _metric_line("Assessment", readiness["assessment"]),
        "",
        "## Detected Qualifying Fixes",
        "",
    ]
    if detected:
        lines.extend(
            [
                "| Commit | Confidence | Repair family | Defect statement |",
                "|---|---|---|---|",
            ]
        )
        for row in detected:
            defect = str(row.get("defect_statement") or "").replace("|", "\\|")
            family = str(row.get("repair_family") or "").replace("|", "\\|")
            lines.append(
                f"| `{row['commit_hash'][:7]}` | {row.get('confidence') or ''} | {family} | {defect} |"
            )
    else:
        lines.append("_No new qualifying fixes detected outside the frozen CA1 cohort._")

    lines.extend(
        [
            "",
            "## Baseline Context",
            "",
            _metric_line("CA4 baseline end date", baseline.get("baseline_end_date")),
            _metric_line("CA4 baseline cohort size", baseline.get("baseline_cohort_size")),
            _metric_line("Baseline primary metric", baseline.get("baseline_primary_metric")),
            "",
            "## Duplicate Suppression",
            "",
            _metric_line(
                "CA1 cohort hashes tracked",
                report["duplicate_suppression"]["ca1_cohort_hash_count"],
            ),
            _metric_line(
                "Suppressed qualifying duplicates",
                len(report["duplicate_suppression"]["suppressed_qualifying_hashes"]),
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_corrective_fix_watch_report(
    md_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
    *,
    review_queue_path: str | Path | None = None,
    ca1_cohort_csv_path: str | Path | None = None,
    baseline_json_path: str | Path | None = None,
    ca10_json_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    root = _repo_root(repo_root)
    review_queue = load_review_queue(review_queue_path)
    ca1_hashes = load_ca1_cohort_commit_hashes(ca1_cohort_csv_path, repo_root=root)
    baseline = load_baseline_summary(baseline_json_path, repo_root=root)
    ca10_report = load_ca10_report(ca10_json_path, repo_root=root)

    report = build_corrective_fix_watch_report(
        review_queue=review_queue,
        ca1_commit_hashes=ca1_hashes,
        baseline=baseline,
        ca10_report=ca10_report,
    )
    markdown = render_corrective_fix_watch_report_md(report)

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
