# CL3 Diagnostic Ownership String Realignment

## Files changed

- `tests/helpers/protected_field_routing_contract.py`
- `tests/helpers/fem_normalization_contract.py`
- `tests/helpers/trace_nest_contract.py`
- `tests/helpers/golden_replay_projection_extractors.py`
- `tests/test_cf2_protected_field_routing.py`
- `docs/audits/CF2_protected_field_source_default_matrix.md`
- `CL2_projection_presence_policy_extraction.md`

## Ownership labels updated

- CF2 routing rows now expose explicit labels for:
  - `extractor_spec_owner`: `tests.helpers.golden_replay_projection_extractors._PROTECTED_EXTRACTION_SPECS`
  - `presence_policy_owner`: `tests.helpers.golden_replay_projection_presence._build_projection_status`
  - `unavailable_policy_owner`: `tests.helpers.golden_replay_projection_presence._unavailable_paths_for_projection`
  - `representation_policy_owner`: `tests.helpers.golden_replay_projection_presence.protected_path_is_represented_in_observed_turn`
- CF2 tests now assert those owner labels directly.
- CF3 FEM normalization contract now points presence ownership at `golden_replay_projection_presence._build_projection_status`.
- CF4 trace-nest contract now imports trace presence/unavailable constants from `golden_replay_projection_presence.py` and points lookup/unavailable/representation owner constants at the presence module.
- The CF2 audit doc now documents the CL2/CL3 ownership split.
- `golden_replay_projection_extractors.py` re-exports `MISSING` again to preserve existing compatibility imports.

## Intentionally unchanged strings

- `_PROTECTED_EXTRACTION_SPECS` ownership remains assigned to `golden_replay_projection_extractors.py`; this is the extractor spec registry, not presence policy.
- FEM flat extraction ownership remains assigned to extractor helpers such as `_extract_fem_flat_observed_fields`; this is value extraction, not raw/normalized presence policy.
- `_trace_from_payload_or_snapshot` remains assigned to the extractor helper; this is trace source extraction, not unavailable/representation policy.
- Existing compatibility imports/wrappers from `golden_replay_projection_extractors.py` remain intact by design.
- Historical/generated audit fan-in data under `docs/audits/BU_caller_fan_in.csv` was left unchanged because it records old symbol fan-in, not the live conceptual ownership contract.

## Validation commands run and results

Requested command failed because `python` is not on PATH in this PowerShell session:

```powershell
python -m pytest tests/test_cf2_protected_field_routing.py tests/test_golden_replay_projection_presence_integration.py tests/test_golden_replay_projection_modules.py -q
```

Successful equivalent with bundled runtime Python:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_cf2_protected_field_routing.py tests\\test_golden_replay_projection_presence_integration.py tests\\test_golden_replay_projection_modules.py -q
```

Result: `104 passed`.

Docs/manifest validation because the CF2 audit doc was touched:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection_registry.py tests\\test_golden_replay_projection_manifest.py -q
```

Result: `6 passed`.

Additional contract sanity check because CF3/CF4 diagnostic owner constants were touched:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_cf3_raw_normalized_fem_field_matrix.py tests\\test_cf4_trace_nest_dotted_path_contract.py -q
```

Result: `70 passed`.

## Recommended next block

CL4 should target remaining replay-projection churn in generated or historical audit surfaces only if they are still consumed by active tests or dashboards. Avoid classifier/dashboard refactors until the projection helper ownership split has settled.
