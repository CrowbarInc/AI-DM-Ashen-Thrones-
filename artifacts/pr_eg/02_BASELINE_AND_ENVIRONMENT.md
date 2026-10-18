# 02 — Baseline and Environment

## Repository

- Revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: PR-BN bounded DM improvisational authority
- Working tree: already dirty before this cycle, including many game modules, tests, and prior artifacts. This cycle did not revert those files and did not create a commit.
- Python: `.venv/Scripts/python.exe`

## Provider

- Configured model: `gpt-4.1-mini` (`experiments/pr_dp/__init__.py`, `CONFIGURED_MODEL`)
- Observed live model: `gpt-4.1-mini-2025-04-14`
- Key: loaded from the local `.env` through dotenv. The key is not recorded in these artifacts.
- Live qualification sets `ASHEN_DISABLE_LIVE_INTERPRETATION=0` after imports that would otherwise disable it.
- Transport: FastAPI `TestClient` `POST /api/chat?ui_mode=player`, storage patched to a temporary directory by `tests.test_pr_ef_gm_authority.seed_scene`.
- Budget for the live run: 80 requests, 800,000 input tokens, 40,000 output tokens, 840,000 total tokens, 45-second provider timeout, 700-token narration cap.

## Regression command

The PR-EF-R2 family plus `tests/test_pr_ef_r4_authorization.py`:

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
  --tb=line -q --override-ini=addopts=
```

Junit: `artifacts/pr_eg/baseline_junit.xml` before production edits, `artifacts/pr_eg/regression_junit.xml` after the final code.

## Baseline, re-established before production edits

369 tests. 349 passed. 20 failed. 31.37 seconds.

The 20 identities match the PR-EF-R4 historical set. They are listed in `15_REGRESSION_COMPARISON.md`.

## Dialogue generation paths that already existed

- Interpretation, then `assess_addressee_grounding`, then the social resolver.
- `authored_answer_sufficient_for_question` selected a topic. A general or clarification dimension was treated as sufficient even when the sentence did not answer the predicate.
- `_bounded_social_reply_plan_for_missing_topic` could report `authoritative_answer_available` with speech authority `none` when an earlier topic existed.
- Strict-social narration ran unless `social_narration_unnecessary` saw the closed consequential-information plan.
- Failed narration retried once, then `safe_nonresolution` could say the speaker cannot answer from what is settled here.
- Harmless subjective replies and the bounded-improvisation ledger already existed. Ordinary factual gaps did not enter that lane.
