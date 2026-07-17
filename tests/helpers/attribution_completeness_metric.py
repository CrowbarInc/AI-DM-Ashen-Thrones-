"""BR1 attribution completeness repository metric (read-side reporting only).

Consumes BS1 inventory scoring, BS3 contract maturity scores, and frozen BS1
baseline snapshots. Does not modify attribution behavior, producers, projection,
classification, or recurrence generation.

CO96 governance: resolved completeness is the primary production KPI; strict
completeness is reported as an architectural diagnostic only (see
``ATTRIBUTION_GOVERNANCE_RULES`` in ``attribution_contract``).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.attribution_contract import (
    ATTRIBUTION_MATURITY_PRIMARY_KPI,
    ATTRIBUTION_ORIGIN_DIRECT,
    ATTRIBUTION_STRICT_COMPLETENESS_ROLE,
    BS1_MATURITY_SNAPSHOT,
    REPLACEMENT_PATHS,
    REQUIRED_ATTRIBUTION_FIELDS,
    calculate_attribution_maturity_scores,
)
from tests.helpers.replacement_attribution_inventory import (
    BS1_BASELINE_COMPLETENESS,
    BS1_BASELINE_MISSING_FIELD_TOTALS,
    AttributionRecord,
    build_baseline_attribution_corpus,
    build_replacement_path_attribution_report,
    calculate_attribution_completeness,
)

BR1_BASELINE_PATH_RESOLVED: dict[str, tuple[int, int]] = {
    "visibility replacement": (0, 5),
    "first mention replacement": (0, 5),
    "referential replacement": (0, 5),
    "sealed replacement": (0, 5),
    "response type replacement": (0, 6),
    "sanitizer replacement": (0, 10),
    "repair mutation": (0, 7),
    "opening fallback": (3, 7),
    "strict social replacement": (0, 6),
}

DEFAULT_OUTPUT_PATH = "artifacts/attribution_completeness_report.md"


def _is_strict_complete(record: AttributionRecord) -> bool:
    origins = record.get("attribution_origin") or {}
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        value = record.get(field)
        if value is None or str(value).strip() == "":
            return False
        if field in (record.get("missing_fields") or []):
            return False
        if origins.get(field) != ATTRIBUTION_ORIGIN_DIRECT:
            return False
    return True


def _field_coverage_pct(present: int, total: int) -> float:
    return round(100.0 * present / total, 2) if total else 0.0


def _path_resolved_pct(complete: int, total: int) -> float:
    return round(100.0 * complete / total, 2) if total else 0.0


def build_field_coverage_report(records: Sequence[AttributionRecord]) -> dict[str, dict[str, Any]]:
    """Return per-field present/missing counts and coverage percentages."""
    total = len(records)
    report: dict[str, dict[str, Any]] = {}
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        missing = sum(1 for record in records if field in (record.get("missing_fields") or []))
        present = total - missing
        strict_present = sum(
            1
            for record in records
            if field not in (record.get("missing_fields") or [])
            and (record.get("attribution_origin") or {}).get(field) == ATTRIBUTION_ORIGIN_DIRECT
        )
        report[field] = {
            "present": present,
            "missing": missing,
            "coverage_pct": _field_coverage_pct(present, total),
            "strict_present": strict_present,
            "strict_coverage_pct": _field_coverage_pct(strict_present, total),
        }
    return report


def build_path_coverage_report(
    records: Sequence[AttributionRecord],
    *,
    path_report: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Return per-path resolved and strict completeness with missing-field counts."""
    if path_report is None:
        path_report = build_replacement_path_attribution_report(records)
    report: dict[str, dict[str, Any]] = {}
    for path in REPLACEMENT_PATHS:
        path_records = [record for record in records if record.get("replacement_path") == path]
        stats = path_report.get(path) or {}
        total = int(stats.get("total") or len(path_records))
        resolved_complete = int(stats.get("complete") or 0)
        strict_complete = sum(1 for record in path_records if _is_strict_complete(record))
        report[path] = {
            "total": total,
            "resolved_complete": resolved_complete,
            "strict_complete": strict_complete,
            "resolved_completeness_pct": _path_resolved_pct(resolved_complete, total),
            "strict_completeness_pct": _path_resolved_pct(strict_complete, total),
            "missing_owner_bucket": int(stats.get("missing_owner_bucket") or 0),
            "missing_source_family": int(stats.get("missing_source_family") or 0),
            "missing_repair_kind": int(stats.get("missing_repair_kind") or 0),
            "missing_recurrence_key": int(stats.get("missing_recurrence_key") or 0),
            "missing_mutation_classification": int(stats.get("missing_mutation_classification") or 0),
        }
    return report


def _rank_paths_by_resolved_coverage(
    path_coverage: Mapping[str, Mapping[str, Any]],
) -> list[tuple[str, float]]:
    ranked: list[tuple[str, float]] = []
    for path in REPLACEMENT_PATHS:
        stats = path_coverage.get(path) or {}
        total = int(stats.get("total") or 0)
        if total == 0:
            continue
        ranked.append((path, float(stats.get("resolved_completeness_pct") or 0.0)))
    ranked.sort(key=lambda item: (item[1], item[0]))
    return ranked


def _field_baseline_coverage(field: str) -> dict[str, Any]:
    baseline_total = int(BS1_BASELINE_COMPLETENESS["total_records"])
    baseline_missing = int(BS1_BASELINE_MISSING_FIELD_TOTALS.get(field, 0))
    baseline_present = baseline_total - baseline_missing
    return {
        "present": baseline_present,
        "missing": baseline_missing,
        "coverage_pct": _field_coverage_pct(baseline_present, baseline_total),
    }


def build_attribution_completeness_report(
    *,
    records: Sequence[AttributionRecord] | None = None,
) -> dict[str, Any]:
    """Build structured BR1 attribution completeness metric payload."""
    if records is None:
        records = build_baseline_attribution_corpus()

    completeness = calculate_attribution_completeness(records)
    path_report = build_replacement_path_attribution_report(records)
    field_coverage = build_field_coverage_report(records)
    path_coverage = build_path_coverage_report(records, path_report=path_report)
    maturity = calculate_attribution_maturity_scores(records=records)

    baseline_completeness = dict(BS1_BASELINE_COMPLETENESS)
    baseline_maturity = dict(BS1_MATURITY_SNAPSHOT)

    path_ranking = _rank_paths_by_resolved_coverage(path_coverage)
    missing_field_ranking = sorted(
        (
            (field, field_coverage[field]["missing"])
            for field in REQUIRED_ATTRIBUTION_FIELDS
            if field_coverage[field]["missing"] > 0
        ),
        key=lambda item: (-item[1], item[0]),
    )

    field_trend: dict[str, dict[str, Any]] = {}
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        baseline = _field_baseline_coverage(field)
        current = field_coverage[field]
        field_trend[field] = {
            "baseline": baseline,
            "current": {
                "present": current["present"],
                "missing": current["missing"],
                "coverage_pct": current["coverage_pct"],
            },
            "delta_coverage_pct": round(current["coverage_pct"] - baseline["coverage_pct"], 2),
        }

    path_trend: dict[str, dict[str, Any]] = {}
    for path in REPLACEMENT_PATHS:
        baseline_complete, baseline_total = BR1_BASELINE_PATH_RESOLVED.get(path, (0, 0))
        current_stats = path_coverage[path]
        current_pct = float(current_stats["resolved_completeness_pct"])
        baseline_pct = _path_resolved_pct(baseline_complete, baseline_total)
        path_trend[path] = {
            "baseline": {
                "resolved_complete": baseline_complete,
                "total": baseline_total,
                "resolved_completeness_pct": baseline_pct,
            },
            "current": {
                "resolved_complete": current_stats["resolved_complete"],
                "total": current_stats["total"],
                "resolved_completeness_pct": current_pct,
            },
            "delta_resolved_completeness_pct": round(current_pct - baseline_pct, 2),
        }

    return {
        "schema_version": 1,
        "corpus": {
            "baseline_total_records": baseline_completeness["total_records"],
            "current_total_records": completeness["total_records"],
        },
        "overall": {
            "baseline": {
                "strict_completeness_pct": baseline_completeness["strict_completeness_pct"],
                "resolved_completeness_pct": baseline_completeness["resolved_completeness_pct"],
                "strict_complete_records": baseline_completeness["strict_complete_records"],
                "resolved_complete_records": baseline_completeness["resolved_complete_records"],
                "total_records": baseline_completeness["total_records"],
            },
            "current": {
                "strict_completeness_pct": completeness["strict_completeness_pct"],
                "resolved_completeness_pct": completeness["resolved_completeness_pct"],
                "strict_complete_records": completeness["strict_complete_records"],
                "resolved_complete_records": completeness["resolved_complete_records"],
                "total_records": completeness["total_records"],
            },
            "delta": {
                "strict_completeness_pct": round(
                    completeness["strict_completeness_pct"]
                    - baseline_completeness["strict_completeness_pct"],
                    2,
                ),
                "resolved_completeness_pct": round(
                    completeness["resolved_completeness_pct"]
                    - baseline_completeness["resolved_completeness_pct"],
                    2,
                ),
                "strict_complete_records": (
                    completeness["strict_complete_records"]
                    - baseline_completeness["strict_complete_records"]
                ),
                "resolved_complete_records": (
                    completeness["resolved_complete_records"]
                    - baseline_completeness["resolved_complete_records"]
                ),
            },
        },
        "contract_integration": {
            "baseline": {
                "contract_compliance_score_pct": baseline_maturity["contract_compliance_score_pct"],
                "taxonomy_consistency_score_pct": baseline_maturity["taxonomy_consistency_score_pct"],
            },
            "current": {
                "contract_compliance_score_pct": maturity["contract_compliance_score_pct"],
                "taxonomy_consistency_score_pct": maturity["taxonomy_consistency_score_pct"],
            },
            "delta": {
                "contract_compliance_score_pct": round(
                    maturity["contract_compliance_score_pct"]
                    - baseline_maturity["contract_compliance_score_pct"],
                    2,
                ),
                "taxonomy_consistency_score_pct": round(
                    maturity["taxonomy_consistency_score_pct"]
                    - baseline_maturity["taxonomy_consistency_score_pct"],
                    2,
                ),
            },
        },
        "field_coverage": field_coverage,
        "field_trend": field_trend,
        "path_coverage": path_coverage,
        "path_trend": path_trend,
        "risk": {
            "lowest_coverage_paths": path_ranking[:5],
            "highest_coverage_paths": list(reversed(path_ranking[-5:])),
            "most_commonly_missing_fields": missing_field_ranking,
        },
    }


def render_attribution_completeness_report_md(report: Mapping[str, Any]) -> str:
    """Render BR1 attribution completeness markdown report."""
    overall = report["overall"]
    contract = report["contract_integration"]
    field_trend = report["field_trend"]
    path_trend = report["path_trend"]
    path_coverage = report["path_coverage"]
    risk = report["risk"]

    lines = [
        "# Attribution Completeness Report",
        "",
        "> BR1 repository metric — read-side attribution completeness over the deterministic baseline corpus.",
        "",
        f"> **CO96 governance:** primary KPI is `{ATTRIBUTION_MATURITY_PRIMARY_KPI}`; "
        f"strict completeness is `{ATTRIBUTION_STRICT_COMPLETENESS_ROLE}` only "
        "(not a production-stamp target).",
        "",
        "## Overall Completeness",
        "",
        "| Metric | Baseline (BS1) | Current | Delta |",
        "|---|---:|---:|---:|",
        f"| Strict completeness % | {overall['baseline']['strict_completeness_pct']} | "
        f"{overall['current']['strict_completeness_pct']} | "
        f"{overall['delta']['strict_completeness_pct']:+} |",
        f"| Resolved completeness % | {overall['baseline']['resolved_completeness_pct']} | "
        f"{overall['current']['resolved_completeness_pct']} | "
        f"{overall['delta']['resolved_completeness_pct']:+} |",
        f"| Strict complete records | "
        f"{overall['baseline']['strict_complete_records']}/{overall['baseline']['total_records']} | "
        f"{overall['current']['strict_complete_records']}/{overall['current']['total_records']} | "
        f"{overall['delta']['strict_complete_records']:+} |",
        f"| Resolved complete records | "
        f"{overall['baseline']['resolved_complete_records']}/{overall['baseline']['total_records']} | "
        f"{overall['current']['resolved_complete_records']}/{overall['current']['total_records']} | "
        f"{overall['delta']['resolved_complete_records']:+} |",
        "",
        f"_Corpus size: baseline {report['corpus']['baseline_total_records']} records, "
        f"current {report['corpus']['current_total_records']} records._",
        "",
        "## Contract Integration (BS3)",
        "",
        "| Score | Baseline (BS1) | Current | Delta |",
        "|---|---:|---:|---:|",
        f"| Contract compliance % | {contract['baseline']['contract_compliance_score_pct']} | "
        f"{contract['current']['contract_compliance_score_pct']} | "
        f"{contract['delta']['contract_compliance_score_pct']:+} |",
        f"| Taxonomy consistency % | {contract['baseline']['taxonomy_consistency_score_pct']} | "
        f"{contract['current']['taxonomy_consistency_score_pct']} | "
        f"{contract['delta']['taxonomy_consistency_score_pct']:+} |",
        "",
        "## Field Coverage",
        "",
        "| Field | Baseline coverage | Current coverage | Delta | Present | Missing | Strict coverage |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        trend = field_trend[field]
        current = report["field_coverage"][field]
        lines.append(
            f"| `{field}` | {trend['baseline']['coverage_pct']}% | "
            f"{trend['current']['coverage_pct']}% | {trend['delta_coverage_pct']:+} | "
            f"{current['present']} | {current['missing']} | {current['strict_coverage_pct']}% |"
        )

    lines.extend(
        [
            "",
            "## Path Coverage",
            "",
            "| Replacement path | Baseline resolved | Current resolved | Delta | Total | Strict % | "
            "Missing owner | Missing source | Missing repair | Missing recurrence | Missing mutation |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for path in REPLACEMENT_PATHS:
        trend = path_trend[path]
        stats = path_coverage[path]
        lines.append(
            "| {path} | {baseline_pct}% ({baseline_complete}/{baseline_total}) | "
            "{current_pct}% ({current_complete}/{current_total}) | {delta:+} | {total} | "
            "{strict_pct}% | {owner} | {source} | {repair} | {recurrence} | {mutation} |".format(
                path=path,
                baseline_pct=trend["baseline"]["resolved_completeness_pct"],
                baseline_complete=trend["baseline"]["resolved_complete"],
                baseline_total=trend["baseline"]["total"],
                current_pct=trend["current"]["resolved_completeness_pct"],
                current_complete=trend["current"]["resolved_complete"],
                current_total=trend["current"]["total"],
                delta=trend["delta_resolved_completeness_pct"],
                total=stats["total"],
                strict_pct=stats["strict_completeness_pct"],
                owner=stats["missing_owner_bucket"],
                source=stats["missing_source_family"],
                repair=stats["missing_repair_kind"],
                recurrence=stats["missing_recurrence_key"],
                mutation=stats["missing_mutation_classification"],
            )
        )

    lines.extend(["", "## Risk Summary", ""])
    lines.append("### Lowest Coverage Paths")
    lines.append("")
    if risk["lowest_coverage_paths"]:
        for path, pct in risk["lowest_coverage_paths"]:
            lines.append(f"- {path}: {pct}% resolved complete")
    else:
        lines.append("- _none_")

    lines.extend(["", "### Highest Coverage Paths", ""])
    if risk["highest_coverage_paths"]:
        for path, pct in risk["highest_coverage_paths"]:
            lines.append(f"- {path}: {pct}% resolved complete")
    else:
        lines.append("- _none_")

    lines.extend(["", "### Most Commonly Missing Fields", ""])
    if risk["most_commonly_missing_fields"]:
        for field, count in risk["most_commonly_missing_fields"]:
            lines.append(f"- `{field}`: {count} record(s)")
    else:
        lines.append("- _none_")

    lines.append("")
    return "\n".join(lines)


def write_attribution_completeness_report(
    output_path: str | Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Generate BR1 attribution completeness artifact."""
    report = build_attribution_completeness_report()
    markdown = render_attribution_completeness_report_md(report)
    target = Path(output_path or DEFAULT_OUTPUT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return report, markdown
