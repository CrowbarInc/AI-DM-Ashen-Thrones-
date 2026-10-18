"""PR-DM hybrid interpretation refinement.

Experiment-only. This package does not call providers, execute plans,
or write production saves.
"""

from __future__ import annotations

import os

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
