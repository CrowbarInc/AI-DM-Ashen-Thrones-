# BV3C — Observe-Turn Eligibility Audit

**Date:** 2026-06-21  
**Corpus:** 65 deduped `route_kind=observe` FEM instances from canonical replay scan (200 total FEM, post-BV3B refresh).  
**Extract:** `artifacts/bv3c_observe_eligibility.json` (machine-readable companion).

---

## Executive summary

| Bucket | Turns | Share |
|---|---:|---:|
| **Expected BV3A-eligible** (single `ambiguous_entity_reference`, pronoun token, grounding available) | **0** | 0% |
| Expected ineligible (multi-person, wrong token/kind, multi-violation) | 54 | 83% |
| Stale / no upstream instrumentation | 44 | 68% |
| Refreshed turns reaching upstream with violations | 11 | 17% |

No observe turn in the refreshed replay corpus matches the **unit-test eligibility profile** (lone dialogue-attribution `he` + interlocutor + exactly one violation).

---

## BV3A eligibility rules (reference)

From `docs/audits/BV3A_referential_clarity_contract.md`:

1. `res_kind=observe`, not strict-social  
2. Exactly **one** `ambiguous_entity_reference` violation  
3. Pronoun token in `{he, she, him, her, they, them}`  
4. Grounding: interlocutor, `resolution.social.npc_id`, sole visible person, or dialogue-attribution exception  
5. Re-validation passes after substitution  

---

## Candidate records (representative)

### Stale pre-BV3A archive — OBS-001 pattern

| Field | Value |
|---|---|
| **turn id** | OBS-001 (representative of 44 turns) |
| **artifact** | `artifacts/bv3b_replay_refresh/scene_canon_hygiene_runtime.2026-06-21T123437...` (pre-refresh archive) |
| **ambiguity type** | `ambiguous_entity_reference` |
| **ambiguity token** | `he` |
| **visible entities** | emergent_town_crier, guard_captain, refugee, tavern_runner, threadbare_watcher (5) |
| **interlocutor** | null |
| **social NPC** | null |
| **upstream fields** | all null |
| **expected repair eligibility** | ineligible_multi_person_no_grounding |
| **actual outcome** | hard replace (pre-BV3A FEM) |

### Pre-BV3A corpus shape (still in archive) — matches BV3A inventory

| Field | Value |
|---|---|
| **ambiguity type** | `ambiguous_entity_reference` |
| **token** | `he` |
| **sentence shape** | Quoted dialogue + `"…," he says` without named antecedent |
| **visible persons** | 4–5 |
| **interlocutor / social** | absent |
| **expected** | ineligible per contract (multi-person, no grounding) |
| **BV3A design intent** | preserve hard replace |

These turns **would not** activate upstream repair even under BV3A; they were counted in BV3A projections as conservative `-8 to -15` targets only when grounding exists.

### Refreshed hygiene batch — OBS-045 pattern (11 upstream-attempted turns)

| Field | Value |
|---|---|
| **turn id** | OBS-045 (representative of 10 multi-violation + 1 referent_drift) |
| **artifact** | `artifacts/scene_canon_hygiene_runtime/*/data/session_log.jsonl` (post-refresh) |
| **gate candidate preview** | `The pause snaps when a nearby guard points with his spear-butt… "Board, runner, or road," he says.` |
| **ambiguity type (final FEM sample)** | `ambiguous_entity_reference` (primary token often `guard`, not `he`) |
| **visible entities** | gate_guard, gate_serjeant, guard_captain, refugee, tavern_runner, threadbare_watcher (6) |
| **interlocutor** | null |
| **social NPC** | null |
| **upstream_attempted** | true |
| **upstream_eligible** | false |
| **unrepaired_count** | 3 |
| **expected repair eligibility** | **ineligible** — multi-violation (`len(ambiguous) != 1`) and/or non-pronoun token |
| **actual outcome** | hard replace |

**Note:** Standalone validation of the preview text with `seed_frontier_gate_world` returns `ok=True` (named “nearby guard” anchors pronouns). Upstream `unrepaired_count=3` indicates the **text validated at terminal pipeline entry** differed (retry/pre-layer candidate) or carried extra violations (alias collision on `guard` across gate_guard/guard_captain).

### Canonical session_log observe — referent_drift

| Field | Value |
|---|---|
| **turn id** | OBS-065 (`data/session_log.jsonl` line 1) |
| **ambiguity type** | `referent_drift` |
| **token** | `they` |
| **candidate_entity_ids** | gate_guard, gate_serjeant |
| **visible entities** | 6 person-like |
| **interlocutor / social** | null |
| **upstream_attempted** | true |
| **upstream_eligible** | false |
| **expected** | ineligible_out_of_scope_kind (BV3A only targets `ambiguous_entity_reference`) |
| **actual** | `referential_clarity_replacement_applied=true`, `final_route=replaced` |

Violation sample references `"…they say"` — a sentence **not present** in finalized `player_facing_text`, indicating FEM captured an **intermediate retry candidate** while emitted text came from a later pass.

### Refreshed pass-through — OBS-047 pattern (10 turns)

| Field | Value |
|---|---|
| **ambiguity type** | null (validation passed) |
| **preview** | `As you watch the scene, threadbare watchers and refugees cluster… A gate serjeant manages…` |
| **upstream_attempted** | false |
| **replacement_applied** | false |
| **final_route** | accept_candidate |
| **expected** | N/A — no referential violation at enforcement |
| **failure class** | A_bypass_validation_passed |

---

## Eligibility summary table

| Expected eligibility label | Turns | Upstream attempted | Upstream applied |
|---|---:|---:|---:|
| ineligible_multi_person_no_grounding | 30 | 0 | 0 |
| ineligible_token (`his`, `guard`, etc.) | 19 | 10 | 0 |
| ineligible_out_of_scope_kind (`referent_drift`, etc.) | 16 | 1 | 0 |
| eligible_if_single_violation | **0** | 0 | 0 |

---

## Turns that would qualify under BV3A contract but corpus lacks

Synthetic profile from `tests/test_bv3a_observe_referential_clarity_repair.py`:

| Field | Fixture value |
|---|---|
| Candidate | `"Keep your wits about you," he says, glancing toward the checkpoint.` |
| route_kind | observe |
| interlocutor | tavern_runner (via `set_social_target`) |
| social NPC | tavern_runner |
| violations | 1 × `ambiguous_entity_reference`, token `he` |
| **expected eligibility** | **eligible** |
| **observed in replay corpus** | **none** |

---

## Audit implication

The replay corpus **does not contain** observe turns matching BV3A's intended activation profile. Eligibility audit explains **0% repair activation** without invoking instrumentation failure or pipeline bypass on refreshed turns.
