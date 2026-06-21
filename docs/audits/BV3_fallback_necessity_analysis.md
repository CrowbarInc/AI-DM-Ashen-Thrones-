# BV3 — Observe-Route Fallback Necessity Analysis

**Date:** 2026-06-21  
**Question:** For each observe-route fallback path, is it required runtime protection, legacy compatibility, dead defensive code, or ownership ambiguity?  
**Corpus:** 42 observe fallback turns; baseline observe route rate 95.45%.

---

## Classification legend

| Class | Meaning |
|---|---|
| **A. Required runtime protection** | Fallback prevents shipping player-facing text that violates a enforced contract |
| **B. Legacy compatibility path** | Preserves behavior for older FEM shapes, gate labels, or tuple adapters |
| **C. Dead defensive path** | Reachable in code but **zero** observe-corpus incidence; may still fire on other routes |
| **D. Ownership ambiguity path** | Behavior necessary or not, but routing/metadata obscures true owner or duplicates hubs |

---

## Route-by-route analysis

### OR-RC-01 — Referential clarity hard replacement

| Dimension | Assessment |
|---|---|
| **Necessity class** | **A. Required runtime protection** (today) |
| **Rationale** | Without hard replace, 39/42 observe fallback turns would ship GM text failing `validate_player_facing_referential_clarity` with `ambiguous_entity_reference`. Gate contract explicitly hard-replaces via `assert_final_emission_mutation_allowed("hard_replace_illegal_output_with_sealed_fallback")`. |
| **Elimination potential** | **High** — not because the validator is wrong, but because **upstream generation can satisfy referential clarity before the gate**, converting protection into a rare safety net rather than a 86%-of-route default. |
| **Ownership note** | Selection owner correctly stamped post-BK; 8/38 events missing owner bucket → partial **D** |

### OR-PSP-01 — Sealed passive scene pressure (gate-labeled)

| Dimension | Assessment |
|---|---|
| **Necessity class** | **A** (content) + **D** (selection label) |
| **Rationale** | Passive-scene pressure fallback is legitimate sealed content when scene pressure warrants reinspection prose. Gate selection owner on 1 event is legacy lineage packaging — implementation is visibility/sealed modules. |
| **Elimination potential** | **Low** for content; **Medium** for relabeling gate → visibility selection owner in projection only |

### OR-RTP-01 — Response-type prepared emission

| Dimension | Assessment |
|---|---|
| **Necessity class** | **B. Legacy compatibility** + **D. Ownership ambiguity** |
| **Rationale** | 2/3 turns are `accept_candidate`, not hard replace — lineage still emits `fallback_selected` with kind `response_type_prepared_emission`. Missing selection/content owners (3/3) matches BV1B global ownerless bucket gap. |
| **Elimination potential** | **Medium** — distinguish prepared-emission **accept** from fallback **replace** in lineage projection; stamp owners from `final_emission_response_type` registry |

### OR-VIS-01 — Visibility hard replacement

| Dimension | Assessment |
|---|---|
| **Necessity class** | **A** (general) / **C** (on observe route) |
| **Rationale** | Required on other routes when visibility validation fails. On observe corpus: **0 hits** — visibility passes; referential clarity fails instead. |
| **Elimination potential** | **None on observe** — path is not contributing to 95.45% rate |

### OR-FM-01 — First-mention hard replacement

| Dimension | Assessment |
|---|---|
| **Necessity class** | **A** (general) / **C** (on observe route) |
| **Rationale** | First-mention enforcement runs in chain but **never hard-replaces** on observe corpus (`first_mention_replacement_applied=False` on all 42). |
| **Elimination potential** | **None on observe** for incidence; chain ordering could be optimized later |

### OR-RC-LOCAL — Referential clarity local substitution

| Dimension | Assessment |
|---|---|
| **Necessity class** | **A. Required runtime protection** (avoidance mechanism) |
| **Rationale** | Proven pattern to **avoid** fallback on strict-social dialogue turns. Observe turns do not enter this branch (non-strict). |
| **Elimination potential** | **Expand** — generalizing safe local repair to non-strict observe turns is a primary reduction lever (see elimination candidates) |

---

## Visibility candidate branches (content layer)

Evaluated when any hard-replace path calls `standard_visibility_safe_fallback`.

| Candidate path | Necessity | Observe corpus | Notes |
|---|---|---:|---|
| Passive scene pressure | **A** | 40 wins | Correct reinspection content when GM observe text fails clarity |
| Global scene / scene-emit integrity | **A** | 0 | Fallback-of-fallback when passive pressure unavailable |
| Anti-reset local continuation | **A** | 0 | Continuity protection when intro suppressed |
| NPC pursuit neutral | **A** | 0 | Exploration non-progress branch |
| Social active interlocutor | **A** | 0 | Social-mode observe variant |
| Opening visibility mode | **B** | 0 | Opening-mode guard; inactive on observe |
| Strict-social minimal | **A** | 0 | Strict path only |

**Concentration finding:** On observe, sealed passive-scene content is **necessary** as the terminal safety net, but **unnecessary as the default outcome for 90%+ of turns** if upstream text were referentially clear.

---

## Enforcement chain necessity (terminal pipeline)

```
apply_visibility_enforcement
  → (pass visibility) apply_first_mention_enforcement
    → (pass first mention) apply_referential_clarity_enforcement
      → (fail clarity) standard_visibility_safe_fallback → hard replace
```

| Stage | Observe: passes | Observe: hard replace | Class |
|---|---:|---:|---|
| Visibility | 42/42 | 0 | **C** hard-replace branch on observe |
| First mention | 42/42 | 0 | **C** hard-replace branch on observe |
| Referential clarity | 3/42 | 39/42 | **A** — sole active hard-replace trigger |

The three referential-clarity events without `referential_clarity_replacement_applied=True` align with OR-RTP-01 / OR-PSP-01 lineage kinds, not the main RC hard-replace path.

---

## Ownership / packaging paths (cross-cutting)

| Path element | Class | Impact on incidence |
|---|---|---|
| Lineage `event_owner=game.final_emission_gate` (74/74 events) | **B + D** | Zero runtime; inflates gate hub metrics |
| Split selection/content owners (BK) | **B** (migration artifact) | Improved legibility; incidence unchanged |
| Missing owner bucket (12/42 observe) | **D** | Measurement/governance gap; 13 repo-wide (BV1B) |
| Missing `realization_fallback_family` (41/42 observe) | **D** | Provenance stamp gap on referential-clarity → sealed path |
| `visibility_fallback_kind` absent when RC fires | **D** | FEM shape does not reflect actual selection kind |

---

## Summary matrix

| Route / path | A | B | C | D | Observe frequency |
|---|---:|---:|---:|---:|---:|
| OR-RC-01 referential clarity hard replace | ✓ | | | partial | 38 |
| OR-PSP-01 sealed passive (gate label) | ✓ | | | ✓ | 1 |
| OR-RTP-01 response-type prepared emission | | ✓ | | ✓ | 3 |
| OR-VIS-01 visibility hard replace | | | ✓ | | 0 |
| OR-FM-01 first-mention hard replace | | | ✓ | | 0 |
| OR-RC-LOCAL local substitution | ✓ | | | | 0 (avoidance) |

---

## Strategic conclusion

- **Cannot** eliminate observe fallback by relocation or ownership renaming alone — BV1B proved this.
- **Can** reduce incidence by shifting OR-RC-01 from **default outcome** to **rare safety net** via upstream referential-clarity contracts and expanded local repair.
- **Should** close **D-class** gaps (owner bucket, lineage gate label, prepared-emission classification) in parallel — behavior-neutral, improves reduction measurement fidelity.

---

## Evidence

| Source | Role |
|---|---|
| [BV3_observe_route_inventory.md](BV3_observe_route_inventory.md) | Route catalog |
| [BV1B_fallback_migration_analysis.md](BV1B_fallback_migration_analysis.md) | Relocation without removal |
| `game/final_emission_visibility_fallback.py` | Enforcement chain |
| Corpus FEM fields | `referential_clarity_*`, `visibility_*`, `first_mention_*` distributions |
