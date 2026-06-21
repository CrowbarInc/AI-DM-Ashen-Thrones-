# BV3A — Referential Clarity Violation Shape Inventory

**Date:** 2026-06-21  
**Scope:** All `ambiguous_entity_reference` instances in the protected 107-FEM corpus (BV1B scan).  
**Method:** FEM field extraction (`referential_clarity_violation_sample`, `referential_clarity_violation_kinds`) + shape classifier aligned to BV3A contract groups.

---

## Executive summary

All **39** corpus turns carrying `ambiguous_entity_reference` are **`route_kind=observe`**. The dominant shape is **ambiguous speaker** (quoted dialogue + unattributed `he`/`she` speech tag, **35/39** turns). **Zero** candidate entity IDs appear on violations (`candidate_entity_ids=[]` in **48/48** sampled violation records) — pronouns lack a validator-resolved antecedent despite multiple visible scene actors (typically **4** person-like entities).

BV3A repair targets **dialogue-attribution ambiguous speaker** violations with **contextual grounding** (active interlocutor, resolution social `npc_id`, or single visible person).

---

## Corpus counts

| Metric | Value |
|---|---:|
| Turns with `ambiguous_entity_reference` | **39** |
| Observe-route share | **39/39 (100%)** |
| Turns with `referential_clarity_replacement_applied=True` | **39** |
| Turns with `referential_clarity_hard_replacement` lineage kind | **38** (repo-wide) |
| Referential clarity events on observe route | **38/42** observe fallback events |

---

## Shape groups (turn-primary)

| Shape group | Turns | Share | Description |
|---|---:|---:|---|
| **ambiguous_speaker** | **35** | 89.7% | Quoted dialogue followed by `he`/`she` speech tag (`…," he says` / `…" he says`) without named antecedent |
| **missing_actor_identity** | **3** | 7.7% | Neuter/inanimate token (`it`) or dialogue without recoverable person anchor |
| **unresolved_pronoun** | **1** | 2.6% | Narrative possessive (`his`) without local person anchor (non-dialogue-attribution) |
| **ambiguous_target** | **0** | 0% | Multi-entity candidate sets (not observed on this corpus) |
| **ambiguous_ownership** | **0** | 0% | Possessive-only as primary turn shape (possessives appear as secondary violations) |

---

## Shape groups (violation-level)

| Shape group | Violations | Top tokens |
|---|---:|---|
| ambiguous_speaker | 35 | `he` (35) |
| missing_actor_identity | 3 | `it` (1), dialogue without tag match (2) |
| unresolved_pronoun | 10 | `his` (10), `their` (1), `its` (1) |

*Violation count exceeds turn count when multiple pronoun violations appear on one turn (rare; possessive secondary).*

---

## Token frequency (ambiguous_entity_reference)

| Token | Violations |
|---|---:|
| `he` | 35 |
| `his` | 10 |
| `it` | 1 |
| `their` | 1 |
| `its` | 1 |

---

## Visibility context

| Checked entities (person-like visible) | Turns |
|---|---:|
| 4 person-like entities | 30 |
| 5 person-like entities | 1 |
| 0 (missing FEM stamp) | 8 |

Typical visible persons on frontier_gate corpus: `guard_captain`, `refugee`, `tavern_runner`, `threadbare_watcher`.

---

## Representative samples

### ambiguous_speaker (dominant)

```json
{
  "kind": "ambiguous_entity_reference",
  "token": "he",
  "candidate_entity_ids": [],
  "sentence_text": "\"if you're waiting on trouble, it already passed the checkpoint,\" he says",
  "offset": 309
}
```

### missing_actor_identity

```json
{
  "kind": "ambiguous_entity_reference",
  "token": "it",
  "candidate_entity_ids": [],
  "sentence_text": "\"tell me what you know, or get on the east-road trail before it dies"
}
```

### unresolved_pronoun (narrative possessive)

```json
{
  "kind": "ambiguous_entity_reference",
  "token": "his",
  "candidate_entity_ids": [],
  "sentence_text": "half-hidden within that ditch lies the body of a dead courier, his worn dagger still sheathed at his side"
}
```

---

## BV3A repair eligibility (corpus-shaped)

| Shape | BV3A local repair | Rationale |
|---|---|---|
| ambiguous_speaker + contextual grounding | **Eligible** | Speech-tag pronoun + interlocutor/social NPC/single visible person |
| ambiguous_speaker + 4 visible, no grounding | **Ineligible** | Cannot disambiguate speaker without context (preserves hard replace) |
| missing_actor_identity (`it`) | **Ineligible** | Non-person/neuter; no safe substitution |
| unresolved_pronoun (`his` narrative) | **Ineligible** | Multi-clause narration; not dialogue-attribution shaped |

---

## Implementation mapping

| Module | Role |
|---|---|
| `game.final_emission_referential_clarity` | Violation shape detection, local repair, upstream observe repair |
| `game.final_emission_terminal_pipeline` | Upstream repair before `apply_visibility_enforcement` |
| `game.final_emission_visibility_fallback` | Non-strict local repair before hard replace; meta preservation |

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Baseline incidence |
| BV3A corpus scan script (39 turns) | Shape classification |
| [BV3_observe_route_inventory.md](BV3_observe_route_inventory.md) | Route OR-RC-01 context |
