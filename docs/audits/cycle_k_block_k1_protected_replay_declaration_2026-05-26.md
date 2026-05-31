# Cycle K — Block K1 Protected Replay Declaration

## Outcome

This block creates the governance declaration for protected replay. It does not modify production behavior, replay execution, assertions, fixtures, markers, or CI.

Canonical manifest: `docs/testing/protected_replay_manifest.md`.

## Sources Reviewed

- `tests/test_golden_replay.py`
- `tests/helpers/golden_replay.py`
- `docs/archive/dead_governance/2026-05-31/golden_replay_baseline_2026-05-11.md` (historical; current protected replay authority is `docs/testing/protected_replay_manifest.md`)
- `docs/audits/cycle_k_replay_promotion_recon_2026-05-26.md`

The committed baseline identifies nine canonical scenario rows. Eight are now declared `PROTECTED`; the compact three-branch schema smoke is `SUPPORTING`. Synthetic observation IDs used by projection and diagnostic tests are supporting test inputs, not scenario entries.

## Current Golden Scenario Inventory

| Scenario ID | Test Name | Category | Protected Surface | Execution Shape | Current Baseline Status | Declaration |
|---|---|---|---|---|---|---|
| `directed_npc_question` | `test_golden_replay_directed_npc_question_structural_invariants` | `END_TO_END_PROTECTED` | Directed target, social/dialogue route, selected speaker, final emitted source, scaffold safety. | End-to-end | Pass | `PROTECTED` |
| `vocative_override_after_prior_continuity` | `test_golden_replay_vocative_override_after_prior_continuity_structural_invariants` | `END_TO_END_PROTECTED` | Explicit vocative override after continuity, selected speaker, observable route/target, scaffold safety. | End-to-end | Pass | `PROTECTED` |
| `wrong_speaker_strict_social_emission` | `test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants` | `END_TO_END_PROTECTED` | Wrong-speaker removal at strict-social final emission. | End-to-end | Pass | `PROTECTED` |
| `declared_alias_dialogue_plan` | `test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants` | `DIRECT_SEAM_PROTECTED` | Declared alias validity, canonical target preservation, dialogue-plan/final-emission boundary. | Direct-seam | Pass | `PROTECTED` |
| `thin_answer_action_outcome_final_emission` | `test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants` | `END_TO_END_PROTECTED` | Concrete action outcome survival and final-emission repair/source. | End-to-end | Pass | `PROTECTED` |
| `sanitizer_scaffold_leakage` | `test_golden_replay_sanitizer_scaffold_leakage_structural_invariants` | `END_TO_END_PROTECTED` | Sanitizer/final-output protection from internal scaffold leakage. | End-to-end | Pass | `PROTECTED` |
| `opening_fallback_path` | `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership`; `test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership` | `DIRECT_SEAM_PROTECTED` | Opening fallback authorship, fallback family/timeframe, canonical owner/source. | Direct-seam | Pass | `PROTECTED` |
| `lead_followup_with_dialogue_lock` | `test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants` | `END_TO_END_PROTECTED` | Multi-turn dialogue lock and speaker/route continuity on lead follow-up. | End-to-end | Pass | `PROTECTED` |
| `scenario_spine_three_branch` | `test_golden_replay_scenario_spine_three_branch_structural_smoke` | Supporting schema smoke | Compact branch execution, branch identity representation, structural divergence, scaffold safety. | Schema-smoke plus golden harness | Pass | `SUPPORTING` |

## Supporting And Advisory Classification

| Item | Path | Declaration | Reason |
|---|---|---|---|
| Golden observation, drift, renderer, FEM/fallback/sanitizer/runtime-lineage projection tests | `tests/test_golden_replay.py`; `tests/helpers/golden_replay.py` | `SUPPORTING` | They make replay trustworthy and diagnosable, but are not acceptance scenarios. |
| Failure classifier/dashboard contract and known-bad probes | `tests/test_failure_classifier.py`; `tests/test_failure_dashboard_controlled_failures.py`; `tests/test_failure_classification_contract.py` | `SUPPORTING` | Diagnostic contracts rather than successful replay behavior. |
| JSON game-level long-session scenario-spine lane | `data/validation/scenario_spines/*.json`; `tools/run_scenario_spine_validation.py`; scenario-spine tests | `ADVISORY` | Valuable longitudinal evidence, not yet part of protected golden replay. |
| N1 synthetic scenario-spine lane | `tests/helpers/n1_scenarios.py`; `tools/run_n1_scenario_spine_validation.py`; N1 tests | `ADVISORY` | Separate validation lane by design. |
| Transcript/gauntlet replay-adjacent suites | `tests/test_transcript_*.py`; `tests/test_narration_transcript_regressions.py` | `ADVISORY` | Regression evidence outside this declared protected set. |
| Existing golden scenarios classified for removal | N/A | `DEPRECATED`: none | No repo evidence supports deprecating a current golden scenario in this governance block. |

The `scenario_id` strings used only in golden projection/classifier tests are also `SUPPORTING`: `lineage_diagnostic_only`, `recorded_lineage`, `existing_lineage_projection`, `fem_lineage_projection`, `missing_lineage_projection`, `synthetic_opening_owner`, `synthetic_opening_owner_fail_closed`, `synthetic_sealed_owner`, `synthetic_strict_social_sealed_owner`, `synthetic_visibility_owner`, `answer_prepared_projection`, `action_outcome_prepared_projection`, `rejected_prepared_projection`, `answer_prepared_absent_projection`, `action_outcome_prepared_absent_projection`, `malformed_prepared_projection`, `sanitizer_empty_projection`, `strict_social_sanitizer_split`, `sanitizer_clean_lineage`, `sanitizer_debug_lineage`, and `sanitizer_legacy_lineage`. They do not execute a protected player scenario.

## Why Direct-Seam Scenarios Are Protected

`declared_alias_dialogue_plan` and `opening_fallback_path` assert acceptance-critical ownership where final text alone is insufficient:

- An alias can produce plausible prose while violating the canonical selected speaker or dialogue-plan admission contract.
- An opening fallback can produce plausible prose while attributing authorship to a retired compatibility-local path or reporting the wrong fallback source/family.

End-to-end replay checks that a whole turn remains acceptable. Direct-seam replay checks that the final-emission owner boundary remains correct. These protections are complementary rather than redundant.

## Protected Coverage Matrix

Legend: `covered` means a protected test asserts the surface directly; `partially covered` means the surface is conditionally observable or protected by a narrower proxy such as no scaffold leakage; `not covered` means the scenario does not claim that surface.

| Protected Scenario | Routing | Speaker Ownership | Fallback Ownership | Final Emission | Sanitizer | Continuity | Dialogue Lock | Action Outcome | Scenario Identity |
|---|---|---|---|---|---|---|---|---|---|
| `directed_npc_question` | covered | covered | partially covered | covered | partially covered | not covered | partially covered | not covered | partially covered |
| `vocative_override_after_prior_continuity` | partially covered | covered | not covered | partially covered | partially covered | covered | partially covered | not covered | partially covered |
| `wrong_speaker_strict_social_emission` | not covered | covered | not covered | covered | partially covered | partially covered | covered | not covered | partially covered |
| `thin_answer_action_outcome_final_emission` | not covered | not covered | partially covered | covered | partially covered | not covered | not covered | covered | partially covered |
| `sanitizer_scaffold_leakage` | not covered | not covered | partially covered | partially covered | covered | not covered | not covered | not covered | partially covered |
| `lead_followup_with_dialogue_lock` | covered | covered | not covered | covered | partially covered | covered | covered | not covered | partially covered |
| `declared_alias_dialogue_plan` | not covered | covered | not covered | covered | partially covered | partially covered | covered | not covered | partially covered |
| `opening_fallback_path` | not covered | not covered | covered | covered | partially covered | not covered | not covered | not covered | partially covered |

## Acceptance Blind Spots

- Protected replay has no protected full-pipeline opening fallback scenario; opening ownership is protected at a direct seam.
- The supporting three-branch smoke test is not a protected execution of `data/validation/scenario_spines/frontier_gate_long_session.json`; protected replay does not currently cover long-session branch health.
- Scenario identity is carried by scenario IDs/test nodes and is structurally checked in the supporting spine smoke, but the end-to-end protected cases do not assert a separate fixture/manifest identity field at runtime.
- Several end-to-end tests prohibit scaffold leakage without asserting sanitizer lineage or exact sanitizer ownership; `sanitizer_scaffold_leakage` is the dedicated sanitizer-protected case.
- Fallback ownership is strongly protected for opening fallback and partly visible in action/sanitizer cases, but no protected aggregate fallback-frequency or unexpected-fallback budget exists.

## Promotion Recommendation

**YES.**

Replay promotion should proceed immediately to its next implementation block. The protected acceptance set is now explicitly declared: six end-to-end protected scenarios and two direct-seam protected companion scenarios. Each already has executable hard pytest assertions in the current golden replay module, and the direct-seam rows cover ownership facts that end-to-end output alone cannot reliably expose.

The identified blind spots are real but do not block initial promotion of the declared set. They define follow-on work: required CI wiring, failure artifact ergonomics, and an explicit decision on protected longitudinal scenario-spine execution.

## Change Scope

Files added in Block K1:

- `docs/testing/protected_replay_manifest.md`
- `docs/audits/cycle_k_block_k1_protected_replay_declaration_2026-05-26.md`

No production code, test logic, fixture data, or CI workflow is modified by this declaration.
