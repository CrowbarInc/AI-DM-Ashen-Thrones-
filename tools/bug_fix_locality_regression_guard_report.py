#!/usr/bin/env python3
"""Generate BRL2 bug-fix locality regression guard report artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.bug_fix_locality_regression_guard import (  # noqa: E402
    DEFAULT_OUTPUT_PATH,
    assert_locality_metrics_not_regressed,
    write_bug_fix_locality_regression_guard_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate BRL2 bug-fix locality regression guard report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / DEFAULT_OUTPUT_PATH,
        help=f"Markdown output path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / "docs" / "reports" / "BR_commit_classification.csv",
        help="Commit classification CSV path.",
    )
    parser.add_argument(
        "--strict-exit",
        action="store_true",
        help="Exit with code 1 when any required guard check fails.",
    )
    args = parser.parse_args()

    if args.strict_exit:
        try:
            evaluation = assert_locality_metrics_not_regressed(csv_path=args.csv, repo_root=ROOT)
        except AssertionError as exc:
            write_bug_fix_locality_regression_guard_report(
                args.output,
                csv_path=args.csv,
                repo_root=ROOT,
            )
            print(exc, file=sys.stderr)
            return 1
        _, markdown = write_bug_fix_locality_regression_guard_report(
            args.output,
            csv_path=args.csv,
            repo_root=ROOT,
        )
    else:
        evaluation, markdown = write_bug_fix_locality_regression_guard_report(
            args.output,
            csv_path=args.csv,
            repo_root=ROOT,
        )

    print(f"Wrote {args.output} ({len(markdown.splitlines())} lines)")
    if args.strict_exit:
        return 0
    if evaluation["status"] != "pass":
        print("WARNING: locality regression guard reported failures.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
