# CP7 — Opportunistic Corrective Discovery Report

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`, CP1–CP6 corrective reports

## Executive Summary

Opportunistic discovery surfaced **3 failing regression tests** in `tests/test_contextual_minimal_repair_regressions.py` that were not covered by prior CP slices. Root cause: terminal minimal-repair anchoring required non-empty `visible_facts`, but canonical scenes such as `tavern` ship with empty `visible_facts` while still having usable `location`/`summary` metadata. Fixed with a **1-file production change** in `game/gm_retry.py` adding a shared scene-anchor fallback helper.

## Defect Reproduced?

**Yes**

---

## 1. Candidates Considered (Ranked)

### Candidate 1 — Contextual minimal repair scene-anchor degradation (CHOSEN)

| Field | Value |
|---|---|
| **Description** | Empty-resolution terminal repair falls back to generic hard lines (`Something shifts…`, `They answer cautiously…`) instead of scene-anchored contextual repair when `visible_facts` is empty. |
| **Subsystem** | Terminal retry / minimal resolution repair (Block 14) |
| **Likely production files** | `game/gm_retry.py` |
| **Expected files touched** | 1 production |
| **Locality** | Low — single helper + two call sites |
| **Replay impact** | None on protected manifest nodes; affects terminal empty-resolution player-facing text quality |
| **Recurrence potential** | Medium — any scene with empty `visible_facts` but valid location/summary |
| **Confidence** | **High** — 3/7 focused regression tests failed reproducibly |

### Candidate 2 — Opening fallback authorship/source drift

| Field | Value |
|---|---|
| **Description** | Opening fallback reports compatibility-local ownership or wrong upstream source despite acceptable prose. |
| **Subsystem** | Opening fallback / replay projection |
| **Likely production files** | `game/opening_deterministic_fallback.py`, `game/final_emission_opening_fallback.py` |
| **Expected files touched** | 2–5 |
| **Locality** | Medium |
| **Replay impact** | Direct-seam protected opening ownership fields |
| **Recurrence potential** | Watch-tier key in recurrence history |
| **Confidence** | **Low** — direct-seam and opening projection suites green (13 passed, 1 skipped) |

### Candidate 3 — Long-session scenario spine degradation (CP8 class)

| Field | Value |
|---|---|
| **Description** | 25-turn Frontier Gate branch shows late fallback spike or branch convergence failure. |
| **Subsystem** | Scenario spine / long-session stability |
| **Likely production files** | `game/scenario_spine_eval.py`, `game/prompt_context.py`, `game/social_memory.py` |
| **Expected files touched** | 4–8 |
| **Locality** | High blast radius |
| **Replay impact** | Protected 25-turn replay |
| **Recurrence potential** | High if present |
| **Confidence** | **Low** — protected long-session test passed |

### Candidate 4 — Identity repair unsupported named culprit (xfail)

| Field | Value |
|---|---|
| **Description** | Bounded-partial identity repair preserves unsupported named culprit text (`Captain Verrick`). |
| **Subsystem** | Final emission fallback behavior / identity repair |
| **Likely production files** | `game/fallback_behavior.py`, `game/final_emission_repairs.py` |
| **Expected files touched** | 2–4 |
| **Locality** | Medium |
| **Replay impact** | Unknown |
| **Recurrence potential** | Low — test skipped/xfailed under C2 Block C policy |
| **Confidence** | **Low** — marked intentional design debt, not an active regression |

### Candidate 5 — `response_type_candidate_ok` projection drift

| Field | Value |
|---|---|
| **Description** | Golden replay projects `response_type_candidate_ok` inconsistently vs runtime FEM debug. |
| **Subsystem** | Replay projection / failure classifier |
| **Likely production files** | `tests/helpers/golden_replay.py`, `tests/helpers/golden_replay_projection.py` |
| **Expected files touched** | 1–3 (mostly projection helpers) |
| **Locality** | Low–medium |
| **Replay impact** | Elevated recurrence key (count 4) |
| **Recurrence potential** | High in history, but no current failing node |
| **Confidence** | **Low** — classifier and projection integration suites green (~110 tests in CP5 baseline) |

---

## 2. Chosen Candidate

**Contextual minimal repair scene-anchor degradation**

Selection rationale:

- Independent subsystem (terminal retry repair), unrelated to CP2 routing, CP3 vocative, CP5 fallback projection
- Reproducible via existing focused regression tests (no synthetic probe needed)
- Expected ≤5 production files (actual: **1**)
- Measurable validation via `tests/test_contextual_minimal_repair_regressions.py`
- Low governance impact
- No architectural redesign

---

## 3. Reproduction

### Failing tests (before fix)

```bash
python -m pytest tests/test_contextual_minimal_repair_regressions.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 4 |
| **Failed** | 3 |

Failed nodes:

- `test_social_contextual_repair_scene_anchor_without_question_signal`
- `test_nonsocial_minimal_repair_by_context`
- `test_contextual_repair_lines_pass_legality_checks`

### Before-fix signals

**Social** (`active_scene_id=tavern`, emergency fallback monkeypatched empty):

| Signal | Value |
|---|---|
| `first_visible_fact_detail` | `""` |
| `debug_notes` | `…|social_contextual_repair:hard_fallback` |
| `player_facing_text` | Generic hard line / strict-social terminal rewrite |

**Nonsocial** (`active_scene_id=tavern`):

| Signal | Value |
|---|---|
| `first_visible_fact_detail` | `""` |
| `debug_notes` | `…|nonsocial_contextual_repair:hard_fallback` |
| `player_facing_text` | `Something shifts in the scene, drawing your attention forward.` |

Canonical `data/scenes/tavern.json` has `"visible_facts": []` but non-empty `location` (`Rain Barrel Tavern`) and `summary`.

---

## 4. Root Cause

`_minimal_repair_context` and `_nonsocial_minimal_resolution_line` derived repair anchor text exclusively from `visible_facts[0]`. When that list is empty — as on tavern and other canon scenes — contextual repair could not enter the `scene_anchor` path and degraded to `hard_fallback`, producing generic stall wording instead of location/summary-anchored phrasing.

Opening visible-fact curation (`select_opening_narration_visible_facts`) also returns `[]` for tavern, so the pre-existing curation hook did not help.

---

## 5. Implementation Summary

| File | Change |
|---|---|
| `game/gm_retry.py` | Added `_first_scene_repair_anchor_detail(env)` — prefers `visible_facts[0]`, then falls back to scene `location`, then `summary`. Wired into `_minimal_repair_context` and `_nonsocial_minimal_resolution_line`. |

No test file changes required; existing Block 14 regression tests encode the expected behavior.

### After-fix signals

**Social**:

| Signal | Value |
|---|---|
| `first_visible_fact_detail` | `Rain Barrel Tavern` |
| `debug_notes` | `…|social_contextual_repair:scene_anchor` |
| `player_facing_text` | Contains `frames what you hear` / `tavern` |

**Nonsocial**:

| Signal | Value |
|---|---|
| `debug_notes` | `…|nonsocial_contextual_repair:scene_anchor` |
| `player_facing_text` | `Rain Barrel Tavern still frames what you can see; …` |

---

## 6. Validation

### Focused repair suite (post-fix)

```bash
python -m pytest tests/test_contextual_minimal_repair_regressions.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 7 |
| Failed | 0 |

### Adjacent golden structural check

```bash
python -m pytest tests/test_golden_replay_structural_invariants.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 6 |
| Failed | 0 |

Protected replay manifest not touched; no replay field taxonomy change.

---

## 7. Locality Metrics

| Metric | Value |
|---|---:|
| **Total files changed (CP7 slice)** | 1 |
| Production files | 1 (`game/gm_retry.py`) |
| Test files | 0 |
| Helpers | 0 |
| Governance/docs | 1 (this report) |
| Replay/golden | 0 |

Note: working tree contains unrelated prior CP2/CP3/CP5 diffs; CP7 production scope is **`game/gm_retry.py` only**.

---

## 8. Recurrence Evidence

| Source | Evidence |
|---|---|
| Failing regression tests | 3/7 nodes in `test_contextual_minimal_repair_regressions.py` |
| Scene data | `data/scenes/tavern.json` — `visible_facts: []`, `location: Rain Barrel Tavern` |
| Debug mode strings | `social_contextual_repair:hard_fallback` / `nonsocial_contextual_repair:hard_fallback` before fix |
| Recurrence registry | No existing protected recurrence key; defect class is terminal-repair quality, not manifest drift |

---

## 9. Replay Impact

- Protected golden replay scenarios: **no change expected** (terminal empty-resolution path not exercised by manifest nodes)
- Failure classifier / projection: **no change**
- Player-facing impact: scenes with empty `visible_facts` now receive location/summary-anchored terminal repair instead of generic hard lines

---

## 10. Qualifying Corrective Fix?

**Yes** — this is an independent CP cohort #3 qualifying corrective fix:

| Criterion | Met? |
|---|---|
| Real defect reproduced | Yes — 3 failing tests |
| Production code changed | Yes — 1 file |
| Locally fixable | Yes |
| Unrelated to CP2/CP3/CP5 | Yes — terminal retry repair subsystem |
| ≤5 production files | Yes — 1 |
| Measurable validation | Yes — 7/7 regression tests pass |
| Not architectural / governance | Yes |

This is the **fourth** qualifying corrective fix in cohort #3 (after CP2, CP3, CP5).

---

## 11. Areas Explicitly Not Revisited

Per instructions, no re-probing of CP1 (sanitizer/preflight), CP4 (BX guard parity), or CP6 (dialogue lock) unless new defects pointed there. Baseline checks on those surfaces were not repeated in this slice.
