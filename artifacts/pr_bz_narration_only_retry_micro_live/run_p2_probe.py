#!/usr/bin/env python3
"""PR-BZ controlled P2-only micro-live validation.

Loads the PR-BX live harness without changing production code. Phase 0 keeps
the original P1/P2/P3 selector controls, while live execution is limited to P2.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts" / "pr_bx_narration_only_micro_live" / "run_probes.py"
OUT = ROOT / "artifacts" / "pr_bz_narration_only_retry_micro_live" / "evidence"

spec = importlib.util.spec_from_file_location("pr_bx_run_probes", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"could not load {SOURCE}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

module.OUT = OUT
module.PROBES = (
    {
        "id": "P2",
        "scene": "baker",
        "player": "Baker, which loaf do you usually keep for yourself?",
    },
)

if __name__ == "__main__":
    raise SystemExit(module.main(prelive_only="--prelive-only" in sys.argv))
