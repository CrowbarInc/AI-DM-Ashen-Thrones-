# BK — Fallback Ownership Map

**Cycle:** BK — Discovery / Audit  
**Date:** 2026-06-16  

**Legend:** Y = primary responsibility. (c) = consume only. (e) = export/re-export. Partial roles in *italics*.

---

## Tier A — Core runtime owners

| File | Create | Select | Project | Validate | Export | Consume |
|------|:------:|:------:|:-------:|:--------:|:------:|:-------:|
| `game/diegetic_fallback_narration.py` | Y | | | | Y | |
| `game/opening_deterministic_fallback.py` | Y | | *meta* | | Y | (c) |
| `game/upstream_response_repairs.py` | Y | | Y | | Y | (c) |
| `game/fallback_behavior.py` | Y | | | | Y | |
| `game/final_emission_visibility_fallback.py` | | Y | Y | *visibility* | Y | (c) |
| `game/final_emission_opening_fallback.py` | *meta* | Y | Y | *policy* | Y | (c) |
| `game/final_emission_sealed_fallback.py` | | Y | Y | | Y | (c) |
| `game/social_exchange_emission.py` | Y | Y | Y | | Y | (c) |
| `game/gm_retry.py` | Y | Y | Y | | | (c) |
| `game/final_emission_meta.py` | *defaults* | | Y | | Y | (c) |
| `game/final_emission_replay_projection.py` | | | Y | | Y | (c) |
| `game/fallback_provenance_debug.py` | Y | | Y | | Y | (c) |
| `game/realization_provenance.py` | Y | | Y | | Y | |

---

## Tier B — Selection sub-owners and emission paths

| File | Create | Select | Project | Validate | Export | Consume |
|------|:------:|:------:|:-------:|:--------:|:------:|:-------:|
| `game/final_emission_scene_emit_integrity.py` | | Y | | | | (c) |
| `game/final_emission_first_mention_composition.py` | *candidates* | Y | | | | (c) |
| `game/final_emission_passive_scene_pressure.py` | *candidates* | Y | | | | (c) |
| `game/anti_reset_emission_guard.py` | Y | Y | | | | (c) |
| `game/final_emission_text.py` | Y | | | | (e) | (c) |
| `game/output_sanitizer.py` | | Y | Y | | | (c) |
| `game/final_emission_fast_fallback_composition.py` | *compose* | | Y | | Y | (c) |
| `game/final_emission_response_type.py` | | (c) | Y | | | (c) |
| `game/final_emission_generic_exit.py` | | (c) | Y | | | (c) |
| `game/final_emission_terminal_pipeline.py` | | (c) | | | | (c) |
| `game/final_emission_acceptance_quality.py` | | (c) | | | | (c) |
| `game/api.py` | | Y | Y | | | (c) |
| `game/opening_visible_fact_selection.py` | | Y | | | | (c) |

---

## Tier B — Gate, repair, validation stack

| File | Create | Select | Project | Validate | Export | Consume |
|------|:------:|:------:|:-------:|:--------:|:------:|:-------:|
| `game/final_emission_gate.py` | | (c) | Y | | | (c) |
| `game/final_emission_repairs.py` | *reorder* | | Y | | Y | (c) |
| `game/final_emission_validators.py` | | | Y | Y | Y | (c) |
| `game/final_emission_non_strict_stack.py` | | | Y | | | (c) |
| `game/final_emission_strict_social_stack.py` | | | Y | | | (c) |
| `game/final_emission_gate_context.py` | | | Y | | | (c) |
| `game/response_policy_contracts.py` | | | Y | | Y | (c) |
| `game/response_policy_enforcement.py` | | | Y | | | (c) |
| `game/prompt_context.py` | | | Y | | | (c) |
| `game/narration_visibility.py` | | | | Y | Y | |
| `game/realization_authority.py` | Y | | | | Y | |

---

## Tier C — Test, replay, tooling

| File | Create | Select | Project | Validate | Export | Consume |
|------|:------:|:------:|:-------:|:--------:|:------:|:-------:|
| `tests/helpers/golden_replay_projection.py` | *fixtures* | | Y | Y | Y | (c) |
| `tests/helpers/opening_fallback_evidence.py` | Y | | Y | | Y | (c) |
| `tests/helpers/opening_fallback_gate_harness.py` | | (c) | | | | (c) |
| `tests/helpers/fallback_behavior_fixtures.py` | Y | | | | Y | |
| `tests/helpers/replay_observed_row_fixtures.py` | Y | | Y | | | (c) |
| `tests/helpers/failure_classification_sync.py` | | | Y | | | (c) |
| `tests/helpers/failure_classifier.py` | | | Y | | | (c) |
| `tests/helpers/golden_replay.py` | | | Y | Y | Y | (c) |
| `tests/failure_classification_contract.py` | | | | Y | Y | |
| `tools/refresh_protected_replay_manifest.py` | | | Y | | | (c) |
| `tools/final_emission_ownership_audit.py` | | | | Y | | (c) |
| `tools/realization_provenance_audit.py` | | | | Y | | (c) |

---

## Cross-cutting patterns

### Content vs selection (intended split)

| Concern | Content owner | Selection owner |
|---------|---------------|-----------------|
| Opening deterministic | `opening_deterministic_fallback` | `final_emission_opening_fallback` |
| Opening upstream-prepared | `upstream_response_repairs` | `final_emission_opening_fallback` |
| Diegetic templates | `diegetic_fallback_narration` | `final_emission_visibility_fallback` |
| Strict social | `social_exchange_emission` | visibility / gate terminal |
| Retry / fast upstream | `gm_retry` | `api` + `gm_retry` |
| Sealed terminal | delegated | `final_emission_sealed_fallback` |

### Dual projection (intentionally separate)

| Layer | Owner |
|-------|-------|
| Runtime lineage | `final_emission_replay_projection` |
| Acceptance observation | `golden_replay_projection` |
| FEM packaging | `final_emission_meta` |

### Owner-bucket assignment (distributed)

| Bucket family | Assigner |
|---------------|----------|
| Opening | `final_emission_meta` |
| Sealed | `final_emission_sealed_fallback` |
| Visibility | `final_emission_visibility_fallback` |

---

## Overlapping Create + Select (hotspots)

| File | Issue |
|------|-------|
| `final_emission_visibility_fallback` | Routes across 8+ sub-modules; doc denies prose authorship but owns routing policy |
| `social_exchange_emission` | Authors and selects strict-social fallback (governance-aligned) |
| `gm_retry` | Authors and selects retry lines (governance-aligned) |
| `output_sanitizer` | Selects and applies sanitizer fallback at boundary |
| `upstream_response_repairs` | Packages content and stamps authorship at packaging time |
