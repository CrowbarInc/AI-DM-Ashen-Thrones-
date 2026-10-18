"""PR-DP live contract qualification.

Experiment-only. Production saves stay untouched. The gameplay resolvers
are not called. engine_submission is not connected to execution.
"""

from __future__ import annotations

import os

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

EXPERIMENT = "PR-DP"
CONFIGURED_MODEL = "gpt-4.1-mini"
