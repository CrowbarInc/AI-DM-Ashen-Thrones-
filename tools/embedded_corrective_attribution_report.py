"""CA9 embedded corrective work attribution report generator."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.embedded_corrective_attribution import (  # noqa: E402
    DEFAULT_CA8_JSON_PATH,
    DEFAULT_JSON_OUTPUT_PATH,
    DEFAULT_MD_OUTPUT_PATH,
    write_embedded_corrective_attribution_report,
)
from tests.helpers.post_baseline_corrective_cohort import (  # noqa: E402
    DEFAULT_COHORT_CSV_PATH,
    DEFAULT_EXCLUSIONS_CSV_PATH,
    DEFAULT_REVIEW_QUEUE_PATH,
)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate CA9 embedded corrective work attribution report.",
    )
    parser.add_argument("--ca8-json", type=Path, default=ROOT / DEFAULT_CA8_JSON_PATH)
    parser.add_argument("--exclusions-csv", type=Path, default=ROOT / DEFAULT_EXCLUSIONS_CSV_PATH)
    parser.add_argument("--review-queue-csv", type=Path, default=ROOT / DEFAULT_REVIEW_QUEUE_PATH)
    parser.add_argument("--cohort-csv", type=Path, default=ROOT / DEFAULT_COHORT_CSV_PATH)
    parser.add_argument("--output-md", type=Path, default=ROOT / DEFAULT_MD_OUTPUT_PATH)
    parser.add_argument("--output-json", type=Path, default=ROOT / DEFAULT_JSON_OUTPUT_PATH)
    args = parser.parse_args()

    _report, markdown = write_embedded_corrective_attribution_report(
        md_output_path=args.output_md,
        json_output_path=args.output_json,
        ca8_json_path=args.ca8_json,
        exclusions_csv_path=args.exclusions_csv,
        review_queue_path=args.review_queue_csv,
        cohort_csv_path=args.cohort_csv,
        repo_root=ROOT,
    )
    print(f"Wrote {args.output_md} ({len(markdown.splitlines())} lines)")
    print(f"Wrote {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
