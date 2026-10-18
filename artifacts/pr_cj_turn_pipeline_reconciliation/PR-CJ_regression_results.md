# PR-CJ Regression Results

Live provider calls: 0. No game code changed, so these results describe the current dirty worktree.

## 1. Shared turn pipeline

Command:

`python -m pytest tests/test_turn_pipeline_shared.py --tb=line --junitxml=artifacts/pr_cj_turn_pipeline_reconciliation/pytest_shared.xml --basetemp=artifacts/pr_cj_turn_pipeline_reconciliation/pytest_basetemp_parent/run1 -p no:cacheprovider`

Result: 33 failed, 32 passed, 1 warning, 8.16s.

## 2. PR-CI authored-answer finalization and social relevance

Command:

`python -m pytest tests/test_social_question_relevance_answer_selection.py -q --tb=line -o addopts= --basetemp=C:\Users\Master Mandalcio\AppData\Local\prcj_pytest\relevance -p no:cacheprovider`

Result: 25 passed, 1 warning, 1.69s.

This file contains the four previously failing HTTP targets from PR-CI.

## 3. PR-CC

Command:

`python -m pytest tests/test_pr_cc_social_reply_reconciliation.py -q --tb=no -o addopts= --basetemp=C:\Users\Master Mandalcio\AppData\Local\prcj_pytest\split1 -p no:cacheprovider`

Result: 11 passed, 1.15s.

## 4. PR-CE

Command:

`python -m pytest tests/test_pr_ce_subjective_preference_classification.py -q --tb=no -o addopts= --basetemp=C:\Users\Master Mandalcio\AppData\Local\prcj_pytest\split2 -p no:cacheprovider`

Result: 13 passed, 1.17s.

## 5. PR-BY

Command:

`python -m pytest tests/test_pr_by_narration_only_retry_contract.py -q --tb=no -o addopts= --basetemp=C:\Users\Master Mandalcio\AppData\Local\prcj_pytest\split3 -p no:cacheprovider`

Result: 22 passed, 1.21s.

## 6. PR-BW

Command:

`python -m pytest tests/test_pr_bw_narration_only_envelope.py -q --tb=no -o addopts= --basetemp=C:\Users\Master Mandalcio\AppData\Local\prcj_pytest\split4 -p no:cacheprovider`

Result: 5 passed, 1.20s.

## 7. Immutable response

Command:

`python -m pytest tests/test_pr_br_continuation18_immutable_boundary.py tests/test_turn_packet_stage_diff_integration.py tests/test_final_emission_gate.py -q --tb=line -o addopts= --basetemp=C:\Users\Master Mandalcio\AppData\Local\prcj_pytest\immutable -p no:cacheprovider`

Result: 27 passed, 1 warning, 1.82s.

## 8. Authority and C18-adjacent

Command:

`python -m pytest tests/test_pr_br_gm_resolution_decision.py tests/test_pr_br_decision_owned_realization_claims.py tests/test_pr_br_decision_semantic_fidelity_slice3.py tests/test_pr_br_structured_realization_envelope.py tests/test_pr_br_resolution_contract.py -q --tb=line -o addopts= --basetemp=C:\Users\Master Mandalcio\AppData\Local\prcj_pytest\authority -p no:cacheprovider`

Result: 107 passed, 1 warning, 3.72s.

## HEAD comparison

Detached worktree at `d31beb7`, same virtualenv, HEAD's copy of the suite: 6 failures. Names are in `PR-CJ_historical_attribution.md`. The worktree was removed afterward.

## Not claimed

Broad repository regression was not run. Shared turn-pipeline success is not claimed.
