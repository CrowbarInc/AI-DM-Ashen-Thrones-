"""CE3 line-range decomposition for replay_bug_recurrence.py."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tests" / "helpers" / "replay_bug_recurrence.py"
BACKUP = ROOT / "tests" / "helpers" / "replay_bug_recurrence_monolith.py.bak"
HELPERS = ROOT / "tests" / "helpers"

STD_HEADER = """from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_paths import RECURRENCE_TRAJECTORY_HISTORY_JSON_PATH
from tests.helpers.replay_drift_taxonomy import ALLOWED_OWNER_DRIFT_BUCKETS
"""

MODULES: list[tuple[str, int, int, str]] = [
    (
        "replay_bug_recurrence_events",
        16,
        990,
        "Recurrence key derivation, event persistence, and history aggregation foundations.",
    ),
    (
        "replay_bug_recurrence_history",
        991,
        4043,
        "Trend, forecast, portfolio, remediation, governance, and lifecycle analytics.",
    ),
    (
        "replay_bug_recurrence_statistics",
        4046,
        8367,
        "Program effectiveness, maturity, roadmap, completion, and graduation analytics.",
    ),
    (
        "replay_bug_recurrence_serialization",
        8370,
        10466,
        "Confidence calibration, outcome validation, and markdown report rendering.",
    ),
]


def slice_lines(lines: list[str], start: int, end: int) -> str:
    return "".join(lines[start - 1 : end])


def public_names(source: str) -> list[str]:
    tree = ast.parse(source)
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    return names


def main() -> None:
    source_path = BACKUP if BACKUP.is_file() else SRC
    source = source_path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    docstring = ast.get_docstring(ast.parse(source)) or ""

    prior: list[str] = []
    stats: list[tuple[str, int, int]] = []

    for module_name, start, end, description in MODULES:
        import_lines = [
            f"from tests.helpers.{dep} import *  # noqa: F403"
            for dep in prior
        ]
        body = slice_lines(lines, start, end)
        content = (
            f'"""{description}"""\n'
            f"{STD_HEADER}\n"
            + ("\n".join(import_lines) + "\n\n" if import_lines else "")
            + body
        )
        out = HELPERS / f"{module_name}.py"
        if module_name == "replay_bug_recurrence_statistics":
            content = content.replace(
                "from tests.helpers.replay_bug_recurrence_history import *  # noqa: F403\n",
                "from tests.helpers.replay_bug_recurrence_history import *  # noqa: F403\n"
                "from tests.helpers.replay_bug_recurrence_history import _regression_rate_value\n",
                1,
            )
        if module_name == "replay_bug_recurrence_serialization":
            content = content.replace(
                "from tests.helpers.replay_bug_recurrence_statistics import *  # noqa: F403\n",
                "from tests.helpers.replay_bug_recurrence_statistics import *  # noqa: F403\n"
                "from tests.helpers.replay_bug_recurrence_history import _parse_iso_timestamp\n"
                "from tests.helpers.replay_bug_recurrence_statistics import (\n"
                "    _clamp_maturity_score,\n"
                "    _maturity_volume_factor,\n"
                ")\n",
                1,
            )
        out.write_text(content, encoding="utf-8")
        loc = len(content.splitlines())
        func_count = sum(1 for line in body.splitlines() if line.startswith(("def ", "class ")))
        stats.append((module_name, loc, func_count))
        prior.append(module_name)

    facade_imports = [
        f"from tests.helpers.{name} import *  # noqa: F403" for name, *_ in MODULES
    ]
    all_names = sorted(set(public_names(source)))
    facade = (
        f'"""{docstring}\n\n'
        "CE3 facade: re-exports recurrence analytics from focused helper modules.\n"
        '"""\n'
        f"{STD_HEADER}\n"
        + "\n".join(facade_imports)
        + "\n\n"
        + "# Responsibility map (CE3):\n"
        + "# - replay_bug_recurrence_events: keys, rows, event log persistence, history aggregation\n"
        + "# - replay_bug_recurrence_history: trend/forecast/portfolio/remediation/governance/lifecycle analytics\n"
        + "# - replay_bug_recurrence_statistics: effectiveness, maturity, roadmap, completion, graduation\n"
        + "# - replay_bug_recurrence_serialization: confidence calibration, outcome validation, markdown renderers\n"
        + "\n"
        + "__all__ = [\n"
        + "".join(f'    "{name}",\n' for name in all_names)
        + "]\n"
    )
    SRC.write_text(facade, encoding="utf-8")

    # Remove obsolete fine-grained modules from first decomposition attempt.
    obsolete_prefixes = (
        "replay_bug_recurrence_constants",
        "replay_bug_recurrence_classification",
        "replay_bug_recurrence_trends",
        "replay_bug_recurrence_forecast",
        "replay_bug_recurrence_portfolio",
        "replay_bug_recurrence_remediation",
        "replay_bug_recurrence_governance",
        "replay_bug_recurrence_lifecycle",
        "replay_bug_recurrence_trajectory",
        "replay_bug_recurrence_effectiveness",
        "replay_bug_recurrence_maturity",
        "replay_bug_recurrence_roadmap",
        "replay_bug_recurrence_completion",
        "replay_bug_recurrence_graduation",
        "replay_bug_recurrence_confidence",
        "replay_bug_recurrence_outcome",
    )
    for path in HELPERS.glob("replay_bug_recurrence_*.py"):
        if path.stem in obsolete_prefixes:
            path.unlink()

    print("CE3 line-range decomposition complete.")
    for module_name, loc, func_count in stats:
        print(f"  {module_name}: {loc} LOC, {func_count} top-level defs")
    print(f"  replay_bug_recurrence.py (facade): {len(facade.splitlines())} LOC")


if __name__ == "__main__":
    main()
