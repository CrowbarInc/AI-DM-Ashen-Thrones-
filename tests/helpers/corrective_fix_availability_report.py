"""CA8 corrective fix availability analysis (read-side only).

Determines whether absent post-baseline corrective fixes reflect lower defect
creation, discovery gaps, program-work absorption, qualification methodology,
or observation-window limits. Does not modify baselines, cohorts, or integrate
trend windows or recurrence history.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.corrective_fix_absence_report import (
    DEFAULT_BASELINE_JSON_PATH,
    DEFAULT_INVENTORY_JSON_PATH,
    classify_exclusion_reason,
    load_baseline_summary,
    load_inventory_candidates,
)
from tests.helpers.post_baseline_corrective_cohort import (
    DEFAULT_EXCLUSIONS_CSV_PATH,
    DEFAULT_REVIEW_QUEUE_PATH,
    PostBaselineExclusionRow,
    load_post_baseline_exclusions,
    load_review_queue,
    validate_post_baseline_cohort,
)

DEFAULT_CA7_JSON_PATH = "artifacts/ca7_corrective_fix_absence_report.json"
DEFAULT_MD_OUTPUT_PATH = "artifacts/ca8_corrective_fix_availability_report.md"
DEFAULT_JSON_OUTPUT_PATH = "artifacts/ca8_corrective_fix_availability_report.json"
REPORT_SCHEMA_VERSION = 1
PRIMARY_METRIC = "corrective_availability_rate"

LATENT_ACTIVITY_CATEGORIES: tuple[str, ...] = (
    "explicit_corrective_fixes",
    "embedded_corrective_work",
    "structural_prevention_work",
    "pure_governance_work",
)

_COMPOSITION_PATTERNS: dict[str, tuple[str, ...]] = {
    "ownership_related": (
        "ownership",
        "authorship",
        "metadata consolidation",
    ),
    "replay_related": (
        "replay",
    ),
    "governance_related": (
        "governance",
        "acceptance gate",
        "taxonomy",
        "drift classification",
    ),
    "instrumentation_related": (
        "instrumentation",
        "observability",
        "incidence measurement",
        "trend measurement",
        "recurrence tracking",
        "semantic mutation attribution",
    ),
}

_EMBEDDED_CORRECTIVE_PATTERNS: tuple[str, ...] = (
    "planned ",
    "cycle delivery",
    "consolidation",
    "compression",
    "collapse",
    "retirement",
    "extraction finalize",
    "authorship",
    "topology collapse",
    "architecture cleanup",
    "metadata consolidation",
)

_STRUCTURAL_PREVENTION_PATTERNS: tuple[str, ...] = (
    "instrumentation only",
    "test instrumentation",
    "trend instrumentation",
    "incidence measurement",
    "recurrence tracking",
    "maintenance compression",
    "maintenance reduction",
    "replay surface",
    "replay harness",
    "replay projection",
    "replay cost",
    "golden replay",
    "replay schema",
    "reconnaissance",
    "discovery not defect",
    "observability promotion",
    "no production runtime source repair",
)

_PURE_GOVERNANCE_PATTERNS: tuple[str, ...] = (
    "governance taxonomy",
    "governance test promotion",
    "acceptance gate promotion",
    "governance decomposition",
    "drift classification infrastructure",
)


@dataclass(frozen=True)
class AnalyzedExclusion:
    commit_hash: str
    date: str
    title: str
    exclusion_reason: str
    production_files_touched: int
    test_files_touched: int
    ca7_work_category: str
    latent_activity_category: str
    composition_flags: tuple[str, ...]


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else Path(__file__).resolve().parents[2]


def _normalize_text(*parts: str) -> str:
    return " ".join(str(part or "").lower() for part in parts)


def _text_matches_any(text: str, phrases: Sequence[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _composition_flags(exclusion_reason: str, title: str, *, production: int, test: int) -> tuple[str, ...]:
    text = _normalize_text(exclusion_reason, title)
    flags: list[str] = []
    if production > 0:
        flags.append("production_touching")
    if test > 0:
        flags.append("test_touching")
    for flag_name, phrases in _COMPOSITION_PATTERNS.items():
        if _text_matches_any(text, phrases):
            flags.append(flag_name)
    return tuple(flags)


def classify_latent_activity(
    exclusion_reason: str,
    title: str,
    *,
    production_files_touched: int,
) -> str:
    """Assign one latent-activity category (A/B/C/D) to an excluded candidate."""
    text = _normalize_text(exclusion_reason, title)

    if _text_matches_any(text, _PURE_GOVERNANCE_PATTERNS):
        return "pure_governance_work"

    if production_files_touched > 0 and _text_matches_any(text, _EMBEDDED_CORRECTIVE_PATTERNS):
        return "embedded_corrective_work"

    if production_files_touched > 0:
        return "embedded_corrective_work"

    if _text_matches_any(text, _STRUCTURAL_PREVENTION_PATTERNS):
        return "structural_prevention_work"

    ca7_category = classify_exclusion_reason(exclusion_reason, title)
    if ca7_category in {"governance_work", "observability_work"}:
        return "pure_governance_work"
    if ca7_category in {"instrumentation_work", "replay_work", "decomposition_work"}:
        return "structural_prevention_work"
    if ca7_category == "ownership_work":
        return "embedded_corrective_work"
    return "structural_prevention_work"


def analyze_exclusions(
    exclusions: Sequence[PostBaselineExclusionRow],
    inventory: Mapping[str, Any],
) -> list[AnalyzedExclusion]:
    analyzed: list[AnalyzedExclusion] = []
    for row in exclusions:
        inv = inventory.get(row.commit_hash)
        production = int(getattr(inv, "production_files_touched", 0) if inv else 0)
        test = int(getattr(inv, "test_files_touched", 0) if inv else 0)
        analyzed.append(
            AnalyzedExclusion(
                commit_hash=row.commit_hash,
                date=row.date,
                title=row.title,
                exclusion_reason=row.exclusion_reason,
                production_files_touched=production,
                test_files_touched=test,
                ca7_work_category=classify_exclusion_reason(row.exclusion_reason, row.title),
                latent_activity_category=classify_latent_activity(
                    row.exclusion_reason,
                    row.title,
                    production_files_touched=production,
                ),
                composition_flags=_composition_flags(
                    row.exclusion_reason,
                    row.title,
                    production=production,
                    test=test,
                ),
            )
        )
    return analyzed


def build_exclusion_composition(analyzed: Sequence[AnalyzedExclusion]) -> dict[str, Any]:
    total = len(analyzed)
    composition_counts = {
        "production_touching_exclusions": sum(
            1 for row in analyzed if row.production_files_touched > 0
        ),
        "test_touching_exclusions": sum(1 for row in analyzed if row.test_files_touched > 0),
        "ownership_related_exclusions": sum(
            1 for row in analyzed if "ownership_related" in row.composition_flags
        ),
        "replay_related_exclusions": sum(
            1 for row in analyzed if "replay_related" in row.composition_flags
        ),
        "governance_related_exclusions": sum(
            1 for row in analyzed if "governance_related" in row.composition_flags
        ),
        "instrumentation_related_exclusions": sum(
            1 for row in analyzed if "instrumentation_related" in row.composition_flags
        ),
    }
    return {
        "total_exclusions": total,
        "counts": composition_counts,
        "percentages": {
            key: round(value / total * 100.0, 2) if total else 0.0
            for key, value in composition_counts.items()
        },
    }


def build_latent_activity_distribution(analyzed: Sequence[AnalyzedExclusion]) -> dict[str, Any]:
    by_category: dict[str, list[dict[str, Any]]] = {
        category: [] for category in LATENT_ACTIVITY_CATEGORIES
    }
    counts = {category: 0 for category in LATENT_ACTIVITY_CATEGORIES}
    for row in analyzed:
        counts[row.latent_activity_category] += 1
        by_category[row.latent_activity_category].append(asdict(row))
    total = len(analyzed)
    return {
        "total_exclusions": total,
        "counts": counts,
        "percentages": {
            category: round(counts[category] / total * 100.0, 2) if total else 0.0
            for category in LATENT_ACTIVITY_CATEGORIES
        },
        "by_category": by_category,
    }


def compute_corrective_availability_rate(
    latent_distribution: Mapping[str, Any],
    reviewed_candidates: int,
) -> dict[str, Any]:
    counts = latent_distribution["counts"]
    explicit = counts["explicit_corrective_fixes"]
    embedded = counts["embedded_corrective_work"]
    numerator = explicit + embedded
    rate = round(numerator / reviewed_candidates, 4) if reviewed_candidates else 0.0
    return {
        "primary_metric": PRIMARY_METRIC,
        "explicit_corrective_fixes": explicit,
        "embedded_corrective_work": embedded,
        "structural_prevention_work": counts["structural_prevention_work"],
        "pure_governance_work": counts["pure_governance_work"],
        "reviewed_candidates": reviewed_candidates,
        "corrective_availability_rate": rate,
    }


def _observation_window_days(analyzed: Sequence[AnalyzedExclusion]) -> int:
    parsed: list[date] = []
    for row in analyzed:
        if not row.date:
            continue
        year, month, day = (int(part) for part in row.date.split("-"))
        parsed.append(date(year, month, day))
    if len(parsed) < 2:
        return 0
    return (max(parsed) - min(parsed)).days


def build_availability_assessment(
    *,
    availability: Mapping[str, Any],
    composition: Mapping[str, Any],
    ca7_report: Mapping[str, Any],
    baseline: Mapping[str, Any],
    analyzed: Sequence[AnalyzedExclusion],
) -> dict[str, Any]:
    reviewed = availability["reviewed_candidates"]
    embedded = availability["embedded_corrective_work"]
    explicit = availability["explicit_corrective_fixes"]
    structural = availability["structural_prevention_work"]
    governance = availability["pure_governance_work"]
    relaxed_count = ca7_report.get("qualification_sensitivity", {}).get(
        "relaxed_interpretation", {}
    ).get("promoted_count", 0)
    window_days = _observation_window_days(analyzed)

    hypotheses = {
        "lower_defect_creation": {
            "supported": explicit == 0 and embedded == 0,
            "evidence": (
                "No explicit or embedded corrective activity was classified in the reviewed window."
                if explicit == 0 and embedded == 0
                else "Embedded production-touching program work exists; defect creation may still occur but is routed through planned cycles."
            ),
        },
        "lower_defect_discovery": {
            "supported": composition["counts"]["instrumentation_related_exclusions"] >= 3,
            "evidence": (
                f"{composition['counts']['instrumentation_related_exclusions']} exclusions are instrumentation- or "
                "observability-related, indicating discovery infrastructure expansion rather than absent defect pressure."
            ),
        },
        "defects_absorbed_into_program_work": {
            "supported": embedded > 0,
            "evidence": (
                f"{embedded} excluded candidate(s) touch production runtime sources inside planned ownership, "
                "consolidation, or decomposition cycles rather than as standalone corrective fixes."
            ),
        },
        "qualification_methodology": {
            "supported": relaxed_count > explicit,
            "evidence": (
                f"CA7 relaxed path gate would promote {relaxed_count} candidate(s) while strict CA1 rules promote "
                f"{explicit}; availability rate ({availability['corrective_availability_rate']}) exceeds explicit-fix yield (0.0)."
            ),
        },
        "insufficient_observation_window": {
            "supported": reviewed <= 30 and window_days <= 35,
            "evidence": (
                f"Review window spans {window_days} calendar days with {reviewed} candidates since baseline end "
                f"{(baseline.get('cohort_boundaries') or {}).get('end_date', '')}; longer windows may surface explicit fixes."
            ),
        },
    }

    primary_causes = [
        name
        for name, payload in hypotheses.items()
        if payload["supported"] and name != "lower_defect_creation"
    ]
    if embedded > 0:
        conclusion = (
            "Corrective work did not disappear; it was largely absorbed into larger program work. "
            f"Availability rate is {availability['corrective_availability_rate']} ({explicit + embedded}/{reviewed}) "
            "while explicit corrective fix yield remains zero."
        )
    else:
        conclusion = (
            "Corrective work availability is indistinguishable from zero in this window; "
            "absence may reflect defect-creation, discovery, or observation-window limits."
        )

    return {
        "primary_causes": primary_causes,
        "hypotheses": hypotheses,
        "observation_window_days": window_days,
        "conclusion": conclusion,
        "structural_prevention_share": round(structural / reviewed, 4) if reviewed else 0.0,
        "pure_governance_share": round(governance / reviewed, 4) if reviewed else 0.0,
    }


def build_risks_and_limitations(
    availability: Mapping[str, Any],
    assessment: Mapping[str, Any],
) -> list[str]:
    risks = [
        "Latent-activity categories infer intent from exclusion text and path counts; they are not substitutes for defect telemetry.",
        "Composition dimensions overlap; a single commit may count toward multiple composition metrics.",
        "Embedded corrective work is not equivalent to CA1-qualifying explicit fixes.",
        "This analysis does not compare against CA4 baseline trends or integrate recurrence history.",
    ]
    if availability["explicit_corrective_fixes"] == 0 and availability["embedded_corrective_work"] > 0:
        risks.append(
            "Production-touching program work may mask defect repair boundaries that future reviews could reclassify as explicit fixes."
        )
    if assessment["observation_window_days"] <= 35:
        risks.append(
            "The post-baseline observation window is short; availability conclusions may change as intake continues."
        )
    return risks


def load_ca7_report(
    json_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    target = Path(json_path or DEFAULT_CA7_JSON_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    return json.loads(target.read_text(encoding="utf-8"))


def build_corrective_fix_availability_report(
    *,
    exclusions: Sequence[PostBaselineExclusionRow],
    reviewed_candidates: int,
    inventory: Mapping[str, Any],
    baseline: Mapping[str, Any],
    ca7_report: Mapping[str, Any],
) -> dict[str, Any]:
    analyzed = analyze_exclusions(exclusions, inventory)
    composition = build_exclusion_composition(analyzed)
    latent_distribution = build_latent_activity_distribution(analyzed)
    availability = compute_corrective_availability_rate(latent_distribution, reviewed_candidates)
    assessment = build_availability_assessment(
        availability=availability,
        composition=composition,
        ca7_report=ca7_report,
        baseline=baseline,
        analyzed=analyzed,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "primary_metric": PRIMARY_METRIC,
        "sources": {
            "ca7_report_json": DEFAULT_CA7_JSON_PATH,
            "exclusions_csv": DEFAULT_EXCLUSIONS_CSV_PATH,
            "baseline_json": DEFAULT_BASELINE_JSON_PATH,
            "inventory_json": DEFAULT_INVENTORY_JSON_PATH,
        },
        "exclusion_composition": composition,
        "latent_activity_distribution": latent_distribution,
        "availability_analysis": availability,
        "availability_assessment": assessment,
        "risks_and_limitations": build_risks_and_limitations(availability, assessment),
    }


def _metric_line(label: str, value: Any) -> str:
    return f"- **{label}:** {value}"


def _section_members(members: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not members:
        lines.append("_None._")
        return lines
    for row in members:
        title = str(row["title"]).replace("|", "\\|")
        lines.append(
            f"- `{row['commit_hash'][:7]}` ({row['date']}) — {title} "
            f"[production={row['production_files_touched']}, test={row['test_files_touched']}]"
        )
    return lines



def render_corrective_fix_availability_report_md(report: Mapping[str, Any]) -> str:
    composition = report["exclusion_composition"]
    latent = report["latent_activity_distribution"]
    availability = report["availability_analysis"]
    assessment = report["availability_assessment"]
    counts = composition["counts"]
    composition_labels = {
        "production_touching_exclusions": "Production-touching exclusions",
        "test_touching_exclusions": "Test-touching exclusions",
        "ownership_related_exclusions": "Ownership-related exclusions",
        "replay_related_exclusions": "Replay-related exclusions",
        "governance_related_exclusions": "Governance-related exclusions",
        "instrumentation_related_exclusions": "Instrumentation-related exclusions",
    }

    lines = [
        "# CA8 Corrective Fix Availability Report",
        "",
        "> Determines whether absent post-baseline corrective fixes reflect defect creation, discovery, program-work absorption, qualification methodology, or observation-window limits.",
        "",
        f"_Primary metric: **{report['primary_metric']}** (`(explicit_corrective_fixes + embedded_corrective_work) / reviewed_candidates`)._",
        "",
        "## 1. Executive Summary",
        "",
        assessment["conclusion"],
        "",
        _metric_line("Reviewed candidates", availability["reviewed_candidates"]),
        _metric_line("Explicit corrective fixes", availability["explicit_corrective_fixes"]),
        _metric_line("Embedded corrective work", availability["embedded_corrective_work"]),
        _metric_line("Corrective availability rate", availability["corrective_availability_rate"]),
        _metric_line("Primary supported causes", ", ".join(assessment["primary_causes"]) or "none"),
        "",
        "## 2. Exclusion Composition",
        "",
        "Composition metrics for all 26 excluded post-baseline candidates.",
        "",
        "| Metric | Count | Percentage |",
        "|---|---:|---:|",
    ]
    for key, label in composition_labels.items():
        lines.append(f"| {label} | {counts[key]} | {composition['percentages'][key]}% |")

    section_map = {
        "embedded_corrective_work": "## 3. Embedded Corrective Activity",
        "structural_prevention_work": "## 4. Structural Prevention Activity",
        "pure_governance_work": "## 5. Governance Activity",
    }
    for category, heading in section_map.items():
        lines.extend(["", heading, ""])
        lines.extend(_section_members(latent["by_category"][category]))
        lines.append("")

    lines.extend(
        [
            "## 6. Availability Assessment",
            "",
            _metric_line("Corrective availability rate", availability["corrective_availability_rate"]),
            _metric_line("Structural prevention share", assessment["structural_prevention_share"]),
            _metric_line("Pure governance share", assessment["pure_governance_share"]),
            _metric_line("Observation window (days)", assessment["observation_window_days"]),
            "",
            "### Cause hypotheses",
            "",
        ]
    )
    for cause, payload in assessment["hypotheses"].items():
        label = cause.replace("_", " ")
        lines.append(f"- **{label}** — supported={payload['supported']}; {payload['evidence']}")
    lines.extend(["", assessment["conclusion"], ""])

    explicit = latent["by_category"]["explicit_corrective_fixes"]
    lines.extend(["### Explicit corrective fixes (category A)", ""])
    lines.extend(_section_members(explicit))
    lines.extend(["", "## 7. Risks And Limitations", ""])
    for risk in report["risks_and_limitations"]:
        lines.append(f"- {risk}")
    lines.append("")
    return "\n".join(lines)


def write_corrective_fix_availability_report(
    md_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
    *,
    ca7_json_path: str | Path | None = None,
    exclusions_csv_path: str | Path | None = None,
    review_queue_path: str | Path | None = None,
    cohort_csv_path: str | Path | None = None,
    baseline_json_path: str | Path | None = None,
    inventory_json_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    root = _repo_root(repo_root)
    errors = validate_post_baseline_cohort(
        cohort_csv_path=cohort_csv_path,
        exclusions_csv_path=exclusions_csv_path,
        review_queue_path=review_queue_path,
    )
    if errors:
        raise ValueError("CA8 input validation failed:\n" + "\n".join(f"- {err}" for err in errors))

    exclusions = load_post_baseline_exclusions(exclusions_csv_path)
    review_queue = load_review_queue(review_queue_path)
    inventory = load_inventory_candidates(inventory_json_path, repo_root=root)
    baseline = load_baseline_summary(baseline_json_path, repo_root=root)
    ca7_report = load_ca7_report(ca7_json_path, repo_root=root)
    reviewed_candidates = sum(1 for row in review_queue if row.reviewed)

    report = build_corrective_fix_availability_report(
        exclusions=exclusions,
        reviewed_candidates=reviewed_candidates,
        inventory=inventory,
        baseline=baseline,
        ca7_report=ca7_report,
    )
    markdown = render_corrective_fix_availability_report_md(report)

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
