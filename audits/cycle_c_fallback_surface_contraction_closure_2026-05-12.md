# Cycle C - Fallback Surface Contraction Closure

## Executive Summary

Cycle Track C contracted three high-risk fallback families into explicit ownership and observability boundaries:

- Opening fallback
- Thin-answer / action-answer prepared-emission fallback
- Post-gate / sanitizer rewrite fallback surfaces

The cycle reduced ambiguous final-gate fallback authorship by separating prose authorship, selection ownership, repair ownership, and replay/dashboard evidence. Runtime prose behavior changed only where needed to remove ambiguous opening fallback authorship; later blocks focused on telemetry, projection, classification, and dashboard locality.

## Families Contracted

| Family | Closure block | Current status |
| --- | --- | --- |
| Opening fallback | C9 | Complete. Runtime owner set is upstream-prepared or sealed-gate only. |
| Thin-answer / action-answer prepared-emission fallback | C16 | Complete. Answer/action fallback prose is upstream-prepared; final gate validates/selects only valid prepared text. |
| Post-gate / sanitizer rewrite fallback surfaces | C23 | Complete. Sanitizer mode, sanitizer-empty ownership, strict-social sanitizer split, mutation lineage, and reduced unknown classification are locked. |

## Final Ownership Contracts

### Opening Fallback

- Prose owner: `game/upstream_response_repairs.py` owns usable upstream-prepared opening fallback payload prose through `build_upstream_prepared_opening_fallback_payload`.
- Selection owner: `game/final_emission_gate.py` selects a structurally usable upstream-prepared opening payload or fails closed.
- Fallback/repair owner: sealed-gate ownership applies when the upstream payload is missing, malformed/text-only by final gate time, upstream attach failed, or curated facts are insufficient.
- Remaining unknown/legacy cases: compatibility-local ownership remains only as legacy/synthetic telemetry and boundary taxonomy. It maps to `unknown-ambiguous` and is not reachable through normal final-gate opening recovery.
- Key invariant tests:
  - `tests/test_final_emission_gate.py::test_full_gate_malformed_opening_payload_without_upstream_repair_is_sealed_gate`
  - `tests/test_opening_fallback_owner_bucket.py`
  - Golden replay opening fallback assertions rejecting compatibility-local ownership
  - Classifier/dashboard opening owner bucket tests

### Thin-Answer / Action-Answer Prepared-Emission Fallback

- Prose owner: `game/upstream_response_repairs.py` owns `prepared_answer_fallback_text` and `prepared_action_fallback_text` inside `upstream_prepared_emission`.
- Selection owner: `game/final_emission_gate.py` validates and selects valid prepared answer/action text.
- Fallback/repair owner: final gate stamps `answer_upstream_prepared_repair` or `action_outcome_upstream_prepared_repair` only when valid prepared text is used. Malformed or absent prepared answer/action payloads do not synthesize boundary prose.
- Remaining unknown/legacy cases: legacy dashboard/classifier labels may still mention thin answer/action or final-gate response-type repair when prepared-emission telemetry is absent. `strict_social_dialogue_repair` and `dialogue_minimal_repair` remain separate final-gate dialogue repairs.
- Key invariant tests:
  - Valid answer/action prepared-emission owner mapping in `tests/test_failure_classifier.py`
  - Rejected prepared-emission reason preservation in `tests/test_failure_classifier.py`
  - Absent/malformed prepared answer/action payload behavior in `tests/test_final_emission_gate.py`
  - Golden replay prepared-emission projection/debug tests
  - `tests/test_failure_classification_contract.py` prepared-emission owner/source contract

### Sanitizer Empty-Fallback Sibling Split

- Prose owner: the prepared sanitizer-empty fallback text is a sibling field generated upstream as `prepared_sanitizer_empty_fallback_text`.
- Selection owner: `game/output_sanitizer.py` owns empty-output sanitizer selection.
- Fallback/repair owner: sanitizer records `sanitizer_empty_fallback_owner="output_sanitizer"` and `sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"` when selected.
- Remaining unknown/legacy cases: this is not answer/action prepared-emission ownership even though the source string sits under `upstream_prepared_emission`.
- Key invariant tests:
  - `tests/test_output_sanitizer.py::test_strip_only_mode_drops_scaffold_without_diegetic_template_substitution`
  - `tests/test_golden_replay.py::test_golden_observed_turn_projects_sanitizer_empty_fallback_as_sanitizer_owned`
  - `tests/test_failure_classifier.py::test_failure_classifier_sanitizer_empty_fallback_is_sanitizer_owned_not_prepared_answer_action`
  - Dashboard evidence tests for sanitizer-empty fallback

### Post-Gate / Sanitizer Rewrite Surfaces

- Prose owner: normal sanitizer mode is strip-only and does not author substitute narrative prose. Legacy sentence rewrite is diagnostic/test-only.
- Selection owner: sanitizer owns legality strip, empty-output fallback selection, and strict-social fallback selection when sanitizer empty-output handling triggers it.
- Fallback/repair owner: strict-social/social emission owns strict-social fallback prose, while sanitizer records `sanitizer_strict_social_selection_owner="output_sanitizer"` and `sanitizer_strict_social_prose_owner="strict_social_emission"`.
- Remaining unknown/legacy cases: `post_gate_mutation_unknown` remains for boolean-only rows, absent lineage, or unmapped/new lineage tokens. Adjacent sentence-level strict-social sanitizer substitutions still share the social fallback helper, but C23 locks the empty-output path.
- Key invariant tests:
  - Default sanitizer strip-only lineage tests in `tests/test_output_sanitizer.py`
  - Legacy sentence rewrite diagnostic lineage tests in `tests/test_output_sanitizer.py` and classifier/dashboard tests
  - `tests/test_output_sanitizer.py::test_strict_social_empty_output_fallback_records_sanitizer_selection_and_social_prose_owner`
  - Golden replay projection tests for sanitizer lineage, sanitizer-empty fallback, and strict-social sanitizer split
  - `tests/test_failure_classifier.py::test_failure_classifier_reduces_post_gate_unknown_from_final_emission_lineage`
  - `tests/test_failure_classifier.py::test_failure_classifier_keeps_post_gate_unknown_without_lineage_or_specific_evidence`
  - Final-emission lineage tests in `tests/test_final_emission_gate.py`

## Observability Added

- Opening fallback owner buckets distinguish `upstream-prepared`, `sealed-gate`, and legacy/synthetic ambiguous compatibility-local evidence.
- Prepared-emission telemetry projects usage, validity, source, and reject reason:
  - `upstream_prepared_emission_used`
  - `upstream_prepared_emission_valid`
  - `upstream_prepared_emission_source`
  - `upstream_prepared_emission_reject_reason`
- Sanitizer-empty fallback telemetry:
  - `sanitizer_empty_fallback_used`
  - `sanitizer_empty_fallback_source`
  - `sanitizer_empty_fallback_owner`
- Sanitizer lineage telemetry:
  - `sanitizer_lineage_mode`
  - `sanitizer_lineage_changed_count`
  - `sanitizer_lineage_dropped_count`
  - `sanitizer_lineage_empty_fallback_used`
  - `sanitizer_lineage_legacy_rewrite_active`
- Strict-social-from-sanitizer split telemetry:
  - `sanitizer_strict_social_fallback_used`
  - `sanitizer_strict_social_selection_owner`
  - `sanitizer_strict_social_prose_owner`
  - `sanitizer_strict_social_source`
- Final emission mutation lineage:
  - `final_emission_mutation_lineage` records writer sequence separately from `final_emitted_source`.
- Classifier/dashboard evidence now renders compact prepared-emission, sanitizer, strict-social split, and mutation-lineage fields.

## Runtime Behavior Changes

- Opening fallback changed runtime behavior to remove ambiguous final-gate prose authorship:
  - Final gate no longer composes compatibility-local opening fallback prose for normal recovery.
  - Final gate no longer rebuilds malformed/text-only upstream opening fallback stubs.
  - Malformed/missing opening payloads now fail closed through sealed-gate ownership.
- Thin-answer / action-answer prepared-emission blocks did not change final text behavior beyond locking existing fail-closed behavior and telemetry.
- Sanitizer/post-gate blocks were observability/classification focused:
  - Normal sanitizer mode remains strip-only.
  - Legacy sentence rewrite remains diagnostic/test-only.
  - Sanitizer-empty and strict-social sanitizer split fields do not change emitted prose.
  - Post-gate unknown reduction is replay/classifier-only and does not change `final_emitted_source` or emitted text.

## Tests / Verification Matrix

| Area | Representative verification |
| --- | --- |
| Opening fallback runtime closure | `tests/test_final_emission_gate.py`, `tests/test_opening_fallback_owner_bucket.py`, `tests/test_golden_replay.py`, classifier/dashboard contract tests |
| Upstream prepared answer/action ownership | `tests/test_final_emission_gate.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_classification_contract.py` |
| Sanitizer-empty sibling split | `tests/test_output_sanitizer.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py` |
| Sanitizer strip-only / legacy diagnostic split | `tests/test_output_sanitizer.py`, `tests/test_golden_replay.py`, classifier/dashboard evidence tests |
| Strict-social-from-sanitizer owner split | `tests/test_output_sanitizer.py`, `tests/test_golden_replay.py`, `tests/test_failure_classifier.py`, `tests/test_failure_classification_contract.py` |
| Final-emission mutation lineage and unknown reduction | `tests/test_final_emission_gate.py`, `tests/test_failure_classifier.py`, `tests/test_failure_dashboard_controlled_failures.py`, `tests/test_failure_classification_contract.py` |

Latest focused closure verification used bundled Python because plain `python` was not available on PATH:

- `tests/test_output_sanitizer.py -q` - passed, 45 tests
- `tests/test_golden_replay.py -q` - passed, 26 tests
- `tests/test_failure_classifier.py -q` - passed, 50 tests
- `tests/test_failure_dashboard_controlled_failures.py -q` - passed, 17 tests
- `tests/test_failure_classification_contract.py -q` - passed, 20 tests
- `tests/test_final_emission_gate.py -q` - passed, 224 tests

## Remaining Fallback Risk

- Legacy/synthetic compatibility-local opening fallback evidence remains for historical rows and boundary taxonomy, but not as a normal runtime opening recovery path.
- Legacy thin-answer labels remain possible for rows without newer prepared-emission telemetry.
- Post-gate mutation rows remain `emission.post_gate_mutation_unknown` when they are boolean-only, lack `final_emission_mutation_lineage`, or contain only unmapped/new lineage tokens.
- Adjacent strict-social sanitizer substitutions outside the empty-output path still use the social fallback helper, though the empty-output ownership split is locked.
- Future fallback families may still have gate-authored prose or boolean-only observability outside the three families closed here.

## Recommended Next Cycle

Recommended next cycle: run a short Cycle C wrap-up first, then start the next contraction cycle on fallback families that still have direct final-gate prose authorship or boolean-only observability.

Priority candidates:

- Generic acceptance-quality / global-scene terminal fallback paths, especially any branch where final gate authors prose instead of selecting a prepared or sealed payload.
- Non-opening sealed fallback replacements and terminal fallback families that still lack owner buckets comparable to opening fallback.
- Any remaining stage-diff or post-gate mutation rows that depend on boolean-only evidence rather than lineage-backed classification.

Suggested shape for the next cycle:

- Inventory remaining terminal/global fallback prose authors.
- Add owner buckets or lineage tokens before changing behavior.
- Separate prose owner from selection owner before contracting runtime paths.
- Keep unknown buckets, but require them to mean "insufficient evidence" rather than "unmodeled known layer."
