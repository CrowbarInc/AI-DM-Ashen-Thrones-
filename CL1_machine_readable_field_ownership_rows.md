# CL1 - Machine-Readable Field Ownership Rows

Date: 2026-06-26

## Summary

CL1 strengthened the protected replay field routing contract without changing projected replay output or runtime behavior. Each protected field row now carries machine-readable ownership, source, default, unavailable, raw-presence, normalized-presence, and first-line test metadata.

## Files Changed

- `tests/helpers/protected_field_routing_contract.py`
- `tests/test_cf2_protected_field_routing.py`
- `docs/audits/CF2_protected_field_source_default_matrix.md`
- `CL1_machine_readable_field_ownership_rows.md`

## Ownership/Routing Metadata Added

`ProtectedFieldRoutingRow` now includes these explicit contract fields:

- `field_name`
- `source_family`
- `field_owner_group`
- `default_behavior`
- `unavailable_behavior`
- `unavailable_key`
- `raw_presence_expectation`
- `raw_presence_key`
- `normalized_presence_expectation`
- `normalized_presence_key`

The row still preserves the existing fields such as `field`, `source_path`, `normalized_source`, `default`, `unavailable_rule`, `missing_source_rule`, `drift_bucket`, `classification`, `projection_owner`, and `test_owner`.

The new values are derived from the existing protected extraction specs and schema defaults:

- `_PROTECTED_EXTRACTION_SPECS` supplies extraction source, FEM keys, raw-presence mode, normalized-presence tracking, trace container, and unavailable key.
- `protected_observation_default_row()` supplies flat schema defaults.
- `_TRACE_CONTAINER_UNAVAILABLE_KEYS` supplies trace-container unavailable behavior.
- Existing source and test-owner maps supply the first-line contract owner where ownership is already known.

## Tests Added Or Updated

`tests/test_cf2_protected_field_routing.py` now asserts:

- every protected field row has non-empty machine-readable ownership/source metadata;
- default behavior is one of the expected explicit modes;
- unavailable behavior is one of the expected explicit modes;
- raw and normalized presence expectations include machine-readable keys when tracked;
- unavailable keys are present only for projected-none or trace-container unavailable rows;
- known ambiguous field families (`fallback_family`, `opening_fallback_owner_bucket`, `selected_speaker_id`, trace leaves, response-type fields, upstream-prepared fields) have declared owner groups.

## Validation

Initial command:

```powershell
& 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_cf2_protected_field_routing.py tests\test_golden_replay_projection_presence_integration.py -q
```

Result: failed before collection because the bundled Python environment did not have `pytest` importable.

Successful command:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_cf2_protected_field_routing.py tests\test_golden_replay_projection_presence_integration.py -q
```

Result: `56 passed`.

Additional validation after the CF2 audit doc update:

```powershell
$env:PYTHONPATH='.\.venv\Lib\site-packages'; & 'C:\Users\Master Mandalcio\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_golden_replay_projection_registry.py tests\test_golden_replay_projection_manifest.py -q
```

Result: `6 passed`.

## Ambiguous Ownership

No protected field is missing an owner group after CL1. The intentionally compatibility-driven fields remain worth watching:

- `fallback_family`: owned by replay fallback-family projection because it collapses runtime `fallback_family_used`, `realization_fallback_family`, and lineage bridge inference into one protected field.
- `selected_speaker_id`: owned by replay speaker projection because it preserves multi-source compatibility ordering.
- `opening_fallback_owner_bucket`: owned by owner-bucket read views because the value is derived from FEM metadata rather than read as a raw protected key.
- dotted `trace.*` fields: owned by replay trace projection because unavailable handling operates at the parent trace-container level.

## Recommended Next Block

Proceed with CL2: extract raw/normalized presence, `missing_source_by_field`, and unavailable routing into a focused projection presence policy helper behind the existing facade. The new CL1 metadata gives that split a local contract to preserve behavior.
