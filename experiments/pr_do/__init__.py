"""PR-DO intent, claim, and authority separation.

Experiment-only. This package does not call providers, execute plans,
roll dice, or write production saves.
"""

from __future__ import annotations

import os

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

LIVE_PROVIDER_CALLS = 0


def refuse_live_provider_call() -> None:
    """Stop condition. PR-DO has no provider path."""
    raise RuntimeError("PR-DO forbids live provider calls")
