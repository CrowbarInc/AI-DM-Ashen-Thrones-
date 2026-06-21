# BV6 — Residual Referential-Clarity Recommendation

**Date:** 2026-06-21  
**Decision authority:** BV6 discovery closeout

---

## Recommendation

### **REDUCE** (measurement) + **RETAIN** (behavior)

Do **not** expand repair contracts for EC-M01. Split incidence reporting so replay graduation and negative-control regression are both visible.

---

## Rationale

1. **Replay runtime RC elimination is complete.** Zero `referential_clarity_hard_replacement` events exist outside `artifacts/bv3d_measurement/`.
2. **The remaining event is intentional.** OBS-M002 is a negative control proving ungrounded multi-person dialogue still hard-replaces — matching BV3E EC-M01 rejection.
3. **Safe repair is impossible** without guessing between `guard_captain` and `tavern_runner`.
4. **EC-M01 expansion** would trade a metric cosmetic (−1) for speaker-guess risk on ~30 similar archive shapes.
5. **Measurement split** achieves the BV5 "0% incidence" graduation signal on replay without compromising safety or test coverage.

---

## Selected actions

| Priority | Action | Owner surface |
|---|---|---|
| **P0** | Add dual metric: `referential_clarity_hard_replacement_count_replay_only` | `tools/bv3a_referential_clarity_metrics.py` |
| **P0** | Document replay graduation: RC replay = 0 in BV3D scope docs | `docs/audits/BV3D_measurement_scope.md` |
| **P1** | Tag fixture lineage with `measurement_class=negative_control` in scan rows | `tools/bv3d_measurement_scope.py` |
| **Defer** | EC-M01 repair expansion (BV4B-RC track) | `game/final_emission_referential_clarity.py` |

---

## Rejected options

| Option | Verdict | Reason |
|---|---|---|
| **ELIMINATE via EC-M01 repair** | **Reject** | Speaker guess between named co-present NPCs; contradicts BV3E |
| **ELIMINATE via fixture removal** | **Reject** | Loses negative-control activation proof |
| **ELIMINATE via forcing repair on OBS-M002 only** | **Reject** | Special-casing one fixture doesn't generalize; hides contract gap |

---

## Success criteria (BV6 closeout)

| Criterion | Target | Status |
|---|---|---|
| Isolated remaining RC event | documented | **met** |
| Causal trace complete | input → hard replace | **met** |
| Failure classified | primary = no candidate grounding | **met** |
| Zero replay RC achievable | yes, already 0 | **met** |
| Zero combined metric achievable | yes, via measurement split | **met** |
| Safe repair achievable | no | **confirmed** |

---

## Answer to BV6 goal

> We know whether 0 RC fallbacks is realistically achievable and what change would be required.

| Interpretation | Achievable? | Required change |
|---|---|---|
| **0 RC on replay runtime** | **Yes — done** | None |
| **0 RC on BV3D combined metric** | **Yes** | Measurement split excluding negative controls (recommended) |
| **0 RC via safe in-place repair** | **No** | Would require unsafe EC-M01 speaker guessing |
| **0 RC while keeping negative control** | **Yes** | Dual metrics; behavior retained, replay incidence = 0 |

---

## Follow-on (optional BV6B)

If product requires a single headline metric of **0% fallback incidence**:

1. Ship measurement split (BV6B-measurement).
2. Keep negative control in fixture corpus under separate **regression** dashboard, not **incidence** dashboard.
3. Do not pursue EC-M01 unless a **deterministic salience signal** (not speaker guess) is identified and validated on protected replay.

---

## Related artifacts

| Document | Role |
|---|---|
| [BV6_residual_rc_inventory.md](BV6_residual_rc_inventory.md) | Event isolation |
| [BV6_residual_rc_trace.md](BV6_residual_rc_trace.md) | Causal path |
| [BV6_failure_classification.md](BV6_failure_classification.md) | Failure taxonomy |
| [BV6_elimination_feasibility.md](BV6_elimination_feasibility.md) | Options A/B/C/D |
| [BV6_roi_analysis.md](BV6_roi_analysis.md) | Cost/benefit |
| [BV5_follow_on_candidates.md](BV5_follow_on_candidates.md) | BV6 trigger context |
