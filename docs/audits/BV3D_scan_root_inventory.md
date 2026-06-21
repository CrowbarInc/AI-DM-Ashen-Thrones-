# BV3D — Scan Root Inventory

**Date:** 2026-06-21  
**Purpose:** Inventory every artifact source consumed by BV3B refresh, BV3A metrics, and BV1B fallback incidence validation; classify for measurement hygiene.

---

## Consumers and default roots

| Consumer | Entry point | Pre-BV3D roots | Post-BV3D roots |
|---|---|---|---|
| **BV3B replay refresh** | `tools/bv3b_replay_corpus_refresh.py` | Writes `data/`, `artifacts/scene_canon_hygiene_runtime/`; archives to `artifacts/bv3b_replay_refresh/` | Unchanged (generation only) |
| **BV3A metrics** | `tools/bv3a_referential_clarity_metrics.py` | `DEFAULT_ROOTS` = `artifacts/`, `data/` (unfiltered) | `MEASUREMENT_ROOTS` via `tools/bv3d_measurement_scope.py` |
| **BV1B incidence** | `tools/bv1b_fallback_incidence_validation.py` | `DEFAULT_ROOTS` (unfiltered) | `MEASUREMENT_ROOTS` (BV3D filtered) |
| **Projection gap / drift** | `fallback_projection_gap_reality_audit.py`, `projection_drift_watch.py` | `DEFAULT_ROOTS` | **Unchanged** (advisory full-repo scan) |
| **BV3D eligibility** | `tools/bv3d_eligibility_report.py` | — | `MEASUREMENT_ROOTS` |

Implementation owner: `tools/bv3d_measurement_scope.py`.

---

## File-level inventory (repo scan)

| Metric | Count |
|---|---:|
| Legacy scan files (`artifacts/` + `data/`, `.json`/`.jsonl`) | 5,758 |
| BV3D measurement-included files | 1,990 |
| BV3D excluded files | 3,768 |

### Classification (legacy scan)

| Class | Files | Measurement scope |
|---|---:|---|
| **archive** | 3,722 | **excluded** — pre-refresh copies under `artifacts/bv3b_replay_refresh/` |
| **refreshed replay** | 1,921 | **included** — live `scene_canon_hygiene_runtime/`, `scenario_spine_validation/transcript.json` |
| **canonical replay** | 66 | **included** — `data/session_log.jsonl` and related |
| **derived artifact** | 45 | **excluded** — `artifacts/golden_replay/*` reports |
| **debug artifact** | 2 | **excluded** — `run_debug.json` and similar |
| **measurement fixture** | 2 | **included** — `artifacts/bv3d_measurement/` |

### Canonical FEM instances (turn-level, deduped)

| Scope | FEM count | Observe turns |
|---|---:|---:|
| Pre-BV3D unfiltered (BV3C) | 200 | 65 |
| Post-BV3D filtered | **97** | **23** |

---

## Source catalog

### Canonical replay

| Path | Role |
|---|---|
| `data/session_log.jsonl` | Primary live session transcript (post-BV3B refresh) |
| `data/session.json`, `data/world.json`, … | State only — no FEM (prefilter skips) |

### Refreshed replay

| Path | Role |
|---|---|
| `artifacts/scene_canon_hygiene_runtime/<uuid>/data/session_log.jsonl` | 30 BV3B hygiene batches (current code) |
| `artifacts/scenario_spine_validation/*/transcript.json` | Scenario-spine smoke transcripts |

### Archive (preserved, excluded from measurement)

| Path | Role |
|---|---|
| `artifacts/bv3b_replay_refresh/scene_canon_hygiene_runtime.*/*` | Pre-refresh hygiene tree copy (~3,722 files) |
| `artifacts/bv3b_replay_refresh/session_log.pre_refresh.jsonl` | Pre-BV3B canonical session log |
| `artifacts/bv3b_replay_refresh/corpus_refresh_manifest.json` | Refresh provenance (derived) |

### Debug artifact (preserved, excluded)

| Path | Role |
|---|---|
| `**/run_debug.json` | Multi-snapshot gate debug (retry FEM duplicates) |
| FEM under `.stage_diff_telemetry`, `.metadata.emission_debug` | Mid-pipeline snapshots |

### Measurement fixture (BV3D added)

| Path | Role |
|---|---|
| `artifacts/bv3d_measurement/positive_control_fixtures.jsonl` | Gate-finalized BV3A positive/negative controls |
| `artifacts/bv3d_measurement/positive_control_manifest.json` | Fixture provenance |

### Derived artifact (excluded)

| Path | Role |
|---|---|
| `artifacts/golden_replay/bv1b_fallback_incidence_report.json` | Incidence output |
| `artifacts/bv3a_referential_clarity_metrics.json` | BV3A output |
| `artifacts/golden_replay/projection_*.json` | Projection reports |

---

## Terminal FEM path (included)

API/session_log finalized emission is stored at:

```
$.gm_output.internal_state.emission_debug_lane._final_emission_meta
```

Pre-BV3D scanners treated `.emission_debug_lane` as debug-only and dropped these records. BV3D recognizes this as the **terminal finalized** path on turn records (distinct from `run_debug.json` retry snapshots).

---

## Related

- [BV3D_measurement_scope.md](BV3D_measurement_scope.md) — filter rules
- [BV3C_root_cause.md](BV3C_root_cause.md) — why unfiltered scan showed 0% activation
