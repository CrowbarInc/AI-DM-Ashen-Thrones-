"""Run PR-DK deterministic escalation routing investigation."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.pr_dk.runner import generate_reports, refresh_current_review


def main() -> None:
    payload = generate_reports()
    zip_path = refresh_current_review(payload)
    print("PR-DK decision: C")
    print(f"CURRENT_REVIEW: {zip_path}")


if __name__ == "__main__":
    main()
