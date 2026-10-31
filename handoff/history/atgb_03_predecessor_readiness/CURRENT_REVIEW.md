# Campaign

Campaign: ATGB-02A Baseline Readiness and Reproducibility
Identifier: `atgb_02a_baseline_readiness`
Date: 2026-10-18
Generated: 2026-10-18T20:50:37.416093+00:00
Purpose: Validate starting conditions and reproducibility without live providers or production gameplay changes.

# Executive Summary

All ten scenarios have verified machine prerequisites in frozen frontier-gate-v1. S07 and S09 opening delivery remains partially verified; narrative assumptions remain unverified in every scenario. No blocked scenario in the intact baseline. Repeated resets are equivalent. Focused checks: 24 passed; adjacent regression: 49 passed. Replaced mutable working-data bootstrap with a pinned snapshot of an existing replay fixture and defaults; preflight blocks missing or incompatible prerequisites before chat. No production gameplay change, live evaluation, performance score, generalization claim or new Product Realization campaign. Failure class: evaluation instrument setup. Await review before ATGB-03.

Objective status: `MACHINE PREREQUISITES VERIFIED; NARRATIVE DELIVERY PARTIALLY VERIFIED; AWAIT REVIEW`.

# Changes Made

## Production changes

- None. Production reset and gameplay semantics unchanged. Canonical data preserved.

## Validation changes

- 24 readiness/infrastructure tests pass, including repeated resets and rejection paths.

## Tooling changes

- Frozen baseline validator, preflight before chat, preflight-only CLI, separate result reporting; workspace temporary stores.

## Documentation changes

- Readiness matrix, execution instructions, explicit S07 partition supersession notes and NEXT_SESSION update.

## Generated artifacts

- Provider-disabled preflight of all ten scenarios; validation results and logs. No gameplay performance evidence.

# What Was Tested

- **Focused tests:** 24 passed. Existing S06 host-chat regression submits four ordered turns with all providers disabled; repeated initialization test resets 10 scenarios twice without chat.
- **Broader relevant tests:** 49 passed: playability evaluator, review-handoff and validation-evidence-standard tests.
- **Full suite:** Not run.
- **Runtime validation:** 20 repeated isolated resets plus final 10-scenario preflight. Same normalized state hash. No live evaluation.
- **Model/runtime boundary:** Providers disabled; no model evaluation or gameplay scoring. No live run authorized.
- **New regressions:** None observed in the validated scope.
- **Pre-existing failures:** Sandbox socketpair initialization timeout and transient atomic rename denial are preserved as environmental attempts; final authorized provider-disabled tests passed.
- **Self-contained bundle review:** The ZIP contains the matrix, source provenance and complete frozen baseline, preflight and isolation code, all scenario fixtures, execution instructions and validation evidence. It supports review of verified, partially verified, blocked and unverified starting conditions without an external repository search. No live-provider result is claimed.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- Accept the frozen baseline and readiness limitations before ATGB-03. No live baseline authorized by this package.

# Known Problems / Unresolved Findings

## Campaign-specific

- S07/S09 opening context is authored but delivery not verified by silent reset.
- Narrative assumptions remain unverified for all scenarios.
- Windows sandbox blocks local asyncio socketpair startup; authorized provider-disabled test run passed outside sandbox.

## Pre-existing baseline

- Held-out scenarios were previously exposed.
- PR-BL versus later PR-EG session orientation remains unreconciled.

# Missing Concepts / Future Capabilities

- Live baseline with human rubric review (not authorized here).
- Opening context delivery evidence for S07 and S09.

# What This Campaign Does NOT Prove

- Improved gameplay or conversational competence.
- A live ATGB performance result.
- Related or independent conversational generalization.
- Full-suite regression safety.

# Recommended Next Step

Stop. Review readiness matrix and baseline. Await review before ATGB-03; do not initiate live evaluation or a Product Realization campaign.

# Review Bundle Contents

Bundle file count: `59`
Bundle ZIP size: `000000246588` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/development/reports/atgb_02a_readiness.md`: Primary campaign standard/report used to orient the review. Canonical source: `development/reports/atgb_02a_readiness.md`.
- `support/artifacts/atgb/atgb_02a/adjacent.txt`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/adjacent.txt`.
- `support/artifacts/atgb/atgb_02a/adjacent.xml`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/adjacent.xml`.
- `support/artifacts/atgb/atgb_02a/final_focused.txt`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/final_focused.txt`.
- `support/artifacts/atgb/atgb_02a/final_focused.xml`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/final_focused.xml`.
- `support/artifacts/atgb/atgb_02a/host_diagnostic.txt`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/host_diagnostic.txt`.
- `support/artifacts/atgb/atgb_02a/legacy_reset_findings.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/legacy_reset_findings.json`.
- `support/artifacts/atgb/atgb_02a/preflight/report.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/preflight/report.md`.
- `support/artifacts/atgb/atgb_02a/preflight/result.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/preflight/result.json`.
- `support/artifacts/atgb/atgb_02a/validation_results.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `artifacts/atgb/atgb_02a/validation_results.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/campaign.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/campaign.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/character.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/character.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/conditions.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/conditions.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/manifest.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/manifest.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/scenes/frontier_gate.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/scenes/market_quarter.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/scenes/market_quarter.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/scenes/old_milestone.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/scenes/old_milestone.json`.
- `support/data/validation/atgb/baselines/frontier-gate-v1/world.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/baselines/frontier-gate-v1/world.json`.
- `support/data/validation/atgb/corpus.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/corpus.json`.
- `support/data/validation/atgb/held_out/S07.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/held_out/S07.json`.
- `support/data/validation/atgb/held_out/S09.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/held_out/S09.json`.
- `support/data/validation/atgb/held_out/S10.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/held_out/S10.json`.
- `support/data/validation/atgb/visible/S01.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/visible/S01.json`.
- `support/data/validation/atgb/visible/S02.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/visible/S02.json`.
- `support/data/validation/atgb/visible/S03.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/visible/S03.json`.
- `support/data/validation/atgb/visible/S04.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/visible/S04.json`.
- `support/data/validation/atgb/visible/S05.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/visible/S05.json`.
- `support/data/validation/atgb/visible/S06.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/visible/S06.json`.
- `support/data/validation/atgb/visible/S08.json`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `data/validation/atgb/visible/S08.json`.
- `support/development/reports/atgb_01_conversational_benchmark_design.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `development/reports/atgb_01_conversational_benchmark_design.md`.
- `support/development/reports/atgb_01_scenario_catalog.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `development/reports/atgb_01_scenario_catalog.md`.
- `support/development/reports/atgb_02_benchmark_specification.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `development/reports/atgb_02_benchmark_specification.md`.
- `support/development/reports/atgb_02_execution.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `development/reports/atgb_02_execution.md`.
- `support/docs/DEVELOPMENT_CONSTITUTION.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `docs/DEVELOPMENT_CONSTITUTION.md`.
- `support/docs/NEXT_SESSION.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `docs/NEXT_SESSION.md`.
- `support/docs/state_authority_model.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `docs/state_authority_model.md`.
- `support/docs/validation_evidence_standard.md`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `docs/validation_evidence_standard.md`.
- `support/game/campaign_reset.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `game/campaign_reset.py`.
- `support/game/campaign_state.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `game/campaign_state.py`.
- `support/game/defaults.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `game/defaults.py`.
- `support/game/fresh_campaign_verify.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `game/fresh_campaign_verify.py`.
- `support/game/storage.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `game/storage.py`.
- `support/game/world.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `game/world.py`.
- `support/tests/helpers/golden_replay_fixtures.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tests/helpers/golden_replay_fixtures.py`.
- `support/tests/test_atgb_infrastructure.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tests/test_atgb_infrastructure.py`.
- `support/tests/test_atgb_readiness.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tests/test_atgb_readiness.py`.
- `support/tools/atgb/__init__.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/__init__.py`.
- `support/tools/atgb/baseline.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/baseline.py`.
- `support/tools/atgb/budget.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/budget.py`.
- `support/tools/atgb/chat_worker.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/chat_worker.py`.
- `support/tools/atgb/driver.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/driver.py`.
- `support/tools/atgb/fixtures.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/fixtures.py`.
- `support/tools/atgb/isolation.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/isolation.py`.
- `support/tools/atgb/preflight.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/preflight.py`.
- `support/tools/atgb/results.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/results.py`.
- `support/tools/atgb/worksheet.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/atgb/worksheet.py`.
- `support/tools/run_atgb.py`: Review initialization authority, source provenance, prerequisites or provider-disabled validation. Canonical source: `tools/run_atgb.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
