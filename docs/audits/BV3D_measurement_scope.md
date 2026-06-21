# BV3D — Measurement Scope

**Date:** 2026-06-21  
**Policy ID:** BV3D  
**Owner module:** `tools/bv3d_measurement_scope.py`  
**Applied to:** `bv3a_referential_clarity_metrics.py`, `bv1b_fallback_incidence_validation.py`, `bv3d_eligibility_report.py`

---

## Objective

Measure BV3A behavior on **current-code, terminal finalized FEM** only. Archives and debug snapshots remain on disk but are excluded from incidence denominators.

---

## Included roots

```
data/
artifacts/scene_canon_hygiene_runtime/
artifacts/scenario_spine_validation/
artifacts/bv3d_measurement/
```

---

## Exclusion rules

| Rule | Rationale |
|---|---|
| Path prefix `artifacts/bv3b_replay_refresh/` | Pre-refresh archive; pre-BV3A FEM |
| Filename `run_debug.json` | Retry/stage FEM duplicates per turn |
| Filename `session_log.pre_refresh.jsonl` | Pre-BV3B baseline log |
| `artifacts/golden_replay/*.json` / `*.md` | Derived incidence/projection outputs |
| Listed derived metric filenames | Self-referential scan noise |
| FEM context not matching terminal suffixes | Mid-pipeline / layer-debug snapshots |
| FEM context containing `.stage_diff_telemetry`, `.metadata.emission_debug`, … | Non-terminal telemetry |

**Archives are not deleted** — exclusion is read-side only.

---

## Terminal FEM acceptance

A FEM dict is counted when its JSON path ends with one of:

| Suffix |
|---|
| `.gm_output._final_emission_meta` |
| `.gm_output.final_emission_meta` |
| `.gm_output.internal_state.emission_debug_lane._final_emission_meta` |
| `.chat_response.gm_output.internal_state.emission_debug_lane._final_emission_meta` |
| `._final_emission_meta` / `.final_emission_meta` (measurement fixtures) |

Rejected: any other `_final_emission_meta` nested under stage telemetry or layer debug blobs.

---

## Measurement fixture layer

`tools/bv3d_build_positive_control_corpus.py` materializes gate-finalized rows from BV3A unit-test shapes into:

`artifacts/bv3d_measurement/positive_control_fixtures.jsonl`

This supplies **known-eligible** observe turns so activation rate is measurable even when live replay lacks contract-shaped candidates.

---

## API surface

| Function | Purpose |
|---|---|
| `scan_measurement_fem_turns()` | Filtered turn rows for incidence |
| `iter_measurement_artifact_files()` | File list after path exclusions |
| `is_canonical_finalized_fem_context()` | Terminal FEM path gate |
| `classify_artifact_path()` | Audit classification |

Legacy unfiltered scan remains available via `scan_canonical_fem_turns(legacy_unfiltered=True)` in BV1B for historical comparison.

---

## Before / after impact

| Metric | Unfiltered (BV3C) | BV3D filtered |
|---|---:|---:|
| FEM instances | 200 | **97** |
| Observe turns | 65 | **23** |
| `upstream_repair_applied` | 0 | **1** |
| Eligible observe coverage | 0% | **100%** (1/1 eligible) |

---

## Commands

```bash
python tools/bv3d_build_positive_control_corpus.py
python tools/bv3d_eligibility_report.py
python tools/bv3a_referential_clarity_metrics.py
python tools/bv1b_fallback_incidence_validation.py
```
