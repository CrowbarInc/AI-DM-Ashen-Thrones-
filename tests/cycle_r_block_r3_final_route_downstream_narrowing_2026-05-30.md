# Cycle R / R3 — FEM `final_route` Downstream Narrowing

**Date:** 2026-05-30  
**Status:** Complete — all targeted pytest commands green.

---

## Exact `final_route` assertions found (targets)

| File | Test | Line (before) | Assertion |
| --- | --- | --- | --- |
| `test_answer_completeness_rules.py` | `test_frontload_repair_keeps_referential_clarity_explicit_npc_in_opening` | 473 | `== "replaced"` |
| `test_answer_completeness_rules.py` | `test_mixed_player_turn_question_plus_action_still_frontloads_answer` | 512 | `== "replaced"` |
| `test_answer_completeness_rules.py` | `test_authoritative_refusal_stays_substantive_after_repair` | 561 | `== "replaced"` |
| `test_answer_completeness_rules.py` | `test_transcript_style_dodge_opening_repaired_with_meta_flags` | 597 | `== "replaced"` |
| `test_response_delta_requirement.py` | `test_response_delta_unrepaired_failure_triggers_gate_replace_reason` | 731 | `== "replaced"` |
| `test_interaction_continuity_repair.py` | `test_emitted_output_preserves_continuity_constraints_under_strong_complex_narration` | 124 | `== "accept_candidate"` |
| `test_interaction_continuity_repair.py` | `test_emitted_output_surfaces_stripped_interruption_repair_metadata` | 179 | `== "replaced"` |
| `test_turn_packet_stage_diff_integration.py` | `test_gate_output_keeps_provenance_packet_and_observability_metadata_together` | 130 | `"final_route" in fem` (presence only) |
| `test_diegetic_fallback_narration.py` | `test_final_emission_opening_repair_carries_legacy_diegetic_family_to_fem` | 130 | `== "accept_candidate"` |
| `test_diegetic_fallback_narration.py` | `test_valid_final_emission_candidate_does_not_gain_diegetic_fallback_family` | 159 | `!= "replaced"` |

---

## Classification table

| Test | Classification | Rationale |
| --- | --- | --- |
| AC gate-integration quartet (4× `replaced`) | **Passive duplicate** | Primary: `answer_completeness_failed` / `answer_completeness_repaired` + `answer_completeness_unsatisfied_at_boundary_no_reorder` in `rejection_reasons_sample` |
| `test_response_delta_unrepaired_failure_triggers_gate_replace_reason` | **Passive duplicate** | Primary: `response_delta_unsatisfied_at_boundary_no_reorder` in `rejection_reasons_sample` |
| `test_emitted_output_preserves_continuity_constraints_under_strong_complex_narration` | **Passive duplicate** (route-class) | Primary: IC validation fails, continuity repair not applied, candidate text preserved |
| `test_emitted_output_surfaces_stripped_interruption_repair_metadata` | **Passive duplicate** | Primary: continuity repair not applied; `final_emission_gate_replaced` tag already locks replace path |
| `test_gate_output_keeps_provenance_packet…` | **Downstream smoke (already narrow)** | Primary: provenance + turn packet + stage diff + FEM attachment coexist |
| `test_final_emission_opening_repair_carries_legacy_diegetic_family_to_fem` | **Passive duplicate** | Primary: opening fallback text, `final_emitted_source`, realization family, authorship |
| `test_valid_final_emission_candidate_does_not_gain_diegetic_fallback_family` | **Downstream smoke (preserved)** | Primary: valid candidate unchanged; `!= "replaced"` is already route-class smoke |

---

## Assertions narrowed

| File | Change |
| --- | --- |
| `test_answer_completeness_rules.py` (4 tests) | `== "replaced"` → `not in (None, "", "accept_candidate")` (gate did not accept failed AC candidate as-is) |
| `test_response_delta_requirement.py` (1 test) | `== "replaced"` → `not in (None, "", "accept_candidate")` |
| `test_interaction_continuity_repair.py` | Strong narration: `== "accept_candidate"` → `!= "replaced"`; Interruption: `== "replaced"` → `"final_route" in meta` (tag retained) |
| `test_diegetic_fallback_narration.py` | Opening repair: `== "accept_candidate"` → `"final_route" in fem` |

---

## Assertions intentionally preserved

| File | Test | Assertion | Why preserved |
| --- | --- | --- | --- |
| `test_turn_packet_stage_diff_integration.py` | `test_gate_output_keeps_provenance_packet…` | `"final_route" in fem` | Already presence-only downstream smoke; primary is packet/provenance co-attachment |
| `test_diegetic_fallback_narration.py` | `test_valid_final_emission_candidate_does_not_gain_diegetic_fallback_family` | `!= "replaced"` | Route-class smoke aligned with “valid opening candidate not gate-replaced” primary |

---

## Owner coverage for each narrowed case

| Narrowed downstream case | Owner test(s) still locking exact / semantic route |
| --- | --- |
| AC failure → gate replace + boundary reason | `tests/test_social_exchange_emission.py::test_strict_social_emission_answer_completeness_repairs_frontloaded_direct_answer` — `final_route == "replaced"` + `answer_completeness_unsatisfied_at_boundary_no_reorder` |
| AC layer failure extras (no exact route) | `tests/test_final_emission_boundary_convergence.py::test_answer_completeness_layer_does_not_reorder_on_failure` — rejection extra when `answer_completeness_failed` |
| Response-delta failure → gate replace reason | `tests/test_response_delta_requirement.py` — layer tests assert `extra == ["response_delta_unsatisfied_at_boundary_no_reorder"]` (multiple parametrized cases); gate ordering in `tests/test_final_emission_gate.py::test_apply_final_emission_gate_runs_response_delta_before_speaker_enforcement` |
| RD layer failure extras | `tests/test_final_emission_boundary_convergence.py::test_response_delta_layer_does_not_reorder_on_failure` |
| Opening RT repair `accept_candidate` + `opening_deterministic_fallback` | `tests/test_final_emission_gate.py::test_selector_snapshot_opening_rt_repair_vs_generic_terminal_families` — `o_fem["final_route"] == "accept_candidate"` with `final_emitted_source == opening_deterministic_fallback` |
| Opening repair orchestration (no route string) | `tests/test_final_emission_gate.py::test_canonical_final_gate_auto_attaches_upstream_opening_fallback_before_emission` and related opening cluster |
| Generic gate `replaced` orchestration | `tests/test_final_emission_gate.py` — extensive `final_route == "replaced"` table (purity, ASP, sealed fallback, etc.) |
| FEM read/normalize `accept_candidate` / `replaced` | `tests/test_final_emission_meta.py` — projection and snapshot fixtures |
| IC strong violation without continuity repair | `tests/test_final_emission_gate.py` — continuity validate-only / step tests (`test_apply_interaction_continuity_step_*`, ordering hooks) |
| Gate replace tag on emission | `tests/test_final_emission_gate.py` — tags/meta paths referencing `final_emission_gate_replaced` (e.g. sealed-fallback cluster ~5198) |

---

## Files changed

| File | Change |
| --- | --- |
| `tests/test_answer_completeness_rules.py` | 4× exact `replaced` → route-class smoke |
| `tests/test_response_delta_requirement.py` | 1× exact `replaced` → route-class smoke |
| `tests/test_interaction_continuity_repair.py` | 2× exact route → route-class / presence |
| `tests/test_diegetic_fallback_narration.py` | 1× exact `accept_candidate` → presence |

**Not modified:** `test_turn_packet_stage_diff_integration.py` (already narrowed).

---

## Tests run and results

| Command | Result |
| --- | --- |
| `py -3 -m pytest tests/test_answer_completeness_rules.py tests/test_response_delta_requirement.py tests/test_interaction_continuity_repair.py tests/test_turn_packet_stage_diff_integration.py tests/test_diegetic_fallback_narration.py -q` | **PASS** (93 items) |
| `py -3 -m pytest tests/test_final_emission_gate.py tests/test_final_emission_meta.py -q` | **PASS** (270 items) |
| `py -3 -m pytest tests/test_golden_replay.py -m golden_replay -q` | **PASS** (53 items) |

---

## Coverage confirmation

- **Route-owner coverage:** unchanged — `test_final_emission_gate.py` and `test_final_emission_meta.py` not edited; exact `final_route` locks remain in gate/meta owners (including opening selector snapshot and strict-social AC integration).
- **Replay coverage:** unchanged — `test_golden_replay.py` not touched; golden lane (53 tests) passed.
- **Primary downstream concerns preserved:** answer-completeness flags/reasons, response-delta rejection sample, continuity validation/repair metadata, stage-diff FEM presence, diegetic opening family/source/text assertions — all retained.
- **No test functions removed.**
