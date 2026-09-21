# CE4 — Fallback Projection Test Decomposition Summary

## Summary

Decomposed the 1,251-line fallback projection monolith into eight focused test modules plus a redirect stub. Tests were moved verbatim with unchanged assertions, fixtures, imports, parametrize matrices, and markers. Shared lineage event selectors were extracted to a small helper module used by modules that previously shared private `_fallback_selected_event` / `_mutation_event` helpers.

## Files Changed

| File | Change |
|---|---|
| `tests/test_golden_replay_fallback_projection.py` | Replaced monolith with redirect stub (21 LOC) |
| `tests/test_golden_replay_fallback_opening_projection.py` | **Added** — opening/sealed-gate opening projection |
| `tests/test_golden_replay_fallback_sealed_projection.py` | **Added** — sealed and strict-social sealed projection |
| `tests/test_golden_replay_fallback_visibility_projection.py` | **Added** — visibility/referential hard-replacement projection |
| `tests/test_golden_replay_fallback_upstream_projection.py` | **Added** — upstream prepared emission telemetry |
| `tests/test_golden_replay_fallback_sanitizer_projection.py` | **Added** — sanitizer empty/strict-social projection |
| `tests/test_golden_replay_fallback_upstream_fast_projection.py` | **Added** — upstream-fast split-owner projection |
| `tests/test_golden_replay_fallback_long_session_summary.py` | **Added** — long-session lineage/escalation summaries |
| `tests/test_golden_replay_fallback_acceptance_matrix.py` | **Added** — split-owner acceptance matrix alignment |
| `tests/helpers/golden_replay_fallback_projection_helpers.py` | **Added** — shared `fallback_selected_event` / `mutation_event` selectors |
| `tools/ce4_decompose_fallback_projection_tests.py` | **Added** — reproducible line-range extraction script |

Local reference only: `tests/test_golden_replay_fallback_projection_monolith.py.bak`

## Responsibility Map

| Module | Responsibility | Tests moved |
|---|---|---|
| `test_golden_replay_fallback_opening_projection.py` | Opening owner buckets, lineage bundle preference, neutral speaker grounding, fail-closed opening, opening split-owner trifecta, opening classifier bridge | 6 functions (8 parametrized cases) |
| `test_golden_replay_fallback_sealed_projection.py` | Sealed/strict-social owner buckets, sealed-family replacement trifecta, sealed classifier bridge | 4 functions (10 parametrized cases) |
| `test_golden_replay_fallback_visibility_projection.py` | Visibility evidence, hard-replacement buckets, visibility-family trifecta, referential local substitution, visibility classifier bridge | 5 functions (9 parametrized cases) |
| `test_golden_replay_fallback_upstream_projection.py` | Valid/rejected/absent upstream prepared emission telemetry, malformed reject-reason drift classification | 4 functions (6 parametrized cases) |
| `test_golden_replay_fallback_sanitizer_projection.py` | Sanitizer empty fallback, strict-social sanitizer split, sanitizer trifecta, sanitizer classifier bridge | 4 functions |
| `test_golden_replay_fallback_upstream_fast_projection.py` | Upstream-fast split-owner trifecta, upstream-fast classifier bridge | 2 functions |
| `test_golden_replay_fallback_long_session_summary.py` | Long-session lineage stability (sanitizer/upstream-fast, opening, sealed) and scene-action speaker-absence escalation | 4 functions |
| `test_golden_replay_fallback_acceptance_matrix.py` | BU15/BU16 split-owner acceptance matrix golden-replay vs production FEM alignment | 2 functions |
| `test_golden_replay_fallback_projection.py` | Redirect stub documenting focused owners | 1 stub function |

## LOC / Function Comparison

| File | LOC | Test functions |
|---|---:|---:|
| Pre-CE4 monolith | 1,251 | 31 |
| `test_golden_replay_fallback_projection.py` (stub) | 21 | 1 |
| `test_golden_replay_fallback_opening_projection.py` | 253 | 6 |
| `test_golden_replay_fallback_sealed_projection.py` | 214 | 4 |
| `test_golden_replay_fallback_visibility_projection.py` | 278 | 5 |
| `test_golden_replay_fallback_upstream_projection.py` | 232 | 4 |
| `test_golden_replay_fallback_sanitizer_projection.py` | 249 | 4 |
| `test_golden_replay_fallback_upstream_fast_projection.py` | 134 | 2 |
| `test_golden_replay_fallback_long_session_summary.py` | 312 | 4 |
| `test_golden_replay_fallback_acceptance_matrix.py` | 96 | 2 |
| `golden_replay_fallback_projection_helpers.py` | 16 | 0 |
| **Focused modules total** | **1,758** | **31** (+ 1 stub) |

Largest focused module is now **312 LOC** (long-session summaries) vs **1,251 LOC** monolith — **75% reduction** in max single-file test concentration.

## Behavior Preservation

| Dimension | Changed? |
|---|---|
| Assertions | **No** |
| Fixtures / parametrize matrices | **No** |
| Expected values | **No** |
| Protected field semantics | **No** |
| Projection logic under test | **No** |
| Helper public APIs | **No** |
| Total fallback projection test cases (incl. parametrize) | **No** — 44 cases + 1 redirect stub |

## Validation Results

```text
python -m pytest tests/test_golden_replay_fallback_projection.py \
  tests/test_golden_replay_fallback_opening_projection.py \
  tests/test_golden_replay_fallback_sealed_projection.py \
  tests/test_golden_replay_fallback_visibility_projection.py \
  tests/test_golden_replay_fallback_upstream_projection.py \
  tests/test_golden_replay_fallback_sanitizer_projection.py \
  tests/test_golden_replay_fallback_upstream_fast_projection.py \
  tests/test_golden_replay_fallback_long_session_summary.py \
  tests/test_golden_replay_fallback_acceptance_matrix.py \
  tests/test_golden_replay_projection.py \
  tests/test_golden_replay_helper_contracts.py \
  tests/test_replay_maintenance_metrics.py -q --tb=no

# 94 passed
```

Fallback-only suite: **44 passed** (31 original test functions expanded by parametrization, plus redirect stub).

## Known Baseline Issues

**Unchanged** — not caused by CE4:

```text
python -m pytest tests/test_golden_replay_protected_bridge.py::test_protected_golden_assertion_failure_records_canonical_report -q --tb=line

# FAILED — IndexError: list index out of range (pre-existing protected-bridge baseline)
```

## Remaining Concentration Assessment

| Area | Assessment |
|---|---|
| `test_golden_replay_fallback_projection.py` | **Low** — redirect stub only |
| `test_golden_replay_fallback_long_session_summary.py` | **Moderate** — largest focused module (312 LOC); still cohesive (summary/lineage only) |
| `test_golden_replay_fallback_visibility_projection.py` | **Moderate** — 278 LOC; visibility/referential family |
| Other focused modules | **Low–moderate** — 134–253 LOC each, single fallback family ownership |
| Import duplication | **Acceptable tradeoff** — each module retains the original import block verbatim to avoid behavior drift; could be trimmed in a future pass if maintenance touch rises |

Overall replay maintenance cost for fallback projection tests is improved: ownership is aligned to fallback families (opening, sealed, visibility, upstream, sanitizer, upstream-fast, long-session summaries, acceptance matrix), and the historical monolith entry point now redirects to focused files.
