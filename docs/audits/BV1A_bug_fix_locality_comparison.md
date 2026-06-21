# BV1A — Bug-Fix Locality Comparison (BR Baseline vs Post-BI)

**Date:** 2026-06-21
**Question:** Did bug fixes become cheaper after BI–BM?

## Executive answer

**Not demonstrable.** Post-BI corrective cohort remains **N = 0**. The BR median of **9 files per bug-fix commit** is unchanged because no new bug-fix commits exist after BI. BI–BM improved structural legibility (gate thinness, ownership maps, incidence measurement) but has not yet produced repository evidence that defect repair is more local.

**BV1A locality verdict:** **locality unchanged** (unobserved post-BI corrective sample).

## Aggregate bug-fix locality metrics

| Metric | BR baseline (pre-BI, N=11) | Post-BI (N=0) | Delta |
|---|---:|---:|---:|
| Median files touched | 9.0 | — | — |
| Mean files touched | 80 | — | — |
| P90 files touched | 216.0 | — | — |
| Maximum files touched | 538 | — | — |

## Concentration metrics (BR BRL1 vs post-BI)

| Metric | BR baseline | Current (post-BI) | Delta |
|---|---:|---:|---:|
| Hotspot top-cluster share (bug-fix production touches) | 13.85% (`data/session.json`) | Not measurable (0 bug fixes) | — |
| Bug-fix maintenance top-5 file share | 3.98% | Not measurable | — |
| Bug-fix maintenance top-file share | 1.02% | Not measurable | — |
| Ownership concentration (gate historical bug-fix touches) | 3 touches on `game/final_emission_gate.py` | 0 post-BI bug-fix touches | Unchanged / unobserved |

BR concentration sources: `artifacts/bug_fix_locality_report.md`, `docs/BRL2_bug_fix_locality_regression_guard.md`.

## Subsystem breakdown (bug-fix commits only)

Post-BI bug-fix subsystem metrics are **not measurable** (N = 0). Pre-BI BR cohort breakdown:

| subsystem | path touches (11 commits) | commits touching | median files when touching |
|---|---:|---:|---:|
| replay | 0 | 0 | 0.0 |
| fallback | 1 | 1 | 1.0 |
| attribution | 0 | 0 | 0.0 |
| final emission | 6 | 3 | 1.0 |
| speaker finalize | 0 | 0 | 0.0 |
| tests | 24 | 9 | 2.0 |

**Pre-BI pattern:** Bug fixes concentrated in runtime data fixtures (`data/session.json`, `data/combat.json`) and opening/gate seams (`game/final_emission_gate.py`, opening fallback paths). Replay and attribution subsystems had **zero** dedicated bug-fix touches in the BR cohort.

**Post-BI structural shift (proxy from architecture/refactor commits):** Final-emission modules, fallback routers, replay projection helpers, and governance test facades absorbed planned touches — consistent with **REDISTRIBUTED_COST**, not cheaper corrective locality.

## Interpretation

| Criterion | Result |
|---|---|
| Median bug-fix files decreased | **Not observed** — no post-BI bug fixes |
| Hotspot concentration decreased | **Not observed** for corrective cohort |
| Ownership concentration reduced for defect repair | **Not observed** — gate historical cost persists; new hubs unprobed |

## Evidence

| Source | Role |
|---|---|
| `docs/reports/BR_bug_fix_locality_measurement.md` | Pre-BI baseline establishment |
| `docs/audits/BV1_bug_fix_locality_validation.md` | BV1 prior pass (same N=0 finding) |
| `artifacts/bv1_measurements.json` | Post-BI cohort machine data |
