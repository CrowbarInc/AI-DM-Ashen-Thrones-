"""CK-GIT hotspot compression report (read-side only).

Deterministic CK-GIT path-touch aggregation and CK-FI supplementary parse
per docs/processes/hotspot_compression_measurement_standard.md (v1).
"""
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

WATCH_START_COMMIT = "85855df"
WATCH_START_COMMIT_FULL = "85855df00ebdee20a33c0ada447c178bf1f49820"
STANDARD_VERSION = 1
T_TOUCH = 3
T_FI = 10
PRIMARY_METRIC = "hotspot_concentration_index"
REPORT_SCHEMA_VERSION = 1

POPULATION_PREFIXES: tuple[str, ...] = ("game/", "tests/", "scripts/")
EXCLUDED_PREFIXES: tuple[str, ...] = (
    "artifacts/",
    "codex_pytest_tmp/",
    "docs/audits/",
    ".pytest_cache/",
)

DEFAULT_JSON_OUTPUT_PATH = "artifacts/ck1_hotspot_compression_report.json"
DEFAULT_MD_OUTPUT_PATH = "artifacts/ck1_hotspot_compression_report.md"
DEFAULT_BU_CSV_PATH = "docs/audits/BU_import_fan_in_fan_out.csv"

GenerationStatus = Literal["success", "error"]
MeasurementReadiness = Literal["empty_window", "measurement_ready", "insufficient_data"]


@dataclass(frozen=True)
class HotspotEntry:
    path: str
    touch_count: int
    share_pct: float


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else Path(__file__).resolve().parents[2]


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def is_ck_git_population_path(path: str) -> bool:
    """Return True when path belongs to CK-GIT population filters."""
    normalized = _normalize_path(path)
    if not normalized.endswith(".py") or normalized.endswith(".bak"):
        return False
    if any(normalized.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    return any(normalized.startswith(prefix) for prefix in POPULATION_PREFIXES)


def aggregate_touches_from_commit_paths(
    commit_paths: Sequence[Sequence[str]],
) -> Counter[str]:
    """Count one touch per commit per population path."""
    touches: Counter[str] = Counter()
    for paths in commit_paths:
        seen_in_commit: set[str] = set()
        for raw_path in paths:
            path = _normalize_path(raw_path)
            if not path or not is_ck_git_population_path(path):
                continue
            if path in seen_in_commit:
                continue
            seen_in_commit.add(path)
            touches[path] += 1
    return touches


def rank_hotspots(touches: Mapping[str, int]) -> list[HotspotEntry]:
    """Rank hotspots by descending touch count; tie-break ascending path."""
    total = sum(touches.values())
    ranked_pairs = sorted(touches.items(), key=lambda item: (-item[1], item[0]))
    entries: list[HotspotEntry] = []
    for path, count in ranked_pairs:
        share = round(100.0 * count / total, 2) if total else 0.0
        entries.append(HotspotEntry(path=path, touch_count=count, share_pct=share))
    return entries


def compute_concentration_shares(
    ranked: Sequence[HotspotEntry],
    *,
    total_touches: int,
    top_n: int,
) -> float:
    if total_touches <= 0:
        return 0.0
    top_sum = sum(entry.touch_count for entry in ranked[:top_n])
    return round(100.0 * top_sum / total_touches, 2)


def compute_ck_git_metrics(touches: Counter[str]) -> dict[str, Any]:
    ranked = rank_hotspots(touches)
    total_touches = sum(touches.values())
    top5_share_pct = compute_concentration_shares(ranked, total_touches=total_touches, top_n=5)
    top10_share_pct = compute_concentration_shares(ranked, total_touches=total_touches, top_n=10)
    files_above_threshold = sum(1 for count in touches.values() if count >= T_TOUCH)
    largest = ranked[0] if ranked else None
    return {
        "total_touches": total_touches,
        "distinct_paths": len(touches),
        "top5_share_pct": top5_share_pct,
        "top10_share_pct": top10_share_pct,
        "hci": top5_share_pct,
        "t_touch": T_TOUCH,
        "files_above_threshold": files_above_threshold,
        "largest_hotspot": (
            None
            if largest is None
            else {
                "path": largest.path,
                "touch_count": largest.touch_count,
                "share_pct": largest.share_pct,
                "display": f"{largest.path} ({largest.share_pct}%)",
            }
        ),
        "hotspot_rankings": [
            {
                "rank": index + 1,
                "path": entry.path,
                "touch_count": entry.touch_count,
                "share_pct": entry.share_pct,
            }
            for index, entry in enumerate(ranked)
        ],
        "top_10_paths": [
            {
                "path": entry.path,
                "touch_count": entry.touch_count,
                "share_pct": entry.share_pct,
            }
            for entry in ranked[:10]
        ],
    }


def assess_measurement_readiness(
    *,
    total_touches: int,
    commit_count: int,
    watch_start: str,
    measurement_commit: str,
) -> MeasurementReadiness:
    if watch_start == measurement_commit or commit_count == 0:
        return "empty_window"
    if total_touches <= 0:
        return "insufficient_data"
    return "measurement_ready"


def _run_git(
    args: Sequence[str],
    *,
    repo_root: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=check,
    )


def resolve_git_commit(
    commit_ref: str,
    *,
    repo_root: Path,
) -> tuple[str, str]:
    """Return (full_hash, short_hash) for commit_ref."""
    result = _run_git(["git", "rev-parse", commit_ref], repo_root=repo_root)
    full_hash = result.stdout.strip()
    short_result = _run_git(["git", "rev-parse", "--short", full_hash], repo_root=repo_root)
    return full_hash, short_result.stdout.strip()


def git_commit_date(commit_hash: str, *, repo_root: Path) -> str:
    result = _run_git(
        ["git", "log", "-1", "--format=%ad", "--date=short", commit_hash],
        repo_root=repo_root,
    )
    return result.stdout.strip()


def collect_git_commit_paths(
    watch_start: str,
    measurement_commit: str,
    *,
    repo_root: Path,
) -> tuple[list[list[str]], int]:
    """Collect changed paths per commit in REV_RANGE = watch_start..measurement_commit."""
    rev_result = _run_git(
        ["git", "rev-list", f"{watch_start}..{measurement_commit}"],
        repo_root=repo_root,
    )
    shas = [line.strip() for line in rev_result.stdout.splitlines() if line.strip()]
    commit_paths: list[list[str]] = []
    for sha in shas:
        diff_result = _run_git(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", sha],
            repo_root=repo_root,
        )
        paths = [_normalize_path(line) for line in diff_result.stdout.splitlines() if line.strip()]
        commit_paths.append(paths)
    return commit_paths, len(shas)


def parse_ck_fi_metrics(
    csv_path: str | Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    target = Path(csv_path)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    if not target.is_file():
        return {
            "available": False,
            "reason": f"BU CSV not found: {target.as_posix()}",
        }

    rows: list[tuple[str, int]] = []
    with target.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            module = (row.get("module") or "").strip()
            if not module:
                continue
            rows.append((module, int(row.get("fan_in_total") or 0)))

    total_fi = sum(fi for _, fi in rows)
    ranked = sorted(rows, key=lambda item: (-item[1], item[0]))
    top5_share_pct = (
        round(100.0 * sum(fi for _, fi in ranked[:5]) / total_fi, 2) if total_fi else 0.0
    )
    top10_share_pct = (
        round(100.0 * sum(fi for _, fi in ranked[:10]) / total_fi, 2) if total_fi else 0.0
    )
    files_above_threshold = sum(1 for _, fi in ranked if fi >= T_FI)
    largest_module, largest_fi = ranked[0] if ranked else ("", 0)
    largest_share = round(100.0 * largest_fi / total_fi, 2) if total_fi and ranked else 0.0
    notes_string = (
        f"FI top5={top5_share_pct}% top10={top10_share_pct}% above_T10={files_above_threshold}"
    )
    root = _repo_root(repo_root)
    try:
        csv_display_path = target.relative_to(root).as_posix()
    except ValueError:
        csv_display_path = target.as_posix()
    return {
        "available": True,
        "csv_path": csv_display_path,
        "t_fi": T_FI,
        "total_fi": total_fi,
        "distinct_modules": len(ranked),
        "top5_share_pct": top5_share_pct,
        "top10_share_pct": top10_share_pct,
        "files_above_threshold": files_above_threshold,
        "notes_string": notes_string,
        "largest_hotspot": (
            None
            if not ranked
            else {
                "module": largest_module,
                "fan_in_total": largest_fi,
                "share_pct": largest_share,
                "display": f"{largest_module} ({largest_share}%)",
            }
        ),
        "top_10_modules": [
            {"module": module, "fan_in_total": fi, "share_pct": round(100.0 * fi / total_fi, 2) if total_fi else 0.0}
            for module, fi in ranked[:10]
        ],
    }


def format_ck_log_notes(
    *,
    watch_start_short: str,
    measurement_short: str,
    total_touches: int,
    ck_fi: Mapping[str, Any],
    cycle_label: str | None = None,
) -> str:
    rev_range = f"{watch_start_short}..{measurement_short}"
    parts = [f"std=v{STANDARD_VERSION}", f"REV_RANGE={rev_range}", f"total_touches={total_touches}"]
    if ck_fi.get("available"):
        parts.append(str(ck_fi.get("notes_string") or ""))
    if cycle_label:
        parts.append(f"cycle={cycle_label}")
    return "; ".join(parts)


def build_ck_hotspot_compression_report(
    *,
    watch_start_full: str,
    watch_start_short: str,
    measurement_full: str,
    measurement_short: str,
    measurement_date: str,
    commit_paths: Sequence[Sequence[str]],
    commit_count: int,
    ck_fi: Mapping[str, Any],
    cycle_label: str | None = None,
) -> dict[str, Any]:
    touches = aggregate_touches_from_commit_paths(commit_paths)
    ck_git = compute_ck_git_metrics(touches)
    readiness = assess_measurement_readiness(
        total_touches=ck_git["total_touches"],
        commit_count=commit_count,
        watch_start=watch_start_full,
        measurement_commit=measurement_full,
    )
    rev_range = f"{watch_start_short}..{measurement_short}"
    notes = format_ck_log_notes(
        watch_start_short=watch_start_short,
        measurement_short=measurement_short,
        total_touches=ck_git["total_touches"],
        ck_fi=ck_fi,
        cycle_label=cycle_label,
    )
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "primary_metric": PRIMARY_METRIC,
        "standard_version": STANDARD_VERSION,
        "generation_status": "success",
        "measurement_readiness": readiness,
        "data_sufficient": readiness == "measurement_ready",
        "report_provenance": {
            "generator": "tools/ck_hotspot_compression_report.py",
            "helper": "tests/helpers/ck_hotspot_compression_report.py",
            "lane_primary": "CK-GIT",
            "lane_supplementary": "CK-FI",
        },
        "measurement_window": {
            "watch_start_commit": watch_start_short,
            "watch_start_commit_full": watch_start_full,
            "measurement_commit": measurement_short,
            "measurement_commit_full": measurement_full,
            "measurement_date": measurement_date,
            "rev_range": rev_range,
            "commit_count": commit_count,
        },
        "ck_git": ck_git,
        "ck_fi": dict(ck_fi),
        "ck_log_draft": {
            "measurement": cycle_label or "scheduled measurement",
            "commit": measurement_short,
            "date": measurement_date,
            "top_5_pct": ck_git["top5_share_pct"],
            "top_10_pct": ck_git["top10_share_pct"],
            "largest_hotspot": (ck_git["largest_hotspot"] or {}).get("display", "(none)"),
            "files_above_threshold": ck_git["files_above_threshold"],
            "hci": ck_git["hci"],
            "notes": notes,
        },
    }


def render_ck_hotspot_compression_report_md(report: Mapping[str, Any]) -> str:
    window = report["measurement_window"]
    ck_git = report["ck_git"]
    ck_fi = report["ck_fi"]
    draft = report["ck_log_draft"]
    largest = ck_git.get("largest_hotspot") or {}
    lines = [
        "# CK1 Hotspot Compression Report",
        "",
        "> CK-GIT primary measurement for Hotspot Compression Watch #1.",
        "",
        f"_Primary metric: **{report['primary_metric']}** (HCI = Top 5 Share %)._",
        "",
        "## Report Status",
        "",
        f"- **Generation status:** {report['generation_status']}",
        f"- **Measurement readiness:** {report['measurement_readiness']}",
        f"- **Data sufficient for HCI headline:** {report['data_sufficient']}",
        f"- **Standard version:** {report['standard_version']}",
        "",
        "## Measurement Window",
        "",
        f"- **Watch start (W):** `{window['watch_start_commit']}`",
        f"- **Measurement commit (M):** `{window['measurement_commit']}`",
        f"- **Measurement date:** {window['measurement_date']}",
        f"- **REV_RANGE:** `{window['rev_range']}`",
        f"- **Commits in window:** {window['commit_count']}",
        "",
        "## CK-GIT Primary Metrics",
        "",
        f"- **HCI (Top 5 %):** {ck_git['hci']}",
        f"- **Top 5 share %:** {ck_git['top5_share_pct']}",
        f"- **Top 10 share %:** {ck_git['top10_share_pct']}",
        f"- **Total touches:** {ck_git['total_touches']}",
        f"- **Distinct paths:** {ck_git['distinct_paths']}",
        f"- **Largest hotspot:** {largest.get('display', '(none)')}",
        f"- **Files above threshold (T_touch={ck_git['t_touch']}):** {ck_git['files_above_threshold']}",
        "",
        "## Hotspot Rankings (Top 10)",
        "",
    ]
    top_10 = ck_git.get("top_10_paths") or []
    if top_10:
        lines.extend(["| Rank | Path | Touches | Share % |", "|---:|---|---:|---:|"])
        for index, row in enumerate(top_10, start=1):
            lines.append(
                f"| {index} | `{row['path']}` | {row['touch_count']} | {row['share_pct']} |"
            )
    else:
        lines.append("_No population-path touches in measurement window._")

    lines.extend(
        [
            "",
            "## CK-FI Supplementary (Notes only)",
            "",
        ]
    )
    if ck_fi.get("available"):
        fi_largest = ck_fi.get("largest_hotspot") or {}
        lines.extend(
            [
                f"- **Notes string:** `{ck_fi.get('notes_string')}`",
                f"- **FI top 5 share %:** {ck_fi.get('top5_share_pct')}",
                f"- **FI top 10 share %:** {ck_fi.get('top10_share_pct')}",
                f"- **Modules above T_fi={ck_fi.get('t_fi')}:** {ck_fi.get('files_above_threshold')}",
                f"- **Largest FI module:** {fi_largest.get('display', '(none)')}",
            ]
        )
    else:
        lines.append(f"_CK-FI unavailable: {ck_fi.get('reason', 'unknown')}._")

    lines.extend(
        [
            "",
            "## CK Log Draft Row",
            "",
            "| Measurement | Commit | Date | Top 5 % | Top 10 % | Largest Hotspot | Files Above Threshold | Notes |",
            "|---|---|---|---:|---:|---|---:|---|",
            (
                f"| {draft['measurement']} | `{draft['commit']}` | {draft['date']} | "
                f"{draft['top_5_pct']} | {draft['top_10_pct']} | {draft['largest_hotspot']} | "
                f"{draft['files_above_threshold']} | `{draft['notes']}` |"
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_ck_hotspot_compression_report(
    md_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
    *,
    watch_start: str = WATCH_START_COMMIT,
    measurement_commit: str = "HEAD",
    bu_csv_path: str | Path | None = None,
    cycle_label: str | None = None,
    repo_root: Path | None = None,
    commit_paths: Sequence[Sequence[str]] | None = None,
    commit_count: int | None = None,
    watch_start_full: str | None = None,
    watch_start_short: str | None = None,
    measurement_full: str | None = None,
    measurement_short: str | None = None,
    measurement_date: str | None = None,
) -> tuple[dict[str, Any], str]:
    root = _repo_root(repo_root)
    if (
        commit_paths is not None
        and watch_start_full
        and watch_start_short
        and measurement_full
        and measurement_short
        and measurement_date
    ):
        collected_paths = list(commit_paths)
        collected_count = commit_count if commit_count is not None else len(collected_paths)
        resolved_watch_full = watch_start_full
        resolved_watch_short = watch_start_short
        resolved_measurement_full = measurement_full
        resolved_measurement_short = measurement_short
        resolved_measurement_date = measurement_date
    else:
        resolved_watch_full, resolved_watch_short = resolve_git_commit(watch_start, repo_root=root)
        resolved_measurement_full, resolved_measurement_short = resolve_git_commit(
            measurement_commit,
            repo_root=root,
        )
        resolved_measurement_date = git_commit_date(resolved_measurement_full, repo_root=root)
        if commit_paths is None:
            collected_paths, collected_count = collect_git_commit_paths(
                resolved_watch_full,
                resolved_measurement_full,
                repo_root=root,
            )
        else:
            collected_paths = list(commit_paths)
            collected_count = commit_count if commit_count is not None else len(collected_paths)

    ck_fi = parse_ck_fi_metrics(bu_csv_path or DEFAULT_BU_CSV_PATH, repo_root=root)
    report = build_ck_hotspot_compression_report(
        watch_start_full=resolved_watch_full,
        watch_start_short=resolved_watch_short,
        measurement_full=resolved_measurement_full,
        measurement_short=resolved_measurement_short,
        measurement_date=resolved_measurement_date,
        commit_paths=collected_paths,
        commit_count=collected_count,
        ck_fi=ck_fi,
        cycle_label=cycle_label,
    )
    markdown = render_ck_hotspot_compression_report_md(report)

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
