# BV8 — Speaker Failure Family Map

**Date:** 2026-06-21  
**Scope:** Classify all speaker-family recurrence rows by root-cause family.

---

## Classification key

| Cause family | Definition |
|---|---|
| **speaker adoption drift** | Post-emission adoption resolves a different canonical speaker than replay projection |
| **projection mismatch** | `project_turn_observation` resolves `selected_speaker_id` differently than test expectation (alias/canonical/trace priority) |
| **relocation mismatch** | Gate vs isolated speaker enforcement diverges (Block T shadow equivalence) |
| **finalize divergence** | Post-speaker stack layers mutate text/identity before finalize (Block U probes) |
| **ownership ambiguity** | Recurrence owner/investigate_first misattributes seam (golden_replay vs golden_replay_projection) |
| **replay mismatch** | Golden rerun drift on `selected_speaker_id` or `final_text_hash` across runs |
| **other** | Instrumentation, dedupe, or non-speaker-causal noise |

---

## Row-level classification

| Recurrence key | Events | Scenario | Primary cause | Secondary cause | Confidence |
|---|---:|---|---|---|---|
| `speaker_drift\|projection\|selected_speaker_id\|golden_replay.py` | 8 | vocative_override | **projection mismatch** | ownership ambiguity; instrumentation duplicate inflation | **High** |
| `speaker_drift\|speaker\|selected_speaker_id\|speaker_contract_enforcement.py` | 1 | wrong_speaker | **finalize divergence** (enforcement repair) | replay mismatch | **Medium** |

---

## Cause family rollup

| Cause family | Event rows | Share of speaker events | Recurrence keys | Live test status |
|---|---:|---:|---:|---|
| **projection mismatch** | 8 | **88.9%** | 1 | **Green** (vocative test passes) |
| **ownership ambiguity** | 8* | (embedded) | 1 | Classification points to `golden_replay.py`; resolution lives in `golden_replay_projection.py` |
| **instrumentation duplicate inflation** | 7 | **77.8%** | 0 | Duplicates of single 2026-06-04 failure |
| **finalize divergence** | 1 | 11.1% | 1 | wrong_speaker test — enforcement owner path |
| speaker adoption drift | 0 | 0% | 0 | No recurrence rows |
| relocation mismatch | 0 | 0% | 0 | No recurrence rows |
| replay mismatch | 0† | 0% | 0 | Rerun drift not in protected event log |

\*Same rows as projection mismatch — dual classification.  
†Emerging wrong_speaker row may include replay observation mismatch; not yet recurring.

---

## Projection mismatch — detail (dominant family)

**Observed failure (2026-06-04):**

```text
Expected selected_speaker_id: guard
Actual selected_speaker_id:   guard_captain
Drift type:                   structural_drift
Category:                     projection
Investigate first:            tests/helpers/golden_replay.py
```

**Mechanism:**

`_resolve_selected_speaker_id` in `golden_replay_projection.py` resolves from:

1. `turn_trace.social_contract_trace` (`final_reply_owner`, `reply_owner_actor_id`, `visible_grounded_speaker`)
2. `latest_target_id(snap)` fallback
3. `resolution.social.npc_id` fallback

It does **not** parse finalized emitted prose via `detect_emitted_speaker_signature`. The test expectation uses short roster alias **`guard`**; projection emitted canonical NPC id **`guard_captain`**.

**Why this is projection mismatch, not speaker finalize bug:**

- Runtime lineage on failure run: **0 speaker repair events**
- Final source: `anti_reset_local_continuation_fallback` (continuation fallback path, not speaker repair)
- Vocative routing behavior may be correct while **observation field** uses inconsistent ID vocabulary

---

## Finalize divergence — detail (emerging family)

**Observed failure (2026-06-20 backfill):**

| Field | Value |
|---|---|
| Scenario | `wrong_speaker_strict_social_emission` |
| Owner | `game/speaker_contract_enforcement.py` |
| Category | `speaker` (not `projection`) |
| Invariant | Strict-social enforcement must reject/suppress wrong merchant attribution |

This is a **legitimate enforcement-owner** recurrence key — distinct from projection alias mismatch. Single observation; not yet recurring.

---

## Families with zero recurrence rows (latent risk)

| Family | Why it matters | BT evidence |
|---|---|---|
| **speaker adoption drift** | Adoption uses `detect_emitted_speaker_signature` + canonical roster; projection uses trace chain — intentional split per BT | Different resolution paths can diverge without recurrence instrumentation |
| **relocation mismatch** | Block T proves gate/isolated parity on normalized text | No protected replay recurrence capture |
| **finalize divergence** | Block U locates first post-speaker text change | Probes lack speaker identity at checkpoint |
| **replay mismatch** | Rerun scorecard tracks speaker delta count | Session writes excluded from committed log (BQ3.6) |

---

## Verdict

| Question | Answer |
|---|---|
| Dominant cause? | **Projection mismatch** (alias vs canonical ID on `selected_speaker_id`) |
| Multiple unrelated incidents? | **No** — 8/8 projection rows are the **same incident** duplicated |
| Separate emerging cause? | **Yes** — 1 wrong_speaker enforcement row (finalize/enforcement family) |
| Repeated live repair cycle? | **No** — underlying vocative test is green; recurrence is **stale + inflated** |

---

## Evidence

| Source | Role |
|---|---|
| [BV8_recurrence_inventory.md](BV8_recurrence_inventory.md) | Row inventory |
| `tests/helpers/golden_replay_projection.py` | `_resolve_selected_speaker_id` |
| `tests/test_golden_replay_structural_invariants.py` | Expectation `guard` |
| [BT_speaker_finalization_divergence_discovery.md](BT_speaker_finalization_divergence_discovery.md) | Checkpoint gap model |
