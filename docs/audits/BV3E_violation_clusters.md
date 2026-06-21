# BV3E — Violation Cluster Inventory

**Date:** 2026-06-21  
**Scope:** All `ambiguous_entity_reference` observe turns in BV3D measurement corpus (97 FEM / 23 observe).  
**Machine-readable:** `artifacts/bv3e_violation_clusters.json`

---

## Executive summary

| Cluster | Turns | Share of ambiguous observe |
|---|---:|---:|
| **multi_violation** | 10 | 90.9% |
| **ambiguous_speaker** | 1 | 9.1% (positive-control fixture only) |
| ambiguous_target (isolated) | 0 | — |
| ambiguous_ownership (primary) | 0 | — |
| referent_drift (primary) | 0 | — |
| mixed_ambiguity | 0 | — |

Production-shaped observe failures are dominated by **multi-violation alias + pronoun clusters** on the gate-interruption template (`a nearby guard … he says`). BV3A covered only the isolated dialogue-attribution `he` + interlocutor shape (fixture OBS-M001).

---

## Cluster definitions

| Cluster | Detection rule | Representative token(s) |
|---|---|---|
| **ambiguous_speaker** | Single `ambiguous_entity_reference`, pronoun in dialogue speech tag | `he`, `she` |
| **ambiguous_target** | Role alias with multi-entity `candidate_entity_ids` | `guard`, `runner` |
| **ambiguous_ownership** | Possessive pronoun without dialogue attribution | `his`, `their` |
| **referent_drift** | Primary kind `referent_drift` | `they` |
| **multi_violation** | >1 `ambiguous_entity_reference` on turn | `guard` + `his` + `he` |
| **mixed_ambiguity** | Residual / unclassified | — |

---

## multi_violation (10 turns — production template)

**Text shape:**

```text
The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose.
"Board, runner, or road," he says. "Pick one before the gate swallows the trail."
```

**Violation combination (live validation on frontier_gate hygiene world):**

| # | kind | token | candidate_entity_ids |
|---|---|---|---|
| 1 | ambiguous_entity_reference | guard | gate_guard, guard_captain |
| 2 | ambiguous_entity_reference | his | gate_guard, guard_captain |
| 3 | ambiguous_entity_reference | he | (empty — dialogue tag) |

**Visible entities (typical):** gate_guard, gate_serjeant, guard_captain, refugee, tavern_runner, threadbare_watcher (6 person-like).

**Turn ids:** OBS-M003, OBS-M004, OBS-M006, OBS-M008, OBS-M009, OBS-M012, OBS-M014, OBS-M015, OBS-M016, OBS-M021, OBS-M023 (canonical).

**BV3A eligibility:** ineligible (`len(ambiguous) != 1`, non-pronoun primary token in FEM sample).

**BV3E eligibility:** eligible via **exact-alias introducer** disambiguation (`guard` → gate_guard when title-bearing alias excluded).

---

## ambiguous_speaker (1 turn — fixture)

| turn id | source | shape |
|---|---|---|
| OBS-M001 | measurement fixture | `"…," he says` + interlocutor + social NPC |

BV3A upstream repair **applied** on this turn (pre-BV3E).

---

## ambiguous_target / ambiguous_ownership (secondary within multi_violation)

Not observed as **primary** turn shapes in the BV3D corpus. Possessive (`his`) and role alias (`guard`) violations appear as **secondary** violations bundled with dialogue-attribution `he` on the gate-interruption template.

---

## Evidence

| Artifact | Role |
|---|---|
| `artifacts/bv3e_violation_clusters.json` | Cluster assignment per turn |
| `artifacts/bv3d_eligibility_report.json` | Frozen FEM eligibility stamps |
| `artifacts/bv3c_observe_eligibility.json` | Full 65-turn BV3C audit (includes archives) |
| `docs/audits/BV3A_referential_clarity_inventory.md` | Pre-refresh 39-turn shape baseline |
