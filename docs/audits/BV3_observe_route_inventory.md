# BV3 — Observe-Route Fallback Inventory

**Date:** 2026-06-21  
**Scope:** Every fallback routing path that fires on `route_kind == observe` turns in the protected 107-FEM corpus.  
**Baseline route trigger rate:** 95.45% (42/44 observe turns)  
**Measurement:** `artifacts/golden_replay/bv1b_fallback_incidence_report.json` + BP3-style FEM scan with current `build_fem_runtime_lineage_events` projector.

---

## Executive summary

Observe-route fallback is **almost entirely referential-clarity hard replacement**, not visibility or first-mention enforcement. On the corpus, **38/42** observe fallback events are `referential_clarity_hard_replacement`; content resolves through **passive scene pressure** sealed fallback in **40/42** turns (`final_emitted_source=passive_scene_pressure_fallback`). Relocation (BK) named selection/content owners but did not reduce triggers.

---

## Corpus snapshot

| Metric | Value |
|---|---:|
| Observe turns (eligible) | 44 |
| Observe fallback turns | 42 |
| Observe non-fallback turns | 2 (`final_route=accept_candidate`) |
| **Observe fallback route rate** | **95.45%** |
| Share of all fallback events | 42/74 (56.8%) |

---

## Route records

Each record is one **observed fallback routing path** on observe turns. Frequencies are event/turn counts from the corpus unless noted as code-only (0 corpus hits).

### OR-RC-01 — Referential clarity hard replacement (dominant)

| Field | Value |
|---|---|
| **Route ID** | OR-RC-01 |
| **Source module** | `game.final_emission_terminal_pipeline` → `game.final_emission_visibility_fallback.apply_visibility_enforcement` → `apply_first_mention_enforcement` → `apply_referential_clarity_enforcement` |
| **Selection module** | `game.final_emission_visibility_fallback` (`standard_visibility_safe_fallback` → `game.final_emission_sealed_fallback.select_visibility_safe_fallback` → `_standard_visibility_safe_fallback_core`) |
| **Content module** | `game.final_emission_sealed_fallback` (prose via visibility candidate helpers → `game.diegetic_fallback_narration`) |
| **Owner bucket** | `sealed-gate` (30/38 bucketed); **8/38 missing bucket** on lineage projection |
| **Selection owner** | `game.final_emission_visibility_fallback` (38/38) |
| **Content owner** | `game.final_emission_sealed_fallback` (38/38) |
| **Trigger condition** | `validate_player_facing_referential_clarity` fails on gate candidate after visibility + first-mention pass; strict-social local substitution not applied (observe turns are predominantly non-strict); `referential_clarity_replacement_applied=True` |
| **Dominant violation** | `ambiguous_entity_reference` (39/42 observe fallback turns) |
| **Dominant content source** | `passive_scene_pressure_fallback` / `sealed_passive_scene_pressure_fallback` (40/42 turns) |
| **Frequency** | **38 events** (86.4% of observe turns; 51.4% of all fallback events) |

### OR-PSP-01 — Sealed passive scene pressure (gate-labeled selection)

| Field | Value |
|---|---|
| **Route ID** | OR-PSP-01 |
| **Source module** | Terminal pipeline visibility chain; sealed terminal branch or visibility candidate ordering |
| **Selection module** | `game.final_emission_gate` (lineage label; implementation delegated post-BK) |
| **Content module** | `game.final_emission_sealed_fallback` |
| **Owner bucket** | Unbucketed on corpus (1/1) |
| **Trigger condition** | `final_route=replaced`; lineage kind `sealed_passive_scene_pressure_fallback` |
| **Frequency** | **1 event** |

### OR-RTP-01 — Response-type prepared emission (non-hard-replace observe fallback)

| Field | Value |
|---|---|
| **Route ID** | OR-RTP-01 |
| **Source module** | `game.final_emission_response_type` / upstream prepared emission path |
| **Selection module** | Unstamped (lineage: selection owner `None`) |
| **Content module** | Unstamped (lineage: content owner `None`) |
| **Owner bucket** | Unbucketed (3/3) |
| **Trigger condition** | Fallback lineage kind `response_type_prepared_emission`; **2/3** turns have `final_route=accept_candidate` (not hard replace) |
| **Frequency** | **3 events** (6.8% of observe turns) |

### OR-VIS-01 — Visibility hard replacement (code path; zero observe corpus hits)

| Field | Value |
|---|---|
| **Route ID** | OR-VIS-01 |
| **Source module** | `apply_visibility_enforcement` when `validate_player_facing_visibility` fails |
| **Selection module** | `game.final_emission_visibility_fallback` |
| **Content module** | `game.final_emission_sealed_fallback` via `standard_visibility_safe_fallback` |
| **Owner bucket** | Would stamp via `visibility_fallback_owner_bucket_from_fields` |
| **Trigger condition** | Visibility validation failure → `route_visibility_enforcement_after_failed_validation` → hard replace (not continuity/concrete-interaction exemptions) |
| **Frequency** | **0** on observe corpus (`visibility_replacement_applied=False` on all 42 fallback turns) |

### OR-FM-01 — First-mention hard replacement (code path; zero observe corpus hits)

| Field | Value |
|---|---|
| **Route ID** | OR-FM-01 |
| **Source module** | `apply_first_mention_enforcement` when first-mention validation fails |
| **Selection module** | `game.final_emission_visibility_fallback` |
| **Content module** | `game.final_emission_sealed_fallback` |
| **Trigger condition** | First-mention validation failure before referential-clarity stage |
| **Frequency** | **0** on observe corpus (`first_mention_replacement_applied=False` on all 42 fallback turns) |

### OR-RC-LOCAL — Referential clarity local substitution (avoidance path)

| Field | Value |
|---|---|
| **Route ID** | OR-RC-LOCAL |
| **Source module** | `apply_referential_clarity_enforcement` strict-social branch |
| **Destination** | In-place text repair (`_try_strict_social_local_pronoun_substitution_repair`); **no** `fallback_selected` event |
| **Trigger condition** | Strict social + dialogue response type + substitutable violations |
| **Frequency** | **0** on observe corpus (`referential_clarity_local_substitution_applied=False` on all 42) |

---

## Visibility candidate subgraph (content destinations)

When OR-RC-01 fires, `_standard_visibility_safe_fallback_core` evaluates candidates in canonical order. On the observe corpus the winning branch is almost always passive scene pressure.

| Candidate helper | Content prose owner | Observe corpus wins |
|---|---|---:|
| `passive_scene_pressure_visibility_fallback_candidates` | `game.diegetic_fallback_narration` (`observe_perception_fallback`) | **40** |
| `anti_reset_local_continuation_visibility_fallback` | `game.anti_reset_emission_guard` / diegetic | 0 |
| `scene_emit_integrity_global_visibility_fallback` | `game.final_emission_scene_emit_integrity` → diegetic global anchor | 0 |
| `npc_pursuit_neutral_nonprogress_visibility_fallback` | `game.diegetic_fallback_narration` | 0 |
| `social_active_interlocutor_visibility_fallback` | `game.final_emission_visibility_fallback` → diegetic social | 0 |
| `opening_visibility_mode_safe_fallback_selection` | `game.final_emission_opening_fallback` | 0 (opening mode inactive on observe) |
| `strict_social_visibility_minimal_fallback_candidate` | strict-social minimal line | 0 |

---

## Entry fan-in (who routes into observe fallback)

| Caller | Calls | Role |
|---|---|---|
| `game.final_emission_terminal_pipeline.run_gate_terminal_enforcement_pipeline` | `apply_visibility_enforcement` | **Single production entry** for visibility/first-mention/referential-clarity chain |
| `game.final_emission_generic_exit` | terminal pipeline | Accept/replace exit convergence |
| `game.final_emission_strict_social_stack` | terminal pipeline | Strict path uses same enforcement tail |

Production fan-in to `apply_visibility_enforcement`: **1** (terminal pipeline). Test fan-in: visibility fallback module tests + speaker contract probes.

---

## Non-fallback observe turns (control group)

| Turn count | `final_route` | Notes |
|---:|---|---|
| 2 | `accept_candidate` | No `fallback_selected` lineage event; represent **4.55%** of observe turns — target state for reduction |

---

## Metadata gaps (observe-specific)

| Gap | Observe impact |
|---|---:|
| Owner bucket missing on lineage | **12/42** fallback events (28.6%) — includes 8 referential-clarity + 3 response-type + 1 sealed-passive |
| `visibility_fallback_kind` / `visibility_fallback_pool` absent on FEM | 42/42 observe fallback turns — selection routed through referential clarity, not visibility-hard stamp |
| Selection/content owner absent | 3/42 (`response_type_prepared_emission`) |

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Route trigger rates, cross-tabs |
| `game/final_emission_visibility_fallback.py` | Enforcement orchestration (`apply_visibility_enforcement`, `apply_referential_clarity_enforcement`) |
| `game/final_emission_sealed_fallback.py` | Selection facade + route meta stamping |
| `game/final_emission_terminal_pipeline.py` | Production entry (`apply_visibility_enforcement`) |
| `game/final_emission_replay_projection.py` | Lineage kind projection (`referential_clarity_hard_replacement`, sealed sub-kinds) |
| [BV1B_fallback_migration_analysis.md](BV1B_fallback_migration_analysis.md) | Relocation verdict (unchanged incidence) |
