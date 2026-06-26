"""CK1 hotspot compression report generator — CK-GIT primary + CK-FI supplementary."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.ck_hotspot_compression_report import (  # noqa: E402
    DEFAULT_BU_CSV_PATH,
    DEFAULT_JSON_OUTPUT_PATH,
    DEFAULT_MD_OUTPUT_PATH,
    WATCH_START_COMMIT,
    write_ck_hotspot_compression_report,
)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate CK-GIT hotspot compression report (HCI) for Hotspot Compression Watch.",
    )
    parser.add_argument(
        "--watch-start",
        default=WATCH_START_COMMIT,
        help=f"Watch start commit W (default: {WATCH_START_COMMIT}).",
    )
    parser.add_argument(
        "--measurement-commit",
        default="HEAD",
        help="Measurement commit M (default: HEAD).",
    )
    parser.add_argument(
        "--bu-csv",
        type=Path,
        default=ROOT / DEFAULT_BU_CSV_PATH,
        help="Path to BU import fan-in CSV for CK-FI supplementary lane.",
    )
    parser.add_argument(
        "--cycle-label",
        default=None,
        help="Optional maintenance cycle label for CK log draft Notes.",
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

    report, markdown = write_ck_hotspot_compression_report(
        md_output_path=args.output_md,
        json_output_path=args.output_json,
        watch_start=args.watch_start,
        measurement_commit=args.measurement_commit,
        bu_csv_path=args.bu_csv,
        cycle_label=args.cycle_label,
        repo_root=ROOT,
    )
    ck_git = report["ck_git"]
    readiness = report["measurement_readiness"]
    print(f"Wrote {args.output_md} ({len(markdown.splitlines())} lines)")
    print(f"Wrote {args.output_json}")
    print(
        "HCI={hci}; Top 5={top5}%; Top 10={top10}%; "
        "readiness={readiness}; total_touches={touches}".format(
            hci=ck_git["hci"],
            top5=ck_git["top5_share_pct"],
            top10=ck_git["top10_share_pct"],
            readiness=readiness,
            touches=ck_git["total_touches"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
