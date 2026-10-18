"""PR-DQ disposable gameplay slice and IC/OOC message boundary.

Experiment-only. No provider calls and no production UI. One chronological
message history. OOC messages are not authoritative gameplay.
"""

from __future__ import annotations

import os

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

EXPERIMENT = "PR-DQ"
LIVE_PROVIDER_CALLS = 0


def refuse_live_provider_call() -> None:
    """Stop condition. PR-DQ has no provider path."""
    raise RuntimeError("PR-DQ forbids live provider calls")
