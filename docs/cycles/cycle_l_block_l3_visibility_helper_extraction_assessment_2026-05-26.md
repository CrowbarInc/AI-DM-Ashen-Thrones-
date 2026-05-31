# Cycle L Block L3: Visibility Helper Ownership Extraction Assessment

Date: 2026-05-26
Scope: Assessment only. No production code or tests changed.

## Executive summary

`game/final_emission_visibility_fallback.py` is mature enough to receive a
dedicated owner test module:

- Its module contract is explicit: it owns visibility fallback routing/payload
  shaping and must not author fallback prose or write final output.
- Cycle D already closed the production extraction boundary: pure route,
  payload, metadata, annotation, owner-bucket, dispatch, and logging-payload
  shaping live in the helper; selection, prose calls, output writes, and
  sequencing remain in `game/final_emission_gate.py`.
- The direct helper characterization tests are a contiguous block in
  `tests/test_final_emission_gate.py`, from
  `test_visibility_fallback_route_helper_importable_and_callable_from_new_module`
  at line 5005 through
  `test_build_visibility_route_decision_inputs_collects_selector_arguments`
  at line 6320.
- That block contains **42 test functions / 50 collected cases** and has no
  dependency on `feg`, gate fixtures, gate output, or final-gate ordering.
- Genuine gate consumer tests occur before and after the candidate block and
  should remain in `tests/test_final_emission_gate.py`.

**Recommended decision: Extract ownership suite.** Move the contiguous pure
helper block unchanged into
`tests/test_final_emission_visibility_fallback.py`. Preserve every assertion
and parametrized case; the purpose is ownership attribution, not coverage
reduction.

## 1. Pure helper-owner characterization tests

The extraction candidate is the contiguous range beginning at
`tests/test_final_emission_gate.py:5005` and ending before
`test_block_ai_route_visibility_and_opening_rt_selectors_do_not_mutate_inputs`
at line 6351.

| Helper ownership surface | Tests to move unchanged | Collected cases |
| --- | --- | ---: |
| Route helper API and no-prose contract | `test_visibility_fallback_route_helper_importable_and_callable_from_new_module`; `test_visibility_fallback_route_helper_decisions`; `test_visibility_fallback_route_module_contains_no_fallback_prose_literals`; `test_visibility_fallback_helper_module_contains_no_fallback_prose_literals` | 6 |
| Owner-bucket taxonomy | `test_visibility_fallback_owner_bucket_classifier`; `test_visibility_fallback_owner_bucket_taxonomy_includes_ambiguous_bucket` | 7 |
| Validation/pre-route shaping | `test_build_visibility_validation_observation_shapes_pass_result`; `test_build_visibility_validation_observation_shapes_failed_result`; `test_build_visibility_pre_route_validation_context_wraps_validation_result_and_observation`; `test_build_visibility_default_metadata_payload_collects_initial_stamp_kwargs`; `test_build_visibility_first_mention_default_metadata_payload_collects_ordered_meta_updates`; `test_build_visibility_pre_route_metadata_context_groups_default_payloads`; `test_build_visibility_enforcement_stage_context_groups_pre_route_objects` | 7 |
| Metadata stamping and route outcomes | `test_stamp_visibility_fallback_metadata_writes_visibility_fields_only`; `test_stamp_visibility_fallback_metadata_can_mark_nonreplacement_routes`; `test_build_visibility_route_metadata_outcome_for_hard_replacement`; `test_build_visibility_route_metadata_outcome_for_nonreplacement_routes`; `test_build_visibility_non_replacement_route_context_for_continuity_lead_exemption`; `test_build_visibility_non_replacement_route_context_for_concrete_interaction_no_hard_replace` | 7 |
| Hard replacement plan and selected fallback tuple | `test_build_visibility_replacement_annotations_for_hard_replacement`; `test_build_visibility_replacement_annotations_caps_debug_violation_list`; `test_build_visibility_hard_replacement_plan_collects_side_effect_inputs`; `test_visibility_selected_fallback_round_trips_legacy_tuple` | 4 |
| First-mention/referential selected-fallback payload shaping | `test_build_visibility_first_mention_metadata_payload_collects_composition_values`; `test_build_visibility_first_mention_metadata_payload_defaults_when_composition_empty`; `test_build_first_mention_selected_fallback_metadata_payload_collects_replacement_fields`; `test_build_first_mention_selected_fallback_metadata_payload_uses_default_layers`; `test_build_referential_clarity_selected_fallback_metadata_payload_collects_replacement_fields`; `test_build_referential_clarity_selected_fallback_metadata_payload_uses_default_layers` | 6 |
| Logging payload shaping | `test_build_first_mention_replacement_logging_payload_matches_gate_decision_shape`; `test_build_first_mention_replacement_logging_payload_normalizes_empty_interlocutor`; `test_build_referential_clarity_replacement_logging_payload_matches_gate_decision_shape`; `test_build_referential_clarity_replacement_logging_payload_normalizes_boolean_and_interlocutor`; `test_build_visibility_hard_replacement_logging_payload_collects_decision_and_trace_inputs`; `test_build_visibility_hard_replacement_logging_payload_caps_reasons_and_normalizes_empty_interlocutor`; `test_build_visibility_hard_replacement_context_groups_existing_payloads` | 7 |
| Selection-input and route-dispatch context shaping | `test_build_visibility_fallback_selection_inputs_collects_hard_replace_context`; `test_build_visibility_fallback_selection_inputs_prefers_explicit_response_type_context`; `test_build_visibility_route_dispatch_context_for_sealed_hard_replace`; `test_build_visibility_route_dispatch_context_for_continuity_lead_exemption`; `test_build_visibility_route_dispatch_context_for_concrete_interaction_no_hard_replace`; `test_build_visibility_route_decision_inputs_collects_selector_arguments` | 6 |
| **Total** | **42 test functions** | **50** |

These tests are owner-level because they invoke
`game.final_emission_visibility_fallback` directly and inspect its returned
dataclasses, metadata kwargs, route tokens, ownership taxonomy, defensive
copies, or source-level no-prose constraint. They do not observe the gate as a
consumer of those values.

## 2. Genuine gate consumer and integration tests

The following tests should remain in `tests/test_final_emission_gate.py`
because they exercise gate-private entrypoints, final output, FEM propagation,
or orchestration order rather than pure helper return values.

| Gate-owned area | Tests / range | Why it remains gate-owned |
| --- | --- | --- |
| Applied visibility replacement and FEM projection | `test_visibility_safe_fallback_final_emitted_source_snapshot` at line 4699 | Calls `apply_final_emission_gate`; asserts replacement tag, final route, emitted source, realization family, and sealed owner evidence after application. |
| Branch-selector projection snapshots | `test_selector_snapshot_visibility_vs_generic_terminal_distinct_markers` at line 4730; adjacent N4/opening/strict-social/valid-candidate selector snapshots through line 4898 | Distinguishes final-gate branches and final emitted projections, not helper payload construction. |
| Ordering | `test_sealed_branch_order_accept_path_visibility_before_n4`; `test_sealed_branch_order_replace_path_visibility_before_n4` at lines 4900 and 4931 | Monkeypatches gate-private functions to assert layer order. |
| Mixed gate selector reachability | `test_block_ai_sealed_selector_helpers_importable_and_callable` at line 4965 | Calls `feg._route_visibility_enforcement_after_failed_validation`, N4 sealed selection, and opening RT promotion; it is deliberately a gate pressure-reduction/integration lock. |
| Gate-private mutation boundaries | `test_block_ai_route_visibility_and_opening_rt_selectors_do_not_mutate_inputs` at line 6351; the following Block AI N4/non-strict selector tests | Calls `feg` selectors and asserts gate-private non-mutation behavior across visibility and opening/N4 branches. |
| Strict-social referential integration | Block E tests around lines 1220-1494 | Exercises `_apply_referential_clarity_enforcement`, local substitution, fallback application, and gate metadata/side effects. |

`tests/test_final_emission_visibility.py` should also remain unchanged. It
already states that it owns semantic visibility, first-mention, and
referential-clarity legality expectations with `game/narration_visibility.py`;
its pipeline assertions are not substitutes for the pure fallback-helper
contract.

## 3. Can the helper-owner cluster move unchanged?

**Yes.** The candidate helper-owner cluster can be moved unchanged into
`tests/test_final_emission_visibility_fallback.py` without semantic alteration.

Evidence:

- Every function in the candidate range directly calls
  `visibility_fallback.*` or inspects the imported helper module source.
- AST dependency inspection found no use of `feg`, `apply_final_emission_gate`,
  gate fixtures, scene/session builders, monkeypatch, or output metadata
  readers inside the candidate functions.
- The first test immediately before the candidate range calls three `feg`
  private selectors and is therefore correctly excluded.
- The first test immediately after the candidate range again calls `feg`
  private selectors and is therefore correctly excluded.
- A repository search found no external references to the candidate test
  function names outside `tests/test_final_emission_gate.py` and the L2 report.
  Moving the tests changes pytest node IDs but not any known code or documented
  test-name dependency.

The move must be a relocation, not duplication: each test definition should
exist in exactly one suite after extraction.

## 4. Required imports and fixtures

The prospective owner module requires only the following imports used by the
candidate block:

```python
from __future__ import annotations

import ast
import inspect
from typing import Any

import pytest

from game.final_emission_meta import (
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
)
import game.final_emission_visibility_fallback as visibility_fallback

pytestmark = pytest.mark.unit
```

No shared fixtures or copied local helper functions are required. In
particular, do not bring across:

- `game.final_emission_gate as feg`;
- `apply_final_emission_gate`;
- scene/session/world setup helpers;
- `_visibility_offscene_npc_gate_bundle`;
- opening/N4/strict-social fixtures;
- `read_final_emission_meta_dict`;
- sealed fallback or realization-family imports.

## 5. Estimated test count moved

| Measure | Count |
| --- | ---: |
| Test function definitions moved | 42 |
| Additional cases produced by parametrization | 8 |
| Total collected pytest cases moved | 50 |
| Expected net change to total test count | 0 |

The parametrized expansions are:

- `test_visibility_fallback_route_helper_decisions`: 3 cases.
- `test_visibility_fallback_owner_bucket_classifier`: 6 cases.
- `test_build_visibility_route_metadata_outcome_for_nonreplacement_routes`: 2 cases.

## 6. Risks of extraction

| Risk | Level | Mitigation |
| --- | --- | --- |
| Pytest node IDs change from `tests/test_final_emission_gate.py::*` to `tests/test_final_emission_visibility_fallback.py::*`. External CI filters could target old node IDs even though none were found in the repo. | Low | Search repository before implementation, run collection and focused suites afterward, and note node-ID relocation in the implementation report. |
| Accidentally moving adjacent gate-private tests with the pure helper cluster. | Low | Use the exact boundary: include line-5005 helper test through the line-6320 route-decision test; exclude line-4965 and line-6351 tests. |
| Dropping test module imports or parametrized decorators during relocation. | Low | Copy assertions and decorators verbatim; use the minimal import set above; verify that 50 tests collect in the new file. |
| Confusing helper metadata ownership with semantic visibility legality ownership. | Low | Put an owner note in the new file stating it owns pure helper shaping only; retain `tests/test_final_emission_visibility.py` unchanged as legality/pipeline owner. |
| Governance documentation remains broad: `tests/test_ownership_registry.py` currently registers `tests/test_final_emission_gate.py` as the direct owner for final-emission gate orchestration, but has no separate visibility-helper responsibility row. | Low / optional | Do not alter that gate row. A dedicated visibility-helper responsibility record is optional and should be added only if Cycle L explicitly expands registry scope. |
| Later temptation to thin pipeline or diagnostic tests because owner tests moved. | Medium | Treat extraction as ownership relocation only; preserve pipeline, gate consumer, replay, classifier, and dashboard coverage unchanged. |

## 7. Recommended decision

**Extract ownership suite.**

The helper boundary has already stabilized in production and is already covered
as an independent behavioral unit. Keeping its direct test matrix in the gate
suite obscures failure attribution: a gate-file failure can currently mean a
pure dataclass/payload/route-helper regression with no gate orchestration defect.

Moving the 50 collected helper cases to
`tests/test_final_emission_visibility_fallback.py` improves the Cycle L goal:

- a failure in the new suite points first to
  `game/final_emission_visibility_fallback.py`;
- a failure in the remaining gate visibility tests points first to selection,
  application, FEM propagation, order, or side-effect sequencing;
- `tests/test_final_emission_visibility.py` continues to point first to
  validation/pipeline legality behavior.

This is a test ownership relocation, not test deletion, assertion narrowing, or
runtime refactor.

## 8. Exact migration plan preserving every assertion

1. Create `tests/test_final_emission_visibility_fallback.py` with an ownership
   note stating that the module owns pure visibility fallback route, payload,
   metadata, annotation, owner-bucket, dispatch, defensive-copy, and
   logging-payload shaping; it does not own gate orchestration or visibility
   legality semantics.
2. Add exactly the imports listed in section 4 and `pytestmark =
   pytest.mark.unit`.
3. Move, verbatim and in original order, the entire candidate test range from
   `test_visibility_fallback_route_helper_importable_and_callable_from_new_module`
   through `test_build_visibility_route_decision_inputs_collects_selector_arguments`.
   Preserve all decorators, assertion bodies, strings, and test names.
4. Remove only those relocated definitions and their now-local helper-cluster
   heading from `tests/test_final_emission_gate.py`. Leave all gate-owned
   snapshots, selector/order tests, and the `feg` tests immediately bracketing
   the moved range unchanged.
5. Replace the vacated gate-file helper note, if needed for readability, with
   a short consumer-boundary note pointing to
   `tests/test_final_emission_visibility_fallback.py`; do not alter assertions.
6. Do not change `tests/test_final_emission_visibility.py`, production code,
   replay/classifier/dashboard/FEM projection tests, or runtime ownership
   behavior.
7. Inspect `tests/test_ownership_registry.py` after the move. Keep the
   existing `final_emission_gate_orchestration` owner unchanged. Add a separate
   visibility-helper row only if the implementation block explicitly includes
   registry expansion; it is not required to preserve the extracted test
   coverage.
8. Verify collection before behavior execution:
   - `pytest tests/test_final_emission_visibility_fallback.py --collect-only -q`
     must collect 50 cases.
   - `pytest tests/test_final_emission_gate.py --collect-only -q` must collect
     its previous 281 cases minus the 50 moved cases, adjusted only for any
     unrelated pre-existing worktree changes.
9. Run focused behavioral confirmation after relocation:
   - `pytest tests/test_final_emission_visibility_fallback.py tests/test_final_emission_gate.py tests/test_final_emission_visibility.py -q`
   - `pytest tests/test_final_emission_meta.py tests/test_golden_replay.py tests/test_failure_classifier.py tests/test_failure_dashboard_controlled_failures.py -q`

## Commands run and results

| Command | Result |
| --- | --- |
| `git status --short --branch` plus focused `rg` and `Get-Content` inspection of `tests/test_final_emission_gate.py` | Confirmed pre-existing L1 edits/reports remain in the worktree; identified gate consumer block at lines approximately 4690-4931 and helper candidate block at 5005-6337. |
| `Get-Content game\final_emission_visibility_fallback.py`, `Get-Content tests\test_final_emission_visibility.py`, `Get-Content audits\cycle_d_visibility_fallback_contraction_closure_2026-05-13.md`, and prior L2 report | Confirmed helper module contract, semantic visibility owner note, and Cycle D closed ownership split. |
| `rg -n` over imports, test names, helper calls, and gate-private calls in `tests\test_final_emission_gate.py` | Established that candidate tests call `visibility_fallback.*`, while adjacent excluded tests call `feg.*` or full gate entrypoints. |
| Bundled-Python AST scan of candidate range `5005 <= lineno <= 6338` | Counted 42 candidate test definitions and 50 collected cases after literal `pytest.mark.parametrize` expansion. |
| Bundled-Python AST dependency scan over the candidate functions | Found only `Any`, `ast`, `inspect`, `pytest`, `visibility_fallback`, and six `VISIBILITY_FALLBACK_OWNER_*` constants as required external names. No gate dependency found. |
| `rg -n` for candidate test names and `test_final_emission_visibility_fallback.py` outside the current gate/helper files | Found audit/report references to the helper boundary, but no repository dependency on the candidate test node names. |
| Inspection of `tests/test_ownership_registry.py` | Found an existing direct-owner row for final-emission gate orchestration and no dedicated visibility-helper responsibility row; extraction need not change the gate owner registration. |
