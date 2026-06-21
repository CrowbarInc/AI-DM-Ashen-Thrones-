# BV6 — Residual Referential-Clarity Causal Trace

**Date:** 2026-06-21  
**Event:** OBS-M002 / `bv3a_negative_control_multi_person_hard_replace`  
**Input text:** `Guard Captain and Tavern Runner stand near the gate. "Back away," he says.`

---

## Path overview

```
observe resolution (no social target)
  → final_emission_gate entry (candidate text)
  → apply_observe_referential_clarity_upstream_repair
      → validate_player_facing_referential_clarity → FAIL (1 violation)
      → eligibility check → INELIGIBLE
      → repair attempt → SKIPPED (no eligible path)
  → apply_visibility_enforcement / apply_referential_clarity_enforcement
      → re-validate → FAIL
      → local substitution attempt → INELIGIBLE (multi-entity guard)
      → standard_visibility_safe_fallback (enforce_referential_clarity=True)
      → hard replacement text emitted
  → final_route=replaced, lineage referential_clarity_hard_replacement
```

---

## Stage 1 — Input

| Field | Value |
|---|---|
| Resolution kind | `observe` |
| Prompt | `I look around.` |
| Social block | absent |
| Active interlocutor | none |
| Session/scene | `frontier_gate` with 4 visible person-like entities |
| Candidate text | Both named NPCs in scene + unattributed dialogue tag |

---

## Stage 2 — Validator

**Module:** `game.final_emission_referential_clarity.validate_player_facing_referential_clarity`

| Result | Value |
|---|---|
| `ok` | `false` |
| Violation count | 1 |
| Kind | `ambiguous_entity_reference` |
| Token | `he` |
| Offset | 66 |
| `candidate_entity_ids` | `['guard_captain', 'tavern_runner']` |
| Dialogue attribution | **yes** (`_is_dialogue_attribution_he_she_violation` → true) |

Both named entities appear **before** the pronoun, so the validator correctly assigns a **2-entity candidate set** rather than empty candidates.

---

## Stage 3 — Upstream repair eligibility

**Module:** `apply_observe_referential_clarity_upstream_repair`  
**Function:** `_violations_eligible_for_non_strict_local_repair`

| Check | Result | Reason |
|---|---|---|
| Route gate (`observe`, non-strict-social) | pass | resolution kind = observe |
| BV3A single-violation pronoun repair | **fail** | multi-entity candidates (`len(cids) > 1`) |
| BV3E exact-alias introducer | **fail** | no singular indefinite introducer before token (`a guard`, `a runner`, etc.) |
| BV3E multi-violation dialogue speaker | **fail** | only 1 ambiguous violation (requires ≥2) |
| **Composite eligible** | **false** | |

**FEM stamps:**

| Field | Value |
|---|---|
| `referential_clarity_upstream_repair_attempted` | `true` |
| `referential_clarity_upstream_repair_eligible` | `false` |
| `referential_clarity_upstream_repair_applied` | `false` |
| `referential_clarity_unrepaired_violation_count` | `1` |

---

## Stage 4 — Upstream repair attempt

**Module:** `_try_non_strict_local_pronoun_substitution_repair`

Because composite eligibility is false, the function returns `(None, dbg)` immediately after BV3E alias path fails — **no token substitution attempted**.

**Grounding resolution trace** (`_resolve_grounded_person_entity_for_referential_repair`):

| Step | Result |
|---|---|
| Single candidate shortcut | fail — 2 candidates |
| Social NPC from resolution | fail — no social block |
| Active interlocutor | fail — empty |
| Single visible person | fail — 4 visible |
| Contextual speaker (dialogue attribution) | **fail — returns None** (multi-person without grounding) |

Multi-person guard at line 865–866 in `final_emission_referential_clarity.py`:

```python
if len(person_ids) > 1 and not contextual_grounding:
    return None, dbg
```

---

## Stage 5 — Terminal enforcement / repair rejection

**Module:** `game.final_emission_visibility_fallback.apply_referential_clarity_enforcement`

| Step | Outcome |
|---|---|
| Re-validation | fail (same violation) |
| Preserved upstream repair meta | restored (attempted=true, eligible=false) |
| Non-strict local repair retry | ineligible (same guards) |
| Multi-entity candidate bypass (`they` dialogue-only) | not applicable — token is `he` |
| **Hard replace branch** | **entered** |

**FEM stamps at terminal:**

| Field | Value |
|---|---|
| `referential_clarity_local_substitution_attempted` | `false` |
| `referential_clarity_local_substitution_applied` | `false` |
| `referential_clarity_replacement_applied` | `true` |
| `referential_clarity_validation_passed` | `false` |
| `producer_repair_kind` | `referential_clarity_enforcement` |
| `final_emitted_source` | `global_scene_fallback` |

---

## Stage 6 — Hard replacement

**Module:** `standard_visibility_safe_fallback` → sealed global scene fallback

| Field | Value |
|---|---|
| `final_route` | `replaced` |
| Output preview | Passive-scene pressure fallback text (284 chars) |
| Tags | `final_emission_gate_replaced`, `referential_clarity_enforcement_replaced`, `referential_clarity_violation:ambiguous_entity_reference` |
| Lineage `fallback_kind` | `referential_clarity_hard_replacement` |
| Lineage `stage` | `gate` |
| Lineage `owner` | `game.final_emission_gate` |
| `fallback_selection_owner` | `game.final_emission_visibility_fallback` |
| `fallback_content_owner` | `game.final_emission_sealed_fallback` |

**Stage diff telemetry:**

| Stage | Fingerprint | Preview |
|---|---|---|
| gate_entry | `743402c14d150f29253c` | `Guard Captain and Tavern Runner stand near the gate. "Back away," he says.` |
| gate_exit | `1916c4f5a1d168c6fbc3` | Replaced passive-scene text |

---

## Why BV3E/BV4B did not clear this event

| Prior cycle | Effect on OBS-M002 |
|---|---|
| **BV3E** | Cleared MV-01 exact-alias introducer cluster (11 replay turns); **EC-M01 explicitly rejected** |
| **BV4B** | Eliminated PSP fallbacks (10 → 0); RC negative control **unchanged by design** |
| **Replay refresh** | No live replay turn reproduces this shape with hard replace |

---

## Code path reference

| Stage | Module / function |
|---|---|
| Validation | `game.final_emission_referential_clarity.validate_player_facing_referential_clarity` |
| Upstream repair | `apply_observe_referential_clarity_upstream_repair` |
| Eligibility | `_violations_eligible_for_non_strict_local_repair` |
| Grounding | `_resolve_grounded_person_entity_for_referential_repair` |
| Terminal enforcement | `game.final_emission_visibility_fallback.apply_referential_clarity_enforcement` |
| Hard replace selection | `standard_visibility_safe_fallback` |
| Fixture source | `tools/bv3d_build_positive_control_corpus.py` |
