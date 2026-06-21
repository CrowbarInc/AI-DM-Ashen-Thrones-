# BV8 — Verification Projection

**Date:** 2026-06-21  
**Scope:** Estimate recurrence metrics after Phase 1 (stale key retirement + dedupe) and after full BV8 (Phases 1–3).

---

## Baseline (pre-BV8)

| Metric | Value | Source |
|---|---:|---|
| Total recurrence event rows | 11 | `bug_recurrence_event_log.json` |
| Speaker-family event rows | 9 (81.8%) | event log |
| Dominant key event rows | 8 (72.7%) | projection key |
| Unique recurrence keys | 4 | history JSON |
| Recurring keys (occurrence ≥ 2) | 1 | history JSON |
| Regression recurrence rate | 25% (1/4 keys) | history JSON |
| Portfolio concentration | **0.686** | `portfolio_trajectory_summary` |
| `validated_outcome_count` | **0** | `outcome_validation_summary` |
| Dominant key status | `active` | watchlist: **prioritize** |
| Vocative test live status | **PASS** | BV8 re-run |

---

## After Phase 1 — stale key retirement + dedupe

**Actions:** Retire projection key; collapse 8 duplicate events; regenerate history.

| Metric | Projected | Delta | Notes |
|---|---:|---:|---|
| Total recurrence event rows | **3** | −8 | Remove 7 dupes + retire/remove dominant key |
| Speaker-family event rows | **1** | −8 | Only wrong_speaker enforcement row remains |
| Dominant key event rows | **0** | −8 | Projection key retired |
| Unique recurrence keys (active) | **3** | −1 | Projection key → retired |
| Recurring keys | **0** | −1 | No key with occurrence_count ≥ 2 |
| Regression recurrence rate | **0%** (0/3) | −25 pp | No recurring keys remain |
| Portfolio concentration | **~0.33** | −0.36 | Roughly equal 3 emerging keys |
| Dominant key share (events) | **0%** | −72.7 pp | |
| `validated_outcome_count` | **1** | +1 | Retired projection key with test-green evidence |
| Watchlist prioritize entries | **0** | −1 | Projection key leaves prioritize tier |

### Scenario concentration after Phase 1

| Scenario | Events | Share |
|---|---:|---:|
| wrong_speaker_strict_social_emission | 1 | 33.3% |
| directed_npc_question | 1 | 33.3% |
| sanitizer_scaffold_leakage | 1 | 33.3% |
| vocative_override_after_prior_continuity | 0 | 0% |

---

## After Phase 2 — canonical ID contract

| Metric | Projected | Delta vs baseline |
|---|---:|---|
| New projection-key events (next 2 CI cycles) | **0** | Prevents regrowth |
| Alias mismatch class | **Retired** | Tests + projection use canonical ids |
| investigate_first misrouting | **0** | Points to `golden_replay_projection.py` |
| wrong_speaker key | **unchanged or retired** | Depends on live test status |

**Maintenance impact:** Engineers stop investigating `golden_replay.py` for `selected_speaker_id` mismatches — projection contract becomes explicit.

---

## After Phase 3 — registry protection

| Metric | Projected | Notes |
|---|---:|---|
| Duplicate event inflation | **Blocked** | Dedupe guard on append |
| Retirement without evidence | **Blocked** | Requires validated outcome blob |
| Recurrence concentration regrowth | **Low risk** | Registry tests + dedupe |

---

## Expected maintenance impact

| Area | Before BV8 | After Phase 1 | After full BV8 |
|---|---|---|---|
| **False recurrence signal** | 8-hit "recurring" projection key drives prioritize tier | **Eliminated** | Locked |
| **Investigation routing** | Misdirected to `golden_replay.py` | Unchanged | **Fixed** to projection owner |
| **Protected replay repair churn** | Repeated alias/canonical patches possible | Reduced | **Contract prevents** |
| **Scorecard recurrence dimension** | Inconclusive (0 validated outcomes) | **1 validated retirement** | Sustainable |
| **BV5 maintenance drag claim** | "Speaker projection 8 hits unchanged" | **Retired** | Prevention locked |

### Maintenance economics projection

| Scorecard lever | Phase 1 impact | Full BV8 impact |
|---|---|---|
| Maintenance Drag | **+0.5** (remove false prioritize target) | **+0.5 to +1.0** (contract + registry) |
| Ownership Clarity | neutral | **+0.5** (investigate_first alignment) |
| Operational Simplicity | **+0.25** (dedupe hygiene) | **+0.5** (registry guards) |

---

## Risk register (verification)

| Risk | Mitigation | Residual |
|---|---|---|
| Retiring key while bug latent | Phase 1 gated on vocative test green + full golden replay lane | Low |
| Over-deduping legitimate repeats | Dedupe on `(key, scenario, run_id)` only; allow cross-run repeats | Low |
| Canonical ID change breaks tests | Phase 2 updates expectations + manifest together | Low-medium |
| wrong_speaker key grows to recurring | Phase 2.5 monitoring before retirement | Medium |

---

## Verification commands

```bash
# Phase 1 gate — protected replay green
python -m pytest -m golden_replay -q --tb=short

# Phase 1 gate — vocative scenario
python -m pytest tests/test_golden_replay_structural_invariants.py::test_golden_replay_vocative_override_after_prior_continuity_structural_invariants -q

# Post-retirement — regenerate history (tooling)
python -m pytest tests/test_replay_bug_class_recurrence.py -q

# Phase 2 gate — projection contract
python -m pytest tests/test_golden_replay_projection.py -q
```

---

## Success metrics summary

| Metric | Start | After Phase 1 | Target (full BV8) |
|---|---:|---:|---:|
| Dominant key share | **72.7%** | **0%** | **0%** (sustained) |
| Recurring keys | **1** | **0** | **0** |
| Recurrence concentration | **0.686** | **~0.33** | **≤0.35** |
| `validated_outcome_count` | **0** | **1** | **≥1** |
| Live vocative test | PASS | PASS | PASS |

---

## Verdict

A **clear retirement path exists**. Phase 1 alone removes **72.7%** of recurrence event concentration with **no runtime changes** because the underlying failure is **already resolved** — recurrence is instrumentation debt. Phases 2–3 prevent the same mismatch class from re-entering history.

---

## Evidence

| Source | Role |
|---|---|
| [BV8_retirement_plan.md](BV8_retirement_plan.md) | Phase definitions |
| [BV8_concentration_report.md](BV8_concentration_report.md) | Baseline concentration |
| [BV8_recurrence_inventory.md](BV8_recurrence_inventory.md) | Duplicate row analysis |
