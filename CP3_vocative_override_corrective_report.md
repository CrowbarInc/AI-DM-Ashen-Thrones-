# CP3 — Vocative Speaker Override Corrective Report

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`, `CP2_directed_route_corrective_report.md`

## Executive Summary

Baseline tests passed (54/54), so exploratory probing continued. A **reproducible vocative override defect** was found: discourse-prefixed vocatives with **dash separators** or **bare question words** (no comma) failed to override prior speaker continuity. Fixed with a localized change to spoken-vocative extraction in `game/interaction_context.py` plus two targeted regression tests.

## Defect Reproduced?

**Yes**

## Reproduction Scenario

Setup: engaged social continuity pinned to `runner`; `gate_guard` also present.

Player input:

```text
Hey guard - what did you notice by the north arch?
```

Also reproduced for:

```text
Listen guard what did you hear about the patrol?
```

Protected golden `vocative_override_after_prior_continuity` uses comma vocatives (`Guard, what did you see?`) and **did not** cover these variants.

### Before fix

| Signal | Value |
|---|---|
| `resolve_spoken_vocative_target.has_spoken_vocative` | `False` |
| `resolve_directed_social_entry.target_actor_id` | `runner` |
| `resolve_directed_social_entry.target_source` | `active_interlocutor` |
| `continuity_overridden_by_spoken_vocative` | `False` |
| `resolve_authoritative_social_target.source` | `continuity` |
| Downstream `selected_speaker_id` (implicit) | would remain `runner` |

Contrast: `Guard, what did you see?` and `Listen guard, what did you hear?` correctly switched to `gate_guard` via `spoken_vocative`.

### After fix

| Signal | Value |
|---|---|
| `has_spoken_vocative` | `True` |
| `target_actor_id` | `gate_guard` |
| `target_source` | `spoken_vocative` |
| `continuity_overridden_by_spoken_vocative` | `True` |
| `resolve_authoritative_social_target.source` | `spoken_vocative` |

## Root Cause

`_extract_comma_vocative_phrase_after_discourse` only recognized discourse + name when followed by a **comma** (`_DISCOURSE_SPACE_THEN_NAME_COMMA_RE`). Real player lines often use:

- Dash separators: `Hey guard - …`, `Hey guard—…`
- No separator before a question: `Listen guard what …`

When spoken vocative extraction failed, `resolve_directed_social_entry` fell through to **active interlocutor follow-up**, preserving the wrong speaker despite an explicit vocative cue.

No changes were required in `speaker_contract_enforcement.py`, `final_emission_speaker_observation.py`, or `post_emission_speaker_adoption.py` — the defect was upstream in vocative target binding.

## Production Files Changed

| File | Change |
|---|---|
| `game/interaction_context.py` | Extended discourse vocative patterns: `_DISCOURSE_SPACE_THEN_NAME_SEP_RE` (comma/dash) and `_DISCOURSE_SPACE_THEN_NAME_BEFORE_QUESTION_RE` (bare question after role/name) |

## Tests Added/Modified

| File | Change |
|---|---|
| `tests/test_directed_social_routing.py` | Added `test_spoken_vocative_hey_guard_dash_overrides_runner_continuity` |
| `tests/test_directed_social_routing.py` | Added `test_spoken_vocative_listen_guard_bare_question_overrides_runner_continuity` |

## Validation Summary

### CP3 baseline suite

```bash
python -m pytest tests/test_vocative_direct_address_recovery.py tests/test_speaker_contract_enforcement.py tests/test_final_emission_speaker_observation.py tests/test_golden_replay_structural_invariants.py -q --tb=short
```

| Outcome | Count |
|---|---:|
| **Passed** | 54 |
| Failed | 0 |

Breakdown: vocative recovery (5), speaker contract (36), speaker observation (7), golden structural (6).

### New regression tests

```bash
python -m pytest tests/test_directed_social_routing.py::test_spoken_vocative_hey_guard_dash_overrides_runner_continuity tests/test_directed_social_routing.py::test_spoken_vocative_listen_guard_bare_question_overrides_runner_continuity -q --tb=short
```

Result: **2 passed**

### Protected vocative golden

```bash
python -m pytest tests/test_golden_replay_structural_invariants.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants -q --tb=short
```

Result: **1 passed** — `selected_speaker_id == "guard"` on turn 2 unchanged.

### Manifest check

```bash
python tools/refresh_protected_replay_manifest.py --check
```

Result: **exit 0**

## Locality Metrics (CP3 slice)

| Metric | Value |
|---|---:|
| Total files changed (CP3) | 2 |
| Production files touched | 1 |
| Test files touched | 1 |
| Governance/docs files touched | 0 |
| Replay/golden files touched | 0 |

Note: `game/interaction_context.py` also contains the CP2 generic-role perception pattern from the prior slice; CP3 adds only the discourse vocative regex/extraction delta in the same file.

Within stop thresholds (≤5 production files, no governance, no redesign).

## Before/After Speaker Diagnostics

Scenario: runner continuity → `Hey guard - what did you notice by the north arch?`

| Field | Before | After |
|---|---|---|
| `target_actor_id` / dialogue target | `runner` | `gate_guard` |
| `target_source` / `selected_speaker_source` | `active_interlocutor` | `spoken_vocative` |
| `continuity_overridden_by_spoken_vocative` | `False` | `True` |
| Canonical speaker binding | continuity | spoken vocative |
| `selected_speaker_id` (downstream) | `runner` (wrong) | `gate_guard` |

## Replay Impact

- Protected `vocative_override_after_prior_continuity`: **pass**, no golden rewrite
- No manifest drift
- No replay artifact edits

## Recurrence Evidence

- Historical recurrence keys exist for `selected_speaker_id` / `selected_speaker_source` speaker drift and the `vocative_override_after_prior_continuity` scenario (corpus observations).
- This slice adds **new prevention evidence** for dash/bare-question vocative variants not covered by the protected comma-vocative scenario.
- No recurrence registry retirement performed (no documented protected failure→fix key for these exact line shapes).

## CP Cohort #3 Qualification

| Criterion | Met? |
|---|---|
| Reproduced real defect | **Yes** |
| Bounded production fix | **Yes** (1 file) |
| Focused regression tests | **Yes** (2 tests) |
| failure → fix → validation cycle | **Yes** |
| Locality within budget | **Yes** |

**Verdict: qualifies as an independent CP corrective-locality cohort #3 entry** (second production fix after CP2; CP1 was validation-only).

## Recommended Next Candidate

**CP5 — Fallback-family projection mismatch**

Rationale:

1. CP2 (route binding) and CP3 (vocative override) both touched speaker/routing surfaces; discovery advises running **only one** of CP3/CP4 first to avoid over-concentrating on speaker work — CP3 is now complete.
2. CP4 (BX guard parity) remains valid but adds another speaker-identity slice; defer to limit cohort concentration.
3. CP5 has low–medium blast radius, no expected golden rewrite, and addresses replay/projection correctness (`fallback_family`) including the unrelated CO102 operational sentinel class — good diversity for cohort #3.

**Alternative:** CP4 if the next slice should stay on speaker parity before projection work.
