"""Run PR-DJ deterministic selective interpretation preflight."""
from __future__ import annotations

from experiments.pr_dj.reports import generate_reports, refresh_current_review


def main() -> None:
    summary = generate_reports()
    zip_path = refresh_current_review(summary)
    print(f"PR-DJ decision: {summary['decision']}")
    print(f"CURRENT_REVIEW: {zip_path}")


if __name__ == "__main__":
    main()

