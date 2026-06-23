"""CA8 corrective fix availability report generator."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.corrective_fix_availability_report import (  # noqa: E402
    DEFAULT_BASELINE_JSON_PATH,
    DEFAULT_CA7_JSON_PATH,
    DEFAULT_JSON_OUTPUT_PATH,
    DEFAULT_MD_OUTPUT_PATH,
    write_corrective_fix_availability_report,
)
from tests.helpers.post_baseline_corrective_cohort import (  # noqa: E402
    DEFAULT_COHORT_CSV_PATH,
    DEFAULT_EXCLUSIONS_CSV_PATH,
    DEFAULT_REVIEW_QUEUE_PATH,
)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate CA8 corrective fix availability report.",
    )
    parser.add_argument("--ca7-json", type=Path, default=ROOT / DEFAULT_CA7_JSON_PATH)
    parser.add_argument("--exclusions-csv", type=Path, default=ROOT / DEFAULT_EXCLUSIONS_CSV_PATH)
    parser.add_argument("--review-queue-csv", type=Path, default=ROOT / DEFAULT_REVIEW_QUEUE_PATH)
    parser.add_argument("--cohort-csv", type=Path, default=ROOT / DEFAULT_COHORT_CSV_PATH)
    parser.add_argument("--baseline-json", type=Path, default=ROOT / DEFAULT_BASELINE_JSON_PATH)
    parser.add_argument("--output-md", type=Path, default=ROOT / DEFAULT_MD_OUTPUT_PATH)
    parser.add_argument("--output-json", type=Path, default=ROOT / DEFAULT_JSON_OUTPUT_PATH)
    args = parser.parse_args()

    _report, markdown = write_corrective_fix_availability_report(
        md_output_path=args.output_md,
        json_output_path=args.output_json,
        ca7_json_path=args.ca7_json,
        exclusions_csv_path=args.exclusions_csv,
        review_queue_path=args.review_queue_csv,
        cohort_csv_path=args.cohort_csv,
        baseline_json_path=args.baseline_json,
        repo_root=ROOT,
    )
    print(f"Wrote {args.output_md} ({len(markdown.splitlines())} lines)")
    print(f"Wrote {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
