# CE5 — Acceptance Projection Ownership Split Summary

## Summary

Split the 1,756-line golden replay acceptance projection monolith into five focused helper modules plus a compatibility facade. `tests/helpers/golden_replay_projection.py` remains the public import surface and still owns `project_turn_observation` orchestration. Protected observation registry contents, field order, manifest rendered text, and projection output are unchanged.

## Files Changed

| File | Change |
|---|---|
| `tests/helpers/golden_replay_projection_fields.py` | **Added** — protected field registry, drift buckets, classifier evidence derivation, text/scaffold helpers |
| `tests/helpers/golden_replay_projection_manifest.py` | **Added** — manifest section render/extract/parity |
| `tests/helpers/golden_replay_projection_extractors.py` | **Added** — extraction registry, payload/trace/sanitizer projection, presence routing |
| `tests/helpers/golden_replay_projection_fallbacks.py` | **Added** — dual fallback-family read-side projection |
| `tests/helpers/golden_replay_projection_speaker.py` | **Added** — BX2 speaker observation read + parity projection |
| `tests/helpers/golden_replay_projection.py` | **Refactored** — compatibility facade + `project_turn_observation` orchestration |
| `tests/test_golden_replay_projection_modules.py` | **Added** — public API, registry/manifest parity, import-cycle contract tests |
| `tools/ce5_split_golden_replay_projection.py` | **Added** — reproducible line-range extraction script |

Local reference only: `tests/helpers/golden_replay_projection.py.bak`

## Responsibility Map

| Module | Responsibility moved |
|---|---|
| `golden_replay_projection_fields.py` | `ProtectedObservationField`, `PROTECTED_OBSERVATION_FIELDS`, drift bucket sets/maps, default rows, classifier evidence exclusions/derivation, scaffold/text helpers, shared `_first_present` / `MISSING` |
| `golden_replay_projection_manifest.py` | Manifest markers, row/count derivation, render/extract/current checks, registry parity errors |
| `golden_replay_projection_extractors.py` | Extraction specs/registry validation, FEM/sanitizer/trace extractors, nested payload search, presence/unavailable routing, flat protected projection, semantic mutation summary |
| `golden_replay_projection_fallbacks.py` | `REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS`, diegetic-first `project_replay_fallback_family_from_fem`, neutral-reply bridge family, `_resolve_fallback_family` |
| `golden_replay_projection_speaker.py` | `SpeakerProjectionParityStatus`, `read_final_speaker_observation_for_replay`, `project_speaker_projection_parity`, selected-speaker resolution |
| `golden_replay_projection.py` (facade) | Public re-exports, `project_turn_observation` turn orchestration |

## Compatibility Preserved

| Dimension | Changed? |
|---|---|
| `PROTECTED_OBSERVATION_FIELDS` path order/content | **No** — 41 fields, identical order and drift buckets vs pre-CE5 backup |
| Manifest rendered text | **No** — `render_protected_observation_manifest_section()` byte-identical vs backup |
| Projection output | **No** — existing projection/fallback/speaker tests pass unchanged |
| Drift bucket semantics | **No** |
| Public imports from `golden_replay_projection.py` | **No** — facade re-exports/delegates; no import-site churn |
| Fixtures / expected outputs | **No** rewrites |

Import graph among focused modules is acyclic (`fields` → `fallbacks`/`manifest`/`speaker` → `extractors` → facade). Focused modules do not import the facade.

## LOC / Function Comparison

| File | LOC | Functions |
|---|---:|---:|
| Pre-CE5 monolith (`golden_replay_projection.py.bak`) | 1,756 | 70 |
| `golden_replay_projection.py` (facade) | 301 | 1 |
| `golden_replay_projection_fields.py` | 198 | 15 |
| `golden_replay_projection_manifest.py` | 151 | 6 |
| `golden_replay_projection_extractors.py` | 978 | 39 |
| `golden_replay_projection_fallbacks.py` | 76 | 6 |
| `golden_replay_projection_speaker.py` | 154 | 4 |
| **Focused modules total** | **1,557** | **71** |
| **Post-CE5 total (focused + facade)** | **1,858** | **72** |

Largest implementation module is now **978 LOC** (extractors) vs **1,756 LOC** monolith — **44% reduction** in max single-file acceptance-projection concentration. Facade stays at **301 LOC** for orchestration and re-exports.

## Manifest / Protected-Field Behavior Preservation

- `PROTECTED_OBSERVATION_FIELDS`: 41 paths; structural (39) + semantic (2); order verified against backup in `test_protected_observation_fields_order_and_content_unchanged_from_backup`.
- Manifest section: 2,927 characters rendered; identical to pre-split backup (`test_render_protected_observation_manifest_section_unchanged_from_backup`).
- Registry/extraction parity validations (`_validate_protected_extraction_registry`, `_validate_protected_classifier_evidence_derivation`, `_validate_protected_projection_sources`) still run at import time in focused modules.

## Validation Results

```text
python -m pytest tests/test_golden_replay_projection.py \
  tests/test_golden_replay_fallback_projection.py \
  tests/test_golden_replay_fallback_opening_projection.py \
  tests/test_golden_replay_fallback_sealed_projection.py \
  tests/test_golden_replay_fallback_visibility_projection.py \
  tests/test_golden_replay_fallback_upstream_projection.py \
  tests/test_golden_replay_fallback_sanitizer_projection.py \
  tests/test_golden_replay_fallback_upstream_fast_projection.py \
  tests/test_golden_replay_fallback_long_session_summary.py \
  tests/test_golden_replay_fallback_acceptance_matrix.py \
  tests/test_golden_replay_helper_contracts.py \
  tests/test_replay_maintenance_metrics.py \
  tests/test_failure_dashboard_recurrence.py \
  tests/test_golden_replay_projection_modules.py -q --tb=line

# 143 passed
```

## Known Baseline Issues

**Unchanged** — not caused by CE5:

```text
python -m pytest tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report -q --tb=line

# FAILED — IndexError: list index out of range (pre-existing protected-bridge baseline)
```

## Remaining Concentration Assessment

| Area | Assessment |
|---|---|
| `golden_replay_projection_extractors.py` | **Moderate** — largest focused module (978 LOC); cohesive payload/extraction ownership; candidate for a future CE pass only if extraction sub-families (sanitizer vs trace vs presence) need separate maintenance owners |
| `golden_replay_projection.py` (facade) | **Low–moderate** — 301 LOC orchestration + re-exports; appropriate as stable public surface |
| `golden_replay_projection_fields.py` | **Low** — canonical registry authority isolated |
| `golden_replay_projection_manifest.py` | **Low** — manifest-only |
| `golden_replay_projection_fallbacks.py` | **Low** — dual-family + bridge fallback read path |
| `golden_replay_projection_speaker.py` | **Low** — speaker parity slice |
| Import duplication | **Acceptable** — facade re-exports preserve all existing import sites without churn |

Overall replay maintenance cost for acceptance projection is improved: registry, manifest, extraction, fallback, and speaker concerns now have explicit module ownership while CI acceptance authority remains at `tests/helpers/golden_replay_projection.py`.
