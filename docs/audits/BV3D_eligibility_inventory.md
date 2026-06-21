# BV3D — Eligibility Inventory

**Date:** 2026-06-21  
**Corpus:** BV3D-filtered measurement scope (97 FEM / 23 observe).  
**Machine-readable:** `artifacts/bv3d_eligibility_report.json`

---

## Summary

| Metric | Value |
|---|---:|
| Observe turns | 23 |
| Upstream attempted | 13 |
| Upstream eligible | **1** |
| Upstream applied | **1** |
| Eligible observe coverage (`applied / eligible`) | **100%** |
| Replay-only eligible (excl. fixtures) | **0** |

---

## Per-turn inventory

### Measurement fixtures

| turn id | fixture | violation count | ambiguity | interlocutor | social NPC | validator | BV3A eligibility | applied |
|---|---|---:|---|---|---|---|---|---|
| OBS-M001 | `bv3a_positive_control_interlocutor_he_says` | 0 (post-repair) | — | yes | yes | pass | **applied** | **yes** |
| OBS-M002 | `bv3a_negative_control_multi_person_hard_replace` | 1 | `ambiguous_entity_reference` / `he` | no | no | fail | attempted_ineligible | no |

### Canonical replay

| turn id | source | violation count | ambiguity | interlocutor | social NPC | validator | BV3A eligibility | applied |
|---|---|---:|---|---|---|---|---|---|
| OBS-M023 | `data/session_log.jsonl` | 1 | `referent_drift` / `they` | no | no | fail | attempted_ineligible | no |

### Refreshed replay (20 observe turns — representative groups)

| Group | Turns | violation count | ambiguity | interlocutor | social NPC | validator | BV3A eligibility |
|---|---|---:|---|---|---|---|---|
| Multi-violation guard/his/he | 10 | 3 | `guard`, `his`, `he` | no | no | fail | attempted_ineligible |
| Validation pass (named anchors) | 10 | 0 | — | no | no | pass | validation_passed_no_attempt |

Full per-turn rows: `observe_turns[]` in `artifacts/bv3d_eligibility_report.json` (OBS-M003 … OBS-M022).

---

## Field definitions

| Field | Source |
|---|---|
| **violation count** | `referential_clarity_unrepaired_violation_count` or violation kind list length |
| **ambiguity type** | Primary `referential_clarity_violation_sample[0].kind` |
| **interlocutor present** | `active_interlocutor_id` or `active_interlocutor` in FEM |
| **social NPC present** | `resolution.social.npc_id` or `npc_id` in FEM |
| **validator result** | `referential_clarity_validation_passed` |
| **BV3A eligibility result** | Derived from upstream attempted/eligible/applied flags |

---

## Eligibility outcome distribution

| BV3A eligibility result | Turns |
|---|---:|
| applied | 1 |
| attempted_ineligible | 12 |
| validation_passed_no_attempt | 10 |

| Contract shape (retrospective) | Turns |
|---|---:|
| contract_pass | 11 |
| contract_ineligible_token | 10 |
| contract_ineligible_multi_entity | 1 |
| contract_ineligible_kind | 1 |

---

## Coverage interpretation

- **Eligible Observe-Turn Coverage** (primary BV3D metric): **1.0** on eligible set (1 applied / 1 eligible).
- **Replay-only refreshed corpus**: 0 eligible shapes without measurement fixtures — confirms BV3C eligibility drift finding on live replay text.
- **Measurement validity**: restored by combining filtered replay + positive-control fixture.
