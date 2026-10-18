# 36 — Source and Evidence Inventory

Production: `game/host_constrained_candidates.py`, the candidate branch in `game/unified_semantic_planning.py`.

Tests: `tests/test_pr_eg_r6_r3_r1_candidates.py`.

Qualification: `artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl`, `fresh/live_usage.jsonl`, `fresh/semantic_traces.jsonl`, `fresh/live_status.json`, `matched_planner/live_turns.jsonl`, `matched_candidate_60.jsonl`, `freeze.json`, `frozen_production_holdouts.json`.

Scoring: `tools/score_pr_eg_r6_r3_r1.py`, `tools/qualify_pr_eg_r6_r3_r1.py`.

Disposable session directories under `fresh/state` and `matched_planner/state` are local run state and are not part of the portable bundle.
