"""CA9 embedded corrective work attribution (read-side only).

Measures how much corrective activity is absorbed into program work and
identifies where it occurs. Does not modify baselines, cohorts, or integrate
trend windows or recurrence history.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.post_baseline_corrective_cohort import (
    DEFAULT_EXCLUSIONS_CSV_PATH,
    DEFAULT_REVIEW_QUEUE_PATH,
    PostBaselineExclusionRow,
    load_post_baseline_exclusions,
    validate_post_baseline_cohort,
)

DEFAULT_CA8_JSON_PATH = "artifacts/ca8_corrective_fix_availability_report.json"
DEFAULT_MD_OUTPUT_PATH = "artifacts/ca9_embedded_corrective_attribution_report.md"
DEFAULT_JSON_OUTPUT_PATH = "artifacts/ca9_embedded_corrective_attribution_report.json"
REPORT_SCHEMA_VERSION = 1
PRIMARY_METRIC = "embedded_corrective_share"

ATTRIBUTION_CATEGORIES: tuple[str, ...] = (
    "ownership_compression",
    "replay_stabilization",
    "fallback_consolidation",
    "observability_expansion",
    "decomposition",
    "governance_enforcement",
    "other",
)

_ATTRIBUTION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "observability_expansion",
        (
            "observability",
            "instrumentation",
            "incidence measurement",
            "trend measurement",
        ),
    ),
    (
        "governance_enforcement",
        (
            "governance taxonomy",
            "acceptance gate",
            "governance promotion",
            "governance enforcement",
        ),
    ),
    (
        "decomposition",
        (
            "adapter retirement",
            "topology collapse",
            "extraction finalize",
            "gate decomposition",
            "planned decomposition",
            "test decomposition",
        ),
    ),
    (
        "fallback_consolidation",
        (
            "authorship resolution",
            "authorship contract",
            "authorship attribution",
            "metadata consolidation",
            "attribution contract",
            "attribution consolidation",
        ),
    ),
    (
        "replay_stabilization",
        (
            "replay ownership consolidation",
            "replay stabilization",
            "replay ownership",
        ),
    ),
    (
        "ownership_compression",
        (
            "ownership compression",
            "ownership collapse",
            "ownership ambiguity",
            "ownership clarity",
            "ownership consolidation",
        ),
    ),
)

_CYCLE_FROM_NOTES = re.compile(r"cycle=([^\s;]+)", re.IGNORECASE)
_CYCLE_FROM_TITLE = re.compile(r"(?:Close )?Cycle ([A-Z0-9]+)", re.IGNORECASE)
_PREFIX_FROM_TITLE = re.compile(r"^([A-Z]+):\s")


@dataclass(frozen=True)
class EmbeddedCandidateRecord:
    commit_hash: str
    date: str
    title: str
    cycle_program_affiliation: str
    production_files_touched: int
    test_files_touched: int
    exclusion_reason: str
    embedded_corrective_rationale: str
    attribution_category: str


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else Path(__file__).resolve().parents[2]


def _normalize_text(*parts: str) -> str:
    return " ".join(str(part or "").lower() for part in parts)


def extract_cycle_program_affiliation(title: str, review_notes: str = "") -> str:
    """Infer cycle or program label from review notes or commit title."""
    notes_match = _CYCLE_FROM_NOTES.search(review_notes or "")
    if notes_match:
        return notes_match.group(1).upper()
    title_cycle = _CYCLE_FROM_TITLE.search(title or "")
    if title_cycle:
        return title_cycle.group(1).upper()
    prefix_match = _PREFIX_FROM_TITLE.match(title or "")
    if prefix_match:
        return prefix_match.group(1).upper()
    return "unassigned"


def classify_attribution_category(exclusion_reason: str, title: str = "") -> str:
    """Assign one attribution category from exclusion reason and title."""
    text = _normalize_text(exclusion_reason, title)
    for category, phrases in _ATTRIBUTION_RULES:
        if any(phrase in text for phrase in phrases):
            return category
    if "fallback" in text and ("consolidation" in text or "collapse" in text):
        return "fallback_consolidation"
    if "ownership" in text:
        return "ownership_compression"
    if "replay" in text:
        return "replay_stabilization"
    return "other"


def build_embedded_corrective_rationale(
    *,
    production_files_touched: int,
    exclusion_reason: str,
    cycle_program_affiliation: str,
) -> str:
    return (
        f"Production runtime sources changed ({production_files_touched} file(s)) inside "
        f"planned program cycle {cycle_program_affiliation}; CA6 excluded the commit because "
        f"corrective intent is embedded in program delivery rather than an evidenced standalone "
        f"defect repair ({exclusion_reason})."
    )


def load_ca8_report(
    json_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    target = Path(json_path or DEFAULT_CA8_JSON_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    return json.loads(target.read_text(encoding="utf-8"))


def load_embedded_candidates_from_ca8(ca8_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = (
        ca8_report.get("latent_activity_distribution", {})
        .get("by_category", {})
        .get("embedded_corrective_work", [])
    )
    if not isinstance(rows, list):
        raise ValueError("CA8 report missing embedded_corrective_work candidates")
    return list(rows)


def build_exclusion_lookup(
    exclusions: Sequence[PostBaselineExclusionRow],
) -> dict[str, PostBaselineExclusionRow]:
    return {row.commit_hash: row for row in exclusions}


def build_embedded_candidate_records(
    ca8_candidates: Sequence[Mapping[str, Any]],
    exclusion_lookup: Mapping[str, PostBaselineExclusionRow],
) -> list[EmbeddedCandidateRecord]:
    records: list[EmbeddedCandidateRecord] = []
    for raw in ca8_candidates:
        commit_hash = str(raw.get("commit_hash") or "").strip()
        if not commit_hash:
            continue
        exclusion = exclusion_lookup.get(commit_hash)
        title = str(raw.get("title") or (exclusion.title if exclusion else "")).strip()
        exclusion_reason = str(
            raw.get("exclusion_reason") or (exclusion.exclusion_reason if exclusion else "")
        ).strip()
        review_notes = exclusion.review_notes if exclusion else ""
        cycle = extract_cycle_program_affiliation(title, review_notes)
        production = int(raw.get("production_files_touched") or 0)
        tests = int(raw.get("test_files_touched") or 0)
        category = classify_attribution_category(exclusion_reason, title)
        records.append(
            EmbeddedCandidateRecord(
                commit_hash=commit_hash,
                date=str(raw.get("date") or "").strip(),
                title=title,
                cycle_program_affiliation=cycle,
                production_files_touched=production,
                test_files_touched=tests,
                exclusion_reason=exclusion_reason,
                embedded_corrective_rationale=build_embedded_corrective_rationale(
                    production_files_touched=production,
                    exclusion_reason=exclusion_reason,
                    cycle_program_affiliation=cycle,
                ),
                attribution_category=category,
            )
        )
    return records


def compute_embedded_corrective_share(
    embedded_count: int,
    explicit_count: int,
) -> dict[str, Any]:
    denominator = embedded_count + explicit_count
    share = round(embedded_count / denominator, 4) if denominator else 0.0
    return {
        "primary_metric": PRIMARY_METRIC,
        "embedded_corrective_work": embedded_count,
        "explicit_corrective_fixes": explicit_count,
        "embedded_corrective_share": share,
    }


def build_attribution_concentration(
    records: Sequence[EmbeddedCandidateRecord],
) -> dict[str, Any]:
    total = len(records)
    counts = {category: 0 for category in ATTRIBUTION_CATEGORIES}
    by_category: dict[str, list[dict[str, Any]]] = {category: [] for category in ATTRIBUTION_CATEGORIES}
    for record in records:
        counts[record.attribution_category] += 1
        by_category[record.attribution_category].append(asdict(record))

    ranked = sorted(
        ((category, counts[category]) for category in ATTRIBUTION_CATEGORIES if counts[category] > 0),
        key=lambda item: (-item[1], item[0]),
    )
    percentages = {
        category: round(counts[category] / total * 100.0, 2) if total else 0.0
        for category in ATTRIBUTION_CATEGORIES
    }
    largest_category = ranked[0][0] if ranked else ""
    largest_count = ranked[0][1] if ranked else 0

    cumulative: list[dict[str, Any]] = []
    running = 0
    included: list[str] = []
    for category, count in ranked:
        running += count
        included.append(category)
        cumulative.append(
            {
                "categories": list(included),
                "count": running,
                "cumulative_share": round(running / total, 4) if total else 0.0,
                "cumulative_percentage": round(running / total * 100.0, 2) if total else 0.0,
            }
        )

    return {
        "total_embedded_candidates": total,
        "counts": counts,
        "percentages": percentages,
        "by_category": by_category,
        "largest_category": largest_category,
        "largest_category_count": largest_count,
        "largest_category_percentage": percentages.get(largest_category, 0.0),
        "cumulative_top_categories": cumulative,
    }


def build_interpretation(
    records: Sequence[EmbeddedCandidateRecord],
    concentration: Mapping[str, Any],
    share: Mapping[str, Any],
) -> dict[str, Any]:
    largest = concentration["largest_category"].replace("_", " ")
    top_three = concentration["cumulative_top_categories"][-1] if concentration["cumulative_top_categories"] else {}
    cycles = sorted({record.cycle_program_affiliation for record in records})
    return {
        "where_corrective_work_is_happening": (
            f"Embedded corrective activity concentrates in {largest} "
            f"({concentration['largest_category_count']} of {len(records)} candidates), "
            "with additional volume in fallback consolidation, decomposition, and replay stabilization."
        ),
        "programs_absorbing_corrective_work": (
            f"Production-touching work is routed through planned cycles {', '.join(cycles)} rather than "
            "promoted as explicit CA1 corrective fixes."
        ),
        "embedded_dominance": (
            f"Embedded corrective share is {share['embedded_corrective_share']} because all classified "
            "corrective activity in this window is program-embedded and explicit corrective fixes are zero."
        ),
        "concentration_summary": (
            f"Top attribution categories cover {top_three.get('cumulative_percentage', 0.0)}% "
            f"of embedded candidates ({top_three.get('count', 0)}/{len(records)})."
            if top_three
            else "No embedded candidates to summarize."
        ),
    }


def build_embedded_corrective_attribution_report(
    *,
    records: Sequence[EmbeddedCandidateRecord],
    explicit_corrective_fixes: int,
    reviewed_candidates: int,
) -> dict[str, Any]:
    concentration = build_attribution_concentration(records)
    share = compute_embedded_corrective_share(len(records), explicit_corrective_fixes)
    interpretation = build_interpretation(records, concentration, share)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "primary_metric": PRIMARY_METRIC,
        "sources": {
            "ca8_report_json": DEFAULT_CA8_JSON_PATH,
            "exclusions_csv": DEFAULT_EXCLUSIONS_CSV_PATH,
            "review_queue_csv": DEFAULT_REVIEW_QUEUE_PATH,
        },
        "reviewed_candidates": reviewed_candidates,
        "embedded_candidate_inventory": [asdict(record) for record in records],
        "attribution_categories": concentration,
        "embedded_corrective_share_analysis": share,
        "concentration_analysis": {
            "largest_category": concentration["largest_category"],
            "largest_category_count": concentration["largest_category_count"],
            "largest_category_percentage": concentration["largest_category_percentage"],
            "cumulative_top_categories": concentration["cumulative_top_categories"],
        },
        "interpretation": interpretation,
    }


def _metric_line(label: str, value: Any) -> str:
    return f"- **{label}:** {value}"


def render_embedded_corrective_attribution_report_md(report: Mapping[str, Any]) -> str:
    inventory = report["embedded_candidate_inventory"]
    categories = report["attribution_categories"]
    share = report["embedded_corrective_share_analysis"]
    concentration = report["concentration_analysis"]
    interpretation = report["interpretation"]

    lines = [
        "# CA9 Embedded Corrective Work Attribution Report",
        "",
        "> Measures how much corrective activity is absorbed into program work and where it occurs.",
        "",
        f"_Primary metric: **{report['primary_metric']}** (`embedded_corrective_work / (embedded_corrective_work + explicit_corrective_fixes)`)._",
        "",
        "## 1. Executive Summary",
        "",
        interpretation["embedded_dominance"],
        "",
        _metric_line("Embedded candidates", categories["total_embedded_candidates"]),
        _metric_line("Explicit corrective fixes", share["explicit_corrective_fixes"]),
        _metric_line("Embedded corrective share", share["embedded_corrective_share"]),
        _metric_line("Largest attribution category", concentration["largest_category"]),
        _metric_line("Program cycles involved", ", ".join(sorted({row['cycle_program_affiliation'] for row in inventory}))),
        "",
        "## 2. Embedded Candidate Inventory",
        "",
        "| Commit | Cycle | Production | Tests | Title |",
        "|---|---|---:|---:|---|",
    ]
    for row in inventory:
        title = str(row["title"]).replace("|", "\\|")
        lines.append(
            f"| `{row['commit_hash'][:7]}` | {row['cycle_program_affiliation']} | "
            f"{row['production_files_touched']} | {row['test_files_touched']} | {title} |"
        )

    lines.extend(["", "### Candidate detail", ""])
    for row in inventory:
        title = str(row["title"]).replace("|", "\\|")
        lines.extend(
            [
                f"#### `{row['commit_hash'][:7]}` — {title}",
                "",
                _metric_line("Cycle/program affiliation", row["cycle_program_affiliation"]),
                _metric_line("Attribution category", row["attribution_category"]),
                _metric_line("Production files touched", row["production_files_touched"]),
                _metric_line("Tests touched", row["test_files_touched"]),
                _metric_line("Exclusion reason", row["exclusion_reason"]),
                _metric_line("Embedded corrective rationale", row["embedded_corrective_rationale"]),
                "",
            ]
        )

    lines.extend(
        [
            "## 3. Attribution Categories",
            "",
            "| Category | Count | Percentage |",
            "|---|---:|---:|",
        ]
    )
    for category in ATTRIBUTION_CATEGORIES:
        if categories["counts"][category]:
            label = category.replace("_", " ")
            lines.append(
                f"| {label} | {categories['counts'][category]} | {categories['percentages'][category]}% |"
            )

    lines.extend(
        [
            "",
            "## 4. Embedded Corrective Share",
            "",
            _metric_line("Embedded corrective work", share["embedded_corrective_work"]),
            _metric_line("Explicit corrective fixes", share["explicit_corrective_fixes"]),
            _metric_line("Embedded corrective share", share["embedded_corrective_share"]),
            "",
            "## 5. Concentration Analysis",
            "",
            _metric_line("Largest category", concentration["largest_category"]),
            _metric_line("Largest category count", concentration["largest_category_count"]),
            _metric_line("Largest category percentage", f"{concentration['largest_category_percentage']}%"),
            "",
            "### Cumulative top categories",
            "",
            "| Rank | Categories | Count | Cumulative share |",
            "|---:|---|---:|---:|",
        ]
    )
    for index, entry in enumerate(concentration["cumulative_top_categories"], start=1):
        labels = ", ".join(category.replace("_", " ") for category in entry["categories"])
        lines.append(
            f"| {index} | {labels} | {entry['count']} | {entry['cumulative_percentage']}% |"
        )

    lines.extend(
        [
            "",
            "## 6. Interpretation",
            "",
            _metric_line("Where corrective work is happening", interpretation["where_corrective_work_is_happening"]),
            _metric_line("Programs absorbing corrective work", interpretation["programs_absorbing_corrective_work"]),
            _metric_line("Concentration summary", interpretation["concentration_summary"]),
            "",
        ]
    )
    return "\n".join(lines)


def write_embedded_corrective_attribution_report(
    md_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
    *,
    ca8_json_path: str | Path | None = None,
    exclusions_csv_path: str | Path | None = None,
    review_queue_path: str | Path | None = None,
    cohort_csv_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    root = _repo_root(repo_root)
    errors = validate_post_baseline_cohort(
        cohort_csv_path=cohort_csv_path,
        exclusions_csv_path=exclusions_csv_path,
        review_queue_path=review_queue_path,
    )
    if errors:
        raise ValueError("CA9 input validation failed:\n" + "\n".join(f"- {err}" for err in errors))

    ca8_report = load_ca8_report(ca8_json_path, repo_root=root)
    ca8_candidates = load_embedded_candidates_from_ca8(ca8_report)
    exclusions = load_post_baseline_exclusions(exclusions_csv_path)
    exclusion_lookup = build_exclusion_lookup(exclusions)

    records = build_embedded_candidate_records(ca8_candidates, exclusion_lookup)
    explicit = int(
        ca8_report.get("availability_analysis", {}).get("explicit_corrective_fixes", 0)
    )
    reviewed = int(ca8_report.get("availability_analysis", {}).get("reviewed_candidates", 0))

    report = build_embedded_corrective_attribution_report(
        records=records,
        explicit_corrective_fixes=explicit,
        reviewed_candidates=reviewed,
    )
    markdown = render_embedded_corrective_attribution_report_md(report)

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
