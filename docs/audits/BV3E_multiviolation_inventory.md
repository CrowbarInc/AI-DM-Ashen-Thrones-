# BV3E — Multi-Violation Inventory

**Date:** 2026-06-21  
**Source:** BV3C class-B turns + BV3D measurement corpus live re-validation  
**Machine-readable:** `artifacts/bv3e_shape_simulation.json`

---

## Summary

| Metric | Count |
|---|---:|
| Multi-violation observe turns (BV3D corpus) | **11** |
| Distinct violation combination patterns | **1** (gate-interruption template) |
| BV3A-eligible | **0** |
| BV3E-eligible (simulated) | **11** |
| BV3E repair applied (simulated) | **11** |

All 11 turns share the same gate-interruption candidate. The 10 refreshed hygiene replays plus canonical `data/session_log.jsonl` OBS-M023.

---

## Per-pattern inventory

### Pattern MV-01 — alias + possessive + dialogue speaker

| Field | Value |
|---|---|
| **Violation combination** | `guard` (multi-entity alias) + `his` (multi-entity possessive) + `he` (dialogue attribution, empty candidates) |
| **Visible entities** | gate_guard, gate_serjeant, guard_captain, refugee, tavern_runner, threadbare_watcher |
| **Interlocutor / social NPC** | absent |
| **Grounding availability** | Singular indefinite introducer `a nearby guard`; exact-alias tie-break excludes title-bearing `guard_captain` when sentence lacks `captain` |
| **BV3A repair feasibility** | **No** — multi-violation gate + non-pronoun primary in FEM |
| **BV3E repair feasibility** | **Yes (low risk)** — substitute introducer alias `guard` → `gate guard`; re-validation clears all three violations |
| **Repair mode** | `exact_alias_introducer` |
| **Simulated outcome** | upstream repair applied; hard replace avoided |

**Representative turn ids:** OBS-M003 … OBS-M016, OBS-M021, OBS-M023

---

## BV3C archive multi-violation note (30+ stale turns)

Pre-refresh archive turns (OBS-001 … OBS-030) carried the **older** ambiguous-speaker-only shape (`A guard peels away… "…," he says`) with 5 visible persons and no interlocutor. Those remain **ineligible** under BV3E (no singular indefinite introducer alias cluster; dialogue `he` without anchor).

| Archive pattern | BV3E |
|---|---|
| Dialogue `he` + multi-person + no introducer alias | ineligible (preserves hard replace) |
| Gate-interruption `a nearby guard … he says` | **eligible** |

---

## Grounding availability matrix

| Grounding source | MV-01 |
|---|---|
| active_interlocutor | ✗ |
| resolution.social.npc_id | ✗ |
| sole visible person | ✗ (6 persons) |
| dialogue-attribution exception (BV3A) | ✗ (blocked by multi-violation) |
| exact-alias introducer disambiguation (BV3E) | ✓ gate_guard |

---

## Repair feasibility summary

| Risk | Patterns | Action |
|---|---|---|
| **Low** | MV-01 gate-interruption | **Implemented** — alias introducer substitution |
| **Medium** | possessive-only narrative (`his` in non-dialogue) | Not implemented |
| **High** | multi-person dialogue without introducer | Not implemented |
