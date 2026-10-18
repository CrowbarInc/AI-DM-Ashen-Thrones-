# PR-DX Evidence

Decision: A - EXPLICIT MODE BOUNDARY REPAIRED.

Live provider calls: 0. Verification used ASHEN_DISABLE_LIVE_INTERPRETATION=1, ASHEN_DISABLE_PROVIDER_CALLS=1, ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1, and disposable data under artifacts/pr_dx_mode_boundary/disposable_data.

The original PR-DW failure text now resolves at the message boundary as OOC before gameplay parser, resolver, narration, world tick, turn counter, or time-pressure advancement.

Focused evidence: 33 IC/OOC focused checks passed; provider-disable guard passed; real HTTP OOC and browser OOC checks passed. Broad regression command collected 203 passed / 29 failed inherited shared-pipeline failures; no PR-DX focused failure remains.
## PR-DX_recommendation.md
See execution_trace.json and focused_tests.txt for command/evidence details. The implemented boundary lives in game/api.py; provider disable lives in game/gm.py.

