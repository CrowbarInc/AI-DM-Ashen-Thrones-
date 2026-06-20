#!/usr/bin/env python3
"""Generate BR2 attribution regression guard report artifact.

Read-side validation only. Does not modify attribution behavior.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.attribution_regression_guard import (  # noqa: E402
    DEFAULT_OUTPUT_PATH,
    assert_attribution_metrics_not_regressed,
    write_attribution_regression_guard_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate BR2 attribution regression guard report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / DEFAULT_OUTPUT_PATH,
        help=f"Markdown output path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--strict-exit",
        action="store_true",
        help="Exit with code 1 when any required guard check fails.",
    )
    args = parser.parse_args()

    if args.strict_exit:
        try:
            evaluation = assert_attribution_metrics_not_regressed()
        except AssertionError as exc:
            write_attribution_regression_guard_report(args.output)
            print(exc, file=sys.stderr)
            return 1
        _, markdown = write_attribution_regression_guard_report(args.output)
    else:
        evaluation, markdown = write_attribution_regression_guard_report(args.output)

    print(f"Wrote {args.output} ({len(markdown.splitlines())} lines)")
    if args.strict_exit:
        return 0
    if evaluation["status"] != "pass":
        print("WARNING: attribution regression guard reported failures.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
