# pr_play_compound_action_admission_guard — B/PARTIAL

The exact coat-drop/Cinderwatch failure and both action orders are repaired. The specified matrix and four recovery sequences pass. This is **not a reliable general compound boundary**: four additional controlled requests still partially execute. No A/PASS claim.

Original request: travel to market quarter, turn 4→5, coat retained. Final request: clarification, frontier gate, turn 4→4, character/inventory/world/scene/combat/clocks unchanged. Explicit subsequent travel succeeds.

Final matrix: 67 HTTP requests, zero assertion failures; independent cross-request acceptance: 69/69 checks. Durable fresh-process retry: all seven checks pass. Additional boundary: 2/6 safe, 4/6 unsafe. Broad replays: 101 + 86 requests; primary forty outputs unchanged. Combined 408 passed /17 failed before and after, same identities. Original focused 611/611; expanded focused 744/746 with two inherited failures; dedicated/parser selection 95/96 with one inherited failure, including all 29 new tests passing. Live provider calls zero.

Machine evidence: `artifacts/pr_play_compound_action_admission_guard/` (repository relative). Final sources: `game/api.py`, `game/conversational_orchestration.py`; tests: `tests/test_compound_action_admission.py`. Task-start snapshots and milestone-only diffs preserve the distinction from earlier dirty work.

Stop here. No commit/push or next milestone. See LIMITATIONS and NEXT_STEP_DECISION before relying on compound safety.
