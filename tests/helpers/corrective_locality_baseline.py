"""CA4 corrective locality baseline lock (read-side validation only).

Loads and validates the frozen CA3 corrective locality baseline for future
cohort comparison. Does not generate new cohorts, trend analysis, or runtime changes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

DEFAULT_BASELINE_JSON_PATH = "docs/baselines/ca_corrective_locality_baseline.json"
DEFAULT_BASELINE_MD_PATH = "docs/baselines/ca_corrective_locality_baseline.md"
DEFAULT_CA3_REPORT_JSON_PATH = "artifacts/ca3_corrective_locality_report.json"
DEFAULT_CA4_LOCK_REPORT_PATH = "artifacts/ca4_baseline_lock_report.md"

BASELINE_VERSION = 1
PRIMARY_METRIC = "files_touched_per_fix"

REQUIRED_BASELINE_FIELDS: tuple[str, ...] = (
    "baseline_version",
    "created_date",
    "comparison_ready",
    "primary_metric",
    "source_cohort",
    "source_report",
    "cohort_boundaries",
    "cohort_size",
    "median_files_touched_raw",
    "median_files_touched_effective",
    "mean_files_touched",
    "p75_files_touched",
    "p90_files_touched",
    "max_files_touched",
    "median_production_files",
    "median_test_files",
    "generated_artifact_distortion",
    "repair_family_distribution",
)

REQUIRED_DISTORTION_FIELDS: tuple[str, ...] = (
    "raw_median",
    "effective_median",
    "median_distortion_pct",
    "polluted_fix_count",
    "polluted_fix_pct",
)

REQUIRED_REPAIR_FAMILY_FIELDS: tuple[str, ...] = (
    "counts",
    "percentages",
    "largest_repair_family",
    "concentration_ratio",
)

# Frozen at CA4 baseline lock (2026-06-22) from CA3 report reproduction.
CA4_FROZEN_BASELINE: dict[str, Any] = {
    "baseline_version": 1,
    "created_date": "2026-06-22",
    "comparison_ready": True,
    "primary_metric": PRIMARY_METRIC,
    "source_cohort": "docs/audits/CA_corrective_change_locality_cohort.csv",
    "source_report": "artifacts/ca3_corrective_locality_report.json",
    "cohort_boundaries": {
        "start_date": "2026-03-21",
        "end_date": "2026-05-20",
    },
    "cohort_size": 10,
    "median_files_touched_raw": 12.5,
    "median_files_touched_effective": 7.0,
    "mean_files_touched": 87.7,
    "p75_files_touched": 44.0,
    "p90_files_touched": 248.2,
    "max_files_touched": 538,
    "median_production_files": 2.5,
    "median_test_files": 2.0,
    "generated_artifact_distortion": {
        "raw_median": 12.5,
        "effective_median": 7.0,
        "median_distortion_pct": 44.0,
        "polluted_fix_count": 3,
        "polluted_fix_pct": 30.0,
    },
    "repair_family_distribution": {
        "counts": {
            "ci_import": 1,
            "dialogue_routing": 1,
            "opening_fallback": 6,
            "replay_log": 1,
            "routing": 1,
        },
        "percentages": {
            "ci_import": 10.0,
            "dialogue_routing": 10.0,
            "opening_fallback": 60.0,
            "replay_log": 10.0,
            "routing": 10.0,
        },
        "largest_repair_family": "opening_fallback",
        "concentration_ratio": 0.6,
    },
}


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else Path(__file__).resolve().parents[2]


def load_baseline(path: str | Path | None = None) -> dict[str, Any]:
    """Load the frozen corrective locality baseline JSON."""
    target = Path(path or DEFAULT_BASELINE_JSON_PATH)
    if not target.is_absolute():
        target = _repo_root(None) / target
    payload = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{target}: baseline payload must be a JSON object")
    return payload


def validate_required_fields(payload: Mapping[str, Any]) -> list[str]:
    """Return errors for missing top-level baseline fields."""
    errors: list[str] = []
    for field in REQUIRED_BASELINE_FIELDS:
        if field not in payload:
            errors.append(f"missing required field: {field}")
    return errors


def validate_baseline_schema(payload: Mapping[str, Any]) -> list[str]:
    """Return schema validation errors for a baseline payload."""
    errors = validate_required_fields(payload)
    if errors:
        return errors

    if payload.get("primary_metric") != PRIMARY_METRIC:
        errors.append(
            f"primary_metric must be {PRIMARY_METRIC!r}, got {payload.get('primary_metric')!r}"
        )
    if payload.get("comparison_ready") is not True:
        errors.append("comparison_ready must be true")

    distortion = payload.get("generated_artifact_distortion")
    if not isinstance(distortion, Mapping):
        errors.append("generated_artifact_distortion must be an object")
    else:
        for field in REQUIRED_DISTORTION_FIELDS:
            if field not in distortion:
                errors.append(f"generated_artifact_distortion missing {field}")

    families = payload.get("repair_family_distribution")
    if not isinstance(families, Mapping):
        errors.append("repair_family_distribution must be an object")
    else:
        for field in REQUIRED_REPAIR_FAMILY_FIELDS:
            if field not in families:
                errors.append(f"repair_family_distribution missing {field}")

    boundaries = payload.get("cohort_boundaries")
    if not isinstance(boundaries, Mapping):
        errors.append("cohort_boundaries must be an object")
    elif not boundaries.get("start_date") or not boundaries.get("end_date"):
        errors.append("cohort_boundaries requires start_date and end_date")

    return errors


def extract_baseline_payload_from_ca3_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the CA4 baseline shape from a CA3 report payload."""
    files_touched = report.get("files_touched_per_fix") or {}
    production = report.get("production_locality") or {}
    tests = report.get("test_locality") or {}
    distortion = report.get("generated_artifact_distortion") or {}
    families = report.get("repair_family_concentration") or {}
    composition = report.get("cohort_composition") or {}
    date_range = composition.get("date_range") or {}

    return {
        "baseline_version": BASELINE_VERSION,
        "created_date": "2026-06-22",
        "comparison_ready": True,
        "primary_metric": report.get("primary_metric", PRIMARY_METRIC),
        "source_cohort": report.get("source", "docs/audits/CA_corrective_change_locality_cohort.csv"),
        "source_report": DEFAULT_CA3_REPORT_JSON_PATH,
        "cohort_boundaries": {
            "start_date": date_range.get("start", ""),
            "end_date": date_range.get("end", ""),
        },
        "cohort_size": files_touched.get("cohort_size", 0),
        "median_files_touched_raw": distortion.get("raw_median", files_touched.get("median", 0.0)),
        "median_files_touched_effective": distortion.get("effective_median", 0.0),
        "mean_files_touched": files_touched.get("mean", 0.0),
        "p75_files_touched": files_touched.get("p75", 0.0),
        "p90_files_touched": files_touched.get("p90", 0.0),
        "max_files_touched": files_touched.get("maximum", 0),
        "median_production_files": production.get("median", 0.0),
        "median_test_files": tests.get("median", 0.0),
        "generated_artifact_distortion": {
            field: distortion.get(field)
            for field in REQUIRED_DISTORTION_FIELDS
        },
        "repair_family_distribution": {
            "counts": dict(families.get("counts") or {}),
            "percentages": dict(families.get("percentages") or {}),
            "largest_repair_family": families.get("largest_repair_family", ""),
            "concentration_ratio": families.get("concentration_ratio", 0.0),
        },
    }


def _compare_payloads(
    *,
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
    prefix: str = "",
) -> list[str]:
    errors: list[str] = []
    for key, expected_value in expected.items():
        label = f"{prefix}.{key}" if prefix else key
        if key not in actual:
            errors.append(f"missing field: {label}")
            continue
        actual_value = actual[key]
        if isinstance(expected_value, Mapping):
            if not isinstance(actual_value, Mapping):
                errors.append(f"{label} must be an object")
                continue
            errors.extend(
                _compare_payloads(actual=actual_value, expected=expected_value, prefix=label)
            )
        elif actual_value != expected_value:
            errors.append(f"{label} mismatch: {actual_value!r} != {expected_value!r}")
    return errors


def validate_baseline_matches_ca3_report(
    baseline: Mapping[str, Any],
    ca3_report: Mapping[str, Any],
) -> list[str]:
    """Return errors when baseline values diverge from CA3 report measurements."""
    expected = extract_baseline_payload_from_ca3_report(ca3_report)
    compare_keys = [
        key
        for key in REQUIRED_BASELINE_FIELDS
        if key not in {"baseline_version", "created_date", "comparison_ready", "source_report"}
    ]
    filtered_expected = {key: expected[key] for key in compare_keys if key in expected}
    filtered_actual = {key: baseline[key] for key in compare_keys if key in baseline}
    return _compare_payloads(actual=filtered_actual, expected=filtered_expected)


def validate_baseline_matches_frozen_record(baseline: Mapping[str, Any]) -> list[str]:
    """Return errors when on-disk baseline diverges from the CA4 frozen record."""
    compare_keys = [key for key in CA4_FROZEN_BASELINE if key != "source_report"]
    expected = {key: CA4_FROZEN_BASELINE[key] for key in compare_keys}
    actual = {key: baseline[key] for key in compare_keys if key in baseline}
    return _compare_payloads(actual=actual, expected=expected)


def validate_baseline_reproducible_from_cohort(
    baseline: Mapping[str, Any],
    *,
    csv_path: str | Path | None = None,
) -> list[str]:
    """Return errors when CA3 recomputation from cohort authority diverges from baseline."""
    from tools.corrective_change_locality_report import build_corrective_locality_report
    from tests.helpers.corrective_change_locality_cohort import load_cohort, validate_cohort

    target = Path(csv_path or baseline.get("source_cohort") or "docs/audits/CA_corrective_change_locality_cohort.csv")
    if not target.is_absolute():
        target = _repo_root(None) / target

    errors = validate_cohort(target)
    if errors:
        return [f"cohort validation failed: {errors[0]}"]

    rows = load_cohort(target)
    report = build_corrective_locality_report(rows)
    expected = extract_baseline_payload_from_ca3_report(report)
    compare_keys = [
        key
        for key in REQUIRED_BASELINE_FIELDS
        if key
        not in {
            "baseline_version",
            "created_date",
            "comparison_ready",
            "source_cohort",
            "source_report",
            "cohort_boundaries",
        }
    ]
    filtered_expected = {key: expected[key] for key in compare_keys if key in expected}
    filtered_actual = {key: baseline[key] for key in compare_keys if key in baseline}
    return _compare_payloads(actual=filtered_actual, expected=filtered_expected)


def validate_baseline(
    baseline_path: str | Path | None = None,
    *,
    ca3_report_path: str | Path | None = None,
    csv_path: str | Path | None = None,
) -> list[str]:
    """Run full CA4 baseline validation; empty when the lock is intact."""
    root = _repo_root(None)
    baseline = load_baseline(baseline_path)

    errors = validate_baseline_schema(baseline)
    if errors:
        return errors

    ca3_target = Path(ca3_report_path or DEFAULT_CA3_REPORT_JSON_PATH)
    if not ca3_target.is_absolute():
        ca3_target = root / ca3_target
    if not ca3_target.is_file():
        errors.append(f"missing CA3 report: {ca3_target}")
        return errors

    ca3_report = json.loads(ca3_target.read_text(encoding="utf-8"))
    if not isinstance(ca3_report, dict):
        errors.append(f"{ca3_target}: CA3 report must be a JSON object")
        return errors

    errors.extend(validate_baseline_matches_frozen_record(baseline))
    errors.extend(validate_baseline_matches_ca3_report(baseline, ca3_report))
    errors.extend(
        validate_baseline_reproducible_from_cohort(
            baseline,
            csv_path=csv_path or baseline.get("source_cohort"),
        )
    )
    return errors


def render_ca4_baseline_lock_report_md(
    baseline: Mapping[str, Any],
    validation_errors: Sequence[str],
) -> str:
    """Render CA4 baseline lock report markdown."""
    distortion = baseline.get("generated_artifact_distortion") or {}
    families = baseline.get("repair_family_distribution") or {}
    boundaries = baseline.get("cohort_boundaries") or {}
    status = "PASS" if not validation_errors else "FAIL"

    lines = [
        "# CA4 Corrective Locality Baseline Lock Report",
        "",
        "> CA4 frozen historical baseline for future corrective-fix cohort comparison.",
        "",
        "## Lock status",
        "",
        f"- **Validation status:** {status}",
        f"- **Baseline version:** {baseline.get('baseline_version')}",
        f"- **Created date:** {baseline.get('created_date')}",
        f"- **Comparison ready:** {baseline.get('comparison_ready')}",
        f"- **Primary metric:** {baseline.get('primary_metric')}",
        "",
        "## Frozen baseline values",
        "",
        f"- **Cohort size:** {baseline.get('cohort_size')}",
        f"- **Median files touched (raw):** {baseline.get('median_files_touched_raw')}",
        f"- **Median files touched (effective):** {baseline.get('median_files_touched_effective')}",
        f"- **Mean files touched:** {baseline.get('mean_files_touched')}",
        f"- **P75 files touched:** {baseline.get('p75_files_touched')}",
        f"- **P90 files touched:** {baseline.get('p90_files_touched')}",
        f"- **Max files touched:** {baseline.get('max_files_touched')}",
        f"- **Median production files:** {baseline.get('median_production_files')}",
        f"- **Median test files:** {baseline.get('median_test_files')}",
        f"- **Generated-artifact median distortion:** {distortion.get('median_distortion_pct')}%",
        f"- **Polluted fixes:** {distortion.get('polluted_fix_count')} ({distortion.get('polluted_fix_pct')}%)",
        f"- **Largest repair family:** {families.get('largest_repair_family')} "
        f"(concentration ratio {families.get('concentration_ratio')})",
        "",
        "## Validation results",
        "",
    ]
    if validation_errors:
        for error in validation_errors:
            lines.append(f"- FAIL: {error}")
    else:
        lines.append("- PASS: baseline schema valid")
        lines.append("- PASS: required metrics present")
        lines.append("- PASS: values match CA3 report artifact")
        lines.append("- PASS: values reproducible from CA1 cohort authority")
        lines.append("- PASS: on-disk baseline matches CA4 frozen record")

    lines.extend(
        [
            "",
            "## Future comparison guidance",
            "",
            "1. Build a new reviewed corrective cohort with the same CA1 qualifying definition.",
            "2. Run CA3 measurement on the new cohort without changing metric definitions.",
            "3. Compare raw and effective median files touched, median production files, and median test files against this baseline.",
            f"4. Record cohort date range; this baseline covers {boundaries.get('start_date')} through {boundaries.get('end_date')}.",
            "5. Bump `baseline_version` only when intentionally superseding this lock.",
            "",
        ]
    )
    return "\n".join(lines)


def write_ca4_baseline_lock_report(
    output_path: str | Path | None = None,
    *,
    baseline_path: str | Path | None = None,
    ca3_report_path: str | Path | None = None,
    csv_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Validate baseline lock and write CA4 lock report markdown."""
    root = _repo_root(repo_root)
    baseline = load_baseline(baseline_path)
    errors = validate_baseline(
        baseline_path,
        ca3_report_path=ca3_report_path,
        csv_path=csv_path,
    )
    if errors:
        raise ValueError("CA4 baseline validation failed:\n" + "\n".join(f"- {err}" for err in errors))

    markdown = render_ca4_baseline_lock_report_md(baseline, errors)
    target = Path(output_path or DEFAULT_CA4_LOCK_REPORT_PATH)
    if not target.is_absolute():
        target = root / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return dict(baseline), markdown
