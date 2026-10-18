# 02 — Baseline and Environment

## Repository

- Revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: PR-BN bounded DM improvisational authority
- Working tree: already dirty before this cycle (about 472 short-status lines, including prior cycle files). This cycle did not revert those files and did not create a commit.
- Python: `.venv/Scripts/python.exe`

## Provider

- Configured model: `gpt-4.1-mini` (`experiments/pr_dp/__init__.py`, `CONFIGURED_MODEL`)
- Observed live route: `gpt-4.1-mini`, purpose `strict_social` or `interpretation`
- Key: loaded from the local `.env` through dotenv. The key is not recorded.
- Transport: FastAPI `TestClient` `POST /api/chat?ui_mode=player`, storage patched to a temporary directory by `tests.test_pr_ef_gm_authority.seed_scene`.
- Live budget: 120 requests, 1,000,000 input tokens, 60,000 output tokens, 1,060,000 total, 45-second timeout, narration cap 700. Usage file: `artifacts/pr_eg_r1/live.usage.jsonl`.

## Regression command

The PR-EG family plus `tests/test_pr_eg_dialogue_quality.py` and `tests/test_pr_eg_r1_continuity.py`:

```
.venv/Scripts/python.exe -m pytest
  tests/test_pr_ea_conversational_orchestration.py
  tests/test_pr_eb_conversational_continuity.py
  tests/test_turn_pipeline_shared.py
  tests/test_pr_du_player_pipeline.py
  tests/test_pr_dq_ic_ooc_messages.py
  tests/test_social.py
  tests/test_pr_br_qualifier_movement_mixed_intent.py
  tests/test_exploration_resolution.py
  tests/test_exploration_skill_checks.py
  tests/test_unparsed_movement_state_narration_integrity.py
  tests/test_save_load.py
  tests/test_runtime_persistence_regression_suite_obj14.py
  tests/test_final_emission_gate.py
  tests/test_final_emission_response_type.py
  tests/test_pr_ec_movement_partial_intent.py
  tests/test_pr_ed_provider_efficiency.py
  tests/test_pr_ef_gm_authority.py
  tests/test_pr_ef_r1_semantic_handoff.py
  tests/test_pr_ef_r2_social_authority.py
  tests/test_pr_ef_r4_authorization.py
  tests/test_pr_eg_dialogue_quality.py
  tests/test_pr_eg_r1_continuity.py
  --tb=line -q --override-ini=addopts=
```

## Baseline, re-established before production edits

The family without the new continuity file: **371 passed, 19 failed**.

Junit: `artifacts/pr_eg_r1/baseline_junit.xml`.

The 19 identities are the inherited PR-EG set. They are listed in `16_REGRESSION_COMPARISON.md`. The historical PR-EG note of 350 passed / 19 failed was not reused as the count.

## Final measurement

Same family including the new continuity tests: **393 passed, 19 failed**.

Junit: `artifacts/pr_eg_r1/regression_junit.xml`.

The 22 additional passes are the frozen continuity holdouts and the two companion tests. The 19 failing identities are unchanged.
