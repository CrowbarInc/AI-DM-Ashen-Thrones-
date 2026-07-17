# CP5 — Fallback Projection Consistency Corrective Report

Date: 2026-06-28  
Planning authority: `CP_corrective_locality_cohort_3_discovery.md`, `CP2_directed_route_corrective_report.md`, `CP3_vocative_override_corrective_report.md`

## Executive Summary

Baseline projection and classifier suites passed (~110 tests), so exploratory probing continued. A **reproducible fallback projection mismatch** was found on the neutral speaker grounding bridge path: runtime FEM stamps `final_emitted_source=neutral_reply_speaker_grounding_bridge` but replay projected `fallback_family=strict_social_deterministic_fallback` because a generic strict-social realization provenance field overwrote the emission-source taxonomy. Fixed with a localized read-side precedence adjustment in `tests/helpers/golden_replay_projection_fallbacks.py` plus focused regression coverage.

## Defect Reproduced?

**Yes**

## Reproduction Scenario

Runtime bridge emission from `build_final_strict_social_response` when `reply_speaker_grounding_neutral_bridge` is set (see `tests/test_social_speaker_grounding.py::test_build_final_strict_social_emits_neutral_bridge_when_grounding_denied`).

Synthetic replay projection with the stamped FEM meta:

```python
fem_payload(
    final_route="replaced",
    final_emitted_source="neutral_reply_speaker_grounding_bridge",
    fallback_kind="neutral_speaker_grounding_bridge",
    realization_fallback_family="strict_social_deterministic_fallback",
)
```

### Before fix

| Signal | Value |
|---|---|
| `final_emitted_source` | `neutral_reply_speaker_grounding_bridge` |
| `fallback_kind` (FEM) | `neutral_speaker_grounding_bridge` |
| `realization_fallback_family` (FEM) | `strict_social_deterministic_fallback` |
| `fallback_family_used` (FEM) | absent / `None` |
| **Projected `fallback_family`** | **`strict_social_deterministic_fallback`** (wrong) |
| `fallback_family` in `unavailable` | no (present but misclassified) |
| Realization provenance in FEM raw keys | present |
| Long-session fallback escalation | bridge turn counted under generic strict-social family |

Existing test `test_golden_projection_projects_neutral_speaker_grounding_replacement_family` passed only because its FEM fixture omitted the runtime realization stamp that production always attaches (`social_exchange_emission.py` line 1277).

### After fix

| Signal | Value |
|---|---|
| **Projected `fallback_family`** | **`neutral_reply_speaker_grounding_bridge`** |
| `final_emitted_source` | unchanged — matches projection |
| `realization_fallback_family` (FEM raw) | still present (observational, not rewritten) |
| `fallback_family` in `unavailable` | no |
| Long-session fallback escalation | bridge turn correctly attributed |

## Root Cause

CF1 diegetic-first precedence (`fallback_family_used` → `realization_fallback_family`) did not account for bridge emissions where:

1. Production sets an authoritative `final_emitted_source` identifying the bridge template.
2. Production also attaches `realization_fallback_family=strict_social_deterministic_fallback` as **generic strict-social provenance**, not as the observed fallback taxonomy.

`project_replay_fallback_family_from_fem` therefore returned the generic realization stamp before lineage bridge inference could apply, and `_resolve_fallback_family` never reached its lineage fallback because a non-null (but wrong) family was already resolved.

This is a **read-side observational inconsistency**, not a runtime emission defect. No fallback taxonomy redesign was required.

### Probed but not fixed (out of scope)

| Probe | Outcome |
|---|---|
| `wrong_speaker_strict_social_emission` — `fallback_family` unavailable | **Not a defect**: `final_emitted_source=normalized_social_candidate`; FEM keys exist but values are `None`; unavailable is correct |
| Sealed sources without diegetic family (`anti_reset_local_continuation_fallback`, etc.) | **Intentional CF1 behavior** when realization stamp absent; not reproduced as mismatch |
| CO102 operational sentinel on wrong_speaker | Operational classification artifact, not bridge projection |

## Production Files Modified

| File | Change |
|---|---|
| *(none)* | Fix is read-side golden replay projection only |

## Tests / Helpers Modified

| File | Change |
|---|---|
| `tests/helpers/golden_replay_projection_fallbacks.py` | Bridge `final_emitted_source` precedence between diegetic and generic realization in `project_replay_fallback_family_from_fem` |
| `tests/test_cf1_fallback_family_precedence.py` | Added matrix case; updated lineage chain expectations for emission-source bridge |
| `tests/test_golden_replay_projection_fallback_integration.py` | Added bridge+realization integration test and runtime-meta end-to-end test |

## Validation Summary

### CP5 baseline suite (before and after)

```bash
python -m pytest \
  tests/test_golden_replay_projection.py \
  tests/test_golden_replay_projection_presence_integration.py \
  tests/test_golden_replay_projection_fallback_integration.py \
  tests/test_failure_classifier.py \
  -q --tb=short
```

| Outcome | Before | After |
|---|---:|---:|
| Passed | ~110 | ~112 |
| Failed | 0 | 0 |

### CF1 precedence matrix

```bash
python -m pytest tests/test_cf1_fallback_family_precedence.py -q --tb=short
```

Result: **passed** (including new bridge emission-source case)

### Protected bridge projection

```bash
python -m pytest \
  tests/test_golden_replay_fallback_opening_projection.py::test_golden_projection_projects_neutral_speaker_grounding_replacement_family \
  tests/test_social_speaker_grounding.py::test_build_final_strict_social_emits_neutral_bridge_when_grounding_denied \
  -q --tb=short
```

Result: **2 passed**

### Manifest check

```bash
python tools/refresh_protected_replay_manifest.py --check
```

Result: **exit 0** — no manifest field churn

## Locality Metrics (CP5 slice)

| Metric | Value |
|---|---:|
| Total files changed | 3 |
| Production files touched | 0 |
| Test files touched | 2 |
| Test helper files touched | 1 |
| Governance/docs files touched | 0 |
| Replay/golden files touched | 0 |

Within stop thresholds (≤5 production files, no governance, no taxonomy redesign, no golden rewrite).

## Before/After Projection Diagnostics

Bridge turn with runtime realization stamp:

| Field | Before | After |
|---|---|---|
| `fallback_family` (projected) | `strict_social_deterministic_fallback` | `neutral_reply_speaker_grounding_bridge` |
| `final_emitted_source` | `neutral_reply_speaker_grounding_bridge` | unchanged |
| `realization_fallback_family` (FEM raw) | `strict_social_deterministic_fallback` | unchanged |
| `fallback_family_used` (FEM raw) | absent | absent |
| Projection presence (`fallback_family`) | available (wrong value) | available (correct value) |
| `fallback_family` in `unavailable` | no | no |
| Replay impact | misclassified fallback escalation | bridge family aligned with emission |
| Recurrence outcome | potential false strict-social fallback attribution | bridge attribution restored |

## Replay Impact

- No protected golden expectations altered
- No replay artifact edits
- Bridge turns with runtime realization stamps now project the same family as turns without the stamp (existing opening projection test)
- `wrong_speaker_strict_social_emission` unchanged — correctly reports `fallback_family` unavailable for normalized social emission

## Recurrence Evidence

- Long-session fallback escalation summaries (`summarize_long_session_replay_observations`) depend on projected `fallback_family`; misclassified bridge turns inflated generic strict-social fallback counts.
- CO102 pipeline records `wrong_speaker_strict_social_emission` as an operational sentinel for unrelated `fallback_family` unavailability — **not addressed** by this slice (correct behavior retained).
- No recurrence registry retirement performed.

## CP Cohort #3 Qualification

| Criterion | Met? |
|---|---|
| Reproduced real defect | **Yes** |
| Bounded fix | **Yes** (1 helper file, read-side only) |
| Focused regression tests | **Yes** (3 test additions/updates) |
| failure → fix → validation cycle | **Yes** |
| Locality within budget | **Yes** |
| No taxonomy redesign | **Yes** |
| No golden rewrite | **Yes** |

**Verdict: qualifies as an independent CP corrective-locality cohort #3 entry** (third corrective fix after CP2 and CP3; CP1 was validation-only).

## Recommended Next Candidate

**CP6 — Lead follow-up dialogue lock break**

Rationale:

1. CP2 (route), CP3 (vocative), and CP5 (projection) are complete; discovery recommends deferring **CP4** (BX guard parity) to avoid over-concentrating cohort work on speaker-identity surfaces.
2. CP6 addresses multi-turn continuity (target/route/metadata lock) — a distinct failure class from routing, vocative, and projection work already completed.
3. CP6 has medium blast radius but bounded test surface (`lead_followup_with_dialogue_lock`, continuity contract tests) and player-visible impact.
4. **CP9** remains a low-risk alternative if the next slice should stay validation-only or import/config safety without replay involvement.

**Alternative:** CP9 if the cohort should take a low-risk non-replay corrective before tackling cross-module continuity (CP6).
