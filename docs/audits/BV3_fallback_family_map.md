# BV3 — Observe-Route Fallback Family Map

**Date:** 2026-06-21  
**Scope:** Group observe-route fallback paths into the BV3 family taxonomy.  
**Corpus:** 42 observe fallback turns / 74 total fallback events on 107 FEM instances.

---

## Family taxonomy (observe route)

| Family | Lineage / FEM kinds | Observe events | % of observe fallbacks | Primary modules |
|---|---|---:|---:|---|
| **Visibility fallback** | `visibility_hard_replacement` (projected); visibility enforcement hard replace | **0** | 0% | `final_emission_visibility_fallback` |
| **Opening fallback** | `scene_opening`, opening visibility mode candidates | **0** | 0% | `opening_deterministic_fallback`, `final_emission_opening_fallback` |
| **Sealed fallback** | `sealed_passive_scene_pressure_fallback`, passive-scene content sources | **41** | 97.6% | `final_emission_sealed_fallback` + passive-scene/diegetic content |
| **Replay fallback** | Projection-only lineage packaging; golden replay adapters | **0 runtime** | — | `final_emission_replay_projection`, `tests/helpers/golden_replay_projection.py` |
| **Speaker fallback** | Strict-social speaker finalize / emergency lines | **0** | 0% | `social_exchange_emission`, `speaker_contract_enforcement` |
| **Attribution fallback** | Referential clarity + first-mention enforcement replacements | **38** | 90.5% | `final_emission_visibility_fallback`, `final_emission_referential_clarity`, `narration_visibility` |
| **Diagnostics fallback** | Response-type prepared emission without hard replace | **3** | 7.1% | `final_emission_response_type`, upstream prepared emission |

**Note:** Families overlap by design. Referential-clarity hard replacement (attribution) **selects** sealed passive-scene content (sealed) in 40/38 referential-clarity turns — the dominant cross-family pattern on observe.

---

## Cross-family matrix (observe corpus)

|  | Sealed content | Visibility select | Attribution trigger | Diagnostics |
|---|---:|---:|---:|---:|
| **Referential clarity hard replacement** | 38 | 38 | 38 | — |
| **Sealed passive scene pressure** | 1 | 0 (gate label) | — | — |
| **Response type prepared emission** | — | — | — | 3 |

---

## Family detail

### Visibility fallback

- **Runtime paths on observe:** OR-VIS-01 (see inventory) — **zero corpus incidence**.
- **Relationship:** Visibility enforcement runs on every observe turn via terminal pipeline, but **passes**; failures cascade to referential clarity, not visibility-hard replace.
- **Diegetic family:** Would stamp `fallback_family_used=observe` when visibility-hard replace selects observe templates.

### Opening fallback

- **Runtime paths on observe:** Opening visibility mode branch in `_standard_visibility_safe_fallback_core` — inactive (`opening_mode_active_for_turn` false on observe corpus).
- **Scene opening route** is separate (`route_kind=scene_opening`, 31 fallbacks) — excluded from observe inventory but shares sealed/visibility machinery.

### Sealed fallback

- **Dominant content family on observe.** Nearly all hard replaces stamp `prepare_sealed_replacement_route_meta` and project `game.final_emission_sealed_fallback` as content owner.
- **Sub-kind projection:** 40/42 → `sealed_passive_scene_pressure_fallback`; 2/42 → no sealed sub-kind (response-type / accept paths).
- **Realization family:** `gate_terminal_repair` on 1/42 observe fallback turns; **41/42** lack `realization_fallback_family` on FEM — attribution/provenance gap, not absence of sealed content.

### Replay fallback

- **Not a runtime selector.** Read-side projection (`build_fem_runtime_lineage_events`, golden replay helpers) packages runtime events for measurement.
- **Observe impact:** Lineage defaults `event_owner=game.final_emission_gate` on all 74 corpus events while selection owner split shows visibility vs gate — packaging hub, not trigger hub.

### Speaker fallback

- **No observe-corpus events.** Strict-social speaker finalize paths use terminal pipeline but observe turns in corpus are non-strict (`strict_social_active=false` on referential-clarity replacements).
- **Local substitution** (OR-RC-LOCAL) is strict-social-only — unused on observe.

### Attribution fallback

- **Primary cost center.** `referential_clarity_hard_replacement` accounts for **38/74 (51.4%)** of **all** fallback events repo-wide, not just observe.
- **Violation profile:** `ambiguous_entity_reference` on 39/42 observe fallback turns.
- **First-mention attribution:** Runs but does not fire hard replace on observe corpus.

### Diagnostics fallback

- **`response_type_prepared_emission`:** 3 observe events; 2 with `final_route=accept_candidate` — classified as diagnostics/prepared-emission lineage, not terminal hard replace.
- **Ownerless:** All 3 lack selection/content owner stamps — contributes to global 13 ownerless count (BV1B).

---

## Family ↔ owner bucket alignment (observe)

| Family | Expected bucket | Observe bucketed | Observe unbucketed |
|---|---|---:|---:|
| Attribution → sealed content | `sealed-gate` | 30 | 8 (referential clarity) |
| Sealed passive (gate label) | `sealed-gate` | 0 | 1 |
| Diagnostics / response-type | mixed / upstream-prepared | 0 | 3 |

---

## Implications for reduction

1. **Attribution + sealed content coupling** — reducing observe fallback requires fixing **upstream referential clarity**, not relocating sealed content ownership again.
2. **Visibility/opening/speaker families** — code paths exist but are **not** observe-corpus cost drivers; elimination candidates there are low ROI for route rate.
3. **Diagnostics family** — small volume but high ownership ambiguity; registry enforcement closes gaps without behavior change.
4. **Replay family** — adjust projection defaults (gate label vs selection owner) for measurement clarity only; no incidence impact.

---

## Evidence

| Source | Role |
|---|---|
| [BV3_observe_route_inventory.md](BV3_observe_route_inventory.md) | Route IDs OR-RC-01 … OR-RTP-01 |
| `tools/bv1b_fallback_incidence_validation.py` | `FAMILY_ROUTES`, `FAMILY_SUBSYSTEMS` |
| `game/final_emission_replay_projection.py` | Kind constants and split-owner projection |
| `game/diegetic_fallback_narration.py` | Diegetic `fallback_family` taxonomy (`observe`, `scene_opening`, …) |
