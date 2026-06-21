# BV3C — Activation Failure Map

**Date:** 2026-06-21  
**Primary metric:** Repair Activation Rate = `upstream_repair_applied / observe_turns` = **0 / 65 = 0%**

Failure taxonomy: **A** never reached · **B** eligibility mismatch · **C** metadata mismatch · **D** pipeline ordering · **E** replay-only divergence · **F** other

---

## Summary

| Class | Turns | Share of observe corpus | Primary cause |
|---|---:|---:|---|
| **A** Never reached / stale FEM | 44 | 68% | Pre-BV3A archived hygiene snapshots in scan roots |
| **A′** Validation pass (no violation at upstream) | 10 | 15% | Named-entity anchors / clean prepared text |
| **B** Eligibility mismatch | 11 | 17% | Multi-violation, wrong kind, no grounding |
| **C** Metadata mismatch | 0 | 0% | — |
| **D** Pipeline ordering | 0 | 0% | Upstream runs before visibility (by design) |
| **E** Replay-only divergence | ≥1 | ≥2% | Retry/FEM snapshot vs emitted text |
| **F** Other | 0 | 0% | — |

**Dominant classification:** **B (eligibility mismatch)** on refreshed turns; **A (stale FEM)** inflates zero-instrumentation count across full scan.

---

## Per-class detail

### A — Never reached repair code (44 turns)

| Signal | Value |
|---|---|
| FEM fields | `referential_clarity_upstream_repair_*` all **null** |
| Source | `artifacts/bv3b_replay_refresh/scene_canon_hygiene_runtime.2026-06-21T123437...` (archived **pre-refresh** batches) |
| Code path | Finalized under pre-BV3A gate; upstream hook did not exist |
| Hard replace | Still present (`referential_clarity_replacement_applied=true`) |

**Not** a runtime bypass in current code — corpus contamination from archived snapshots still indexed by `DEFAULT_ROOTS`.

---

### A′ — Reached pipeline, validation passed at upstream (10 turns)

| Signal | Value |
|---|---|
| `upstream_repair_attempted` | false |
| `unrepaired_violation_count` | 0 |
| `final_route` | accept_candidate |
| Example | OBS-047 prepared scene narration with explicit entity names |

Upstream function exits at `validation.ok is True` without stamping `attempted=true`.

---

### B — Eligibility mismatch (11 turns with `attempted=true`, all `eligible=false`)

#### B1 — Multi-violation (10 turns)

| Signal | Value |
|---|---|
| `unrepaired_violation_count` | 3 |
| Sample tokens | `guard`, `his`, `he` |
| Rule blocked | `_violations_eligible_for_non_strict_local_pronoun_repair` requires exactly one `ambiguous_entity_reference` |
| Downstream | Hard replace; `referential_clarity_replacement_applied=true` |

#### B2 — Violation kind out of scope (1 turn)

| Signal | Value |
|---|---|
| Kind | `referent_drift` |
| Token | `they` |
| candidate_entity_ids | gate_guard, gate_serjeant |
| Rule blocked | Eligibility helper filters to `ambiguous_entity_reference` only |
| Contract | BV3A explicitly excludes `referent_drift` |

#### B3 — Multi-person without grounding (30 archived + refreshed candidates)

| Signal | Value |
|---|---|
| Visible persons | 4–6 |
| interlocutor / social NPC | null |
| Shape | `"…," he says` without contextual speaker |
| Expected | Ineligible by design |

---

### C — Metadata mismatch (0 turns)

Checked:

- Snapshot restore in `apply_visibility_enforcement` / `apply_referential_clarity_enforcement` preserves upstream flags when repair applied.  
- Unit test `test_observe_dialogue_he_says_repairs_via_upstream_not_hard_fallback` confirms `referential_clarity_upstream_repair_applied=true` in finalized FEM for eligible fixture.

No evidence of upstream-applied meta being dropped before persistence on replay turns (none were applied).

---

### D — Pipeline ordering (0 failure turns)

Upstream repair is the **first** step in `run_gate_terminal_enforcement_pipeline`, before visibility and downstream referential enforcement. Ordering matches BV3A contract.

Observed issue is **not** “repair after hard replace” but “never eligible before hard replace.”

---

### E — Replay-only divergence (≥1 confirmed)

| Signal | Example |
|---|---|
| FEM violation sentence | `"if you're looking for something, say it before the trail shifts," they say` |
| Final `player_facing_text` | Guard spear-butt dialogue (no `they say` sentence) |
| Tags | `retry_escape_hatch`, `forced_retry_fallback`, `model_retry_attempt: 2` |
| Interpretation | Nested/intermediate FEM from retry gate pass; metrics read stale violation context |

Also: BV3B refresh manifest describes stub GPT `"Keep moving," he says` but API path emits **prepared/retry** text — corpus shape ≠ refresh script comment.

---

### F — Other (0 turns)

No strict-social observe misroutes, no `res_kind` mislabels on scanned observe FEM.

---

## Failure → symptom matrix

| Symptom in metrics | Failure class |
|---|---|
| `upstream_*` fields null | A (stale FEM) |
| `attempted=false`, accept path | A′ |
| `attempted=true`, `eligible=false`, `unrepaired>1` | B1 |
| `attempted=true`, `eligible=false`, `referent_drift` | B2 |
| `attempted=true`, `eligible=false`, multi-person `he` | B3 |
| FEM sample ≠ emitted text | E |

---

## Activation rate decomposition

| Numerator / denominator | Value |
|---|---|
| Observe turns scanned | 65 |
| `upstream_repair_applied=true` | **0** |
| **Repair Activation Rate** | **0%** |
| Refreshed-only (exclude archive null-upstream) | 21 turns → still **0%** |
| Turns matching unit-test eligibility profile | **0** → expected applied **0** |
