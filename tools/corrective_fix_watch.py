"""CA11 corrective fix watch — detect new qualifying fixes and CA12 readiness."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.corrective_change_locality_cohort import (  # noqa: E402
    DEFAULT_COHORT_CSV_PATH as CA1_COHORT_CSV_PATH,
)
from tests.helpers.corrective_fix_absence_report import DEFAULT_BASELINE_JSON_PATH  # noqa: E402
from tests.helpers.corrective_fix_watch import (  # noqa: E402
    DEFAULT_CA10_JSON_PATH,
    DEFAULT_JSON_OUTPUT_PATH,
    DEFAULT_MD_OUTPUT_PATH,
    write_corrective_fix_watch_report,
)
from tests.helpers.post_baseline_corrective_cohort import DEFAULT_REVIEW_QUEUE_PATH  # noqa: E402


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run CA11 corrective fix watch and write emergence/readiness report.",
    )
    parser.add_argument(
        "--review-queue-csv",
        type=Path,
        default=ROOT / DEFAULT_REVIEW_QUEUE_PATH,
    )
    parser.add_argument(
        "--ca1-cohort-csv",
        type=Path,
        default=ROOT / CA1_COHORT_CSV_PATH,
    )
    parser.add_argument(
        "--baseline-json",
        type=Path,
        default=ROOT / DEFAULT_BASELINE_JSON_PATH,
    )
    parser.add_argument(
        "--ca10-json",
        type=Path,
        default=ROOT / DEFAULT_CA10_JSON_PATH,
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / DEFAULT_MD_OUTPUT_PATH,
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / DEFAULT_JSON_OUTPUT_PATH,
    )
    args = parser.parse_args()

    report, markdown = write_corrective_fix_watch_report(
        md_output_path=args.output_md,
        json_output_path=args.output_json,
        review_queue_path=args.review_queue_csv,
        ca1_cohort_csv_path=args.ca1_cohort_csv,
        baseline_json_path=args.baseline_json,
        ca10_json_path=args.ca10_json,
        repo_root=ROOT,
    )
    readiness = report["cohort_readiness"]["state"]
    detected = report["watch_summary"]["qualifying_fixes_detected"]
    print(f"Wrote {args.output_md} ({len(markdown.splitlines())} lines)")
    print(f"Wrote {args.output_json}")
    print(f"Qualifying fixes detected: {detected}; readiness: {readiness}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
