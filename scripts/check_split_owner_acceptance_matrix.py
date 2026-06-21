#!/usr/bin/env python3
"""Fast split-owner acceptance matrix drift check (BU20/BU21).

Canonical CI entrypoint in ``.github/workflows/convergence-checks.yml``.
Read-only: validates matrix/report/dashboard parity without writing files or
spawning nested pytest. Local full refresh:
``python scripts/refresh_split_owner_acceptance_matrix.py``.

Usage:
    python scripts/check_split_owner_acceptance_matrix.py
    python scripts/refresh_split_owner_acceptance_matrix.py --check-only
    make split-owner-matrix-check
    make split-owner-matrix-refresh

Also runs in CI: .github/workflows/convergence-checks.yml
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
    args = parser.parse_args(argv)

    exit_code, counts = _ops.run_split_owner_acceptance_matrix_check(repo_root=args.repo_root)
    if exit_code != 0:
        return exit_code

    assert counts is not None
    print(
        "split-owner acceptance matrix contract: OK "
        f"({_ops.format_split_owner_matrix_counts(counts)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
