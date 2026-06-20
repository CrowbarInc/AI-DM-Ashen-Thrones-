"""BRL1 bug-fix locality repository metric (read-side reporting only).

Consumes the BR commit classification CSV and optional git path inventories for
hotspot analysis. Does not modify runtime behavior, ownership, replacement, or
attribution systems.
"""
from __future__ import annotations

import csv
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Mapping, Sequence

DEFAULT_CSV_PATH = "docs/reports/BR_commit_classification.csv"
DEFAULT_OUTPUT_PATH = "artifacts/bug_fix_locality_report.md"

CATEGORY_BUG_FIX = "bug_fix"
CATEGORY_REFACTOR = "refactor_architecture"
CATEGORY_GOVERNANCE = "governance_observability"
CATEGORY_FEATURE = "feature_work"

# Frozen baseline from BR discovery through 3f5ee0c (2026-06-20).
BRL1_BASELINE_LOCALITY: dict[str, dict[str, Any]] = {
    CATEGORY_BUG_FIX: {
        "commit_count": 11,
        "median_files_touched": 9.0,
        "p75_files_touched": 36.0,
        "p90_files_touched": 216.0,
        "max_files_touched": 538,
        "median_production_files_touched": 5.0,
        "locality_score": 11.11,
    },
    CATEGORY_REFACTOR: {
        "commit_count": 101,
        "median_files_touched": 16.0,
        "p75_files_touched": 23.0,
        "p90_files_touched": 41.0,
        "max_files_touched": 1407,
        "median_production_files_touched": 3.0,
        "locality_score": 6.25,
    },
    CATEGORY_GOVERNANCE: {
        "commit_count": 36,
        "median_files_touched": 16.0,
        "p75_files_touched": 24.0,
        "p90_files_touched": 47.5,
        "max_files_touched": 140,
        "median_production_files_touched": 1.0,
        "locality_score": 6.25,
    },
    CATEGORY_FEATURE: {
        "commit_count": 44,
        "median_files_touched": 14.0,
        "p75_files_touched": 17.0,
        "p90_files_touched": 21.0,
        "max_files_touched": 25,
        "median_production_files_touched": 7.5,
        "locality_score": 7.14,
    },
}

DOCS_TOOLING_PREFIXES: tuple[str, ...] = (
    "docs/",
    "audits/",
    "tools/",
    ".github/",
    "artifacts/",
)
DOCS_TOOLING_ROOT_FILES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "pytest.ini",
        "setup.cfg",
        "setup.py",
        "requirements.txt",
        "requirements-dev.txt",
        "Makefile",
        "README.md",
    }
)


@dataclass(frozen=True)
class CommitClassificationRow:
    short_sha: str
    date: str
    subject: str
    category: str
    files_touched_count: int
    production_files_touched_count: int
    test_files_touched_count: int
    docs_tooling_files_touched_count: int
    notes: str


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def classify_changed_path(path: str) -> str:
    """Return path bucket: production, test, or docs_tooling."""
    normalized = _normalize_path(path)
    if not normalized:
        return "docs_tooling"
    name = Path(normalized).name
    if normalized.startswith("tests/"):
        return "test"
    if name.startswith("test_") or name.endswith("_test.py"):
        return "test"
    if "pytest_cache" in normalized or "codex_pytest_tmp" in normalized:
        return "test"
    if normalized.startswith(DOCS_TOOLING_PREFIXES):
        return "docs_tooling"
    if normalized.endswith(".md") or normalized.endswith(".txt"):
        return "docs_tooling"
    if normalized in DOCS_TOOLING_ROOT_FILES:
        return "docs_tooling"
    return "production"


def path_cluster(path: str) -> str:
    """Return a coarse directory cluster for hotspot grouping."""
    normalized = _normalize_path(path)
    parts = [part for part in normalized.split("/") if part]
    if not parts:
        return "<root>"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]}/{parts[1]}"


def load_commit_classification_rows(
    csv_path: str | Path | None = None,
) -> list[CommitClassificationRow]:
    """Load BR commit classification CSV rows."""
    target = Path(csv_path or DEFAULT_CSV_PATH)
    rows: list[CommitClassificationRow] = []
    with target.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            rows.append(
                CommitClassificationRow(
                    short_sha=str(raw["short_sha"]).strip(),
                    date=str(raw["date"]).strip(),
                    subject=str(raw["subject"]).strip(),
                    category=str(raw["category"]).strip(),
                    files_touched_count=int(raw["files_touched_count"]),
                    production_files_touched_count=int(raw["production_files_touched_count"]),
                    test_files_touched_count=int(raw["test_files_touched_count"]),
                    docs_tooling_files_touched_count=int(raw["docs_tooling_files_touched_count"]),
                    notes=str(raw.get("notes") or "").strip(),
                )
            )
    return rows


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


def _locality_score(median_files_touched: float) -> float:
    """Higher score means more local (fewer files touched)."""
    return round(100.0 / max(median_files_touched, 1.0), 2)


def _distribution_stats(values: Sequence[int]) -> dict[str, Any]:
    if not values:
        return {
            "commit_count": 0,
            "median_files_touched": 0.0,
            "p75_files_touched": 0.0,
            "p90_files_touched": 0.0,
            "max_files_touched": 0,
            "median_production_files_touched": 0.0,
            "locality_score": 0.0,
        }
    return {
        "commit_count": len(values),
        "median_files_touched": float(median(values)),
        "p75_files_touched": _percentile(values, 75),
        "p90_files_touched": _percentile(values, 90),
        "max_files_touched": max(values),
        "locality_score": _locality_score(float(median(values))),
    }


def _distribution_stats_for_category(
    rows: Sequence[CommitClassificationRow],
    category: str,
) -> dict[str, Any]:
    category_rows = [row for row in rows if row.category == category]
    file_counts = [row.files_touched_count for row in category_rows]
    production_counts = [row.production_files_touched_count for row in category_rows]
    stats = _distribution_stats(file_counts)
    stats["median_production_files_touched"] = float(median(production_counts)) if production_counts else 0.0
    return stats


def _trend_block(
    *,
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
    keys: Sequence[str],
) -> dict[str, dict[str, Any]]:
    trend: dict[str, dict[str, Any]] = {}
    for key in keys:
        baseline_value = baseline.get(key)
        current_value = current.get(key)
        delta = None
        if isinstance(baseline_value, (int, float)) and isinstance(current_value, (int, float)):
            delta = round(float(current_value) - float(baseline_value), 2)
        trend[key] = {
            "baseline": baseline_value,
            "current": current_value,
            "delta": delta,
        }
    return trend


def _git_changed_paths(short_sha: str, *, repo_root: Path | None = None) -> list[str]:
    root = repo_root or Path.cwd()
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", short_sha],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [_normalize_path(line) for line in result.stdout.splitlines() if line.strip()]


def _hotspot_analysis(
    rows: Sequence[CommitClassificationRow],
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    file_touch_counts: Counter[str] = Counter()
    bug_fix_cluster_counts: Counter[str] = Counter()
    refactor_cluster_counts: Counter[str] = Counter()
    category_file_touches: dict[str, Counter[str]] = {
        CATEGORY_BUG_FIX: Counter(),
        CATEGORY_REFACTOR: Counter(),
    }

    for row in rows:
        if row.category not in {CATEGORY_BUG_FIX, CATEGORY_REFACTOR, CATEGORY_GOVERNANCE, CATEGORY_FEATURE}:
            continue
        changed_paths = _git_changed_paths(row.short_sha, repo_root=repo_root)
        if not changed_paths:
            continue
        for path in changed_paths:
            file_touch_counts[path] += 1
            if row.category in category_file_touches:
                category_file_touches[row.category][path] += 1
            if classify_changed_path(path) != "production":
                continue
            cluster = path_cluster(path)
            if row.category == CATEGORY_BUG_FIX:
                bug_fix_cluster_counts[cluster] += 1
            elif row.category == CATEGORY_REFACTOR:
                refactor_cluster_counts[cluster] += 1

    def _concentration(counter: Counter[str]) -> dict[str, Any]:
        total = sum(counter.values())
        if total == 0:
            return {"top5_share_pct": 0.0, "top_file_share_pct": 0.0, "distinct_paths": 0}
        top5 = sum(count for _, count in counter.most_common(5))
        top1 = counter.most_common(1)[0][1]
        return {
            "top5_share_pct": round(100.0 * top5 / total, 2),
            "top_file_share_pct": round(100.0 * top1 / total, 2),
            "distinct_paths": len(counter),
        }

    bug_fix_cluster_total = sum(bug_fix_cluster_counts.values())
    refactor_cluster_total = sum(refactor_cluster_counts.values())
    bug_top_cluster, bug_top_cluster_count = (
        bug_fix_cluster_counts.most_common(1)[0] if bug_fix_cluster_counts else (None, 0)
    )
    refactor_top_cluster, refactor_top_cluster_count = (
        refactor_cluster_counts.most_common(1)[0] if refactor_cluster_counts else (None, 0)
    )

    return {
        "most_frequently_touched_files": file_touch_counts.most_common(10),
        "bug_fix_clusters": bug_fix_cluster_counts.most_common(10),
        "refactor_clusters": refactor_cluster_counts.most_common(10),
        "maintenance_concentration": {
            CATEGORY_BUG_FIX: _concentration(category_file_touches[CATEGORY_BUG_FIX]),
            CATEGORY_REFACTOR: _concentration(category_file_touches[CATEGORY_REFACTOR]),
        },
        "hotspot_concentration": {
            CATEGORY_BUG_FIX: {
                "top_cluster": bug_top_cluster,
                "top_cluster_share_pct": round(
                    100.0 * bug_top_cluster_count / bug_fix_cluster_total,
                    2,
                )
                if bug_fix_cluster_total
                else 0.0,
            },
            CATEGORY_REFACTOR: {
                "top_cluster": refactor_top_cluster,
                "top_cluster_share_pct": round(
                    100.0 * refactor_top_cluster_count / refactor_cluster_total,
                    2,
                )
                if refactor_cluster_total
                else 0.0,
            },
        },
    }


def build_bug_fix_locality_report(
    *,
    csv_path: str | Path | None = None,
    repo_root: Path | None = None,
    include_hotspots: bool = True,
) -> dict[str, Any]:
    """Build structured BRL1 bug-fix locality metric payload."""
    target_csv = Path(csv_path or DEFAULT_CSV_PATH)
    try:
        root = (repo_root or Path.cwd()).resolve()
        source_csv = str(target_csv.resolve().relative_to(root))
    except ValueError:
        source_csv = str(target_csv)
    rows = load_commit_classification_rows(target_csv)
    current = {
        CATEGORY_BUG_FIX: _distribution_stats_for_category(rows, CATEGORY_BUG_FIX),
        CATEGORY_REFACTOR: _distribution_stats_for_category(rows, CATEGORY_REFACTOR),
        CATEGORY_GOVERNANCE: _distribution_stats_for_category(rows, CATEGORY_GOVERNANCE),
        CATEGORY_FEATURE: _distribution_stats_for_category(rows, CATEGORY_FEATURE),
    }
    baseline = dict(BRL1_BASELINE_LOCALITY)

    metric_keys = (
        "commit_count",
        "median_files_touched",
        "p75_files_touched",
        "p90_files_touched",
        "max_files_touched",
        "locality_score",
    )
    trend = {
        category: _trend_block(baseline=baseline[category], current=current[category], keys=metric_keys)
        for category in current
    }

    economics = {
        "bug_fix_locality_score": current[CATEGORY_BUG_FIX]["locality_score"],
        "refactor_locality_score": current[CATEGORY_REFACTOR]["locality_score"],
        "governance_locality_score": current[CATEGORY_GOVERNANCE]["locality_score"],
        "feature_locality_score": current[CATEGORY_FEATURE]["locality_score"],
        "score_trend": {
            CATEGORY_BUG_FIX: _trend_block(
                baseline=baseline[CATEGORY_BUG_FIX],
                current=current[CATEGORY_BUG_FIX],
                keys=("locality_score",),
            )["locality_score"],
            CATEGORY_REFACTOR: _trend_block(
                baseline=baseline[CATEGORY_REFACTOR],
                current=current[CATEGORY_REFACTOR],
                keys=("locality_score",),
            )["locality_score"],
        },
    }

    report: dict[str, Any] = {
        "schema_version": 1,
        "source_csv": source_csv,
        "total_commits": len(rows),
        "baseline": baseline,
        "current": current,
        "trend": trend,
        "economics": economics,
    }
    if include_hotspots:
        report["hotspots"] = _hotspot_analysis(rows, repo_root=repo_root)
    return report


def _render_distribution_section(
    *,
    title: str,
    category: str,
    report: Mapping[str, Any],
    include_percentiles: bool,
) -> list[str]:
    trend = report["trend"][category]
    lines = [f"## {title}", ""]
    if include_percentiles:
        lines.extend(
            [
                "| Metric | Baseline | Current | Delta |",
                "|---|---:|---:|---:|",
            ]
        )
        for key, label in (
            ("median_files_touched", "Median files touched"),
            ("p75_files_touched", "P75 files touched"),
            ("p90_files_touched", "P90 files touched"),
            ("max_files_touched", "Max files touched"),
        ):
            block = trend[key]
            delta = block["delta"]
            delta_display = "—" if delta is None else f"{delta:+}"
            lines.append(
                f"| {label} | {block['baseline']} | {block['current']} | {delta_display} |"
            )
    else:
        block = trend["median_files_touched"]
        delta = block["delta"]
        delta_display = "—" if delta is None else f"{delta:+}"
        lines.extend(
            [
                "| Metric | Baseline | Current | Delta |",
                "|---|---:|---:|---:|",
                f"| Median files touched | {block['baseline']} | {block['current']} | {delta_display} |",
            ]
        )
    commit_block = trend["commit_count"]
    lines.append(
        f"\n_Commits in cohort: {commit_block['current']} "
        f"(baseline snapshot: {commit_block['baseline']})._"
    )
    lines.append("")
    return lines


def render_bug_fix_locality_report_md(report: Mapping[str, Any]) -> str:
    """Render BRL1 bug-fix locality markdown report."""
    economics = report["economics"]
    hotspots = report.get("hotspots") or {}

    lines = [
        "# Bug-Fix Locality Report",
        "",
        "> BRL1 repository metric — commit cohort locality over the BR classification inventory.",
        "",
        f"_Source: `{report['source_csv']}` ({report['total_commits']} commits)._",
        "",
    ]
    lines.extend(
        _render_distribution_section(
            title="Bug-Fix Locality",
            category=CATEGORY_BUG_FIX,
            report=report,
            include_percentiles=True,
        )
    )
    lines.extend(
        _render_distribution_section(
            title="Refactor Locality",
            category=CATEGORY_REFACTOR,
            report=report,
            include_percentiles=True,
        )
    )
    lines.extend(
        _render_distribution_section(
            title="Governance Locality",
            category=CATEGORY_GOVERNANCE,
            report=report,
            include_percentiles=False,
        )
    )
    lines.extend(
        _render_distribution_section(
            title="Feature Locality",
            category=CATEGORY_FEATURE,
            report=report,
            include_percentiles=False,
        )
    )

    lines.extend(
        [
            "## Repository Economics Summary",
            "",
            "| Score | Baseline | Current | Delta | Interpretation |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for label, key, baseline_key in (
        ("Bug-fix locality score", "bug_fix_locality_score", CATEGORY_BUG_FIX),
        ("Refactor locality score", "refactor_locality_score", CATEGORY_REFACTOR),
    ):
        trend = report["economics"]["score_trend"][baseline_key]
        delta = trend["delta"]
        delta_display = "—" if delta is None else f"{delta:+}"
        interpretation = "Higher is more local (fewer median files touched)."
        lines.append(
            f"| {label} | {trend['baseline']} | {trend['current']} | {delta_display} | {interpretation} |"
        )

    concentration = hotspots.get("maintenance_concentration") or {}
    bug_conc = concentration.get(CATEGORY_BUG_FIX) or {}
    refactor_conc = concentration.get(CATEGORY_REFACTOR) or {}
    lines.extend(
        [
            "",
            "### Maintenance Concentration Indicators",
            "",
            f"- Bug-fix top-5 file touch share: **{bug_conc.get('top5_share_pct', 0.0)}%**",
            f"- Bug-fix top-file touch share: **{bug_conc.get('top_file_share_pct', 0.0)}%**",
            f"- Refactor top-5 file touch share: **{refactor_conc.get('top5_share_pct', 0.0)}%**",
            f"- Distinct bug-fix paths touched: **{bug_conc.get('distinct_paths', 0)}**",
            f"- Distinct refactor paths touched: **{refactor_conc.get('distinct_paths', 0)}**",
            "",
            "## Hotspot Reporting",
            "",
            "### Most Frequently Touched Files",
            "",
        ]
    )
    file_hotspots = hotspots.get("most_frequently_touched_files") or []
    if file_hotspots:
        for path, count in file_hotspots:
            lines.append(f"- `{path}`: {count} commit(s)")
    else:
        lines.append("- _none_")

    lines.extend(["", "### Most Common Bug-Fix Clusters", ""])
    bug_clusters = hotspots.get("bug_fix_clusters") or []
    if bug_clusters:
        for cluster, count in bug_clusters:
            lines.append(f"- `{cluster}`: {count} production touch(es)")
    else:
        lines.append("- _none_")

    lines.extend(["", "### Most Common Refactor Clusters", ""])
    refactor_clusters = hotspots.get("refactor_clusters") or []
    if refactor_clusters:
        for cluster, count in refactor_clusters:
            lines.append(f"- `{cluster}`: {count} production touch(es)")
    else:
        lines.append("- _none_")

    lines.append("")
    return "\n".join(lines)


def write_bug_fix_locality_report(
    output_path: str | Path | None = None,
    *,
    csv_path: str | Path | None = None,
    repo_root: Path | None = None,
    include_hotspots: bool = True,
) -> tuple[dict[str, Any], str]:
    """Generate BRL1 bug-fix locality artifact."""
    report = build_bug_fix_locality_report(
        csv_path=csv_path,
        repo_root=repo_root,
        include_hotspots=include_hotspots,
    )
    markdown = render_bug_fix_locality_report_md(report)
    target = Path(output_path or DEFAULT_OUTPUT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return report, markdown
