# BV3C — Fixture vs Replay Analysis

**Date:** 2026-06-21  
**Compares:** `tests/test_bv3a_observe_referential_clarity_repair.py` fixtures vs post-BV3B replay corpus (`artifacts/bv3c_observe_eligibility.json`).

---

## Side-by-side assumptions

| Dimension | Unit-test fixture | Replay corpus (observe) |
|---|---|---|
| **Candidate text** | Single-sentence dialogue attribution: `"…," he says` **without** prior named anchor in same sentence | Named anchor common (`a nearby guard`, `A gate serjeant`); or multi-sentence retry bundles |
| **Violation count** | Exactly **1** | **0** (pass), **1** (`referent_drift`), or **3** (guard/his/he) |
| **Violation kind** | `ambiguous_entity_reference` only | Mostly `ambiguous_entity_reference`; refreshed session_log includes `referent_drift` |
| **Pronoun token** | `he` (dialogue tag) | `he`, `his`, `guard` (alias collision), `they` |
| **Visible persons** | 4+ frontier_gate actors | 4–6 (includes gate_guard, gate_serjeant) |
| **Interlocutor** | `tavern_runner` via `set_social_target` | **null** on all 65 scanned observe turns |
| **resolution.social.npc_id** | Present in positive test | **null** on observe replay turns |
| **strict_social_active** | false | false |
| **Gate entry helper** | `apply_final_emission_gate_consumer` (full finalize) | Live `/api/chat` + retry/prepared-emission stack |
| **Layer stack** | Minimal — direct gate on candidate | Full non-strict stack, passive-scene pressure, retry escalation |
| **FEM age** | Current BV3A code | 68% pre-BV3A archived snapshots still in scan roots |

---

## Test cases mapped to corpus

| Test | Fixture intent | Corpus analogue | Match? |
|---|---|---|---|
| `test_observe_dialogue_he_says_repairs_via_upstream_not_hard_fallback` | Eligible repair with interlocutor | **None** | **No** |
| `test_observe_ambiguous_speaker_without_interlocutor_still_hard_replaces` | Multi-person hard replace | OBS-001…030 archive shapes | **Partial** (shape match, stale FEM) |
| `test_observe_single_visible_person_dialogue_he_says_repairs_without_social_target` | Single-person exception | **None** (all observe turns ≥4 visible persons) | **No** |

---

## Assumptions in tests **absent** in replay

1. **Social grounding present** — positive test sets interlocutor + `resolution.social.npc_id`; replay observe turns never carry social target.  
2. **Isolated single violation** — replay gate candidates often fail with 3 violations or pass entirely.  
3. **Synthetic minimal candidate** — replay text is prepared/retry emission, not raw `"he says"` stub.  
4. **Named-anchor-free dialogue** — replay `"nearby guard … he says"` passes standalone validator (`ok=True`); BV3B refresh stub `"a guard shifts his weight… he says"` also passes — **upstream never attempts**.  
5. **Homogeneous FEM provenance** — tests finalize once; replay logs nested `emission_debug_lane` FEM from retry iterations.  
6. **Corpus free of pre-BV3A artifacts** — metrics scan still indexes archived hygiene tree copied to `artifacts/bv3b_replay_refresh/`.

---

## Assumptions in replay **absent** in tests

1. **Retry exhaustion** — `retry_escape_hatch`, `forced_retry_fallback`, multi-attempt candidates.  
2. **`referent_drift` with plural `they`** and multi-entity candidates (gate_guard vs gate_serjeant).  
3. **Alias collision token `guard`** across gate_guard / guard_captain with 6 visible entities.  
4. **Passive-scene / prepared-emission** accept path text with explicit entity introductions.  
5. **Expanded entity roster** (gate_guard, gate_serjeant) vs default_scene-only tests.

---

## BV3B refresh expectation gap

| BV3B manifest claim | Reality (BV3C) |
|---|---|
| Stub returns `"Keep moving," he says` | Refresh runs stub, but **canonical session_log** observe turn is **retry/prepared** guard dialogue |
| “Including BV3A upstream repair hooks” | Hooks execute; **0 eligible shapes** in emitted candidates |
| Projected `-8 to -15` referential_clarity_hard_replacement delta | Requires grounding + single-violation shapes **not present** in corpus |

---

## Why tests pass but replay shows 0%

```
Unit test profile:     1 violation + he + interlocutor → eligible → applied=true
Replay profile:        0 violations OR 3 violations OR referent_drift OR stale FEM
Intersection:          ∅
```

Tests prove **code correctness** on the contract slice. Replay proves **corpus/eligibility mismatch** — not a failing code path on observed shapes.

---

## Recommendations for future verification (analysis-only; no code changes here)

1. Add replay fixtures that mirror positive test (interlocutor + single `he` violation) if measuring activation rate is a release gate.  
2. Restrict incidence scan to **top-level post-finalize FEM** and exclude `artifacts/bv3b_replay_refresh/**` archive paths.  
3. Align BV3B refresh stub with **validator-failing** shape (no named guard anchor) if refresh is meant to stress BV3A.
