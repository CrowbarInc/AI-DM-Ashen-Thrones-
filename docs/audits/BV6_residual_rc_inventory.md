# BV6 — Residual Referential-Clarity Inventory

**Date:** 2026-06-21  
**Primary metric:** `referential_clarity_hard_replacement` count = **1** (BV3D measurement scope)  
**Corpus:** 95 FEM instances, 23 observe turns (`tools/bv3a_referential_clarity_metrics.py`)

---

## Executive summary

The sole remaining `referential_clarity_hard_replacement` event is **not a replay regression**. It is the **BV3D negative-control fixture** `bv3a_negative_control_multi_person_hard_replace`, materialized from `test_observe_ambiguous_speaker_without_interlocutor_still_hard_replaces`.

**Replay-only RC hard replacement count: 0.**

---

## Isolated event record

| Field | Value |
|---|---|
| **Turn id** | `OBS-M002` (BV3D eligibility inventory) |
| **Fixture id** | `bv3a_negative_control_multi_person_hard_replace` |
| **Artifact** | `artifacts/bv3d_measurement/positive_control_fixtures.jsonl` |
| **Locator** | `$line[2]` |
| **Route** | `observe` |
| **Resolution prompt** | `I look around.` |
| **Triggering text (gate entry)** | `Guard Captain and Tavern Runner stand near the gate. "Back away," he says.` |
| **Violation sentence** | `"back away," he says` |
| **Ambiguity classification** | `ambiguous_speaker` — dialogue-attribution `he` with **2-entity candidate set**, no contextual grounding |
| **Violation kind** | `ambiguous_entity_reference` |
| **Token** | `he` |
| **Candidate entity ids** | `guard_captain`, `tavern_runner` |
| **Candidate aliases** | `guard captain`, `tavern runner` |
| **Visible person-like entities** | 4 (`guard_captain`, `refugee`, `tavern_runner`, `threadbare_watcher`) |
| **Interlocutor present** | no (`active_interlocutor_id=null`, `npc_id=null`) |
| **Social NPC present** | no |
| **Owner bucket** | `sealed-gate` |
| **Selection owner** | `game.final_emission_visibility_fallback` |
| **Content owner** | `game.final_emission_sealed_fallback` |
| **Lineage kind** | `referential_clarity_hard_replacement` |
| **Final route** | `replaced` |
| **Entry replay fingerprint** | `743402c14d150f29253c` |
| **Exit replay fingerprint** | `1916c4f5a1d168c6fbc3` |
| **Measurement provenance** | `bv3d_positive_control_from_test_bv3a` |

---

## Shape taxonomy alignment

| Taxonomy | Classification |
|---|---|
| BV3A shape group | `ambiguous_speaker` |
| BV3E candidate | **EC-M01** — isolated dialogue `he` + multi-person, no interlocutor |
| BV3E decision | **Reject** — preserve hard replace |
| BV4B-RC track | Deferred medium-risk expansion |

---

## Corpus split

| Sub-corpus | RC hard replacement events |
|---|---:|
| Replay (`data/`, `artifacts/scene_canon_hygiene_runtime/`, `artifacts/scenario_spine_validation/`) | **0** |
| Measurement fixtures (`artifacts/bv3d_measurement/`) | **1** |
| **Total BV3D scope** | **1** |

---

## Related positive control (contrast)

| Field | `bv3a_positive_control_interlocutor_he_says` (line 1) |
|---|---|
| Triggering text | `"Keep your wits about you," he says, glancing toward the checkpoint.` |
| Grounding | `social.npc_id=tavern_runner`, `active_interlocutor_id=tavern_runner` |
| Outcome | upstream repair applied → `accept_candidate` (no hard replace) |

The negative control exists specifically to prove the symmetric ungrounded multi-person path still hard-replaces.

---

## Evidence

| Source | Role |
|---|---|
| `artifacts/bv3a_referential_clarity_metrics.json` | Current count = 1 |
| `artifacts/bv3d_measurement/positive_control_fixtures.jsonl` | Frozen FEM for OBS-M002 |
| `artifacts/bv3d_measurement/positive_control_manifest.json` | Fixture manifest |
| `docs/audits/BV3D_eligibility_inventory.md` | OBS-M001 / OBS-M002 rows |
| `tools/bv3d_build_positive_control_corpus.py` | Fixture materialization source |
