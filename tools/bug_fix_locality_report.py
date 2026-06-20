#!/usr/bin/env python3
"""Generate BRL1 bug-fix locality repository metric artifact.

Read-side reporting only. Does not modify runtime behavior.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.bug_fix_locality_metric import (  # noqa: E402
    DEFAULT_CSV_PATH,
    DEFAULT_OUTPUT_PATH,
    write_bug_fix_locality_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate BRL1 bug-fix locality repository metric report.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT / DEFAULT_CSV_PATH,
        help=f"Commit classification CSV (default: {DEFAULT_CSV_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / DEFAULT_OUTPUT_PATH,
        help=f"Markdown output path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--no-hotspots",
        action="store_true",
        help="Skip git-backed hotspot analysis.",
    )
    args = parser.parse_args()

    _report, markdown = write_bug_fix_locality_report(
        args.output,
        csv_path=args.csv,
        repo_root=ROOT,
        include_hotspots=not args.no_hotspots,
    )
    print(f"Wrote {args.output} ({len(markdown.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
