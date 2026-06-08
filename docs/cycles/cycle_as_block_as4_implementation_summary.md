# Cycle AS4 — FEM Read-Path Redirect and Compatibility Cleanup Implementation Summary

**Date:** 2026-06-04  
**Block:** AS4 — Consolidate downstream FEM read helpers; retire compat shim  
**Behavior change:** None (import/facade relocation only)

---

## Files changed

| File | Change |
| --- | --- |
| `tests/helpers/golden_replay_projection.py` | `build_fem_runtime_lineage_events` from `final_emission_replay_projection`; added `read_fem_meta_from_gate_output` |
| `tests/helpers/emission_smoke_assertions.py` | AS4 docstring (FEM read routing guidance) |
| `tests/helpers/opening_fallback_evidence.py` | Docstring: retired `final_emission_gate_fixtures` shim reference |
| `tests/helpers/transcript_snapshots.py` | `read_final_emission_meta_dict` → `final_emission_meta_from_output` |
| `tests/helpers/final_emission_gate_fixtures.py` | **Deleted** (zero importers since AS1) |
| `tools/run_scenario_spine_validation.py` | Lineage from `final_emission_replay_projection`; retained raw FEM read |
| `tests/test_golden_replay.py` | FEM gate reads → `read_fem_meta_from_gate_output` |
| `tests/test_c4_narrative_mode_live_pipeline.py` | `_fem` → `final_emission_meta_from_output` |
| `tests/test_narration_transcript_regressions.py` | All FEM reads → smoke facade |
| `tests/test_api_narration_path_selection.py` | All FEM reads → smoke facade |
| `tests/test_block_s_speaker_local_rebind_equivalence.py` | FEM read → smoke facade |
| `tests/test_block_u_finalize_stack_divergence.py` | FEM reads → smoke facade |
| `tests/test_scene_transition_authority.py` | `read_debug_notes_from_turn_payload` → `read_turn_debug_notes` |
| `tests/test_run_scenario_spine_validation.py` | Lineage + FEM reads via replay projection / `golden_replay_projection` |
| `tests/test_bounded_partial_quality.py` | `repair_fallback_behavior` → `repairs_consumer_facade` |
| `tests/test_social_fallback_leak_containment.py` | `repair_fallback_behavior` → `repairs_consumer_facade` |

---

## FEM read imports removed (downstream suites)

| Suite / module | Removed symbol(s) | Replacement |
| --- | --- | --- |
| `test_golden_replay.py` | `read_final_emission_meta_dict` | `golden_replay_projection.read_fem_meta_from_gate_output` |
| `test_c4_narrative_mode_live_pipeline.py` | `read_final_emission_meta_dict` | `emission_smoke_assertions.final_emission_meta_from_output` |
| `test_narration_transcript_regressions.py` | `read_final_emission_meta_dict` (9 call sites) | `final_emission_meta_from_output` |
| `test_api_narration_path_selection.py` | `read_final_emission_meta_dict` (6 call sites) | `final_emission_meta_from_output` |
| `test_block_s_speaker_local_rebind_equivalence.py` | `read_final_emission_meta_dict` | `final_emission_meta_from_output` |
| `test_block_u_finalize_stack_divergence.py` | `read_final_emission_meta_dict` | `final_emission_meta_from_output` |
| `test_scene_transition_authority.py` | `read_debug_notes_from_turn_payload` | `read_turn_debug_notes` |
| `transcript_snapshots.py` | `read_final_emission_meta_dict` | `final_emission_meta_from_output` |
| `test_run_scenario_spine_validation.py` (lineage test) | meta re-export pair | `read_fem_meta_from_gate_output` + `final_emission_replay_projection.build_fem_runtime_lineage_events` |

**Lineage compat re-export removed from:**

| Module | Before | After |
| --- | --- | --- |
| `golden_replay_projection.py` | `build_fem_runtime_lineage_events` via `game.final_emission_meta` | `game.final_emission_replay_projection` (canonical owner) |
| `tools/run_scenario_spine_validation.py` | both via meta | lineage via replay_projection; FEM read retained from meta |

---

## FEM read imports retained (with reason)

| Import | Location | Reason |
| --- | --- | --- |
| `read_final_emission_meta_dict` | `tests/helpers/emission_smoke_assertions.py` | Single smoke-facade delegate for HTTP/pipeline downstream |
| `read_debug_notes_from_turn_payload` | `emission_smoke_assertions.py` | Single smoke-facade delegate for turn-packet debug notes |
| `read_final_emission_meta_dict` (lazy) | `golden_replay_projection.read_fem_meta_from_gate_output` | Replay/spine diagnostic hub — one meta read concentration point |
| `read_final_emission_meta_from_turn_payload`, normalize, bucket helpers | `golden_replay_projection.py` | Acceptance projection owner (AO5); not downstream smoke |
| `read_final_emission_meta_dict` | `tools/run_scenario_spine_validation.py` | **Tooling** — CLI records post-gate FEM from live chat payloads; direct meta read documented inline |
| `build_fem_runtime_lineage_events` | `game/final_emission_meta.py` | Owner re-export for production normalize path (unchanged) |
| `read_final_emission_meta_dict` | Owner suites + production (`stage_diff_telemetry`, `gm_retry`, …) | **KEEP** — gate/meta/FEM owner and production observability |

Non-owner test files still calling `read_final_emission_meta_dict` directly (outside AS4 primary candidates) remain for AS5+ incremental thinning — e.g. `test_social_exchange_emission.py`, `test_fallback_behavior_gate.py`, equivalence neighbors.

---

## Compatibility shims deleted or retained

| Shim | AS4 action |
| --- | --- |
| `tests/helpers/final_emission_gate_fixtures.py` | **Deleted** — zero Python importers since AS1 split |
| `game.final_emission_meta.build_fem_runtime_lineage_events` re-export | **Retained** — production `normalize_final_emission_meta_for_observability` path; downstream tests/tooling no longer depend on meta for lineage |

---

## Repairs facade migrations completed

| Suite | Before | After |
| --- | --- | --- |
| `test_bounded_partial_quality.py` | `game.final_emission_repairs.repair_fallback_behavior` | `repairs_consumer_facade.repair_fallback_behavior` |
| `test_social_fallback_leak_containment.py` | same | same |

---

## Helpers added / expanded

### `golden_replay_projection.read_fem_meta_from_gate_output(gm_output)`

Thin delegate to `read_final_emission_meta_dict` for golden-replay and spine-lineage diagnostic tests.

### Unchanged (reused)

- `emission_smoke_assertions.final_emission_meta_from_output`
- `emission_smoke_assertions.read_turn_debug_notes`
- `repairs_consumer_facade.repair_fallback_behavior`

---

## Validation commands and results

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_ownership_registry.py tests/test_final_emission_debt_retirement.py -q` | **PASS** (24) |
| `python -m pytest tests/test_golden_replay.py -q` | **PASS** (68) |
| `python -m pytest tests/test_bounded_partial_quality.py tests/test_social_fallback_leak_containment.py -q` | **PASS** (1 skipped) |
| `python -m pytest tests/test_turn_pipeline_shared.py -q` | **PASS** (69) |
| Touched suites (C4, transcript, API narration, block S/U, scene transition, spine lineage test) | **PASS** (115) |

---

## Recommended AS5 target

**AS5 — Test-to-test import and convergence assert retirement** (from AS recon)

- Extract shared contracts from `test_fallback_behavior_gate.py` / `test_narrative_mode_output_validator.py` into `tests/helpers/` (remove test-to-test imports in `test_narration_transcript_regressions.py` and neighbors)
- Continue incremental FEM read thinning in remaining high-read non-owner suites (`test_social_exchange_emission.py`, `test_fallback_behavior_gate.py`, `test_lead_lifecycle_block3_transcript_regression.py`, …)
- Optional: migrate `test_final_emission_boundary_no_semantic_repair.py` repairs imports to `repairs_consumer_facade` (AS3 leftover)

**Do not proceed to AS5 in this block.**
