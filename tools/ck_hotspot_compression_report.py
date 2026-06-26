"""CK1 hotspot compression report generator — CK-GIT primary + CK-FI supplementary."""
from __future__ import annotations

import shlex
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


def format_invocation_command(args: object) -> str:
    """Reconstruct argv for report provenance."""
    parts = ["python", "tools/ck_hotspot_compression_report.py"]
    watch_start = getattr(args, "watch_start", WATCH_START_COMMIT)
    measurement_commit = getattr(args, "measurement_commit", "HEAD")
    cycle_label = getattr(args, "cycle_label", None)
    bu_csv = getattr(args, "bu_csv", ROOT / DEFAULT_BU_CSV_PATH)
    output_md = getattr(args, "output_md", ROOT / DEFAULT_MD_OUTPUT_PATH)
    output_json = getattr(args, "output_json", ROOT / DEFAULT_JSON_OUTPUT_PATH)

    if watch_start != WATCH_START_COMMIT:
        parts.extend(["--watch-start", watch_start])
    if measurement_commit != "HEAD":
        parts.extend(["--measurement-commit", measurement_commit])
    if cycle_label:
        parts.extend(["--cycle-label", cycle_label])
    if Path(bu_csv) != ROOT / DEFAULT_BU_CSV_PATH:
        parts.extend(["--bu-csv", str(bu_csv)])
    if Path(output_md) != ROOT / DEFAULT_MD_OUTPUT_PATH:
        parts.extend(["--output-md", str(output_md)])
    if Path(output_json) != ROOT / DEFAULT_JSON_OUTPUT_PATH:
        parts.extend(["--output-json", str(output_json)])
    return shlex.join(parts)


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
        help="Maintenance cycle label for Measurement Log and Notes (required for production rows).",
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

    invocation_command = format_invocation_command(args)
    report, markdown = write_ck_hotspot_compression_report(
        md_output_path=args.output_md,
        json_output_path=args.output_json,
        watch_start=args.watch_start,
        measurement_commit=args.measurement_commit,
        bu_csv_path=args.bu_csv,
        cycle_label=args.cycle_label,
        repo_root=ROOT,
        invocation_command=invocation_command,
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
