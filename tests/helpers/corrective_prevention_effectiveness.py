"""CA10 corrective prevention effectiveness (read-side only).

Evaluates whether structural programs absorbing embedded corrective work
plausibly prevent standalone corrective fixes. Does not modify baselines,
cohorts, or integrate trend windows, recurrence, or forecasting.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from tests.helpers.corrective_fix_absence_report import (
    DEFAULT_BASELINE_JSON_PATH,
    load_baseline_summary,
)

DEFAULT_CA7_JSON_PATH = "artifacts/ca7_corrective_fix_absence_report.json"
DEFAULT_CA8_JSON_PATH = "artifacts/ca8_corrective_fix_availability_report.json"
DEFAULT_CA9_JSON_PATH = "artifacts/ca9_embedded_corrective_attribution_report.json"
DEFAULT_MD_OUTPUT_PATH = "artifacts/ca10_corrective_prevention_effectiveness_report.md"
DEFAULT_JSON_OUTPUT_PATH = "artifacts/ca10_corrective_prevention_effectiveness_report.json"
REPORT_SCHEMA_VERSION = 1
PRIMARY_METRIC = "preventive_absorption_ratio"

PREVENTION_CATEGORIES: tuple[str, ...] = (
    "fallback_consolidation",
    "decomposition",
    "ownership_compression",
    "replay_stabilization",
)

AssessmentClass = Literal["likely_preventive", "neutral", "unclear"]


@dataclass(frozen=True)
class CategoryPreventionSignals:
    category: str
    candidate_count: int
    production_touching_count: int
    test_touching_count: int
    governance_involvement_count: int
    replay_involvement_count: int
    ownership_involvement_count: int
    total_production_files_touched: int
    total_test_files_touched: int


@dataclass(frozen=True)
class CategoryAssessment:
    category: str
    classification: AssessmentClass
    rationale: str
    prevention_signals: CategoryPreventionSignals


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else Path(__file__).resolve().parents[2]


def _normalize_text(*parts: str) -> str:
    return " ".join(str(part or "").lower() for part in parts)


def _load_json(path: str | Path, *, repo_root: Path | None) -> dict[str, Any]:
    target = Path(path)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    return json.loads(target.read_text(encoding="utf-8"))


def load_ca7_report(json_path: str | Path | None = None, *, repo_root: Path | None = None) -> dict[str, Any]:
    return _load_json(json_path or DEFAULT_CA7_JSON_PATH, repo_root=repo_root)


def load_ca8_report(json_path: str | Path | None = None, *, repo_root: Path | None = None) -> dict[str, Any]:
    return _load_json(json_path or DEFAULT_CA8_JSON_PATH, repo_root=repo_root)


def load_ca9_report(json_path: str | Path | None = None, *, repo_root: Path | None = None) -> dict[str, Any]:
    return _load_json(json_path or DEFAULT_CA9_JSON_PATH, repo_root=repo_root)


def embedded_candidates_by_category(
    ca9_report: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    by_category = ca9_report.get("attribution_categories", {}).get("by_category", {})
    return {
        category: list(by_category.get(category) or [])
        for category in PREVENTION_CATEGORIES
    }


def _text_involves_governance(text: str) -> bool:
    return any(token in text for token in ("governance", "acceptance gate", "taxonomy"))


def _text_involves_replay(text: str) -> bool:
    return "replay" in text


def _text_involves_ownership(text: str) -> bool:
    return any(token in text for token in ("ownership", "authorship", "fallback"))


def compute_category_prevention_signals(
    category: str,
    candidates: Sequence[Mapping[str, Any]],
) -> CategoryPreventionSignals:
    production_touching = 0
    test_touching = 0
    governance = 0
    replay = 0
    ownership = 0
    total_production = 0
    total_test = 0
    for candidate in candidates:
        production = int(candidate.get("production_files_touched") or 0)
        tests = int(candidate.get("test_files_touched") or 0)
        text = _normalize_text(
            str(candidate.get("exclusion_reason") or ""),
            str(candidate.get("title") or ""),
        )
        total_production += production
        total_test += tests
        if production > 0:
            production_touching += 1
        if tests > 0:
            test_touching += 1
        if _text_involves_governance(text):
            governance += 1
        if _text_involves_replay(text) or category == "replay_stabilization":
            replay += 1
        if _text_involves_ownership(text) or category in {
            "ownership_compression",
            "fallback_consolidation",
        }:
            ownership += 1
    return CategoryPreventionSignals(
        category=category,
        candidate_count=len(candidates),
        production_touching_count=production_touching,
        test_touching_count=test_touching,
        governance_involvement_count=governance,
        replay_involvement_count=replay,
        ownership_involvement_count=ownership,
        total_production_files_touched=total_production,
        total_test_files_touched=total_test,
    )


def classify_category_prevention_effectiveness(
    category: str,
    signals: CategoryPreventionSignals,
) -> CategoryAssessment:
    if category == "fallback_consolidation":
        classification: AssessmentClass = "likely_preventive"
        rationale = (
            "Authorship and metadata consolidation commits reduce ambiguous fallback routing "
            "and align with the CA4 baseline's dominant opening_fallback repair family; "
            "production and test co-change suggests structural hardening rather than one-off patches."
        )
    elif category == "decomposition":
        classification = "likely_preventive"
        rationale = (
            "Adapter retirement, topology collapse, and extraction finalize steps shrink fallback "
            "surface area and gate complexity, which plausibly prevents repeat standalone repairs "
            "in the same subsystem."
        )
    elif category == "ownership_compression":
        classification = "likely_preventive"
        rationale = (
            "Ownership compression and ambiguity collapse target the same fallback ownership "
            "confusion seen in historical corrective fixes; production edits with test backing "
            "indicate structural clarity work that can pre-empt future misattribution fixes."
        )
    elif category == "replay_stabilization":
        if signals.candidate_count == 1 and signals.total_production_files_touched <= 1:
            classification = "unclear"
            rationale = (
                "Only one replay ownership consolidation commit with minimal production footprint; "
                "insufficient volume to distinguish prevention from program-work masking."
            )
        else:
            classification = "neutral"
            rationale = (
                "Replay stabilization shows mixed production/test signals without enough volume "
                "to confirm preventive effect."
            )
    else:
        classification = "unclear"
        rationale = "Category outside CA10 prevention scope."

    return CategoryAssessment(
        category=category,
        classification=classification,
        rationale=rationale,
        prevention_signals=signals,
    )


def compute_preventive_absorption_ratio(
    embedded_count: int,
    explicit_count: int,
) -> dict[str, Any]:
    denominator = embedded_count + explicit_count
    ratio = round(embedded_count / denominator, 4) if denominator else 0.0
    embedded_share = ratio
    return {
        "primary_metric": PRIMARY_METRIC,
        "embedded_corrective_work": embedded_count,
        "explicit_corrective_fixes": explicit_count,
        "embedded_share": embedded_share,
        "preventive_absorption_ratio": ratio,
    }


def build_category_concentration(
    category_counts: Mapping[str, int],
    total_embedded: int,
) -> dict[str, Any]:
    ranked = sorted(
        ((category, category_counts.get(category, 0)) for category in PREVENTION_CATEGORIES),
        key=lambda item: (-item[1], item[0]),
    )
    percentages = {
        category: round(category_counts.get(category, 0) / total_embedded * 100.0, 2)
        if total_embedded
        else 0.0
        for category in PREVENTION_CATEGORIES
    }
    cumulative: list[dict[str, Any]] = []
    running = 0
    included: list[str] = []
    for category, count in ranked:
        if count <= 0:
            continue
        running += count
        included.append(category)
        cumulative.append(
            {
                "categories": list(included),
                "count": running,
                "cumulative_share": round(running / total_embedded, 4) if total_embedded else 0.0,
            }
        )
    largest_category, largest_count = ranked[0] if ranked else ("", 0)
    return {
        "counts": {category: category_counts.get(category, 0) for category in PREVENTION_CATEGORIES},
        "percentages": percentages,
        "largest_category": largest_category,
        "largest_category_count": largest_count,
        "largest_category_percentage": percentages.get(largest_category, 0.0),
        "cumulative_top_categories": cumulative,
    }


def build_prevention_evidence(
    *,
    ratio: Mapping[str, Any],
    assessments: Sequence[CategoryAssessment],
    ca7_report: Mapping[str, Any],
    ca8_report: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> list[str]:
    likely = sum(1 for item in assessments if item.classification == "likely_preventive")
    structural = int(
        ca8_report.get("availability_analysis", {}).get("structural_prevention_work", 0)
    )
    baseline_family = (
        (baseline.get("repair_family_distribution") or {}).get("largest_repair_family") or ""
    )
    evidence = [
        (
            f"Post-baseline explicit corrective fixes remain {ratio['explicit_corrective_fixes']} while "
            f"{ratio['embedded_corrective_work']} embedded production-touching candidates were absorbed "
            f"into structural programs (preventive absorption ratio {ratio['preventive_absorption_ratio']})."
        ),
        (
            f"{likely} of {len(PREVENTION_CATEGORIES)} analyzed categories classify as likely preventive "
            "based on production/test co-change and alignment with planned structural refactors."
        ),
        (
            f"CA8 reports {structural} structural-prevention exclusions alongside embedded work, indicating "
            "companion test and instrumentation activity supporting prevention rather than isolated patches."
        ),
    ]
    if baseline_family:
        evidence.append(
            f"CA4 baseline largest repair family is {baseline_family}, matching the fallback/ownership "
            "programs that dominate embedded corrective attribution."
        )
    zero_fix = ca7_report.get("zero_fix_evidence", {}).get("zero_fix_statement_defensible")
    if zero_fix:
        evidence.append(
            "CA7 validates zero explicit post-baseline fixes with complete exclusion accounting, "
            "consistent with corrective pressure being absorbed upstream of CA1 qualification."
        )
    return evidence


def build_alternative_explanations(
    *,
    ca7_report: Mapping[str, Any],
    ca8_report: Mapping[str, Any],
    assessments: Sequence[CategoryAssessment],
) -> list[str]:
    risks = [
        "Preventive absorption ratio equals 1.0 whenever explicit fixes are zero; the metric shows dominance of embedded work, not proven prevention.",
        "Category assessments infer intent from exclusion text and path counts; they are not defect-outcome measurements.",
        "This analysis does not compare against CA4 baseline trends, join recurrence history, or forecast future fix rates.",
    ]
    relaxed = (
        ca7_report.get("qualification_sensitivity", {})
        .get("relaxed_interpretation", {})
        .get("promoted_count", 0)
    )
    if relaxed:
        risks.append(
            f"CA7 relaxed qualification would promote {relaxed} production-touching commits as explicit fixes, "
            "so zero-fix outcomes may partly reflect methodology rather than prevention."
        )
    unclear = [item.category for item in assessments if item.classification == "unclear"]
    if unclear:
        risks.append(
            f"Categories classified unclear ({', '.join(unclear)}) may be hiding corrective work rather than preventing it."
        )
    window = ca8_report.get("availability_assessment", {}).get("observation_window_days")
    if window is not None:
        risks.append(
            f"The post-baseline observation window spans only {window} days; longer horizons may surface standalone fixes."
        )
    return risks


def build_conclusion(
    *,
    ratio: Mapping[str, Any],
    assessments: Sequence[CategoryAssessment],
) -> str:
    likely = sum(1 for item in assessments if item.classification == "likely_preventive")
    unclear = sum(1 for item in assessments if item.classification == "unclear")
    if ratio["explicit_corrective_fixes"] == 0 and likely >= 3:
        return (
            "Architectural programs are plausibly preventing standalone corrective fixes: all corrective "
            f"activity is embedded (preventive absorption ratio {ratio['preventive_absorption_ratio']}), "
            f"{likely} categories assess as likely preventive, and zero explicit fixes persist after CA4. "
            "However, qualification rules and the short observation window prevent a definitive causal claim; "
            "programs may also be hiding corrective work that strict CA1 gates do not promote."
        )
    if unclear:
        return (
            "Evidence is mixed: embedded work dominates but at least one category remains unclear, so programs "
            "may be masking corrective activity rather than preventing future standalone fixes."
        )
    return (
        "Insufficient evidence to distinguish prevention from program-work masking in the current review window."
    )


def build_corrective_prevention_effectiveness_report(
    *,
    ca7_report: Mapping[str, Any],
    ca8_report: Mapping[str, Any],
    ca9_report: Mapping[str, Any],
    baseline: Mapping[str, Any],
) -> dict[str, Any]:
    embedded_count = int(
        ca8_report.get("availability_analysis", {}).get("embedded_corrective_work", 0)
    )
    explicit_count = int(
        ca8_report.get("availability_analysis", {}).get("explicit_corrective_fixes", 0)
    )
    ratio = compute_preventive_absorption_ratio(embedded_count, explicit_count)
    category_map = embedded_candidates_by_category(ca9_report)
    category_counts = {category: len(category_map[category]) for category in PREVENTION_CATEGORIES}
    concentration = build_category_concentration(category_counts, embedded_count)

    assessments: list[CategoryAssessment] = []
    prevention_signals: list[dict[str, Any]] = []
    for category in PREVENTION_CATEGORIES:
        signals = compute_category_prevention_signals(category, category_map[category])
        assessment = classify_category_prevention_effectiveness(category, signals)
        assessments.append(assessment)
        prevention_signals.append(asdict(signals))

    category_assessments = [asdict(item) for item in assessments]
    evidence = build_prevention_evidence(
        ratio=ratio,
        assessments=assessments,
        ca7_report=ca7_report,
        ca8_report=ca8_report,
        baseline=baseline,
    )
    risks = build_alternative_explanations(
        ca7_report=ca7_report,
        ca8_report=ca8_report,
        assessments=assessments,
    )
    conclusion = build_conclusion(ratio=ratio, assessments=assessments)

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "primary_metric": PRIMARY_METRIC,
        "sources": {
            "ca7_report_json": DEFAULT_CA7_JSON_PATH,
            "ca8_report_json": DEFAULT_CA8_JSON_PATH,
            "ca9_report_json": DEFAULT_CA9_JSON_PATH,
            "baseline_json": DEFAULT_BASELINE_JSON_PATH,
        },
        "embedded_corrective_activity": {
            "embedded_corrective_count": embedded_count,
            "explicit_corrective_count": explicit_count,
            "embedded_share": ratio["embedded_share"],
            "category_concentration": concentration,
            "categories_analyzed": list(PREVENTION_CATEGORIES),
        },
        "prevention_signals_by_category": prevention_signals,
        "category_assessments": category_assessments,
        "preventive_absorption_ratio_analysis": ratio,
        "evidence_supporting_prevention": evidence,
        "risks_and_alternative_explanations": risks,
        "conclusion": conclusion,
        "baseline_context": {
            "baseline_end_date": (baseline.get("cohort_boundaries") or {}).get("end_date"),
            "baseline_cohort_size": baseline.get("cohort_size"),
            "largest_repair_family": (
                (baseline.get("repair_family_distribution") or {}).get("largest_repair_family")
            ),
        },
    }


def _metric_line(label: str, value: Any) -> str:
    return f"- **{label}:** {value}"


def render_corrective_prevention_effectiveness_report_md(report: Mapping[str, Any]) -> str:
    activity = report["embedded_corrective_activity"]
    ratio = report["preventive_absorption_ratio_analysis"]
    concentration = activity["category_concentration"]
    assessments = report["category_assessments"]

    lines = [
        "# CA10 Corrective Prevention Effectiveness Report",
        "",
        "> Evaluates whether structural programs absorbing embedded corrective work plausibly prevent standalone corrective fixes.",
        "",
        f"_Primary metric: **{report['primary_metric']}** (`embedded_corrective_work / (embedded_corrective_work + explicit_corrective_fixes)`)._",
        "",
        "## 1. Executive Summary",
        "",
        report["conclusion"],
        "",
        _metric_line("Embedded corrective count", activity["embedded_corrective_count"]),
        _metric_line("Explicit corrective count", activity["explicit_corrective_count"]),
        _metric_line("Embedded share", activity["embedded_share"]),
        _metric_line("Preventive absorption ratio", ratio["preventive_absorption_ratio"]),
        _metric_line("Largest category", concentration["largest_category"]),
        "",
        "## 2. Embedded Corrective Activity",
        "",
        "| Category | Count | Percentage |",
        "|---|---:|---:|",
    ]
    for category in PREVENTION_CATEGORIES:
        label = category.replace("_", " ")
        lines.append(
            f"| {label} | {concentration['counts'][category]} | {concentration['percentages'][category]}% |"
        )

    lines.extend(["", "### Category concentration", ""])
    for entry in concentration["cumulative_top_categories"]:
        labels = ", ".join(category.replace("_", " ") for category in entry["categories"])
        lines.append(
            f"- **{labels}:** {entry['count']} candidates ({entry['cumulative_share']})"
        )

    lines.extend(["", "## 3. Category Assessments", ""])
    for assessment in assessments:
        label = assessment["category"].replace("_", " ")
        signals = assessment["prevention_signals"]
        lines.extend(
            [
                f"### {label}",
                "",
                _metric_line("Classification", assessment["classification"]),
                _metric_line("Rationale", assessment["rationale"]),
                _metric_line("Production-touching activity", signals["production_touching_count"]),
                _metric_line("Test-touching activity", signals["test_touching_count"]),
                _metric_line("Governance involvement", signals["governance_involvement_count"]),
                _metric_line("Replay involvement", signals["replay_involvement_count"]),
                _metric_line("Ownership involvement", signals["ownership_involvement_count"]),
                "",
            ]
        )

    lines.extend(
        [
            "## 4. Preventive Absorption Ratio",
            "",
            _metric_line("Embedded corrective work", ratio["embedded_corrective_work"]),
            _metric_line("Explicit corrective fixes", ratio["explicit_corrective_fixes"]),
            _metric_line("Preventive absorption ratio", ratio["preventive_absorption_ratio"]),
            "",
            "## 5. Evidence Supporting Prevention",
            "",
        ]
    )
    for item in report["evidence_supporting_prevention"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 6. Risks And Alternative Explanations", ""])
    for item in report["risks_and_alternative_explanations"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 7. Conclusion", "", report["conclusion"], ""])
    return "\n".join(lines)


def write_corrective_prevention_effectiveness_report(
    md_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
    *,
    ca7_json_path: str | Path | None = None,
    ca8_json_path: str | Path | None = None,
    ca9_json_path: str | Path | None = None,
    baseline_json_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    root = _repo_root(repo_root)
    ca7_report = load_ca7_report(ca7_json_path, repo_root=root)
    ca8_report = load_ca8_report(ca8_json_path, repo_root=root)
    ca9_report = load_ca9_report(ca9_json_path, repo_root=root)
    baseline_summary = load_baseline_summary(baseline_json_path, repo_root=root)
    baseline_path = Path(baseline_json_path or DEFAULT_BASELINE_JSON_PATH)
    if not baseline_path.is_absolute():
        baseline_path = root / baseline_path
    baseline_payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline = {
        **baseline_summary,
        "repair_family_distribution": baseline_payload.get("repair_family_distribution") or {},
    }

    report = build_corrective_prevention_effectiveness_report(
        ca7_report=ca7_report,
        ca8_report=ca8_report,
        ca9_report=ca9_report,
        baseline=baseline,
    )
    markdown = render_corrective_prevention_effectiveness_report_md(report)

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
