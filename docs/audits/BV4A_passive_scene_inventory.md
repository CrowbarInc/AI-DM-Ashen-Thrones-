# BV4A — Passive Scene Pressure Fallback Inventory

**Date:** 2026-06-21  
**Scope:** Post-BV3F refreshed corpus (BV3D measurement filter).  
**Authority:** `tools/bv4a_passive_scene_inventory.py` → `artifacts/bv4a_passive_scene_inventory.json`

---

## Executive summary

The refreshed corpus contains **10** `sealed_passive_scene_pressure_fallback` events — **100%** on the observe route, **90.9%** of remaining observe-route fallback burden (10/11).

All 10 events form a **single homogeneous cluster**:

- Player action: passive observe (`I scan the notice board and watch who reacts.`)
- Upstream GM text: atmospheric scene description **without** concrete interaction beat
- Non-strict rejection: `passive_scene_pressure_missing_concrete_beat`
- Preceding path: BV3E referential-clarity upstream repair succeeded (`exact_alias_introducer`)
- Terminal emission: identical sealed generic guard-interruption template

BV3E eliminated referential-clarity hard replace on these turns; passive-scene pressure sealed fallback is the **residual terminal path** when upstream text fails the concrete-interaction obligation.

---

## Corpus context

| Metric | Value |
|---|---:|
| Canonical FEM instances (BV3D scan) | 95 |
| Observe turns | 23 |
| Observe fallback turns | 11 |
| `sealed_passive_scene_pressure_fallback` events | **10** |
| `referential_clarity_hard_replacement` (residual) | 1 |
| Unique upstream text shapes | **1** |
| Unique emitted content shapes | **1** |

---

## Event records

| Event ID | Turn ID | Route | Owner bucket | Selection owner | Preceding family | Triggering condition | Emitted content (preview) |
|---|---|---|---|---|---|---|---|
| PSP-E001 | OBS-PSP001 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | The pause snaps when a nearby gate guard points with his spear-butt… |
| PSP-E002 | OBS-PSP002 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E003 | OBS-PSP003 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E004 | OBS-PSP004 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E005 | OBS-PSP005 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E006 | OBS-PSP006 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E007 | OBS-PSP007 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E008 | OBS-PSP008 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E009 | OBS-PSP009 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |
| PSP-E010 | OBS-PSP010 | observe | sealed-gate | `game.final_emission_gate` | referential_clarity_upstream_repair | `passive_scene_pressure_missing_concrete_beat` | (same template) |

**Content owner (all events):** `game.final_emission_sealed_fallback`  
**Realization family (all events):** `gate_terminal_repair`  
**Final emitted source (all events):** `passive_scene_pressure_fallback`  
**Source class (all events):** refreshed replay (`artifacts/scene_canon_hygiene_runtime/*/data/session_log.jsonl`)

---

## Per-event detail (representative: PSP-E001)

| Field | Value |
|---|---|
| **Artifact** | `artifacts/scene_canon_hygiene_runtime/235b7066411f48b5bb8e21012a1737d2/data/session_log.jsonl` |
| **Locator** | `$line[2]` |
| **Player text** | `I scan the notice board and watch who reacts.` |
| **Upstream text (pre-gate)** | `As you watch the scene, the notice board lists taxes, curfew rules, and a warning about a missing patrol…` |
| **Rejection reasons** | `passive_scene_pressure_missing_concrete_beat` |
| **BV3E repair** | `referential_clarity_bv3e_repair_mode=exact_alias_introducer`; `upstream_repair_applied=true` |
| **RC violations post-repair** | 0 |
| **Emitted content** | `The pause snaps when a nearby gate guard points with his spear-butt instead of waiting for you to choose. "Board, runner, or road," he says. "Pick one before the gate swallows the trail."` |
| **Passive candidate kind** | `passive_scene_pressure_generic` (terminal sealed pool) |

Remaining nine events differ only by hygiene-runtime batch path; behavioral fingerprint is identical.

---

## Causal chain (all 10 events)

```text
Passive observe player action
  → scene runtime marks passive action / pressure due (guard in visible facts)
  → GM returns atmospheric observe narration (no dialogue / approach / interruption)
  → non_strict_stack: passive_scene_pressure_missing_concrete_beat
  → BV3E upstream RC repair succeeds in-place
  → terminal visibility chain still selects sealed passive_scene_pressure branch
  → final_route=replaced; lineage kind=sealed_passive_scene_pressure_fallback
```

---

## Why this family dominates post-BV3F

Before BV3F, these turns classified as **`referential_clarity_hard_replacement`** (attribution family) because RC violations triggered hard replace **before** passive-scene content was the visible lineage kind. BV3E upstream repair clears RC violations, exposing the **underlying** passive-scene pressure terminal path that was previously masked by attribution hard replace.

This is **not** a new failure mode — it is the **next layer** of the same observe-turn stack becoming measurable after BV3E success.

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/bv4a_passive_scene_inventory.json` | Machine-readable event inventory |
| `artifacts/bv3f_reduction_metrics.json` | Post-BV3F family counts |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Incidence cross-tabs |
| `game/final_emission_non_strict_stack.py` L137–142 | Concrete-beat rejection gate |
| `game/final_emission_passive_scene_pressure.py` | Sealed candidate builder |
