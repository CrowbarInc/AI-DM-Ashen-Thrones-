# BV4A — Upstream Satisfier Map

**Date:** 2026-06-21  
**Question:** What upstream condition would have prevented each `sealed_passive_scene_pressure_fallback` event?  
**Authority:** `artifacts/bv4a_passive_scene_inventory.json`, code path analysis.

---

## Gap taxonomy

| Gap type | Events affected | Share | Description |
|---|---:|---:|---|
| **Missing contract** | 10 | 100% | No enforced upstream obligation that observe text under passive-scene pressure must include a concrete interaction beat |
| **Missing narrative obligation** | 10 | 100% | GM output is atmospheric-only; fails `_reply_already_has_concrete_interaction` |
| **Missing initiative source** | 10 | 100% | No NPC/guard speaks first, approaches, or interrupts in upstream text |
| **Missing projection** | 10 | 100% | BV3E RC repair succeeds but projection/lineage still routes to sealed replace rather than accepting repaired upstream |
| **Missing ownership source** | 10 | 100% | Selection owner stamped as `game.final_emission_gate` instead of visibility/passive-scene module |

---

## Per-event satisfier matrix

All 10 events share identical satisfier requirements:

| Event | Missing contract | Missing projection | Missing initiative source | Missing narrative obligation | Missing ownership source | Satisfier that would prevent fallback |
|---|---|---|---|---|---|---|
| PSP-E001 … PSP-E010 | ✓ | ✓ | ✓ | ✓ | ✓ | Upstream concrete-beat contract + accept repaired text at terminal fork |

---

## Satisfier specifications

### SAT-01 — Passive-scene concrete interaction contract (primary)

**Prevents:** All 10 events  
**Gap closed:** missing_contract, missing_narrative_obligation, missing_initiative_source

**Condition:** When `passive_scene_pressure` payload is active (or `_passive_scene_pressure_due_for_fallback` would be true), upstream GM output MUST satisfy `_reply_already_has_concrete_interaction(text)` before terminal gate.

**Concrete patterns required (any one):**

- Quoted dialogue (`"…"`)
- Approach / interruption verbs (`approaches`, `comes straight to`, `speaks first`, `points`, `blocks`, `interrupts`, …)

**Existing partial implementation:** `game/gm.py` injects equivalent instructions into GM payload when pressure is due — but stubbed refresh GPT ignores them, and gate has no upstream repair loop for this contract (unlike BV3E RC repair).

**Enforcement options (analysis only):**

| Option | Layer | Mechanism |
|---|---|---|
| SAT-01a | Upstream validator | Reject/regenerate GM output missing concrete beat when `passive_scene_pressure` active |
| SAT-01b | Upstream repair | Deterministic beat injection (named guard speaks) before gate — analogous to BV3E alias introducer |
| SAT-01c | Retry policy | Extend scene_stall / answer retry to target `passive_scene_pressure_missing_concrete_beat` |

---

### SAT-02 — Post-repair accept path (secondary)

**Prevents:** 10 events where BV3E repair already fixed RC  
**Gap closed:** missing_projection

**Condition:** After `referential_clarity_upstream_repair_applied=true` and `referential_clarity_unrepaired_violation_count=0`, re-evaluate concrete-beat check on **repaired** text. If repaired text satisfies concrete interaction, accept upstream instead of sealed replace.

**Rationale:** Current stack applies BV3E repair then still hard-replaces via passive-scene branch because original upstream failed concrete beat; repaired text may include dialogue from introducer substitution but corpus shows guard-interruption template still selected — indicating check runs pre-repair or repaired text still fails pattern match.

**Verification needed in implementation cycle:** Trace whether `_reply_already_has_concrete_interaction` runs on pre- vs post-BV3E text in terminal pipeline ordering.

---

### SAT-03 — Visible-fact-aligned initiative (scene-aware)

**Prevents:** Generic template substitution; improves narrative quality  
**Gap closed:** missing_initiative_source (quality)

**Condition:** Concrete beat MUST reference a visible-scene entity (guard, runner, board watcher) consistent with `visible_facts` and `recent_contextual_leads`.

**Existing candidate pool:** `game/final_emission_passive_scene_pressure.py` already builds scene-aware candidates (`passive_scene_pressure_guard_rumor`, `lead_figure`, `visible_figure`) — upstream satisfier should **produce equivalent beats**, not rely on terminal sealed replace.

---

### SAT-04 — Selection owner alignment (measurement)

**Prevents:** 0 incidence events (behavior-neutral)  
**Gap closed:** missing_ownership_source

**Condition:** Passive-scene terminal selections stamp `game.final_emission_visibility_fallback` as selection owner, not gate hub.

**Note:** Measurement-only; does not reduce incidence but prevents false relocation signals during BV4A verification (mirrors BV3 Phase 1 EC-05/EC-10 pattern).

---

## Satisfier ↔ trigger class mapping

| Trigger class | Primary satisfier | Secondary satisfier |
|---|---|---|
| Missing actor initiative (10) | **SAT-01** concrete interaction contract | SAT-02 post-repair accept |
| Stalled interaction (latent) | SAT-01 + streak-aware escalation in GM payload | SAT-03 lead-figure beats |
| Unresolved scene pressure (latent) | SAT-03 visible-fact initiative | SAT-01 |
| No actionable participant (latent) | SAT-03 | — |
| Dialogue dead-end (latent) | Strict-social path (out of scope) | — |

---

## Why upstream satisfiers were not previously required

| Layer | BV3 focus | BV4A gap |
|---|---|---|
| Referential clarity | BV3A/BV3E upstream repair for ambiguous pronouns | **Satisfied** on 10/10 events |
| Passive scene pressure | Prompt instructions only (`gm.py`) | **Not enforced** at upstream validator or repair layer |
| Terminal sealed branch | Always available when non-strict stack rejects | Becomes dominant path once RC hard replace eliminated |

---

## Evidence

| Source | Role |
|---|---|
| `game/final_emission_non_strict_stack.py` L47–55, L137–142 | Concrete interaction patterns + rejection |
| `game/gm.py` L3994–4016 | Passive-scene upstream instructions |
| `game/final_emission_passive_scene_pressure.py` | Scene-aware candidate templates |
| [BV4A_trigger_taxonomy.md](BV4A_trigger_taxonomy.md) | Trigger classification |
