# CP6 — Lead Follow-up Dialogue Lock Corrective Report

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`, `CP2_directed_route_corrective_report.md`, `CP3_vocative_override_corrective_report.md`, `CP5_fallback_projection_corrective_report.md`

## Executive Summary

Baseline continuity suites and the protected `lead_followup_with_dialogue_lock` golden replay all passed (~169 + 1 tests). Exploratory probing continued across dialogue-lock follow-ups, multi-NPC switching, narration/observation interrupts, canonical entry projection, prompt-context interlocutor export, and conversational memory anchoring. **No reproducible dialogue-lock continuity defect was found.** No production changes were made.

## Defect Reproduced?

**No**

## Baseline Validation

### CP6 continuity suite

```bash
python -m pytest \
  tests/test_interaction_continuity_contract.py \
  tests/test_interaction_continuity_repair.py \
  tests/test_prompt_context.py \
  tests/test_conversational_memory_window.py \
  -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 169 |
| Failed | 0 |

### Protected replay

```bash
python -m pytest \
  tests/test_golden_replay_structural_invariants.py::test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants \
  -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 1 |
| Failed | 0 |

Turn 2 expectations: `selected_speaker_id == "tavern_runner"`, dialogue route persists, no scaffold leakage.

### Manifest check

```bash
python tools/refresh_protected_replay_manifest.py --check
```

Result: **exit 0**

## Probe Scenarios Investigated

Ephemeral probes in `codex_pytest_tmp/` (not part of the test suite) exercised the edge cases listed in the CP6 brief.

### 1. Bare follow-up after established dialogue lock

**Setup:** Turn 1 vocative to Tavern Runner about patrol; turn 2 bare `"Where were they last seen?"`

| Signal | Value |
|---|---|
| `route_kind` | `dialogue` |
| `selected_speaker_id` | `tavern_runner` |
| `canonical_entry.target_source` | `active_interlocutor` |
| `canonical_entry.reason` | `active_interlocutor_followup` |
| `active_interaction_target_id` (post-turn 1) | `tavern_runner` |

**Verdict:** Works as designed when social lock is held.

### 2. Protected scenario (explicit vocative turn 2)

Same as manifest scenario (`"Runner, where were they last seen?"`):

| Signal | Value |
|---|---|
| `canonical_entry.target_source` | `spoken_vocative` |
| `selected_speaker_id` | `tavern_runner` |

**Verdict:** Protected replay passes; replay/runtime agree.

### 3. Narration interrupt then bare follow-up

**Setup:** Social question → `"I glance around the tavern."` → bare patrol follow-up

| Turn | `active_target` | `current_interlocutor` | `interaction_mode` | `npc_id` |
|---:|---|---|---|---|
| 1 | `tavern_runner` | `tavern_runner` | `social` | `tavern_runner` |
| 2 (narration) | `None` | `None` | `activity` | `None` |
| 3 (follow-up) | `tavern_runner` | `tavern_runner` | `social` | `tavern_runner` |

Turn 2 canonical entry: `no_addressable_target` (expected — narration breaks lock).  
Turn 3 recovery: `scene_address_resolution` / directed social (not `active_interlocutor_followup`) but speaker still `tavern_runner`.

**Verdict:** Intentional lock break on narration; follow-up recovers runner without defect. Matches transcript regression intent (`test_transcript_tavern_runner_patrol_wait_beat_then_follow_up_question`).

### 4. Two-NPC switch (lead → supporting → bare follow-up)

**Setup:** Runner engaged → vocative to Guard Captain → bare `"Where were they last seen?"`

With correct session mutation (do not assign `update_after_resolved_action` return value to `session`):

| Signal | Value |
|---|---|
| `target_actor_id` | `guard_captain` |
| `target_source` | `active_interlocutor` |
| `reason` | `active_interlocutor_followup` |

**Verdict:** Continuity correctly follows **last** interlocutor, not lead NPC. Expected behavior, not a lock defect.

### 5. Observation during lock

**Setup:** Engaged runner; `"What do I notice in the tavern?"`

| Signal | Value |
|---|---|
| `should_route_social` | `False` |
| `reason` | `local_scene_observation_query` |
| `active_interaction_target_id` | preserved (`tavern_runner`) |

**Verdict:** Observation does not hijack dialogue route; lock fields preserved. Covered by Objective #21 recovery tests (`tests/test_local_observation_followup_social_recovery.py`).

### 6. Prompt context / memory window

- `build_active_interlocutor_export` requires `active_interaction_target_id`; existing unit coverage in `tests/test_prompt_context.py` passes.
- `conversational_memory_window` anchored/active-target bonuses covered by baseline suite; no drift found under dialogue-lock probes.
- No replay disagreement between runtime session state and projected turn observations on protected or probe scenarios.

### 7. Probed but ruled out

| Candidate | Outcome |
|---|---|
| `update_after_resolved_action` clearing lock on social `question` kind | **Not a defect** — preserves target when called on session dict (probe bug was assigning return ctx dict to `session`) |
| Bare follow-up failing with two NPCs | **Not reproduced** with correct session handling |
| Canonical entry unavailable on bare follow-up while `npc_id` correct | **Not reproduced** in golden replay projection (HTTP probe read wrong debug path) |
| Lead-followup recurrence in `replay_failure_report.md` | **No active failure** for `lead_followup_with_dialogue_lock` |

## Root Cause

N/A — no defect reproduced.

Observed behavior matches existing design:

- Dialogue lock binds via `active_interaction_target_id` + social mode.
- Bare information-seeking follow-ups use `active_interlocutor_followup` when no explicit addressee cue (`resolve_directed_social_entry` in `game/interaction_context.py`).
- Non-social narration/observation intentionally breaks lock (`update_after_resolved_action` / world-action escape paths).
- Objective #21 local-observation recovery handles `"what's going on at…"` misroutes without redesigning continuity.
- Post-emission adoption and stale-anchor clearing covered by `tests/test_narration_transcript_regressions.py` (obj21 suite).

## Production Files Modified

| File | Change |
|---|---|
| *(none)* | — |

## Tests Added or Updated

| File | Change |
|---|---|
| *(none)* | Ephemeral probes only in `codex_pytest_tmp/` (not committed to test suite) |

## Validation Summary (post-probe)

All baseline and protected commands re-run green after probing. No regression introduced (no code changes).

## Locality Metrics (CP6 slice)

| Metric | Value |
|---|---:|
| Total files changed | 0 |
| Production files touched | 0 |
| Test files touched | 0 |
| Replay/helper files touched | 0 |
| Governance/docs files touched | 1 (this report) |
| Replay/golden files touched | 0 |

Within stop thresholds. Stopped per instruction: no reproducible defect.

## Before/After Diagnostics

No fix applied. Representative probe rows:

| Field | Bare follow-up (lock held) | After narration + follow-up |
|---|---|---|
| `active_interlocutor` / `active_interaction_target_id` | `tavern_runner` → `tavern_runner` | `tavern_runner` → `None` → `tavern_runner` |
| `canonical_entry.reason` | `active_interlocutor_followup` | `no_addressable_target` → `directed_social_question` |
| `dialogue lock state` | held | broken then recovered |
| `interaction continuity` | preserved | broken on narration, restored on follow-up |
| `prompt context` | interlocutor exported when target set | not probed for defect (no mismatch found) |
| `replay impact` | none | none |
| `recurrence outcome` | no new failure | no new failure |

## Replay Impact

- Protected `lead_followup_with_dialogue_lock`: **pass**, unchanged
- No golden expectation edits
- No manifest drift
- Trend-window artifacts show `active_interlocutor_followup` on lead-followup turns (consistent with runtime)

## Recurrence Evidence

- Historical protected scenario `lead_followup_with_dialogue_lock` remains stable in trend-window runs.
- Related continuity recurrence keys (`selected_speaker_id`, route drift) addressed in prior cohort slices CP2/CP3/CP5 — no new CP6-specific failure observed.
- No recurrence registry retirement performed (no failure→fix cycle).

## CP Cohort #3 Qualification

| Criterion | Met? |
|---|---|
| Reproduced real defect | **No** |
| Bounded production fix | **No** |
| Focused regression tests | **No** (probes only) |
| failure → fix → validation cycle | **No** |
| Locality within budget | **Yes** (zero production churn) |

**Verdict: does NOT qualify as an independent CP corrective-locality cohort #3 entry.** This slice confirms dialogue-lock / lead-follow-up surfaces are currently stable after CP2/CP3/CP5 runtime and projection fixes. Same class as CP1 (validation-only).

## Recommended Next Candidate

**CP4 — BX guard parity drift**

Rationale:

1. CP6 found no actionable continuity defect; remaining cohort candidates with player-visible risk are CP4 (speaker identity) and CP9 (preflight/config).
2. Discovery advises running **only one** of CP3/CP4 first — CP3 is complete; CP4 is the natural next speaker-identity slice.
3. CP4 has existing BX marker suite (`pytest -m bx_speaker_parity`), protected replay paths, and concrete parity metrics (`guard`, `gate_guard`, `guard_captain` collapse cases).
4. CP6 continuity work is stable; speaker parity defects would surface as wrong `selected_speaker_id` / source parity — distinct from dialogue-lock binding probed here.

**Alternative:** **CP9** if the cohort should take a low-risk non-replay corrective (preflight/config safety) before another speaker-identity slice. CP9 was validation-only in CP1 and may still be stable, but it offers the lowest blast radius if the cohort needs a small production win.
