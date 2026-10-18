# 02 — Baseline and Environment

Repository revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`d31beb7`, PR-BN bounded DM improvisational authority).

The worktree was already dirty before this cycle. Cycle files touched for PR-EG-R3-R1:

- `game/expressive_dialogue.py` (untracked module, extended)
- `game/dialogue_authority.py` (untracked module, extended)
- `game/conversational_continuity.py` (untracked module, extended)
- `game/conversational_orchestration.py` (untracked module, extended)
- `game/api.py` (tracked, modified)
- `tests/test_pr_eg_r3_r1_expression_semantics.py`
- `tools/validate_pr_eg_r3_r1.py`

Provider configuration recorded on the live usage log: configured model `gpt-4.1-mini`, response model `gpt-4.1-mini-2025-04-14`. Expression calls use temperature 0.2 and a maximum of 80 output tokens. Pytest sets `ASHEN_DISABLE_EXPRESSION_GENERATION=1`. The live runner sets expression generation on and records usage to `artifacts/pr_eg_r3_r1/live_usage.jsonl`. The API key is not recorded.

PR-EG-R3 predecessor, retained as the comparison baseline and not assumed to still be the tree before this cycle's edits: 605 passed / 25 failed of 630 relevant tests; 10/10 frozen holdouts; 27 fresh turns; 22 provider calls; 12 expression calls; 8/12 adopted; 0 narration; 0 retries; 20,652 input tokens; 2,150 output tokens; 1.36 seconds mean turn latency. Final personal characterization in that repaired sample: 0/3 adopted.

This cycle's confirming relevant suite is {'failed': 25, 'passed': 692} of 717 tests. The extra tests are the R3-R1 matrix, the R3 expression file, and the R2C-R2 reference-eligibility file. The full repository suite was not run.
