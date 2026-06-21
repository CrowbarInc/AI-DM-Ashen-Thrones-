# BV6 — Residual Referential-Clarity Failure Classification

**Date:** 2026-06-21  
**Event:** OBS-M002 / `bv3a_negative_control_multi_person_hard_replace`

---

## Primary classification

### **No candidate grounding**

The repair stack correctly refuses to pick between `guard_captain` and `tavern_runner` when:

- both appear as named anchors in the same sentence,
- the dialogue-attribution pronoun `he` has a **2-entity candidate set**,
- no interlocutor, social NPC, or resolution grounding is present,
- four person-like entities are visible in scene.

This is the **intended EC-M01 rejection path** documented in BV3E.

---

## Secondary factors (not primary blockers)

| Classification | Applies? | Notes |
|---|---|---|
| Multi-violation exclusion | **no** | Single violation only; BV3E multi-violation dialogue path requires ≥2 ambiguous violations |
| Ownership ambiguity | **no** | Ownership buckets are stable (`sealed-gate`); not a selection-owner mislabel |
| Referent drift | **no** | Kind is `ambiguous_entity_reference`, not `referent_drift` |
| Speaker ambiguity | **partial** | Underlying shape is ambiguous speaker, but failure mode is **grounding absence**, not speaker-contract divergence |
| Contract violation | **no** | Validator and repair contracts behave as specified; outcome matches negative-control test intent |

---

## Eligibility gate decision tree

```
ambiguous_entity_reference (he, dialogue attribution)
├── single violation?                    YES
├── multi-entity candidates?             YES → BV3A pronoun repair BLOCKED
├── singular indefinite introducer?      NO  → BV3E alias introducer BLOCKED
├── multi-violation dialogue cluster?  NO  → BV3E MV dialogue BLOCKED
├── interlocutor / social NPC?           NO
├── single visible person?               NO (4 visible)
└── composite eligible?                  NO → hard replace
```

---

## Comparison with cleared shapes

| Shape | Grounding | Candidates | BV3E/BV3A outcome |
|---|---|---|---|
| `"Keep your wits…," he says` + `npc_id=tavern_runner` | yes | 0–1 after repair context | **repaired** (OBS-M001) |
| `"A guard interrupts…," he says` + MV-01 introducer | alias introducer | 2+ disambiguated via introducer | **repaired** (11 replay turns) |
| `Guard Captain and Tavern Runner… "Back away," he says` | **none** | 2 (both named) | **hard replace** (OBS-M002) |

---

## Failure is intentional, not accidental

The event survives because:

1. **Contract design** — BV3E explicitly rejected EC-M01 expansion as medium risk.
2. **Measurement design** — BV3D includes a negative control fixture to prove ineligible shapes still hard-replace.
3. **Replay corpus** — no remaining live turn exhibits this terminal path; incidence is fixture-driven.

Repair did not occur because **no safe deterministic grounding exists**, not because of instrumentation gap or eligibility bug.

---

## Classification verdict

| Field | Value |
|---|---|
| **Primary cause** | `no candidate grounding` |
| **Secondary tag** | `speaker ambiguity` (latent — would manifest if repair were forced) |
| **Accidental vs intentional** | **Intentional retention** per EC-M01 / negative-control contract |
