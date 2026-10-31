# Campaign

Campaign: ATGB-R2-04 — Question-to-Evidence Interpretation Contract Repair
Identifier: `atgb_r2_04`
Date: 2026-10-19
Generated: 2026-10-19T17:59:28.103849-04:00
Purpose: External review of bounded existing instruction replacement; no live-provider authority

# Executive Summary

B — Conditional. Instruction and deterministic host compatibility pass; 39 explicitly blocked HTTP tests leave a regression coverage gap. 198 focused / 332 broader non-HTTP passed. No live inference or behavioral improvement claim. Historical evidence packet below is R2-03 provenance, not a new R2-04 performance result.

Objective status: `B — Conditional`.

# Changes Made

## Production changes

- One existing system instruction literal in game/live_chat_interpretation.py.

## Validation changes

- 18 new tests of effective request and R2-03 controlled host inputs.

## Tooling changes

- Disposable offline scripts packaged as reproducibility evidence; no runtime/tool owner changes.

## Documentation changes

- Eight reports and concise canonical session orientation.

## Generated artifacts

- Captured requests/schema, source diff, compatibility/authority, size and regression evidence.

# What Was Tested

- **Focused tests:** 198 passed; no HTTP transport.
- **Broader relevant tests:** 332 passed, 39 explicitly deselected HTTP cases; entry comparison 314/39.
- **Full suite:** Not run; full broader HTTP attempts interrupted before completion.
- **Runtime validation:** Four controlled substitutions pass current adapter + unchanged host record reconsideration, all in memory; original semantic failures remain historical.
- **Model/runtime boundary:** Offline only. Provider dispatch replaced; network forbidden in captures/controls; pytest live-model guard active. No live inference or connectivity diagnostic.
- **New regressions:** None demonstrated in completed scope; HTTP result unknown.
- **Pre-existing failures:** No failed case in completed entry slice; two historically known HTTP failures not reproduced in current environment. Initial partial error/failure log remains indeterminate.
- **Self-contained bundle review:** All eight reports, exact instruction before/after, working-entry diff, source/test snapshots, requests/schema, exact host controls, XML/logs and excluded node inventory are included; ZIP hashes verified after construction.

# Behavioral Evidence

## Evidence Packet: atgb_r2_03

Runs / turns: `2` / `4`
Runtime/model boundary: Historical live interpretations retained; no new model call or final API emission

### Representative success

No example observed in this campaign.

### Representative failure

Example: `S02.2`
Player classification: `representative_player_behavior`
Player: When does the curfew start?
GM: The notice board lists taxes, curfew rules, and a warning about a missing patrol.
Automated result: `FAIL`
Human review: `UNREVIEWED` - New causal assessment awaits external review; imported historical rubric preserved
Source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`

### Evaluator disagreement

No example observed in this campaign.

### Ambiguous/unexpected

No example observed in this campaign.

### Stress probe

No example observed in this campaign.

### All evaluator disagreements

No example observed in this campaign.


# Decisions Requiring Human Review

- Review bounded wording and whether HTTP coverage gap permits retention; no next action or provider trial executed.

# Known Problems / Unresolved Findings

## Campaign-specific

- 39 HTTP tests could not complete on entry; B verdict.
- No new model selection/repair-effect result.

## Pre-existing baseline

- Semantic failures retained in original ATGB logs; R1-07 live acceptance pending.

# Missing Concepts / Future Capabilities

- No new architecture requirement established.

# What This Campaign Does NOT Prove

- Improved live evidence selection or subject continuity.
- Live authority preservation, broad conversational competence, benchmark or independent generalization.
- Complete HTTP or full-suite regression.

# Recommended Next Step

External review of this ZIP and HTTP coverage limitation; stop before further implementation or live work.

# Review Bundle Contents

Bundle file count: `68`
Bundle ZIP size: `000000437011` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_r2_04/08_final_verdict_and_handoff.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_r2_04/08_final_verdict_and_handoff.md`.
- `support/artifacts/validation_evidence/atgb_r2_03/evidence_summary.md`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r2_03/evidence_summary.md`.
- `support/artifacts/validation_evidence/atgb_r2_03/evidence_manifest.json`: Standardized behavioral evidence packet consumed by the handoff. Canonical source: `artifacts/validation_evidence/atgb_r2_03/evidence_manifest.json`.
- `support/artifacts/atgb/atgb_r2_04/after_nonhttp.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/after_nonhttp.txt`.
- `support/artifacts/atgb/atgb_r2_04/after_nonhttp.xml`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/after_nonhttp.xml`.
- `support/artifacts/atgb/atgb_r2_04/baseline.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/baseline.json`.
- `support/artifacts/atgb/atgb_r2_04/baseline_bundled.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/baseline_bundled.txt`.
- `support/artifacts/atgb/atgb_r2_04/baseline_nonhttp.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/baseline_nonhttp.txt`.
- `support/artifacts/atgb/atgb_r2_04/baseline_nonhttp.xml`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/baseline_nonhttp.xml`.
- `support/artifacts/atgb/atgb_r2_04/baseline_regression.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/baseline_regression.txt`.
- `support/artifacts/atgb/atgb_r2_04/baseline_regression_retry.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/baseline_regression_retry.txt`.
- `support/artifacts/atgb/atgb_r2_04/contract_preservation.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/contract_preservation.json`.
- `support/artifacts/atgb/atgb_r2_04/effective_after.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/effective_after.json`.
- `support/artifacts/atgb/atgb_r2_04/effective_before.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/effective_before.json`.
- `support/artifacts/atgb/atgb_r2_04/entry_hashes.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/entry_hashes.json`.
- `support/artifacts/atgb/atgb_r2_04/focused.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/focused.txt`.
- `support/artifacts/atgb/atgb_r2_04/focused.xml`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/focused.xml`.
- `support/artifacts/atgb/atgb_r2_04/focused_final.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/focused_final.txt`.
- `support/artifacts/atgb/atgb_r2_04/focused_final.xml`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/focused_final.xml`.
- `support/artifacts/atgb/atgb_r2_04/focused_verified.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/focused_verified.txt`.
- `support/artifacts/atgb/atgb_r2_04/focused_verified.xml`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/focused_verified.xml`.
- `support/artifacts/atgb/atgb_r2_04/historical_compatibility.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/historical_compatibility.json`.
- `support/artifacts/atgb/atgb_r2_04/historical_provenance_verification.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/historical_provenance_verification.json`.
- `support/artifacts/atgb/atgb_r2_04/http_after_inventory.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/http_after_inventory.json`.
- `support/artifacts/atgb/atgb_r2_04/http_baseline_inventory.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/http_baseline_inventory.json`.
- `support/artifacts/atgb/atgb_r2_04/instruction_after.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/instruction_after.txt`.
- `support/artifacts/atgb/atgb_r2_04/instruction_before.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/instruction_before.txt`.
- `support/artifacts/atgb/atgb_r2_04/integrity.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/integrity.json`.
- `support/artifacts/atgb/atgb_r2_04/live_chat_interpretation.py.before`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/live_chat_interpretation.py.before`.
- `support/artifacts/atgb/atgb_r2_04/NEXT_SESSION.md.before`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/NEXT_SESSION.md.before`.
- `support/artifacts/atgb/atgb_r2_04/orientation.diff`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/orientation.diff`.
- `support/artifacts/atgb/atgb_r2_04/prompt_sizes.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/prompt_sizes.json`.
- `support/artifacts/atgb/atgb_r2_04/regression_summary.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/regression_summary.json`.
- `support/artifacts/atgb/atgb_r2_04/repository_status_after.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/repository_status_after.txt`.
- `support/artifacts/atgb/atgb_r2_04/repository_status_before.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/repository_status_before.txt`.
- `support/artifacts/atgb/atgb_r2_04/review_config.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/review_config.json`.
- `support/artifacts/atgb/atgb_r2_04/schema_after.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/schema_after.json`.
- `support/artifacts/atgb/atgb_r2_04/schema_inventory.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/schema_inventory.json`.
- `support/artifacts/atgb/atgb_r2_04/sensitive_payload_check.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/sensitive_payload_check.json`.
- `support/artifacts/atgb/atgb_r2_04/source.diff`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_04/source.diff`.
- `support/development/reports/atgb_r2_04/01_baseline_and_contract_inventory.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/reports/atgb_r2_04/01_baseline_and_contract_inventory.md`.
- `support/development/reports/atgb_r2_04/02_instruction_change_analysis.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/reports/atgb_r2_04/02_instruction_change_analysis.md`.
- `support/development/reports/atgb_r2_04/03_implementation_diff.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/reports/atgb_r2_04/03_implementation_diff.md`.
- `support/development/reports/atgb_r2_04/04_deterministic_contract_validation.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/reports/atgb_r2_04/04_deterministic_contract_validation.md`.
- `support/development/reports/atgb_r2_04/05_historical_compatibility.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/reports/atgb_r2_04/05_historical_compatibility.md`.
- `support/development/reports/atgb_r2_04/06_authority_and_regression.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/reports/atgb_r2_04/06_authority_and_regression.md`.
- `support/development/reports/atgb_r2_04/07_prompt_size_and_performance.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/reports/atgb_r2_04/07_prompt_size_and_performance.md`.
- `support/game/live_chat_interpretation.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `game/live_chat_interpretation.py`.
- `support/tests/test_atgb_r2_04_question_evidence_contract.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `tests/test_atgb_r2_04_question_evidence_contract.py`.
- `support/tests/test_atgb_r1_07_correction_contract.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `tests/test_atgb_r1_07_correction_contract.py`.
- `support/tests/test_atgb_r1_04_readiness.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `tests/test_atgb_r1_04_readiness.py`.
- `support/docs/NEXT_SESSION.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/validation_evidence_standard.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `docs/validation_evidence_standard.md`.
- `support/docs/product_realization_validation.md`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `docs/product_realization_validation.md`.
- `support/development/tmp/atgb_r2_04_baseline.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/tmp/atgb_r2_04_baseline.py`.
- `support/development/tmp/atgb_r2_04_capture.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/tmp/atgb_r2_04_capture.py`.
- `support/development/tmp/atgb_r2_04_evidence.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/tmp/atgb_r2_04_evidence.py`.
- `support/development/tmp/atgb_r2_04_nonhttp.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/tmp/atgb_r2_04_nonhttp.py`.
- `support/development/tmp/atgb_r2_04_package.py`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `development/tmp/atgb_r2_04_package.py`.
- `support/artifacts/atgb/atgb_r2_03/adapter_controls.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_03/adapter_controls.json`.
- `support/artifacts/atgb/atgb_r2_03/context_and_original_logs.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_03/context_and_original_logs.json`.
- `support/artifacts/atgb/atgb_r2_03/historical_trace_excerpts.json`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_03/historical_trace_excerpts.json`.
- `support/artifacts/atgb/atgb_r2_02/regression_slice.txt`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_r2_02/regression_slice.txt`.
- `support/artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_03/S02/stores/S02-ae287e6dca444d4f88da672a81b41b87/session_log.jsonl`.
- `support/artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/session_log.jsonl`: Explicit source/test, baseline, captured request, deterministic compatibility or validation evidence needed for external review. Canonical source: `artifacts/atgb/atgb_03c/S05/stores/S05-303c654ed3bc4f3988158742cb13bc5d/session_log.jsonl`.

## Explicit omissions

- `artifacts/atgb/atgb_r2_04/schema_before.json`: duplicate content of artifacts/atgb/atgb_r2_04/schema_after.json; canonical reference retained

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
