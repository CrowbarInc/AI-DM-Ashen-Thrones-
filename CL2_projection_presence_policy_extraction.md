# CL2 Projection Presence Policy Extraction

## Files changed

- `tests/helpers/golden_replay_projection_presence.py`
  - New focused helper for raw/normalized presence, missing-source classification, unavailable routing, and protected-path representation coverage.
- `tests/helpers/golden_replay_projection_extractors.py`
  - Removed embedded presence/unavailable implementation.
  - Kept compatibility imports/wrappers so existing imports from this module still work.
- `tests/test_golden_replay_projection_presence_integration.py`
  - Added focused CL2 locks for missing-source labels and parent trace-container unavailable coverage.
- `tests/test_golden_replay_projection_modules.py`
  - Added the new presence helper to the projection module import-graph cycle check.

## Functions moved or re-exported

Moved to `tests.helpers.golden_replay_projection_presence`:

- `_ProjectionStatus`
- `_SupportingRawPresenceSpec`
- `_TRACE_CONTAINER_RAW_PRESENCE`
- `_TRACE_CONTAINER_UNAVAILABLE_KEYS`
- `_SUPPORTING_RAW_PRESENCE_SPECS`
- `lookup_observation_path`
- `_unavailable_paths`
- `protected_path_covered_by_unavailable`
- `protected_path_is_represented_in_observed_turn`
- `protected_path_representation_errors`
- `_has_path`
- `_raw_presence_key_for_spec`
- `_raw_presence_for_protected_spec`
- `_normalized_presence_for_protected_spec`
- `_missing_source_by_field_from_presence`
- `_unavailable_paths_for_projection`
- `_build_projection_status`

Still import-compatible from `tests.helpers.golden_replay_projection_extractors`:

- `_ProjectionStatus`
- `_TRACE_CONTAINER_RAW_PRESENCE`
- `_TRACE_CONTAINER_UNAVAILABLE_KEYS`
- `_missing_source_by_field_from_presence`
- `lookup_observation_path`
- `protected_path_covered_by_unavailable`
- `protected_path_is_represented_in_observed_turn`
- `protected_path_representation_errors`
- `_unavailable_paths_for_projection`
- `_build_projection_status`
- `_fem_has_any_key` and `_fem_dual_fallback_family_present` remain re-exported for existing CF3 imports.

## Behavior compatibility notes

- No protected replay fields were renamed.
- `project_turn_observation` call shape and output semantics are unchanged.
- Unavailable routing keeps the same sorted set behavior and labels.
- Missing-source labels remain:
  - `runtime_missing_raw_absent`
  - `projection_missing_raw_present`
  - `normalized_view_missing_raw_present`
- Dotted trace paths remain covered by parent unavailable entries such as `trace.canonical_entry`.
- Sparse-turn unavailable output remains locked by the existing presence integration test.
- Runtime files were not changed.

## Validation commands run and results

Initial requested command failed because `python` is not on PATH in this PowerShell session:

```powershell
python -m pytest tests/test_cf2_protected_field_routing.py tests/test_cf3_raw_normalized_fem_field_matrix.py tests/test_golden_replay_projection_presence_integration.py -q
```

Successful validation using the bundled Codex runtime Python with repo venv packages:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_cf2_protected_field_routing.py tests\\test_cf3_raw_normalized_fem_field_matrix.py tests\\test_golden_replay_projection_presence_integration.py -q
```

Result: `107 passed`.

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection.py tests\\test_golden_replay_projection_metadata.py -q
```

Result: `9 passed`.

Additional module-boundary sanity check:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection_modules.py -q
```

Result: `44 passed`.

## Remaining presence/unavailable policy in extractor module

- `_PROTECTED_EXTRACTION_SPECS` still carries the CL1 machine-readable routing metadata (`raw_presence`, `normalized_presence`, `unavailable_key`, `trace_container`).
- `_unavailable_paths_for_projection` and `_build_projection_status` remain as compatibility wrappers that inject `_PROTECTED_EXTRACTION_SPECS` into the presence policy module.
- Presence constants are imported/re-exported for existing tests and helper contracts.

## Recommended next block

CL3 follow-up was to realign diagnostic ownership strings that still named the extractor as the conceptual owner of presence/unavailable policy, while preserving compatibility imports until downstream churn settled.

CL3 status note (2026-06-26): diagnostic ownership labels were realigned; extractor compatibility wrappers remain intentionally available.
