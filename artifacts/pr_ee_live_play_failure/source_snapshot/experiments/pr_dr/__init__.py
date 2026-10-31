"""PR-DR live interpretation wired to the disposable PR-DQ slice.

Experiment-only. Production chat, narration, and save files are not used.
"""

from __future__ import annotations

import os

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

EXPERIMENT = "PR-DR"
MODEL_ID = "gpt-4.1-mini"
