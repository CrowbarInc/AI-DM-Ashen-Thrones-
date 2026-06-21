# BV3A — Observe-Route Referential Clarity Contract

**Date:** 2026-06-21  
**Scope:** Explicit referential-clarity contract for **`route_kind=observe`** turns entering terminal enforcement.  
**Goal:** Satisfy clarity at the source via local repair; reserve hard replace for unrecoverable violations.

---

## Contract overview

Observe-route player-facing text MUST satisfy `validate_player_facing_referential_clarity` before referential-clarity hard replacement. BV3A adds an **upstream repair layer** and **non-strict local substitution** path that restores clarity without sealed fallback when contract requirements can be met from grounded scene context.

---

## Minimum actor identity requirements

| Requirement | Rule |
|---|---|
| **Dialogue speech tags** | Pronouns in attribution tags (`he says`, `she insisted`, …) MUST refer to a **grounded person entity** |
| **Grounding sources (priority order)** | 1) Single `candidate_entity_id` on violation 2) `resolution.social.npc_id` when visible 3) `active_interlocutor` when visible 4) Sole person-like visible entity |
| **Visible person-like kinds** | `npc`, `scene_actor`, `creature`, `humanoid`, `person` |
| **Named anchor alternative** | Explicit entity name or unique descriptor reanchor in same sentence (existing validator pass path — unchanged) |

---

## Minimum target requirements

| Requirement | Rule |
|---|---|
| **Multi-person scenes** | When **>1** person-like entity is visible, speech-tag repair requires **contextual grounding** (interlocutor or social NPC) — not majority-vote guessing |
| **Single-person scenes** | Sole visible person-like entity may ground speech-tag pronouns without active interlocutor |
| **Non-dialogue pronouns** | Narrative pronouns (`He steps forward` across sentences) require **single visible person** OR explicit candidate — no interlocutor-only grounding |

---

## Acceptable ambiguity thresholds

| Condition | Threshold | Outcome |
|---|---|---|
| Violation count | Exactly **1** `ambiguous_entity_reference` | Repair may be attempted |
| Multi-entity candidates on violation | **0 or 1** entity id | Repair may be attempted |
| Pronoun token | `he`, `she`, `him`, `her`, `they`, `them` | In substitution set |
| Dialogue attribution shape | Speech-tag regex match OR comma-quote-pronoun-verb pattern | Allows interlocutor grounding with multiple visible persons |
| Player-coref safe harbor | Validator safe harbor applies | No repair; pass through (unchanged) |
| Dialogue attribution `they` only | `_referential_clarity_violations_only_dialogue_attribution_they` | Pass without replace (unchanged) |

---

## Repair eligibility rules

### Upstream repair (before visibility enforcement)

**Entry:** `apply_observe_referential_clarity_upstream_repair` in terminal pipeline when `res_kind=observe` and not strict-social.

| Step | Rule |
|---|---|
| 1 | Run `validate_player_facing_referential_clarity` on gate candidate |
| 2 | If `ok`, exit (no-op) |
| 3 | If eligible per non-strict local repair rules, attempt substitution |
| 4 | Re-validate referential clarity, first mention, visibility on repaired text |
| 5 | On success: stamp upstream + local substitution meta; **do not** hard replace |
| 6 | On failure: leave text unchanged; downstream enforcement unchanged |

### Non-strict local repair (before hard replace)

**Entry:** `apply_referential_clarity_enforcement` when `strict_social_active=False`, after strict-social branch.

Same eligibility and re-validation rules as upstream path. Strict-social turns continue to use `_try_strict_social_local_pronoun_substitution_repair` unchanged.

### Hard replace (unchanged fallback)

**Trigger:** Repair ineligible OR repair attempted and re-validation fails.

**Behavior:** `standard_visibility_safe_fallback` → sealed passive-scene content — **unchanged**.

---

## Ineligible shapes (must remain hard replace)

| Shape | Reason |
|---|---|
| Multi-person scene + speech tag + **no** interlocutor/social NPC | Cannot identify speaker safely |
| `referent_drift` | Separate validator kind — not in BV3A scope |
| Possessive narrative (`his`/`their` in non-dialogue clauses) | No safe single-token substitution |
| Neuter/inanimate (`it`) without anchor | missing_actor_identity |
| Multiple violations on one turn | Ambiguity not isolated |
| Multi-entity `candidate_entity_ids` | True ambiguous target |

---

## Instrumentation contract (FEM)

| Field | Meaning |
|---|---|
| `referential_clarity_upstream_repair_attempted` | Upstream layer evaluated observe turn |
| `referential_clarity_upstream_repair_eligible` | Violation shape matched repair preconditions |
| `referential_clarity_upstream_repair_applied` | Upstream repair succeeded |
| `referential_clarity_upstream_repair_entity_id` | Grounded entity used |
| `referential_clarity_unrepaired_violation_count` | Violations remaining after upstream attempt |
| `referential_clarity_local_substitution_*` | Local repair attempt/outcome (shared with strict-social path) |
| `referential_clarity_repair_entity_id` | Entity id used for substitution |
| `referential_clarity_fallback_avoided` | True when local repair succeeded |

---

## Regression guards

| Guard | Enforcement |
|---|---|
| No narrative-quality regression | Re-validate referential clarity + first mention + visibility after repair |
| No speaker-finalize regression | Strict-social path unchanged; tests in `test_speaker_contract_enforcement.py` |
| No replay divergence | Repair meta preserved through visibility/first-mention/referential stages via snapshot restore |
| Multi-person ambiguous quote tag | Existing test `test_pipeline_referential_clarity_replaces_ambiguous_quoted_speaker_tag` still hard-replaces without grounding |

---

## Code references

| Function | Module |
|---|---|
| `apply_observe_referential_clarity_upstream_repair` | `game.final_emission_referential_clarity` |
| `_try_non_strict_local_pronoun_substitution_repair` | `game.final_emission_referential_clarity` |
| `_resolve_grounded_person_entity_for_referential_repair` | `game.final_emission_referential_clarity` |
| `_is_dialogue_attribution_he_she_violation` | `game.final_emission_referential_clarity` |
| `run_gate_terminal_enforcement_pipeline` | `game.final_emission_terminal_pipeline` |

---

## Related audits

| Document | Role |
|---|---|
| [BV3A_referential_clarity_inventory.md](BV3A_referential_clarity_inventory.md) | Violation shape data |
| [BV3_fallback_reduction_plan.md](BV3_fallback_reduction_plan.md) | Phase 2 EC-01/EC-02 plan |
| [BV3_observe_route_inventory.md](BV3_observe_route_inventory.md) | Route OR-RC-01 |
