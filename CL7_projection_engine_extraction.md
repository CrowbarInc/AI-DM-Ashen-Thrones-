# CL7 Projection Engine Extraction

## Files Changed

- `tests/helpers/golden_replay_projection_engine.py` created as the protected field projection execution owner.
- `tests/helpers/golden_replay_projection_extractors.py` now imports and re-exports engine symbols while retaining orchestration/compatibility helpers.
- `tests/helpers/fem_normalization_contract.py` now identifies FEM flat projection execution as engine-owned.
- `tests/test_golden_replay_projection_engine.py` added focused CL7 parity and compatibility tests.
- `tests/test_golden_replay_projection_modules.py` now includes the engine module in projection module boundary checks.

Note: the worktree already contained CL1-CL6 and audit edits before CL7. Those were left intact.

## Engine Functions Moved

- `_extract_fem_flat_observed_fields`
- `_extract_sanitizer_trace_flat_observed_fields`
- `_extract_sanitizer_lineage_observed_fields`
- `_observed_fem_flat_values`
- `_sanitizer_lineage_field`
- `_resolve_route_kind`
- `_HANDLED_FLAT_PROTECTED_SOURCES`
- `_TRACE_NEST_PROTECTED_SOURCES`
- `_validate_protected_projection_sources`
- `_project_flat_protected_observed_fields`

## Compatibility Re-exports Retained

`tests.helpers.golden_replay_projection_extractors` still exposes the moved engine symbols:

- `_extract_fem_flat_observed_fields`
- `_extract_sanitizer_trace_flat_observed_fields`
- `_extract_sanitizer_lineage_observed_fields`
- `_observed_fem_flat_values`
- `_sanitizer_lineage_field`
- `_resolve_route_kind`
- `_HANDLED_FLAT_PROTECTED_SOURCES`
- `_TRACE_NEST_PROTECTED_SOURCES`
- `_validate_protected_projection_sources`
- `_project_flat_protected_observed_fields`

Existing imports from the extractor module continue to function.

## Responsibility Breakdown

Before:

- `golden_replay_projection_extractors.py` owned registry compatibility, presence compatibility wrappers, payload trace helpers, runtime lineage helpers, and protected flat projection execution.
- Field value assembly, extraction dispatch, and projection source validation lived beside orchestration helpers.

After:

- `golden_replay_projection_engine.py` owns protected field projection execution over the registry:
  flat FEM extraction, sanitizer trace extraction, sanitizer lineage extraction, route-kind resolution, source-handler validation, and flat protected observed-field assembly.
- `golden_replay_projection_registry.py` continues to own registry data and derived extractor tuples.
- `golden_replay_projection_presence.py` continues to own presence/unavailable/missing-source policy.
- `golden_replay_projection_semantic.py` continues to own semantic mutation projection.
- `golden_replay_projection_extractors.py` remains a compatibility/orchestration facade for older imports and non-engine payload helpers.

## Remaining Extractor Responsibilities

`golden_replay_projection_extractors.py` still owns:

- Protected classifier evidence derivation validation.
- Sanitizer debug count derivation.
- Response-delta echo overlap banding.
- Trace lookup from payload or snapshot.
- Nested mapping/list search helpers.
- Runtime lineage event extraction from payload or FEM.
- Presence policy compatibility wrappers.
- Compatibility re-exports for registry, presence, semantic, and engine symbols.

## Validation

- `python -m pytest tests/test_golden_replay_projection_engine.py -q`
  - Passed: `4 passed`
- `python -m pytest tests/test_golden_replay_projection.py tests/test_golden_replay_projection_metadata.py tests/test_golden_replay_projection_registry.py -q`
  - Passed: `17 passed`
- `python -m pytest tests/test_golden_replay_projection_modules.py -q`
  - Passed: `44 passed`
- Adjacent compatibility consumers:
  - `python -m pytest tests/test_cf1_route_and_trace_precedence.py -q`
  - Passed: `10 passed`
  - `python -m pytest tests/test_cf3_raw_normalized_fem_field_matrix.py -q`
  - Passed: `47 passed`
- Static compile:
  - `python -m py_compile tests/helpers/golden_replay_projection_engine.py tests/helpers/golden_replay_projection_extractors.py tests/test_golden_replay_projection_engine.py tests/test_golden_replay_projection_modules.py tests/helpers/fem_normalization_contract.py`
  - Passed

All pytest commands were run with the bundled workspace Python executable and `PYTHONPATH=.\\.venv\\Lib\\site-packages`.

## Next Block Recommendation

CL8 should target the remaining payload/orchestration helpers in `golden_replay_projection_extractors.py`, especially trace lookup, nested payload search, and runtime lineage extraction. Those helpers are now distinct from registry, presence, semantic, and protected field projection engine ownership.
