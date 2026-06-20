#!/usr/bin/env python3
"""Generate BR1 attribution completeness repository metric artifact.

Read-side reporting only. Does not modify attribution behavior.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.attribution_completeness_metric import (  # noqa: E402
    DEFAULT_OUTPUT_PATH,
    write_attribution_completeness_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate BR1 attribution completeness repository metric report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / DEFAULT_OUTPUT_PATH,
        help=f"Markdown output path (default: {DEFAULT_OUTPUT_PATH})",
    )
    args = parser.parse_args()
    _report, markdown = write_attribution_completeness_report(args.output)
    print(f"Wrote {args.output} ({len(markdown.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
