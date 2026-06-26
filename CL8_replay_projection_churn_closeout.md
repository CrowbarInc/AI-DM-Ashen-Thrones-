# CL8 Replay Projection Churn Closeout

## Final Recommendation

**Stop CL / Success.**

CL1-CL7 reduced the replay projection churn risk enough to end this cycle. The remaining work in `tests/helpers/golden_replay_projection_extractors.py` is no longer a high-churn protected projection implementation cluster. It is now a thin-to-moderate compatibility/orchestration facade with a few small payload helper responsibilities.

No CL8 refactor was performed. No runtime files were changed, no replay fields were renamed, and no public APIs were removed.

## Final Module Responsibility Map

- `tests/helpers/golden_replay_projection.py`
  - Public facade and `project_turn_observation` orchestration.
  - Builds the final observed row from focused helper modules.
- `tests/helpers/golden_replay_projection_fields.py`
  - Protected observation field schema, field paths, defaults, drift buckets, classifier-evidence path derivation, text hashing/normalization.
- `tests/helpers/golden_replay_projection_registry.py`
  - Protected extraction spec dataclasses, `_PROTECTED_EXTRACTION_SPECS`, registry validation, registry lookup helpers, and derived extractor tuples.
- `tests/helpers/golden_replay_projection_engine.py`
  - Protected field projection execution: FEM flat extraction, sanitizer trace extraction, sanitizer lineage extraction, route-kind resolution, source validation, and flat protected observed-field assembly.
- `tests/helpers/golden_replay_projection_presence.py`
  - Raw/normalized presence policy, missing-source classification, unavailable routing, dotted-path lookup/representation coverage.
- `tests/helpers/golden_replay_projection_semantic.py`
  - Semantic mutation summary projection.
- `tests/helpers/golden_replay_projection_fallbacks.py`
  - Replay fallback-family compatibility projection and related FEM fallback helpers.
- `tests/helpers/golden_replay_projection_speaker.py`
  - Speaker selection and speaker projection parity.
- `tests/helpers/protected_field_routing_contract.py`
  - Machine-readable protected field routing/ownership contract rows derived from registry, presence policy, defaults, and drift buckets.
- `tests/helpers/golden_replay_projection_extractors.py`
  - Compatibility/orchestration facade plus remaining payload helper functions.

## Before/After Churn Risk Summary

Before CL1-CL7:

- `golden_replay_projection_extractors.py` concentrated protected field registry ownership, projection execution, presence/unavailable policy, semantic mutation projection, routing diagnostics, and compatibility imports.
- Ownership strings and tests still pointed at the extractor for responsibilities that had begun to move.
- Adding or changing a protected field risked touching registry data, projection dispatch, presence policy, routing diagnostics, and tests in one large surface.

After CL1-CL7:

- Registry, engine, presence, semantic, routing contract, fallback, and speaker responsibilities are separated.
- The extractor is no longer the owner of registry contents, protected projection execution, presence policy, or semantic mutation projection.
- Compatibility imports are still intentionally retained, but the conceptual owners are now focused modules.
- Module-boundary tests include the new registry, engine, presence, and semantic modules.

Current churn classification:

- `golden_replay_projection_extractors.py`: **thin-to-moderate compatibility/orchestration facade**.
- Not currently a high-churn implementation module.
- Remaining risk is mostly compatibility import fan-in and a few payload-search helper functions, not protected field projection policy concentration.

## Remaining Extractor Responsibilities

Appropriate facade/orchestration responsibility:

- `_trace_from_payload_or_snapshot`
  - Chooses the best debug trace source from payload/session/snapshot.
- `_find_nested_mapping`, `_find_nested_list`, `_find_nested_list_field`
  - Local payload search utilities used by `project_turn_observation`.
- `_runtime_lineage_events_from_payload`
  - Chooses payload-stamped runtime lineage events when present, otherwise builds from FEM.
- `_sanitizer_debug_change_counts`
  - Small observed-row diagnostic derivation for sanitizer debug events.
- `_echo_overlap_band`, `_echo_overlap_ratio`
  - Small observed-row diagnostic shaping for response-delta echo overlap.
- `_validate_protected_classifier_evidence_derivation`
  - Import-time contract guard tying classifier evidence path derivation to the extraction registry.
- `_unavailable_paths_for_projection`, `_build_projection_status`
  - Compatibility wrappers injecting `_PROTECTED_EXTRACTION_SPECS` into the presence policy module.

Compatibility re-export:

- Registry symbols from `golden_replay_projection_registry.py`.
- Engine symbols from `golden_replay_projection_engine.py`.
- Presence symbols from `golden_replay_projection_presence.py`.
- `project_semantic_mutation_summary` from `golden_replay_projection_semantic.py`.
- `MISSING` and `_first_present` compatibility exposure.

Candidate for future extraction:

- Trace/payload utility helpers could become a future `golden_replay_projection_payload.py` or `golden_replay_projection_trace.py` module if they grow.
- Runtime lineage extraction could move to a focused replay-lineage helper if more lineage policy accumulates.

Unnecessary duplication:

- `_first_present` is still duplicated locally in the extractor while also existing in `golden_replay_projection_fields.py`. This is low risk and currently compatibility-preserving. It does not justify another CL block by itself.

## Remaining Direct Private Imports

Intentional compatibility/facade imports:

- `tests/helpers/golden_replay_projection.py` imports many private helper names from `golden_replay_projection_extractors.py`. This is the public facade/orchestration file and remains compatible by design.
- `tests/helpers/golden_replay_projection_extractors.py` imports private symbols from registry, engine, presence, and semantic modules to re-export old extractor paths.

Focused owner-to-owner private imports:

- `golden_replay_projection_engine.py` imports registry internals: `_FEM_FLAT_OBSERVED_EXTRACTORS`, `_PROTECTED_EXTRACTION_SPECS`, `_SANITIZER_LINEAGE_OBSERVED_EXTRACTORS`, `_SANITIZER_TRACE_FLAT_OBSERVED_EXTRACTORS`, `_flat_extractor_source_keys`.
- `protected_field_routing_contract.py`, `trace_nest_contract.py`, and `fem_normalization_contract.py` import registry/presence internals for diagnostic contract construction.

Compatibility tests locking old module paths:

- `tests/test_cf1_route_and_trace_precedence.py`
  - Imports `_resolve_route_kind`, `_trace_from_payload_or_snapshot` from extractor.
- `tests/test_cf1_runtime_lineage_precedence.py`
  - Imports `_runtime_lineage_events_from_payload` from extractor.
- `tests/test_cf3_raw_normalized_fem_field_matrix.py`
  - Imports `_extract_fem_flat_observed_fields`, `_fem_has_any_key` from extractor.
- `tests/test_cf4_trace_nest_dotted_path_contract.py`
  - Imports `MISSING`, `protected_path_covered_by_unavailable`, `protected_path_representation_errors` from extractor.
- `tests/test_golden_replay_projection_semantic.py`
  - Confirms extractor semantic compatibility import.
- `tests/test_golden_replay_projection_registry.py` and `tests/test_golden_replay_projection_engine.py`
  - Confirm extractor compatibility re-exports.

Churn assessment:

- These imports are visible and intentional. They preserve the public/private compatibility surface from before CL1-CL7.
- The remaining old-boundary coupling is not likely to cause high churn unless compatibility imports are removed prematurely.
- Do not remove compatibility imports in this cycle.

## Validation

Focused replay projection validation:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection.py tests\\test_golden_replay_projection_metadata.py tests\\test_golden_replay_projection_registry.py tests\\test_golden_replay_projection_engine.py tests\\test_golden_replay_projection_semantic.py tests\\test_golden_replay_projection_presence_integration.py -q
```

Result: `32 passed`.

Module/routing/FEM/trace validation:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_golden_replay_projection_modules.py tests\\test_cf2_protected_field_routing.py tests\\test_cf3_raw_normalized_fem_field_matrix.py tests\\test_cf4_trace_nest_dotted_path_contract.py -q
```

Result: `167 passed`.

Optional classifier/dashboard bridge validation:

```powershell
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'; & 'C:\\Users\\Master Mandalcio\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe' -m pytest tests\\test_failure_classifier.py tests\\test_failure_dashboard_report.py tests\\test_cf7_synthetic_row_classifier_evidence_bridge.py -q
```

Result: `155 passed`.

## Remaining Churn Risks

- Compatibility imports from `golden_replay_projection_extractors.py` are intentionally broad. Removing them would create churn; leave them in place.
- `golden_replay_projection.py` still imports through the extractor facade rather than directly from every focused module. This is acceptable because it keeps the public facade stable.
- Payload trace/nested-search helpers remain in the extractor. They are small and cohesive enough to defer.
- Historical docs and audit snapshots may still mention older ownership names. CL4 already separated active tested surfaces from historical discovery artifacts.

## Final Decision

**Stop CL / Success.**

Do not start another replay projection refactor block now. The next work should be demand-driven: only extract payload/trace/runtime-lineage helpers if future changes repeatedly touch those functions together or if a specific failing test reveals real ownership ambiguity.
