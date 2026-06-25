#!/usr/bin/env python3
"""CE1 — read-only replay maintenance concentration metrics.

Analyzes replay helper/test ownership, import concentration, and recent git
activity. Does not modify repository contents except when explicitly writing
report artifacts.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON_OUT = ROOT / "artifacts" / "golden_replay" / "replay_maintenance_metrics.json"
DEFAULT_MD_OUT = ROOT / "artifacts" / "golden_replay" / "replay_maintenance_metrics.md"

SCHEMA_VERSION = 1
AUDIT_ID = "CE1"

TARGET_MODULES: tuple[str, ...] = (
    "tests.helpers.failure_dashboard_report",
    "tests.helpers.failure_dashboard_recurrence",
    "tests.helpers.failure_dashboard_drift",
    "tests.helpers.failure_dashboard_stability",
    "tests.helpers.failure_dashboard_session",
    "tests.helpers.failure_dashboard_paths",
    "tests.helpers.golden_replay",
    "tests.helpers.golden_replay_projection",
    "tests.helpers.protected_replay_registry",
)

REPLAY_ARTIFACT_MODULES: tuple[str, ...] = (
    "tests/helpers/failure_dashboard_paths.py",
    "tests/helpers/failure_dashboard_session.py",
    "tests/helpers/failure_dashboard_recurrence.py",
    "tests/helpers/failure_dashboard_drift.py",
    "tests/helpers/failure_dashboard_stability.py",
    "tests/helpers/failure_dashboard_orchestration.py",
)

COMPATIBILITY_FACADE_PATH = "tests/helpers/failure_dashboard_report.py"

REPLAY_HELPER_PATTERNS: tuple[str, ...] = (
    "tests/helpers/golden_replay*.py",
    "tests/helpers/replay_*.py",
    "tests/helpers/protected_replay*.py",
    "tests/helpers/failure_dashboard*.py",
    "tests/helpers/failure_classifier.py",
    "tests/helpers/failure_classification_sync.py",
    "tests/helpers/runtime_lineage_reporting.py",
)

REPLAY_TEST_PATTERNS: tuple[str, ...] = (
    "tests/test_*golden*replay*.py",
    "tests/test_*replay*.py",
    "tests/test_*protected_replay*.py",
    "tests/test_failure_dashboard*.py",
    "tests/test_failure_classifier.py",
    "tests/test_failure_classification_contract.py",
    "tests/test_stability_reporting_contract.py",
    "tests/test_recurrence_trajectory_history.py",
)

REPLAY_OWNERSHIP_PATTERNS: tuple[str, ...] = (
    *REPLAY_HELPER_PATTERNS,
    *REPLAY_TEST_PATTERNS,
    "tests/helpers/failure_dashboard_fixtures.py",
    "game/final_emission_replay_projection.py",
    "tools/*replay*.py",
    "tools/*protected_replay*.py",
    "tools/expand_protected_replay_observations.py",
    "tools/refresh_protected_replay_manifest.py",
    "tools/run_protected_replay_trend.py",
    "tools/compare_scenario_spine_reruns.py",
)

SCAN_ROOTS: tuple[str, ...] = ("tests", "game", "tools")

TOP_LEVEL_JSON_KEYS: tuple[str, ...] = (
    "schema_version",
    "audit_id",
    "generated_at",
    "repo_root",
    "executive_summary",
    "ownership_totals",
    "concentration_indicators",
    "largest_replay_files",
    "largest_replay_helpers",
    "largest_replay_tests",
    "top_files_by_loc",
    "top_files_by_functions",
    "top_files_by_importers",
    "dependency_concentration",
    "import_concentration",
    "touch_concentration",
    "ownership_concentration",
    "maintenance_risk_assessment",
)


@dataclass(frozen=True)
class FileMetrics:
    path: str
    loc: int
    functions: int
    classes: int
    category: str


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _matches_any(rel: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch(rel, pattern) for pattern in patterns)


def _module_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    if rel.name == "__init__.py":
        return ".".join(rel.parts[:-1])
    return ".".join(rel.with_suffix("").parts)


def _parse_source(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8-sig"))
    except (OSError, SyntaxError, UnicodeError):
        return None


def _count_symbols(tree: ast.AST) -> tuple[int, int]:
    functions = 0
    classes = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
    return functions, classes


def _file_metrics(path: Path, root: Path, category: str) -> FileMetrics:
    rel = _relative(path, root)
    text = path.read_text(encoding="utf-8-sig")
    loc = len(text.splitlines())
    tree = ast.parse(text)
    functions, classes = _count_symbols(tree)
    return FileMetrics(path=rel, loc=loc, functions=functions, classes=classes, category=category)


def _collect_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for scan_root in SCAN_ROOTS:
        base = root / scan_root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            files.append(path)
    return files


def _categorize_file(rel: str) -> str | None:
    if rel == COMPATIBILITY_FACADE_PATH:
        return "compatibility_facade"
    if rel in REPLAY_ARTIFACT_MODULES:
        return "replay_artifact_module"
    if _matches_any(rel, REPLAY_HELPER_PATTERNS):
        return "replay_helper"
    if _matches_any(rel, REPLAY_TEST_PATTERNS):
        return "replay_test"
    if _matches_any(rel, REPLAY_OWNERSHIP_PATTERNS):
        return "replay_other"
    return None


def _collect_replay_files(root: Path) -> list[FileMetrics]:
    metrics: list[FileMetrics] = []
    seen: set[str] = set()
    for path in _collect_python_files(root):
        rel = _relative(path, root)
        category = _categorize_file(rel)
        if category is None:
            continue
        if rel in seen:
            continue
        seen.add(rel)
        metrics.append(_file_metrics(path, root, category))
    return sorted(metrics, key=lambda item: item.path)


def _build_import_graph(root: Path) -> tuple[dict[str, Path], dict[str, set[str]]]:
    modules: dict[str, Path] = {}
    imports: dict[str, set[str]] = {}
    for path in _collect_python_files(root):
        module = _module_name(path, root)
        modules[module] = path
        imports[module] = set()
        tree = _parse_source(path)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(("game", "tests", "tools")):
                        imports[module].add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(("game", "tools", "tests")):
                    imports[module].add(node.module)
    return modules, imports


def _resolve_fan_in(target: str, modules: Mapping[str, Path], imports: Mapping[str, set[str]]) -> int:
    count = 0
    for importer, outgoing in imports.items():
        if importer == target:
            continue
        for imported in outgoing:
            if imported == target or imported.startswith(f"{target}."):
                count += 1
                break
    return count


def _resolve_fan_out(module: str, imports: Mapping[str, set[str]]) -> int:
    return len(imports.get(module, set()))


def _importer_count(target: str, modules: Mapping[str, Path], imports: Mapping[str, set[str]]) -> int:
    return _resolve_fan_in(target, modules, imports)


def _aggregate_totals(files: Sequence[FileMetrics]) -> dict[str, Any]:
    buckets: dict[str, list[FileMetrics]] = defaultdict(list)
    for item in files:
        buckets[item.category].append(item)
    totals: dict[str, Any] = {}
    for category, bucket in sorted(buckets.items()):
        total_loc = sum(item.loc for item in bucket)
        total_functions = sum(item.functions for item in bucket)
        totals[category] = {
            "file_count": len(bucket),
            "total_loc": total_loc,
            "total_functions": total_functions,
            "average_loc": round(total_loc / len(bucket), 1) if bucket else 0.0,
            "average_functions": round(total_functions / len(bucket), 1) if bucket else 0.0,
        }
    return totals


def _top_n(items: Sequence[dict[str, Any]], key: str, n: int = 20) -> list[dict[str, Any]]:
    return sorted(items, key=lambda row: (-int(row[key]), row["path"]))[:n]


def _concentration_indicators(files: Sequence[FileMetrics]) -> dict[str, Any]:
    helpers = [item for item in files if item.category == "replay_helper"]
    tests = [item for item in files if item.category == "replay_test"]
    all_replay = list(files)
    total_loc = sum(item.loc for item in all_replay) or 1
    helper_loc = sum(item.loc for item in helpers) or 1
    test_loc = sum(item.loc for item in tests) or 1

    largest = max(all_replay, key=lambda item: item.loc) if all_replay else None
    largest_helper = max(helpers, key=lambda item: item.loc) if helpers else None
    largest_test = max(tests, key=lambda item: item.loc) if tests else None

    return {
        "largest_file_share_pct": round((largest.loc / total_loc) * 100.0, 2) if largest else 0.0,
        "largest_file_path": largest.path if largest else None,
        "largest_helper_share_pct": round((largest_helper.loc / helper_loc) * 100.0, 2) if largest_helper else 0.0,
        "largest_helper_path": largest_helper.path if largest_helper else None,
        "largest_test_share_pct": round((largest_test.loc / test_loc) * 100.0, 2) if largest_test else 0.0,
        "largest_test_path": largest_test.path if largest_test else None,
        "average_replay_helper_loc": round(helper_loc / len(helpers), 1) if helpers else 0.0,
        "average_replay_test_loc": round(test_loc / len(tests), 1) if tests else 0.0,
        "average_replay_helper_functions": round(
            sum(item.functions for item in helpers) / len(helpers),
            1,
        )
        if helpers
        else 0.0,
        "average_replay_test_functions": round(
            sum(item.functions for item in tests) / len(tests),
            1,
        )
        if tests
        else 0.0,
    }


def _git_available(root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except (OSError, subprocess.SubprocessError):
        return False


def _git_touch_count(path: str, days: int, root: Path) -> int:
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                f"--since={days} days ago",
                "--format=%H",
                "--",
                path,
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return 0
        return len([line for line in result.stdout.splitlines() if line.strip()])
    except (OSError, subprocess.SubprocessError):
        return 0


def _touch_concentration(files: Sequence[FileMetrics], root: Path) -> dict[str, Any]:
    git_ok = _git_available(root)
    rows: list[dict[str, Any]] = []
    for item in files:
        row = {
            "path": item.path,
            "category": item.category,
            "loc": item.loc,
            "touches_30d": _git_touch_count(item.path, 30, root) if git_ok else None,
            "touches_60d": _git_touch_count(item.path, 60, root) if git_ok else None,
            "touches_90d": _git_touch_count(item.path, 90, root) if git_ok else None,
        }
        rows.append(row)
    return {
        "git_available": git_ok,
        "files": rows,
        "top_touches_30d": _top_n(
            [{**row, "value": row["touches_30d"]} for row in rows if row["touches_30d"] is not None],
            "value",
            20,
        ),
        "top_touches_60d": _top_n(
            [{**row, "value": row["touches_60d"]} for row in rows if row["touches_60d"] is not None],
            "value",
            20,
        ),
        "top_touches_90d": _top_n(
            [{**row, "value": row["touches_90d"]} for row in rows if row["touches_90d"] is not None],
            "value",
            20,
        ),
    }


def _maintenance_risk_assessment(
    *,
    concentration: Mapping[str, Any],
    dependency_rows: Sequence[Mapping[str, Any]],
    touch_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    report_hub = next((row for row in dependency_rows if row["module"] == "tests.helpers.failure_dashboard_report"), None)
    risks: list[str] = []
    if concentration.get("largest_file_share_pct", 0) >= 15:
        risks.append(
            "Single replay file exceeds 15% of replay ownership LOC; decomposition may still be warranted."
        )
    if concentration.get("largest_helper_share_pct", 0) >= 20:
        risks.append(
            "One replay helper exceeds 20% of helper LOC; helper concentration remains elevated."
        )
    if report_hub and int(report_hub.get("fan_in", 0)) >= 15:
        risks.append(
            "Compatibility/report hub fan-in remains high; import surface area is a maintenance hotspot."
        )
    active = sorted(
        [row for row in touch_rows if isinstance(row.get("touches_30d"), int) and row["touches_30d"] > 0],
        key=lambda row: (-int(row["touches_30d"]), row["path"]),
    )
    if len(active) >= 5:
        risks.append(
            f"{len(active)} replay ownership files changed in the last 30 days; churn is active."
        )
    if not risks:
        risks.append("No elevated concentration signals detected in current snapshot.")
    return {
        "risk_level": "elevated" if len(risks) > 1 else "moderate",
        "signals": risks,
        "report_hub_fan_in": report_hub.get("fan_in") if report_hub else None,
    }


def build_metrics(root: Path | None = None, *, generated_at: str | None = None) -> dict[str, Any]:
    repo_root = (root or ROOT).resolve()
    replay_files = _collect_replay_files(repo_root)
    modules, imports = _build_import_graph(repo_root)

    file_rows = [
        {
            "path": item.path,
            "loc": item.loc,
            "functions": item.functions,
            "classes": item.classes,
            "category": item.category,
            "importers": _importer_count(
                ".".join(Path(item.path).with_suffix("").parts),
                modules,
                imports,
            ),
        }
        for item in replay_files
    ]

    dependency_concentration = [
        {
            "module": module,
            "fan_in": _resolve_fan_in(module, modules, imports),
            "fan_out": _resolve_fan_out(module, imports),
        }
        for module in TARGET_MODULES
    ]

    ownership_totals = _aggregate_totals(replay_files)
    concentration = _concentration_indicators(replay_files)
    touch = _touch_concentration(replay_files, repo_root)

    helpers = [row for row in file_rows if row["category"] == "replay_helper"]
    tests = [row for row in file_rows if row["category"] == "replay_test"]

    executive_summary = {
        "replay_file_count": len(replay_files),
        "replay_total_loc": sum(item.loc for item in replay_files),
        "replay_total_functions": sum(item.functions for item in replay_files),
        "replay_helper_loc": ownership_totals.get("replay_helper", {}).get("total_loc", 0),
        "replay_test_loc": ownership_totals.get("replay_test", {}).get("total_loc", 0),
        "replay_artifact_module_loc": ownership_totals.get("replay_artifact_module", {}).get("total_loc", 0),
        "compatibility_facade_loc": ownership_totals.get("compatibility_facade", {}).get("total_loc", 0),
        "largest_replay_file": concentration.get("largest_file_path"),
        "largest_replay_helper": concentration.get("largest_helper_path"),
        "largest_replay_test": concentration.get("largest_test_path"),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "generated_at": generated_at
        or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "repo_root": str(repo_root),
        "executive_summary": executive_summary,
        "ownership_totals": ownership_totals,
        "concentration_indicators": concentration,
        "largest_replay_files": _top_n(file_rows, "loc", 20),
        "largest_replay_helpers": _top_n(helpers, "loc", 20),
        "largest_replay_tests": _top_n(tests, "loc", 20),
        "top_files_by_loc": _top_n(file_rows, "loc", 20),
        "top_files_by_functions": _top_n(file_rows, "functions", 20),
        "top_files_by_importers": _top_n(file_rows, "importers", 20),
        "dependency_concentration": dependency_concentration,
        "import_concentration": {
            "target_modules": dependency_concentration,
            "highest_fan_in": max(dependency_concentration, key=lambda row: row["fan_in"]),
            "highest_fan_out": max(dependency_concentration, key=lambda row: row["fan_out"]),
        },
        "touch_concentration": touch,
        "ownership_concentration": concentration,
        "maintenance_risk_assessment": _maintenance_risk_assessment(
            concentration=concentration,
            dependency_rows=dependency_concentration,
            touch_rows=touch["files"],
        ),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = report["executive_summary"]
    concentration = report["concentration_indicators"]
    risk = report["maintenance_risk_assessment"]
    lines = [
        "# Replay Maintenance Metrics",
        "",
        "## Executive Summary",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Replay files analyzed: `{summary['replay_file_count']}`",
        f"- Replay total LOC: `{summary['replay_total_loc']}`",
        f"- Replay helper LOC: `{summary['replay_helper_loc']}`",
        f"- Replay test LOC: `{summary['replay_test_loc']}`",
        f"- Artifact module LOC: `{summary['replay_artifact_module_loc']}`",
        f"- Compatibility facade LOC: `{summary['compatibility_facade_loc']}`",
        f"- Largest replay file: `{summary['largest_replay_file']}`",
        "",
        "## Largest Replay Files",
        "",
        "| Path | LOC | Functions | Importers | Category |",
        "|---|---:|---:|---:|---|",
    ]
    for row in report["largest_replay_files"]:
        lines.append(
            f"| `{row['path']}` | {row['loc']} | {row['functions']} | {row['importers']} | {row['category']} |"
        )
    lines.extend(["", "## Largest Replay Helpers", "", "| Path | LOC | Functions | Importers |", "|---|---:|---:|---:|"])
    for row in report["largest_replay_helpers"]:
        lines.append(f"| `{row['path']}` | {row['loc']} | {row['functions']} | {row['importers']} |")
    lines.extend(["", "## Largest Replay Tests", "", "| Path | LOC | Functions | Importers |", "|---|---:|---:|---:|"])
    for row in report["largest_replay_tests"]:
        lines.append(f"| `{row['path']}` | {row['loc']} | {row['functions']} | {row['importers']} |")
    lines.extend(["", "## Import Concentration", "", "| Module | Fan-In | Fan-Out |", "|---|---:|---:|"])
    for row in report["dependency_concentration"]:
        lines.append(f"| `{row['module']}` | {row['fan_in']} | {row['fan_out']} |")
    lines.extend(
        [
            "",
            "## Touch Concentration",
            "",
            f"- Git history available: `{report['touch_concentration']['git_available']}`",
            "",
            "### Top Touches (30 days)",
            "",
            "| Path | Touches | LOC |",
            "|---|---:|---:|",
        ]
    )
    for row in report["touch_concentration"]["top_touches_30d"]:
        lines.append(f"| `{row['path']}` | {row['value']} | {row['loc']} |")
    lines.extend(
        [
            "",
            "## Ownership Concentration",
            "",
            f"- Largest file share: `{concentration['largest_file_share_pct']}%` (`{concentration['largest_file_path']}`)",
            f"- Largest helper share: `{concentration['largest_helper_share_pct']}%` (`{concentration['largest_helper_path']}`)",
            f"- Largest test share: `{concentration['largest_test_share_pct']}%` (`{concentration['largest_test_path']}`)",
            f"- Average replay helper LOC: `{concentration['average_replay_helper_loc']}`",
            f"- Average replay test LOC: `{concentration['average_replay_test_loc']}`",
            "",
            "## Maintenance Risk Assessment",
            "",
            f"- Risk level: `{risk['risk_level']}`",
            f"- Report hub fan-in: `{risk['report_hub_fan_in']}`",
            "",
        ]
    )
    for signal in risk["signals"]:
        lines.append(f"- {signal}")
    lines.append("")
    return "\n".join(lines)


def write_reports(
    report: Mapping[str, Any],
    *,
    json_out: Path,
    markdown_out: Path,
) -> tuple[Path, Path]:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_out.write_text(render_markdown(report), encoding="utf-8")
    return json_out, markdown_out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument(
        "--generated-at",
        default=None,
        help="Fixed timestamp for deterministic output (ISO-8601).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_metrics(args.repo_root.resolve(), generated_at=args.generated_at)
    json_out, markdown_out = write_reports(
        report,
        json_out=args.json_out.resolve(),
        markdown_out=args.markdown_out.resolve(),
    )
    print(f"Wrote {json_out}")
    print(f"Wrote {markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
