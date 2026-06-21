#!/usr/bin/env python3
"""Windows-native split-owner matrix refresh workflow (BU24).

Local maintainer entrypoint: regenerates the checked-in audit report, runs the
BU20/BU21 contract gate, and optionally the pytest contract slice. CI uses the
read-only check script instead — see docs/convergence_ci_inventory.md.

Usage:
    python scripts/refresh_split_owner_acceptance_matrix.py
    python scripts/refresh_split_owner_acceptance_matrix.py --write-report-only
    python scripts/refresh_split_owner_acceptance_matrix.py --check-only
    python scripts/refresh_split_owner_acceptance_matrix.py --skip-pytest
    make split-owner-matrix-refresh

Discovery index: docs/convergence_ci_inventory.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import split_owner_acceptance_matrix_ops as _ops


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repository root containing docs/audits/BU15_split_owner_acceptance_matrix.md",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write-report-only",
        action="store_true",
        help="Regenerate docs/audits/BU15_split_owner_acceptance_matrix.md only.",
    )
    mode.add_argument(
        "--check-only",
        action="store_true",
        help="Run the contract gate only (no report regeneration).",
    )
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Regenerate and validate without the pytest contract slice.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root
    write_report = not args.check_only
    run_check = not args.write_report_only
    run_pytest = not args.write_report_only and not args.check_only and not args.skip_pytest

    counts: dict[str, int] | None = None

    if write_report:
        report_path = _ops.write_split_owner_acceptance_matrix_report(repo_root=repo_root)
        report_step_total = 1
        if run_check:
            report_step_total = 3 if run_pytest else 2
        print(
            f"[1/{report_step_total}] regenerated "
            f"{report_path.relative_to(repo_root).as_posix()}"
        )

    if run_check:
        step = 2 if write_report else 1
        total = 3 if run_pytest else 2 if write_report else 1
        exit_code, counts = _ops.run_split_owner_acceptance_matrix_check(repo_root=repo_root)
        if exit_code != 0:
            print(f"[{step}/{total}] split-owner acceptance matrix contract: FAIL")
            return exit_code
        assert counts is not None
        print(
            f"[{step}/{total}] split-owner acceptance matrix contract: OK "
            f"({_ops.format_split_owner_matrix_counts(counts)})"
        )

    if run_pytest:
        exit_code = _ops.run_split_owner_acceptance_matrix_pytest(repo_root=repo_root)
        if exit_code != 0:
            print("[3/3] split-owner acceptance matrix pytest contract: FAIL")
            return exit_code
        print("[3/3] split-owner acceptance matrix pytest contract: OK")

    if counts is not None:
        print(
            "split-owner acceptance matrix refresh: OK "
            f"({_ops.format_split_owner_matrix_counts(counts)})"
        )
    elif write_report and not run_check:
        print("split-owner acceptance matrix report: OK (write-report-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
