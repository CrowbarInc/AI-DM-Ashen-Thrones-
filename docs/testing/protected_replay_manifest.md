# Protected Replay Manifest

## Purpose

This manifest declares the canonical protected replay set for acceptance review. It is governance-only: it does not change runtime behavior, pytest assertions, markers, selection, or CI wiring.

Classification meanings:

| Status | Meaning |
|---|---|
| `PROTECTED` | A failure should block acceptance. |
| `SUPPORTING` | Useful replay signal, but not itself an acceptance blocker. |
| `ADVISORY` | Informational or exploratory evidence only. |
| `DEPRECATED` | No longer intended for long-term protection. |

Current executable location: `tests/test_golden_replay.py`. Current helper/projection location: `tests/helpers/golden_replay.py`. Current documentary baseline: `audits/golden_replay_baseline_2026-05-11.md`.

Protected replay reproduction command:

```bash
python -m pytest tests/test_golden_replay.py -q
```

`tests/test_golden_replay.py` currently contains protected and supporting tests in one pytest module. This manifest classifies their acceptance ownership; it does not alter today's test execution behavior.

## Metadata Ownership

Golden replay owns `scenario_id` as the replay acceptance identifier. Scenario-spine fixtures own `spine_id`, `branch_id`, and per-turn `turn_id`; when a golden replay is scenario-spine-backed, those fixture identifiers remain source metadata rather than replacing the golden `scenario_id`. The N1 longitudinal lane uses `scenario_spine_id` and remains a separate synthetic/advisory lane, not a silent extension of protected golden replay.

Text fields are layer-specific projections: `player_facing_text` is the runtime response field, `gm_text` is a snapshot/transcript projection, and `final_text` is the golden replay observed assertion surface. Protected replay failure reports may include `source_path`, `branch_id`, and `turn_id` when a replay row can be traced back to a scenario-spine fixture.

## End-To-End Protected Scenarios

Category: `END_TO_END_PROTECTED`. These cases execute turns through `run_golden_replay(...)` and the chat pipeline with deterministic test setup/model responses.

| Scenario ID | Test | Purpose | Invariant Protected | Status | Reproduction Command |
|---|---|---|---|---|---|
| `directed_npc_question` | `test_golden_replay_directed_npc_question_structural_invariants` | Preserve directed NPC question routing through final output. | Runner remains target/speaker; route remains social/dialogue-shaped; output has a non-global emitted source and no scaffold leakage. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_directed_npc_question_structural_invariants -q` |
| `vocative_override_after_prior_continuity` | `test_golden_replay_vocative_override_after_prior_continuity_structural_invariants` | Preserve explicit address override after an established interaction. | Guard becomes selected speaker after direct vocative; observable route/trace, when emitted, agrees with the switch; output does not leak scaffolding. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants -q` |
| `wrong_speaker_strict_social_emission` | `test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants` | Prevent illegal speaker attribution from surviving strict-social finalization. | Canonical runner owns the reply; injected `Merchant` attribution is absent from final text; output has no scaffold leakage. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants -q` |
| `thin_answer_action_outcome_final_emission` | `test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants` | Preserve concrete action outcome repair across final emission. | `action_outcome` remains required and repaired; final source is not global fallback; final text remains concrete and non-scaffold. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants -q` |
| `sanitizer_scaffold_leakage` | `test_golden_replay_sanitizer_scaffold_leakage_structural_invariants` | Prevent internal planning/validation text from reaching the player. | Planner/router/validator/scaffold terms are absent; emitted text remains non-empty; legacy sanitizer rewrite is not reactivated. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants -q` |
| `lead_followup_with_dialogue_lock` | `test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants` | Preserve multi-turn NPC follow-up continuity after a lead is established. | Tavern runner remains selected speaker; dialogue/social route persists; observable canonical target remains the runner; no scaffold leakage. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants -q` |
| `frontier_gate_social_inquiry_25_turn` | `test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability` | Preserve sustained-play structural stability across the full canonical 25-turn social inquiry branch. | Replay completes all 25 deterministic turns with bounded route/speaker drift, no scaffold leakage, clean/warning continuity classification, no progressive degradation, no late fallback spike, no fallback owner oscillation, no fallback behavior repair loop, bounded unavailable/fallback coupling, and compact lineage-backed artifact output. This protected golden replay is backed by `data/validation/scenario_spines/frontier_gate_long_session.json` branch `branch_social_inquiry`. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability -q` |

## Direct-Seam Protected Scenarios

Category: `DIRECT_SEAM_PROTECTED`. A direct-seam scenario is protected where the acceptance-critical invariant is owned at final-emission/gate composition and a full chat run would add routing/setup noise without improving the ownership check.

These cases are not redundant with end-to-end replay:

- End-to-end replay verifies that the full pipeline reaches an acceptable player-facing outcome.
- Direct-seam replay verifies specific ownership boundaries and metadata/source contracts at the seam that decides the final emitted output.
- A full-pipeline pass can hide a wrong ownership source when later output still appears plausible; these direct-seam checks keep that contract visible.

| Scenario ID | Test | Purpose | Invariant Protected | Why Direct-Seam Is Needed | Status | Reproduction Command |
|---|---|---|---|---|---|---|
| `declared_alias_dialogue_plan` | `test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants` | Preserve declared speaker alias handling at strict-social final emission. | A permitted alias is accepted without losing the canonical runner target; dialogue plan remains valid; final text is non-scaffold. | It directly checks gate/dialogue-plan alias ownership; an end-to-end prompt could pass while masking whether alias admission occurred at the correct contract boundary. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants -q` |
| `opening_fallback_path` | `test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership`; companion lock `test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership` | Preserve canonical opening fallback authorship and source ownership. | Opening repair is selected from the upstream-prepared deterministic fallback, reports the upstream owner bucket/family/timeframe, and never reports compatibility-local authorship. | It protects final source/ownership metadata that is acceptance-relevant even when opening prose would look acceptable through a full chat path. | `PROTECTED` | `python -m pytest tests/test_golden_replay.py::test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership tests/test_golden_replay.py::test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership -q` |

## Supporting Replay Scenarios

| Scenario ID / Group | Test / Path | Purpose | Status | Reason It Is Not Protected |
|---|---|---|---|---|
| `scenario_spine_three_branch` | `tests/test_golden_replay.py::test_golden_replay_scenario_spine_three_branch_structural_smoke` | Confirm compact branch representation, per-branch execution, minimal structural divergence, and no scaffold leakage. | `SUPPORTING` | It is a locally constructed one-turn-per-branch schema smoke and does not execute the committed long-session scenario-spine fixture. |
| Golden observation/projection contract rows | `tests/test_golden_replay.py` tests before the named baseline scenarios; `tests/helpers/golden_replay.py` | Protect projection of FEM, owner buckets, prepared emissions, sanitizer lineage, runtime lineage, drift classification, and report formatting. | `SUPPORTING` | These are test-harness and diagnostic contracts, not replay scenarios asserting player-facing acceptance. Synthetic `scenario_id` values in those tests are not protected scenarios. |
| Failure classification/dashboard controlled probes | `tests/test_failure_classifier.py`; `tests/test_failure_dashboard_controlled_failures.py`; `tests/test_failure_classification_contract.py` | Ensure replay failure explanation remains classifiable and readable. | `SUPPORTING` | They validate diagnostic behavior with known-bad rows; they do not define acceptable gameplay output. |

Replay-shaped synthetic identifiers in the golden module are classified as follows:

| Synthetic Identifier(s) | Supporting Purpose | Status |
|---|---|---|
| `lineage_diagnostic_only`; `recorded_lineage`; `existing_lineage_projection`; `fem_lineage_projection`; `missing_lineage_projection` | Runtime-lineage projection and opt-in dashboard behavior. | `SUPPORTING` |
| `synthetic_opening_owner`; `synthetic_opening_owner_fail_closed`; `synthetic_sealed_owner`; `synthetic_strict_social_sealed_owner`; `synthetic_visibility_owner` | Fallback owner-bucket and visibility evidence projection. | `SUPPORTING` |
| `answer_prepared_projection`; `action_outcome_prepared_projection`; `rejected_prepared_projection`; `answer_prepared_absent_projection`; `action_outcome_prepared_absent_projection`; `malformed_prepared_projection` | Upstream-prepared emission projection and rejection/missing evidence handling. | `SUPPORTING` |
| `sanitizer_empty_projection`; `strict_social_sanitizer_split`; `sanitizer_clean_lineage`; `sanitizer_debug_lineage`; `sanitizer_legacy_lineage` | Sanitizer ownership and lineage projection. | `SUPPORTING` |

## Advisory Replay Scenarios

| Scenario / Lane | Path | Purpose | Status | Notes |
|---|---|---|---|---|
| Game-level long-session scenario-spine execution | `data/validation/scenario_spines/frontier_gate_long_session.json`; `tools/run_scenario_spine_validation.py` | Long-session branch health, convergence, divergence, and artifact review. | `ADVISORY` | The full 25-turn `branch_social_inquiry` source material now has a protected golden replay bridge, but the standalone scenario-spine runner remains advisory and does not hard-fail on evaluated health failures. |
| Opening scenario-spine paths | `data/validation/scenario_spines/c1a_opening_convergence_paths.json`; `tests/test_scenario_spine_opening_convergence.py` | Opening-convergence evidence. | `ADVISORY` | Evaluator/fixture evidence adjacent to protected replay, not a declared golden scenario. |
| N1 longitudinal scenario-spine lane | `tests/helpers/n1_scenarios.py`; `tools/run_n1_scenario_spine_validation.py` | Synthetic continuity, revisit, progression, and branching artifacts. | `ADVISORY` | Intentionally separate lane; not silently merged into golden replay acceptance. |
| Transcript/gauntlet replay-adjacent regressions | `tests/test_transcript_regression.py`; `tests/test_transcript_gauntlet_actor_addressing.py`; `tests/test_transcript_gauntlet_campaign_cleanliness.py`; `tests/test_narration_transcript_regressions.py` | Broader multi-turn behavior evidence. | `ADVISORY` | Valuable regression evidence, but not declared protected golden scenarios here. |

## Deprecated Replay Scenarios

No existing golden replay scenario is classified `DEPRECATED` in this declaration.
