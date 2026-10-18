# 02 — Baseline and Environment

Revision `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Python `3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]`. Client date October 17, 2026, America/New_York. Dirty worktree captured completely in `working_tree_before.txt`; no reset, checkout or cleanup. No applicable AGENTS.md was found at the workspace/ancestor paths inspected or by repository file search.

Protected baseline: 1246 files under game/data/tests/tools; changed paths: `[]`. Existing dirty/untracked source is the actual investigation baseline, not pristine HEAD. Research files are under artifacts/pr_eg_r2b; established handoff files are rebuilt after preserving predecessor review.

Provider: existing strict_social route selects gpt-4.1-mini; returned gpt-4.1-mini-2025-04-14. Explicit Responses endpoint https://api.openai.com/v1; provider-default sampling, max_output_tokens 3500, 45-second timeout, zero SDK retries. No production narration configuration changed. Exact synthetic prompts/usage/errors retained in provider.jsonl. Initial sandbox connection failure recovered through network-enabled execution; no credential values or active saves exported.

Test infrastructure: .venv Python, pytest, disposable seed_scene, current synchronous api.chat and external interpretation/narration seams. 41 passed, 2 deselected with the same narrowly scoped R2A selection; focused_junit.xml retains result. Historical 393 passing/19 failing not rerun. No full regression or live HTTP qualification. Source copies under sources/game; predecessor reports under history; source inventory in report 24.

Evidence classes: STATIC = current source inspection; LOCAL = executed current production functions with disposable fixtures and external wire doubles; FRESH = new provider request; HISTORICAL = retained predecessor evidence; REPLAY = recombination of measured results; INFERENCE = proposed design; UNVERIFIED = not exercised. No fresh full-production API test was performed.
