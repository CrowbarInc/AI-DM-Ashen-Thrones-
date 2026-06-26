# CL6 Protected Extraction Registry Extraction

## Files Changed

- `tests/helpers/golden_replay_projection_registry.py` created as the protected extraction registry owner.
- `tests/helpers/golden_replay_projection_extractors.py` now consumes and re-exports registry symbols while retaining projection execution.
- `tests/helpers/fem_normalization_contract.py` now reads `_PROTECTED_EXTRACTION_SPECS` from the registry owner.
- `tests/helpers/protected_field_routing_contract.py` now reads registry specs from the registry owner and reports registry ownership.
- `tests/helpers/trace_nest_contract.py` now reads registry specs from the registry owner.
- `tests/test_golden_replay_projection_registry.py` adds CL6 registry parity, ordering, uniqueness, and compatibility-import tests.
- `tests/test_golden_replay_projection_modules.py` includes the registry module in projection module boundary checks.
- `tests/test_cf2_protected_field_routing.py` updates the expected registry-owner label.

Note: the worktree already contained unrelated CL1-CL5/audit edits before CL6. Those were not reverted.

## Registry Symbols Moved

- `_FlatObservedFieldExtractor`
- `_SanitizerLineageObservedExtractor`
- `_ProtectedExtractionSpec`
- `_flat_extractor_source_keys`
- `_protected_extraction_spec`
- `_PROTECTED_EXTRACTION_SPECS`
- `_validate_protected_extraction_registry`
- `protected_observation_extraction_registry`
- `protected_observation_extraction_source_by_path`
- `_fem_flat_extractors_from_registry`
- `_sanitizer_trace_extractors_from_registry`
- `_sanitizer_lineage_extractors_from_registry`
- `_FEM_FLAT_OBSERVED_EXTRACTORS`
- `_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS`
- `_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS`

## Compatibility Re-exports Retained

`tests.helpers.golden_replay_projection_extractors` still exposes:

- `_PROTECTED_EXTRACTION_SPECS`
- `_ProtectedExtractionSpec`
- `_FlatObservedFieldExtractor`
- `_SanitizerLineageObservedExtractor`
- `_flat_extractor_source_keys`
- `protected_observation_extraction_registry`
- `protected_observation_extraction_source_by_path`
- `MISSING`

## Responsibility Summary

Before:

- `golden_replay_projection_extractors.py` owned both protected extraction registry data and projection execution.
- Registry metadata, extractor tuple construction, lookup helpers, and payload projection changed in the same module.

After:

- `golden_replay_projection_registry.py` owns protected extraction specs, registry validation, ordering, and derived extractor registration tuples.
- `golden_replay_projection_extractors.py` owns projection execution over the registry.
- Diagnostic contracts can import registry data from the registry owner while old extractor imports continue to work.

## Remaining Extractor Responsibilities

`golden_replay_projection_extractors.py` still owns:

- FEM and sanitizer observed-field extraction execution.
- Sanitizer lineage fallback execution.
- FEM flat observed-value shaping.
- Classifier evidence derivation validation against the registry.
- Payload/snapshot trace lookup helpers.
- Runtime lineage event extraction from payload or FEM.
- Route-kind resolution.
- Presence-policy compatibility wrappers.
- Projection source-handler validation.
- Flat protected observed-field projection.
- Trace observed-field assembly and other payload projection helpers below the registry boundary.

## Validation

- `python -m pytest tests/test_golden_replay_projection_registry.py tests/test_golden_replay_projection.py tests/test_golden_replay_projection_metadata.py -q`
  - Passed: `17 passed`
- `python -m pytest tests/test_golden_replay_projection_modules.py -q`
  - Passed: `44 passed`
- Adjacent registry-specific check:
  - `python -m pytest tests/test_protected_replay_registry.py -q`
  - Passed: `8 passed`

All commands were run with the bundled workspace Python executable and `PYTHONPATH=.\\.venv\\Lib\\site-packages`.

## Next Block Recommendation

CL7 should target the remaining projection execution concentration inside `golden_replay_projection_extractors.py`: separate trace assembly/runtime-lineage helper execution from flat protected-field projection, keeping the registry module stable and read-only.
