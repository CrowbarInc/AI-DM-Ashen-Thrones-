# BV3D — Measurement Validation

**Date:** 2026-06-21  
**Scope:** Post-BV3D re-run of BV3A metrics and BV1B fallback incidence validation.

---

## Commands executed

```bash
python tools/bv3d_build_positive_control_corpus.py
python tools/bv3d_eligibility_report.py
python tools/bv3a_referential_clarity_metrics.py
python tools/bv1b_fallback_incidence_validation.py
```

Archives under `artifacts/bv3b_replay_refresh/` were **not** deleted or modified.

---

## Corpus delta (unfiltered → BV3D)

| Metric | BV3C unfiltered | BV3D filtered |
|---|---:|---:|
| FEM instances | 200 | **97** |
| Observe turns | 65 | **23** |
| Archive-contaminated observe (null upstream) | 44 | **0** |
| `upstream_repair_applied` | 0 | **1** |
| Eligible observe coverage | 0% | **100%** (1/1) |

---

## BV3A metrics (`artifacts/bv3a_referential_clarity_metrics.json`)

| Metric | Value |
|---|---:|
| Observe turn count | 23 |
| `upstream_repair_applied_count` | **1** |
| `local_substitution_applied_count` | 1 |
| `referential_clarity_replacement_applied_count` | 12 |
| Repair success on ambiguous turns | 9.1% (1/11) |
| `referential_clarity_hard_replacement` lineage | 12 |

### vs BV1B baseline (pre-BV3B, unfiltered 107-FEM era)

| Metric | Baseline | BV3D current | Delta |
|---|---:|---:|---:|
| Fallback incidence | 0.692 | **0.464** | −0.228 pp |
| Observe route rate | 0.955 | **0.522** | −0.433 pp |
| RC hard replacement | 38 | **12** | −26 |

Baseline source: `artifacts/golden_replay/bv1b_fallback_incidence_report.baseline.json` (intentionally pre-filter corpus for historical comparison).

---

## BV1B incidence (`artifacts/golden_replay/bv1b_fallback_incidence_report.json`)

| Metric | Value |
|---|---:|
| Canonical FEM instances | 97 |
| Fallback events | 45 |
| Fallback trigger rate | 0.464 |
| Measurement scope tag | BV3D |

Updated audit docs regenerated: `BV1B_fallback_incidence_validation.md`, baseline comparison, migration analysis, maintenance hotspots.

---

## Eligibility report (`artifacts/bv3d_eligibility_report.json`)

| Metric | Value |
|---|---:|
| `eligible_observe_turn_coverage` | **1.0** |
| `repair_activation_rate_all_observe` | 0.0435 (1/23 — dominated by ineligible replay shapes) |
| `replay_only_eligible_count` | **0** |
| `measurement_fixture_applied_count` | **1** |

---

## Validation checklist

| Check | Status |
|---|---|
| Archive contamination removed from scan | **PASS** — 3,722 archive files excluded |
| Nested `run_debug.json` FEM excluded | **PASS** |
| Terminal session_log FEM included | **PASS** — `emission_debug_lane._final_emission_meta` |
| Positive-control eligible case present | **PASS** — OBS-M001 |
| BV3A activation measurable | **PASS** — applied=1 on eligible=1 |
| Production behavior unchanged | **PASS** — read-side filters + fixture materialization only |

---

## Interpretation

BV3D metrics are now **internally consistent**: the one eligible observe turn (positive control) shows `upstream_repair_applied=true`. Replay-only corpus still shows **0 eligible** shapes — consistent with BV3C — but no longer confounds activation rate with pre-BV3A archive FEM or debug-lane misclassification.

---

## Artifacts

| Path | Role |
|---|---|
| `tools/bv3d_measurement_scope.py` | Scope policy |
| `artifacts/bv3d_measurement/positive_control_fixtures.jsonl` | Eligible case source |
| `artifacts/bv3d_eligibility_report.json` | Coverage authority |
| `artifacts/bv3a_referential_clarity_metrics.json` | BV3A incidence |
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | BV1B incidence |
