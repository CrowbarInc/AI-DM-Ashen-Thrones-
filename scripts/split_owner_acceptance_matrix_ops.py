"""Shared split-owner acceptance matrix report/check helpers (BU24).

Used by ``refresh_split_owner_acceptance_matrix.py`` and
``check_split_owner_acceptance_matrix.py``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH = (
    "docs/audits/BU15_split_owner_acceptance_matrix.md"
)
SPLIT_OWNER_MATRIX_CONTRACT_PYTEST_ARGS = (
    "tests/test_split_owner_acceptance_matrix_contract.py",
    "-q",
    "-m",
    "split_owner_matrix_contract",
)


def ensure_repo_root_on_path(repo_root: Path) -> None:
    root = str(repo_root)
    if root not in sys.path:
        sys.path.insert(0, root)


def split_owner_acceptance_matrix_report_path(*, repo_root: Path) -> Path:
    return repo_root / SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH


def write_split_owner_acceptance_matrix_report(*, repo_root: Path) -> Path:
    """Regenerate the checked-in BU15 matrix report from the canonical tuple."""
    ensure_repo_root_on_path(repo_root)
    from tests.helpers.failure_classification_sync import (
        render_split_owner_acceptance_matrix_report,
    )

    report_path = split_owner_acceptance_matrix_report_path(repo_root=repo_root)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_split_owner_acceptance_matrix_report(), encoding="utf-8")
    return report_path


def format_split_owner_matrix_counts(counts: dict[str, int]) -> str:
    return (
        f"rows={counts['total_rows']} "
        f"dashboard={counts['dashboard_covered_rows']} "
        f"fem={counts['fem_projection_rows']} "
        f"legacy={counts['legacy_only_rows']}"
    )


def run_split_owner_acceptance_matrix_check(*, repo_root: Path) -> tuple[int, dict[str, int] | None]:
    """Validate matrix/report/dashboard parity. Returns (exit_code, counts)."""
    ensure_repo_root_on_path(repo_root)
    report_path = split_owner_acceptance_matrix_report_path(repo_root=repo_root)
    if not report_path.is_file():
        print("split-owner acceptance matrix contract: FAIL", file=sys.stderr)
        print("split-owner acceptance matrix contract drift:", file=sys.stderr)
        print(
            f"- missing report: {SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH}",
            file=sys.stderr,
        )
        return 1, None

    from tests.helpers.failure_classification_sync import (
        assert_split_owner_acceptance_matrix_contract,
        split_owner_acceptance_matrix_contract_misalignments,
        split_owner_acceptance_matrix_counts,
    )

    misalignments = split_owner_acceptance_matrix_contract_misalignments(repo_root=repo_root)
    if misalignments:
        print("split-owner acceptance matrix contract: FAIL", file=sys.stderr)
        print("split-owner acceptance matrix contract drift:", file=sys.stderr)
        for item in misalignments:
            print(f"- {item}", file=sys.stderr)
        return 1, None

    counts = split_owner_acceptance_matrix_counts()
    assert_split_owner_acceptance_matrix_contract(repo_root=repo_root)
    return 0, counts


def run_split_owner_acceptance_matrix_pytest(*, repo_root: Path) -> int:
    """Run the fast pytest contract slice."""
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *SPLIT_OWNER_MATRIX_CONTRACT_PYTEST_ARGS],
        cwd=repo_root,
    )
    return int(completed.returncode)
