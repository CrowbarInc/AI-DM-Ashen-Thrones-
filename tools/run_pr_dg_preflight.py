"""Run the PR-DG preflight and refresh its artifacts. No provider calls."""
from __future__ import annotations

import os

os.environ.setdefault("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")

from experiments.pr_dg.reports import write_reports
from experiments.pr_dg.runner import run_preflight, write_results


def main() -> None:
    payload = run_preflight(measure_narration=True)
    path = write_results(payload)
    write_reports()
    print(path)
    print(payload["decision"]["code"], payload["decision"]["reason"])


if __name__ == "__main__":
    main()
