"""PR-DT authoritative narration experiment.

Experiment-only. Production narration and save paths are not modified.
"""

from __future__ import annotations

import os

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

EXPERIMENT = "PR-DT"
MODEL_ID = "gpt-4.1-mini"
