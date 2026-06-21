# BV4B — Concrete Beat Contract

**Date:** 2026-06-21  
**Phase:** BV4B (EC-4A-01 / EC-4A-02)  
**Trigger closed:** `passive_scene_pressure_missing_concrete_beat`  
**Authority:** `game/final_emission_passive_scene_pressure.py`, `game/final_emission_non_strict_stack.py`

---

## Purpose

Define the upstream contract for satisfying passive-scene pressure **before** terminal sealed replacement (`sealed_passive_scene_pressure_fallback`). A turn satisfies the contract when player-facing text includes at least one **concrete beat** detectable by `reply_has_concrete_interaction()`.

This contract is enforced upstream at:

1. **Gate pre-stack** — `apply_observe_passive_scene_concrete_beat_upstream_satisfier` before `run_non_strict_layer_stack`
2. **Terminal pre-visibility** — same satisfier after BV3E referential-clarity repair
3. **Visibility / first-mention / RC skip guards** — when satisfier meta + concrete text are present

---

## Contract predicate

```text
passive_scene_concrete_beat_satisfied(text) :=
    reply_has_concrete_interaction(text) is True
```

Detection uses `_CONCRETE_INTERACTION_PATTERNS`:

| Pattern class | Examples |
|---|---|
| Quoted dialogue | `"Move along."`, `'Tell me what you know.'` |
| Initiative / approach verbs | `approaches`, `comes straight to`, `squares up`, `cuts across`, `blocks`, `halts`, `calls out`, `speaks first`, `says`, `asks`, `warns`, `orders`, `interrupts`, `points`, `hands` |

Atmospheric-only observe prose (board lists, curfew rules, ambient description) **does not** satisfy the contract.

---

## Valid beat types

### 1. Valid interaction beat

**Definition:** A visible actor performs a directed physical or social action toward the player without necessarily speaking.

**Satisfies when:** Text includes an initiative verb from the concrete-interaction pattern set tied to a scene-visible actor.

**Examples:**

- `A guard squares up to you.`
- `The runner cuts through the crowd and stops at your shoulder.`

**Beat type stamp:** `guard_reaction`, `observer_interruption` (when lead-figure pool selected)

---

### 2. Valid interruption beat

**Definition:** A scene actor breaks passive observation by interrupting, blocking, or forcing a choice.

**Satisfies when:** Text includes interruption semantics (`interrupts`, `blocks`, `halts`, `points`, `comes straight to`) plus player-directed framing.

**Examples:**

- `The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose.`
- `"Enough watching," they say. "Ask me now, or lose the trail."`

**Beat type stamp:** `generic_interruption`, `observer_interruption`

---

### 3. Valid dialogue beat

**Definition:** Quoted speech from a scene-visible actor establishes initiative.

**Satisfies when:** Text contains quoted dialogue (`"…"` or `'…'`) attributed to or adjacent with a visible actor.

**Examples:**

- `'A guard notices you lingering and comes over. "If you're waiting on trouble, it already passed," he says.'`
- `"Standing still won't help that patrol," he says, stabbing two fingers at the posting.`

**Beat type stamp:** `guard_reaction` (guard-rumor / visible-figure pools)

---

### 4. Valid environmental reaction beat

**Definition:** A non-dialogue scene element reacts in a way that forces player attention (merchant nod, board change, crowd shift) when no named NPC pool applies.

**Satisfies when:** Text describes an environmental actor acknowledging the player's passive stance with directed framing.

**Examples:**

- `A nearby merchant catches your lingering look and nods. "If you mean to buy or ask, speak up before the board changes," she says.`

**Beat type stamp:** `merchant_acknowledgement`, `environmental_reaction`

---

## Upstream satisfier rules (EC-4A-01)

| Condition | Action |
|---|---|
| `res_kind != observe` or strict-social active | No-op |
| Passive-scene pressure not due | No-op |
| Text already satisfies contract | No injection; `satisfier_applied=false` |
| Pressure due + beat absent + visible actor pool exists | Inject minimal deterministic beat (EC-4A-02) |
| Injection succeeds | Stamp `passive_scene_concrete_beat_satisfier_applied=true`, `passive_scene_pressure_fallback_avoided=true` |

**Due-check:** `_passive_scene_pressure_due_for_fallback` (passive streak, contextual leads, guard/watch/rumor visible facts).

**Beat selection:** `_select_deterministic_upstream_concrete_beat` — same candidate pool as sealed fallback, merged onto existing upstream text via `_merge_upstream_concrete_beat`.

---

## Deterministic injection rules (EC-4A-02)

| Input state | Output |
|---|---|
| Atmospheric upstream + pressure due + guard/rumor visible facts | Guard-rumor or visible-figure beat appended |
| Atmospheric upstream + pressure due + contextual lead | Lead-figure interruption beat appended |
| Atmospheric upstream + pressure due + merchant in visible facts | Merchant acknowledgement beat appended |
| Atmospheric upstream + pressure due + no specific pool | Generic guard interruption beat appended |

Injection is **replay-safe**: candidate selection reads only session runtime + scene `visible_facts` + deterministic ordering. No RNG.

---

## Meta instrumentation

| Field | Meaning |
|---|---|
| `passive_scene_concrete_beat_satisfier_attempted` | Satisfier evaluated on observe route |
| `passive_scene_concrete_beat_satisfier_eligible` | Pressure due and beat absent at evaluation |
| `passive_scene_concrete_beat_satisfier_applied` | Beat injected upstream |
| `passive_scene_concrete_beat_type` | Selected beat classification |
| `passive_scene_pressure_fallback_avoided` | Sealed PSP replace skipped due to contract satisfaction |
| `producer_repair_kind` | `passive_scene_concrete_beat` when applied |

Meta is preserved across `build_gate_accept_fem_base` in the generic accept exit path.

---

## Non-goals (ownership unchanged)

- Sealed fallback candidate builders remain in `final_emission_passive_scene_pressure.py`
- Visibility enforcement ownership unchanged; skip guards only when upstream contract already satisfied
- No relocation of PSP selection to a new module
- No speaker-finalize or replay-divergence tolerance introduced

---

## Related artifacts

| Artifact | Role |
|---|---|
| `artifacts/bv4b_concrete_beat_metrics.json` | Post-refresh measurement |
| `artifacts/bv4a_passive_scene_inventory.json` | Pre-BV4B PSP cluster inventory |
| `tests/test_bv4b_concrete_beat_upstream_satisfier.py` | Unit + gate integration tests |
