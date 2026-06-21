# BV4A — Passive Scene Pressure Trigger Taxonomy

**Date:** 2026-06-21  
**Corpus:** 10 `sealed_passive_scene_pressure_fallback` events (post-BV3F refresh).  
**Authority:** `artifacts/bv4a_passive_scene_inventory.json`

---

## Taxonomy overview

| Trigger class | Events | Share | Primary rejection signal |
|---|---:|---:|---|
| **Missing actor initiative** | **10** | **100%** | `passive_scene_pressure_missing_concrete_beat` |
| Stalled interaction | 0 | 0% | — |
| Unresolved scene pressure | 0 | 0% | — |
| No actionable participant | 0 | 0% | — |
| Dialogue dead-end | 0 | 0% | — |
| Other | 0 | 0% | — |

**Concentration:** A **single trigger class** accounts for **100%** of passive-scene sealed fallbacks on the current corpus.

---

## Class definitions and mapping

### Missing actor initiative (10/10)

**Definition:** Passive player action on an observe turn where scene pressure is due, but upstream GM narration lacks a concrete interaction beat (no NPC speaks first, approaches, interrupts, or otherwise advances the moment).

**Detection signals:**

- Player text matches passive observe patterns (`look around`, `watch`, `scan`, `observe`)
- `_passive_scene_pressure_due_for_fallback` would be true when session/scene runtime is present (guard/watch tokens in visible facts)
- `_reply_already_has_concrete_interaction(upstream_text)` returns **false**
- FEM `rejection_reasons_sample` contains `passive_scene_pressure_missing_concrete_beat`

**Representative upstream text:**

```text
As you watch the scene, the notice board lists taxes, curfew rules, and a warning about a missing patrol…
```

**What upstream lacked:** Quoted speech, approach verbs, interruption, or other patterns matched by `_CONCRETE_INTERACTION_PATTERNS` in `game/final_emission_non_strict_stack.py`.

**Terminal response:** Generic guard spear-butt interruption (`passive_scene_pressure_generic` candidate).

---

### Stalled interaction (0/10)

**Definition:** `passive_action_streak >= 2` with continued atmospheric upstream output.

**Corpus status:** Not observed on refreshed corpus. Refresh playthroughs are single-turn hygiene batches; runtime streak metadata is not persisted on FEM records. **Latent risk** on multi-turn sessions.

---

### Unresolved scene pressure (0/10)

**Definition:** Passive-scene pressure due with visible contextual leads present, but upstream fails to activate a lead figure beat.

**Corpus status:** Not observed. No `recent_contextual_leads` captured on FEM; refresh stubs do not populate lead-figure paths (`passive_scene_pressure_lead_figure`).

---

### No actionable participant (0/10)

**Definition:** Pressure due but candidate builder finds no visible entity to attach initiative.

**Corpus status:** Not observed. Frontier-gate scene always has guard visible facts; generic guard candidate always available.

---

### Dialogue dead-end (0/10)

**Definition:** Upstream includes dialogue but fails social continuity or strict-speaker contracts, cascading to sealed replace.

**Corpus status:** Not observed. `strict_social_active=false` on all 10 events; upstream lacks dialogue entirely.

---

### Other (0/10)

**Definition:** Fallback via passive-scene branch without `passive_scene_pressure_missing_concrete_beat` signal.

**Corpus status:** Not observed on current corpus.

---

## Cross-reference: preceding fallback family

| Preceding family | Events | Notes |
|---|---:|---|
| `referential_clarity_upstream_repair` | **10** | BV3E repair applied; RC violations cleared before sealed replace |
| `referential_clarity_hard_replacement` | 0 | Previously masked this path pre-BV3E |

All passive-scene events occur **after successful BV3E RC repair**, confirming the trigger is **not** referential ambiguity — it is **missing concrete interaction** on repaired upstream text.

---

## Trigger mechanism (code path)

```text
apply_non_strict_layer_stack()
  if _passive_scene_pressure_due_for_fallback(...) 
     and not _reply_already_has_concrete_interaction(text):
       reasons.append("passive_scene_pressure_missing_concrete_beat")
```

Downstream terminal pipeline (`select_non_strict_terminal_fallback_for_sealed`) selects `passive_scene_pressure` branch when candidates exist, emitting `passive_scene_pressure_fallback` content.

**GM upstream mirror (existing, not enforced at gate):** `game/gm.py` already injects passive-scene instructions when pressure is due:

```text
"Advance the moment with direct interaction pressure: someone approaches, an NPC speaks first,
 a guard reacts, an interruption lands, or a clue becomes active now."
```

**Gap:** Instructions are prompt-side only; non-strict stack enforces concrete beat at gate without upstream repair loop for this contract.

---

## Implications for BV4A

1. **Single-cluster dominance** simplifies Phase 1 — one upstream satisfier targets 100% of current incidence.
2. **Stalled interaction** and **lead-figure pressure** classes are **latent** on multi-turn corpus; plan should include streak-aware contract without overfitting to single-turn refresh.
3. Taxonomy should be re-run after corpus diversification (multi-turn spine, varied observe prompts) before Phase 3 fallback retirement.

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/bv4a_passive_scene_inventory.json` | Per-event classification |
| `game/final_emission_non_strict_stack.py` | Rejection gate |
| `game/gm.py` L3994–4016 | Upstream instruction mirror |
| [BV4A_passive_scene_inventory.md](BV4A_passive_scene_inventory.md) | Event records |
